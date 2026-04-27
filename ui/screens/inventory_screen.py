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
        if slot.get("kind") == "stackable":
            item_text = slot["item"]
            quantity = slot.get("quantity")
            quantity_text = f"x{quantity}" if quantity is not None else ""
        else:
            item_text = slot.get("name", slot.get("item", "Item"))
            quantity_text = ""

        item_label = self.small_font.render(str(item_text), True, (245, 245, 245))
        screen.blit(item_label, (rect.x + 6, rect.y + 10))

        if quantity_text:
            quantity_label = self.small_font.render(
                quantity_text, True, (220, 220, 160)
            )
            screen.blit(quantity_label, (rect.x + 6, rect.y + 42))
