import pygame


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
WARNING = (218, 176, 72)
DISABLED_BG = (42, 40, 36)
DISABLED_TEXT = (120, 116, 105)


CATEGORIES = (
    "Best Runs",
    "Dungeons",
    "Bosses",
    "Loot",
    "Professions",
    "Progress",
)


class TrialsOverlay:
    def __init__(self, game):
        if not pygame.font.get_init():
            pygame.font.init()

        self.game = game
        self.opened = False
        self.selected_category = "Best Runs"
        self.title_font = pygame.font.Font(None, 38)
        self.header_font = pygame.font.Font(None, 27)
        self.body_font = pygame.font.Font(None, 22)
        self.small_font = pygame.font.Font(None, 18)
        self.panel_rect = pygame.Rect(0, 0, 0, 0)
        self.close_rect = pygame.Rect(0, 0, 0, 0)
        self.category_rect = pygame.Rect(0, 0, 0, 0)
        self.content_rect = pygame.Rect(0, 0, 0, 0)
        self.footer_rect = pygame.Rect(0, 0, 0, 0)
        self.category_rects = []

    def open(self):
        self.opened = True
        if self.selected_category not in CATEGORIES:
            self.selected_category = CATEGORIES[0]

    def close(self):
        self.opened = False

    def is_open(self):
        return self.opened

    def handle_event(self, event):
        if not self.opened:
            return False

        if event.type == pygame.KEYDOWN:
            if event.key in (pygame.K_ESCAPE, pygame.K_t):
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

        for category, rect in self.category_rects:
            if rect.collidepoint(position):
                self.selected_category = category
                return True

        return True

    def draw(self, screen):
        if not self.opened:
            return

        self._draw_overlay_background(screen)
        self.panel_rect = self._get_panel_rect(screen)
        self._layout_rects()
        self._draw_panel(screen, self.panel_rect)
        self.close_rect = pygame.Rect(self.panel_rect.right - 48, self.panel_rect.y + 14, 30, 28)
        self._draw_button(screen, self.close_rect, "X")

        if not isinstance(getattr(self.game, "player", None), dict):
            self._draw_message(screen, "No player record available.")
            return

        self._draw_category_list(screen, self.category_rect)
        self._draw_record_content(screen, self.content_rect)
        self._draw_footer(screen)

    def _get_panel_rect(self, screen):
        width, height = screen.get_size()
        panel_width = min(width - 28, max(740, int(width * 0.88)))
        panel_height = min(height - 72, max(480, int(height * 0.82)))
        panel_width = max(620, min(panel_width, width - 20))
        panel_height = max(440, min(panel_height, height - 62))
        return pygame.Rect((width - panel_width) // 2, 24, panel_width, panel_height)

    def _layout_rects(self):
        content_top = self.panel_rect.y + 82
        content_bottom = self.panel_rect.bottom - 58
        gap = 16
        category_width = min(230, max(190, int((self.panel_rect.width - 36) * 0.31)))
        self.category_rect = pygame.Rect(
            self.panel_rect.x + 18,
            content_top,
            category_width,
            content_bottom - content_top,
        )
        self.content_rect = pygame.Rect(
            self.category_rect.right + gap,
            content_top,
            self.panel_rect.right - self.category_rect.right - gap - 18,
            content_bottom - content_top,
        )
        self.footer_rect = pygame.Rect(
            self.panel_rect.x + 24,
            self.panel_rect.bottom - 44,
            self.panel_rect.width - 48,
            24,
        )

    def _draw_overlay_background(self, screen):
        overlay = pygame.Surface(screen.get_size(), pygame.SRCALPHA)
        overlay.fill(OVERLAY_DIM)
        screen.blit(overlay, (0, 0))

    def _draw_panel(self, screen, rect):
        pygame.draw.rect(screen, PANEL_BG, rect, border_radius=10)
        pygame.draw.rect(screen, BORDER_BRIGHT, rect, 2, border_radius=10)
        pygame.draw.rect(screen, BORDER_NORMAL, rect.inflate(-8, -8), 1, border_radius=8)
        title = self.title_font.render("Hall of Trials", True, TEXT_PRIMARY)
        screen.blit(title, (rect.x + 22, rect.y + 16))
        subtitle = self.small_font.render("Personal records and unfinished ambitions.", True, TEXT_SECONDARY)
        screen.blit(subtitle, (rect.x + 24, rect.y + 52))

    def _draw_button(self, screen, rect, label, active=False, enabled=True, warm=False):
        if warm and enabled:
            bg, border, color = (116, 82, 34), BORDER_SELECTED, TEXT_PRIMARY
        else:
            bg = CARD_BG_SELECTED if active else CARD_BG if enabled else DISABLED_BG
            border = BORDER_SELECTED if active else BORDER_NORMAL if enabled else DISABLED_TEXT
            color = TEXT_PRIMARY if enabled else DISABLED_TEXT
        pygame.draw.rect(screen, bg, rect, border_radius=5)
        pygame.draw.rect(screen, border, rect, 2 if active or warm else 1, border_radius=5)
        text = self.small_font.render(self._truncate_text(label, self.small_font, rect.width - 10), True, color)
        screen.blit(text, text.get_rect(center=rect.center))

    def _draw_category_list(self, screen, rect):
        self.category_rects = []
        pygame.draw.rect(screen, PANEL_BG_SECONDARY, rect, border_radius=8)
        pygame.draw.rect(screen, BORDER_NORMAL, rect, 2, border_radius=8)

        y = rect.y + 12
        row_height = 38
        for category in CATEGORIES:
            row = pygame.Rect(rect.x + 10, y, rect.width - 20, row_height - 6)
            self.category_rects.append((category, row))
            self._draw_button(screen, row, category, active=category == self.selected_category)
            y += row_height

    def _draw_record_content(self, screen, rect):
        pygame.draw.rect(screen, PANEL_BG_SECONDARY, rect, border_radius=8)
        pygame.draw.rect(screen, BORDER_NORMAL, rect, 2, border_radius=8)

        title = self.header_font.render(self.selected_category, True, TEXT_PRIMARY)
        screen.blit(title, (rect.x + 16, rect.y + 14))
        y = rect.y + 52

        for label, value, status in self._get_records_for_category(self.selected_category):
            y = self._draw_record_row(screen, rect.x + 16, y, label, value, status)
            if y > rect.bottom - 34:
                break

        note = self._get_category_note(self.selected_category)
        note_lines = self._wrap_text(note, self.small_font, rect.width - 32, 2)
        note_y = rect.bottom - 42
        for line in note_lines:
            text = self.small_font.render(line, True, TEXT_MUTED)
            screen.blit(text, (rect.x + 16, note_y))
            note_y += 17

    def _draw_record_row(self, screen, x, y, label, value, status=None):
        row_rect = pygame.Rect(x, y, self.content_rect.right - x - 16, 30)
        pygame.draw.rect(screen, CARD_BG, row_rect, border_radius=5)
        pygame.draw.rect(screen, BORDER_NORMAL, row_rect, 1, border_radius=5)

        label_text = self.small_font.render(
            self._truncate_text(label, self.small_font, row_rect.width - 130),
            True,
            TEXT_SECONDARY,
        )
        screen.blit(label_text, (row_rect.x + 10, row_rect.y + 8))

        color = self._get_status_color(status, value)
        value_text = self.small_font.render(
            self._truncate_text(str(value), self.small_font, 116),
            True,
            color,
        )
        screen.blit(value_text, value_text.get_rect(midright=(row_rect.right - 10, row_rect.centery)))
        return y + 36

    def _draw_footer(self, screen):
        message = "Do better. The ledger has room."
        text = self.small_font.render(self._truncate_text(message, self.small_font, self.footer_rect.width), True, WARNING)
        screen.blit(text, (self.footer_rect.x, self.footer_rect.y + 4))

    def _draw_message(self, screen, message):
        text = self.body_font.render(message, True, TEXT_SECONDARY)
        screen.blit(text, text.get_rect(center=self.panel_rect.center))

    def _get_records_for_category(self, category):
        if category == "Best Runs":
            return [
                ("Best gold run", "Coming soon", "pending"),
                ("Best XP run", "Coming soon", "pending"),
                ("Fastest run", "Coming soon", "pending"),
                ("Best loot run", "Coming soon", "pending"),
            ]
        if category == "Dungeons":
            return [
                ("Goblin Camp clears", self._get_dungeon_clear_count("forest_goblin_camp"), "value"),
                ("Buried Grove clears", self._get_dungeon_clear_count("forest_buried_grove"), "value"),
                ("Deathless clears", "Coming soon", "pending"),
                ("Fastest clear", "Coming soon", "pending"),
            ]
        if category == "Bosses":
            return [
                ("Grubfang defeated", self._format_yes_no(self._is_boss_defeated("grubfang_rootcaller")), "value"),
                ("Rootcaller defeated", self._format_yes_no(self._is_boss_defeated("grubfang_rootcaller")), "value"),
                ("Cleanest boss kill", "Coming soon", "pending"),
            ]
        if category == "Loot":
            return [
                ("Best item found", "Coming soon", "pending"),
                ("Most gold earned", "Coming soon", "pending"),
                ("Rarest drop", "Coming soon", "pending"),
                ("Goblin ears collected", self._get_inventory_item_count("goblin_ear"), "value"),
            ]
        if category == "Professions":
            highest_level, highest_mastery = self._get_profession_highs()
            return [
                ("Highest profession level", highest_level, "value"),
                ("Highest mastery", highest_mastery, "value"),
                ("Most gathered resource", "Coming soon", "pending"),
                ("Offline gathering record", "Coming soon", "pending"),
            ]
        if category == "Progress":
            achievements = self._get_achievements_state()
            quests = self._get_quests_state()
            player = self._get_player()
            return [
                ("Achievements unlocked", self._get_safe_count(achievements.get("unlocked")), "value"),
                ("Achievements claimed", self._get_safe_count(achievements.get("claimed")), "value"),
                ("Active quests", self._get_safe_count(quests.get("active")), "value"),
                ("Completed quests", self._get_safe_count(quests.get("completed") or quests.get("last_completed")), "value"),
                ("Current level", player.get("level", "-"), "value"),
                ("Gold", player.get("gold", "-"), "value"),
            ]
        return [(category, self._format_missing_record("Record"), "pending")]

    def _get_player(self):
        player = getattr(self.game, "player", None)
        return player if isinstance(player, dict) else {}

    def _get_achievements_state(self):
        achievements = self._get_player().get("achievements", {})
        return achievements if isinstance(achievements, dict) else {}

    def _get_quests_state(self):
        quests = self._get_player().get("quests", {})
        return quests if isinstance(quests, dict) else {}

    def _get_professions_state(self):
        professions = self._get_player().get("professions", {})
        return professions if isinstance(professions, dict) else {}

    def _get_dungeons_state(self):
        dungeons = self._get_player().get("dungeons", {})
        return dungeons if isinstance(dungeons, dict) else {}

    def _get_safe_count(self, container):
        if isinstance(container, (list, tuple, set, dict)):
            return len(container)
        return "-"

    def _format_missing_record(self, label):
        return f"{label}: Coming soon"

    def _get_dungeon_clear_count(self, dungeon_id):
        dungeons = self._get_dungeons_state()
        dungeon_state = dungeons.get(dungeon_id, {}) if isinstance(dungeons, dict) else {}
        if isinstance(dungeon_state, dict):
            for key in ("clears", "completed", "clear_count"):
                value = dungeon_state.get(key)
                if isinstance(value, int):
                    return value

        progress = self._get_achievements_state().get("progress", {})
        if not isinstance(progress, dict):
            return "-"
        best = None
        achievements_data = getattr(getattr(self.game, "data", None), "achievements", {}) or {}
        if not isinstance(achievements_data, dict):
            return "-"
        for achievement_id, achievement in achievements_data.items():
            if not isinstance(achievement, dict):
                continue
            objective = achievement.get("objective", {})
            if not isinstance(objective, dict):
                continue
            if objective.get("type") != "clear_dungeon" or objective.get("target") != dungeon_id:
                continue
            value = progress.get(achievement_id)
            if isinstance(value, int):
                best = value if best is None else max(best, value)
        return best if best is not None else "-"

    def _is_boss_defeated(self, boss_id):
        achievements = self._get_achievements_state()
        unlocked = achievements.get("unlocked", [])
        if not isinstance(unlocked, list):
            return None
        if "forest_rootcaller_defeated" in unlocked and boss_id == "grubfang_rootcaller":
            return True
        achievements_data = getattr(getattr(self.game, "data", None), "achievements", {}) or {}
        if not isinstance(achievements_data, dict):
            return None
        for achievement_id in unlocked:
            achievement = achievements_data.get(achievement_id, {})
            objective = achievement.get("objective", {}) if isinstance(achievement, dict) else {}
            if isinstance(objective, dict) and objective.get("type") == "defeat_boss" and objective.get("target") == boss_id:
                return True
        return False

    def _format_yes_no(self, value):
        if value is True:
            return "Yes"
        if value is False:
            return "No"
        return "-"

    def _get_inventory_item_count(self, item_id):
        inventory = self._get_player().get("inventory", {})
        slots = inventory.get("slots", []) if isinstance(inventory, dict) else []
        if not isinstance(slots, list):
            return "-"
        total = 0
        found = False
        for slot in slots:
            if not isinstance(slot, dict) or slot.get("item") != item_id:
                continue
            found = True
            quantity = slot.get("quantity", 1)
            total += quantity if isinstance(quantity, int) else 1
        return total if found else "-"

    def _get_profession_highs(self):
        professions = self._get_professions_state()
        if not professions:
            return "-", "-"
        highest_level = None
        highest_mastery = None
        for profession in professions.values():
            if not isinstance(profession, dict):
                continue
            level = profession.get("level")
            if isinstance(level, int):
                highest_level = level if highest_level is None else max(highest_level, level)
                highest_mastery = level if highest_mastery is None else max(highest_mastery, level)
        return (
            highest_level if highest_level is not None else "-",
            highest_mastery if highest_mastery is not None else "-",
        )

    def _get_category_note(self, category):
        notes = {
            "Best Runs": "No recorded trials yet. Convenient.",
            "Dungeons": "Some victories deserve numbers. Some defeats deserve silence.",
            "Bosses": "The forest remembers. Mostly your mistakes.",
            "Loot": "Shiny things are not achievements. They are evidence.",
            "Professions": "Honest work, suspiciously measured.",
            "Progress": "Progress is progress, even when it limps.",
        }
        return notes.get(category, "Do better. The ledger has room.")

    def _get_status_color(self, status, value):
        if status == "pending" or value in {"Coming soon", "-"}:
            return TEXT_MUTED
        if value == "Yes":
            return SUCCESS
        if value == "No":
            return TEXT_SECONDARY
        return TEXT_PRIMARY

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
