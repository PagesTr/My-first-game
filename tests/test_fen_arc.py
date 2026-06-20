import json
from pathlib import Path

from systems.dialogues import apply_npc_conversation_result, build_npc_conversation
from systems.inventory import create_inventory
from systems.quests import create_player_quests, ensure_player_quests, record_quest_event


PROJECT_ROOT = Path(__file__).resolve().parent.parent

FEN_QUEST_IDS = [
    "forest_fen_scouts_honor_used_once",
    "forest_fen_tracks_facing_wrong_way",
    "forest_fen_shortcut_got_longer",
    "forest_fen_goblin_signs_terrible_arrows",
    "forest_fen_path_not_run_from",
    "forest_fen_smoke_beyond_trees",
]

EXPECTED_TITLES = [
    "Scout's Honor, Used Once",
    "Tracks Facing the Wrong Way",
    "The Shortcut That Got Longer",
    "Goblin Signs, Terrible Arrows",
    "The Path I Did Not Run From",
    "Smoke Beyond the Trees",
]


def load_json(relative_path):
    with (PROJECT_ROOT / relative_path).open(encoding="utf-8") as data_file:
        return json.load(data_file)


def test_fen_has_six_official_core_quests_in_order():
    quests = load_json("data/quests.json")
    npcs = load_json("data/npcs.json")

    assert npcs["retired_scout"]["related_quests"] == FEN_QUEST_IDS
    assert [quests[quest_id]["name"] for quest_id in FEN_QUEST_IDS] == EXPECTED_TITLES
    assert "forest_pack_watches" not in quests
    assert "forest_smoke_above_trees" not in quests


def test_fen_core_quests_form_a_sequential_chain():
    quests = load_json("data/quests.json")

    assert quests[FEN_QUEST_IDS[0]]["required_quests"] == []
    for previous_id, quest_id in zip(FEN_QUEST_IDS, FEN_QUEST_IDS[1:]):
        assert quests[quest_id]["required_quests"] == [previous_id]
        assert quest_id in quests[previous_id]["next_quests"]


def test_fen_objectives_use_supported_existing_enemies():
    quests = load_json("data/quests.json")
    enemies = load_json("data/enemies.json")

    for quest_id in FEN_QUEST_IDS:
        quest = quests[quest_id]
        assert quest["npc_id"] == "retired_scout"
        assert len(quest["objectives"]) == 1
        objective = quest["objectives"][0]
        assert objective["type"] == "kill_enemy"
        assert objective["target"] in enemies
        assert objective["required"] > 0


def test_fen_dialogues_cover_every_core_quest_state():
    dialogues = load_json("data/npc_dialogues.json")["retired_scout"]

    assert len(dialogues["intro"].split("\n\n")) >= 6
    assert set(dialogues["quests"]) == set(FEN_QUEST_IDS)
    for quest_id in FEN_QUEST_IDS:
        assert set(dialogues["quests"][quest_id]) == {
            "quest_offer",
            "progress",
            "completion",
            "transition",
        }


def test_osric_and_marn_use_official_fen_milestones():
    quests = load_json("data/quests.json")

    assert quests["forest_osric_bones_without_appointment"]["required_quests"] == [
        "forest_fen_goblin_signs_terrible_arrows"
    ]
    assert "forest_fen_smoke_beyond_trees" in quests["forest_marn_gate_not_decorative"]["required_quests"]


def test_legacy_pack_quest_migrates_to_tracks_with_first_step_backfilled():
    quests = load_json("data/quests.json")
    player = {
        "quests": {
            "available": [],
            "active": ["forest_pack_watches"],
            "completed": [],
            "progress": {"forest_pack_watches": {"0": 3, "1": 1}},
            "last_completed": [],
        }
    }

    state = ensure_player_quests(player, quests)

    assert FEN_QUEST_IDS[1] in state["active"]
    assert FEN_QUEST_IDS[0] in state["completed"]
    assert state["progress"][FEN_QUEST_IDS[1]] == {"0": 3}
    assert FEN_QUEST_IDS[0] in player["npc_dialogue_state"]["completed_quests_seen"]


def test_legacy_smoke_quest_migrates_to_final_step_with_prior_steps_backfilled():
    quests = load_json("data/quests.json")
    player = {
        "quests": {
            "available": [],
            "active": ["forest_smoke_above_trees"],
            "completed": [],
            "progress": {"forest_smoke_above_trees": {"0": 6, "1": 1}},
            "last_completed": [],
        }
    }

    state = ensure_player_quests(player, quests)

    assert FEN_QUEST_IDS[-1] in state["active"]
    assert all(quest_id in state["completed"] for quest_id in FEN_QUEST_IDS[:-1])
    assert state["progress"][FEN_QUEST_IDS[-1]] == {}
    assert all(
        quest_id in player["npc_dialogue_state"]["completed_quests_seen"]
        for quest_id in FEN_QUEST_IDS[:-1]
    )


def test_fen_core_arc_can_be_completed_in_sequence():
    quests = load_json("data/quests.json")
    npcs = load_json("data/npcs.json")
    dialogues = load_json("data/npc_dialogues.json")
    player = {
        "gold": 0,
        "exp": 0,
        "inventory": create_inventory(),
        "quests": create_player_quests(quests),
    }

    for quest_id in FEN_QUEST_IDS:
        offer = build_npc_conversation(
            player,
            npcs,
            quests,
            dialogues,
            "retired_scout",
        )
        assert offer["accept_quest_id"] == quest_id
        apply_npc_conversation_result(player, quests, offer)

        objective = quests[quest_id]["objectives"][0]
        result = record_quest_event(
            player,
            quests,
            {
                "type": objective["type"],
                "target": objective["target"],
                "amount": objective["required"],
            },
        )
        assert result["completed"] == [quest_id]

        completion = build_npc_conversation(
            player,
            npcs,
            quests,
            dialogues,
            "retired_scout",
        )
        assert completion["completed_quest_id"] == quest_id
        apply_npc_conversation_result(player, quests, completion)

    assert all(quest_id in player["quests"]["completed"] for quest_id in FEN_QUEST_IDS)
