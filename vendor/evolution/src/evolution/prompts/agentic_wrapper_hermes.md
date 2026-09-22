# Skill Editing — Tool Session (trace evidence on disk)

You are refining one reusable skill so a separate solver succeeds more often on this task class. You work in a workspace where the trace evidence and current skill body are on disk.

## Tool Protocol
- Task Context names the exact skill file and trace-evidence directory. Read those supplied paths. The evidence directory contains `index.json` and per-trace files.
- Explore only your workspace. Do not read the dataset, the held-out verifier, other skills, or anything outside the workspace.
- There are {n_traces} trace(s) this round. Use the supplied `index.json`, group traces by failure category, and diagnose the top recurring root cause before you write anything.

## Task Context
{task_context}

{runtime_contract}

## Current Skill Body (reference; the file on disk is the source of truth)
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

## Your Task
Diagnose the recurring gap across the traces, then decide AT MOST {edit_budget} surgical edits that fix the root cause while keeping the body within {size_budget}. Preserve what the round memory marks as working, and do not repeat a rejected attempt.

## Output

Write your edits as a single JSON object to the file at `{output_path}` (PROPOSED_EDITS.json). Nothing you print in chat is read — only that file is. The JSON must have exactly this shape:

{"edits": [{"op": "append" | "insert_after" | "replace" | "delete", "target": "<exact substring copied from the CURRENT skill body; empty for append>", "content": "<markdown to add; empty for delete>", "rationale": "<one sentence tied to evidence>", "evidence_refs": ["<trace/task ids>"]}]}

Your edits apply to the skill body; the YAML frontmatter, including the skill name, is not editable here. Choose each `target` knowing how edits are applied:
- `target` matches as an EXACT substring of the current body and the FIRST match wins, so copy it verbatim — same characters, spacing, and capitalization — and prefer a short, unique anchor such as a heading line or one distinctive sentence — never a line inside a code fence, or the inserted content lands inside that fence.
- `append` adds `content` at the end of the body and ignores `target`, so pass an empty string for it.
- `insert_after` places `content` immediately after `target`; if `target` is not found it falls back to appending at the end.
- `replace` swaps the matched `target` for `content`, and `delete` removes the matched `target` with empty `content`; if the `target` of a `replace` or `delete` is not found, that edit is SKIPPED.
- Write {"edits": []} to the file only when the evidence does not localize a concrete, fixable skill gap.
