from systems.combat import CombatSystem
from systems.instance import run_instant_instance


def make_player():
    return {
        "class": "warrior",
        "level": 1,
        "exp": 0,
        "next_exp": 100,
        "gold": 0,
        "max_hp": 10,
        "current_hp": 3,
        "attack": 5,
        "defense": 0,
    }


def make_zone():
    return {
        "name": "Test Zone",
        "enemy_pool": ["test_enemy"],
        "difficulty_multiplier": 1.0,
    }


def make_enemy_template():
    return {
        "name": "Test Enemy",
        "behavior": "aggressive",
        "stats": {
            "hp": 4,
            "attack": 1,
            "defense": 0,
        },
        "exp": 5,
        "gold": 3,
        "drops": [],
    }


class ScriptedCombat:
    init_hp_values = []
    actions = []
    outcomes = []

    def __init__(self, player, enemy, skills_data=None):
        self.player = player
        self.enemy = enemy
        self.is_over = False
        self.winner = None
        self.outcome = self.outcomes.pop(0)
        self.init_hp_values.append(player["current_hp"])

    def step(self, player_action=None):
        self.actions.append(player_action)
        self.is_over = True
        self.winner = self.outcome["winner"]
        self.player["current_hp"] = self.outcome["player_hp"]


def setup_scripted_combat(monkeypatch, outcomes):
    ScriptedCombat.init_hp_values = []
    ScriptedCombat.actions = []
    ScriptedCombat.outcomes = list(outcomes)
    monkeypatch.setattr("systems.instance.CombatSystem", ScriptedCombat)


def test_instance_returns_marked_result_with_death_enemy(monkeypatch):
    setup_scripted_combat(monkeypatch, [{"winner": "enemy", "player_hp": 0}])

    result = run_instant_instance(
        make_player(),
        "test_zone",
        {"test_zone": make_zone()},
        {"test_enemy": make_enemy_template()},
        {},
    )

    assert result["is_instance_result"] is True
    assert result["death_enemy"] == "Test Enemy"
    assert result["combats_won"] >= 0


def test_instance_cumulates_exp_and_gold(monkeypatch):
    setup_scripted_combat(
        monkeypatch,
        [
            {"winner": "player", "player_hp": 5},
            {"winner": "player", "player_hp": 1},
            {"winner": "enemy", "player_hp": 0},
        ],
    )

    result = run_instant_instance(
        make_player(),
        "test_zone",
        {"test_zone": make_zone()},
        {"test_enemy": make_enemy_template()},
        {},
    )

    assert result["combats_won"] == 2
    assert result["exp_gained"] >= 10
    assert result["gold_gained"] >= 6


def test_instance_merges_stackables_and_keeps_individual_equipment(monkeypatch):
    setup_scripted_combat(
        monkeypatch,
        [
            {"winner": "player", "player_hp": 5},
            {"winner": "player", "player_hp": 1},
            {"winner": "enemy", "player_hp": 0},
        ],
    )
    drops_by_fight = [
        [
            {"kind": "stackable", "item": "bone", "quantity": 1},
            {"kind": "individual", "item": "iron_sword", "rarity": "common"},
        ],
        [
            {"kind": "stackable", "item": "bone", "quantity": 2},
            {"kind": "individual", "item": "iron_sword", "rarity": "rare"},
        ],
    ]

    def fake_loot(_enemy, _items, _player):
        return drops_by_fight.pop(0)

    monkeypatch.setattr("systems.instance.generate_combat_loot", fake_loot)

    result = run_instant_instance(
        make_player(),
        "test_zone",
        {"test_zone": make_zone()},
        {"test_enemy": make_enemy_template()},
        {},
    )

    stackables = [drop for drop in result["drops"] if drop.get("kind") == "stackable"]
    individuals = [drop for drop in result["drops"] if drop.get("kind") == "individual"]
    assert stackables == [{"kind": "stackable", "item": "bone", "quantity": 3}]
    assert len(individuals) == 2
    assert {drop["rarity"] for drop in individuals} == {"common", "rare"}


def test_player_does_not_recover_hp_between_instance_combats(monkeypatch):
    setup_scripted_combat(
        monkeypatch,
        [
            {"winner": "player", "player_hp": 4},
            {"winner": "enemy", "player_hp": 0},
        ],
    )

    run_instant_instance(
        make_player(),
        "test_zone",
        {"test_zone": make_zone()},
        {"test_enemy": make_enemy_template()},
        {},
    )

    assert ScriptedCombat.init_hp_values == [10, 4]


def test_instance_uses_combat_auto_action(monkeypatch):
    setup_scripted_combat(monkeypatch, [{"winner": "enemy", "player_hp": 0}])

    run_instant_instance(
        make_player(),
        "test_zone",
        {"test_zone": make_zone()},
        {"test_enemy": make_enemy_template()},
        {},
    )

    assert ScriptedCombat.actions == [None]


def test_player_auto_action_no_longer_uses_heal():
    player = make_player()
    player["current_hp"] = 1
    enemy = {
        "current_hp": 1,
        "max_hp": 1,
        "attack": 1,
        "defense": 0,
    }
    combat = CombatSystem(player, enemy)

    assert combat._player_auto_action() == "attack"


def test_heal_action_is_treated_as_attack(monkeypatch):
    monkeypatch.setattr("systems.combat.random.random", lambda: 0.5)
    player = make_player()
    player["current_hp"] = 1
    player["healing_power"] = 20
    enemy = {
        "current_hp": 1,
        "max_hp": 1,
        "attack": 1,
        "defense": 0,
    }
    combat = CombatSystem(player, enemy)

    combat.step("heal")

    assert player["current_hp"] == 1
    assert enemy["current_hp"] == 0
