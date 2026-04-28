def apply_combat_rewards(player, enemy):
    player["exp"] = player.get("exp", 0)
    player["gold"] = player.get("gold", 0)
    player["level"] = player.get("level", 1)
    player["next_exp"] = player.get("next_exp", 100)

    xp_bonus = player.get("xp_bonus", 0.0)
    gold_bonus = player.get("gold_bonus", 0.0)

    base_exp = enemy["exp"]
    base_gold = enemy["gold"]

    exp_gained = int(base_exp * (1 + xp_bonus))
    gold_gained = int(base_gold * (1 + gold_bonus))

    exp_gained = max(base_exp, exp_gained)
    gold_gained = max(base_gold, gold_gained)

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
        "base_exp": base_exp,
        "base_gold": base_gold,
        "xp_bonus": xp_bonus,
        "gold_bonus": gold_bonus,
    }
