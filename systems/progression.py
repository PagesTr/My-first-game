def apply_combat_rewards(player, enemy):
    player["exp"] = player.get("exp", 0)
    player["gold"] = player.get("gold", 0)
    player["level"] = player.get("level", 1)
    player["next_exp"] = player.get("next_exp", 100)

    exp_gained = enemy["exp"]
    gold_gained = enemy["gold"]

    player["exp"] += exp_gained
    player["gold"] += gold_gained

    levels_gained = 0
    while player["exp"] >= player["next_exp"]:
        player["exp"] -= player["next_exp"]
        player["level"] += 1
        player["next_exp"] = int(player["next_exp"] * 1.5)
        levels_gained += 1

    return {
        "exp_gained": exp_gained,
        "gold_gained": gold_gained,
        "leveled_up": levels_gained > 0,
        "levels_gained": levels_gained,
        "new_level": player["level"],
    }
