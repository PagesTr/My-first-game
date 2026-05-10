import json
from pathlib import Path

from systems.crafting import (
    can_craft,
    can_craft_recipe,
    craft_item,
    craft_recipe,
)
from systems.inventory import add_individual_item, add_stackable_item, create_inventory


PROJECT_ROOT = Path(__file__).resolve().parent.parent
RECIPES_PATH = PROJECT_ROOT / "data" / "recipes.json"
ITEMS_PATH = PROJECT_ROOT / "data" / "items.json"
ZONES_PATH = PROJECT_ROOT / "data" / "zones.json"
ENEMIES_PATH = PROJECT_ROOT / "data" / "enemies.json"
VALID_INGREDIENT_KINDS = {"stackable", "individual"}
LEGACY_INGREDIENT_KIND_ALIASES = {"unique": "individual"}
# wolf_fang_charm is still dropped by legacy enemies until the old forest content is migrated.
ALLOWED_CRAFTED_ENEMY_DROP_OVERLAPS = {"bone_talisman", "wolf_fang_charm"}


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


def individual_recipe(item_id="rusty_sword", result_item="restored_sword"):
    return {
        "ingredients": [
            {"kind": "individual", "item": item_id, "quantity": 1}
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
            "rarity": "common",
            "stats": {
                "attack": 2,
            },
        },
        "iron_helmet": {
            "type": "equipment",
            "category": "helmet",
            "rarity": "common",
            "stats": {
                "vitality": 1,
                "defense": 2,
            },
        },
    }


def copy_slots(inventory):
    return [slot.copy() if slot is not None else None for slot in inventory["slots"]]


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
            kind = LEGACY_INGREDIENT_KIND_ALIASES.get(
                ingredient["kind"],
                ingredient["kind"],
            )
            assert kind in VALID_INGREDIENT_KINDS, recipe_id


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


def test_crafted_items_are_not_enemy_drop_items():
    recipes = load_json(RECIPES_PATH)
    enemies = load_json(ENEMIES_PATH)

    crafted_items = {
        recipe["result"]["item"]
        for recipe in recipes.values()
    }

    enemy_drop_items = set()
    for enemy in enemies.values():
        for drop in enemy.get("drops", []):
            enemy_drop_items.add(drop["item"])

    overlapping_items = (
        crafted_items
        & enemy_drop_items
        - ALLOWED_CRAFTED_ENEMY_DROP_OVERLAPS
    )
    assert not overlapping_items, overlapping_items


def test_can_craft_returns_true_when_all_stackable_ingredients_are_available():
    inventory = create_inventory()
    add_stackable_item(inventory, "leather", 2)

    assert can_craft(inventory, stackable_recipe()) is True


def test_can_craft_recipe_with_stackable_ingredients():
    inventory = create_inventory()
    add_stackable_item(inventory, "leather", 2)
    add_stackable_item(inventory, "iron_ore", 3)
    recipe = {
        "ingredients": [
            {"kind": "stackable", "item": "leather", "quantity": 2},
            {"kind": "stackable", "item": "iron_ore", "quantity": 3},
        ],
        "result": {"item": "iron_helmet", "quantity": 1},
    }

    assert can_craft_recipe(inventory, recipe) is True


def test_can_craft_returns_false_when_a_stackable_ingredient_is_missing():
    inventory = create_inventory()
    add_stackable_item(inventory, "leather", 1)

    assert can_craft(inventory, stackable_recipe()) is False


def test_cannot_craft_recipe_when_stackable_ingredient_is_missing():
    inventory = create_inventory()
    add_stackable_item(inventory, "leather", 1)
    recipe = stackable_recipe(item_id="leather", quantity=2)

    assert can_craft_recipe(inventory, recipe) is False


def test_can_craft_returns_true_when_an_individual_ingredient_is_available():
    inventory = create_inventory()
    add_individual_item(inventory, {"item": "rusty_sword"})

    assert can_craft(inventory, individual_recipe()) is True


def test_can_craft_recipe_with_individual_ingredient():
    inventory = create_inventory()
    add_individual_item(inventory, {"item": "rusty_sword"})

    assert can_craft_recipe(inventory, individual_recipe()) is True


