# Game Economy V1

This document defines the economic rules used to calculate the sell value of all items in the game.

The goal of this system is to create a scalable economy where:

- item value grows strongly with level
- rarity affects value
- crafting is slightly rewarded
- dropped items are more valuable than crafted equivalents
- raw item stats never influence sell price
- manual overrides remain possible for balancing

This system is intentionally simple so that the game can be balanced iteratively.

---

# 1. Core Philosophy

Item price is determined by **economic properties**, not by combat stats.

Sell value depends on:

- economic level (usually the monster level)
- rarity
- economic source (drop, craft, resource, etc.)
- optional manual multipliers
- crafting recipes

Stats such as attack, defense, or bonuses **must not influence price calculations**.

---

# 2. Level Curve

The base economic value is derived from the item level.

Formula:

base_level_value = 33 × level^1.73

Example values:

| Level | Base Value |
|------|-----------|
| 1 | ~33 |
| 5 | ~530 |
| 10 | ~1760 |
| 20 | ~5800 |
| 50 | ~28400 |
| 100 | ~94000 |

This curve ensures that high level items become exponentially more valuable.

This allows the economy to scale toward late game values around **100k for level 100 crafted items**.

---

# 3. Rarity Multipliers

Rarity modifies economic value.


RARITY_MULTIPLIERS = {
"common": 1.00,
"uncommon": 1.35,
"rare": 2.00,
"epic": 3.50,
"legendary": 6.00,
"unique": 10.00
}


Notes:

- **unique items are the highest rarity (red items)**.
- rarity also influences **drop probability**.
- rare resources should drop less frequently rather than being overpriced.

---

# 4. Economic Source

Each item belongs to a source category.


SOURCE_MULTIPLIERS = {
"harvested_resource": 0.30,
"dropped_resource": 0.35,
"crafted_item": 1.00,
"dropped_item": 1.25,
"consumable": 0.60
}


Meaning:

| Source | Purpose |
|------|------|
harvested_resource | gathering system (future feature)
dropped_resource | monster drops used in crafting
crafted_item | baseline reference value
dropped_item | more valuable than crafted equivalent
consumable | lower resale value

---

# 5. Crafted Items

Crafting should be slightly rewarded.

Selling crafted items gives a small bonus compared to selling their components individually.


crafted_sell_price = component_value × 1.08


This provides a small economic reward for crafting without creating infinite gold loops.

Crafting is intended for **progression and unlocking equipment**, not for generating large profits.

Important rule:

Craftable items **are not purchasable from shops**.

Players must craft them to obtain them.

---

# 6. Dropped Items

Dropped equipment items use the level formula directly.


dropped_item_price =
base_level_value
× rarity_multiplier
× dropped_item_multiplier
× value_multiplier


Dropped items should always be slightly more valuable than crafted equivalents.

This makes rare drops feel rewarding.

---

# 7. Droppable Resources

Resources dropped by monsters use the same level curve.


resource_price =
base_level_value
× rarity_multiplier
× dropped_resource_multiplier
× value_multiplier


Rare resources should primarily be balanced by:

- drop rate
- rarity multiplier

rather than extremely high prices.

---

# 8. Crafted Item Pricing (Method B)

Crafted items use the **level formula rather than stat calculation**.

Stats are ignored.


crafted_item_price =
base_level_value
× rarity_multiplier
× crafted_item_multiplier


Where:


crafted_item_multiplier = 1.00


The crafting reward is applied separately through the component value bonus.

---

# 9. Manual Adjustments

Balancing must remain possible without rewriting formulas.

Two override mechanisms exist.

## Value Multiplier


"value_multiplier": 1.0


Example:


"value_multiplier": 2.5


Used for rare crafting materials or special resources.

---

## Manual Sell Price Override


"manual_sell_price": 500000


This completely overrides all formulas.

Used for special items or balancing exceptions.

Priority order:


manual_sell_price
→ value_multiplier
→ economic formula


---

# 10. Value Hierarchy

For the same level and rarity:


harvested resource
< dropped resource
< crafted item
< dropped item


This hierarchy ensures:

- crafting has value
- drops feel rewarding
- resources remain useful but not overly profitable

---

# 11. Design Constraints

The following rules must always remain true:

- item stats never determine economic value
- crafting gives a small economic reward
- drops should feel exciting and valuable
- rare resources are balanced via drop rate
- formulas must remain simple and adjustable

---

# 12. Unsellable Items

By default, items are sellable.

Quest items or protected items can define:


"sellable": false


Unsellable items must return a sell price of 0.

Unsellable items must not be removed from inventory by merchant selling.

The merchant screen may display them, but should clearly show that they cannot be sold.

---

# 13. Future Systems (Not Implemented Yet)

The economy must remain compatible with:

- resource harvesting
- consumables
- vendor shops
- player trading
- crafting stations
- drop tables
- difficulty scaling

Balancing will be adjusted once these systems are implemented.

---

# 14. Important Notes for Future Balancing

Keep the following in mind when adding new systems:

- monster drop rate affects the entire economy
- crafting recipes influence resource demand
- shop pricing must remain higher than sell values
- late game items should not break the gold curve

The system is intentionally flexible so it can evolve with the game.
