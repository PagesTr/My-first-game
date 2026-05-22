import pygame

from systems.equipment import EQUIPMENT_SLOTS, can_equip_item, equip_item, unequip_item
from systems.inventory import compact_inventory, use_consumable_item
from systems.stats import prepare_player_for_combat


class InventoryOverlay:
    def __init__(self, game):
        self.game = game
        self.opened = False
        self.title_font = pygame.font.Font(None, 34)
        self.body_font = pygame.font.Font(None, 23)
        self.small_font = pygame.font.Font(None, 19)
        self.close_rect = pygame.Rect(0, 0, 0, 0)
        self.compact_rect = pygame.Rect(0, 0, 0, 0)
        self.slot_rects = []
        self.equipment_rects = {}
        self.action_rects = {}
        self.filter_rects = {}
        self.active_filter = "all"
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

        inventory_rect = pygame.Rect(panel.x + 20, panel.y + 104, 372, panel.height - 128)
        equipment_rect = pygame.Rect(panel.x + 410, panel.y + 76, panel.right - panel.x - 430, 210)
        details_rect = pygame.Rect(panel.x + 410, panel.y + 304, panel.right - panel.x - 430, panel.bottom - panel.y - 328)

        self._draw_filter_row(screen, pygame.Rect(panel.x + 20, panel.y + 76, 372, 24))
        self._draw_inventory_grid(screen, inventory_rect)
        self._draw_equipment_panel(screen, equipment_rect)
        self._draw_details_panel(screen, details_rect)

    def _handle_click(self, position):
        if self.close_rect.collidepoint(position):
            self.close()
            return

        if self.compact_rect.collidepoint(position):
            self._compact_inventory()
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
        self._draw_item_icon(screen, icon_rect, slot, item_data)

        quantity = slot.get("quantity")
        if quantity is not None:
            quantity_surface = self.small_font.render(str(quantity), True, (255, 236, 170))
            quantity_rect = quantity_surface.get_rect(bottomright=(rect.right - 4, rect.bottom - 2))
            screen.blit(quantity_surface, quantity_rect)

        item_name = self._get_item_display_name(slot, item_data)
        label = self._shorten_text(item_name, rect.width - 4, self.small_font)
        label_surface = self.small_font.render(label, True, (230, 217, 190))
        screen.blit(label_surface, label_surface.get_rect(midbottom=(rect.centerx, rect.bottom - 3)))

    def _draw_item_icon(self, screen, rect, item, item_data):
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

    def _draw_equipment_panel(self, screen, area):
        title = self.body_font.render("Equipment", True, (238, 226, 194))
        screen.blit(title, (area.x, area.y - 24))

        equipment = self._get_equipment()
        self.equipment_rects = {}
        slot_width = max(94, (area.width - 8) // 2)
        slot_height = 33
        labels = self._equipment_labels()

        for index, slot_key in enumerate(EQUIPMENT_SLOTS):
            column = index % 2
            row = index // 2
            rect = pygame.Rect(
                area.x + column * (slot_width + 8),
                area.y + row * (slot_height + 7),
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
            screen.blit(label_surface, (rect.x + 5, rect.y + 3))
            item_surface = self.small_font.render(self._shorten_text(item_label, rect.width - 10, self.small_font), True, border_color if item else (130, 119, 101))
            screen.blit(item_surface, (rect.x + 5, rect.y + 17))

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

        name_surface = self.body_font.render(self._shorten_text(name, rect.width - 20, self.body_font), True, self._get_rarity_color(item, item_data))
        screen.blit(name_surface, (rect.x + 10, y))
        y += 25

        detail_lines = [
            f"ID: {item.get('item', '-')}",
            f"Kind: {item.get('kind', '-')}",
            f"Type: {item_data.get('type', '-')}",
            f"Rarity: {str(rarity).capitalize()}",
        ]
        quantity = item.get("quantity")
        if quantity is not None:
            detail_lines.append(f"Quantity: {quantity}")
        level = item.get("level") or item_data.get("level")
        if level is not None:
            detail_lines.append(f"Level: {level}")

        for line in detail_lines:
            surface = self.small_font.render(self._shorten_text(line, rect.width - 20, self.small_font), True, (210, 198, 174))
            screen.blit(surface, (rect.x + 10, y))
            y += 18

        stats = item.get("stats") or item_data.get("stats")
        if isinstance(stats, dict) and stats:
            y += 2
            stats_label = self.small_font.render("Stats", True, (238, 226, 194))
            screen.blit(stats_label, (rect.x + 10, y))
            y += 17
            for stat_name, value in list(stats.items())[:4]:
                stat_text = self.small_font.render(f"{self._format_stat_name(stat_name)}: {value}", True, (190, 215, 184))
                screen.blit(stat_text, (rect.x + 16, y))
                y += 16

        description = item_data.get("description")
        if description and y < rect.bottom - 72:
            y += 4
            y = self._draw_wrapped_text(screen, description, rect.x + 10, y, rect.width - 20, self.small_font, (191, 181, 158), rect.bottom - 50)

        self._draw_action_buttons(screen, rect)

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

    def _get_player_gold(self):
        player = getattr(self.game, "player", {})
        if isinstance(player, dict):
            return player.get("gold", 0)
        return 0

    def _get_items_data(self):
        data = getattr(self.game, "data", None)
        items = getattr(data, "items", {}) if data is not None else {}
        return items if isinstance(items, dict) else {}

    def _get_item_data(self, item):
        if item is None:
            return {}
        return self._get_items_data().get(item.get("item"), {})

    def _get_item_display_name(self, item, item_data):
        if item is None:
            return ""
        item_id = item.get("item", "")
        return item_data.get("name") or item_id

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
