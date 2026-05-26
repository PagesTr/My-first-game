import copy
import json
import re
from pathlib import Path


PROJECT_ROOT = Path(__file__).resolve().parents[1]
SKILLS_PATH = PROJECT_ROOT / "data" / "skills.json"
CLASSES_PATH = PROJECT_ROOT / "data" / "classes.json"
LEVEL_KEYS = {"1", "2", "3", "4"}
SNAKE_CASE_PATTERN = re.compile(r"^[a-z][a-z0-9]*(?:_[a-z0-9]+)*$")

SUPPORTED_NOW_TRIGGERS = {
    "always",
    "before_player_attack_after_damage_taken",
    "before_player_attack_when_enemy_low_hp",
}

DATA_ONLY_TRIGGERS = {
    "before_player_attack",
    "turn_start",
    "turn_end",
    "combat_start",
    "combat_end",
    "after_player_attack",
    "after_damage_taken",
    "on_critical_hit",
    "on_dodge",
    "on_block",
    "on_kill",
}

ALLOWED_STATS = {
    "max_hp",
    "attack",
    "defense",
    "strength",
    "dexterity",
    "intelligence",
    "vitality",
    "wisdom",
    "luck",
    "accuracy",
    "dodge_chance",
    "block_chance",
    "crit_chance",
    "crit_damage",
    "loot_bonus",
    "xp_bonus",
    "gold_bonus",
    "prospector_mastery",
    "prospector_xp_bonus",
    "archaeologist_mastery",
    "archaeologist_xp_bonus",
    "druid_mastery",
    "druid_xp_bonus",
}


def load_json_file(path):
    if not path.exists():
        raise FileNotFoundError(f"Missing required file: {path}")

    try:
        with path.open("r", encoding="utf-8") as file:
            data = json.load(file)
    except json.JSONDecodeError as error:
        raise ValueError(f"Invalid JSON in {path}: {error}") from error

    if not isinstance(data, dict):
        raise ValueError(f"Expected a JSON object in {path}.")

    return data


def save_json_file(path, data):
    sorted_data = {skill_id: data[skill_id] for skill_id in sorted(data)}
    text = json.dumps(sorted_data, indent=2, ensure_ascii=False) + "\n"
    path.write_text(text, encoding="utf-8")


def prompt_text(label, allow_empty=False):
    while True:
        value = input(f"{label}: ").strip()
        if value.lower() == "cancel":
            return None
        if value or allow_empty:
            return value
        print("Value cannot be empty. Type 'cancel' to abort.")


def prompt_choice(label, choices):
    valid_choices = set(choices)
    while True:
        print(label)
        for key, description in choices.items():
            print(f"{key}. {description}")
        value = input("> ").strip()
        if value.lower() == "cancel":
            return None
        if value in valid_choices:
            return value
        print("Invalid choice. Type 'cancel' to abort.")


def prompt_float(label, minimum=None, maximum=None):
    while True:
        value = input(f"{label}: ").strip()
        if value.lower() == "cancel":
            return None
        try:
            number = float(value)
        except ValueError:
            print("Enter a valid number. Type 'cancel' to abort.")
            continue
        if minimum is not None and number < minimum:
            print(f"Value must be at least {minimum}.")
            continue
        if maximum is not None and number > maximum:
            print(f"Value must be at most {maximum}.")
            continue
        return number


def prompt_int(label, minimum=None):
    while True:
        value = input(f"{label}: ").strip()
        if value.lower() == "cancel":
            return None
        try:
            number = int(value)
        except ValueError:
            print("Enter a valid integer. Type 'cancel' to abort.")
            continue
        if minimum is not None and number < minimum:
            print(f"Value must be at least {minimum}.")
            continue
        return number


def prompt_yes_no(label):
    while True:
        value = input(f"{label} [y/n]: ").strip().lower()
        if value in {"y", "yes"}:
            return True
        if value in {"n", "no"}:
            return False
        print("Enter y or n.")


