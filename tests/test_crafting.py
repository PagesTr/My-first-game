import json
from pathlib import Path

from systems.crafting import can_craft, craft_item
from systems.inventory import add_stackable_item, add_unique_item, create_inventory


PROJECT_ROOT = Path(__file__).resolve().parent.parent
RECIPES_PATH = PROJECT_ROOT / "data" / "recipes.json"
ITEMS_PATH = PROJECT_ROOT / "data" / "items.json"
ZONES_PATH = PROJECT_ROOT / "data" / "zones.json"
VALID_INGREDIENT_KINDS = {"stackable", "unique"}


def load_json(path):
    with path.open("r", encoding="utf-8") as json_file:
        return json.load(json_file)


def stackable_recipe(item_id="leather", quantity=2, result_item="field_dressing"):
    return {
        "ingredients": [
            {"kind": "stackable", "item": item_id, "quantity": quantity}
        ],
        "result": {"item": result_item, "quantity": 1},
    }


def unique_recipe(item_id="rusty_sword", result_item="restored_sword"):
    return {
        "ingredients": [
            {"kind": "unique", "item": item_id, "quantity": 1}
        ],
        "result": {"item": result_item, "quantity": 1},
    }


def minimal_items():
    return {
        "field_dressing": {
            "type": "consumable",
            "category": "potion",
        },
        "restored_sword": {
            "type": "equipment",
            "category": "weapon",
        },
    }


def test_recipes_file_exists():
    assert RECIPES_PATH.exists()


def test_recipes_file_contains_at_least_one_recipe():
    recipes = load_json(RECIPES_PATH)

    assert recipes


def test_each_recipe_has_ingredients_and_result():
    recipes = load_json(RECIPES_PATH)

    for recipe_id, recipe in recipes.items():
        assert "ingredients" in recipe, recipe_id
        assert "result" in recipe, recipe_id


def test_recipe_ingredients_are_non_empty_lists():
    recipes = load_json(RECIPES_PATH)

    for recipe_id, recipe in recipes.items():
        assert isinstance(recipe["ingredients"], list), recipe_id
        assert recipe["ingredients"], recipe_id


def test_each_ingredient_has_required_fields():
    recipes = load_json(RECIPES_PATH)

    for recipe_id, recipe in recipes.items():
        for ingredient in recipe["ingredients"]:
            assert "kind" in ingredient, recipe_id
            assert "item" in ingredient, recipe_id
            assert "quantity" in ingredient, recipe_id


def test_ingredient_kind_is_valid():
    recipes = load_json(RECIPES_PATH)

    for recipe_id, recipe in recipes.items():
        for ingredient in recipe["ingredients"]:
            assert ingredient["kind"] in VALID_INGREDIENT_KINDS, recipe_id


def test_ingredient_quantity_is_positive_integer():
    recipes = load_json(RECIPES_PATH)

    for recipe_id, recipe in recipes.items():
        for ingredient in recipe["ingredients"]:
            assert isinstance(ingredient["quantity"], int), recipe_id
            assert ingredient["quantity"] > 0, recipe_id


def test_recipe_result_is_an_object():
    recipes = load_json(RECIPES_PATH)

    for recipe_id, recipe in recipes.items():
        assert isinstance(recipe["result"], dict), recipe_id


def test_recipe_result_has_required_fields():
    recipes = load_json(RECIPES_PATH)

    for recipe_id, recipe in recipes.items():
        assert "item" in recipe["result"], recipe_id
        assert "quantity" in recipe["result"], recipe_id


def test_recipe_result_quantity_is_positive_integer():
    recipes = load_json(RECIPES_PATH)

    for recipe_id, recipe in recipes.items():
        assert isinstance(recipe["result"]["quantity"], int), recipe_id
        assert recipe["result"]["quantity"] > 0, recipe_id


def test_all_ingredient_items_exist_in_items_data():
    recipes = load_json(RECIPES_PATH)
    items = load_json(ITEMS_PATH)

    for recipe_id, recipe in recipes.items():
        for ingredient in recipe["ingredients"]:
            assert ingredient["item"] in items, recipe_id


