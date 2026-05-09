import systems.gathering as gathering
from systems.gathering import (
    gather_from_zone,
    generate_gathering_rewards,
    get_gathering_node,
    get_profession_xp_gain,
)
from systems.inventory import create_inventory


PROFESSIONS_DATA = {
    "prospector": {
        "primary_stat": "strength",
        "mastery_bonus_stat": "prospector_mastery",
        "xp_bonus_stat": "prospector_xp_bonus",
    },
    "druid": {
        "primary_stat": "intelligence",
        "mastery_bonus_stat": "druid_mastery",
        "xp_bonus_stat": "druid_xp_bonus",
    },
}

GATHERING_NODES = {
    "forest_goblin": {
        "druid": {
            "name": "Forest Herbs",
            "description": "Useful herbs grow between goblin trails.",
            "xp": 4,
            "rewards": [
                {
                    "item": "healing_herb",
                    "chance": 1.0,
                    "min_quantity": 1,
                    "max_quantity": 1,
                }
            ],
        }
    }
}


def make_player():
    return {
        "intelligence": 0,
        "strength": 0,
        "professions": {
            "druid": {"level": 1, "xp": 0, "next_xp": 20},
            "prospector": {"level": 1, "xp": 0, "next_xp": 20},
        },
    }


def test_get_gathering_node_returns_existing_node():
    node = get_gathering_node(GATHERING_NODES, "forest_goblin", "druid")

    assert node["name"] == "Forest Herbs"


def test_get_gathering_node_returns_none_for_unknown_node():
    assert get_gathering_node(GATHERING_NODES, "town", "druid") is None
    assert get_gathering_node(GATHERING_NODES, "forest_goblin", "prospector") is None


def test_generate_gathering_rewards_returns_guaranteed_reward(monkeypatch):
    node = {
        "rewards": [
            {
                "item": "healing_herb",
                "chance": 1.0,
                "min_quantity": 2,
                "max_quantity": 2,
            }
        ]
    }
    monkeypatch.setattr(gathering.random, "random", lambda: 1.0)
    monkeypatch.setattr(gathering.random, "randint", lambda minimum, maximum: minimum)

    rewards = generate_gathering_rewards(node, mastery=0)

    assert rewards == [{"kind": "stackable", "item": "healing_herb", "quantity": 2}]


def test_generate_gathering_rewards_ignores_zero_chance_reward(monkeypatch):
    node = {
        "rewards": [
            {
                "item": "rough_gem",
                "chance": 0,
                "min_quantity": 1,
                "max_quantity": 1,
            }
        ]
    }
    monkeypatch.setattr(gathering.random, "random", lambda: 1.0)

    assert generate_gathering_rewards(node, mastery=0) == []


def test_mastery_increases_rare_reward_chance(monkeypatch):
    node = {
        "rewards": [
            {
                "item": "rough_gem",
                "chance": 0.2,
                "min_quantity": 1,
                "max_quantity": 1,
                "is_rare": True,
            }
        ]
    }
    monkeypatch.setattr(gathering.random, "randint", lambda minimum, maximum: minimum)
    rolls = iter([0.21, 0.21, 1.0])
    monkeypatch.setattr(gathering.random, "random", lambda: next(rolls))

    assert generate_gathering_rewards(node, mastery=0) == []
    assert generate_gathering_rewards(node, mastery=1) == [
        {"kind": "stackable", "item": "rough_gem", "quantity": 1}
    ]


def test_gather_from_zone_adds_rewards_to_inventory(monkeypatch):
    player = make_player()
    inventory = create_inventory(size=2)
    monkeypatch.setattr(gathering.random, "random", lambda: 1.0)
    monkeypatch.setattr(gathering.random, "randint", lambda minimum, maximum: minimum)

    result = gather_from_zone(
        player,
        inventory,
        "forest_goblin",
        "druid",
        GATHERING_NODES,
        PROFESSIONS_DATA,
        {},
    )

    assert result["gathered"] is True
    assert inventory["slots"][0] == {
        "kind": "stackable",
        "item": "healing_herb",
        "quantity": 1,
    }


def test_gather_from_zone_returns_unknown_node_for_invalid_zone_or_profession():
    player = make_player()
    inventory = create_inventory(size=2)

    invalid_zone = gather_from_zone(
        player,
        inventory,
        "town",
        "druid",
        GATHERING_NODES,
        PROFESSIONS_DATA,
        {},
    )
    invalid_profession = gather_from_zone(
        player,
        inventory,
        "forest_goblin",
        "prospector",
        GATHERING_NODES,
        PROFESSIONS_DATA,
        {},
    )

    assert invalid_zone == {"gathered": False, "reason": "unknown_node"}
    assert invalid_profession == {"gathered": False, "reason": "unknown_node"}


def test_gather_from_zone_returns_inventory_full_when_nothing_can_be_added(monkeypatch):
    player = make_player()
    inventory = create_inventory(size=1)
    inventory["slots"][0] = {"kind": "stackable", "item": "iron_ore", "quantity": 1}
    monkeypatch.setattr(gathering.random, "random", lambda: 1.0)
    monkeypatch.setattr(gathering.random, "randint", lambda minimum, maximum: minimum)

    result = gather_from_zone(
        player,
        inventory,
        "forest_goblin",
        "druid",
        GATHERING_NODES,
        PROFESSIONS_DATA,
        {},
    )

    assert result == {"gathered": False, "reason": "inventory_full"}


def test_gather_from_zone_adds_profession_xp_when_rewards_are_added(monkeypatch):
    player = make_player()
    inventory = create_inventory(size=2)
    monkeypatch.setattr(gathering.random, "random", lambda: 1.0)
    monkeypatch.setattr(gathering.random, "randint", lambda minimum, maximum: minimum)

    result = gather_from_zone(
        player,
        inventory,
        "forest_goblin",
        "druid",
        GATHERING_NODES,
        PROFESSIONS_DATA,
        {},
    )

    assert result["profession_xp"] == 4
    assert player["professions"]["druid"]["xp"] == 4


def test_profession_xp_bonus_affects_xp_gain():
    player = {"druid_xp_bonus": 0.5}
    node = {"xp": 10}

    xp = get_profession_xp_gain(player, "druid", node, PROFESSIONS_DATA)

    assert xp == 15


def test_mastery_does_not_affect_xp_gain():
    node = {"xp": 10}
    low_mastery_player = {"intelligence": 0}
    high_mastery_player = {"intelligence": 100, "gathering_mastery": 100}

    low_xp = get_profession_xp_gain(low_mastery_player, "druid", node, PROFESSIONS_DATA)
    high_xp = get_profession_xp_gain(high_mastery_player, "druid", node, PROFESSIONS_DATA)

    assert low_xp == 10
    assert high_xp == 10
