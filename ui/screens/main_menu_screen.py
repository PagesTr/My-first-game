import pygame

from systems.save_load import has_save_file


class Button:
    def __init__(self, rect, text, enabled=True):
        self.rect = pygame.Rect(rect)
        self.text = text
        self.enabled = enabled

    def draw(self, screen, font):
        bg_color = (58, 68, 78) if self.enabled else (44, 46, 50)
        border_color = (210, 220, 225) if self.enabled else (95, 95, 100)
        text_color = (245, 245, 245) if self.enabled else (140, 145, 150)

        pygame.draw.rect(screen, bg_color, self.rect, border_radius=6)
        pygame.draw.rect(screen, border_color, self.rect, 2, border_radius=6)
        label = font.render(self.text, True, text_color)
        label_rect = label.get_rect(center=self.rect.center)
        screen.blit(label, label_rect)

    def is_clicked(self, pos):
        return self.enabled and self.rect.collidepoint(pos)


class MainMenuScreen:
    def __init__(self, game, app=None):
        self.game = game
        self.app = app
        self.title_font = pygame.font.Font(None, 64)
        self.subtitle_font = pygame.font.Font(None, 24)
        self.button_font = pygame.font.Font(None, 30)
        self.continue_button = Button((290, 230, 220, 56), "Continue")
        self.new_game_button = Button((290, 302, 220, 56), "New Game")
        self.quit_button = Button((290, 374, 220, 56), "Quit")
        self.message = ""
        self.message_until = 0

    def handle_event(self, event):
        if event.type != pygame.MOUSEBUTTONDOWN:
            return

        self.continue_button.enabled = has_save_file()
        if self.continue_button.is_clicked(event.pos):
            if not self.game.load_saved_game():
                self._set_message("Failed to load save")
            return

        if self.new_game_button.is_clicked(event.pos):
            self.game.start_new_game()
            return

        if self.quit_button.is_clicked(event.pos):
            if self.app is not None:
                self.app.running = False
            else:
                pygame.event.post(pygame.event.Event(pygame.QUIT))

    def draw(self, screen):
        screen.fill((18, 24, 30))
        self.continue_button.enabled = has_save_file()

        title = self.title_font.render("My First Game", True, (245, 245, 245))
        title_rect = title.get_rect(center=(400, 120))
        screen.blit(title, title_rect)

        subtitle = self.subtitle_font.render(
            "Every expedition ends. Progress remains.",
            True,
            (190, 200, 205),
        )
        subtitle_rect = subtitle.get_rect(center=(400, 164))
        screen.blit(subtitle, subtitle_rect)

        self.continue_button.draw(screen, self.button_font)
        self.new_game_button.draw(screen, self.button_font)
        self.quit_button.draw(screen, self.button_font)

        if not self.continue_button.enabled:
            no_save = self.subtitle_font.render("No save found", True, (150, 155, 160))
            no_save_rect = no_save.get_rect(center=(400, 292))
            screen.blit(no_save, no_save_rect)

        if self.message and pygame.time.get_ticks() <= self.message_until:
            message = self.subtitle_font.render(self.message, True, (220, 210, 140))
            message_rect = message.get_rect(center=(400, 460))
            screen.blit(message, message_rect)
        elif self.message:
            self.message = ""

        version = self.subtitle_font.render("Version: prototype", True, (120, 130, 140))
        screen.blit(version, (50, 548))

    def _set_message(self, message):
        self.message = message
        self.message_until = pygame.time.get_ticks() + 1800
