# Diagnose Passing Traces

You are given {n_traces} passing trace(s) drawn from the SAME task class, produced by a solver that followed the current skill. Identify what in the skill made these solves succeed and MUST be preserved — the working procedure to protect from future edits, not a fix to apply.

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

## Analysis Request
1. Reinforcement pattern: what concrete behaviour in the skill enabled these passes?
2. Helpful sections: which top-level skill sections (verbatim headings) carried the load?
3. Transferability: will this approach generalize to sibling tasks of the same class?

{{include:_blocks/generality_rules}}

## Output

Respond with ONLY this JSON object, keys exactly as shown — no prose before or after it:

{"reinforcement_pattern": "import_strategy | step_sequencing | edge_case_handling | api_choice | other", "helpful_sections": ["## Heading A", "## Heading B"], "transferability": "task_specific | partial | broad", "evidence_sufficiency": "sufficient | insufficient", "preserve_recommended": true}

Set `evidence_sufficiency` to `insufficient` and `preserve_recommended` to `false` when the trace does not localize concrete skill text worth preserving.
