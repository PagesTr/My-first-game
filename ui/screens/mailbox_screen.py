import pygame


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


class MailboxScreen:
    def __init__(self, game):
        self.game = game
        self.title_font = pygame.font.Font(None, 44)
        self.option_font = pygame.font.Font(None, 28)
        self.body_font = pygame.font.Font(None, 22)
        self.back_button = Button((620, 48, 120, 48), "Back")
        self.report_rows = []
        self.selected_report_index = 0

    def handle_event(self, event):
        if event.type != pygame.MOUSEBUTTONDOWN:
            return

        pos = event.pos
        if self.back_button.is_clicked(pos):
            self.game.state = "town"
            return

        for index, rect in self.report_rows:
            if rect.collidepoint(pos):
                self.selected_report_index = index
                return

    def draw(self, screen):
        screen.fill((18, 24, 30))
        self.report_rows = []

        title = self.title_font.render("Mailbox", True, (245, 245, 245))
        screen.blit(title, (60, 48))
        self.back_button.draw(screen, self.option_font)

        reports = getattr(self.game, "combat_reports", [])
        if not reports:
            empty_text = self.body_font.render(
                "No combat reports yet.",
                True,
                (190, 200, 205),
            )
            screen.blit(empty_text, (62, 130))
            return

        self.selected_report_index = min(self.selected_report_index, len(reports) - 1)

        y = 120
        for index, report in enumerate(reports[:8]):
            self._draw_report_row(screen, index, report, y)
            y += 70

        self._draw_report_detail(screen, reports[self.selected_report_index])

    def _draw_report_row(self, screen, index, report, y):
        rect = pygame.Rect(60, y, 300, 58)
        bg = (48, 58, 68) if index == self.selected_report_index else (34, 42, 50)
        pygame.draw.rect(screen, bg, rect, border_radius=6)
        pygame.draw.rect(screen, (105, 120, 132), rect, 2, border_radius=6)
        self.report_rows.append((index, rect))

        title = self.body_font.render(
            report.get("title", "Combat report"),
            True,
            (245, 245, 245),
        )
        summary = self.body_font.render(
            f"Turns: {report.get('turns', 0)}",
            True,
            (190, 200, 205),
        )
        screen.blit(title, (rect.x + 12, rect.y + 10))
        screen.blit(summary, (rect.x + 12, rect.y + 32))

    def _format_drop(self, drop):
        if isinstance(drop, str):
            return drop
        if isinstance(drop, dict):
            item = drop.get("item", "unknown_item")
            quantity = drop.get("quantity")
            if quantity is not None and quantity > 1:
                return f"{item} x{quantity}"
            return item
        return str(drop)

    def _format_drops(self, drops):
        if not drops:
            return "None"
        return ", ".join(self._format_drop(drop) for drop in drops)

    def _draw_report_detail(self, screen, report):
        rect = pygame.Rect(390, 120, 350, 420)
        pygame.draw.rect(screen, (34, 42, 50), rect, border_radius=6)
        pygame.draw.rect(screen, (105, 120, 132), rect, 2, border_radius=6)

        drops = report.get("drops", [])
        lines = [
            report.get("title", "Combat report"),
            f"Turns: {report.get('turns', 0)}",
            f"EXP: {report.get('exp_gained', 0)}",
            f"Gold: {report.get('gold_gained', 0)}",
            f"Drops: {self._format_drops(drops)}",
        ]

        y = rect.y + 18
        for line in lines:
            text = self.body_font.render(line, True, (220, 228, 235))
            screen.blit(text, (rect.x + 16, y))
            y += 26

        y += 10
        history_title = self.body_font.render("History", True, (245, 245, 245))
        screen.blit(history_title, (rect.x + 16, y))
        y += 28

        for line in report.get("history", [])[-12:]:
            text = self.body_font.render(line, True, (190, 200, 205))
            screen.blit(text, (rect.x + 16, y))
            y += 24