def prompt_skill_id(skills):
    while True:
        skill_id = prompt_text("Skill id")
        if skill_id is None:
            return None
        if not SNAKE_CASE_PATTERN.match(skill_id):
            print("Skill id must be snake_case.")
            continue
        if skill_id in skills:
            print("Skill id already exists.")
            continue
        return skill_id


def generate_skill_id(class_id, name):
    raw_value = f"{class_id}_{name}".lower()
    raw_value = re.sub(r"[\s-]+", "_", raw_value)
    raw_value = re.sub(r"[^a-z0-9_]", "", raw_value)
    raw_value = re.sub(r"_+", "_", raw_value).strip("_")
    if not raw_value or not raw_value[0].isalpha():
        raw_value = f"skill_{raw_value}".strip("_")
    return raw_value


def make_unique_skill_id(base_id, skills):
    if base_id not in skills:
        return base_id

    suffix = 2
    while f"{base_id}_{suffix}" in skills:
        suffix += 1
    return f"{base_id}_{suffix}"


def prompt_skill_id_or_generate(skills, class_id, name):
    generated_id = make_unique_skill_id(generate_skill_id(class_id, name), skills)
    if prompt_yes_no(f'Use generated id "{generated_id}"?'):
        return generated_id
    return prompt_skill_id(skills)


def prompt_class_id(classes):
    while True:
        class_id = prompt_text("Class")
        if class_id is None:
            return None
        if class_id in classes:
            return class_id
        print("Unknown class. Available classes: " + ", ".join(sorted(classes)))


def prompt_class_id_with_default(classes, default_class):
    while True:
        value = input(f"Class [{default_class}]: ").strip()
        if value.lower() == "cancel":
            return None
        if not value:
            if default_class in classes:
                return default_class
            print("The current class is unknown. Choose a valid class.")
            print("Available classes: " + ", ".join(sorted(classes)))
            continue
        if value in classes:
            return value
        print("Unknown class. Available classes: " + ", ".join(sorted(classes)))


def prompt_stat_values(title):
    values = {}
    print(title)
    print("Enter allowed stat names one by one. Leave empty when done.")
    while True:
        stat = input("Stat: ").strip()
        if stat.lower() == "cancel":
            return None
        if not stat:
            if values:
                return values
            print("Add at least one stat or type 'cancel' to abort.")
            continue
        if stat not in ALLOWED_STATS:
            print("Unknown stat. Allowed stats: " + ", ".join(sorted(ALLOWED_STATS)))
            continue
        value = prompt_float(f"Value for {stat}")
        if value is None:
            return None
        values[stat] = value


def make_level_dicts():
    return {"1": {}, "2": {}, "3": {}, "4": {}}


def prompt_level_values(field_name, value_type="float", minimum=None, maximum=None, allow_zero=True):
    while True:
        raw_value = input(f"{field_name} levels 1-4: ").strip()
        if raw_value.lower() == "cancel":
            return None

        parts = [part for part in re.split(r"[\s,]+", raw_value) if part]
        if len(parts) != 4:
            print("Enter exactly 4 values, separated by commas or spaces. Type 'cancel' to abort.")
            continue

        values = {}
        has_error = False
        for index, part in enumerate(parts, start=1):
            try:
                if value_type == "int":
                    if re.search(r"[.eE]", part):
                        raise ValueError
                    number = int(part)
                else:
                    number = float(part)
            except ValueError:
                print(f"Invalid value for level {index}: {part}")
                has_error = True
                break

            if not allow_zero and number == 0:
                print(f"Value for level {index} cannot be zero.")
                has_error = True
                break
            if minimum is not None and number < minimum:
                print(f"Value for level {index} must be at least {minimum}.")
                has_error = True
                break
            if maximum is not None and number > maximum:
                print(f"Value for level {index} must be at most {maximum}.")
                has_error = True
                break
            values[str(index)] = number

        if not has_error:
            return values


def preview_skill(skill_id, skill):
    print()
    print(f"Skill preview: {skill_id}")
    print(f"Status: {get_engine_support_status(skill_id, skill)}")
    print()
    print(json.dumps(skill, indent=2, ensure_ascii=False))


