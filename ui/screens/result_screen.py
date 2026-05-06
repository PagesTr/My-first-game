import pygame


PALETTE = {
    "sky_top": (18, 24, 32),
    "sky_bottom": (20, 42, 35),
    "forest_back": (18, 46, 37),
    "forest_front": (12, 28, 24),
    "ground": (17, 20, 22),
    "ground_light": (36, 41, 34),
    "panel": (37, 45, 54),
    "panel_dark": (27, 34, 42),
    "panel_light": (64, 73, 78),
    "border": (92, 82, 58),
    "border_light": (192, 172, 105),
    "text": (238, 232, 214),
    "muted": (174, 184, 174),
    "gold": (228, 188, 86),
    "xp": (112, 146, 205),
    "victory": (105, 198, 117),
    "defeat": (194, 82, 76),
    "level_up": (120, 217, 138),
    "button": (42, 58, 54),
    "button_border": (192, 172, 105),
    "shadow": (8, 10, 13),
}


class Button:
    def __init__(self, rect, text):
        self.rect = pygame.Rect(rect)
        self.text = text

    def draw(self, screen, font):
        pygame.draw.rect(screen, PALETTE["shadow"], self.rect.move(4, 4))
        pygame.draw.rect(screen, PALETTE["button"], self.rect)
        pygame.draw.rect(screen, PALETTE["button_border"], self.rect, 3)
        pygame.draw.rect(screen, PALETTE["panel_light"], self.rect.inflate(-10, -10), 1)

        label = font.render(self.text, True, PALETTE["text"])
        label_rect = label.get_rect(center=self.rect.center)
        screen.blit(label, label_rect)

    def is_clicked(self, pos):
        return self.rect.collidepoint(pos)


