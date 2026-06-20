import json
from pathlib import Path

from core.dataManager import DataManager
from systems.npcs import (
    get_npc,
    get_npc_for_quest,
    get_npc_quest_ids,
    get_npcs_by_chapter,
    validate_npc_data,
)


PROJECT_ROOT = Path(__file__).resolve().parent.parent
NPCS_PATH = PROJECT_ROOT / "data" / "npcs.json"
QUESTS_PATH = PROJECT_ROOT / "data" / "quests.json"

EXPECTED_FOREST_NPC_IDS = {
    "camp_quartermaster",
    "old_herbalist",
    "bone_scribe",
    "retired_scout",
    "dungeon_warden",
}


def load_json(path):
    with path.open(encoding="utf-8") as data_file:
        return json.load(data_file)


def load_npcs():
    return load_json(NPCS_PATH)


def load_quests():
    return load_json(QUESTS_PATH)


def test_forest_npcs_exist():
    npcs = load_npcs()

    assert set(npcs) == EXPECTED_FOREST_NPC_IDS


def test_forest_npcs_have_required_metadata():
    npcs = load_npcs()

    for npc_id in EXPECTED_FOREST_NPC_IDS:
        npc = npcs[npc_id]
        assert npc.get("name")
        assert npc.get("chapter") == "forest"
        assert npc.get("role")
        assert npc.get("tone")
        assert isinstance(npc.get("related_quests"), list)
        assert npc["related_quests"]
        assert isinstance(npc.get("related_zones"), list)


def test_npc_related_quests_reference_existing_quests():
    npcs = load_npcs()
    quests = load_quests()

    for npc in npcs.values():
        for quest_id in npc["related_quests"]:
            assert quest_id in quests


def test_forest_quests_have_valid_npc_links():
    npcs = load_npcs()
    quests = load_quests()

    for quest_id, quest in quests.items():
        if quest.get("chapter") != "forest":
            continue
        npc_id = quest.get("npc_id")
        assert npc_id in npcs
        assert quest_id in npcs[npc_id]["related_quests"]


def test_validate_npc_data_accepts_current_data():
    npcs = load_npcs()
    quests = load_quests()

    assert validate_npc_data(npcs, quests) == []


def test_get_npc_returns_npc_or_none():
    npcs = load_npcs()

    assert get_npc(npcs, "camp_quartermaster")["name"] == "Quartermaster Brindle"
    assert get_npc(npcs, "unknown_npc") is None


def test_get_npcs_by_chapter_filters_npcs():
    npcs = load_npcs()

    forest_npcs = get_npcs_by_chapter(npcs, "forest")

    assert set(forest_npcs) == EXPECTED_FOREST_NPC_IDS
    assert get_npcs_by_chapter(npcs, "caves") == {}


def test_get_npc_quest_ids_returns_related_quests():
    npcs = load_npcs()

    assert get_npc_quest_ids(npcs, "retired_scout") == [
        "forest_fen_scouts_honor_used_once",
        "forest_fen_tracks_facing_wrong_way",
        "forest_fen_shortcut_got_longer",
        "forest_fen_goblin_signs_terrible_arrows",
        "forest_fen_path_not_run_from",
        "forest_fen_smoke_beyond_trees",
    ]
    assert get_npc_quest_ids(npcs, "unknown_npc") == []


def test_get_npc_for_quest_uses_quest_npc_id():
    npcs = load_npcs()
    quests = load_quests()

    npc = get_npc_for_quest(npcs, quests, "forest_maela_polite_amount_leaves")

    assert npc["name"] == "Maela the Herbalist"


def test_data_manager_loads_npcs():
    data = DataManager()

    assert set(data.npcs) == EXPECTED_FOREST_NPC_IDS
