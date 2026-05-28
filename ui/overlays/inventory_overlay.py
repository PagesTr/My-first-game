import json
from pathlib import Path

import pygame

from systems.economy import calculate_item_sell_price
from systems.equipment import (
    EQUIPMENT_SLOTS,
    RING_SLOTS,
    can_equip_item,
    equip_item,
    get_equipment_slot,
    unequip_item,
)
from systems.equipment_sets import count_equipped_set_pieces, load_equipment_sets
from systems.inventory import compact_inventory, use_consumable_item
from systems.stats import prepare_player_for_combat


class InventoryOverlay:
    def __init__(self, game):
        self.game = game
        self.opened = False
        self.title_font = pygame.font.Font(None, 34)
        self.body_font = pygame.font.Font(None, 23)
        self.small_font = pygame.font.Font(None, 19)
        self.panel_rect = pygame.Rect(0, 0, 0, 0)
        self.close_rect = pygame.Rect(0, 0, 0, 0)
        self.compact_rect = pygame.Rect(0, 0, 0, 0)
        self.stats_details_rect = pygame.Rect(0, 0, 0, 0)
        self.slot_rects = []
        self.equipment_rects = {}
        self.action_rects = {}
        self.filter_rects = {}
        self.active_filter = "all"
        self.show_advanced_stats = False
        self.equipment_sets = load_equipment_sets()
        self.item_icon_map = self._load_item_icon_map()
        self.item_icon_surfaces = {}
        self.icon_warnings = []
        self.selected_item = None
        self.selected_item_source = None
        self.selected_item_position = None
        self.feedback_message = ""
        self.feedback_until_ms = 0
        self.last_click_time = 0
        self.last_click_source = None
        self.double_click_delay = 400

    def open(self):
        self.opened = True

    def close(self):
        self.opened = False
        self._clear_selection()

    def is_open(self):
        return self.opened

    def handle_event(self, event):
        if not self.opened:
            return False

        if event.type == pygame.KEYDOWN:
            if event.key in (pygame.K_ESCAPE, pygame.K_i):
                self.close()
            return True

        if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
            if self.panel_rect.width > 0 and not self.panel_rect.collidepoint(event.pos):
                self.close()
                return True
            self._handle_click(event.pos)
            return True

        return False

    def draw(self, screen):
        if not self.opened:
            return

        overlay = pygame.Surface(screen.get_size(), pygame.SRCALPHA)
        overlay.fill((0, 0, 0, 165))
        screen.blit(overlay, (0, 0))

        panel = self._get_panel_rect(screen)
        self.panel_rect = panel
        pygame.draw.rect(screen, (34, 27, 22), panel, border_radius=8)
        pygame.draw.rect(screen, (171, 132, 70), panel, 2, border_radius=8)
        pygame.draw.rect(screen, (78, 56, 36), panel.inflate(-8, -8), 1, border_radius=6)

        title = self.title_font.render("Inventory", True, (246, 235, 205))
        screen.blit(title, (panel.x + 20, panel.y + 14))

        self.close_rect = pygame.Rect(panel.right - 44, panel.y + 14, 28, 28)
        self.compact_rect = pygame.Rect(panel.right - 150, panel.y + 14, 92, 28)
        self._draw_button(screen, self.close_rect, "X")
        self._draw_button(screen, self.compact_rect, "Compact")

        if not isinstance(getattr(self.game, "player", None), dict):
            message = self.body_font.render("No player inventory available.", True, (236, 224, 195))
            screen.blit(message, (panel.x + 24, panel.y + 76))
            return

        gold_text = self.body_font.render(f"Gold: {self._get_player_gold()}", True, (237, 194, 83))
        screen.blit(gold_text, (panel.x + 22, panel.y + 52))

        if self.feedback_message and pygame.time.get_ticks() < self.feedback_until_ms:
            feedback = self.small_font.render(self.feedback_message, True, (210, 232, 175))
            screen.blit(feedback, (panel.x + 140, panel.y + 56))

        inventory_rect = pygame.Rect(panel.x + 20, panel.y + 104, 372, 232)
        stats_rect = pygame.Rect(panel.x + 20, panel.y + 354, 180, panel.bottom - panel.y - 378)
        effects_rect = pygame.Rect(panel.x + 212, panel.y + 354, 180, panel.bottom - panel.y - 378)
        equipment_rect = pygame.Rect(panel.x + 410, panel.y + 76, panel.right - panel.x - 430, 176)
        details_rect = pygame.Rect(panel.x + 410, panel.y + 270, panel.right - panel.x - 430, panel.bottom - panel.y - 294)

        self._draw_filter_row(screen, pygame.Rect(panel.x + 20, panel.y + 76, 372, 24))
        self._draw_inventory_grid(screen, inventory_rect)
        self._draw_equipment_panel(screen, equipment_rect)
        self._draw_player_stats_panel(screen, stats_rect)
        self._draw_active_effects_panel(screen, effects_rect)
        self._draw_details_panel(screen, details_rect)
        if self.show_advanced_stats:
            self._draw_advanced_stats_panel(screen, panel)

    def _handle_click(self, position):
        if self.close_rect.collidepoint(position):
            self.close()
            return

        if self.compact_rect.collidepoint(position):
            self._compact_inventory()
            return

        if self.stats_details_rect.collidepoint(position):
            self.show_advanced_stats = not self.show_advanced_stats
            return

        for filter_id, rect in self.filter_rects.items():
            if rect.collidepoint(position):
                self.active_filter = filter_id
                self._clear_selection()
                return

        for action_id, rect in self.action_rects.items():
            if rect.collidepoint(position):
                self._handle_action_button(action_id)
                return

        item, source, rect = self._get_item_at_position(position)
        if source is None:
            self._clear_selection()
            return

        if item is None:
            self._clear_selection()
            self.last_click_source = None
            return

        if self._is_double_click(source):
            self._handle_item_action(source)
            return

        self._select_item(item, source, rect)

    def _draw_filter_row(self, screen, area):
        filters = [
            ("all", "All"),
            ("gear", "Gear"),
            ("consumables", "Consumables"),
            ("materials", "Materials"),
        ]
        self.filter_rects = {}
        x = area.x
        for filter_id, label in filters:
            width = max(48, self.small_font.size(label)[0] + 16)
            rect = pygame.Rect(x, area.y, width, area.height)
            self.filter_rects[filter_id] = rect
            is_active = filter_id == self.active_filter
            pygame.draw.rect(screen, (80, 58, 35) if is_active else (44, 37, 32), rect, border_radius=4)
            pygame.draw.rect(screen, (215, 176, 91) if is_active else (105, 82, 52), rect, 1, border_radius=4)
            text = self.small_font.render(label, True, (246, 235, 205) if is_active else (204, 191, 168))
            screen.blit(text, text.get_rect(center=rect.center))
            x += width + 6

    def _draw_inventory_grid(self, screen, area):
        label = self.body_font.render("Bag", True, (238, 226, 194))
        screen.blit(label, (area.x, area.y - 24))

        slot_size = 46
        spacing = 6
        columns = 7
        self.slot_rects = []

        visible_slots = self._get_visible_inventory_slots()
        for visible_index, (slot_index, slot) in enumerate(visible_slots):
            column = visible_index % columns
            row = visible_index // columns
            rect = pygame.Rect(
                area.x + column * (slot_size + spacing),
                area.y + row * (slot_size + spacing),
                slot_size,
                slot_size,
            )
            if rect.bottom > area.bottom:
                break
            self.slot_rects.append((slot_index, rect))
            self._draw_inventory_slot(screen, rect, slot, ("inventory", slot_index))

    def _draw_inventory_slot(self, screen, rect, slot, source):
        is_selected = source == self.selected_item_source
        item_data = self._get_item_data(slot)
        rarity_color = self._get_rarity_color(slot, item_data)
        pygame.draw.rect(screen, (38, 31, 27) if slot is None else (50, 40, 31), rect, border_radius=5)
        pygame.draw.rect(screen, rarity_color if slot is not None else (84, 70, 50), rect, 2, border_radius=5)
        if is_selected:
            pygame.draw.rect(screen, (248, 220, 113), rect.inflate(4, 4), 2, border_radius=6)

        if slot is None:
            return

        icon_rect = rect.inflate(-12, -15)
        icon_rect.y -= 2
        used_mapped_icon = self._draw_item_icon(screen, icon_rect, slot, item_data)

        quantity = slot.get("quantity")
        if quantity is not None:
            quantity_surface = self.small_font.render(str(quantity), True, (255, 236, 170))
            quantity_rect = quantity_surface.get_rect(bottomright=(rect.right - 4, rect.bottom - 2))
            screen.blit(quantity_surface, quantity_rect)

        if not used_mapped_icon:
            item_name = self._get_item_display_name(slot, item_data)
            label = self._shorten_text(item_name, rect.width - 4, self.small_font)
            label_surface = self.small_font.render(label, True, (230, 217, 190))
            screen.blit(label_surface, label_surface.get_rect(midbottom=(rect.centerx, rect.bottom - 3)))

    def _draw_item_icon(self, screen, rect, item, item_data):
        item_id = item.get("item") if isinstance(item, dict) else None
        icon_surface = self._get_item_icon_surface(item_id)
        if icon_surface is not None:
            self._draw_icon_surface(screen, icon_surface, rect)
            return True

        item_type = item_data.get("type")
        category = item_data.get("category") or item_type or item.get("kind")
        center = rect.center

        if item_type == "equipment" or category in {"weapon", "armor", "helmet", "chest", "pants", "gloves", "boots", "ring", "amulet", "trinket"}:
            if category == "weapon":
                pygame.draw.line(screen, (202, 213, 214), (rect.left + 4, rect.bottom - 4), (rect.right - 4, rect.top + 4), 3)
                pygame.draw.line(screen, (122, 82, 50), (rect.left + 6, rect.bottom - 6), (rect.left + 13, rect.bottom - 13), 4)
                pygame.draw.line(screen, (221, 174, 79), (rect.left + 8, rect.bottom - 15), (rect.left + 18, rect.bottom - 5), 2)
            else:
                points = [(center[0], rect.top + 2), (rect.right - 3, rect.top + 9), (rect.right - 7, rect.bottom - 4), (center[0], rect.bottom), (rect.left + 7, rect.bottom - 4), (rect.left + 3, rect.top + 9)]
                pygame.draw.polygon(screen, (116, 135, 142), points)
                pygame.draw.polygon(screen, (197, 156, 83), points, 2)
        elif item_type == "consumable":
            bottle = pygame.Rect(center[0] - 6, rect.top + 7, 12, rect.height - 9)
            pygame.draw.rect(screen, (93, 43, 122), (center[0] - 3, rect.top + 2, 6, 7), border_radius=2)
            pygame.draw.rect(screen, (55, 129, 122), bottle, border_radius=4)
            pygame.draw.rect(screen, (168, 224, 190), bottle.inflate(-5, -7), border_radius=2)
        elif item_type in {"material", "resource"} or item.get("kind") == "stackable":
            points = [(center[0], rect.top + 3), (rect.right - 4, center[1]), (center[0], rect.bottom - 3), (rect.left + 4, center[1])]
            pygame.draw.polygon(screen, (64, 159, 113), points)
            pygame.draw.polygon(screen, (175, 218, 151), points, 2)
        elif item_type == "quest":
            page = pygame.Rect(rect.left + 6, rect.top + 3, rect.width - 12, rect.height - 6)
            pygame.draw.rect(screen, (211, 184, 127), page, border_radius=2)
            pygame.draw.line(screen, (105, 75, 42), (page.x + 4, page.y + 7), (page.right - 4, page.y + 7), 1)
            pygame.draw.line(screen, (105, 75, 42), (page.x + 4, page.y + 13), (page.right - 7, page.y + 13), 1)
        elif item_type == "recipe":
            pygame.draw.rect(screen, (85, 122, 82), rect.inflate(-5, -3), border_radius=2)
            pygame.draw.line(screen, (226, 214, 159), (center[0], rect.top + 3), (center[0], rect.bottom - 3), 1)
        else:
            pygame.draw.rect(screen, (116, 100, 78), rect.inflate(-6, -6), border_radius=3)
            question = self.small_font.render("?", True, (245, 230, 190))
            screen.blit(question, question.get_rect(center=center))
        return False

    def _draw_equipment_panel(self, screen, area):
        title = self.body_font.render("Equipment", True, (238, 226, 194))
        screen.blit(title, (area.x, area.y - 24))

        equipment = self._get_equipment()
        self.equipment_rects = {}
        slot_width = max(94, (area.width - 8) // 2)
        slot_height = 25
        labels = self._equipment_labels()

        for index, slot_key in enumerate(EQUIPMENT_SLOTS):
            column = index % 2
            row = index // 2
            rect = pygame.Rect(
                area.x + column * (slot_width + 8),
                area.y + row * (slot_height + 4),
                slot_width,
                slot_height,
            )
            self.equipment_rects[slot_key] = rect
            item = equipment.get(slot_key) if isinstance(equipment, dict) else None
            source = ("equipment", slot_key)
            is_selected = source == self.selected_item_source
            item_data = self._get_item_data(item)
            border_color = self._get_rarity_color(item, item_data) if item else (91, 74, 54)
            pygame.draw.rect(screen, (38, 31, 27), rect, border_radius=4)
            pygame.draw.rect(screen, (248, 220, 113) if is_selected else border_color, rect, 2, border_radius=4)

            slot_label = labels.get(slot_key, slot_key)
            item_label = self._get_item_display_name(item, item_data) if item is not None else "Empty"
            label_surface = self.small_font.render(slot_label, True, (199, 178, 139))
            screen.blit(label_surface, (rect.x + 5, rect.y + 2))
            item_surface = self.small_font.render(self._shorten_text(item_label, rect.width - 10, self.small_font), True, border_color if item else (130, 119, 101))
            screen.blit(item_surface, (rect.x + 5, rect.y + 13))

    def _draw_player_stats_panel(self, screen, rect):
        pygame.draw.rect(screen, (30, 25, 22), rect, border_radius=6)
        pygame.draw.rect(screen, (121, 91, 55), rect, 1, border_radius=6)
        title = self.small_font.render("Stats", True, (238, 226, 194))
        screen.blit(title, (rect.x + 8, rect.y + 6))

        self.stats_details_rect = pygame.Rect(rect.right - 58, rect.y + 5, 50, 20)
        self._draw_button(screen, self.stats_details_rect, "Details")

        player = self._get_player()
        stats = [
            ("Max HP", "max_hp", player.get("max_hp", 0)),
            ("Current HP", "current_hp", player.get("current_hp", 0)),
            ("Attack", "attack", player.get("attack", 0)),
            ("Defense", "defense", player.get("defense", 0)),
            ("Strength", "strength", player.get("strength", player.get("force", 0))),
            ("Dexterity", "agility", player.get("dexterity", player.get("agility", 0))),
            ("Intelligence", "intelligence", player.get("intelligence", 0)),
            ("Vitality", "vitality", player.get("vitality", 0)),
            ("Wisdom", "wisdom", player.get("wisdom", 0)),
            ("Luck", "luck", player.get("luck", 0)),
        ]

        start_y = rect.y + 29
        column_width = 88
        for index, (label, stat_key, value) in enumerate(stats):
            column = index // 5
            row = index % 5
            line = f"{label}: {self._format_stat_value(stat_key, value)}"
            surface = self.small_font.render(self._shorten_text(line, column_width - 4, self.small_font), True, (212, 202, 180))
            screen.blit(surface, (rect.x + 8 + column * column_width, start_y + row * 15))

    def _draw_advanced_stats_panel(self, screen, parent_rect):
        rect = pygame.Rect(0, 0, 390, 250)
        rect.center = parent_rect.center
        pygame.draw.rect(screen, (24, 21, 20), rect, border_radius=8)
        pygame.draw.rect(screen, (207, 160, 82), rect, 2, border_radius=8)

        title = self.body_font.render("Advanced Stats", True, (246, 235, 205))
        screen.blit(title, (rect.x + 16, rect.y + 12))

        player = self._get_player()
        stats = [
            ("Magic Attack", "magic_attack", player.get("magic_attack", 0)),
            ("Magic Defense", "magic_defense", player.get("magic_defense", 0)),
            ("Accuracy", "accuracy", player.get("accuracy", 0)),
            ("Dodge", "dodge_chance", player.get("dodge_chance", 0)),
            ("Block", "block_chance", player.get("block_chance", 0)),
            ("Crit Chance", "crit_chance", player.get("crit_chance", 0)),
            ("Crit Damage", "crit_damage", player.get("crit_damage", 0)),
            ("Initiative", "initiative", player.get("initiative", 0)),
            ("Healing Power", "healing_power", player.get("healing_power", 0)),
            ("Status Resist", "status_resistance", player.get("status_resistance", 0)),
            ("Loot Bonus", "loot_bonus", player.get("loot_bonus", 0)),
            ("Gold Bonus", "gold_bonus", player.get("gold_bonus", 0)),
            ("Rare Find", "rare_find_bonus", player.get("rare_find_bonus", 0)),
            ("XP Bonus", "xp_bonus", player.get("xp_bonus", 0)),
        ]

        x_positions = [rect.x + 18, rect.x + 205]
        y_positions = [rect.y + 46, rect.y + 46]
        for index, (label, stat_key, value) in enumerate(stats):
            column = index // 7
            line = f"{label}: {self._format_stat_value(stat_key, value)}"
            surface = self.small_font.render(self._shorten_text(line, 168, self.small_font), True, (212, 202, 180))
            screen.blit(surface, (x_positions[column], y_positions[column]))
            y_positions[column] += 22

        hint = self.small_font.render("Click Details again to close", True, (168, 156, 138))
        screen.blit(hint, (rect.x + 16, rect.bottom - 28))

    def _draw_active_effects_panel(self, screen, rect):
        pygame.draw.rect(screen, (30, 25, 22), rect, border_radius=6)
        pygame.draw.rect(screen, (121, 91, 55), rect, 1, border_radius=6)
        title = self.small_font.render("Active Effects", True, (238, 226, 194))
        screen.blit(title, (rect.x + 8, rect.y + 6))

        active_effects = self._get_player().get("active_effects", [])
        valid_effects = [effect for effect in active_effects if isinstance(effect, dict)]
        if not valid_effects:
            none_text = self.small_font.render("None", True, (168, 156, 138))
            screen.blit(none_text, (rect.x + 8, rect.y + 28))
            return

        y = rect.y + 28
        for effect in valid_effects[:4]:
            line = self._format_effect_line(effect)
            surface = self.small_font.render(self._shorten_text(line, rect.width - 16, self.small_font), True, (212, 202, 180))
            screen.blit(surface, (rect.x + 8, y))
            y += 15

    def _draw_details_panel(self, screen, rect):
        pygame.draw.rect(screen, (30, 25, 22), rect, border_radius=6)
        pygame.draw.rect(screen, (121, 91, 55), rect, 1, border_radius=6)
        self.action_rects = {}

        item = self._get_selected_item()
        if item is None:
            text = self.small_font.render("Select an item to view details.", True, (205, 190, 164))
            screen.blit(text, (rect.x + 12, rect.y + 12))
            return

        item_data = self._get_item_data(item)
        name = self._get_item_display_name(item, item_data)
        rarity = item.get("rarity") or item_data.get("rarity") or "common"
        y = rect.y + 10

        name_width = rect.width - 20
        icon_rect = pygame.Rect(rect.right - 44, rect.y + 8, 32, 32)
        self._draw_item_icon(screen, icon_rect, item, item_data)
        name_width -= 40

        name_surface = self.body_font.render(self._shorten_text(name, name_width, self.body_font), True, self._get_rarity_color(item, item_data))
        screen.blit(name_surface, (rect.x + 10, y))
        y += 25

        sell_price = calculate_item_sell_price(item, item_data)
        detail_lines = [
            ("Item", "section"),
            (f"Type: {self._get_type_label(item_data.get('type'))}", "normal"),
            (f"Kind: {item.get('kind', '-')}", "normal"),
            (f"Rarity: {str(rarity).capitalize()}", "rarity"),
            (f"Sell price: {sell_price} gold" if sell_price > 0 else "Sell price: -", "normal"),
        ]
        quantity = item.get("quantity")
        if quantity is not None:
            detail_lines.append((f"Quantity: {quantity}", "normal"))
        level = item.get("level") or item_data.get("level")
        if level is not None:
            detail_lines.append((f"Level: {level}", "normal"))

        for line, role in detail_lines:
            color = self._get_detail_role_color(role, item, item_data)
            surface = self.small_font.render(self._shorten_text(line, rect.width - 20, self.small_font), True, color)
            screen.blit(surface, (rect.x + 10, y))
            y += 15

        stats = self._get_item_stats(item)
        if isinstance(stats, dict) and stats:
            stats_label = self.small_font.render("Stats", True, (238, 226, 194))
            screen.blit(stats_label, (rect.x + 10, y))
            y += 17
            for stat_name, value in list(stats.items())[:3]:
                stat_text = self.small_font.render(
                    f"{self._get_stat_label(stat_name)}: {self._format_stat_value(stat_name, value)}",
                    True,
                    (190, 215, 184),
                )
                screen.blit(stat_text, (rect.x + 16, y))
                y += 15

        y = self._draw_comparison_section(screen, rect, item, y)
        y = self._draw_set_section(screen, rect, item, y)

        description = item_data.get("description")
        if description and y < rect.bottom - 60:
            y += 4
            self._draw_wrapped_text(screen, description, rect.x + 10, y, rect.width - 20, self.small_font, (191, 181, 158), rect.bottom - 40)

        self._draw_action_buttons(screen, rect)

    def _draw_comparison_section(self, screen, rect, item, y):
        current_item = self._get_comparison_item_for_source(item, self.selected_item_source)
        if self.selected_item_source is None or self.selected_item_source[0] != "inventory":
            return y
        if not can_equip_item(item, self._get_items_data()):
            return y

        if y > rect.bottom - 78:
            return y

        title = self.small_font.render("Comparison", True, (238, 226, 194))
        screen.blit(title, (rect.x + 10, y))
        y += 16

        if current_item is None:
            empty = self.small_font.render("Compared slot is empty.", True, (168, 156, 138))
            screen.blit(empty, (rect.x + 16, y))
            return y + 15

        current_name = self._get_item_display_name(current_item, self._get_item_data(current_item))
        compared = self.small_font.render(self._shorten_text(f"Vs: {current_name}", rect.width - 26, self.small_font), True, (200, 190, 168))
        screen.blit(compared, (rect.x + 16, y))
        y += 15

        new_stats = self._get_item_stats(item)
        current_stats = self._get_item_stats(current_item)
        stat_keys = sorted(set(new_stats) | set(current_stats), key=self._get_stat_label)
        for stat_key in stat_keys[:3]:
            new_value = new_stats.get(stat_key, 0)
            current_value = current_stats.get(stat_key, 0)
            if not isinstance(new_value, (int, float)) or not isinstance(current_value, (int, float)):
                continue
            diff = new_value - current_value
            color = (105, 210, 124) if diff > 0 else (224, 94, 94) if diff < 0 else (165, 160, 150)
            line = (
                f"{self._get_stat_label(stat_key)}: "
                f"{self._format_stat_value(stat_key, new_value)} vs "
                f"{self._format_stat_value(stat_key, current_value)} "
                f"({self._format_stat_difference(stat_key, diff)})"
            )
            surface = self.small_font.render(self._shorten_text(line, rect.width - 26, self.small_font), True, color)
            screen.blit(surface, (rect.x + 16, y))
            y += 15
            if y > rect.bottom - 46:
                break
        return y

    def _draw_set_section(self, screen, rect, item, y):
        set_id = self._get_item_set_id(item)
        if not set_id or y > rect.bottom - 76:
            return y

        set_data = self._get_set_data(set_id)
        progress = self._get_set_progress(set_id)
        set_name = set_data.get("name", str(set_id))
        title = f"Set: {set_name} ({progress['equipped_count']}/{progress['total_count']})"
        surface = self.small_font.render(self._shorten_text(title, rect.width - 20, self.small_font), True, (207, 176, 98))
        screen.blit(surface, (rect.x + 10, y))
        y += 16

        pieces = []
        for piece_id in progress["piece_ids"][:3]:
            piece_data = self._get_items_data().get(piece_id, {})
            piece_name = piece_data.get("name", piece_id) if isinstance(piece_data, dict) else piece_id
            marker = "*" if piece_id in progress["equipped_piece_ids"] else "-"
            pieces.append(f"{marker} {piece_name}")
        if pieces:
            piece_line = self._shorten_text(", ".join(pieces), rect.width - 26, self.small_font)
            piece_surface = self.small_font.render(piece_line, True, (190, 202, 188))
            screen.blit(piece_surface, (rect.x + 16, y))
            y += 15

        bonuses = set_data.get("bonuses", {})
        if isinstance(bonuses, dict):
            sorted_bonuses = []
            for threshold_key, threshold_bonuses in bonuses.items():
                try:
                    sorted_bonuses.append((int(threshold_key), threshold_bonuses))
                except (TypeError, ValueError):
                    continue
            for threshold, threshold_bonuses in sorted(sorted_bonuses)[:2]:
                is_active = progress["equipped_count"] >= threshold
                marker = "*" if is_active else "-"
                line = f"{marker} {self._format_set_bonus_line(threshold, threshold_bonuses)}"
                color = (105, 210, 124) if is_active else (145, 136, 120)
                bonus_surface = self.small_font.render(self._shorten_text(line, rect.width - 26, self.small_font), True, color)
                screen.blit(bonus_surface, (rect.x + 16, y))
                y += 15
                if y > rect.bottom - 46:
                    break
        return y

    def _draw_action_buttons(self, screen, details_rect):
        actions = self._get_available_actions()
        x = details_rect.x + 10
        y = details_rect.bottom - 34
        for action_id, label in actions:
            width = max(68, self.small_font.size(label)[0] + 18)
            rect = pygame.Rect(x, y, width, 24)
            self.action_rects[action_id] = rect
            self._draw_button(screen, rect, label)
            x += width + 8

    def _draw_button(self, screen, rect, label):
        pygame.draw.rect(screen, (72, 49, 31), rect, border_radius=5)
        pygame.draw.rect(screen, (188, 144, 74), rect, 1, border_radius=5)
        highlight = pygame.Rect(rect.x + 2, rect.y + 2, rect.width - 4, 1)
        pygame.draw.rect(screen, (228, 187, 104), highlight)
        text = self.small_font.render(label, True, (246, 235, 205))
        screen.blit(text, text.get_rect(center=rect.center))

    def _get_item_at_position(self, position):
        for index, rect in self.slot_rects:
            if rect.collidepoint(position):
                slots = self._get_inventory_slots()
                return (slots[index], ("inventory", index), rect) if index < len(slots) else (None, None, rect)

        equipment = self._get_equipment()
        for slot_key, rect in self.equipment_rects.items():
            if rect.collidepoint(position):
                item = equipment.get(slot_key) if isinstance(equipment, dict) else None
                return item, ("equipment", slot_key), rect

        return None, None, None

    def _select_item(self, item, source, rect):
        self.selected_item = item
        self.selected_item_source = source
        self.selected_item_position = rect.center if rect is not None else None

    def _is_double_click(self, source):
        current_time = pygame.time.get_ticks()
        is_double_click = (
            source == self.last_click_source
            and current_time - self.last_click_time <= self.double_click_delay
        )
        self.last_click_time = current_time
        self.last_click_source = source
        return is_double_click

    def _handle_action_button(self, action_id):
        if action_id == "equip" and self.selected_item_source is not None:
            success = self._handle_item_action(self.selected_item_source)
            self._set_feedback("Equipped" if success else "Cannot equip")
        elif action_id == "use" and self.selected_item_source is not None:
            success = self._handle_item_action(self.selected_item_source)
            self._set_feedback("Used" if success else "Cannot use")
        elif action_id == "unequip" and self.selected_item_source is not None:
            success = self._handle_item_action(self.selected_item_source)
            self._set_feedback("Unequipped" if success else "Cannot unequip")

    def _handle_item_action(self, source):
        if not self._has_player_inventory():
            self._clear_selection()
            return False

        source_type, source_key = source
        action_done = False
        success_message = ""

        if source_type == "inventory":
            inventory = self.game.player["inventory"]
            slots = inventory.get("slots", [])
            if not isinstance(source_key, int) or source_key < 0 or source_key >= len(slots):
                self._clear_selection()
                return False

            item = slots[source_key]
            if item is None:
                self._clear_selection()
                return False

            item_data = self._get_item_data(item)
            if item.get("kind") == "stackable" and item_data.get("type") == "consumable":
                action_done = use_consumable_item(self.game.player, inventory, source_key, self._get_items_data())
                success_message = "Used"
                if not action_done:
                    self._set_feedback("Cannot use")
            else:
                action_done = equip_item(self.game.player, inventory, source_key, self._get_items_data())
                success_message = "Equipped"
                if not action_done:
                    self._set_feedback("Cannot equip")
        elif source_type == "equipment":
            action_done = unequip_item(self.game.player, self.game.player["inventory"], source_key)
            success_message = "Unequipped"
            if not action_done:
                self._set_feedback("Cannot unequip")

        if action_done:
            self._after_inventory_change()
            self._set_feedback(success_message)
        return action_done

    def _compact_inventory(self):
        if not self._has_player_inventory():
            self._set_feedback("No inventory")
            return False
        compacted = compact_inventory(self.game.player["inventory"])
        if compacted:
            self._clear_selection()
            self._save_current_game()
            self._set_feedback("Inventory compacted")
        else:
            self._set_feedback("Cannot compact")
        return compacted

    def _after_inventory_change(self):
        data = getattr(self.game, "data", None)
        prepare_player_for_combat(
            self.game.player,
            self._get_items_data(),
            getattr(data, "classes", {}) if data is not None else {},
            getattr(data, "skills", {}) if data is not None else None,
        )
        self._save_current_game()
        self._clear_selection()

    def _save_current_game(self):
        if hasattr(self.game, "save_current_game"):
            self.game.save_current_game()

    def _clear_selection(self):
        self.selected_item = None
        self.selected_item_source = None
        self.selected_item_position = None
        self.last_click_source = None

    def _get_selected_item(self):
        if self.selected_item_source is None:
            return None
        source_type, source_key = self.selected_item_source
        if source_type == "inventory":
            slots = self._get_inventory_slots()
            if isinstance(source_key, int) and 0 <= source_key < len(slots):
                self.selected_item = slots[source_key]
                return self.selected_item
            return None
        if source_type == "equipment":
            equipment = self._get_equipment()
            self.selected_item = equipment.get(source_key) if isinstance(equipment, dict) else None
            return self.selected_item
        return None

    def _get_available_actions(self):
        item = self._get_selected_item()
        if item is None or self.selected_item_source is None:
            return []

        source_type, source_key = self.selected_item_source
        item_data = self._get_item_data(item)
        if source_type == "equipment":
            return [("unequip", "Unequip")]
        if source_type == "inventory" and item.get("kind") == "stackable" and item_data.get("type") == "consumable":
            return [("use", "Use")]
        if source_type == "inventory" and can_equip_item(item, self._get_items_data()):
            return [("equip", "Equip")]
        return []

    def _has_player_inventory(self):
        player = getattr(self.game, "player", None)
        return (
            isinstance(player, dict)
            and isinstance(player.get("inventory"), dict)
            and isinstance(player["inventory"].get("slots"), list)
        )

    def _get_inventory_slots(self):
        if not self._has_player_inventory():
            return []
        return self.game.player["inventory"]["slots"]

    def _get_visible_inventory_slots(self):
        slots = self._get_inventory_slots()
        if self.active_filter == "all":
            return list(enumerate(slots))

        visible = []
        for index, slot in enumerate(slots):
            if slot is not None and self._slot_matches_filter(slot, self.active_filter):
                visible.append((index, slot))
        return visible

    def _slot_matches_filter(self, item, filter_id):
        item_data = self._get_item_data(item)
        item_type = item_data.get("type")
        category = item_data.get("category")
        if filter_id == "gear":
            return item_type == "equipment" or category in {"weapon", "armor", "helmet", "chest", "pants", "gloves", "boots", "ring", "amulet", "trinket"}
        if filter_id == "consumables":
            return item_type == "consumable"
        if filter_id == "materials":
            return item_type in {"material", "resource"} or item.get("kind") == "stackable"
        return True

    def _get_equipment(self):
        player = getattr(self.game, "player", {})
        equipment = player.get("equipment", {}) if isinstance(player, dict) else {}
        return equipment if isinstance(equipment, dict) else {}

    def _get_player(self):
        player = getattr(self.game, "player", {})
        return player if isinstance(player, dict) else {}

    def _get_player_gold(self):
        player = getattr(self.game, "player", {})
        if isinstance(player, dict):
            return player.get("gold", 0)
        return 0

    def _get_items_data(self):
        data = getattr(self.game, "data", None)
        items = getattr(data, "items", {}) if data is not None else {}
        return items if isinstance(items, dict) else {}

    def _load_item_icon_map(self):
        icon_map_path = Path("data/item_icons.json")
        if not icon_map_path.exists():
            return {}
        try:
            raw_mapping = json.loads(icon_map_path.read_text(encoding="utf-8"))
        except (OSError, json.JSONDecodeError):
            return {}
        if not isinstance(raw_mapping, dict):
            return {}
        return {
            str(item_id): str(icon_path)
            for item_id, icon_path in raw_mapping.items()
            if item_id and isinstance(icon_path, str) and icon_path.strip()
        }

    def _get_item_icon_surface(self, item_id):
        if not item_id:
            return None
        item_id = str(item_id)
        if item_id in self.item_icon_surfaces:
            return self.item_icon_surfaces[item_id]

        icon_path = self.item_icon_map.get(item_id)
        if not icon_path:
            self.item_icon_surfaces[item_id] = None
            return None

        path = Path(icon_path)
        if not path.exists():
            self.icon_warnings.append(f"Missing icon for {item_id}: {icon_path}")
            self.item_icon_surfaces[item_id] = None
            return None

        try:
            surface = pygame.image.load(str(path)).convert_alpha()
        except (OSError, pygame.error):
            self.icon_warnings.append(f"Invalid icon for {item_id}: {icon_path}")
            surface = None
        self.item_icon_surfaces[item_id] = surface
        return surface

    def _draw_icon_surface(self, screen, icon_surface, rect):
        icon_size = min(32, rect.width, rect.height)
        scaled_icon = pygame.transform.scale(icon_surface, (icon_size, icon_size))
        screen.blit(scaled_icon, scaled_icon.get_rect(center=rect.center))

    def _get_item_data(self, item):
        if item is None:
            return {}
        return self._get_items_data().get(item.get("item"), {})

    def _get_item_display_name(self, item, item_data):
        if item is None:
            return ""
        item_id = item.get("item", "")
        return item_data.get("name") or item_id

    def _get_item_stats(self, item):
        if not isinstance(item, dict):
            return {}
        item_data = self._get_item_data(item)
        stats = item.get("stats")
        if stats is None:
            stats = item_data.get("stats", {})
        return stats if isinstance(stats, dict) else {}

    def _get_item_set_id(self, item):
        return self._get_item_data(item).get("set_id")

    def _get_set_data(self, set_id):
        set_data = self.equipment_sets.get(set_id, {})
        return set_data if isinstance(set_data, dict) else {}

    def _get_set_piece_ids(self, set_id):
        piece_ids = []
        for item_id, item_data in self._get_items_data().items():
            if isinstance(item_data, dict) and item_data.get("set_id") == set_id:
                piece_ids.append(item_id)
        return piece_ids

    def _get_equipped_set_piece_ids(self, set_id):
        equipped_piece_ids = set()
        for item in self._get_equipment().values():
            if not isinstance(item, dict):
                continue
            item_data = self._get_item_data(item)
            if item_data.get("set_id") == set_id:
                equipped_piece_ids.add(item.get("item"))
        return equipped_piece_ids

    def _get_set_progress(self, set_id):
        piece_ids = self._get_set_piece_ids(set_id)
        set_counts = count_equipped_set_pieces(self._get_player(), self._get_items_data())
        equipped_piece_ids = self._get_equipped_set_piece_ids(set_id)
        return {
            "piece_ids": piece_ids,
            "equipped_piece_ids": equipped_piece_ids,
            "equipped_count": set_counts.get(set_id, len(equipped_piece_ids)),
            "total_count": len(piece_ids),
        }

    def _get_comparison_item_for_source(self, item, source):
        if source is None or source[0] != "inventory":
            return None
        equipment_type = self._get_equipment_type(item)
        if equipment_type is None:
            return None
        return self._get_comparison_item_for_equipment_type(equipment_type)

    def _get_equipment_type(self, item):
        item_data = self._get_item_data(item)
        item_type = item_data.get("type")
        item_category = item_data.get("category") if item_type == "equipment" else item_type
        if item_category == "ring":
            return "ring"
        return get_equipment_slot(item_data)

    def _get_comparison_item_for_equipment_type(self, equipment_type):
        equipment = self._get_equipment()
        if equipment_type != "ring":
            return equipment.get(equipment_type)
        for ring_slot in RING_SLOTS:
            if equipment.get(ring_slot) is None:
                return None
        return equipment.get(RING_SLOTS[0])

    def _get_type_label(self, item_type):
        labels = {
            "equipment": "Equipment",
            "consumable": "Consumable",
            "resource": "Resource",
            "material": "Material",
            "currency": "Currency",
            "quest": "Quest",
            "recipe": "Recipe",
        }
        if not item_type:
            return "Unknown"
        return labels.get(item_type, str(item_type).replace("_", " ").title())

    def _get_detail_role_color(self, role, item, item_data):
        if role == "section":
            return (238, 226, 194)
        if role == "rarity":
            return self._get_rarity_color(item, item_data)
        return (210, 198, 174)

    def _format_stat_value(self, stat_key, value):
        percent_stats = {
            "accuracy",
            "dodge_chance",
            "block_chance",
            "crit_chance",
            "status_resistance",
            "loot_bonus",
            "gold_bonus",
            "rare_find_bonus",
            "xp_bonus",
        }
        if stat_key in percent_stats and isinstance(value, (int, float)):
            return f"{value * 100:.1f}%"
        if stat_key == "crit_damage":
            return f"x{value}"
        return str(value)

    def _format_stat_difference(self, stat_key, diff):
        if not isinstance(diff, (int, float)):
            return "="
        rounded_diff = round(diff, 10)
        if rounded_diff == 0:
            return "="
        sign = "+" if rounded_diff > 0 else "-"
        absolute_diff = abs(rounded_diff)
        percent_stats = {
            "accuracy",
            "dodge_chance",
            "block_chance",
            "crit_chance",
            "status_resistance",
            "loot_bonus",
            "gold_bonus",
            "rare_find_bonus",
            "xp_bonus",
        }
        if stat_key in percent_stats:
            return f"{sign}{absolute_diff * 100:.1f}%"
        if stat_key == "crit_damage":
            return f"{sign}{absolute_diff:.2f}"
        if float(absolute_diff).is_integer():
            return f"{sign}{int(absolute_diff)}"
        return f"{sign}{absolute_diff:.2f}".rstrip("0").rstrip(".")

    def _format_effect_line(self, effect):
        name = effect.get("name", effect.get("id", "Unknown Effect"))
        duration_type = effect.get("duration_type")
        if duration_type == "combat":
            duration = f"{effect.get('remaining_combats', 0)} combat(s)"
        elif duration_type == "time":
            duration = f"{effect.get('remaining_seconds', 0)}s"
        else:
            duration = "Unknown"

        modifier_text = ""
        modifiers = effect.get("modifiers", {})
        if isinstance(modifiers, dict):
            for stat, value in modifiers.items():
                if isinstance(value, (int, float)):
                    sign = "+" if value > 0 else "-" if value < 0 else ""
                    modifier_text = f"{sign}{self._format_stat_value(stat, abs(value))} {self._get_stat_label(stat)}"
                    break
        return f"{name} {duration} {modifier_text}".strip()

    def _format_set_bonus_line(self, threshold, bonuses):
        bonus_parts = []
        if not isinstance(bonuses, dict):
            bonuses = {}
        for stat, value in bonuses.items():
            if not isinstance(value, (int, float)):
                continue
            sign = "+" if value > 0 else ""
            bonus_parts.append(f"{sign}{self._format_stat_value(stat, value)} {self._get_stat_label(stat)}")
        bonus_text = ", ".join(bonus_parts) if bonus_parts else "No bonus"
        return f"{threshold} pieces: {bonus_text}"

    def _get_stat_label(self, stat_name):
        labels = {
            "attack": "Attack",
            "defense": "Defense",
            "hp": "HP",
            "max_hp": "Max HP",
            "current_hp": "Current HP",
            "force": "Strength",
            "strength": "Strength",
            "agility": "Agility",
            "dexterity": "Dexterity",
            "intelligence": "Intelligence",
            "vitality": "Vitality",
            "wisdom": "Wisdom",
            "luck": "Luck",
            "magic_attack": "Magic Attack",
            "magic_defense": "Magic Defense",
            "accuracy": "Accuracy",
            "dodge_chance": "Dodge",
            "block_chance": "Block",
            "crit_chance": "Crit Chance",
            "crit_damage": "Crit Damage",
            "initiative": "Initiative",
            "healing_power": "Healing Power",
            "status_resistance": "Status Resist",
            "loot_bonus": "Loot Bonus",
            "gold_bonus": "Gold Bonus",
            "rare_find_bonus": "Rare Find",
            "xp_bonus": "XP Bonus",
        }
        return labels.get(stat_name, self._format_stat_name(stat_name))

    def _get_rarity_color(self, item, item_data=None):
        colors = {
            "common": (178, 174, 164),
            "uncommon": (95, 205, 119),
            "rare": (91, 151, 236),
            "epic": (174, 105, 231),
            "legendary": (241, 166, 62),
            "unique": (230, 82, 82),
        }
        if item is None:
            return (92, 78, 58)
        if item_data is None:
            item_data = self._get_item_data(item)
        rarity = item.get("rarity") or item_data.get("rarity")
        return colors.get(rarity, (178, 174, 164))

    def _get_panel_rect(self, screen):
        screen_rect = screen.get_rect()
        panel_width = min(760, screen_rect.width - 32)
        panel_height = min(500, screen_rect.height - 76)
        panel = pygame.Rect(0, 0, panel_width, panel_height)
        panel.centerx = screen_rect.centerx
        panel.y = max(18, (screen_rect.height - panel_height - 42) // 2)
        return panel

    def _equipment_labels(self):
        return {
            "weapon": "Weapon",
            "helmet": "Helmet",
            "chest": "Chest",
            "pants": "Pants",
            "gloves": "Gloves",
            "boots": "Boots",
            "amulet": "Amulet",
            "ring_1": "Ring 1",
            "ring_2": "Ring 2",
            "ring_3": "Ring 3",
            "trinket": "Trinket",
        }

    def _format_stat_name(self, stat_name):
        return str(stat_name).replace("_", " ").title()

    def _set_feedback(self, message):
        self.feedback_message = message
        self.feedback_until_ms = pygame.time.get_ticks() + 1800

    def _draw_wrapped_text(self, screen, text, x, y, max_width, font, color, bottom):
        for line in self._wrap_text(text, max_width, font, 5):
            if y + font.get_height() > bottom:
                break
            surface = font.render(line, True, color)
            screen.blit(surface, (x, y))
            y += surface.get_height() + 4
        return y

    def _wrap_text(self, text, max_width, font, max_lines):
        words = str(text).split()
        lines = []
        current = ""
        for word in words:
            candidate = f"{current} {word}".strip()
            if font.size(candidate)[0] <= max_width:
                current = candidate
                continue
            if current:
                lines.append(current)
            current = word
            if len(lines) >= max_lines:
                break
        if current and len(lines) < max_lines:
            lines.append(current)
        if len(lines) == max_lines and words:
            lines[-1] = self._shorten_text(lines[-1], max_width, font)
        return lines

    def _shorten_text(self, text, max_width, font):
        text = str(text)
        if font.size(text)[0] <= max_width:
            return text
        ellipsis = "..."
        while text and font.size(text + ellipsis)[0] > max_width:
            text = text[:-1]
        return text + ellipsis if text else ellipsis
