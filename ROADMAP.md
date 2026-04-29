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

## Leveling and progression

- Keep leveling simple and readable before adding complex progression.
- Improve level-up rewards.
  - Stat increases
  - Max HP increase
  - Possible class-based bonuses
- Decide if the player chooses stat upgrades manually or receives automatic class-based growth.
- Add clear feedback when the player levels up.
- Review XP curve and enemy rewards after more zones are added.

## Active and passive skills

- Add a generic skill system later, separate from consumables.
- Active skills should be usable during combat.
  - Damage skill
  - Heal skill
  - Defensive skill
  - Buff or debuff skill
- Passive skills should modify the player without direct activation.
  - Permanent stat bonus
  - Loot bonus
  - Crit bonus
  - Class identity bonus
- Decide how skills are unlocked.
  - Level milestones
  - Skill tree
  - Class progression
  - Quest rewards
- Reuse the temporary effects system for active skill buffs when possible.
- Keep passive effects separate from temporary effects if they are permanent.

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
- Add level-up feedback to the result screen later.
- Add skill display when the skill system exists.

## Testing and tools

- Keep pytest coverage for inventory, loot, equipment, effects, progression, and skills.
- Add tests when new gameplay rules are added.
- Keep debug tools separate from gameplay systems.
