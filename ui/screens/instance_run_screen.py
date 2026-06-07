import pygame


class InstanceRunScreen:
    def __init__(self, game):
        self.game = game
        self.title_font = pygame.font.Font(None, 44)
        self.header_font = pygame.font.Font(None, 32)
        self.font = pygame.font.Font(None, 26)
        self.small_font = pygame.font.Font(None, 20)
        self.started_at_ms = pygame.time.get_ticks()
        self.last_result_ref = None
        self.duration_ms = 3200

    def handle_event(self, event):
        if event.type != pygame.KEYDOWN:
            return
        if event.key not in (pygame.K_RETURN, pygame.K_SPACE, pygame.K_ESCAPE):
            return
        if self._get_result():
            self.game.state = "combat_result"
        else:
            self.game.state = "exploration"

    def update(self):
        result = self._get_result()
        self._reset_animation_if_needed(result)
        if not result:
            return

        elapsed_ms = pygame.time.get_ticks() - self.started_at_ms
        if elapsed_ms >= self.duration_ms:
            self.game.state = "combat_result"

    def draw(self, screen):
        result = self._get_result()
        self._reset_animation_if_needed(result)
        self._draw_background(screen)

        if not result:
            self._draw_empty_state(screen)
            return

        progress = self._get_progress()
        zone_name = result.get("zone_name") or result.get("zone_key") or "Unknown zone"
        combats_won = self._as_int(result.get("combats_won"))
        displayed_combats = int(combats_won * progress)
        death_enemy = result.get("death_enemy") or "Unknown enemy"
        exp_gained = self._as_int(result.get("exp_gained"))
        gold_gained = self._as_int(result.get("gold_gained"))

        panel = pygame.Rect(0, 0, 520, 310)
        panel.center = screen.get_rect().center
        pygame.draw.rect(screen, (23, 28, 25), panel, border_radius=8)
        pygame.draw.rect(screen, (124, 155, 107), panel, 2, border_radius=8)

        title = self.title_font.render("Instance resolved", True, (235, 232, 202))
        screen.blit(title, title.get_rect(center=(panel.centerx, panel.y + 44)))

        zone_text = self.header_font.render(str(zone_name), True, (190, 220, 156))
        screen.blit(zone_text, zone_text.get_rect(center=(panel.centerx, panel.y + 84)))

        status = "Combats resolved..." if displayed_combats != 1 else "Combat 1..."
        status_text = self.font.render(status, True, (224, 224, 210))
        screen.blit(status_text, (panel.x + 42, panel.y + 124))

        self._draw_progress_bar(screen, panel, progress)

        rows = [
            ("Combats won", f"{displayed_combats} / {combats_won}"),
            ("Final enemy", str(death_enemy)),
            ("XP gained", str(exp_gained)),
            ("Gold gained", str(gold_gained)),
        ]
        row_y = panel.y + 178
        for label, value in rows:
            label_surface = self.font.render(label, True, (170, 184, 164))
            value_surface = self.font.render(value, True, (238, 236, 214))
            screen.blit(label_surface, (panel.x + 46, row_y))
            screen.blit(value_surface, value_surface.get_rect(topright=(panel.right - 46, row_y)))
            row_y += 34

        skip_text = self.small_font.render("Enter / Space / Escape to continue", True, (156, 164, 150))
        screen.blit(skip_text, skip_text.get_rect(center=(panel.centerx, panel.bottom - 24)))

    def _get_result(self):
        result = self.game.last_instance_result or self.game.last_combat_result or {}
        return result if isinstance(result, dict) and result.get("is_instance_result") else {}

    def _reset_animation_if_needed(self, result):
        result_ref = id(result) if result else None
        if result_ref == self.last_result_ref:
            return
        self.last_result_ref = result_ref
        self.started_at_ms = pygame.time.get_ticks()

    def _get_progress(self):
        elapsed_ms = pygame.time.get_ticks() - self.started_at_ms
        return max(0.0, min(1.0, elapsed_ms / self.duration_ms))

    def _draw_background(self, screen):
        width, height = screen.get_size()
        for y in range(height):
            blend = y / max(1, height)
            color = (
                int(12 + blend * 18),
                int(24 + blend * 28),
                int(32 + blend * 10),
            )
            pygame.draw.line(screen, color, (0, y), (width, y))

        ground_y = int(height * 0.72)
        pygame.draw.rect(screen, (28, 46, 30), (0, ground_y, width, height - ground_y))
        pygame.draw.rect(screen, (38, 66, 38), (0, ground_y, width, 12))

        for index, x in enumerate(range(-40, width + 80, 90)):
            tree_height = 120 + (index % 3) * 28
            trunk = pygame.Rect(x + 30, ground_y - tree_height + 48, 18, tree_height)
            pygame.draw.rect(screen, (19, 25, 19), trunk)
            points = [
                (x, ground_y - 18),
                (x + 40, ground_y - tree_height),
                (x + 84, ground_y - 18),
            ]
            pygame.draw.polygon(screen, (14, 36, 24), points)
            points = [
                (x + 8, ground_y - 58),
                (x + 42, ground_y - tree_height - 34),
                (x + 76, ground_y - 58),
            ]
            pygame.draw.polygon(screen, (18, 48, 30), points)

    def _draw_progress_bar(self, screen, panel, progress):
        bar = pygame.Rect(panel.x + 42, panel.y + 154, panel.width - 84, 14)
        pygame.draw.rect(screen, (12, 16, 14), bar, border_radius=7)
        fill = bar.copy()
        fill.width = int(bar.width * progress)
        if fill.width > 0:
            pygame.draw.rect(screen, (146, 190, 102), fill, border_radius=7)
        pygame.draw.rect(screen, (88, 112, 78), bar, 1, border_radius=7)

    def _draw_empty_state(self, screen):
        panel = pygame.Rect(0, 0, 440, 150)
        panel.center = screen.get_rect().center
        pygame.draw.rect(screen, (23, 28, 25), panel, border_radius=8)
        pygame.draw.rect(screen, (124, 155, 107), panel, 2, border_radius=8)
        text = self.header_font.render("Aucune instance a afficher.", True, (235, 232, 202))
        screen.blit(text, text.get_rect(center=(panel.centerx, panel.y + 58)))
        hint = self.small_font.render("Enter / Space / Escape to return", True, (156, 164, 150))
        screen.blit(hint, hint.get_rect(center=(panel.centerx, panel.y + 100)))

    def _as_int(self, value):
        try:
            return int(value)
        except (TypeError, ValueError):
            return 0
