import pygame


PALETTE = {
    "background_top": (14, 16, 24),
    "background_bottom": (29, 24, 34),
    "panel": (33, 35, 47),
    "panel_dark": (22, 23, 32),
    "panel_light": (48, 50, 64),
    "border": (119, 108, 92),
    "border_light": (194, 166, 100),
    "text": (238, 232, 214),
    "muted": (174, 168, 158),
    "gold": (235, 184, 72),
    "victory": (139, 215, 118),
    "defeat": (170, 72, 72),
    "level_up": (98, 226, 137),
    "button": (64, 57, 66),
    "button_border": (220, 190, 112),
}


class Button:
    def __init__(self, rect, text):
        self.rect = pygame.Rect(rect)
        self.text = text

    def draw(self, screen, font):
        pygame.draw.rect(screen, (70, 70, 70), self.rect)
        pygame.draw.rect(screen, (200, 200, 200), self.rect, 2)

        label = font.render(self.text, True, (255, 255, 255))
        screen.blit(label, (self.rect.x + 20, self.rect.y + 12))

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
        title_text = "Victoire !" if victory else "Defaite..."
        title_color = PALETTE["victory"] if victory else PALETTE["defeat"]

        result = self.game.last_combat_result or {}
        exp_gained = result.get("exp_gained", 0)
        gold_gained = result.get("gold_gained", 0)
        drops = result.get("drops", [])
        current_level = self.game.player.get("level", 1) if self.game.player else 1

        self._draw_title(screen, title_text, title_color)

        summary_rect = pygame.Rect(70, 145, 310, 310)
        loot_rect = pygame.Rect(420, 145, 310, 310)
        self._draw_panel(screen, summary_rect, "Resume")
        self._draw_panel(screen, loot_rect, "Butin")

        y = summary_rect.y + 66
        y = self._draw_summary_line(screen, "XP gagnee", exp_gained, y)
        y = self._draw_summary_line(
            screen, "Gold gagne", gold_gained, y, PALETTE["gold"]
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
        screen.fill(PALETTE["background_top"])
        for y in range(0, 600, 4):
            blend = y / 600
            color = (
                int(
                    PALETTE["background_top"][0] * (1 - blend)
                    + PALETTE["background_bottom"][0] * blend
                ),
                int(
                    PALETTE["background_top"][1] * (1 - blend)
                    + PALETTE["background_bottom"][1] * blend
                ),
                int(
                    PALETTE["background_top"][2] * (1 - blend)
                    + PALETTE["background_bottom"][2] * blend
                ),
            )
            pygame.draw.rect(screen, color, (0, y, 800, 4))

        for x in range(0, 800, 32):
            pygame.draw.line(screen, (20, 22, 31), (x, 0), (x, 600))
        for y in range(0, 600, 32):
            pygame.draw.line(screen, (20, 22, 31), (0, y), (800, y))

    def _draw_title(self, screen, title_text, title_color):
        shadow = self.title_font.render(title_text, True, PALETTE["panel_dark"])
        title = self.title_font.render(title_text, True, title_color)
        title_rect = title.get_rect(center=(400, 72))
        shadow_rect = shadow.get_rect(center=(403, 75))
        screen.blit(shadow, shadow_rect)
        screen.blit(title, title_rect)

    def _draw_panel(self, screen, rect, title):
        pygame.draw.rect(screen, PALETTE["panel_dark"], rect.move(5, 5))
        pygame.draw.rect(screen, PALETTE["panel"], rect)
        pygame.draw.rect(screen, PALETTE["border"], rect, 3)
        pygame.draw.rect(screen, PALETTE["panel_light"], rect.inflate(-14, -14), 1)

        title_bg = pygame.Rect(rect.x + 18, rect.y + 14, rect.width - 36, 34)
        pygame.draw.rect(screen, PALETTE["panel_dark"], title_bg)
        pygame.draw.rect(screen, PALETTE["border_light"], title_bg, 2)
        title_text = self.header_font.render(title, True, PALETTE["text"])
        screen.blit(title_text, (title_bg.x + 12, title_bg.y + 5))

    def _draw_button(self, screen, button):
        pygame.draw.rect(screen, PALETTE["panel_dark"], button.rect.move(4, 4))
        pygame.draw.rect(screen, PALETTE["button"], button.rect)
        pygame.draw.rect(screen, PALETTE["button_border"], button.rect, 3)
        pygame.draw.rect(screen, PALETTE["panel_light"], button.rect.inflate(-10, -10), 1)

        label = self.font.render(button.text, True, PALETTE["text"])
        label_rect = label.get_rect(center=button.rect.center)
        screen.blit(label, label_rect)

    def _draw_summary_line(self, screen, label, value, y, value_color=None):
        label_text = self.font.render(f"{label} :", True, PALETTE["muted"])
        value_text = self.font.render(str(value), True, value_color or PALETTE["text"])
        screen.blit(label_text, (95, y))
        screen.blit(value_text, (270, y))
        return y + 38

    def _draw_loot_section(self, screen, rect, drops):
        y = rect.y + 72
        if drops:
            for drop in drops[:6]:
                row_rect = pygame.Rect(rect.x + 20, y - 4, rect.width - 40, 30)
                pygame.draw.rect(screen, PALETTE["panel_dark"], row_rect)
                pygame.draw.rect(screen, (70, 66, 70), row_rect, 1)
                loot_text = self.font.render(
                    self._format_drop(drop), True, self._get_drop_color(drop)
                )
                screen.blit(loot_text, (300, loot_y + 35 + index * 28))
        else:
            no_loot_text = self.font.render("Aucun loot", True, (200, 200, 200))
            screen.blit(no_loot_text, (300, loot_y + 35))

        self.continue_btn.draw(screen, self.font)

    def _draw_combat_report_mail(self, screen, result):
        mail = result.get("combat_report_mail")
        if not mail:
            return

        small_font = pygame.font.Font(None, 22)
        text = small_font.render(
            "Combat report saved to Mailbox", True, (190, 200, 205)
        )
        screen.blit(text, (300, 480))

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
