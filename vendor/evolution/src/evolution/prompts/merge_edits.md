# Merge Edit Proposals

Several independent editors each proposed edits for the same skill. Consolidate them into one ranked, non-redundant edit list.

## Task Context
{task_context}

{runtime_contract}

## Current Skill Body
{skill_body}

## Evidence Mode
{evidence_policy}

## Proposal Sets
{proposals}

## Your Task
- Deduplicate edits that make the same change, and resolve conflicts between edits that touch overlapping `target` text by keeping the clearer, more general one.
- Rank edits that FIX a failure ahead of edits that merely polish, and drop any proposal that violates the active evidence mode or split boundary.
- Return AT MOST {edit_budget} edits — the highest-value ones under that cap.
- {edit_brake_policy}

{{include:_blocks/leak_rules}}

## Output

Emit ONLY a JSON object — no prose, no code fence, nothing before or after it — in exactly this shape:

{"edits": [{"op": "append" | "insert_after" | "replace" | "delete", "target": "<exact substring copied from the CURRENT skill body; empty for append>", "content": "<markdown to add; empty for delete>", "rationale": "<one sentence tied to evidence>", "evidence_refs": ["<trace/task ids>"]}]}

Carry each edit you keep through unchanged — preserve its `op`, `target`, `content`, and `evidence_refs` exactly (you may only tighten a `rationale`), because `target` must still match as a verbatim substring of the skill body when the edit is applied. List failure-fixing edits before polish, and return {"edits": []} only if no proposed edit is worth keeping.
