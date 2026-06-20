import json
from pathlib import Path

from systems.inventory import create_inventory
from systems.quests import (
    accept_quest,
    create_player_quests,
    ensure_player_quests,
    get_quest_progress,
    record_quest_event,
)


PROJECT_ROOT = Path(__file__).resolve().parent.parent
QUESTS_PATH = PROJECT_ROOT / "data" / "quests.json"
BRINDLE_FIRST_QUEST_ID = "forest_brindle_pest_control_officially"
MAELA_FIRST_QUEST_ID = "forest_maela_polite_amount_leaves"
FEN_FIRST_QUEST_ID = "forest_fen_scouts_honor_used_once"


def load_quests():
    with QUESTS_PATH.open("r", encoding="utf-8") as quests_file:
        return json.load(quests_file)


def create_test_player(quests_data):
    player = {
        "gold": 0,
        "exp": 0,
        "inventory": create_inventory(),
        "quests": create_player_quests(quests_data),
    }
    accept_quest(player, quests_data, BRINDLE_FIRST_QUEST_ID)
    return player


def test_create_player_quests_offers_parallel_root_quests():
    quests_data = load_quests()

    quests = create_player_quests(quests_data)

    assert quests["available"] == [
        BRINDLE_FIRST_QUEST_ID,
        MAELA_FIRST_QUEST_ID,
        FEN_FIRST_QUEST_ID,
    ]
    assert quests["active"] == []


def test_accept_quest_moves_available_quest_to_active():
    quests_data = load_quests()
    player = {
        "gold": 0,
        "exp": 0,
        "inventory": create_inventory(),
        "quests": create_player_quests(quests_data),
    }

    assert accept_quest(player, quests_data, BRINDLE_FIRST_QUEST_ID) is True
    assert player["quests"]["available"] == [
        MAELA_FIRST_QUEST_ID,
        FEN_FIRST_QUEST_ID,
    ]
    assert player["quests"]["active"] == [BRINDLE_FIRST_QUEST_ID]


def test_unaccepted_quest_does_not_receive_progress():
    quests_data = load_quests()
    player = {
        "gold": 0,
        "exp": 0,
        "inventory": create_inventory(),
        "quests": create_player_quests(quests_data),
    }

    record_quest_event(
        player,
        quests_data,
        {"type": "kill_enemy", "target": "forest_rat", "amount": 2},
    )

    assert get_quest_progress(player, BRINDLE_FIRST_QUEST_ID, 0) == 0


def test_ensure_player_quests_migrates_active_quest_from_older_save():
    quests_data = load_quests()
    player = {
        "quests": {
            "active": ["forest_secure_outskirts"],
            "completed": [],
            "progress": {"forest_secure_outskirts": {"0": 3}},
            "last_completed": [],
        },
        "npc_dialogue_state": {
            "introduced_npcs": ["camp_quartermaster"],
            "completed_quests_seen": ["forest_secure_outskirts"],
        },
    }

    state = ensure_player_quests(player, quests_data)

    assert state["available"] == [
        MAELA_FIRST_QUEST_ID,
        FEN_FIRST_QUEST_ID,
    ]
    assert state["active"] == [BRINDLE_FIRST_QUEST_ID]
    assert state["progress"][BRINDLE_FIRST_QUEST_ID] == {"0": 3}
    assert player["npc_dialogue_state"]["completed_quests_seen"] == [BRINDLE_FIRST_QUEST_ID]


def test_goblin_signs_completion_unlocks_next_fen_and_osric_quests():
    quests_data = load_quests()
    player = create_test_player(quests_data)
    player["quests"]["active"] = ["forest_fen_goblin_signs_terrible_arrows"]
    player["quests"]["available"] = []

    record_quest_event(
        player,
        quests_data,
        {"type": "kill_enemy", "target": "goblin_scout", "amount": 6},
    )

    assert "forest_osric_bones_without_appointment" in player["quests"]["available"]
    assert "forest_fen_path_not_run_from" in player["quests"]["available"]


def test_marns_first_quest_requires_brindle_and_fens_final_milestones():
    quests_data = load_quests()
    player = {
        "quests": {
            "available": [],
            "active": [],
            "completed": [
                "forest_brindle_forwarded_to_gate",
                "forest_fen_goblin_signs_terrible_arrows",
            ],
            "progress": {},
            "last_completed": [],
        }
    }

    state = ensure_player_quests(player, quests_data)
    assert "forest_marn_gate_not_decorative" not in state["available"]

    state["completed"].append("forest_fen_smoke_beyond_trees")
    ensure_player_quests(player, quests_data)

    assert "forest_marn_gate_not_decorative" in state["available"]


def test_quest_prerequisites_reference_existing_quests():
    quests_data = load_quests()

    for quest_id, quest in quests_data.items():
        required_quests = quest.get("required_quests", [])
        assert isinstance(required_quests, list), quest_id
        for required_quest_id in required_quests:
            assert required_quest_id in quests_data
            assert quest_id in quests_data[required_quest_id].get("next_quests", [])


