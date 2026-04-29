from systems.inventory import add_stackable_item, create_inventory
from systems.stats import derive_stats

def create_player(char_class, classes, items):
    """Create a new player using a chosen character class."""
    player = {
        'name': 'Hero',
        'class': char_class,
        'level': 1,
        'exp': 0,
        'next_exp': 10,
        'gold': 0,
        'potions': 2,
        'equipment': {
            'weapon': None,
            'armor': None,
            'accessory': None,
        },
        'inventory': create_inventory(),
        'active_effects': [],
        'current_hp': 0,
    }
    # Temporary test items for buff effect validation.
    add_stackable_item(player["inventory"], "rage_potion", 2)
    add_stackable_item(player["inventory"], "guard_potion", 1)

    stats = derive_stats(player, items, classes)
    player.update({
        'force': stats['force'],
        'agility': stats['agility'],
        'intelligence': stats['intelligence'],
        'max_hp': stats['hp'],
        'current_hp': stats['hp'],
        'attack': stats['attack'],
        'defense': stats['defense'],
    })
    return player
