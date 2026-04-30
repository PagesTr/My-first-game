from copy import deepcopy

from systems.inventory import add_stackable_item, add_unique_item


def _is_valid_inventory(inventory):
    return (
        isinstance(inventory, dict)
        and isinstance(inventory.get("slots"), list)
        and isinstance(inventory.get("size"), int)
        and len(inventory["slots"]) == inventory["size"]
    )


def _count_stackable_item(inventory, item_id):
    total = 0
    for slot in inventory["slots"]:
        if (
            slot is not None
            and slot.get("kind") == "stackable"
            and slot.get("item") == item_id
        ):
            total += slot.get("quantity", 0)
    return total


def _count_unique_item(inventory, item_id):
    total = 0
    for slot in inventory["slots"]:
        if (
            slot is not None
            and slot.get("kind") == "unique"
            and slot.get("item") == item_id
        ):
            total += 1
    return total


def _consume_stackable_item(inventory, item_id, quantity):
    remaining = quantity
    for index, slot in enumerate(inventory["slots"]):
        if (
            slot is None
            or slot.get("kind") != "stackable"
            or slot.get("item") != item_id
        ):
            continue

        consumed = min(slot.get("quantity", 0), remaining)
        slot["quantity"] -= consumed
        remaining -= consumed

        if slot["quantity"] <= 0:
            inventory["slots"][index] = None
        if remaining == 0:
            return True

    return False


def _consume_unique_item(inventory, item_id, quantity):
    remaining = quantity
    for index, slot in enumerate(inventory["slots"]):
        if (
            slot is not None
            and slot.get("kind") == "unique"
            and slot.get("item") == item_id
        ):
            inventory["slots"][index] = None
            remaining -= 1
            if remaining == 0:
                return True

    return False


def _is_unique_result(item_id, items):
    item_data = items.get(item_id, {})
    return (
        item_data.get("type") == "equipment"
        and item_data.get("category") in {"weapon", "armor", "accessory"}
    )


def can_craft(inventory, recipe):
    """Check if the inventory has enough ingredients to craft a recipe."""
    if not _is_valid_inventory(inventory):
        return False

    for ingredient in recipe.get("ingredients", []):
        item_id = ingredient.get("item")
        quantity = ingredient.get("quantity", 0)
        kind = ingredient.get("kind")

        if kind == "stackable":
            if _count_stackable_item(inventory, item_id) < quantity:
                return False
        elif kind == "unique":
            if _count_unique_item(inventory, item_id) < quantity:
                return False
        else:
            return False

    return True


def craft_item(inventory, recipe, items):
    """Consume recipe ingredients and add the crafted result to inventory."""
    if not can_craft(inventory, recipe):
        return False

    updated_inventory = deepcopy(inventory)

    for ingredient in recipe.get("ingredients", []):
        item_id = ingredient["item"]
        quantity = ingredient["quantity"]
        kind = ingredient["kind"]

        if kind == "stackable":
            consumed = _consume_stackable_item(updated_inventory, item_id, quantity)
        else:
            consumed = _consume_unique_item(updated_inventory, item_id, quantity)

        if not consumed:
            return False

    result = recipe.get("result", {})
    result_item_id = result.get("item")
    result_quantity = result.get("quantity", 0)

    if _is_unique_result(result_item_id, items):
        added = add_unique_item(updated_inventory, {"item": result_item_id})
    else:
        added = add_stackable_item(updated_inventory, result_item_id, result_quantity)

    if not added:
        return False

    inventory["slots"] = updated_inventory["slots"]
    return True
