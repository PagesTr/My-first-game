import random


RARITIES = ("common", "uncommon", "rare", "epic", "legendary", "unique")

RARITY_WEIGHTS = {
    "common": 60,
    "uncommon": 25,
    "rare": 10,
    "epic": 4,
    "legendary": 1,
    "unique": 0.5,
}

RARITY_BONUS = {
    "common": 0,
    "uncommon": 1,
    "rare": 2,
    "epic": 3,
    "legendary": 4,
    "unique": 5,
}


def is_unique_equipment(item_data):
    return item_data.get("type") in ("weapon", "armor", "accessory")


def get_allowed_rarities(item_data):
    allowed_rarities = item_data.get("rarities")
    if not allowed_rarities:
        return RARITIES

    filtered_rarities = tuple(
        rarity for rarity in allowed_rarities if rarity in RARITIES
    )
    if not filtered_rarities:
        return RARITIES
    return filtered_rarities


def generate_rarity(allowed_rarities=None):
    rarities = tuple(allowed_rarities) if allowed_rarities is not None else RARITIES
    return random.choices(
        rarities,
        weights=[RARITY_WEIGHTS[rarity] for rarity in rarities],
        k=1,
    )[0]


def generate_randomized_stats(base_stats, rarity="common"):
    stats = {}
    rarity_bonus = RARITY_BONUS.get(rarity, 0)
    for stat, value in base_stats.items():
        if isinstance(value, (int, float)):
            stats[stat] = value + random.randint(0, 2) + rarity_bonus
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
                allowed_rarities = get_allowed_rarities(item_data)
                rarity = generate_rarity(allowed_rarities)
                drops.append(
                    {
                        "kind": "unique",
                        "item": item_id,
                        "rarity": rarity,
                        "stats": generate_randomized_stats(
                            item_data.get("stats", {}),
                            rarity,
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
