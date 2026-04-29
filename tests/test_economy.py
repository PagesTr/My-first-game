from systems.economy import sell_inventory_item
from systems.inventory import create_inventory


def test_sell_stackable_item_increases_player_gold():
    player = {"gold": 10}
    inventory = create_inventory(size=1)
    inventory["slots"][0] = {"kind": "stackable", "item": "leather", "quantity": 2}
    items = {"leather": {"sell_price": 3}}

    sold = sell_inventory_item(player, inventory, 0, items)

    assert sold is True
    assert player["gold"] == 13


def test_sell_stackable_item_decreases_quantity():
    player = {"gold": 0}
    inventory = create_inventory(size=1)
    inventory["slots"][0] = {"kind": "stackable", "item": "leather", "quantity": 2}
    items = {"leather": {"sell_price": 3}}

    sold = sell_inventory_item(player, inventory, 0, items)

    assert sold is True
    assert inventory["slots"][0]["quantity"] == 1


def test_sell_last_stackable_item_clears_slot():
    player = {"gold": 0}
    inventory = create_inventory(size=1)
    inventory["slots"][0] = {"kind": "stackable", "item": "leather", "quantity": 1}
    items = {"leather": {"sell_price": 3}}

    sold = sell_inventory_item(player, inventory, 0, items)

    assert sold is True
    assert inventory["slots"][0] is None


def test_sell_unique_item_clears_slot():
    player = {"gold": 0}
    inventory = create_inventory(size=1)
    inventory["slots"][0] = {"kind": "unique", "item": "iron_sword"}
    items = {"iron_sword": {"sell_price": 15}}

    sold = sell_inventory_item(player, inventory, 0, items)

    assert sold is True
    assert inventory["slots"][0] is None


def test_sell_empty_slot_returns_false():
    player = {"gold": 0}
    inventory = create_inventory(size=1)
    items = {"leather": {"sell_price": 3}}

    sold = sell_inventory_item(player, inventory, 0, items)

    assert sold is False
    assert player["gold"] == 0


def test_sell_item_without_sell_price_returns_false():
    player = {"gold": 0}
    inventory = create_inventory(size=1)
    inventory["slots"][0] = {"kind": "stackable", "item": "leather", "quantity": 2}
    items = {"leather": {}}

    sold = sell_inventory_item(player, inventory, 0, items)

    assert sold is False
    assert player["gold"] == 0
    assert inventory["slots"][0]["quantity"] == 2


def test_sell_item_with_invalid_index_returns_false():
    player = {"gold": 0}
    inventory = create_inventory(size=1)
    inventory["slots"][0] = {"kind": "stackable", "item": "leather", "quantity": 1}
    items = {"leather": {"sell_price": 3}}

    assert sell_inventory_item(player, inventory, -1, items) is False
    assert sell_inventory_item(player, inventory, 1, items) is False
    assert player["gold"] == 0
