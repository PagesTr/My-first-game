import json
from pathlib import Path


FOREST_ENEMY_IDS = {
    "forest_rat",
    "young_goblin",
    "stray_wolf",
    "goblin_scout",
    "forest_wolf",
    "thorn_sprite",
    "bone_gnawer",
    "lost_adventurer",
    "goblin_shaman",
    "alpha_wolf",
    "rootbound_remnant",
    "grubfang_rootcaller",
}

FOREST_ENEMY_TIERS = {
    "forest_rat": 1,
    "young_goblin": 1,
    "stray_wolf": 1,
    "goblin_scout": 2,
    "forest_wolf": 2,
    "thorn_sprite": 2,
    "bone_gnawer": 3,
    "lost_adventurer": 3,
    "goblin_shaman": 4,
    "alpha_wolf": 4,
    "rootbound_remnant": 5,
    "grubfang_rootcaller": 6,
}

FOREST_GATHERING_ZONE_IDS = {
    "forest_outskirts",
    "forest_deep_trails",
    "forest_buried_paths",
    "forest_ritual_grounds",
}

EXPECTED_FOREST_ZONE_PROFESSIONS = {
    "forest_outskirts": {"druid", "archaeologist"},
    "forest_deep_trails": {"druid"},
    "forest_buried_paths": {"archaeologist", "druid"},
    "forest_ritual_grounds": {"druid", "archaeologist"},
}

EXPECTED_FOREST_ZONE_UNLOCK_LEVELS = {
    "forest_outskirts": 1,
    "forest_deep_trails": 2,
    "forest_buried_paths": 3,
    "forest_ritual_grounds": 4,
}

FOREST_SET_DROP_IDS = {
    "scavenger_gloves",
    "wolf_stalker_boots",
    "forest_gatherer_gloves",
    "adventurer_relic_ring",
    "wolf_stalker_hood",
    "rootbound_amulet",
    "forest_remnant_trinket",
}

FOREST_NEW_ITEM_IDS = {
    "rat_tail",
    "small_fang",
    "torn_cloth",
    "crude_charm",
    "scout_badge",
    "goblin_map_scrap",
    "wolf_fang",
    "wild_heart",
    "thorn_essence",
    "forest_spore",
    "chewed_bone",
    "cracked_skull",
    "old_charm_fragment",
    "broken_adventurer_tag",
    "rusted_ring",
    "shaman_totem",
    "ritual_paint",
    "alpha_fang",
    "rootbound_relic",
    "briar_sap",
    "rootcaller_totem",
    "corrupted_root",
    "forest_core",
    "scavenger_gloves",
    "wolf_stalker_boots",
    "forest_gatherer_gloves",
    "adventurer_relic_ring",
    "wolf_stalker_hood",
    "rootbound_amulet",
    "forest_remnant_trinket",
}

NON_IDENTITY_DROP_IDS = {"minor_health_potion", "health_potion", "leather"}
RARE_RESOURCE_RARITIES = {"rare", "epic", "legendary", "unique"}


def load_json(path):
    data_path = Path(__file__).resolve().parents[1] / path
    with data_path.open(encoding="utf-8") as data_file:
        return json.load(data_file)


def get_enemy_drop_items(enemy):
    return [drop.get("item") for drop in enemy.get("drops", [])]


def test_forest_enemies_exist():
    enemies = load_json("data/enemies.json")

    for enemy_id in FOREST_ENEMY_IDS:
        assert enemy_id in enemies


def test_forest_enemies_have_required_metadata():
    enemies = load_json("data/enemies.json")

    for enemy_id in FOREST_ENEMY_IDS:
        enemy = enemies[enemy_id]
        assert enemy.get("name")
        assert enemy.get("behavior")
        assert {"hp", "attack", "defense"} <= set(enemy.get("stats", {}))
        assert isinstance(enemy.get("exp"), int) and enemy["exp"] > 0
        assert isinstance(enemy.get("gold"), int) and enemy["gold"] >= 0
        assert isinstance(enemy.get("drops"), list) and enemy["drops"]
        assert enemy.get("family")
        assert enemy.get("chapter") == "forest"
        assert isinstance(enemy.get("tier"), int) and enemy["tier"] >= 1
        assert enemy.get("description")


