DEFAULT_INVENTORY_SIZE = 30


def create_inventory(size=DEFAULT_INVENTORY_SIZE):
    return {
        "slots": [None] * size,
        "size": size,
    }


def is_valid_slot(inventory, index):
    return isinstance(index, int) and 0 <= index < inventory["size"]


def find_first_empty_slot(inventory):
    for index, slot in enumerate(inventory["slots"]):
        if slot is None:
            return index
    return None


def add_stackable_item(inventory, item_id, quantity=1):
    for slot in inventory["slots"]:
        if (
            slot is not None
            and slot.get("kind") == "stackable"
            and slot.get("item") == item_id
        ):
            slot["quantity"] += quantity
            return True

    empty_index = find_first_empty_slot(inventory)
    if empty_index is None:
        return False

    inventory["slots"][empty_index] = {
        "kind": "stackable",
        "item": item_id,
        "quantity": quantity,
    }
    return True


def add_unique_item(inventory, item_instance):
    empty_index = find_first_empty_slot(inventory)
    if empty_index is None:
        return False

    item_instance["kind"] = "unique"
    inventory["slots"][empty_index] = item_instance
    return True


def add_drops_to_inventory(inventory, drops):
    result = {
        "added": [],
        "failed": [],
    }

    for drop in drops:
        kind = drop.get("kind")
        item_id = drop["item"]
        if kind == "stackable":
            quantity = drop.get("quantity", 1)
            added = add_stackable_item(inventory, item_id, quantity)
        elif kind == "unique":
            added = add_unique_item(inventory, drop.copy())
        else:
            added = False

        if added:
            result["added"].append(drop)
        else:
            result["failed"].append(drop)

    return result


def use_consumable_item(player, inventory, slot_index, items):
    if not is_valid_slot(inventory, slot_index):
        return False

    slot = inventory["slots"][slot_index]
    if slot is None:
        return False

    item_id = slot.get("item")
    item_data = items.get(item_id, {})
    if item_data.get("type") != "consumable":
        return False

    stats = item_data.get("stats", {})
    effect_applied = False

    if "hp" in stats:
        max_hp = player.get("max_hp", 0)
        current_hp = player.get("current_hp", 0)
        healed_hp = min(max_hp, current_hp + stats["hp"])
        if healed_hp > current_hp:
            player["current_hp"] = healed_hp
            effect_applied = True

    if not effect_applied:
        return False

    slot["quantity"] = slot.get("quantity", 1) - 1
    if slot["quantity"] <= 0:
        inventory["slots"][slot_index] = None

    return True


def move_item(inventory, source_index, target_index):
    if not is_valid_slot(inventory, source_index):
        return False
    if not is_valid_slot(inventory, target_index):
        return False

    slots = inventory["slots"]
    slots[source_index], slots[target_index] = slots[target_index], slots[source_index]
    return True
