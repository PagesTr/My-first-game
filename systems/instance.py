import random

from entities.enemy import create_enemy
from systems.combat import CombatSystem
from systems.loot import generate_combat_loot, get_item_kind


EXACT_COMBAT_LIMIT = 100
MAX_TURNS_PER_EXACT_COMBAT = 300
ABSOLUTE_MAX_COMBATS = 10_000_000_000
INSTANCE_POWER_GROWTH = 0.06


def run_instant_instance(
    player,
    zone_key,
    zones,
    enemies,
    items,
    skills_data=None,
    max_combats=ABSOLUTE_MAX_COMBATS,
):
    zone = zones[zone_key]
    player_snapshot = _create_player_snapshot(player)
    player["current_hp"] = player["max_hp"]

    combat_limit = min(max_combats, ABSOLUTE_MAX_COMBATS)
    total_exp = 0
    total_gold = 0
    combats_won = 0
    exact_combats = 0
    estimated_combats = 0
    exact_drops = []
    estimated_drops = []
    death_enemy = None
    end_reason = "absolute_limit"
    highest_enemy_multiplier = zone.get("difficulty_multiplier", 1.0)

    while (
        player.get("current_hp", 0) > 0
        and combats_won < combat_limit
        and exact_combats < EXACT_COMBAT_LIMIT
    ):
        enemy = _create_scaled_enemy(player_snapshot, zone, enemies, combats_won)
        highest_enemy_multiplier = max(
            highest_enemy_multiplier,
            enemy.get("instance_multiplier", highest_enemy_multiplier),
        )
        combat = CombatSystem(player, enemy, skills_data)
        turns = 0

        while combat.is_over is False and turns < MAX_TURNS_PER_EXACT_COMBAT:
            combat.step()
            turns += 1

        if combat.is_over is False:
            player["current_hp"] = 0
            death_enemy = enemy.get("name", "Unknown Enemy")
            end_reason = "turn_limit_death"
            break

        if combat.winner != "player":
            death_enemy = enemy.get("name", "Unknown Enemy")
            end_reason = "death"
            break

        rewards = _estimate_batch_rewards(player_snapshot, enemy, 1)
        total_exp += rewards["exp_gained"]
        total_gold += rewards["gold_gained"]
        exact_drops.extend(generate_combat_loot(enemy, items, player_snapshot))
        combats_won += 1
        exact_combats += 1

    if (
        player.get("current_hp", 0) > 0
        and combats_won < combat_limit
        and end_reason == "absolute_limit"
    ):
        while player.get("current_hp", 0) > 0 and combats_won < combat_limit:
            batch_size = min(_get_batch_size(combats_won), combat_limit - combats_won)
            estimated_depth = combats_won + batch_size // 2
            enemy = _create_scaled_enemy(player_snapshot, zone, enemies, estimated_depth)
            highest_enemy_multiplier = max(
                highest_enemy_multiplier,
                enemy.get("instance_multiplier", highest_enemy_multiplier),
            )
            combat_cost = _estimate_combat_cost(player_snapshot, enemy)
            survivable_combats = int(player["current_hp"] // combat_cost)

            if survivable_combats < batch_size:
                completed = max(0, survivable_combats)
                if completed > 0:
                    rewards = _estimate_batch_rewards(
                        player_snapshot,
                        enemy,
                        completed,
                    )
                    total_exp += rewards["exp_gained"]
                    total_gold += rewards["gold_gained"]
                    estimated_drops.extend(
                        _estimate_batch_loot(enemy, items, player_snapshot, completed)
                    )
                    combats_won += completed
                    estimated_combats += completed
                    player["current_hp"] = max(
                        0,
                        int(player["current_hp"] - combat_cost * completed),
                    )

                death_enemy = enemy.get("name", "Unknown Enemy")
                end_reason = "estimated_death"
                player["current_hp"] = 0
                break

            rewards = _estimate_batch_rewards(player_snapshot, enemy, batch_size)
            total_exp += rewards["exp_gained"]
            total_gold += rewards["gold_gained"]
            estimated_drops.extend(
                _estimate_batch_loot(enemy, items, player_snapshot, batch_size)
            )
            combats_won += batch_size
            estimated_combats += batch_size
            player["current_hp"] = max(
                0,
                int(player["current_hp"] - combat_cost * batch_size),
            )

    if combats_won >= combat_limit and player.get("current_hp", 0) > 0:
        end_reason = "absolute_limit"

    if death_enemy is None:
        death_enemy = "Unknown Enemy"

    reward_result = _apply_instance_rewards(player, total_exp, total_gold)
    merged_drops = _merge_stackable_drops(exact_drops + estimated_drops)
    total_drops_found = sum(int(drop.get("quantity", 1)) for drop in merged_drops)
    simulation_mode = "batched" if estimated_combats > 0 else "exact"

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
        "leveled_up": reward_result["leveled_up"],
        "levels_gained": reward_result["levels_gained"],
        "new_level": reward_result["new_level"],
        "simulation_mode": simulation_mode,
        "exact_combats": exact_combats,
        "estimated_combats": estimated_combats,
        "end_reason": end_reason,
        "estimated_drops": _merge_stackable_drops(estimated_drops),
        "highest_enemy_multiplier": highest_enemy_multiplier,
        "total_drops_found": total_drops_found,
        "final_player_level": player.get("level", 1),
    }


