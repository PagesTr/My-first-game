# Project Roadmap

This file tracks planned improvements and deferred ideas.
It should stay short, practical, and focused on the next useful development steps.

## Inventory and items

- Remove temporary test items from the starting inventory when another acquisition method exists.
  - `rage_potion`
  - `guard_potion`
- Decide how buff consumables become available.
  - Enemy drops
  - Shop
  - Crafting
  - Quest rewards
  - Chests
- Add a proper value and selling system for resources.
- Improve item tooltips.
  - Show effects more clearly.
  - Separate item value from combat stats.
  - Add descriptions later.
- Decide whether the temporary `Compact` button should stay or be removed later.

## Temporary effects

- Display active effects in combat, not only in the inventory.
- Connect time-based effects to a real game clock.
- Add more effect types later.
  - Poison
  - Bleed
  - Healing over time
  - Shield
  - Damage reduction
  - XP bonus
  - Loot bonus
- Keep the current stacking rule by default.
  - Same effect id refreshes duration.
  - Different effect ids can coexist.
- Decide later if rare effects need special stacking rules.

## Loot and resources

- Use `tools/simulate_loot.py` after drop changes to check balance.
- Give rare resources a real use.
  - `troll_heart`
  - `warrior_trophy`
  - `hidden_pouch`
  - `goblin_charm`
- Decide the main purpose of resources.
  - Selling
  - Crafting
  - Equipment upgrades
  - Quests

## Consumables

- Add more buff consumables only when their effects are supported.
- Possible future consumables:
  - Critical chance potion
  - Dodge potion
  - Loot bonus potion
  - XP bonus potion
  - Out-of-combat healing item

## UI

- Improve the Active Effects panel readability.
- Show multiple modifiers per effect when needed.
- Add buff and debuff colors later.
- Keep tooltip and comparison behavior simple and readable.

## Testing and tools

- Keep pytest coverage for inventory, loot, equipment, and effects.
- Add tests when new gameplay rules are added.
- Keep debug tools separate from gameplay systems.
