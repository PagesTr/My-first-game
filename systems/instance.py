import random

from entities.enemy import create_enemy
from systems.combat import CombatSystem
from systems.loot import generate_combat_loot
from systems.progression import apply_combat_rewards


INSTANCE_POWER_GROWTH = 0.06
DEFAULT_MAX_COMBATS = 500


def run_instant_instance(
    player,
    zone_key,
    zones,
    enemies,
    items,
    skills_data=None,
    max_combats=DEFAULT_MAX_COMBATS,
):
    zone = zones[zone_key]
    player["current_hp"] = player["max_hp"]

    total_exp = 0
    total_gold = 0
    combats_won = 0
    drops = []
    death_enemy = None
    start_level = player.get("level", 1)

    while player.get("current_hp", 0) > 0 and combats_won < max_combats:
        enemy = _create_scaled_enemy(player, zone, enemies, combats_won)
        combat = CombatSystem(player, enemy, skills_data)

        while combat.is_over is False:
            combat.step()

        if combat.winner != "player":
            death_enemy = enemy.get("name", "Unknown Enemy")
            break

        rewards = apply_combat_rewards(player, enemy)
        total_exp += rewards.get("exp_gained", 0)
        total_gold += rewards.get("gold_gained", 0)
        drops.extend(generate_combat_loot(enemy, items, player))
        combats_won += 1

    if death_enemy is None:
        death_enemy = "Unknown Enemy"

    merged_drops = _merge_stackable_drops(drops)
    levels_gained = max(0, player.get("level", 1) - start_level)

    return {
        "is_instance_result": True,
        "zone_key": zone_key,
        "zone_name": zone.get("name", zone_key),
        "combats_won": combats_won,
        "death_enemy": death_enemy,
        "exp_gained": total_exp,
        "gold_gained": total_gold,
        "drops": merged_drops,
        "inventory_result": {
            "added": [],
            "failed": [],
            "pending": list(merged_drops),
        },
        "leveled_up": levels_gained > 0,
        "levels_gained": levels_gained,
        "new_level": player.get("level", 1),
    }


def _create_scaled_enemy(player, zone, enemies, combats_won):
    enemy_key = random.choice(zone["enemy_pool"])
    enemy_template = enemies[enemy_key]
    enemy = create_enemy(enemy_template, player.get("level", 1))
    zone_multiplier = zone.get("difficulty_multiplier", 1.0)
    depth_multiplier = 1 + (combats_won * INSTANCE_POWER_GROWTH)
    multiplier = zone_multiplier * depth_multiplier

    for stat in ("max_hp", "attack", "defense", "exp", "gold"):
        enemy[stat] = max(1, int(enemy[stat] * multiplier))
    enemy["current_hp"] = enemy["max_hp"]
    return enemy


def _merge_stackable_drops(drops):
    merged = []
    stackable_by_item = {}

    for drop in drops:
        if drop.get("kind") != "stackable":
            merged.append(dict(drop))
            continue

        item_id = drop.get("item")
        if item_id not in stackable_by_item:
            merged_drop = dict(drop)
            merged_drop["quantity"] = int(merged_drop.get("quantity", 1))
            stackable_by_item[item_id] = merged_drop
            merged.append(merged_drop)
        else:
            stackable_by_item[item_id]["quantity"] += int(drop.get("quantity", 1))

    return merged
