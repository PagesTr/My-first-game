WARRIOR_COMEBACK_STRIKE = "warrior_comeback_strike"


def ensure_skills(player):
    if "skills" not in player:
        player["skills"] = {}
    return player["skills"]


def ensure_skill_cooldowns(player):
    if "skill_cooldowns" not in player:
        player["skill_cooldowns"] = {}
    return player["skill_cooldowns"]


def get_skill_slot_count(player):
    level = player.get("level", 1)
    if level >= 10:
        return 3
    if level >= 5:
        return 2
    return 1


def ensure_equipped_skills(player):
    if "equipped_skills" not in player:
        player["equipped_skills"] = []
    return player["equipped_skills"]


def is_skill_equipped(player, skill_id):
    equipped_skills = ensure_equipped_skills(player)
    return skill_id in equipped_skills


def get_available_class_skills(skills_data, player):
    return [
        (skill_id, skill_data)
        for skill_id, skill_data in (skills_data or {}).items()
        if skill_data.get("class") == player.get("class")
    ]


def get_skill_type(skills_data, skill_id):
    return (skills_data or {}).get(skill_id, {}).get("type", "active")


def spend_skill_point(player):
    if player.get("skill_points", 0) <= 0:
        return False

    player["skill_points"] -= 1
    return True


def refund_skill_point(player):
    player["skill_points"] = player.get("skill_points", 0) + 1
    return True


def learn_or_upgrade_skill(player, skill_id):
    skill_state = get_player_skill_state(player, skill_id)
    if skill_state["level"] == 0:
        return learn_skill(player, skill_id)
    if skill_state["level"] < 4:
        return upgrade_skill(player, skill_id)
    return False


def learn_skill(player, skill_id):
    skills = ensure_skills(player)
    if skill_id in skills:
        return False

    skills[skill_id] = {"level": 1, "enhanced": False}
    return True


def upgrade_skill(player, skill_id):
    skills = ensure_skills(player)
    if skill_id not in skills:
        return False

    skill_state = get_player_skill_state(player, skill_id)
    level = skill_state["level"]
    if level >= 4:
        return False

    skills[skill_id]["level"] = level + 1
    return True


def enhance_skill(player, skill_id):
    skills = ensure_skills(player)
    if skill_id not in skills:
        return False

    skill_state = get_player_skill_state(player, skill_id)
    if skill_state["level"] < 4 or skill_state["enhanced"] is True:
        return False

    skills[skill_id]["enhanced"] = True
    return True


def is_skill_known(player, skill_id):
    return get_player_skill_state(player, skill_id)["level"] >= 1


def equip_skill(player, skill_id):
    if not is_skill_known(player, skill_id):
        return False

    equipped_skills = ensure_equipped_skills(player)
    if skill_id in equipped_skills:
        return True

    if len(equipped_skills) >= get_skill_slot_count(player):
        return False

    equipped_skills.append(skill_id)
    return True


def unequip_skill(player, skill_id):
    equipped_skills = ensure_equipped_skills(player)
    if skill_id not in equipped_skills:
        return False

    equipped_skills.remove(skill_id)
    return True


def get_player_skill_state(player, skill_id):
    skills = ensure_skills(player)
    skill_state = skills.get(skill_id)
    if skill_state is None:
        return {"level": 0, "enhanced": False}

    level = max(0, min(4, int(skill_state.get("level", 0))))
    enhanced = bool(skill_state.get("enhanced", False))
    if enhanced and level < 4:
        enhanced = False

    return {"level": level, "enhanced": enhanced}


def get_skill_values(skills_data, player, skill_id):
    skills_data = skills_data or {}
    skill_state = get_player_skill_state(player, skill_id)
    level = skill_state["level"]
    if level == 0:
        return None

    skill_definition = skills_data.get(skill_id)
    if not skill_definition:
        return None

    if skill_state["enhanced"] and level == 4:
        values = skill_definition.get("enhanced")
    else:
        levels = skill_definition.get("levels", {})
        values = levels.get(str(level))

    if not isinstance(values, dict):
        return None
    return values


def get_passive_skill_stat_modifiers(skills_data, player):
    skills_data = skills_data or {}
    modifiers = {}

    for skill_id in ensure_skills(player):
        skill_definition = skills_data.get(skill_id)
        if not skill_definition or skill_definition.get("type") != "passive":
            continue

        skill_values = get_skill_values(skills_data, player, skill_id)
        if skill_values is None:
            continue

        flat_modifiers = skill_values.get("stat_modifiers", {})
        if not isinstance(flat_modifiers, dict):
            flat_modifiers = {}
        for stat, value in flat_modifiers.items():
            if isinstance(value, (int, float)) and not isinstance(value, bool):
                modifiers[stat] = modifiers.get(stat, 0) + value

        level = player.get("level", 1)
        per_level_modifiers = skill_values.get(
            "stat_modifiers_per_character_level",
            {},
        )
        if not isinstance(per_level_modifiers, dict):
            per_level_modifiers = {}
        for stat, value in per_level_modifiers.items():
            if isinstance(value, (int, float)) and not isinstance(value, bool):
                modifiers[stat] = modifiers.get(stat, 0) + value * level

    return modifiers


def apply_before_action_skills(combat, actor, target, action, is_player):
    if (
        is_player is not True
        or actor.get("class") != "warrior"
        or action != "attack"
        or combat.player_took_damage_since_last_action is not True
        or is_skill_known(actor, WARRIOR_COMEBACK_STRIKE) is not True
        or is_skill_equipped(actor, WARRIOR_COMEBACK_STRIKE) is not True
    ):
        return

    cooldowns = ensure_skill_cooldowns(actor)
    if cooldowns.get(WARRIOR_COMEBACK_STRIKE, 0) > 0:
        return

    skill_values = get_skill_values(
        combat.skills_data,
        actor,
        WARRIOR_COMEBACK_STRIKE,
    )
    if skill_values is None:
        return
    if "damage_multiplier" not in skill_values:
        return

    combat.pending_damage_multiplier = skill_values["damage_multiplier"]
    cooldown = skill_values.get("cooldown", 0)
    if cooldown > 0:
        cooldowns[WARRIOR_COMEBACK_STRIKE] = cooldown
    combat.log.append("Comeback Strike activated!")


def tick_skill_cooldowns(player):
    cooldowns = ensure_skill_cooldowns(player)
    for skill_id, cooldown in cooldowns.items():
        if cooldown > 0:
            cooldowns[skill_id] = max(0, cooldown - 1)
