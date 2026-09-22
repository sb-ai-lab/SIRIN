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

## Execution Evidence
{failure_evidence}

## Produced Artifact Metadata
{produced_artifacts}
{tests_section}
## Analysis Request
1. **Reinforcement pattern**: What concrete behaviour in the skill enabled this pass?
2. **Helpful sections**: Which top-level skill sections (verbatim headings) carried the load?
3. **Transferability**: Will this approach generalise to sibling tasks of the same class?

Respond as JSON:
```json
{{
  "reinforcement_pattern": "import_strategy|step_sequencing|edge_case_handling|api_choice|other",
  "helpful_sections": ["## Heading A", "## Heading B"],
  "transferability": "task_specific|partial|broad",
  "evidence_sufficiency": "sufficient|insufficient",
  "preserve_recommended": true
}}
```
Set `evidence_sufficiency` to `insufficient` and `preserve_recommended` to
false when the trace does not localise concrete skill text worth preserving.