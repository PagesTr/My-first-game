# Combat Design

This document describes the current combat direction for the project.
It should stay practical and evolve with the code.

---

## Current combat direction

Combat is moving toward an automatic turn-based system.

The player should mostly influence combat before it starts through:

- character class;
- equipment;
- stats;
- active skills;
- passive skills;
- temporary effects.

Manual actions can still exist during the transition, but the long-term design should favor build preparation and automatic resolution.

---

## Current combat flow

The current combat system is handled by `CombatSystem`.

A combat turn currently follows this structure:

```text
Choose player action
Start turn hooks
Apply player action
Check combat end
Choose enemy action
Apply enemy action
Check combat end
End turn hooks
```

The current player actions are:

- `attack`
- `heal`

When no player action is provided, the combat system chooses an automatic player action.

---

## Player automatic action

The player auto action is intentionally simple:

```text
If current HP <= 30% of max HP: heal
Otherwise: attack
```

This is not meant to be final AI.
It is a first step toward automatic combat and future skill-driven behavior.

---

## Enemy behavior

Enemies have a `behavior` value.

Supported behaviors:

- `aggressive`
- `defensive`
- `balanced`

Current rules:

| Behavior | Rule |
| --- | --- |
| aggressive | always attacks |
| defensive | heals at or below 30% HP, otherwise attacks |
| balanced | heals at or below 25% HP, otherwise attacks |

Enemy behavior gives enemies identity without creating complex AI too early.

---

## Combat hooks

Combat hooks are intended to prepare future skills and effects.

Current or planned basic hooks:

- `_on_turn_start()`
- `_on_before_action(actor, target, action, is_player)`
- `_on_after_action(actor, target, action, is_player)`
- `_on_turn_end()`

Hooks should initially stay simple and deterministic.

They may later support:

- damage bonuses;
- cooldown reduction;
- automatic skills;
- poison or bleed;
- shields;
- class passives;
- turn-based buffs.

---

## Skill design principles

Skills should be introduced progressively.

A skill can be:

- active: triggers during combat;
- passive: modifies stats or behavior without direct activation.

The first skills should be simple and hard-coded enough to validate the concept before building a full skill system.

Do not create a full skill tree until the basic combat skill loop is stable.

---

## First warrior skill direction

The first planned warrior skill is a simple comeback attack.

Concept:

```text
After the warrior has lost HP, they can occasionally perform a stronger attack.
The effect has a cooldown of several turns.
```

Initial design proposal:

- class: warrior
- trigger: before player attack
- condition: player has lost HP
- effect: increase the current attack damage
- cooldown: several turns

This should be implemented as a minimal combat rule first.

Do not create a full generic skill system yet unless the minimal version proves too limiting.

---

## Deferred combat ideas

The following ideas are useful but should not be implemented immediately:

- full skill tree;
- mana system;
- complex cooldown UI;
- stun system;
- damage over time;
- team combat;
- advanced enemy skills;
- manual defend action.

The manual defend action is deferred because combat is moving toward automatic resolution.
Defensive gameplay should preferably come from skills, passives, stats, or effects.

---

## Testing rules

Combat tests should stay deterministic.

When randomness is involved, tests should use monkeypatching or controlled values.

Priority tests:

- player attack reduces enemy HP;
- player heal restores HP;
- combat ends when enemy dies;
- combat ends when player dies;
- enemy behavior selects expected actions;
- player auto action selects expected actions;
- future skills trigger only under their conditions;
- future cooldowns prevent repeated triggers.

---

## Current next step

Implement the first warrior combat skill in the smallest safe way.

Recommended next rule:

```text
If the player is a warrior, attacks while damaged, and the skill cooldown is ready,
then the attack deals increased damage and the skill enters cooldown.
```
