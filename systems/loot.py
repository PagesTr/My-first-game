import random


def is_unique_equipment(item_data):
    return item_data.get("type") in ("weapon", "armor", "accessory")


def generate_randomized_stats(base_stats):
    stats = {}
    for stat, value in base_stats.items():
        if isinstance(value, (int, float)):
            stats[stat] = value + random.randint(0, 2)
        else:
            stats[stat] = value
    return stats


def generate_combat_loot(enemy, items):
    drops = []

    for drop in enemy.get("drops", []):
        if random.random() <= drop["chance"]:
            item_id = drop["item"]
            item_data = items.get(item_id, {})

            if is_unique_equipment(item_data):
                drops.append(
                    {
                        "kind": "unique",
                        "item": item_id,
                        "stats": generate_randomized_stats(
                            item_data.get("stats", {})
                        ),
                    }
                )
            else:
                drops.append(
                    {
                        "kind": "stackable",
                        "item": item_id,
                        "quantity": 1,
                    }
                )

    return drops
