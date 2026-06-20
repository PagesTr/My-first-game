import json
from pathlib import Path

from systems.dialogues import apply_npc_conversation_result, build_npc_conversation
from systems.inventory import create_inventory
from systems.quests import create_player_quests, record_quest_event


PROJECT_ROOT = Path(__file__).resolve().parent.parent

BRINDLE_QUEST_IDS = [
    "forest_brindle_pest_control_officially",
    "forest_brindle_crates_claws_negligence",
    "forest_brindle_goblin_paperwork_incident",
    "forest_brindle_wolves_supply_line",
    "forest_brindle_reports_do_not_bleed",
    "forest_brindle_forwarded_to_gate",
]

EXPECTED_TITLES = [
    "Pest Control, Officially",
    "Crates, Claws and Casual Negligence",
    "Goblin Paperwork Incident",
    "Wolves in the Supply Line",
    "Reports Do Not Bleed",
    "Forwarded to the Gate",
]


def load_json(relative_path):
    with (PROJECT_ROOT / relative_path).open(encoding="utf-8") as data_file:
        return json.load(data_file)


def test_brindle_has_six_official_core_quests_in_order():
    quests = load_json("data/quests.json")
    npcs = load_json("data/npcs.json")

    assert npcs["camp_quartermaster"]["related_quests"] == BRINDLE_QUEST_IDS
    assert [quests[quest_id]["name"] for quest_id in BRINDLE_QUEST_IDS] == EXPECTED_TITLES
    assert "forest_secure_outskirts" not in quests


def test_brindle_core_quests_form_a_sequential_chain():
    quests = load_json("data/quests.json")

    assert quests[BRINDLE_QUEST_IDS[0]]["required_quests"] == []
    for previous_id, quest_id in zip(BRINDLE_QUEST_IDS, BRINDLE_QUEST_IDS[1:]):
        assert quests[quest_id]["required_quests"] == [previous_id]
        assert quest_id in quests[previous_id]["next_quests"]


def test_brindle_objectives_use_supported_existing_enemies():
    quests = load_json("data/quests.json")
    enemies = load_json("data/enemies.json")

    for quest_id in BRINDLE_QUEST_IDS:
        quest = quests[quest_id]
        assert quest["npc_id"] == "camp_quartermaster"
        assert len(quest["objectives"]) == 1
        objective = quest["objectives"][0]
        assert objective["type"] == "kill_enemy"
        assert objective["target"] in enemies
        assert objective["required"] > 0


def test_brindle_dialogues_cover_every_core_quest_state():
    dialogues = load_json("data/npc_dialogues.json")["camp_quartermaster"]

    assert len(dialogues["intro"].split("\n\n")) >= 4
    assert set(dialogues["quests"]) == set(BRINDLE_QUEST_IDS)
    for quest_id in BRINDLE_QUEST_IDS:
        assert set(dialogues["quests"][quest_id]) == {
            "quest_offer",
            "progress",
            "completion",
            "transition",
        }


def test_marn_requires_brindles_final_core_quest():
    quests = load_json("data/quests.json")

    assert "forest_brindle_forwarded_to_gate" in quests["forest_marn_gate_not_decorative"]["required_quests"]


def test_brindle_core_arc_can_be_completed_in_sequence():
    quests = load_json("data/quests.json")
    npcs = load_json("data/npcs.json")
    dialogues = load_json("data/npc_dialogues.json")
    player = {
        "gold": 0,
        "exp": 0,
        "inventory": create_inventory(),
        "quests": create_player_quests(quests),
    }

    for quest_id in BRINDLE_QUEST_IDS:
        offer = build_npc_conversation(
            player,
            npcs,
            quests,
            dialogues,
            "camp_quartermaster",
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
            "camp_quartermaster",
        )
        assert completion["completed_quest_id"] == quest_id
        apply_npc_conversation_result(player, quests, completion)

    assert all(quest_id in player["quests"]["completed"] for quest_id in BRINDLE_QUEST_IDS)
