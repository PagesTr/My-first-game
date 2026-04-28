from systems.inventory import (
    add_drops_to_inventory,
    add_stackable_item,
    add_unique_item,
    create_inventory,
    move_item,
)


def test_create_inventory_with_expected_number_of_slots():
    inventory = create_inventory(size=5)

    assert inventory["size"] == 5
    assert inventory["slots"] == [None, None, None, None, None]


def test_add_stackable_item_uses_empty_slot():
    inventory = create_inventory(size=2)

    added = add_stackable_item(inventory, "leather", 3)

    assert added is True
    assert inventory["slots"][0] == {
        "kind": "stackable",
        "item": "leather",
        "quantity": 3,
    }


def test_identical_stackable_items_stack_in_same_slot():
    inventory = create_inventory(size=2)

    add_stackable_item(inventory, "leather", 1)
    add_stackable_item(inventory, "leather", 2)

    assert inventory["slots"][0]["quantity"] == 3
    assert inventory["slots"][1] is None


def test_add_unique_item_uses_empty_slot():
    inventory = create_inventory(size=2)
    item = {"item": "iron_sword", "stats": {"attack": 4}}

    added = add_unique_item(inventory, item)

    assert added is True
    assert inventory["slots"][0]["kind"] == "unique"
    assert inventory["slots"][0]["item"] == "iron_sword"


def test_identical_unique_items_use_different_slots():
    inventory = create_inventory(size=2)

    add_unique_item(inventory, {"item": "iron_sword", "stats": {"attack": 4}})
    add_unique_item(inventory, {"item": "iron_sword", "stats": {"attack": 5}})

    assert inventory["slots"][0]["item"] == "iron_sword"
    assert inventory["slots"][1]["item"] == "iron_sword"


def test_full_inventory_refuses_new_item():
    inventory = create_inventory(size=1)
    add_stackable_item(inventory, "leather", 1)

    added = add_stackable_item(inventory, "bone", 1)

    assert added is False


def test_move_item_swaps_two_slots():
    inventory = create_inventory(size=2)
    add_stackable_item(inventory, "leather", 1)
    add_stackable_item(inventory, "bone", 1)

    moved = move_item(inventory, 0, 1)

    assert moved is True
    assert inventory["slots"][0]["item"] == "bone"
    assert inventory["slots"][1]["item"] == "leather"


def test_move_item_returns_false_for_invalid_indexes():
    inventory = create_inventory(size=2)

    assert move_item(inventory, -1, 0) is False
    assert move_item(inventory, 0, 2) is False


def test_add_drops_to_inventory_adds_stackable_drop():
    inventory = create_inventory(size=2)
    drops = [{"kind": "stackable", "item": "leather", "quantity": 2}]

    result = add_drops_to_inventory(inventory, drops)

    assert result["added"] == drops
    assert result["failed"] == []
    assert inventory["slots"][0]["quantity"] == 2


def test_add_drops_to_inventory_adds_unique_drop():
    inventory = create_inventory(size=2)
    drops = [{"kind": "unique", "item": "iron_sword", "stats": {"attack": 4}}]

    result = add_drops_to_inventory(inventory, drops)

    assert result["added"] == drops
    assert result["failed"] == []
    assert inventory["slots"][0]["kind"] == "unique"
    assert inventory["slots"][0]["stats"] == {"attack": 4}


def test_add_drops_to_inventory_puts_unknown_kind_in_failed():
    inventory = create_inventory(size=2)
    drops = [{"kind": "unknown", "item": "mystery"}]

    result = add_drops_to_inventory(inventory, drops)

    assert result["added"] == []
    assert result["failed"] == drops
    assert inventory["slots"][0] is None
