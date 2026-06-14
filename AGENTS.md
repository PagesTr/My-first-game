# AGENTS.md

This file defines the default instructions for AI coding agents working on this repository.

Primary references:

- `docs/ai_workflow.md`
- `docs/ai_agents_prompts.md`
- `docs/project_structure.md`
- `docs/roadmap.md`

AI agents must read and follow these documents before proposing or modifying code.

---

## 1. Project context

This is a Python / Pygame game project.

Current working branch for integration is:

```text
integ
```

The default branch is `main`, but agents must not merge into `main`.

The project is in a learning and incremental development phase.

Main goals:

- keep the game playable;
- progress through small stable steps;
- preserve the current architecture;
- keep changes understandable;
- keep Git history clean;
- help the human developer learn instead of replacing technical understanding.

---

## 2. Repository structure

Expected architecture:

```text
core/          high-level orchestration, game state, coordination
systems/       gameplay logic and testable business rules
entities/      player, enemies, structures, game entities
ui/            Pygame interface layer
ui/screens/    game screens
assets/        images, sounds, fonts, music
data/          JSON game data
tests/         pytest tests
docs/          roadmap, design notes, workflow decisions
.github/       GitHub issue, PR and CI configuration
```

Responsibility rules:

- `core/` orchestrates and coordinates.
- `systems/` contains testable gameplay logic.
- `entities/` contains game entities.
- `ui/` and `ui/screens/` handle display, input and screens.
- `data/` contains static game content in JSON.
- `tests/` protects important behavior with pytest.
- `docs/` preserves decisions and workflow rules.

Do not move responsibilities between folders without explicit human validation.

---

## 3. General development rules

Always prefer:

- small changes;
- localized edits;
- readable code;
- simple solutions;
- explicit behavior;
- pytest coverage for important logic;
- preserving existing behavior;
- clear commit messages.

Avoid:

- global refactors;
- unnecessary renaming;
- premature generic systems;
- hidden architecture changes;
- broad formatting-only changes;
- mixing unrelated tasks;
- modifying many files at once;
- hardcoding static game content inside gameplay systems;
- placing business logic inside UI code.

If a task is unclear, too broad or risky, stop and propose a smaller plan before implementation.

---

## 4. Git restrictions

Agents must not perform these actions unless the human explicitly asks:

```text
create a branch
delete a branch
rename a branch
merge a branch
merge into main
rewrite Git history
force push
delete files
rename files
perform a global refactor
```

Agents may suggest Git commands, but the human keeps final control.

Before any commit or PR recommendation, agents must check:

- whether the change has one clear purpose;
- whether the modified files are coherent with the task;
- whether tests are needed;
- whether the change should be split;
- whether the change respects the architecture.

---

## 5. Agent role selection

Before responding to a development task, classify the task and use the appropriate role from `docs/ai_agents_prompts.md`.

Use **Agent Orchestrateur de Workflow** as the default entry point when:

- the task is unclear;
- the task has several steps;
- several agents may be needed;
- the human asks for a simplified workflow;
- the task involves issue, PR, tests, Git or Codex coordination;
- the human wants only the next validation action.

The orchestrator coordinates the workflow, but must not code directly, merge, delete files, rename branches, or make architecture decisions alone.

Use this routing:

| Task type | Required role |
| --- | --- |
| unclear task | Agent Orchestrateur de Workflow first |
| broad task | Agent Orchestrateur de Workflow first |
| multi-step task | Agent Orchestrateur de Workflow first |
| request to reduce copy-paste | Agent Orchestrateur de Workflow first |
| new feature | Agent Orchestrateur de Workflow, then Agent Cadrage & Découpage |
| localized code change | Agent Implémentation Localisée |
| system logic change | Agent Tests & Stabilité also required |
| `systems/` change | Agent Tests & Stabilité also required |
| `entities/` change | Agent Tests & Stabilité also required |
| `data/` balance change | Agent Gameplay / Balance Data |
| UI or screen change | Agent UI / UX / Narration if useful |
| pre-commit review | Agent Review Architecture & Git |
| PR review | Agent Review Architecture & Git |
| architecture-sensitive task | Agent Orchestrateur de Workflow, then Agent Cadrage & Découpage, then human validation |

