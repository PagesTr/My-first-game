from systems.inventory import add_stackable_item, create_inventory
from systems.professions import create_player_professions
from systems.stats import derive_stats

def create_player(char_class, classes, items, professions_data=None):
    """Create a new player using a chosen character class."""
    if professions_data is None:
        professions_data = {}

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
            'helmet': None,
            'chest': None,
            'pants': None,
            'gloves': None,
            'boots': None,
            'amulet': None,
            'ring_1': None,
            'ring_2': None,
            'ring_3': None,
            'trinket': None,
        },
        'inventory': create_inventory(),
        'active_effects': [],
        'skill_points': 1,
        'enhanced_skill_points': 0,
        'skills': {},
        'equipped_skills': [],
        'skill_cooldowns': {},
        'professions': create_player_professions(professions_data),
        'offline_activity': None,
        'current_hp': 0,
    }
    # Temporary test items for buff effect validation.
    add_stackable_item(player["inventory"], "rage_potion", 2)
    add_stackable_item(player["inventory"], "guard_potion", 1)
    add_stackable_item(player["inventory"], "sealed_quest_letter", 1)

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
