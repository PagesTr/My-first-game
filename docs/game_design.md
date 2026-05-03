# Game Design

## Vision

The game is a Python/Pygame RPG with semi-idle progression.

The long-term goal is to build a game where the player manages characters, zones, combat builds, dungeons, jobs, loot, and offline progression.

The game should remain simple to understand, incremental to develop, and stable after every change.

## Core Game Loop

```text
Choose a zone
Choose an activity
Resolve combat, dungeon, job, or idle progression
Gain experience, gold, items, and resources
Improve characters, equipment, skills, and jobs
Unlock new zones, companions, and challenges
```

## Main Systems

### Zones

Zones are the foundation of the world structure.

Each zone should have:

- a clear identity;
- a list of enemies that belong to the zone;
- one dungeon;
- gathering or crafting activities;
- possible idle activities;
- rewards linked to the zone theme.

Examples:

| Zone | Identity | Enemies | Jobs |
| --- | --- | --- | --- |
| Forest | Wild nature | Wolves, boars, spiders | Woodcutting, herbalism |
| Goblin Village | Hostile settlement | Goblins, goblin guards, shamans | Scavenging |
| Graveyard | Undead area | Skeletons, zombies, ghosts | Bone gathering, occult materials |
| Mountain | Harsh terrain | Trolls, beasts, golems | Mining, hunting |

### Combat

Combat should progressively move toward an automatic turn-based system.

The player should mainly influence combat before it starts through:

- character choice;
- equipment;
- active skills;
- passive skills;
- stats;
- buffs.

Combat should remain readable and deterministic enough to test.

The active player experience should stay more rewarding than passive idle combat.

### Classes and Skills

Each class should have its own skill pool.

Skills can be:

- active skills, which trigger during combat;
- passive skills, which modify stats or behavior.

The number of equipped skill slots should increase progressively with character level or progression.

Examples:

| Class | Active idea | Passive idea |
| --- | --- | --- |
| Warrior | Occasional stronger attack | More defense or health |
| Archer | Extra opening attack | More accuracy or crit chance |
| Mage | Stun or magic burst | More magic attack |
| Rogue | Critical strike | More dodge chance |

### Dungeons

Each zone should eventually have one dungeon.

A dungeon should initially be simple:

```text
Fight several enemies from the zone
Fight a zone boss
Receive dungeon rewards
```

Dungeons should be more rewarding than simple combat, but also more demanding.

### Idle Progression

The player should be able to choose an idle activity in a zone before leaving the game.

Idle rewards should be based on:

- time spent away;
- character power;
- selected zone;
- selected enemy, job, or activity;
- active buffs and damage output.

Important balance rule:

```text
Active gameplay must always reward more than passive idle progression.
```

A safe first target is:

```text
Idle reward = around 40% to 70% of equivalent active reward.
```

### Jobs and Gathering

Jobs should be linked to zones.

Examples:

| Zone | Possible jobs |
| --- | --- |
| Forest | Woodcutting, herbalism |
| Mine | Mining |
| River | Fishing |
| Mountain | Mining, hunting |
| Village | Crafting, cooking |

In a zone, the player should eventually choose between:

- simple combat;
- dungeon;
- job activity;
- idle activity.

### Companions and Team Management

The player should eventually recruit several characters.

Short-term rule:

```text
Only one character fights at a time.
```

Long-term possibilities:

- multiple characters available;
- one active character per activity;
- companions specialized in jobs;
- later team-based combat.

Team combat is intentionally postponed because it will require deeper combat changes.

## Development Principles

- Prefer minimal and localized changes.
- Keep the game functional after every step.
- Avoid large rewrites.
- Add tests before or during risky changes.
- Add data-driven systems progressively.
- Do not create every future system before it is needed.

## Current Priority

The next technical priority is:

```text
Refine enemy identity and move toward automatic turn-based combat.
```

Recommended first implementation direction:

- add simple enemy behaviors;
- keep the current combat UI working;
- add basic combat tests;
- postpone full skill trees, dungeons, idle, and companions until the combat base is safer.
