import pygame

from systems.notices import (
    get_notices_by_channel,
    load_local_notices,
    sort_notices,
)


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
WARNING = (218, 176, 72)
DISABLED_BG = (42, 40, 36)
DISABLED_TEXT = (120, 116, 105)


class MailboxScreen:
    def __init__(self, game):
        self.game = game
        self.title_font = pygame.font.Font(None, 44)
        self.option_font = pygame.font.Font(None, 28)
        self.body_font = pygame.font.Font(None, 22)
        self.small_font = pygame.font.Font(None, 18)
        self.back_rect = pygame.Rect(620, 48, 120, 44)
        self.tab_rects = []
        self.notice_buttons = []
        self.selected_tab = "notice"
        self.selected_notice_id = None
        self.notices = self._load_notices()
        self.scroll_offset = 0

    def handle_event(self, event):
        if event.type == pygame.MOUSEWHEEL:
            visible = self._get_visible_notices()
            max_offset = max(0, len(visible) - self._get_visible_notice_count())
            self.scroll_offset = max(0, min(max_offset, self.scroll_offset - event.y))
            return

        if event.type != pygame.MOUSEBUTTONDOWN or event.button != 1:
            return

        position = event.pos
        if self.back_rect.collidepoint(position):
            self.game.state = "town"
            return

        for tab_id, rect in self.tab_rects:
            if rect.collidepoint(position):
                self.selected_tab = tab_id
                self.scroll_offset = 0
                self._ensure_selected_notice(force=True)
                return

        for notice_id, rect in self.notice_buttons:
            if rect.collidepoint(position):
                self.selected_notice_id = notice_id
                return

    def draw(self, screen):
        screen.fill((18, 16, 13))
        self.notices = self._load_notices()
        self._ensure_selected_notice()

        title = self.title_font.render("Notice Board", True, TEXT_PRIMARY)
        screen.blit(title, (54, 38))
        subtitle = self.body_font.render("Town notices and courier letters", True, TEXT_SECONDARY)
        screen.blit(subtitle, (56, 78))
        self._draw_button(screen, self.back_rect, "Back")

        self._draw_tabs(screen)
        self._draw_notice_list(screen)
        self._draw_notice_detail(screen)

    def _load_notices(self):
        return sort_notices(load_local_notices())

    def _get_visible_notices(self):
        return get_notices_by_channel(self.notices, self.selected_tab)

    def _ensure_selected_notice(self, force=False):
        visible = self._get_visible_notices()
        visible_ids = {notice["id"] for notice in visible}
        if force or self.selected_notice_id not in visible_ids:
            self.selected_notice_id = visible[0]["id"] if visible else None
        max_offset = max(0, len(visible) - self._get_visible_notice_count())
        self.scroll_offset = max(0, min(self.scroll_offset, max_offset))

    def _draw_tabs(self, screen):
        self.tab_rects = []
        tabs = (("notice", "Notices"), ("letter", "Letters"))
        x = 54
        y = 112
        for tab_id, label in tabs:
            rect = pygame.Rect(x, y, 112, 30)
            self.tab_rects.append((tab_id, rect))
            self._draw_button(screen, rect, label, active=tab_id == self.selected_tab)
            x += rect.width + 10

    def _draw_notice_list(self, screen):
        panel = pygame.Rect(54, 154, 306, 392)
        self._draw_panel(screen, panel)
        self.notice_buttons = []

        visible = self._get_visible_notices()
        if not visible:
            label = "No notices available." if self.selected_tab == "notice" else "No letters available."
            text = self.body_font.render(label, True, TEXT_MUTED)
            screen.blit(text, (panel.x + 14, panel.y + 16))
            return

        visible_count = self._get_visible_notice_count()
        visible_notices = visible[self.scroll_offset:self.scroll_offset + visible_count]
        y = panel.y + 12
        row_height = 64
        for notice in visible_notices:
            rect = pygame.Rect(panel.x + 10, y, panel.width - 20, row_height - 8)
            active = notice["id"] == self.selected_notice_id
            self.notice_buttons.append((notice["id"], rect))
            self._draw_notice_row(screen, rect, notice, active)
            y += row_height

        if len(visible) > visible_count:
            hint = self.small_font.render("Mouse wheel to scroll", True, TEXT_MUTED)
            screen.blit(hint, (panel.x + 12, panel.bottom - 22))

    def _draw_notice_row(self, screen, rect, notice, active):
        pygame.draw.rect(screen, CARD_BG_SELECTED if active else CARD_BG, rect, border_radius=6)
        pygame.draw.rect(screen, BORDER_SELECTED if active else BORDER_NORMAL, rect, 2 if active else 1, border_radius=6)

        title = self.body_font.render(
            self._truncate_text(notice.get("title", "Notice"), self.body_font, rect.width - 22),
            True,
            TEXT_PRIMARY,
        )
        screen.blit(title, (rect.x + 10, rect.y + 8))

        meta = f"{notice.get('sender', 'Unknown sender')} - {notice.get('date', '-')}"
        meta_text = self.small_font.render(
            self._truncate_text(meta, self.small_font, rect.width - 22),
            True,
            WARNING if notice.get("important") else TEXT_SECONDARY,
        )
        screen.blit(meta_text, (rect.x + 10, rect.y + 34))

    def _draw_notice_detail(self, screen):
        panel = pygame.Rect(386, 154, 360, 392)
        self._draw_panel(screen, panel)
        notice = self._get_selected_notice()
        if notice is None:
            text = self.body_font.render("Select a message.", True, TEXT_MUTED)
            screen.blit(text, (panel.x + 16, panel.y + 16))
            return

        x = panel.x + 16
        y = panel.y + 16
        max_width = panel.width - 32
        title = self.option_font.render(
            self._truncate_text(notice.get("title", "Notice"), self.option_font, max_width),
            True,
            TEXT_PRIMARY,
        )
        screen.blit(title, (x, y))
        y += 34

        if notice.get("important"):
            badge = pygame.Rect(x, y, 96, 24)
            self._draw_button(screen, badge, "IMPORTANT", active=True, warm=True)
            y += 32

        meta_lines = [
            f"From: {notice.get('sender', 'Unknown sender')}",
            f"Date: {notice.get('date', '-')}",
            f"Type: {str(notice.get('type', 'notice')).replace('_', ' ').title()}",
        ]
        for line in meta_lines:
            text = self.small_font.render(self._truncate_text(line, self.small_font, max_width), True, TEXT_SECONDARY)
            screen.blit(text, (x, y))
            y += 20

        y += 10
        for line in self._wrap_text(notice.get("body", ""), self.body_font, max_width, 12):
            text = self.body_font.render(line, True, TEXT_PRIMARY)
            screen.blit(text, (x, y))
            y += 24

    def _get_selected_notice(self):
        for notice in self._get_visible_notices():
            if notice.get("id") == self.selected_notice_id:
                return notice
        return None

    def _get_visible_notice_count(self):
        return 5

    def _draw_button(self, screen, rect, label, active=False, enabled=True, warm=False):
        if warm and enabled:
            bg, border, color = (116, 82, 34), BORDER_SELECTED, TEXT_PRIMARY
        else:
            bg = CARD_BG_SELECTED if active else CARD_BG if enabled else DISABLED_BG
            border = BORDER_SELECTED if active else BORDER_NORMAL if enabled else DISABLED_TEXT
            color = TEXT_PRIMARY if enabled else DISABLED_TEXT
        pygame.draw.rect(screen, bg, rect, border_radius=6)
        pygame.draw.rect(screen, border, rect, 2 if active or warm else 1, border_radius=6)
        text = self.small_font.render(self._truncate_text(label, self.small_font, rect.width - 10), True, color)
        screen.blit(text, text.get_rect(center=rect.center))

    def _draw_panel(self, screen, rect):
        pygame.draw.rect(screen, PANEL_BG_SECONDARY, rect, border_radius=8)
        pygame.draw.rect(screen, BORDER_NORMAL, rect, 2, border_radius=8)

    def _wrap_text(self, text, font, max_width, max_lines):
        words = str(text or "").split()
        lines = []
        line = ""
        for word in words:
            candidate = word if not line else f"{line} {word}"
            if font.size(candidate)[0] <= max_width:
                line = candidate
                continue
            if line:
                lines.append(line)
            line = word
            if len(lines) >= max_lines:
                break
        if line and len(lines) < max_lines:
            lines.append(line)
        if len(lines) == max_lines and words:
            lines[-1] = self._truncate_text(lines[-1], font, max_width)
        return lines

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
