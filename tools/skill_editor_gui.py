import copy
import json
import sys
from pathlib import Path

import pygame

try:
    from tools.skill_editor import (
        ALLOWED_STATS,
        CLASSES_PATH,
        DATA_ONLY_TRIGGERS,
        SKILLS_PATH,
        SUPPORTED_NOW_TRIGGERS,
        generate_skill_id,
        get_engine_support_status,
        load_json_file,
        save_json_file,
        validate_skills,
    )
except ModuleNotFoundError:
    sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
    from tools.skill_editor import (
        ALLOWED_STATS,
        CLASSES_PATH,
        DATA_ONLY_TRIGGERS,
        SKILLS_PATH,
        SUPPORTED_NOW_TRIGGERS,
        generate_skill_id,
        get_engine_support_status,
        load_json_file,
        save_json_file,
        validate_skills,
    )


WINDOW_SIZE = (1400, 850)
LEVEL_KEYS = ("1", "2", "3", "4")
LEFT_PANEL_X = 10
LEFT_PANEL_Y = 10
FILTER_ROW_HEIGHT = 34
BUTTON_ROW_Y = 166
SKILL_LIST_START_Y = 212
BACKGROUND = (25, 28, 34)
PANEL = (34, 38, 46)
PANEL_ALT = (42, 47, 56)
BORDER = (74, 81, 95)
TEXT = (232, 236, 242)
MUTED = (157, 166, 181)
ACCENT = (86, 156, 214)
WARNING = (232, 181, 82)
ERROR = (232, 96, 96)
OK = (104, 196, 128)
INPUT_BG = (24, 27, 33)

ENGINE_STATUS_LABELS = {
    "supported_now": "usable now",
    "data_only": "data only",
    "invalid": "invalid",
}

TEMPLATE_HELP = {
    "Execute": {
        "title": "Execute",
        "role": "finishing move when enemy HP is low.",
        "engine_status": "usable now",
        "best_for": "warrior, archer, aggressive classes.",
        "generated_fields": "damage_multiplier, enemy_hp_threshold, cooldown.",
        "tuning_tips": "increase threshold to trigger more often, increase cooldown to reduce power.",
        "warning": "high threshold values can make the skill trigger too often.",
    },
    "Revenge": {
        "title": "Revenge",
        "role": "stronger attack after taking damage.",
        "engine_status": "usable now",
        "best_for": "warrior, tank, defensive builds.",
        "generated_fields": "damage_multiplier, cooldown.",
        "tuning_tips": "lower cooldown makes it more reliable, higher damage multiplier makes it burstier.",
        "warning": "this is best for characters that survive several turns.",
    },
    "Damage Boost": {
        "title": "Damage Boost",
        "role": "generic damage boost before attacking.",
        "engine_status": "data only",
        "best_for": "mage, archer, future offensive builds.",
        "generated_fields": "damage_multiplier, cooldown.",
        "tuning_tips": "keep multipliers modest until the generic skill engine exists.",
        "warning": "this template is saved in data but is not interpreted yet by the current combat engine.",
    },
    "Stat Passive": {
        "title": "Stat Passive",
        "role": "passive stat growth by character level.",
        "engine_status": "usable now",
        "best_for": "class identity and long-term progression.",
        "generated_fields": "stat_modifiers_per_character_level.",
        "tuning_tips": "per-level values scale strongly over time.",
        "warning": "high per-level bonuses can break progression quickly.",
    },
    "Crit Passive": {
        "title": "Crit Passive",
        "role": "improve critical chance and critical damage.",
        "engine_status": "usable now",
        "best_for": "archer, rogue-like builds, high dexterity characters.",
        "generated_fields": "stat_modifiers with crit_chance and crit_damage.",
        "tuning_tips": "crit_chance should stay low because it compounds with crit_damage.",
        "warning": "crit scaling can become unstable if both values grow too fast.",
    },
    "Gathering Passive": {
        "title": "Gathering Passive",
        "role": "improve profession mastery and profession XP gain.",
        "engine_status": "usable now if these stats are used by gathering systems.",
        "best_for": "profession-focused builds.",
        "generated_fields": "profession mastery stat and profession xp bonus stat.",
        "tuning_tips": "keep bonuses small because gathering repeats often.",
        "warning": "this affects resource economy and crafting speed.",
    },
}


def draw_text(surface, font, text, x, y, color=TEXT):
    rendered = font.render(str(text), True, color)
    surface.blit(rendered, (x, y))
    return rendered.get_rect(topleft=(x, y))


def draw_wrapped_text(surface, font, text, rect, color=TEXT, line_height=20):
    lines = wrap_text(text, font, rect.width)

    y = rect.y
    for line in lines:
        if y + line_height > rect.bottom:
            break
        draw_text(surface, font, line, rect.x, y, color)
        y += line_height


def wrap_text(text, font, max_width):
    words = str(text).split()
    lines = []
    current = ""
    for word in words:
        candidate = f"{current} {word}".strip()
        if font.size(candidate)[0] <= max_width:
            current = candidate
        else:
            if current:
                lines.append(current)
            current = word
    if current:
        lines.append(current)
    return lines


def parse_float(value):
    value = str(value).strip()
    if not value:
        return None
    try:
        return float(value)
    except ValueError:
        return None


def parse_int(value):
    value = str(value).strip()
    if not value:
        return None
    try:
        if "." in value:
            return None
        return int(value)
    except ValueError:
        return None


def generate_unique_skill_id(skills, class_id, name):
    base_id = generate_skill_id(class_id, name)
    if base_id not in skills:
        return base_id
    suffix = 2
    while f"{base_id}_{suffix}" in skills:
        suffix += 1
    return f"{base_id}_{suffix}"


def format_json_preview(skill):
    try:
        return json.dumps(skill, indent=2, ensure_ascii=False)
    except TypeError:
        return "<invalid skill data>"


class TextInput:
    def __init__(self, rect, text="", numeric=False):
        self.rect = pygame.Rect(rect)
        self.text = str(text)
        self.numeric = numeric
        self.focused = False

    def handle_event(self, event):
        if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
            self.focused = self.rect.collidepoint(event.pos)
            return False
        if event.type != pygame.KEYDOWN or not self.focused:
            return False
        if event.key == pygame.K_RETURN:
            self.focused = False
            return True
        if event.key == pygame.K_BACKSPACE:
            self.text = self.text[:-1]
            return True
        if event.key == pygame.K_TAB:
            return False
        if event.unicode:
            if self.numeric and event.unicode not in "0123456789.-":
                return False
            self.text += event.unicode
            return True
        return False

    def draw(self, surface, font):
        color = ACCENT if self.focused else BORDER
        pygame.draw.rect(surface, INPUT_BG, self.rect, border_radius=4)
        pygame.draw.rect(surface, color, self.rect, 1, border_radius=4)
        clipped = self.text
        while font.size(clipped)[0] > self.rect.width - 12 and clipped:
            clipped = clipped[1:]
        draw_text(surface, font, clipped, self.rect.x + 6, self.rect.y + 6)


