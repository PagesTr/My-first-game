import pygame

from systems.equipment import (
    CATEGORY_TO_SLOT,
    EQUIPMENT_SLOTS,
    RING_SLOTS,
    equip_item,
    unequip_item,
)
from systems.economy import calculate_item_sell_price
from systems.equipment_sets import load_equipment_sets, count_equipped_set_pieces
from systems.inventory import compact_inventory, use_consumable_item
from systems.stats import prepare_player_for_combat


class Button:
    def __init__(self, rect, text):
        self.rect = pygame.Rect(rect)
        self.text = text

    def draw(self, screen, font):
        pygame.draw.rect(screen, (70, 70, 70), self.rect)
        pygame.draw.rect(screen, (200, 200, 200), self.rect, 2)

        label = font.render(self.text, True, (255, 255, 255))
        screen.blit(label, (self.rect.x + 18, self.rect.y + 10))

    def is_clicked(self, pos):
        return self.rect.collidepoint(pos)


class InventoryScreen:
    def __init__(self, game):
        self.game = game
        self.title_font = pygame.font.Font(None, 46)
        self.font = pygame.font.Font(None, 24)
        self.small_font = pygame.font.Font(None, 20)
        self.back_btn = Button((50, 520, 140, 50), "Back")
        self.compact_btn = Button((210, 520, 140, 50), "Compact")
        self.show_advanced_stats = False
        self.stats_details_btn = Button((650, 430, 100, 40), "Details")
        self.selected_item = None
        self.selected_item_source = None
        self.selected_item_position = None
        self.last_click_time = 0
        self.last_click_source = None
        self.double_click_delay = 400
        self.start_x = 50
        self.start_y = 110
        self.slot_size = 70
        self.gap = 10
        self.columns = 6
        self.equipment_panel_x = 550
        self.equipment_panel_y = 135
        self.equipment_slot_width = 95
        self.equipment_slot_height = 43
        self.equipment_slot_gap = 5
        self.equipment_columns = 2
        self.equipment_sets = load_equipment_sets()

    def handle_event(self, event):
        if event.type == pygame.MOUSEBUTTONDOWN:
            if self.back_btn.is_clicked(event.pos):
                self.game.state = "town"
                return

            if not self.game.player:
                return

            if self.compact_btn.is_clicked(event.pos):
                compact_inventory(self.game.player["inventory"])
                self._clear_selected_item()
                return

            if self.stats_details_btn.is_clicked(event.pos):
                self.show_advanced_stats = not self.show_advanced_stats
                return

            item_instance, source = self._get_item_at_pos(event.pos)
            if item_instance is None:
                self._clear_selected_item()
                self.last_click_source = None
                return

            if self._is_double_click(source):
                self._handle_item_action(source)
                return

            self._select_item(item_instance, source, event.pos)

    def draw(self, screen):
        screen.fill((18, 24, 30))

        title = self.title_font.render("Inventory", True, (245, 245, 245))
        screen.blit(title, (50, 40))

        if not self.game.player:
            self.back_btn.draw(screen, self.font)
            return

        self._draw_gold_panel(screen)

        slots = self.game.player["inventory"]["slots"]

        for index, slot in enumerate(slots):
            col = index % self.columns
            row = index // self.columns
            rect = pygame.Rect(
                self.start_x + col * (self.slot_size + self.gap),
                self.start_y + row * (self.slot_size + self.gap),
                self.slot_size,
                self.slot_size,
            )
            pygame.draw.rect(screen, (45, 50, 58), rect)
            border_color = (120, 130, 140)
            if slot is not None and slot.get("kind") == "individual" and slot.get("rarity"):
                border_color = self._get_rarity_color(slot)
            pygame.draw.rect(screen, border_color, rect, 2)

            if slot is not None:
                self._draw_slot_content(screen, rect, slot)

        self._draw_equipment_panel(screen)
        self._draw_player_stats_panel(screen)
        self._draw_active_effects_panel(screen)
        if self.show_advanced_stats:
            self._draw_advanced_stats_panel(screen)
        self.back_btn.draw(screen, self.font)
        self.compact_btn.draw(screen, self.font)
        self._draw_item_tooltip(screen)

    def _get_slot_index_at_pos(self, pos):
        if not self.game.player:
            return None

        slots = self.game.player["inventory"]["slots"]
        for index in range(len(slots)):
            col = index % self.columns
            row = index // self.columns
            rect = pygame.Rect(
                self.start_x + col * (self.slot_size + self.gap),
                self.start_y + row * (self.slot_size + self.gap),
                self.slot_size,
                self.slot_size,
            )
            if rect.collidepoint(pos):
                return index

        return None

    def _get_equipment_slot_at_pos(self, pos):
        for slot_key in EQUIPMENT_SLOTS:
            if self._get_equipment_slot_rect(slot_key).collidepoint(pos):
                return slot_key
        return None

    def _get_equipment_slot_rect(self, slot_key):
        index = EQUIPMENT_SLOTS.index(slot_key)
        col = index % self.equipment_columns
        row = index // self.equipment_columns
        return pygame.Rect(
            self.equipment_panel_x
            + col * (self.equipment_slot_width + self.equipment_slot_gap),
            self.equipment_panel_y
            + row * (self.equipment_slot_height + self.equipment_slot_gap),
            self.equipment_slot_width,
            self.equipment_slot_height,
        )

    def _get_item_at_pos(self, pos):
        if not self.game.player:
            return None, None

        slot_index = self._get_slot_index_at_pos(pos)
        if slot_index is not None:
            item_instance = self.game.player["inventory"]["slots"][slot_index]
            if item_instance is not None:
                return item_instance, ("inventory", slot_index)
            return None, None

        equipment_slot = self._get_equipment_slot_at_pos(pos)
        if equipment_slot is not None:
            item_instance = self.game.player["equipment"].get(equipment_slot)
            if item_instance is not None:
                return item_instance, ("equipment", equipment_slot)

        return None, None

    def _select_item(self, item_instance, source, pos):
        self.selected_item = item_instance
        self.selected_item_source = source
        self.selected_item_position = (pos[0] + 14, pos[1] + 14)

    def _clear_selected_item(self):
        self.selected_item = None
        self.selected_item_source = None
        self.selected_item_position = None
        self.last_click_source = None

    def _is_double_click(self, source):
        current_time = pygame.time.get_ticks()
        is_double_click = (
            source == self.last_click_source
            and current_time - self.last_click_time <= self.double_click_delay
        )
        self.last_click_time = current_time
        self.last_click_source = source
        return is_double_click

    def _handle_item_action(self, source):
        source_type, source_key = source
        action_done = False

        if source_type == "inventory":
            inventory = self.game.player["inventory"]
            item_instance = inventory["slots"][source_key]
            if item_instance is None:
                self._clear_selected_item()
                return False

            item_data = self.game.data.items.get(item_instance.get("item"), {})
            if (
                item_instance.get("kind") == "stackable"
                and item_data.get("type") == "consumable"
            ):
                action_done = use_consumable_item(
                    self.game.player,
                    inventory,
                    source_key,
                    self.game.data.items,
                )
                if action_done:
                    prepare_player_for_combat(
                        self.game.player,
                        self.game.data.items,
                        self.game.data.classes,
                        self.game.data.skills,
                    )
            else:
                action_done = equip_item(
                    self.game.player,
                    inventory,
                    source_key,
                    self.game.data.items,
                )
                if action_done:
                    prepare_player_for_combat(
                        self.game.player,
                        self.game.data.items,
                        self.game.data.classes,
                        self.game.data.skills,
                    )
        elif source_type == "equipment":
            action_done = self._unequip_item(source_key)

        if action_done:
            self._clear_selected_item()

        return action_done

    def _get_hovered_item(self):
        if not self.game.player:
            return None

        mouse_pos = pygame.mouse.get_pos()
        slot_index = self._get_slot_index_at_pos(mouse_pos)
        if slot_index is not None:
            return self.game.player["inventory"]["slots"][slot_index]

        equipment_slot = self._get_equipment_slot_at_pos(mouse_pos)
        if equipment_slot is not None:
            return self.game.player["equipment"].get(equipment_slot)

        return None

    def _unequip_item(self, equipment_slot):
        unequipped = unequip_item(
            self.game.player,
            self.game.player["inventory"],
            equipment_slot,
        )
        if unequipped:
            prepare_player_for_combat(
                self.game.player,
                self.game.data.items,
                self.game.data.classes,
                self.game.data.skills,
            )
        return unequipped

    def _draw_gold_panel(self, screen):
        gold = self.game.player.get("gold", 0)
        gold_text = self.font.render(f"Gold: {gold}", True, (245, 220, 120))
        screen.blit(gold_text, (560, 70))

    def _draw_equipment_panel(self, screen):
        equipment = self.game.player["equipment"]
        labels = {
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

        title = self.font.render("Equipment", True, (245, 245, 245))
        screen.blit(title, (560, 110))
        set_counts = count_equipped_set_pieces(
            self.game.player,
            self.game.data.items,
        )

        for slot_key in EQUIPMENT_SLOTS:
            label = labels[slot_key]
            rect = self._get_equipment_slot_rect(slot_key)
            pygame.draw.rect(screen, (45, 50, 58), rect)
            item = equipment.get(slot_key)
            border_color = (120, 130, 140)
            set_id = self._get_item_set_id(item)
            if set_id:
                if set_counts.get(set_id, 0) >= 2:
                    border_color = (120, 220, 140)
                else:
                    border_color = (245, 220, 120)
            pygame.draw.rect(screen, border_color, rect, 2)

            label_text = self.small_font.render(label, True, (220, 220, 220))
            screen.blit(label_text, (rect.x + 5, rect.y + 4))

            if item is None:
                item_text = "Empty"
                name_color = (245, 245, 245)
            else:
                item_text = self._get_item_display_name(item)
                name_color = self._get_rarity_color(item)

            name_label = self.small_font.render(
                self._short_text(item_text, 11), True, name_color
            )
            screen.blit(name_label, (rect.x + 5, rect.y + 22))

    def _draw_player_stats_panel(self, screen):
        player = self.game.player
        stats = [
            ("Max HP", player.get("max_hp", 0)),
            ("Current HP", player.get("current_hp", 0)),
            ("Attack", player.get("attack", 0)),
            ("Defense", player.get("defense", 0)),
            ("Strength", player.get("strength", player.get("force", 0))),
            ("Dexterity", player.get("dexterity", player.get("agility", 0))),
            ("Intelligence", player.get("intelligence", 0)),
            ("Vitality", player.get("vitality", 0)),
            ("Wisdom", player.get("wisdom", 0)),
            ("Luck", player.get("luck", 0)),
        ]

        title = self.font.render("Stats", True, (245, 245, 245))
        screen.blit(title, (560, 440))
        self.stats_details_btn.draw(screen, self.small_font)

        start_x = 560
        start_y = 466
        column_width = 100
        line_height = 13
        rows_per_column = 10

        for index, (label, value) in enumerate(stats):
            col = index // rows_per_column
            row = index % rows_per_column
            stat_text = self.small_font.render(
                f"{label}: {value}", True, (220, 220, 220)
            )
            screen.blit(
                stat_text,
                (start_x + col * column_width, start_y + row * line_height),
            )

    def _draw_advanced_stats_panel(self, screen):
        player = self.game.player
        rect = pygame.Rect(180, 80, 440, 420)
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

        pygame.draw.rect(screen, (28, 34, 42), rect)
        pygame.draw.rect(screen, (180, 190, 200), rect, 2)

        title = self.font.render("Advanced Stats", True, (245, 245, 245))
        screen.blit(title, (rect.x + 16, rect.y + 14))

        start_x = rect.x + 18
        start_y = rect.y + 54
        column_width = 205
        line_height = 22
        rows_per_column = 7

        for index, (label, stat_key, value) in enumerate(stats):
            col = index // rows_per_column
            row = index % rows_per_column
            stat_text = self.small_font.render(
                f"{label}: {self._format_stat_value(stat_key, value)}",
                True,
                (220, 220, 220),
            )
            screen.blit(
                stat_text,
                (start_x + col * column_width, start_y + row * line_height),
            )

        hint = self.small_font.render(
            "Click Details again to close", True, (170, 175, 180)
        )
        screen.blit(hint, (rect.x + 16, rect.bottom - 32))

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
        if stat_key in percent_stats:
            return f"{value * 100:.1f}%"
        if stat_key == "crit_damage":
            return f"x{value}"
        return str(value)

    def _format_effect_modifier(self, stat, value):
        label = self._get_stat_label(stat)
        if value > 0:
            sign = "+"
        elif value < 0:
            sign = "-"
        else:
            sign = ""

        formatted_value = self._format_stat_value(stat, abs(value))
        return f"{sign}{formatted_value} {label}"

    def _draw_active_effects_panel(self, screen):
        player = self.game.player
        active_effects = player.get("active_effects", [])
        rect = pygame.Rect(360, 520, 180, 70)

        pygame.draw.rect(screen, (35, 40, 48), rect)
        pygame.draw.rect(screen, (120, 130, 140), rect, 2)

        title = self.small_font.render("Active Effects", True, (245, 245, 245))
        screen.blit(title, (rect.x + 8, rect.y + 6))

        valid_effects = [effect for effect in active_effects if isinstance(effect, dict)]
        if not valid_effects:
            none_text = self.small_font.render("None", True, (170, 175, 180))
            screen.blit(none_text, (rect.x + 8, rect.y + 28))
            return

        y = rect.y + 26
        for effect in valid_effects[:4]:
            name = effect.get("name", effect.get("id", "Unknown Effect"))
            duration_type = effect.get("duration_type")
            if duration_type == "combat":
                duration = f"{effect.get('remaining_combats', 0)} combat(s)"
            elif duration_type == "time":
                duration = f"{effect.get('remaining_seconds', 0)}s"
            else:
                duration = "Unknown duration"

            modifiers = effect.get("modifiers", {})
            modifier_text = ""
            if isinstance(modifiers, dict):
                for stat, value in modifiers.items():
                    if isinstance(value, (int, float)):
                        modifier_text = self._format_effect_modifier(stat, value)
                        break

            line = f"{self._short_text(name, 11)} {duration}"
            if modifier_text:
                line = f"{line} {modifier_text}"

            effect_text = self.small_font.render(
                self._short_text(line, 24), True, (220, 220, 220)
            )
            screen.blit(effect_text, (rect.x + 8, y))
            y += 14

    def _draw_comparison_panel(self, screen):
        source = self.selected_item_source
        if source is None:
            return

        source_type, source_key = source
        if source_type != "inventory":
            return

        inventory = self.game.player["inventory"]
        item = inventory["slots"][source_key]
        if item is None:
            return

        equipment_type = self._get_equipment_type(item)
        if equipment_type is None:
            return

        current_item = self._get_comparison_item_for_equipment_type(equipment_type)
        comparison_lines = self._build_stats_comparison(
            item.get("stats", {}),
            current_item.get("stats", {}) if current_item else {},
        )

        rect = pygame.Rect(215, 430, 325, 160)
        pygame.draw.rect(screen, (35, 40, 48), rect)
        pygame.draw.rect(screen, (120, 130, 140), rect, 2)

        title = self.font.render("Comparison", True, (245, 245, 245))
        screen.blit(title, (rect.x + 10, rect.y + 8))

        item_text = self.small_font.render(
            f"Item: {self._short_text(self._get_item_display_name(item), 22)}",
            True,
            self._get_rarity_color(item),
        )
        equipped_text = self.small_font.render(
            f"Equipped: {self._short_text(self._get_item_display_name(current_item), 20)}",
            True,
            self._get_rarity_color(current_item),
        )
        screen.blit(item_text, (rect.x + 10, rect.y + 32))
        screen.blit(equipped_text, (rect.x + 10, rect.y + 50))

        y = rect.y + 76
        for label, new_value, current_value, diff in comparison_lines[:5]:
            stat_key = self._get_stat_key_from_label(label)
            if diff > 0:
                color = (120, 220, 140)
            elif diff < 0:
                color = (230, 110, 110)
            else:
                color = (170, 170, 170)

            diff_text = self._format_stat_difference(stat_key, diff)
            line = f"{label}: {new_value} vs {current_value} ({diff_text})"
            stat_text = self.small_font.render(line, True, color)
            screen.blit(stat_text, (rect.x + 10, y))
            y += 18

    def _get_tooltip_lines(self, item_instance):
        return [text for text, _ in self._get_tooltip_entries(item_instance)]

    def _get_tooltip_entries(self, item_instance, current_item=None):
        item_data = self._get_item_data(item_instance)
        item_type = item_data.get("type", "unknown")
        stats = item_instance.get("stats") or item_data.get("stats", {})

        entries = [
            (self._get_item_display_name(item_instance), "title"),
            (f"Type: {self._get_type_label(item_type)}", "normal"),
        ]

        rarity = item_instance.get("rarity")
        if rarity:
            entries.append((f"Rarity: {rarity.capitalize()}", "rarity"))

        quantity = item_instance.get("quantity")
        if quantity is not None:
            entries.append((f"Quantity: {quantity}", "normal"))

        sell_price = calculate_item_sell_price(item_instance, item_data)
        if sell_price > 0:
            entries.append((f"Sell price: {sell_price} gold", "normal"))
        else:
            entries.append(("Sell price: -", "normal"))

        if stats:
            entries.append(("Stats:", "section"))
            for stat, value in stats.items():
                label = self._get_stat_label(stat)
                formatted_value = self._format_stat_value(stat, value)
                entries.append((f"{label}: {formatted_value}", "normal"))
        else:
            entries.append(("No stats", "normal"))

        entries.extend(self._get_comparison_tooltip_entries(item_instance, current_item))
        entries.extend(self._get_set_tooltip_entries(item_instance))
        return entries

    def _get_item_data(self, item_instance):
        if not isinstance(item_instance, dict):
            return {}

        item_id = item_instance.get("item")
        item_data = self.game.data.items.get(item_id, {})
        if not isinstance(item_data, dict):
            return {}
        return item_data

    def _get_item_set_id(self, item_instance):
        return self._get_item_data(item_instance).get("set_id")

    def _get_set_data(self, set_id):
        set_data = self.equipment_sets.get(set_id, {})
        if not isinstance(set_data, dict):
            return {}
        return set_data

    def _get_set_piece_ids(self, set_id):
        piece_ids = []
        for item_id, item_data in self.game.data.items.items():
            if not isinstance(item_data, dict):
                continue
            if item_data.get("set_id") == set_id:
                piece_ids.append(item_id)
        return piece_ids

    def _get_equipped_set_piece_ids(self, set_id):
        equipped_piece_ids = set()
        equipment = self.game.player.get("equipment", {})
        if not isinstance(equipment, dict):
            return equipped_piece_ids

        for item_instance in equipment.values():
            if not isinstance(item_instance, dict):
                continue

            item_id = item_instance.get("item")
            item_data = self.game.data.items.get(item_id, {})
            if not isinstance(item_data, dict):
                continue
            if item_data.get("set_id") == set_id:
                equipped_piece_ids.add(item_id)

        return equipped_piece_ids

    def _get_set_progress(self, set_id):
        piece_ids = self._get_set_piece_ids(set_id)
        equipped_piece_ids = self._get_equipped_set_piece_ids(set_id)
        return {
            "piece_ids": piece_ids,
            "equipped_piece_ids": equipped_piece_ids,
            "equipped_count": len(equipped_piece_ids),
            "total_count": len(piece_ids),
        }

    def _format_set_bonus_line(self, threshold, bonuses):
        bonus_parts = []
        if not isinstance(bonuses, dict):
            bonuses = {}

        for stat, value in bonuses.items():
            if not isinstance(value, (int, float)):
                continue

            label = self._get_stat_label(stat)
            sign = "+" if value > 0 else ""
            formatted_value = self._format_stat_value(stat, value)
            bonus_parts.append(f"{sign}{formatted_value} {label}")

        bonus_text = ", ".join(bonus_parts) if bonus_parts else "No bonus"
        return f"{threshold} pieces: {bonus_text}"

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

    def _get_stat_key_from_label(self, label):
        for stat_key in self._get_known_stat_labels():
            if self._get_stat_label(stat_key) == label:
                return stat_key
        return label

    def _get_known_stat_labels(self):
        return {
            "attack",
            "defense",
            "hp",
            "max_hp",
            "force",
            "agility",
            "intelligence",
            "magic_attack",
            "magic_defense",
            "accuracy",
            "dodge_chance",
            "block_chance",
            "crit_chance",
            "crit_damage",
            "initiative",
            "healing_power",
            "status_resistance",
            "loot_bonus",
            "gold_bonus",
            "rare_find_bonus",
            "xp_bonus",
        }

    def _get_item_stats(self, item_instance):
        item_data = self._get_item_data(item_instance)
        stats = item_instance.get("stats") if isinstance(item_instance, dict) else None
        if stats is None:
            stats = item_data.get("stats", {})
        if not isinstance(stats, dict):
            return {}
        return stats

    def _get_comparison_tooltip_entries(self, item_instance, current_item):
        if current_item is None:
            return []

        new_stats = self._get_item_stats(item_instance)
        current_stats = self._get_item_stats(current_item)
        stat_keys = sorted(set(new_stats) | set(current_stats), key=self._get_stat_label)
        if not stat_keys:
            return []

        comparison_entries = []

        for stat_key in stat_keys:
            new_value = new_stats.get(stat_key, 0)
            current_value = current_stats.get(stat_key, 0)
            if not isinstance(new_value, (int, float)):
                continue
            if not isinstance(current_value, (int, float)):
                continue

            diff = new_value - current_value
            if diff > 0:
                role = "comparison_positive"
            elif diff < 0:
                role = "comparison_negative"
            else:
                role = "comparison_neutral"

            label = self._get_stat_label(stat_key)
            new_text = self._format_stat_value(stat_key, new_value)
            current_text = self._format_stat_value(stat_key, current_value)
            diff_text = self._format_stat_difference(stat_key, diff)
            comparison_entries.append(
                (
                    f"{label}: {new_text} vs {current_text} ({diff_text})",
                    role,
                )
            )
            if len(comparison_entries) >= 6:
                break

        if not comparison_entries:
            return []

        return [
            ("", "normal"),
            ("Comparison:", "section"),
            (
                f"Compared with: {self._get_item_display_name(current_item)}",
                "normal",
            ),
            *comparison_entries,
        ]

    def _get_set_tooltip_entries(self, item_instance):
        set_id = self._get_item_set_id(item_instance)
        if not set_id:
            return []

        set_data = self._get_set_data(set_id)
        progress = self._get_set_progress(set_id)
        set_name = set_data.get("name", str(set_id))
        equipped_count = progress["equipped_count"]
        total_count = progress["total_count"]
        equipped_piece_ids = progress["equipped_piece_ids"]

        entries = [
            ("", "normal"),
            (f"Set: {set_name} ({equipped_count}/{total_count})", "set_title"),
            ("Pieces:", "section"),
        ]

        for piece_id in progress["piece_ids"]:
            piece_data = self.game.data.items.get(piece_id, {})
            if isinstance(piece_data, dict):
                piece_name = piece_data.get("name", piece_id)
            else:
                piece_name = piece_id
            is_equipped = piece_id in equipped_piece_ids
            marker = "✓" if is_equipped else "✗"
            role = "active" if is_equipped else "inactive"
            entries.append((f"{marker} {piece_name}", role))

        bonuses = set_data.get("bonuses", {})
        if not isinstance(bonuses, dict):
            bonuses = {}

        if bonuses:
            entries.append(("Bonuses:", "section"))

        sorted_bonus_entries = []
        for threshold_key, threshold_bonuses in bonuses.items():
            try:
                threshold = int(threshold_key)
            except (TypeError, ValueError):
                continue
            sorted_bonus_entries.append((threshold, threshold_bonuses))

        for threshold, threshold_bonuses in sorted(sorted_bonus_entries):
            marker = "✓" if equipped_count >= threshold else "✗"
            role = "active" if equipped_count >= threshold else "inactive"
            line = self._format_set_bonus_line(threshold, threshold_bonuses)
            entries.append((f"{marker} {line}", role))

        return entries

    def _get_type_label(self, item_type):
        labels = {
            "equipment": "Equipment",
            "consumable": "Consumable",
            "resource": "Resource",
            "currency": "Currency",
            "quest": "Quest",
        }
        if not item_type:
            return "Unknown"
        return labels.get(item_type, str(item_type).capitalize())

    def _get_selected_comparison_item(self, item_instance):
        return self._get_comparison_item_for_source(
            item_instance,
            self.selected_item_source,
        )

    def _get_comparison_item_for_source(self, item_instance, source):
        if source is None:
            return None

        source_type, _ = source
        if source_type != "inventory":
            return None

        equipment_type = self._get_equipment_type(item_instance)
        if equipment_type is None:
            return None

        return self._get_comparison_item_for_equipment_type(equipment_type)

    def _get_comparison_item_for_equipment_type(self, equipment_type):
        equipment = self.game.player["equipment"]
        if equipment_type != "ring":
            return equipment.get(equipment_type)

        for ring_slot in RING_SLOTS:
            if equipment.get(ring_slot) is None:
                return None
        return equipment.get(RING_SLOTS[0])

    def _get_tooltip_stat_line_indexes(self, lines):
        stat_line_indexes = {}
        in_stats_section = False

        for index, line_entry in enumerate(lines):
            if isinstance(line_entry, tuple):
                line, role = line_entry
            else:
                line = line_entry
                role = "normal"

            if line == "Stats:":
                in_stats_section = True
                continue
            if in_stats_section and role in {"section", "set_title"}:
                break
            if not in_stats_section or role != "normal" or ":" not in line:
                continue

            stat_label = line.split(":", 1)[0]
            stat_line_indexes[stat_label] = index

        return stat_line_indexes

    def _build_comparison_values(self, item_instance, current_item):
        item_id = item_instance.get("item")
        current_item_id = current_item.get("item")
        item_data = self.game.data.items.get(item_id, {})
        current_item_data = self.game.data.items.get(current_item_id, {})
        new_stats = item_instance.get("stats") or item_data.get("stats", {})
        current_stats = current_item.get("stats") or current_item_data.get("stats", {})
        comparison_values = {}

        for stat, new_value in new_stats.items():
            current_value = current_stats.get(stat, 0)
            diff = new_value - current_value
            label = self._get_stat_label(stat)
            comparison_values[label] = self._format_stat_difference(stat, diff)

        return comparison_values

    def _draw_item_tooltip(self, screen):
        mouse_pos = pygame.mouse.get_pos()
        item_instance, source = self._get_item_at_pos(mouse_pos)
        if item_instance is None or source is None:
            return

        current_item = self._get_comparison_item_for_source(item_instance, source)
        entries = self._get_tooltip_entries(item_instance, current_item)
        tooltip_colors = {
            "normal": (220, 220, 220),
            "section": (220, 220, 160),
            "set_title": (245, 220, 120),
            "active": (120, 220, 140),
            "inactive": (150, 155, 160),
            "comparison_positive": (120, 220, 140),
            "comparison_negative": (230, 110, 110),
            "comparison_neutral": (170, 170, 170),
            "rarity": self._get_rarity_color(item_instance),
            "title": self._get_rarity_color(item_instance),
        }
        left_rendered_lines = [
            self.small_font.render(
                text,
                True,
                tooltip_colors.get(role, (220, 220, 220)),
            )
            for text, role in entries
        ]
        if not left_rendered_lines:
            return

        padding = 10
        line_height = 18
        left_width = max(line.get_width() for line in left_rendered_lines)
        width = left_width + padding * 2

        height = len(left_rendered_lines) * line_height + padding * 2
        x, y = mouse_pos[0] + 14, mouse_pos[1] + 14

        if x + width > screen.get_width():
            x = max(0, screen.get_width() - width - 6)
        if y + height > screen.get_height():
            y = max(0, screen.get_height() - height - 6)

        rect = pygame.Rect(x, y, width, height)
        pygame.draw.rect(screen, (28, 34, 42), rect)
        pygame.draw.rect(screen, (180, 190, 200), rect, 2)

        for index, (line, role) in enumerate(entries):
            color = tooltip_colors.get(role, (220, 220, 220))
            text = self.small_font.render(line, True, color)
            screen.blit(text, (rect.x + padding, rect.y + padding + index * line_height))

    def _get_equipment_type(self, item_instance):
        if item_instance is None:
            return None
        if item_instance.get("kind") != "individual":
            return None

        item_id = item_instance["item"]
        item_data = self.game.data.items.get(item_id, {})
        item_type = item_data.get("type")
        item_category = item_data.get("category") if item_type == "equipment" else item_type
        if item_category == "ring":
            return "ring"
        if item_category in CATEGORY_TO_SLOT:
            return CATEGORY_TO_SLOT[item_category]
        return None

    def _get_item_name(self, item_instance):
        if item_instance is None:
            return "None"
        item_id = item_instance["item"]
        item_data = self.game.data.items.get(item_id, {})
        return item_data.get("name", item_id)

    def _get_rarity_label(self, item_instance):
        if item_instance is None:
            return ""
        rarity = item_instance.get("rarity")
        if not rarity:
            return ""
        return rarity.capitalize()

    def _get_rarity_color(self, item_instance):
        if item_instance is None:
            return (245, 245, 245)
        colors = {
            "common": (170, 170, 170),
            "uncommon": (100, 220, 120),
            "rare": (100, 160, 255),
            "epic": (180, 120, 255),
            "legendary": (255, 200, 80),
            "unique": (240, 90, 90),
        }
        return colors.get(item_instance.get("rarity"), (245, 245, 245))

    def _get_item_display_name(self, item_instance):
        if item_instance is None:
            return "None"
        item_name = self._get_item_name(item_instance)
        rarity = self._get_rarity_label(item_instance)
        if rarity:
            return f"[{rarity}] {item_name}"
        return item_name

    def _get_stat_label(self, stat):
        labels = {
            "attack": "Attack",
            "defense": "Defense",
            "hp": "HP",
            "max_hp": "Max HP",
            "force": "Strength",
            "agility": "Agility",
            "intelligence": "Intelligence",
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
        return labels.get(stat, stat)

    def _build_stats_comparison(self, new_stats, current_stats):
        comparison = []
        stat_names = sorted(set(new_stats) | set(current_stats))
        for stat in stat_names:
            new_value = new_stats.get(stat, 0)
            current_value = current_stats.get(stat, 0)
            diff = new_value - current_value
            comparison.append(
                (self._get_stat_label(stat), new_value, current_value, diff)
            )
        return comparison

    def _draw_slot_content(self, screen, rect, slot):
        item_id = slot["item"]
        item_data = self.game.data.items.get(item_id, {})

        if slot.get("kind") == "stackable":
            item_name = item_data.get("name", item_id)
            quantity = slot.get("quantity")
            detail_text = f"x{quantity}" if quantity is not None else ""
            item_color = (245, 245, 245)
        elif slot.get("kind") == "individual":
            item_name = self._get_item_display_name(slot)
            detail_text = self._format_short_stats(slot.get("stats", {}))
            item_color = self._get_rarity_color(slot)
        else:
            item_name = item_data.get("name", item_id)
            detail_text = ""
            item_color = (245, 245, 245)

        item_label = self.small_font.render(
            self._short_text(item_name), True, item_color
        )
        screen.blit(item_label, (rect.x + 6, rect.y + 10))

        if detail_text:
            detail_label = self.small_font.render(
                self._short_text(detail_text), True, (220, 220, 160)
            )
            screen.blit(detail_label, (rect.x + 6, rect.y + 42))

    def _format_short_stats(self, stats):
        for stat, value in stats.items():
            return f"{self._get_stat_label(stat)} +{value}"
        return ""

    def _short_text(self, text, max_length=10):
        text = str(text)
        if len(text) <= max_length:
            return text
        return text[: max_length - 1] + "."
