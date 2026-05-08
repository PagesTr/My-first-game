from systems.inventory import find_first_empty_slot, is_valid_slot


EQUIPMENT_SLOTS = (
    "weapon",
    "helmet",
    "chest",
    "pants",
    "gloves",
    "boots",
    "amulet",
    "ring_1",
    "ring_2",
    "ring_3",
    "trinket",
)
RING_SLOTS = ("ring_1", "ring_2", "ring_3")
EQUIPMENT_CATEGORIES = (
    "weapon",
    "helmet",
    "chest",
    "armor",
    "pants",
    "gloves",
    "boots",
    "amulet",
    "ring",
    "trinket",
    "accessory",
)
CATEGORY_TO_SLOT = {
    "weapon": "weapon",
    "helmet": "helmet",
    "chest": "chest",
    "armor": "chest",
    "pants": "pants",
    "gloves": "gloves",
    "boots": "boots",
    "amulet": "amulet",
    "trinket": "trinket",
    "accessory": "trinket",
}


def get_equipment_slot(item_data):
    item_type = item_data.get("type")
    if item_type != "equipment":
        if item_type == "ring":
            return RING_SLOTS[0]
        if item_type in CATEGORY_TO_SLOT:
            return CATEGORY_TO_SLOT[item_type]
        return None

    equipment_category = item_data.get("category")
    if equipment_category == "ring":
        return RING_SLOTS[0]
    return CATEGORY_TO_SLOT.get(equipment_category)


def _resolve_equipment_slot(player, item_data):
    item_type = item_data.get("type")
    item_category = item_data.get("category") if item_type == "equipment" else item_type

    if item_category != "ring":
        return get_equipment_slot(item_data)

    equipment = player.get("equipment", {})
    for ring_slot in RING_SLOTS:
        if equipment.get(ring_slot) is None:
            return ring_slot
    return RING_SLOTS[0]


def can_equip_item(item_instance, items):
    if item_instance is None:
        return False
    if item_instance.get("kind") != "individual":
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
    equipment_slot = _resolve_equipment_slot(player, item_data)
    if equipment_slot is None:
        return False

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


def unequip_item(player, inventory, equipment_slot):
    equipment = player.get("equipment")
    if not isinstance(equipment, dict):
        return False
    if equipment_slot not in equipment:
        return False

    item = equipment[equipment_slot]
    if item is None:
        return False

    empty_slot = find_first_empty_slot(inventory)
    if empty_slot is None:
        return False

    inventory["slots"][empty_slot] = item
    equipment[equipment_slot] = None
    return True
