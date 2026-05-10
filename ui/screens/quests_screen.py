import pygame

from systems.quests import get_quest_progress


class QuestButton:
    def __init__(self, rect, label, enabled=True):
        self.rect = pygame.Rect(rect)
        self.label = label
        self.enabled = enabled

    def draw(self, screen, font, selected=False):
        bg = (65, 76, 84) if self.enabled else (45, 45, 50)
        border = (210, 220, 145) if selected else (115, 125, 135)
        text_color = (245, 245, 245) if self.enabled else (145, 145, 150)
        pygame.draw.rect(screen, bg, self.rect, border_radius=6)
        pygame.draw.rect(screen, border, self.rect, 2, border_radius=6)
        text = font.render(self._truncate(self.label, font, self.rect.w - 24), True, text_color)
        screen.blit(text, (self.rect.x + 12, self.rect.y + 12))

    def is_clicked(self, pos):
        return self.enabled and self.rect.collidepoint(pos)

    def _truncate(self, text, font, max_width):
        text = str(text or "")
        if max_width <= 0:
            return ""
        if font.size(text)[0] <= max_width:
            return text
        ellipsis = "..."
        if font.size(ellipsis)[0] > max_width:
            return ""
        while text and font.size(text + ellipsis)[0] > max_width:
            text = text[:-1]
        return text + ellipsis if text else ellipsis


class QuestScreen:
    def __init__(self, game):
        self.game = game
        self.title_font = pygame.font.Font(None, 46)
        self.option_font = pygame.font.Font(None, 30)
        self.body_font = pygame.font.Font(None, 22)
        self.back_button = QuestButton((600, 54, 120, 44), "Back")
        self.quest_buttons = []
        self.selected_quest_id = None

    def handle_event(self, event):
        if event.type != pygame.MOUSEBUTTONDOWN:
            return
        pos = event.pos
        if self.back_button.is_clicked(pos):
            self.game.state = "town"
            return
        for quest_id, button in self.quest_buttons:
            if button.is_clicked(pos):
                self.selected_quest_id = quest_id
                return

    def draw(self, screen):
        screen.fill((18, 24, 30))
        title = self.title_font.render("Quest Log", True, (245, 245, 245))
        screen.blit(title, (80, 64))
        self.back_button.draw(screen, self.option_font)

        player = self.game.player or {}
        quests_state = player.get("quests", {}) if isinstance(player, dict) else {}
        active_ids = list(quests_state.get("active", []))
        if self.selected_quest_id not in active_ids:
            self.selected_quest_id = active_ids[0] if active_ids else None

        self._draw_active_quests(screen, active_ids)
        self._draw_selected_quest(screen, self.selected_quest_id)
        self._draw_completed_quests(screen, quests_state)

    def _draw_active_quests(self, screen, active_ids):
        heading = self.option_font.render("Active", True, (245, 245, 245))
        screen.blit(heading, (80, 126))
        self.quest_buttons = []
        y = 160
        for quest_id in active_ids[:7]:
            quest = self.game.data.quests.get(quest_id, {})
            button = QuestButton((80, y, 280, 44), quest.get("name", quest_id))
            self.quest_buttons.append((quest_id, button))
            button.draw(screen, self.body_font, selected=quest_id == self.selected_quest_id)
            y += 52
        if not active_ids:
            text = self.body_font.render("No active quests", True, (150, 155, 160))
            screen.blit(text, (80, 162))

    def _draw_selected_quest(self, screen, quest_id):
        rect = pygame.Rect(390, 130, 330, 330)
        pygame.draw.rect(screen, (35, 40, 48), rect, border_radius=6)
        pygame.draw.rect(screen, (120, 130, 140), rect, 2, border_radius=6)

        if not quest_id:
            text = self.body_font.render("Select a quest", True, (150, 155, 160))
            screen.blit(text, (rect.x + 16, rect.y + 20))
            return

        quest = self.game.data.quests.get(quest_id, {})
        y = rect.y + 16
        lines = [
            quest.get("name", quest_id),
            quest.get("description", ""),
            "Objectives:",
        ]
        for line in lines:
            text = self.body_font.render(
                self._truncate_text(line, self.body_font, rect.w - 32),
                True,
                (230, 235, 225),
            )
            screen.blit(text, (rect.x + 16, y))
            y += 28

        for index, objective in enumerate(quest.get("objectives", [])):
            current = get_quest_progress(self.game.player, quest_id, index)
            required = objective.get("required", 0)
            label = self._format_objective(objective, current, required)
            text = self.body_font.render(
                self._truncate_text(label, self.body_font, rect.w - 32),
                True,
                (190, 210, 190) if current >= required else (210, 200, 175),
            )
            screen.blit(text, (rect.x + 16, y))
            y += 26

        reward_heading = self.body_font.render("Rewards:", True, (230, 235, 225))
        screen.blit(reward_heading, (rect.x + 16, y + 4))
        y += 30
        for reward in quest.get("rewards", [])[:4]:
            text = self.body_font.render(
                self._truncate_text(self._format_reward(reward), self.body_font, rect.w - 32),
                True,
                (190, 200, 210),
            )
            screen.blit(text, (rect.x + 16, y))
            y += 24

    def _draw_completed_quests(self, screen, quests_state):
        rect = pygame.Rect(390, 478, 330, 80)
        pygame.draw.rect(screen, (35, 40, 48), rect, border_radius=6)
        pygame.draw.rect(screen, (90, 100, 110), rect, 2, border_radius=6)
        title = self.body_font.render("Completed", True, (245, 245, 245))
        screen.blit(title, (rect.x + 14, rect.y + 10))
        completed = list(quests_state.get("last_completed", []))[-3:]
        if not completed:
            text = self.body_font.render("None yet", True, (150, 155, 160))
            screen.blit(text, (rect.x + 14, rect.y + 36))
            return
        names = [
            self.game.data.quests.get(quest_id, {}).get("name", quest_id)
            for quest_id in completed
        ]
        text = self.body_font.render(
            self._truncate_text(", ".join(names), self.body_font, rect.w - 28),
            True,
            (190, 200, 210),
        )
        screen.blit(text, (rect.x + 14, rect.y + 36))

    def _format_objective(self, objective, current, required):
        objective_type = objective.get("type", "objective").replace("_", " ").title()
        target = objective.get("target", "unknown").replace("_", " ").title()
        return f"{objective_type}: {target} {current}/{required}"

    def _format_reward(self, reward):
        reward_type = reward.get("type")
        if reward_type == "gold":
            return f"Gold: {reward.get('amount', 0)}"
        if reward_type == "xp":
            return f"XP: {reward.get('amount', 0)}"
        if reward_type == "item":
            item_id = reward.get("item", "unknown")
            item = self.game.data.items.get(item_id, {})
            name = item.get("name", item_id.replace("_", " ").title())
            return f"{name} x{reward.get('quantity', 1)}"
        return "Reward"

    def _truncate_text(self, text, font, max_width):
        text = str(text or "")
        if max_width <= 0:
            return ""
        if font.size(text)[0] <= max_width:
            return text
        ellipsis = "..."
        if font.size(ellipsis)[0] > max_width:
            return ""
        while text and font.size(text + ellipsis)[0] > max_width:
            text = text[:-1]
        return text + ellipsis if text else ellipsis
