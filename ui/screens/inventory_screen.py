import pygame

from systems.equipment import equip_item
from systems.inventory import find_first_empty_slot
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
        self.back_btn = Button((50, 520, 140, 50), "Retour")
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

        title = self.title_font.render("Inventaire", True, (245, 245, 245))
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
            pygame.draw.rect(screen, (120, 130, 140), rect, 2)

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
        player = self.game.player
        item = player["equipment"].get(equipment_slot)
        if item is None:
            return False

        inventory = player["inventory"]
        empty_slot = find_first_empty_slot(inventory)
        if empty_slot is None:
            return False

        inventory["slots"][empty_slot] = item
        player["equipment"][equipment_slot] = None
        prepare_player_for_combat(
            player,
            self.game.data.items,
            self.game.data.classes,
        )
        return True

    def _draw_equipment_panel(self, screen):
        equipment = self.game.player["equipment"]
        labels = {
            "weapon": "Arme",
            "armor": "Armure",
            "accessory": "Accessoire",
        }

        title = self.font.render("Équipement", True, (245, 245, 245))
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
                item_text = "Vide"
                detail_text = ""
            else:
                item_id = item["item"]
                item_data = self.game.data.items.get(item_id, {})
                item_text = item_data.get("name", item_id)
                detail_text = self._format_short_stats(item.get("stats", {}))

            name_label = self.small_font.render(
                self._short_text(item_text, 18), True, (245, 245, 245)
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
            ("PV max", player.get("max_hp", 0)),
            ("PV actuels", player.get("current_hp", 0)),
            ("Attaque", player.get("attack", 0)),
            ("Défense", player.get("defense", 0)),
            ("Force", player.get("force", 0)),
            ("Agilité", player.get("agility", 0)),
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
        comparison_lines = self._format_stats_comparison(
            item.get("stats", {}),
            current_item.get("stats", {}) if current_item else {},
        )

        rect = pygame.Rect(220, 510, 320, 80)
        pygame.draw.rect(screen, (35, 40, 48), rect)
        pygame.draw.rect(screen, (120, 130, 140), rect, 2)

        title = self.font.render("Comparaison", True, (245, 245, 245))
        screen.blit(title, (rect.x + 10, rect.y + 8))

        item_text = self.small_font.render(
            f"Objet : {self._short_text(self._get_item_name(item), 22)}",
            True,
            (220, 220, 220),
        )
        equipped_text = self.small_font.render(
            f"Équipé : {self._short_text(self._get_item_name(current_item), 20)}",
            True,
            (220, 220, 220),
        )
        screen.blit(item_text, (rect.x + 10, rect.y + 32))
        screen.blit(equipped_text, (rect.x + 10, rect.y + 50))

        x = rect.x + 180
        y = rect.y + 32
        for line in comparison_lines[:2]:
            stat_text = self.small_font.render(line, True, (220, 220, 160))
            screen.blit(stat_text, (x, y))
            y += 18

    def _get_equipment_type(self, item_instance):
        item_id = item_instance["item"]
        item_data = self.game.data.items.get(item_id, {})
        item_type = item_data.get("type")
        if item_type in ("weapon", "armor", "accessory"):
            return item_type
        return None

    def _format_stats_comparison(self, new_stats, current_stats):
        lines = []
        stat_names = sorted(set(new_stats) | set(current_stats))
        for stat in stat_names:
            diff = new_stats.get(stat, 0) - current_stats.get(stat, 0)
            if diff > 0:
                lines.append(f"{stat}: +{diff}")
            elif diff < 0:
                lines.append(f"{stat}: {diff}")
            else:
                lines.append(f"{stat}: =")
        return lines

    def _get_item_name(self, item_instance):
        if item_instance is None:
            return "Aucun"
        item_id = item_instance["item"]
        item_data = self.game.data.items.get(item_id, {})
        return item_data.get("name", item_id)

    def _draw_slot_content(self, screen, rect, slot):
        item_id = slot["item"]
        item_data = self.game.data.items.get(item_id, {})
        item_name = item_data.get("name", item_id)

        if slot.get("kind") == "stackable":
            quantity = slot.get("quantity")
            detail_text = f"x{quantity}" if quantity is not None else ""
        elif slot.get("kind") == "unique":
            detail_text = self._format_short_stats(slot.get("stats", {}))
        else:
            detail_text = ""

        item_label = self.small_font.render(
            self._short_text(item_name), True, (245, 245, 245)
        )
        screen.blit(item_label, (rect.x + 6, rect.y + 10))

        if detail_text:
            detail_label = self.small_font.render(
                self._short_text(detail_text), True, (220, 220, 160)
            )
            screen.blit(detail_label, (rect.x + 6, rect.y + 42))

    def _format_short_stats(self, stats):
        for stat, value in stats.items():
            return f"{stat} +{value}"
        return ""

    def _short_text(self, text, max_length=10):
        text = str(text)
        if len(text) <= max_length:
            return text
        return text[: max_length - 1] + "."
