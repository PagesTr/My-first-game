from core.game import Game
from systems.inventory import (
    build_inventory_item_from_drop,
    claim_all_pending_drops,
    claim_pending_drop,
    move_inventory_slot_to_pending,
    swap_pending_drop_with_inventory_slot,
)


def test_build_inventory_item_from_stackable_drop():
    drop = {"kind": "stackable", "item": "wolf_pelt", "quantity": 2}

    item = build_inventory_item_from_drop(drop)

    assert item["kind"] == "stackable"
    assert item["item"] == "wolf_pelt"
    assert item["quantity"] == 2


def test_build_inventory_item_from_unique_drop_returns_copy():
    drop = {
        "kind": "individual",
        "item": "iron_sword",
        "rarity": "common",
        "stats": {"attack": 3},
    }

    item = build_inventory_item_from_drop(drop)
    item["item"] = "changed"

    assert item["kind"] == "individual"
    assert item["rarity"] == "common"
    assert item["stats"]["attack"] == 3
    assert drop["item"] == "iron_sword"


def test_claim_pending_drop_with_available_inventory_space():
    inventory = {"slots": [None, None], "size": 2}
    drop = {"kind": "stackable", "item": "wolf_pelt", "quantity": 1}
    inventory_result = {"added": [], "failed": [], "pending": [drop]}

    claimed = claim_pending_drop(inventory, inventory_result, 0)

    assert claimed is True
    assert inventory["slots"][0] == drop
    assert inventory_result["pending"] == []
    assert inventory_result["added"] == [drop]
    assert inventory_result["failed"] == []


def test_claim_pending_drop_with_full_inventory_fails_without_modifying_inventory():
    inventory = {
        "slots": [
            {"kind": "individual", "item": "old_sword"},
            {"kind": "individual", "item": "old_helmet"},
        ],
        "size": 2,
    }
    original_slots = [slot.copy() for slot in inventory["slots"]]
    drop = {"kind": "individual", "item": "iron_sword", "rarity": "common"}
    inventory_result = {"added": [], "failed": [], "pending": [drop]}

    claimed = claim_pending_drop(inventory, inventory_result, 0)

    assert claimed is False
    assert inventory["slots"] == original_slots
    assert inventory_result["pending"] == [drop]
    assert inventory_result["failed"] == [drop]


def test_claim_all_pending_drops_with_enough_space():
    inventory = {"slots": [None, None, None], "size": 3}
    drops = [
        {"kind": "stackable", "item": "wolf_pelt", "quantity": 2},
        {"kind": "individual", "item": "iron_sword", "rarity": "common"},
    ]
    inventory_result = {"added": [], "failed": [], "pending": list(drops)}

    claimed = claim_all_pending_drops(inventory, inventory_result)

    assert claimed is True
    assert inventory_result["pending"] == []
    assert inventory_result["added"] == drops
    assert inventory["slots"][0]["item"] == "wolf_pelt"
    assert inventory["slots"][1]["item"] == "iron_sword"


def test_claim_all_pending_drops_when_only_some_fit():
    inventory = {
        "slots": [{"kind": "individual", "item": "old_sword"}, None],
        "size": 2,
    }
    drops = [
        {"kind": "individual", "item": "iron_sword", "rarity": "common"},
        {"kind": "individual", "item": "iron_helmet", "rarity": "common"},
    ]
    inventory_result = {"added": [], "failed": [], "pending": list(drops)}

    claimed = claim_all_pending_drops(inventory, inventory_result)

    assert claimed is False
    assert len(inventory_result["added"]) == 1
    assert len(inventory_result["pending"]) == 1
    assert len(inventory_result["failed"]) == 1


def test_swap_pending_drop_with_inventory_slot_keeps_replaced_item_pending():
    inventory = {
        "slots": [{"kind": "stackable", "item": "old_item", "quantity": 1}],
        "size": 1,
    }
    drop = {
        "kind": "individual",
        "item": "iron_sword",
        "rarity": "common",
        "stats": {"attack": 3},
    }
    inventory_result = {"added": [], "failed": [], "pending": [drop]}

    swapped = swap_pending_drop_with_inventory_slot(inventory, inventory_result, 0, 0)

    assert swapped is True
    assert inventory["slots"][0]["item"] == "iron_sword"
    assert inventory_result["pending"] == [
        {"kind": "stackable", "item": "old_item", "quantity": 1}
    ]
    assert inventory_result["added"] == [drop]


def test_move_inventory_slot_to_pending_moves_item_and_empties_slot():
    item = {"kind": "stackable", "item": "wolf_pelt", "quantity": 2}
    inventory = {"slots": [item], "size": 1}
    inventory_result = {"added": [], "failed": [], "pending": []}

    moved = move_inventory_slot_to_pending(inventory, inventory_result, 0)

    assert moved is True
    assert inventory["slots"][0] is None
    assert inventory_result["pending"] == [item]


def test_move_inventory_slot_to_pending_returns_false_for_empty_slot():
    inventory = {"slots": [None], "size": 1}
    inventory_result = {"added": [], "failed": [], "pending": []}

    moved = move_inventory_slot_to_pending(inventory, inventory_result, 0)

    assert moved is False
    assert inventory_result["pending"] == []


def test_game_discard_pending_combat_loot_moves_pending_to_discarded():
    game = Game()
    drop_1 = {"kind": "stackable", "item": "wolf_pelt", "quantity": 1}
    drop_2 = {"kind": "individual", "item": "iron_sword", "rarity": "common"}
    added = [{"kind": "stackable", "item": "herb", "quantity": 1}]
    game.last_combat_result = {
        "inventory_result": {
            "added": list(added),
            "failed": [],
            "pending": [drop_1, drop_2],
        }
    }

    discarded = game.discard_pending_combat_loot()

    inventory_result = game.last_combat_result["inventory_result"]
    assert discarded is True
    assert inventory_result["pending"] == []
    assert inventory_result["discarded"] == [drop_1, drop_2]
    assert inventory_result["added"] == added
