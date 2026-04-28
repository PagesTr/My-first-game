from systems.inventory import (
    add_drops_to_inventory,
    add_stackable_item,
    add_unique_item,
    compact_inventory,
    create_inventory,
    move_item,
    use_consumable_item,
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


def test_use_consumable_heals_player():
    player = {"current_hp": 5, "max_hp": 20}
    inventory = create_inventory(size=1)
    inventory["slots"][0] = {
        "kind": "stackable",
        "item": "health_potion",
        "quantity": 2,
    }
    items = {"health_potion": {"type": "consumable", "stats": {"hp": 10}}}

    used = use_consumable_item(player, inventory, 0, items)

    assert used is True
    assert player["current_hp"] == 15


def test_use_consumable_does_not_exceed_max_hp():
    player = {"current_hp": 18, "max_hp": 20}
    inventory = create_inventory(size=1)
    inventory["slots"][0] = {
        "kind": "stackable",
        "item": "health_potion",
        "quantity": 2,
    }
    items = {"health_potion": {"type": "consumable", "stats": {"hp": 10}}}

    used = use_consumable_item(player, inventory, 0, items)

    assert used is True
    assert player["current_hp"] == 20


def test_use_consumable_decreases_quantity_after_use():
    player = {"current_hp": 5, "max_hp": 20}
    inventory = create_inventory(size=1)
    inventory["slots"][0] = {
        "kind": "stackable",
        "item": "health_potion",
        "quantity": 2,
    }
    items = {"health_potion": {"type": "consumable", "stats": {"hp": 10}}}

    used = use_consumable_item(player, inventory, 0, items)

    assert used is True
    assert inventory["slots"][0]["quantity"] == 1


def test_use_consumable_clears_slot_when_quantity_reaches_zero():
    player = {"current_hp": 5, "max_hp": 20}
    inventory = create_inventory(size=1)
    inventory["slots"][0] = {
        "kind": "stackable",
        "item": "health_potion",
        "quantity": 1,
    }
    items = {"health_potion": {"type": "consumable", "stats": {"hp": 10}}}

    used = use_consumable_item(player, inventory, 0, items)

    assert used is True
    assert inventory["slots"][0] is None


def test_use_consumable_returns_false_for_non_consumable_item():
    player = {"current_hp": 5, "max_hp": 20}
    inventory = create_inventory(size=1)
    inventory["slots"][0] = {
        "kind": "stackable",
        "item": "leather",
        "quantity": 1,
    }
    items = {"leather": {"type": "resource", "stats": {"value": 5}}}

    used = use_consumable_item(player, inventory, 0, items)

    assert used is False
    assert player["current_hp"] == 5
    assert inventory["slots"][0]["quantity"] == 1


def test_use_consumable_returns_false_for_invalid_slot():
    player = {"current_hp": 5, "max_hp": 20}
    inventory = create_inventory(size=1)
    items = {"health_potion": {"type": "consumable", "stats": {"hp": 10}}}

    assert use_consumable_item(player, inventory, -1, items) is False
    assert use_consumable_item(player, inventory, 1, items) is False


def test_use_consumable_with_effects_adds_temporary_effect_to_player():
    player = {"current_hp": 10, "max_hp": 20, "active_effects": []}
    inventory = create_inventory(size=1)
    inventory["slots"][0] = {
        "kind": "stackable",
        "item": "rage_potion",
        "quantity": 2,
    }
    items = {
        "rage_potion": {
            "type": "consumable",
            "effects": [
                {
                    "id": "rage_test",
                    "name": "Rage",
                    "source": "test",
                    "modifiers": {"attack": 3},
                    "duration_type": "combat",
                    "remaining_combats": 2,
                }
            ],
            "stats": {"value": 20},
        }
    }

    used = use_consumable_item(player, inventory, 0, items)

    assert used is True
    assert len(player["active_effects"]) == 1
    assert player["active_effects"][0]["modifiers"] == {"attack": 3}


def test_use_consumable_with_effects_decreases_quantity_after_use():
    player = {"current_hp": 10, "max_hp": 20, "active_effects": []}
    inventory = create_inventory(size=1)
    inventory["slots"][0] = {
        "kind": "stackable",
        "item": "rage_potion",
        "quantity": 2,
    }
    items = {
        "rage_potion": {
            "type": "consumable",
            "effects": [
                {
                    "modifiers": {"attack": 3},
                    "duration_type": "combat",
                    "remaining_combats": 2,
                }
            ],
        }
    }

    used = use_consumable_item(player, inventory, 0, items)

    assert used is True
    assert inventory["slots"][0]["quantity"] == 1


def test_use_consumable_with_effects_clears_slot_when_quantity_reaches_zero():
    player = {"current_hp": 10, "max_hp": 20, "active_effects": []}
    inventory = create_inventory(size=1)
    inventory["slots"][0] = {
        "kind": "stackable",
        "item": "rage_potion",
        "quantity": 1,
    }
    items = {
        "rage_potion": {
            "type": "consumable",
            "effects": [
                {
                    "modifiers": {"attack": 3},
                    "duration_type": "combat",
                    "remaining_combats": 2,
                }
            ],
        }
    }

    used = use_consumable_item(player, inventory, 0, items)

    assert used is True
    assert inventory["slots"][0] is None


def test_use_consumable_with_invalid_effects_is_not_consumed():
    player = {"current_hp": 10, "max_hp": 20, "active_effects": []}
    inventory = create_inventory(size=1)
    inventory["slots"][0] = {
        "kind": "stackable",
        "item": "broken_potion",
        "quantity": 1,
    }
    items = {
        "broken_potion": {
            "type": "consumable",
            "effects": [
                {
                    "modifiers": {"attack": 3},
                    "duration_type": "combat",
                    "remaining_combats": 0,
                }
            ],
        }
    }

    used = use_consumable_item(player, inventory, 0, items)

    assert used is False
    assert player["active_effects"] == []
    assert inventory["slots"][0]["quantity"] == 1


def test_use_consumable_health_potion_still_heals_player():
    player = {"current_hp": 5, "max_hp": 20, "active_effects": []}
    inventory = create_inventory(size=1)
    inventory["slots"][0] = {
        "kind": "stackable",
        "item": "health_potion",
        "quantity": 1,
    }
    items = {"health_potion": {"type": "consumable", "stats": {"hp": 10}}}

    used = use_consumable_item(player, inventory, 0, items)

    assert used is True
    assert player["current_hp"] == 15


def test_use_consumable_with_heal_and_effect_consumes_if_effect_is_applied():
    player = {"current_hp": 20, "max_hp": 20, "active_effects": []}
    inventory = create_inventory(size=1)
    inventory["slots"][0] = {
        "kind": "stackable",
        "item": "mixed_potion",
        "quantity": 1,
    }
    items = {
        "mixed_potion": {
            "type": "consumable",
            "stats": {"hp": 10},
            "effects": [
                {
                    "modifiers": {"attack": 3},
                    "duration_type": "combat",
                    "remaining_combats": 2,
                }
            ],
        }
    }

    used = use_consumable_item(player, inventory, 0, items)

    assert used is True
    assert player["current_hp"] == 20
    assert len(player["active_effects"]) == 1
    assert inventory["slots"][0] is None


def test_compact_inventory_moves_items_to_front():
    inventory = create_inventory(size=5)
    item_a = {"kind": "stackable", "item": "a", "quantity": 1}
    item_b = {"kind": "stackable", "item": "b", "quantity": 1}
    item_c = {"kind": "stackable", "item": "c", "quantity": 1}
    inventory["slots"] = [item_a, None, item_b, None, item_c]

    compacted = compact_inventory(inventory)

    assert compacted is True
    assert inventory["slots"] == [item_a, item_b, item_c, None, None]


def test_compact_inventory_preserves_relative_order():
    inventory = create_inventory(size=4)
    item_a = {"kind": "stackable", "item": "a", "quantity": 1}
    item_b = {"kind": "stackable", "item": "b", "quantity": 1}
    item_c = {"kind": "stackable", "item": "c", "quantity": 1}
    inventory["slots"] = [None, item_a, item_b, item_c]

    compact_inventory(inventory)

    assert inventory["slots"][:3] == [item_a, item_b, item_c]


def test_compact_inventory_preserves_unique_item_stats():
    inventory = create_inventory(size=3)
    unique_item = {
        "kind": "unique",
        "item": "iron_sword",
        "stats": {"attack": 4, "crit_chance": 0.1},
    }
    inventory["slots"] = [None, unique_item, None]

    compact_inventory(inventory)

    assert inventory["slots"][0] is unique_item
    assert inventory["slots"][0]["stats"] == {"attack": 4, "crit_chance": 0.1}


def test_compact_inventory_preserves_inventory_size():
    inventory = create_inventory(size=4)
    inventory["slots"] = [
        None,
        {"kind": "stackable", "item": "a", "quantity": 1},
        None,
        None,
    ]

    compact_inventory(inventory)

    assert inventory["size"] == 4
    assert len(inventory["slots"]) == 4


def test_compact_inventory_works_with_empty_inventory():
    inventory = create_inventory(size=3)

    compacted = compact_inventory(inventory)

    assert compacted is True
    assert inventory["slots"] == [None, None, None]


def test_compact_inventory_returns_false_for_invalid_inventory():
    assert compact_inventory(None) is False
    assert compact_inventory({}) is False
    assert compact_inventory({"slots": [], "size": 1}) is False
    assert compact_inventory({"slots": None, "size": 1}) is False
