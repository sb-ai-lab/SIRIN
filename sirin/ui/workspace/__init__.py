"""Typed backend boundary for the SIRIN Streamlit workspace."""

from __future__ import annotations

from importlib import import_module
from typing import Any


_EXPORTS = {
    'ActionEnvelope': 'contracts',
    'ActionReceipt': 'contracts',
    'Activity': 'contracts',
    'AnalysisResult': 'contracts',
    'CapabilitySet': 'contracts',
    'DiagnosticsSummary': 'contracts',
    'DownloadTransfer': 'contracts',
    'ExampleSummary': 'contracts',
    'Provenance': 'contracts',
    'RunInputs': 'contracts',
    'RunRecord': 'contracts',
    'RunRequest': 'contracts',
    'RunStatus': 'contracts',
    'RunSummary': 'contracts',
    'SetupSnapshot': 'contracts',
    'WorkspaceEvent': 'contracts',
    'WorkspacePayload': 'contracts',
    'WorkspaceController': 'controller',
    'ExampleRegistry': 'examples',
    'present_analysis': 'presenter',
    'RunEngine': 'run_engine',
    'PortableFormatError': 'session',
    'WorkspaceSession': 'session',
    'export_bundle': 'session',
    'export_run': 'session',
    'import_portable_json': 'session',
}

__all__ = list(_EXPORTS)


def __getattr__(name: str) -> Any:
    module_name = _EXPORTS.get(name)
    if module_name is None:
        raise AttributeError(f'module {__name__!r} has no attribute {name!r}')
    value = getattr(import_module(f'.{module_name}', __name__), name)
    globals()[name] = value
    return value
