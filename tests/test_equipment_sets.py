from systems.equipment_sets import count_equipped_set_pieces, get_active_set_bonuses
from systems.stats import derive_stats


def test_count_equipped_set_pieces_returns_empty_without_equipment():
    assert count_equipped_set_pieces({}, {}) == {}
    assert count_equipped_set_pieces({"equipment": {}}, {}) == {}


def test_count_equipped_set_pieces_counts_known_set_items():
    player = {
        "equipment": {
            "helmet": {"item": "scout_hood"},
            "boots": {"item": "swift_boots"},
        }
    }
    items = {
        "scout_hood": {"set_id": "wolf_stalker"},
        "swift_boots": {"set_id": "wolf_stalker"},
    }

    assert count_equipped_set_pieces(player, items) == {"wolf_stalker": 2}


def test_count_equipped_set_pieces_ignores_items_without_set():
    player = {
        "equipment": {
            "helmet": {"item": "scout_hood"},
            "weapon": {"item": "iron_sword"},
        }
    }
    items = {
        "scout_hood": {"set_id": "wolf_stalker"},
        "iron_sword": {},
    }

    assert count_equipped_set_pieces(player, items) == {"wolf_stalker": 1}


def test_active_set_bonuses_apply_two_piece_bonus():
    player = {
        "equipment": {
            "helmet": {"item": "scout_hood"},
            "boots": {"item": "swift_boots"},
        }
    }
    items = {
        "scout_hood": {"set_id": "wolf_stalker"},
        "swift_boots": {"set_id": "wolf_stalker"},
    }
    equipment_sets = {
        "wolf_stalker": {
            "bonuses": {
                "2": {"dodge_chance": 0.03},
                "4": {"crit_chance": 0.04},
            }
        }
    }

    assert get_active_set_bonuses(player, items, equipment_sets) == {
        "dodge_chance": 0.03
    }


def test_active_set_bonuses_apply_two_and_four_piece_bonuses():
    player = {
        "equipment": {
            "helmet": {"item": "scout_hood"},
            "pants": {"item": "duelist_pants"},
            "boots": {"item": "swift_boots"},
            "trinket": {"item": "wolf_fang_charm"},
        }
    }
    items = {
        "scout_hood": {"set_id": "wolf_stalker"},
        "duelist_pants": {"set_id": "wolf_stalker"},
        "swift_boots": {"set_id": "wolf_stalker"},
        "wolf_fang_charm": {"set_id": "wolf_stalker"},
    }
    equipment_sets = {
        "wolf_stalker": {
            "bonuses": {
                "2": {"dodge_chance": 0.03},
                "4": {"crit_chance": 0.04},
            }
        }
    }

    bonuses = get_active_set_bonuses(player, items, equipment_sets)

    assert bonuses["dodge_chance"] == 0.03
    assert bonuses["crit_chance"] == 0.04


def test_active_set_bonuses_ignore_unknown_set_id():
    player = {"equipment": {"helmet": {"item": "unknown_hood"}}}
    items = {"unknown_hood": {"set_id": "unknown_set"}}

    assert get_active_set_bonuses(player, items, {}) == {}


def test_derive_stats_includes_equipment_set_bonuses(monkeypatch):
    monkeypatch.setattr(
        "systems.equipment_sets.load_equipment_sets",
        lambda: {
            "wolf_stalker": {
                "bonuses": {
                    "2": {
                        "dodge_chance": 0.03,
                    }
                }
            }
        },
    )
    classes = {
        "warrior": {
            "base_stats": {
                "strength": 0,
                "dexterity": 0,
                "intelligence": 0,
                "vitality": 0,
                "wisdom": 0,
                "luck": 0,
            }
        }
    }
    items = {
        "scout_hood": {"set_id": "wolf_stalker"},
        "swift_boots": {"set_id": "wolf_stalker"},
    }
    player = {
        "class": "warrior",
        "equipment": {
            "helmet": {"item": "scout_hood", "stats": {}},
            "boots": {"item": "swift_boots", "stats": {}},
        },
    }

    stats = derive_stats(player, items, classes)

    assert stats["dodge_chance"] >= 0.03
