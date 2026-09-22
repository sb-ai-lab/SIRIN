The file you are editing is `SKILL.md` in your current working directory.
Its current contents are reproduced below for your reference; the source
of truth is the file on disk.

## Current SKILL.md body (parent)
{skill_body}

## Existing workflows
The parent SKILL.md has these top-level sections. Preserve working guidance unless the reflections directly contradict it:

{preserve_headings}

## Training context
- Task: {task_instruction}
- Source model(s): {source_models}
- Failing traces analyzed: {n_traces}
{scripts_section}
## Consensus failure
{consensus_summary}

## All actionable reflections ({n_reflections})
{all_reflections}

## Failure pattern summary
{pattern_summary}
{success_preserve_section}
## Size envelope (HARD)
Keep the body within {max_chars} characters and {max_lines} non-empty lines. The shared edit brake separately checks finalized normalized line churn.

## Your task
Apply the smallest sufficient edit that addresses the consensus failure above. Use your file-edit tools to modify SKILL.md. Do not output the body in chat.
