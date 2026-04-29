# Target Project Structure

This document describes the target structure for the game project.

The goal is to keep the project modular, readable, and easy to extend without mixing gameplay logic, UI, data, documentation, and tooling.

---

# Main Principles

The project should be organized around four main pillars:

```text
Game code
Game data
Documentation
Project management
```

The code should remain modular and focused:

- gameplay logic should live in systems
- UI screens should live in ui
- static game content should live in data
- design rules and roadmap notes should live in docs
- developer tools should live in tools when needed

---

# Target Folder Structure

```text
My-first-game/
│
├── core/
├── systems/
├── ui/
├── data/
│
├── docs/
├── tests/
├── tools/
│
├── .github/
│
└── README.md
```

---

# Folder Roles

## core/

Core game orchestration.

Examples:

- game state
- main game object
- high-level flow
- data loading coordination

This folder should not contain item data, balancing values, or UI layout logic.

---

## systems/

Gameplay systems and pure logic.

Examples:

- combat
- inventory
- equipment
- economy
- loot
- crafting
- progression
- stats

Systems should be testable without launching Pygame whenever possible.

---

## ui/

Pygame interface and screens.

Examples:

- menu screen
- combat screen
- inventory screen
- merchant screen
- crafting screen
- tooltips

UI code should call systems, but should not contain core gameplay rules or balancing formulas.

---

## data/

Game content stored outside the code.

Examples:

- items.json
- enemies.json
- zones.json
- recipes.json
- classes.json

The code should read this data rather than hardcoding game content.

This makes balancing and content creation easier.

---

## docs/

Design documentation and project notes.

Examples:

- economy_v1.md
- crafting_system.md
- combat_system.md
- loot_tables.md
- item_design.md
- project_structure.md

Docs should preserve important design decisions so they are not lost in chat history.

---

## tests/

Automated tests.

Examples:

- economy tests
- inventory tests
- crafting tests
- item data validation tests
- loot balance tests

Tests should protect existing behavior when new features are added.

---

## tools/

Future developer tools.

Examples:

- item generator
- enemy generator
- loot table editor
- balance simulator
- data validators

This folder should be created only when tooling becomes useful.

---

## .github/

GitHub-specific configuration.

Examples:

- GitHub Actions workflows
- issue templates
- pull request templates

---

# Data-Driven Design Rule

Gameplay code should not contain static game content.

For example:

- economy.py should contain price calculation logic
- items.json should contain item metadata
- enemies.json should contain enemy data
- recipes.json should contain crafting recipes

This separation keeps the project easier to balance and extend.

---

# Recommended GitHub Labels

Use a small set of labels to keep issues readable:

```text
feature
system
ui
balance
tooling
later
```

Suggested meaning:

- feature: new gameplay feature
- system: core gameplay or architecture work
- ui: interface-related work
- balance: tuning numbers, rewards, drops, prices, or difficulty
- tooling: developer tools
- later: postponed ideas

---

# Recommended GitHub Project Columns

Use a simple board:

```text
Backlog
Ready
In Progress
Done
Later
```

Meaning:

- Backlog: unprioritized ideas and potential future work
- Ready: defined tasks ready to be picked up
- In Progress: work currently under development
- Done: completed, tested, and validated work
- Later: deferred ideas for a later stage of the project

---

# Current Direction

The project should continue to evolve by small, stable blocks.

Recommended block order:

1. Economy and selling
2. Crafting system
3. Advanced loot tables
4. Resource gathering
5. Item and enemy generation tooling
6. Shop buying and gold sinks

Each block should remain focused and avoid unnecessary refactoring.