class ResultScreen:
    def __init__(self, game):
        self.game = game
        self.title_font = pygame.font.Font(None, 58)
        self.header_font = pygame.font.Font(None, 34)
        self.font = pygame.font.Font(None, 28)
        self.small_font = pygame.font.Font(None, 22)
        self.continue_btn = Button((300, 530, 200, 50), "Continuer")

    def handle_event(self, event):
        if event.type == pygame.MOUSEBUTTONDOWN:
            if self.continue_btn.is_clicked(event.pos):
                self.game.continue_after_combat_result()

    def draw(self, screen):
        self._draw_background(screen)

        combat = self.game.combat
        victory = combat is not None and combat.winner == "player"
        title_text = "Victoire !" if victory else "Défaite..."
        title_color = PALETTE["victory"] if victory else PALETTE["defeat"]

        result = self.game.last_combat_result or {}
        exp_gained = result.get("exp_gained", 0)
        gold_gained = result.get("gold_gained", 0)
        drops = result.get("drops", [])
        current_level = self.game.player.get("level", 1) if self.game.player else 1

        self._draw_title(screen, title_text, title_color)

        summary_rect = pygame.Rect(64, 138, 322, 318)
        loot_rect = pygame.Rect(414, 138, 322, 318)
        self._draw_panel(screen, summary_rect, "Résumé")
        self._draw_panel(screen, loot_rect, "Butin")

        y = summary_rect.y + 66
        y = self._draw_summary_line(screen, "XP gagnée", exp_gained, y, PALETTE["xp"])
        y = self._draw_summary_line(
            screen, "Gold gagné", gold_gained, y, PALETTE["gold"]
        )
        y = self._draw_summary_line(screen, "Niveau actuel", current_level, y)

        if result.get("leveled_up", False):
            y += 10
            y = self._draw_summary_line(
                screen, "Level up", "Oui", y, PALETTE["level_up"]
            )
            self._draw_summary_line(
                screen,
                "Nouveau niveau",
                result.get("new_level", current_level),
                y,
                PALETTE["level_up"],
            )

        self._draw_loot_section(screen, loot_rect, drops)
        self._draw_combat_report_mail(screen, result)
        self._draw_button(screen, self.continue_btn)

    def _draw_background(self, screen):
        for y in range(0, 600, 4):
            blend = y / 600
            color = (
                int(
                    PALETTE["sky_top"][0] * (1 - blend)
                    + PALETTE["sky_bottom"][0] * blend
                ),
                int(
                    PALETTE["sky_top"][1] * (1 - blend)
                    + PALETTE["sky_bottom"][1] * blend
                ),
                int(
                    PALETTE["sky_top"][2] * (1 - blend)
                    + PALETTE["sky_bottom"][2] * blend
                ),
            )
            pygame.draw.rect(screen, color, (0, y, 800, 4))

        moon_color = (216, 211, 172)
        pygame.draw.rect(screen, moon_color, (620, 48, 44, 44))
        pygame.draw.rect(screen, PALETTE["sky_top"], (610, 42, 22, 54))

        back_points = [(0, 354), (70, 286), (140, 354)]
        for x in range(-40, 840, 110):
            points = [(px + x, py) for px, py in back_points]
            pygame.draw.polygon(screen, PALETTE["forest_back"], points)
            pygame.draw.rect(screen, PALETTE["forest_back"], (x + 54, 320, 30, 96))

        front_points = [(0, 420), (52, 318), (104, 420)]
        for x in range(-30, 850, 86):
            points = [(px + x, py) for px, py in front_points]
            pygame.draw.polygon(screen, PALETTE["forest_front"], points)
            pygame.draw.rect(screen, PALETTE["forest_front"], (x + 43, 374, 18, 86))

        pygame.draw.rect(screen, PALETTE["ground"], (0, 430, 800, 170))
        pygame.draw.rect(screen, PALETTE["ground_light"], (0, 430, 800, 4))
        for x in range(0, 800, 24):
            pygame.draw.rect(screen, (12, 15, 15), (x, 468 + (x % 48), 16, 4))

    def _draw_title(self, screen, title_text, title_color):
        banner_rect = pygame.Rect(250, 36, 300, 72)
        pygame.draw.rect(screen, PALETTE["shadow"], banner_rect.move(4, 4))
        pygame.draw.rect(screen, PALETTE["panel_dark"], banner_rect)
        pygame.draw.rect(screen, PALETTE["border_light"], banner_rect, 3)

        shadow = self.title_font.render(title_text, True, PALETTE["shadow"])
        title = self.title_font.render(title_text, True, title_color)
        title_rect = title.get_rect(center=(400, 72))
        shadow_rect = shadow.get_rect(center=(403, 75))
        screen.blit(shadow, shadow_rect)
        screen.blit(title, title_rect)

    def _draw_panel(self, screen, rect, title):
        pygame.draw.rect(screen, PALETTE["shadow"], rect.move(5, 5))
        pygame.draw.rect(screen, PALETTE["panel"], rect)
        pygame.draw.rect(screen, PALETTE["border"], rect, 3)
        pygame.draw.rect(screen, PALETTE["panel_light"], rect.inflate(-14, -14), 1)
        pygame.draw.line(
            screen,
            PALETTE["border_light"],
            (rect.x + 10, rect.y + 10),
            (rect.right - 10, rect.y + 10),
            2,
        )

        title_bg = pygame.Rect(rect.x + 18, rect.y + 14, rect.width - 36, 34)
        pygame.draw.rect(screen, PALETTE["panel_dark"], title_bg)
        pygame.draw.rect(screen, PALETTE["border_light"], title_bg, 2)
        title_text = self.header_font.render(title, True, PALETTE["text"])
        screen.blit(title_text, (title_bg.x + 12, title_bg.y + 5))

    def _draw_button(self, screen, button):
        pygame.draw.rect(screen, PALETTE["shadow"], button.rect.move(4, 4))
        pygame.draw.rect(screen, PALETTE["button"], button.rect)
        pygame.draw.rect(screen, PALETTE["button_border"], button.rect, 3)
        pygame.draw.rect(
            screen, PALETTE["panel_light"], button.rect.inflate(-10, -10), 1
        )

        label = self.font.render(button.text, True, PALETTE["text"])
        label_rect = label.get_rect(center=button.rect.center)
        screen.blit(label, label_rect)

    def _draw_summary_line(self, screen, label, value, y, value_color=None):
        row_rect = pygame.Rect(92, y - 5, 250, 31)
        pygame.draw.rect(screen, PALETTE["panel_dark"], row_rect)
        pygame.draw.rect(screen, (58, 66, 66), row_rect, 1)
        label_text = self.font.render(f"{label} :", True, PALETTE["muted"])
        value_text = self.font.render(str(value), True, value_color or PALETTE["text"])
        screen.blit(label_text, (row_rect.x + 10, y))
        screen.blit(value_text, (row_rect.right - value_text.get_width() - 10, y))
        return y + 38

    def _draw_loot_section(self, screen, rect, drops):
        y = rect.y + 72
        if drops:
            for drop in drops[:6]:
                row_rect = pygame.Rect(rect.x + 20, y - 4, rect.width - 40, 30)
                pygame.draw.rect(screen, PALETTE["panel_dark"], row_rect)
                pygame.draw.rect(screen, (70, 66, 70), row_rect, 1)
                pygame.draw.rect(screen, self._get_drop_color(drop), (row_rect.x, row_rect.y, 4, row_rect.height))
                loot_text = self.font.render(
                    self._format_drop(drop), True, self._get_drop_color(drop)
                )
                screen.blit(loot_text, (row_rect.x + 12, row_rect.y + 5))
                y += 38
        else:
            row_rect = pygame.Rect(rect.x + 20, y - 4, rect.width - 40, 42)
            pygame.draw.rect(screen, PALETTE["panel_dark"], row_rect)
            pygame.draw.rect(screen, (70, 66, 70), row_rect, 1)
            no_loot_text = self.font.render("Aucun loot", True, PALETTE["muted"])
            screen.blit(no_loot_text, (row_rect.x + 10, row_rect.y + 10))

    def _draw_combat_report_mail(self, screen, result):
        mail = result.get("combat_report_mail")
        if not mail:
            return

        text = self.small_font.render(
            "Rapport archivé dans la boîte aux lettres", True, PALETTE["muted"]
        )
        text_rect = text.get_rect(center=(400, 490))
        screen.blit(text, text_rect)

    def _format_drop(self, drop):
        item_id = drop["item"]
        item_data = self.game.data.items.get(item_id, {})
        item_name = item_data.get("name", item_id)
        kind = drop.get("kind")

        if kind == "stackable":
            return f"- {item_name} x {drop.get('quantity', 1)}"

        if kind == "unique":
            rarity = self._get_rarity_label(drop)
            display_name = f"[{rarity}] {item_name}" if rarity else item_name
            stats_text = self._format_stats(drop.get("stats", {}))
            if stats_text:
                return f"- {display_name} ({stats_text})"
            return f"- {display_name}"

        return f"- {item_name}"

    def _get_rarity_label(self, drop):
        if drop is None:
            return ""
        rarity = drop.get("rarity")
        if not rarity:
            return ""
        return rarity.capitalize()

    def _get_rarity_color(self, drop):
        if drop is None:
            return (200, 200, 200)
        colors = {
            "common": (170, 170, 170),
            "uncommon": (100, 220, 120),
            "rare": (100, 160, 255),
            "epic": (180, 120, 255),
            "legendary": (255, 200, 80),
            "unique": (240, 90, 90),
        }
        return colors.get(drop.get("rarity"), (200, 200, 200))

    def _get_drop_color(self, drop):
        if drop.get("kind") == "unique":
            return self._get_rarity_color(drop)
        return (200, 200, 200)

    def _format_stats(self, stats):
        parts = []
        for stat, value in stats.items():
            parts.append(f"{self._get_stat_label(stat)} +{value}")
        return ", ".join(parts)

    def _get_stat_label(self, stat):
        labels = {
            "attack": "Attack",
            "defense": "Defense",
            "hp": "HP",
            "max_hp": "Max HP",
            "force": "Strength",
            "agility": "Agility",
            "intelligence": "Intelligence",
        }
        return labels.get(stat, stat)
