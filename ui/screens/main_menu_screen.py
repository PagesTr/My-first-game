import pygame

from systems.save_load import has_save_file
from ui.assets import load_image
from ui.overlays.notice_board_overlay import NoticeBoardOverlay


PALETTE = {
    "sky_top": (18, 20, 24),
    "sky_bottom": (42, 34, 27),
    "forest_back": (18, 46, 37),
    "forest_front": (12, 28, 24),
    "ground": (17, 20, 22),
    "ground_light": (36, 41, 34),
    "panel": (38, 34, 28),
    "panel_dark": (25, 22, 18),
    "panel_light": (86, 70, 45),
    "border": (118, 92, 45),
    "border_light": (205, 170, 80),
    "text": (238, 232, 214),
    "muted": (190, 184, 160),
    "gold": (228, 188, 86),
    "button": (76, 58, 38),
    "button_hover": (96, 73, 44),
    "button_disabled": (42, 40, 36),
    "button_border": (205, 170, 80),
    "button_border_hover": (236, 204, 112),
    "shadow": (8, 10, 13),
}


class Button:
    def __init__(self, rect, text, enabled=True):
        self.rect = pygame.Rect(rect)
        self.text = text
        self.enabled = enabled

    def draw(self, screen, font):
        hovered = self.enabled and self.rect.collidepoint(pygame.mouse.get_pos())
        if not self.enabled:
            bg_color = PALETTE["button_disabled"]
            border_color = (88, 92, 96)
        elif hovered:
            bg_color = PALETTE["button_hover"]
            border_color = PALETTE["button_border_hover"]
        else:
            bg_color = PALETTE["button"]
            border_color = PALETTE["button_border"]
        text_color = PALETTE["text"] if self.enabled else (132, 138, 142)

        pygame.draw.rect(screen, PALETTE["shadow"], self.rect.move(4, 4))
        pygame.draw.rect(screen, bg_color, self.rect)
        pygame.draw.rect(screen, border_color, self.rect, 3)
        pygame.draw.rect(screen, PALETTE["panel_light"], self.rect.inflate(-10, -10), 1)
        label = font.render(self.text, True, text_color)
        label_rect = label.get_rect(center=self.rect.center)
        screen.blit(label, label_rect)

    def is_clicked(self, pos):
        return self.enabled and self.rect.collidepoint(pos)


