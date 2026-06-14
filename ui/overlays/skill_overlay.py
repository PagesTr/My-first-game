import json
from pathlib import Path

import pygame

from systems.skills import (
    enhance_skill,
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


class SkillOverlay:
    def __init__(self, game):
        if not pygame.font.get_init():
            pygame.font.init()

        self.game = game
        self.opened = False
        self.selected_skill_id = None
        self.selected_level_tab = "current"
        self.skill_kind_tab = "active"
        self.status_message = ""
        self.title_font = pygame.font.Font(None, 38)
        self.header_font = pygame.font.Font(None, 27)
        self.body_font = pygame.font.Font(None, 22)
        self.small_font = pygame.font.Font(None, 18)
        self.panel_rect = pygame.Rect(0, 0, 0, 0)
        self.close_rect = pygame.Rect(0, 0, 0, 0)
        self.library_rect = pygame.Rect(0, 0, 0, 0)
        self.active_slots_rect = pygame.Rect(0, 0, 0, 0)
        self.detail_rect = pygame.Rect(0, 0, 0, 0)
        self.learn_button_rect = pygame.Rect(0, 0, 0, 0)
        self.enhance_button_rect = pygame.Rect(0, 0, 0, 0)
        self.equip_button_rect = pygame.Rect(0, 0, 0, 0)
        self.prev_page_rect = pygame.Rect(0, 0, 0, 0)
        self.next_page_rect = pygame.Rect(0, 0, 0, 0)
        self.skill_page = 0
        self.skill_pages = {"active": 0, "passive": 0}
        self.skill_slot_rects = []
        self.active_slot_rects = []
        self.skill_kind_tab_rects = []
        self.level_tab_rects = []
        self.skill_icon_map = self._load_skill_icon_map()
        self.skill_icon_surfaces = {}

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
            elif event.key == pygame.K_TAB:
                self._set_skill_kind_tab("passive" if self.skill_kind_tab == "active" else "active")
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

        for kind_id, rect in self.skill_kind_tab_rects:
            if rect.collidepoint(position):
                self._set_skill_kind_tab(kind_id)
                return True

        visible_skills = self._get_visible_skills()
        current_page = self._get_current_skill_page()
        total_pages = self._get_total_skill_pages(visible_skills)
        if self.prev_page_rect.collidepoint(position) and current_page > 0:
            self.skill_pages[self.skill_kind_tab] = current_page - 1
            return True
        if self.next_page_rect.collidepoint(position) and current_page < total_pages - 1:
            self.skill_pages[self.skill_kind_tab] = current_page + 1
            return True

        for tab_id, rect, enabled in self.level_tab_rects:
            if rect.collidepoint(position):
                if enabled:
                    self.selected_level_tab = tab_id
                return True

        if self.learn_button_rect.collidepoint(position):
            self._learn_or_upgrade_selected_skill()
            return True

        if self.enhance_button_rect.collidepoint(position):
            self._enhance_selected_skill()
            return True

        if self.equip_button_rect.collidepoint(position):
            self._toggle_selected_skill_equipped()
            return True

        for skill_id, rect in self.skill_slot_rects:
            if rect.collidepoint(position):
                self.selected_skill_id = skill_id
                self._normalize_selected_level_tab(self._get_skill_data(self._get_skills_data(), skill_id))
                self.status_message = ""
                return True

        for skill_id, rect in self.active_slot_rects:
            if rect.collidepoint(position):
                if skill_id:
                    self.selected_skill_id = skill_id
                    self._normalize_selected_level_tab(self._get_skill_data(self._get_skills_data(), skill_id))
                    self.status_message = ""
                else:
                    self.status_message = "Empty skill slot."
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

        all_skills = self._get_available_skills()
        if not all_skills:
            self._draw_message(screen, "No skills available.")
            return

        visible_skills = self._get_visible_skills()
        if visible_skills and self.selected_skill_id not in {skill_id for skill_id, _ in visible_skills}:
            self.selected_skill_id = visible_skills[0][0]
        elif self.selected_skill_id not in {skill_id for skill_id, _ in all_skills}:
            self.selected_skill_id = all_skills[0][0]

        self._normalize_selected_level_tab(self._get_skill_data(skills_data, self.selected_skill_id))
        self.skill_slot_rects = []
        self.active_slot_rects = []
        self.skill_kind_tab_rects = []
        self.level_tab_rects = []
        self._draw_summary(screen, player)
        total_pages = self._get_total_skill_pages(visible_skills)
        self.skill_pages[self.skill_kind_tab] = max(0, min(self._get_current_skill_page(), total_pages - 1))
        self._draw_skill_library_panel(screen, self.library_rect, visible_skills)
        self._draw_active_slots_panel(screen, self.active_slots_rect)
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
        top = panel.y + 82
        detail_height = min(190, max(175, int(panel.h * 0.36)))
        top_panel_bottom = panel.bottom - detail_height - 18
        top_panel_height = max(170, top_panel_bottom - top)
        gap = 14
        content_width = panel.w - 36
        active_width = max(190, int(content_width * 0.29))
        library_width = content_width - active_width - gap
        self.library_rect = pygame.Rect(panel.x + 18, top, library_width, top_panel_height)
        self.active_slots_rect = pygame.Rect(self.library_rect.right + gap, top, active_width, top_panel_height)
        self.detail_rect = pygame.Rect(panel.x + 18, top_panel_bottom + 12, panel.w - 36, detail_height - 4)
        button_y = self.detail_rect.bottom - 34
        self.learn_button_rect = pygame.Rect(self.detail_rect.right - 402, button_y, 124, 26)
        self.enhance_button_rect = pygame.Rect(self.detail_rect.right - 268, button_y, 118, 26)
        self.equip_button_rect = pygame.Rect(self.detail_rect.right - 140, button_y, 122, 26)

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

    def _draw_summary(self, screen, player):
        used_slots = len(player.get("equipped_skills", [])) if isinstance(player.get("equipped_skills", []), list) else 0
        slot_count = get_skill_slot_count(player)
        parts = [
            ("Skill points: ", TEXT_SECONDARY),
            (str(player.get("skill_points", 0)), WARNING),
            ("   Enhanced points: ", TEXT_SECONDARY),
            (str(player.get("enhanced_skill_points", 0)), WARNING),
            ("   Active slots: ", TEXT_SECONDARY),
            (f"{used_slots} / {slot_count}", TEXT_PRIMARY),
        ]
        x = self.panel_rect.x + 24
        y = self.panel_rect.y + 58
        for text, color in parts:
            surface = self.body_font.render(text, True, color)
            screen.blit(surface, (x, y))
            x += surface.get_width()
        if self.status_message:
            message = self.small_font.render(self._truncate_text(self.status_message, self.small_font, self.panel_rect.w - 48), True, WARNING)
            screen.blit(message, (self.panel_rect.x + 24, self.panel_rect.y + 80))

    def _draw_skill_library_panel(self, screen, rect, skills):
        pygame.draw.rect(screen, PANEL_BG_SECONDARY, rect, border_radius=6)
        pygame.draw.rect(screen, BORDER_NORMAL, rect, 2, border_radius=6)
        self._draw_skill_kind_tabs(screen, pygame.Rect(rect.x + 12, rect.y + 10, rect.w - 24, 26))

        if not skills:
            label = "No active skills available." if self.skill_kind_tab == "active" else "No passive skills available."
            empty = self.body_font.render(label, True, TEXT_MUTED)
            screen.blit(empty, (rect.x + 14, rect.y + 48))
            return

        total_pages = self._get_total_skill_pages(skills)
        self._draw_skill_grid(screen, rect, skills)
        self._draw_pagination(screen, rect, total_pages)

    def _draw_skill_kind_tabs(self, screen, area):
        self.skill_kind_tab_rects = []
        x = area.x
        for kind_id, label in (("active", "Active"), ("passive", "Passive")):
            width = max(72, self.small_font.size(label)[0] + 22)
            rect = pygame.Rect(x, area.y, width, area.h)
            self.skill_kind_tab_rects.append((kind_id, rect))
            self._draw_button(screen, rect, label, active=kind_id == self.skill_kind_tab, enabled=True)
            x += width + 8

    def _draw_skill_grid(self, screen, rect, skills):
        columns = 4
        rows = 3
        spacing = 7
        grid_top = rect.y + 38
        pagination_height = 26
        available_width = rect.w - 36
        available_height = rect.bottom - grid_top - pagination_height - 6
        slot_size = min(
            66,
            max(
                50,
                min(
                    (available_width - spacing * (columns - 1)) // columns,
                    (available_height - spacing * (rows - 1)) // rows,
                ),
            ),
        )
        total_grid_width = columns * slot_size + (columns - 1) * spacing
        total_grid_height = rows * slot_size + (rows - 1) * spacing
        start_x = rect.x + (rect.w - total_grid_width) // 2
        start_y = grid_top + max(0, (available_height - total_grid_height) // 2)
        page_skills = self._get_current_page_skills(skills)

        for index, (skill_id, skill_data) in enumerate(page_skills):
            column = index % columns
            row = index // columns
            slot_rect = pygame.Rect(
                start_x + column * (slot_size + spacing),
                start_y + row * (slot_size + spacing),
                slot_size,
                slot_size,
            )
            self.skill_slot_rects.append((skill_id, slot_rect))
            self._draw_skill_slot(screen, slot_rect, skill_id, skill_data, skill_id == self.selected_skill_id)

    def _draw_active_slots_panel(self, screen, rect):
        pygame.draw.rect(screen, PANEL_BG_SECONDARY, rect, border_radius=6)
        pygame.draw.rect(screen, BORDER_NORMAL, rect, 2, border_radius=6)

        player = getattr(self.game, "player", {}) or {}
        if not isinstance(player, dict):
            text = self.small_font.render("No active slots.", True, TEXT_MUTED)
            screen.blit(text, (rect.x + 12, rect.y + 14))
            return

        slot_count = max(0, get_skill_slot_count(player))
        if slot_count <= 0:
            text = self.small_font.render("No active slots.", True, TEXT_MUTED)
            screen.blit(text, (rect.x + 12, rect.y + 14))
            return

        equipped_skills = self._get_equipped_skill_ids()
        y = rect.y + 10
        row_height = 38
        visible_slots = max(1, (rect.bottom - y - 12) // row_height)
        slots_to_draw = min(slot_count, visible_slots)
        for index in range(slots_to_draw):
            skill_id = equipped_skills[index] if index < len(equipped_skills) else None
            slot_rect = pygame.Rect(rect.x + 10, y + index * row_height, rect.w - 20, row_height - 8)
            self.active_slot_rects.append((skill_id, slot_rect))
            self._draw_active_slot(screen, slot_rect, skill_id, skill_id == self.selected_skill_id)

        if slot_count > slots_to_draw:
            more = self.small_font.render(f"+{slot_count - slots_to_draw} more", True, TEXT_MUTED)
            screen.blit(more, (rect.x + 12, rect.bottom - 24))

    def _draw_active_slot(self, screen, rect, skill_id, selected=False):
        has_skill = bool(skill_id)
        bg = CARD_BG_SELECTED if has_skill else CARD_BG
        border = BORDER_SELECTED if selected else SUCCESS if has_skill else BORDER_NORMAL
        pygame.draw.rect(screen, bg, rect, border_radius=6)
        pygame.draw.rect(screen, border, rect, 2 if selected else 1, border_radius=6)

        icon_rect = pygame.Rect(rect.x + 8, rect.y + 5, 28, 28)
        if has_skill:
            skill_data = self._get_skill_data(self._get_skills_data(), skill_id)
            self._draw_skill_icon(screen, icon_rect, skill_id, skill_data, self._get_skill_state(skill_id))
            name = self._get_skill_name(skill_id)
            color = TEXT_PRIMARY
            pygame.draw.circle(screen, SUCCESS, (rect.right - 12, rect.centery), 5)
        else:
            pygame.draw.rect(screen, DISABLED_BG, icon_rect, border_radius=4)
            pygame.draw.rect(screen, BORDER_NORMAL, icon_rect, 1, border_radius=4)
            name = "Empty"
            color = TEXT_MUTED

        label = self.small_font.render(self._truncate_text(name, self.small_font, rect.w - 58), True, color)
        screen.blit(label, (rect.x + 44, rect.y + 12))

    def _draw_skill_slot(self, screen, rect, skill_id, skill_data, selected):
        skill_state = self._get_skill_state(skill_id)
        level = skill_state["level"]
        skill_type = get_skill_type(self._get_skills_data(), skill_id)
        equipped = level > 0 and skill_type == "active" and is_skill_equipped(getattr(self.game, "player", {}) or {}, skill_id)
        can_upgrade = level < 4 and (getattr(self.game, "player", {}) or {}).get("skill_points", 0) > 0

        if selected:
            bg, border = CARD_BG_SELECTED, BORDER_SELECTED
        elif level <= 0:
            bg, border = DISABLED_BG, BORDER_NORMAL
        elif equipped:
            bg, border = CARD_BG_SELECTED, SUCCESS
        elif can_upgrade:
            bg, border = CARD_BG_SELECTED, WARNING
        else:
            bg, border = CARD_BG, BORDER_NORMAL

        pygame.draw.rect(screen, bg, rect, border_radius=8)
        pygame.draw.rect(screen, border, rect, 3 if selected else 2, border_radius=8)
        icon_size = min(52, max(42, rect.w - 26))
        icon_rect = pygame.Rect(0, 0, icon_size, icon_size)
        icon_rect.center = (rect.centerx, rect.centery - 4)
        self._draw_skill_icon(screen, icon_rect, skill_id, skill_data, skill_state)
        self._draw_skill_badges(screen, rect, skill_id, skill_data, skill_state)

    def _draw_skill_icon(self, screen, rect, skill_id, skill_data, skill_state):
        visibility = self._get_skill_visibility(skill_id, skill_data, skill_state)
        if visibility == "secret":
            pygame.draw.rect(screen, PANEL_BG, rect, border_radius=5)
            return
        if visibility == "undiscovered":
            text = self.header_font.render("?", True, TEXT_MUTED)
            screen.blit(text, text.get_rect(center=rect.center))
            return

        icon = self._get_skill_icon_surface(skill_id)
        if icon is not None:
            size = min(rect.w, rect.h)
            icon = pygame.transform.scale(icon, (size, size))
            screen.blit(icon, icon.get_rect(center=rect.center))
        else:
            self._draw_fallback_skill_icon(screen, rect, get_skill_type(self._get_skills_data(), skill_id))

        if visibility == "known_locked":
            veil = pygame.Surface(rect.size, pygame.SRCALPHA)
            veil.fill((0, 0, 0, 115))
            screen.blit(veil, rect.topleft)

    def _draw_fallback_skill_icon(self, screen, rect, skill_type):
        center = rect.center
        if skill_type == "passive":
            points = [
                (center[0], rect.y + 2),
                (center[0] + 5, center[1] - 4),
                (rect.right - 3, center[1]),
                (center[0] + 5, center[1] + 4),
                (center[0], rect.bottom - 2),
                (center[0] - 5, center[1] + 4),
                (rect.x + 3, center[1]),
                (center[0] - 5, center[1] - 4),
            ]
            pygame.draw.polygon(screen, SUCCESS, points)
            pygame.draw.circle(screen, TEXT_PRIMARY, center, max(3, rect.w // 8))
            return
        if skill_type == "active":
            pygame.draw.line(screen, TEXT_PRIMARY, (rect.x + 7, rect.bottom - 6), (rect.right - 5, rect.y + 5), 4)
            pygame.draw.polygon(screen, WARNING, [(rect.right - 5, rect.y + 5), (rect.right - 14, rect.y + 7), (rect.right - 7, rect.y + 16)])
            pygame.draw.line(screen, (95, 70, 46), (rect.x + 6, rect.bottom - 5), (rect.x + 14, rect.bottom - 13), 4)
            return
        text = self.header_font.render("?", True, TEXT_PRIMARY)
        screen.blit(text, text.get_rect(center=center))

    def _draw_skill_badges(self, screen, rect, skill_id, skill_data, skill_state):
        player = getattr(self.game, "player", {}) or {}
        level = skill_state["level"]
        skill_type = get_skill_type(self._get_skills_data(), skill_id)
        level_label = "Max" if level >= 4 else f"Lv {level}"
        badge_width = 42 if level < 4 else 38
        badge = pygame.Rect(0, rect.bottom - 20, badge_width, 16)
        badge.centerx = rect.centerx
        pygame.draw.rect(screen, PANEL_BG, badge, border_radius=4)
        pygame.draw.rect(screen, BORDER_NORMAL, badge, 1, border_radius=4)
        text = self.small_font.render(level_label, True, TEXT_PRIMARY)
        screen.blit(text, text.get_rect(center=badge.center))

        if level > 0 and skill_type == "active" and is_skill_equipped(player, skill_id):
            pygame.draw.circle(screen, SUCCESS, (rect.right - 12, rect.y + 12), 6)
            marker = self.small_font.render("E", True, (18, 32, 24))
            screen.blit(marker, marker.get_rect(center=(rect.right - 12, rect.y + 12)))

        if level < 4 and player.get("skill_points", 0) > 0:
            plus = pygame.Rect(rect.right - 21, rect.bottom - 21, 17, 17)
            pygame.draw.rect(screen, (116, 82, 34), plus, border_radius=4)
            pygame.draw.rect(screen, WARNING, plus, 1, border_radius=4)
            text = self.small_font.render("+", True, TEXT_PRIMARY)
            screen.blit(text, text.get_rect(center=plus.center))

        if skill_state.get("enhanced") is True:
            points = [
                (rect.x + 12, rect.y + 4),
                (rect.x + 15, rect.y + 10),
                (rect.x + 21, rect.y + 12),
                (rect.x + 15, rect.y + 15),
                (rect.x + 12, rect.y + 21),
                (rect.x + 9, rect.y + 15),
                (rect.x + 3, rect.y + 12),
                (rect.x + 9, rect.y + 10),
            ]
            pygame.draw.polygon(screen, (204, 146, 222), points)
            pygame.draw.polygon(screen, (238, 205, 140), points, 1)

    def _draw_pagination(self, screen, rect, total_pages):
        y = rect.bottom - 24
        center_x = rect.centerx
        self.prev_page_rect = pygame.Rect(center_x - 94, y, 28, 22)
        self.next_page_rect = pygame.Rect(center_x + 66, y, 28, 22)
        if total_pages > 1:
            self._draw_button(screen, self.prev_page_rect, "<", enabled=self.skill_page > 0)
            self._draw_button(screen, self.next_page_rect, ">", enabled=self.skill_page < total_pages - 1)
        else:
            self.prev_page_rect = pygame.Rect(0, 0, 0, 0)
            self.next_page_rect = pygame.Rect(0, 0, 0, 0)
        page_label = self.small_font.render(f"Page {self.skill_page + 1} / {total_pages}", True, TEXT_SECONDARY)
        screen.blit(page_label, page_label.get_rect(center=(rect.centerx, y + 11)))

    def _draw_skill_details(self, screen, rect, skill_id, skill_data):
        pygame.draw.rect(screen, PANEL_BG_SECONDARY, rect, border_radius=6)
        pygame.draw.rect(screen, BORDER_NORMAL, rect, 2, border_radius=6)
        if not skill_id or not isinstance(skill_data, dict):
            text = self.body_font.render("No skill selected.", True, TEXT_MUTED)
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
        action_top = self.learn_button_rect.y - 24

        title = self.header_font.render(self._truncate_text(name, self.header_font, rect.w - 32), True, TEXT_PRIMARY)
        screen.blit(title, (rect.x + 14, rect.y + 10))
        meta = (
            f"{skill_type.title()} | Current level: {level} / 4 | "
            f"Selected tab: {self._get_level_tab_label(self.selected_level_tab)} | "
            f"View: {self._get_level_view_label(skill_state)}"
        )
        meta_surface = self.body_font.render(self._truncate_text(meta, self.body_font, rect.w - 32), True, TEXT_SECONDARY)
        screen.blit(meta_surface, (rect.x + 14, rect.y + 38))

        tab_bottom = self._draw_level_tabs(screen, skill_data, skill_state, pygame.Rect(rect.x + 14, rect.y + 64, rect.w - 28, 26))
        description_lines = self._wrap_text(skill_data.get("description", "No description."), self.small_font, rect.w - 348, 2)
        y = tab_bottom + 8
        for line in description_lines:
            screen.blit(self.small_font.render(line, True, TEXT_SECONDARY), (rect.x + 14, y))
            y += 16

        effects_rect = pygame.Rect(rect.x + 14, y + 1, rect.w - 32, max(20, action_top - y - 4))
        self._draw_skill_effects(screen, effects_rect, effect_lines)

        if self.status_message:
            message = self.small_font.render(
                self._truncate_text(self.status_message, self.small_font, rect.w - 430),
                True,
                WARNING,
            )
            screen.blit(message, (rect.x + 14, self.learn_button_rect.y + 5))

        action_label, action_enabled = self._get_learn_action(player, level)
        self._draw_button(screen, self.learn_button_rect, action_label, enabled=action_enabled, warm=action_enabled)
        enhance_label, enhance_enabled = self._get_enhance_action(player, skill_data, skill_state)
        self._draw_button(screen, self.enhance_button_rect, enhance_label, enabled=enhance_enabled, warm=enhance_enabled)

        if skill_type == "active" and level > 0:
            equipped = is_skill_equipped(player, skill_id)
            self._draw_button(screen, self.equip_button_rect, "Unequip" if equipped else "Equip", active=equipped, enabled=True)
        else:
            self._draw_button(screen, self.equip_button_rect, "Passive" if level > 0 else "Equip", enabled=False)

    def _draw_skill_effects(self, screen, rect, effect_lines):
        if not effect_lines:
            effect_lines = [("No level data.", (160, 168, 176))]
        y = rect.y
        line_height = 16
        max_lines = max(1, rect.h // line_height)
        for line, color in effect_lines[:max_lines]:
            text = self.small_font.render(self._truncate_text(line, self.small_font, rect.w), True, color)
            screen.blit(text, (rect.x, y))
            y += line_height

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
                bg = CARD_BG_SELECTED if active else CARD_BG
                border = BORDER_SELECTED if active else BORDER_NORMAL
                color = TEXT_PRIMARY
            elif enabled:
                bg = CARD_BG_SELECTED if active else CARD_BG
                border = BORDER_SELECTED if active else BORDER_NORMAL
                color = TEXT_PRIMARY
            else:
                bg, border, color = DISABLED_BG, DISABLED_TEXT, DISABLED_TEXT
            pygame.draw.rect(screen, bg, rect, border_radius=5)
            pygame.draw.rect(screen, border, rect, 2 if active else 1, border_radius=5)
            text = self.small_font.render(self._truncate_text(label, self.small_font, rect.w - 6), True, color)
            screen.blit(text, text.get_rect(center=rect.center))
            x += width + 6
        return area.bottom

    def _draw_button(self, screen, rect, label, active=False, enabled=True, warm=False):
        font = self.small_font if rect.h <= 26 else self.body_font
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

    def _get_skills_data(self):
        skills_data = getattr(getattr(self.game, "data", None), "skills", {})
        if not isinstance(skills_data, dict):
            return {}
        return {skill_id: skill_data for skill_id, skill_data in skills_data.items() if isinstance(skill_data, dict)}

    def _get_available_skills(self):
        player = getattr(self.game, "player", None)
        skills_data = self._get_skills_data()
        if not isinstance(player, dict) or not skills_data:
            return []
        skills = get_available_class_skills(skills_data, player)
        return sorted(
            [(skill_id, skill_data) for skill_id, skill_data in skills if isinstance(skill_data, dict)],
            key=lambda item: (
                0 if get_skill_type(skills_data, item[0]) == "active" else 1,
                item[1].get("name", item[0]),
                item[0],
            ),
        )

    def _get_visible_skills(self):
        skills_data = self._get_skills_data()
        return [
            (skill_id, skill_data)
            for skill_id, skill_data in self._get_available_skills()
            if get_skill_type(skills_data, skill_id) == self.skill_kind_tab
        ]

    def _set_skill_kind_tab(self, kind_id):
        if kind_id not in {"active", "passive"} or kind_id == self.skill_kind_tab:
            return
        self.skill_kind_tab = kind_id
        self.skill_pages[kind_id] = max(0, self.skill_pages.get(kind_id, 0))
        visible_skills = self._get_visible_skills()
        self.skill_pages[kind_id] = max(0, min(self.skill_pages[kind_id], self._get_total_skill_pages(visible_skills) - 1))
        if visible_skills and self.selected_skill_id not in {skill_id for skill_id, _ in visible_skills}:
            self.selected_skill_id = visible_skills[0][0]
            self._normalize_selected_level_tab(self._get_skill_data(self._get_skills_data(), self.selected_skill_id))

    def _get_current_skill_page(self):
        return self.skill_pages.get(self.skill_kind_tab, 0)

    def _get_skill_state(self, skill_id):
        player = getattr(self.game, "player", {}) or {}
        if not isinstance(player, dict):
            return {"level": 0, "enhanced": False}
        return get_player_skill_state(player, skill_id)

    def _get_equipped_skill_ids(self):
        player = getattr(self.game, "player", {}) or {}
        equipped_skills = player.get("equipped_skills", []) if isinstance(player, dict) else []
        return [skill_id for skill_id in equipped_skills if skill_id] if isinstance(equipped_skills, list) else []

    def _get_skill_name(self, skill_id):
        skill_data = self._get_skill_data(self._get_skills_data(), skill_id)
        if isinstance(skill_data, dict) and skill_data.get("name"):
            return skill_data["name"]
        return str(skill_id or "Unknown")

    def _get_skill_visibility(self, skill_id, skill_data, skill_state):
        if skill_state.get("level", 0) <= 0:
            return "known_locked"
        return "learned"

    def _get_total_skill_pages(self, skills):
        skills_per_page = 12
        return max(1, (len(skills) + skills_per_page - 1) // skills_per_page)

    def _get_current_page_skills(self, skills):
        skills_per_page = 12
        total_pages = self._get_total_skill_pages(skills)
        current_page = max(0, min(self._get_current_skill_page(), total_pages - 1))
        self.skill_pages[self.skill_kind_tab] = current_page
        self.skill_page = current_page
        start = current_page * skills_per_page
        return skills[start:start + skills_per_page]

    def _select_first_page_skill_if_needed(self, skills):
        if self.selected_skill_id in {skill_id for skill_id, _ in skills}:
            return
        page_skills = self._get_current_page_skills(skills)
        self.selected_skill_id = page_skills[0][0] if page_skills else None
        if self.selected_skill_id:
            self._normalize_selected_level_tab(self._get_skill_data(self._get_skills_data(), self.selected_skill_id))

    def _load_skill_icon_map(self):
        path = Path("data/skill_icons.json")
        if not path.exists():
            return {}
        try:
            with path.open("r", encoding="utf-8") as handle:
                data = json.load(handle)
        except (OSError, json.JSONDecodeError):
            return {}
        if not isinstance(data, dict):
            return {}
        return {str(skill_id): str(icon_path) for skill_id, icon_path in data.items() if isinstance(icon_path, str)}

    def _get_skill_icon_surface(self, skill_id):
        if skill_id in self.skill_icon_surfaces:
            return self.skill_icon_surfaces[skill_id]
        icon_path = self.skill_icon_map.get(skill_id)
        if not icon_path:
            self.skill_icon_surfaces[skill_id] = None
            return None
        try:
            surface = pygame.image.load(icon_path).convert_alpha()
        except (OSError, pygame.error, TypeError, ValueError):
            surface = None
        self.skill_icon_surfaces[skill_id] = surface
        return surface

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

    def _get_enhance_action(self, player, skill_data, skill_state):
        if skill_state.get("enhanced") is True:
            return "Enhanced", False
        if not isinstance(skill_data, dict) or not isinstance(skill_data.get("enhanced"), dict):
            return "Enhance", False
        if skill_state.get("level", 0) < 4:
            return "Enhance", False
        enhanced_points = player.get("enhanced_skill_points", 0)
        if not isinstance(enhanced_points, (int, float)) or isinstance(enhanced_points, bool):
            enhanced_points = 0
        return "Enhance", enhanced_points > 0

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
            return "Current enhanced" if enhanced else "Enhanced version"
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
            return f"x{float(value):.2f}"
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

    def _enhance_selected_skill(self):
        player = getattr(self.game, "player", None)
        if not isinstance(player, dict) or not self.selected_skill_id:
            self.status_message = "No skill selected."
            return

        skill_data = self._get_skill_data(self._get_skills_data(), self.selected_skill_id)
        skill_state = get_player_skill_state(player, self.selected_skill_id)
        if skill_state.get("enhanced") is True:
            self.status_message = "Skill already enhanced."
            return
        if not isinstance(skill_data.get("enhanced"), dict):
            self.status_message = "Cannot enhance skill."
            return
        if skill_state.get("level", 0) < 4:
            self.status_message = "Reach level 4 first."
            return
        enhanced_points = player.get("enhanced_skill_points", 0)
        if not isinstance(enhanced_points, (int, float)) or isinstance(enhanced_points, bool):
            enhanced_points = 0
        enhanced_points = max(0, enhanced_points)
        if enhanced_points <= 0:
            self.status_message = "Not enough enhanced points."
            return

        previous_max_hp = player.get("max_hp", 0)
        if enhance_skill(player, self.selected_skill_id):
            player["enhanced_skill_points"] = max(0, enhanced_points - 1)
            self._recalculate_player_stats(previous_max_hp)
            self._save_current_game()
            self.status_message = "Skill enhanced."
            if self._is_level_tab_available(skill_data, "enhanced"):
                self.selected_level_tab = "enhanced"
            return

        self.status_message = "Cannot enhance skill."

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
