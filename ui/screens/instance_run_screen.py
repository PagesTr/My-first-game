import pygame


class InstanceRunScreen:
    def __init__(self, game):
        self.game = game
        self.title_font = pygame.font.Font(None, 44)
        self.header_font = pygame.font.Font(None, 32)
        self.font = pygame.font.Font(None, 26)
        self.small_font = pygame.font.Font(None, 20)
        self.started_at_ms = pygame.time.get_ticks()
        self.phase_started_at_ms = self.started_at_ms
        self.last_result_ref = None
        self.phase = "running"
        self.run_duration_ms = 3000
        self.death_pause_ms = 2000

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

        current_time_ms = pygame.time.get_ticks()
        elapsed_ms = current_time_ms - self.phase_started_at_ms
        if self.phase == "running" and elapsed_ms >= self.run_duration_ms:
            self.phase = "death"
            self.phase_started_at_ms = current_time_ms
            return
        if self.phase == "death" and elapsed_ms >= self.death_pause_ms:
            self.game.state = "combat_result"

    def draw(self, screen):
        result = self._get_result()
        self._reset_animation_if_needed(result)
        self._draw_background(screen)

        if not result:
            self._draw_empty_state(screen)
            return

        zone_name = result.get("zone_name") or result.get("zone_key") or "Unknown zone"
        combats_won = self._as_int(result.get("combats_won"))
        death_enemy = result.get("death_enemy") or "Unknown enemy"

        if self.phase == "death":
            self._draw_death_phase(screen, combats_won, death_enemy)
            return

        self._draw_running_phase(screen, zone_name, combats_won)

    def _draw_running_phase(self, screen, zone_name, combats_won):
        progress = self._get_progress()
        displayed_combats = int(combats_won * progress)
        panel = pygame.Rect(0, 0, 520, 310)
        panel.center = screen.get_rect().center
        pygame.draw.rect(screen, (23, 28, 25), panel, border_radius=8)
        pygame.draw.rect(screen, (124, 155, 107), panel, 2, border_radius=8)

        title = self.title_font.render("Expédition", True, (235, 232, 202))
        screen.blit(title, title.get_rect(center=(panel.centerx, panel.y + 44)))

        zone_text = self.header_font.render(str(zone_name), True, (190, 220, 156))
        screen.blit(zone_text, zone_text.get_rect(center=(panel.centerx, panel.y + 84)))

        status = "Tu tiens bon pour l'instant..." if progress < 0.7 else "Combats en cours..."
        status_text = self.font.render(status, True, (224, 224, 210))
        screen.blit(status_text, (panel.x + 42, panel.y + 124))

        self._draw_progress_bar(screen, panel, progress)

        rows = [
            ("Combats remportés", f"{displayed_combats} / {combats_won}"),
            ("Progression", "L'expédition avance..."),
        ]
        row_y = panel.y + 178
        for label, value in rows:
            label_surface = self.font.render(label, True, (170, 184, 164))
            value_surface = self.font.render(value, True, (238, 236, 214))
            screen.blit(label_surface, (panel.x + 46, row_y))
            screen.blit(value_surface, value_surface.get_rect(topright=(panel.right - 46, row_y)))
            row_y += 34

        skip_text = self.small_font.render("Entrée / Espace / Échap - Continuer", True, (156, 164, 150))
        screen.blit(skip_text, skip_text.get_rect(center=(panel.centerx, panel.bottom - 24)))

    def _draw_death_phase(self, screen, combats_won, death_enemy):
        panel = pygame.Rect(0, 0, 520, 260)
        panel.center = screen.get_rect().center
        pygame.draw.rect(screen, (34, 22, 22), panel, border_radius=8)
        pygame.draw.rect(screen, (178, 84, 72), panel, 2, border_radius=8)

        title = self.title_font.render("Tu es mort", True, (246, 218, 205))
        screen.blit(title, title.get_rect(center=(panel.centerx, panel.y + 54)))

        rows = [
            ("Vaincu par", str(death_enemy)),
            ("Combats remportés", str(combats_won)),
        ]
        row_y = panel.y + 112
        for label, value in rows:
            label_surface = self.font.render(label, True, (206, 158, 148))
            value_surface = self.font.render(value, True, (246, 236, 218))
            screen.blit(label_surface, (panel.x + 52, row_y))
            screen.blit(value_surface, value_surface.get_rect(topright=(panel.right - 52, row_y)))
            row_y += 42

        hint = self.small_font.render("Entrée / Espace - Voir le résultat", True, (198, 172, 164))
        screen.blit(hint, hint.get_rect(center=(panel.centerx, panel.bottom - 28)))

    def _get_result(self):
        result = self.game.last_instance_result or self.game.last_combat_result or {}
        return result if isinstance(result, dict) and result.get("is_instance_result") else {}

    def _reset_animation_if_needed(self, result):
        result_ref = id(result) if result else None
        if result_ref == self.last_result_ref:
            return
        self.last_result_ref = result_ref
        current_time_ms = pygame.time.get_ticks()
        self.started_at_ms = current_time_ms
        self.phase_started_at_ms = current_time_ms
        self.phase = "running"

    def _get_progress(self):
        elapsed_ms = pygame.time.get_ticks() - self.started_at_ms
        return max(0.0, min(1.0, elapsed_ms / self.run_duration_ms))

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
        hint = self.small_font.render("Entrée / Espace / Échap - Retour", True, (156, 164, 150))
        screen.blit(hint, hint.get_rect(center=(panel.centerx, panel.y + 100)))

    def _as_int(self, value):
        try:
            return int(value)
        except (TypeError, ValueError):
            return 0
