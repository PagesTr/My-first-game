# Project Roadmap

This file tracks planned improvements and deferred ideas.
It should stay practical, but now also aligned with the global block-based roadmap.

---

# Global Development Strategy

The project evolves in small, stable, and incremental blocks.

Each block must:

- keep the game playable;
- avoid breaking existing systems;
- modify as few files as possible;
- be testable;
- prepare the next block without overengineering.

---

# Current Block

## Block 1 — Combat refinement

Objective:

- improve enemy identity;
- prepare automatic combat behavior;
- stabilize the combat system.

Scope:

- enemy behaviors (aggressive, defensive, balanced);
- basic AI improvements;
- minimal extensions to combat actions;
- add combat tests.

Avoid:

- full skill systems;
- full automation;
- major UI changes.

---

# Future Blocks

## Block 2 — Zones system

- introduce zones
- link enemies to zones
- define zone identity

## Block 3 — Dungeons

- sequential fights
- boss per zone

## Block 4 — Skills system

- active and passive skills
- class identity

## Block 5 — Idle system

- offline progression
- balance with active play

## Block 6 — Jobs and gathering

- zone-based professions

## Block 7 — Companions

- multiple characters
- specialization

---

# Detailed Systems (from original roadmap)

## Inventory and items

- Remove temporary test items from the starting inventory when another acquisition method exists.
- Decide how buff consumables become available.
- Add a proper value and selling system for resources.
- Improve item tooltips.

## Leveling and progression

- Keep leveling simple before adding complexity.
- Improve level-up rewards.
- Add clear feedback on level-up.
- Review XP curve after zones are added.

## Active and passive skills

- Add a generic skill system (Block 4).
- Active skills during combat.
- Passive skills modifying stats.
- Decide unlocking method.
- Reuse temporary effects system.

## Professions and crafting jobs

- Add professions after resources are useful.
- Keep first version simple.

## Crafting and upgrades

- Stabilize Craft V1.
- Keep crafting separate from loot.

## Economy and shops

- Add selling system first.
- Add shops later.

## Quests and objectives

- Add simple objectives.
- Use quests to introduce systems.

## Zones and exploration

- Expand zones (Block 2).
- Add identity and content per zone.

## Temporary effects

- Display effects in combat.
- Add more effect types later.

## Loot and resources

- Balance drops.
- Give resources a purpose.

## Consumables

- Add new consumables only when supported.

## UI

- Improve readability.
- Add skill and profession UI later.

## Save system

- Add save/load later.
- Keep JSON format.

## Testing and tools

- Maintain pytest coverage.
- Add tests with each new system.

---

# Next Step

Focus on:

```text
Block 1 — Combat refinement
```

Specifically:

- enemy behavior
- AI improvement
- combat stability
- first tests
