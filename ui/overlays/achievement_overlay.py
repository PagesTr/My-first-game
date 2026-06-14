import pygame

from systems.achievements import (
    claim_achievement_reward,
    get_achievement_claim_status,
    get_claimable_achievements,
)


OVERLAY_DIM = (0, 0, 0, 150)
PANEL_BG = (28, 25, 20)
PANEL_BG_SECONDARY = (34, 31, 25)
CARD_BG = (38, 36, 30)
CARD_BG_SELECTED = (48, 45, 36)
BORDER_NORMAL = (118, 92, 45)
BORDER_BRIGHT = (205, 170, 80)
BORDER_SELECTED = (238, 205, 110)
TEXT_PRIMARY = (238, 232, 205)
TEXT_SECONDARY = (190, 184, 160)
TEXT_MUTED = (130, 124, 105)
SUCCESS = (98, 190, 125)
INFO = (95, 155, 190)
WARNING = (218, 176, 72)
DISABLED_BG = (42, 40, 36)
DISABLED_TEXT = (120, 116, 105)


CATEGORIES = [
    ("all", "All"),
    ("claimable", "Claimable"),
    ("in_progress", "In Progress"),
    ("claimed", "Claimed"),
    ("combat", "Combat"),
    ("gathering", "Gathering"),
    ("craft", "Craft"),
    ("sets", "Sets"),
    ("dungeons", "Dungeons"),
    ("boss", "Boss"),
    ("run", "Run"),
]


