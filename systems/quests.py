from copy import deepcopy

from systems.inventory import add_individual_item, add_stackable_item


SUPPORTED_EVENT_TYPES = {
    "kill_enemy",
    "gather_item",
    "craft_recipe",
    "talk_to_npc",
    "clear_dungeon",
    "defeat_boss",
}

LEGACY_QUEST_ID_MIGRATIONS = {
    "forest_secure_outskirts": "forest_brindle_pest_control_officially",
    "forest_first_harvest": "forest_maela_polite_amount_leaves",
    "forest_pack_watches": "forest_fen_tracks_facing_wrong_way",
    "forest_smoke_above_trees": "forest_fen_smoke_beyond_trees",
    "forest_bones_under_roots": "forest_osric_bones_without_appointment",
    "forest_clear_goblin_camp": "forest_marn_break_goblin_camp",
    "forest_buried_grove": "forest_marn_rootbound_warning",
    "forest_silence_rootcaller": "forest_marn_grubfang_must_fall",
}

LEGACY_QUEST_PREDECESSOR_BACKFILLS = {
    "forest_pack_watches": [
        "forest_fen_scouts_honor_used_once",
    ],
    "forest_smoke_above_trees": [
        "forest_fen_scouts_honor_used_once",
        "forest_fen_tracks_facing_wrong_way",
        "forest_fen_shortcut_got_longer",
        "forest_fen_goblin_signs_terrible_arrows",
        "forest_fen_path_not_run_from",
    ],
    "forest_clear_goblin_camp": [
        "forest_marn_gate_not_decorative",
        "forest_marn_noise_goblin_camp",
    ],
    "forest_buried_grove": [
        "forest_marn_gate_not_decorative",
        "forest_marn_noise_goblin_camp",
        "forest_marn_break_goblin_camp",
        "forest_marn_buried_grove_stirs",
    ],
    "forest_silence_rootcaller": [
        "forest_marn_gate_not_decorative",
        "forest_marn_noise_goblin_camp",
        "forest_marn_break_goblin_camp",
        "forest_marn_buried_grove_stirs",
        "forest_marn_rootbound_warning",
        "forest_marn_rootcallers_door",
    ],
}

LEGACY_QUEST_PROGRESS_KEYS = {
    "forest_secure_outskirts": {"0"},
    "forest_first_harvest": {"0"},
    "forest_pack_watches": {"0"},
    "forest_smoke_above_trees": set(),
    "forest_bones_under_roots": {"0"},
    "forest_clear_goblin_camp": {"0"},
    "forest_buried_grove": {"0"},
    "forest_silence_rootcaller": {"0"},
}


def create_player_quests(quests_data):
    quests_data = quests_data if isinstance(quests_data, dict) else {}
    available_quests = [
        quest_id
        for quest_id, quest in sorted(
            quests_data.items(),
            key=lambda entry: entry[1].get("order", 0) if isinstance(entry[1], dict) else 0,
        )
        if isinstance(quest, dict) and not quest.get("required_quests", [])
    ]
    return {
        "available": available_quests,
        "active": [],
        "completed": [],
        "progress": {},
        "last_completed": [],
    }


def ensure_player_quests(player, quests_data):
    if not isinstance(player, dict):
        return create_player_quests(quests_data)

    quests = player.get("quests")
    if not isinstance(quests, dict):
        quests = create_player_quests(quests_data)
        player["quests"] = quests

    backfilled_quest_ids = _migrate_legacy_quest_state(quests, quests_data)
    _migrate_legacy_dialogue_state(player, backfilled_quest_ids)

    quests.setdefault("available", [])
    quests.setdefault("active", [])
    quests.setdefault("completed", [])
    quests.setdefault("progress", {})
    quests.setdefault("last_completed", [])

    if not isinstance(quests["available"], list):
        quests["available"] = []
    if not isinstance(quests["active"], list):
        quests["active"] = []
    if not isinstance(quests["completed"], list):
        quests["completed"] = []
    if not isinstance(quests["progress"], dict):
        quests["progress"] = {}
    if not isinstance(quests["last_completed"], list):
        quests["last_completed"] = []

    if not quests["available"] and not quests["active"] and not quests["completed"]:
        quests["available"] = create_player_quests(quests_data)["available"]
    _refresh_available_quests_state(quests, quests_data)
    return quests


def get_available_quests(player, quests_data):
    quests = ensure_player_quests(player, quests_data)
    available_quests = []
    for quest_id in quests.get("available", []):
        quest = quests_data.get(quest_id)
        if isinstance(quest, dict):
            quest_entry = deepcopy(quest)
            quest_entry["id"] = quest_id
            available_quests.append(quest_entry)
    return available_quests


def accept_quest(player, quests_data, quest_id):
    quests = ensure_player_quests(player, quests_data)
    if quest_id not in quests_data or quest_id not in quests.get("available", []):
        return False
    if quest_id in quests.get("completed", []):
        return False

    quests["available"].remove(quest_id)
    if quest_id not in quests["active"]:
        quests["active"].append(quest_id)
    return True


