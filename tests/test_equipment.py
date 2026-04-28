from systems.equipment import can_equip_item, equip_item
from systems.inventory import create_inventory
from systems.stats import derive_stats


def make_items():
    return {
        "iron_sword": {"type": "weapon", "stats": {"attack": 3}},
        "leather_armor": {"type": "armor", "stats": {"defense": 2}},
        "magic_ring": {"type": "accessory", "stats": {"intelligence": 1}},
        "leather": {"type": "resource", "stats": {"value": 5}},
        "health_potion": {"type": "consumable", "stats": {"hp": 10}},
    }


def make_player():
    return {
        "class": "warrior",
        "equipment": {
            "weapon": None,
            "armor": None,
            "accessory": None,
        },
    }


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


def test_unique_weapon_is_equipable():
    item = {"kind": "unique", "item": "iron_sword", "stats": {"attack": 4}}

    assert can_equip_item(item, make_items()) is True


def test_unique_armor_is_equipable():
    item = {"kind": "unique", "item": "leather_armor", "stats": {"defense": 3}}

    assert can_equip_item(item, make_items()) is True


def test_stackable_item_is_not_equipable():
    item = {"kind": "stackable", "item": "leather", "quantity": 2}

    assert can_equip_item(item, make_items()) is False


def test_unique_resource_or_consumable_is_not_equipable():
    items = make_items()
    resource = {"kind": "unique", "item": "leather", "stats": {"value": 5}}
    consumable = {"kind": "unique", "item": "health_potion", "stats": {"hp": 10}}

    assert can_equip_item(resource, items) is False
    assert can_equip_item(consumable, items) is False


def test_equip_item_moves_weapon_from_inventory_to_equipment_slot():
    player = make_player()
    inventory = create_inventory(size=2)
    weapon = {"kind": "unique", "item": "iron_sword", "stats": {"attack": 4}}
    inventory["slots"][0] = weapon

    equipped = equip_item(player, inventory, 0, make_items())

    assert equipped is True
    assert player["equipment"]["weapon"] == weapon


def test_inventory_slot_becomes_none_after_equipping():
    player = make_player()
    inventory = create_inventory(size=2)
    inventory["slots"][0] = {
        "kind": "unique",
        "item": "iron_sword",
        "stats": {"attack": 4},
    }

    equip_item(player, inventory, 0, make_items())

    assert inventory["slots"][0] is None


def test_replacing_equipment_puts_old_item_back_in_inventory():
    player = make_player()
    old_weapon = {"kind": "unique", "item": "iron_sword", "stats": {"attack": 3}}
    new_weapon = {"kind": "unique", "item": "iron_sword", "stats": {"attack": 5}}
    player["equipment"]["weapon"] = old_weapon
    inventory = create_inventory(size=2)
    inventory["slots"][0] = new_weapon

    equipped = equip_item(player, inventory, 0, make_items())

    assert equipped is True
    assert player["equipment"]["weapon"] == new_weapon
    assert old_weapon in inventory["slots"]


def test_equip_item_returns_false_with_invalid_index():
    player = make_player()
    inventory = create_inventory(size=1)

    assert equip_item(player, inventory, 3, make_items()) is False


def test_derive_stats_uses_unique_equipment_stats():
    player = make_player()
    player["equipment"]["weapon"] = {
        "kind": "unique",
        "item": "iron_sword",
        "stats": {"attack": 5},
    }

    stats = derive_stats(player, make_items(), make_classes())

    assert stats["attack"] == 12


def test_derive_stats_keeps_compatibility_with_old_equipment_list():
    player = {
        "class": "warrior",
        "equipment": ["iron_sword"],
    }

    stats = derive_stats(player, make_items(), make_classes())

    assert stats["attack"] == 10
