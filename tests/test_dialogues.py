import json
from pathlib import Path

from core.dataManager import DataManager
from systems.dialogues import (
    get_npc_dialogues,
    get_npc_intro,
    get_quest_dialogues,
    select_quest_dialogue,
    validate_dialogue_data,
)


PROJECT_ROOT = Path(__file__).resolve().parent.parent
DIALOGUES_PATH = PROJECT_ROOT / "data" / "npc_dialogues.json"
NPCS_PATH = PROJECT_ROOT / "data" / "npcs.json"
QUESTS_PATH = PROJECT_ROOT / "data" / "quests.json"


def load_json(path):
    with path.open(encoding="utf-8") as data_file:
        return json.load(data_file)


def load_dialogues():
    return load_json(DIALOGUES_PATH)


def load_npcs():
    return load_json(NPCS_PATH)


def load_quests():
    return load_json(QUESTS_PATH)


def test_dialogues_validate_against_npcs_and_quests():
    dialogues = load_dialogues()
    npcs = load_npcs()
    quests = load_quests()

    assert validate_dialogue_data(dialogues, npcs, quests) == []


def test_every_forest_quest_has_dialogue_entry():
    dialogues = load_dialogues()
    quests = load_quests()

    for quest_id, quest in quests.items():
        if quest.get("chapter") != "forest":
            continue
        npc_dialogues = dialogues[quest["npc_id"]]
        assert quest_id in npc_dialogues["quests"]


def test_get_npc_dialogues_returns_dialogues_or_none():
    dialogues = load_dialogues()

    assert get_npc_dialogues(dialogues, "dungeon_warden")["intro"]
    assert get_npc_dialogues(dialogues, "unknown_npc") is None


def test_get_npc_intro_returns_text_or_empty_string():
    dialogues = load_dialogues()

    assert "Marn" in get_npc_intro(dialogues, "dungeon_warden")
    assert get_npc_intro(dialogues, "unknown_npc") == ""


def test_get_quest_dialogues_uses_quest_npc_id():
    dialogues = load_dialogues()
    npcs = load_npcs()
    quests = load_quests()

    quest_dialogues = get_quest_dialogues(
        dialogues,
        npcs,
        quests,
        "forest_fen_smoke_beyond_trees",
    )

    assert "smoke beyond the trees" in quest_dialogues["quest_offer"].lower()


def test_select_quest_dialogue_returns_requested_state():
    dialogues = load_dialogues()
    npcs = load_npcs()
    quests = load_quests()

    text = select_quest_dialogue(
        dialogues,
        npcs,
        quests,
        "forest_marn_rootbound_warning",
        "completion",
    )

    assert "Remnant has fallen" in text


def test_select_quest_dialogue_falls_back_to_offer_for_unknown_state():
    dialogues = load_dialogues()
    npcs = load_npcs()
    quests = load_quests()

    text = select_quest_dialogue(
        dialogues,
        npcs,
        quests,
        "forest_marn_grubfang_must_fall",
        "unknown_state",
    )

    assert text == dialogues["dungeon_warden"]["quests"]["forest_marn_grubfang_must_fall"]["quest_offer"]


def test_select_quest_dialogue_returns_empty_string_for_unknown_quest():
    dialogues = load_dialogues()
    npcs = load_npcs()
    quests = load_quests()

    assert select_quest_dialogue(dialogues, npcs, quests, "unknown_quest", "quest_offer") == ""


def test_data_manager_loads_npc_dialogues():
    data = DataManager()

    assert "dungeon_warden" in data.npc_dialogues
    assert "forest_marn_grubfang_must_fall" in data.npc_dialogues["dungeon_warden"]["quests"]
