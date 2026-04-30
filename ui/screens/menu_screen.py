import pygame


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

        self.class_buttons = self._build_class_buttons()
        self.zone_buttons = self._build_zone_buttons()
        self.inventory_button = MenuButton((560, 54, 160, 52), "Inventaire")
        self.merchant_button = MenuButton((560, 116, 160, 52), "Merchant")
        self.crafting_button = MenuButton((560, 178, 160, 52), "Craft")

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
        y = 140
        for zone_key, zone_data in self.game.data.zones.items():
            subtitle = (
                f"Niveau {zone_data['unlock_level']} - "
                f"Difficulte x{zone_data['difficulty_multiplier']}"
            )
            buttons.append(
                (zone_key, MenuButton((80, y, 640, 80), zone_data["name"], subtitle))
            )
            y += 100
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

        if self.game.state == "zone_select":
            if self.inventory_button.is_clicked(pos):
                self.game.state = "inventory"
                return

            if self.merchant_button.is_clicked(pos):
                self.game.state = "merchant"
                return

            if self.crafting_button.is_clicked(pos):
                self.game.state = "crafting"
                return

            for zone_key, button in self.zone_buttons:
                if button.is_clicked(pos):
                    self.game.select_zone(zone_key)
                    return

    def draw(self, screen):
        screen.fill((18, 24, 30))

        if self.game.state == "class_select":
            self._draw_class_select(screen)
        elif self.game.state == "zone_select":
            self._draw_zone_select(screen)

    def _draw_class_select(self, screen):
        title = self.title_font.render("Choisis ta classe", True, (245, 245, 245))
        screen.blit(title, (80, 64))

        for _, button in self.class_buttons:
            button.draw(screen, self.option_font, self.body_font)

    def _draw_zone_select(self, screen):
        player_level = self.game.player["level"] if self.game.player else 1

        title = self.title_font.render("Choisis ta zone", True, (245, 245, 245))
        screen.blit(title, (80, 64))

        class_name = self.game.data.classes[self.game.selected_class]["name"]
        subtitle = self.body_font.render(
            f"{class_name} - Niveau {player_level}", True, (190, 200, 205)
        )
        screen.blit(subtitle, (82, 105))
        self.inventory_button.draw(screen, self.option_font, self.body_font)
        self.merchant_button.draw(screen, self.option_font, self.body_font)
        self.crafting_button.draw(screen, self.option_font, self.body_font)

        for zone_key, button in self.zone_buttons:
            zone = self.game.data.zones[zone_key]
            button.enabled = player_level >= zone["unlock_level"]
            button.draw(screen, self.option_font, self.body_font)
