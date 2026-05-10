import json
from pathlib import Path

from systems.inventory import create_inventory
from systems.quests import (
    create_player_quests,
    get_quest_progress,
    record_quest_event,
)


PROJECT_ROOT = Path(__file__).resolve().parent.parent
QUESTS_PATH = PROJECT_ROOT / "data" / "quests.json"


def load_quests():
    with QUESTS_PATH.open("r", encoding="utf-8") as quests_file:
        return json.load(quests_file)


def create_test_player(quests_data):
    return {
        "gold": 0,
        "exp": 0,
        "inventory": create_inventory(),
        "quests": create_player_quests(quests_data),
    }


def test_create_player_quests_starts_first_root_quest():
    quests_data = load_quests()

    quests = create_player_quests(quests_data)

    assert quests["active"] == ["forest_secure_outskirts"]


def test_record_kill_enemy_progress_updates_matching_objective():
    quests_data = load_quests()
    player = create_test_player(quests_data)

    record_quest_event(
        player,
        quests_data,
        {"type": "kill_enemy", "target": "forest_rat", "amount": 2},
    )

    assert get_quest_progress(player, "forest_secure_outskirts", 0) == 2


def test_progress_does_not_exceed_required():
    quests_data = load_quests()
    player = create_test_player(quests_data)

    record_quest_event(
        player,
        quests_data,
        {"type": "kill_enemy", "target": "forest_rat", "amount": 999},
    )

    assert get_quest_progress(player, "forest_secure_outskirts", 0) == 5


def test_complete_quest_moves_to_completed_and_activates_next():
    quests_data = load_quests()
    player = create_test_player(quests_data)

    record_quest_event(
        player,
        quests_data,
        {"type": "kill_enemy", "target": "forest_rat", "amount": 5},
    )
    result = record_quest_event(
        player,
        quests_data,
        {"type": "kill_enemy", "target": "young_goblin", "amount": 3},
    )

    assert result["completed"] == ["forest_secure_outskirts"]
    assert "forest_secure_outskirts" in player["quests"]["completed"]
    assert "forest_first_harvest" in player["quests"]["active"]


def test_gather_item_progress():
    quests_data = load_quests()
    player = create_test_player(quests_data)
    player["quests"]["active"] = ["forest_first_harvest"]

    record_quest_event(
        player,
        quests_data,
        {"type": "gather_item", "target": "healing_herb", "amount": 3},
    )

    assert get_quest_progress(player, "forest_first_harvest", 0) == 3


def test_craft_recipe_progress():
    quests_data = load_quests()
    player = create_test_player(quests_data)
    player["quests"]["active"] = ["forest_pack_watches"]

    record_quest_event(
        player,
        quests_data,
        {
            "type": "craft_recipe",
            "target": "craft_wolf_fang_charm",
            "amount": 1,
        },
    )

    assert get_quest_progress(player, "forest_pack_watches", 1) == 1


def test_apply_gold_reward():
    quests_data = load_quests()
    player = create_test_player(quests_data)

    record_quest_event(
        player,
        quests_data,
        {"type": "kill_enemy", "target": "forest_rat", "amount": 5},
    )
    record_quest_event(
        player,
        quests_data,
        {"type": "kill_enemy", "target": "young_goblin", "amount": 3},
    )

    assert player["gold"] == 25


def test_clear_dungeon_progress():
    quests_data = load_quests()
    player = create_test_player(quests_data)
    player["quests"]["active"] = ["forest_clear_goblin_camp"]

    record_quest_event(
        player,
        quests_data,
        {
            "type": "clear_dungeon",
            "target": "forest_goblin_camp",
            "amount": 1,
        },
    )

    assert get_quest_progress(player, "forest_clear_goblin_camp", 0) == 1


def test_clear_dungeon_completion_activates_next():
    quests_data = load_quests()
    player = create_test_player(quests_data)
    player["quests"]["active"] = ["forest_clear_goblin_camp"]

    result = record_quest_event(
        player,
        quests_data,
        {
            "type": "clear_dungeon",
            "target": "forest_goblin_camp",
            "amount": 1,
        },
    )

    assert result["completed"] == ["forest_clear_goblin_camp"]
    assert "forest_clear_goblin_camp" in player["quests"]["completed"]
    assert "forest_buried_grove" in player["quests"]["active"]
