---
name: AI-ready task
description: Prepare a scoped task for ChatGPT, Codex, or another AI coding agent
title: "[AI Task] "
labels: ["ai-task"]
assignees: []
---

# AI-ready task

Use this template to prepare a task before asking an AI agent to help.

The goal is to keep changes small, understandable, testable, and aligned with the current architecture.

Before using an AI coding agent, check:

- `AGENTS.md`
- `docs/ai_workflow.md`
- `docs/ai_agents_prompts.md`
- `docs/project_structure.md`
- `docs/roadmap.md`

---

## 1. Task type

Select one main type:

- [ ] Bug localized
- [ ] Small UI improvement
- [ ] New local feature
- [ ] New system
- [ ] Data / JSON change
- [ ] Gameplay / balance change
- [ ] Test / pytest
- [ ] Documentation
- [ ] GitHub Actions / tooling
- [ ] Refactorization
- [ ] PR review
- [ ] Other

If the task touches architecture, several systems, or many files, it must go through **Agent Cadrage & Découpage** before implementation.

---

## 2. Recommended AI agent

Select the first agent to use:

- [ ] Agent Cadrage & Découpage
- [ ] Agent Implémentation Localisée
- [ ] Agent Tests & Stabilité
- [ ] Agent Review Architecture & Git
- [ ] Agent Gameplay / Balance Data
- [ ] Agent UI / UX / Narration

Recommended routing:

| Situation | First agent |
| --- | --- |
| Task is unclear or broad | Agent Cadrage & Découpage |
| Code change is already scoped | Agent Implémentation Localisée |
| Logic in systems/entities/data changes | Agent Tests & Stabilité also required |
| Data, XP, loot, economy or balance change | Agent Gameplay / Balance Data |
| UI text, screen, feedback or narration | Agent UI / UX / Narration |
| Before commit or PR | Agent Review Architecture & Git |

---

## 3. Objective

Describe the expected result in one or two sentences.

```text
Example:
Add a simple defensive behavior for enemies during combat.
```

Objective:

```text

```

---

## 4. Context

Explain why this task exists and how it fits the current roadmap or current problem.

```text
Example:
The current roadmap focuses on combat refinement. This task should improve enemy identity without adding a full skill system or major UI changes.
```

Context:

```text

```

---

## 5. Current behavior

Describe what currently happens.

```text
Example:
All enemies use the same attack behavior.
```

Current behavior:

```text

```

---

## 6. Expected behavior

Describe what should happen after the task is completed.

```text
Example:
Defensive enemies should sometimes reduce incoming damage or choose a safer combat action.
```

Expected behavior:

```text

```

---

## 7. Files allowed

List the files or folders the AI may inspect or modify.

```text
Example:
- systems/combat.py
- entities/enemy.py
- tests/test_combat.py
```

Allowed files:

```text

```

---

## 8. Files forbidden or sensitive

List files or folders that should not be modified without explicit human validation.

Default sensitive areas:

```text
main.py
core/*
.github/workflows/*
data/*.json in bulk
large cross-folder changes
```

Forbidden or sensitive files:

```text

```

---

## 9. Out of scope

List what must not be done in this task.

Examples:

- no global refactor;
- no branch creation;
- no merge;
- no file rename;
- no full system rewrite;
- no unrelated UI change;
- no balance overhaul;
- no future roadmap block unless explicitly requested.

Out of scope:

```text

```

---

## 10. Acceptance criteria

The task is done only if these criteria are met.

Examples:

- [ ] The new behavior is implemented locally.
- [ ] Existing behavior is preserved.
- [ ] No unrelated files are modified.
- [ ] Relevant pytest tests pass.
- [ ] Manual launch is checked if UI is affected.
- [ ] The change can be summarized in one clear commit message.

Acceptance criteria:

- [ ] 
- [ ] 
- [ ] 

---

## 11. Tests expected

Select what is expected.

- [ ] No test needed because this is documentation only
- [ ] Existing tests only
- [ ] New pytest test required
- [ ] Existing pytest test must be updated
- [ ] Manual `python main.py` check required because UI is affected
- [ ] GitHub Actions check required

Commands to run:

```bash
pytest
```

If UI is affected:

```bash
python main.py
```

Specific test command if known:

```bash

```

---

## 12. Risks

List the risks the AI must watch for.

Examples:

- logic placed in the wrong folder;
- too many files modified;
- behavior changed unintentionally;
- tests missing;
- UI depends on business rules;
- data hardcoded in Python;
- feature becomes larger than planned.

Risks:

```text

```

---

## 13. Human decisions required

List decisions that the AI must not make alone.

Examples:

- architecture change;
- branch creation or merge;
- balancing values with major gameplay impact;
- deletion or renaming;
- roadmap priority change.

Human decisions required:

```text

```

---

## 14. Expected AI output

The AI response should include:

```text
Summary
Files affected
Implementation plan or patch
Tests to run
Risks
What is intentionally out of scope
```

For review tasks, the AI response should include:

```text
Architecture check
File scope check
Test coverage check
Git risk check
Suggested commit message
Verdict: OK / OK with reservations / Needs changes / Split before commit
```

---

## 15. Final checklist before implementation

- [ ] The task has one clear objective.
- [ ] The first AI agent role is selected.
- [ ] Files allowed are listed.
- [ ] Files forbidden or sensitive are listed.
- [ ] Out-of-scope items are explicit.
- [ ] Tests are defined.
- [ ] Human decisions are identified.
- [ ] The task is small enough for one focused change.
