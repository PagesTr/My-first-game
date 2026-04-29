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

## Professions and crafting jobs

- Add professions only after resources have a clear purpose.
- Possible professions:
  - Blacksmithing for weapons and armor upgrades
  - Alchemy for potions and consumables
  - Leatherworking for armor and utility items
  - Gathering for raw resources
- Keep the first profession system simple.
  - Profession level
  - XP per craft
  - Basic recipes
- Avoid adding too many professions before crafting is useful.
- Decide if professions are unlocked by level, quests, or zones.

## Crafting and upgrades

- Add a simple recipe system later.
- Recipes should consume resources and create items or consumables.
- Equipment upgrades can use rare resources later.
- Keep crafting separate from loot generation.
- Add recipe tests before adding many recipes.

## Economy and shops

- Add basic item selling before complex shops.
- Use item `value` when selling resources.
- Add shops later for consumables and starter gear.
- Keep prices simple until the economy is balanced.

## Quests and objectives

- Add simple objectives later.
  - Defeat enemies
  - Collect resources
  - Reach a level
  - Craft an item
- Use quests to introduce systems progressively.
- Avoid complex branching quests early.

## Zones and exploration

- Add more zones after current systems are stable.
- Use zones to introduce enemy families, resources, and professions.
- Decide if zones have special effects or modifiers.
- Keep zone unlock rules simple at first.

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
- Add profession display when professions exist.
- Add crafting UI only after the recipe system exists.

## Save system

- Add save and load only after the player state becomes worth preserving.
- Save player progression, inventory, equipment, effects, and unlocked zones.
- Keep the first save format simple and JSON-based.
- Add tests for save data compatibility later.

## Testing and tools

- Keep pytest coverage for inventory, loot, equipment, effects, progression, and skills.
- Add tests when new gameplay rules are added.
- Keep debug tools separate from gameplay systems.
