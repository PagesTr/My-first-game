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
        danger_level = int(20 * progress)
        panel_color = (
            max(10, 23 - danger_level),
            max(12, 28 - danger_level),
            max(12, 25 - danger_level),
        )
        if visual_hp_ratio < 0.35:
            panel_color = (max(8, panel_color[0] - 8), max(8, panel_color[1] - 10), max(8, panel_color[2] - 8))
        pygame.draw.rect(screen, panel_color, panel, border_radius=8)
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

        self._draw_expedition_animation(screen, panel, progress, visual_hp_ratio)
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

    def _draw_expedition_animation(self, screen, panel, progress, visual_hp_ratio):
        elapsed_ms = pygame.time.get_ticks() - self.phase_started_at_ms
        cycle_ms = 700
        cycle_progress = (elapsed_ms % cycle_ms) / cycle_ms
        step_wave = cycle_progress * 2 if cycle_progress < 0.5 else (1.0 - cycle_progress) * 2

        path = pygame.Rect(panel.x + 48, panel.y + 150, panel.width - 96, 88)
        danger_shift = int(22 * progress)
        path_color = (
            max(8, 18 - danger_shift // 3),
            max(10, 26 - danger_shift // 2),
            max(9, 20 - danger_shift // 3),
        )
        pygame.draw.rect(screen, path_color, path, border_radius=8)
        path_border = (94, 58, 56) if visual_hp_ratio < 0.35 else (56, 74, 62)
        pygame.draw.rect(screen, path_border, path, 1, border_radius=8)

        ground_y = path.bottom - 16
        pygame.draw.line(
            screen,
            (42, 61, 45),
            (path.x + 22, ground_y),
            (path.right - 22, ground_y),
            2,
        )
        for marker_index in range(6):
            marker_x = path.x + 34 + marker_index * 74 - int((cycle_progress * 26) % 26)
            pygame.draw.line(screen, (31, 45, 35), (marker_x, ground_y + 6), (marker_x + 28, ground_y + 6), 2)

        player_x = path.x + int(path.width * (0.30 + 0.15 * step_wave))
        player_y = ground_y
        self._draw_player_silhouette(screen, player_x, player_y, step_wave, visual_hp_ratio)

        enemy_visible = 0.15 <= cycle_progress <= 0.75
        impact_visible = 0.45 <= cycle_progress <= 0.60
        if enemy_visible:
            enemy_life = 1.0
            if cycle_progress > 0.60:
                enemy_life = max(0.0, 1.0 - ((cycle_progress - 0.60) / 0.15))
            enemy_x = player_x + 92 + int(20 * (1.0 - min(cycle_progress, 0.45) / 0.45))
            enemy_y = ground_y
            enemy_scale = 0.65 + 0.35 * enemy_life
            self._draw_enemy_shadow(screen, enemy_x, enemy_y, enemy_life)
            enemy_color = (52, 42, 43) if visual_hp_ratio >= 0.35 else (66, 36, 38)
            pygame.draw.circle(screen, enemy_color, (enemy_x, enemy_y - int(32 * enemy_scale)), int(16 * enemy_scale))
            pygame.draw.rect(
                screen,
                enemy_color,
                (enemy_x - int(12 * enemy_scale), enemy_y - int(30 * enemy_scale), int(24 * enemy_scale), int(24 * enemy_scale)),
                border_radius=4,
            )
            eye_color = (222, 54, 48) if visual_hp_ratio < 0.35 else (188, 62, 58)
            pygame.draw.circle(screen, eye_color, (enemy_x - int(5 * enemy_scale), enemy_y - int(35 * enemy_scale)), 2)
            pygame.draw.circle(screen, eye_color, (enemy_x + int(5 * enemy_scale), enemy_y - int(35 * enemy_scale)), 2)

        if impact_visible:
            self._draw_impact_effect(screen, player_x + 66, ground_y - 38, progress)

        if visual_hp_ratio < 0.15 and self._is_danger_flash_on():
            warning = self.small_font.render("Danger", True, (238, 132, 108))
            screen.blit(warning, warning.get_rect(center=(path.right - 48, path.y + 18)))

    def _draw_player_silhouette(self, screen, x, base_y, step_wave, visual_hp_ratio):
        color = (82, 132, 182) if visual_hp_ratio >= 0.35 else (92, 112, 148)
        shadow = pygame.Rect(0, 0, 44, 8)
        shadow.center = (x, base_y + 4)
        pygame.draw.ellipse(screen, (7, 10, 9), shadow)
        bob = int(3 * step_wave)
        pygame.draw.circle(screen, color, (x, base_y - 48 - bob), 11)
        pygame.draw.rect(screen, color, (x - 9, base_y - 38 - bob, 18, 28), border_radius=4)
        pygame.draw.line(screen, color, (x - 7, base_y - 12), (x - 18, base_y - int(4 * step_wave)), 4)
        pygame.draw.line(screen, color, (x + 7, base_y - 12), (x + 18, base_y - int(4 * (1.0 - step_wave))), 4)
        pygame.draw.line(screen, (226, 220, 178), (x + 10, base_y - 31 - bob), (x + 36, base_y - 38 - bob), 3)
        pygame.draw.line(screen, (226, 220, 178), (x + 30, base_y - 43 - bob), (x + 40, base_y - 35 - bob), 2)

    def _draw_enemy_shadow(self, screen, x, base_y, enemy_life):
        shadow_width = max(8, int(42 * enemy_life))
        shadow = pygame.Rect(0, 0, shadow_width, 7)
        shadow.center = (x, base_y + 4)
        pygame.draw.ellipse(screen, (8, 8, 8), shadow)

    def _draw_impact_effect(self, screen, x, y, progress):
        impact_color = (246, 232, 150) if progress < 0.78 else (244, 134, 104)
        pygame.draw.line(screen, impact_color, (x - 18, y + 10), (x + 20, y - 8), 3)
        pygame.draw.line(screen, impact_color, (x - 12, y - 10), (x + 12, y + 12), 2)
        pygame.draw.line(screen, impact_color, (x + 2, y - 20), (x + 18, y + 4), 2)

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
