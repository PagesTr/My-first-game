import pygame

try:
    from systems.crafting import can_craft_recipe
except ImportError:
    from systems.crafting import can_craft as can_craft_recipe

from systems.professions import get_profession_mastery
from ui.assets import draw_background, load_image


class MenuButton:
    def __init__(self, rect, title, subtitle="", enabled=True):
        self.rect = pygame.Rect(rect)
        self.title = title
        self.subtitle = subtitle
        self.enabled = enabled

    def draw(self, screen, title_font, body_font):
        bg = (58, 68, 78) if self.enabled else (45, 45, 50)
        border = (210, 220, 225) if self.enabled else (95, 95, 100)
        text_color = (245, 245, 245) if self.enabled else (145, 145, 150)
        sub_color = (190, 200, 205) if self.enabled else (120, 120, 125)

        pygame.draw.rect(screen, bg, self.rect, border_radius=6)
        pygame.draw.rect(screen, border, self.rect, 2, border_radius=6)

        title = title_font.render(self.title, True, text_color)
        screen.blit(title, (self.rect.x + 16, self.rect.y + 14))

        if self.subtitle:
            subtitle = body_font.render(self.subtitle, True, sub_color)
            screen.blit(subtitle, (self.rect.x + 16, self.rect.y + 48))

    def is_clicked(self, pos):
        return self.enabled and self.rect.collidepoint(pos)