def _create_player_snapshot(player):
    return {
        "class": player.get("class"),
        "level": player.get("level", 1),
        "max_hp": player.get("max_hp", 1),
        "current_hp": player.get("max_hp", 1),
        "attack": player.get("attack", 1),
        "defense": player.get("defense", 0),
        "accuracy": player.get("accuracy", 1.0),
        "dodge_chance": player.get("dodge_chance", 0.0),
        "block_chance": player.get("block_chance", 0.0),
        "crit_chance": player.get("crit_chance", 0.1),
        "crit_damage": player.get("crit_damage", 2.0),
        "xp_bonus": player.get("xp_bonus", 0.0),
        "gold_bonus": player.get("gold_bonus", 0.0),
        "loot_bonus": player.get("loot_bonus", 0.0),
        "rare_find_bonus": player.get("rare_find_bonus", 0.0),
        "skills": dict(player.get("skills", {})),
        "equipped_skills": list(player.get("equipped_skills", [])),
        "skill_cooldowns": dict(player.get("skill_cooldowns", {})),
    }


def _create_scaled_enemy(player_snapshot, zone, enemies, combats_won):
    enemy_key = random.choice(zone["enemy_pool"])
    enemy_template = enemies[enemy_key]
    enemy = create_enemy(enemy_template, player_snapshot.get("level", 1))
    zone_multiplier = zone.get("difficulty_multiplier", 1.0)
    depth_multiplier = 1 + (combats_won * INSTANCE_POWER_GROWTH)
    multiplier = zone_multiplier * depth_multiplier

    for stat in ("max_hp", "attack", "defense", "exp", "gold"):
        enemy[stat] = max(1, int(enemy[stat] * multiplier))
    enemy["current_hp"] = enemy["max_hp"]
    enemy["instance_multiplier"] = multiplier
    return enemy


def _estimate_damage(attacker, defender):
    base_damage = max(1, attacker.get("attack", 1) - defender.get("defense", 0))
    hit_chance = attacker.get("accuracy", 1.0) - defender.get("dodge_chance", 0.0)
    hit_chance = max(0.05, min(0.95, hit_chance))
    crit_chance = attacker.get("crit_chance", 0.1)
    crit_damage = attacker.get("crit_damage", 2.0)
    crit_factor = 1 + crit_chance * (crit_damage - 1)
    block_factor = 1 - defender.get("block_chance", 0.0) * 0.5
    expected_damage = base_damage * hit_chance * crit_factor * block_factor
    return max(1, expected_damage)


