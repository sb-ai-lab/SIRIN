# Diagnose Failing Traces

You are given {n_traces} failing trace(s) drawn from the SAME task class, produced by a solver that followed the current skill. Diagnose the ONE recurring procedural gap behind them — a consensus root cause across the traces, not a separate patch per trace. A gap that repeats across traces and models is stronger signal than one that appears in a single idiosyncratic trace.

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
1. Root cause: what specifically went wrong in the generated code across these traces?
2. Skill gap: what is the current skill missing, or stating wrongly or ambiguously, that let this failure happen?
3. Fix: what general change to the skill would prevent this failure on unseen instances of the same class?

{{include:_blocks/leak_rules}}

{{include:_blocks/generality_rules}}

## Output

Respond with ONLY this JSON object, keys exactly as shown — no prose before or after it:

{"root_cause": "...", "skill_gap": "...", "suggested_fix": "...", "severity": "critical | major | minor", "pattern": "wrong_library | wrong_api | missing_step | logic_error | other", "evidence_sufficiency": "sufficient | insufficient", "rewrite_recommended": true}

Set `evidence_sufficiency` to `insufficient` and `rewrite_recommended` to `false` when the evidence does not localize a concrete, fixable procedural skill gap.