def test_forest_enemy_tiers_are_progressive():
    enemies = load_json("data/enemies.json")

    for enemy_id, expected_tier in FOREST_ENEMY_TIERS.items():
        assert enemies[enemy_id]["tier"] == expected_tier


def test_forest_boss_is_last_tier():
    enemies = load_json("data/enemies.json")
    boss = enemies["grubfang_rootcaller"]
    max_forest_tier = max(enemies[enemy_id]["tier"] for enemy_id in FOREST_ENEMY_IDS)

    assert boss["family"] == "boss"
    assert boss["tier"] == max_forest_tier


def test_forest_enemy_drops_reference_existing_items():
    enemies = load_json("data/enemies.json")
    items = load_json("data/items.json")

    for enemy_id in FOREST_ENEMY_IDS:
        for drop in enemies[enemy_id]["drops"]:
            assert drop.get("item") in items
            assert isinstance(drop.get("chance"), (int, float))
            assert 0 <= drop["chance"] <= 1


def test_forest_enemies_have_specific_drop():
    enemies = load_json("data/enemies.json")

    for enemy_id in FOREST_ENEMY_IDS:
        identity_drops = [
            drop
            for drop in enemies[enemy_id]["drops"]
            if drop.get("item") not in NON_IDENTITY_DROP_IDS
            and drop.get("chance", 0) >= 0.5
        ]
        assert identity_drops, enemy_id


def test_not_every_forest_enemy_has_rare_drop():
    enemies = load_json("data/enemies.json")
    items = load_json("data/items.json")
    enemies_without_rare_resource = 0

    for enemy_id in FOREST_ENEMY_IDS:
        rare_resource_drops = [
            item_id
            for item_id in get_enemy_drop_items(enemies[enemy_id])
            if items[item_id]["type"] == "resource"
            and items[item_id]["rarity"] in RARE_RESOURCE_RARITIES
        ]
        if not rare_resource_drops:
            enemies_without_rare_resource += 1

    assert enemies_without_rare_resource >= 3


def test_forest_rare_resource_drops_are_selective():
    enemies = load_json("data/enemies.json")
    items = load_json("data/items.json")
    enemies_with_rare_resource = 0
    enemies_without_rare_resource = 0

    for enemy_id in FOREST_ENEMY_IDS:
        rare_resource_drops = [
            item_id
            for item_id in get_enemy_drop_items(enemies[enemy_id])
            if items[item_id]["type"] == "resource"
            and items[item_id]["rarity"] in RARE_RESOURCE_RARITIES
        ]
        if rare_resource_drops:
            enemies_with_rare_resource += 1
        else:
            enemies_without_rare_resource += 1

    assert enemies_with_rare_resource >= 3
    assert enemies_without_rare_resource >= 3


def test_forest_set_direct_drops_are_selective():
    enemies = load_json("data/enemies.json")
    items = load_json("data/items.json")
    dropped_items = {
        item_id
        for enemy_id in FOREST_ENEMY_IDS
        for item_id in get_enemy_drop_items(enemies[enemy_id])
    }

    for item_id in FOREST_SET_DROP_IDS:
        assert item_id in items
        assert item_id in dropped_items

    enemies_without_set_drop = 0
    for enemy_id in FOREST_ENEMY_IDS:
        has_set_drop = any(
            items[item_id].get("type") == "equipment" and items[item_id].get("set_id")
            for item_id in get_enemy_drop_items(enemies[enemy_id])
        )
        if not has_set_drop:
            enemies_without_set_drop += 1

    assert enemies_without_set_drop >= 4


def test_forest_direct_set_drops_are_not_on_every_enemy():
    enemies = load_json("data/enemies.json")
    items = load_json("data/items.json")
    enemies_without_set_drop = 0

    for enemy_id in FOREST_ENEMY_IDS:
        has_set_drop = any(
            items[item_id].get("type") == "equipment" and items[item_id].get("set_id")
            for item_id in get_enemy_drop_items(enemies[enemy_id])
        )
        if not has_set_drop:
            enemies_without_set_drop += 1

    assert enemies_without_set_drop >= 4


def test_legacy_forest_enemies_are_still_present():
    enemies = load_json("data/enemies.json")

    assert "goblin" in enemies
    assert "wolf" in enemies


def test_new_forest_zones_exist():
    zones = load_json("data/zones.json")

    for zone_id in FOREST_GATHERING_ZONE_IDS:
        assert zone_id in zones