def refresh_available_quests(player, quests_data):
    previous_available = set()
    if isinstance(player, dict) and isinstance(player.get("quests"), dict):
        available = player["quests"].get("available", [])
        if isinstance(available, list):
            previous_available.update(available)
    quests = ensure_player_quests(player, quests_data)
    return [
        quest_id
        for quest_id in quests.get("available", [])
        if quest_id not in previous_available
    ]


def get_active_quests(player, quests_data):
    quests = ensure_player_quests(player, quests_data)
    active_quests = []
    for quest_id in quests.get("active", []):
        quest = quests_data.get(quest_id)
        if isinstance(quest, dict):
            quest_entry = deepcopy(quest)
            quest_entry["id"] = quest_id
            active_quests.append(quest_entry)
    return active_quests


def get_quest_progress(player, quest_id, objective_index):
    if not isinstance(player, dict):
        return 0
    quests = player.get("quests", {})
    progress = quests.get("progress", {}) if isinstance(quests, dict) else {}
    quest_progress = progress.get(quest_id, {}) if isinstance(progress, dict) else {}
    return int(quest_progress.get(str(objective_index), 0))


def record_quest_event(player, quests_data, event):
    if not isinstance(player, dict) or not isinstance(event, dict):
        return {"updated": False, "completed": []}

    event_type = event.get("type")
    target = event.get("target")
    amount = event.get("amount", 1)
    if event_type not in SUPPORTED_EVENT_TYPES or not target:
        return {"updated": False, "completed": []}
    if not isinstance(amount, int) or amount <= 0:
        return {"updated": False, "completed": []}

    quests = ensure_player_quests(player, quests_data)
    updated = False
    for quest_id in list(quests.get("active", [])):
        quest = quests_data.get(quest_id, {})
        objectives = quest.get("objectives", []) if isinstance(quest, dict) else []
        quest_progress = quests["progress"].setdefault(quest_id, {})
        for index, objective in enumerate(objectives):
            if not _objective_matches_event(objective, event_type, target):
                continue
            key = str(index)
            required = int(objective.get("required", 0))
            current = int(quest_progress.get(key, 0))
            new_value = min(required, current + amount)
            if new_value != current:
                quest_progress[key] = new_value
                updated = True

    completed = complete_ready_quests(player, quests_data)
    return {"updated": updated, "completed": completed}


def is_quest_completed(player, quests_data, quest_id):
    quest = quests_data.get(quest_id)
    if not isinstance(quest, dict):
        return False

    objectives = quest.get("objectives", [])
    if not isinstance(objectives, list) or not objectives:
        return False

    for index, objective in enumerate(objectives):
        required = objective.get("required", 0)
        if get_quest_progress(player, quest_id, index) < required:
            return False
    return True


def complete_ready_quests(player, quests_data):
    quests = ensure_player_quests(player, quests_data)
    completed_now = []
    for quest_id in list(quests.get("active", [])):
        if not is_quest_completed(player, quests_data, quest_id):
            continue

        quest = quests_data.get(quest_id, {})
        quests["active"].remove(quest_id)
        if quest_id not in quests["completed"]:
            quests["completed"].append(quest_id)
        quests["last_completed"].append(quest_id)
        quests["last_completed"] = quests["last_completed"][-5:]
        apply_quest_rewards(player, quest, None)
        completed_now.append(quest_id)
    _refresh_available_quests_state(quests, quests_data)
    return completed_now


def _refresh_available_quests_state(quests, quests_data):
    added = []
    completed = set(quests.get("completed", []))
    unavailable_ids = set(quests.get("available", []))
    unavailable_ids.update(quests.get("active", []))
    unavailable_ids.update(completed)

    ordered_quests = sorted(
        quests_data.items(),
        key=lambda entry: entry[1].get("order", 0) if isinstance(entry[1], dict) else 0,
    )
    for quest_id, quest in ordered_quests:
        if quest_id in unavailable_ids or not isinstance(quest, dict):
            continue
        required_quests = quest.get("required_quests", [])
        if not isinstance(required_quests, list):
            continue
        if all(required_quest_id in completed for required_quest_id in required_quests):
            quests["available"].append(quest_id)
            unavailable_ids.add(quest_id)
            added.append(quest_id)
    return added