def _estimate_combat_cost(player_snapshot, enemy):
    player_expected_damage = _estimate_damage(player_snapshot, enemy)
    enemy_expected_damage = _estimate_damage(enemy, player_snapshot)
    turns_to_kill_enemy = enemy.get("max_hp", 1) / player_expected_damage
    damage_taken = turns_to_kill_enemy * enemy_expected_damage
    return max(1, damage_taken)


def _get_batch_size(combats_won):
    if combats_won < 1_000:
        return 10
    if combats_won < 10_000:
        return 100
    if combats_won < 1_000_000:
        return 1_000
    if combats_won < 100_000_000:
        return 100_000
    return 1_000_000


def _estimate_batch_rewards(player_snapshot, enemy, batch_size):
    exp_gained = int(enemy.get("exp", 0) * (1 + player_snapshot.get("xp_bonus", 0.0)))
    gold_gained = int(
        enemy.get("gold", 0) * (1 + player_snapshot.get("gold_bonus", 0.0))
    )
    exp_gained = max(enemy.get("exp", 0), exp_gained)
    gold_gained = max(enemy.get("gold", 0), gold_gained)
    return {
        "exp_gained": exp_gained * batch_size,
        "gold_gained": gold_gained * batch_size,
    }


def _estimate_batch_loot(enemy, items, player_snapshot, batch_size):
    drops = []
    loot_bonus = player_snapshot.get("loot_bonus", 0.0)

    for drop in enemy.get("drops", []):
        estimated_quantity = int(drop.get("chance", 0) * (1 + loot_bonus) * batch_size)
        if estimated_quantity <= 0:
            continue

        item_id = drop.get("item")
        item_data = items.get(item_id, {})
        if get_item_kind(item_data) == "individual":
            drops.append(
                {
                    "kind": "estimated_individual_stack",
                    "item": item_id,
                    "rarity": "estimated",
                    "quantity": estimated_quantity,
                }
            )
        else:
            drops.append(
                {
                    "kind": "stackable",
                    "item": item_id,
                    "quantity": estimated_quantity,
                }
            )

    return drops


def _merge_stackable_drops(drops):
    merged = []
    stackable_by_item = {}
    estimated_equipment_by_item = {}

    for drop in drops:
        kind = drop.get("kind")
        item_id = drop.get("item")

        if kind == "stackable":
            if item_id not in stackable_by_item:
                merged_drop = dict(drop)
                merged_drop["quantity"] = int(merged_drop.get("quantity", 1))
                stackable_by_item[item_id] = merged_drop
                merged.append(merged_drop)
            else:
                stackable_by_item[item_id]["quantity"] += int(drop.get("quantity", 1))
            continue

        if kind == "estimated_individual_stack":
            if item_id not in estimated_equipment_by_item:
                merged_drop = dict(drop)
                merged_drop["quantity"] = int(merged_drop.get("quantity", 1))
                estimated_equipment_by_item[item_id] = merged_drop
                merged.append(merged_drop)
            else:
                estimated_equipment_by_item[item_id]["quantity"] += int(
                    drop.get("quantity", 1)
                )
            continue

        merged.append(dict(drop))

    return merged


def _apply_instance_rewards(player, total_exp, total_gold):
    player["exp"] = player.get("exp", 0) + total_exp
    player["gold"] = player.get("gold", 0) + total_gold
    player["level"] = player.get("level", 1)
    player["next_exp"] = player.get("next_exp", 100)

    levels_gained = 0
    while player["exp"] >= player["next_exp"]:
        player["exp"] -= player["next_exp"]
        player["level"] += 1
        player["next_exp"] = int(player["next_exp"] * 1.5)
        levels_gained += 1

    return {
        "leveled_up": levels_gained > 0,
        "levels_gained": levels_gained,
        "new_level": player["level"],
    }
