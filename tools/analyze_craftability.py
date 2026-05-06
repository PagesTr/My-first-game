import json
from datetime import datetime
from pathlib import Path


PROJECT_ROOT = Path(__file__).resolve().parents[1]
ITEMS_PATH = PROJECT_ROOT / "data" / "items.json"
RECIPES_PATH = PROJECT_ROOT / "data" / "recipes.json"
ENEMIES_PATH = PROJECT_ROOT / "data" / "enemies.json"
ZONES_PATH = PROJECT_ROOT / "data" / "zones.json"
OBSIDIAN_REPORTS_DIR = PROJECT_ROOT / "obsidian_reports" / "craftability"
PROJECT_NAME = "My-first-game"
BRANCH_NAME = "feature_craft"


def load_json(path):
    with path.open("r", encoding="utf-8") as json_file:
        return json.load(json_file)


def collect_recipe_ingredients(recipes):
    ingredient_items = set()
    for recipe in recipes.values():
        for ingredient in recipe.get("ingredients", []):
            item_id = ingredient.get("item")
            if item_id:
                ingredient_items.add(item_id)
    return ingredient_items


def collect_recipe_results(recipes):
    result_items = set()
    for recipe in recipes.values():
        result = recipe.get("result", {})
        item_id = result.get("item")
        if item_id:
            result_items.add(item_id)
    return result_items


def collect_enemy_drop_items(enemies):
    drop_items = set()
    for enemy in enemies.values():
        for drop in enemy.get("drops", []):
            item_id = drop.get("item")
            if item_id:
                drop_items.add(item_id)
    return drop_items


def collect_zone_loot_items(zones):
    loot_items = set()
    for zone in zones.values():
        for item_id in zone.get("loot_table", []):
            if item_id:
                loot_items.add(item_id)
    return loot_items


def build_enemy_sources(enemies, items):
    sources = {}
    for enemy in enemies.values():
        enemy_name = enemy.get("name", "Unknown Enemy")
        for drop in enemy.get("drops", []):
            item_id = drop.get("item")
            if item_id:
                sources.setdefault(item_id, set()).add(enemy_name)
    return sources


def build_zone_sources(zones):
    sources = {}
    for zone in zones.values():
        zone_name = zone.get("name", "Unknown Zone")
        for item_id in zone.get("loot_table", []):
            if item_id:
                sources.setdefault(item_id, set()).add(zone_name)
    return sources


def find_blocked_recipes(recipes, available_items):
    blocked_recipes = {}
    for recipe_id, recipe in recipes.items():
        missing_items = []
        for ingredient in recipe.get("ingredients", []):
            item_id = ingredient.get("item")
            if item_id and item_id not in available_items:
                missing_items.append(item_id)
        if missing_items:
            blocked_recipes[recipe_id] = missing_items
    return blocked_recipes


def collect_resource_items(items):
    return {
        item_id
        for item_id, item_data in items.items()
        if item_data.get("type") == "resource"
    }


def get_item_name(items, item_id):
    item_data = items.get(item_id, {})
    return item_data.get("name", item_id)


def format_item_label(items, item_id):
    return f"{get_item_name(items, item_id)} ({item_id})"


def format_item(items, item_id):
    return format_item_label(items, item_id)


def print_section(title):
    print(f"=== {title} ===")


def print_item_list(title, items_data, item_ids):
    print(title)
    if not item_ids:
        print("- None")
        return

    for item_id in sorted(item_ids):
        print(f"- {format_item(items_data, item_id)}")


def recipe_is_available_from_drops(recipe, available_items):
    for ingredient in recipe.get("ingredients", []):
        item_id = ingredient.get("item")
        if item_id not in available_items:
            return False
    return True


def get_recipe_status(recipe, available_items):
    missing_items = []
    for ingredient in recipe.get("ingredients", []):
        item_id = ingredient.get("item")
        if item_id and item_id not in available_items:
            missing_items.append(item_id)

    if missing_items:
        return "BLOCKED", sorted(set(missing_items))
    return "OK", []


def print_summary(recipes, crafted_result_items, blocked_recipes, unused_resource_items):
    craftable_count = len(recipes) - len(blocked_recipes)

    print_section("Craftability Summary")
    print(f"Recipes: {len(recipes)}")
    print(f"Craftable from current drops: {craftable_count}")
    print(f"Blocked recipes: {len(blocked_recipes)}")
    print(f"Unused resources: {len(unused_resource_items)}")
    print(f"Crafted result items: {len(crafted_result_items)}")
    print()


def print_recipe_status(items, recipes, available_items):
    print_section("Recipe Status")
    if not recipes:
        print("- None")
        print()
        return

    for recipe_id in sorted(recipes):
        recipe = recipes[recipe_id]
        result_item = recipe.get("result", {}).get("item", "unknown")
        status, missing_items = get_recipe_status(recipe, available_items)
        print(f"[{status}] {recipe_id} -> {get_item_name(items, result_item)}")
        if missing_items:
            missing_names = ", ".join(get_item_name(items, item_id) for item_id in missing_items)
            print(f"  Missing: {missing_names}")
    print()


