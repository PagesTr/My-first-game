import json
from pathlib import Path

from systems.achievements import (
    SUPPORTED_OBJECTIVE_TYPES,
    SUPPORTED_REWARD_TYPES,
    apply_achievement_rewards,
    clear_last_unlocked,
    create_player_achievements,
    ensure_player_achievements,
    get_achievement_progress,
    get_visible_achievements,
    is_achievement_unlocked,
    record_achievement_event,
)
from systems.inventory import create_inventory


ROOT = Path(__file__).resolve().parents[1]
REQUIRED_ACHIEVEMENT_FIELDS = {
    "name",
    "description",
    "chapter",
    "category",
    "tier",
    "hidden",
    "repeatable",
    "objective",
    "rewards",
}
FOREST_ZONE_IDS = {
    "forest_rat_outskirts",
    "forest_young_goblin_trail",
    "forest_stray_wolf_path",
    "forest_goblin_scout_trails",
    "forest_wolf_hunting_ground",
    "forest_thorn_sprite_grove",
    "forest_bone_gnawer_den",
    "forest_lost_adventurer_path",
    "forest_goblin_shaman_grounds",
    "forest_alpha_wolf_lair",
}


def load_json(path):
    with (ROOT / path).open(encoding="utf-8") as data_file:
        return json.load(data_file)


def load_achievements():
    return load_json("data/achievements.json")


def make_player():
    return {
        "gold": 0,
        "achievements": create_player_achievements({}),
    }


def test_create_player_achievements_has_expected_shape():
    assert create_player_achievements({}) == {
        "unlocked": [],
        "progress": {},
        "last_unlocked": [],
    }


def test_ensure_player_achievements_preserves_existing_progress():
    player = {
        "achievements": {
            "unlocked": ["forest_rat_cleaner_1"],
            "progress": {"forest_rat_cleaner_2": 12},
        }
    }

    achievements = ensure_player_achievements(player, {})

    assert achievements["unlocked"] == ["forest_rat_cleaner_1"]
    assert achievements["progress"] == {"forest_rat_cleaner_2": 12}
    assert achievements["last_unlocked"] == []


def test_achievements_data_has_required_fields():
    achievements = load_achievements()

    for achievement_id, achievement in achievements.items():
        assert REQUIRED_ACHIEVEMENT_FIELDS <= achievement.keys(), achievement_id


def test_forest_achievements_count_is_at_least_30():
    achievements = load_achievements()

    forest_achievements = [
        achievement
        for achievement in achievements.values()
        if achievement["chapter"] == "forest"
    ]

    assert len(forest_achievements) >= 55


def test_record_kill_enemy_unlocks_rat_cleaner():
    achievements = load_achievements()
    player = make_player()

    result = record_achievement_event(
        player,
        achievements,
        {"type": "kill_enemy", "target": "forest_rat", "amount": 25},
    )

    assert result["unlocked"] == ["forest_rat_cleaner_1"]
    assert is_achievement_unlocked(player, "forest_rat_cleaner_1")


def test_progress_is_capped_at_required():
    achievements = load_achievements()
    player = make_player()

    record_achievement_event(
        player,
        achievements,
        {"type": "kill_enemy", "target": "forest_rat", "amount": 30},
    )

    assert get_achievement_progress(player, "forest_rat_cleaner_1") == 25


def test_max_progress_mode_keeps_best_value():
    achievements = {
        "test_run": {
            "progress_mode": "max",
            "objective": {
                "type": "single_expedition_kills",
                "target": "test_zone",
                "required": 20,
            },
            "rewards": [],
        }
    }
    player = make_player()

    record_achievement_event(
        player,
        achievements,
        {"type": "expedition_finished", "target": "test_zone", "amount": 8},
    )
    record_achievement_event(
        player,
        achievements,
        {"type": "expedition_finished", "target": "test_zone", "amount": 5},
    )

    assert get_achievement_progress(player, "test_run") == 8


def test_max_progress_mode_updates_when_new_best_is_higher():
    achievements = {
        "test_run": {
            "progress_mode": "max",
            "objective": {
                "type": "single_expedition_kills",
                "target": "test_zone",
                "required": 20,
            },
            "rewards": [],
        }
    }
    player = make_player()

    record_achievement_event(
        player,
        achievements,
        {"type": "expedition_finished", "target": "test_zone", "amount": 8},
    )
    record_achievement_event(
        player,
        achievements,
        {"type": "expedition_finished", "target": "test_zone", "amount": 12},
    )

    assert get_achievement_progress(player, "test_run") == 12


def test_max_progress_mode_caps_at_required():
    achievements = {
        "test_run": {
            "progress_mode": "max",
            "objective": {
                "type": "single_expedition_kills",
                "target": "test_zone",
                "required": 10,
            },
            "rewards": [],
        }
    }
    player = make_player()

    record_achievement_event(
        player,
        achievements,
        {"type": "expedition_finished", "target": "test_zone", "amount": 999},
    )

    assert get_achievement_progress(player, "test_run") == 10


