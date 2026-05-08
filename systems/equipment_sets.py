import json
from pathlib import Path


def load_equipment_sets():
    sets_path = Path(__file__).resolve().parent.parent / "data" / "equipment_sets.json"
    if not sets_path.exists():
        return {}

    with sets_path.open("r", encoding="utf-8") as sets_file:
        return json.load(sets_file)


def count_equipped_set_pieces(player, items):
    equipment = player.get("equipment", {})
    if not isinstance(equipment, dict):
        return {}

    set_counts = {}
    for item_instance in equipment.values():
        if not isinstance(item_instance, dict):
            continue

        item_id = item_instance.get("item")
        item_data = items.get(item_id)
        if not isinstance(item_data, dict):
            continue

        set_id = item_data.get("set_id")
        if not set_id:
            continue

        set_counts[set_id] = set_counts.get(set_id, 0) + 1

    return set_counts


def get_active_set_bonuses(player, items, equipment_sets=None):
    if equipment_sets is None:
        equipment_sets = load_equipment_sets()

    set_counts = count_equipped_set_pieces(player, items)
    active_bonuses = {}
    for set_id, piece_count in set_counts.items():
        set_data = equipment_sets.get(set_id)
        if not isinstance(set_data, dict):
            continue

        bonuses = set_data.get("bonuses", {})
        if not isinstance(bonuses, dict):
            continue

        for threshold_key, threshold_bonuses in bonuses.items():
            try:
                threshold = int(threshold_key)
            except (TypeError, ValueError):
                continue

            if piece_count < threshold or not isinstance(threshold_bonuses, dict):
                continue

            for stat, value in threshold_bonuses.items():
                active_bonuses[stat] = active_bonuses.get(stat, 0) + value

    return active_bonuses
