from systems.stats import derive_stats


def make_warrior_class():
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


def test_derive_stats_uses_new_primary_stats():
    player = {
        "class": "warrior",
        "equipment": {},
    }
    classes = make_warrior_class()
    items = {}

    stats = derive_stats(player, items, classes)

    assert stats["strength"] == 4
    assert stats["dexterity"] == 1
    assert stats["vitality"] == 4
    assert stats["wisdom"] == 1
    assert stats["luck"] == 0
    assert stats["max_hp"] > 20
    assert stats["attack"] > 5
    assert stats["defense"] >= 2
    assert stats["hp"] == stats["max_hp"]


def test_derive_stats_applies_equipped_item_stats():
    player = {
        "class": "warrior",
        "equipment": {
            "weapon": {
                "item": "test_sword",
                "stats": {
                    "strength": 2,
                    "attack": 5,
                    "crit_chance": 0.10,
                },
            }
        },
    }
    classes = make_warrior_class()
    items = {}

    stats = derive_stats(player, items, classes)

    assert stats["strength"] == 6
    assert stats["attack"] >= 10
    assert stats["crit_chance"] >= 0.10


def test_derive_stats_supports_legacy_force_and_agility():
    player = {
        "class": "warrior",
        "equipment": {},
    }
    classes = {
        "warrior": {
            "base_stats": {
                "force": 3,
                "agility": 2,
                "intelligence": 1,
            }
        }
    }
    items = {}

    stats = derive_stats(player, items, classes)

    assert stats["strength"] == 3
    assert stats["dexterity"] == 2
    assert stats["intelligence"] == 1
