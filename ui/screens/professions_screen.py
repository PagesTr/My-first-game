import pygame

from systems.professions import (
    get_profession_mastery,
    get_profession_progress,
)


class Button:
    def __init__(self, rect, text):
        self.rect = pygame.Rect(rect)
        self.text = text

    def draw(self, screen, font):
        pygame.draw.rect(screen, (58, 68, 78), self.rect, border_radius=6)
        pygame.draw.rect(screen, (210, 220, 225), self.rect, 2, border_radius=6)
        label = font.render(self.text, True, (245, 245, 245))
        screen.blit(label, (self.rect.x + 14, self.rect.y + 13))

    def is_clicked(self, pos):
        return self.rect.collidepoint(pos)


class ProfessionsScreen:
    def __init__(self, game):
        self.game = game
        self.title_font = pygame.font.Font(None, 46)
        self.font = pygame.font.Font(None, 24)
        self.small_font = pygame.font.Font(None, 20)
        self.back_btn = Button((50, 520, 140, 50), "Back")
        self.selected_profession_id = None
        self.profession_card_buttons = []

    def handle_event(self, event):
        if event.type != pygame.MOUSEBUTTONDOWN:
            return

        pos = event.pos
        if self.back_btn.is_clicked(pos):
            self.game.state = "town"
            return

        for profession_id, rect in self.profession_card_buttons:
            if rect.collidepoint(pos):
                self.selected_profession_id = profession_id
                return

    def draw(self, screen):
        screen.fill((18, 24, 30))
        self._ensure_selected_profession()

        title = self.title_font.render("Professions", True, (245, 245, 245))
        screen.blit(title, (50, 42))
        subtitle = self.font.render(
            "Gathering progress and mastery",
            True,
            (190, 200, 205),
        )
        screen.blit(subtitle, (52, 86))

        self._draw_profession_cards(screen)
        self._draw_profession_detail(screen)
        self.back_btn.draw(screen, self.font)

    def _get_professions_data(self):
        professions = getattr(self.game.data, "professions", {}) or {}
        if isinstance(professions, dict):
            return professions
        return {}

    def _ensure_selected_profession(self):
        professions = self._get_professions_data()
        if self.selected_profession_id in professions:
            return
        self.selected_profession_id = next(iter(professions), None)

    def _draw_profession_cards(self, screen):
        professions = self._get_professions_data()
        self.profession_card_buttons = []

        if not professions:
            empty = self.font.render("No professions available", True, (190, 200, 205))
            screen.blit(empty, (54, 150))
            return

        player = self.game.player or {}
        for index, (profession_id, profession_data) in enumerate(professions.items()):
            rect = self._get_profession_card_rect(index)
            progress = get_profession_progress(player, profession_id)
            mastery = get_profession_mastery(player, profession_id, professions)
            selected = profession_id == self.selected_profession_id
            border = (230, 210, 110) if selected else (105, 120, 132)

            pygame.draw.rect(screen, (34, 42, 50), rect, border_radius=6)
            pygame.draw.rect(screen, border, rect, 2, border_radius=6)

            name = profession_data.get("name", profession_id)
            name_text = self.font.render(name, True, (245, 245, 245))
            screen.blit(name_text, (rect.x + 16, rect.y + 12))

            level_text = self.small_font.render(
                f"Level {progress['level']}  Mastery {mastery}",
                True,
                (190, 200, 205),
            )
            screen.blit(level_text, (rect.x + 16, rect.y + 40))

            xp_text = self.small_font.render(
                f"XP {progress['xp']} / {progress['next_xp']}",
                True,
                (190, 200, 205),
            )
            screen.blit(xp_text, (rect.x + 16, rect.y + 62))
            self._draw_progress_bar(
                screen,
                pygame.Rect(rect.x + 16, rect.y + 84, rect.w - 32, 8),
                progress["xp"],
                progress["next_xp"],
            )

            self.profession_card_buttons.append((profession_id, rect))

    def _draw_profession_detail(self, screen):
        professions = self._get_professions_data()
        profession_id = self.selected_profession_id
        profession_data = professions.get(profession_id)
        if not isinstance(profession_data, dict):
            return

        player = self.game.player or {}
        progress = get_profession_progress(player, profession_id)
        mastery = get_profession_mastery(player, profession_id, professions)
        primary_stat = profession_data.get("primary_stat", "")
        mastery_bonus_stat = profession_data.get("mastery_bonus_stat", "")
        xp_bonus_stat = profession_data.get("xp_bonus_stat", "")
        mastery_bonus = self._get_player_bonus_value(mastery_bonus_stat)
        global_mastery = self._get_player_bonus_value("gathering_mastery")
        xp_bonus = self._get_player_bonus_value(xp_bonus_stat)
        global_xp_bonus = self._get_player_bonus_value("gathering_xp_bonus")

        panel = pygame.Rect(360, 132, 390, 390)
        pygame.draw.rect(screen, (34, 42, 50), panel, border_radius=6)
        pygame.draw.rect(screen, (105, 120, 132), panel, 2, border_radius=6)

        y = panel.y + 16
        name = profession_data.get("name", profession_id)
        name_text = self.font.render(name, True, (245, 245, 245))
        screen.blit(name_text, (panel.x + 18, y))
        y += 28

        description = profession_data.get("description", "")
        if description:
            desc_text = self.small_font.render(description[:48], True, (190, 200, 205))
            screen.blit(desc_text, (panel.x + 18, y))
            y += 28

        detail_lines = [
            f"Primary stat: {self._format_stat_label(primary_stat)}",
            "Mastery: level + primary stat / 2 + bonuses",
            f"Level: {progress['level']}  XP: {progress['xp']} / {progress['next_xp']}",
            f"Mastery: {mastery}",
            f"Mastery bonus: +{mastery_bonus}  Global: +{global_mastery}",
            (
                f"XP bonus: {self._format_bonus_percent(xp_bonus)}  "
                f"Global: {self._format_bonus_percent(global_xp_bonus)}"
            ),
            f"Mastery stat: {self._format_stat_label(mastery_bonus_stat)}",
            f"XP stat: {self._format_stat_label(xp_bonus_stat)}",
        ]

        for line in detail_lines:
            text = self.small_font.render(line, True, (210, 220, 225))
            screen.blit(text, (panel.x + 18, y))
            y += 22

        y += 4
        used_in = self.small_font.render("Used in:", True, (245, 245, 245))
        screen.blit(used_in, (panel.x + 18, y))
        y += 22

        usable_zones = self._get_profession_usable_zones(profession_id)
        if not usable_zones:
            empty = self.small_font.render(
                "No known gathering zones",
                True,
                (190, 200, 205),
            )
            screen.blit(empty, (panel.x + 30, y))
            return

        for zone_id in usable_zones[:5]:
            zone_name = self._get_zone_name(zone_id)
            zone_line = self.small_font.render(f"- {zone_name}", True, (190, 200, 205))
            screen.blit(zone_line, (panel.x + 30, y))
            y += 20

    def _get_profession_card_rect(self, index):
        return pygame.Rect(50, 142 + index * 116, 280, 100)

    def _get_profession_usable_zones(self, profession_id):
        gathering_nodes = getattr(self.game.data, "gathering_nodes", {}) or {}
        if not isinstance(gathering_nodes, dict):
            return []

        zones = []
        for zone_id, zone_nodes in gathering_nodes.items():
            if isinstance(zone_nodes, dict) and profession_id in zone_nodes:
                zones.append(zone_id)
        return zones

    def _get_zone_name(self, zone_id):
        zones = getattr(self.game.data, "zones", {}) or {}
        zone_data = zones.get(zone_id, {})
        return zone_data.get("name", zone_id)

    def _format_stat_label(self, stat_key):
        labels = {
            "strength": "Strength",
            "dexterity": "Dexterity",
            "intelligence": "Intelligence",
            "gathering_mastery": "Gathering Mastery",
        }
        if stat_key in labels:
            return labels[stat_key]
        return str(stat_key or "None").replace("_", " ").title()

    def _draw_progress_bar(self, screen, rect, current, maximum):
        pygame.draw.rect(screen, (22, 28, 34), rect, border_radius=4)
        pygame.draw.rect(screen, (85, 95, 105), rect, 1, border_radius=4)
        if maximum <= 0:
            return

        ratio = max(0, min(1, current / maximum))
        fill = pygame.Rect(rect.x, rect.y, int(rect.w * ratio), rect.h)
        pygame.draw.rect(screen, (90, 150, 125), fill, border_radius=4)

    def _get_player_bonus_value(self, stat_key):
        if not self.game.player:
            return 0
        return self.game.player.get(stat_key, 0)

    def _format_bonus_percent(self, value):
        if isinstance(value, float):
            return f"+{int(value * 100)}%"
        return f"+{value}%"
