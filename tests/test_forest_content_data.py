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

EXPECTED_FOREST_ENEMY_DROPS = {
    "forest_rat": {"rat_tail"},
    "young_goblin": {"goblin_ear"},
    "stray_wolf": {"wolf_pelt"},
    "goblin_scout": {"scout_badge", "goblin_map_scrap", "scavenger_gloves"},
    "forest_wolf": {"wolf_fang", "wild_heart", "wolf_stalker_boots"},
    "thorn_sprite": {"thorn_essence", "forest_gatherer_gloves"},
    "bone_gnawer": {"chewed_bone", "cracked_skull"},
    "lost_adventurer": {"broken_adventurer_tag", "rusted_ring", "adventurer_relic_ring"},
    "goblin_shaman": {"shaman_totem", "ritual_paint"},
    "alpha_wolf": {"alpha_fang", "wild_heart", "wolf_stalker_hood"},
    "rootbound_remnant": {"rootbound_relic", "briar_sap", "rootbound_amulet"},
    "grubfang_rootcaller": {"rootcaller_totem", "forest_core", "forest_remnant_trinket"},
}

EXPECTED_FOREST_ZONE_ENEMIES = {
    "forest_rat_outskirts": "forest_rat",
    "forest_young_goblin_trail": "young_goblin",
    "forest_stray_wolf_path": "stray_wolf",
    "forest_goblin_scout_trails": "goblin_scout",
    "forest_wolf_hunting_ground": "forest_wolf",
    "forest_thorn_sprite_grove": "thorn_sprite",
    "forest_bone_gnawer_den": "bone_gnawer",
    "forest_lost_adventurer_path": "lost_adventurer",
    "forest_goblin_shaman_grounds": "goblin_shaman",
    "forest_alpha_wolf_lair": "alpha_wolf",
}

FOREST_GATHERING_ZONE_IDS = set(EXPECTED_FOREST_ZONE_ENEMIES)
FOREST_GENERIC_ZONE_IDS = set(EXPECTED_FOREST_ZONE_ENEMIES)

LEGACY_FOREST_ZONE_IDS = {
    "forest_goblin",
    "forest_wolf",
    "forest_outskirts",
    "forest_deep_trails",
    "forest_buried_paths",
    "forest_ritual_grounds",
}

EXPECTED_FOREST_ZONE_PROFESSIONS = {
    "forest_rat_outskirts": {"druid", "archaeologist"},
    "forest_young_goblin_trail": {"druid"},
    "forest_stray_wolf_path": {"druid"},
    "forest_goblin_scout_trails": {"archaeologist"},
    "forest_wolf_hunting_ground": {"druid"},
    "forest_thorn_sprite_grove": {"druid"},
    "forest_bone_gnawer_den": {"archaeologist"},
    "forest_lost_adventurer_path": {"archaeologist"},
    "forest_goblin_shaman_grounds": {"druid", "archaeologist"},
    "forest_alpha_wolf_lair": {"druid"},
}

