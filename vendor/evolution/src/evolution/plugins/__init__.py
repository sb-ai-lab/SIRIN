"""Discovery seams the core reads without depending on what it finds.

The merge's dependency rule is one-directional and absolute: an agent framework
may import ``evolution``, and ``evolution`` may **never** import an agent
framework. That rule and the product goal -- one framework in which any agent can
be registered and optimized -- pull against each other, and this package is where
they are reconciled.

The reconciliation is that the core never names a framework. It names a *group*,
and the installed distribution names itself into that group through its own
packaging metadata. So the coupling lives in an installed metadata file, which is
data, rather than in a product module, which is code.

That is not a trick to slip past a test. It is what makes the core wheel able to
build, install and run with no agent framework present at all -- which
``tests/product/test_core_wheel_is_self_sufficient.py`` proves by installing it
into an empty environment.
"""

from __future__ import annotations

from evolution.plugins.agent_frameworks import (
    AGENT_FRAMEWORK_GROUP,
    AgentFramework,
    installed_agent_frameworks,
    load_agent_framework,
)

__all__ = [
    "AGENT_FRAMEWORK_GROUP",
    "AgentFramework",
    "installed_agent_frameworks",
    "load_agent_framework",
]
