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


def get_rarity_weights(item_data):
    item_weights = item_data.get("rarity_weights")
    if isinstance(item_weights, dict):
        filtered_weights = {
            rarity: weight
            for rarity, weight in item_weights.items()
            if rarity in RARITIES
            and isinstance(weight, (int, float))
            and weight > 0
        }
        if filtered_weights:
            return filtered_weights

    allowed_rarities = get_allowed_rarities(item_data)
    return {
        rarity: RARITY_WEIGHTS[rarity]
        for rarity in allowed_rarities
    }


def generate_rarity(rarity_weights=None):
    weights_by_rarity = rarity_weights if rarity_weights is not None else RARITY_WEIGHTS
    return random.choices(
        list(weights_by_rarity.keys()),
        weights=list(weights_by_rarity.values()),
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
                rarity_weights = get_rarity_weights(item_data)
                rarity = generate_rarity(rarity_weights)
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