class Button:
    def __init__(self, rect, label, action=None):
        self.rect = pygame.Rect(rect)
        self.label = label
        self.action = action

    def is_clicked(self, event):
        return event.type == pygame.MOUSEBUTTONDOWN and event.button == 1 and self.rect.collidepoint(event.pos)

    def draw(self, surface, font, active=False):
        bg = ACCENT if active else PANEL_ALT
        pygame.draw.rect(surface, bg, self.rect, border_radius=5)
        pygame.draw.rect(surface, BORDER, self.rect, 1, border_radius=5)
        text_rect = font.render(self.label, True, TEXT).get_rect(center=self.rect.center)
        surface.blit(font.render(self.label, True, TEXT), text_rect)


class Dropdown:
    def __init__(self, rect, label, options, value, on_select, max_visible=8, scroll_offset=0):
        self.rect = pygame.Rect(rect)
        self.label = label
        self.options = list(options)
        self.value = value
        self.on_select = on_select
        self.max_visible = max_visible
        self.scroll_offset = max(0, min(scroll_offset, max(0, len(self.options) - self.max_visible)))
        self.option_height = 28

    def draw(self, surface, font, open_menu=False):
        pygame.draw.rect(surface, INPUT_BG, self.rect, border_radius=4)
        pygame.draw.rect(surface, ACCENT if open_menu else BORDER, self.rect, 1, border_radius=4)
        display = str(self.value)
        while font.size(display)[0] > self.rect.width - 24 and display:
            display = display[:-1]
        draw_text(surface, font, display, self.rect.x + 8, self.rect.y + 6)
        draw_text(surface, font, "v", self.rect.right - 16, self.rect.y + 6, MUTED)

    def draw_options(self, surface, font):
        menu_rect = self.get_menu_rect()
        pygame.draw.rect(surface, INPUT_BG, menu_rect, border_radius=4)
        pygame.draw.rect(surface, ACCENT, menu_rect, 1, border_radius=4)
        for index, option in enumerate(self.visible_options()):
            option_rect = pygame.Rect(menu_rect.x, menu_rect.y + index * self.option_height, menu_rect.width, self.option_height)
            if option == self.value:
                pygame.draw.rect(surface, PANEL_ALT, option_rect)
            display = str(option)
            while font.size(display)[0] > option_rect.width - 12 and display:
                display = display[:-1]
            draw_text(surface, font, display, option_rect.x + 6, option_rect.y + 6)
        if len(self.options) > self.max_visible:
            draw_text(surface, font, "scroll", menu_rect.right - 48, menu_rect.bottom - 20, MUTED)

    def visible_options(self):
        end = self.scroll_offset + self.max_visible
        return self.options[self.scroll_offset : end]

    def get_menu_rect(self):
        height = max(1, len(self.visible_options())) * self.option_height
        y = self.rect.bottom + 2
        if y + height > WINDOW_SIZE[1] - 8:
            y = max(8, self.rect.y - height - 2)
        return pygame.Rect(self.rect.x, y, self.rect.width, height)

    def option_at(self, pos):
        menu_rect = self.get_menu_rect()
        if not menu_rect.collidepoint(pos):
            return None
        index = (pos[1] - menu_rect.y) // self.option_height
        options = self.visible_options()
        if 0 <= index < len(options):
            return options[int(index)]
        return None


