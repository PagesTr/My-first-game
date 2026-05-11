from systems.inventory import add_individual_item, add_stackable_item


SUPPORTED_OBJECTIVE_TYPES = {
    "kill_enemy",
    "kill_family",
    "gather_profession",
    "gather_item",
    "craft_recipe",
    "craft_chapter",
    "clear_dungeon",
    "defeat_boss",
    "boss_victory_count",
    "equip_set_pieces",
}

SUPPORTED_REWARD_TYPES = {
    "gold",
    "item",
    "stat_bonus",
    "percent_bonus",
}


def create_player_achievements(achievements_data):
    return {
        "unlocked": [],
        "progress": {},
        "last_unlocked": [],
    }


def ensure_player_achievements(player, achievements_data):
    achievements = player.get("achievements")
    if not isinstance(achievements, dict):
        achievements = create_player_achievements(achievements_data)
        player["achievements"] = achievements

    if not isinstance(achievements.get("unlocked"), list):
        achievements["unlocked"] = []
    if not isinstance(achievements.get("progress"), dict):
        achievements["progress"] = {}
    if not isinstance(achievements.get("last_unlocked"), list):
        achievements["last_unlocked"] = []

    return achievements


def get_achievement(achievements_data, achievement_id):
    if not isinstance(achievements_data, dict):
        return None
    return achievements_data.get(achievement_id)


def get_achievement_progress(player, achievement_id):
    achievements = player.get("achievements", {})
    progress = achievements.get("progress", {})
    value = progress.get(achievement_id, 0)
    if not isinstance(value, int):
        return 0
    return value


def is_achievement_unlocked(player, achievement_id):
    achievements = player.get("achievements", {})
    unlocked = achievements.get("unlocked", [])
    return achievement_id in unlocked


def get_unlocked_achievements(player):
    achievements = player.get("achievements", {})
    unlocked = achievements.get("unlocked", [])
    if not isinstance(unlocked, list):
        return []
    return list(unlocked)


def get_visible_achievements(player, achievements_data, include_hidden=False):
    visible = []
    for achievement_id, achievement in achievements_data.items():
        hidden = achievement.get("hidden", False)
        if hidden and not include_hidden and not is_achievement_unlocked(player, achievement_id):
            continue
        visible.append({
            "id": achievement_id,
            "achievement": achievement,
        })

    visible.sort(
        key=lambda entry: (
            entry["achievement"].get("chapter", ""),
            entry["achievement"].get("category", ""),
            entry["achievement"].get("tier", 0),
            entry["id"],
        )
    )
    return visible


def record_achievement_event(player, achievements_data, event, items=None):
    amount = event.get("amount", 1) if isinstance(event, dict) else 0
    if not isinstance(amount, int) or amount <= 0:
        return {
            "updated": False,
            "unlocked": [],
        }

    achievements = ensure_player_achievements(player, achievements_data)
    updated = False
    newly_unlocked = []

    for achievement_id, achievement in achievements_data.items():
        if achievement_id in achievements["unlocked"]:
            continue

        objective = achievement.get("objective", {})
        if not _objective_matches_event(objective, event):
            continue

        required = objective.get("required", 0)
        if not isinstance(required, int) or required <= 0:
            continue

        current = get_achievement_progress(player, achievement_id)
        next_value = min(required, current + amount)
        if next_value != current:
            achievements["progress"][achievement_id] = next_value
            updated = True

        if next_value >= required and achievement_id not in achievements["unlocked"]:
            achievements["unlocked"].append(achievement_id)
            achievements["last_unlocked"].append(achievement_id)
            apply_achievement_rewards(player, achievement, items)
            newly_unlocked.append(achievement_id)
            updated = True

    return {
        "updated": updated,
        "unlocked": newly_unlocked,
    }


def apply_achievement_rewards(player, achievement, items=None):
    result = {
        "applied": [],
        "failed": [],
    }

    for reward in achievement.get("rewards", []):
        reward_type = reward.get("type")
        applied = False

        if reward_type == "gold":
            amount = reward.get("amount", 0)
            if isinstance(amount, (int, float)):
                player["gold"] = player.get("gold", 0) + amount
                applied = True
        elif reward_type in {"stat_bonus", "percent_bonus"}:
            stat = reward.get("stat")
            amount = reward.get("amount", 0)
            if isinstance(stat, str) and isinstance(amount, (int, float)):
                player[stat] = player.get(stat, 0) + amount
                applied = True
        elif reward_type == "item":
            applied = _apply_item_reward(player, reward, items)

        target = result["applied"] if applied else result["failed"]
        target.append(reward)

    return result


def clear_last_unlocked(player):
    achievements = player.get("achievements")
    if not isinstance(achievements, dict):
        return
    achievements["last_unlocked"] = []


def _objective_matches_event(objective, event):
    if not isinstance(objective, dict) or not isinstance(event, dict):
        return False

    objective_type = objective.get("type")
    target = objective.get("target")
    event_type = event.get("type")
    event_target = event.get("target")
    metadata = event.get("metadata", {})
    if not isinstance(metadata, dict):
        metadata = {}

    if objective_type == "kill_enemy":
        return event_type == "kill_enemy" and event_target == target
    if objective_type == "kill_family":
        return event_type == "kill_enemy" and metadata.get("family") == target
    if objective_type == "gather_profession":
        return event_type in {"gather_item", "gather_tick"} and metadata.get("profession_id") == target
    if objective_type == "gather_item":
        return event_type == "gather_item" and event_target == target
    if objective_type == "craft_recipe":
        return event_type == "craft_recipe" and event_target == target
    if objective_type == "craft_chapter":
        return event_type == "craft_recipe" and metadata.get("chapter") == target
    if objective_type == "clear_dungeon":
        return event_type == "clear_dungeon" and event_target == target
    if objective_type == "defeat_boss":
        return event_type == "defeat_boss" and event_target == target
    if objective_type == "boss_victory_count":
        return event_type == "defeat_boss" and event_target == target
    if objective_type == "equip_set_pieces":
        return (
            event_type == "equip_set_pieces"
            and (
                target == event_target
                or (target == "any_forest_set" and metadata.get("chapter") == "forest")
            )
        )
    return False


def _apply_item_reward(player, reward, items=None):
    inventory = player.get("inventory")
    if not isinstance(inventory, dict):
        return False

    item_id = reward.get("item")
    quantity = reward.get("quantity", 1)
    if not isinstance(item_id, str) or not isinstance(quantity, int) or quantity <= 0:
        return False

    item_data = items.get(item_id, {}) if isinstance(items, dict) else {}
    if item_data.get("type") == "equipment":
        added = True
        for _ in range(quantity):
            item_instance = {
                "item": item_id,
            }
            if not add_individual_item(inventory, item_instance):
                added = False
        return added

    return add_stackable_item(inventory, item_id, quantity)
