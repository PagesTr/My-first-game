from entities.players import create_player
from systems.effects import (
    add_temporary_effect,
    ensure_effects_container,
    get_active_stat_modifiers,
    tick_combat_effects,
    tick_time_effects,
)
from systems.stats import prepare_player_for_combat


def make_combat_effect(effect_id="rage_test", remaining_combats=2):
    return {
        "id": effect_id,
        "name": "Rage",
        "source": "test",
        "modifiers": {
            "attack": 3,
        },
        "duration_type": "combat",
        "remaining_combats": remaining_combats,
    }


def make_time_effect(effect_id="focus_test", remaining_seconds=60):
    return {
        "id": effect_id,
        "name": "Focus",
        "source": "test",
        "modifiers": {
            "crit_chance": 0.05,
        },
        "duration_type": "time",
        "remaining_seconds": remaining_seconds,
    }


def make_classes():
    return {
        "warrior": {
            "base_stats": {
                "strength": 4,
                "dexterity": 1,
                "intelligence": 0,
                "vitality": 4,
                "wisdom": 1,
                "luck": 0,
            }
        }
    }


def test_ensure_effects_container_adds_active_effects_when_missing():
    player = {}

    active_effects = ensure_effects_container(player)

    assert active_effects == []
    assert player["active_effects"] is active_effects


def test_add_temporary_effect_accepts_valid_combat_effect():
    player = {}
    effect = make_combat_effect()

    added = add_temporary_effect(player, effect)

    assert added is True
    assert player["active_effects"][0] == effect
    assert player["active_effects"][0] is not effect


def test_add_temporary_effect_rejects_invalid_effect():
    player = {}

    assert add_temporary_effect(player, None) is False
    assert add_temporary_effect(player, {"modifiers": {}}) is False
    assert add_temporary_effect(
        player,
        {
            "modifiers": [],
            "duration_type": "combat",
            "remaining_combats": 1,
        },
    ) is False
    assert add_temporary_effect(
        player,
        {
            "modifiers": {"attack": 1},
            "duration_type": "combat",
            "remaining_combats": 0,
        },
    ) is False


def test_get_active_stat_modifiers_sums_multiple_effects():
    player = {
        "active_effects": [
            {
                "modifiers": {"attack": 2},
            },
            {
                "modifiers": {"attack": 3, "defense": 1},
            },
        ]
    }

    modifiers = get_active_stat_modifiers(player)

    assert modifiers == {"attack": 5, "defense": 1}


def test_tick_combat_effects_reduces_remaining_combats():
    player = {"active_effects": [make_combat_effect(remaining_combats=2)]}

    removed = tick_combat_effects(player)

    assert removed == 0
    assert player["active_effects"][0]["remaining_combats"] == 1


def test_tick_combat_effects_removes_expired_combat_effect():
    player = {"active_effects": [make_combat_effect(remaining_combats=1)]}

    removed = tick_combat_effects(player)

    assert removed == 1
    assert player["active_effects"] == []


def test_tick_combat_effects_does_not_modify_time_effects():
    player = {"active_effects": [make_time_effect(remaining_seconds=60)]}

    removed = tick_combat_effects(player)

    assert removed == 0
    assert player["active_effects"][0]["remaining_seconds"] == 60


def test_tick_time_effects_reduces_remaining_seconds():
    player = {"active_effects": [make_time_effect(remaining_seconds=60)]}

    removed = tick_time_effects(player, 15)

    assert removed == 0
    assert player["active_effects"][0]["remaining_seconds"] == 45


def test_tick_time_effects_removes_expired_time_effect():
    player = {"active_effects": [make_time_effect(remaining_seconds=10)]}

    removed = tick_time_effects(player, 10)

    assert removed == 1
    assert player["active_effects"] == []


def test_tick_time_effects_does_not_modify_combat_effects():
    player = {"active_effects": [make_combat_effect(remaining_combats=2)]}

    removed = tick_time_effects(player, 15)

    assert removed == 0
    assert player["active_effects"][0]["remaining_combats"] == 2


def test_prepare_player_for_combat_applies_temporary_attack_bonus():
    classes = make_classes()
    items = {}
    player = create_player("warrior", classes, items)
    base_attack = player["attack"]
    add_temporary_effect(
        player,
        {
            "id": "attack_test",
            "name": "Attack Test",
            "source": "test",
            "modifiers": {
                "attack": 5,
            },
            "duration_type": "combat",
            "remaining_combats": 1,
        },
    )

    prepare_player_for_combat(player, items, classes)

    assert player["attack"] == base_attack + 5
