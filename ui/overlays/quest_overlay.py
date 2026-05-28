import pygame

from systems.quests import get_quest_progress


class QuestOverlay:
    def __init__(self, game):
        if not pygame.font.get_init():
            pygame.font.init()

        self.game = game
        self.opened = False
        self.selected_quest_id = None
        self.title_font = pygame.font.Font(None, 38)
        self.header_font = pygame.font.Font(None, 27)
        self.body_font = pygame.font.Font(None, 22)
        self.small_font = pygame.font.Font(None, 18)
        self.panel_rect = pygame.Rect(0, 0, 0, 0)
        self.close_rect = pygame.Rect(0, 0, 0, 0)
        self.list_rect = pygame.Rect(0, 0, 0, 0)
        self.detail_rect = pygame.Rect(0, 0, 0, 0)
        self.completed_rect = pygame.Rect(0, 0, 0, 0)
        self.quest_row_rects = []

    def open(self):
        self.opened = True
        self._select_first_active_quest_if_needed()

    def close(self):
        self.opened = False

    def is_open(self):
        return self.opened

    def handle_event(self, event):
        if not self.opened:
            return False

        if event.type == pygame.KEYDOWN:
            if event.key in (pygame.K_ESCAPE, pygame.K_j):
                self.close()
            return True

        if event.type != pygame.MOUSEBUTTONDOWN or event.button != 1:
            return False

        position = event.pos
        if not self.panel_rect.collidepoint(position):
            self.close()
            return True

        if self.close_rect.collidepoint(position):
            self.close()
            return True

        for quest_id, rect in self.quest_row_rects:
            if rect.collidepoint(position):
                self.selected_quest_id = quest_id
                return True

        return True

    def draw(self, screen):
        if not self.opened:
            return

        self._draw_overlay_background(screen)
        self.panel_rect = self._get_panel_rect(screen)
        self._layout_rects()
        self._draw_panel(screen, self.panel_rect, "Journal de quetes")
        self.close_rect = pygame.Rect(self.panel_rect.right - 48, self.panel_rect.y + 14, 30, 28)
        self._draw_button(screen, self.close_rect, "X")

        if not isinstance(getattr(self.game, "player", None), dict):
            self._draw_message(screen, "Aucune quete disponible")
            return

        quests_data = getattr(getattr(self.game, "data", None), "quests", {})
        if not isinstance(quests_data, dict):
            self._draw_message(screen, "Aucune quete disponible")
            return

        active_quest_ids = self._get_active_quest_ids()
        if self.selected_quest_id not in active_quest_ids:
            self.selected_quest_id = active_quest_ids[0] if active_quest_ids else None

        self.quest_row_rects = []
        self._draw_active_quests(screen, active_quest_ids)
        self._draw_selected_quest(screen, self.selected_quest_id)
        self._draw_recently_completed(screen)

    def _get_panel_rect(self, screen):
        width, height = screen.get_size()
        panel_width = min(width - 28, max(760, int(width * 0.9)))
        panel_height = min(height - 70, max(500, int(height * 0.82)))
        panel_width = max(620, min(panel_width, width - 20))
        panel_height = max(480, min(panel_height, height - 62))
        return pygame.Rect((width - panel_width) // 2, 24, panel_width, panel_height)

    def _layout_rects(self):
        panel = self.panel_rect
        top = panel.y + 70
        bottom = panel.bottom - 18
        completed_height = 86
        gap = 14
        list_width = max(240, int((panel.w - 50) * 0.36))
        self.list_rect = pygame.Rect(panel.x + 18, top, list_width, bottom - top)
        detail_height = bottom - top - completed_height - gap
        self.detail_rect = pygame.Rect(self.list_rect.right + gap, top, panel.right - self.list_rect.right - gap - 18, detail_height)
        self.completed_rect = pygame.Rect(self.detail_rect.x, self.detail_rect.bottom + gap, self.detail_rect.w, completed_height)

    def _draw_overlay_background(self, screen):
        overlay = pygame.Surface(screen.get_size(), pygame.SRCALPHA)
        overlay.fill((0, 0, 0, 170))
        screen.blit(overlay, (0, 0))

    def _draw_panel(self, screen, rect, title):
        pygame.draw.rect(screen, (34, 27, 22), rect, border_radius=8)
        pygame.draw.rect(screen, (171, 132, 70), rect, 2, border_radius=8)
        pygame.draw.rect(screen, (78, 56, 36), rect.inflate(-8, -8), 1, border_radius=6)
        text = self.title_font.render(title, True, (246, 235, 205))
        screen.blit(text, (rect.x + 20, rect.y + 12))

    def _draw_message(self, screen, message):
        text = self.body_font.render(message, True, (236, 224, 195))
        screen.blit(text, (self.panel_rect.x + 24, self.panel_rect.y + 76))

    def _draw_active_quests(self, screen, active_quest_ids):
        self._draw_box(screen, self.list_rect)
        title = self.header_font.render("Quetes actives", True, (246, 235, 205))
        screen.blit(title, (self.list_rect.x + 12, self.list_rect.y + 10))

        if not active_quest_ids:
            text = self.body_font.render("Aucune quete active", True, (160, 168, 176))
            screen.blit(text, (self.list_rect.x + 14, self.list_rect.y + 48))
            return

        y = self.list_rect.y + 44
        row_height = 44
        for quest_id in active_quest_ids:
            if y + row_height > self.list_rect.bottom - 10:
                remaining = len(active_quest_ids) - len(self.quest_row_rects)
                text = self.small_font.render(f"+{remaining} autres quetes", True, (160, 168, 176))
                screen.blit(text, (self.list_rect.x + 14, self.list_rect.bottom - 26))
                break
            quest = self._get_quest_data(quest_id)
            row = pygame.Rect(self.list_rect.x + 10, y, self.list_rect.w - 20, row_height - 7)
            self.quest_row_rects.append((quest_id, row))
            self._draw_button(
                screen,
                row,
                quest.get("name", quest_id) or quest_id,
                active=quest_id == self.selected_quest_id,
            )
            y += row_height

    def _draw_selected_quest(self, screen, quest_id):
        self._draw_box(screen, self.detail_rect)
        if not quest_id:
            text = self.body_font.render("Selectionne une quete", True, (160, 168, 176))
            screen.blit(text, (self.detail_rect.x + 14, self.detail_rect.y + 16))
            return

        quest = self._get_quest_data(quest_id)
        total_current, total_required = self._get_quest_progress_summary(quest_id, quest)
        x = self.detail_rect.x + 14
        y = self.detail_rect.y + 12

        title = self.header_font.render(
            self._truncate_text(quest.get("name", quest_id) or quest_id, self.header_font, self.detail_rect.w - 28),
            True,
            (246, 235, 205),
        )
        screen.blit(title, (x, y))
        y += 30

        for line in self._wrap_text(quest.get("description", ""), self.small_font, self.detail_rect.w - 28, 3):
            text = self.small_font.render(line, True, (210, 218, 220))
            screen.blit(text, (x, y))
            y += 18

        y += 3
        progress = self.body_font.render(f"Progression : {total_current} / {total_required}", True, (230, 224, 180))
        screen.blit(progress, (x, y))
        y += 22
        self._draw_progress_bar(screen, pygame.Rect(x, y, self.detail_rect.w - 28, 12), total_current, total_required)
        y += 24

        heading = self.body_font.render("Objectifs", True, (246, 235, 205))
        screen.blit(heading, (x, y))
        y += 22
        objectives = quest.get("objectives", []) if isinstance(quest.get("objectives"), list) else []
        for index, objective in enumerate(objectives[:5]):
            current = get_quest_progress(getattr(self.game, "player", {}), quest_id, index)
            required = self._get_required_amount(objective)
            label = self._format_objective(objective, current, required)
            color = (145, 215, 160) if required > 0 and current >= required else (220, 208, 178)
            text = self.small_font.render(self._truncate_text(label, self.small_font, self.detail_rect.w - 28), True, color)
            screen.blit(text, (x, y))
            y += 18

        y += 3
        reward_title = self.body_font.render("Recompenses", True, (246, 235, 205))
        screen.blit(reward_title, (x, y))
        y += 22
        rewards = quest.get("rewards", []) if isinstance(quest.get("rewards"), list) else []
        if not rewards:
            text = self.small_font.render("Aucune recompense", True, (160, 168, 176))
            screen.blit(text, (x, y))
        for reward in rewards[:4]:
            text = self.small_font.render(
                self._truncate_text(f"- {self._format_reward(reward)}", self.small_font, self.detail_rect.w - 28),
                True,
                (205, 220, 190),
            )
            screen.blit(text, (x, y))
            y += 18

        mood = self._get_quest_mood_line(total_current, total_required)
        text = self.small_font.render(self._truncate_text(mood, self.small_font, self.detail_rect.w - 28), True, (170, 180, 170))
        screen.blit(text, (x, self.detail_rect.bottom - 22))

    def _draw_recently_completed(self, screen):
        self._draw_box(screen, self.completed_rect)
        title = self.body_font.render("Terminees recemment", True, (246, 235, 205))
        screen.blit(title, (self.completed_rect.x + 12, self.completed_rect.y + 8))

        completed = self._get_quests_state().get("last_completed", [])
        completed = completed[-3:] if isinstance(completed, list) else []
        if not completed:
            text = self.small_font.render("Aucune terminee recemment", True, (160, 168, 176))
            screen.blit(text, (self.completed_rect.x + 12, self.completed_rect.y + 36))
            return

        x = self.completed_rect.x + 12
        y = self.completed_rect.y + 34
        for quest_id in completed:
            quest = self._get_quest_data(quest_id)
            name = quest.get("name", quest_id) if isinstance(quest, dict) else quest_id
            text = self.small_font.render(self._truncate_text(str(name), self.small_font, self.completed_rect.w - 24), True, (205, 220, 190))
            screen.blit(text, (x, y))
            y += 16

    def _draw_box(self, screen, rect):
        pygame.draw.rect(screen, (31, 28, 25), rect, border_radius=6)
        pygame.draw.rect(screen, (118, 91, 54), rect, 2, border_radius=6)

    def _draw_button(self, screen, rect, label, active=False, enabled=True):
        bg = (80, 58, 35) if active else (44, 37, 32) if enabled else (38, 35, 32)
        border = (235, 198, 92) if active else (105, 82, 52) if enabled else (74, 68, 62)
        color = (246, 235, 205) if enabled else (130, 124, 116)
        pygame.draw.rect(screen, bg, rect, border_radius=5)
        pygame.draw.rect(screen, border, rect, 2 if active else 1, border_radius=5)
        text = self.body_font.render(self._truncate_text(label, self.body_font, rect.w - 12), True, color)
        screen.blit(text, text.get_rect(center=rect.center))

    def _get_quests_state(self):
        player = getattr(self.game, "player", None)
        if not isinstance(player, dict):
            return {"active": [], "completed": [], "progress": {}, "last_completed": []}
        quests = player.get("quests", {})
        if not isinstance(quests, dict):
            return {"active": [], "completed": [], "progress": {}, "last_completed": []}
        return {
            "active": quests.get("active", []) if isinstance(quests.get("active"), list) else [],
            "completed": quests.get("completed", []) if isinstance(quests.get("completed"), list) else [],
            "progress": quests.get("progress", {}) if isinstance(quests.get("progress"), dict) else {},
            "last_completed": quests.get("last_completed", []) if isinstance(quests.get("last_completed"), list) else [],
        }

    def _get_active_quest_ids(self):
        return list(self._get_quests_state().get("active", []))

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

    def _get_required_amount(self, objective):
        if not isinstance(objective, dict):
            return 0
        required = objective.get("required", 0)
        return required if isinstance(required, int) and required > 0 else 0

    def _get_objective_target_label(self, objective):
        if not isinstance(objective, dict):
            return "Inconnu"
        target = objective.get("target", "unknown")
        objective_type = objective.get("type")
        if objective_type == "kill_enemy":
            enemy = self._get_enemies_data().get(target, {})
            return enemy.get("name", self._titleize_id(target)) if isinstance(enemy, dict) else self._titleize_id(target)
        if objective_type == "gather_item":
            item = self._get_items_data().get(target, {})
            return item.get("name", self._titleize_id(target)) if isinstance(item, dict) else self._titleize_id(target)
        if objective_type == "craft_recipe":
            recipe = self._get_recipes_data().get(target, {})
            result = recipe.get("result", {}) if isinstance(recipe, dict) else {}
            item_id = result.get("item") if isinstance(result, dict) else None
            if item_id:
                item = self._get_items_data().get(item_id, {})
                return item.get("name", self._titleize_id(item_id)) if isinstance(item, dict) else self._titleize_id(item_id)
            return self._titleize_id(target)
        return self._titleize_id(target)

    def _format_objective(self, objective, current, required):
        objective_type = objective.get("type") if isinstance(objective, dict) else None
        target = self._get_objective_target_label(objective)
        labels = {
            "kill_enemy": "Vaincre",
            "gather_item": "Recolter",
            "craft_recipe": "Fabriquer",
        }
        marker = "OK" if required > 0 and current >= required else "O"
        action = labels.get(objective_type, str(objective_type or "Objectif"))
        return f"{marker} {action} {target} {current}/{required}"

    def _format_reward(self, reward):
        if not isinstance(reward, dict):
            return "Recompense"
        reward_type = reward.get("type")
        if reward_type == "gold":
            return f"+{reward.get('amount', 0)} gold"
        if reward_type == "xp":
            return f"+{reward.get('amount', 0)} XP"
        if reward_type == "item":
            item_id = reward.get("item", "unknown")
            item = self._get_items_data().get(item_id, {})
            name = item.get("name", self._titleize_id(item_id)) if isinstance(item, dict) else self._titleize_id(item_id)
            return f"+{reward.get('quantity', 1)} {name}"
        return "Recompense"

    def _get_quest_progress_summary(self, quest_id, quest):
        total_current = 0
        total_required = 0
        objectives = quest.get("objectives", []) if isinstance(quest, dict) and isinstance(quest.get("objectives"), list) else []
        for index, objective in enumerate(objectives):
            required = self._get_required_amount(objective)
            current = min(get_quest_progress(getattr(self.game, "player", {}), quest_id, index), required)
            total_current += current
            total_required += required
        return total_current, total_required

    def _draw_progress_bar(self, screen, rect, current, total):
        pygame.draw.rect(screen, (20, 24, 28), rect, border_radius=5)
        ratio = 0 if total <= 0 else max(0, min(current / total, 1))
        fill = pygame.Rect(rect.x, rect.y, int(rect.w * ratio), rect.h)
        if fill.w > 0:
            pygame.draw.rect(screen, (120, 178, 104), fill, border_radius=5)
        pygame.draw.rect(screen, (130, 110, 72), rect, 1, border_radius=5)

    def _get_quest_mood_line(self, current, total):
        if total > 0 and current >= total:
            return "Termine. Contre toute attente."
        if total > 0 and current >= max(1, total - 1):
            return "Presque termine. C'est souvent le moment ou tout derape."
        return "Le plan est simple. C'est souvent mauvais signe."

    def _select_first_active_quest_if_needed(self):
        active_quest_ids = self._get_active_quest_ids()
        if self.selected_quest_id not in active_quest_ids:
            self.selected_quest_id = active_quest_ids[0] if active_quest_ids else None

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

    def _titleize_id(self, value):
        return str(value or "unknown").replace("_", " ").title()
