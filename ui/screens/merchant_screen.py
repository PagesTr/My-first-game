import pygame

from systems.economy import calculate_item_sell_price, sell_inventory_item


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


class MerchantScreen:
    def __init__(self, game):
        self.game = game
        self.title_font = pygame.font.Font(None, 46)
        self.font = pygame.font.Font(None, 24)
        self.small_font = pygame.font.Font(None, 20)
        self.back_btn = Button((50, 520, 140, 50), "Back")
        self.sell_btn = Button((210, 520, 140, 50), "Sell")
        self.selected_slot_index = None
        self.start_x = 50
        self.start_y = 120
        self.slot_size = 70
        self.gap = 10
        self.columns = 6

    def handle_event(self, event):
        if event.type != pygame.MOUSEBUTTONDOWN:
            return

        if self.back_btn.is_clicked(event.pos):
            self.game.state = "zone_select"
            return

        if not self.game.player:
            return

        if self.sell_btn.is_clicked(event.pos):
            self._sell_selected_item()
            return

        slot_index = self._get_slot_index_at_pos(event.pos)
        if slot_index is None:
            return

        inventory = self.game.player["inventory"]
        if inventory["slots"][slot_index] is not None:
            self._select_slot(slot_index)
        else:
            self.selected_slot_index = None

    def draw(self, screen):
        screen.fill((18, 24, 30))

        title = self.title_font.render("Merchant", True, (245, 245, 245))
        screen.blit(title, (50, 40))

        if self.game.player:
            self._draw_gold_panel(screen)
            self._draw_inventory_slots(screen)
            self._draw_selected_item_panel(screen)
        else:
            message = self.font.render("No player available.", True, (220, 220, 220))
            screen.blit(message, (50, 120))

        self.back_btn.draw(screen, self.font)
        self.sell_btn.draw(screen, self.font)

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

    def _select_slot(self, slot_index):
        self.selected_slot_index = slot_index

    def _sell_selected_item(self):
        if not self.game.player or self.selected_slot_index is None:
            return False

        sold = sell_inventory_item(
            self.game.player,
            self.game.player["inventory"],
            self.selected_slot_index,
            self.game.data.items,
        )
        if sold:
            self.selected_slot_index = None

        return sold

    def _draw_inventory_slots(self, screen):
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
            border_color = (230, 215, 120) if index == self.selected_slot_index else (120, 130, 140)
            pygame.draw.rect(screen, border_color, rect, 3 if index == self.selected_slot_index else 2)

            if slot is None:
                continue

            item_name = self._short_text(self._get_item_name(slot), 10)
            item_label = self.small_font.render(item_name, True, (245, 245, 245))
            screen.blit(item_label, (rect.x + 6, rect.y + 10))

            if slot.get("kind") == "stackable" and slot.get("quantity") is not None:
                quantity_label = self.small_font.render(
                    f"x{slot['quantity']}",
                    True,
                    (220, 220, 160),
                )
                screen.blit(quantity_label, (rect.x + 6, rect.y + 42))

    def _draw_gold_panel(self, screen):
        gold = self.game.player.get("gold", 0)
        gold_text = self.font.render(f"Gold: {gold}", True, (245, 220, 120))
        screen.blit(gold_text, (560, 70))

    def _draw_selected_item_panel(self, screen):
        rect = pygame.Rect(560, 120, 190, 170)
        pygame.draw.rect(screen, (35, 40, 48), rect)
        pygame.draw.rect(screen, (120, 130, 140), rect, 2)

        title = self.font.render("Selected Item", True, (245, 245, 245))
        screen.blit(title, (rect.x + 10, rect.y + 10))

        item_instance = None
        if self.selected_slot_index is not None:
            slots = self.game.player["inventory"]["slots"]
            if 0 <= self.selected_slot_index < len(slots):
                item_instance = slots[self.selected_slot_index]

        if item_instance is None:
            message = self.small_font.render(
                "Select an item to sell.",
                True,
                (190, 200, 205),
            )
            screen.blit(message, (rect.x + 10, rect.y + 45))
            return

        name = self.small_font.render(
            self._short_text(self._get_item_name(item_instance), 20),
            True,
            (245, 245, 245),
        )
        screen.blit(name, (rect.x + 10, rect.y + 45))

        y = rect.y + 70
        quantity = item_instance.get("quantity")
        if quantity is not None:
            quantity_text = self.small_font.render(
                f"Quantity: {quantity}",
                True,
                (220, 220, 220),
            )
            screen.blit(quantity_text, (rect.x + 10, y))
            y += 24

        sell_price = self._get_item_sell_price(item_instance)
        if sell_price > 0:
            price_line = f"Sell price: {sell_price} gold"
        else:
            price_line = "Sell price: -"

        price_text = self.small_font.render(price_line, True, (245, 220, 120))
        screen.blit(price_text, (rect.x + 10, y))

    def _get_item_name(self, item_instance):
        item_id = item_instance.get("item")
        item_data = self.game.data.items.get(item_id, {})
        return item_data.get("name", item_id)

    def _get_item_sell_price(self, item_instance):
        item_id = item_instance.get("item")
        item_data = self.game.data.items.get(item_id, {})
        return calculate_item_sell_price(item_instance, item_data)

    def _short_text(self, text, max_length=16):
        text = str(text)
        if len(text) <= max_length:
            return text
        return text[: max_length - 1] + "."
