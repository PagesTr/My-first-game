import json
from pathlib import Path

from systems.dialogues import apply_npc_conversation_result, build_npc_conversation
from systems.inventory import create_inventory
from systems.quests import create_player_quests, ensure_player_quests, record_quest_event


PROJECT_ROOT = Path(__file__).resolve().parent.parent

MARN_QUEST_IDS = [
    "forest_marn_gate_not_decorative",
    "forest_marn_noise_goblin_camp",
    "forest_marn_break_goblin_camp",
    "forest_marn_buried_grove_stirs",
    "forest_marn_rootbound_warning",
    "forest_marn_rootcallers_door",
    "forest_marn_grubfang_must_fall",
]

EXPECTED_TITLES = [
    "The Gate Is Not Decorative",
    "Noise from Goblin Camp",
    "Break the Goblin Camp",
    "Buried Grove Stirs",
    "The Rootbound Warning",
    "Rootcaller's Door",
    "Grubfang Must Fall",
]


def load_json(relative_path):
    with (PROJECT_ROOT / relative_path).open(encoding="utf-8") as data_file:
        return json.load(data_file)


def test_marn_has_seven_official_core_quests_in_order():
    quests = load_json("data/quests.json")
    npcs = load_json("data/npcs.json")

    assert npcs["dungeon_warden"]["related_quests"] == MARN_QUEST_IDS
    assert [quests[quest_id]["name"] for quest_id in MARN_QUEST_IDS] == EXPECTED_TITLES
    assert "forest_clear_goblin_camp" not in quests
    assert "forest_buried_grove" not in quests
    assert "forest_silence_rootcaller" not in quests


def test_marn_core_quests_form_the_expected_chain():
    quests = load_json("data/quests.json")

    assert quests[MARN_QUEST_IDS[0]]["required_quests"] == [
        "forest_brindle_forwarded_to_gate",
        "forest_fen_smoke_beyond_trees",
    ]
    assert quests[MARN_QUEST_IDS[3]]["required_quests"] == [
        MARN_QUEST_IDS[2],
        "forest_maela_cure_might_apologize",
        "forest_osric_grave_administrative_error",
    ]
    for previous_id, quest_id in zip(MARN_QUEST_IDS, MARN_QUEST_IDS[1:]):
        assert previous_id in quests[quest_id]["required_quests"]
        assert quest_id in quests[previous_id]["next_quests"]


def test_marn_objectives_use_supported_existing_targets():
    quests = load_json("data/quests.json")
    npcs = load_json("data/npcs.json")
    items = load_json("data/items.json")
    recipes = load_json("data/recipes.json")
    dungeons = load_json("data/dungeons.json")
    enemies = load_json("data/enemies.json")
    targets = {
        "talk_to_npc": npcs,
        "gather_item": items,
        "craft_recipe": recipes,
        "clear_dungeon": dungeons,
        "defeat_boss": enemies,
    }

    for quest_id in MARN_QUEST_IDS:
        objective = quests[quest_id]["objectives"][0]
        assert quests[quest_id]["npc_id"] == "dungeon_warden"
        assert len(quests[quest_id]["objectives"]) == 1
        assert objective["type"] in targets
        assert objective["target"] in targets[objective["type"]]
        assert objective["required"] > 0


def test_marn_dialogues_cover_every_core_quest_state():
    dialogues = load_json("data/npc_dialogues.json")["dungeon_warden"]

    assert len(dialogues["intro"].split("\n\n")) >= 9
    assert set(dialogues["quests"]) == set(MARN_QUEST_IDS)
    for quest_id in MARN_QUEST_IDS:
        assert set(dialogues["quests"][quest_id]) == {
            "quest_offer",
            "progress",
            "completion",
            "transition",
        }


def test_talking_to_marn_completes_the_gate_quest_after_acceptance():
    quests = load_json("data/quests.json")
    npcs = load_json("data/npcs.json")
    dialogues = load_json("data/npc_dialogues.json")
    player = {
        "gold": 0,
        "exp": 0,
        "inventory": create_inventory(),
        "quests": create_player_quests(quests),
    }
    player["quests"]["completed"].extend([
        "forest_brindle_forwarded_to_gate",
        "forest_fen_smoke_beyond_trees",
    ])
    ensure_player_quests(player, quests)

    offer = build_npc_conversation(player, npcs, quests, dialogues, "dungeon_warden")
    result = apply_npc_conversation_result(player, quests, offer)

    assert result["accepted_quest_id"] == MARN_QUEST_IDS[0]
    assert MARN_QUEST_IDS[0] in player["quests"]["completed"]
    assert MARN_QUEST_IDS[1] in player["quests"]["available"]


def test_legacy_marn_quest_states_are_migrated_with_prior_steps_backfilled():
    quests = load_json("data/quests.json")
    cases = [
        ("forest_clear_goblin_camp", 2, MARN_QUEST_IDS[2]),
        ("forest_buried_grove", 4, MARN_QUEST_IDS[4]),
        ("forest_silence_rootcaller", 6, MARN_QUEST_IDS[6]),
    ]

    for legacy_id, predecessor_count, migrated_id in cases:
        player = {
            "quests": {
                "available": [],
                "active": [legacy_id],
                "completed": [],
                "progress": {legacy_id: {"0": 1}},
                "last_completed": [],
            }
        }

        state = ensure_player_quests(player, quests)

        assert migrated_id in state["active"]
        assert state["progress"][migrated_id] == {"0": 1}
        assert all(quest_id in state["completed"] for quest_id in MARN_QUEST_IDS[:predecessor_count])


def test_marn_core_arc_can_be_completed_in_sequence():
    quests = load_json("data/quests.json")
    npcs = load_json("data/npcs.json")
    dialogues = load_json("data/npc_dialogues.json")
    player = {
        "gold": 0,
        "exp": 0,
        "inventory": create_inventory(),
        "quests": create_player_quests(quests),
    }
    player["quests"]["completed"].extend([
        "forest_brindle_forwarded_to_gate",
        "forest_fen_smoke_beyond_trees",
        "forest_maela_cure_might_apologize",
        "forest_osric_grave_administrative_error",
    ])
    ensure_player_quests(player, quests)

    for quest_id in MARN_QUEST_IDS:
        offer = build_npc_conversation(player, npcs, quests, dialogues, "dungeon_warden")
        assert offer["accept_quest_id"] == quest_id
        apply_npc_conversation_result(player, quests, offer)

        objective = quests[quest_id]["objectives"][0]
        if objective["type"] != "talk_to_npc":
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
        else:
            assert quest_id in player["quests"]["completed"]

        completion = build_npc_conversation(player, npcs, quests, dialogues, "dungeon_warden")
        assert completion["completed_quest_id"] == quest_id
        apply_npc_conversation_result(player, quests, completion)

    assert all(quest_id in player["quests"]["completed"] for quest_id in MARN_QUEST_IDS)
