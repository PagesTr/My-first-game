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

        if self.phase == "death":
            self._draw_death_phase(screen)
            return

        self._draw_running_phase(screen, zone_name)

    def _draw_running_phase(self, screen, zone_name):
        progress = self._get_phase_progress()
        visual_hp_ratio = max(0.0, 1.0 - progress)
        max_hp = self._get_visual_max_hp()
        displayed_hp = int(max_hp * visual_hp_ratio)
        panel = pygame.Rect(0, 0, 560, 370)
        panel.center = screen.get_rect().center
        pygame.draw.rect(screen, (23, 28, 25), panel, border_radius=8)
        border_color = (190, 72, 64) if visual_hp_ratio < 0.15 and self._is_danger_flash_on() else (124, 155, 107)
        pygame.draw.rect(screen, border_color, panel, 2, border_radius=8)

        title = self.title_font.render("Expédition en cours", True, (235, 232, 202))
        screen.blit(title, title.get_rect(center=(panel.centerx, panel.y + 44)))

        zone_text = self.header_font.render(str(zone_name), True, (190, 220, 156))
        screen.blit(zone_text, zone_text.get_rect(center=(panel.centerx, panel.y + 84)))

        if progress < 0.35:
            status = "Tu avances dans la zone..."
        elif progress < 0.72:
            status = "Les combats s'enchaînent..."
        else:
            status = "Tes forces diminuent..."
        status_text = self.font.render(status, True, (224, 224, 210))
        screen.blit(status_text, (panel.x + 42, panel.y + 124))

        self._draw_combat_animation(screen, panel, progress)
        self._draw_health_bar(screen, panel, visual_hp_ratio, displayed_hp, max_hp)

        skip_text = self.small_font.render("Entrée / Espace / Échap - Continuer", True, (156, 164, 150))
        screen.blit(skip_text, skip_text.get_rect(center=(panel.centerx, panel.bottom - 24)))

    def _draw_death_phase(self, screen):
        panel = pygame.Rect(0, 0, 520, 260)
        panel.center = screen.get_rect().center
        pygame.draw.rect(screen, (34, 22, 22), panel, border_radius=8)
        pygame.draw.rect(screen, (178, 84, 72), panel, 2, border_radius=8)

        title = self.title_font.render("Tu es mort", True, (246, 218, 205))
        screen.blit(title, title.get_rect(center=(panel.centerx, panel.y + 54)))

        message = self.header_font.render("L'expédition est terminée.", True, (246, 236, 218))
        screen.blit(message, message.get_rect(center=(panel.centerx, panel.y + 122)))

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

    def _get_phase_progress(self):
        elapsed_ms = pygame.time.get_ticks() - self.started_at_ms
        return max(0.0, min(1.0, elapsed_ms / self.run_duration_ms))

    def _get_visual_max_hp(self):
        player = getattr(self.game, "player", None)
        if isinstance(player, dict):
            return max(1, self._as_int(player.get("max_hp")) or 100)
        return 100

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

    def _draw_combat_animation(self, screen, panel, progress):
        elapsed_ms = pygame.time.get_ticks() - self.phase_started_at_ms
        cycle_ms = 700
        cycle_progress = (elapsed_ms % cycle_ms) / cycle_ms
        cycle_index = int(elapsed_ms / cycle_ms)
        lunge = cycle_progress * 2 if cycle_progress < 0.5 else (1.0 - cycle_progress) * 2
        lunge_offset = int(24 * lunge)

        arena = pygame.Rect(panel.x + 48, panel.y + 150, panel.width - 96, 88)
        pygame.draw.rect(screen, (16, 22, 19), arena, border_radius=8)
        pygame.draw.rect(screen, (56, 74, 62), arena, 1, border_radius=8)
        pygame.draw.line(
            screen,
            (38, 55, 43),
            (arena.x + 24, arena.bottom - 12),
            (arena.right - 24, arena.bottom - 12),
            2,
        )

        player_x = arena.x + 92 + (lunge_offset if cycle_index % 2 == 0 else 0)
        enemy_x = arena.right - 92 - (lunge_offset if cycle_index % 2 == 1 else 0)
        base_y = arena.bottom - 18
        self._draw_fighter(screen, player_x, base_y, (92, 142, 196), facing=1)
        self._draw_fighter(screen, enemy_x, base_y, (172, 84, 72), facing=-1)

        if 0.38 <= cycle_progress <= 0.58:
            impact_x = arena.centerx + (16 if cycle_index % 2 == 0 else -16)
            impact_y = arena.centery + 4
            impact_color = (246, 232, 150) if progress < 0.78 else (244, 134, 104)
            pygame.draw.line(screen, impact_color, (impact_x - 18, impact_y), (impact_x + 18, impact_y), 3)
            pygame.draw.line(screen, impact_color, (impact_x, impact_y - 18), (impact_x, impact_y + 18), 3)
            pygame.draw.line(screen, impact_color, (impact_x - 13, impact_y - 13), (impact_x + 13, impact_y + 13), 2)
            pygame.draw.line(screen, impact_color, (impact_x - 13, impact_y + 13), (impact_x + 13, impact_y - 13), 2)

    def _draw_fighter(self, screen, x, base_y, color, facing):
        shadow = pygame.Rect(0, 0, 44, 8)
        shadow.center = (x, base_y + 4)
        pygame.draw.ellipse(screen, (7, 10, 9), shadow)
        pygame.draw.circle(screen, color, (x, base_y - 48), 11)
        pygame.draw.rect(screen, color, (x - 9, base_y - 38, 18, 28), border_radius=4)
        pygame.draw.line(screen, color, (x - 7, base_y - 12), (x - 17, base_y), 4)
        pygame.draw.line(screen, color, (x + 7, base_y - 12), (x + 17, base_y), 4)
        pygame.draw.line(screen, (226, 220, 178), (x + facing * 10, base_y - 31), (x + facing * 32, base_y - 41), 3)
        pygame.draw.line(screen, (226, 220, 178), (x + facing * 26, base_y - 45), (x + facing * 36, base_y - 37), 2)

    def _draw_health_bar(self, screen, panel, hp_ratio, displayed_hp, max_hp):
        label_color = (248, 190, 170) if hp_ratio < 0.15 and self._is_danger_flash_on() else (238, 236, 214)
        label = self.font.render(f"PV : {displayed_hp} / {max_hp}", True, label_color)
        screen.blit(label, (panel.x + 42, panel.y + 258))

        bar = pygame.Rect(panel.x + 42, panel.y + 292, panel.width - 84, 22)
        pygame.draw.rect(screen, (12, 16, 14), bar, border_radius=7)
        fill = bar.copy()
        fill.width = int(bar.width * hp_ratio)
        if fill.width > 0:
            if hp_ratio > 0.5:
                fill_color = (108, 190, 102)
            elif hp_ratio > 0.35:
                fill_color = (216, 166, 72)
            else:
                fill_color = (190, 72, 64)
            pygame.draw.rect(screen, fill_color, fill, border_radius=7)
        outline_color = (246, 158, 128) if hp_ratio < 0.15 and self._is_danger_flash_on() else (118, 72, 68)
        pygame.draw.rect(screen, outline_color, bar, 1, border_radius=7)

    def _is_danger_flash_on(self):
        elapsed_ms = pygame.time.get_ticks() - self.phase_started_at_ms
        return (elapsed_ms // 180) % 2 == 0

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
