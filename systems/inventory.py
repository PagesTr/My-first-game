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
        item_id = drop["item"]
        quantity = drop.get("quantity", 1)
        if add_stackable_item(inventory, item_id, quantity):
            result["added"].append(drop)
        else:
            result["failed"].append(drop)

    return result


def move_item(inventory, source_index, target_index):
    if not is_valid_slot(inventory, source_index):
        return False
    if not is_valid_slot(inventory, target_index):
        return False

    slots = inventory["slots"]
    slots[source_index], slots[target_index] = slots[target_index], slots[source_index]
    return True
