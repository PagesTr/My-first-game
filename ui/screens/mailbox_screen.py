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
        self.mail_rows = []
        self.selected_mail_index = 0

    def handle_event(self, event):
        if event.type != pygame.MOUSEBUTTONDOWN:
            return

        pos = event.pos
        if self.back_button.is_clicked(pos):
            self.game.state = "town"
            return

        for index, rect in self.mail_rows:
            if rect.collidepoint(pos):
                self.selected_mail_index = index
                return

    def draw(self, screen):
        screen.fill((18, 24, 30))
        self.mail_rows = []

        title = self.title_font.render("Mailbox", True, (245, 245, 245))
        screen.blit(title, (60, 48))
        self.back_button.draw(screen, self.option_font)

        mails = getattr(self.game, "mailbox", [])
        if not mails:
            empty_text = self.body_font.render("No mail yet.", True, (190, 200, 205))
            screen.blit(empty_text, (62, 130))
            return

        self.selected_mail_index = min(self.selected_mail_index, len(mails) - 1)

        y = 120
        for index, mail in enumerate(mails[:8]):
            self._draw_mail_row(screen, index, mail, y)
            y += 76

        self._draw_mail_detail(screen, mails[self.selected_mail_index])

    def _draw_mail_row(self, screen, index, mail, y):
        rect = pygame.Rect(60, y, 300, 64)
        bg = (48, 58, 68) if index == self.selected_mail_index else (34, 42, 50)
        pygame.draw.rect(screen, bg, rect, border_radius=6)
        pygame.draw.rect(screen, (105, 120, 132), rect, 2, border_radius=6)
        self.mail_rows.append((index, rect))

        title = self.body_font.render(
            mail.get("title", "Mail"),
            True,
            (245, 245, 245),
        )
        summary = self.body_font.render(
            mail.get("summary", ""),
            True,
            (190, 200, 205),
        )
        screen.blit(title, (rect.x + 12, rect.y + 10))
        screen.blit(summary, (rect.x + 12, rect.y + 36))

    def _draw_mail_detail(self, screen, mail):
        rect = pygame.Rect(390, 120, 350, 420)
        pygame.draw.rect(screen, (34, 42, 50), rect, border_radius=6)
        pygame.draw.rect(screen, (105, 120, 132), rect, 2, border_radius=6)

        title = self.option_font.render(
            mail.get("title", "Mail"),
            True,
            (245, 245, 245),
        )
        screen.blit(title, (rect.x + 16, rect.y + 16))

        y = rect.y + 54
        for line in mail.get("body", "").splitlines()[:15]:
            text = self.body_font.render(line, True, (190, 200, 205))
            screen.blit(text, (rect.x + 16, y))
            y += 24