def print_next_actions(items, blocked_recipes, unused_resource_items):
    print_section("Next Actions")
    has_suggestions = False

    missing_items = sorted(
        {
            item_id
            for recipe_missing_items in blocked_recipes.values()
            for item_id in recipe_missing_items
        }
    )
    for item_id in missing_items:
        has_suggestions = True
        print(
            f'- Suggestion: add a drop source for missing ingredient "{item_id}" '
            "or change the recipe."
        )

    if unused_resource_items:
        has_suggestions = True
        print(
            "- Suggestion: add recipes using unused resources or keep them for "
            "selling only."
        )

    if not blocked_recipes:
        has_suggestions = True
        print("- Suggestion: run manual gameplay tests to check if recipes feel reachable.")

    if not has_suggestions:
        print("- None")
    print()


def print_ingredient_sources(items, ingredient_items, enemy_sources, zone_sources):
    print_section("Ingredient Sources")
    if not ingredient_items:
        print("- None")
        print()
        return

    for item_id in sorted(ingredient_items):
        enemy_names = sorted(enemy_sources.get(item_id, []))
        zone_names = sorted(zone_sources.get(item_id, []))
        print(format_item(items, item_id))
        print(f"Enemy drops: {', '.join(enemy_names) if enemy_names else 'None'}")
        print(f"Zone loot: {', '.join(zone_names) if zone_names else 'None'}")
        print()


def print_blocked_recipes(items, recipes, blocked_recipes):
    print_section("Blocked Recipes")
    if not blocked_recipes:
        print("All recipes have available ingredients.")
        print()
        return

    for recipe_id in sorted(blocked_recipes):
        recipe = recipes.get(recipe_id, {})
        result_item = recipe.get("result", {}).get("item", "unknown")
        print(f"{recipe_id} -> {get_item_name(items, result_item)}")
        print("Missing:")
        for item_id in sorted(blocked_recipes[recipe_id]):
            print(f"- {format_item(items, item_id)}")
        print()


def print_unused_resources(items, unused_resource_items):
    print_section("Unused Resources")
    if not unused_resource_items:
        print("- None")
        print()
        return

    for item_id in sorted(unused_resource_items):
        item_data = items.get(item_id, {})
        rarity = item_data.get("rarity", "unknown")
        economic_source = item_data.get("economic_source", "unknown")
        print(f"- {format_item(items, item_id)}")
        print(f"  Rarity: {rarity}")
        print(f"  Economic source: {economic_source}")
    print()


def ensure_reports_directory():
    OBSIDIAN_REPORTS_DIR.mkdir(parents=True, exist_ok=True)


def get_timestamped_report_path():
    ensure_reports_directory()
    timestamp = datetime.now().strftime("%Y-%m-%d_%H%M")
    filename = f"{timestamp}_craftability_report.md"
    report_path = OBSIDIAN_REPORTS_DIR / filename
    if not report_path.exists():
        return report_path

    counter = 2
    while True:
        filename = f"{timestamp}_craftability_report_{counter}.md"
        report_path = OBSIDIAN_REPORTS_DIR / filename
        if not report_path.exists():
            return report_path
        counter += 1


def markdown_value(value):
    if value in (None, "", []):
        return "-"
    return str(value).replace("|", "\\|")


def format_markdown_table(headers, rows):
    lines = [
        "| " + " | ".join(headers) + " |",
        "| " + " | ".join("---" for _ in headers) + " |",
    ]
    for row in rows:
        lines.append("| " + " | ".join(markdown_value(value) for value in row) + " |")
    return "\n".join(lines)


def build_summary(recipes, crafted_result_items, blocked_recipes, unused_resource_items):
    craftable_count = len(recipes) - len(blocked_recipes)
    return [
        ("Recipes", len(recipes)),
        ("Craftable recipes", craftable_count),
        ("Blocked recipes", len(blocked_recipes)),
        ("Crafted result items", len(crafted_result_items)),
        ("Unused resources", len(unused_resource_items)),
    ]


def build_recipe_status_rows(items, recipes, available_items):
    rows = []
    for recipe_id in sorted(recipes):
        recipe = recipes[recipe_id]
        result_item = recipe.get("result", {}).get("item", "unknown")
        status, missing_items = get_recipe_status(recipe, available_items)
        missing_names = ", ".join(
            get_item_name(items, item_id)
            for item_id in sorted(missing_items, key=lambda value: get_item_name(items, value))
        )
        rows.append(
            (
                status,
                recipe_id,
                get_item_name(items, result_item),
                missing_names or "-",
            )
        )
    return rows


