"""An ``AgentRuntime``-shaped adapter for the flat ``SKILL.md`` / pytest family.

This package exists to answer one question from the agent-harness merge plan:
can `evolution`'s evaluator kind be expressed through the agent family's runtime
seam? It is a measurement instrument, not a product feature. Nothing in
`evolution` imports it, and it is not wired into the CLI.

**It must never import ``agent_harness`` (or its pre-rename name
``skill_evolution``).** The four Protocols on the other side are all
``@runtime_checkable``, which is presence-only, so a structurally typed class
satisfies ``isinstance`` with zero import. ``tests/product/test_agent_shim.py``
mirrors those Protocols and proves conformance without a dependency.

What the exercise measures, recorded here because it is the finding rather than
a defect to fix:

* **10 of the 14 introspection methods are vacuous for this family.** The tool
  catalog is empty in all four methods, because a flat-skill solver writes code
  rather than calling a registered action. Six of the ten contract methods
  describe a navigable skill *graph* — layers, roots, sinks, non-targetable
  nodes, a Jinja renderer, a retrieval catalog — and a flat artefact is a single
  file with no graph to describe.
* **The evaluation request is the real seam mismatch.** ``EvalRequest`` is frozen
  at six fields on purpose. ``evolution.workflow.solve`` takes twenty-one, of
  which eight carry meaning no agent-family field can hold: the skill name and
  its snapshot, the split manifest and its scope, the child environment
  allowlist, the solve timeout, the attempt seed, and the project directory.
  They can only travel as opaque payload on ``cfg``, which is what
  ``evaluation.py`` does and documents.

Both are evidence *for* keeping the two evaluator kinds behind a registry rather
than unifying them.
"""

from evolution.agent_shim.corpus import FlatTaskCorpus
from evolution.agent_shim.evaluation import PytestEvaluationSuite, SolveOverrides
from evolution.agent_shim.runtime import FlatSkillContract, FlatSkillRuntime, FlatToolCatalog
from evolution.agent_shim.scoring import CaseOutcome, score_cases

__all__ = [
    "CaseOutcome",
    "FlatSkillContract",
    "FlatSkillRuntime",
    "FlatTaskCorpus",
    "FlatToolCatalog",
    "PytestEvaluationSuite",
    "SolveOverrides",
    "score_cases",
]
