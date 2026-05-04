WARRIOR_COMEBACK_STRIKE = "warrior_comeback_strike"


def ensure_skill_cooldowns(player):
    if "skill_cooldowns" not in player:
        player["skill_cooldowns"] = {}
    return player["skill_cooldowns"]


def apply_before_action_skills(combat, actor, target, action, is_player):
    cooldowns = ensure_skill_cooldowns(actor)

    if (
        is_player is True
        and actor.get("class") == "warrior"
        and action == "attack"
        and actor["current_hp"] < actor["max_hp"]
        and cooldowns.get(WARRIOR_COMEBACK_STRIKE, 0) == 0
    ):
        combat.pending_damage_multiplier = 1.5
        cooldowns[WARRIOR_COMEBACK_STRIKE] = 3
        combat.log.append("Warrior comeback strike activated!")


def tick_skill_cooldowns(player):
    cooldowns = ensure_skill_cooldowns(player)
    for skill_id, cooldown in cooldowns.items():
        if cooldown > 0:
            cooldowns[skill_id] = max(0, cooldown - 1)
