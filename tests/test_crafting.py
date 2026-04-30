import json
from pathlib import Path


PROJECT_ROOT = Path(__file__).resolve().parent.parent
RECIPES_PATH = PROJECT_ROOT / "data" / "recipes.json"
ITEMS_PATH = PROJECT_ROOT / "data" / "items.json"
VALID_INGREDIENT_KINDS = {"stackable", "unique"}


def load_json(path):
    with path.open("r", encoding="utf-8") as json_file:
        return json.load(json_file)


def test_recipes_file_exists():
    assert RECIPES_PATH.exists()


def test_recipes_file_contains_at_least_one_recipe():
    recipes = load_json(RECIPES_PATH)

    assert recipes


def test_each_recipe_has_ingredients_and_result():
    recipes = load_json(RECIPES_PATH)

    for recipe_id, recipe in recipes.items():
        assert "ingredients" in recipe, recipe_id
        assert "result" in recipe, recipe_id


def test_recipe_ingredients_are_non_empty_lists():
    recipes = load_json(RECIPES_PATH)

    for recipe_id, recipe in recipes.items():
        assert isinstance(recipe["ingredients"], list), recipe_id
        assert recipe["ingredients"], recipe_id


def test_each_ingredient_has_required_fields():
    recipes = load_json(RECIPES_PATH)

    for recipe_id, recipe in recipes.items():
        for ingredient in recipe["ingredients"]:
            assert "kind" in ingredient, recipe_id
            assert "item" in ingredient, recipe_id
            assert "quantity" in ingredient, recipe_id


def test_ingredient_kind_is_valid():
    recipes = load_json(RECIPES_PATH)

    for recipe_id, recipe in recipes.items():
        for ingredient in recipe["ingredients"]:
            assert ingredient["kind"] in VALID_INGREDIENT_KINDS, recipe_id


def test_ingredient_quantity_is_positive_integer():
    recipes = load_json(RECIPES_PATH)

    for recipe_id, recipe in recipes.items():
        for ingredient in recipe["ingredients"]:
            assert isinstance(ingredient["quantity"], int), recipe_id
            assert ingredient["quantity"] > 0, recipe_id


def test_recipe_result_is_an_object():
    recipes = load_json(RECIPES_PATH)

    for recipe_id, recipe in recipes.items():
        assert isinstance(recipe["result"], dict), recipe_id


def test_recipe_result_has_required_fields():
    recipes = load_json(RECIPES_PATH)

    for recipe_id, recipe in recipes.items():
        assert "item" in recipe["result"], recipe_id
        assert "quantity" in recipe["result"], recipe_id


def test_recipe_result_quantity_is_positive_integer():
    recipes = load_json(RECIPES_PATH)

    for recipe_id, recipe in recipes.items():
        assert isinstance(recipe["result"]["quantity"], int), recipe_id
        assert recipe["result"]["quantity"] > 0, recipe_id


def test_all_ingredient_items_exist_in_items_data():
    recipes = load_json(RECIPES_PATH)
    items = load_json(ITEMS_PATH)

    for recipe_id, recipe in recipes.items():
        for ingredient in recipe["ingredients"]:
            assert ingredient["item"] in items, recipe_id


def test_all_result_items_exist_in_items_data():
    recipes = load_json(RECIPES_PATH)
    items = load_json(ITEMS_PATH)

    for recipe_id, recipe in recipes.items():
        assert recipe["result"]["item"] in items, recipe_id
