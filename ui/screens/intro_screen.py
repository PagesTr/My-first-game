import pygame


class IntroScreen:
    def __init__(self, game, exploration_screen):
        self.game = game
        self.exploration_screen = exploration_screen
        self.title_font = pygame.font.Font(None, 34)
        self.body_font = pygame.font.Font(None, 28)
        self.hint_font = pygame.font.Font(None, 22)
        self.pages = [
            (
                "Tu te souviens d'une chute.",
                "Puis du silence.",
            ),
            (
                "Ton corps est perdu.",
                "Mais quelque chose de toi repond encore.",
            ),
            (
                "La pierre ne rend pas la vie.",
                "Elle rappelle ce qui refuse de disparaitre.",
            ),
            (
                "Une lumiere ancienne pulse dans l'obscurite.",
                "Ton echo s'eveille.",
            ),
        ]
        self.page_index = 0
        self.page_started_at_ms = pygame.time.get_ticks()
        self.was_active = False

    def handle_event(self, event):
        self._ensure_active_page()
        if event.type != pygame.KEYDOWN:
            return

        if event.key == pygame.K_ESCAPE:
            self._finish_intro()
            return

        if event.key in (pygame.K_RETURN, pygame.K_KP_ENTER, pygame.K_SPACE):
            self._advance_page()

    def update(self):
        self._ensure_active_page()

    def draw(self, screen):
        self._ensure_active_page()
        screen.fill((0, 0, 0))

        alpha = self._get_text_alpha()
        page = self.pages[self.page_index]
        center_y = screen.get_height() // 2 - 28
        line_spacing = 36

        for index, text in enumerate(page):
            rendered = self.body_font.render(text, True, (226, 238, 232))
            rendered.set_alpha(alpha)
            rect = rendered.get_rect(center=(screen.get_width() // 2, center_y + index * line_spacing))
            screen.blit(rendered, rect)

        hint_alpha = min(220, max(70, alpha))
        hint = self.hint_font.render("Entree / Espace - Continuer", True, (120, 172, 164))
        hint.set_alpha(hint_alpha)
        hint_rect = hint.get_rect(center=(screen.get_width() // 2, screen.get_height() - 58))
        screen.blit(hint, hint_rect)

    def _ensure_active_page(self):
        is_active = self.game.state == "intro_text"
        if is_active and not self.was_active:
            self.page_index = 0
            self.page_started_at_ms = pygame.time.get_ticks()
        self.was_active = is_active

    def _advance_page(self):
        if self.page_index >= len(self.pages) - 1:
            self._finish_intro()
            return
        self.page_index += 1
        self.page_started_at_ms = pygame.time.get_ticks()

    def _finish_intro(self):
        load_map = getattr(self.exploration_screen, "_load_map", None)
        if callable(load_map):
            try:
                load_map("altar_01", "first_spawn")
            except Exception:
                pass
        self.game.finish_intro()
        self.was_active = False

    def _get_text_alpha(self):
        elapsed_ms = pygame.time.get_ticks() - self.page_started_at_ms
        return min(255, max(0, int(elapsed_ms / 700 * 255)))