def test_record_kill_enemy_progress_updates_matching_objective():
    quests_data = load_quests()
    player = create_test_player(quests_data)

    record_quest_event(
        player,
        quests_data,
        {"type": "kill_enemy", "target": "forest_rat", "amount": 2},
    )

    assert get_quest_progress(player, BRINDLE_FIRST_QUEST_ID, 0) == 2


def test_progress_does_not_exceed_required():
    quests_data = load_quests()
    player = create_test_player(quests_data)

    record_quest_event(
        player,
        quests_data,
        {"type": "kill_enemy", "target": "forest_rat", "amount": 999},
    )

    assert get_quest_progress(player, BRINDLE_FIRST_QUEST_ID, 0) == 5


def test_complete_quest_moves_to_completed_and_offers_next_brindle_quest():
    quests_data = load_quests()
    player = create_test_player(quests_data)

    result = record_quest_event(
        player,
        quests_data,
        {"type": "kill_enemy", "target": "forest_rat", "amount": 5},
    )

    assert result["completed"] == [BRINDLE_FIRST_QUEST_ID]
    assert BRINDLE_FIRST_QUEST_ID in player["quests"]["completed"]
    assert "forest_brindle_crates_claws_negligence" in player["quests"]["available"]
    assert "forest_brindle_crates_claws_negligence" not in player["quests"]["active"]


def test_gather_item_progress():
    quests_data = load_quests()
    player = create_test_player(quests_data)
    player["quests"]["active"] = [MAELA_FIRST_QUEST_ID]

    record_quest_event(
        player,
        quests_data,
        {"type": "gather_item", "target": "healing_herb", "amount": 3},
    )

    assert get_quest_progress(player, MAELA_FIRST_QUEST_ID, 0) == 3


def test_craft_recipe_progress():
    quests_data = load_quests()
    player = create_test_player(quests_data)
    player["quests"]["active"] = ["forest_maela_cure_might_apologize"]

    record_quest_event(
        player,
        quests_data,
        {
            "type": "craft_recipe",
            "target": "craft_herbal_poultice",
            "amount": 1,
        },
    )

    assert get_quest_progress(player, "forest_maela_cure_might_apologize", 0) == 1


def test_apply_gold_reward():
    quests_data = load_quests()
    player = create_test_player(quests_data)

    record_quest_event(
        player,
        quests_data,
        {"type": "kill_enemy", "target": "forest_rat", "amount": 5},
    )
    assert player["gold"] == 15


def test_clear_dungeon_progress():
    quests_data = load_quests()
    player = create_test_player(quests_data)
    player["quests"]["active"] = ["forest_marn_break_goblin_camp"]

    record_quest_event(
        player,
        quests_data,
        {
            "type": "clear_dungeon",
            "target": "forest_goblin_camp",
            "amount": 1,
        },
    )

    assert get_quest_progress(player, "forest_marn_break_goblin_camp", 0) == 1


def test_clear_dungeon_completion_activates_next():
    quests_data = load_quests()
    player = create_test_player(quests_data)
    player["quests"]["active"] = ["forest_marn_break_goblin_camp"]
    player["quests"]["completed"].append("forest_maela_cure_might_apologize")
    player["quests"]["completed"].append("forest_osric_grave_administrative_error")

    result = record_quest_event(
        player,
        quests_data,
        {
            "type": "clear_dungeon",
            "target": "forest_goblin_camp",
            "amount": 1,
        },
    )

    assert result["completed"] == ["forest_marn_break_goblin_camp"]
    assert "forest_marn_break_goblin_camp" in player["quests"]["completed"]
    assert "forest_marn_buried_grove_stirs" in player["quests"]["available"]
    assert "forest_marn_buried_grove_stirs" not in player["quests"]["active"]


def test_defeat_boss_progress():
    quests_data = load_quests()
    player = create_test_player(quests_data)
    player["quests"]["active"] = ["forest_marn_grubfang_must_fall"]

    result = record_quest_event(
        player,
        quests_data,
        {
            "type": "defeat_boss",
            "target": "grubfang_rootcaller",
            "amount": 1,
        },
    )

    assert get_quest_progress(player, "forest_marn_grubfang_must_fall", 0) == 1
    assert result["completed"] == ["forest_marn_grubfang_must_fall"]
    assert "forest_marn_grubfang_must_fall" in player["quests"]["completed"]


def test_buried_grove_activates_rootcaller_quest():
    quests_data = load_quests()
    player = create_test_player(quests_data)
    player["quests"]["active"] = ["forest_marn_rootbound_warning"]

    result = record_quest_event(
        player,
        quests_data,
        {
            "type": "clear_dungeon",
            "target": "forest_buried_grove",
            "amount": 1,
        },
    )

    assert result["completed"] == ["forest_marn_rootbound_warning"]
    assert "forest_marn_rootbound_warning" in player["quests"]["completed"]
    assert "forest_marn_rootcallers_door" in player["quests"]["available"]
    assert "forest_marn_rootcallers_door" not in player["quests"]["active"]
