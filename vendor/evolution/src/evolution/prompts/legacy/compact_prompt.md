## Baseline Skill Body
{baseline_body}

## Oversized Draft Rewrite
{draft_body}

## Failure Fixes That Must Remain Covered
{reflection_summary}

## Size Limits
- Maximum characters: {max_chars}
- Maximum non-empty lines: {max_lines}

## Compacting Rules
- Preserve the baseline's core successful procedure unless a reflection explicitly contradicts it
- Fold repeated warnings into one short checklist
- Remove redundant examples and keep only the most general working code pattern
- Remove speculative, task-specific, or contradictory advice
- Strip any embedded test/verifier/assertion text, hardcoded dataset/table/column
  names, private file paths, literal expected answers, or one-off constants
- Keep enough exact library/API details for an LLM to execute the procedure
- Output ONLY the compacted markdown body