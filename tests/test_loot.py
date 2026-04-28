from systems.loot import generate_combat_loot


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


def test_generated_stats_are_between_base_value_and_base_plus_two():
    items = {"iron_sword": {"type": "weapon", "stats": {"attack": 3}}}

    drops = generate_combat_loot(make_enemy_with_drop("iron_sword"), items)

    assert 3 <= drops[0]["stats"]["attack"] <= 5


def test_enemy_without_drops_returns_empty_list():
    assert generate_combat_loot({}, {}) == []
