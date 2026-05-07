import random


def create_enemy(template, level):
    """Create a combat enemy instance from a stable enemy template."""
    stats = template['stats']
    enemy_level = template.get('level', 1)
    return {
        'name': template['name'],
        'behavior': template.get('behavior', 'balanced'),
        'level': enemy_level,
        'max_hp': stats['hp'],
        'current_hp': stats['hp'],
        'attack': stats['attack'],
        'defense': stats['defense'],
        'exp': template['exp'],
        'gold': template['gold'],
        'drops': template.get('drops', []),
    }


def generate_drops(enemy_template, player_luck=0):
    """Generate a list of items dropped by an enemy based on drop chances."""
    drops = []
    for drop in enemy_template.get('drops', []):
        chance = drop['chance'] + (player_luck * 0.01)  # luck increases drop chance
        if random.random() < chance:
            drops.append(drop['item'])
    return drops