class AchievementOverlay:
    def __init__(self, game):
        if not pygame.font.get_init():
            pygame.font.init()

        self.game = game
        self.opened = False
        self.selected_category = "all"
        self.selected_achievement_id = None
        self.page = 0
        self.title_font = pygame.font.Font(None, 38)
        self.header_font = pygame.font.Font(None, 27)
        self.body_font = pygame.font.Font(None, 22)
        self.small_font = pygame.font.Font(None, 18)
        self.panel_rect = pygame.Rect(0, 0, 0, 0)
        self.close_rect = pygame.Rect(0, 0, 0, 0)
        self.list_rect = pygame.Rect(0, 0, 0, 0)
        self.detail_rect = pygame.Rect(0, 0, 0, 0)
        self.prev_rect = pygame.Rect(0, 0, 0, 0)
        self.next_rect = pygame.Rect(0, 0, 0, 0)
        self.claim_button_rect = pygame.Rect(0, 0, 0, 0)
        self.category_rects = []
        self.row_rects = []
        self.last_claim_result = None
        self.last_claim_achievement_id = None

    def open(self):
        self.opened = True
        self._select_first_visible_achievement()

    def close(self):
        self.opened = False

    def is_open(self):
        return self.opened

    def handle_event(self, event):
        if not self.opened:
            return False

        if event.type == pygame.KEYDOWN:
            if event.key in (pygame.K_ESCAPE, pygame.K_a):
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

        for category_id, rect in self.category_rects:
            if rect.collidepoint(position):
                self.selected_category = category_id
                self.page = 0
                self.selected_achievement_id = None
                self._select_first_visible_achievement()
                return True

        achievements = self._get_filtered_achievements()
        total_pages = self._get_total_pages(achievements)
        if self.prev_rect.collidepoint(position) and self.page > 0:
            self.page -= 1
            self.selected_achievement_id = None
            self._select_first_visible_achievement()
            return True
        if self.next_rect.collidepoint(position) and self.page < total_pages - 1:
            self.page += 1
            self.selected_achievement_id = None
            self._select_first_visible_achievement()
            return True

        if (
            self.claim_button_rect.collidepoint(position)
            and self._get_claim_status(self.selected_achievement_id) == "claimable"
        ):
            self._claim_selected_achievement()
            return True

        for achievement_id, rect in self.row_rects:
            if rect.collidepoint(position):
                self.selected_achievement_id = achievement_id
                return True

        return True

    def draw(self, screen):
        if not self.opened:
            return

        self._draw_overlay_background(screen)
        self.panel_rect = self._get_panel_rect(screen)
        self._layout_content_rects()
        self._draw_panel(screen, self.panel_rect, "Achievements")
        self.close_rect = pygame.Rect(self.panel_rect.right - 48, self.panel_rect.y + 14, 30, 28)
        self._draw_button(screen, self.close_rect, "X")

        if not isinstance(getattr(self.game, "player", None), dict):
            self._draw_message(screen, "No player achievements available.")
            return

        achievements_data = getattr(getattr(self.game, "data", None), "achievements", {})
        if not isinstance(achievements_data, dict) or not achievements_data:
            self._draw_message(screen, "No achievements available.")
            return

        self._draw_summary(screen)
        category_bottom = self._draw_category_tabs(screen)
        self._layout_content_rects(category_bottom + 12)
        self._draw_achievement_list(screen)
        self._draw_selected_achievement(screen)

    def _get_panel_rect(self, screen):
        width, height = screen.get_size()
        panel_width = min(width - 28, max(760, int(width * 0.9)))
        panel_height = min(height - 70, max(500, int(height * 0.82)))
        panel_width = max(620, min(panel_width, width - 20))
        panel_height = max(480, min(panel_height, height - 62))
        return pygame.Rect((width - panel_width) // 2, 24, panel_width, panel_height)

    def _layout_content_rects(self, top=None):
        panel = self.panel_rect
        content_top = top if top is not None else panel.y + 116
        bottom = panel.bottom - 56
        gap = 14
        left_width = max(260, int((panel.w - 54) * 0.46))
        self.list_rect = pygame.Rect(panel.x + 18, content_top, left_width, max(180, bottom - content_top))
        self.detail_rect = pygame.Rect(
            self.list_rect.right + gap,
            content_top,
            panel.right - self.list_rect.right - gap - 18,
            max(180, bottom - content_top),
        )
        self.prev_rect = pygame.Rect(self.list_rect.x, panel.bottom - 42, 42, 28)
        self.next_rect = pygame.Rect(self.list_rect.right - 42, panel.bottom - 42, 42, 28)
        self.claim_button_rect = pygame.Rect(self.detail_rect.right - 170, panel.bottom - 42, 152, 28)

    def _draw_overlay_background(self, screen):
        overlay = pygame.Surface(screen.get_size(), pygame.SRCALPHA)
        overlay.fill(OVERLAY_DIM)
        screen.blit(overlay, (0, 0))

    def _draw_panel(self, screen, rect, title):
        pygame.draw.rect(screen, PANEL_BG, rect, border_radius=8)
        pygame.draw.rect(screen, BORDER_BRIGHT, rect, 2, border_radius=8)
        pygame.draw.rect(screen, BORDER_NORMAL, rect.inflate(-8, -8), 1, border_radius=6)
        text = self.title_font.render(title, True, TEXT_PRIMARY)
        screen.blit(text, (rect.x + 20, rect.y + 12))

    def _draw_message(self, screen, message):
        text = self.body_font.render(message, True, TEXT_PRIMARY)
        screen.blit(text, (self.panel_rect.x + 24, self.panel_rect.y + 76))

    def _draw_summary(self, screen):
        data = getattr(getattr(self.game, "data", None), "achievements", {})
        unlocked = set(self._get_player_achievements().get("unlocked", []))
        visible_total = sum(
            1
            for achievement_id, achievement in data.items()
            if isinstance(achievement, dict)
            and (not achievement.get("hidden", False) or achievement_id in unlocked)
        )
        unlocked_count = len([achievement_id for achievement_id in unlocked if achievement_id in data])
        claimable_count = len(get_claimable_achievements(getattr(self.game, "player", {}) or {}))

        x = self.panel_rect.x + 24
        y = self.panel_rect.y + 56
        base = f"Unlocked: {unlocked_count} / {visible_total}   Claimable: "
        base_text = self.body_font.render(base, True, TEXT_SECONDARY)
        screen.blit(base_text, (x, y))
        color = WARNING if claimable_count > 0 else TEXT_SECONDARY
        screen.blit(self.body_font.render(str(claimable_count), True, color), (x + base_text.get_width(), y))

    def _draw_category_tabs(self, screen):
        self.category_rects = []
        x = self.panel_rect.x + 20
        y = self.panel_rect.y + 84
        max_x = self.panel_rect.right - 20
        row_height = 28
        for category_id, label in CATEGORIES:
            width = max(52, min(104, self.small_font.size(label)[0] + 18))
            if x + width > max_x:
                x = self.panel_rect.x + 20
                y += row_height + 6
            rect = pygame.Rect(x, y, width, row_height)
            self.category_rects.append((category_id, rect))
            self._draw_button(screen, rect, label, category_id == self.selected_category, font=self.small_font)
            x += width + 6
        return y + row_height

    def _draw_achievement_list(self, screen):
        self._draw_content_box(screen, self.list_rect)
        achievements = self._get_filtered_achievements()
        total_pages = self._get_total_pages(achievements)
        self.page = max(0, min(self.page, total_pages - 1))
        page_size = self._get_page_size()
        page_items = achievements[self.page * page_size:(self.page + 1) * page_size]

        valid_ids = {achievement_id for achievement_id, _ in achievements}
        if self.selected_achievement_id not in valid_ids:
            self.selected_achievement_id = page_items[0][0] if page_items else None

        self.row_rects = []
        if not page_items:
            empty = self.body_font.render("No achievements here.", True, TEXT_MUTED)
            screen.blit(empty, (self.list_rect.x + 16, self.list_rect.y + 18))
        y = self.list_rect.y + 10
        row_height = self._get_row_height()
        for achievement_id, achievement in page_items:
            row = pygame.Rect(self.list_rect.x + 10, y, self.list_rect.w - 20, row_height - 4)
            self.row_rects.append((achievement_id, row))
            self._draw_list_row(screen, row, achievement_id, achievement, achievement_id == self.selected_achievement_id)
            y += row_height

        page_label = self.small_font.render(f"Page {self.page + 1} / {total_pages}", True, TEXT_SECONDARY)
        screen.blit(page_label, page_label.get_rect(center=(self.list_rect.centerx, self.prev_rect.centery)))
        self._draw_button(screen, self.prev_rect, "<", enabled=self.page > 0)
        self._draw_button(screen, self.next_rect, ">", enabled=self.page < total_pages - 1)

    def _draw_list_row(self, screen, row, achievement_id, achievement, selected):
        status = self._get_claim_status(achievement_id)
        current, required = self._get_progress_summary(achievement_id, achievement)
        hidden = achievement.get("hidden", False) and status == "locked"
        in_progress = current > 0 and current < required and status == "locked"
        almost = required > 0 and current / required >= 0.8 and status == "locked"

        if hidden:
            label, bg, badge_bg, badge_text = "HIDE", DISABLED_BG, (72, 68, 60), TEXT_MUTED
        elif status == "claimable":
            label, bg, badge_bg, badge_text = "CLAIM", CARD_BG_SELECTED, (116, 82, 34), TEXT_PRIMARY
        elif status == "claimed":
            label, bg, badge_bg, badge_text = "DONE", CARD_BG, (45, 88, 56), TEXT_PRIMARY
        elif in_progress:
            label, bg, badge_bg, badge_text = "TODO", CARD_BG, (54, 74, 86), TEXT_PRIMARY
        else:
            label, bg, badge_bg, badge_text = "TODO", CARD_BG, (64, 60, 52), TEXT_MUTED

        pygame.draw.rect(screen, bg, row, border_radius=5)
        border = BORDER_SELECTED if selected else WARNING if status == "claimable" else BORDER_NORMAL
        pygame.draw.rect(screen, border, row, 2 if selected or status == "claimable" else 1, border_radius=5)

        badge = pygame.Rect(row.x + 6, row.y + 7, 52, 22)
        pygame.draw.rect(screen, badge_bg, badge, border_radius=5)
        badge_surface = self.small_font.render(label, True, badge_text)
        screen.blit(badge_surface, badge_surface.get_rect(center=badge.center))

        name = "Hidden achievement" if hidden else achievement.get("name", achievement_id)
        if status == "claimable":
            name = f"{name} - Reward ready"
        elif almost:
            name = f"{name} - Almost"
        color = WARNING if status == "claimable" else TEXT_PRIMARY
        text = self.body_font.render(self._truncate_text(name, self.body_font, row.w - 138), True, color)
        screen.blit(text, (row.x + 66, row.y + 8))
        progress_text = self.small_font.render(f"{current}/{required}", True, TEXT_SECONDARY)
        screen.blit(progress_text, (row.right - progress_text.get_width() - 8, row.y + 10))

    def _draw_selected_achievement(self, screen):
        self._draw_content_box(screen, self.detail_rect)
        achievement = self._get_achievement_data(self.selected_achievement_id)
        if not isinstance(achievement, dict) or not achievement:
            text = self.body_font.render("No achievement selected", True, TEXT_MUTED)
            screen.blit(text, (self.detail_rect.x + 16, self.detail_rect.y + 18))
            return

        status = self._get_claim_status(self.selected_achievement_id)
        hidden = achievement.get("hidden", False) and status == "locked"
        current, required = self._get_progress_summary(self.selected_achievement_id, achievement)
        x = self.detail_rect.x + 16
        y = self.detail_rect.y + 14
        name = "Hidden achievement" if hidden else achievement.get("name", self.selected_achievement_id)
        title = self.header_font.render(self._truncate_text(name, self.header_font, self.detail_rect.w - 32), True, TEXT_PRIMARY)
        screen.blit(title, (x, y))
        y += 31

        self._draw_status_badge(screen, pygame.Rect(x, y, 150, 24), self._get_detail_status_label(status, current, required), status)
        y += 31
        meta = f"{achievement.get('category', 'unknown').title()} | Tier {achievement.get('tier', 0)}"
        self._draw_line(screen, meta, x, y, TEXT_SECONDARY)
        y += 24

        detail_lines = ["Description: Hidden", "Objective: Hidden"] if hidden else [
            achievement.get("description", ""),
            self._format_objective(achievement),
        ]
        for line in detail_lines:
            y = self._draw_wrapped_text(screen, line, x, y, self.detail_rect.w - 32, TEXT_SECONDARY)
            y += 2

        self._draw_line(screen, f"Progress: {current} / {required}", x, y, TEXT_PRIMARY)
        y += 22
        self._draw_progress_bar(screen, pygame.Rect(x, y, self.detail_rect.w - 32, 14), current, required)
        y += 24

        rewards_title = self.body_font.render("Rewards", True, TEXT_PRIMARY)
        screen.blit(rewards_title, (x, y))
        y += 22
        rewards = achievement.get("rewards", [])
        if not isinstance(rewards, list):
            rewards = []
        if not rewards:
            self._draw_line(screen, "No reward.", x, y, TEXT_MUTED)
        for reward in rewards[:4]:
            prefix = "DONE" if status == "claimed" else "CLAIM" if status == "claimable" else "-"
            self._draw_line(screen, f"{prefix} {self._format_reward(reward)}", x, y, TEXT_SECONDARY)
            y += 20

        self._draw_detail_action_area(screen, status, x)

    def _draw_detail_action_area(self, screen, status, x):
        action_y = self.detail_rect.bottom + 16
        message = self._format_claim_result_message()
        if message:
            self._draw_line(screen, message, x, action_y, WARNING, self.detail_rect.w - 180)
        if status == "claimable":
            self._draw_button(screen, self.claim_button_rect, "Claim Reward", warm=True)
        elif status == "claimed":
            self._draw_line(screen, "Reward already claimed.", x, action_y, SUCCESS, self.detail_rect.w - 180)
        elif not message:
            self._draw_line(screen, "Complete this achievement first.", x, action_y, TEXT_MUTED, self.detail_rect.w - 180)

    def _draw_status_badge(self, screen, rect, label, status):
        if status == "claimable":
            bg, border, color = (116, 82, 34), WARNING, TEXT_PRIMARY
        elif status == "claimed":
            bg, border, color = (45, 88, 56), SUCCESS, TEXT_PRIMARY
        elif label == "IN PROGRESS":
            bg, border, color = (42, 58, 66), INFO, TEXT_PRIMARY
        else:
            bg, border, color = DISABLED_BG, BORDER_NORMAL, TEXT_SECONDARY
        pygame.draw.rect(screen, bg, rect, border_radius=5)
        pygame.draw.rect(screen, border, rect, 2, border_radius=5)
        text = self.small_font.render(label, True, color)
        screen.blit(text, text.get_rect(center=rect.center))

    def _draw_content_box(self, screen, rect):
        pygame.draw.rect(screen, PANEL_BG_SECONDARY, rect, border_radius=6)
        pygame.draw.rect(screen, BORDER_NORMAL, rect, 2, border_radius=6)

    def _draw_button(self, screen, rect, label, active=False, enabled=True, warm=False, font=None):
        font = font or self.body_font
        if warm and enabled:
            bg, border, color = (116, 82, 34), BORDER_SELECTED, TEXT_PRIMARY
        else:
            bg = CARD_BG_SELECTED if active else CARD_BG if enabled else DISABLED_BG
            border = BORDER_SELECTED if active else BORDER_NORMAL if enabled else DISABLED_TEXT
            color = TEXT_PRIMARY if enabled else DISABLED_TEXT
        pygame.draw.rect(screen, bg, rect, border_radius=5)
        pygame.draw.rect(screen, border, rect, 1 if rect.h < 30 else 2, border_radius=5)
        text = font.render(self._truncate_text(label, font, rect.w - 8), True, color)
        screen.blit(text, text.get_rect(center=rect.center))

    def _draw_progress_bar(self, screen, rect, current, required):
        pygame.draw.rect(screen, PANEL_BG, rect, border_radius=5)
        ratio = 0 if required <= 0 else max(0, min(current / required, 1))
        fill = pygame.Rect(rect.x, rect.y, int(rect.w * ratio), rect.h)
        if fill.w > 0:
            pygame.draw.rect(screen, SUCCESS, fill, border_radius=5)
        pygame.draw.rect(screen, BORDER_NORMAL, rect, 1, border_radius=5)

    def _draw_line(self, screen, text, x, y, color, max_width=None):
        max_width = max_width or self.detail_rect.w - 32
        line = self.body_font.render(self._truncate_text(text, self.body_font, max_width), True, color)
        screen.blit(line, (x, y))

    def _draw_wrapped_text(self, screen, text, x, y, max_width, color):
        words = str(text or "").split()
        if not words:
            return y
        line = ""
        for word in words:
            candidate = word if not line else f"{line} {word}"
            if self.body_font.size(candidate)[0] <= max_width:
                line = candidate
                continue
            if line:
                screen.blit(self.body_font.render(line, True, color), (x, y))
                y += 20
            line = word
        if line:
            screen.blit(self.body_font.render(self._truncate_text(line, self.body_font, max_width), True, color), (x, y))
            y += 20
        return y

    def _truncate_text(self, text, font, max_width):
        text = str(text or "")
        if max_width <= 0:
            return ""
        if font.size(text)[0] <= max_width:
            return text
        ellipsis = "..."
        while text and font.size(text + ellipsis)[0] > max_width:
            text = text[:-1]
        return text + ellipsis if text else ellipsis

    def _get_player_achievements(self):
        player = getattr(self.game, "player", None)
        if not isinstance(player, dict):
            return {"unlocked": [], "claimed": [], "progress": {}, "last_unlocked": []}
        achievements = player.get("achievements")
        if not isinstance(achievements, dict):
            return {"unlocked": [], "claimed": [], "progress": {}, "last_unlocked": []}
        return {
            "unlocked": achievements.get("unlocked", []) if isinstance(achievements.get("unlocked"), list) else [],
            "claimed": achievements.get("claimed", []) if isinstance(achievements.get("claimed"), list) else [],
            "progress": achievements.get("progress", {}) if isinstance(achievements.get("progress"), dict) else {},
            "last_unlocked": achievements.get("last_unlocked", []) if isinstance(achievements.get("last_unlocked"), list) else [],
        }

    def _get_filtered_achievements(self):
        data = getattr(getattr(self.game, "data", None), "achievements", {})
        if not isinstance(data, dict):
            return []

        achievements = []
        for achievement_id, achievement in data.items():
            if not isinstance(achievement, dict):
                continue
            if achievement.get("hidden", False) and not self._is_unlocked(achievement_id):
                if self.selected_category in {"claimable", "in_progress", "claimed"}:
                    continue

            if self.selected_category == "claimable":
                if self._get_claim_status(achievement_id) != "claimable":
                    continue
            elif self.selected_category == "in_progress":
                current, required = self._get_progress_summary(achievement_id, achievement)
                if self._is_unlocked(achievement_id) or current <= 0 or current >= required:
                    continue
            elif self.selected_category == "claimed":
                if self._get_claim_status(achievement_id) != "claimed":
                    continue
            elif self.selected_category != "all" and achievement.get("category", "") != self.selected_category:
                continue
            achievements.append((achievement_id, achievement))

        achievements.sort(
            key=lambda item: (
                self._get_status_sort_rank(item[0]),
                item[1].get("chapter", ""),
                item[1].get("category", ""),
                item[1].get("tier", 0),
                item[0],
            )
        )
        return achievements

    def _get_achievement_data(self, achievement_id):
        data = getattr(getattr(self.game, "data", None), "achievements", {})
        if not isinstance(data, dict):
            return {}
        achievement = data.get(achievement_id, {})
        return achievement if isinstance(achievement, dict) else {}

    def _get_achievement_progress(self, achievement_id):
        progress = self._get_player_achievements().get("progress", {})
        value = progress.get(achievement_id, 0)
        return value if isinstance(value, int) else 0

    def _is_unlocked(self, achievement_id):
        return achievement_id in self._get_player_achievements().get("unlocked", [])

    def _get_claim_status(self, achievement_id):
        if not achievement_id:
            return "locked"
        player = getattr(self.game, "player", {}) or {}
        if not isinstance(player, dict):
            return "locked"
        return get_achievement_claim_status(player, achievement_id)

    def _get_status_sort_rank(self, achievement_id):
        status = self._get_claim_status(achievement_id)
        if status == "claimable":
            return 0
        if status == "claimed":
            return 3
        current, required = self._get_progress_summary(achievement_id, self._get_achievement_data(achievement_id))
        return 1 if current > 0 and current < required else 2

    def _get_progress_summary(self, achievement_id, achievement):
        objective = achievement.get("objective", {}) if isinstance(achievement, dict) else {}
        required = objective.get("required", 0)
        if not isinstance(required, int) or required < 0:
            required = 0
        current = required if self._is_unlocked(achievement_id) else self._get_achievement_progress(achievement_id)
        return max(0, min(current, required)), required

    def _get_total_pages(self, achievements):
        page_size = self._get_page_size()
        return max(1, (len(achievements) + page_size - 1) // page_size)

    def _get_page_size(self):
        return max(3, self.list_rect.h // self._get_row_height())

    def _get_row_height(self):
        return 40

    def _select_first_visible_achievement(self):
        achievements = self._get_filtered_achievements()
        total_pages = self._get_total_pages(achievements)
        self.page = max(0, min(self.page, total_pages - 1))
        page_size = self._get_page_size()
        page_items = achievements[self.page * page_size:(self.page + 1) * page_size]
        self.selected_achievement_id = page_items[0][0] if page_items else None

    def _get_detail_status_label(self, status, current, required):
        if status == "claimable":
            return "REWARD AVAILABLE"
        if status == "claimed":
            return "CLAIMED"
        if current > 0 and current < required:
            return "IN PROGRESS"
        return "LOCKED"

    def _claim_selected_achievement(self):
        achievement_id = self.selected_achievement_id
        player = getattr(self.game, "player", None)
        data = getattr(getattr(self.game, "data", None), "achievements", {})
        items = getattr(getattr(self.game, "data", None), "items", {})
        if not achievement_id or not isinstance(player, dict):
            result = {"claimed": False, "reason": "not_unlocked", "rewards": {"applied": [], "failed": []}}
        else:
            result = claim_achievement_reward(player, data, achievement_id, items=items)
        self.last_claim_result = result
        self.last_claim_achievement_id = achievement_id
        if result.get("claimed") and hasattr(self.game, "save_current_game"):
            self.game.save_current_game()
        return result

    def _format_claim_result_message(self):
        if self.selected_achievement_id != self.last_claim_achievement_id:
            return ""
        result = self.last_claim_result
        if not isinstance(result, dict):
            return ""
        if result.get("claimed"):
            return "Reward claimed."
        reason = result.get("reason")
        if reason == "reward_failed":
            return "Inventory full. Free a slot and try again."
        if reason == "already_claimed":
            return "Already claimed."
        if reason == "not_unlocked":
            return "Complete this achievement first."
        return ""

    def _format_reward(self, reward):
        if not isinstance(reward, dict):
            return "Unknown reward"
        reward_type = reward.get("type")
        amount = reward.get("amount", reward.get("quantity", 1))
        if reward_type == "gold":
            return f"+{amount} gold"
        if reward_type == "item":
            return f"+{reward.get('quantity', 1)} {self._get_item_name(reward.get('item'))}"
        if reward_type == "stat_bonus":
            return f"+{amount} {reward.get('stat', 'stat')}"
        if reward_type == "percent_bonus":
            percent = int(round(float(amount) * 100)) if isinstance(amount, (int, float)) else amount
            return f"+{percent}% {reward.get('stat', 'bonus')}"
        return "Unknown reward"

    def _format_objective(self, achievement):
        objective = achievement.get("objective", {}) if isinstance(achievement, dict) else {}
        objective_type = objective.get("type", "unknown")
        target = objective.get("target", "unknown")
        required = objective.get("required", 0)
        name = self._resolve_target_name(objective_type, target)
        formats = {
            "kill_enemy": f"Kill {name}: {required}",
            "kill_family": f"Kill {name} family: {required}",
            "gather_profession": f"Gather with {name}: {required}",
            "gather_item": f"Gather {name}: {required}",
            "craft_recipe": f"Craft {name}: {required}",
            "craft_chapter": f"Craft {name.title()} recipes: {required}",
            "clear_dungeon": f"Clear {name}: {required}",
            "defeat_boss": f"Defeat {name}: {required}",
            "boss_victory_count": f"Boss victories against {name}: {required}",
            "equip_set_pieces": f"Equip set pieces: {required}",
            "single_expedition_kills": f"Best expedition in {name}: {required} kills",
            "single_dungeon_kills": f"Best dungeon run in {name}: {required} kills",
            "single_boss_victories": f"Best boss loop against {name}: {required} victories",
        }
        return formats.get(objective_type, f"{objective_type}: {name} {required}")

    def _resolve_target_name(self, objective_type, target):
        data = getattr(self.game, "data", None)
        if data is None:
            return self._humanize_id(target)
        maps = {
            "kill_enemy": getattr(data, "enemies", {}),
            "defeat_boss": getattr(data, "enemies", {}),
            "boss_victory_count": getattr(data, "enemies", {}),
            "single_boss_victories": getattr(data, "enemies", {}),
            "gather_item": getattr(data, "items", {}),
            "craft_recipe": getattr(data, "recipes", {}),
            "clear_dungeon": getattr(data, "dungeons", {}),
            "single_dungeon_kills": getattr(data, "dungeons", {}),
            "single_expedition_kills": getattr(data, "zones", {}),
            "equip_set_pieces": getattr(data, "equipment_sets", {}),
        }
        source = maps.get(objective_type, {})
        entry = source.get(target, {}) if isinstance(source, dict) else {}
        if isinstance(entry, dict) and entry.get("name"):
            return entry["name"]
        return self._humanize_id(target)

    def _get_item_name(self, item_id):
        items = getattr(getattr(self.game, "data", None), "items", {})
        item = items.get(item_id, {}) if isinstance(items, dict) else {}
        if isinstance(item, dict):
            return item.get("name", self._humanize_id(item_id))
        return self._humanize_id(item_id)

    def _humanize_id(self, value):
        return str(value or "unknown").replace("_", " ").title()
