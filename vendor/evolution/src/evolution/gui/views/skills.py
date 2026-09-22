"""Skills page — browse, inspect, diff, and manage skills."""

from __future__ import annotations

import json
from pathlib import Path

import streamlit as st

from evolution.lineage.state_io import skill_mutation_lock


def render(get_store, project_dir: Path) -> None:
    store = get_store()
    entries = store.list()

    if not entries:
        st.title("Skills")
        st.warning("No skills found.")
        return

    # ── Sidebar: skill selector ─────────────────────────────────────
    skill_names = [e.name for e in entries]
    selected = st.sidebar.selectbox("Skill", skill_names, key="skill_select")

    skill = store.get(selected)

    # ── Header row ──────────────────────────────────────────────────
    st.title(f"{skill.name}")
    st.caption(skill.description)

    # Metrics row
    from evolution.lineage.traces import TraceStore
    from evolution.lineage.tracker import LineageTracker
    from evolution.lineage.version import VersionStore

    tracker = LineageTracker(skill)
    ts = TraceStore(skill)
    vs = VersionStore(skill)

    versions = vs.list_versions()
    current_ver = tracker.current_version or "—"
    trace_count = ts.count()
    current_fitness = ts.fitness(current_ver) if current_ver != "—" else None

    cols = st.columns(4)
    cols[0].metric("Current Version", current_ver)
    cols[1].metric("Total Versions", len(versions))
    cols[2].metric("Traces", trace_count)
    cols[3].metric(
        "Fitness",
        f"{current_fitness:.0%}" if current_fitness is not None else "—",
    )

    audit_path = skill.path / ".evolution" / "last_rewrite_audit.json"
    if audit_path.is_file():
        try:
            audit = json.loads(audit_path.read_text(encoding="utf-8"))
            brake = audit.get("edit_brake") or {}
            if brake:
                attempts = audit.get("rewrite_attempts") or []
                with st.expander("Last edit-brake evidence", expanded=False):
                    st.dataframe(
                        [
                            {
                                "Version decay": brake.get("version_decay_enabled", "—"),
                                "Parent version": brake.get("parent_version", "—"),
                                "Promotion count": brake.get("promotion_count", "—"),
                                "Base budget": brake.get("base_budget_frac", "—"),
                                "Effective budget": brake.get("effective_budget_frac", "—"),
                                "Observed churn": brake.get("normalized_churn", "—"),
                                "Attempts": len(attempts),
                                "Decision": brake.get("decision", "—"),
                                "Candidate hash": brake.get("candidate_sha256", "—"),
                                "Evidence": str(audit_path),
                            }
                        ],
                        width="stretch",
                        hide_index=True,
                    )
        except (OSError, ValueError):
            st.caption("Edit brake evidence is unavailable.")

    # ── Tabs ────────────────────────────────────────────────────────
    tab_content, tab_lineage, tab_diff, tab_traces, tab_actions = st.tabs(
        ["Content", "Lineage", "Diff", "Traces", "Actions"]
    )

    with tab_content:
        _render_content(skill, vs, versions, current_ver)

    with tab_lineage:
        _render_lineage(tracker, ts, skill.name)

    with tab_diff:
        _render_diff(skill, vs, tracker, versions)

    with tab_traces:
        _render_traces(ts, skill.name)

    with tab_actions:
        _render_actions(skill, tracker, vs, versions)


# ── Content tab ─────────────────────────────────────────────────────


def _render_content(skill, vs, versions, current_ver):
    """Show SKILL.md content with version selector."""
    view_ver = st.selectbox(
        "View version",
        ["working copy"] + versions,
        index=0,
        key="content_version",
    )

    if view_ver == "working copy":
        body = skill.body
        fm = skill.frontmatter
    else:
        try:
            ver_skill = vs.load(view_ver)
            body = ver_skill.body
            fm = ver_skill.frontmatter
        except KeyError:
            st.error(f"Version {view_ver} not found")
            return

    # Frontmatter summary
    with st.expander("Frontmatter", expanded=False):
        fm_dict = fm.model_dump(exclude_none=True)
        st.json(fm_dict)

    # Rendered markdown body
    st.markdown(body)


# ── Lineage tab ─────────────────────────────────────────────────────


