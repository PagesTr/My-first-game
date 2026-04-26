def apply_combat_rewards(player, enemy):
    player["exp"] = player.get("exp", 0)
    player["gold"] = player.get("gold", 0)

    exp_gained = enemy["exp"]
    gold_gained = enemy["gold"]

    player["exp"] += exp_gained
    player["gold"] += gold_gained

    return {
        "exp_gained": exp_gained,
        "gold_gained": gold_gained,
        "leveled_up": False,
    }
