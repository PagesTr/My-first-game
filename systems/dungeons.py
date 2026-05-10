def get_dungeon(dungeons, dungeon_id):
    if not isinstance(dungeons, dict):
        return None
    dungeon = dungeons.get(dungeon_id)
    return dungeon if isinstance(dungeon, dict) else None


def get_dungeon_route(dungeon):
    if not isinstance(dungeon, dict):
        return []
    route = dungeon.get("route", [])
    return route if isinstance(route, list) else []


def get_next_dungeon_step(dungeon, step_index):
    route = get_dungeon_route(dungeon)
    if not isinstance(step_index, int):
        return None
    if step_index < 0 or step_index >= len(route):
        return None
    step = route[step_index]
    return step if isinstance(step, dict) else None


def is_rest_choice_step(step):
    return isinstance(step, dict) and step.get("type") == "rest_choice"


def is_boss_loop_step(step):
    return isinstance(step, dict) and step.get("type") == "boss_loop"


def apply_rest_choice(player, choice):
    if choice not in {"heal", "loot"}:
        return {
            "applied": False,
            "choice": choice,
            "healed": 0,
            "loot_bonus": False,
            "reason": "invalid_choice",
        }

    if choice == "loot":
        return {
            "applied": True,
            "choice": choice,
            "healed": 0,
            "loot_bonus": True,
        }

    max_hp = 0
    current_hp = 0
    if isinstance(player, dict):
        max_hp = int(player.get("max_hp", 0))
        current_hp = int(player.get("current_hp", 0))
    heal_amount = max(0, int(max_hp * 0.30))
    new_hp = min(max_hp, current_hp + heal_amount)
    healed = max(0, new_hp - current_hp)
    if isinstance(player, dict):
        player["current_hp"] = new_hp

    return {
        "applied": True,
        "choice": choice,
        "healed": healed,
        "loot_bonus": False,
    }


def calculate_boss_multiplier(victories, scaling_rate):
    victories = _safe_non_negative_number(victories)
    scaling_rate = _safe_number(scaling_rate)
    return 1.0 + victories * scaling_rate


def calculate_boss_reward_multiplier(victories, reward_multiplier_per_victory):
    victories = _safe_non_negative_number(victories)
    reward_multiplier_per_victory = _safe_number(reward_multiplier_per_victory)
    return 1.0 + victories * reward_multiplier_per_victory


def create_dungeon_state(dungeon_id):
    return {
        "dungeon_id": dungeon_id,
        "step_index": 0,
        "boss_victories": 0,
        "rest_choice_used": False,
        "completed": False,
        "failed": False,
    }


def _safe_number(value):
    if isinstance(value, (int, float)):
        return value
    return 0


def _safe_non_negative_number(value):
    if isinstance(value, (int, float)):
        return max(0, value)
    return 0
