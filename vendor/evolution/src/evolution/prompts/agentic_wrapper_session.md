# Skill Editing — Runnable Tool Session

You are evolving one reusable skill (SKILL.md) so a separate, weaker solver that follows it succeeds more often on this task class. You have a runnable workspace with real train tasks and full tools (shell, read, write).

## Tool Protocol
- Off-limits — never open, list, or read, for any reason: the verifier, any `tests/` directory, any ground-truth file, or `output/`. You have no business there; the only score you may read is the aggregate `passed/total` from `measure.sh`.
- You MAY read `TRACES.md` when present. It contains sanitized train-trace evidence. You MAY also read task inputs and the current skill body in `SKILL.md`. Write `solution.py`, then run `bash solve.sh` and `bash measure.sh` to read only that aggregate self-check score. Stay inside this workspace and do not modify `tasks/`.
- There are {n_traces} train trace(s) this round; diagnose the recurring procedural gap across them, not a per-trace patch.

## Task Context
{task_context}

{runtime_contract}

## Current Skill Body
{skill_body}

## Evidence Policy
{evidence_policy}

{round_memory}
{rejected_attempts}

## Editing Rules

{{include:_blocks/leak_rules}}

{{include:_blocks/generality_rules}}

{{include:_blocks/refinement_rules}}

## Edit Brake

{edit_brake_policy}

## Round Protocol
- Diagnose the consensus gap across the {n_traces} traces, then decide AT MOST {edit_budget} surgical edits that close it while keeping the body within {size_budget}. Preserve what the round memory marks as working, and do not repeat a rejected attempt.
- Self-validate only if budget remains, at most two short cycles: write `solution.py` from your intended skill plus the task instruction (you are blind to the tests), run `bash solve.sh` then `bash measure.sh`, and read only the aggregate `passed/total`. The deliverable is a better GENERAL skill, not a passing one-off — a higher self-score won by specializing to these traces is rejected when the parent and your skill are re-scored on held-out cases you never see.
- If the current skill already closes the gap, return an empty edit list.

## Output

Write your edits as a single JSON object to the file at `{output_path}` (PROPOSED_EDITS.json). Only that file is read, not anything you print. The JSON must have exactly this shape:

{"edits": [{"op": "append" | "insert_after" | "replace" | "delete", "target": "<exact substring copied from the CURRENT skill body; empty for append>", "content": "<markdown to add; empty for delete>", "rationale": "<one sentence tied to evidence>", "evidence_refs": ["<trace/task ids>"]}]}

Your edits apply to the skill body; the YAML frontmatter, including the skill name, is not editable here. Choose each `target` knowing how edits are applied:
- `target` matches as an EXACT substring of the current body and the FIRST match wins, so copy it verbatim — same characters, spacing, and capitalization — and prefer a short, unique anchor such as a heading line or one distinctive sentence — never a line inside a code fence, or the inserted content lands inside that fence.
- `append` adds `content` at the end of the body and ignores `target`, so pass an empty string for it.
- `insert_after` places `content` immediately after `target`; if `target` is not found it falls back to appending at the end.
- `replace` swaps the matched `target` for `content`, and `delete` removes the matched `target` with empty `content`; if the `target` of a `replace` or `delete` is not found, that edit is SKIPPED.
- Write {"edits": []} to the file when the current skill already closes the gap.
