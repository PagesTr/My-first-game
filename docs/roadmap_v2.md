# Project Roadmap V2

This roadmap merges the block-based roadmap with the older detailed roadmap.
It reflects what is currently visible in the code on the `feature_craft` branch.

Do not treat this file as a final design document. It is a practical working roadmap.

---

## Current state observed in code

### Combat

Already present:

- `systems/combat.py` contains a turn-based combat system.
- Player actions currently include `attack` and `heal`.
- Enemy AI now uses `behavior`.
- Supported enemy behaviors:
  - `aggressive`
  - `defensive`
  - `balanced`
- Combat uses existing stats such as attack, defense, accuracy, dodge, block, crit, and healing power.

Next useful steps:

- Add more combat tests.
- Keep enemy behavior simple for now.
- Prepare the move toward automatic combat without replacing the current UI immediately.

### Enemies

Already present:

- `data/enemies.json` defines enemies, stats, rewards, drops, and behavior.
- `entities/enemy.py` creates scaled enemy instances.
- Enemy behavior defaults to `balanced` when missing.

Next useful steps:

- Keep enemy identity consistent with zones.
- Avoid adding advanced enemy skills before combat is stable.

### Zones

Already present:

- `data/zones.json` defines zones.
- Zones already include:
  - name
  - description
  - unlock level
  - enemy pool
  - loot table
  - difficulty multiplier
  - farming rate

Next useful steps:

- Improve zone identity.
- Make enemy pools more thematic.
- Later, connect jobs and dungeons to zones.

### Crafting

Already present:

- `systems/crafting.py` exists.
- `data/recipes.json` exists.
- Crafting supports stackable and unique ingredients.
- Crafting can produce stackable or unique results.
- Tests exist in `tests/test_crafting.py`.

Next useful steps:

- Stabilize Craft V1.
- Keep crafted items separate from loot-only items.
- Add only a small number of recipes until resources have a stronger purpose.

### Effects and stats

Already present:

- A generic temporary effects system exists.
- Stats can include temporary modifiers.
- Effects can be combat-based or time-based.

Next useful steps:

- Display active effects in combat.
- Reuse effects later for skills, buffs, zones, and consumables.

### Testing

Already present:

- Combat tests exist.
- Crafting tests exist.
- Other systems already have pytest coverage.

Next useful steps:

- Add tests when new gameplay rules are added.
- Keep tests deterministic when randomness is involved.

---

## Global development blocks

### Block 1 — Combat refinement

Goal:

- improve enemy identity;
- prepare automatic turn-based combat;
- keep combat stable.

Current status:

- enemy behaviors are implemented.
- first combat behavior tests exist.

Next steps:

- add tests for basic attack, heal, victory, and defeat;
- decide how player auto action should work;
- avoid skill systems for now.

Do not do yet:

- full skill trees;
- stun effects;
- cooldowns;
- team combat;
- major UI redesign.

### Block 2 — Zones and enemy identity

Goal:

- make zones central to exploration and enemy selection.

Current status:

- zones already exist in data.
- each zone has an enemy pool.

Next steps:

- strengthen zone identity;
- make forest focus more on animals and natural enemies;
- move goblins toward a dedicated goblin area later;
- prepare one dungeon per zone.

### Block 3 — Dungeons

Goal:

- add structured zone challenges.

Future scope:

- several fights in sequence;
- one boss per zone;
- rewards at the end.

Keep first version simple:

- no dungeon map;
- no branching paths;
- reuse combat.

### Block 4 — Active and passive skills

Goal:

- add class identity through skills.

Future scope:

- active skills that modify combat actions;
- passive skills that modify stats;
- progressive skill slots.

Examples:

- warrior: occasional stronger attack;
- archer: opening extra attack;
- mage: stun or magic effect.

Keep first version simple:

- one or two skills only;
- no full skill tree at first.

### Block 5 — Idle system

Goal:

- allow offline progression by zone.

Future scope:

- select zone activity before leaving;
- calculate rewards based on time away and character power;
- ensure active play remains more rewarding than passive play.

Balance rule:

