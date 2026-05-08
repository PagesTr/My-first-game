from entities.players import create_player
from systems.equipment import equip_item
from systems.inventory import create_inventory
from systems.loot import get_default_item_kind, get_item_kind


def make_classes():
    return {
        "warrior": {
            "base_stats": {
                "force": 2,
                "agility": 1,
                "intelligence": 0,
            }
        }
    }


def make_items():
    return {
        "helmet": {"type": "equipment", "category": "helmet", "stats": {"defense": 1}},
        "pants": {"type": "equipment", "category": "pants", "stats": {"defense": 1}},
        "armor": {"type": "equipment", "category": "armor", "stats": {"defense": 2}},
        "ring_a": {"type": "equipment", "category": "ring", "stats": {"attack": 1}},
        "ring_b": {"type": "equipment", "category": "ring", "stats": {"attack": 2}},
        "ring_c": {"type": "equipment", "category": "ring", "stats": {"attack": 3}},
        "ring_d": {"type": "equipment", "category": "ring", "stats": {"attack": 4}},
        "boots": {"type": "equipment", "category": "boots", "stats": {"defense": 1}},
    }


def make_player():
    return {
        "class": "warrior",
        "equipment": {
            "weapon": None,
            "helmet": None,
            "chest": None,
            "pants": None,
            "gloves": None,
            "boots": None,
            "amulet": None,
            "ring_1": None,
            "ring_2": None,
            "ring_3": None,
            "trinket": None,
        },
    }


def put_item(inventory, slot_index, item_id):
    item = {"kind": "individual", "item": item_id, "stats": {}}
    inventory["slots"][slot_index] = item
    return item


def test_create_player_initializes_all_equipment_slots_to_none():
    player = create_player("warrior", make_classes(), make_items())

    assert player["equipment"] == {
        "weapon": None,
        "helmet": None,
        "chest": None,
        "pants": None,
        "gloves": None,
        "boots": None,
        "amulet": None,
        "ring_1": None,
        "ring_2": None,
        "ring_3": None,
        "trinket": None,
    }


def test_helmet_item_equips_to_helmet_slot():
    player = make_player()
    inventory = create_inventory(size=2)
    helmet = put_item(inventory, 0, "helmet")

    assert equip_item(player, inventory, 0, make_items()) is True
    assert player["equipment"]["helmet"] == helmet


def test_pants_item_equips_to_pants_slot():
    player = make_player()
    inventory = create_inventory(size=2)
    pants = put_item(inventory, 0, "pants")

    assert equip_item(player, inventory, 0, make_items()) is True
    assert player["equipment"]["pants"] == pants


def test_armor_category_equips_to_chest_slot_for_compatibility():
    player = make_player()
    inventory = create_inventory(size=2)
    armor = put_item(inventory, 0, "armor")

    assert equip_item(player, inventory, 0, make_items()) is True
    assert player["equipment"]["chest"] == armor


def test_ring_equips_to_ring_1_when_ring_slots_are_empty():
    player = make_player()
    inventory = create_inventory(size=2)
    ring = put_item(inventory, 0, "ring_a")

    assert equip_item(player, inventory, 0, make_items()) is True
    assert player["equipment"]["ring_1"] == ring


def test_three_rings_fill_all_ring_slots():
    player = make_player()
    inventory = create_inventory(size=4)
    rings = [
        put_item(inventory, 0, "ring_a"),
        put_item(inventory, 1, "ring_b"),
        put_item(inventory, 2, "ring_c"),
    ]

    for index in range(3):
        assert equip_item(player, inventory, index, make_items()) is True

    assert player["equipment"]["ring_1"] == rings[0]
    assert player["equipment"]["ring_2"] == rings[1]
    assert player["equipment"]["ring_3"] == rings[2]


def test_fourth_ring_replaces_ring_1_and_returns_old_ring_to_inventory():
    player = make_player()
    inventory = create_inventory(size=5)
    first_ring = put_item(inventory, 0, "ring_a")
    put_item(inventory, 1, "ring_b")
    put_item(inventory, 2, "ring_c")
    fourth_ring = put_item(inventory, 3, "ring_d")

    for index in range(3):
        assert equip_item(player, inventory, index, make_items()) is True

    assert equip_item(player, inventory, 3, make_items()) is True
    assert player["equipment"]["ring_1"] == fourth_ring
    assert first_ring in inventory["slots"]


def test_new_equipment_category_is_individual_by_default():
    item_data = {"type": "equipment", "category": "boots"}

    assert get_default_item_kind(item_data) == "individual"
    assert get_item_kind(item_data) == "individual"
