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

VALID_ITEM_KINDS = ("stackable", "individual")
EQUIPMENT_CATEGORIES = (
    "weapon",
    "helmet",
    "chest",
    "armor",
    "pants",
    "gloves",
    "boots",
    "amulet",
    "ring",
    "trinket",
    "accessory",
)
PERCENTAGE_STATS = {
    "accuracy",
    "dodge_chance",
    "block_chance",
    "crit_chance",
    "status_resistance",
    "loot_bonus",
    "gold_bonus",
    "rare_find_bonus",
    "xp_bonus",
}
MULTIPLIER_STATS = {
    "crit_damage",
}


def is_individual_equipment(item_data):
    item_type = item_data.get("type")
    if item_type in EQUIPMENT_CATEGORIES:
        return True

    return (
        item_type == "equipment"
        and item_data.get("category") in EQUIPMENT_CATEGORIES
    )


def get_default_item_kind(item_data):
    if is_individual_equipment(item_data):
        return "individual"
    return "stackable"


def get_item_kind(item_data):
    item_kind = item_data.get("kind")
    if item_kind in VALID_ITEM_KINDS:
        return item_kind
    return get_default_item_kind(item_data)


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


def apply_rare_find_bonus(rarity_weights, rare_find_bonus):
    adjusted_weights = dict(rarity_weights)
    if rare_find_bonus <= 0:
        return adjusted_weights

    bonus_multiplier = 1 + rare_find_bonus
    for rarity, weight in rarity_weights.items():
        if rarity == "common":
            adjusted_weights[rarity] = max(0.1, weight * (1 - rare_find_bonus))
        elif rarity in ("rare", "epic", "legendary", "unique"):
            adjusted_weights[rarity] = weight * bonus_multiplier
        else:
            adjusted_weights[rarity] = weight

    return adjusted_weights


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
        if not isinstance(value, (int, float)):
            stats[stat] = value
        elif stat in PERCENTAGE_STATS:
            random_bonus = random.randint(0, 2) * 0.01
            stats[stat] = round(value + random_bonus + rarity_bonus * 0.01, 4)
        elif stat in MULTIPLIER_STATS:
            random_bonus = random.randint(0, 2) * 0.05
            stats[stat] = round(value + random_bonus + rarity_bonus * 0.05, 4)
        else:
            stats[stat] = value + random.randint(0, 2) + rarity_bonus
    return stats


def roll_drop_count(chance):
    if not isinstance(chance, (int, float)) or chance <= 0:
        return 0

    guaranteed_count = int(chance)
    extra_chance = chance - guaranteed_count
    count = guaranteed_count
    if random.random() <= extra_chance:
        count += 1
    return count


def generate_combat_loot(enemy, items, player=None):
    drops = []
    loot_bonus = 0.0
    rare_find_bonus = 0.0

    if player is not None:
        loot_bonus = player.get("loot_bonus", 0.0)
        rare_find_bonus = player.get("rare_find_bonus", 0.0)

    for drop in enemy.get("drops", []):
        base_chance = drop.get("chance", 0)
        modified_chance = base_chance * (1 + loot_bonus)
        drop_count = roll_drop_count(modified_chance)
        if drop_count <= 0:
            continue

        item_id = drop["item"]
        item_data = items.get(item_id, {})
        item_kind = get_item_kind(item_data)

        if item_kind == "individual":
            rarity_weights = apply_rare_find_bonus(
                get_rarity_weights(item_data),
                rare_find_bonus,
            )
            for _ in range(drop_count):
                rarity = generate_rarity(rarity_weights)
                drops.append(
                    {
                        "kind": "individual",
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
                    "quantity": drop_count,
                }
            )

    return drops
