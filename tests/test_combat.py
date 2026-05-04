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


def test_attack_reduces_enemy_hp(monkeypatch):
    monkeypatch.setattr("systems.combat.random.random", lambda: 0.5)
    player = make_player()
    player["attack"] = 10
    enemy = make_enemy("aggressive", current_hp=20)
    combat = CombatSystem(player, enemy)

    combat.step("attack")

    assert enemy["current_hp"] < 20


def test_heal_restores_player_hp(monkeypatch):
    monkeypatch.setattr("systems.combat.random.random", lambda: 0.5)
    player = make_player()
    player["current_hp"] = 5
    player["healing_power"] = 20
    enemy = make_enemy("aggressive", current_hp=20)
    enemy["accuracy"] = 0.0
    combat = CombatSystem(player, enemy)

    combat.step("heal")

    assert player["current_hp"] == player["max_hp"]


def test_combat_ends_when_enemy_dies(monkeypatch):
    monkeypatch.setattr("systems.combat.random.random", lambda: 0.5)
    player = make_player()
    player["attack"] = 10
    enemy = make_enemy("aggressive", current_hp=1)
    combat = CombatSystem(player, enemy)

    combat.step("attack")

    assert combat.is_over is True
    assert combat.winner == "player"


def test_combat_ends_when_player_dies(monkeypatch):
    monkeypatch.setattr("systems.combat.random.random", lambda: 0.5)
    player = make_player()
    player["current_hp"] = 1
    player["max_hp"] = 1
    player["attack"] = 1
    player["defense"] = 0
    enemy = make_enemy("aggressive", current_hp=20)
    enemy["attack"] = 10
    combat = CombatSystem(player, enemy)

    combat.step("attack")

    assert combat.is_over is True
    assert combat.winner == "enemy"


def test_player_auto_action_returns_heal_when_player_hp_is_low():
    player = make_player()
    player["current_hp"] = 6
    combat = CombatSystem(player, make_enemy("aggressive", current_hp=20))

    assert combat._player_auto_action() == "heal"


def test_player_auto_action_returns_attack_when_player_hp_is_high():
    player = make_player()
    player["current_hp"] = 7
    combat = CombatSystem(player, make_enemy("aggressive", current_hp=20))

    assert combat._player_auto_action() == "attack"


def test_step_uses_player_auto_action_when_action_is_none(monkeypatch):
    monkeypatch.setattr("systems.combat.random.random", lambda: 0.5)
    player = make_player()
    player["current_hp"] = 6
    enemy = make_enemy("aggressive", current_hp=20)
    combat = CombatSystem(player, enemy)

    combat.step(None)

    assert player["current_hp"] > 6
