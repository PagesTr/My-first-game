import json
from pathlib import Path

from systems.dungeons import (
    apply_rest_choice,
    calculate_boss_multiplier,
    calculate_boss_reward_multiplier,
    create_dungeon_state,
    get_dungeon,
    get_dungeon_route,
    get_next_dungeon_step,
    is_boss_loop_step,
    is_rest_choice_step,
)


PROJECT_ROOT = Path(__file__).resolve().parent.parent
DUNGEONS_PATH = PROJECT_ROOT / "data" / "dungeons.json"
ENEMIES_PATH = PROJECT_ROOT / "data" / "enemies.json"
FOREST_DUNGEON_IDS = {"forest_goblin_camp", "forest_buried_grove"}
ALLOWED_FUTURE_ENEMY_IDS = {"goblin_quartermaster"}


def load_json(path):
    with path.open("r", encoding="utf-8") as json_file:
        return json.load(json_file)


def test_get_dungeon_returns_dungeon():
    dungeons = load_json(DUNGEONS_PATH)

    dungeon = get_dungeon(dungeons, "forest_goblin_camp")

    assert dungeon["name"] == "Goblin Camp"


def test_dungeon_routes_contain_rest_choice_before_boss_loop():
    dungeons = load_json(DUNGEONS_PATH)

    for dungeon_id in FOREST_DUNGEON_IDS:
        route = get_dungeon_route(dungeons[dungeon_id])
        rest_indexes = [
            index for index, step in enumerate(route) if is_rest_choice_step(step)
        ]
        boss_indexes = [
            index for index, step in enumerate(route) if is_boss_loop_step(step)
        ]

        assert len(rest_indexes) == 1
        assert len(boss_indexes) == 1
        assert rest_indexes[0] < boss_indexes[0]


def test_create_dungeon_state_starts_at_step_zero():
    state = create_dungeon_state("forest_goblin_camp")

    assert state == {
        "dungeon_id": "forest_goblin_camp",
        "step_index": 0,
        "boss_victories": 0,
        "rest_choice_used": False,
        "completed": False,
        "failed": False,
    }


def test_apply_rest_choice_heals_player():
    player = {"max_hp": 100, "current_hp": 40}

    result = apply_rest_choice(player, "heal")

    assert result["applied"] is True
    assert result["choice"] == "heal"
    assert result["healed"] == 30
    assert result["loot_bonus"] is False
    assert player["current_hp"] == 70


def test_apply_rest_choice_does_not_exceed_max_hp():
    player = {"max_hp": 100, "current_hp": 90}

    result = apply_rest_choice(player, "heal")

    assert result["healed"] == 10
    assert player["current_hp"] == 100


def test_apply_rest_choice_loot_returns_bonus_flag():
    player = {"max_hp": 100, "current_hp": 40}

    result = apply_rest_choice(player, "loot")

    assert result == {
        "applied": True,
        "choice": "loot",
        "healed": 0,
        "loot_bonus": True,
    }
    assert player["current_hp"] == 40


def test_apply_rest_choice_rejects_invalid_choice():
    player = {"max_hp": 100, "current_hp": 40}

    result = apply_rest_choice(player, "nap")

    assert result == {
        "applied": False,
        "choice": "nap",
        "healed": 0,
        "loot_bonus": False,
        "reason": "invalid_choice",
    }


def test_calculate_boss_multiplier_scales_linearly():
    assert calculate_boss_multiplier(0, 0.15) == 1.0
    assert calculate_boss_multiplier(1, 0.15) == 1.15
    assert calculate_boss_multiplier(2, 0.15) == 1.30


def test_calculate_boss_reward_multiplier_scales_linearly():
    assert calculate_boss_reward_multiplier(0, 0.20) == 1.0
    assert calculate_boss_reward_multiplier(1, 0.20) == 1.20
    assert calculate_boss_reward_multiplier(2, 0.20) == 1.40


def test_forest_dungeons_have_required_fields():
    dungeons = load_json(DUNGEONS_PATH)

    for dungeon_id in FOREST_DUNGEON_IDS:
        dungeon = dungeons[dungeon_id]
        assert dungeon["name"]
        assert dungeon["chapter"] == "forest"
        assert isinstance(dungeon["unlock_level"], int)
        assert dungeon["unlock_level"] > 0
        assert dungeon["description"]
        assert isinstance(dungeon["route"], list)
        assert dungeon["route"]
        assert dungeon["boss_enemy_id"]
        assert dungeon["scaling_rate"] == 0.15
        assert dungeon["reward_multiplier_per_victory"] == 0.20


def test_dungeon_route_enemy_ids_are_valid():
    dungeons = load_json(DUNGEONS_PATH)
    enemies = load_json(ENEMIES_PATH)

    for dungeon in dungeons.values():
        for step in get_dungeon_route(dungeon):
            enemy_id = step.get("enemy_id")
            if not enemy_id:
                continue
            assert enemy_id in enemies or enemy_id in ALLOWED_FUTURE_ENEMY_IDS
        boss_enemy_id = dungeon.get("boss_enemy_id")
        assert (
            boss_enemy_id in enemies
            or boss_enemy_id in ALLOWED_FUTURE_ENEMY_IDS
        )


def test_get_next_dungeon_step_returns_step_or_none():
    dungeons = load_json(DUNGEONS_PATH)
    dungeon = dungeons["forest_buried_grove"]

    assert get_next_dungeon_step(dungeon, 0) == dungeon["route"][0]
    assert get_next_dungeon_step(dungeon, -1) is None
    assert get_next_dungeon_step(dungeon, 999) is None