class MenuScreen:
    def __init__(self, game):
        self.game = game
        self.title_font = pygame.font.Font(None, 46)
        self.option_font = pygame.font.Font(None, 30)
        self.body_font = pygame.font.Font(None, 24)
        self.town_background = load_image("assets/backgrounds/town.png", (800, 600))
        self.zone_background = load_image(
            "assets/backgrounds/zone_select.png", (800, 600)
        )
        self.class_background = load_image(
            "assets/backgrounds/class_select.png", (800, 600)
        )

        self.class_buttons = self._build_class_buttons()
        self.zone_buttons = self._build_zone_buttons()
        self.expedition_button = MenuButton(
            (80, 150, 300, 72),
            "Expedition",
            "Choose a combat zone",
        )
        self.inventory_button = MenuButton(
            (80, 238, 300, 72),
            "Inventory",
            "Manage gear and items",
        )
        self.merchant_button = MenuButton(
            (80, 326, 300, 72),
            "Merchant",
            "Sell items",
        )
        self.crafting_button = MenuButton(
            (80, 414, 300, 72),
            "Craft",
            "Use resources",
        )
        self.skills_button = MenuButton(
            (80, 502, 300, 72),
            "Skills",
            "Learn and equip skills",
        )
        self.mailbox_button = MenuButton(
            (400, 414, 300, 72),
            "Mailbox",
            "View combat reports",
        )
        self.zone_back_button = MenuButton((560, 54, 160, 52), "Back")
        self.start_expedition_button = MenuButton(
            (490, 238, 220, 52),
            "Start expedition",
            "Combat",
        )
        self.gather_action_buttons = []

    def _build_class_buttons(self):
        buttons = []
        y = 140
        for class_key, class_data in self.game.data.classes.items():
            stats = class_data["base_stats"]
            subtitle = (
                f"STR {stats.get('strength', 0)}  "
                f"DEX {stats.get('dexterity', 0)}  "
                f"INT {stats.get('intelligence', 0)}  "
                f"VIT {stats.get('vitality', 0)}  "
                f"WIS {stats.get('wisdom', 0)}  "
                f"LUCK {stats.get('luck', 0)}"
            )
            buttons.append(
                (class_key, MenuButton((80, y, 640, 80), class_data["name"], subtitle))
            )
            y += 100
        return buttons

    def _build_zone_buttons(self):
        buttons = []
        y = 128
        for zone_key, zone_data in self.game.data.zones.items():
            subtitle = (
                f"Niveau {zone_data['unlock_level']} - "
                f"Difficulte x{zone_data['difficulty_multiplier']}"
            )
            buttons.append(
                (zone_key, MenuButton((80, y, 640, 64), zone_data["name"], subtitle))
            )
            y += 72
        return buttons

    def handle_event(self, event):
        if event.type != pygame.MOUSEBUTTONDOWN:
            return

        pos = event.pos
        if self.game.state == "class_select":
            for class_key, button in self.class_buttons:
                if button.is_clicked(pos):
                    self.game.select_class(class_key)
                    self.zone_buttons = self._build_zone_buttons()
                    return

        if self.game.state == "town":
            if self.expedition_button.is_clicked(pos):
                self.game.state = "zone_select"
                return

            if self.inventory_button.is_clicked(pos):
                self.game.state = "inventory"
                return

            if self.merchant_button.is_clicked(pos):
                self.game.state = "merchant"
                return

            if self.crafting_button.is_clicked(pos):
                self.game.state = "crafting"
                return

            if self.skills_button.is_clicked(pos):
                self.game.state = "skills"
                return

            if self.mailbox_button.is_clicked(pos):
                self.game.state = "mailbox"
                return

        if self.game.state == "zone_select":
            if self.zone_back_button.is_clicked(pos):
                self.game.state = "town"
                return

            for zone_key, button in self.zone_buttons:
                if button.is_clicked(pos):
                    self.game.select_zone_for_actions(zone_key)
            return

        if self.game.state == "zone_actions":
            if self._handle_zone_actions_click(pos):
                return

            for zone_key, button in self.zone_buttons:
                if button.is_clicked(pos):
                    self.game.select_zone_for_actions(zone_key)
                    return

    def draw(self, screen):
        if self.game.state == "class_select":
            draw_background(screen, self.class_background, (18, 24, 30))
            self._draw_class_select(screen)
        elif self.game.state == "town":
            draw_background(screen, self.town_background, (18, 24, 30))
            self._draw_town(screen)
        elif self.game.state in ("zone_select", "zone_actions"):
            draw_background(screen, self.zone_background, (18, 24, 30))
            self._draw_zone_select(screen)

    def _draw_class_select(self, screen):
        title = self.title_font.render("Choisis ta classe", True, (245, 245, 245))
        screen.blit(title, (80, 64))

        for _, button in self.class_buttons:
            button.draw(screen, self.option_font, self.body_font)

    def _draw_town(self, screen):
        player_level = self.game.player["level"] if self.game.player else 1

        title = self.title_font.render("Town", True, (245, 245, 245))
        screen.blit(title, (80, 64))

        if self.game.selected_class:
            class_name = self.game.data.classes[self.game.selected_class]["name"]
        else:
            class_name = "Adventurer"
        subtitle = self.body_font.render(
            f"{class_name} - Level {player_level}", True, (190, 200, 205)
        )
        screen.blit(subtitle, (82, 105))

        self.expedition_button.draw(screen, self.option_font, self.body_font)
        self.inventory_button.draw(screen, self.option_font, self.body_font)
        self.merchant_button.draw(screen, self.option_font, self.body_font)
        has_available_recipe = self._has_available_crafting_recipe()
        if has_available_recipe:
            self.crafting_button.subtitle = "Recipes available"
        else:
            self.crafting_button.subtitle = "Use resources"
        self.crafting_button.draw(screen, self.option_font, self.body_font)
        if has_available_recipe:
            self._draw_crafting_ready_badge(screen)
        self.skills_button.draw(screen, self.option_font, self.body_font)
        self.mailbox_button.draw(screen, self.option_font, self.body_font)
        self._draw_town_player_panel(screen)

    def _has_available_crafting_recipe(self):
        if not self.game.player:
            return False

        recipes = getattr(self.game.data, "recipes", {}) or {}
        if not isinstance(recipes, dict):
            return False

        inventory = self.game.player.get("inventory")
        for recipe in recipes.values():
            if not isinstance(recipe, dict):
                continue
            if can_craft_recipe(inventory, recipe):
                return True
        return False

    def _draw_crafting_ready_badge(self, screen):
        badge_rect = pygame.Rect(
            self.crafting_button.rect.right - 76,
            self.crafting_button.rect.y + 14,
            58,
            24,
        )
        pygame.draw.rect(screen, (78, 104, 50), badge_rect, border_radius=10)
        pygame.draw.rect(screen, (220, 220, 120), badge_rect, 2, border_radius=10)

        label = self.body_font.render("Ready", True, (245, 245, 245))
        screen.blit(label, (badge_rect.x + 8, badge_rect.y + 3))

    def _draw_town_player_panel(self, screen):
        rect = pygame.Rect(470, 150, 250, 220)
        pygame.draw.rect(screen, (35, 40, 48), rect, border_radius=6)
        pygame.draw.rect(screen, (120, 130, 140), rect, 2, border_radius=6)

        title = self.option_font.render("Player", True, (245, 245, 245))
        screen.blit(title, (rect.x + 18, rect.y + 18))

        player = self.game.player or {}
        if self.game.selected_class:
            class_name = self.game.data.classes[self.game.selected_class]["name"]
        else:
            class_name = "Adventurer"

        lines = [
            f"Class: {class_name}",
            f"Level: {player.get('level', 1)}",
            f"HP: {player.get('current_hp', 0)} / {player.get('max_hp', 0)}",
            f"Gold: {player.get('gold', 0)}",
        ]

        y = rect.y + 62
        for line in lines:
            text = self.body_font.render(line, True, (190, 200, 205))
            screen.blit(text, (rect.x + 18, y))
            y += 34

    def _draw_zone_select(self, screen):
        player_level = self.game.player["level"] if self.game.player else 1
        has_actions_panel = self.game.state == "zone_actions"

        title = self.title_font.render("Choisis ta zone", True, (245, 245, 245))
        screen.blit(title, (80, 64))

        if self.game.selected_class:
            class_name = self.game.data.classes[self.game.selected_class]["name"]
        else:
            class_name = "Adventurer"
        subtitle = self.body_font.render(
            f"{class_name} - Niveau {player_level}", True, (190, 200, 205)
        )
        screen.blit(subtitle, (82, 105))
        self.zone_back_button.draw(screen, self.option_font, self.body_font)

        for zone_key, button in self.zone_buttons:
            zone = self.game.data.zones[zone_key]
            button.enabled = player_level >= zone["unlock_level"]
            if has_actions_panel:
                button.rect.x = 60
                button.rect.w = 380
            else:
                button.rect.x = 80
                button.rect.w = 640
            button.draw(screen, self.option_font, self.body_font)
            if has_actions_panel and zone_key == self.game.selected_zone:
                pygame.draw.rect(screen, (230, 210, 110), button.rect, 3, border_radius=6)

        if has_actions_panel:
            self._draw_zone_actions_panel(screen)

    def _draw_zone_actions_panel(self, screen):
        panel = pygame.Rect(470, 128, 260, 410)
        pygame.draw.rect(screen, (35, 40, 48), panel, border_radius=6)
        pygame.draw.rect(screen, (120, 130, 140), panel, 2, border_radius=6)

        zone_key = self.game.selected_zone
        zone = self.game.data.zones.get(zone_key, {}) if zone_key else {}
        zone_name = zone.get("name", "No zone selected")
        zone_description = zone.get("description", "")

        title = self.option_font.render(zone_name, True, (245, 245, 245))
        screen.blit(title, (panel.x + 16, panel.y + 16))

        if zone_description:
            description = self.body_font.render(zone_description[:34], True, (190, 200, 205))
            screen.blit(description, (panel.x + 16, panel.y + 48))

        self.start_expedition_button.rect = pygame.Rect(panel.x + 20, panel.y + 92, 220, 52)
        self.start_expedition_button.enabled = zone_key in self.game.data.zones
        self.start_expedition_button.draw(screen, self.body_font, self.body_font)

        gathering_title = self.body_font.render("Gathering", True, (245, 245, 245))
        screen.blit(gathering_title, (panel.x + 20, panel.y + 158))

        self.gather_action_buttons = []
        available_professions = self.game.get_available_gathering_professions(zone_key)
        y = panel.y + 188
        if available_professions:
            for profession_id, node_data in available_professions.items():
                profession_name = self._get_profession_name(profession_id)
                node_name = node_data.get("name", "Gathering node")
                mastery = 0
                if self.game.player:
                    mastery = get_profession_mastery(
                        self.game.player,
                        profession_id,
                        self.game.data.professions,
                    )
                button = MenuButton(
                    (panel.x + 20, y, 220, 48),
                    profession_name,
                    f"{node_name} - Mastery: {mastery}",
                )
                self.gather_action_buttons.append((profession_id, button))
                button.draw(screen, self.body_font, self.body_font)
                y += 56
        else:
            empty_text = self.body_font.render("No gathering node", True, (145, 145, 150))
            screen.blit(empty_text, (panel.x + 20, y))
            y += 34

        result = self.game.last_gathering_result
        if isinstance(result, dict):
            result_zone = result.get("zone_id", zone_key)
            if result_zone == zone_key:
                self._draw_gathering_result(screen, result, panel.x + 20, max(y + 8, panel.y + 310))

    def _draw_gathering_result(self, screen, result, x, y):
        for line in self._format_gathering_result(result):
            text = self.body_font.render(line, True, (210, 220, 205))
            screen.blit(text, (x, y))
            y += 22

    def _handle_zone_actions_click(self, pos):
        if self.zone_back_button.is_clicked(pos):
            self.game.state = "town"
            return True

        if self.start_expedition_button.is_clicked(pos):
            if self.game.selected_zone:
                self.game.select_zone(self.game.selected_zone)
            return True

        for profession_id, button in self.gather_action_buttons:
            if button.is_clicked(pos):
                self.game.gather_in_zone(self.game.selected_zone, profession_id)
                return True
        return False

    def _format_gathering_result(self, result):
        if result.get("gathered") is not True:
            return [self._get_gathering_failure_message(result.get("reason"))]

        lines = ["Gathered:"]
        for reward in result.get("rewards", []):
            item_name = self._get_item_name(reward.get("item"))
            quantity = reward.get("quantity", 1)
            lines.append(f"+{quantity} {item_name}")

        profession_id = result.get("profession_id")
        profession_name = self._get_profession_name(profession_id)
        xp_gain = result.get("profession_xp", 0)
        if xp_gain:
            lines.append(f"+{xp_gain} {profession_name} XP")
        if result.get("leveled_up"):
            lines.append("Level up!")
        return lines[:6]

    def _get_item_name(self, item_id):
        item_data = self.game.data.items.get(item_id, {})
        return item_data.get("name", item_id or "Unknown item")

    def _get_profession_name(self, profession_id):
        profession_data = self.game.data.professions.get(profession_id, {})
        return profession_data.get("name", profession_id or "Unknown profession")

    def _get_gathering_failure_message(self, reason):
        messages = {
            "unknown_node": "No gathering node",
            "inventory_full": "Inventory full",
            "invalid_zone": "Invalid zone",
            "locked_zone": "Zone locked",
        }
        return messages.get(reason, "Gathering failed")