def build_ingredient_source_rows(items, ingredient_items, enemy_sources, zone_sources):
    rows = []
    for item_id in sorted(ingredient_items, key=lambda value: get_item_name(items, value)):
        enemy_names = sorted(enemy_sources.get(item_id, []))
        zone_names = sorted(zone_sources.get(item_id, []))
        rows.append(
            (
                get_item_name(items, item_id),
                ", ".join(enemy_names) or "-",
                ", ".join(zone_names) or "-",
            )
        )
    return rows


def build_unused_resource_rows(items, unused_resource_items):
    rows = []
    for item_id in sorted(unused_resource_items, key=lambda value: get_item_name(items, value)):
        item_data = items.get(item_id, {})
        rows.append(
            (
                get_item_name(items, item_id),
                item_data.get("rarity", "-"),
                item_data.get("economic_source", "-"),
            )
        )
    return rows


def build_next_actions(blocked_recipes, unused_resource_items):
    actions = []
    missing_items = sorted(
        {
            item_id
            for missing_items in blocked_recipes.values()
            for item_id in missing_items
        }
    )

    for item_id in missing_items:
        actions.append(
            f'Add a drop source for missing ingredient "{item_id}" or change the recipe.'
        )

    if unused_resource_items:
        actions.append(
            "Add recipes using unused resources or keep them as selling resources."
        )

    if not blocked_recipes:
        actions.append("Run manual gameplay tests to check if recipes feel reachable.")

    return actions


def write_markdown_report(
    items,
    recipes,
    ingredient_items,
    crafted_result_items,
    enemy_sources,
    zone_sources,
    all_drop_items,
    unused_resource_items,
    blocked_recipes,
    report_path,
):
    summary_rows = build_summary(
        recipes,
        crafted_result_items,
        blocked_recipes,
        unused_resource_items,
    )
    recipe_status_rows = build_recipe_status_rows(items, recipes, all_drop_items)
    ingredient_source_rows = build_ingredient_source_rows(
        items,
        ingredient_items,
        enemy_sources,
        zone_sources,
    )
    unused_resource_rows = build_unused_resource_rows(items, unused_resource_items)
    next_actions = build_next_actions(blocked_recipes, unused_resource_items)
    created_at = datetime.now().strftime("%Y-%m-%d %H:%M")

    lines = [
        "---",
        "type: craftability-report",
        f"created: {created_at}",
        f"project: {PROJECT_NAME}",
        f"branch: {BRANCH_NAME}",
        "---",
        "",
        "# Craftability Report",
        "",
        "Related notes:",
        "- [[Craft V1]]",
        "- [[Loot and resources]]",
        "- [[Craftability]]",
        "",
        "## Summary",
        "",
        format_markdown_table(("Metric", "Value"), summary_rows),
        "",
        "## Recipe Status",
        "",
        format_markdown_table(
            ("Status", "Recipe", "Result", "Missing ingredients"),
            recipe_status_rows,
        ),
        "",
        "## Ingredient Sources",
        "",
        format_markdown_table(
            ("Ingredient", "Enemy drops", "Zone loot"),
            ingredient_source_rows,
        ),
        "",
        "## Unused Resources",
        "",
        format_markdown_table(
            ("Resource", "Rarity", "Economic source"),
            unused_resource_rows,
        ),
        "",
        "## Next Actions",
        "",
    ]

    if next_actions:
        lines.extend(f"- {action}" for action in next_actions)
    else:
        lines.append("- No immediate actions.")

    report_path.write_text("\n".join(lines) + "\n", encoding="utf-8")


def main():
    items = load_json(ITEMS_PATH)
    recipes = load_json(RECIPES_PATH)
    enemies = load_json(ENEMIES_PATH)
    zones = load_json(ZONES_PATH)

    ingredient_items = collect_recipe_ingredients(recipes)
    crafted_result_items = collect_recipe_results(recipes)
    enemy_drop_items = collect_enemy_drop_items(enemies)
    zone_loot_items = collect_zone_loot_items(zones)
    all_drop_items = enemy_drop_items | zone_loot_items
    enemy_sources = build_enemy_sources(enemies, items)
    zone_sources = build_zone_sources(zones)
    resource_items = collect_resource_items(items)
    used_resource_items = {
        item_id
        for item_id in ingredient_items
        if items.get(item_id, {}).get("type") == "resource"
    }
    unused_resource_items = resource_items - used_resource_items
    blocked_recipes = find_blocked_recipes(recipes, all_drop_items)
    report_path = get_timestamped_report_path()

    write_markdown_report(
        items,
        recipes,
        ingredient_items,
        crafted_result_items,
        enemy_sources,
        zone_sources,
        all_drop_items,
        unused_resource_items,
        blocked_recipes,
        report_path,
    )
    relative_report_path = report_path.relative_to(PROJECT_ROOT)
    print(f"Craftability report written to {relative_report_path.as_posix()}")


if __name__ == "__main__":
    main()
