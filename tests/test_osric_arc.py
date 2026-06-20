import json
from pathlib import Path

from systems.dialogues import apply_npc_conversation_result, build_npc_conversation
from systems.inventory import create_inventory
from systems.quests import create_player_quests, ensure_player_quests, record_quest_event


PROJECT_ROOT = Path(__file__).resolve().parent.parent

OSRIC_QUEST_IDS = [
    "forest_osric_bones_without_appointment",
    "forest_osric_catalog_poor_decisions",
    "forest_osric_previous_expedition",
    "forest_osric_names_forest_kept",
    "forest_osric_grove_remembers",
    "forest_osric_grave_administrative_error",
]

EXPECTED_TITLES = [
    "Bones Without Appointment",
    "Catalog of Poor Decisions",
    "The Previous Expedition",
    "Names the Forest Kept",
    "The Grove Remembers",
    "A Grave Administrative Error",
]


def load_json(relative_path):
    with (PROJECT_ROOT / relative_path).open(encoding="utf-8") as data_file:
        return json.load(data_file)


def test_osric_has_six_official_core_quests_in_order():
    quests = load_json("data/quests.json")
    npcs = load_json("data/npcs.json")

    assert npcs["bone_scribe"]["related_quests"] == OSRIC_QUEST_IDS
    assert [quests[quest_id]["name"] for quest_id in OSRIC_QUEST_IDS] == EXPECTED_TITLES
    assert "forest_bones_under_roots" not in quests


def test_osric_core_quests_form_a_sequential_chain_after_fens_milestone():
    quests = load_json("data/quests.json")

    assert quests[OSRIC_QUEST_IDS[0]]["required_quests"] == [
        "forest_fen_goblin_signs_terrible_arrows"
    ]
    for previous_id, quest_id in zip(OSRIC_QUEST_IDS, OSRIC_QUEST_IDS[1:]):
        assert quests[quest_id]["required_quests"] == [previous_id]
        assert quest_id in quests[previous_id]["next_quests"]


def test_osric_objectives_use_supported_existing_items():
    quests = load_json("data/quests.json")
    items = load_json("data/items.json")

    for quest_id in OSRIC_QUEST_IDS:
        quest = quests[quest_id]
        assert quest["npc_id"] == "bone_scribe"
        assert len(quest["objectives"]) == 1
        objective = quest["objectives"][0]
        assert objective["type"] == "gather_item"
        assert objective["target"] in items
        assert objective["required"] > 0


def test_osric_dialogues_cover_every_core_quest_state():
    dialogues = load_json("data/npc_dialogues.json")["bone_scribe"]

    assert len(dialogues["intro"].split("\n\n")) >= 6
    assert set(dialogues["quests"]) == set(OSRIC_QUEST_IDS)
    for quest_id in OSRIC_QUEST_IDS:
        assert set(dialogues["quests"][quest_id]) == {
            "quest_offer",
            "progress",
            "completion",
            "transition",
        }


def test_buried_grove_requires_osrics_final_core_quest():
    quests = load_json("data/quests.json")

    assert OSRIC_QUEST_IDS[-1] in quests["forest_marn_buried_grove_stirs"]["required_quests"]
    assert "forest_marn_buried_grove_stirs" in quests[OSRIC_QUEST_IDS[-1]]["next_quests"]
    assert OSRIC_QUEST_IDS[-1] not in quests["forest_marn_gate_not_decorative"]["required_quests"]


def test_legacy_osric_quest_state_is_migrated():
    quests = load_json("data/quests.json")
    player = {
        "quests": {
            "available": [],
            "active": ["forest_bones_under_roots"],
            "completed": [],
            "progress": {"forest_bones_under_roots": {"0": 4, "1": 1}},
            "last_completed": [],
        },
        "npc_dialogue_state": {
            "introduced_npcs": ["bone_scribe"],
            "completed_quests_seen": ["forest_bones_under_roots"],
        },
    }

    state = ensure_player_quests(player, quests)

    assert OSRIC_QUEST_IDS[0] in state["active"]
    assert state["progress"][OSRIC_QUEST_IDS[0]] == {"0": 4}
    assert player["npc_dialogue_state"]["completed_quests_seen"] == [OSRIC_QUEST_IDS[0]]


def test_osric_core_arc_can_be_completed_in_sequence():
    quests = load_json("data/quests.json")
    npcs = load_json("data/npcs.json")
    dialogues = load_json("data/npc_dialogues.json")
    player = {
        "gold": 0,
        "exp": 0,
        "inventory": create_inventory(),
        "quests": create_player_quests(quests),
    }
    player["quests"]["completed"].append("forest_fen_goblin_signs_terrible_arrows")
    ensure_player_quests(player, quests)

    for quest_id in OSRIC_QUEST_IDS:
        offer = build_npc_conversation(
            player,
            npcs,
            quests,
            dialogues,
            "bone_scribe",
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
            "bone_scribe",
        )
        assert completion["completed_quest_id"] == quest_id
        apply_npc_conversation_result(player, quests, completion)

    assert all(quest_id in player["quests"]["completed"] for quest_id in OSRIC_QUEST_IDS)
