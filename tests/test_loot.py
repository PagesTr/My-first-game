from systems.loot import (
    RARITIES,
    RARITY_WEIGHTS,
    generate_combat_loot,
    generate_randomized_stats,
    generate_rarity,
    get_allowed_rarities,
    get_rarity_weights,
)


def make_enemy_with_drop(item_id):
    return {
        "drops": [
            {
                "item": item_id,
                "chance": 1.0,
            }
        ]
    }


def test_resource_item_generates_stackable_drop():
    items = {"leather": {"type": "resource", "stats": {}}}

    drops = generate_combat_loot(make_enemy_with_drop("leather"), items)

    assert drops[0]["kind"] == "stackable"
    assert drops[0]["item"] == "leather"
    assert drops[0]["quantity"] == 1


def test_currency_item_generates_stackable_drop():
    items = {"gold_coin": {"type": "currency", "stats": {}}}

    drops = generate_combat_loot(make_enemy_with_drop("gold_coin"), items)

    assert drops[0]["kind"] == "stackable"
    assert drops[0]["item"] == "gold_coin"
    assert drops[0]["quantity"] == 1


def test_weapon_item_generates_unique_drop():
    items = {"iron_sword": {"type": "weapon", "stats": {"attack": 3}}}

    drops = generate_combat_loot(make_enemy_with_drop("iron_sword"), items)

    assert drops[0]["kind"] == "unique"
    assert drops[0]["item"] == "iron_sword"


def test_armor_item_generates_unique_drop():
    items = {"leather_armor": {"type": "armor", "stats": {"defense": 2}}}

    drops = generate_combat_loot(make_enemy_with_drop("leather_armor"), items)

    assert drops[0]["kind"] == "unique"
    assert drops[0]["item"] == "leather_armor"


def test_accessory_item_generates_unique_drop():
    items = {"magic_ring": {"type": "accessory", "stats": {"intelligence": 1}}}

    drops = generate_combat_loot(make_enemy_with_drop("magic_ring"), items)

    assert drops[0]["kind"] == "unique"
    assert drops[0]["item"] == "magic_ring"


def test_unique_drop_contains_stats_dict():
    items = {"iron_sword": {"type": "weapon", "stats": {"attack": 3}}}

    drops = generate_combat_loot(make_enemy_with_drop("iron_sword"), items)

    assert isinstance(drops[0]["stats"], dict)


def test_generated_stats_include_rarity_bonus():
    items = {"iron_sword": {"type": "weapon", "stats": {"attack": 3}}}

    drops = generate_combat_loot(make_enemy_with_drop("iron_sword"), items)

    assert 3 <= drops[0]["stats"]["attack"] <= 10


def test_enemy_without_drops_returns_empty_list():
    assert generate_combat_loot({}, {}) == []


def test_unique_drop_contains_rarity():
    items = {"iron_sword": {"type": "weapon", "stats": {"attack": 3}}}

    drops = generate_combat_loot(make_enemy_with_drop("iron_sword"), items)

    assert "rarity" in drops[0]


def test_generated_rarity_is_known():
    items = {"iron_sword": {"type": "weapon", "stats": {"attack": 3}}}

    drops = generate_combat_loot(make_enemy_with_drop("iron_sword"), items)

    assert drops[0]["rarity"] in RARITIES


def test_stackable_drop_does_not_contain_rarity():
    items = {"leather": {"type": "resource", "stats": {}}}

    drops = generate_combat_loot(make_enemy_with_drop("leather"), items)

    assert "rarity" not in drops[0]


def test_rare_randomized_stats_include_rarity_bonus():
    stats = generate_randomized_stats({"attack": 3}, rarity="rare")

    assert 5 <= stats["attack"] <= 7


def test_unique_randomized_stats_include_rarity_bonus():
    stats = generate_randomized_stats({"attack": 3}, rarity="unique")

    assert 8 <= stats["attack"] <= 10


def test_get_allowed_rarities_returns_global_rarities_when_missing():
    item = {"type": "weapon", "stats": {"attack": 3}}

    assert get_allowed_rarities(item) == RARITIES


def test_get_allowed_rarities_filters_unknown_values():
    item = {"type": "weapon", "rarities": ["rare", "invalid", "legendary"]}

    allowed_rarities = get_allowed_rarities(item)

    assert "rare" in allowed_rarities
    assert "legendary" in allowed_rarities
    assert "invalid" not in allowed_rarities


def test_generate_rarity_uses_only_allowed_rarities():
    rarity_weights = {
        "legendary": RARITY_WEIGHTS["legendary"],
        "unique": RARITY_WEIGHTS["unique"],
    }

    generated = {generate_rarity(rarity_weights) for _ in range(50)}

    assert generated <= set(rarity_weights)


def test_unique_drop_uses_item_allowed_rarities():
    items = {
        "legendary_sword": {
            "type": "weapon",
            "stats": {"attack": 10},
            "rarities": ["legendary", "unique"],
        }
    }

    for _ in range(50):
        drops = generate_combat_loot(make_enemy_with_drop("legendary_sword"), items)
        assert drops[0]["rarity"] in ("legendary", "unique")


def test_basic_equipment_can_be_limited_to_common_and_uncommon():
    items = {
        "iron_sword": {
            "type": "weapon",
            "stats": {"attack": 3},
            "rarities": ["common", "uncommon"],
        }
    }

    for _ in range(50):
        drops = generate_combat_loot(make_enemy_with_drop("iron_sword"), items)
        assert drops[0]["rarity"] in ("common", "uncommon")


def test_get_rarity_weights_uses_item_specific_weights():
    item = {"rarity_weights": {"rare": 80, "epic": 20}}

    assert get_rarity_weights(item) == {"rare": 80, "epic": 20}


def test_get_rarity_weights_filters_invalid_entries():
    item = {
        "rarity_weights": {
            "rare": 10,
            "invalid": 99,
            "epic": 0,
            "legendary": -5,
        }
    }

    assert get_rarity_weights(item) == {"rare": 10}


def test_get_rarity_weights_falls_back_to_rarities_pool():
    item = {"rarities": ["legendary", "unique"]}

    assert get_rarity_weights(item) == {
        "legendary": RARITY_WEIGHTS["legendary"],
        "unique": RARITY_WEIGHTS["unique"],
    }


def test_generate_rarity_uses_specific_weights_keys():
    rarity_weights = {"legendary": 90, "unique": 10}

    generated = {generate_rarity(rarity_weights) for _ in range(50)}

    assert generated <= set(rarity_weights)


def test_unique_drop_uses_item_specific_rarity_weights():
    items = {
        "legendary_sword": {
            "type": "weapon",
            "stats": {"attack": 10},
            "rarity_weights": {"legendary": 90, "unique": 10},
        }
    }

    for _ in range(50):
        drops = generate_combat_loot(make_enemy_with_drop("legendary_sword"), items)
        assert drops[0]["rarity"] in ("legendary", "unique")