def test_new_forest_zones_use_new_forest_enemies():
    zones = load_json("data/zones.json")
    enemies = load_json("data/enemies.json")
    legacy_enemy_ids = {"goblin", "wolf"}

    for zone_id in FOREST_GATHERING_ZONE_IDS:
        enemy_pool = zones[zone_id].get("enemy_pool", [])
        assert enemy_pool
        for enemy_id in enemy_pool:
            assert enemy_id in enemies
            assert enemy_id in FOREST_ENEMY_IDS
            assert enemy_id not in legacy_enemy_ids
            assert enemies[enemy_id].get("chapter") == "forest"


def test_new_forest_zone_loot_tables_reference_existing_items():
    zones = load_json("data/zones.json")
    items = load_json("data/items.json")

    for zone_id in FOREST_GATHERING_ZONE_IDS:
        loot_table = zones[zone_id].get("loot_table", [])
        assert loot_table
        for item_id in loot_table:
            assert item_id in items


def test_new_forest_zone_unlock_levels_are_progressive():
    zones = load_json("data/zones.json")
    unlock_levels = {
        zone_id: zones[zone_id]["unlock_level"]
        for zone_id in EXPECTED_FOREST_ZONE_UNLOCK_LEVELS
    }

    assert unlock_levels["forest_outskirts"] == 1
    assert unlock_levels["forest_deep_trails"] >= unlock_levels["forest_outskirts"]
    assert unlock_levels["forest_buried_paths"] >= unlock_levels["forest_deep_trails"]
    assert unlock_levels["forest_ritual_grounds"] >= unlock_levels["forest_buried_paths"]


def test_new_forest_zones_have_matching_gathering_nodes_when_expected():
    gathering_nodes = load_json("data/gathering_nodes.json")

    for zone_id, expected_professions in EXPECTED_FOREST_ZONE_PROFESSIONS.items():
        assert zone_id in gathering_nodes
        assert set(gathering_nodes[zone_id]) == expected_professions


def test_legacy_forest_zones_do_not_block_new_forest_content():
    zones = load_json("data/zones.json")

    # Legacy forest zones are tolerated until full migration cleanup.
    assert FOREST_GATHERING_ZONE_IDS <= set(zones)


def test_forest_gathering_nodes_exist():
    gathering_nodes = load_json("data/gathering_nodes.json")

    for zone_id in FOREST_GATHERING_ZONE_IDS:
        assert zone_id in gathering_nodes


def test_forest_gathering_rewards_are_gathered_resources():
    gathering_nodes = load_json("data/gathering_nodes.json")
    items = load_json("data/items.json")

    for zone_id in FOREST_GATHERING_ZONE_IDS:
        for node_data in gathering_nodes[zone_id].values():
            for reward in node_data.get("rewards", []):
                item = items[reward["item"]]
                assert item["type"] == "resource"
                assert item["economic_source"] == "gathered_resource"


def test_forest_gathering_tick_seconds_are_in_expected_ranges():
    gathering_nodes = load_json("data/gathering_nodes.json")
    expected_ranges = {
        "druid": (3, 6),
        "archaeologist": (10, 15),
        "prospector": (6, 10),
    }

    for zone_id in FOREST_GATHERING_ZONE_IDS:
        for profession_id, node_data in gathering_nodes[zone_id].items():
            minimum, maximum = expected_ranges[profession_id]
            assert minimum <= node_data["tick_seconds"] <= maximum


def test_forest_new_items_have_valid_categories_and_sources():
    items = load_json("data/items.json")

    for item_id in FOREST_NEW_ITEM_IDS:
        item = items[item_id]
        assert item.get("name")
        assert item.get("type")
        assert item.get("category")
        assert item.get("economic_source")
        assert item.get("rarity")


def test_boss_has_boss_family_and_forest_core_drop():
    enemies = load_json("data/enemies.json")
    items = load_json("data/items.json")
    boss = enemies["grubfang_rootcaller"]
    boss_drops = set(get_enemy_drop_items(boss))

    assert boss["family"] == "boss"
    assert "rootcaller_totem" in boss_drops
    assert "forest_core" in boss_drops
    assert items["forest_core"]["rarity"] in RARE_RESOURCE_RARITIES
