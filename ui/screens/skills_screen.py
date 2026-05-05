import pygame

from systems.stats import prepare_player_for_combat
from systems.skills import (
    equip_skill,
    get_available_class_skills,
    get_player_skill_state,
    get_skill_type,
    is_skill_equipped,
    learn_or_upgrade_skill,
    spend_skill_point,
    unequip_skill,
)


class Button:
    def __init__(self, rect, text):
        self.rect = pygame.Rect(rect)
        self.text = text

    def draw(self, screen, font):
        pygame.draw.rect(screen, (58, 68, 78), self.rect, border_radius=6)
        pygame.draw.rect(screen, (210, 220, 225), self.rect, 2, border_radius=6)
        label = font.render(self.text, True, (245, 245, 245))
        screen.blit(label, (self.rect.x + 14, self.rect.y + 12))

    def is_clicked(self, pos):
        return self.rect.collidepoint(pos)


class SkillsScreen:
    def __init__(self, game):
        self.game = game
        self.title_font = pygame.font.Font(None, 44)
        self.option_font = pygame.font.Font(None, 28)
        self.body_font = pygame.font.Font(None, 22)
        self.back_button = Button((620, 48, 120, 48), "Back")
        self.skill_rows = []
        self.equip_buttons = []

    def handle_event(self, event):
        if event.type != pygame.MOUSEBUTTONDOWN:
            return

        pos = event.pos
        if self.back_button.is_clicked(pos):
            self.game.state = "town"
            return

        player = self.game.player
        if not player:
            return

        for skill_id, rect in self.equip_buttons:
            if rect.collidepoint(pos):
                if is_skill_equipped(player, skill_id):
                    unequip_skill(player, skill_id)
                else:
                    equip_skill(player, skill_id)
                return

        for skill_id, rect in self.skill_rows:
            if rect.collidepoint(pos):
                if player.get("skill_points", 0) <= 0:
                    return
                if learn_or_upgrade_skill(player, skill_id):
                    spend_skill_point(player)
                    previous_max_hp = self.game.player.get("max_hp", 0)
                    prepare_player_for_combat(
                        self.game.player,
                        self.game.data.items,
                        self.game.data.classes,
                        self.game.data.skills,
                    )
                    new_max_hp = self.game.player.get("max_hp", 0)
                    max_hp_gain = new_max_hp - previous_max_hp
                    if max_hp_gain > 0:
                        self.game.player["current_hp"] = min(
                            new_max_hp,
                            self.game.player.get("current_hp", 0) + max_hp_gain,
                        )
                return

    def draw(self, screen):
        screen.fill((18, 24, 30))
        self.skill_rows = []
        self.equip_buttons = []

        title = self.title_font.render("Skills", True, (245, 245, 245))
        screen.blit(title, (60, 48))
        self.back_button.draw(screen, self.option_font)

        player = self.game.player or {}
        points = self.body_font.render(
            f"Skill points: {player.get('skill_points', 0)}",
            True,
            (210, 220, 225),
        )
        enhanced_points = self.body_font.render(
            f"Enhanced points: {player.get('enhanced_skill_points', 0)}",
            True,
            (210, 220, 225),
        )
        screen.blit(points, (62, 100))
        screen.blit(enhanced_points, (62, 126))

        y = 170
        for skill_id, skill_data in get_available_class_skills(self.game.data.skills, player):
            y = self._draw_skill_row(screen, skill_id, skill_data, y)

    def _draw_skill_row(self, screen, skill_id, skill_data, y):
        player = self.game.player or {}
        rect = pygame.Rect(60, y, 680, 82)
        pygame.draw.rect(screen, (34, 42, 50), rect, border_radius=6)
        pygame.draw.rect(screen, (105, 120, 132), rect, 2, border_radius=6)
        self.skill_rows.append((skill_id, rect))

        skill_type = get_skill_type(self.game.data.skills, skill_id)
        skill_state = get_player_skill_state(player, skill_id)
        level = skill_state["level"]
        enhanced = skill_state["enhanced"]

        if level == 0:
            action_text = "Learn"
        elif level < 4:
            action_text = "Upgrade"
        else:
            action_text = "Max"

        name = skill_data.get("name", skill_id)
        title = self.option_font.render(name, True, (245, 245, 245))
        screen.blit(title, (rect.x + 16, rect.y + 12))

        details = f"{skill_type} | Level {level} | {action_text}"
        if enhanced:
            details = f"{details} | Enhanced"
        detail_text = self.body_font.render(details, True, (190, 200, 205))
        screen.blit(detail_text, (rect.x + 16, rect.y + 46))

        if level > 0 and skill_type == "active":
            equip_text = "Equipped" if is_skill_equipped(player, skill_id) else "Not equipped"
            equip_rect = pygame.Rect(rect.right - 160, rect.y + 22, 130, 38)
            pygame.draw.rect(screen, (58, 68, 78), equip_rect, border_radius=5)
            pygame.draw.rect(screen, (210, 220, 225), equip_rect, 2, border_radius=5)
            label = self.body_font.render(equip_text, True, (245, 245, 245))
            screen.blit(label, (equip_rect.x + 10, equip_rect.y + 10))
            self.equip_buttons.append((skill_id, equip_rect))
        elif level > 0 and skill_type == "passive":
            passive_text = self.body_font.render(
                "Passive active",
                True,
                (145, 220, 165),
            )
            screen.blit(passive_text, (rect.right - 150, rect.y + 34))

        return y + 96
