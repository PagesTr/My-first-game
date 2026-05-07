from systems.combat import CombatSystem
from systems.instance import run_instant_instance


def make_player():
    return {
        "class": "warrior",
        "level": 1,
        "exp": 0,
        "next_exp": 100,
        "gold": 0,
        "max_hp": 100,
        "current_hp": 3,
        "attack": 20,
        "defense": 2,
        "accuracy": 1.0,
        "dodge_chance": 0.0,
        "block_chance": 0.0,
        "crit_chance": 0.0,
        "crit_damage": 2.0,
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


def make_items():
    return {
        "bone": {"type": "resource"},
        "iron_sword": {"type": "equipment", "category": "weapon"},
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


class EndlessCombat:
    def __init__(self, player, enemy, skills_data=None):
        self.player = player
        self.enemy = enemy
        self.is_over = False
        self.winner = None

    def step(self, player_action=None):
        return


def setup_scripted_combat(monkeypatch, outcomes):
    ScriptedCombat.init_hp_values = []
    ScriptedCombat.actions = []
    ScriptedCombat.outcomes = list(outcomes)
    monkeypatch.setattr("systems.instance.CombatSystem", ScriptedCombat)


def test_small_instance_can_stay_exact(monkeypatch):
    setup_scripted_combat(
        monkeypatch,
        [
            {"winner": "player", "player_hp": 50},
            {"winner": "enemy", "player_hp": 0},
        ],
    )

    result = run_instant_instance(
        make_player(),
        "test_zone",
        {"test_zone": make_zone()},
        {"test_enemy": make_enemy_template()},
        make_items(),
    )

    assert result["is_instance_result"] is True
    assert result["simulation_mode"] == "exact"
    assert result["end_reason"] == "death"
    assert result["exact_combats"] == 1
    assert result["estimated_combats"] == 0
    assert result["death_enemy"] == "Test Enemy"


def test_large_instance_can_use_batched_simulation(monkeypatch):
    monkeypatch.setattr("systems.instance.EXACT_COMBAT_LIMIT", 1)
    setup_scripted_combat(monkeypatch, [{"winner": "player", "player_hp": 95}])

    result = run_instant_instance(
        make_player(),
        "test_zone",
        {"test_zone": make_zone()},
        {"test_enemy": make_enemy_template()},
        make_items(),
        max_combats=50,
    )

    assert result["simulation_mode"] == "batched"
    assert result["end_reason"] in ("estimated_death", "absolute_limit")
    assert result["exact_combats"] == 1
    assert result["estimated_combats"] > 0
    assert result["combats_won"] == result["exact_combats"] + result["estimated_combats"]


def test_absolute_max_combats_prevents_infinite_loop(monkeypatch):
    monkeypatch.setattr("systems.instance.EXACT_COMBAT_LIMIT", 0)
    monkeypatch.setattr("systems.instance.ABSOLUTE_MAX_COMBATS", 25)
    monkeypatch.setattr("systems.instance._estimate_combat_cost", lambda _player, _enemy: 1)
    player = make_player()
    player["max_hp"] = 1_000

    result = run_instant_instance(
        player,
        "test_zone",
        {"test_zone": make_zone()},
        {"test_enemy": make_enemy_template()},
        make_items(),
        max_combats=1_000_000,
    )

    assert result["end_reason"] == "absolute_limit"
    assert result["combats_won"] == 25


def test_estimated_stackables_are_aggregated(monkeypatch):
    monkeypatch.setattr("systems.instance.EXACT_COMBAT_LIMIT", 0)
    monkeypatch.setattr("systems.instance._estimate_combat_cost", lambda _player, _enemy: 1)
    enemy_template = make_enemy_template()
    enemy_template["drops"] = [{"item": "bone", "chance": 1.0}]
    player = make_player()
    player["max_hp"] = 1_000

    result = run_instant_instance(
        player,
        "test_zone",
        {"test_zone": make_zone()},
        {"test_enemy": enemy_template},
        make_items(),
        max_combats=20,
    )

    stackables = [drop for drop in result["drops"] if drop.get("kind") == "stackable"]
    assert stackables == [{"kind": "stackable", "item": "bone", "quantity": 20}]


def test_estimated_equipment_uses_aggregated_kind(monkeypatch):
    monkeypatch.setattr("systems.instance.EXACT_COMBAT_LIMIT", 0)
    monkeypatch.setattr("systems.instance._estimate_combat_cost", lambda _player, _enemy: 1)
    enemy_template = make_enemy_template()
    enemy_template["drops"] = [{"item": "iron_sword", "chance": 1.0}]
    player = make_player()
    player["max_hp"] = 1_000

    result = run_instant_instance(
        player,
        "test_zone",
        {"test_zone": make_zone()},
        {"test_enemy": enemy_template},
        make_items(),
        max_combats=20,
    )

    estimated_items = [
        drop
        for drop in result["drops"]
        if drop.get("kind") == "estimated_individual_stack"
    ]
    assert estimated_items == [
        {
            "kind": "estimated_individual_stack",
            "item": "iron_sword",
            "rarity": "estimated",
            "quantity": 20,
        }
    ]


def test_exact_drops_keep_individual_equipment(monkeypatch):
    setup_scripted_combat(
        monkeypatch,
        [
            {"winner": "player", "player_hp": 50},
            {"winner": "enemy", "player_hp": 0},
        ],
    )
    drops_by_fight = [
        [
            {"kind": "stackable", "item": "bone", "quantity": 1},
            {"kind": "individual", "item": "iron_sword", "rarity": "common"},
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
        make_items(),
    )

    individuals = [drop for drop in result["drops"] if drop.get("kind") == "individual"]
    assert individuals == [
        {"kind": "individual", "item": "iron_sword", "rarity": "common"}
    ]


def test_player_does_not_recover_hp_between_exact_combats(monkeypatch):
    setup_scripted_combat(
        monkeypatch,
        [
            {"winner": "player", "player_hp": 40},
            {"winner": "enemy", "player_hp": 0},
        ],
    )

    run_instant_instance(
        make_player(),
        "test_zone",
        {"test_zone": make_zone()},
        {"test_enemy": make_enemy_template()},
        make_items(),
    )

    assert ScriptedCombat.init_hp_values == [100, 40]


def test_instance_uses_combat_auto_action(monkeypatch):
    setup_scripted_combat(monkeypatch, [{"winner": "enemy", "player_hp": 0}])

    run_instant_instance(
        make_player(),
        "test_zone",
        {"test_zone": make_zone()},
        {"test_enemy": make_enemy_template()},
        make_items(),
    )

    assert ScriptedCombat.actions == [None]


def test_build_is_frozen_until_instance_rewards_are_applied(monkeypatch):
    created_levels = []

    def fake_create_enemy(template, level):
        created_levels.append(level)
        return {
            "name": template["name"],
            "behavior": "aggressive",
            "level": level,
            "max_hp": 4,
            "current_hp": 4,
            "attack": 1,
            "defense": 0,
            "exp": 100,
            "gold": 3,
            "drops": [],
        }

    monkeypatch.setattr("systems.instance.create_enemy", fake_create_enemy)
    setup_scripted_combat(
        monkeypatch,
        [
            {"winner": "player", "player_hp": 80},
            {"winner": "player", "player_hp": 60},
            {"winner": "enemy", "player_hp": 0},
        ],
    )
    player = make_player()
    player["next_exp"] = 10

    result = run_instant_instance(
        player,
        "test_zone",
        {"test_zone": make_zone()},
        {"test_enemy": make_enemy_template()},
        make_items(),
    )

    assert created_levels == [1, 1, 1]
    assert player["level"] > 1
    assert result["final_player_level"] == player["level"]


def test_xp_and_gold_are_applied_to_player_at_the_end(monkeypatch):
    setup_scripted_combat(
        monkeypatch,
        [
            {"winner": "player", "player_hp": 50},
            {"winner": "enemy", "player_hp": 0},
        ],
    )
    player = make_player()

    result = run_instant_instance(
        player,
        "test_zone",
        {"test_zone": make_zone()},
        {"test_enemy": make_enemy_template()},
        make_items(),
    )

    assert result["exp_gained"] > 0
    assert result["gold_gained"] > 0
    assert player["exp"] == result["exp_gained"]
    assert player["gold"] == result["gold_gained"]


def test_turn_limit_death_ends_exact_combat(monkeypatch):
    monkeypatch.setattr("systems.instance.CombatSystem", EndlessCombat)
    monkeypatch.setattr("systems.instance.MAX_TURNS_PER_EXACT_COMBAT", 2)

    result = run_instant_instance(
        make_player(),
        "test_zone",
        {"test_zone": make_zone()},
        {"test_enemy": make_enemy_template()},
        make_items(),
    )

    assert result["end_reason"] == "turn_limit_death"
    assert result["simulation_mode"] == "exact"


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