EXPECTED_FOREST_ZONE_UNLOCK_LEVELS = {
    "forest_rat_outskirts": 1,
    "forest_young_goblin_trail": 1,
    "forest_stray_wolf_path": 1,
    "forest_goblin_scout_trails": 2,
    "forest_wolf_hunting_ground": 2,
    "forest_thorn_sprite_grove": 2,
    "forest_bone_gnawer_den": 3,
    "forest_lost_adventurer_path": 3,
    "forest_goblin_shaman_grounds": 4,
    "forest_alpha_wolf_lair": 4,
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
UNPLANNED_FOREST_DROP_NOISE = {
    "leather",
    "minor_health_potion",
    "health_potion",
    "copper_coin",
    "gold_coin",
    "torn_cloth",
    "old_charm_fragment",
    "buried_bones",
    "healing_herb",
    "forest_spore",
    "wild_root",
}


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


def test_forest_enemy_drops_match_plan_exactly():
    enemies = load_json("data/enemies.json")

    for enemy_id, expected_drops in EXPECTED_FOREST_ENEMY_DROPS.items():
        assert set(get_enemy_drop_items(enemies[enemy_id])) == expected_drops


def test_forest_enemy_drops_do_not_include_unplanned_generic_noise():
    enemies = load_json("data/enemies.json")

    for enemy_id in FOREST_ENEMY_IDS:
        drop_items = set(get_enemy_drop_items(enemies[enemy_id]))
        assert not (drop_items & UNPLANNED_FOREST_DROP_NOISE), enemy_id

    assert "wolf_pelt" not in get_enemy_drop_items(enemies["forest_wolf"])
    assert "goblin_ear" not in get_enemy_drop_items(enemies["goblin_scout"])


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


def test_legacy_forest_enemies_are_removed():
    enemies = load_json("data/enemies.json")

    assert "goblin" not in enemies
    assert "wolf" not in enemies


def test_new_forest_zones_exist():
    zones = load_json("data/zones.json")

    for zone_id in FOREST_GENERIC_ZONE_IDS:
        assert zone_id in zones


def test_new_forest_zones_use_new_forest_enemies():
    zones = load_json("data/zones.json")
    enemies = load_json("data/enemies.json")
    legacy_enemy_ids = {"goblin", "wolf"}

    for zone_id in FOREST_GENERIC_ZONE_IDS:
        enemy_pool = zones[zone_id].get("enemy_pool", [])
        assert enemy_pool
        for enemy_id in enemy_pool:
            assert enemy_id in enemies
            assert enemy_id in FOREST_ENEMY_IDS
            assert enemy_id not in legacy_enemy_ids
            assert enemies[enemy_id].get("chapter") == "forest"


def test_forest_generic_zones_have_single_enemy():
    zones = load_json("data/zones.json")

    for zone_id, expected_enemy_id in EXPECTED_FOREST_ZONE_ENEMIES.items():
        enemy_pool = zones[zone_id].get("enemy_pool")
        assert isinstance(enemy_pool, list)
        assert len(enemy_pool) == 1
        assert enemy_pool[0] == expected_enemy_id


def test_forest_zones_do_not_use_legacy_enemies():
    zones = load_json("data/zones.json")
    legacy_enemy_ids = {"goblin", "wolf"}

    for zone_id in FOREST_GENERIC_ZONE_IDS:
        assert not (set(zones[zone_id].get("enemy_pool", [])) & legacy_enemy_ids)


def test_forest_zones_loot_tables_match_enemy_drops_exactly():
    zones = load_json("data/zones.json")
    enemies = load_json("data/enemies.json")

    for zone_id in FOREST_GENERIC_ZONE_IDS:
        enemy_id = zones[zone_id]["enemy_pool"][0]
        assert set(zones[zone_id]["loot_table"]) == set(get_enemy_drop_items(enemies[enemy_id]))


def test_new_forest_zone_loot_tables_reference_existing_items():
    zones = load_json("data/zones.json")
    items = load_json("data/items.json")

    for zone_id in FOREST_GENERIC_ZONE_IDS:
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

    assert unlock_levels["forest_rat_outskirts"] == 1
    assert unlock_levels["forest_young_goblin_trail"] == 1
    assert unlock_levels["forest_stray_wolf_path"] == 1
    assert unlock_levels["forest_goblin_scout_trails"] >= unlock_levels["forest_rat_outskirts"]
    assert unlock_levels["forest_wolf_hunting_ground"] >= unlock_levels["forest_young_goblin_trail"]
    assert unlock_levels["forest_thorn_sprite_grove"] >= unlock_levels["forest_stray_wolf_path"]
    assert unlock_levels["forest_bone_gnawer_den"] >= unlock_levels["forest_goblin_scout_trails"]
    assert unlock_levels["forest_lost_adventurer_path"] >= unlock_levels["forest_wolf_hunting_ground"]
    assert unlock_levels["forest_goblin_shaman_grounds"] >= unlock_levels["forest_bone_gnawer_den"]
    assert unlock_levels["forest_alpha_wolf_lair"] >= unlock_levels["forest_lost_adventurer_path"]


def test_forest_gathering_nodes_match_expected_zones():
    gathering_nodes = load_json("data/gathering_nodes.json")

    for zone_id, expected_professions in EXPECTED_FOREST_ZONE_PROFESSIONS.items():
        assert zone_id in gathering_nodes
        assert set(gathering_nodes[zone_id]) == expected_professions


def test_legacy_forest_zones_are_removed():
    zones = load_json("data/zones.json")

    for zone_id in LEGACY_FOREST_ZONE_IDS:
        assert zone_id not in zones


def test_legacy_forest_gathering_nodes_are_removed():
    gathering_nodes = load_json("data/gathering_nodes.json")

    for zone_id in LEGACY_FOREST_ZONE_IDS:
        assert zone_id not in gathering_nodes


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
