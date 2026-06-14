# Pull Request

Use this template to keep pull requests small, reviewable, and aligned with the project workflow.

Before opening or merging this PR, check:

- `AGENTS.md`
- `docs/ai_workflow.md`
- `docs/ai_agents_prompts.md`
- `docs/project_structure.md`
- `docs/roadmap.md`

---

## 1. Summary

Describe the change in one or two sentences.

```text

```

---

## 2. Task / Issue

Related issue or task:

```text
Closes #
```

If there is no issue, explain why this PR exists:

```text

```

---

## 3. Type of change

Select one main type:

- [ ] Bug fix
- [ ] Small UI improvement
- [ ] New local feature
- [ ] New system V1
- [ ] Data / JSON change
- [ ] Gameplay / balance change
- [ ] Test / pytest
- [ ] Documentation
- [ ] GitHub Actions / tooling
- [ ] Refactorization
- [ ] Other

If this PR mixes several types, explain why:

```text

```

---

## 4. Files changed

List the most important files changed and why.

```text
- path/to/file.py: reason
- path/to/test_file.py: reason
```

---

## 5. Scope control

Confirm that the PR stays focused.

- [ ] This PR has one clear objective.
- [ ] The change is limited to the necessary files.
- [ ] No unrelated feature is included.
- [ ] No unrelated bugfix is included.
- [ ] No unnecessary file rename was done.
- [ ] No unnecessary deletion was done.
- [ ] No global refactor was done.

If one item is not checked, explain why:

```text

```

---

## 6. Architecture check

Confirm that responsibilities remain in the correct folders.

- [ ] `core/` is used only for orchestration, state, and coordination.
- [ ] `systems/` contains gameplay logic and testable business rules.
- [ ] `entities/` contains player, enemy, or entity models.
- [ ] `ui/` and `ui/screens/` contain display, input, and screen logic only.
- [ ] `data/` contains static JSON game data when relevant.
- [ ] `tests/` contains pytest tests when logic is affected.
- [ ] `docs/` contains decisions or workflow notes when relevant.

If the PR intentionally changes architecture, explain the validated decision:

```text

```

---

## 7. AI agent workflow

If AI helped with this PR, select the agents used.

- [ ] Agent Cadrage & Découpage
- [ ] Agent Implémentation Localisée
- [ ] Agent Tests & Stabilité
- [ ] Agent Review Architecture & Git
- [ ] Agent Gameplay / Balance Data
- [ ] Agent UI / UX / Narration
- [ ] No AI used

AI notes or limitations:

```text

```

---

## 8. Tests

Select what was done.

- [ ] `pytest` was run.
- [ ] A targeted pytest command was run.
- [ ] New tests were added.
- [ ] Existing tests were updated.
- [ ] No tests were needed because this is documentation only.
- [ ] No tests were needed because this is a pure UI/text change.
- [ ] Manual `python main.py` check was done because UI is affected.
- [ ] GitHub Actions must pass before merge.

Commands run:

```bash

```

Test result:

```text

```

---

## 9. Manual verification

Describe manual checks, especially if UI, gameplay feel, or data balance is affected.

```text

```

---

## 10. Risks and regressions

List possible risks introduced by this PR.

Examples:

- behavior changed unintentionally;
- tests do not cover a case;
- UI behavior needs manual verification;
- balance values may need later tuning;
- change may need to be split.

Risks:

```text

```

---

## 11. Out of scope

List what this PR intentionally does not do.

Examples:

- no global refactor;
- no full system rewrite;
- no future roadmap block;
- no broad balance pass;
- no unrelated UI work.

Out of scope:

```text

```

---

## 12. Review checklist

Before merge, confirm:

- [ ] The PR is small enough to review.
- [ ] The PR matches its title and description.
- [ ] Modified files are coherent with the task.
- [ ] Tests are sufficient or the absence of tests is justified.
- [ ] The change preserves existing behavior unless stated otherwise.
- [ ] Architecture-sensitive changes were validated by the human developer.
- [ ] No branch was created, deleted, renamed, or merged automatically by an AI agent.
- [ ] This PR must not be merged into `main` without human validation.

---

## 13. Suggested commit / merge summary

Write the final summary that should appear in Git history.

```text

```
