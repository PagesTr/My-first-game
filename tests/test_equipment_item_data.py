from pathlib import Path
import json


PROJECT_ROOT = Path(__file__).resolve().parent.parent
ITEMS_PATH = PROJECT_ROOT / "data" / "items.json"

NEW_EQUIPMENT_ITEMS = (
    "brutal_axe",
    "duelist_blade",
    "iron_helmet",
    "scout_hood",
    "reinforced_chestplate",
    "hunter_vest",
    "traveler_pants",
    "duelist_pants",
    "duelist_gloves",
    "guard_gauntlets",
    "swift_boots",
    "heavy_boots",
    "amulet_of_power",
    "amulet_of_life",
    "amulet_of_wisdom",
    "ring_of_precision",
    "ring_of_luck",
    "ring_of_gold",
    "ring_of_learning",
    "goblin_totem",
    "wolf_fang_charm",
    "bone_talisman",
)

VALID_EQUIPMENT_CATEGORIES = {
    "weapon",
    "helmet",
    "chest",
    "pants",
    "gloves",
    "boots",
    "amulet",
    "ring",
    "trinket",
}

VALID_STATS = {
    "strength",
    "dexterity",
    "intelligence",
    "vitality",
    "wisdom",
    "luck",
    "max_hp",
    "attack",
    "defense",
    "magic_attack",
    "magic_defense",
    "accuracy",
    "dodge_chance",
    "block_chance",
    "crit_chance",
    "crit_damage",
    "initiative",
    "healing_power",
    "status_resistance",
    "loot_bonus",
    "gold_bonus",
    "rare_find_bonus",
    "xp_bonus",
}


def load_items():
    with ITEMS_PATH.open("r", encoding="utf-8") as items_file:
        return json.load(items_file)


def test_new_build_equipment_items_exist():
    items = load_items()

    for item_id in NEW_EQUIPMENT_ITEMS:
        assert item_id in items


def test_new_build_equipment_items_have_valid_type_and_category():
    items = load_items()

    for item_id in NEW_EQUIPMENT_ITEMS:
        item = items[item_id]

        assert item["type"] == "equipment"
        assert item["category"] in VALID_EQUIPMENT_CATEGORIES


def test_new_build_equipment_items_have_valid_stats():
    items = load_items()

    for item_id in NEW_EQUIPMENT_ITEMS:
        stats = items[item_id].get("stats")

        assert isinstance(stats, dict)
        assert stats

        for stat_name in stats:
            assert stat_name in VALID_STATS