def test_unique_ingredient_kind_is_treated_as_individual():
    inventory = create_inventory()
    inventory["slots"][0] = {"kind": "unique", "item": "rusty_sword"}
    recipe = {
        "ingredients": [
            {"kind": "unique", "item": "rusty_sword", "quantity": 1}
        ],
        "result": {"item": "restored_sword", "quantity": 1},
    }

    assert can_craft_recipe(inventory, recipe) is True


def test_can_craft_returns_false_when_an_individual_ingredient_is_missing():
    inventory = create_inventory()

    assert can_craft(inventory, individual_recipe()) is False


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


def test_craft_recipe_consumes_stackable_ingredients():
    inventory = create_inventory()
    add_stackable_item(inventory, "leather", 3)
    recipes = {"test_recipe": stackable_recipe()}

    result = craft_recipe(inventory, recipes, "test_recipe", minimal_items())

    assert result["crafted"] is True
    assert inventory["slots"][0] == {
        "kind": "stackable",
        "item": "leather",
        "quantity": 1,
    }


def test_craft_item_consumes_individual_ingredients():
    inventory = create_inventory()
    add_individual_item(inventory, {"item": "rusty_sword"})

    crafted = craft_item(inventory, individual_recipe(), minimal_items())

    assert crafted is True
    assert all(
        slot is None or slot.get("item") != "rusty_sword"
        for slot in inventory["slots"]
    )


def test_craft_recipe_consumes_individual_ingredient():
    inventory = create_inventory()
    add_individual_item(inventory, {"item": "rusty_sword"})
    recipes = {"test_recipe": individual_recipe()}

    result = craft_recipe(inventory, recipes, "test_recipe", minimal_items())

    assert result["crafted"] is True
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


def test_craft_recipe_adds_stackable_result():
    inventory = create_inventory()
    add_stackable_item(inventory, "goblin_ear", 1)
    add_stackable_item(inventory, "wolf_pelt", 1)
    recipes = load_json(RECIPES_PATH)

    result = craft_recipe(
        inventory,
        recipes,
        "brew_field_dressing",
        load_json(ITEMS_PATH),
    )

    assert result["crafted"] is True
    assert any(
        slot == {"kind": "stackable", "item": "field_dressing", "quantity": 1}
        for slot in inventory["slots"]
    )


def test_craft_item_adds_an_individual_result():
    inventory = create_inventory()
    add_individual_item(inventory, {"item": "rusty_sword"})

    crafted = craft_item(inventory, individual_recipe(), minimal_items())

    assert crafted is True
    assert inventory["slots"][0] == {
        "kind": "individual",
        "item": "restored_sword",
        "rarity": "common",
        "stats": {
            "attack": 2,
        },
    }


def test_craft_recipe_adds_equipment_result_as_individual():
    inventory = create_inventory()
    add_stackable_item(inventory, "iron_ore", 2)
    add_stackable_item(inventory, "bone", 1)
    recipes = load_json(RECIPES_PATH)
    items = load_json(ITEMS_PATH)

    result = craft_recipe(inventory, recipes, "craft_iron_helmet", items)

    assert result["crafted"] is True
    assert any(
        slot == {
            "kind": "individual",
            "item": "iron_helmet",
            "rarity": "common",
            "stats": {
                "vitality": 1,
                "defense": 2,
            },
        }
        for slot in inventory["slots"]
    )


def test_herbal_field_dressing_recipe_uses_gathered_druid_resources():
    inventory = create_inventory()
    add_stackable_item(inventory, "healing_herb", 2)
    add_stackable_item(inventory, "wild_root", 1)
    recipes = load_json(RECIPES_PATH)
    items = load_json(ITEMS_PATH)

    result = craft_recipe(
        inventory,
        recipes,
        "craft_herbal_field_dressing",
        items,
    )

    assert result["crafted"] is True
    assert any(
        slot == {"kind": "stackable", "item": "field_dressing", "quantity": 2}
        for slot in inventory["slots"]
    )
    assert all(
        slot is None or slot.get("item") not in {"healing_herb", "wild_root"}
        for slot in inventory["slots"]
    )


def test_bone_talisman_recipe_uses_archaeology_resources():
    inventory = create_inventory()
    add_stackable_item(inventory, "buried_bones", 2)
    add_stackable_item(inventory, "fossil_fragment", 1)
    recipes = load_json(RECIPES_PATH)
    items = load_json(ITEMS_PATH)

    result = craft_recipe(inventory, recipes, "craft_bone_talisman", items)

    assert result["crafted"] is True
    assert any(
        slot is not None
        and slot.get("kind") == "individual"
        and slot.get("item") == "bone_talisman"
        for slot in inventory["slots"]
    )


