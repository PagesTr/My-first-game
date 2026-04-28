from systems.inventory import find_first_empty_slot, is_valid_slot


EQUIPMENT_TYPES = ("weapon", "armor", "accessory")


def get_equipment_slot(item_data):
    item_type = item_data.get("type")
    if item_type in EQUIPMENT_TYPES:
        return item_type
    return None


def can_equip_item(item_instance, items):
    if item_instance is None:
        return False
    if item_instance.get("kind") != "unique":
        return False

    item_data = items.get(item_instance.get("item"))
    if not item_data:
        return False

    return get_equipment_slot(item_data) is not None


def equip_item(player, inventory, slot_index, items):
    if not is_valid_slot(inventory, slot_index):
        return False

    slots = inventory["slots"]
    item_instance = slots[slot_index]
    if not can_equip_item(item_instance, items):
        return False

    item_data = items[item_instance["item"]]
    equipment_slot = get_equipment_slot(item_data)
    current_equipment = player["equipment"].get(equipment_slot)

    slots[slot_index] = None
    player["equipment"][equipment_slot] = item_instance

    if current_equipment is None:
        return True

    empty_slot = find_first_empty_slot(inventory)
    if empty_slot is None:
        player["equipment"][equipment_slot] = current_equipment
        slots[slot_index] = item_instance
        return False

    slots[empty_slot] = current_equipment
    return True
