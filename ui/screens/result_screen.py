import pygame


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
        self.title_font = pygame.font.Font(None, 48)
        self.font = pygame.font.Font(None, 32)
        self.continue_btn = Button((300, 530, 200, 50), "Continuer")

    def handle_event(self, event):
        if event.type == pygame.MOUSEBUTTONDOWN:
            if self.continue_btn.is_clicked(event.pos):
                self.game.continue_after_combat_result()

    def draw(self, screen):
        screen.fill((20, 20, 30))

        combat = self.game.combat
        victory = combat is not None and combat.winner == "player"
        title_text = "Victoire" if victory else "Défaite"

        result = self.game.last_combat_result or {}
        exp_gained = result.get("exp_gained", 0)
        gold_gained = result.get("gold_gained", 0)
        drops = result.get("drops", [])
        current_level = self.game.player.get("level", 1) if self.game.player else 1

        title = self.title_font.render(title_text, True, (245, 245, 245))
        screen.blit(title, (330, 120))

        xp_text = self.font.render(f"XP gagné: {exp_gained}", True, (255, 255, 255))
        gold_text = self.font.render(
            f"Gold gagné: {gold_gained}", True, (255, 220, 120)
        )

        level_text = self.font.render(
            f"Niveau actuel: {current_level}", True, (255, 255, 255)
        )

        screen.blit(xp_text, (300, 170))
        screen.blit(gold_text, (300, 210))
        screen.blit(level_text, (300, 250))

        loot_y = 300
        if result.get("leveled_up", False):
            level_up_text = self.font.render(
                "Niveau supérieur !", True, (120, 255, 160)
            )
            new_level_text = self.font.render(
                f"Nouveau niveau : {result.get('new_level', current_level)}",
                True,
                (120, 255, 160),
            )
            screen.blit(level_up_text, (300, 290))
            screen.blit(new_level_text, (300, 325))
            loot_y = 370

        loot_title = self.font.render("Loot :", True, (255, 255, 255))
        screen.blit(loot_title, (300, loot_y))

        if drops:
            for index, drop in enumerate(drops[:4]):
                loot_text = self.font.render(
                    self._format_drop(drop), True, (200, 200, 200)
                )
                screen.blit(loot_text, (300, loot_y + 35 + index * 28))
        else:
            no_loot_text = self.font.render("Aucun loot", True, (200, 200, 200))
            screen.blit(no_loot_text, (300, loot_y + 35))

        self.continue_btn.draw(screen, self.font)

    def _format_drop(self, drop):
        item_id = drop["item"]
        item_data = self.game.data.items.get(item_id, {})
        item_name = item_data.get("name", item_id)
        kind = drop.get("kind")

        if kind == "stackable":
            return f"- {item_name} x {drop.get('quantity', 1)}"

        if kind == "unique":
            stats_text = self._format_stats(drop.get("stats", {}))
            if stats_text:
                return f"- {item_name} ({stats_text})"
            return f"- {item_name}"

        return f"- {item_name}"

    def _format_stats(self, stats):
        parts = []
        for stat, value in stats.items():
            parts.append(f"{stat} +{value}")
        return ", ".join(parts)