def test_all_result_items_exist_in_items_data():
    recipes = load_json(RECIPES_PATH)
    items = load_json(ITEMS_PATH)

    for recipe_id, recipe in recipes.items():
        assert recipe["result"]["item"] in items, recipe_id


def test_crafted_items_are_not_zone_loot_items():
    recipes = load_json(RECIPES_PATH)
    zones = load_json(ZONES_PATH)

    crafted_items = {
        recipe["result"]["item"]
        for recipe in recipes.values()
    }

    zone_loot_items = set()
    for zone in zones.values():
        zone_loot_items.update(zone.get("loot_table", []))

    overlapping_items = crafted_items & zone_loot_items
    assert not overlapping_items, overlapping_items


def test_can_craft_returns_true_when_all_stackable_ingredients_are_available():
    inventory = create_inventory()
    add_stackable_item(inventory, "leather", 2)

    assert can_craft(inventory, stackable_recipe()) is True


def test_can_craft_returns_false_when_a_stackable_ingredient_is_missing():
    inventory = create_inventory()
    add_stackable_item(inventory, "leather", 1)

    assert can_craft(inventory, stackable_recipe()) is False


def test_can_craft_returns_true_when_a_unique_ingredient_is_available():
    inventory = create_inventory()
    add_unique_item(inventory, {"item": "rusty_sword"})

    assert can_craft(inventory, unique_recipe()) is True


def test_can_craft_returns_false_when_a_unique_ingredient_is_missing():
    inventory = create_inventory()

    assert can_craft(inventory, unique_recipe()) is False


def test_craft_item_consumes_stackable_ingredients():
    inventory = create_inventory()
    add_stackable_item(inventory, "leather", 3)

    crafted = craft_item(inventory, stackable_recipe(), minimal_items())

    assert crafted is True
    assert inventory["slots"][0] == {
        "kind": "stackable",
        "item": "leather",
        "quantity": 1,
    }


def test_craft_item_consumes_unique_ingredients():
    inventory = create_inventory()
    add_unique_item(inventory, {"item": "rusty_sword"})

    crafted = craft_item(inventory, unique_recipe(), minimal_items())

    assert crafted is True
    assert all(
        slot is None or slot.get("item") != "rusty_sword"
        for slot in inventory["slots"]
    )


def test_craft_item_adds_a_stackable_result():
    inventory = create_inventory()
    add_stackable_item(inventory, "leather", 2)

    crafted = craft_item(inventory, stackable_recipe(), minimal_items())

    assert crafted is True
    assert inventory["slots"][0] == {
        "kind": "stackable",
        "item": "field_dressing",
        "quantity": 1,
    }


def test_craft_item_adds_a_unique_result():
    inventory = create_inventory()
    add_unique_item(inventory, {"item": "rusty_sword"})

    crafted = craft_item(inventory, unique_recipe(), minimal_items())

    assert crafted is True
    assert inventory["slots"][0] == {
        "kind": "unique",
        "item": "restored_sword",
    }


def test_craft_item_does_not_modify_inventory_when_ingredients_are_missing():
    inventory = create_inventory()
    add_stackable_item(inventory, "leather", 1)
    original_slots = [slot.copy() if slot is not None else None for slot in inventory["slots"]]

    crafted = craft_item(inventory, stackable_recipe(), minimal_items())

    assert crafted is False
    assert inventory["slots"] == original_slots


def test_craft_item_does_not_consume_ingredients_when_the_result_cannot_be_added():
    inventory = create_inventory(size=1)
    add_stackable_item(inventory, "leather", 3)
    original_slots = [slot.copy() if slot is not None else None for slot in inventory["slots"]]
    recipe = stackable_recipe(result_item="restored_sword")

    crafted = craft_item(inventory, recipe, minimal_items())

    assert crafted is False
    assert inventory["slots"] == original_slots