def preview_existing_skill(skills):
    skill_id = prompt_text("Skill id")
    if skill_id is None:
        return
    if skill_id not in skills:
        print("Unknown skill id.")
        return
    preview_skill(skill_id, skills[skill_id])


def confirm_skill_add(skill_id, skill, skills):
    preview_skill(skill_id, skill)
    if not prompt_yes_no("Add this skill?"):
        print("Skill creation cancelled.")
        return False
    skills[skill_id] = skill
    return True


def list_skills(skills):
    if not skills:
        print("No skills found.")
        return

    print("Skills:")
    for skill_id in sorted(skills):
        skill = skills[skill_id]
        if not isinstance(skill, dict):
            print(f"- {skill_id} | <invalid> | <invalid> | <invalid> | <invalid> | invalid")
            continue
        name = skill.get("name", "")
        class_id = skill.get("class", "")
        skill_type = skill.get("type", "")
        trigger = skill.get("trigger", "")
        status = get_engine_support_status(skill_id, skill)
        print(f"- {skill_id} | {name} | {class_id} | {skill_type} | {trigger} | {status}")


def create_passive_skill(skills, classes):
    skill_id = prompt_skill_id(skills)
    if skill_id is None:
        return False
    name = prompt_text("Name")
    if name is None:
        return False
    class_id = prompt_class_id(classes)
    if class_id is None:
        return False
    description = prompt_text("Description")
    if description is None:
        return False

    template = prompt_choice(
        "Passive template",
        {
            "1": "Flat stat bonus",
            "2": "Stat bonus per character level",
            "3": "Mixed flat and per-level stat bonus",
        },
    )
    if template is None:
        return False

    levels = make_level_dicts()
    enhanced = {}

    if template in {"1", "3"}:
        for level in sorted(levels):
            values = prompt_stat_values(f"Flat stat modifiers for level {level}")
            if values is None:
                return False
            levels[level]["stat_modifiers"] = values
        values = prompt_stat_values("Enhanced flat stat modifiers")
        if values is None:
            return False
        enhanced["stat_modifiers"] = values

    if template in {"2", "3"}:
        for level in sorted(levels):
            values = prompt_stat_values(f"Per-character-level stat modifiers for skill level {level}")
            if values is None:
                return False
            levels[level]["stat_modifiers_per_character_level"] = values
        values = prompt_stat_values("Enhanced per-character-level stat modifiers")
        if values is None:
            return False
        enhanced["stat_modifiers_per_character_level"] = values

    skill = {
        "name": name,
        "class": class_id,
        "type": "passive",
        "trigger": "always",
        "description": description,
        "levels": levels,
        "enhanced": enhanced,
    }
    if not confirm_skill_add(skill_id, skill, skills):
        return False
    print(f"Created passive skill: {skill_id}")
    return True


