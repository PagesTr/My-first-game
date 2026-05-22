import pygame


class InventoryOverlay:
    def __init__(self, game):
        self.game = game
        self.opened = False
        self.title_font = pygame.font.Font(None, 34)
        self.body_font = pygame.font.Font(None, 24)
        self.small_font = pygame.font.Font(None, 20)
        self.close_rect = pygame.Rect(0, 0, 0, 0)
        self.slot_rects = []

    def open(self):
        self.opened = True

    def close(self):
        self.opened = False

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
            if self.close_rect.collidepoint(event.pos):
                self.close()
            return True

        return False

    def draw(self, screen):
        if not self.opened:
            return

        overlay = pygame.Surface(screen.get_size(), pygame.SRCALPHA)
        overlay.fill((0, 0, 0, 150))
        screen.blit(overlay, (0, 0))

        screen_rect = screen.get_rect()
        panel_width = min(640, screen_rect.width - 64)
        panel_height = min(470, screen_rect.height - 88)
        panel = pygame.Rect(0, 0, panel_width, panel_height)
        panel.center = screen_rect.center
        pygame.draw.rect(screen, (22, 25, 26), panel, border_radius=8)
        pygame.draw.rect(screen, (126, 145, 110), panel, 2, border_radius=8)

        title = self.title_font.render("Inventory", True, (232, 226, 184))
        screen.blit(title, (panel.x + 24, panel.y + 18))

        gold_text = self.body_font.render(f"Gold: {self._get_player_gold()}", True, (226, 200, 96))
        screen.blit(gold_text, (panel.x + 24, panel.y + 52))

        self.close_rect = pygame.Rect(panel.right - 46, panel.y + 16, 28, 28)
        pygame.draw.rect(screen, (54, 58, 58), self.close_rect, border_radius=5)
        pygame.draw.rect(screen, (160, 175, 150), self.close_rect, 1, border_radius=5)
        close_text = self.body_font.render("X", True, (235, 230, 210))
        screen.blit(close_text, close_text.get_rect(center=self.close_rect.center))

        slots = self._get_inventory_slots()
        slot_size = 52
        spacing = 8
        columns = min(6, max(1, (panel.width - 48) // (slot_size + spacing)))
        grid_x = panel.x + 24
        grid_y = panel.y + 88
        max_rows = max(1, (panel.bottom - grid_y - 28) // (slot_size + spacing))
        self.slot_rects = []

        for index, slot in enumerate(slots[: columns * max_rows]):
            column = index % columns
            row = index // columns
            rect = pygame.Rect(
                grid_x + column * (slot_size + spacing),
                grid_y + row * (slot_size + spacing),
                slot_size,
                slot_size,
            )
            self.slot_rects.append((index, rect))
            self._draw_slot(screen, rect, slot)

        hovered_slot = self._get_hovered_slot(slots)
        if hovered_slot is not None:
            tooltip_x = grid_x + columns * (slot_size + spacing) + 20
            tooltip = pygame.Rect(tooltip_x, grid_y, panel.right - tooltip_x - 24, 132)
            if tooltip.width < 170:
                tooltip = pygame.Rect(panel.x + 24, panel.bottom - 116, panel.width - 48, 88)
            self._draw_item_tooltip(screen, tooltip, hovered_slot)

    def _draw_slot(self, screen, rect, slot):
        border_color = self._get_rarity_color(slot) if slot is not None else (78, 88, 82)
        fill_color = (34, 39, 39) if slot is None else (41, 47, 45)
        pygame.draw.rect(screen, fill_color, rect, border_radius=5)
        pygame.draw.rect(screen, border_color, rect, 2, border_radius=5)

        if slot is None:
            return

        item_name = self._get_item_name(slot)
        label = self._fit_text(self.small_font, item_name, rect.width - 8)
        label_surface = self.small_font.render(label, True, (235, 232, 210))
        label_rect = label_surface.get_rect(center=(rect.centerx, rect.centery - 3))
        screen.blit(label_surface, label_rect)

        quantity = slot.get("quantity")
        if quantity is not None:
            quantity_surface = self.small_font.render(str(quantity), True, (242, 228, 178))
            quantity_rect = quantity_surface.get_rect(bottomright=(rect.right - 4, rect.bottom - 3))
            screen.blit(quantity_surface, quantity_rect)

    def _draw_item_tooltip(self, screen, rect, slot):
        pygame.draw.rect(screen, (18, 21, 22), rect, border_radius=6)
        pygame.draw.rect(screen, self._get_rarity_color(slot), rect, 1, border_radius=6)

        item_data = self._get_item_data(slot)
        lines = [
            (self._get_item_name(slot), self.body_font, (236, 232, 206)),
        ]
        item_type = item_data.get("type") or slot.get("kind")
        if item_type:
            lines.append((f"Type: {item_type}", self.small_font, (204, 214, 196)))
        quantity = slot.get("quantity")
        if quantity is not None:
            lines.append((f"Quantity: {quantity}", self.small_font, (204, 214, 196)))
        rarity = slot.get("rarity") or item_data.get("rarity")
        if rarity:
            lines.append((f"Rarity: {str(rarity).capitalize()}", self.small_font, self._get_rarity_color(slot)))

        y = rect.y + 10
        for text, font, color in lines:
            fitted = self._fit_text(font, text, rect.width - 18)
            surface = font.render(fitted, True, color)
            screen.blit(surface, (rect.x + 10, y))
            y += surface.get_height() + 5

    def _get_hovered_slot(self, slots):
        mouse_position = pygame.mouse.get_pos()
        for index, rect in self.slot_rects:
            if index < len(slots) and rect.collidepoint(mouse_position):
                return slots[index]
        return None

    def _get_inventory_slots(self):
        player = getattr(self.game, "player", {})
        inventory = player.get("inventory", {}) if isinstance(player, dict) else {}
        slots = inventory.get("slots", []) if isinstance(inventory, dict) else []
        return slots if isinstance(slots, list) else []

    def _get_player_gold(self):
        player = getattr(self.game, "player", {})
        if isinstance(player, dict):
            return player.get("gold", 0)
        return 0

    def _get_item_data(self, slot):
        if slot is None:
            return {}
        item_id = slot.get("item")
        data = getattr(self.game, "data", None)
        items = getattr(data, "items", {}) if data is not None else {}
        return items.get(item_id, {}) if isinstance(items, dict) else {}

    def _get_item_name(self, slot):
        if slot is None:
            return ""
        item_id = slot.get("item", "")
        item_data = self._get_item_data(slot)
        return item_data.get("name", item_id)

    def _get_rarity_color(self, slot):
        colors = {
            "common": (170, 170, 170),
            "uncommon": (100, 220, 120),
            "rare": (100, 160, 255),
            "epic": (180, 120, 255),
            "legendary": (255, 200, 80),
            "unique": (240, 90, 90),
        }
        if slot is None:
            return (82, 96, 88)
        item_data = self._get_item_data(slot)
        rarity = slot.get("rarity") or item_data.get("rarity")
        return colors.get(rarity, (210, 216, 198))

    def _fit_text(self, font, text, max_width):
        text = str(text)
        if font.size(text)[0] <= max_width:
            return text
        ellipsis = "..."
        while text and font.size(text + ellipsis)[0] > max_width:
            text = text[:-1]
        return text + ellipsis if text else ellipsis
