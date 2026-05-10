import pygame

try:
    from systems.crafting import (
        can_craft_recipe,
        craft_recipe,
        count_individual_item,
        count_stackable_item,
    )
except ImportError:
    from systems.crafting import can_craft, craft_item

    def can_craft_recipe(inventory, recipe):
        return can_craft(inventory, recipe)

    def craft_recipe(inventory, recipes, recipe_id, items):
        recipe = recipes.get(recipe_id) if isinstance(recipes, dict) else None
        if not isinstance(recipe, dict):
            return {
                "crafted": False,
                "recipe_id": recipe_id,
                "reason": "unknown_recipe",
            }
        if not can_craft(inventory, recipe):
            return {
                "crafted": False,
                "recipe_id": recipe_id,
                "reason": "missing_ingredients",
            }
        if not craft_item(inventory, recipe, items):
            return {
                "crafted": False,
                "recipe_id": recipe_id,
                "reason": "inventory_full",
            }
        return {
            "crafted": True,
            "recipe_id": recipe_id,
            "result": recipe.get("result", {}),
        }

    def count_stackable_item(inventory, item_id):
        if not isinstance(inventory, dict) or not isinstance(inventory.get("slots"), list):
            return 0

        total = 0
        for slot in inventory["slots"]:
            if not isinstance(slot, dict):
                continue
            if slot.get("kind") == "stackable" and slot.get("item") == item_id:
                total += slot.get("quantity", 0)
        return total

    def count_individual_item(inventory, item_id):
        if not isinstance(inventory, dict) or not isinstance(inventory.get("slots"), list):
            return 0

        total = 0
        for slot in inventory["slots"]:
            if not isinstance(slot, dict):
                continue
            if slot.get("kind") in {"individual", "unique"} and slot.get("item") == item_id:
                total += 1
        return total


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
        self.craft_btn = Button((350, 520, 140, 50), "Craft")
        self.recipe_panel = pygame.Rect(38, 88, 284, 410)
        self.detail_panel = pygame.Rect(342, 88, 410, 410)
        self.recipes = getattr(self.game.data, "recipes", {}) or {}
        self.recipe_buttons = []
        self.filter_buttons = []
        self.selected_recipe_id = None
        self.selected_filter = "All"
        self.recipe_scroll_offset = 0
        self.max_visible_recipes = 8
        self.message = ""
        self.message_success = None
        self.message_until = 0
        self._build_filter_buttons()
        self._build_recipe_buttons()

    def handle_event(self, event):
        if event.type == pygame.MOUSEWHEEL:
            self._scroll_recipes(-event.y)
            return

        if event.type != pygame.MOUSEBUTTONDOWN:
            return

        if self.back_btn.is_clicked(event.pos):
            self.game.state = "town"
            return

        for filter_name, button in self.filter_buttons:
            if button.is_clicked(event.pos):
                self.selected_filter = filter_name
                self.recipe_scroll_offset = 0
                self._select_first_filtered_recipe()
                self.message = ""
                return

        for recipe_id, button in self.recipe_buttons:
            if button.is_clicked(event.pos):
                self.selected_recipe_id = recipe_id
                self.message = ""
                return

        if self.craft_btn.is_clicked(event.pos):
            if not self._is_selected_recipe_available():
                self._set_message("Missing ingredients", False)
                return
            self._try_craft()
            return

    def draw(self, screen):
        screen.fill((18, 24, 30))

        title = self.title_font.render("Crafting", True, (245, 245, 245))
        screen.blit(title, (50, 40))

        self._draw_recipe_list(screen)
        self._draw_recipe_details(screen)
        self._draw_message(screen)
        self.back_btn.draw(screen, self.font)
        self._draw_craft_button(screen)

    def _build_filter_buttons(self):
        filter_specs = [
            ("All", (50, 122, 42, 28)),
            ("Ready", (98, 122, 58, 28)),
            ("Consumables", (162, 122, 96, 28)),
            ("Equipment", (50, 154, 88, 28)),
            ("Profession", (144, 154, 98, 28)),
        ]
        self.filter_buttons = [
            (filter_name, Button(rect, filter_name))
            for filter_name, rect in filter_specs
        ]

    def _build_recipe_buttons(self):
        self.recipe_buttons = []
        if not isinstance(self.recipes, dict):
            self.recipes = {}

        filtered_recipe_ids = self._get_filtered_recipe_ids()
        self._clamp_recipe_scroll_offset(filtered_recipe_ids)
        visible_recipe_ids = filtered_recipe_ids[
            self.recipe_scroll_offset : self.recipe_scroll_offset + self.max_visible_recipes
        ]

        for index, recipe_id in enumerate(visible_recipe_ids):
            rect = (50, 194 + index * 36, 250, 32)
            self.recipe_buttons.append(
                (recipe_id, Button(rect, self._format_recipe_name(recipe_id)))
            )

        if self.selected_recipe_id not in filtered_recipe_ids:
            self.selected_recipe_id = filtered_recipe_ids[0] if filtered_recipe_ids else None

    def _try_craft(self):
        if not self.game.player or self.selected_recipe_id is None:
            self._set_message("Cannot craft", False)
            return

        result = craft_recipe(
            self.game.player["inventory"],
            self.recipes,
            self.selected_recipe_id,
            self.game.data.items,
        )

        if result.get("crafted") is True:
            if hasattr(self.game, "record_craft_quest_progress"):
                self.game.record_craft_quest_progress(self.selected_recipe_id, result)
            self._save_current_game()
            result_name = self._get_recipe_result_name(self._get_selected_recipe())
            self._set_message(f"Crafted: {result_name}", True)
            self._build_recipe_buttons()
        else:
            self._set_message(self._get_craft_failure_message(result), False)

    def _save_current_game(self):
        if hasattr(self.game, "save_current_game"):
            self.game.save_current_game()

    def _set_message(self, message, success=None):
        self.message = message
        self.message_success = success
        self.message_until = pygame.time.get_ticks() + 1800

    def _draw_recipe_list(self, screen):
        self._build_recipe_buttons()
        self._draw_panel(screen, self.recipe_panel)
        list_title = self.font.render("Recipes", True, (245, 245, 245))
        screen.blit(list_title, (self.recipe_panel.x + 12, self.recipe_panel.y + 12))

        for filter_name, button in self.filter_buttons:
            selected = filter_name == self.selected_filter
            self._draw_filter_button(screen, button, selected)

        filtered_recipe_ids = self._get_filtered_recipe_ids()
        showing_text = self.small_font.render(
            f"Showing: {self.selected_filter} ({len(filtered_recipe_ids)})",
            True,
            (190, 200, 205),
        )
        screen.blit(showing_text, (self.recipe_panel.x + 12, self.recipe_panel.y + 96))

        if not self.recipe_buttons:
            empty_text = self.small_font.render("No recipes", True, (150, 155, 160))
            screen.blit(empty_text, (self.recipe_panel.x + 12, self.recipe_panel.y + 128))
            return

        for recipe_id, button in self.recipe_buttons:
            recipe = self.recipes.get(recipe_id, {})
            is_available = self._is_recipe_available(recipe)
            bg_color = (44, 58, 48) if is_available else (42, 44, 48)
            border_color = (105, 170, 110) if is_available else (95, 100, 105)
            text_color = (145, 220, 150) if is_available else (150, 155, 160)
            status = "READY" if is_available else "MISS"

            pygame.draw.rect(screen, bg_color, button.rect)
            pygame.draw.rect(screen, border_color, button.rect, 2)

            name = self._truncate_to_width(
                self._get_recipe_result_name(recipe),
                self.small_font,
                168,
            )
            name_text = self.small_font.render(name, True, text_color)
            screen.blit(name_text, (button.rect.x + 8, button.rect.y + 4))

            status_text = self.small_font.render(status, True, text_color)
            screen.blit(status_text, (button.rect.right - 58, button.rect.y + 4))

            summary = "Can craft" if is_available else self._get_recipe_missing_summary(recipe)
            summary_text = self.small_font.render(
                self._truncate_to_width(summary, self.small_font, 230),
                True,
                (185, 195, 190) if is_available else (205, 150, 110),
            )
            screen.blit(summary_text, (button.rect.x + 8, button.rect.y + 18))

            if recipe_id == self.selected_recipe_id:
                pygame.draw.rect(screen, (220, 220, 120), button.rect, 2)

    def _draw_recipe_details(self, screen):
        self._draw_panel(screen, self.detail_panel)
        if self.selected_recipe_id is None:
            message = self.font.render("Select a recipe", True, (190, 200, 205))
            screen.blit(message, (self.detail_panel.x + 16, self.detail_panel.y + 18))
            return

        recipe = self._get_selected_recipe()
        x = self.detail_panel.x + 16
        y = self.detail_panel.y + 18

        name = self._get_recipe_result_name(recipe)
        name_text = self.font.render(name, True, (245, 245, 245))
        screen.blit(name_text, (x, y))

        is_available = self._is_recipe_available(recipe)
        status = self._get_recipe_status_text(recipe)
        status_color = (120, 190, 130) if is_available else (210, 120, 90)
        status_text = self.small_font.render(status, True, status_color)
        screen.blit(status_text, (x, y + 28))

        ingredients_title = self.small_font.render("Ingredients", True, (220, 220, 160))
        screen.blit(ingredients_title, (x, y + 58))

        line_y = y + 84
        ingredients = recipe.get("ingredients", []) if isinstance(recipe, dict) else []
        if not isinstance(ingredients, list):
            ingredients = []

        if not ingredients:
            missing_text = self.small_font.render("No ingredients", True, (150, 155, 160))
            screen.blit(missing_text, (x, line_y))
            line_y += 24

        for ingredient in ingredients[:8]:
            if not isinstance(ingredient, dict):
                continue
            item_name = self._get_item_name(ingredient.get("item"))
            required_quantity = ingredient.get("quantity", 0)
            owned_quantity = self._count_owned_ingredient(ingredient)
            has_ingredient = owned_quantity >= required_quantity
            prefix = "✓" if has_ingredient else "✗"
            line = f"{prefix} {item_name}: {owned_quantity} / {required_quantity}"
            color = (
                (120, 190, 130)
                if has_ingredient
                else (220, 130, 80)
            )
            text = self.small_font.render(line, True, color)
            screen.blit(text, (x, line_y))
            line_y += 20

        result = recipe.get("result", {})
        result_title = self.small_font.render("Result", True, (220, 220, 160))
        screen.blit(result_title, (x, line_y + 12))

        result_name = self._get_recipe_result_name(recipe)
        result_quantity = result.get("quantity", 0)
        result_text = self.small_font.render(
            f"{result_name} x{result_quantity}",
            True,
            (220, 220, 220),
        )
        screen.blit(result_text, (x, line_y + 38))

        result_data = self._get_recipe_result_data(recipe)
        result_type = self._get_item_type_label(self._get_recipe_result_item_id(recipe))
        result_category = self._get_item_category_label(self._get_recipe_result_item_id(recipe))
        type_text = self.small_font.render(
            f"Type: {result_type}",
            True,
            (220, 220, 220),
        )
        category_text = self.small_font.render(
            f"Category: {result_category}",
            True,
            (220, 220, 220),
        )
        screen.blit(type_text, (x, line_y + 62))
        screen.blit(category_text, (x, line_y + 84))

        stats = result_data.get("stats", {}) if isinstance(result_data, dict) else {}
        if isinstance(stats, dict) and stats:
            stats_title = self.small_font.render("Stats", True, (220, 220, 160))
            screen.blit(stats_title, (x, line_y + 116))
            stats_text = self._format_item_stats(stats)
            stats_y = line_y + 140
            for stat_line in stats_text[:5]:
                text = self.small_font.render(stat_line, True, (220, 220, 220))
                screen.blit(text, (x, stats_y))
                stats_y += 18

    def _draw_message(self, screen):
        if not self.message:
            return
        if pygame.time.get_ticks() > self.message_until:
            self.message = ""
            self.message_success = None
            return

        text = self.small_font.render(self._short_text(self.message, 34), True, self._get_message_color())
        screen.blit(text, (self.detail_panel.x + 14, self.detail_panel.bottom + 10))

    def _draw_craft_button(self, screen):
        is_available = self._is_selected_recipe_available()
        bg_color = (70, 70, 70)
        border_color = (200, 200, 200)
        if self.selected_recipe_id is None:
            bg_color = (45, 45, 48)
            border_color = (95, 95, 100)
        elif is_available:
            bg_color = (64, 78, 48)
            border_color = (120, 190, 130)
        else:
            bg_color = (45, 45, 48)
            border_color = (95, 95, 100)

        pygame.draw.rect(screen, bg_color, self.craft_btn.rect)
        pygame.draw.rect(screen, border_color, self.craft_btn.rect, 2)

        text_color = (255, 255, 255) if is_available else (150, 155, 160)
        label = self.font.render("Craft", True, text_color)
        screen.blit(label, (self.craft_btn.rect.x + 12, self.craft_btn.rect.y + 10))

    def _draw_filter_button(self, screen, button, selected):
        bg_color = (72, 82, 58) if selected else (48, 54, 62)
        border_color = (220, 220, 120) if selected else (110, 120, 130)
        pygame.draw.rect(screen, bg_color, button.rect, border_radius=4)
        pygame.draw.rect(screen, border_color, button.rect, 2, border_radius=4)
        label = self.small_font.render(button.text, True, (245, 245, 245))
        screen.blit(label, (button.rect.x + 6, button.rect.y + 6))

    def _draw_panel(self, screen, rect):
        pygame.draw.rect(screen, (28, 34, 42), rect)
        pygame.draw.rect(screen, (120, 130, 140), rect, 2)

    def _scroll_recipes(self, direction):
        filtered_recipe_ids = self._get_filtered_recipe_ids()
        max_offset = max(0, len(filtered_recipe_ids) - self.max_visible_recipes)
        self.recipe_scroll_offset = max(
            0,
            min(max_offset, self.recipe_scroll_offset + direction),
        )

    def _clamp_recipe_scroll_offset(self, recipe_ids):
        max_offset = max(0, len(recipe_ids) - self.max_visible_recipes)
        self.recipe_scroll_offset = max(0, min(max_offset, self.recipe_scroll_offset))

    def _select_first_filtered_recipe(self):
        filtered_recipe_ids = self._get_filtered_recipe_ids()
        self.selected_recipe_id = filtered_recipe_ids[0] if filtered_recipe_ids else None
        self._build_recipe_buttons()

    def _get_recipe_result_type(self, recipe):
        result_item_id = self._get_recipe_result_item_id(recipe)
        return self._get_item_data(result_item_id).get("type", "unknown")

    def _recipe_uses_gathered_resource(self, recipe):
        ingredients = recipe.get("ingredients", []) if isinstance(recipe, dict) else []
        if not isinstance(ingredients, list):
            return False
        for ingredient in ingredients:
            if not isinstance(ingredient, dict):
                continue
            item_data = self._get_item_data(ingredient.get("item"))
            if item_data.get("economic_source") == "gathered_resource":
                return True
        return False

    def _get_filtered_recipe_ids(self):
        if not isinstance(self.recipes, dict):
            return []
        return [
            recipe_id
            for recipe_id, recipe in self.recipes.items()
            if self._recipe_matches_filter(recipe_id, recipe)
        ]

    def _recipe_matches_filter(self, recipe_id, recipe):
        if not isinstance(recipe, dict):
            return False
        if self.selected_filter == "All":
            return True
        if self.selected_filter == "Ready":
            return self._is_recipe_available(recipe)
        if self.selected_filter == "Consumables":
            return self._get_recipe_result_type(recipe) == "consumable"
        if self.selected_filter == "Equipment":
            return self._get_recipe_result_type(recipe) == "equipment"
        if self.selected_filter == "Profession":
            return self._recipe_uses_gathered_resource(recipe)
        return True

    def _get_recipe_missing_summary(self, recipe):
        ingredients = recipe.get("ingredients", []) if isinstance(recipe, dict) else []
        if not isinstance(ingredients, list):
            return "Need: ingredients"

        missing = []
        for ingredient in ingredients:
            if not isinstance(ingredient, dict):
                continue
            required_quantity = ingredient.get("quantity", 0)
            owned_quantity = self._count_owned_ingredient(ingredient)
            if owned_quantity < required_quantity:
                missing.append((ingredient, owned_quantity, required_quantity))

        if not missing:
            return "Can craft"

        ingredient, owned_quantity, required_quantity = missing[0]
        item_name = self._get_item_name(ingredient.get("item"))
        summary = f"Need: {item_name} {owned_quantity}/{required_quantity}"
        if len(missing) > 1:
            summary += f" +{len(missing) - 1}"
        return summary

    def _format_recipe_name(self, recipe_id):
        recipe = self.recipes.get(recipe_id, {})
        name = recipe.get("name", recipe_id)
        return str(name).replace("_", " ").title()

    def _get_item_name(self, item_id):
        item_data = self._get_item_data(item_id)
        return item_data.get("name", item_id)

    def _get_item_data(self, item_id):
        item_data = self.game.data.items.get(item_id, {})
        return item_data if isinstance(item_data, dict) else {}

    def _get_item_category_label(self, item_id):
        category = self._get_item_data(item_id).get("category", "unknown")
        return str(category).replace("_", " ").title()

    def _get_item_type_label(self, item_id):
        item_type = self._get_item_data(item_id).get("type", "unknown")
        return str(item_type).replace("_", " ").title()

    def _get_message_color(self):
        if self.message_success is True:
            return (120, 190, 130)
        if self.message_success is False:
            return (220, 130, 80)
        return (245, 245, 245)

    def _is_selected_recipe_available(self):
        if not self.game.player or self.selected_recipe_id is None:
            return False
        return self._is_recipe_available(self._get_selected_recipe())

    def _is_recipe_available(self, recipe):
        if not self.game.player or not isinstance(recipe, dict):
            return False
        return can_craft_recipe(self.game.player["inventory"], recipe)

    def _get_recipe_status_text(self, recipe):
        if self._is_recipe_available(recipe):
            return "Ready to craft"
        return "Missing ingredients"

    def _get_selected_recipe(self):
        if self.selected_recipe_id is None or not isinstance(self.recipes, dict):
            return {}
        recipe = self.recipes.get(self.selected_recipe_id, {})
        return recipe if isinstance(recipe, dict) else {}

    def _get_recipe_result_item_id(self, recipe):
        if not isinstance(recipe, dict):
            return None
        result = recipe.get("result", {})
        if not isinstance(result, dict):
            return None
        return result.get("item")

    def _get_recipe_result_name(self, recipe):
        item_id = self._get_recipe_result_item_id(recipe)
        if item_id:
            return self._get_item_name(item_id)
        if self.selected_recipe_id:
            return self._format_recipe_name(self.selected_recipe_id)
        return "Unknown"

    def _get_recipe_result_data(self, recipe):
        return self._get_item_data(self._get_recipe_result_item_id(recipe))

    def _format_item_stats(self, stats):
        lines = []
        for stat_key, value in stats.items():
            stat_label = self._get_stat_label(stat_key)
            formatted_value = self._format_stat_value(stat_key, value)
            lines.append(f"{stat_label}: {formatted_value}")
        return lines

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
        if stat_key in percent_stats and isinstance(value, (int, float)):
            return f"{value * 100:.1f}%"
        if stat_key == "crit_damage":
            return f"x{value}"
        return str(value)

    def _get_stat_label(self, stat_key):
        labels = {
            "attack": "Attack",
            "defense": "Defense",
            "hp": "HP",
            "max_hp": "Max HP",
            "force": "Strength",
            "strength": "Strength",
            "agility": "Agility",
            "dexterity": "Dexterity",
            "intelligence": "Intelligence",
            "vitality": "Vitality",
            "wisdom": "Wisdom",
            "luck": "Luck",
            "block_chance": "Block",
            "crit_chance": "Crit Chance",
            "crit_damage": "Crit Damage",
            "dodge_chance": "Dodge",
            "initiative": "Initiative",
            "xp_bonus": "XP Bonus",
        }
        return labels.get(stat_key, str(stat_key).replace("_", " ").title())

    def _count_owned_ingredient(self, ingredient):
        if not self.game.player or not isinstance(ingredient, dict):
            return 0

        item_id = ingredient.get("item")
        inventory = self.game.player["inventory"]
        if ingredient.get("kind") == "stackable":
            return count_stackable_item(inventory, item_id)
        if ingredient.get("kind") in {"individual", "unique"}:
            return count_individual_item(inventory, item_id)
        return 0

    def _get_craft_failure_message(self, result):
        reasons = {
            "missing_ingredients": "Missing ingredients",
            "inventory_full": "Inventory full",
            "unknown_recipe": "Unknown recipe",
            "invalid_recipe": "Invalid recipe",
        }
        return reasons.get(result.get("reason"), "Cannot craft")

    def _short_text(self, text, max_length):
        text = str(text)
        if len(text) <= max_length:
            return text
        return text[: max_length - 1] + "."

    def _truncate_to_width(self, text, font, max_width):
        text = str(text or "")
        if max_width <= 0:
            return ""

        if font.size(text)[0] <= max_width:
            return text

        ellipsis = "..."
        if font.size(ellipsis)[0] > max_width:
            return ""

        while text and font.size(text + ellipsis)[0] > max_width:
            text = text[:-1]

        return text + ellipsis if text else ellipsis
