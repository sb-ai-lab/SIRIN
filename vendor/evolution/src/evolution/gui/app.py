"""Evolution GUI — Streamlit app for managing LLM agent skills."""

from __future__ import annotations

from pathlib import Path

import streamlit as st

from evolution.gui.navigation import PAGES

st.set_page_config(
    page_title="Evolution — Skills Manager",
    page_icon="🧬",
    layout="wide",
    initial_sidebar_state="expanded",
)

PROJECT_DIR = Path.cwd()


def get_store():
    """Cached SkillStore instance."""
    from evolution.core.store import SkillStore

    return SkillStore(project_dir=PROJECT_DIR, user_dir=Path.home())


# ── Sidebar navigation ─────────────────────────────────────────────
st.sidebar.title("Evolution")
page = st.sidebar.radio(
    "Navigate",
    PAGES,
    label_visibility="collapsed",
)

# ── Page routing ────────────────────────────────────────────────────
if page == "Skills":
    from evolution.gui.views.skills import render

    render(get_store, PROJECT_DIR)
elif page == "Tasks":
    from evolution.gui.views.tasks import render as render_tasks

    render_tasks(get_store, PROJECT_DIR)
elif page == "Benchmarks":
    from evolution.gui.views.benchmarks import render as render_benchmarks

    render_benchmarks(get_store, PROJECT_DIR)
elif page == "Traces":
    from evolution.gui.views.traces import render as render_traces

    render_traces(get_store, PROJECT_DIR)
