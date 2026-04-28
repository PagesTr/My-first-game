import json
from pathlib import Path


def load_json(relative_path):
    project_root = Path(__file__).resolve().parent.parent
    with (project_root / relative_path).open("r", encoding="utf-8") as json_file:
        return json.load(json_file)



def test_percentage_item_stats_are_reasonable():
    items = load_json("data/items.json")
    percentage_stats = {
        "accuracy",
        "dodge_chance",
        "block_chance",
        "crit_chance",
        "status_resistance",
        "loot_bonus",
        "gold_bonus",
        "rare_find_bonus",
        "xp_bonus",
    }

    for item_id, item in items.items():
        for stat, value in item.get("stats", {}).items():
            if stat in percentage_stats:
                assert 0 <= value <= 1, f"{item_id}.{stat} should be between 0 and 1"


def test_crit_damage_item_bonus_is_reasonable():
    items = load_json("data/items.json")

    for item_id, item in items.items():
        stats = item.get("stats", {})
        if "crit_damage" in stats:
            assert 0 <= stats["crit_damage"] <= 2, (
                f"{item_id}.crit_damage bonus is too high"
            )


def test_equipment_items_have_non_empty_stats():
    items = load_json("data/items.json")

    for item_id, item in items.items():
        if item.get("type") in ("weapon", "armor", "accessory"):
            assert item.get("stats"), f"{item_id} should have stats"


def test_rarity_weights_are_positive():
    items = load_json("data/items.json")

    for item_id, item in items.items():
        for rarity, weight in item.get("rarity_weights", {}).items():
            assert isinstance(weight, (int, float)), (
                f"{item_id}.{rarity} rarity weight should be positive"
            )
            assert weight > 0, f"{item_id}.{rarity} rarity weight should be positive"
