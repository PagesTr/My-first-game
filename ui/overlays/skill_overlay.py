import pygame

from systems.skills import (
    equip_skill,
    get_available_class_skills,
    get_player_skill_state,
    get_skill_slot_count,
    get_skill_type,
    is_skill_equipped,
    learn_or_upgrade_skill,
    spend_skill_point,
    unequip_skill,
)
from systems.stats import prepare_player_for_combat


class SkillOverlay:
    def __init__(self, game):
        if not pygame.font.get_init():
            pygame.font.init()

        self.game = game
        self.opened = False
        self.selected_skill_id = None
        self.selected_level_tab = "current"
        self.status_message = ""
        self.title_font = pygame.font.Font(None, 38)
        self.header_font = pygame.font.Font(None, 27)
        self.body_font = pygame.font.Font(None, 22)
        self.small_font = pygame.font.Font(None, 18)
        self.panel_rect = pygame.Rect(0, 0, 0, 0)
        self.close_rect = pygame.Rect(0, 0, 0, 0)
        self.active_rect = pygame.Rect(0, 0, 0, 0)
        self.passive_rect = pygame.Rect(0, 0, 0, 0)
        self.detail_rect = pygame.Rect(0, 0, 0, 0)
        self.learn_button_rect = pygame.Rect(0, 0, 0, 0)
        self.equip_button_rect = pygame.Rect(0, 0, 0, 0)
        self.skill_row_rects = []
        self.level_tab_rects = []

    def open(self):
        self.opened = True
        self._select_first_available_skill()

    def close(self):
        self.opened = False

    def is_open(self):
        return self.opened

    def handle_event(self, event):
        if not self.opened:
            return False

        if event.type == pygame.KEYDOWN:
            if event.key in (pygame.K_ESCAPE, pygame.K_k):
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

        for tab_id, rect, enabled in self.level_tab_rects:
            if rect.collidepoint(position):
                if enabled:
                    self.selected_level_tab = tab_id
                return True

        if self.learn_button_rect.collidepoint(position):
            self._learn_or_upgrade_selected_skill()
            return True

        if self.equip_button_rect.collidepoint(position):
            self._toggle_selected_skill_equipped()
            return True

        for skill_id, rect in self.skill_row_rects:
            if rect.collidepoint(position):
                self.selected_skill_id = skill_id
                self._normalize_selected_level_tab(self._get_skill_data(self._get_skills_data(), skill_id))
                self.status_message = ""
                return True

        return True

    def draw(self, screen):
        if not self.opened:
            return

        self._draw_overlay_background(screen)
        self.panel_rect = self._get_panel_rect(screen)
        self._layout_rects()
        self._draw_panel(screen, self.panel_rect, "Skills")

        self.close_rect = pygame.Rect(self.panel_rect.right - 48, self.panel_rect.y + 14, 30, 28)
        self._draw_button(screen, self.close_rect, "X")

        player = getattr(self.game, "player", None)
        if not isinstance(player, dict):
            self._draw_message(screen, "No player skills available.")
            return

        skills_data = self._get_skills_data()
        if not skills_data:
            self._draw_message(screen, "No skills available.")
            return

        active_skills, passive_skills = self._get_skill_groups(player, skills_data)
        if not active_skills and not passive_skills:
            self._draw_message(screen, "No skills available.")
            return

        if self.selected_skill_id not in {skill_id for skill_id, _ in active_skills + passive_skills}:
            self.selected_skill_id = (active_skills + passive_skills)[0][0]

        self._normalize_selected_level_tab(self._get_skill_data(skills_data, self.selected_skill_id))
        self.skill_row_rects = []
        self.level_tab_rects = []
        self._draw_summary(screen, player)
        self._draw_skill_list(screen, self.active_rect, "Active skills", active_skills)
        self._draw_skill_list(screen, self.passive_rect, "Passive skills", passive_skills)
        selected_data = self._get_skill_data(skills_data, self.selected_skill_id)
        self._draw_skill_details(screen, self.detail_rect, self.selected_skill_id, selected_data)

    def _get_panel_rect(self, screen):
        width, height = screen.get_size()
        panel_width = min(width - 28, max(760, int(width * 0.9)))
        panel_height = min(height - 70, max(500, int(height * 0.82)))
        panel_width = max(620, min(panel_width, width - 20))
        panel_height = max(480, min(panel_height, height - 62))
        return pygame.Rect((width - panel_width) // 2, 24, panel_width, panel_height)

    def _layout_rects(self):
        panel = self.panel_rect
        top = panel.y + 102
        detail_height = min(230, max(195, int(panel.h * 0.42)))
        list_bottom = panel.bottom - detail_height - 18
        gap = 14
        column_width = (panel.w - 50) // 2
        self.active_rect = pygame.Rect(panel.x + 18, top, column_width, max(170, list_bottom - top))
        self.passive_rect = pygame.Rect(self.active_rect.right + gap, top, column_width, max(170, list_bottom - top))
        self.detail_rect = pygame.Rect(panel.x + 18, list_bottom + 12, panel.w - 36, detail_height - 4)
        self.learn_button_rect = pygame.Rect(self.detail_rect.right - 304, self.detail_rect.bottom - 42, 140, 28)
        self.equip_button_rect = pygame.Rect(self.detail_rect.right - 154, self.detail_rect.bottom - 42, 136, 28)

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

    def _draw_summary(self, screen, player):
        used_slots = len(player.get("equipped_skills", [])) if isinstance(player.get("equipped_skills", []), list) else 0
        slot_count = get_skill_slot_count(player)
        parts = [
            ("Skill points: ", (204, 191, 168)),
            (str(player.get("skill_points", 0)), (245, 198, 92)),
            ("   Enhanced points: ", (204, 191, 168)),
            (str(player.get("enhanced_skill_points", 0)), (245, 198, 92)),
            ("   Active slots: ", (204, 191, 168)),
            (f"{used_slots} / {slot_count}", (190, 220, 235)),
        ]
        x = self.panel_rect.x + 24
        y = self.panel_rect.y + 58
        for text, color in parts:
            surface = self.body_font.render(text, True, color)
            screen.blit(surface, (x, y))
            x += surface.get_width()
        if self.status_message:
            message = self.small_font.render(self._truncate_text(self.status_message, self.small_font, self.panel_rect.w - 48), True, (238, 205, 140))
            screen.blit(message, (self.panel_rect.x + 24, self.panel_rect.y + 80))

    def _draw_skill_list(self, screen, rect, title, skills):
        pygame.draw.rect(screen, (31, 28, 25), rect, border_radius=6)
        pygame.draw.rect(screen, (118, 91, 54), rect, 2, border_radius=6)
        title_surface = self.header_font.render(title, True, (246, 235, 205))
        screen.blit(title_surface, (rect.x + 12, rect.y + 10))

        y = rect.y + 44
        row_height = 70
        for skill_id, skill_data in skills:
            if y + row_height > rect.bottom - 8:
                more = self.small_font.render("More skills available.", True, (160, 168, 176))
                screen.blit(more, (rect.x + 14, rect.bottom - 24))
                break
            row = pygame.Rect(rect.x + 10, y, rect.w - 20, row_height - 8)
            self.skill_row_rects.append((skill_id, row))
            self._draw_skill_row(screen, row, skill_id, skill_data, skill_id == self.selected_skill_id)
            y += row_height

        if not skills:
            empty = self.body_font.render("No skills available.", True, (160, 168, 176))
            screen.blit(empty, (rect.x + 14, rect.y + 48))

    def _draw_skill_row(self, screen, rect, skill_id, skill_data, selected=False):
        player = getattr(self.game, "player", {}) or {}
        skills_data = self._get_skills_data()
        skill_type = get_skill_type(skills_data, skill_id)
        skill_state = get_player_skill_state(player, skill_id)
        level = skill_state["level"]
        enhanced = skill_state["enhanced"]
        status = self._get_skill_status(player, skills_data, skill_id, skill_type, level)

        if selected:
            bg, border = (45, 55, 58), (235, 230, 190)
        elif level > 0 and skill_type == "active":
            bg, border = (36, 49, 55), (82, 125, 148)
        elif level > 0:
            bg, border = (38, 56, 46), (70, 118, 78)
        else:
            bg, border = (38, 35, 32), (78, 64, 46)
        pygame.draw.rect(screen, bg, rect, border_radius=5)
        pygame.draw.rect(screen, border, rect, 2 if selected else 1, border_radius=5)

        name = skill_data.get("name", skill_id) if isinstance(skill_data, dict) else skill_id
        title = self.body_font.render(self._truncate_text(name, self.body_font, rect.w - 24), True, (246, 235, 205))
        screen.blit(title, (rect.x + 10, rect.y + 8))

        details = f"{skill_type.title()} | Level {level} | {status}"
        if enhanced:
            details = f"{details} | Enhanced"
        detail_color = (145, 220, 165) if "Equipped" in status or "Passive active" in status else (190, 202, 210)
        detail = self.small_font.render(self._truncate_text(details, self.small_font, rect.w - 24), True, detail_color)
        screen.blit(detail, (rect.x + 10, rect.y + 36))

    def _draw_skill_details(self, screen, rect, skill_id, skill_data):
        pygame.draw.rect(screen, (31, 28, 25), rect, border_radius=6)
        pygame.draw.rect(screen, (118, 91, 54), rect, 2, border_radius=6)
        if not skill_id or not isinstance(skill_data, dict):
            text = self.body_font.render("No skill selected.", True, (160, 168, 176))
            screen.blit(text, (rect.x + 14, rect.y + 14))
            return

        player = getattr(self.game, "player", {}) or {}
        skills_data = self._get_skills_data()
        skill_type = get_skill_type(skills_data, skill_id)
        skill_state = get_player_skill_state(player, skill_id)
        level = skill_state["level"]
        name = skill_data.get("name", skill_id)
        level_data = self._get_skill_level_data(skill_data, self.selected_level_tab, skill_state)
        effect_lines = self._format_skill_effect_lines(skill_data, level_data)

        title = self.header_font.render(self._truncate_text(name, self.header_font, rect.w - 32), True, (246, 235, 205))
        screen.blit(title, (rect.x + 14, rect.y + 10))
        meta = (
            f"{skill_type.title()} | Current level: {level} / 4 | "
            f"Selected tab: {self._get_level_tab_label(self.selected_level_tab)} | "
            f"View: {self._get_level_view_label(skill_state)}"
        )
        meta_surface = self.body_font.render(self._truncate_text(meta, self.body_font, rect.w - 32), True, (190, 202, 210))
        screen.blit(meta_surface, (rect.x + 14, rect.y + 38))

        tab_bottom = self._draw_level_tabs(screen, skill_data, skill_state, pygame.Rect(rect.x + 14, rect.y + 64, rect.w - 28, 26))
        description_lines = self._wrap_text(skill_data.get("description", "No description."), self.small_font, rect.w - 348, 2)
        y = tab_bottom + 8
        for line in description_lines:
            screen.blit(self.small_font.render(line, True, (210, 218, 220)), (rect.x + 14, y))
            y += 18

        effect_y = y + 2
        effect_x = rect.x + 14
        max_effect_y = self.learn_button_rect.y - 6
        if not effect_lines:
            effect_lines = [("No level data.", (160, 168, 176))]
        for line, color in effect_lines:
            if effect_y + 18 > max_effect_y:
                more = self.small_font.render("More effects available.", True, (160, 168, 176))
                screen.blit(more, (effect_x, effect_y))
                break
            text = self.small_font.render(self._truncate_text(line, self.small_font, rect.w - 348), True, color)
            screen.blit(text, (effect_x, effect_y))
            effect_y += 18

        action_label, action_enabled = self._get_learn_action(player, level)
        self._draw_button(screen, self.learn_button_rect, action_label, enabled=action_enabled, warm=action_enabled)

        if skill_type == "active" and level > 0:
            equipped = is_skill_equipped(player, skill_id)
            self._draw_button(screen, self.equip_button_rect, "Unequip" if equipped else "Equip", active=equipped, enabled=True)
        else:
            self._draw_button(screen, self.equip_button_rect, "Passive" if level > 0 else "Equip", enabled=False)

    def _draw_level_tabs(self, screen, skill_data, skill_state, area):
        tabs = [
            ("current", "Current"),
            ("1", "Lv 1"),
            ("2", "Lv 2"),
            ("3", "Lv 3"),
            ("4", "Lv 4"),
            ("enhanced", "Enhanced"),
        ]
        self.level_tab_rects = []
        x = area.x
        for tab_id, label in tabs:
            width = max(58, self.small_font.size(label)[0] + 16)
            if x + width > area.right:
                break
            enabled = self._is_level_tab_available(skill_data, tab_id)
            rect = pygame.Rect(x, area.y, width, area.h)
            self.level_tab_rects.append((tab_id, rect, enabled))
            active = tab_id == self.selected_level_tab
            if tab_id == "enhanced" and enabled:
                bg = (58, 45, 70) if active else (44, 35, 52)
                border = (218, 178, 108) if active else (116, 86, 132)
                color = (246, 226, 174)
            elif enabled:
                bg = (80, 58, 35) if active else (44, 37, 32)
                border = (235, 198, 92) if active else (105, 82, 52)
                color = (246, 235, 205)
            else:
                bg, border, color = (38, 35, 32), (74, 68, 62), (130, 124, 116)
            pygame.draw.rect(screen, bg, rect, border_radius=5)
            pygame.draw.rect(screen, border, rect, 2 if active else 1, border_radius=5)
            text = self.small_font.render(self._truncate_text(label, self.small_font, rect.w - 6), True, color)
            screen.blit(text, text.get_rect(center=rect.center))
            x += width + 6
        return area.bottom

    def _draw_button(self, screen, rect, label, active=False, enabled=True, warm=False):
        if warm and enabled:
            bg, border, color = (132, 99, 42), (245, 198, 92), (255, 235, 160)
        else:
            bg = (56, 82, 90) if active else (44, 37, 32) if enabled else (38, 35, 32)
            border = (120, 190, 210) if active else (105, 82, 52) if enabled else (74, 68, 62)
            color = (246, 235, 205) if enabled else (130, 124, 116)
        pygame.draw.rect(screen, bg, rect, border_radius=5)
        pygame.draw.rect(screen, border, rect, 1 if rect.h < 30 else 2, border_radius=5)
        text = self.body_font.render(self._truncate_text(label, self.body_font, rect.w - 8), True, color)
        screen.blit(text, text.get_rect(center=rect.center))

    def _get_skills_data(self):
        skills_data = getattr(getattr(self.game, "data", None), "skills", {})
        if not isinstance(skills_data, dict):
            return {}
        return {skill_id: skill_data for skill_id, skill_data in skills_data.items() if isinstance(skill_data, dict)}

    def _get_skill_groups(self, player, skills_data):
        available_skills = get_available_class_skills(skills_data, player)
        active_skills = []
        passive_skills = []
        for skill_id, skill_data in available_skills:
            if get_skill_type(skills_data, skill_id) == "passive":
                passive_skills.append((skill_id, skill_data))
            else:
                active_skills.append((skill_id, skill_data))
        return active_skills, passive_skills

    def _get_skill_data(self, skills_data, skill_id):
        skill_data = skills_data.get(skill_id, {}) if isinstance(skills_data, dict) else {}
        return skill_data if isinstance(skill_data, dict) else {}

    def _select_first_available_skill(self):
        player = getattr(self.game, "player", None)
        skills_data = self._get_skills_data()
        if not isinstance(player, dict) or not skills_data:
            self.selected_skill_id = None
            return
        active_skills, passive_skills = self._get_skill_groups(player, skills_data)
        skills = active_skills + passive_skills
        self.selected_skill_id = skills[0][0] if skills else None
        self.selected_level_tab = "current"

    def _normalize_selected_level_tab(self, skill_data):
        if self._is_level_tab_available(skill_data, self.selected_level_tab):
            return
        self.selected_level_tab = "current"

    def _get_skill_status(self, player, skills_data, skill_id, skill_type, level):
        if level == 0:
            return "Learn"
        if skill_type == "active":
            return "Equipped" if is_skill_equipped(player, skill_id) else "Not equipped"
        if skill_type == "passive":
            return "Passive active"
        if level < 4:
            return "Upgrade"
        return "Max"

    def _get_learn_action(self, player, level):
        if level >= 4:
            return "Max", False
        label = "Learn" if level == 0 else "Upgrade"
        return label, player.get("skill_points", 0) > 0

    def _is_level_tab_available(self, skill_data, tab_id):
        if tab_id == "current":
            return True
        if not isinstance(skill_data, dict):
            return False
        if tab_id == "enhanced":
            return isinstance(skill_data.get("enhanced"), dict)
        levels = skill_data.get("levels", {})
        return isinstance(levels, dict) and isinstance(levels.get(tab_id), dict)

    def _get_skill_level_data(self, skill_data, tab_id, skill_state):
        if not isinstance(skill_data, dict):
            return None
        if not isinstance(skill_state, dict):
            skill_state = {"level": 0, "enhanced": False}

        levels = skill_data.get("levels", {})
        if not isinstance(levels, dict):
            levels = {}

        if tab_id == "current":
            if skill_state.get("enhanced") is True and isinstance(skill_data.get("enhanced"), dict):
                return skill_data.get("enhanced")
            level = skill_state.get("level", 0)
            if level > 0:
                return levels.get(str(level))
            return levels.get("1")

        if tab_id in {"1", "2", "3", "4"}:
            return levels.get(tab_id)

        if tab_id == "enhanced":
            return skill_data.get("enhanced") if isinstance(skill_data.get("enhanced"), dict) else None

        return None

    def _format_skill_effect_lines(self, skill_data, level_data):
        if not isinstance(skill_data, dict) or not isinstance(level_data, dict):
            return [("No data for this level.", (160, 168, 176))]

        lines = []
        stat_modifiers = level_data.get("stat_modifiers")
        if isinstance(stat_modifiers, dict):
            for stat_key, value in stat_modifiers.items():
                if isinstance(value, (int, float)) and not isinstance(value, bool):
                    lines.append((f"{self._format_signed_value(value)} {self._format_stat_label(stat_key)}", (170, 230, 178)))

        per_level_modifiers = level_data.get("stat_modifiers_per_character_level")
        if isinstance(per_level_modifiers, dict):
            for stat_key, value in per_level_modifiers.items():
                if isinstance(value, (int, float)) and not isinstance(value, bool):
                    label = self._format_stat_label(stat_key)
                    lines.append((f"{self._format_signed_value(value)} {label} per character level", (170, 230, 178)))

        known_fields = {"stat_modifiers", "stat_modifiers_per_character_level"}
        for field_key, value in level_data.items():
            if field_key in known_fields:
                continue
            if isinstance(value, (int, float)) and not isinstance(value, bool):
                lines.append((f"{self._format_field_label(field_key)}: {self._format_numeric_value(field_key, value)}", self._get_effect_line_color(field_key)))
            elif isinstance(value, dict):
                for nested_key, nested_value in list(value.items())[:3]:
                    nested_label = f"{self._format_field_label(field_key)} {self._format_field_label(nested_key)}"
                    lines.append((f"{nested_label}: {nested_value}", (210, 218, 220)))
            elif value is not None:
                lines.append((f"{self._format_field_label(field_key)}: {value}", (210, 218, 220)))

        trigger = skill_data.get("trigger")
        if trigger:
            lines.append((f"Trigger: {self._format_trigger_label(trigger)}", (176, 205, 225)))

        return lines or [("No level data.", (160, 168, 176))]

    def _get_level_view_label(self, skill_state):
        tab_id = self.selected_level_tab
        level = skill_state.get("level", 0) if isinstance(skill_state, dict) else 0
        enhanced = skill_state.get("enhanced", False) if isinstance(skill_state, dict) else False
        if tab_id == "enhanced":
            return "Enhanced version"
        if tab_id == "current":
            return "Enhanced" if enhanced else "Current" if level > 0 else "Preview"
        if tab_id in {"1", "2", "3", "4"}:
            tab_level = int(tab_id)
            if tab_level == level and not enhanced:
                return "Current"
            if tab_level > level:
                return "Preview"
            return "Previous"
        return "Preview"

    def _get_level_tab_label(self, tab_id):
        if tab_id == "current":
            return "Current"
        if tab_id == "enhanced":
            return "Enhanced"
        if tab_id in {"1", "2", "3", "4"}:
            return f"Lv {tab_id}"
        return "Unknown"

    def _format_stat_label(self, stat_key):
        labels = {
            "max_hp": "Max HP",
            "current_hp": "Current HP",
            "hp": "HP",
        }
        return labels.get(str(stat_key), self._format_field_label(stat_key))

    def _format_field_label(self, field_key):
        labels = {
            "damage_multiplier": "Damage multiplier",
            "enemy_hp_threshold": "Enemy HP threshold",
            "max_hp": "Max HP",
            "current_hp": "Current HP",
            "hp": "HP",
        }
        key = str(field_key or "unknown")
        return labels.get(key, key.replace("_", " ").capitalize())

    def _format_numeric_value(self, field_key, value):
        if field_key == "damage_multiplier":
            return f"x{self._format_plain_number(value)}"
        if field_key == "enemy_hp_threshold":
            return f"{int(round(value * 100))}%"
        if field_key == "cooldown":
            turns = int(value) if float(value).is_integer() else value
            return f"{turns} turns"
        return self._format_plain_number(value)

    def _format_trigger_label(self, trigger):
        labels = {
            "always": "Always active",
            "before_player_attack_after_damage_taken": "After taking damage",
            "before_player_attack_when_enemy_low_hp": "When enemy HP is low",
        }
        return labels.get(str(trigger), self._format_field_label(trigger))

    def _format_signed_value(self, value):
        prefix = "+" if value >= 0 else ""
        return f"{prefix}{self._format_plain_number(value)}"

    def _format_plain_number(self, value):
        if isinstance(value, float) and value.is_integer():
            return str(int(value))
        return str(value)

    def _get_effect_line_color(self, field_key):
        if field_key in {"cooldown", "enemy_hp_threshold"}:
            return (176, 205, 225)
        if field_key == "damage_multiplier":
            return (224, 232, 190)
        return (210, 218, 220)

    def _learn_or_upgrade_selected_skill(self):
        player = getattr(self.game, "player", None)
        if not isinstance(player, dict) or not self.selected_skill_id:
            self.status_message = "No skill selected."
            return
        level = get_player_skill_state(player, self.selected_skill_id)["level"]
        if level >= 4:
            self.status_message = "Skill already maxed."
            return
        if player.get("skill_points", 0) <= 0:
            self.status_message = "No skill points available."
            return

        if not learn_or_upgrade_skill(player, self.selected_skill_id):
            self.status_message = "Skill action failed."
            return
        if not spend_skill_point(player):
            self.status_message = "No skill points available."
            return

        previous_max_hp = player.get("max_hp", 0)
        self._recalculate_player_stats(previous_max_hp)
        self._save_current_game()
        self.status_message = "Skill learned." if level == 0 else "Skill upgraded."

    def _toggle_selected_skill_equipped(self):
        player = getattr(self.game, "player", None)
        skills_data = self._get_skills_data()
        if not isinstance(player, dict) or not self.selected_skill_id:
            self.status_message = "No skill selected."
            return
        if get_skill_type(skills_data, self.selected_skill_id) != "active":
            self.status_message = "Passive skills cannot be equipped."
            return
        if get_player_skill_state(player, self.selected_skill_id)["level"] <= 0:
            self.status_message = "Learn this skill first."
            return

        if is_skill_equipped(player, self.selected_skill_id):
            if unequip_skill(player, self.selected_skill_id):
                self.status_message = "Skill unequipped."
                self._save_current_game()
            else:
                self.status_message = "Could not unequip skill."
            return

        if equip_skill(player, self.selected_skill_id):
            self.status_message = "Skill equipped."
            self._save_current_game()
        else:
            self.status_message = "No active skill slot available."

    def _save_current_game(self):
        if hasattr(self.game, "save_current_game"):
            self.game.save_current_game()

    def _recalculate_player_stats(self, previous_max_hp):
        player = getattr(self.game, "player", None)
        data = getattr(self.game, "data", None)
        if not isinstance(player, dict) or data is None:
            return
        prepare_player_for_combat(
            player,
            getattr(data, "items", {}),
            getattr(data, "classes", {}),
            getattr(data, "skills", {}),
        )
        new_max_hp = player.get("max_hp", 0)
        max_hp_gain = new_max_hp - previous_max_hp
        if max_hp_gain > 0:
            player["current_hp"] = min(new_max_hp, player.get("current_hp", 0) + max_hp_gain)

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
        return lines or [""]
