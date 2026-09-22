## Skill evolution session{round_banner}

You are improving the procedural skill `SKILL.md` in your working directory so
that future agents solve this CLASS of task more reliably.
{round_context}{rejected_context}
## The task class this skill must serve
{task_instruction}

## Sections in the current SKILL.md
Preserve useful working guidance. Add or reorganize sections when a minimal general fix needs them.
{preserve_headings}

## Train traces to diagnose
There are {n_traces} train trace(s) under `traces/`, from source model(s):
{source_models}. Each `traces/<id>/` has `solve.py` (the code that model
produced under the parent skill), `result.json` (scalar pass/total), and
`evidence.md` (sanitized failure signal). These are the procedural-memory
traces you are learning from.

## Round protocol — follow exactly
Step 1 — Diagnose. Read EVERY `traces/<id>/` (all three files). Form a single
  CONSENSUS diagnosis of the recurring procedural gap across the traces — not a
  per-trace patch. A gap that appears in one idiosyncratic trace is weaker
  signal than one repeated across traces/models.
Step 2 — Edit. Improve SKILL.md so the gap is closed as a GENERAL procedure —
  revise, add, or reorganize sections however fits best. Keep working guidance
  the traces did not implicate; fix root causes rather than regenerate from
  scratch. Edit the file in place. If the parent SKILL.md already handles the
  gap, leave it unchanged.
Step 3 — Record your decision NOW. Write `DIAGNOSIS.json` (keys below) to the
  working directory IMMEDIATELY, before any self-validation. SKILL.md and
  DIAGNOSIS.json are your PRIMARY deliverables — the harness lifts them from
  disk, so they must already exist if you later run out of time.
  `rewrite_recommended` is coupled to your EDIT, not to your opinion: set it
  `true` if you changed SKILL.md in any way, and `false` ONLY when you left
  SKILL.md byte-for-byte identical to the parent (because the parent already
  closes the gap). Editing SKILL.md AND setting `rewrite_recommended:false` is a
  contradiction — the harness then discards your edit and keeps the buggy
  parent, wasting the session. If your diagnosis is `severity:critical`/`major`
  with `evidence_sufficiency:sufficient`, you found a real gap: edit the file and
  set `rewrite_recommended:true`.
Step 4 — Self-validate ONLY if budget remains (AT MOST 2 short cycles). Write
  `solution.py` from ONLY your edited SKILL.md + the task instruction (you are
  blind to the tests), run `bash solve.sh`, then `bash measure.sh`, and read
  ONLY the aggregate `passed/total`. The deliverable is a better GENERAL skill,
  NOT a passing solution — do NOT keep iterating to make one task instance pass.
  A higher self-score earned by specializing to THESE traces will be REJECTED:
  the harness re-scores the parent vs. your skill on held-back cases you never
  see, and keeps the parent unless your skill wins THERE. If a cycle reveals a
  clear, general refinement, make the smallest edit and UPDATE `DIAGNOSIS.json`
  (`best_self_score`, `rounds_self_run`). Stop as soon as you are out of
  evidence-grounded hypotheses or budget.

## DIAGNOSIS.json keys (EXACTLY these)
  {{"consensus_pattern": str, "root_cause": str, "skill_gap": str,
    "suggested_fix": str, "severity": "critical|major|minor|info",
    "evidence_sufficiency": "sufficient|insufficient",
    "rewrite_recommended": bool,  // true iff you changed SKILL.md
    "rounds_self_run": int, "best_self_score": "passed/total"}}
Do NOT print SKILL.md or its body in chat — only the files on disk matter.

## Size envelope (HARD)
Keep the body within {max_chars} characters and {max_lines} non-empty lines.
Edit churn is capped; broad rewrites are rejected before scoring.
