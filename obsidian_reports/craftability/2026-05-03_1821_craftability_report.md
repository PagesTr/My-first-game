---
type: craftability-report
created: 2026-05-03 18:21
project: My-first-game
branch: feature_craft
---

# Craftability Report

Related notes:
- [[Craft V1]]
- [[Loot and resources]]
- [[Craftability]]

## Summary

| Metric | Value |
| --- | --- |
| Recipes | 3 |
| Craftable recipes | 1 |
| Blocked recipes | 2 |
| Crafted result items | 3 |
| Unused resources | 11 |

## Recipe Status

| Status | Recipe | Result | Missing ingredients |
| --- | --- | --- | --- |
| OK | brew_field_dressing | Field Dressing | - |
| BLOCKED | patch_worn_leather_armor | Patched Leather Armor | Worn Leather Armor |
| BLOCKED | restore_rusty_sword | Restored Sword | Rusty Sword |

## Ingredient Sources

| Ingredient | Enemy drops | Zone loot |
| --- | --- | --- |
| Goblin Ear | Goblin | - |
| Iron Ore | Orc, Skeleton | - |
| Leather | Goblin, Wolf | - |
| Rusty Sword | - | - |
| Wolf Pelt | Wolf | - |
| Worn Leather Armor | - | - |

## Unused Resources

| Resource | Rarity | Economic source |
| --- | --- | --- |
| Ancient Bone | uncommon | dropped_resource |
| Bandit Badge | common | dropped_resource |
| Bone | common | dropped_resource |
| Goblin Charm | rare | dropped_resource |
| Hidden Pouch | rare | dropped_resource |
| Orc Tusk | uncommon | dropped_resource |
| Rare Gem | epic | dropped_resource |
| Sharp Fang | rare | dropped_resource |
| Troll Heart | epic | dropped_resource |
| Troll Hide | rare | dropped_resource |
| Warrior Trophy | rare | dropped_resource |

## Next Actions

- Add a drop source for missing ingredient "rusty_sword" or change the recipe.
- Add a drop source for missing ingredient "worn_leather_armor" or change the recipe.
- Add recipes using unused resources or keep them as selling resources.
