import pygame

from systems.professions import (
    get_profession_mastery,
    get_profession_progress,
)


class ProfessionOverlay:
    def __init__(self, game):
        if not pygame.font.get_init():
            pygame.font.init()

        self.game = game
        self.opened = False
        self.selected_profession_id = None
        self.title_font = pygame.font.Font(None, 38)
        self.header_font = pygame.font.Font(None, 27)
        self.body_font = pygame.font.Font(None, 22)
        self.small_font = pygame.font.Font(None, 18)
        self.panel_rect = pygame.Rect(0, 0, 0, 0)
        self.close_rect = pygame.Rect(0, 0, 0, 0)
        self.list_rect = pygame.Rect(0, 0, 0, 0)
        self.detail_rect = pygame.Rect(0, 0, 0, 0)
        self.profession_card_rects = []

    def open(self):
        self.opened = True
        self._ensure_selected_profession()

    def close(self):
        self.opened = False

    def is_open(self):
        return self.opened

    def handle_event(self, event):
        if not self.opened:
            return False

        if event.type == pygame.KEYDOWN:
            if event.key in (pygame.K_ESCAPE, pygame.K_p):
                self.close()
            return True

        if event.type != pygame.MOUSEBUTTONDOWN or event.button != 1:
            return False

        position = event.pos
        if self.panel_rect.width > 0 and not self.panel_rect.collidepoint(position):
            self.close()
            return True

        if self.close_rect.collidepoint(position):
            self.close()
            return True

        for profession_id, rect in self.profession_card_rects:
            if rect.collidepoint(position):
                self.selected_profession_id = profession_id
                return True

        return True

    def draw(self, screen):
        if not self.opened:
            return

        self._draw_overlay_background(screen)
        self.panel_rect = self._get_panel_rect(screen)
        self._layout_rects()
        self._draw_panel(screen, self.panel_rect, "Professions")
        self.close_rect = pygame.Rect(self.panel_rect.right - 48, self.panel_rect.y + 14, 30, 28)
        self._draw_button(screen, self.close_rect, "X")

        player = getattr(self.game, "player", None)
        if not isinstance(player, dict):
            self._draw_message(screen, "No player available.")
            return

        professions = self._get_professions_data()
        if not professions:
            self._draw_message(screen, "No professions available.")
            return

        self._ensure_selected_profession()
        self._draw_profession_list(screen, professions, player)
        self._draw_profession_detail(screen, professions, player)

    def _get_professions_data(self):
        data = getattr(self.game, "data", None)
        professions = getattr(data, "professions", {}) if data is not None else {}
        return professions if isinstance(professions, dict) else {}

    def _ensure_selected_profession(self):
        professions = self._get_professions_data()
        if self.selected_profession_id in professions:
            return
        self.selected_profession_id = next(iter(professions), None)

    def _draw_profession_list(self, screen, professions, player):
        self.profession_card_rects = []
        pygame.draw.rect(screen, (28, 32, 34), self.list_rect, border_radius=8)
        pygame.draw.rect(screen, (137, 104, 55), self.list_rect, 2, border_radius=8)

        if not professions:
            text = self.body_font.render("No professions available.", True, (214, 205, 176))
            screen.blit(text, (self.list_rect.x + 18, self.list_rect.y + 18))
            return

        card_height = 94
        spacing = 10
        y = self.list_rect.y + 14
        max_y = self.list_rect.bottom - 12
        for profession_id, profession_data in professions.items():
            if y + card_height > max_y:
                break

            rect = pygame.Rect(self.list_rect.x + 14, y, self.list_rect.width - 28, card_height)
            selected = profession_id == self.selected_profession_id
            self._draw_profession_card(screen, rect, profession_id, profession_data, player, selected)
            self.profession_card_rects.append((profession_id, rect))
            y += card_height + spacing

    def _draw_profession_card(self, screen, rect, profession_id, profession_data, player, selected):
        progress = get_profession_progress(player, profession_id)
        professions = self._get_professions_data()
        mastery = get_profession_mastery(player, profession_id, professions)
        border = (232, 202, 96) if selected else (91, 77, 54)
        fill = (49, 41, 31) if selected else (35, 38, 38)

        pygame.draw.rect(screen, fill, rect, border_radius=7)
        pygame.draw.rect(screen, border, rect, 2, border_radius=7)

        name = profession_data.get("name", profession_id) if isinstance(profession_data, dict) else profession_id
        name_text = self.body_font.render(self._truncate_text(name, self.body_font, rect.width - 24), True, (239, 229, 194))
        screen.blit(name_text, (rect.x + 12, rect.y + 10))

        level = progress.get("level", 0)
        xp = progress.get("xp", 0)
        next_xp = progress.get("next_xp", 0)
        info = f"Level {level}  Mastery {mastery}"
        info_text = self.small_font.render(info, True, (194, 206, 190))
        screen.blit(info_text, (rect.x + 12, rect.y + 38))

        xp_text = self.small_font.render(f"XP {xp} / {next_xp}", True, (214, 205, 176))
        screen.blit(xp_text, (rect.x + 12, rect.y + 58))
        self._draw_progress_bar(screen, pygame.Rect(rect.x + 12, rect.y + 78, rect.width - 24, 8), xp, next_xp)

    def _draw_profession_detail(self, screen, professions, player):
        pygame.draw.rect(screen, (28, 32, 34), self.detail_rect, border_radius=8)
        pygame.draw.rect(screen, (137, 104, 55), self.detail_rect, 2, border_radius=8)

        profession_id = self.selected_profession_id
        profession_data = professions.get(profession_id)
        if not isinstance(profession_data, dict):
            self._draw_text_line(screen, self.detail_rect.x + 18, self.detail_rect.y + 18, "No profession selected.", self.body_font)
            return

        progress = get_profession_progress(player, profession_id)
        mastery = get_profession_mastery(player, profession_id, professions)
        primary_stat = profession_data.get("primary_stat", "")
        mastery_bonus_stat = profession_data.get("mastery_bonus_stat", "")
        xp_bonus_stat = profession_data.get("xp_bonus_stat", "")
        mastery_bonus = self._get_player_bonus_value(mastery_bonus_stat)
        global_mastery = self._get_player_bonus_value("gathering_mastery")
        xp_bonus = self._get_player_bonus_value(xp_bonus_stat)
        global_xp_bonus = self._get_player_bonus_value("gathering_xp_bonus")

        x = self.detail_rect.x + 18
        y = self.detail_rect.y + 16
        max_width = self.detail_rect.width - 36
        name = profession_data.get("name", profession_id)
        name_text = self.header_font.render(self._truncate_text(name, self.header_font, max_width), True, (244, 232, 190))
        screen.blit(name_text, (x, y))
        y += 30

        description = profession_data.get("description", "")
        for line in self._wrap_text(description, self.small_font, max_width, 2):
            self._draw_text_line(screen, x, y, line, self.small_font, (200, 195, 174))
            y += 20
        if description:
            y += 4

        level = progress.get("level", 0)
        xp = progress.get("xp", 0)
        next_xp = progress.get("next_xp", 0)
        detail_lines = [
            f"Primary stat: {self._format_stat_label(primary_stat)}",
            f"Level: {level}  XP: {xp} / {next_xp}",
            f"Mastery: {mastery}",
            "Mastery = level + primary stat / 2 + bonuses",
            f"Mastery bonus: +{mastery_bonus}  Global: +{global_mastery}",
            f"XP bonus: {self._format_bonus_percent(xp_bonus)}  Global: {self._format_bonus_percent(global_xp_bonus)}",
            f"Mastery stat: {self._format_stat_label(mastery_bonus_stat)}",
            f"XP stat: {self._format_stat_label(xp_bonus_stat)}",
        ]

        for line in detail_lines:
            self._draw_text_line(screen, x, y, self._truncate_text(line, self.small_font, max_width), self.small_font)
            y += 21

        y += 6
        self._draw_text_line(screen, x, y, "Used in:", self.body_font, (244, 232, 190))
        y += 24
        zones = self._get_profession_usable_zones(profession_id)
        if not zones:
            self._draw_text_line(screen, x + 12, y, "No known gathering zones.", self.small_font, (183, 179, 163))
            return

        for zone_id in zones[:5]:
            zone_name = self._get_zone_name(zone_id)
            line = self._truncate_text(f"- {zone_name}", self.small_font, max_width - 12)
            self._draw_text_line(screen, x + 12, y, line, self.small_font, (200, 195, 174))
            y += 20

    def _get_player_bonus_value(self, stat_key):
        player = getattr(self.game, "player", None)
        if not isinstance(player, dict) or not stat_key:
            return 0
        value = player.get(stat_key, 0)
        return value if isinstance(value, (int, float)) else 0

    def _format_bonus_percent(self, value):
        if isinstance(value, float):
            return f"+{int(value * 100)}%"
        return f"+{int(value)}%"

    def _format_stat_label(self, stat_key):
        labels = {
            "strength": "Strength",
            "dexterity": "Dexterity",
            "intelligence": "Intelligence",
            "gathering_mastery": "Gathering Mastery",
            "gathering_xp_bonus": "Gathering XP Bonus",
        }
        if stat_key in labels:
            return labels[stat_key]
        return str(stat_key or "None").replace("_", " ").title()

    def _get_profession_usable_zones(self, profession_id):
        data = getattr(self.game, "data", None)
        gathering_nodes = getattr(data, "gathering_nodes", {}) if data is not None else {}
        if not isinstance(gathering_nodes, dict):
            return []

        zones = []
        for zone_id, zone_nodes in gathering_nodes.items():
            if isinstance(zone_nodes, dict) and profession_id in zone_nodes:
                zones.append(zone_id)
        return zones

    def _get_zone_name(self, zone_id):
        data = getattr(self.game, "data", None)
        zones = getattr(data, "zones", {}) if data is not None else {}
        if not isinstance(zones, dict):
            return str(zone_id)
        zone_data = zones.get(zone_id, {})
        if isinstance(zone_data, dict):
            return zone_data.get("name", zone_id)
        return str(zone_id)

    def _get_panel_rect(self, screen):
        width, height = screen.get_size()
        panel_width = min(width - 28, max(720, int(width * 0.9)))
        panel_height = min(height - 74, max(480, int(height * 0.82)))
        panel_width = max(620, panel_width)
        panel_height = max(430, panel_height)
        return pygame.Rect((width - panel_width) // 2, 24, panel_width, panel_height)

    def _layout_rects(self):
        content = self.panel_rect.inflate(-36, -88)
        content.y += 52
        content.height = self.panel_rect.bottom - content.y - 22
        list_width = min(330, max(260, int(content.width * 0.39)))
        self.list_rect = pygame.Rect(content.x, content.y, list_width, content.height)
        self.detail_rect = pygame.Rect(
            self.list_rect.right + 18,
            content.y,
            content.width - list_width - 18,
            content.height,
        )

    def _draw_overlay_background(self, screen):
        overlay = pygame.Surface(screen.get_size(), pygame.SRCALPHA)
        overlay.fill((3, 5, 6, 176))
        screen.blit(overlay, (0, 0))

    def _draw_panel(self, screen, rect, title):
        pygame.draw.rect(screen, (22, 24, 25), rect, border_radius=10)
        pygame.draw.rect(screen, (114, 78, 38), rect, 3, border_radius=10)
        pygame.draw.rect(screen, (202, 164, 82), rect.inflate(-8, -8), 1, border_radius=8)
        title_text = self.title_font.render(title, True, (244, 232, 190))
        screen.blit(title_text, (rect.x + 22, rect.y + 17))
        subtitle = self.small_font.render("Gathering progress and mastery", True, (183, 179, 163))
        screen.blit(subtitle, (rect.x + 24, rect.y + 52))

    def _draw_button(self, screen, rect, label, active=False, enabled=True):
        fill = (70, 55, 35) if active else (46, 44, 40)
        border = (223, 190, 96) if active else (123, 101, 61)
        text_color = (244, 232, 190) if enabled else (119, 116, 104)
        pygame.draw.rect(screen, fill, rect, border_radius=6)
        pygame.draw.rect(screen, border, rect, 2, border_radius=6)
        text = self.small_font.render(label, True, text_color)
        screen.blit(text, text.get_rect(center=rect.center))

    def _draw_progress_bar(self, screen, rect, current, maximum):
        current = current if isinstance(current, (int, float)) else 0
        maximum = maximum if isinstance(maximum, (int, float)) else 0
        pygame.draw.rect(screen, (18, 20, 20), rect, border_radius=4)
        pygame.draw.rect(screen, (88, 77, 55), rect, 1, border_radius=4)
        if maximum <= 0:
            return
        ratio = max(0.0, min(1.0, current / maximum))
        fill = pygame.Rect(rect.x, rect.y, int(rect.width * ratio), rect.height)
        pygame.draw.rect(screen, (88, 156, 105), fill, border_radius=4)

    def _draw_message(self, screen, message):
        text = self.body_font.render(message, True, (214, 205, 176))
        screen.blit(text, text.get_rect(center=self.panel_rect.center))

    def _draw_text_line(self, screen, x, y, text, font, color=(214, 205, 176)):
        screen.blit(font.render(str(text), True, color), (x, y))

    def _truncate_text(self, text, font, max_width):
        text = str(text or "")
        if font.size(text)[0] <= max_width:
            return text
        ellipsis = "..."
        while text and font.size(text + ellipsis)[0] > max_width:
            text = text[:-1]
        return text + ellipsis if text else ellipsis

    def _wrap_text(self, text, font, max_width, max_lines):
        words = str(text or "").split()
        if not words:
            return []

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

        if len(lines) == max_lines and words:
            lines[-1] = self._truncate_text(lines[-1], font, max_width)
        return lines