- idle rewards should generally stay below active rewards.

### Block 6 — Jobs and gathering

Goal:

- add professions and gathering linked to zones.

Future scope:

- forest: woodcutting or herbalism;
- mountain: mining;
- other zones: thematic resources.

Keep first version simple:

- profession level;
- basic rewards;
- no complex crafting economy yet.

### Block 7 — Companions

Goal:

- recruit and manage several characters.

Future scope:

- one active character at first;
- later, assign different characters to different activities;
- later, specialize companions in jobs.

Do not do yet:

- team combat.

---

## Detailed backlog by system

### Inventory and items

- Remove temporary test items from starting inventory when another acquisition method exists.
- Decide how buff consumables become available:
  - enemy drops;
  - shop;
  - crafting;
  - quests;
  - chests.
- Add item selling.
- Improve item tooltips.
- Separate item value from combat stats.

### Leveling and progression

- Keep leveling simple and readable.
- Improve level-up rewards.
- Decide between manual stat upgrades and automatic class-based growth.
- Add clear level-up feedback.
- Review XP curve after more zone content is added.

### Skills

- Add a generic skill system later.
- Keep active skills separate from consumables.
- Keep permanent passive skills separate from temporary effects.
- Reuse the effects system where appropriate.

### Professions and crafting jobs

- Add professions only after resources have a clear purpose.
- Possible professions:
  - blacksmithing;
  - alchemy;
  - leatherworking;
  - gathering.
- Decide unlock method:
  - level;
  - quests;
  - zones.

### Crafting and upgrades

- Craft V1 is active on this branch.
- Recipes are stored in `data/recipes.json`.
- Recipes consume stackable or unique inventory items.
- Crafted items should stay separate from droppable items.
- Keep crafting separate from loot generation.
- Add upgrades later using rare resources.

### Economy and shops

- Add basic item selling before complex shops.
- Use item `value` when selling resources.
- Add shops later for consumables and starter gear.
- Keep prices simple until economy is balanced.

### Quests and objectives

- Add simple objectives later:
  - defeat enemies;
  - collect resources;
  - reach a level;
  - craft an item.
- Use quests to introduce systems progressively.
- Avoid branching quests early.

### Zones and exploration

- Use zones to introduce enemy families, resources, professions, and dungeons.
- Keep unlock rules simple.
- Add zone identity before complex map navigation.

### Temporary effects

- Display active effects in combat.
- Connect time-based effects to a real game clock later.
- Future effect types:
  - poison;
  - bleed;
  - healing over time;
  - shield;
  - damage reduction;
  - XP bonus;
  - loot bonus.
- Keep current stacking rule by default.

### Loot and resources

- Use `tools/simulate_loot.py` after drop changes.
- Give rare resources a real use:
  - `troll_heart`;
  - `warrior_trophy`;
  - `hidden_pouch`;
  - `goblin_charm`.
- Decide main resource purpose:
  - selling;
  - crafting;
  - upgrades;
  - quests.

### Consumables

- Add more buff consumables only when supported.
- Possible future consumables:
  - critical chance potion;
  - dodge potion;
  - loot bonus potion;
  - XP bonus potion;
  - out-of-combat healing item.

### UI

- Improve active effects readability.
- Show active effects in combat.
- Add skill display when skills exist.
- Add profession display when professions exist.
- Improve crafting UI only after recipe logic is stable.

### Save system

- Add save/load when player state becomes worth preserving.
- Save:
  - progression;
  - inventory;
  - equipment;
  - effects;
  - unlocked zones;
  - later companions and jobs.
- Keep first format JSON-based.

### Testing and tools

- Keep pytest coverage for:
  - inventory;
  - loot;
  - equipment;
  - effects;
  - progression;
  - combat;
  - crafting.
- Add tests for every new gameplay rule.
- Keep debug tools separate from gameplay systems.

---

## Immediate next steps

1. Finish and validate the current enemy behavior change.
2. Run pytest locally and with GitHub Actions.
3. Add missing combat tests for core combat outcomes.
4. Then decide between:
   - player auto action;
   - defend action;
   - combat effect display.
