import pygame

from systems.equipment import equip_item, unequip_item
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

            equipment_slot = self._get_equipment_slot_at_pos(event.pos)
            if equipment_slot is not None:
                self._unequip_item(equipment_slot)
                return

            slot_index = self._get_slot_index_at_pos(event.pos)
            if slot_index is None:
                return

            inventory = self.game.player["inventory"]
            if inventory["slots"][slot_index] is None:
                return

            equipped = equip_item(
                self.game.player,
                inventory,
                slot_index,
                self.game.data.items,
            )
            if equipped:
                prepare_player_for_combat(
                    self.game.player,
                    self.game.data.items,
                    self.game.data.classes,
                )

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
        self._draw_comparison_panel(screen)
        self.back_btn.draw(screen, self.font)

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
            ("Strength", player.get("force", 0)),
            ("Agility", player.get("agility", 0)),
            ("Intelligence", player.get("intelligence", 0)),
        ]

        title = self.font.render("Stats", True, (245, 245, 245))
        screen.blit(title, (560, 440))

        y = 468
        for label, value in stats:
            stat_text = self.small_font.render(
                f"{label}: {value}", True, (220, 220, 220)
            )
            screen.blit(stat_text, (560, y))
            y += 16

    def _draw_comparison_panel(self, screen):
        mouse_pos = pygame.mouse.get_pos()
        slot_index = self._get_slot_index_at_pos(mouse_pos)
        if slot_index is None:
            return

        inventory = self.game.player["inventory"]
        item = inventory["slots"][slot_index]
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
