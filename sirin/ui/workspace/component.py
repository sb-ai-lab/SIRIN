"""Streamlit Components v2 registration for the SIRIN workspace."""

from __future__ import annotations

from functools import lru_cache
from typing import Any, Mapping

from .contracts import WorkspacePayload


def _noop() -> None:
    """Register component state without adding Python-side callback behavior."""


@lru_cache(maxsize=1)
def _renderer() -> Any:
    import streamlit as st

    return st.components.v2.component(
        "sirin.sirin_workspace",
        js="index-*.js",
        css="style-*.css",
        isolate_styles=True,
    )


def _json_payload(payload: WorkspacePayload | Mapping[str, Any]) -> dict[str, Any]:
    if hasattr(payload, "model_dump"):
        return payload.model_dump(mode="json", by_alias=True, exclude_none=True)
    return dict(payload)


def render_workspace(
    payload: WorkspacePayload | Mapping[str, Any],
    *,
    key: str = "sirin.workspace.v2",
) -> Mapping[str, Any]:
    """Mount the unified workspace and return its persistent state/action trigger."""
    data = _json_payload(payload)
    state = _renderer()(
        key=key,
        data=data,
        default={
            "draft": None,
            "selectedRunId": None,
        },
        on_action_change=_noop,
        on_draft_change=_noop,
        on_viewState_change=_noop,
        on_appearance_change=_noop,
        on_selectedRunId_change=_noop,
    )
    if isinstance(state, Mapping):
        return state
    return {"action": getattr(state, "action", None)}
