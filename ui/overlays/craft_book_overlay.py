import pygame

try:
    from systems.crafting import (
        can_craft_recipe,
        count_individual_item,
        count_stackable_item,
    )
except ImportError:
    from systems.crafting import can_craft

    def can_craft_recipe(inventory, recipe):
        return can_craft(inventory, recipe)

    def count_stackable_item(inventory, item_id):
        if not isinstance(inventory, dict) or not isinstance(inventory.get("slots"), list):
            return 0
        total = 0
        for slot in inventory["slots"]:
            if isinstance(slot, dict) and slot.get("kind") == "stackable" and slot.get("item") == item_id:
                total += slot.get("quantity", 0)
        return total

    def count_individual_item(inventory, item_id):
        if not isinstance(inventory, dict) or not isinstance(inventory.get("slots"), list):
            return 0
        total = 0
        for slot in inventory["slots"]:
            if isinstance(slot, dict) and slot.get("kind") in {"individual", "unique"} and slot.get("item") == item_id:
                total += 1
        return total


OVERLAY_DIM = (0, 0, 0, 150)
PANEL_BG = (28, 25, 20)
PANEL_BG_SECONDARY = (34, 31, 25)
CARD_BG = (38, 36, 30)
CARD_BG_SELECTED = (48, 45, 36)
BORDER_NORMAL = (118, 92, 45)
BORDER_BRIGHT = (205, 170, 80)
BORDER_SELECTED = (238, 205, 110)
TEXT_PRIMARY = (238, 232, 205)
TEXT_SECONDARY = (190, 184, 160)
TEXT_MUTED = (130, 124, 105)
SUCCESS = (98, 190, 125)
WARNING = (218, 176, 72)
DANGER = (160, 80, 70)
DISABLED_BG = (42, 40, 36)
DISABLED_TEXT = (120, 116, 105)

FILTERS = ("All", "Ready", "Consumables", "Equipment", "Profession")