def _render_lineage(tracker, ts, skill_name):
    """Show version history table and fitness chart."""
    entries = tracker.lineage

    if not entries:
        st.info("No lineage recorded.")
        return

    import pandas as pd

    rows = []
    for entry in entries:
        vtraces = ts.list(skill_version=entry.version)
        trace_fitness = ts.fitness(entry.version)
        trace_count = len(vtraces)
        fitness = trace_fitness if trace_fitness is not None else entry.fitness
        # Per-version cost: average LLM tokens + generation time across this
        # version's traces. Each SkillTrace records tokens_in/out + time_ms.
        if vtraces:
            avg_tokens = sum(
                (t.get("tokens_in", 0) + t.get("tokens_out", 0)) for t in vtraces
            ) / len(vtraces)
            avg_time_ms = sum(t.get("time_ms", 0) for t in vtraces) / len(vtraces)
        else:
            avg_tokens = None
            avg_time_ms = None
        rows.append(
            {
                "Version": entry.version,
                "Fitness": fitness,
                "Traces": trace_count,
                "Avg tokens": round(avg_tokens) if avg_tokens is not None else None,
                "Avg LLM ms": round(avg_time_ms) if avg_time_ms is not None else None,
                "Origin": entry.origin,
                "Status": entry.status,
                "Date": entry.timestamp.strftime("%Y-%m-%d %H:%M") if entry.timestamp else "—",
            }
        )

    df = pd.DataFrame(rows)

    # Highlight active row
    def highlight_active(row):
        if row["Status"] == "active":
            return ["background-color: #1a3a1a"] * len(row)
        return [""] * len(row)

    st.dataframe(
        df.style.apply(highlight_active, axis=1),
        width="stretch",
        hide_index=True,
    )

    # Performance-vs-cost trajectory across versions: pass-rate on the left
    # axis, average LLM tokens/solve on the right axis. Lets you see whether
    # an evolution round bought accuracy at the price of more tokens.
    chart_df = df[df["Fitness"].notna()].copy()
    if not chart_df.empty:
        import plotly.graph_objects as go

        fig = go.Figure()
        fig.add_trace(
            go.Scatter(
                x=chart_df["Version"],
                y=chart_df["Fitness"],
                name="Pass rate",
                mode="lines+markers",
                line=dict(color="#2ca02c"),
            )
        )
        cost_df = chart_df[chart_df["Avg tokens"].notna()]
        if not cost_df.empty:
            fig.add_trace(
                go.Bar(
                    x=cost_df["Version"],
                    y=cost_df["Avg tokens"],
                    name="Avg tokens / solve",
                    yaxis="y2",
                    marker=dict(color="#1f77b4"),
                    opacity=0.35,
                )
            )
        fig.update_layout(
            title="Performance vs cost by version",
            yaxis=dict(title="Pass rate", tickformat=".0%", range=[0, 1.05]),
            yaxis2=dict(
                title="Avg tokens / solve",
                overlaying="y",
                side="right",
                showgrid=False,
                rangemode="tozero",
            ),
            height=340,
            legend=dict(orientation="h", yanchor="bottom", y=1.02),
            margin=dict(t=60),
        )
        st.plotly_chart(fig, width="stretch")


# ── Diff tab ────────────────────────────────────────────────────────


