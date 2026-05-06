from systems.loot import (
    RARITIES,
    RARITY_WEIGHTS,
    apply_rare_find_bonus,
    generate_combat_loot,
    generate_randomized_stats,
    generate_rarity,
    get_allowed_rarities,
    get_default_item_kind,
    get_item_kind,
    get_rarity_weights,
    roll_drop_count,
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


def make_enemy_with_drop_chance(item_id, chance):
    return {
        "drops": [
            {
                "item": item_id,
                "chance": chance,
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


def test_consumable_item_generates_stackable_drop_by_default():
    items = {"health_potion": {"type": "consumable", "stats": {"hp": 20}}}

    drops = generate_combat_loot(make_enemy_with_drop("health_potion"), items)

    assert drops[0]["kind"] == "stackable"
    assert drops[0]["item"] == "health_potion"
    assert drops[0]["quantity"] == 1


def test_weapon_item_generates_individual_drop():
    items = {"iron_sword": {"type": "weapon", "stats": {"attack": 3}}}

    drops = generate_combat_loot(make_enemy_with_drop("iron_sword"), items)

    assert drops[0]["kind"] == "individual"
    assert drops[0]["item"] == "iron_sword"


def test_equipment_weapon_item_generates_individual_drop():
    items = {
        "iron_sword": {
            "type": "equipment",
            "category": "weapon",
            "stats": {"attack": 3},
        }
    }

    drops = generate_combat_loot(make_enemy_with_drop("iron_sword"), items)

    assert drops[0]["kind"] == "individual"
    assert drops[0]["item"] == "iron_sword"


def test_armor_item_generates_individual_drop():
    items = {"leather_armor": {"type": "armor", "stats": {"defense": 2}}}

    drops = generate_combat_loot(make_enemy_with_drop("leather_armor"), items)

    assert drops[0]["kind"] == "individual"
    assert drops[0]["item"] == "leather_armor"


def test_accessory_item_generates_individual_drop():
    items = {"magic_ring": {"type": "accessory", "stats": {"intelligence": 1}}}

    drops = generate_combat_loot(make_enemy_with_drop("magic_ring"), items)

    assert drops[0]["kind"] == "individual"
    assert drops[0]["item"] == "magic_ring"


def test_resource_with_individual_kind_override_generates_individual_drop():
    items = {
        "ancient_relic": {
            "type": "resource",
            "kind": "individual",
            "stats": {"intelligence": 1},
        }
    }

    drops = generate_combat_loot(make_enemy_with_drop("ancient_relic"), items)

    assert drops[0]["kind"] == "individual"
    assert drops[0]["item"] == "ancient_relic"
    assert "rarity" in drops[0]
    assert "stats" in drops[0]


def test_equipment_with_stackable_kind_override_generates_stackable_drop():
    items = {
        "training_blade": {
            "type": "equipment",
            "category": "weapon",
            "kind": "stackable",
            "stats": {"attack": 1},
        }
    }

    drops = generate_combat_loot(make_enemy_with_drop("training_blade"), items)

    assert drops[0]["kind"] == "stackable"
    assert drops[0]["item"] == "training_blade"
    assert drops[0]["quantity"] == 1
    assert "rarity" not in drops[0]


def test_invalid_kind_falls_back_to_default_item_kind():
    equipment = {
        "type": "equipment",
        "category": "weapon",
        "kind": "invalid",
    }
    resource = {"type": "resource", "kind": "invalid"}

    assert get_item_kind(equipment) == "individual"
    assert get_item_kind(resource) == "stackable"


def test_unique_rarity_is_valid_but_not_a_valid_item_kind():
    item = {"type": "resource", "kind": "unique", "rarities": ["unique"]}

    assert "unique" in RARITIES
    assert get_allowed_rarities(item) == ("unique",)
    assert get_item_kind(item) == "stackable"


def test_default_item_kind_uses_equipment_classification():
    weapon = {"type": "equipment", "category": "weapon"}
    resource = {"type": "resource"}

    assert get_default_item_kind(weapon) == "individual"
    assert get_default_item_kind(resource) == "stackable"


def test_individual_drop_contains_stats_dict():
    items = {"iron_sword": {"type": "weapon", "stats": {"attack": 3}}}

    drops = generate_combat_loot(make_enemy_with_drop("iron_sword"), items)

    assert isinstance(drops[0]["stats"], dict)


def test_generated_stats_include_rarity_bonus():
    items = {"iron_sword": {"type": "weapon", "stats": {"attack": 3}}}

    drops = generate_combat_loot(make_enemy_with_drop("iron_sword"), items)

    assert 3 <= drops[0]["stats"]["attack"] <= 10


def test_enemy_without_drops_returns_empty_list():
    assert generate_combat_loot({}, {}) == []


def test_individual_drop_contains_rarity():
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


def test_roll_drop_count_returns_zero_for_zero_or_negative_chance():
    assert roll_drop_count(0) == 0
    assert roll_drop_count(-1) == 0


def test_roll_drop_count_returns_integer_part_as_guaranteed_count():
    assert roll_drop_count(1.0) == 1
    assert roll_drop_count(2.0) == 2


def test_stackable_drop_uses_drop_count_as_quantity():
    items = {"leather": {"type": "resource", "stats": {}}}

    drops = generate_combat_loot(make_enemy_with_drop_chance("leather", 2.0), items)

    assert len(drops) == 1
    assert drops[0]["kind"] == "stackable"
    assert drops[0]["quantity"] == 2


def test_individual_drop_generates_multiple_instances_when_chance_above_one():
    items = {"iron_sword": {"type": "weapon", "stats": {"attack": 3}}}

    drops = generate_combat_loot(make_enemy_with_drop_chance("iron_sword", 2.0), items)

    assert len(drops) == 2
    for drop in drops:
        assert drop["kind"] == "individual"
        assert drop["item"] == "iron_sword"
        assert "rarity" in drop
        assert "stats" in drop


def test_fractional_chance_above_one_keeps_guaranteed_drop():
    items = {"iron_sword": {"type": "weapon", "stats": {"attack": 3}}}

    for _ in range(50):
        drops = generate_combat_loot(
            make_enemy_with_drop_chance("iron_sword", 1.5),
            items,
        )
        assert 1 <= len(drops) <= 2


def test_apply_rare_find_bonus_improves_high_rarity_weights():
    weights = {
        "common": 60,
        "uncommon": 25,
        "rare": 10,
        "epic": 4,
        "legendary": 1,
        "unique": 0.5,
    }

    adjusted = apply_rare_find_bonus(weights, 0.10)

    assert adjusted is not weights
    assert adjusted["common"] < weights["common"]
    assert adjusted["uncommon"] == weights["uncommon"]
    assert adjusted["rare"] > weights["rare"]
    assert adjusted["epic"] > weights["epic"]
    assert adjusted["legendary"] > weights["legendary"]
    assert adjusted["unique"] > weights["unique"]


def test_apply_rare_find_bonus_returns_copy_without_bonus():
    weights = {
        "common": 60,
        "uncommon": 25,
        "rare": 10,
        "epic": 4,
        "legendary": 1,
        "unique": 0.5,
    }

    adjusted = apply_rare_find_bonus(weights, 0.0)

    assert adjusted == weights
    assert adjusted is not weights


def test_apply_rare_find_bonus_keeps_weights_positive():
    weights = {
        "common": 60,
        "uncommon": 25,
        "rare": 10,
        "epic": 4,
        "legendary": 1,
        "unique": 0.5,
    }

    adjusted = apply_rare_find_bonus(weights, 0.95)

    assert all(weight > 0 for weight in adjusted.values())
