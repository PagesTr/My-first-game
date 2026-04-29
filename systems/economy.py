RARITY_MULTIPLIERS = {
    "common": 1.00,
    "uncommon": 1.35,
    "rare": 2.00,
    "epic": 3.50,
    "legendary": 6.00,
    "unique": 10.00,
}

SOURCE_MULTIPLIERS = {
    "harvested_resource": 0.30,
    "dropped_resource": 0.35,
    "crafted_item": 1.00,
    "dropped_item": 1.25,
    "consumable": 0.60,
}


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


def calculate_base_level_value(level):
    return 33 * level**1.73


def calculate_item_sell_price(item_instance, item_data):
    manual_sell_price = item_data.get("manual_sell_price")
    if "manual_sell_price" in item_instance:
        manual_sell_price = item_instance["manual_sell_price"]

    value_multiplier = item_data.get("value_multiplier", 1.0)
    if "value_multiplier" in item_instance:
        value_multiplier = item_instance["value_multiplier"]

    if manual_sell_price is not None:
        if not isinstance(manual_sell_price, int) or manual_sell_price <= 0:
            return 0
        return manual_sell_price

    level = item_instance.get("level", item_data.get("level", 1))
    rarity = item_instance.get("rarity", item_data.get("rarity", "common"))
    economic_source = item_instance.get(
        "economic_source",
        item_data.get("economic_source", "dropped_item"),
    )

    base_value = calculate_base_level_value(level)
    rarity_multiplier = RARITY_MULTIPLIERS.get(rarity, RARITY_MULTIPLIERS["common"])
    source_multiplier = SOURCE_MULTIPLIERS.get(
        economic_source,
        SOURCE_MULTIPLIERS["dropped_item"],
    )

    return int(base_value * rarity_multiplier * source_multiplier * value_multiplier)


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
    sell_price = calculate_item_sell_price(slot, item_data)
    if sell_price <= 0:
        return False

    kind = slot.get("kind")
    if kind == "stackable":
        slot["quantity"] = slot.get("quantity", 1) - 1
        if slot["quantity"] <= 0:
            inventory["slots"][slot_index] = None
    elif kind == "unique":
        inventory["slots"][slot_index] = None
    else:
        return False

    player["gold"] = player.get("gold", 0) + sell_price
    return True