class MainMenuScreen:
    def __init__(self, game, app=None):
        self.game = game
        self.app = app
        self.background = load_image("assets/backgrounds/main_menu.png", (800, 600))
        self.title_font = pygame.font.Font(None, 48)
        self.header_font = pygame.font.Font(None, 34)
        self.subtitle_font = pygame.font.Font(None, 24)
        self.button_font = pygame.font.Font(None, 28)
        self.continue_button = Button((76, 220, 248, 48), "Continue")
        self.new_game_button = Button((76, 290, 248, 48), "New Game")
        self.notice_board_button = Button((76, 360, 248, 48), "Notice Board")
        self.quit_button = Button((76, 430, 248, 48), "Quit")
        self.notice_board_overlay = NoticeBoardOverlay(self.game)
        self.message = ""
        self.message_until = 0

    def handle_event(self, event):
        if self.notice_board_overlay.is_open():
            self.notice_board_overlay.handle_event(event)
            return

        if event.type != pygame.MOUSEBUTTONDOWN:
            return

        self.continue_button.enabled = has_save_file()
        if self.continue_button.is_clicked(event.pos):
            if not self.game.load_saved_game():
                self._set_message("Failed to load save")
                return
            if hasattr(self.game, "open_exploration"):
                self.game.open_exploration()
            else:
                self.game.state = "exploration"
            return

        if self.new_game_button.is_clicked(event.pos):
            self.game.start_new_game()
            return

        if self.notice_board_button.is_clicked(event.pos):
            self.notice_board_overlay.open()
            return

        if self.quit_button.is_clicked(event.pos):
            if self.app is not None:
                self.app.running = False
            else:
                pygame.event.post(pygame.event.Event(pygame.QUIT))

    def draw(self, screen):
        self._draw_background(screen)
        self.continue_button.enabled = has_save_file()
        game_message = getattr(self.game, "main_menu_message", "")
        if game_message and not self.message:
            self._set_message(game_message)
            self.game.main_menu_message = ""

        self._draw_title_banner(screen)
        self._draw_menu_panel(screen)

        self.continue_button.draw(screen, self.button_font)
        self.new_game_button.draw(screen, self.button_font)
        self.notice_board_button.draw(screen, self.button_font)
        self.quit_button.draw(screen, self.button_font)

        if not self.continue_button.enabled:
            no_save = self.subtitle_font.render("No save found", True, PALETTE["muted"])
            no_save_rect = no_save.get_rect(center=(200, 279))
            screen.blit(no_save, no_save_rect)

        if self.message and pygame.time.get_ticks() <= self.message_until:
            self._draw_message(screen, self.message)
        elif self.message:
            self.message = ""

        self._draw_footer(screen)

        if self.notice_board_overlay.is_open():
            self.notice_board_overlay.draw(screen)

    def _set_message(self, message):
        self.message = message
        self.message_until = pygame.time.get_ticks() + 1800

    def _draw_background(self, screen):
        if self.background is None:
            self._draw_fallback_background(screen)
            return

        screen.blit(self.background, (0, 0))
        readability_overlay = pygame.Surface((800, 600), pygame.SRCALPHA)
        readability_overlay.fill((5, 7, 12, 38))
        pygame.draw.rect(readability_overlay, (3, 5, 10, 112), (0, 0, 370, 600))
        pygame.draw.rect(readability_overlay, (3, 5, 10, 72), (370, 0, 70, 600))
        screen.blit(readability_overlay, (0, 0))

    def _draw_fallback_background(self, screen):
        for y in range(0, 600, 4):
            blend = y / 600
            color = (
                int(PALETTE["sky_top"][0] * (1 - blend) + PALETTE["sky_bottom"][0] * blend),
                int(PALETTE["sky_top"][1] * (1 - blend) + PALETTE["sky_bottom"][1] * blend),
                int(PALETTE["sky_top"][2] * (1 - blend) + PALETTE["sky_bottom"][2] * blend),
            )
            pygame.draw.rect(screen, color, (0, y, 800, 4))

        pygame.draw.rect(screen, (216, 211, 172), (622, 50, 44, 44))
        pygame.draw.rect(screen, PALETTE["sky_top"], (612, 44, 22, 54))

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

    def _draw_title_banner(self, screen):
        banner_rect = pygame.Rect(48, 36, 304, 108)
        pygame.draw.rect(screen, PALETTE["shadow"], banner_rect.move(5, 5))
        pygame.draw.rect(screen, PALETTE["panel_dark"], banner_rect)
        pygame.draw.rect(screen, PALETTE["border_light"], banner_rect, 3)
        pygame.draw.rect(screen, PALETTE["panel_light"], banner_rect.inflate(-14, -14), 1)

        title_shadow = self.title_font.render("My First Game", True, PALETTE["shadow"])
        title = self.title_font.render("My First Game", True, PALETTE["gold"])
        title_rect = title.get_rect(center=(200, 77))
        shadow_rect = title_shadow.get_rect(center=(203, 80))
        screen.blit(title_shadow, shadow_rect)
        screen.blit(title, title_rect)

        subtitle = self.subtitle_font.render(
            "The forest keeps count.",
            True,
            PALETTE["muted"],
        )
        subtitle_rect = subtitle.get_rect(center=(200, 116))
        screen.blit(subtitle, subtitle_rect)

    def _draw_menu_panel(self, screen):
        panel_rect = pygame.Rect(48, 164, 304, 332)
        pygame.draw.rect(screen, PALETTE["shadow"], panel_rect.move(5, 5))
        panel_surface = pygame.Surface(panel_rect.size, pygame.SRCALPHA)
        panel_surface.fill((*PALETTE["panel_dark"], 224))
        pygame.draw.rect(panel_surface, PALETTE["border"], panel_surface.get_rect(), 3)
        pygame.draw.rect(panel_surface, PALETTE["panel_light"], panel_surface.get_rect().inflate(-14, -14), 1)
        pygame.draw.line(
            panel_surface,
            PALETTE["border_light"],
            (12, 12),
            (panel_rect.w - 12, 12),
            2,
        )
        screen.blit(panel_surface, panel_rect)
        header = self.header_font.render("Main Menu", True, PALETTE["text"])
        header_rect = header.get_rect(center=(200, panel_rect.y + 30))
        screen.blit(header, header_rect)

    def _draw_message(self, screen, message):
        rect = pygame.Rect(60, 506, 280, 34)
        pygame.draw.rect(screen, PALETTE["shadow"], rect.move(3, 3))
        pygame.draw.rect(screen, PALETTE["panel_dark"], rect)
        pygame.draw.rect(screen, PALETTE["border_light"], rect, 1)
        text = self.subtitle_font.render(message, True, PALETTE["gold"])
        text_rect = text.get_rect(center=rect.center)
        screen.blit(text, text_rect)

    def _draw_footer(self, screen):
        version = self.subtitle_font.render("Prototype build", True, (130, 124, 105))
        screen.blit(version, (62, 558))
        hint = self.subtitle_font.render("Top-down exploration", True, PALETTE["muted"])
        screen.blit(hint, (604, 548))
