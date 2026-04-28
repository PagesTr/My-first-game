import json
from pathlib import Path


def load_stat_scaling():
    scaling_path = Path(__file__).resolve().parent.parent / "data" / "stat_scaling.json"
    with scaling_path.open("r", encoding="utf-8") as scaling_file:
        return json.load(scaling_file)


def normalize_primary_stats(total):
    if "force" in total:
        total["strength"] = total.get("strength", 0) + total["force"]
    if "agility" in total:
        total["dexterity"] = total.get("dexterity", 0) + total["agility"]

    for stat in ("strength", "dexterity", "intelligence", "vitality", "wisdom", "luck"):
        total.setdefault(stat, 0)

    return total


def derive_stats(player, items, classes):
    """Calculate the player's final stats from class and equipment.

    This function starts with the class base stats and then adds any
    equipment modifiers. The derived values are returned as a dict.
    """
    class_data = classes[player['class']]
    total = dict(class_data['base_stats'])

    # Add stats from equipped items. Supports the new slot dict and the old list format.
    equipment = player.get('equipment', [])
    if isinstance(equipment, dict):
        for item_instance in equipment.values():
            if not item_instance:
                continue
            for stat, value in item_instance.get('stats', {}).items():
                total[stat] = total.get(stat, 0) + value
    else:
        for item_key in equipment:
            item = items.get(item_key)
            if not item:
                continue
            for stat, value in item.get('stats', {}).items():
                total[stat] = total.get(stat, 0) + value

    total = normalize_primary_stats(total)
    scaling = load_stat_scaling()

    secondary_stats = (
        scaling["combat_secondary_stats"]
        + scaling["progression_secondary_stats"]
    )
    final_stats = dict(scaling["base_values"])

    for stat in secondary_stats:
        final_stats[stat] = final_stats.get(stat, 0) + total.get(stat, 0)

    # Temporary compatibility for existing item modifiers that still use hp.
    final_stats["max_hp"] = final_stats.get("max_hp", 0) + total.get("hp", 0)

    for primary_stat, conversions in scaling["primary_to_secondary"].items():
        primary_value = total.get(primary_stat, 0)
        for secondary_stat, coefficient in conversions.items():
            final_stats[secondary_stat] = (
                final_stats.get(secondary_stat, 0)
                + primary_value * coefficient
            )

    for stat, cap in scaling["caps"].items():
        if stat in final_stats:
            final_stats[stat] = min(final_stats[stat], cap)

    int_stats = (
        "max_hp",
        "attack",
        "defense",
        "magic_attack",
        "magic_defense",
        "initiative",
        "healing_power",
    )
    for stat in int_stats:
        final_stats[stat] = int(final_stats.get(stat, 0))

    final_stats["hp"] = final_stats["max_hp"]

    return {
        'force': total.get('force', 0),
        'agility': total.get('agility', 0),
        'strength': total.get('strength', 0),
        'dexterity': total.get('dexterity', 0),
        'intelligence': total.get('intelligence', 0),
        'vitality': total.get('vitality', 0),
        'wisdom': total.get('wisdom', 0),
        'luck': total.get('luck', 0),
        'max_hp': final_stats['max_hp'],
        'hp': final_stats['hp'],
        'attack': final_stats['attack'],
        'defense': final_stats['defense'],
        'magic_attack': final_stats['magic_attack'],
        'magic_defense': final_stats['magic_defense'],
        'accuracy': final_stats['accuracy'],
        'dodge_chance': final_stats['dodge_chance'],
        'block_chance': final_stats['block_chance'],
        'crit_chance': final_stats['crit_chance'],
        'crit_damage': final_stats['crit_damage'],
        'initiative': final_stats['initiative'],
        'healing_power': final_stats['healing_power'],
        'status_resistance': final_stats['status_resistance'],
        'loot_bonus': final_stats['loot_bonus'],
        'gold_bonus': final_stats['gold_bonus'],
        'rare_find_bonus': final_stats['rare_find_bonus'],
        'xp_bonus': final_stats['xp_bonus'],
    }


def prepare_player_for_combat(player, items, classes):
    stats = derive_stats(player, items, classes)

    player["max_hp"] = stats["hp"]
    player["attack"] = stats["attack"]
    player["defense"] = stats["defense"]
    player["magic_attack"] = stats["magic_attack"]
    player["magic_defense"] = stats["magic_defense"]
    player["accuracy"] = stats["accuracy"]
    player["dodge_chance"] = stats["dodge_chance"]
    player["block_chance"] = stats["block_chance"]
    player["crit_chance"] = stats["crit_chance"]
    player["crit_damage"] = stats["crit_damage"]
    player["initiative"] = stats["initiative"]
    player["healing_power"] = stats["healing_power"]
    player["status_resistance"] = stats["status_resistance"]
    player["loot_bonus"] = stats["loot_bonus"]
    player["gold_bonus"] = stats["gold_bonus"]
    player["rare_find_bonus"] = stats["rare_find_bonus"]
    player["xp_bonus"] = stats["xp_bonus"]

    if player.get("current_hp", 0) <= 0:
        player["current_hp"] = stats["hp"]
    elif player["current_hp"] > stats["hp"]:
        player["current_hp"] = stats["hp"]

    return player


def apply_item_stats(base, item_stats):
    """Add item stat modifiers to a base stat dictionary."""
    result = dict(base)
    for stat, value in item_stats.items():
        result[stat] = result.get(stat, 0) + value
    return result