def _migrate_legacy_quest_state(quests, quests_data):
    legacy_ids_present = set()
    for state_key in ("available", "active", "completed", "last_completed"):
        quest_ids = quests.get(state_key)
        if isinstance(quest_ids, list):
            legacy_ids_present.update(
                quest_id for quest_id in quest_ids if quest_id in LEGACY_QUEST_ID_MIGRATIONS
            )
    progress = quests.get("progress")
    if isinstance(progress, dict):
        legacy_ids_present.update(
            quest_id for quest_id in progress if quest_id in LEGACY_QUEST_ID_MIGRATIONS
        )

    for state_key in ("available", "active", "completed", "last_completed"):
        quest_ids = quests.get(state_key)
        if not isinstance(quest_ids, list):
            continue
        migrated_ids = []
        for quest_id in quest_ids:
            migrated_id = LEGACY_QUEST_ID_MIGRATIONS.get(quest_id, quest_id)
            if quest_id in LEGACY_QUEST_ID_MIGRATIONS and migrated_id not in quests_data:
                migrated_id = quest_id
            if migrated_id in migrated_ids:
                continue
            migrated_ids.append(migrated_id)
        quests[state_key] = migrated_ids

    progress = quests.get("progress")
    if not isinstance(progress, dict):
        progress = {}
        quests["progress"] = progress
    for legacy_id, migrated_id in LEGACY_QUEST_ID_MIGRATIONS.items():
        legacy_progress = progress.pop(legacy_id, None)
        if legacy_progress is not None and migrated_id in quests_data:
            allowed_keys = LEGACY_QUEST_PROGRESS_KEYS.get(legacy_id)
            if isinstance(legacy_progress, dict) and allowed_keys is not None:
                legacy_progress = {
                    key: value
                    for key, value in legacy_progress.items()
                    if key in allowed_keys
                }
            progress.setdefault(migrated_id, legacy_progress)

    completed = quests.get("completed")
    if not isinstance(completed, list):
        completed = []
        quests["completed"] = completed
    backfilled_quest_ids = []
    occupied_ids = set(completed)
    occupied_ids.update(quests.get("available", []) if isinstance(quests.get("available"), list) else [])
    occupied_ids.update(quests.get("active", []) if isinstance(quests.get("active"), list) else [])
    for legacy_id in LEGACY_QUEST_ID_MIGRATIONS:
        if legacy_id not in legacy_ids_present:
            continue
        for quest_id in LEGACY_QUEST_PREDECESSOR_BACKFILLS.get(legacy_id, []):
            if quest_id not in quests_data or quest_id in occupied_ids:
                continue
            completed.append(quest_id)
            occupied_ids.add(quest_id)
            backfilled_quest_ids.append(quest_id)
    return backfilled_quest_ids


def _migrate_legacy_dialogue_state(player, backfilled_quest_ids=None):
    dialogue_state = player.get("npc_dialogue_state") if isinstance(player, dict) else None
    if not isinstance(dialogue_state, dict):
        if not backfilled_quest_ids:
            return
        dialogue_state = {
            "introduced_npcs": [],
            "completed_quests_seen": [],
        }
        player["npc_dialogue_state"] = dialogue_state
    completed_seen = dialogue_state.get("completed_quests_seen")
    if not isinstance(completed_seen, list):
        completed_seen = []
    completed_seen = list(dict.fromkeys(
        LEGACY_QUEST_ID_MIGRATIONS.get(quest_id, quest_id)
        for quest_id in completed_seen
    ))
    for quest_id in backfilled_quest_ids or []:
        if quest_id not in completed_seen:
            completed_seen.append(quest_id)
    dialogue_state["completed_quests_seen"] = completed_seen


def apply_quest_rewards(player, quest, items):
    failed_rewards = []
    if not isinstance(player, dict) or not isinstance(quest, dict):
        return {"applied": [], "failed_rewards": failed_rewards}

    applied = []
    for reward in quest.get("rewards", []):
        if not isinstance(reward, dict):
            continue
        reward_type = reward.get("type")
        if reward_type == "gold":
            amount = int(reward.get("amount", 0))
            player["gold"] = player.get("gold", 0) + amount
            applied.append(dict(reward))
        elif reward_type == "xp":
            amount = int(reward.get("amount", 0))
            player["exp"] = player.get("exp", 0) + amount
            applied.append(dict(reward))
        elif reward_type == "item":
            if _apply_item_reward(player, reward, items):
                applied.append(dict(reward))
            else:
                failed_rewards.append(dict(reward))
    return {"applied": applied, "failed_rewards": failed_rewards}


def _objective_matches_event(objective, event_type, target):
    return (
        isinstance(objective, dict)
        and objective.get("type") == event_type
        and objective.get("target") == target
    )


def _apply_item_reward(player, reward, items):
    inventory = player.get("inventory")
    if not isinstance(inventory, dict):
        return False

    item_id = reward.get("item")
    quantity = int(reward.get("quantity", 1))
    item_data = items.get(item_id, {}) if isinstance(items, dict) else {}
    if item_data.get("type") == "equipment":
        return add_individual_item(
            inventory,
            {
                "kind": "individual",
                "item": item_id,
                "rarity": item_data.get("rarity", "common"),
                "stats": deepcopy(item_data.get("stats", {})),
            },
        )
    return add_stackable_item(inventory, item_id, quantity)
