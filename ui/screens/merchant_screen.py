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
        self.sell_quantity = 1
        self.decrease_quantity_btn = Button((560, 390, 40, 36), "-")
        self.increase_quantity_btn = Button((610, 390, 40, 36), "+")
        self.sell_all_btn = Button((660, 390, 90, 36), "All")
        self.quantity_input_active = False
        self.quantity_input_text = "1"
        self.quantity_input_rect = pygame.Rect(560, 440, 190, 36)
        self.message = ""
        self.message_color = (190, 200, 205)
        self.start_x = 50
        self.start_y = 120
        self.slot_size = 70
        self.gap = 10
        self.columns = 6

    def handle_event(self, event):
        if self._handle_quantity_keyboard_input(event):
            return

        if event.type != pygame.MOUSEBUTTONDOWN:
            return

        if self.back_btn.is_clicked(event.pos):
            self.game.state = "zone_select"
            return

        if not self.game.player:
            return

        if self.quantity_input_rect.collidepoint(event.pos):
            selected_item = self._get_selected_item()
            if selected_item is not None and selected_item.get("kind") == "stackable":
                self.quantity_input_active = True
                self.quantity_input_text = str(self.sell_quantity)
            return

        if self.decrease_quantity_btn.is_clicked(event.pos):
            self.sell_quantity = max(1, self.sell_quantity - 1)
            self.quantity_input_text = str(self.sell_quantity)
            return

        if self.increase_quantity_btn.is_clicked(event.pos):
            selected_item = self._get_selected_item()
            if selected_item is not None and selected_item.get("kind") == "stackable":
                available_quantity = self._get_available_quantity()
                self.sell_quantity = min(available_quantity, self.sell_quantity + 1)
            else:
                self.sell_quantity = 1
            self.quantity_input_text = str(self.sell_quantity)
            return

        if self.sell_all_btn.is_clicked(event.pos):
            selected_item = self._get_selected_item()
            if selected_item is not None and selected_item.get("kind") == "stackable":
                self.sell_quantity = self._get_available_quantity()
            else:
                self.sell_quantity = 1
            self.quantity_input_text = str(self.sell_quantity)
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
            self.sell_quantity = 1
            self.quantity_input_text = "1"
            self.quantity_input_active = False
            self.message = ""
        else:
            self.selected_slot_index = None
            self.sell_quantity = 1
            self.quantity_input_text = "1"
            self.quantity_input_active = False
            self.message = ""

    def draw(self, screen):
        screen.fill((18, 24, 30))

        title = self.title_font.render("Merchant", True, (245, 245, 245))
        screen.blit(title, (50, 40))

        if self.game.player:
            self._draw_gold_panel(screen)
            self._draw_inventory_slots(screen)
            self._draw_selected_item_panel(screen)
            self._draw_quantity_controls(screen)
            self._draw_quantity_input(screen)
            self._draw_message(screen)
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

    def _get_selected_item(self):
        if not self.game.player or self.selected_slot_index is None:
            return None

        slots = self.game.player["inventory"]["slots"]
        if not 0 <= self.selected_slot_index < len(slots):
            return None

        return slots[self.selected_slot_index]

    def _get_available_quantity(self):
        item_instance = self._get_selected_item()
        if item_instance is None:
            return 0
        if item_instance.get("kind") == "stackable":
            quantity = item_instance.get("quantity")
            if type(quantity) is int and quantity > 0:
                return quantity
            return 0
        return 1

    def _handle_quantity_keyboard_input(self, event):
        if not self.quantity_input_active:
            return False
        if event.type != pygame.KEYDOWN:
            return False

        selected_item = self._get_selected_item()
        if selected_item is None or selected_item.get("kind") != "stackable":
            self.quantity_input_active = False
            return False

        if event.key == pygame.K_RETURN:
            self._apply_quantity_input()
            self.quantity_input_active = False
            return True
        if event.key == pygame.K_ESCAPE:
            self.quantity_input_active = False
            self.quantity_input_text = str(self.sell_quantity)
            return True
        if event.key == pygame.K_BACKSPACE:
            self.quantity_input_text = self.quantity_input_text[:-1]
            return True
        if event.unicode.isdigit():
            self.quantity_input_text += event.unicode
            return True

        return True

    def _apply_quantity_input(self):
        if not self.quantity_input_text:
            self.sell_quantity = 1
        else:
            try:
                self.sell_quantity = int(self.quantity_input_text)
            except ValueError:
                self.sell_quantity = 1

        available_quantity = self._get_available_quantity()
        if available_quantity <= 0:
            self.sell_quantity = 1
        else:
            self.sell_quantity = max(1, min(self.sell_quantity, available_quantity))
        self.quantity_input_text = str(self.sell_quantity)

    def _sell_selected_item(self):
        if not self.game.player or self.selected_slot_index is None:
            self.message = "Select an item first."
            self.message_color = (230, 160, 120)
            return False

        inventory = self.game.player["inventory"]
        slots = inventory["slots"]
        item_instance = self._get_selected_item()
        if item_instance is None:
            self.message = "Select an item first."
            self.message_color = (230, 160, 120)
            return False

        self._apply_quantity_input()
        item_name = self._get_item_name(item_instance)
        unit_price = self._get_item_sell_price(item_instance)
        total_price = unit_price * self.sell_quantity
        sold = sell_inventory_item(
            self.game.player,
            inventory,
            self.selected_slot_index,
            self.game.data.items,
            self.sell_quantity,
        )

        if not sold:
            self.message = "This item cannot be sold."
            self.message_color = (230, 160, 120)
            return False

        if self.sell_quantity == 1:
            self.message = f"Sold {item_name} for {total_price} gold."
        else:
            self.message = f"Sold {self.sell_quantity}x {item_name} for {total_price} gold."
        self.message_color = (120, 220, 140)

        if slots[self.selected_slot_index] is None:
            self.selected_slot_index = None
            self.sell_quantity = 1
            self.quantity_input_active = False
        else:
            available_quantity = self._get_available_quantity()
            self.sell_quantity = min(self.sell_quantity, available_quantity)
        self.quantity_input_text = str(self.sell_quantity)

        return True

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

        item_instance = self._get_selected_item()
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
        unit_price = self._get_item_sell_price(item_instance)
        available_quantity = self._get_available_quantity()
        if item_instance.get("kind") != "stackable":
            self.sell_quantity = 1
        elif available_quantity > 0:
            self.sell_quantity = min(self.sell_quantity, available_quantity)
        if not self.quantity_input_active:
            self.quantity_input_text = str(self.sell_quantity)

        if unit_price > 0:
            unit_price_line = f"Unit price: {unit_price} gold"
            total_line = f"Total: {unit_price * self.sell_quantity} gold"
        else:
            unit_price_line = "Unit price: -"
            total_line = "Total: -"

        panel_lines = [
            unit_price_line,
            f"Quantity to sell: {self.sell_quantity}",
            total_line,
        ]
        for line in panel_lines:
            line_text = self.small_font.render(line, True, (245, 220, 120))
            screen.blit(line_text, (rect.x + 10, y))
            y += 24

    def _draw_message(self, screen):
        if not self.message:
            return

        message_text = self.small_font.render(self.message, True, self.message_color)
        screen.blit(message_text, (560, 310))

    def _draw_quantity_controls(self, screen):
        item_instance = self._get_selected_item()
        if item_instance is None or item_instance.get("kind") != "stackable":
            return

        self.decrease_quantity_btn.draw(screen, self.font)
        self.increase_quantity_btn.draw(screen, self.font)
        self.sell_all_btn.draw(screen, self.small_font)

    def _draw_quantity_input(self, screen):
        item_instance = self._get_selected_item()
        if item_instance is None or item_instance.get("kind") != "stackable":
            return

        label = self.small_font.render("Enter quantity", True, (190, 200, 205))
        screen.blit(label, (self.quantity_input_rect.x, self.quantity_input_rect.y - 20))

        pygame.draw.rect(screen, (35, 40, 48), self.quantity_input_rect)
        border_color = (230, 230, 180) if self.quantity_input_active else (120, 130, 140)
        pygame.draw.rect(screen, border_color, self.quantity_input_rect, 2)

        input_text = self.small_font.render(
            self.quantity_input_text,
            True,
            (245, 245, 245),
        )
        screen.blit(
            input_text,
            (self.quantity_input_rect.x + 10, self.quantity_input_rect.y + 9),
        )

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