class SkillEditorGui:
    def __init__(self):
        pygame.init()
        self.screen = pygame.display.set_mode(WINDOW_SIZE)
        pygame.display.set_caption("Skill Editor")
        self.clock = pygame.time.Clock()
        self.font = pygame.font.SysFont("consolas", 15)
        self.small_font = pygame.font.SysFont("consolas", 13)
        self.title_font = pygame.font.SysFont("consolas", 20, bold=True)

        self.skills = {}
        self.classes = {}
        self.selected_id = None
        self.original_skill = None
        self.form = {}
        self.inputs = []
        self.buttons = []
        self.filter_mode = "All"
        self.search_input = TextInput((LEFT_PANEL_X + 14, LEFT_PANEL_Y + 70, 298, 30))
        self.list_scroll = 0
        self.preview_scroll = 0
        self.messages = []
        self.dirty = False
        self.draft = False
        self.reload_confirm = False
        self.quit_confirm = False
        self.running = True
        self.left_buttons = []
        self.center_buttons = []
        self.right_buttons = []
        self.dropdowns = []
        self.open_dropdown_key = None
        self.dropdown_scrolls = {}
        self.selected_template_help = None
        self.class_options = []
        self.trigger_options = []
        self.type_options = ["active", "passive"]
        self.stat_options = sorted(ALLOWED_STATS)

        self.left_rect = pygame.Rect(LEFT_PANEL_X, LEFT_PANEL_Y, 330, 830)
        self.center_rect = pygame.Rect(350, 10, 620, 830)
        self.right_rect = pygame.Rect(980, 10, 410, 830)
        self.load_data()
        self.rebuild_form_inputs()

    def load_data(self):
        try:
            self.skills = load_json_file(SKILLS_PATH)
            self.classes = load_json_file(CLASSES_PATH)
            self.class_options = sorted(self.classes)
            self.trigger_options = sorted(SUPPORTED_NOW_TRIGGERS) + sorted(DATA_ONLY_TRIGGERS)
            self.messages = ["[OK] Data loaded."]
            self.selected_id = None
            self.original_skill = None
            self.form = {}
            self.draft = False
        except Exception as error:
            self.skills = {}
            self.classes = {}
            self.class_options = []
            self.trigger_options = sorted(SUPPORTED_NOW_TRIGGERS) + sorted(DATA_ONLY_TRIGGERS)
            self.messages = [f"[ERROR] {error}"]

    def rebuild_form_inputs(self):
        self.inputs = []
        x = self.center_rect.x + 110
        y = self.center_rect.y + 48
        self.form.setdefault("skill_id", "")
        self.form.setdefault("name", "")
        self.form.setdefault("class", self.class_options[0] if self.class_options else "")
        self.form.setdefault("type", "active")
        self.form.setdefault("trigger", "before_player_attack_when_enemy_low_hp")
        self.form.setdefault("description", "")
        self.form.setdefault("level_values", {level: {} for level in LEVEL_KEYS})
        self.form.setdefault("enhanced_values", {})
        self.form.setdefault("stat", "max_hp")
        self.form.setdefault("per_level_stat", "max_hp")
        self.form.setdefault("extra_level_stat_modifiers", {})
        self.form.setdefault("extra_level_per_stat_modifiers", {})
        self.form.setdefault("extra_enhanced_stat_modifiers", {})
        self.form.setdefault("extra_enhanced_per_stat_modifiers", {})

        self.inputs.append(("skill_id", TextInput((x, y, 360, 30), self.form.get("skill_id", ""))))
        self.inputs.append(("name", TextInput((x, y + 38, 360, 30), self.form.get("name", ""))))
        self.inputs.append(("description", TextInput((x, y + 190, 470, 30), self.form.get("description", ""))))

        grid_y = y + 306
        columns = [
            ("damage_multiplier", 70, 88),
            ("cooldown", 170, 82),
            ("enemy_hp_threshold", 270, 86),
            ("stat_value", 370, 92),
            ("per_level_value", 480, 104),
        ]
        for row, level in enumerate(LEVEL_KEYS):
            level_data = self.form["level_values"].setdefault(level, {})
            row_y = grid_y + 32 + row * 38
            for key, offset, width in columns:
                text = level_data.get(key, "")
                self.inputs.append(
                    (f"level:{level}:{key}", TextInput((self.center_rect.x + offset, row_y, width, 28), text, numeric=True))
                )

        enhanced_y = grid_y + 210
        enhanced_fields = [
            ("damage_multiplier", 22, 98),
            ("cooldown", 128, 70),
            ("enemy_hp_threshold", 206, 98),
            ("stat_value", 312, 90),
            ("per_level_value", 412, 104),
        ]
        for key, offset, width in enhanced_fields:
            text = self.form["enhanced_values"].get(key, "")
            self.inputs.append(
                (f"enhanced:{key}", TextInput((self.center_rect.x + offset, enhanced_y + 34, width, 28), text, numeric=True))
            )

    def sync_inputs_to_form(self):
        for key, input_box in self.inputs:
            if key in {"skill_id", "name", "description"}:
                self.form[key] = input_box.text
            elif key.startswith("level:"):
                _, level, field = key.split(":")
                self.form["level_values"].setdefault(level, {})[field] = input_box.text
            elif key.startswith("enhanced:"):
                _, field = key.split(":")
                self.form["enhanced_values"][field] = input_box.text

    def load_skill_into_form(self, skill_id):
        skill = self.skills.get(skill_id)
        if not isinstance(skill, dict):
            self.messages = [f"[ERROR] Cannot load invalid skill: {skill_id}"]
            return
        self.selected_id = skill_id
        self.original_skill = copy.deepcopy(skill)
        self.draft = False
        self.form = self.form_from_skill(skill_id, skill)
        self.rebuild_form_inputs()
        self.messages = [f"[OK] Loaded {skill_id}."]

    def form_from_skill(self, skill_id, skill):
        level_values = {level: {} for level in LEVEL_KEYS}
        enhanced_values = {}
        stat = "max_hp"
        per_level_stat = "max_hp"
        extra_level_stat_modifiers = {}
        extra_level_per_stat_modifiers = {}
        extra_enhanced_stat_modifiers = {}
        extra_enhanced_per_stat_modifiers = {}

        levels = skill.get("levels", {})
        if isinstance(levels, dict):
            for level in LEVEL_KEYS:
                level_data = levels.get(level, {})
                if not isinstance(level_data, dict):
                    continue
                level_values[level]["damage_multiplier"] = stringify_number(level_data.get("damage_multiplier"))
                level_values[level]["cooldown"] = stringify_number(level_data.get("cooldown"))
                level_values[level]["enemy_hp_threshold"] = stringify_number(level_data.get("enemy_hp_threshold"))
                stat, level_values[level]["stat_value"], extra_level_stat_modifiers[level] = split_stat_values(
                    level_data.get("stat_modifiers"), stat
                )
                per_level_stat, level_values[level]["per_level_value"], extra_level_per_stat_modifiers[level] = split_stat_values(
                    level_data.get("stat_modifiers_per_character_level"), per_level_stat
                )

        enhanced = skill.get("enhanced", {})
        if isinstance(enhanced, dict):
            enhanced_values["damage_multiplier"] = stringify_number(enhanced.get("damage_multiplier"))
            enhanced_values["cooldown"] = stringify_number(enhanced.get("cooldown"))
            enhanced_values["enemy_hp_threshold"] = stringify_number(enhanced.get("enemy_hp_threshold"))
            stat, enhanced_values["stat_value"], extra_enhanced_stat_modifiers = split_stat_values(
                enhanced.get("stat_modifiers"), stat
            )
            per_level_stat, enhanced_values["per_level_value"], extra_enhanced_per_stat_modifiers = split_stat_values(
                enhanced.get("stat_modifiers_per_character_level"), per_level_stat
            )

        return {
            "skill_id": skill_id,
            "name": str(skill.get("name", "")),
            "class": str(skill.get("class", self.class_options[0] if self.class_options else "")),
            "type": str(skill.get("type", "active")),
            "trigger": str(skill.get("trigger", "before_player_attack_when_enemy_low_hp")),
            "description": str(skill.get("description", "")),
            "level_values": level_values,
            "enhanced_values": enhanced_values,
            "stat": stat,
            "per_level_stat": per_level_stat,
            "extra_level_stat_modifiers": extra_level_stat_modifiers,
            "extra_level_per_stat_modifiers": extra_level_per_stat_modifiers,
            "extra_enhanced_stat_modifiers": extra_enhanced_stat_modifiers,
            "extra_enhanced_per_stat_modifiers": extra_enhanced_per_stat_modifiers,
        }

    def build_skill_from_form(self):
        self.sync_inputs_to_form()
        skill_type = self.form.get("type", "active")
        skill = {
            "name": self.form.get("name", "").strip(),
            "class": self.form.get("class", ""),
            "type": skill_type,
            "trigger": self.form.get("trigger", ""),
            "description": self.form.get("description", "").strip(),
            "levels": {level: {} for level in LEVEL_KEYS},
            "enhanced": {},
        }

        for level in LEVEL_KEYS:
            values = self.form.get("level_values", {}).get(level, {})
            level_data = skill["levels"][level]
            damage = parse_float(values.get("damage_multiplier", ""))
            cooldown = parse_int(values.get("cooldown", ""))
            threshold = parse_float(values.get("enemy_hp_threshold", ""))
            stat_value = parse_float(values.get("stat_value", ""))
            per_level_value = parse_float(values.get("per_level_value", ""))

            if damage is not None:
                level_data["damage_multiplier"] = damage
            if cooldown is not None and cooldown > 0:
                level_data["cooldown"] = cooldown
            if threshold is not None:
                level_data["enemy_hp_threshold"] = threshold
            if skill_type == "passive" and self.form.get("stat") and stat_value is not None:
                level_data["stat_modifiers"] = {self.form["stat"]: stat_value}
            if skill_type == "passive":
                extra_stats = self.form.get("extra_level_stat_modifiers", {}).get(level, {})
                if extra_stats:
                    level_data.setdefault("stat_modifiers", {}).update(extra_stats)
            if skill_type == "passive" and self.form.get("per_level_stat") and per_level_value is not None:
                level_data["stat_modifiers_per_character_level"] = {self.form["per_level_stat"]: per_level_value}
            if skill_type == "passive":
                extra_per_stats = self.form.get("extra_level_per_stat_modifiers", {}).get(level, {})
                if extra_per_stats:
                    level_data.setdefault("stat_modifiers_per_character_level", {}).update(extra_per_stats)

        enhanced_values = self.form.get("enhanced_values", {})
        damage = parse_float(enhanced_values.get("damage_multiplier", ""))
        cooldown = parse_int(enhanced_values.get("cooldown", ""))
        threshold = parse_float(enhanced_values.get("enemy_hp_threshold", ""))
        stat_value = parse_float(enhanced_values.get("stat_value", ""))
        per_level_value = parse_float(enhanced_values.get("per_level_value", ""))

        if damage is not None:
            skill["enhanced"]["damage_multiplier"] = damage
        if cooldown is not None and cooldown > 0:
            skill["enhanced"]["cooldown"] = cooldown
        if threshold is not None:
            skill["enhanced"]["enemy_hp_threshold"] = threshold
        if skill_type == "passive" and self.form.get("stat") and stat_value is not None:
            skill["enhanced"]["stat_modifiers"] = {self.form["stat"]: stat_value}
        if skill_type == "passive" and self.form.get("extra_enhanced_stat_modifiers"):
            skill["enhanced"].setdefault("stat_modifiers", {}).update(self.form["extra_enhanced_stat_modifiers"])
        if skill_type == "passive" and self.form.get("per_level_stat") and per_level_value is not None:
            skill["enhanced"]["stat_modifiers_per_character_level"] = {self.form["per_level_stat"]: per_level_value}
        if skill_type == "passive" and self.form.get("extra_enhanced_per_stat_modifiers"):
            skill["enhanced"].setdefault("stat_modifiers_per_character_level", {}).update(
                self.form["extra_enhanced_per_stat_modifiers"]
            )

        return skill

    def make_new_active(self):
        class_id = self.class_options[0] if self.class_options else ""
        self.selected_id = None
        self.original_skill = None
        self.draft = True
        self.form = {
            "skill_id": "",
            "name": "",
            "class": class_id,
            "type": "active",
            "trigger": "before_player_attack_when_enemy_low_hp",
            "description": "",
            "level_values": {
                "1": {"damage_multiplier": "1.10", "cooldown": "3", "enemy_hp_threshold": ""},
                "2": {"damage_multiplier": "1.20", "cooldown": "3", "enemy_hp_threshold": ""},
                "3": {"damage_multiplier": "1.30", "cooldown": "2", "enemy_hp_threshold": ""},
                "4": {"damage_multiplier": "1.40", "cooldown": "2", "enemy_hp_threshold": ""},
            },
            "enhanced_values": {"damage_multiplier": "1.60", "cooldown": "1", "enemy_hp_threshold": ""},
            "stat": "max_hp",
            "per_level_stat": "max_hp",
        }
        self.rebuild_form_inputs()
        self.messages = ["[OK] New active draft created."]

    def make_new_passive(self):
        class_id = self.class_options[0] if self.class_options else ""
        self.selected_id = None
        self.original_skill = None
        self.draft = True
        self.form = {
            "skill_id": "",
            "name": "",
            "class": class_id,
            "type": "passive",
            "trigger": "always",
            "description": "",
            "level_values": {
                "1": {"per_level_value": "1"},
                "2": {"per_level_value": "2"},
                "3": {"per_level_value": "3"},
                "4": {"per_level_value": "4"},
            },
            "enhanced_values": {"per_level_value": "6"},
            "stat": "max_hp",
            "per_level_stat": "max_hp",
        }
        self.rebuild_form_inputs()
        self.messages = ["[OK] New passive draft created."]

    def load_template(self, template_name):
        self.selected_template_help = template_name
        class_id = self.get_template_class()
        builders = {
            "Execute": self.build_execute_template,
            "Revenge": self.build_revenge_template,
            "Damage Boost": self.build_damage_boost_template,
            "Stat Passive": self.build_stat_passive_template,
            "Crit Passive": self.build_crit_passive_template,
            "Gathering Passive": self.build_gathering_passive_template,
        }
        skill = builders[template_name](class_id)
        skill_id = generate_unique_skill_id(self.skills, class_id, skill["name"])
        self.selected_id = skill_id
        self.original_skill = None
        self.draft = True
        self.form = self.form_from_skill(skill_id, skill)
        self.rebuild_form_inputs()
        self.messages = [f"[OK] Template loaded: {template_name}. Adjust values, then click Apply Changes."]
        if template_name == "Damage Boost":
            self.messages.append("[WARNING] This template is data only until the combat engine supports this trigger.")

    def get_template_class(self):
        self.sync_inputs_to_form()
        current_class = self.form.get("class", "")
        if current_class in self.classes:
            return current_class
        return self.class_options[0] if self.class_options else ""

    def build_execute_template(self, class_id):
        return {
            "name": "Finishing Blow",
            "class": class_id,
            "type": "active",
            "trigger": "before_player_attack_when_enemy_low_hp",
            "description": "Deal increased damage when the enemy is low on HP.",
            "levels": {
                "1": {"damage_multiplier": 1.20, "enemy_hp_threshold": 0.20, "cooldown": 3},
                "2": {"damage_multiplier": 1.30, "enemy_hp_threshold": 0.25, "cooldown": 3},
                "3": {"damage_multiplier": 1.40, "enemy_hp_threshold": 0.30, "cooldown": 2},
                "4": {"damage_multiplier": 1.55, "enemy_hp_threshold": 0.35, "cooldown": 2},
            },
            "enhanced": {"damage_multiplier": 1.80, "enemy_hp_threshold": 0.45, "cooldown": 1},
        }

    def build_revenge_template(self, class_id):
        return {
            "name": "Revenge Strike",
            "class": class_id,
            "type": "active",
            "trigger": "before_player_attack_after_damage_taken",
            "description": "Deal increased damage after taking damage.",
            "levels": {
                "1": {"damage_multiplier": 1.20, "cooldown": 4},
                "2": {"damage_multiplier": 1.30, "cooldown": 4},
                "3": {"damage_multiplier": 1.45, "cooldown": 3},
                "4": {"damage_multiplier": 1.60, "cooldown": 3},
            },
            "enhanced": {"damage_multiplier": 1.90, "cooldown": 2},
        }

    def build_damage_boost_template(self, class_id):
        return {
            "name": "Damage Boost",
            "class": class_id,
            "type": "active",
            "trigger": "before_player_attack",
            "description": "Increase damage before attacking.",
            "levels": {
                "1": {"damage_multiplier": 1.10, "cooldown": 3},
                "2": {"damage_multiplier": 1.20, "cooldown": 3},
                "3": {"damage_multiplier": 1.30, "cooldown": 2},
                "4": {"damage_multiplier": 1.40, "cooldown": 2},
            },
            "enhanced": {"damage_multiplier": 1.60, "cooldown": 1},
        }

    def build_stat_passive_template(self, class_id):
        stat = {"warrior": "strength", "archer": "dexterity", "mage": "intelligence"}.get(class_id, "max_hp")
        return self.build_single_per_level_passive(
            class_id,
            "Stat Training",
            "Increase a main stat based on character level.",
            stat,
            [1, 2, 3, 4],
            6,
        )

    def build_crit_passive_template(self, class_id):
        return {
            "name": "Critical Training",
            "class": class_id,
            "type": "passive",
            "trigger": "always",
            "description": "Increase critical chance and critical damage.",
            "levels": {
                "1": {"stat_modifiers": {"crit_chance": 0.02, "crit_damage": 0.10}},
                "2": {"stat_modifiers": {"crit_chance": 0.03, "crit_damage": 0.15}},
                "3": {"stat_modifiers": {"crit_chance": 0.04, "crit_damage": 0.20}},
                "4": {"stat_modifiers": {"crit_chance": 0.05, "crit_damage": 0.30}},
            },
            "enhanced": {"stat_modifiers": {"crit_chance": 0.08, "crit_damage": 0.50}},
        }

    def build_gathering_passive_template(self, class_id):
        mastery_stat, xp_stat = {
            "warrior": ("prospector_mastery", "prospector_xp_bonus"),
            "archer": ("archaeologist_mastery", "archaeologist_xp_bonus"),
            "mage": ("druid_mastery", "druid_xp_bonus"),
        }.get(class_id, ("druid_mastery", "druid_xp_bonus"))
        values = [0.03, 0.05, 0.08, 0.12]
        return {
            "name": "Gathering Focus",
            "class": class_id,
            "type": "passive",
            "trigger": "always",
            "description": "Improve profession mastery and profession experience gain.",
            "levels": {
                level: {"stat_modifiers": {mastery_stat: values[index], xp_stat: values[index]}}
                for index, level in enumerate(LEVEL_KEYS)
            },
            "enhanced": {"stat_modifiers": {mastery_stat: 0.18, xp_stat: 0.18}},
        }

    def build_single_per_level_passive(self, class_id, name, description, stat, values, enhanced_value):
        return {
            "name": name,
            "class": class_id,
            "type": "passive",
            "trigger": "always",
            "description": description,
            "levels": {
                level: {"stat_modifiers_per_character_level": {stat: values[index]}}
                for index, level in enumerate(LEVEL_KEYS)
            },
            "enhanced": {"stat_modifiers_per_character_level": {stat: enhanced_value}},
        }

    def duplicate_selected(self):
        if not self.selected_id or self.selected_id not in self.skills:
            self.messages = ["[ERROR] Select a skill before duplicating."]
            return
        source = copy.deepcopy(self.skills[self.selected_id])
        source["name"] = f"{source.get('name', self.selected_id)} Copy"
        class_id = source.get("class", self.class_options[0] if self.class_options else "")
        new_id = generate_unique_skill_id(self.skills, class_id, source["name"])
        self.selected_id = None
        self.original_skill = None
        self.draft = True
        self.form = self.form_from_skill(new_id, source)
        self.rebuild_form_inputs()
        self.messages = [f"[OK] Draft duplicated from {new_id.replace('_copy', '')}."]

    def generate_id_for_form(self):
        self.sync_inputs_to_form()
        class_id = self.form.get("class", "")
        name = self.form.get("name", "")
        if not class_id or not name:
            self.messages = ["[ERROR] Name and class are required to generate an id."]
            return
        current_id = self.form.get("skill_id", "")
        temporary_skills = dict(self.skills)
        if current_id in temporary_skills and current_id == self.selected_id:
            temporary_skills.pop(current_id, None)
        self.form["skill_id"] = generate_unique_skill_id(temporary_skills, class_id, name)
        self.rebuild_form_inputs()
        self.messages = [f"[OK] Generated id {self.form['skill_id']}."]

    def apply_changes(self):
        skill_id = self.get_form_skill_id()
        if not skill_id:
            self.messages = ["[ERROR] skill_id is required."]
            return
        if skill_id != self.selected_id and skill_id in self.skills:
            self.messages = [f"[ERROR] Skill id already exists: {skill_id}"]
            return
        skill = self.build_skill_from_form()
        previous_id = self.selected_id
        if previous_id and previous_id != skill_id:
            self.skills.pop(previous_id, None)
        self.skills[skill_id] = skill
        self.selected_id = skill_id
        self.original_skill = copy.deepcopy(skill)
        self.draft = False
        self.dirty = True
        self.rebuild_form_inputs()
        self.messages = [f"[OK] Applied changes to {skill_id}. Save to write the file."]

    def revert_current(self):
        if self.draft:
            self.selected_id = None
            self.original_skill = None
            self.form = {}
            self.draft = False
            self.rebuild_form_inputs()
            self.messages = ["[OK] Draft deleted."]
            return
        if not self.selected_id or self.original_skill is None:
            self.messages = ["[ERROR] No selected skill to revert."]
            return
        self.skills[self.selected_id] = copy.deepcopy(self.original_skill)
        self.form = self.form_from_skill(self.selected_id, self.original_skill)
        self.rebuild_form_inputs()
        self.messages = [f"[OK] Reverted {self.selected_id}."]

    def delete_draft(self):
        if self.draft:
            self.selected_id = None
            self.original_skill = None
            self.form = {}
            self.draft = False
            self.rebuild_form_inputs()
            self.messages = ["[OK] Draft deleted."]
        else:
            self.messages = ["[WARNING] Delete Draft only clears unsaved drafts."]

    def validate_current(self):
        skill_id = self.get_form_skill_id() or "<draft>"
        skill = self.build_skill_from_form()
        errors, warnings = validate_skills({skill_id: skill}, self.classes)
        self.messages = format_validation_messages(errors, warnings)

    def validate_all(self):
        errors, warnings = validate_skills(self.skills, self.classes)
        self.messages = format_validation_messages(errors, warnings)

    def save(self):
        errors, warnings = validate_skills(self.skills, self.classes)
        if errors:
            self.messages = format_validation_messages(errors, warnings)
            self.messages.insert(0, "[ERROR] Save refused because errors exist.")
            return
        try:
            save_json_file(SKILLS_PATH, self.skills)
            self.dirty = False
            self.messages = format_validation_messages(errors, warnings)
            self.messages.insert(0, "[OK] Saved data/skills.json.")
        except Exception as error:
            self.messages = [f"[ERROR] Save failed: {error}"]

    def show_engine_help(self):
        self.messages = [
            "[OK] Engine status:",
            "usable now: the current combat engine can use this skill.",
            "data only: saved but not interpreted yet.",
            "invalid: the skill definition has errors.",
        ]

    def reload(self):
        if self.dirty and not self.reload_confirm:
            self.reload_confirm = True
            self.messages = ["[WARNING] Unsaved changes. Click Reload again to confirm."]
            return
        self.reload_confirm = False
        self.dirty = False
        self.load_data()
        self.rebuild_form_inputs()

    def request_quit(self):
        if self.dirty and not self.quit_confirm:
            self.quit_confirm = True
            self.messages = ["[WARNING] Unsaved changes. Click Quit again to confirm."]
            return
        self.running = False

    def get_form_skill_id(self):
        self.sync_inputs_to_form()
        return self.form.get("skill_id", "").strip()

    def select_dropdown_value(self, key, value):
        self.sync_inputs_to_form()
        self.form[key] = value
        if key == "type" and value == "passive":
            self.form["trigger"] = "always"
        self.rebuild_form_inputs()
        self.open_dropdown_key = None

    def filtered_skill_ids(self):
        search = self.search_input.text.strip().lower()
        result = []
        for skill_id in sorted(self.skills):
            skill = self.skills[skill_id]
            if not isinstance(skill, dict):
                status = "invalid"
                skill_type = ""
            else:
                status = get_engine_support_status(skill_id, skill)
                skill_type = skill.get("type", "")
            if self.filter_mode == "Active" and skill_type != "active":
                continue
            if self.filter_mode == "Passive" and skill_type != "passive":
                continue
            if self.filter_mode == "Usable" and status != "supported_now":
                continue
            if self.filter_mode == "Data only" and status != "data_only":
                continue
            if self.filter_mode == "Invalid" and status != "invalid":
                continue
            if search and search not in skill_id.lower() and search not in str(skill.get("name", "")).lower():
                continue
            result.append(skill_id)
        return result

    def handle_event(self, event):
        if event.type == pygame.QUIT:
            self.request_quit()
            return

        if event.type == pygame.MOUSEWHEEL:
            open_dropdown = self.get_open_dropdown()
            if open_dropdown:
                max_scroll = max(0, len(open_dropdown.options) - open_dropdown.max_visible)
                current_scroll = self.dropdown_scrolls.get(self.open_dropdown_key, 0)
                self.dropdown_scrolls[self.open_dropdown_key] = max(0, min(max_scroll, current_scroll - event.y))
                return
            mouse_pos = pygame.mouse.get_pos()
            if self.left_rect.collidepoint(mouse_pos):
                self.list_scroll = max(0, self.list_scroll - event.y * 26)
            elif self.right_rect.collidepoint(mouse_pos):
                self.preview_scroll = max(0, self.preview_scroll - event.y * 26)

        if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
            if self.handle_dropdown_click(event.pos):
                return

        if self.search_input.handle_event(event):
            return

        for _, input_box in self.inputs:
            if input_box.handle_event(event):
                self.reload_confirm = False
                self.quit_confirm = False
                return

        if event.type == pygame.KEYDOWN and event.key == pygame.K_TAB:
            self.focus_next_input()
            return

        if event.type != pygame.MOUSEBUTTONDOWN or event.button != 1:
            return

        self.handle_left_click(event.pos)
        self.handle_center_click(event.pos)
        self.handle_right_click(event.pos)

    def handle_dropdown_click(self, pos):
        open_dropdown = self.get_open_dropdown()
        if open_dropdown:
            option = open_dropdown.option_at(pos)
            if option is not None:
                open_dropdown.on_select(option)
                return True
            if open_dropdown.rect.collidepoint(pos):
                self.open_dropdown_key = None
                return True
            self.open_dropdown_key = None
            return True

        for key, dropdown in self.dropdowns:
            if dropdown.rect.collidepoint(pos):
                self.open_dropdown_key = key
                return True
        return False

    def get_open_dropdown(self):
        for key, dropdown in self.dropdowns:
            if key == self.open_dropdown_key:
                return dropdown
        return None

    def focus_next_input(self):
        all_inputs = [self.search_input] + [input_box for _, input_box in self.inputs]
        focused_index = None
        for index, input_box in enumerate(all_inputs):
            if input_box.focused:
                focused_index = index
                input_box.focused = False
                break
        next_index = 0 if focused_index is None else (focused_index + 1) % len(all_inputs)
        all_inputs[next_index].focused = True

    def handle_left_click(self, pos):
        for button in self.left_buttons:
            if button.is_clicked(pygame.event.Event(pygame.MOUSEBUTTONDOWN, {"pos": pos, "button": 1})):
                button.action()
                return

        list_top = self.left_rect.y + SKILL_LIST_START_Y
        row_height = 58
        ids = self.filtered_skill_ids()
        index = (pos[1] - list_top + self.list_scroll) // row_height
        if self.left_rect.collidepoint(pos) and 0 <= index < len(ids):
            self.load_skill_into_form(ids[int(index)])

    def handle_center_click(self, pos):
        for button in self.center_buttons:
            if button.is_clicked(pygame.event.Event(pygame.MOUSEBUTTONDOWN, {"pos": pos, "button": 1})):
                button.action()
                return

    def handle_right_click(self, pos):
        for button in self.right_buttons:
            if button.is_clicked(pygame.event.Event(pygame.MOUSEBUTTONDOWN, {"pos": pos, "button": 1})):
                button.action()
                return

    def draw(self):
        self.screen.fill(BACKGROUND)
        self.draw_left_panel()
        self.draw_center_panel()
        self.draw_right_panel()
        self.draw_open_dropdown()
        pygame.display.flip()

    def draw_open_dropdown(self):
        dropdown = self.get_open_dropdown()
        if dropdown:
            dropdown.draw_options(self.screen, self.font)

    def draw_panel(self, rect, title):
        pygame.draw.rect(self.screen, PANEL, rect, border_radius=6)
        pygame.draw.rect(self.screen, BORDER, rect, 1, border_radius=6)
        draw_text(self.screen, self.title_font, title, rect.x + 12, rect.y + 12)

    def draw_left_panel(self):
        self.draw_panel(self.left_rect, "Skill list")
        filters = ["All", "Active", "Passive", "Usable", "Data only", "Invalid"]
        self.left_buttons = []
        filter_rows = [filters[:3], filters[3:]]
        for row_index, row_filters in enumerate(filter_rows):
            x = self.left_rect.x + 12
            y = self.left_rect.y + 112 + row_index * FILTER_ROW_HEIGHT
            for label in row_filters:
                width = 92 if label == "Data only" else 88
                button = Button((x, y, width, 28), label, lambda value=label: self.set_filter(value))
                button.draw(self.screen, self.small_font, self.filter_mode == label)
                self.left_buttons.append(button)
                x += width + 8

        draw_text(self.screen, self.small_font, "Search", self.left_rect.x + 14, self.left_rect.y + 52, MUTED)
        self.search_input.draw(self.screen, self.font)

        actions = [
            ("New Passive", self.make_new_passive),
            ("New Active", self.make_new_active),
            ("Duplicate", self.duplicate_selected),
        ]
        x = self.left_rect.x + 12
        for label, action in actions:
            width = 96
            if label == "Duplicate":
                width = 92
            button = Button((x, self.left_rect.y + BUTTON_ROW_Y, width, 30), label, action)
            button.draw(self.screen, self.small_font)
            self.left_buttons.append(button)
            x += width + 8

        list_clip = pygame.Rect(
            self.left_rect.x + 8,
            self.left_rect.y + SKILL_LIST_START_Y,
            self.left_rect.width - 16,
            self.left_rect.bottom - self.left_rect.y - SKILL_LIST_START_Y - 10,
        )
        old_clip = self.screen.get_clip()
        self.screen.set_clip(list_clip)
        y = list_clip.y - self.list_scroll
        for skill_id in self.filtered_skill_ids():
            skill = self.skills.get(skill_id, {})
            row = pygame.Rect(list_clip.x, y, list_clip.width, 52)
            if row.bottom >= list_clip.y and row.y <= list_clip.bottom:
                selected = skill_id == self.selected_id
                pygame.draw.rect(self.screen, PANEL_ALT if selected else INPUT_BG, row, border_radius=4)
                pygame.draw.rect(self.screen, ACCENT if selected else BORDER, row, 1, border_radius=4)
                status = get_engine_support_status(skill_id, skill) if isinstance(skill, dict) else "invalid"
                draw_text(self.screen, self.small_font, skill_id[:34], row.x + 8, row.y + 6)
                engine = engine_status_label(status)
                meta = f"{skill.get('class', '?')} | {skill.get('type', '?')} | {engine}" if isinstance(skill, dict) else "invalid"
                draw_text(self.screen, self.small_font, meta[:38], row.x + 8, row.y + 28, MUTED)
            y += 58
        self.screen.set_clip(old_clip)

    def set_filter(self, value):
        self.filter_mode = value
        self.list_scroll = 0

    def draw_center_panel(self):
        self.draw_panel(self.center_rect, "Skill form")
        self.dropdowns = []
        y = self.center_rect.y + 54
        labels = [
            ("skill_id", y),
            ("name", y + 38),
            ("class", y + 76),
            ("type", y + 114),
            ("trigger", y + 152),
            ("description", y + 190),
        ]
        for label, label_y in labels:
            draw_text(self.screen, self.small_font, label, self.center_rect.x + 20, label_y + 7, MUTED)

        for _, input_box in self.inputs:
            input_box.draw(self.screen, self.font)

        self.center_buttons = []
        self.add_dropdown("class", self.class_options, (self.center_rect.x + 110, y + 76, 190, 30))
        self.add_dropdown("type", self.type_options, (self.center_rect.x + 110, y + 114, 190, 30))
        self.add_dropdown("trigger", self.trigger_options, (self.center_rect.x + 110, y + 152, 360, 30), max_visible=7)
        generate_button = Button((self.center_rect.x + 478, y, 112, 30), "Generate ID", self.generate_id_for_form)
        generate_button.draw(self.screen, self.small_font)
        self.center_buttons.append(generate_button)

        stats_y = y + 238
        draw_text(self.screen, self.small_font, "Flat stat", self.center_rect.x + 20, stats_y + 7, MUTED)
        self.add_dropdown("stat", self.stat_options, (self.center_rect.x + 100, stats_y, 180, 30), max_visible=8)
        draw_text(self.screen, self.small_font, "Per-level stat", self.center_rect.x + 306, stats_y + 7, MUTED)
        self.add_dropdown("per_level_stat", self.stat_options, (self.center_rect.x + 410, stats_y, 180, 30), max_visible=8)

        grid_y = y + 306
        draw_text(self.screen, self.font, "Levels", self.center_rect.x + 20, grid_y - 28)
        headers = ["Level", "Damage", "Cooldown", "Enemy HP", "Flat value", "Per-level value"]
        positions = [20, 70, 170, 270, 370, 480]
        for header, offset in zip(headers, positions):
            draw_text(self.screen, self.small_font, header, self.center_rect.x + offset, grid_y, MUTED)
        for row, level in enumerate(LEVEL_KEYS):
            row_y = grid_y + 38 + row * 38
            draw_text(self.screen, self.font, level, self.center_rect.x + 28, row_y + 4)

        draw_text(self.screen, self.font, "Enhanced", self.center_rect.x + 20, grid_y + 210)
        for label, offset in zip(["Damage", "Cooldown", "Enemy HP", "Flat value", "Per-level value"], [22, 128, 206, 312, 398]):
            draw_text(self.screen, self.small_font, label, self.center_rect.x + offset, grid_y + 238, MUTED)

        self.draw_templates_section(grid_y + 284)

        action_y = self.center_rect.bottom - 52
        actions = [
            ("Apply Changes", self.apply_changes, 124),
            ("Revert", self.revert_current, 78),
            ("Delete Draft", self.delete_draft, 104),
            ("Validate Current", self.validate_current, 138),
        ]
        x = self.center_rect.x + 20
        for label, action, width in actions:
            button = Button((x, action_y, width, 34), label, action)
            button.draw(self.screen, self.small_font)
            self.center_buttons.append(button)
            x += width + 10

    def draw_templates_section(self, y):
        draw_text(self.screen, self.font, "Templates", self.center_rect.x + 20, y)
        help_text = "Templates create editable drafts. Apply Changes adds them to memory; Save writes skills.json."
        draw_text(self.screen, self.small_font, help_text, self.center_rect.x + 118, y + 3, MUTED)
        templates = [
            ("Execute", 82),
            ("Revenge", 86),
            ("Damage Boost", 118),
            ("Stat Passive", 112),
            ("Crit Passive", 108),
            ("Gathering Passive", 150),
        ]
        x = self.center_rect.x + 20
        button_y = y + 28
        for label, width in templates:
            if x + width > self.center_rect.right - 18:
                x = self.center_rect.x + 20
                button_y += 38
            button = Button((x, button_y, width, 30), label, lambda template=label: self.load_template(template))
            button.draw(self.screen, self.small_font)
            self.center_buttons.append(button)
            x += width + 8

    def add_dropdown(self, key, options, rect, max_visible=8):
        value = self.form.get(key, "")
        dropdown_options = options_with_current(options, value)
        dropdown = Dropdown(
            rect,
            key,
            dropdown_options,
            value,
            lambda selected, field=key: self.select_dropdown_value(field, selected),
            max_visible=max_visible,
            scroll_offset=self.dropdown_scrolls.get(key, 0),
        )
        dropdown.draw(self.screen, self.font, self.open_dropdown_key == key)
        self.dropdowns.append((key, dropdown))

    def draw_right_panel(self):
        self.draw_panel(self.right_rect, "Preview / validation")
        self.right_buttons = []
        skill_id = self.get_form_skill_id() or "<none>"
        skill = self.build_skill_from_form() if self.form else {}
        status = get_engine_support_status(skill_id, skill) if self.form else "invalid"
        draw_text(
            self.screen,
            self.font,
            f"Engine: {engine_status_label(status)}",
            self.right_rect.x + 14,
            self.right_rect.y + 44,
            status_color(status),
        )
        dirty_text = "Dirty: yes" if self.dirty else "Dirty: no"
        draw_text(self.screen, self.small_font, dirty_text, self.right_rect.x + 300, self.right_rect.y + 48, WARNING if self.dirty else MUTED)

        help_button = Button((self.right_rect.x + 14, self.right_rect.y + 72, 170, 26), "Help: engine status", self.show_engine_help)
        help_button.draw(self.screen, self.small_font)
        self.right_buttons.append(help_button)

        message_rect = pygame.Rect(self.right_rect.x + 14, self.right_rect.y + 108, self.right_rect.width - 28, 113)
        pygame.draw.rect(self.screen, INPUT_BG, message_rect, border_radius=4)
        pygame.draw.rect(self.screen, BORDER, message_rect, 1, border_radius=4)
        y = message_rect.y + 8
        for message in self.messages[:4]:
            color = ERROR if message.startswith("[ERROR]") else WARNING if message.startswith("[WARNING]") else OK
            draw_wrapped_text(self.screen, self.small_font, message, pygame.Rect(message_rect.x + 8, y, message_rect.width - 16, 24), color, line_height=16)
            y += 26

        self.draw_template_help_panel(pygame.Rect(self.right_rect.x + 14, self.right_rect.y + 236, self.right_rect.width - 28, 160))

        preview_rect = pygame.Rect(self.right_rect.x + 14, self.right_rect.y + 408, self.right_rect.width - 28, 298)
        pygame.draw.rect(self.screen, INPUT_BG, preview_rect, border_radius=4)
        pygame.draw.rect(self.screen, BORDER, preview_rect, 1, border_radius=4)
        lines = format_json_preview(skill).splitlines()
        old_clip = self.screen.get_clip()
        self.screen.set_clip(preview_rect)
        y = preview_rect.y + 8 - self.preview_scroll
        for line in lines:
            if y > preview_rect.bottom:
                break
            if y + 18 >= preview_rect.y:
                draw_text(self.screen, self.small_font, line[:58], preview_rect.x + 8, y, TEXT)
            y += 18
        self.screen.set_clip(old_clip)

        action_y = self.right_rect.bottom - 118
        actions = [
            ("Validate All", self.validate_all),
            ("Save", self.save),
            ("Reload", self.reload),
            ("Quit", self.request_quit),
        ]
        x = self.right_rect.x + 14
        for index, (label, action) in enumerate(actions):
            button = Button((x, action_y + (index // 2) * 44, 180, 34), label, action)
            button.draw(self.screen, self.small_font)
            self.right_buttons.append(button)
            if index % 2 == 0:
                x += 190
            else:
                x = self.right_rect.x + 14

    def draw_template_help_panel(self, rect):
        pygame.draw.rect(self.screen, INPUT_BG, rect, border_radius=4)
        pygame.draw.rect(self.screen, BORDER, rect, 1, border_radius=4)
        draw_text(self.screen, self.font, "Template Help", rect.x + 8, rect.y + 8)

        help_data = get_template_help(self.selected_template_help)
        if not help_data:
            message = "No help available for this template." if self.selected_template_help else (
                "Select a template to see its design role, engine status, generated fields, and tuning tips."
            )
            draw_wrapped_text(self.screen, self.small_font, message, pygame.Rect(rect.x + 8, rect.y + 36, rect.width - 16, rect.height - 44), MUTED, 16)
            return

        title = help_data.get("title", self.selected_template_help or "Template")
        engine = help_data.get("engine_status", "invalid")
        draw_text(self.screen, self.small_font, title, rect.x + 126, rect.y + 10, TEXT)
        draw_text(self.screen, self.small_font, f"Engine: {engine}", rect.x + 226, rect.y + 10, template_engine_color(engine))

        lines = [
            ("Role", help_data.get("role", "")),
            ("Best", help_data.get("best_for", "")),
            ("Fields", help_data.get("generated_fields", "")),
            ("Tips", help_data.get("tuning_tips", "")),
            ("Warning", help_data.get("warning", "")),
        ]
        y = rect.y + 34
        for label, value in lines:
            color = WARNING if label == "Warning" else MUTED
            text = f"{label}: {value}"
            wrapped = wrap_text(text, self.small_font, rect.width - 16)
            for line in wrapped[:2]:
                if y + 16 > rect.bottom - 4:
                    return
                draw_text(self.screen, self.small_font, line, rect.x + 8, y, color)
                y += 16

    def run(self):
        while self.running:
            for event in pygame.event.get():
                self.handle_event(event)
            self.draw()
            self.clock.tick(60)
        pygame.quit()


def stringify_number(value):
    if value is None:
        return ""
    return str(value)


def first_stat_value(value, default_stat):
    if isinstance(value, dict) and value:
        stat = next(iter(value))
        return stat, stringify_number(value.get(stat))
    return default_stat, ""


def split_stat_values(value, default_stat):
    if not isinstance(value, dict) or not value:
        return default_stat, "", {}
    stat = next(iter(value))
    extra_values = {key: amount for key, amount in value.items() if key != stat}
    return stat, stringify_number(value.get(stat)), extra_values


def format_validation_messages(errors, warnings):
    messages = [f"[ERROR] {error}" for error in errors]
    messages.extend(f"[WARNING] {warning}" for warning in warnings)
    if not messages:
        messages.append("[OK] Skills data is valid.")
    elif not errors:
        messages.insert(0, "[OK] Skills data is valid with warnings.")
    return messages


def options_with_current(options, current):
    result = list(options)
    if current and current not in result:
        result.insert(0, current)
    return result


def get_template_help(template_id):
    if not template_id:
        return None
    return TEMPLATE_HELP.get(template_id)


def engine_status_label(status):
    return ENGINE_STATUS_LABELS.get(status, "invalid")


def template_engine_color(engine_status):
    if str(engine_status).startswith("usable now"):
        return OK
    if str(engine_status).startswith("data only"):
        return WARNING
    return ERROR


def status_color(status):
    if status == "supported_now":
        return OK
    if status == "data_only":
        return WARNING
    return ERROR


if __name__ == "__main__":
    SkillEditorGui().run()
