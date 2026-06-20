import pygame

from systems.dialogues import apply_npc_conversation_result
from systems.quests import get_quest_progress


OVERLAY_DIM = (0, 0, 0, 170)
PANEL_BG = (28, 25, 20)
BORDER = (205, 170, 80)
TEXT_PRIMARY = (238, 232, 205)
TEXT_SECONDARY = (190, 184, 160)
BUTTON_BG = (52, 48, 38)
BUTTON_HOVER = (68, 62, 46)


class NPCDialogueOverlay:
    def __init__(self, game):
        if not pygame.font.get_init():
            pygame.font.init()

        self.game = game
        self.opened = False
        self.npc = None
        self.conversation = None
        self.page_index = 0
        self.last_result = None
        self.speaker_font = pygame.font.Font(None, 30)
        self.body_font = pygame.font.Font(None, 24)
        self.small_font = pygame.font.Font(None, 20)
        self.button_font = pygame.font.Font(None, 22)
        self.panel_rect = pygame.Rect(0, 0, 0, 0)
        self.continue_rect = pygame.Rect(0, 0, 0, 0)

    def open(self, npc, conversation):
        pages = conversation.get("pages", []) if isinstance(conversation, dict) else []
        if not isinstance(npc, dict) or not isinstance(pages, list) or not pages:
            return False
        self.npc = npc
        self.conversation = conversation
        self.page_index = 0
        self.last_result = None
        self.opened = True
        return True

    def close(self):
        self.opened = False

    def is_open(self):
        return self.opened

    def handle_event(self, event):
        if not self.opened:
            return False

        if event.type == pygame.KEYDOWN:
            if event.key == pygame.K_ESCAPE:
                self.close()
                return True
            if event.key in (pygame.K_e, pygame.K_RETURN, pygame.K_SPACE):
                self._advance()
                return True

        if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
            if self.continue_rect.collidepoint(event.pos):
                self._advance()
                return True
        return False

    def draw(self, screen):
        if not self.opened:
            return

        overlay = pygame.Surface(screen.get_size(), pygame.SRCALPHA)
        overlay.fill(OVERLAY_DIM)
        screen.blit(overlay, (0, 0))

        page = self._get_current_page()
        is_quest_summary = page.get("state") == "quest_summary"
        width = min(screen.get_width() - 40, 760)
        preferred_height = 380 if is_quest_summary else 220
        height = min(preferred_height, screen.get_height() - 40)
        self.panel_rect = pygame.Rect(
            (screen.get_width() - width) // 2,
            screen.get_height() - height - 24,
            width,
            height,
        )
        pygame.draw.rect(screen, PANEL_BG, self.panel_rect, border_radius=8)
        pygame.draw.rect(screen, BORDER, self.panel_rect, 2, border_radius=8)

        speaker = self.npc.get("display_name") or self.npc.get("name") or "NPC"
        speaker_text = self.speaker_font.render(str(speaker), True, TEXT_PRIMARY)
        screen.blit(speaker_text, (self.panel_rect.x + 22, self.panel_rect.y + 18))

        if is_quest_summary:
            self._draw_quest_summary(screen, page)
        else:
            y = self.panel_rect.y + 58
            for line in self._wrap_text(page.get("text", ""), self.body_font, self.panel_rect.w - 44, 5):
                text = self.body_font.render(line, True, TEXT_SECONDARY)
                screen.blit(text, (self.panel_rect.x + 22, y))
                y += 25

        self.continue_rect = pygame.Rect(self.panel_rect.right - 154, self.panel_rect.bottom - 48, 132, 30)
        hovered = self.continue_rect.collidepoint(pygame.mouse.get_pos())
        pygame.draw.rect(
            screen,
            BUTTON_HOVER if hovered else BUTTON_BG,
            self.continue_rect,
            border_radius=5,
        )
        pygame.draw.rect(screen, BORDER, self.continue_rect, 1, border_radius=5)
        label = self._get_action_label()
        label_text = self.button_font.render(label, True, TEXT_PRIMARY)
        screen.blit(label_text, label_text.get_rect(center=self.continue_rect.center))

    def _advance(self):
        pages = self.conversation.get("pages", [])
        if self.page_index < len(pages) - 1:
            self.page_index += 1
            return

        self.last_result = apply_npc_conversation_result(
            self.game.player,
            self.game.data.quests,
            self.conversation,
        )
        self.opened = False
        self.game.save_current_game()

    def _get_current_page(self):
        pages = self.conversation.get("pages", []) if isinstance(self.conversation, dict) else []
        if not pages:
            return {}
        return pages[min(self.page_index, len(pages) - 1)]

    def _get_action_label(self):
        pages = self.conversation.get("pages", [])
        if self.page_index < len(pages) - 1:
            return "Continue"
        if self.conversation.get("accept_quest_id"):
            return "Accept quest"
        return "Close"

    def _draw_quest_summary(self, screen, page):
        quest_id = page.get("quest_id")
        quests = getattr(getattr(self.game, "data", None), "quests", {})
        quest = quests.get(quest_id, {}) if isinstance(quests, dict) else {}
        if not isinstance(quest, dict):
            return

        x = self.panel_rect.x + 22
        y = self.panel_rect.y + 58
        max_width = self.panel_rect.w - 44
        title = self.body_font.render(
            self._truncate_text(quest.get("name", quest_id), self.body_font, max_width),
            True,
            TEXT_PRIMARY,
        )
        screen.blit(title, (x, y))
        y += 28

        total_current, total_required = self._get_progress_summary(quest_id, quest)
        progress = self.small_font.render(
            f"Progress: {total_current} / {total_required}",
            True,
            TEXT_SECONDARY,
        )
        screen.blit(progress, (x, y))
        y += 24

        objective_title = self.small_font.render("Objectives", True, TEXT_PRIMARY)
        screen.blit(objective_title, (x, y))
        y += 21
        objectives = quest.get("objectives", []) if isinstance(quest.get("objectives"), list) else []
        for index, objective in enumerate(objectives[:4]):
            current = get_quest_progress(self.game.player, quest_id, index)
            required = self._required_amount(objective)
            label = self._format_objective(objective, current, required)
            text = self.small_font.render(
                self._truncate_text(label, self.small_font, max_width),
                True,
                TEXT_SECONDARY,
            )
            screen.blit(text, (x, y))
            y += 20

        y += 4
        reward_title = self.small_font.render("Rewards", True, TEXT_PRIMARY)
        screen.blit(reward_title, (x, y))
        y += 21
        rewards = quest.get("rewards", []) if isinstance(quest.get("rewards"), list) else []
        for reward in rewards[:3]:
            label = self._format_reward(reward)
            text = self.small_font.render(
                self._truncate_text(f"- {label}", self.small_font, max_width),
                True,
                TEXT_SECONDARY,
            )
            screen.blit(text, (x, y))
            y += 20

    def _get_progress_summary(self, quest_id, quest):
        current_total = 0
        required_total = 0
        objectives = quest.get("objectives", []) if isinstance(quest.get("objectives"), list) else []
        for index, objective in enumerate(objectives):
            required = self._required_amount(objective)
            current = min(get_quest_progress(self.game.player, quest_id, index), required)
            current_total += current
            required_total += required
        return current_total, required_total

    def _format_objective(self, objective, current, required):
        objective_type = objective.get("type") if isinstance(objective, dict) else None
        target = objective.get("target", "unknown") if isinstance(objective, dict) else "unknown"
        action_labels = {
            "kill_enemy": "Defeat",
            "gather_item": "Gather",
            "craft_recipe": "Craft",
            "talk_to_npc": "Talk to",
            "clear_dungeon": "Clear",
            "defeat_boss": "Defeat",
        }
        target_name = self._get_target_name(objective_type, target)
        return f"{action_labels.get(objective_type, 'Complete')} {target_name} {current}/{required}"

    def _get_target_name(self, objective_type, target):
        data = getattr(self.game, "data", None)
        collection_name = {
            "kill_enemy": "enemies",
            "defeat_boss": "enemies",
            "gather_item": "items",
            "talk_to_npc": "npcs",
            "clear_dungeon": "dungeons",
        }.get(objective_type)
        if collection_name and data is not None:
            collection = getattr(data, collection_name, {})
            entry = collection.get(target, {}) if isinstance(collection, dict) else {}
            if isinstance(entry, dict) and entry.get("name"):
                return entry["name"]
        if objective_type == "craft_recipe" and data is not None:
            recipe = getattr(data, "recipes", {}).get(target, {})
            result = recipe.get("result", {}) if isinstance(recipe, dict) else {}
            item_id = result.get("item") if isinstance(result, dict) else None
            item = getattr(data, "items", {}).get(item_id, {}) if item_id else {}
            if isinstance(item, dict) and item.get("name"):
                return item["name"]
        return self._titleize_id(target)

    def _format_reward(self, reward):
        if not isinstance(reward, dict):
            return "Reward"
        reward_type = reward.get("type")
        if reward_type == "gold":
            return f"{reward.get('amount', 0)} gold"
        if reward_type == "xp":
            return f"{reward.get('amount', 0)} XP"
        if reward_type == "item":
            item_id = reward.get("item", "unknown")
            items = getattr(getattr(self.game, "data", None), "items", {})
            item = items.get(item_id, {}) if isinstance(items, dict) else {}
            name = item.get("name", self._titleize_id(item_id)) if isinstance(item, dict) else self._titleize_id(item_id)
            return f"{reward.get('quantity', 1)} {name}"
        return "Reward"

    def _required_amount(self, objective):
        required = objective.get("required", 0) if isinstance(objective, dict) else 0
        return required if isinstance(required, int) and required > 0 else 0

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
        return lines or [""]

    def _truncate_text(self, text, font, max_width):
        text = str(text or "")
        if font.size(text)[0] <= max_width:
            return text
        ellipsis = "..."
        while text and font.size(text + ellipsis)[0] > max_width:
            text = text[:-1]
        return text + ellipsis if text else ellipsis

    def _titleize_id(self, value):
        return str(value or "unknown").replace("_", " ").title()