class CraftBookOverlay:
    def __init__(self, game):
        if not pygame.font.get_init():
            pygame.font.init()

        self.game = game
        self.opened = False
        self.selected_filter = "All"
        self.selected_recipe_id = None
        self.recipe_scroll_offset = 0
        self.title_font = pygame.font.Font(None, 38)
        self.header_font = pygame.font.Font(None, 27)
        self.body_font = pygame.font.Font(None, 22)
        self.small_font = pygame.font.Font(None, 18)
        self.panel_rect = pygame.Rect(0, 0, 0, 0)
        self.close_rect = pygame.Rect(0, 0, 0, 0)
        self.filter_rects = []
        self.list_rect = pygame.Rect(0, 0, 0, 0)
        self.detail_rect = pygame.Rect(0, 0, 0, 0)
        self.station_message_rect = pygame.Rect(0, 0, 0, 0)
        self.recipe_row_rects = []

    def open(self):
        self.opened = True
        self._select_first_filtered_recipe_if_needed(force=False)

    def close(self):
        self.opened = False

    def is_open(self):
        return self.opened

    def handle_event(self, event):
        if not self.opened:
            return False

        if event.type == pygame.KEYDOWN:
            if event.key in (pygame.K_ESCAPE, pygame.K_r):
                self.close()
            return True

        if event.type == pygame.MOUSEWHEEL:
            self._scroll_recipes(-event.y)
            return True

        if event.type != pygame.MOUSEBUTTONDOWN or event.button != 1:
            return False

        position = event.pos
        if self.panel_rect.width > 0 and not self.panel_rect.collidepoint(position):
            self.close()
            return True

        if self.close_rect.collidepoint(position):
            self.close()
            return True

        for filter_name, rect in self.filter_rects:
            if rect.collidepoint(position):
                self.selected_filter = filter_name
                self.recipe_scroll_offset = 0
                self._select_first_filtered_recipe_if_needed(force=True)
                return True

        for recipe_id, rect in self.recipe_row_rects:
            if rect.collidepoint(position):
                self.selected_recipe_id = recipe_id
                return True

        return True

    def draw(self, screen):
        if not self.opened:
            return

        self._draw_overlay_background(screen)
        self.panel_rect = self._get_panel_rect(screen)
        self._layout_rects()
        self._draw_panel(screen, self.panel_rect)
        self.close_rect = pygame.Rect(self.panel_rect.right - 48, self.panel_rect.y + 14, 30, 28)
        self._draw_button(screen, self.close_rect, "X")

        player = getattr(self.game, "player", None)
        if not isinstance(player, dict):
            self._draw_message_line(screen, "No player available.")
            return
        if not isinstance(self._get_inventory().get("slots"), list):
            self._draw_message_line(screen, "No inventory.")
            return
        if not self._get_recipes_data():
            self._draw_message_line(screen, "No recipes.")
            return

        self._select_first_filtered_recipe_if_needed(force=False)
        self._draw_recipe_list(screen)
        self._draw_recipe_detail(screen)
        self._draw_station_message(screen)

    def _draw_recipe_list(self, screen):
        self.recipe_row_rects = []
        self.filter_rects = []
        pygame.draw.rect(screen, PANEL_BG_SECONDARY, self.list_rect, border_radius=8)
        pygame.draw.rect(screen, BORDER_NORMAL, self.list_rect, 2, border_radius=8)

        self._draw_filters(screen)
        recipe_ids = self._get_filtered_recipe_ids()
        self._clamp_recipe_scroll_offset(recipe_ids)
        showing = self.small_font.render(f"Showing: {self.selected_filter} ({len(recipe_ids)})", True, TEXT_SECONDARY)
        screen.blit(showing, (self.list_rect.x + 14, self.list_rect.y + 76))

        if not recipe_ids:
            text = self.body_font.render("No recipes.", True, TEXT_MUTED)
            screen.blit(text, (self.list_rect.x + 14, self.list_rect.y + 108))
            return

        y = self.list_rect.y + 102
        row_height = 42
        visible_ids = recipe_ids[self.recipe_scroll_offset:]
        for recipe_id in visible_ids:
            if y + row_height > self.list_rect.bottom - 10:
                break
            recipe = self._get_recipes_data().get(recipe_id, {})
            rect = pygame.Rect(self.list_rect.x + 10, y, self.list_rect.width - 20, row_height - 6)
            self.recipe_row_rects.append((recipe_id, rect))
            self._draw_recipe_row(screen, rect, recipe_id, recipe)
            y += row_height

    def _draw_filters(self, screen):
        x = self.list_rect.x + 12
        y = self.list_rect.y + 12
        max_x = self.list_rect.right - 12
        for filter_name in FILTERS:
            width = max(54, self.small_font.size(filter_name)[0] + 18)
            if x + width > max_x:
                x = self.list_rect.x + 12
                y += 30
            rect = pygame.Rect(x, y, width, 24)
            self.filter_rects.append((filter_name, rect))
            self._draw_button(screen, rect, filter_name, active=filter_name == self.selected_filter, font=self.small_font)
            x += width + 6

    def _draw_recipe_row(self, screen, rect, recipe_id, recipe):
        selected = recipe_id == self.selected_recipe_id
        available = self._is_recipe_available(recipe)
        bg = CARD_BG_SELECTED if selected else CARD_BG
        border = BORDER_SELECTED if selected else SUCCESS if available else BORDER_NORMAL
        status_color = SUCCESS if available else DANGER
        pygame.draw.rect(screen, bg, rect, border_radius=6)
        pygame.draw.rect(screen, border, rect, 2 if selected or available else 1, border_radius=6)

        status = "READY" if available else "MISS"
        name = self._truncate_text(self._get_recipe_result_name(recipe), self.body_font, rect.width - 86)
        name_text = self.body_font.render(name, True, TEXT_PRIMARY if available else TEXT_SECONDARY)
        screen.blit(name_text, (rect.x + 10, rect.y + 5))
        status_text = self.small_font.render(status, True, status_color)
        screen.blit(status_text, (rect.right - status_text.get_width() - 8, rect.y + 7))

        summary = "Can craft at station" if available else self._get_recipe_missing_summary(recipe)
        summary_color = SUCCESS if available else DANGER
        summary_text = self.small_font.render(self._truncate_text(summary, self.small_font, rect.width - 20), True, summary_color)
        screen.blit(summary_text, (rect.x + 10, rect.y + 23))

    def _draw_recipe_detail(self, screen):
        pygame.draw.rect(screen, PANEL_BG_SECONDARY, self.detail_rect, border_radius=8)
        pygame.draw.rect(screen, BORDER_NORMAL, self.detail_rect, 2, border_radius=8)
        recipe = self._get_selected_recipe()
        if not recipe:
            text = self.body_font.render("Select a recipe.", True, TEXT_MUTED)
            screen.blit(text, (self.detail_rect.x + 16, self.detail_rect.y + 18))
            return

        x = self.detail_rect.x + 16
        y = self.detail_rect.y + 14
        max_width = self.detail_rect.width - 32
        available = self._is_recipe_available(recipe)
        name = self._get_recipe_result_name(recipe)
        title = self.header_font.render(self._truncate_text(name, self.header_font, max_width), True, TEXT_PRIMARY)
        screen.blit(title, (x, y))
        y += 30

        status = "Ready at crafting station" if available else "Missing ingredients"
        status_color = SUCCESS if available else DANGER
        screen.blit(self.body_font.render(status, True, status_color), (x, y))
        y += 30

        y = self._draw_ingredients(screen, recipe, x, y, max_width)
        y += 8
        y = self._draw_result(screen, recipe, x, y, max_width)
        y += 8
        self._draw_result_stats(screen, recipe, x, y, max_width)

    def _draw_ingredients(self, screen, recipe, x, y, max_width):
        title = self.body_font.render("Ingredients", True, TEXT_PRIMARY)
        screen.blit(title, (x, y))
        y += 24
        ingredients = recipe.get("ingredients", []) if isinstance(recipe, dict) else []
        if not isinstance(ingredients, list) or not ingredients:
            text = self.small_font.render("No ingredients.", True, TEXT_MUTED)
            screen.blit(text, (x + 10, y))
            return y + 20

        for ingredient in ingredients[:8]:
            if not isinstance(ingredient, dict):
                continue
            item_name = self._get_item_name(ingredient.get("item"))
            required = ingredient.get("quantity", 0)
            owned = self._count_owned_ingredient(ingredient)
            has_item = isinstance(required, int) and required > 0 and owned >= required
            marker = "OK" if has_item else "NO"
            line = f"{marker} {item_name}: {owned} / {required}"
            color = SUCCESS if has_item else DANGER
            text = self.small_font.render(self._truncate_text(line, self.small_font, max_width - 10), True, color)
            screen.blit(text, (x + 10, y))
            y += 18
        return y

    def _draw_result(self, screen, recipe, x, y, max_width):
        result = recipe.get("result", {}) if isinstance(recipe, dict) else {}
        if not isinstance(result, dict):
            result = {}
        title = self.body_font.render("Result", True, TEXT_PRIMARY)
        screen.blit(title, (x, y))
        y += 24
        item_id = self._get_recipe_result_item_id(recipe)
        quantity = result.get("quantity", 1)
        lines = [
            f"Name: {self._get_recipe_result_name(recipe)}",
            f"Quantity: {quantity}",
            f"Type: {self._get_item_type_label(item_id)}",
            f"Category: {self._get_item_category_label(item_id)}",
        ]
        for line in lines:
            text = self.small_font.render(self._truncate_text(line, self.small_font, max_width), True, TEXT_SECONDARY)
            screen.blit(text, (x + 10, y))
            y += 18
        return y

    def _draw_result_stats(self, screen, recipe, x, y, max_width):
        result_data = self._get_recipe_result_data(recipe)
        stats = result_data.get("stats", {}) if isinstance(result_data, dict) else {}
        if not isinstance(stats, dict) or not stats:
            return
        title = self.body_font.render("Stats", True, TEXT_PRIMARY)
        screen.blit(title, (x, y))
        y += 23
        bottom = self.detail_rect.bottom - 10
        for line in self._format_item_stats(stats)[:8]:
            if y + 18 > bottom:
                break
            text = self.small_font.render(self._truncate_text(line, self.small_font, max_width), True, TEXT_SECONDARY)
            screen.blit(text, (x + 10, y))
            y += 18

    def _get_recipes_data(self):
        data = getattr(self.game, "data", None)
        recipes = getattr(data, "recipes", {}) if data is not None else {}
        return recipes if isinstance(recipes, dict) else {}

    def _get_items_data(self):
        data = getattr(self.game, "data", None)
        items = getattr(data, "items", {}) if data is not None else {}
        return items if isinstance(items, dict) else {}

    def _get_inventory(self):
        player = getattr(self.game, "player", None)
        if not isinstance(player, dict):
            return {}
        inventory = player.get("inventory", {})
        return inventory if isinstance(inventory, dict) else {}

    def _get_filtered_recipe_ids(self):
        return [
            recipe_id
            for recipe_id, recipe in self._get_recipes_data().items()
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

    def _recipe_uses_gathered_resource(self, recipe):
        ingredients = recipe.get("ingredients", []) if isinstance(recipe, dict) else []
        if not isinstance(ingredients, list):
            return False
        for ingredient in ingredients:
            if not isinstance(ingredient, dict):
                continue
            if self._get_item_data(ingredient.get("item")).get("economic_source") == "gathered_resource":
                return True
        return False

    def _is_recipe_available(self, recipe):
        inventory = self._get_inventory()
        if not isinstance(recipe, dict) or not isinstance(inventory.get("slots"), list):
            return False
        return can_craft_recipe(inventory, recipe)

    def _count_owned_ingredient(self, ingredient):
        if not isinstance(ingredient, dict):
            return 0
        item_id = ingredient.get("item")
        inventory = self._get_inventory()
        if ingredient.get("kind") == "stackable":
            return count_stackable_item(inventory, item_id)
        if ingredient.get("kind") in {"individual", "unique"}:
            return count_individual_item(inventory, item_id)
        return 0

    def _get_recipe_missing_summary(self, recipe):
        ingredients = recipe.get("ingredients", []) if isinstance(recipe, dict) else []
        if not isinstance(ingredients, list):
            return "Need: ingredients"
        missing = []
        for ingredient in ingredients:
            if not isinstance(ingredient, dict):
                continue
            required = ingredient.get("quantity", 0)
            owned = self._count_owned_ingredient(ingredient)
            if not isinstance(required, int) or owned < required:
                missing.append((ingredient, owned, required))
        if not missing:
            return "Can craft at station"
        ingredient, owned, required = missing[0]
        summary = f"Need: {self._get_item_name(ingredient.get('item'))} {owned}/{required}"
        if len(missing) > 1:
            summary += f" +{len(missing) - 1}"
        return summary

    def _get_selected_recipe(self):
        recipe = self._get_recipes_data().get(self.selected_recipe_id, {}) if self.selected_recipe_id else {}
        return recipe if isinstance(recipe, dict) else {}

    def _get_recipe_result_item_id(self, recipe):
        result = recipe.get("result", {}) if isinstance(recipe, dict) else {}
        return result.get("item") if isinstance(result, dict) else None

    def _get_recipe_result_name(self, recipe):
        item_id = self._get_recipe_result_item_id(recipe)
        if item_id:
            return self._get_item_name(item_id)
        if self.selected_recipe_id:
            recipe = self._get_recipes_data().get(self.selected_recipe_id, {})
            if isinstance(recipe, dict) and recipe.get("name"):
                return str(recipe["name"])
            return str(self.selected_recipe_id).replace("_", " ").title()
        return "Unknown"

    def _get_recipe_result_data(self, recipe):
        return self._get_item_data(self._get_recipe_result_item_id(recipe))

    def _get_item_name(self, item_id):
        item_data = self._get_item_data(item_id)
        return item_data.get("name", item_id or "Unknown")

    def _get_item_data(self, item_id):
        items = self._get_items_data()
        item_data = items.get(item_id, {}) if item_id else {}
        return item_data if isinstance(item_data, dict) else {}

    def _get_recipe_result_type(self, recipe):
        return self._get_item_data(self._get_recipe_result_item_id(recipe)).get("type", "unknown")

    def _get_item_type_label(self, item_id):
        return str(self._get_item_data(item_id).get("type", "unknown")).replace("_", " ").title()

    def _get_item_category_label(self, item_id):
        return str(self._get_item_data(item_id).get("category", "unknown")).replace("_", " ").title()

    def _format_item_stats(self, stats):
        lines = []
        if not isinstance(stats, dict):
            return lines
        for stat_key, value in stats.items():
            lines.append(f"{self._format_stat_label(stat_key)}: {self._format_stat_value(stat_key, value)}")
        return lines

    def _format_stat_label(self, stat_key):
        labels = {
            "attack": "Attack",
            "defense": "Defense",
            "hp": "HP",
            "max_hp": "Max HP",
            "strength": "Strength",
            "force": "Strength",
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
        return labels.get(str(stat_key), str(stat_key).replace("_", " ").title())

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

    def _scroll_recipes(self, direction):
        recipe_ids = self._get_filtered_recipe_ids()
        max_visible = self._get_max_visible_recipe_rows()
        max_offset = max(0, len(recipe_ids) - max_visible)
        self.recipe_scroll_offset = max(0, min(max_offset, self.recipe_scroll_offset + direction))

    def _clamp_recipe_scroll_offset(self, recipe_ids):
        max_visible = self._get_max_visible_recipe_rows()
        max_offset = max(0, len(recipe_ids) - max_visible)
        self.recipe_scroll_offset = max(0, min(max_offset, self.recipe_scroll_offset))

    def _get_max_visible_recipe_rows(self):
        if self.list_rect.height <= 0:
            return 8
        return max(1, (self.list_rect.bottom - (self.list_rect.y + 102) - 10) // 42)

    def _select_first_filtered_recipe_if_needed(self, force=False):
        recipe_ids = self._get_filtered_recipe_ids()
        self._clamp_recipe_scroll_offset(recipe_ids)
        if force or self.selected_recipe_id not in recipe_ids:
            self.selected_recipe_id = recipe_ids[0] if recipe_ids else None

    def _get_panel_rect(self, screen):
        width, height = screen.get_size()
        panel_width = min(width - 28, max(760, int(width * 0.9)))
        panel_height = min(height - 70, max(500, int(height * 0.82)))
        panel_width = max(620, min(panel_width, width - 20))
        panel_height = max(460, min(panel_height, height - 62))
        return pygame.Rect((width - panel_width) // 2, 24, panel_width, panel_height)

    def _layout_rects(self):
        content_top = self.panel_rect.y + 78
        bottom = self.panel_rect.bottom - 22
        gap = 16
        content_width = self.panel_rect.width - 36
        list_width = min(340, max(286, int(content_width * 0.42)))
        self.list_rect = pygame.Rect(self.panel_rect.x + 18, content_top, list_width, bottom - content_top)
        self.detail_rect = pygame.Rect(
            self.list_rect.right + gap,
            content_top,
            content_width - list_width - gap,
            bottom - content_top - 42,
        )
        self.station_message_rect = pygame.Rect(self.detail_rect.x, self.panel_rect.bottom - 48, self.detail_rect.width, 24)

    def _draw_overlay_background(self, screen):
        overlay = pygame.Surface(screen.get_size(), pygame.SRCALPHA)
        overlay.fill(OVERLAY_DIM)
        screen.blit(overlay, (0, 0))

    def _draw_panel(self, screen, rect):
        pygame.draw.rect(screen, PANEL_BG, rect, border_radius=10)
        pygame.draw.rect(screen, BORDER_BRIGHT, rect, 2, border_radius=10)
        pygame.draw.rect(screen, BORDER_NORMAL, rect.inflate(-8, -8), 1, border_radius=8)
        title = self.title_font.render("Craft Book", True, TEXT_PRIMARY)
        screen.blit(title, (rect.x + 22, rect.y + 16))
        subtitle = self.small_font.render("Consult known recipes", True, TEXT_SECONDARY)
        screen.blit(subtitle, (rect.x + 24, rect.y + 52))

    def _draw_button(self, screen, rect, label, active=False, enabled=True, warm=False, font=None):
        font = font or (self.small_font if rect.height <= 26 else self.body_font)
        if warm and enabled:
            bg, border, color = (116, 82, 34), BORDER_SELECTED, TEXT_PRIMARY
        else:
            bg = CARD_BG_SELECTED if active else CARD_BG if enabled else DISABLED_BG
            border = BORDER_SELECTED if active else BORDER_NORMAL if enabled else DISABLED_TEXT
            color = TEXT_PRIMARY if enabled else DISABLED_TEXT
        pygame.draw.rect(screen, bg, rect, border_radius=5)
        pygame.draw.rect(screen, border, rect, 2 if active or warm else 1, border_radius=5)
        text = font.render(self._truncate_text(label, font, rect.width - 8), True, color)
        screen.blit(text, text.get_rect(center=rect.center))

    def _draw_message_line(self, screen, message):
        text = self.body_font.render(message, True, TEXT_SECONDARY)
        screen.blit(text, (self.panel_rect.x + 24, self.panel_rect.y + 82))

    def _draw_station_message(self, screen):
        message = "Use a crafting station to craft this recipe."
        text = self.small_font.render(self._truncate_text(message, self.small_font, self.station_message_rect.width), True, TEXT_SECONDARY)
        screen.blit(text, (self.station_message_rect.x, self.station_message_rect.y + 4))

    def _truncate_text(self, text, font, max_width):
        text = str(text or "")
        if max_width <= 0:
            return ""
        if font.size(text)[0] <= max_width:
            return text
        ellipsis = "..."
        while text and font.size(text + ellipsis)[0] > max_width:
            text = text[:-1]
        return text + ellipsis if text else ellipsis

    def _wrap_text(self, text, font, max_width, max_lines):
        words = str(text or "").split()
        lines = []
        line = ""
        for word in words:
            candidate = word if not line else f"{line} {word}"
            if font.size(candidate)[0] <= max_width:
                line = candidate
                continue
            if line:
                lines.append(line)
            line = word
            if len(lines) >= max_lines:
                break
        if line and len(lines) < max_lines:
            lines.append(line)
        if len(lines) == max_lines and words:
            lines[-1] = self._truncate_text(lines[-1], font, max_width)
        return lines
