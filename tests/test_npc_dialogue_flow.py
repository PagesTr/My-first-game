import json
from pathlib import Path

from systems.dialogues import (
    apply_npc_conversation_result,
    build_npc_conversation,
)
from systems.quests import create_player_quests


PROJECT_ROOT = Path(__file__).resolve().parent.parent
BRINDLE_FIRST_QUEST_ID = "forest_brindle_pest_control_officially"
MAELA_FIRST_QUEST_ID = "forest_maela_polite_amount_leaves"
FEN_FIRST_QUEST_ID = "forest_fen_scouts_honor_used_once"


def load_json(relative_path):
    path = PROJECT_ROOT / relative_path
    with path.open(encoding="utf-8") as data_file:
        return json.load(data_file)


def load_data():
    return (
        load_json("data/npcs.json"),
        load_json("data/quests.json"),
        load_json("data/npc_dialogues.json"),
    )


def create_player(quests_data):
    return {
        "quests": create_player_quests(quests_data),
    }


def test_first_npc_conversation_contains_intro_and_offer():
    npcs, quests, dialogues = load_data()
    player = create_player(quests)

    conversation = build_npc_conversation(
        player,
        npcs,
        quests,
        dialogues,
        "camp_quartermaster",
    )

    states = [page["state"] for page in conversation["pages"]]
    assert states[0] == "intro"
    assert "quest_offer" in states
    assert states[-1] == "quest_summary"
    assert conversation["accept_quest_id"] == BRINDLE_FIRST_QUEST_ID
    assert player["quests"]["active"] == []


def test_finishing_offer_marks_intro_and_activates_quest():
    npcs, quests, dialogues = load_data()
    player = create_player(quests)
    conversation = build_npc_conversation(
        player,
        npcs,
        quests,
        dialogues,
        "camp_quartermaster",
    )

    result = apply_npc_conversation_result(player, quests, conversation)

    assert result["introduced"] is True
    assert result["accepted_quest_id"] == BRINDLE_FIRST_QUEST_ID
    assert "camp_quartermaster" in player["npc_dialogue_state"]["introduced_npcs"]
    assert player["quests"]["available"] == [
        MAELA_FIRST_QUEST_ID,
        FEN_FIRST_QUEST_ID,
    ]
    assert player["quests"]["active"] == [BRINDLE_FIRST_QUEST_ID]


def test_active_quest_conversation_uses_progress_without_repeating_intro():
    npcs, quests, dialogues = load_data()
    player = create_player(quests)
    first_conversation = build_npc_conversation(
        player,
        npcs,
        quests,
        dialogues,
        "camp_quartermaster",
    )
    apply_npc_conversation_result(player, quests, first_conversation)

    conversation = build_npc_conversation(
        player,
        npcs,
        quests,
        dialogues,
        "camp_quartermaster",
    )

    states = [page["state"] for page in conversation["pages"]]
    assert states[0] == "progress"
    assert states[-1] == "quest_summary"
    assert "intro" not in states
    assert conversation["accept_quest_id"] is None


def test_different_npcs_can_offer_quests_at_the_same_time():
    npcs, quests, dialogues = load_data()
    player = create_player(quests)

    brindle = build_npc_conversation(
        player,
        npcs,
        quests,
        dialogues,
        "camp_quartermaster",
    )
    maela = build_npc_conversation(
        player,
        npcs,
        quests,
        dialogues,
        "old_herbalist",
    )
    fen = build_npc_conversation(
        player,
        npcs,
        quests,
        dialogues,
        "retired_scout",
    )

    assert brindle["accept_quest_id"] == BRINDLE_FIRST_QUEST_ID
    assert maela["accept_quest_id"] == MAELA_FIRST_QUEST_ID
    assert fen["accept_quest_id"] == FEN_FIRST_QUEST_ID
    assert brindle["pages"][-1]["state"] == "quest_summary"
    assert maela["pages"][-1]["state"] == "quest_summary"
    assert fen["pages"][-1]["state"] == "quest_summary"


def test_completed_quest_conversation_is_shown_once():
    npcs, quests, dialogues = load_data()
    player = create_player(quests)
    player["quests"]["available"] = []
    player["quests"]["completed"] = [BRINDLE_FIRST_QUEST_ID]
    player["npc_dialogue_state"] = {
        "introduced_npcs": ["camp_quartermaster"],
        "completed_quests_seen": [],
    }

    conversation = build_npc_conversation(
        player,
        npcs,
        quests,
        dialogues,
        "camp_quartermaster",
    )

    states = [page["state"] for page in conversation["pages"]]
    assert states[0] == "completion"
    assert states[-1] == "transition"
    apply_npc_conversation_result(player, quests, conversation)
    assert player["npc_dialogue_state"]["completed_quests_seen"] == [BRINDLE_FIRST_QUEST_ID]
