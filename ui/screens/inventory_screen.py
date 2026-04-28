import pygame


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

    def handle_event(self, event):
        if event.type == pygame.MOUSEBUTTONDOWN:
            if self.back_btn.is_clicked(event.pos):
                self.game.state = "zone_select"

    def draw(self, screen):
        screen.fill((18, 24, 30))

        title = self.title_font.render("Inventaire", True, (245, 245, 245))
        screen.blit(title, (50, 40))

        if not self.game.player:
            self.back_btn.draw(screen, self.font)
            return

        slots = self.game.player["inventory"]["slots"]
        start_x = 50
        start_y = 110
        slot_size = 70
        gap = 10
        columns = 6

        for index, slot in enumerate(slots):
            col = index % columns
            row = index // columns
            rect = pygame.Rect(
                start_x + col * (slot_size + gap),
                start_y + row * (slot_size + gap),
                slot_size,
                slot_size,
            )
            pygame.draw.rect(screen, (45, 50, 58), rect)
            pygame.draw.rect(screen, (120, 130, 140), rect, 2)

            if slot is not None:
                self._draw_slot_content(screen, rect, slot)

        self.back_btn.draw(screen, self.font)

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