def _render_diff(skill, vs, tracker, versions):
    """Side-by-side diff between two versions."""
    from evolution.lineage.diff import skill_diff

    if len(versions) < 1:
        st.info("Need at least one committed version to diff.")
        return

    options = ["working copy"] + versions

    def _step_diff_versions(opts, delta):
        """Move both From/To selections by ``delta`` positions in ``opts``,
        clamped independently so a list already at an end stays put."""
        for key in ("diff_left", "diff_right"):
            current = st.session_state.get(key, opts[0])
            idx = opts.index(current) if current in opts else 0
            st.session_state[key] = opts[max(0, min(len(opts) - 1, idx + delta))]

    # Inline "▲ / ▼" stepper between the dropdowns. Five TOP-LEVEL columns
    # (not nested) so the arrows stay on one row instead of collapsing.
    st.markdown(
        "<style>"
        "div.st-key-diff_step_up,div.st-key-diff_step_down{display:flex;justify-content:center;}"
        "div.st-key-diff_step_up button,div.st-key-diff_step_down button"
        "{min-width:2.6rem;padding-left:0;padding-right:0;}"
        "</style>",
        unsafe_allow_html=True,
    )
    spacer = "<div style='height:1.7rem'></div>"  # aligns arrows with the boxes
    c_from, c_up, c_sep, c_dn, c_to = st.columns([6, 1, 0.5, 1, 6])
    with c_from:
        left = st.selectbox("From", options, index=min(1, len(options) - 1), key="diff_left")
    with c_up:
        st.markdown(spacer, unsafe_allow_html=True)
        st.button(
            "▲",
            key="diff_step_up",
            on_click=_step_diff_versions,
            args=(options, 1),
            help="Step both From and To to the next version (+1, stops at the last).",
        )
    with c_sep:
        st.markdown(
            spacer + "<div style='text-align:center;padding-top:0.35rem'>/</div>",
            unsafe_allow_html=True,
        )
    with c_dn:
        st.markdown(spacer, unsafe_allow_html=True)
        st.button(
            "▼",
            key="diff_step_down",
            on_click=_step_diff_versions,
            args=(options, -1),
            help="Step both From and To to the previous version (−1, stops at the first).",
        )
    with c_to:
        right = st.selectbox("To", options, index=0, key="diff_right")

    if left == right:
        st.info("Select two different versions to compare.")
        return

    def _load(label):
        if label == "working copy":
            return skill
        return vs.load(label)

    try:
        old_skill = _load(left)
        new_skill = _load(right)
    except KeyError as e:
        st.error(str(e))
        return

    d = skill_diff(old_skill, new_skill)

    if not d.text_diff and not d.frontmatter_changes:
        st.success("No changes.")
        return

    st.markdown(f"**Summary:** {d.summary}")

    if d.frontmatter_changes:
        with st.expander("Frontmatter changes", expanded=True):
            for key, (old_val, new_val) in d.frontmatter_changes.items():
                st.markdown(f"- **{key}**: `{old_val}` → `{new_val}`")

    if d.text_diff:
        st.code(d.text_diff, language="diff")


# ── Traces tab ──────────────────────────────────────────────────────


def _render_traces(ts, skill_name):
    """Show traces for this skill with filters."""
    traces = ts.list()

    if not traces:
        st.info("No traces recorded.")
        return

    # Filters
    col1, col2, col3 = st.columns(3)
    all_versions = sorted(set(t.get("skill_version", "") for t in traces))
    all_models = sorted(set(t.get("model", "") for t in traces))
    all_tasks = sorted(set(t.get("task", "") for t in traces))

    with col1:
        ver_filter = st.selectbox("Version", ["All"] + all_versions, key="trace_ver")
    with col2:
        model_filter = st.selectbox("Model", ["All"] + all_models, key="trace_model")
    with col3:
        task_filter = st.selectbox("Task", ["All"] + all_tasks, key="trace_task")

    filtered = ts.list(
        skill_version=ver_filter if ver_filter != "All" else None,
        model=model_filter if model_filter != "All" else None,
        task=task_filter if task_filter != "All" else None,
    )

    if not filtered:
        st.warning("No traces match the selected filters.")
        return

    import pandas as pd

    rows = []
    for i, t in enumerate(filtered, 1):
        passed = t.get("passed", 0)
        total = t.get("total", 0)
        rows.append(
            {
                "#": i,
                "Version": t.get("skill_version", ""),
                "Model": _short_model(t.get("model", "")),
                "Task": t.get("task", ""),
                "Result": f"{passed}/{total}",
                "Pass Rate": t.get("pass_rate", 0),
                "Tokens": f"{t.get('tokens_in', 0)}+{t.get('tokens_out', 0)}",
                "Time (ms)": t.get("time_ms", 0),
            }
        )

    df = pd.DataFrame(rows)

    def color_result(val):
        if "/" in str(val):
            parts = str(val).split("/")
            if parts[0] == parts[1] and parts[1] != "0":
                return "color: #4caf50"
            elif parts[0] == "0":
                return "color: #f44336"
        return ""

    st.dataframe(
        df.style.map(color_result, subset=["Result"]),
        width="stretch",
        hide_index=True,
    )

    # Trace detail viewer
    if filtered:
        trace_idx = st.selectbox(
            "View trace details",
            range(1, len(filtered) + 1),
            format_func=lambda i: (
                f"#{i} — {_short_model(filtered[i - 1].get('model', ''))} / {filtered[i - 1].get('task', '')}"
            ),
            key="trace_detail",
        )

        trace = filtered[trace_idx - 1]
        trace_dir = ts.resolve_trace_dir(trace["id"])

        if trace_dir.is_dir():
            sub_tabs = st.tabs(["Response", "Code", "Prompt", "Result"])

            with sub_tabs[0]:
                _show_trace_file(ts.resolve_trace_file(trace["id"], "response.md"), "markdown")
            with sub_tabs[1]:
                _show_trace_file(ts.resolve_trace_file(trace["id"], "solve.py"), "python")
            with sub_tabs[2]:
                _show_trace_file(ts.resolve_trace_file(trace["id"], "prompt.md"), "markdown")
            with sub_tabs[3]:
                _show_trace_file(ts.resolve_trace_file(trace["id"], "result.json"), "json")


