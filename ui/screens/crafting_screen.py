import json
from pathlib import Path

import pygame

from systems.crafting import craft_item


class Button:
    def __init__(self, rect, text):
        self.rect = pygame.Rect(rect)
        self.text = text

    def draw(self, screen, font):
        pygame.draw.rect(screen, (70, 70, 70), self.rect)
        pygame.draw.rect(screen, (200, 200, 200), self.rect, 2)

        label = font.render(self.text, True, (255, 255, 255))
        screen.blit(label, (self.rect.x + 12, self.rect.y + 10))

    def is_clicked(self, pos):
        return self.rect.collidepoint(pos)


class CraftingScreen:
    def __init__(self, game):
        self.game = game
        self.title_font = pygame.font.Font(None, 46)
        self.font = pygame.font.Font(None, 24)
        self.small_font = pygame.font.Font(None, 20)
        self.back_btn = Button((50, 520, 140, 50), "Back")
        self.recipes = self._load_recipes()
        self.recipe_buttons = []
        self.selected_recipe_id = None
        self.message = ""
        self.message_until = 0
        self._build_recipe_buttons()

    def handle_event(self, event):
        if event.type != pygame.MOUSEBUTTONDOWN:
            return

        if self.back_btn.is_clicked(event.pos):
            self.game.state = "inventory"
            return

        for recipe_id, button in self.recipe_buttons:
            if button.is_clicked(event.pos):
                self.selected_recipe_id = recipe_id
                self._try_craft(recipe_id)
                return

    def draw(self, screen):
        screen.fill((18, 24, 30))

        title = self.title_font.render("Crafting", True, (245, 245, 245))
        screen.blit(title, (50, 40))

        self._draw_recipe_list(screen)
        self._draw_recipe_details(screen)
        self._draw_message(screen)
        self.back_btn.draw(screen, self.font)

    def _load_recipes(self):
        recipes_path = Path(__file__).resolve().parents[2] / "data" / "recipes.json"
        with recipes_path.open("r", encoding="utf-8") as recipes_file:
            return json.load(recipes_file)

    def _build_recipe_buttons(self):
        self.recipe_buttons = []
        for index, recipe_id in enumerate(list(self.recipes)[:8]):
            rect = (50, 110 + index * 46, 250, 38)
            self.recipe_buttons.append((recipe_id, Button(rect, self._format_recipe_name(recipe_id))))

        if self.recipe_buttons and self.selected_recipe_id is None:
            self.selected_recipe_id = self.recipe_buttons[0][0]

    def _try_craft(self, recipe_id):
        if not self.game.player:
            self._set_message("Cannot craft")
            return

        recipe = self.recipes[recipe_id]
        crafted = craft_item(
            self.game.player["inventory"],
            recipe,
            self.game.data.items,
        )
        if crafted:
            self._set_message("Craft successful")
        else:
            self._set_message("Cannot craft")

    def _set_message(self, message):
        self.message = message
        self.message_until = pygame.time.get_ticks() + 1800

    def _draw_recipe_list(self, screen):
        list_title = self.font.render("Recipes", True, (245, 245, 245))
        screen.blit(list_title, (50, 82))

        for recipe_id, button in self.recipe_buttons:
            button.draw(screen, self.small_font)
            if recipe_id == self.selected_recipe_id:
                pygame.draw.rect(screen, (220, 220, 120), button.rect, 2)

    def _draw_recipe_details(self, screen):
        if self.selected_recipe_id is None:
            return

        recipe = self.recipes[self.selected_recipe_id]
        x = 350
        y = 110

        name = self._format_recipe_name(self.selected_recipe_id)
        name_text = self.font.render(name, True, (245, 245, 245))
        screen.blit(name_text, (x, y))

        ingredients_title = self.small_font.render("Ingredients", True, (220, 220, 160))
        screen.blit(ingredients_title, (x, y + 44))

        line_y = y + 70
        for ingredient in recipe.get("ingredients", []):
            item_name = self._get_item_name(ingredient.get("item"))
            quantity = ingredient.get("quantity", 0)
            kind = ingredient.get("kind", "unknown")
            line = f"{item_name} x{quantity} ({kind})"
            text = self.small_font.render(line, True, (220, 220, 220))
            screen.blit(text, (x, line_y))
            line_y += 24

        result = recipe.get("result", {})
        result_title = self.small_font.render("Result", True, (220, 220, 160))
        screen.blit(result_title, (x, line_y + 20))

        result_name = self._get_item_name(result.get("item"))
        result_quantity = result.get("quantity", 0)
        result_text = self.small_font.render(
            f"{result_name} x{result_quantity}",
            True,
            (220, 220, 220),
        )
        screen.blit(result_text, (x, line_y + 46))

    def _draw_message(self, screen):
        if not self.message:
            return
        if pygame.time.get_ticks() > self.message_until:
            self.message = ""
            return

        text = self.font.render(self.message, True, (245, 245, 245))
        screen.blit(text, (220, 535))

    def _format_recipe_name(self, recipe_id):
        recipe = self.recipes.get(recipe_id, {})
        name = recipe.get("name", recipe_id)
        return str(name).replace("_", " ").title()

    def _get_item_name(self, item_id):
        item_data = self.game.data.items.get(item_id, {})
        return item_data.get("name", item_id)
