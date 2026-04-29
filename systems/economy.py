def is_valid_inventory(inventory):
    if not isinstance(inventory, dict):
        return False
    if "slots" not in inventory or "size" not in inventory:
        return False
    if not isinstance(inventory["slots"], list):
        return False
    if not isinstance(inventory["size"], int):
        return False
    return len(inventory["slots"]) == inventory["size"]


def sell_inventory_item(player, inventory, slot_index, items):
    if not is_valid_inventory(inventory):
        return False
    if not isinstance(slot_index, int) or slot_index < 0 or slot_index >= inventory["size"]:
        return False

    slot = inventory["slots"][slot_index]
    if slot is None:
        return False

    item_id = slot.get("item")
    item_data = items.get(item_id, {})
    sell_price = item_data.get("sell_price")
    if sell_price is None or sell_price <= 0:
        return False

    player["gold"] += sell_price

    if slot.get("kind") == "stackable":
        slot["quantity"] = slot.get("quantity", 1) - 1
        if slot["quantity"] <= 0:
            inventory["slots"][slot_index] = None
    elif slot.get("kind") == "unique":
        inventory["slots"][slot_index] = None

    return True
