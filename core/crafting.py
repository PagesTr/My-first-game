def can_craft(recipe, player_inventory):
    """Check if the player has enough ingredients to craft an item."""
    for ingredient in recipe['ingredients']:
        item = ingredient['item']
        quantity_needed = ingredient['quantity']
        if player_inventory.get(item, 0) < quantity_needed:
            return False
    return True


def craft_item(recipe, player_inventory):
    """Consume ingredients and add the crafted item to inventory."""
    if not can_craft(recipe, player_inventory):
        return False
    for ingredient in recipe['ingredients']:
        item = ingredient['item']
        quantity_needed = ingredient['quantity']
        player_inventory[item] -= quantity_needed
    crafted_item = recipe['name']
    player_inventory[crafted_item] = player_inventory.get(crafted_item, 0) + 1
    return True