def create_active_skill(skills, classes):
    skill_id = prompt_skill_id(skills)
    if skill_id is None:
        return False
    name = prompt_text("Name")
    if name is None:
        return False
    class_id = prompt_class_id(classes)
    if class_id is None:
        return False
    description = prompt_text("Description")
    if description is None:
        return False

    template = prompt_choice(
        "Active template",
        {
            "1": "Damage multiplier after taking damage",
            "2": "Damage multiplier when enemy low HP",
            "3": "Generic damage multiplier before player attack",
        },
    )
    if template is None:
        return False

    trigger_by_template = {
        "1": "before_player_attack_after_damage_taken",
        "2": "before_player_attack_when_enemy_low_hp",
        "3": "before_player_attack",
    }
    trigger = trigger_by_template[template]

    scaling_mode = prompt_choice(
        "Scaling mode",
        {
            "1": "Manual",
            "2": "Linear",
        },
    )
    if scaling_mode is None:
        return False

    fields = ["damage_multiplier"]
    if template == "2":
        fields.append("enemy_hp_threshold")
    if template in {"1", "3"}:
        fields.append("cooldown")
    elif prompt_yes_no("Add cooldown"):
        fields.append("cooldown")

    levels = make_level_dicts()
    enhanced = {}

    for field in fields:
        if scaling_mode == "1":
            for level in sorted(levels):
                value = prompt_active_field(field, f"{field} for level {level}")
                if value is None:
                    return False
                if field != "cooldown" or value != 0:
                    levels[level][field] = value
            value = prompt_active_field(field, f"Enhanced {field}")
            if value is None:
                return False
            if field != "cooldown" or value != 0:
                enhanced[field] = value
        else:
            start = prompt_active_field(field, f"Starting {field}")
            if start is None:
                return False
            step = prompt_active_step(field)
            if step is None:
                return False
            for index, level in enumerate(sorted(levels)):
                value = start + step * index
                if field == "cooldown":
                    value = int(value)
                if field != "cooldown" or value != 0:
                    levels[level][field] = value
            value = prompt_active_field(field, f"Enhanced {field}")
            if value is None:
                return False
            if field != "cooldown" or value != 0:
                enhanced[field] = value

    skill = {
        "name": name,
        "class": class_id,
        "type": "active",
        "trigger": trigger,
        "description": description,
        "levels": levels,
        "enhanced": enhanced,
    }
    if not confirm_skill_add(skill_id, skill, skills):
        return False
    print(f"Created active skill: {skill_id} ({get_engine_support_status(skill_id, skill)})")
    return True


def quick_create_active_skill(skills, classes):
    class_id = prompt_class_id(classes)
    if class_id is None:
        return False
    name = prompt_text("Name")
    if name is None:
        return False
    skill_id = prompt_skill_id_or_generate(skills, class_id, name)
    if skill_id is None:
        return False
    description = prompt_text("Description")
    if description is None:
        return False

    template = prompt_choice(
        "Active template",
        {
            "1": "Damage multiplier after taking damage",
            "2": "Damage multiplier when enemy low HP",
            "3": "Generic damage multiplier before player attack",
        },
    )
    if template is None:
        return False

    trigger_by_template = {
        "1": "before_player_attack_after_damage_taken",
        "2": "before_player_attack_when_enemy_low_hp",
        "3": "before_player_attack",
    }
    trigger = trigger_by_template[template]

    fields = ["damage_multiplier"]
    if template == "2":
        fields.append("enemy_hp_threshold")
        if prompt_yes_no("Add cooldown?"):
            fields.append("cooldown")
    else:
        fields.append("cooldown")

    levels = make_level_dicts()
    enhanced = {}

    for field in fields:
        values = prompt_quick_field_values(field)
        if values is None:
            return False
        enhanced_value = prompt_active_field(field, f"Enhanced {field}")
        if enhanced_value is None:
            return False

        for level, value in values.items():
            if field != "cooldown" or value != 0:
                levels[level][field] = value
            if field == "enemy_hp_threshold" and value > 0.75:
                print(f"[WARNING] enemy_hp_threshold for level {level} is above 0.75.")

        if field != "cooldown" or enhanced_value != 0:
            enhanced[field] = enhanced_value

    skill = {
        "name": name,
        "class": class_id,
        "type": "active",
        "trigger": trigger,
        "description": description,
        "levels": levels,
        "enhanced": enhanced,
    }
    if not confirm_skill_add(skill_id, skill, skills):
        return False
    print(f"Created active skill: {skill_id} ({get_engine_support_status(skill_id, skill)})")
    return True


def prompt_quick_field_values(field):
    if field == "cooldown":
        return prompt_level_values(field, value_type="int", minimum=0)
    if field == "enemy_hp_threshold":
        return prompt_level_values(field, value_type="float", minimum=0.01, maximum=1.0, allow_zero=False)
    return prompt_level_values(field, value_type="float", minimum=0.000001, allow_zero=False)


def prompt_active_field(field, label):
    if field == "cooldown":
        return prompt_int(label, minimum=0)
    if field == "enemy_hp_threshold":
        value = prompt_float(label, minimum=0.01, maximum=1.0)
        if value is not None and value > 0.75:
            print("[WARNING] enemy_hp_threshold above 0.75 may trigger too often.")
        return value
    return prompt_float(label, minimum=0.000001)


