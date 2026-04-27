import random

def create_enemy(template, level):
    """Create a combat enemy instance from a template and player level."""
    stats = template['stats']
    enemy_level = max(1, level + random.randint(-1, 1))
    return {
        'name': template['name'],
        'level': enemy_level,
        'max_hp': stats['hp'] + enemy_level * 2,
        'current_hp': stats['hp'] + enemy_level * 2,
        'attack': stats['attack'] + enemy_level // 2,
        'defense': stats['defense'] + enemy_level // 3,
        'exp': template['exp'] + enemy_level * 2,
        'gold': template['gold'] + enemy_level,
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
