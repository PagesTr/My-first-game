def derive_stats(player, items, classes):
    """Calculate the player's final stats from class and equipment.

    This function starts with the class base stats and then adds any
    equipment modifiers. The derived values are returned as a dict.
    """
    class_data = classes[player['class']]
    total = dict(class_data['base_stats'])

    # Add stats from each equipped item.
    for item_key in player.get('equipment', []):
        item = items.get(item_key)
        if not item:
            continue
        for stat, value in item.get('stats', {}).items():
            total[stat] = total.get(stat, 0) + value

    # Compute final derived stats from base values.
    hp = (
        20
        + total.get('force', 0) * 2
        + total.get('intelligence', 0)
        + total.get('hp', 0)
    )
    attack = (
        5
        + total.get('force', 0)
        + total.get('agility', 0) // 2
        + total.get('intelligence', 0) // 2
        + total.get('attack', 0)
    )
    defense = (
        2
        + total.get('force', 0) // 2
        + total.get('intelligence', 0) // 2
        + total.get('defense', 0)
    )

    return {
        'force': total.get('force', 0),
        'agility': total.get('agility', 0),
        'intelligence': total.get('intelligence', 0),
        'hp': hp,
        'attack': attack,
        'defense': defense,
    }

def apply_item_stats(base, item_stats):
    """Add item stat modifiers to a base stat dictionary."""
    result = dict(base)
    for stat, value in item_stats.items():
        result[stat] = result.get(stat, 0) + value
    return result
