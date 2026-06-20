import json
from pathlib import Path

from systems.dialogues import apply_npc_conversation_result, build_npc_conversation
from systems.inventory import create_inventory
from systems.quests import create_player_quests, ensure_player_quests, record_quest_event


PROJECT_ROOT = Path(__file__).resolve().parent.parent

MAELA_QUEST_IDS = [
    "forest_maela_polite_amount_leaves",
    "forest_maela_remedies_bite_shaped_mistakes",
    "forest_maela_mushrooms_with_opinions",
    "forest_maela_roots_should_not_twitch",
    "forest_maela_sap_is_listening",
    "forest_maela_cure_might_apologize",
]

EXPECTED_TITLES = [
    "A Polite Amount of Leaves",
    "Remedies for Bite-Shaped Mistakes",
    "Mushrooms With Opinions",
    "Roots Should Not Twitch",
    "The Sap Is Listening",
    "A Cure That Might Apologize",
]


def load_json(relative_path):
    with (PROJECT_ROOT / relative_path).open(encoding="utf-8") as data_file:
        return json.load(data_file)


def test_maela_has_six_official_core_quests_in_order():
    quests = load_json("data/quests.json")
    npcs = load_json("data/npcs.json")

    assert npcs["old_herbalist"]["related_quests"] == MAELA_QUEST_IDS
    assert [quests[quest_id]["name"] for quest_id in MAELA_QUEST_IDS] == EXPECTED_TITLES
    assert "forest_first_harvest" not in quests


def test_maela_core_quests_form_a_sequential_chain():
    quests = load_json("data/quests.json")

    assert quests[MAELA_QUEST_IDS[0]]["required_quests"] == []
    for previous_id, quest_id in zip(MAELA_QUEST_IDS, MAELA_QUEST_IDS[1:]):
        assert quests[quest_id]["required_quests"] == [previous_id]
        assert quest_id in quests[previous_id]["next_quests"]


def test_maela_objectives_use_existing_gathering_or_recipe_targets():
    quests = load_json("data/quests.json")
    items = load_json("data/items.json")
    recipes = load_json("data/recipes.json")

    for quest_id in MAELA_QUEST_IDS:
        quest = quests[quest_id]
        assert quest["npc_id"] == "old_herbalist"
        assert len(quest["objectives"]) == 1
        objective = quest["objectives"][0]
        assert objective["type"] in {"gather_item", "craft_recipe"}
        if objective["type"] == "gather_item":
            assert objective["target"] in items
        else:
            assert objective["target"] in recipes


def test_maela_dialogues_cover_every_core_quest_state():
    dialogues = load_json("data/npc_dialogues.json")["old_herbalist"]

    assert len(dialogues["intro"].split("\n\n")) >= 5
    assert set(dialogues["quests"]) == set(MAELA_QUEST_IDS)
    for quest_id in MAELA_QUEST_IDS:
        assert set(dialogues["quests"][quest_id]) == {
            "quest_offer",
            "progress",
            "completion",
            "transition",
        }


def test_buried_grove_requires_maelas_final_core_quest():
    quests = load_json("data/quests.json")

    assert "forest_maela_cure_might_apologize" in quests["forest_marn_buried_grove_stirs"]["required_quests"]


def test_legacy_maela_quest_state_is_migrated():
    quests = load_json("data/quests.json")
    player = {
        "quests": {
            "available": [],
            "active": ["forest_first_harvest"],
            "completed": [],
            "progress": {"forest_first_harvest": {"0": 4}},
            "last_completed": [],
        },
        "npc_dialogue_state": {
            "introduced_npcs": ["old_herbalist"],
            "completed_quests_seen": ["forest_first_harvest"],
        },
    }

    state = ensure_player_quests(player, quests)

    assert MAELA_QUEST_IDS[0] in state["active"]
    assert state["progress"][MAELA_QUEST_IDS[0]] == {"0": 4}
    assert player["npc_dialogue_state"]["completed_quests_seen"] == [MAELA_QUEST_IDS[0]]


def test_maela_core_arc_can_be_completed_in_sequence():
    quests = load_json("data/quests.json")
    npcs = load_json("data/npcs.json")
    dialogues = load_json("data/npc_dialogues.json")
    player = {
        "gold": 0,
        "exp": 0,
        "inventory": create_inventory(),
        "quests": create_player_quests(quests),
    }

    for quest_id in MAELA_QUEST_IDS:
        offer = build_npc_conversation(
            player,
            npcs,
            quests,
            dialogues,
            "old_herbalist",
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
            "old_herbalist",
        )
        assert completion["completed_quest_id"] == quest_id
        apply_npc_conversation_result(player, quests, completion)

    assert all(quest_id in player["quests"]["completed"] for quest_id in MAELA_QUEST_IDS)
