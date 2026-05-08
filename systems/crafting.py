from copy import deepcopy

from systems.inventory import (
    add_individual_item,
    add_stackable_item,
    find_first_empty_slot,
)


def _is_valid_inventory(inventory):
    return (
        isinstance(inventory, dict)
        and isinstance(inventory.get("slots"), list)
        and isinstance(inventory.get("size"), int)
        and len(inventory["slots"]) == inventory["size"]
    )


def _get_ingredient_kind(ingredient):
    if not isinstance(ingredient, dict):
        return None

    kind = ingredient.get("kind")
    if kind == "unique":
        return "individual"
    return kind


def get_recipe(recipes, recipe_id):
    if not isinstance(recipes, dict):
        return None
    recipe = recipes.get(recipe_id)
    if not isinstance(recipe, dict):
        return None
    return recipe


def count_stackable_item(inventory, item_id):
    if not _is_valid_inventory(inventory):
        return 0

    total = 0
    for slot in inventory["slots"]:
        if not isinstance(slot, dict):
            continue
        if slot.get("kind") != "stackable" or slot.get("item") != item_id:
            continue

        quantity = slot.get("quantity", 0)
        if isinstance(quantity, int):
            total += quantity

    return total


def count_individual_item(inventory, item_id):
    if not _is_valid_inventory(inventory):
        return 0

    total = 0
    for slot in inventory["slots"]:
        if not isinstance(slot, dict):
            continue
        if slot.get("kind") not in {"individual", "unique"}:
            continue
        if slot.get("item") == item_id:
            total += 1

    return total


def has_ingredient(inventory, ingredient):
    if not isinstance(ingredient, dict):
        return False

    kind = _get_ingredient_kind(ingredient)
    item_id = ingredient.get("item")
    quantity = ingredient.get("quantity")
    if not item_id or not isinstance(quantity, int) or quantity <= 0:
        return False

    if kind == "stackable":
        return count_stackable_item(inventory, item_id) >= quantity
    if kind == "individual":
        return count_individual_item(inventory, item_id) >= quantity
    return False


def can_craft_recipe(inventory, recipe):
    if not _is_valid_inventory(inventory) or not isinstance(recipe, dict):
        return False

    ingredients = recipe.get("ingredients")
    if not isinstance(ingredients, list) or not ingredients:
        return False

    return all(has_ingredient(inventory, ingredient) for ingredient in ingredients)


def _consume_stackable_item(inventory, item_id, quantity):
    if count_stackable_item(inventory, item_id) < quantity:
        return False

    remaining = quantity
    for index, slot in enumerate(inventory["slots"]):
        if not isinstance(slot, dict):
            continue
        if slot.get("kind") != "stackable" or slot.get("item") != item_id:
            continue

        slot_quantity = slot.get("quantity", 0)
        if not isinstance(slot_quantity, int) or slot_quantity <= 0:
            continue

        consumed = min(slot_quantity, remaining)
        slot["quantity"] -= consumed
        remaining -= consumed

        if slot["quantity"] <= 0:
            inventory["slots"][index] = None
        if remaining == 0:
            return True

    return False


def _consume_individual_item(inventory, item_id, quantity):
    if count_individual_item(inventory, item_id) < quantity:
        return False

    remaining = quantity
    for index, slot in enumerate(inventory["slots"]):
        if not isinstance(slot, dict):
            continue
        if slot.get("kind") not in {"individual", "unique"}:
            continue
        if slot.get("item") != item_id:
            continue

        inventory["slots"][index] = None
        remaining -= 1
        if remaining == 0:
            return True

    return False


def consume_ingredients(inventory, recipe):
    if not can_craft_recipe(inventory, recipe):
        return False

    for ingredient in recipe["ingredients"]:
        item_id = ingredient["item"]
        quantity = ingredient["quantity"]
        kind = _get_ingredient_kind(ingredient)

        if kind == "stackable":
            consumed = _consume_stackable_item(inventory, item_id, quantity)
        else:
            consumed = _consume_individual_item(inventory, item_id, quantity)

        if not consumed:
            return False

    return True


def build_crafted_item_instance(result, items):
    if not isinstance(result, dict) or not isinstance(items, dict):
        return None

    item_id = result.get("item")
    quantity = result.get("quantity", 1)
    if not item_id or not isinstance(quantity, int) or quantity <= 0:
        return None

    item_data = items.get(item_id)
    if not isinstance(item_data, dict):
        return None

    if item_data.get("type") == "equipment":
        return {
            "kind": "individual",
            "item": item_id,
            "rarity": item_data.get("rarity", "common"),
            "stats": deepcopy(item_data.get("stats", {})),
        }

    return {
        "kind": "stackable",
        "item": item_id,
        "quantity": quantity,
    }


def can_add_craft_result(inventory, result, items):
    if not _is_valid_inventory(inventory):
        return False

    item_instance = build_crafted_item_instance(result, items)
    if item_instance is None:
        return False

    if item_instance["kind"] == "stackable":
        for slot in inventory["slots"]:
            if not isinstance(slot, dict):
                continue
            if slot.get("kind") == "stackable" and slot.get("item") == item_instance["item"]:
                return True
        return find_first_empty_slot(inventory) is not None

    return find_first_empty_slot(inventory) is not None


def add_craft_result(inventory, result, items):
    item_instance = build_crafted_item_instance(result, items)
    if item_instance is None:
        return False

    if item_instance["kind"] == "stackable":
        return add_stackable_item(
            inventory,
            item_instance["item"],
            item_instance["quantity"],
        )

    return add_individual_item(inventory, item_instance)


def craft_recipe(inventory, recipes, recipe_id, items):
    recipe = get_recipe(recipes, recipe_id)
    if recipe is None:
        return {
            "crafted": False,
            "recipe_id": recipe_id,
            "reason": "unknown_recipe",
        }

    result = recipe.get("result")
    if not isinstance(result, dict) or build_crafted_item_instance(result, items) is None:
        return {
            "crafted": False,
            "recipe_id": recipe_id,
            "reason": "invalid_recipe",
        }

    if not can_craft_recipe(inventory, recipe):
        return {
            "crafted": False,
            "recipe_id": recipe_id,
            "reason": "missing_ingredients",
        }

    if not can_add_craft_result(inventory, result, items):
        return {
            "crafted": False,
            "recipe_id": recipe_id,
            "reason": "inventory_full",
        }

    if not consume_ingredients(inventory, recipe):
        return {
            "crafted": False,
            "recipe_id": recipe_id,
            "reason": "missing_ingredients",
        }

    if not add_craft_result(inventory, result, items):
        return {
            "crafted": False,
            "recipe_id": recipe_id,
            "reason": "inventory_full",
        }

    return {
        "crafted": True,
        "recipe_id": recipe_id,
        "result": result,
    }


def can_craft(inventory, recipe):
    return can_craft_recipe(inventory, recipe)


def craft_item(inventory, recipe, items):
    recipes = {"legacy_recipe": recipe}
    result = craft_recipe(inventory, recipes, "legacy_recipe", items)
    return result["crafted"] is True
