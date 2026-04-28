from systems.progression import apply_combat_rewards


def test_apply_combat_rewards_uses_xp_and_gold_bonus():
    player = {
        "exp": 0,
        "gold": 0,
        "level": 1,
        "next_exp": 100,
        "xp_bonus": 0.10,
        "gold_bonus": 0.25,
    }
    enemy = {
        "exp": 50,
        "gold": 40,
    }

    result = apply_combat_rewards(player, enemy)

    assert result["base_exp"] == 50
    assert result["base_gold"] == 40
    assert result["exp_gained"] == 55
    assert result["gold_gained"] == 50
    assert player["exp"] == 55
    assert player["gold"] == 50
    assert result["leveled_up"] is False


def test_apply_combat_rewards_keeps_existing_behavior_without_bonus():
    player = {
        "exp": 0,
        "gold": 0,
        "level": 1,
        "next_exp": 100,
    }
    enemy = {
        "exp": 50,
        "gold": 40,
    }

    result = apply_combat_rewards(player, enemy)

    assert result["exp_gained"] == enemy["exp"]
    assert result["gold_gained"] == enemy["gold"]
    assert player["exp"] == enemy["exp"]
    assert player["gold"] == enemy["gold"]
