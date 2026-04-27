import random


def generate_combat_loot(enemy):
    drops = []

    for drop in enemy.get("drops", []):
        if random.random() <= drop["chance"]:
            drops.append(
                {
                    "item": drop["item"],
                    "quantity": 1,
                }
            )

    return drops
