"""The runtime, tool catalog and prompt contract, shaped for the agent seam.

Every method that has no meaning for a flat ``SKILL.md`` returns an explicit
empty value and says why in its docstring. That is deliberate: a plausible-
looking fake would make the adapter look like a better fit than it is, and the
count of empty methods is the measurement.
"""

from __future__ import annotations

from pathlib import Path
from typing import Any

from evolution import prompts
from evolution.agent_shim.evaluation import PytestEvaluationSuite

#: Methods that carry no information for the flat/pytest family. Named here so
#: the count is asserted by a test rather than recounted by hand in a report.
VACUOUS_METHODS = frozenset(
    {
        "ensure_initialized",
        "introspect_actions",
        "introspect_action_descriptions",
        "introspect_action_required_tools",
        "make_renderer",
        "layer_names",
        "rag_catalog_text",
        "non_targetable_skill_ids",
        "root_skill_ids",
        "sink_skill_ids",
    }
)

#: Methods that return real content for this family.
MEANINGFUL_METHODS = frozenset(
    {
        "system_prompt_template",
        "default_wrapper_prompts",
        "agent_description",
        "reference_skills_dir",
    }
)


class FlatToolCatalog:
    """A tool catalog for a family that has no tools.

    The agent family's runtimes expose a registered action list, and the writer
    prompts are built from it. A flat-skill solver is handed a workspace and
    writes code; there is no action to register, no description to introspect,
    and no per-action tool requirement. All four methods are therefore empty,
    and emptiness is the honest answer rather than a stub to fill in later.
    """

    def ensure_initialized(self) -> None:
        """No tool runtime to start."""

    def introspect_actions(self) -> list[tuple[str, str]]:
        """No registered actions: the solver emits code, not tool calls."""
        return []

    def introspect_action_descriptions(self) -> dict[str, str]:
        """No actions, so no descriptions."""
        return {}

    def introspect_action_required_tools(self) -> dict[str, str]:
        """No actions, so no per-action tool requirements."""
        return {}


class FlatSkillContract:
    """The prompt/render contract for a flat ``SKILL.md`` artefact.

    Four of the ten methods return real content. The other six describe a
    navigable skill graph — layers, roots, sinks, non-targetable nodes, a Jinja
    renderer and a retrieval catalog — and this family's artefact is one file.
    """

    def __init__(
        self, skills_dir: Path, *, agent_description: str = "Evolution flat skill"
    ) -> None:
        self._skills_dir = Path(skills_dir)
        self._agent_description = agent_description

    # --- meaningful ---------------------------------------------------------

    def system_prompt_template(self) -> str:
        """The reflection system prompt this family actually sends."""
        return prompts.load_prompt("system_reflect")

    def default_wrapper_prompts(self) -> dict[str, str]:
        """The agentic wrappers that surround a skill body in a solve."""
        return {
            "session": prompts.load_prompt("agentic_wrapper_session"),
            "hermes": prompts.load_prompt("agentic_wrapper_hermes"),
        }

    def agent_description(self) -> str:
        """What a writer is told it is editing."""
        return self._agent_description

    def reference_skills_dir(self) -> Path:
        """The skill store directory this runtime edits."""
        return self._skills_dir

    # --- vacuous ------------------------------------------------------------

    def make_renderer(self, skills_dir: Any) -> Any:
        """No renderer: a flat ``SKILL.md`` is injected as bytes, not templated.

        Returning ``None`` rather than an identity renderer keeps the absence
        visible; a caller that templates unconditionally fails loudly here.
        """
        return None

    def layer_names(self) -> dict[str, Any]:
        """No layers: one file cannot be a policy/router/leaf hierarchy."""
        return {}

    def rag_catalog_text(self) -> str:
        """No retrieval store, so there are no citable document ids."""
        return ""

    def non_targetable_skill_ids(self) -> frozenset[str]:
        """Targeting is trivial when there is exactly one skill to target."""
        return frozenset()

    def root_skill_ids(self) -> frozenset[str]:
        """No navigation graph, so no navigational-only skills.

        Empty here means "this family has no such layer", which is the same
        answer ``agent_oc`` gives, and it is distinct from "no case got stuck".
        """
        return frozenset()

    def sink_skill_ids(self) -> frozenset[str]:
        """No catch-all terminal exists to give up into."""
        return frozenset()


class FlatSkillRuntime:
    """Bundles the catalog, contract and evaluator for the flat/pytest family."""

    def __init__(
        self,
        skills_dir: Path,
        *,
        tasks_dir: Path | None = None,
        name: str = "evolution-flat",
    ) -> None:
        self.name = name
        self._tool_catalog = FlatToolCatalog()
        self._contract = FlatSkillContract(skills_dir)
        self._evaluator = PytestEvaluationSuite(tasks_dir=tasks_dir)

    @property
    def tool_catalog(self) -> FlatToolCatalog:
        return self._tool_catalog

    @property
    def contract(self) -> FlatSkillContract:
        return self._contract

    @property
    def evaluator(self) -> PytestEvaluationSuite:
        return self._evaluator

    def install(self) -> None:
        """Nothing process-wide to apply.

        The agent family installs runtime settings here. This family's
        equivalent state travels per call, and writing it into the process
        would violate the import-purity contract this repository now enforces.
        Idempotent by being empty.
        """
