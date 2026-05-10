import json
from pathlib import Path


FOREST_SET_IDS = {
    "wolf_stalker",
    "goblin_scavenger",
    "forest_remnant",
}

FOREST_SET_ITEM_IDS = {
    "wolf_stalker_boots",
    "wolf_stalker_hood",
    "wolf_stalker_gloves",
    "wolf_fang_charm",
    "scavenger_gloves",
    "scavenger_badge",
    "lucky_goblin_totem",
    "goblin_ritual_amulet",
    "adventurer_relic_ring",
    "bone_signet",
    "rootbound_amulet",
    "forest_remnant_trinket",
}

REQUIRED_FOREST_RECIPE_IDS = {
    "craft_herbal_poultice",
    "craft_wolf_fang_charm",
    "craft_wolf_stalker_gloves",
    "craft_scavenger_badge",
    "craft_lucky_goblin_totem",
    "craft_goblin_ritual_amulet",
    "craft_bone_signet",
    "craft_rootbound_amulet",
    "craft_forest_remnant_trinket",
}

HYBRID_RECIPE_IDS = {
    "craft_wolf_fang_charm",
    "craft_wolf_stalker_gloves",
    "craft_scavenger_badge",
    "craft_rootbound_amulet",
}

FOREST_REMNANT_ITEM_IDS = {
    "adventurer_relic_ring",
    "bone_signet",
    "rootbound_amulet",
    "forest_remnant_trinket",
}

ALLOWED_SET_BONUS_STATS = {
    "strength",
    "dexterity",
    "intelligence",
    "vitality",
    "wisdom",
    "luck",
    "attack",
    "defense",
    "max_hp",
    "crit_chance",
    "crit_damage",
    "dodge_chance",
    "block_chance",
    "initiative",
    "loot_bonus",
    "gold_bonus",
    "xp_bonus",
    "rare_find_bonus",
    "status_resistance",
    "healing_power",
}


def load_json(path):
    data_path = Path(__file__).resolve().parents[1] / path
    with data_path.open(encoding="utf-8") as data_file:
        return json.load(data_file)


def get_forest_recipe_ids(recipes, items):
    recipe_ids = set(REQUIRED_FOREST_RECIPE_IDS)
    if "forest_gatherer_gloves" in items:
        recipe_ids.add("craft_forest_gatherer_gloves")
    return recipe_ids


def recipe_item_ids(recipe):
    return [ingredient["item"] for ingredient in recipe.get("ingredients", [])]


def get_enemy_resource_drop_ids(enemies, items):
    drop_ids = set()
    for enemy in enemies.values():
        for drop in enemy.get("drops", []):
            item_id = drop.get("item")
            if item_id in items and items[item_id].get("type") == "resource":
                drop_ids.add(item_id)
    return drop_ids


def test_forest_sets_exist():
    equipment_sets = load_json("data/equipment_sets.json")

    for set_id in FOREST_SET_IDS:
        assert set_id in equipment_sets


def test_forest_sets_have_progressive_bonuses():
    equipment_sets = load_json("data/equipment_sets.json")

    for set_id in FOREST_SET_IDS:
        bonuses = equipment_sets[set_id].get("bonuses")
        assert isinstance(bonuses, dict)
        assert "2" in bonuses
        for threshold, bonus_stats in bonuses.items():
            assert threshold.isdigit()
            assert isinstance(bonus_stats, dict)
            assert bonus_stats


def test_forest_set_items_reference_existing_sets():
    items = load_json("data/items.json")
    equipment_sets = load_json("data/equipment_sets.json")

    for item_id in FOREST_SET_ITEM_IDS:
        assert item_id in items
        item = items[item_id]
        assert item["type"] == "equipment"
        assert item.get("set_id")
        assert item["set_id"] in equipment_sets


def test_forest_recipes_exist():
    recipes = load_json("data/recipes.json")
    items = load_json("data/items.json")

    for recipe_id in get_forest_recipe_ids(recipes, items):
        assert recipe_id in recipes


def test_forest_recipe_items_exist():
    recipes = load_json("data/recipes.json")
    items = load_json("data/items.json")

    for recipe_id in get_forest_recipe_ids(recipes, items):
        recipe = recipes[recipe_id]
        for ingredient in recipe.get("ingredients", []):
            assert ingredient.get("item") in items
            assert ingredient.get("kind") in {"stackable", "unique"}
            assert isinstance(ingredient.get("quantity"), int)
            assert ingredient["quantity"] > 0
        result = recipe.get("result", {})
        assert result.get("item") in items
        assert isinstance(result.get("quantity"), int)
        assert result["quantity"] > 0


def test_forest_recipes_connect_enemy_and_gathering_resources():
    recipes = load_json("data/recipes.json")
    items = load_json("data/items.json")
    enemies = load_json("data/enemies.json")
    enemy_resource_drop_ids = get_enemy_resource_drop_ids(enemies, items)

    for recipe_id in HYBRID_RECIPE_IDS:
        ingredient_ids = recipe_item_ids(recipes[recipe_id])
        has_enemy_resource = any(item_id in enemy_resource_drop_ids for item_id in ingredient_ids)
        has_gathered_resource = any(
            items[item_id].get("economic_source") == "gathered_resource"
            for item_id in ingredient_ids
        )
        assert has_enemy_resource, recipe_id
        assert has_gathered_resource, recipe_id


def test_forest_remnant_items_use_forest_remnant_set():
    items = load_json("data/items.json")

    for item_id in FOREST_REMNANT_ITEM_IDS:
        assert items[item_id]["set_id"] == "forest_remnant"


def test_no_forest_recipe_result_is_missing_type_or_stats():
    recipes = load_json("data/recipes.json")
    items = load_json("data/items.json")

    for recipe_id in get_forest_recipe_ids(recipes, items):
        result_item = items[recipes[recipe_id]["result"]["item"]]
        assert result_item.get("type")
        if result_item["type"] == "equipment":
            assert isinstance(result_item.get("stats"), dict)
            assert result_item["stats"]
        if result_item["type"] == "consumable":
            assert result_item.get("stats") or result_item.get("effects")


def test_forest_set_bonus_stats_are_known_basic_stats():
    equipment_sets = load_json("data/equipment_sets.json")

    for set_id in FOREST_SET_IDS:
        for bonus_stats in equipment_sets[set_id]["bonuses"].values():
            for stat_name in bonus_stats:
                assert stat_name in ALLOWED_SET_BONUS_STATS
