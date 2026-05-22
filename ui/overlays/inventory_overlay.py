import pygame

from systems.equipment import EQUIPMENT_SLOTS, equip_item, unequip_item
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
        self.selected_source = None
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
        overlay.fill((0, 0, 0, 150))
        screen.blit(overlay, (0, 0))

        panel = self._get_panel_rect(screen)
        pygame.draw.rect(screen, (22, 25, 26), panel, border_radius=8)
        pygame.draw.rect(screen, (126, 145, 110), panel, 2, border_radius=8)

        title = self.title_font.render("Inventory", True, (232, 226, 184))
        screen.blit(title, (panel.x + 20, panel.y + 14))

        self.close_rect = pygame.Rect(panel.right - 44, panel.y + 14, 28, 28)
        self.compact_rect = pygame.Rect(panel.right - 148, panel.y + 14, 92, 28)
        self._draw_button(screen, self.close_rect, "X")
        self._draw_button(screen, self.compact_rect, "Compact")

        if not isinstance(getattr(self.game, "player", None), dict):
            message = self.body_font.render("No player inventory available.", True, (230, 220, 190))
            screen.blit(message, (panel.x + 24, panel.y + 76))
            return

        gold_text = self.body_font.render(f"Gold: {self._get_player_gold()}", True, (226, 200, 96))
        screen.blit(gold_text, (panel.x + 22, panel.y + 52))

        inventory_rect = pygame.Rect(panel.x + 20, panel.y + 82, 372, panel.height - 106)
        equipment_rect = pygame.Rect(panel.x + 410, panel.y + 70, panel.right - panel.x - 430, 210)
        details_rect = pygame.Rect(panel.x + 410, panel.y + 294, panel.right - panel.x - 430, panel.bottom - panel.y - 318)

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

        item, source = self._get_item_at_position(position)
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

        self.selected_source = source

    def _draw_inventory_grid(self, screen, area):
        label = self.body_font.render("Bag", True, (220, 226, 200))
        screen.blit(label, (area.x, area.y - 24))

        slots = self._get_inventory_slots()
        slot_size = 46
        spacing = 6
        columns = 7
        self.slot_rects = []

        for index, slot in enumerate(slots):
            column = index % columns
            row = index // columns
            rect = pygame.Rect(
                area.x + column * (slot_size + spacing),
                area.y + row * (slot_size + spacing),
                slot_size,
                slot_size,
            )
            if rect.bottom > area.bottom:
                break
            self.slot_rects.append((index, rect))
            self._draw_inventory_slot(screen, rect, slot, ("inventory", index))

    def _draw_inventory_slot(self, screen, rect, slot, source):
        is_selected = source == self.selected_source
        border_color = self._get_rarity_color(slot) if slot is not None else (78, 88, 82)
        if is_selected:
            border_color = (242, 226, 126)

        pygame.draw.rect(screen, (34, 39, 39) if slot is None else (41, 47, 45), rect, border_radius=5)
        pygame.draw.rect(screen, border_color, rect, 3 if is_selected else 2, border_radius=5)

        if slot is None:
            return

        label = self._abbreviate_name(self._get_item_name(slot), 7)
        label_surface = self.small_font.render(label, True, (235, 232, 210))
        label_rect = label_surface.get_rect(center=(rect.centerx, rect.centery - 3))
        screen.blit(label_surface, label_rect)

        quantity = slot.get("quantity")
        if quantity is not None:
            quantity_surface = self.small_font.render(str(quantity), True, (242, 228, 178))
            quantity_rect = quantity_surface.get_rect(bottomright=(rect.right - 4, rect.bottom - 3))
            screen.blit(quantity_surface, quantity_rect)

    def _draw_equipment_panel(self, screen, area):
        title = self.body_font.render("Equipment", True, (220, 226, 200))
        screen.blit(title, (area.x, area.y - 24))

        equipment = self._get_equipment()
        self.equipment_rects = {}
        slot_width = max(92, (area.width - 8) // 2)
        slot_height = 31
        labels = self._equipment_labels()

        for index, slot_key in enumerate(EQUIPMENT_SLOTS):
            column = index % 2
            row = index // 2
            rect = pygame.Rect(
                area.x + column * (slot_width + 8),
                area.y + row * (slot_height + 6),
                slot_width,
                slot_height,
            )
            self.equipment_rects[slot_key] = rect
            item = equipment.get(slot_key) if isinstance(equipment, dict) else None
            source = ("equipment", slot_key)
            is_selected = source == self.selected_source
            border_color = (242, 226, 126) if is_selected else self._get_rarity_color(item)
            pygame.draw.rect(screen, (33, 37, 39), rect, border_radius=4)
            pygame.draw.rect(screen, border_color, rect, 2, border_radius=4)

            slot_label = labels.get(slot_key, slot_key)
            item_label = self._get_item_name(item) if item is not None else "-"
            text = self._fit_text(self.small_font, f"{slot_label}: {item_label}", rect.width - 8)
            surface = self.small_font.render(text, True, (224, 226, 208))
            screen.blit(surface, (rect.x + 5, rect.y + 8))

    def _draw_details_panel(self, screen, rect):
        pygame.draw.rect(screen, (18, 21, 22), rect, border_radius=6)
        pygame.draw.rect(screen, (80, 96, 88), rect, 1, border_radius=6)

        item = self._get_selected_item()
        if item is None:
            text = self.small_font.render("Select an item to view details.", True, (198, 205, 188))
            screen.blit(text, (rect.x + 12, rect.y + 12))
            return

        item_data = self._get_item_data(item)
        lines = [
            (self._get_item_name(item), self.body_font, (236, 232, 206)),
            (f"ID: {item.get('item', '-')}", self.small_font, (190, 202, 188)),
            (f"Kind: {item.get('kind', '-')}", self.small_font, (204, 214, 196)),
        ]

        item_type = item_data.get("type")
        if item_type:
            lines.append((f"Type: {item_type}", self.small_font, (204, 214, 196)))
        rarity = item.get("rarity") or item_data.get("rarity")
        if rarity:
            lines.append((f"Rarity: {str(rarity).capitalize()}", self.small_font, self._get_rarity_color(item)))
        quantity = item.get("quantity")
        if quantity is not None:
            lines.append((f"Quantity: {quantity}", self.small_font, (204, 214, 196)))
        level = item.get("level") or item_data.get("level")
        if level is not None:
            lines.append((f"Level: {level}", self.small_font, (204, 214, 196)))

        description = item_data.get("description")
        if description:
            lines.extend((line, self.small_font, (190, 202, 188)) for line in self._wrap_text(description, rect.width - 24, self.small_font, 4))

        y = rect.y + 10
        for text, font, color in lines:
            if y + font.get_height() > rect.bottom - 8:
                break
            fitted = self._fit_text(font, text, rect.width - 20)
            surface = font.render(fitted, True, color)
            screen.blit(surface, (rect.x + 10, y))
            y += surface.get_height() + 5

    def _draw_button(self, screen, rect, label):
        pygame.draw.rect(screen, (54, 58, 58), rect, border_radius=5)
        pygame.draw.rect(screen, (160, 175, 150), rect, 1, border_radius=5)
        text = self.small_font.render(label, True, (235, 230, 210))
        screen.blit(text, text.get_rect(center=rect.center))

    def _get_item_at_position(self, position):
        for index, rect in self.slot_rects:
            if rect.collidepoint(position):
                slots = self._get_inventory_slots()
                return (slots[index], ("inventory", index)) if index < len(slots) else (None, None)

        equipment = self._get_equipment()
        for slot_key, rect in self.equipment_rects.items():
            if rect.collidepoint(position):
                item = equipment.get(slot_key) if isinstance(equipment, dict) else None
                return item, ("equipment", slot_key)

        return None, None

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
        if not self._has_player_inventory():
            self._clear_selection()
            return False

        source_type, source_key = source
        action_done = False

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
                action_done = use_consumable_item(self.game.player, inventory, source_key, self.game.data.items)
            else:
                action_done = equip_item(self.game.player, inventory, source_key, self.game.data.items)
        elif source_type == "equipment":
            action_done = unequip_item(self.game.player, self.game.player["inventory"], source_key)

        if action_done:
            self._after_inventory_change()
        return action_done

    def _compact_inventory(self):
        if not self._has_player_inventory():
            return False
        compacted = compact_inventory(self.game.player["inventory"])
        if compacted:
            self._clear_selection()
            self._save_current_game()
        return compacted

    def _after_inventory_change(self):
        prepare_player_for_combat(
            self.game.player,
            self.game.data.items,
            self.game.data.classes,
            self.game.data.skills,
        )
        self._save_current_game()
        self._clear_selection()

    def _save_current_game(self):
        if hasattr(self.game, "save_current_game"):
            self.game.save_current_game()

    def _clear_selection(self):
        self.selected_source = None
        self.last_click_source = None

    def _get_selected_item(self):
        if self.selected_source is None:
            return None
        source_type, source_key = self.selected_source
        if source_type == "inventory":
            slots = self._get_inventory_slots()
            if isinstance(source_key, int) and 0 <= source_key < len(slots):
                return slots[source_key]
            return None
        if source_type == "equipment":
            equipment = self._get_equipment()
            return equipment.get(source_key) if isinstance(equipment, dict) else None
        return None

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

    def _get_equipment(self):
        player = getattr(self.game, "player", {})
        equipment = player.get("equipment", {}) if isinstance(player, dict) else {}
        return equipment if isinstance(equipment, dict) else {}

    def _get_player_gold(self):
        player = getattr(self.game, "player", {})
        if isinstance(player, dict):
            return player.get("gold", 0)
        return 0

    def _get_item_data(self, item):
        if item is None:
            return {}
        item_id = item.get("item")
        data = getattr(self.game, "data", None)
        items = getattr(data, "items", {}) if data is not None else {}
        return items.get(item_id, {}) if isinstance(items, dict) else {}

    def _get_item_name(self, item):
        if item is None:
            return ""
        item_id = item.get("item", "")
        item_data = self._get_item_data(item)
        return item_data.get("name", item_id)

    def _get_rarity_color(self, item):
        colors = {
            "common": (170, 170, 170),
            "uncommon": (100, 220, 120),
            "rare": (100, 160, 255),
            "epic": (180, 120, 255),
            "legendary": (255, 200, 80),
            "unique": (240, 90, 90),
        }
        if item is None:
            return (82, 96, 88)
        item_data = self._get_item_data(item)
        rarity = item.get("rarity") or item_data.get("rarity")
        return colors.get(rarity, (210, 216, 198))

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

    def _abbreviate_name(self, text, max_chars):
        words = str(text).replace("_", " ").split()
        if len(words) > 1:
            abbreviation = "".join(word[:1] for word in words[:3]).upper()
            if abbreviation:
                return abbreviation[:max_chars]
        return str(text)[:max_chars]

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
            lines[-1] = self._fit_text(font, lines[-1], max_width)
        return lines

    def _fit_text(self, font, text, max_width):
        text = str(text)
        if font.size(text)[0] <= max_width:
            return text
        ellipsis = "..."
        while text and font.size(text + ellipsis)[0] > max_width:
            text = text[:-1]
        return text + ellipsis if text else ellipsis
