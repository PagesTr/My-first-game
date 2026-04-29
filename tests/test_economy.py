import json
from pathlib import Path

import pytest

from systems.economy import (
    RARITY_MULTIPLIERS,
    SOURCE_MULTIPLIERS,
    calculate_base_level_value,
    calculate_item_sell_price,
    sell_inventory_item,
)
from systems.inventory import create_inventory


def test_calculate_base_level_value_for_level_one():
    assert calculate_base_level_value(1) == pytest.approx(33)


def test_calculate_base_level_value_for_level_one_hundred():
    assert calculate_base_level_value(100) == pytest.approx(94000, rel=0.02)


def test_common_crafted_level_one_item_is_worth_about_base_value():
    item_data = {
        "level": 1,
        "rarity": "common",
        "economic_source": "crafted_item",
    }

    price = calculate_item_sell_price({}, item_data)

    assert price == pytest.approx(33, abs=1)


def test_common_crafted_level_one_hundred_item_is_worth_about_base_value():
    item_data = {
        "level": 100,
        "rarity": "common",
        "economic_source": "crafted_item",
    }

    price = calculate_item_sell_price({}, item_data)

    assert price == pytest.approx(94000, rel=0.02)


def test_unique_item_is_worth_more_than_equivalent_common_item():
    common_item = {
        "level": 10,
        "rarity": "common",
        "economic_source": "crafted_item",
    }
    unique_item = {
        "level": 10,
        "rarity": "unique",
        "economic_source": "crafted_item",
    }

    common_price = calculate_item_sell_price({}, common_item)
    unique_price = calculate_item_sell_price({}, unique_item)

    assert unique_price > common_price


def test_dropped_item_is_worth_more_than_equivalent_crafted_item():
    crafted_item = {
        "level": 10,
        "rarity": "common",
        "economic_source": "crafted_item",
    }
    dropped_item = {
        "level": 10,
        "rarity": "common",
        "economic_source": "dropped_item",
    }

    crafted_price = calculate_item_sell_price({}, crafted_item)
    dropped_price = calculate_item_sell_price({}, dropped_item)

    assert dropped_price > crafted_price


def test_manual_sell_price_overrides_formula():
    item_data = {
        "manual_sell_price": 12,
        "level": 100,
        "rarity": "unique",
        "economic_source": "dropped_item",
    }

    price = calculate_item_sell_price({}, item_data)

    assert price == 12


def test_manual_sell_price_is_not_changed_by_value_multiplier():
    item_data = {
        "manual_sell_price": 12,
        "value_multiplier": 3.0,
        "level": 100,
        "rarity": "unique",
        "economic_source": "dropped_item",
    }

    price = calculate_item_sell_price({}, item_data)

    assert price == 12


def test_invalid_manual_sell_price_returns_zero():
    assert calculate_item_sell_price({}, {"manual_sell_price": 0}) == 0
    assert calculate_item_sell_price({}, {"manual_sell_price": -1}) == 0
    assert calculate_item_sell_price({}, {"manual_sell_price": 1.5}) == 0


def test_value_multiplier_changes_final_price():
    base_item = {
        "level": 10,
        "rarity": "common",
        "economic_source": "crafted_item",
    }
    multiplied_item = {
        "level": 10,
        "rarity": "common",
        "economic_source": "crafted_item",
        "value_multiplier": 2.0,
    }

    base_price = calculate_item_sell_price({}, base_item)
    multiplied_price = calculate_item_sell_price({}, multiplied_item)

    assert multiplied_price == base_price * 2


def test_item_stats_do_not_change_price():
    item_without_stats = {
        "level": 10,
        "rarity": "common",
        "economic_source": "crafted_item",
    }
    item_with_stats = {
        "level": 10,
        "rarity": "common",
        "economic_source": "crafted_item",
        "stats": {"attack": 999, "defense": 999, "hp": 999},
    }

    price_without_stats = calculate_item_sell_price({}, item_without_stats)
    price_with_stats = calculate_item_sell_price({}, item_with_stats)

    assert price_with_stats == price_without_stats


def test_all_items_have_valid_economic_valuation_fields():
    items_path = Path(__file__).resolve().parents[1] / "data" / "items.json"
    with items_path.open(encoding="utf-8") as items_file:
        items = json.load(items_file)

    for item_id, item_data in items.items():
        has_manual_price = "manual_sell_price" in item_data
        has_formula_fields = all(
            field in item_data
            for field in ("level", "rarity", "economic_source")
        )

        assert has_manual_price or has_formula_fields, item_id
        if "economic_source" in item_data:
            assert item_data["economic_source"] in SOURCE_MULTIPLIERS, item_id
        if "rarity" in item_data:
            assert item_data["rarity"] in RARITY_MULTIPLIERS, item_id


def test_sell_stackable_item_increases_gold_and_decreases_quantity():
    player = {"gold": 10}
    inventory = create_inventory(size=1)
    inventory["slots"][0] = {"kind": "stackable", "item": "leather", "quantity": 2}
    items = {
        "leather": {
            "level": 1,
            "rarity": "common",
            "economic_source": "crafted_item",
        }
    }

    sold = sell_inventory_item(player, inventory, 0, items)

    assert sold is True
    assert player["gold"] == 43
    assert inventory["slots"][0]["quantity"] == 1


def test_sell_last_stackable_item_clears_slot():
    player = {"gold": 0}
    inventory = create_inventory(size=1)
    inventory["slots"][0] = {"kind": "stackable", "item": "leather", "quantity": 1}
    items = {
        "leather": {
            "level": 1,
            "rarity": "common",
            "economic_source": "crafted_item",
        }
    }

    sold = sell_inventory_item(player, inventory, 0, items)

    assert sold is True
    assert inventory["slots"][0] is None


def test_sell_unique_item_clears_slot():
    player = {"gold": 0}
    inventory = create_inventory(size=1)
    inventory["slots"][0] = {"kind": "unique", "item": "iron_sword"}
    items = {
        "iron_sword": {
            "level": 1,
            "rarity": "common",
            "economic_source": "crafted_item",
        }
    }

    sold = sell_inventory_item(player, inventory, 0, items)

    assert sold is True
    assert inventory["slots"][0] is None


def test_sell_unknown_kind_returns_false_without_changing_gold_or_slot():
    player = {"gold": 5}
    inventory = create_inventory(size=1)
    slot = {"kind": "unknown", "item": "mystery_item"}
    inventory["slots"][0] = slot
    items = {
        "mystery_item": {
            "level": 1,
            "rarity": "common",
            "economic_source": "crafted_item",
        }
    }

    sold = sell_inventory_item(player, inventory, 0, items)

    assert sold is False
    assert player["gold"] == 5
    assert inventory["slots"][0] is slot


def test_sell_empty_slot_returns_false():
    player = {"gold": 0}
    inventory = create_inventory(size=1)
    items = {"leather": {"level": 1}}

    sold = sell_inventory_item(player, inventory, 0, items)

    assert sold is False
    assert player["gold"] == 0


def test_sell_item_with_invalid_index_returns_false():
    player = {"gold": 0}
    inventory = create_inventory(size=1)
    inventory["slots"][0] = {"kind": "stackable", "item": "leather", "quantity": 1}
    items = {"leather": {"level": 1}}

    assert sell_inventory_item(player, inventory, -1, items) is False
    assert sell_inventory_item(player, inventory, 1, items) is False
    assert player["gold"] == 0
