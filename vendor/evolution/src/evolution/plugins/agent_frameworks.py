"""The registry of agent frameworks installed beside the core.

An agent framework is a second distribution that knows how to drive some agent.
It declares itself in its own ``pyproject.toml``::

    [project.entry-points."evolution.agent_frameworks"]
    <name> = "<its.module>:<its_attribute>"

and the core finds it here. No name above is a literal in this package: the only
literal the core holds is the group name. That is what lets the core wheel
install and run with no framework present, and it is checked from the outside by
``tests/product/test_import_fence.py``. The example is deliberately abstract --
writing a real framework's package here would be the very coupling the group
exists to avoid.

**Discovery imports nothing.** :func:`installed_agent_frameworks` reads metadata
only, so listing what is available costs no import and can never pull a heavy
dependency into a process that just wanted to print a table.
:func:`load_agent_framework` is the one function that imports, and it is
explicit about it -- a caller that loads a framework has asked for it by name.
"""

from __future__ import annotations

from dataclasses import dataclass
from importlib.metadata import entry_points
from typing import Any

#: The group an agent framework declares itself into. The core's only literal.
AGENT_FRAMEWORK_GROUP = "evolution.agent_frameworks"


@dataclass(frozen=True)
class AgentFramework:
    """One installed framework, described without loading it.

    ``target`` is the entry point's ``module:attribute`` string, kept as data so
    that ``evo`` can show an operator what *would* be imported before anything
    is. It is deliberately not resolved here.
    """

    name: str
    target: str

    @property
    def module(self) -> str:
        """The module the entry point would import."""
        return self.target.split(":", 1)[0]


def installed_agent_frameworks() -> list[AgentFramework]:
    """Every framework installed beside the core, by metadata alone.

    Sorted by name so a listing is stable between runs and between machines,
    which matters because this output ends up in run receipts.
    """
    found = [
        AgentFramework(name=entry.name, target=entry.value)
        for entry in entry_points(group=AGENT_FRAMEWORK_GROUP)
    ]
    return sorted(found, key=lambda framework: framework.name)


def load_agent_framework(name: str) -> Any:
    """Import and return one framework's registration object.

    This is the only place the core causes an agent framework to be imported,
    and it happens because a caller named one. The name comes from the operator
    or from a manifest; it is never a literal in this package.
    """
    for entry in entry_points(group=AGENT_FRAMEWORK_GROUP):
        if entry.name == name:
            return entry.load()
    available = [framework.name for framework in installed_agent_frameworks()]
    raise LookupError(
        f"no agent framework named {name!r} is installed. "
        f"Installed: {available or 'none'}. A framework declares itself with an "
        f"entry point in the {AGENT_FRAMEWORK_GROUP!r} group."
    )
