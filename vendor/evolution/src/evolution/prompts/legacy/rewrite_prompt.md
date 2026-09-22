## Current Skill
{skill_body}

## Task This Skill Must Solve
{task_instruction}
{scripts_section}
## Failure Reflections (from {n_reflections} failing traces)
{reflections}

## Failure Pattern Summary
{pattern_summary}
{success_preserve_section}{best_trace_section}
## Size Budget (HARD)
- Maximum characters: {max_chars}
- Maximum non-empty lines: {max_lines}
Stay within this budget. Be concise: revise, do not accrete.

## Rewrite Instructions
Rewrite the skill body. Key rules:
- Keep the skill a GENERAL, transferable procedure for this TYPE of task. The
  instruction above is ONE example; the skill must work on unseen instances.
- Fix ROOT CAUSES by correcting libraries/APIs, steps, and general guardrails.
- Show exact imports and API calls as GENERAL patterns parameterized over inputs.
- DO NOT embed or paraphrase the task's tests/verifier/assertions, the expected
  answer, specific dataset/table/column names, or input file paths.
- You MAY include short general pitfalls from the reflections.
- Make the smallest sufficient edit. The shared edit brake rejects changes above its effective churn budget.
- Output ONLY the markdown body (no YAML frontmatter, no code fences around the whole output)
