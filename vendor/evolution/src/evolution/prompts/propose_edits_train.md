# Propose Train-Optimized Skill Edits

Diagnose the failure from the evidence, then propose a set of concrete procedural edits to the current skill body that improves TRAIN performance for this task class. Change what the evidence implicates, but do not under-edit when multiple train failures expose distinct missing procedures.

## Task Context
{task_context}

{runtime_contract}

## Current Skill Body
{skill_body}

## Evidence
{evidence_policy}

{evidence}

{round_memory}
{rejected_attempts}
{apply_feedback}

## Editing Rules

{{include:_blocks/leak_rules}}

{{include:_blocks/generality_rules}}

{{include:_blocks/refinement_rules}}

## Your Task
- Propose up to {edit_budget} edits. While train performance still has headroom, use the budget for distinct train-failure root causes instead of returning a single tiny patch.
- Each content-adding edit should be a coherent procedure: a short heading, the failure condition it prevents, a copyable code idiom when useful, and a verification step the next solver should perform.
- Prefer `replace` when the skill already has a section for the topic; use `insert_after` or `append` only for genuinely missing procedures.
- Preserve everything the round memory above marks as working, and do not re-propose any edit the rejected-attempts section shows was already tried and rejected.
- If the feedback section reports that a target did not match, copy the anchor more carefully from the body above rather than resubmitting the same target.
- Keep the resulting body within {size_budget}; spend size on executable procedural guidance, not commentary.
- {edit_brake_policy}

## Output

Emit ONLY a JSON object — no prose, no code fence, nothing before or after it — in exactly this shape:

{"edits": [{"op": "append" | "insert_after" | "replace" | "delete", "target": "<exact substring copied from the CURRENT skill body; empty for append>", "content": "<markdown to add; empty for delete>", "rationale": "<one sentence tied to evidence>", "evidence_refs": ["<trace/task ids>"]}]}

Your edits apply to the skill body shown above; the YAML frontmatter, including the skill name, is not editable here. Choose each `target` knowing how edits are applied:
- `target` matches as an EXACT substring of the current body and the FIRST match wins, so copy it verbatim — same characters, spacing, and capitalization — and prefer a short, unique anchor such as a heading line or one distinctive sentence — never a line inside a code fence, or the inserted content lands inside that fence.
- `append` adds `content` at the end of the body and ignores `target`, so pass an empty string for it.
- `insert_after` places `content` immediately after `target`; if `target` is not found it falls back to appending at the end outside train repair mode.
- `replace` swaps the matched `target` for `content`, and `delete` removes the matched `target` with empty `content`; if the `target` of a `replace` or `delete` is not found, that edit is SKIPPED.
- Return {"edits": []} only when the evidence does not localize a concrete, fixable skill gap.
