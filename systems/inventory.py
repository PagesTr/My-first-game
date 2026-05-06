from systems.effects import add_temporary_effect


DEFAULT_INVENTORY_SIZE = 30


def create_inventory(size=DEFAULT_INVENTORY_SIZE):
    return {
        "slots": [None] * size,
        "size": size,
    }


def _is_inventory_valid(inventory):
    return (
        isinstance(inventory, dict)
        and isinstance(inventory.get("slots"), list)
        and isinstance(inventory.get("size"), int)
        and len(inventory["slots"]) == inventory["size"]
    )


def is_valid_slot(inventory, index):
    return _is_inventory_valid(inventory) and isinstance(index, int) and 0 <= index < inventory["size"]


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


def build_inventory_item_from_drop(drop):
    if not isinstance(drop, dict) or "item" not in drop:
        return None

    kind = drop.get("kind")
    item_id = drop["item"]
    if kind == "stackable":
        return {
            "kind": "stackable",
            "item": item_id,
            "quantity": drop.get("quantity", 1),
        }

    if kind == "unique":
        item_instance = drop.copy()
        item_instance["kind"] = "unique"
        return item_instance

    return None


def claim_pending_drop(inventory, inventory_result, drop_index):
    if not _is_inventory_valid(inventory):
        return False
    if not isinstance(inventory_result, dict):
        return False

    pending = inventory_result.get("pending")
    if not isinstance(pending, list):
        return False
    if not isinstance(drop_index, int) or drop_index < 0 or drop_index >= len(pending):
        return False

    drop = pending[drop_index]
    kind = drop.get("kind")
    item_id = drop["item"]
    if kind == "stackable":
        added = add_stackable_item(inventory, item_id, drop.get("quantity", 1))
    elif kind == "unique":
        added = add_unique_item(inventory, drop.copy())
    else:
        added = False

    if added:
        claimed_drop = pending.pop(drop_index)
        inventory_result.setdefault("added", []).append(claimed_drop)
        return True

    failed = inventory_result.setdefault("failed", [])
    if drop not in failed:
        failed.append(drop)
    return False


def claim_all_pending_drops(inventory, inventory_result):
    if not _is_inventory_valid(inventory):
        return False
    if not isinstance(inventory_result, dict):
        return False

    pending = inventory_result.get("pending")
    if not isinstance(pending, list):
        return True

    index = 0
    while index < len(pending):
        if claim_pending_drop(inventory, inventory_result, index):
            continue
        index += 1

    return len(pending) == 0


def swap_pending_drop_with_inventory_slot(
    inventory,
    inventory_result,
    drop_index,
    slot_index,
):
    if not _is_inventory_valid(inventory):
        return False
    if not isinstance(inventory_result, dict):
        return False

    pending = inventory_result.get("pending")
    if not isinstance(pending, list):
        return False
    if not isinstance(drop_index, int) or drop_index < 0 or drop_index >= len(pending):
        return False
    if not is_valid_slot(inventory, slot_index):
        return False

    drop = pending[drop_index]
    replacement = build_inventory_item_from_drop(drop)
    if replacement is None:
        return False

    previous_slot = inventory["slots"][slot_index]
    inventory["slots"][slot_index] = replacement
    claimed_drop = pending.pop(drop_index)
    if previous_slot is not None:
        pending.append(previous_slot)
    inventory_result.setdefault("added", []).append(claimed_drop)
    return True


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

    for effect in item_data.get("effects", []):
        if add_temporary_effect(player, effect):
            effect_applied = True

    if not effect_applied:
        return False

    slot["quantity"] = slot.get("quantity", 1) - 1
    if slot["quantity"] <= 0:
        inventory["slots"][slot_index] = None

    return True


def compact_inventory(inventory):
    if not isinstance(inventory, dict):
        return False
    if "slots" not in inventory or "size" not in inventory:
        return False
    if not isinstance(inventory["slots"], list):
        return False
    if not isinstance(inventory["size"], int):
        return False
    if len(inventory["slots"]) != inventory["size"]:
        return False

    compacted_slots = [slot for slot in inventory["slots"] if slot is not None]
    empty_count = inventory["size"] - len(compacted_slots)
    if empty_count < 0:
        return False

    inventory["slots"] = compacted_slots + [None] * empty_count
    return True


def move_item(inventory, source_index, target_index):
    if not is_valid_slot(inventory, source_index):
        return False
    if not is_valid_slot(inventory, target_index):
        return False

    slots = inventory["slots"]
    slots[source_index], slots[target_index] = slots[target_index], slots[source_index]
    return True