def prompt_active_step(field):
    if field == "cooldown":
        return prompt_int(f"{field} step per level")
    return prompt_float(f"{field} step per level")


def duplicate_skill(skills, classes):
    list_skills(skills)
    source_id = prompt_text("Source skill id")
    if source_id is None:
        return False
    if source_id not in skills:
        print("Unknown source skill id.")
        return False
    if not isinstance(skills[source_id], dict):
        print("Source skill is invalid and cannot be duplicated.")
        return False

    source_skill = skills[source_id]
    new_skill = copy.deepcopy(source_skill)
    new_name = prompt_text("New name")
    if new_name is None:
        return False
    old_class = source_skill.get("class", "")
    new_class = prompt_class_id_with_default(classes, old_class)
    if new_class is None:
        return False
    new_id = prompt_skill_id_or_generate(skills, new_class, new_name)
    if new_id is None:
        return False

    old_description = source_skill.get("description", "")
    new_description = prompt_text(f"New description [{old_description}]", allow_empty=True)
    if new_description is None:
        return False
    if not new_description:
        new_description = old_description

    new_skill["name"] = new_name
    new_skill["class"] = new_class
    new_skill["description"] = new_description

    if not confirm_skill_add(new_id, new_skill, skills):
        return False
    print(f"Duplicated skill: {source_id} -> {new_id}")
    return True


def edit_skill(skills, classes):
    skill_id = prompt_text("Skill id")
    if skill_id is None:
        return False
    if skill_id not in skills:
        print("Unknown skill id.")
        return False
    if not isinstance(skills[skill_id], dict):
        print("This skill is invalid and cannot be edited.")
        return False

    dirty = False
    while True:
        print()
        print("1. Rename skill")
        print("2. Change description")
        print("3. Change class")
        print("4. Change trigger")
        print("5. Edit level field values")
        print("6. Edit enhanced field value")
        print("7. Preview current skill")
        print("0. Back")
        choice = input("> ").strip()

        if choice == "1":
            dirty = apply_skill_edit(skills, skill_id, edit_skill_name) or dirty
        elif choice == "2":
            dirty = apply_skill_edit(skills, skill_id, edit_skill_description) or dirty
        elif choice == "3":
            dirty = apply_skill_edit(skills, skill_id, lambda skill: edit_skill_class(skill, classes)) or dirty
        elif choice == "4":
            dirty = apply_skill_edit(skills, skill_id, edit_skill_trigger) or dirty
        elif choice == "5":
            dirty = apply_skill_edit(skills, skill_id, edit_level_field_values) or dirty
        elif choice == "6":
            dirty = apply_skill_edit(skills, skill_id, edit_enhanced_field_value) or dirty
        elif choice == "7":
            preview_skill(skill_id, skills[skill_id])
        elif choice == "0":
            return dirty
        else:
            print("Invalid menu choice.")


def apply_skill_edit(skills, skill_id, edit_function):
    previous_skill = copy.deepcopy(skills[skill_id])
    changed = edit_function(skills[skill_id])
    if not changed:
        return False

    preview_skill(skill_id, skills[skill_id])
    if prompt_yes_no("Keep this change?"):
        return True

    skills[skill_id] = previous_skill
    print("Change discarded.")
    return False


def edit_skill_name(skill):
    value = prompt_text("New name")
    if value is None:
        return False
    skill["name"] = value
    return True


def edit_skill_description(skill):
    value = prompt_text("New description")
    if value is None:
        return False
    skill["description"] = value
    return True


def edit_skill_class(skill, classes):
    value = prompt_class_id(classes)
    if value is None:
        return False
    skill["class"] = value
    return True


def edit_skill_trigger(skill):
    triggers = sorted(SUPPORTED_NOW_TRIGGERS) + sorted(DATA_ONLY_TRIGGERS)
    print("Allowed triggers:")
    for trigger in triggers:
        print(f"- {trigger}")
    value = prompt_text("New trigger")
    if value is None:
        return False
    if value not in triggers:
        print("Unknown trigger.")
        return False
    skill["trigger"] = value
    print(f"New status: {get_engine_support_status('<current>', skill)}")
    return True


