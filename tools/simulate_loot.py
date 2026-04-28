import json
import sys
from collections import Counter
from pathlib import Path


PROJECT_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(PROJECT_ROOT))

from systems.loot import generate_combat_loot


RUNS_PER_ENEMY = 50


def load_json(project_root, relative_path):
    with (project_root / relative_path).open("r", encoding="utf-8") as json_file:
        return json.load(json_file)


def simulate_enemy_loot(enemy, items):
    drop_counts = Counter()
    rarity_counts = Counter()

    for _ in range(RUNS_PER_ENEMY):
        drops = generate_combat_loot(enemy, items, player=None)
        for drop in drops:
            item_id = drop["item"]
            if drop.get("kind") == "stackable":
                drop_counts[item_id] += drop.get("quantity", 1)
            elif drop.get("kind") == "unique":
                drop_counts[item_id] += 1
                rarity = drop.get("rarity")
                if rarity:
                    rarity_counts[f"{item_id} {rarity}"] += 1
            else:
                drop_counts[item_id] += 1

    return drop_counts, rarity_counts


def print_counter(title, counter):
    if not counter:
        return

    print(title)
    for item_id, count in counter.most_common():
        print(f"- {item_id}: {count}")


def main():
    enemies = load_json(PROJECT_ROOT, "data/enemies.json")
    items = load_json(PROJECT_ROOT, "data/items.json")

    for enemy in enemies.values():
        drop_counts, rarity_counts = simulate_enemy_loot(enemy, items)

        print(f"Enemy: {enemy['name']}")
        print(f"Runs: {RUNS_PER_ENEMY}")
        print_counter("Drops:", drop_counts)
        print_counter("Unique rarities:", rarity_counts)
        print()


if __name__ == "__main__":
    main()
