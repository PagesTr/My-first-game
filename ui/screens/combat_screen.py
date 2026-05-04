import pygame


class Button:
    def __init__(self, rect, text):
        self.rect = pygame.Rect(rect)
        self.text = text

    def draw(self, screen, font):
        pygame.draw.rect(screen, (70, 70, 70), self.rect)
        pygame.draw.rect(screen, (200, 200, 200), self.rect, 2)

        label = font.render(self.text, True, (255, 255, 255))
        screen.blit(label, (self.rect.x + 10, self.rect.y + 10))

    def is_clicked(self, pos):
        return self.rect.collidepoint(pos)


class CombatScreen:
    def __init__(self, game):
        self.game = game
        self.font = pygame.font.Font(None, 32)

        # boutons
        self.attack_btn = Button((50, 450, 150, 50), "Attaquer")
        self.heal_btn = Button((220, 450, 150, 50), "Soigner")
        self.auto_btn = Button((390, 450, 150, 50), "Auto")
        self.last_auto_step = 0
        self.auto_delay = 700

    # ======================
    # INPUT
    # ======================

    def handle_event(self, event):
        if event.type == pygame.MOUSEBUTTONDOWN:
            pos = event.pos

            if self.attack_btn.is_clicked(pos):
                self.game.update_combat("attack")

            elif self.heal_btn.is_clicked(pos):
                self.game.update_combat("heal")

            elif self.auto_btn.is_clicked(pos):
                self.game.auto_mode = not self.game.auto_mode

    # ======================
    # UPDATE
    # ======================

    def update(self):
        if self.game.auto_mode:
            now = pygame.time.get_ticks()
            if now - self.last_auto_step >= self.auto_delay:
                self.game.update_combat()  # action via AI
                self.last_auto_step = now

    # ======================
    # RENDER
    # ======================

    def draw(self, screen):
        screen.fill((20, 20, 30))

        combat = self.game.combat
        if combat is None:
            return

        state = combat.get_state()

        # --- Player ---
        player_text = self.font.render(
            f"Player HP: {state['player_hp']}", True, (255, 255, 255)
        )
        screen.blit(player_text, (50, 50))

        active_effects = self.game.player.get("active_effects", [])
        log_y = 180
        if active_effects:
            effects_title = self.font.render(
                "Active effects:", True, (180, 220, 255)
            )
            screen.blit(effects_title, (50, 130))

            effect_y = 160
            for effect in active_effects[:4]:
                effect_name = effect.get("name") or effect.get("id") or "Unknown effect"
                duration_type = effect.get("duration_type")

                if duration_type == "combat" and "remaining_combats" in effect:
                    effect_name = f"{effect_name} ({effect['remaining_combats']} combats)"
                elif duration_type == "time" and "remaining_seconds" in effect:
                    effect_name = f"{effect_name} ({effect['remaining_seconds']}s)"

                effect_text = self.font.render(effect_name, True, (210, 210, 210))
                screen.blit(effect_text, (70, effect_y))
                effect_y += 28

            log_y = effect_y + 10

        # --- Enemy ---
        enemy_text = self.font.render(
            f"Enemy HP: {state['enemy_hp']}", True, (255, 100, 100)
        )
        screen.blit(enemy_text, (50, 100))

        # --- Log combat ---
        y = log_y
        for line in state["log"][-5:]:  # dernières lignes
            log_text = self.font.render(line, True, (200, 200, 200))
            screen.blit(log_text, (50, y))
            y += 30

        # --- Boutons ---
        self.attack_btn.draw(screen, self.font)
        self.heal_btn.draw(screen, self.font)

        # bouton auto (couleur dynamique)
        auto_color = (0, 150, 0) if self.game.auto_mode else (70, 70, 70)
        pygame.draw.rect(screen, auto_color, self.auto_btn.rect)
        pygame.draw.rect(screen, (200, 200, 200), self.auto_btn.rect, 2)

        auto_text = self.font.render("AUTO", True, (255, 255, 255))
        screen.blit(auto_text, (self.auto_btn.rect.x + 30, self.auto_btn.rect.y + 10))
