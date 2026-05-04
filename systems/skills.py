WARRIOR_COMEBACK_STRIKE = "warrior_comeback_strike"


def ensure_skills(player):
    if "skills" not in player:
        player["skills"] = {}
    return player["skills"]


def ensure_skill_cooldowns(player):
    if "skill_cooldowns" not in player:
        player["skill_cooldowns"] = {}
    return player["skill_cooldowns"]


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

    if not values:
        return None
    if "damage_multiplier" not in values or "cooldown" not in values:
        return None
    return values


def apply_before_action_skills(combat, actor, target, action, is_player):
    if (
        is_player is not True
        or actor.get("class") != "warrior"
        or action != "attack"
        or combat.player_took_damage_since_last_action is not True
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

    combat.pending_damage_multiplier = skill_values["damage_multiplier"]
    cooldowns[WARRIOR_COMEBACK_STRIKE] = skill_values["cooldown"]
    combat.log.append("Comeback Strike activated!")


def tick_skill_cooldowns(player):
    cooldowns = ensure_skill_cooldowns(player)
    for skill_id, cooldown in cooldowns.items():
        if cooldown > 0:
            cooldowns[skill_id] = max(0, cooldown - 1)
