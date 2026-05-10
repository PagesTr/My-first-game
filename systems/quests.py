from copy import deepcopy

from systems.inventory import add_individual_item, add_stackable_item


SUPPORTED_EVENT_TYPES = {"kill_enemy", "gather_item", "craft_recipe"}


def create_player_quests(quests_data):
    quests_data = quests_data if isinstance(quests_data, dict) else {}
    chained_quests = set()
    for quest in quests_data.values():
        if not isinstance(quest, dict):
            continue
        chained_quests.update(quest.get("next_quests", []))

    root_quests = [
        quest_id
        for quest_id, quest in sorted(
            quests_data.items(),
            key=lambda entry: entry[1].get("order", 0) if isinstance(entry[1], dict) else 0,
        )
        if quest_id not in chained_quests
    ]
    return {
        "active": root_quests,
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

    quests.setdefault("active", [])
    quests.setdefault("completed", [])
    quests.setdefault("progress", {})
    quests.setdefault("last_completed", [])

    if not isinstance(quests["active"], list):
        quests["active"] = []
    if not isinstance(quests["completed"], list):
        quests["completed"] = []
    if not isinstance(quests["progress"], dict):
        quests["progress"] = {}
    if not isinstance(quests["last_completed"], list):
        quests["last_completed"] = []

    if not quests["active"] and not quests["completed"]:
        quests["active"] = create_player_quests(quests_data)["active"]
    return quests


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
        for next_quest_id in quest.get("next_quests", []):
            if (
                next_quest_id in quests_data
                and next_quest_id not in quests["active"]
                and next_quest_id not in quests["completed"]
            ):
                quests["active"].append(next_quest_id)
        completed_now.append(quest_id)
    return completed_now


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