def test_cumulative_progress_mode_still_adds_amounts():
    achievements = {
        "test_cumulative": {
            "objective": {
                "type": "kill_enemy",
                "target": "test_enemy",
                "required": 10,
            },
            "rewards": [],
        }
    }
    player = make_player()

    record_achievement_event(
        player,
        achievements,
        {"type": "kill_enemy", "target": "test_enemy", "amount": 4},
    )
    record_achievement_event(
        player,
        achievements,
        {"type": "kill_enemy", "target": "test_enemy", "amount": 5},
    )

    assert get_achievement_progress(player, "test_cumulative") == 9


def test_unlocked_achievement_is_not_unlocked_twice():
    achievements = load_achievements()
    player = make_player()

    record_achievement_event(
        player,
        achievements,
        {"type": "kill_enemy", "target": "forest_rat", "amount": 25},
    )
    result = record_achievement_event(
        player,
        achievements,
        {"type": "kill_enemy", "target": "forest_rat", "amount": 25},
    )

    assert result["unlocked"] == []
    assert player["achievements"]["unlocked"].count("forest_rat_cleaner_1") == 1
    assert player["gold"] == 50


def test_kill_family_matches_metadata_family():
    achievements = load_achievements()
    player = make_player()

    result = record_achievement_event(
        player,
        achievements,
        {
            "type": "kill_enemy",
            "target": "young_goblin",
            "amount": 50,
            "metadata": {"family": "goblin"},
        },
    )

    assert "forest_goblin_problem_1" in result["unlocked"]


def test_gather_profession_matches_metadata_profession():
    achievements = load_achievements()
    player = make_player()

    result = record_achievement_event(
        player,
        achievements,
        {
            "type": "gather_tick",
            "target": "healing_herb",
            "amount": 25,
            "metadata": {"profession_id": "druid"},
        },
    )

    assert result["unlocked"] == ["forest_first_harvest"]


def test_craft_chapter_matches_metadata_chapter():
    achievements = load_achievements()
    player = make_player()

    result = record_achievement_event(
        player,
        achievements,
        {
            "type": "craft_recipe",
            "target": "craft_herbal_poultice",
            "amount": 1,
            "metadata": {"chapter": "forest"},
        },
    )

    assert result["unlocked"] == ["forest_first_craft"]


def test_clear_dungeon_matches_target():
    achievements = load_achievements()
    player = make_player()

    result = record_achievement_event(
        player,
        achievements,
        {"type": "clear_dungeon", "target": "forest_goblin_camp", "amount": 1},
    )

    assert result["unlocked"] == ["forest_camp_breaker_1"]


def test_defeat_boss_matches_target():
    achievements = load_achievements()
    player = make_player()

    result = record_achievement_event(
        player,
        achievements,
        {"type": "defeat_boss", "target": "grubfang_rootcaller", "amount": 1},
    )

    assert "forest_rootcaller_defeated" in result["unlocked"]


def test_boss_victory_count_matches_defeat_boss_event():
    achievements = load_achievements()
    player = make_player()

    result = record_achievement_event(
        player,
        achievements,
        {"type": "defeat_boss", "target": "grubfang_rootcaller", "amount": 3},
    )

    assert "forest_rootcaller_argument" in result["unlocked"]


def test_equip_set_pieces_matches_specific_set():
    achievements = load_achievements()
    player = make_player()

    result = record_achievement_event(
        player,
        achievements,
        {"type": "equip_set_pieces", "target": "wolf_stalker", "amount": 2},
    )

    assert "forest_wolf_stalker_initiate" in result["unlocked"]


def test_equip_set_pieces_matches_any_forest_set():
    achievements = load_achievements()
    player = make_player()

    result = record_achievement_event(
        player,
        achievements,
        {
            "type": "equip_set_pieces",
            "target": "wolf_stalker",
            "amount": 2,
            "metadata": {"chapter": "forest"},
        },
    )

    assert "forest_set_apprentice" in result["unlocked"]


def test_single_expedition_kills_matches_expedition_finished_event():
    achievements = load_achievements()
    player = make_player()

    result = record_achievement_event(
        player,
        achievements,
        {
            "type": "expedition_finished",
            "target": "forest_rat_outskirts",
            "amount": 10,
        },
    )

    assert "forest_rat_outskirts_push_1" in result["unlocked"]


def test_single_dungeon_kills_matches_dungeon_run_finished_event():
    achievements = load_achievements()
    player = make_player()

    result = record_achievement_event(
        player,
        achievements,
        {
            "type": "dungeon_run_finished",
            "target": "forest_goblin_camp",
            "amount": 5,
        },
    )

    assert "forest_goblin_camp_push_1" in result["unlocked"]


def test_single_boss_victories_matches_boss_loop_finished_event():
    achievements = load_achievements()
    player = make_player()

    result = record_achievement_event(
        player,
        achievements,
        {
            "type": "boss_loop_finished",
            "target": "grubfang_rootcaller",
            "amount": 2,
        },
    )

    assert "forest_rootcaller_loop_1" in result["unlocked"]


