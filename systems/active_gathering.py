from copy import deepcopy

from systems.gathering import gather_from_zone


DEFAULT_ACTIVE_GATHERING_TICK_SECONDS = 5.0


def create_active_gathering_activity(
    zone_id,
    profession_id,
    current_time_ms,
    tick_seconds=None,
):
    if tick_seconds is None:
        tick_seconds = DEFAULT_ACTIVE_GATHERING_TICK_SECONDS
    try:
        tick_seconds = float(tick_seconds)
    except (TypeError, ValueError):
        tick_seconds = DEFAULT_ACTIVE_GATHERING_TICK_SECONDS
    if tick_seconds <= 0:
        tick_seconds = DEFAULT_ACTIVE_GATHERING_TICK_SECONDS

    return {
        "type": "gathering",
        "zone_id": zone_id,
        "profession_id": profession_id,
        "started_at_ms": current_time_ms,
        "last_tick_at_ms": current_time_ms,
        "tick_seconds": tick_seconds,
    }


def get_node_tick_seconds(node_data):
    if not isinstance(node_data, dict):
        return DEFAULT_ACTIVE_GATHERING_TICK_SECONDS
    try:
        tick_seconds = float(node_data.get("tick_seconds"))
    except (TypeError, ValueError):
        return DEFAULT_ACTIVE_GATHERING_TICK_SECONDS
    if tick_seconds <= 0:
        return DEFAULT_ACTIVE_GATHERING_TICK_SECONDS
    return tick_seconds


def is_active_gathering_tick_ready(activity, current_time_ms):
    if not isinstance(activity, dict):
        return False
    last_tick_at_ms = activity.get("last_tick_at_ms")
    tick_seconds = get_node_tick_seconds(activity)
    if not isinstance(last_tick_at_ms, (int, float)):
        return False
    elapsed_ms = current_time_ms - last_tick_at_ms
    if elapsed_ms < 0:
        return False
    return elapsed_ms >= tick_seconds * 1000


def get_active_gathering_remaining_ms(activity, current_time_ms):
    if is_active_gathering_tick_ready(activity, current_time_ms):
        return 0
    if not isinstance(activity, dict):
        return 0
    last_tick_at_ms = activity.get("last_tick_at_ms")
    if not isinstance(last_tick_at_ms, (int, float)):
        return 0
    tick_seconds = get_node_tick_seconds(activity)
    remaining_ms = int((tick_seconds * 1000) - (current_time_ms - last_tick_at_ms))
    return max(0, remaining_ms)


def resolve_active_gathering_tick(player, activity, gathering_nodes, professions_data, items):
    if not isinstance(activity, dict) or activity.get("type") != "gathering":
        return {"gathered": False, "reason": "invalid_activity"}
    return gather_from_zone(
        player,
        player["inventory"],
        activity.get("zone_id"),
        activity.get("profession_id"),
        gathering_nodes,
        professions_data,
        items,
    )


def advance_active_gathering_tick(activity, current_time_ms):
    activity["last_tick_at_ms"] = current_time_ms
    return activity


def format_tick_rate(tick_seconds):
    try:
        tick_seconds = float(tick_seconds)
    except (TypeError, ValueError):
        tick_seconds = DEFAULT_ACTIVE_GATHERING_TICK_SECONDS
    if tick_seconds <= 0:
        tick_seconds = DEFAULT_ACTIVE_GATHERING_TICK_SECONDS

    if tick_seconds >= 1.0:
        if tick_seconds.is_integer():
            value = str(int(tick_seconds))
        else:
            value = f"{tick_seconds:.1f}"
        return f"1 tick / {value}s"

    ticks_per_second = 1 / tick_seconds
    if ticks_per_second.is_integer():
        value = str(int(ticks_per_second))
    else:
        value = f"{ticks_per_second:.1f}"
    return f"{value} ticks/s"
