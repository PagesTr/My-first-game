# Roadmap

## Development Strategy

The project evolves in small, stable, and incremental blocks.

Each block must:

- keep the game playable;
- avoid breaking existing systems;
- modify as few files as possible;
- be testable;
- prepare the next block without overengineering.

---

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

## Block 2 — Zones system

Objective:

- introduce zones as the main game structure.

Scope:

- define zones in data;
- link enemies to zones;
- simple zone selection.

Avoid:

- complex navigation;
- full world map.

---

## Block 3 — Dungeons

Objective:

- add structured challenges per zone.

Scope:

- sequential fights;
- simple boss;
- reward system.

Avoid:

- complex dungeon layouts;
- branching paths.

---

## Block 4 — Skills system

Objective:

- introduce class identity through skills.

Scope:

- passive stat modifiers;
- simple triggered active effects;
- skill slots.

Avoid:

- complex cooldown systems;
- full skill trees.

---

## Block 5 — Idle system

Objective:

- allow passive progression.

Scope:

- offline reward calculation;
- zone-based idle activity.

Constraint:

- active play must remain more rewarding.

---

## Block 6 — Jobs and gathering

Objective:

- add resource collection systems.

Scope:

- zone-based jobs;
- simple progression.

---

## Block 7 — Companions

Objective:

- manage multiple characters.

Scope:

- recruitment;
- specialization;
- multiple activity assignments.

Avoid:

- team combat at this stage.

---

## Long-Term Goals

- team-based combat;
- advanced skill trees;
- deeper dungeon mechanics;
- economy and crafting depth;
- balancing idle vs active gameplay.

---

## Next Step

Focus on:

```text
Block 1 — Combat refinement
```

Specifically:

- add enemy behavior;
- improve enemy AI;
- ensure combat remains stable;
- add first combat tests.