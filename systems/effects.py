def ensure_effects_container(player):
    if "active_effects" not in player:
        player["active_effects"] = []
    return player["active_effects"]


def add_temporary_effect(player, effect):
    active_effects = ensure_effects_container(player)
    if not isinstance(effect, dict):
        return False

    modifiers = effect.get("modifiers")
    if not isinstance(modifiers, dict):
        return False

    duration_type = effect.get("duration_type")
    if duration_type not in ("combat", "time"):
        return False

    if duration_type == "combat":
        remaining_combats = effect.get("remaining_combats")
        if not isinstance(remaining_combats, int) or remaining_combats <= 0:
            return False

    if duration_type == "time":
        remaining_seconds = effect.get("remaining_seconds")
        if not isinstance(remaining_seconds, (int, float)) or remaining_seconds <= 0:
            return False

    effect_copy = dict(effect)
    effect_copy["modifiers"] = dict(modifiers)
    effect_id = effect_copy.get("id")
    if effect_id:
        for active_effect in active_effects:
            if not isinstance(active_effect, dict):
                continue
            if active_effect.get("id") != effect_id:
                continue

            active_effect["modifiers"] = dict(modifiers)
            if "name" in effect_copy:
                active_effect["name"] = effect_copy["name"]
            if "source" in effect_copy:
                active_effect["source"] = effect_copy["source"]
            active_effect["duration_type"] = duration_type
            if duration_type == "combat":
                active_effect["remaining_combats"] = effect_copy["remaining_combats"]
                active_effect.pop("remaining_seconds", None)
            if duration_type == "time":
                active_effect["remaining_seconds"] = effect_copy["remaining_seconds"]
                active_effect.pop("remaining_combats", None)
            return True

    active_effects.append(effect_copy)
    return True


def get_active_stat_modifiers(player):
    modifiers_total = {}

    for effect in player.get("active_effects", []):
        if not isinstance(effect, dict):
            continue

        modifiers = effect.get("modifiers")
        if not isinstance(modifiers, dict):
            continue

        for stat, value in modifiers.items():
            if isinstance(value, (int, float)):
                modifiers_total[stat] = modifiers_total.get(stat, 0) + value

    return modifiers_total


def tick_combat_effects(player):
    active_effects = ensure_effects_container(player)
    remaining_effects = []
    removed_count = 0

    for effect in active_effects:
        if not isinstance(effect, dict):
            removed_count += 1
            continue

        if effect.get("duration_type") != "combat":
            remaining_effects.append(effect)
            continue

        effect["remaining_combats"] = effect.get("remaining_combats", 0) - 1
        if effect["remaining_combats"] > 0:
            remaining_effects.append(effect)
        else:
            removed_count += 1

    player["active_effects"] = remaining_effects
    return removed_count


def tick_time_effects(player, elapsed_seconds):
    if not isinstance(elapsed_seconds, (int, float)) or elapsed_seconds <= 0:
        return 0

    active_effects = ensure_effects_container(player)
    remaining_effects = []
    removed_count = 0

    for effect in active_effects:
        if not isinstance(effect, dict):
            removed_count += 1
            continue

        if effect.get("duration_type") != "time":
            remaining_effects.append(effect)
            continue

        effect["remaining_seconds"] = effect.get("remaining_seconds", 0) - elapsed_seconds
        if effect["remaining_seconds"] > 0:
            remaining_effects.append(effect)
        else:
            removed_count += 1

    player["active_effects"] = remaining_effects
    return removed_count