def test_ring_of_learning_recipe_uses_fossil_and_rough_gem():
    inventory = create_inventory()
    add_stackable_item(inventory, "fossil_fragment", 2)
    add_stackable_item(inventory, "rough_gem", 1)
    recipes = load_json(RECIPES_PATH)
    items = load_json(ITEMS_PATH)

    result = craft_recipe(
        inventory,
        recipes,
        "craft_ring_of_learning_from_relics",
        items,
    )

    assert result["crafted"] is True
    assert any(
        slot is not None
        and slot.get("kind") == "individual"
        and slot.get("item") == "ring_of_learning"
        for slot in inventory["slots"]
    )


def test_amulet_of_power_recipe_uses_prospecting_resources():
    inventory = create_inventory()
    add_stackable_item(inventory, "iron_ore", 3)
    add_stackable_item(inventory, "rough_gem", 1)
    recipes = load_json(RECIPES_PATH)
    items = load_json(ITEMS_PATH)

    result = craft_recipe(
        inventory,
        recipes,
        "craft_amulet_of_power_from_ore",
        items,
    )

    assert result["crafted"] is True
    assert any(
        slot is not None
        and slot.get("kind") == "individual"
        and slot.get("item") == "amulet_of_power"
        for slot in inventory["slots"]
    )


def test_amulet_of_wisdom_recipe_uses_druid_and_archaeology_resources():
    inventory = create_inventory()
    add_stackable_item(inventory, "wild_root", 2)
    add_stackable_item(inventory, "fossil_fragment", 1)
    recipes = load_json(RECIPES_PATH)
    items = load_json(ITEMS_PATH)

    result = craft_recipe(
        inventory,
        recipes,
        "craft_amulet_of_wisdom_from_roots",
        items,
    )

    assert result["crafted"] is True
    assert any(
        slot is not None
        and slot.get("kind") == "individual"
        and slot.get("item") == "amulet_of_wisdom"
        for slot in inventory["slots"]
    )


def test_craft_item_does_not_modify_inventory_when_ingredients_are_missing():
    inventory = create_inventory()
    add_stackable_item(inventory, "leather", 1)
    original_slots = copy_slots(inventory)

    crafted = craft_item(inventory, stackable_recipe(), minimal_items())

    assert crafted is False
    assert inventory["slots"] == original_slots


def test_crafting_missing_ingredients_does_not_modify_inventory():
    inventory = create_inventory()
    add_stackable_item(inventory, "leather", 1)
    original_slots = copy_slots(inventory)
    recipes = {"test_recipe": stackable_recipe(item_id="leather", quantity=2)}

    result = craft_recipe(inventory, recipes, "test_recipe", minimal_items())

    assert result == {
        "crafted": False,
        "recipe_id": "test_recipe",
        "reason": "missing_ingredients",
    }
    assert inventory["slots"] == original_slots


def test_craft_item_does_not_consume_ingredients_when_the_result_cannot_be_added():
    inventory = create_inventory(size=1)
    add_stackable_item(inventory, "leather", 3)
    original_slots = copy_slots(inventory)
    recipe = stackable_recipe(result_item="restored_sword")

    crafted = craft_item(inventory, recipe, minimal_items())

    assert crafted is False
    assert inventory["slots"] == original_slots


def test_craft_recipe_is_atomic_when_inventory_is_full():
    inventory = create_inventory(size=2)
    add_stackable_item(inventory, "iron_ore", 2)
    add_stackable_item(inventory, "bone", 1)
    original_slots = copy_slots(inventory)
    recipes = load_json(RECIPES_PATH)

    result = craft_recipe(
        inventory,
        recipes,
        "craft_iron_helmet",
        load_json(ITEMS_PATH),
    )

    assert result == {
        "crafted": False,
        "recipe_id": "craft_iron_helmet",
        "reason": "inventory_full",
    }
    assert inventory["slots"] == original_slots


def test_unknown_recipe_returns_failure():
    inventory = create_inventory()

    result = craft_recipe(inventory, {}, "missing_recipe", minimal_items())

    assert result == {
        "crafted": False,
        "recipe_id": "missing_recipe",
        "reason": "unknown_recipe",
    }
