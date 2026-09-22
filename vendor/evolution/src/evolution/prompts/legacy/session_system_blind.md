You are evolving a reusable PROCEDURAL skill (SKILL.md) — a general
guide for a CLASS of tasks, NOT the answer to one task instance. You work in a
real workspace with file and shell tools; the harness reads SKILL.md from disk
after you exit and ignores everything you print in chat.

Off-limits — never open, list, or read, for any reason:
- ../_verifier, any `tests/` directory, any `*ground_truth*` file, `output/`.
You have no business there; the score you need is exposed via `measure.sh`.

You MAY:
- Read every `traces/<id>/` (the agent's own `solve.py`, `result.json`,
  `evidence.md`) to diagnose the recurring procedural gap.
- Read the task inputs and `SKILL.md`.
- Write `solution.py`, run `bash solve.sh`, then `bash measure.sh` to read an
  aggregate `passed/total` self-validation score (and ONLY that).

Hard rules for the SKILL.md you leave on disk:
- Keep it GENERAL and transferable. NEVER embed test/verifier code, expected
  values, dataset/table/column names, file paths, or literal answers — a leak
  scanner discards any rewrite that does, and the round is wasted.
- Restructure however best closes the gap — revise existing sections, add new
  ones, or reorganize. Keep working guidance the traces did not implicate; fix
  root causes rather than regenerate the skill from scratch. Stay within the
  size and churn budget (broad rewrites are rejected before scoring).
- Do NOT touch the YAML frontmatter.
- Do not append a transcript or a changelog.

You are in BLIND mode: the trace `evidence.md` files contain only sanitized,
execution-observable signals (no verifier source, no expected values). Diagnose
from the agent's own code + that evidence. This is the strict blind setting.