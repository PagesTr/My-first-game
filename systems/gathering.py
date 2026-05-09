import random

from systems.inventory import add_stackable_item
from systems.professions import add_profession_xp, get_profession_mastery


def get_gathering_node(gathering_nodes, zone_id, profession_id):
    if not isinstance(gathering_nodes, dict):
        return None

    zone_nodes = gathering_nodes.get(zone_id)
    if not isinstance(zone_nodes, dict):
        return None

    node = zone_nodes.get(profession_id)
    if not isinstance(node, dict):
        return None
    return node


def _calculate_reward_chance(reward, mastery):
    chance = reward.get("chance", 0)
    if reward.get("is_rare") is True:
        chance += min(0.25, mastery * 0.02)
    return min(1.0, max(0.0, chance))


def _roll_reward_quantity(reward, mastery):
    min_quantity = reward.get("min_quantity", 1)
    max_quantity = reward.get("max_quantity", 1)
    if (
        not isinstance(min_quantity, int)
        or not isinstance(max_quantity, int)
        or min_quantity <= 0
        or max_quantity < min_quantity
    ):
        min_quantity = 1
        max_quantity = 1

    quantity = random.randint(min_quantity, max_quantity)
    bonus_quantity_chance = min(0.50, mastery * 0.05)
    if random.random() <= bonus_quantity_chance:
        quantity += 1
    return max(1, quantity)


def generate_gathering_rewards(node_data, mastery):
    rewards = []
    if not isinstance(node_data, dict):
        return rewards

    for reward in node_data.get("rewards", []):
        if not isinstance(reward, dict):
            continue

        item_id = reward.get("item")
        if not item_id:
            continue

        chance = _calculate_reward_chance(reward, mastery)
        if random.random() <= chance:
            rewards.append({
                "kind": "stackable",
                "item": item_id,
                "quantity": _roll_reward_quantity(reward, mastery),
            })

    return rewards


def get_profession_xp_gain(player, profession_id, node_data, professions_data):
    if not isinstance(node_data, dict):
        return 0

    xp = node_data.get("xp", 0)
    if not isinstance(xp, (int, float)):
        xp = 0

    profession_data = {}
    if isinstance(professions_data, dict):
        profession_data = professions_data.get(profession_id, {})
    xp_bonus_stat = profession_data.get("xp_bonus_stat")
    bonus = player.get(xp_bonus_stat, 0) + player.get("gathering_xp_bonus", 0)
    if bonus > 0:
        xp = int(xp * (1 + bonus))
    return max(0, xp)


def gather_from_zone(player, inventory, zone_id, profession_id, gathering_nodes, professions_data, items):
    node = get_gathering_node(gathering_nodes, zone_id, profession_id)
    if node is None:
        return {"gathered": False, "reason": "unknown_node"}

    mastery = get_profession_mastery(player, profession_id, professions_data)
    generated_rewards = generate_gathering_rewards(node, mastery)
    added_rewards = []
    failed_rewards = []

    for reward in generated_rewards:
        added = add_stackable_item(inventory, reward["item"], reward["quantity"])
        if added:
            added_rewards.append(reward)
        else:
            failed_rewards.append(reward)

    if generated_rewards and not added_rewards:
        return {"gathered": False, "reason": "inventory_full"}

    xp_gain = 0
    xp_result = {"leveled_up": False}
    if added_rewards:
        xp_gain = get_profession_xp_gain(player, profession_id, node, professions_data)
        xp_result = add_profession_xp(player, profession_id, xp_gain)

    return {
        "gathered": True,
        "zone_id": zone_id,
        "profession_id": profession_id,
        "mastery": mastery,
        "rewards": added_rewards,
        "failed": failed_rewards,
        "profession_xp": xp_gain,
        "leveled_up": xp_result["leveled_up"],
    }