Do not jump directly to implementation when orchestration or cadrage is required.

---

## 6. Required workflow by task size

### Orchestrated task

Use when the human asks for one validation step at a time.

```text
Agent Orchestrateur de Workflow
Human validation: OK / STOP / MODIFIER
Then only the agent selected by the orchestrator
Agent Review Architecture & Git before commit or PR
```

Expected scope:

- one next action at a time;
- explicit allowed and forbidden files;
- no coding by the orchestrator;
- no hidden expansion of the task.

---

### Very small fix

Use:

```text
Agent Implémentation Localisée
Agent Tests & Stabilité if logic is affected
Agent Review Architecture & Git before commit
```

Expected scope:

- one clear bug or adjustment;
- one or two files if possible;
- no refactor.

---

### Local feature

Use:

```text
Agent Orchestrateur de Workflow if the task has several steps
Agent Cadrage & Découpage
Agent Implémentation Localisée
Agent Tests & Stabilité
Agent Review Architecture & Git
```

Expected scope:

- clear behavior;
- limited files;
- tests for logic;
- no unrelated changes.

---

### New system

Use:

```text
Agent Orchestrateur de Workflow
Agent Cadrage & Découpage
Human validation
Agent Tests & Stabilité
Agent Implémentation Localisée by small increments
Agent Review Architecture & Git
Human validation before merge
```

Expected scope:

- minimal V1 first;
- no full system in one step;
- document important decisions if architecture changes.

---

### Architecture-sensitive task

Use:

```text
Agent Orchestrateur de Workflow
Agent Cadrage & Découpage
Agent Review Architecture & Git
Human validation
Implementation only after approval
```

Do not code before validation.

---

## 7. Testing rules

Use pytest for important logic.

Preferred command:

```bash
pytest
```

For targeted tests, use for example:

```bash
pytest tests/test_inventory.py
pytest tests/test_loot.py
pytest tests/test_progression.py
```

If UI behavior is modified, also recommend a manual launch:

```bash
python main.py
```

Tests should avoid launching the Pygame loop when the logic can be tested without UI.

---

## 8. File-specific guidance

### core/

Allowed for orchestration and high-level flow only.

Do not place balancing data, item data or screen layout logic here.

### systems/

Allowed for gameplay rules and testable logic.

Systems should be usable without launching Pygame whenever possible.

### entities/

Allowed for player, enemies and game entity models.

Avoid turning entities into orchestration containers.

### ui/ and ui/screens/

Allowed for rendering, input handling and screen flow.

Do not place core gameplay rules, balancing formulas or item definitions here.

### data/

Allowed for JSON content such as items, enemies, zones, recipes, classes and balance values.

Do not duplicate static content in Python code when it belongs in JSON.

### tests/

Use for pytest coverage of systems, entities, data validation and regression cases.

### docs/

Use for roadmap, design notes, architectural decisions and AI workflow documentation.

---

## 9. Output expectations for agents

When orchestrating a workflow, include:

```text
Diagnostic
Périmètre proposé
Fichiers autorisés
Fichiers interdits
Étapes minimales
Prochaine action
Validation demandée: OK / STOP / MODIFIER
```

When proposing a change, include:

```text
Summary
Files affected
Implementation plan or patch
Tests to run
Risks
What is intentionally out of scope
```

When reviewing a change, include:

```text
Architecture check
File scope check
Test coverage check
Git risk check
Suggested commit message
Verdict: OK / OK with reservations / Needs changes / Split before commit
```

---

## 10. Current project priority

Follow the roadmap in `docs/roadmap.md`.

Do not advance future blocks early unless the human explicitly asks.

If the current task conflicts with the roadmap or appears premature, say so and propose a smaller step.

---

## 11. Final rule

The goal is not to maximize automation.

The goal is to help the human developer make steady, understandable and testable progress while keeping control of architecture, Git and gameplay decisions.