# ── Actions tab ─────────────────────────────────────────────────────


def _render_actions(skill, tracker, vs, versions):
    """Promote, commit, discard actions."""
    st.subheader("Promote")
    if versions:
        promote_ver = st.selectbox("Switch to version", versions, key="promote_ver")
        if st.button("Promote", key="promote_btn"):
            with skill_mutation_lock(skill.path):
                tracker.promote(promote_ver)
            st.success(f"Promoted to {promote_ver}")
            st.rerun()
    else:
        st.info("No versions to promote.")

    st.divider()

    st.subheader("Commit")
    st.caption("Snapshot current working copy as a new version.")
    commit_msg = st.text_input("Commit message", key="commit_msg")
    if st.button("Commit", key="commit_btn", disabled=not commit_msg):
        from datetime import datetime

        from evolution.core.models import LineageEntry
        from evolution.core.validator import validate_skill

        with skill_mutation_lock(skill.path):
            vr = validate_skill(skill.path)
            if not vr.valid:
                st.error("Validation failed: " + "; ".join(vr.errors))
            else:
                active_ver = tracker.current_version
                new_ver = tracker.next_version_label()
                vs.save(new_ver)
                entry = LineageEntry(
                    version=new_ver,
                    parent=active_ver or None,
                    timestamp=datetime.now(),
                    origin="manual",
                    mutation_type="manual-edit",
                    status="candidate",
                )
                tracker.record(entry)
                tracker.promote(new_ver)
                st.success(f"Committed as {new_ver}: {commit_msg}")
                st.rerun()

    st.divider()

    st.subheader("Discard Changes")
    st.caption("Revert working copy to the current active version.")
    if st.button("Discard", key="discard_btn", type="secondary"):
        from evolution.lineage.diff import skill_diff

        with skill_mutation_lock(skill.path):
            active_ver = tracker.current_version
            if active_ver and vs.exists(active_ver):
                old = vs.load(active_ver)
                d = skill_diff(old, skill)
                if not d.text_diff and not d.frontmatter_changes:
                    st.info("No uncommitted changes.")
                else:
                    tracker.promote(active_ver)
                    st.success(f"Restored to {active_ver}")
                    st.rerun()
            else:
                st.warning("No committed version to restore.")


# ── Helpers ─────────────────────────────────────────────────────────


def _short_model(model: str) -> str:
    """Extract last segment of a model path."""
    return model.rsplit("/", 1)[-1] if "/" in model else model


def _show_trace_file(path: Path, language: str) -> None:
    """Display a trace file with appropriate formatting."""
    if not path.exists():
        st.info(f"{path.name} not found.")
        return

    content = path.read_text(encoding="utf-8")

    if language == "json":
        import json

        try:
            st.json(json.loads(content))
        except json.JSONDecodeError:
            st.code(content, language="json")
    elif language == "python":
        st.code(content, language="python")
    else:
        # For markdown (prompt/response) — show raw in an expander, rendered below
        if len(content) > 5000:
            st.markdown(content[:5000] + "\n\n*... truncated ...*")
            with st.expander("Full content"):
                st.code(content, language="markdown")
        else:
            st.markdown(content)
