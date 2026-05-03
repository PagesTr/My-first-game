from entities.enemy import create_enemy
from systems.combat import CombatSystem


def make_template(behavior=None):
    template = {
        "name": "Test Enemy",
        "stats": {
            "hp": 10,
            "attack": 2,
            "defense": 1,
        },
        "exp": 1,
        "gold": 1,
    }
    if behavior is not None:
        template["behavior"] = behavior
    return template


def make_player():
    return {
        "current_hp": 20,
        "max_hp": 20,
        "attack": 5,
        "defense": 1,
    }


def make_enemy(behavior, current_hp, max_hp=20):
    return {
        "behavior": behavior,
        "current_hp": current_hp,
        "max_hp": max_hp,
        "attack": 4,
        "defense": 1,
    }


def test_create_enemy_adds_behavior(monkeypatch):
    monkeypatch.setattr("entities.enemy.random.randint", lambda _low, _high: 0)

    enemy = create_enemy(make_template("aggressive"), 1)

    assert enemy["behavior"] == "aggressive"


def test_create_enemy_defaults_to_balanced(monkeypatch):
    monkeypatch.setattr("entities.enemy.random.randint", lambda _low, _high: 0)

    enemy = create_enemy(make_template(), 1)

    assert enemy["behavior"] == "balanced"


def test_enemy_ai_returns_attack_for_aggressive_enemy():
    combat = CombatSystem(make_player(), make_enemy("aggressive", current_hp=1))

    assert combat._enemy_ai() == "attack"


def test_enemy_ai_returns_heal_for_defensive_enemy_with_low_hp():
    combat = CombatSystem(make_player(), make_enemy("defensive", current_hp=6))

    assert combat._enemy_ai() == "heal"


def test_enemy_ai_returns_attack_for_defensive_enemy_with_enough_hp():
    combat = CombatSystem(make_player(), make_enemy("defensive", current_hp=7))

    assert combat._enemy_ai() == "attack"