def edit_level_field_values(skill):
    field = prompt_editable_field()
    if field is None:
        return False

    levels = skill.setdefault("levels", make_level_dicts())
    if not isinstance(levels, dict):
        print("Levels must be a dictionary before editing.")
        return False
    for level in LEVEL_KEYS:
        levels.setdefault(level, {})

    if field in {"damage_multiplier", "cooldown", "enemy_hp_threshold"}:
        values = prompt_values_for_field(field)
        if values is None:
            return False
        for level, value in values.items():
            if field == "cooldown" and value == 0:
                levels[level].pop("cooldown", None)
            else:
                levels[level][field] = value
        return True

    stat = prompt_allowed_stat()
    if stat is None:
        return False
    values = prompt_level_values(stat, value_type="float")
    if values is None:
        return False
    for level, value in values.items():
        levels[level].setdefault(field, {})[stat] = value
    return True


def edit_enhanced_field_value(skill):
    field = prompt_editable_field()
    if field is None:
        return False
    enhanced = skill.setdefault("enhanced", {})
    if not isinstance(enhanced, dict):
        print("Enhanced must be a dictionary before editing.")
        return False

    if field in {"damage_multiplier", "cooldown", "enemy_hp_threshold"}:
        value = prompt_active_field(field, f"Enhanced {field}")
        if value is None:
            return False
        if field == "cooldown" and value == 0:
            enhanced.pop("cooldown", None)
        else:
            enhanced[field] = value
        return True

    stat = prompt_allowed_stat()
    if stat is None:
        return False
    value = prompt_float(f"Enhanced {field}.{stat}")
    if value is None:
        return False
    enhanced.setdefault(field, {})[stat] = value
    return True


def prompt_editable_field():
    return prompt_choice(
        "Field",
        {
            "damage_multiplier": "damage_multiplier",
            "cooldown": "cooldown",
            "enemy_hp_threshold": "enemy_hp_threshold",
            "stat_modifiers": "stat_modifiers",
            "stat_modifiers_per_character_level": "stat_modifiers_per_character_level",
        },
    )


def prompt_allowed_stat():
    while True:
        stat = prompt_text("Stat")
        if stat is None:
            return None
        if stat in ALLOWED_STATS:
            return stat
        print("Unknown stat. Allowed stats: " + ", ".join(sorted(ALLOWED_STATS)))


def prompt_values_for_field(field):
    if field == "cooldown":
        return prompt_level_values(field, value_type="int", minimum=0)
    if field == "enemy_hp_threshold":
        return prompt_level_values(field, value_type="float", minimum=0.01, maximum=1.0, allow_zero=False)
    return prompt_level_values(field, value_type="float", minimum=0.000001, allow_zero=False)


