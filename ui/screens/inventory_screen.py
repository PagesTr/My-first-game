import pygame

from systems.equipment import equip_item, unequip_item
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

    def handle_event(self, event):
        if event.type == pygame.MOUSEBUTTONDOWN:
            if self.back_btn.is_clicked(event.pos):
                self.game.state = "zone_select"
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
            if slot is not None and slot.get("kind") == "unique" and slot.get("rarity"):
                border_color = self._get_rarity_color(slot)
            pygame.draw.rect(screen, border_color, rect, 2)

            if slot is not None:
                self._draw_slot_content(screen, rect, slot)

        self._draw_equipment_panel(screen)
        self._draw_player_stats_panel(screen)
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
        for slot_key in ("weapon", "armor", "accessory"):
            if self._get_equipment_slot_rect(slot_key).collidepoint(pos):
                return slot_key
        return None

    def _get_equipment_slot_rect(self, slot_key):
        slot_order = ("weapon", "armor", "accessory")
        index = slot_order.index(slot_key)
        return pygame.Rect(550, 150 + index * 95, 200, 80)

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
            )
        return unequipped

    def _draw_equipment_panel(self, screen):
        equipment = self.game.player["equipment"]
        labels = {
            "weapon": "Weapon",
            "armor": "Armor",
            "accessory": "Accessory",
        }

        title = self.font.render("Equipment", True, (245, 245, 245))
        screen.blit(title, (560, 110))

        y = 150
        for slot_key, label in labels.items():
            rect = self._get_equipment_slot_rect(slot_key)
            pygame.draw.rect(screen, (45, 50, 58), rect)
            pygame.draw.rect(screen, (120, 130, 140), rect, 2)

            label_text = self.small_font.render(label, True, (220, 220, 220))
            screen.blit(label_text, (rect.x + 8, rect.y + 8))

            item = equipment.get(slot_key)
            if item is None:
                item_text = "Empty"
                detail_text = ""
                name_color = (245, 245, 245)
            else:
                item_text = self._get_item_display_name(item)
                detail_text = self._format_short_stats(item.get("stats", {}))
                name_color = self._get_rarity_color(item)

            name_label = self.small_font.render(
                self._short_text(item_text, 18), True, name_color
            )
            screen.blit(name_label, (rect.x + 8, rect.y + 32))

            if detail_text:
                detail_label = self.small_font.render(
                    self._short_text(detail_text, 18), True, (220, 220, 160)
                )
                screen.blit(detail_label, (rect.x + 8, rect.y + 54))

            y += 95

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

        current_item = self.game.player["equipment"].get(equipment_type)
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
            if diff > 0:
                diff_text = f"+{diff}"
                color = (120, 220, 140)
            elif diff < 0:
                diff_text = str(diff)
                color = (230, 110, 110)
            else:
                diff_text = "="
                color = (170, 170, 170)

            line = f"{label}: {new_value} vs {current_value} ({diff_text})"
            stat_text = self.small_font.render(line, True, color)
            screen.blit(stat_text, (rect.x + 10, y))
            y += 18

    def _get_tooltip_lines(self, item_instance):
        item_id = item_instance.get("item")
        item_data = self.game.data.items.get(item_id, {})
        item_type = item_data.get("type", "unknown")
        item_kind = item_instance.get("kind", "unknown")
        stats = item_instance.get("stats") or item_data.get("stats", {})

        lines = [
            self._get_item_display_name(item_instance),
            f"Type: {item_type}",
            f"Kind: {item_kind}",
        ]

        rarity = item_instance.get("rarity")
        if rarity:
            lines.append(f"Rarity: {rarity.capitalize()}")

        quantity = item_instance.get("quantity")
        if quantity is not None:
            lines.append(f"Quantity: {quantity}")

        if stats:
            lines.append("Stats:")
            for stat, value in stats.items():
                label = self._get_stat_label(stat)
                formatted_value = self._format_stat_value(stat, value)
                lines.append(f"{label}: {formatted_value}")
        else:
            lines.append("No stats")

        return lines

    def _get_selected_comparison_item(self, item_instance):
        source = self.selected_item_source
        if source is None:
            return None

        source_type, _ = source
        if source_type != "inventory":
            return None

        equipment_type = self._get_equipment_type(item_instance)
        if equipment_type is None:
            return None

        return self.game.player["equipment"].get(equipment_type)

    def _get_tooltip_stat_line_indexes(self, lines):
        stat_line_indexes = {}
        in_stats_section = False

        for index, line in enumerate(lines):
            if line == "Stats:":
                in_stats_section = True
                continue
            if not in_stats_section or ":" not in line:
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
            if stat == "crit_damage":
                formatted_diff = str(abs(diff))
            else:
                formatted_diff = self._format_stat_value(stat, abs(diff))

            if diff > 0:
                comparison_values[label] = f"+{formatted_diff}"
            elif diff < 0:
                comparison_values[label] = f"-{formatted_diff}"
            else:
                comparison_values[label] = "="

        return comparison_values

    def _draw_item_tooltip(self, screen):
        item_instance = self.selected_item
        source = self.selected_item_source
        if item_instance is None or source is None or self.selected_item_position is None:
            return

        source_type, source_key = source
        if source_type == "inventory":
            item_instance = self.game.player["inventory"]["slots"][source_key]
        elif source_type == "equipment":
            item_instance = self.game.player["equipment"].get(source_key)

        if item_instance is None:
            self._clear_selected_item()
            return

        self.selected_item = item_instance
        lines = self._get_tooltip_lines(item_instance)
        left_rendered_lines = [
            self.small_font.render(line, True, (220, 220, 220))
            for line in lines
        ]
        if not left_rendered_lines:
            return

        padding = 10
        line_height = 18
        column_gap = 28
        current_item = self._get_selected_comparison_item(item_instance)
        comparison_values = {}
        stat_line_indexes = {}
        right_header_lines = []
        right_width = 0

        if current_item is not None:
            comparison_values = self._build_comparison_values(item_instance, current_item)
            stat_line_indexes = self._get_tooltip_stat_line_indexes(lines)
            right_header_lines = [
                "Compared to equipped",
                self._get_item_display_name(current_item),
            ]
            right_texts = right_header_lines + list(comparison_values.values())
            right_width = max(
                self.small_font.render(text, True, (220, 220, 220)).get_width()
                for text in right_texts
            )

        left_width = max(line.get_width() for line in left_rendered_lines)
        width = left_width + padding * 2
        if current_item is not None:
            width += column_gap + right_width

        height = len(left_rendered_lines) * line_height + padding * 2
        x, y = self.selected_item_position

        if x + width > screen.get_width():
            x = max(0, screen.get_width() - width - 6)
        if y + height > screen.get_height():
            y = max(0, screen.get_height() - height - 6)

        rect = pygame.Rect(x, y, width, height)
        pygame.draw.rect(screen, (28, 34, 42), rect)
        pygame.draw.rect(screen, (180, 190, 200), rect, 2)

        for index, line in enumerate(lines):
            color = (220, 220, 220)
            if index == 0:
                color = self._get_rarity_color(item_instance)
            elif line == "Stats:":
                color = (220, 220, 160)

            text = self.small_font.render(line, True, color)
            screen.blit(text, (rect.x + padding, rect.y + padding + index * line_height))

        if current_item is None:
            return

        right_x = rect.x + padding + left_width + column_gap
        for index, line in enumerate(right_header_lines):
            color = (220, 220, 220)
            if index == 1:
                color = self._get_rarity_color(current_item)
            text = self.small_font.render(line, True, color)
            screen.blit(text, (right_x, rect.y + padding + index * line_height))

        for stat_label, diff_text in comparison_values.items():
            line_index = stat_line_indexes.get(stat_label)
            if line_index is None:
                continue

            if diff_text.startswith("+"):
                color = (120, 220, 140)
            elif diff_text.startswith("-"):
                color = (230, 110, 110)
            else:
                color = (170, 170, 170)

            text = self.small_font.render(diff_text, True, color)
            screen.blit(text, (right_x, rect.y + padding + line_index * line_height))

    def _get_equipment_type(self, item_instance):
        if item_instance is None:
            return None
        if item_instance.get("kind") != "unique":
            return None

        item_id = item_instance["item"]
        item_data = self.game.data.items.get(item_id, {})
        item_type = item_data.get("type")
        if item_type in ("weapon", "armor", "accessory"):
            return item_type
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
        elif slot.get("kind") == "unique":
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
