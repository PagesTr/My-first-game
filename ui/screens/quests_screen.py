import pygame

from systems.quests import get_quest_progress


class QuestButton:
    def __init__(self, rect, label, enabled=True):
        self.rect = pygame.Rect(rect)
        self.label = label
        self.enabled = enabled

    def draw(self, screen, font, selected=False):
        bg = (72, 84, 72) if selected else (65, 76, 84)
        if not self.enabled:
            bg = (45, 45, 50)
        border = (235, 220, 145) if selected else (115, 125, 135)
        text_color = (245, 245, 245) if self.enabled else (145, 145, 150)
        pygame.draw.rect(screen, bg, self.rect, border_radius=6)
        pygame.draw.rect(screen, border, self.rect, 3 if selected else 2, border_radius=6)
        marker = "> " if selected else ""
        label = self._truncate(f"{marker}{self.label}", font, self.rect.w - 24)
        text = font.render(label, True, text_color)
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
        self.small_font = pygame.font.Font(None, 20)
        self.back_button = QuestButton((600, 54, 120, 44), "Retour")
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
        title = self.title_font.render("Journal de quêtes", True, (245, 245, 245))
        screen.blit(title, (80, 64))
        self.back_button.draw(screen, self.option_font)

        player = self.game.player or {}
        quests_state = player.get("quests", {}) if isinstance(player, dict) else {}
        active_ids = list(quests_state.get("active", [])) if isinstance(quests_state, dict) else []
        if self.selected_quest_id not in active_ids:
            self.selected_quest_id = active_ids[0] if active_ids else None

        self._draw_active_quests(screen, active_ids)
        self._draw_selected_quest(screen, self.selected_quest_id)
        self._draw_completed_quests(screen, quests_state)

    def _draw_active_quests(self, screen, active_ids):
        panel = pygame.Rect(70, 120, 300, 438)
        pygame.draw.rect(screen, (30, 35, 42), panel, border_radius=6)
        pygame.draw.rect(screen, (95, 105, 115), panel, 2, border_radius=6)
        heading = self.option_font.render("Quêtes actives", True, (245, 245, 245))
        screen.blit(heading, (panel.x + 14, panel.y + 12))
        self.quest_buttons = []
        y = panel.y + 52
        for quest_id in active_ids[:7]:
            quest = self._get_quest_data(quest_id)
            button = QuestButton((panel.x + 14, y, 272, 44), quest.get("name", quest_id))
            self.quest_buttons.append((quest_id, button))
            button.draw(screen, self.body_font, selected=quest_id == self.selected_quest_id)
            y += 52
        if len(active_ids) > 7:
            remaining = len(active_ids) - 7
            text = self.body_font.render(f"+{remaining} autres quêtes", True, (175, 185, 190))
            screen.blit(text, (panel.x + 18, y + 4))
        if not active_ids:
            text = self.body_font.render("Aucune quête active", True, (150, 155, 160))
            screen.blit(text, (panel.x + 18, panel.y + 60))

    def _draw_selected_quest(self, screen, quest_id):
        rect = pygame.Rect(390, 120, 330, 342)
        pygame.draw.rect(screen, (35, 40, 48), rect, border_radius=6)
        pygame.draw.rect(screen, (120, 130, 140), rect, 2, border_radius=6)

        if not quest_id:
            text = self.body_font.render("Sélectionne une quête", True, (150, 155, 160))
            screen.blit(text, (rect.x + 16, rect.y + 20))
            return

        quest = self._get_quest_data(quest_id)
        total_current, total = self._get_quest_progress_summary(quest_id, quest)
        y = rect.y + 14

        name = self._truncate_text(quest.get("name", quest_id), self.option_font, rect.w - 32)
        name_text = self.option_font.render(name, True, (245, 245, 245))
        screen.blit(name_text, (rect.x + 16, y))
        y += 32

        description_lines = self._wrap_text(
            quest.get("description", ""),
            self.small_font,
            rect.w - 32,
            2,
        )
        for line in description_lines:
            text = self.body_font.render(
                self._truncate_text(line, self.body_font, rect.w - 32),
                True,
                (190, 200, 205),
            )
            screen.blit(text, (rect.x + 16, y))
            y += 20

        y += 4
        progress_text = self.body_font.render(
            f"Progression : {total_current} / {total}",
            True,
            (230, 235, 225),
        )
        screen.blit(progress_text, (rect.x + 16, y))
        y += 24
        self._draw_progress_bar(
            screen,
            pygame.Rect(rect.x + 16, y, rect.w - 32, 12),
            total_current,
            total,
        )
        y += 24

        heading = self.body_font.render("Objectifs", True, (245, 245, 245))
        screen.blit(heading, (rect.x + 16, y))
        y += 24

        for index, objective in enumerate(quest.get("objectives", [])[:4]):
            current = get_quest_progress(self.game.player, quest_id, index)
            required = self._get_required_amount(objective)
            label = self._format_objective(objective, current, required)
            text = self.body_font.render(
                self._truncate_text(label, self.body_font, rect.w - 32),
                True,
                (145, 215, 160) if current >= required else (210, 200, 175),
            )
            screen.blit(text, (rect.x + 16, y))
            y += 22

        y += 4
        reward_heading = self.body_font.render("Récompenses", True, (245, 245, 245))
        screen.blit(reward_heading, (rect.x + 16, y))
        y += 24
        for reward in quest.get("rewards", [])[:3]:
            text = self.body_font.render(
                self._truncate_text(f"• {self._format_reward(reward)}", self.body_font, rect.w - 32),
                True,
                (190, 200, 210),
            )
            screen.blit(text, (rect.x + 16, y))
            y += 20

        mood = self._get_quest_mood_line(total_current, total)
        mood_text = self.small_font.render(
            self._truncate_text(mood, self.small_font, rect.w - 32),
            True,
            (170, 180, 170),
        )
        screen.blit(mood_text, (rect.x + 16, rect.bottom - 24))

    def _draw_completed_quests(self, screen, quests_state):
        rect = pygame.Rect(390, 478, 330, 80)
        pygame.draw.rect(screen, (35, 40, 48), rect, border_radius=6)
        pygame.draw.rect(screen, (90, 100, 110), rect, 2, border_radius=6)
        title = self.body_font.render("Terminées récemment", True, (245, 245, 245))
        screen.blit(title, (rect.x + 14, rect.y + 10))
        completed = (
            list(quests_state.get("last_completed", []))[-3:]
            if isinstance(quests_state, dict)
            else []
        )
        if not completed:
            text = self.body_font.render("Aucune pour l'instant", True, (150, 155, 160))
            screen.blit(text, (rect.x + 14, rect.y + 36))
            return
        y = rect.y + 34
        for quest_id in completed:
            quest = self._get_quest_data(quest_id)
            text = self.body_font.render(
                self._truncate_text(quest.get("name", quest_id), self.body_font, rect.w - 28),
                True,
                (190, 200, 210),
            )
            screen.blit(text, (rect.x + 14, y))
            y += 18

    def _format_objective(self, objective, current, required):
        objective_type = objective.get("type") if isinstance(objective, dict) else None
        target = self._get_objective_target_label(objective)
        labels = {
            "kill_enemy": "Vaincre",
            "gather_item": "Récolter",
            "craft_recipe": "Fabriquer",
        }
        prefix = "✓" if current >= required else "○"
        action = labels.get(objective_type, str(objective_type or "Objectif"))
        return f"{prefix} {action} {target} {current}/{required}"

    def _format_reward(self, reward):
        if not isinstance(reward, dict):
            return "Récompense"
        reward_type = reward.get("type")
        if reward_type == "gold":
            return f"+{reward.get('amount', 0)} gold"
        if reward_type == "xp":
            return f"+{reward.get('amount', 0)} XP"
        if reward_type == "item":
            item_id = reward.get("item", "unknown")
            item = self._get_items_data().get(item_id, {})
            name = item.get("name", item_id.replace("_", " ").title())
            return f"+{reward.get('quantity', 1)} {name}"
        return "Récompense"

    def _get_quest_progress_summary(self, quest_id, quest):
        total_current = 0
        total_required = 0
        for index, objective in enumerate(quest.get("objectives", [])):
            required = self._get_required_amount(objective)
            current = min(get_quest_progress(self.game.player, quest_id, index), required)
            total_current += current
            total_required += required
        return total_current, total_required

    def _draw_progress_bar(self, screen, rect, current, total):
        pygame.draw.rect(screen, (24, 28, 34), rect, border_radius=5)
        pygame.draw.rect(screen, (85, 95, 105), rect, 1, border_radius=5)
        if total <= 0:
            return
        ratio = max(0, min(1, current / total))
        fill_rect = pygame.Rect(rect.x, rect.y, int(rect.w * ratio), rect.h)
        if fill_rect.w > 0:
            pygame.draw.rect(screen, (120, 190, 125), fill_rect, border_radius=5)

    def _get_quest_mood_line(self, current, total):
        if total > 0 and current >= total:
            return "Terminé. Contre toute attente."
        if total > 0 and current >= max(1, total - 1):
            return "Presque terminé. Ce qui est généralement le moment où tout dérape."
        return "Le plan est simple. C'est souvent mauvais signe."

    def _get_objective_target_label(self, objective):
        if not isinstance(objective, dict):
            return "Inconnu"
        target = objective.get("target", "unknown")
        objective_type = objective.get("type")
        if objective_type == "kill_enemy":
            enemy = self._get_enemies_data().get(target, {})
            return enemy.get("name", self._titleize_id(target))
        if objective_type == "gather_item":
            item = self._get_items_data().get(target, {})
            return item.get("name", self._titleize_id(target))
        if objective_type == "craft_recipe":
            recipe = self._get_recipes_data().get(target, {})
            result = recipe.get("result", {}) if isinstance(recipe, dict) else {}
            item_id = result.get("item") if isinstance(result, dict) else None
            if item_id:
                item = self._get_items_data().get(item_id, {})
                return item.get("name", self._titleize_id(item_id))
            return self._titleize_id(target)
        return self._titleize_id(target)

    def _get_required_amount(self, objective):
        if not isinstance(objective, dict):
            return 0
        required = objective.get("required", 0)
        return required if isinstance(required, int) and required > 0 else 0

    def _get_quest_data(self, quest_id):
        quests = getattr(getattr(self.game, "data", None), "quests", {}) or {}
        quest = quests.get(quest_id, {}) if isinstance(quests, dict) else {}
        return quest if isinstance(quest, dict) else {}

    def _get_items_data(self):
        items = getattr(getattr(self.game, "data", None), "items", {}) or {}
        return items if isinstance(items, dict) else {}

    def _get_enemies_data(self):
        enemies = getattr(getattr(self.game, "data", None), "enemies", {}) or {}
        return enemies if isinstance(enemies, dict) else {}

    def _get_recipes_data(self):
        recipes = getattr(getattr(self.game, "data", None), "recipes", {}) or {}
        return recipes if isinstance(recipes, dict) else {}

    def _titleize_id(self, value):
        return str(value or "unknown").replace("_", " ").title()

    def _wrap_text(self, text, font, max_width, max_lines):
        words = str(text or "").split()
        lines = []
        current = ""
        for word in words:
            candidate = f"{current} {word}".strip()
            if font.size(candidate)[0] <= max_width:
                current = candidate
                continue
            if current:
                lines.append(current)
            current = word
            if len(lines) >= max_lines:
                break
        if current and len(lines) < max_lines:
            lines.append(current)
        if not lines:
            return [""]
        if len(lines) == max_lines and len(" ".join(words)) > len(" ".join(lines)):
            lines[-1] = self._truncate_text(lines[-1], font, max_width)
        return lines

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