def test_gold_reward_is_applied():
    player = {"gold": 5}
    achievement = {"rewards": [{"type": "gold", "amount": 50}]}

    result = apply_achievement_rewards(player, achievement)

    assert player["gold"] == 55
    assert result["failed"] == []


def test_stat_bonus_reward_is_applied():
    player = {"luck": 1}
    achievement = {"rewards": [{"type": "stat_bonus", "stat": "luck", "amount": 1}]}

    apply_achievement_rewards(player, achievement)

    assert player["luck"] == 2


def test_percent_bonus_reward_is_applied():
    player = {"crit_chance": 0.02}
    achievement = {
        "rewards": [{"type": "percent_bonus", "stat": "crit_chance", "amount": 0.01}]
    }

    apply_achievement_rewards(player, achievement)

    assert player["crit_chance"] == 0.03


def test_item_reward_is_added_when_inventory_exists():
    items = load_json("data/items.json")
    player = {
        "inventory": create_inventory(),
    }
    achievement = {
        "rewards": [{"type": "item", "item": "field_dressing", "quantity": 2}]
    }

    result = apply_achievement_rewards(player, achievement, items)

    assert result["failed"] == []
    assert player["inventory"]["slots"][0] == {
        "kind": "stackable",
        "item": "field_dressing",
        "quantity": 2,
    }


def test_visible_achievements_hides_hidden_until_unlocked():
    achievements = {
        "visible": {
            "chapter": "forest",
            "category": "combat",
            "tier": 1,
            "hidden": False,
        },
        "hidden": {
            "chapter": "forest",
            "category": "combat",
            "tier": 2,
            "hidden": True,
        },
    }
    player = {"achievements": {"unlocked": [], "progress": {}, "last_unlocked": []}}

    visible_ids = [entry["id"] for entry in get_visible_achievements(player, achievements)]
    player["achievements"]["unlocked"].append("hidden")
    unlocked_visible_ids = [
        entry["id"] for entry in get_visible_achievements(player, achievements)
    ]

    assert visible_ids == ["visible"]
    assert unlocked_visible_ids == ["visible", "hidden"]


def test_clear_last_unlocked_clears_list():
    player = {
        "achievements": {
            "unlocked": ["forest_rat_cleaner_1"],
            "progress": {},
            "last_unlocked": ["forest_rat_cleaner_1"],
        }
    }

    clear_last_unlocked(player)

    assert player["achievements"]["last_unlocked"] == []


def test_all_achievement_objective_types_are_supported():
    achievements = load_achievements()
    objective_types = {
        achievement["objective"]["type"]
        for achievement in achievements.values()
    }

    assert objective_types <= SUPPORTED_OBJECTIVE_TYPES


def test_all_achievement_reward_types_are_supported():
    achievements = load_achievements()
    reward_types = {
        reward["type"]
        for achievement in achievements.values()
        for reward in achievement["rewards"]
    }

    assert reward_types == SUPPORTED_REWARD_TYPES


def test_forest_run_achievements_exist_for_each_forest_zone():
    achievements = load_achievements()

    for zone_id in FOREST_ZONE_IDS:
        zone_achievements = [
            achievement
            for achievement in achievements.values()
            if achievement["objective"]["type"] == "single_expedition_kills"
            and achievement["objective"]["target"] == zone_id
        ]
        assert len(zone_achievements) >= 2, zone_id


def test_forest_run_achievements_count_is_at_least_25():
    achievements = load_achievements()

    run_achievements = [
        achievement
        for achievement in achievements.values()
        if achievement["chapter"] == "forest" and achievement["category"] == "run"
    ]

    assert len(run_achievements) >= 25


def test_forest_achievement_targets_reference_existing_data_when_possible():
    achievements = load_achievements()
    enemies = load_json("data/enemies.json")
    dungeons = load_json("data/dungeons.json")
    recipes = load_json("data/recipes.json")
    equipment_sets = load_json("data/equipment_sets.json")
    zones = load_json("data/zones.json")

    for achievement_id, achievement in achievements.items():
        objective = achievement["objective"]
        objective_type = objective["type"]
        target = objective["target"]

        if achievement["chapter"] != "forest":
            continue
        if objective_type == "kill_enemy":
            assert target in enemies, achievement_id
        if objective_type in {"defeat_boss", "boss_victory_count", "single_boss_victories"}:
            assert target in enemies, achievement_id
        if objective_type in {"clear_dungeon", "single_dungeon_kills"}:
            assert target in dungeons, achievement_id
        if objective_type == "craft_recipe":
            assert target in recipes, achievement_id
        if objective_type == "equip_set_pieces":
            assert target == "any_forest_set" or target in equipment_sets, achievement_id
        if objective_type == "single_expedition_kills":
            assert target in zones, achievement_id
