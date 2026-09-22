## Task Instruction
{instruction}
{workspace_section}
## Skill Content
{skill_body}
{cross_round_section}{rejected_edits_section}
## Generated Code
```python
{code}
```
{siblings_section}
## Result
Passed: {passed}/{total}

## Agent Solve Diagnostics
exit_code: {solve_exit_code}
timeout: {solve_timeout}
diagnostic: {solve_diagnostic}

## Failure Evidence
{failure_evidence}

## Produced Artifact Metadata
{produced_artifacts}
{tests_section}
## Analysis Request
1. **Root cause**: What specifically went wrong in the generated code?
2. **Skill gap**: What is the skill missing or saying incorrectly that led to this failure?
3. **Fix**: What specific change to the skill would prevent this failure?

Respond as JSON:
```json
{{
  "root_cause": "...",
  "skill_gap": "...",
  "suggested_fix": "...",
  "severity": "critical|major|minor",
  "pattern": "wrong_library|wrong_api|missing_step|logic_error|other",
  "evidence_sufficiency": "sufficient|insufficient",
  "rewrite_recommended": true
}}
```
Set `evidence_sufficiency` to `insufficient` and `rewrite_recommended` to
false when the evidence does not localize a concrete procedural skill gap.