def validate_skills(skills, classes):
    errors = []
    warnings = []
    seen_ids = set()

    if not isinstance(skills, dict):
        return ["Skills data must be a JSON object."], warnings

    for skill_id, skill in skills.items():
        location = f"Skill '{skill_id}'"
        if not skill_id:
            errors.append("Skill id cannot be empty.")
        elif not isinstance(skill_id, str):
            errors.append(f"{location}: skill id must be a string.")
        elif not SNAKE_CASE_PATTERN.match(skill_id):
            errors.append(f"{location}: skill id must be snake_case.")

        if skill_id in seen_ids:
            errors.append(f"{location}: duplicate skill id.")
        seen_ids.add(skill_id)

        if not isinstance(skill, dict):
            errors.append(f"{location}: skill definition must be a dictionary.")
            continue

        name = skill.get("name")
        class_id = skill.get("class")
        skill_type = skill.get("type")
        trigger = skill.get("trigger")
        levels = skill.get("levels")
        enhanced = skill.get("enhanced")

        if not isinstance(name, str) or not name.strip():
            errors.append(f"{location}: name cannot be empty.")
        if class_id not in classes:
            errors.append(f"{location}: class must exist in data/classes.json.")
        if skill_type not in {"active", "passive"}:
            errors.append(f"{location}: type must be active or passive.")
        if not isinstance(trigger, str) or not trigger.strip():
            errors.append(f"{location}: trigger cannot be empty.")
        elif trigger not in SUPPORTED_NOW_TRIGGERS and trigger not in DATA_ONLY_TRIGGERS:
            warnings.append(f"{location}: trigger '{trigger}' is not known by this editor.")

        if not isinstance(levels, dict):
            errors.append(f"{location}: levels must be a dictionary.")
        else:
            level_keys = set(levels)
            if level_keys != LEVEL_KEYS:
                errors.append(f"{location}: levels must contain exactly keys 1, 2, 3, 4.")
            for level, level_data in levels.items():
                if not isinstance(level_data, dict):
                    errors.append(f"{location}: level {level} must be a dictionary.")
                    continue
                validate_skill_values(errors, warnings, f"{location} level {level}", level_data)

        if not isinstance(enhanced, dict):
            errors.append(f"{location}: enhanced must be a dictionary.")
        else:
            validate_skill_values(errors, warnings, f"{location} enhanced", enhanced)

        if get_engine_support_status(skill_id, skill) == "invalid":
            errors.append(f"{location}: engine support status is invalid.")

        if skill_type == "active":
            if trigger in DATA_ONLY_TRIGGERS:
                warnings.append(f"{location}: active skill uses data_only trigger '{trigger}'.")
            if not skill_has_field(skill, "damage_multiplier"):
                warnings.append(f"{location}: active skill has no damage_multiplier.")
        elif skill_type == "passive":
            if not skill_has_field(skill, "stat_modifiers") and not skill_has_field(
                skill, "stat_modifiers_per_character_level"
            ):
                warnings.append(
                    f"{location}: passive skill has no stat_modifiers or stat_modifiers_per_character_level."
                )

    return errors, warnings


def skill_has_field(skill, field):
    levels = skill.get("levels")
    if isinstance(levels, dict):
        for level_data in levels.values():
            if isinstance(level_data, dict) and field in level_data:
                return True
    enhanced = skill.get("enhanced")
    return isinstance(enhanced, dict) and field in enhanced


def validate_skill_values(errors, warnings, location, data):
    for key, value in data.items():
        if key in {"stat_modifiers", "stat_modifiers_per_character_level"}:
            validate_stat_modifiers(errors, location, key, value)
            continue

        if key == "damage_multiplier":
            if not is_number(value) or value <= 0:
                errors.append(f"{location}: damage_multiplier must be a number greater than 0.")
            continue

        if key == "enemy_hp_threshold":
            if not is_number(value) or value < 0.01 or value > 1.0:
                errors.append(f"{location}: enemy_hp_threshold must be between 0.01 and 1.0.")
            elif value > 0.75:
                warnings.append(f"{location}: enemy_hp_threshold above 0.75 may trigger too often.")
            continue

        if key == "cooldown":
            if not isinstance(value, int) or isinstance(value, bool) or value < 0:
                errors.append(f"{location}: cooldown must be an integer greater than or equal to 0.")
            continue

        if isinstance(value, dict):
            validate_skill_values(errors, warnings, f"{location}.{key}", value)
        elif not is_number(value) and not isinstance(value, str):
            errors.append(f"{location}: {key} has unsupported value type.")


def validate_stat_modifiers(errors, location, key, value):
    if not isinstance(value, dict):
        errors.append(f"{location}: {key} must be a dictionary.")
        return

    for stat, amount in value.items():
        if stat not in ALLOWED_STATS:
            errors.append(f"{location}: {stat} is not an allowed stat in {key}.")
        if not is_number(amount):
            errors.append(f"{location}: {key}.{stat} must be an int or float, not bool.")


def is_number(value):
    return isinstance(value, (int, float)) and not isinstance(value, bool)


