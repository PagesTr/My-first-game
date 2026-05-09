import time
from copy import deepcopy

from systems.gathering import gather_from_zone, get_gathering_node


DEFAULT_OFFLINE_TICK_SECONDS = 20.0
OFFLINE_EFFICIENCY = 0.25
OFFLINE_TICK_SECONDS = DEFAULT_OFFLINE_TICK_SECONDS


def get_current_timestamp():
    return int(time.time())


def create_offline_gathering_activity(zone_id, profession_id, current_time=None):
    if current_time is None:
        current_time = get_current_timestamp()
    return {
        "type": "gathering",
        "zone_id": zone_id,
        "profession_id": profession_id,
        "started_at": current_time,
        "last_claimed_at": current_time,
    }


def has_offline_activity(player):
    return isinstance(player, dict) and isinstance(player.get("offline_activity"), dict)


def start_offline_gathering(player, zone_id, profession_id, current_time=None):
    if not isinstance(player, dict):
        return {"started": False, "reason": "invalid_player"}
    if has_offline_activity(player):
        return {"started": False, "reason": "activity_already_active"}

    activity = create_offline_gathering_activity(
        zone_id,
        profession_id,
        current_time,
    )
    player["offline_activity"] = activity
    return {
        "started": True,
        "activity": deepcopy(activity),
    }


def stop_offline_activity(player):
    if not isinstance(player, dict):
        return False
    player["offline_activity"] = None
    return True


def get_offline_elapsed_seconds(player, current_time=None):
    if current_time is None:
        current_time = get_current_timestamp()
    if not has_offline_activity(player):
        return 0

    last_claimed_at = player["offline_activity"].get("last_claimed_at")
    if not isinstance(last_claimed_at, (int, float)):
        return 0
    return max(0, int(current_time - last_claimed_at))


def get_node_online_tick_seconds(node_data):
    if not isinstance(node_data, dict):
        return 5.0
    tick_seconds = node_data.get("tick_seconds", 5.0)
    if not isinstance(tick_seconds, (int, float)) or tick_seconds <= 0:
        return 5.0
    return float(tick_seconds)


def calculate_offline_tick_seconds(
    node_data,
    offline_efficiency=OFFLINE_EFFICIENCY,
):
    online_tick_seconds = get_node_online_tick_seconds(node_data)
    if not isinstance(offline_efficiency, (int, float)) or offline_efficiency <= 0:
        offline_efficiency = OFFLINE_EFFICIENCY
    return online_tick_seconds / offline_efficiency


def calculate_offline_ticks(
    elapsed_seconds,
    tick_seconds=DEFAULT_OFFLINE_TICK_SECONDS,
    max_ticks=None,
):
    if not isinstance(tick_seconds, (int, float)) or tick_seconds <= 0:
        tick_seconds = DEFAULT_OFFLINE_TICK_SECONDS
    tick_seconds = float(tick_seconds)

    elapsed_seconds = max(0, elapsed_seconds)
    if elapsed_seconds <= 0:
        return {
            "ticks": 0,
            "elapsed_seconds": int(elapsed_seconds),
            "tick_seconds": tick_seconds,
        }

    ticks = int(elapsed_seconds // tick_seconds)
    return {
        "ticks": int(ticks),
        "elapsed_seconds": int(elapsed_seconds),
        "tick_seconds": tick_seconds,
    }


def _merge_rewards(rewards):
    merged = {}
    for reward in rewards:
        if not isinstance(reward, dict):
            continue
        if reward.get("kind") != "stackable":
            continue
        item_id = reward.get("item")
        quantity = reward.get("quantity", 0)
        if not item_id or not isinstance(quantity, int) or quantity <= 0:
            continue
        merged[item_id] = merged.get(item_id, 0) + quantity

    return [
        {"kind": "stackable", "item": item_id, "quantity": quantity}
        for item_id, quantity in merged.items()
    ]


def resolve_offline_activity(
    player,
    gathering_nodes,
    professions_data,
    items,
    current_time=None,
):
    if not isinstance(player, dict):
        return {"resolved": False, "reason": "invalid_player"}
    if not has_offline_activity(player):
        return {"resolved": False, "reason": "no_activity"}

    activity = player["offline_activity"]
    if activity.get("type") != "gathering":
        return {"resolved": False, "reason": "unsupported_activity"}

    zone_id = activity.get("zone_id")
    profession_id = activity.get("profession_id")
    node_data = get_gathering_node(gathering_nodes, zone_id, profession_id)
    if node_data is None:
        return {"resolved": False, "reason": "unknown_node"}

    if current_time is None:
        current_time = get_current_timestamp()
    elapsed_seconds = get_offline_elapsed_seconds(player, current_time)
    online_tick_seconds = get_node_online_tick_seconds(node_data)
    offline_tick_seconds = calculate_offline_tick_seconds(node_data)
    tick_result = calculate_offline_ticks(elapsed_seconds, offline_tick_seconds)
    ticks = tick_result["ticks"]
    if ticks <= 0:
        return {
            "resolved": False,
            "reason": "not_enough_time",
            "elapsed_seconds": elapsed_seconds,
            "ticks": 0,
            "tick_seconds": offline_tick_seconds,
            "online_tick_seconds": online_tick_seconds,
            "offline_efficiency": OFFLINE_EFFICIENCY,
        }

    rewards = []
    failed = []
    total_xp = 0
    leveled_up = False
    inventory_full_failures = 0

    for _ in range(ticks):
        result = gather_from_zone(
            player,
            player["inventory"],
            zone_id,
            profession_id,
            gathering_nodes,
            professions_data,
            items,
        )
        if result.get("gathered") is True:
            rewards.extend(result.get("rewards", []))
            failed.extend(result.get("failed", []))
            total_xp += result.get("profession_xp", 0)
            leveled_up = leveled_up or result.get("leveled_up") is True
        elif result.get("reason") == "inventory_full":
            inventory_full_failures += 1
        else:
            failed.extend(result.get("failed", []))

    activity["last_claimed_at"] = current_time
    if not rewards and inventory_full_failures == ticks:
        return {
            "resolved": False,
            "reason": "inventory_full",
            "elapsed_seconds": elapsed_seconds,
            "ticks": ticks,
            "tick_seconds": offline_tick_seconds,
            "online_tick_seconds": online_tick_seconds,
            "offline_efficiency": OFFLINE_EFFICIENCY,
        }

    return {
        "resolved": True,
        "activity_type": "gathering",
        "zone_id": zone_id,
        "profession_id": profession_id,
        "elapsed_seconds": elapsed_seconds,
        "ticks": ticks,
        "tick_seconds": offline_tick_seconds,
        "online_tick_seconds": online_tick_seconds,
        "offline_efficiency": OFFLINE_EFFICIENCY,
        "rewards": _merge_rewards(rewards),
        "failed": _merge_rewards(failed),
        "profession_xp": total_xp,
        "leveled_up": leveled_up,
    }
