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


class NoticeBoardOverlay:
    def __init__(self, game):
        self.game = game
        self.title_font = pygame.font.Font(None, 42)
        self.option_font = pygame.font.Font(None, 28)
        self.body_font = pygame.font.Font(None, 22)
        self.small_font = pygame.font.Font(None, 18)
        self.opened = False
        self.selected_tab = "notice"
        self.selected_notice_id = None
        self.notices = load_local_notices()
        self.notice_buttons = []
        self.tab_buttons = []
        self.scroll_offset = 0
        self.panel_rect = None
        self.close_rect = None

    def open(self):
        self.opened = True
        self.notices = self._load_notices()
        self._ensure_selected_notice()

    def close(self):
        self.opened = False

    def is_open(self):
        return self.opened

    def handle_event(self, event):
        if not self.opened:
            return False

        if event.type == pygame.KEYDOWN and event.key == pygame.K_ESCAPE:
            self.close()
            return True

        if event.type == pygame.MOUSEWHEEL:
            visible = self._get_visible_notices()
            max_offset = max(0, len(visible) - self._get_visible_notice_count())
            self.scroll_offset = max(0, min(max_offset, self.scroll_offset - event.y))
            return True

        if event.type != pygame.MOUSEBUTTONDOWN or event.button != 1:
            return True

        position = event.pos
        if self.panel_rect is not None and not self.panel_rect.collidepoint(position):
            self.close()
            return True

        if self.close_rect is not None and self.close_rect.collidepoint(position):
            self.close()
            return True

        for tab_id, rect in self.tab_buttons:
            if rect.collidepoint(position):
                self.selected_tab = tab_id
                self.scroll_offset = 0
                self._ensure_selected_notice(force=True)
                return True

        for notice_id, rect in self.notice_buttons:
            if rect.collidepoint(position):
                self.selected_notice_id = notice_id
                return True

        return True

    def draw(self, screen):
        if not self.opened:
            return

        self.notices = self._load_notices()
        self._ensure_selected_notice()
        self._draw_overlay_background(screen)

        panel = self._get_panel_rect(screen.get_size())
        self.panel_rect = panel
        self._draw_main_panel(screen, panel)

        title = self.title_font.render("Notice Board", True, TEXT_PRIMARY)
        screen.blit(title, (panel.x + 28, panel.y + 20))
        subtitle = self.body_font.render(
            "Town notices and courier letters",
            True,
            TEXT_SECONDARY,
        )
        screen.blit(subtitle, (panel.x + 30, panel.y + 58))

        self.close_rect = pygame.Rect(panel.right - 46, panel.y + 18, 30, 30)
        self._draw_button(screen, self.close_rect, "X", active=True, warm=True)

        self._draw_tabs(screen, panel)

        content_top = panel.y + 126
        content_bottom = panel.bottom - 24
        list_rect = pygame.Rect(panel.x + 24, content_top, 306, content_bottom - content_top)
        detail_rect = pygame.Rect(list_rect.right + 22, content_top, panel.right - list_rect.right - 46, list_rect.h)
        self._draw_notice_list(screen, list_rect)
        self._draw_notice_detail(screen, detail_rect)

    def _load_notices(self):
        return sort_notices(load_local_notices())

    def _get_panel_rect(self, screen_size):
        width, height = screen_size
        panel_width = min(720, max(620, width - 80))
        panel_height = min(500, max(430, height - 90))
        return pygame.Rect(
            (width - panel_width) // 2,
            (height - panel_height) // 2,
            panel_width,
            panel_height,
        )

    def _get_visible_notices(self):
        return get_notices_by_channel(self.notices, self.selected_tab)

    def _get_selected_notice(self):
        for notice in self._get_visible_notices():
            if notice.get("id") == self.selected_notice_id:
                return notice
        return None

    def _ensure_selected_notice(self, force=False):
        visible = self._get_visible_notices()
        visible_ids = {notice.get("id") for notice in visible}
        if force or self.selected_notice_id not in visible_ids:
            self.selected_notice_id = visible[0].get("id") if visible else None
        max_offset = max(0, len(visible) - self._get_visible_notice_count())
        self.scroll_offset = max(0, min(self.scroll_offset, max_offset))

    def _get_visible_notice_count(self):
        return 5

    def _draw_overlay_background(self, screen):
        overlay = pygame.Surface(screen.get_size(), pygame.SRCALPHA)
        overlay.fill((0, 0, 0, 150))
        screen.blit(overlay, (0, 0))

    def _draw_main_panel(self, screen, rect):
        pygame.draw.rect(screen, (8, 7, 6), rect.move(5, 5), border_radius=10)
        pygame.draw.rect(screen, PANEL_BG, rect, border_radius=10)
        pygame.draw.rect(screen, BORDER_BRIGHT, rect, 3, border_radius=10)
        pygame.draw.rect(screen, BORDER_NORMAL, rect.inflate(-12, -12), 1, border_radius=7)

    def _draw_tabs(self, screen, panel):
        self.tab_buttons = []
        x = panel.x + 24
        y = panel.y + 88
        for tab_id, label in (("notice", "Notices"), ("letter", "Letters")):
            rect = pygame.Rect(x, y, 112, 30)
            self.tab_buttons.append((tab_id, rect))
            self._draw_button(screen, rect, label, active=tab_id == self.selected_tab)
            x += rect.width + 10

    def _draw_notice_list(self, screen, rect):
        self._draw_panel(screen, rect)
        self.notice_buttons = []
        visible = self._get_visible_notices()

        if not visible:
            label = "No notices available." if self.selected_tab == "notice" else "No letters available."
            text = self.body_font.render(label, True, TEXT_MUTED)
            screen.blit(text, (rect.x + 14, rect.y + 16))
            return

        visible_count = self._get_visible_notice_count()
        visible_notices = visible[self.scroll_offset:self.scroll_offset + visible_count]
        row_height = 64
        y = rect.y + 12
        for notice in visible_notices:
            row_rect = pygame.Rect(rect.x + 10, y, rect.w - 20, row_height - 8)
            active = notice.get("id") == self.selected_notice_id
            self.notice_buttons.append((notice.get("id"), row_rect))
            self._draw_notice_row(screen, row_rect, notice, active)
            y += row_height

        if len(visible) > visible_count:
            hint = self.small_font.render("Mouse wheel to scroll", True, TEXT_MUTED)
            screen.blit(hint, (rect.x + 12, rect.bottom - 22))

    def _draw_notice_row(self, screen, rect, notice, active):
        pygame.draw.rect(screen, CARD_BG_SELECTED if active else CARD_BG, rect, border_radius=6)
        pygame.draw.rect(
            screen,
            BORDER_SELECTED if active else BORDER_NORMAL,
            rect,
            2 if active else 1,
            border_radius=6,
        )

        title = self.body_font.render(
            self._truncate_text(notice.get("title", "Notice"), self.body_font, rect.w - 22),
            True,
            TEXT_PRIMARY,
        )
        screen.blit(title, (rect.x + 10, rect.y + 8))

        meta = f"{notice.get('sender', 'Unknown sender')} - {notice.get('date', '-')}"
        meta_text = self.small_font.render(
            self._truncate_text(meta, self.small_font, rect.w - 22),
            True,
            WARNING if notice.get("important") else TEXT_SECONDARY,
        )
        screen.blit(meta_text, (rect.x + 10, rect.y + 34))

    def _draw_notice_detail(self, screen, rect):
        self._draw_panel(screen, rect)
        notice = self._get_selected_notice()
        if notice is None:
            text = self.body_font.render("Select a message.", True, TEXT_MUTED)
            screen.blit(text, (rect.x + 16, rect.y + 16))
            return

        x = rect.x + 16
        y = rect.y + 16
        max_width = rect.w - 32
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
            text = self.small_font.render(
                self._truncate_text(line, self.small_font, max_width),
                True,
                TEXT_SECONDARY,
            )
            screen.blit(text, (x, y))
            y += 20

        y += 10
        max_lines = max(5, (rect.bottom - y - 12) // 24)
        for line in self._wrap_text(notice.get("body", ""), self.body_font, max_width, max_lines):
            text = self.body_font.render(line, True, TEXT_PRIMARY)
            screen.blit(text, (x, y))
            y += 24

    def _draw_button(self, screen, rect, label, active=False, enabled=True, warm=False):
        if warm and enabled:
            bg, border, color = (116, 82, 34), BORDER_SELECTED, TEXT_PRIMARY
        else:
            bg = CARD_BG_SELECTED if active else CARD_BG if enabled else DISABLED_BG
            border = BORDER_SELECTED if active else BORDER_NORMAL if enabled else DISABLED_TEXT
            color = TEXT_PRIMARY if enabled else DISABLED_TEXT
        pygame.draw.rect(screen, bg, rect, border_radius=6)
        pygame.draw.rect(screen, border, rect, 2 if active or warm else 1, border_radius=6)
        text = self.small_font.render(
            self._truncate_text(label, self.small_font, rect.w - 10),
            True,
            color,
        )
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