def show_validation_result(errors, warnings):
    for error in errors:
        print(f"[ERROR] {error}")
    for warning in warnings:
        print(f"[WARNING] {warning}")
    if not errors and not warnings:
        print("[OK] Skills data is valid.")
    elif not errors:
        print("[OK] Skills data is valid with warnings.")


def show_skill_report(skills):
    by_class = {}
    passive_count = 0
    active_count = 0
    supported_count = 0
    data_only_count = 0
    invalid_count = 0
    triggers = set()

    for skill_id, skill in skills.items():
        if not isinstance(skill, dict):
            invalid_count += 1
            continue

        class_id = skill.get("class", "<missing>")
        by_class[class_id] = by_class.get(class_id, 0) + 1

        if skill.get("type") == "passive":
            passive_count += 1
        elif skill.get("type") == "active":
            active_count += 1

        trigger = skill.get("trigger")
        if trigger:
            triggers.add(trigger)

        status = get_engine_support_status(skill_id, skill)
        if status == "supported_now":
            supported_count += 1
        elif status == "data_only":
            data_only_count += 1
        else:
            invalid_count += 1

    print(f"Total skills: {len(skills)}")
    print("Skills by class:")
    for class_id in sorted(by_class):
        print(f"- {class_id}: {by_class[class_id]}")
    print(f"Passives: {passive_count}")
    print(f"Actives: {active_count}")
    print(f"supported_now: {supported_count}")
    print(f"data_only: {data_only_count}")
    print(f"invalid: {invalid_count}")
    print("Triggers used:")
    for trigger in sorted(triggers):
        print(f"- {trigger}")


def get_engine_support_status(skill_id, skill):
    if not skill_id or not isinstance(skill_id, str):
        return "invalid"
    if not isinstance(skill, dict):
        return "invalid"
    trigger = skill.get("trigger")
    skill_type = skill.get("type")
    if skill_type not in {"active", "passive"} or not isinstance(trigger, str) or not trigger:
        return "invalid"
    if trigger in SUPPORTED_NOW_TRIGGERS:
        return "supported_now"
    if trigger in DATA_ONLY_TRIGGERS:
        return "data_only"
    return "invalid"


def main():
    try:
        skills = load_json_file(SKILLS_PATH)
        classes = load_json_file(CLASSES_PATH)
    except (FileNotFoundError, ValueError) as error:
        print(f"[ERROR] {error}")
        return

    dirty = False

    while True:
        print()
        print("1. List skills")
        print("2. Create passive skill")
        print("3. Create active skill")
        print("4. Quick create active skill")
        print("5. Duplicate skill")
        print("6. Edit skill")
        print("7. Validate skills")
        print("8. Show skill report")
        print("9. Preview skill JSON")
        print("10. Save skills")
        print("0. Quit")
        choice = input("> ").strip()

        if choice == "1":
            list_skills(skills)
        elif choice == "2":
            if create_passive_skill(skills, classes):
                dirty = True
        elif choice == "3":
            if create_active_skill(skills, classes):
                dirty = True
        elif choice == "4":
            if quick_create_active_skill(skills, classes):
                dirty = True
        elif choice == "5":
            if duplicate_skill(skills, classes):
                dirty = True
        elif choice == "6":
            if edit_skill(skills, classes):
                dirty = True
        elif choice == "7":
            errors, warnings = validate_skills(skills, classes)
            show_validation_result(errors, warnings)
        elif choice == "8":
            show_skill_report(skills)
        elif choice == "9":
            preview_existing_skill(skills)
        elif choice == "10":
            errors, warnings = validate_skills(skills, classes)
            show_validation_result(errors, warnings)
            if errors:
                print("Save refused because errors exist.")
                continue
            if warnings and not prompt_yes_no("Warnings exist. Save anyway"):
                continue
            save_json_file(SKILLS_PATH, skills)
            dirty = False
            print(f"Saved {SKILLS_PATH}")
        elif choice == "0":
            if dirty and not prompt_yes_no("Unsaved changes exist. Quit anyway"):
                continue
            print("Goodbye.")
            return
        else:
            print("Invalid menu choice.")


if __name__ == "__main__":
    main()
