You are editing a single file on disk: SKILL.md, in your current
working directory.  Use your file-edit tools to MODIFY THE FILE IN PLACE.
Do NOT print or return the file body in chat — the harness reads SKILL.md
from disk after you exit and ignores stdout entirely.

The candidate workspace is a tiny git repo at `baseline` state. You may
use `git diff -- SKILL.md` to self-review your edits.

You MUST make at least one substantive, targeted edit informed by the
consensus failure pattern below.  Stay scoped:

- Make the smallest sufficient edit that the consensus failure requires.
- Do NOT touch the YAML frontmatter (name, description, license, metadata).
- Do NOT embed test names, verifier code, expected literal answers, or
  task-specific identifiers (file paths, dataset names, hardcoded values).
  Keep the skill a GENERAL, transferable procedure.
- Prefer a small, surgical change over a sweeping rewrite. The shared edit brake checks finalized line churn before evaluation.

If after reading the reflections you genuinely conclude that the parent
SKILL.md already addresses the failure correctly, you may leave the file
unchanged.  But your default disposition should be: the failing traces
exposed a gap in the skill; find the smallest edit that closes that gap.
