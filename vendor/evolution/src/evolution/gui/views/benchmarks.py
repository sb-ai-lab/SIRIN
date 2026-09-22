"""Benchmarks page — results heatmap, skill impact, run history, launch."""

from __future__ import annotations

import re
from pathlib import Path

import pandas as pd
import streamlit as st

# The 3 standard model tiers
_PRIMARY_MODELS = ["claude-sonnet-4", "qwen3.5-27b", "llama-3.1-8b-instruct"]

# The 6 original tasks used for skill evolution
_PRIMARY_TASKS = [
    "powerlifting-coef-calc",
    "offer-letter-generator",
    "court-form-filling",
    "econ-detrending-correlation",
    "xlsx-recover-data",
    "pptx-reference-formatting",
]


def _default_models(all_models: list[str]) -> list[str]:
    """Return primary models that exist in the data, or all if none match."""
    defaults = [m for m in _PRIMARY_MODELS if m in all_models]
    return defaults if defaults else all_models


def _default_tasks(all_tasks: list[str]) -> list[str]:
    """Return primary tasks that exist in the data, or all if none match."""
    defaults = [t for t in _PRIMARY_TASKS if t in all_tasks]
    return defaults if defaults else all_tasks


_SKILLSBENCH_TASKS = {
    "powerlifting-coef-calc",
    "offer-letter-generator",
    "court-form-filling",
    "econ-detrending-correlation",
    "xlsx-recover-data",
    "pptx-reference-formatting",
    "sales-pivot-analysis",
    "weighted-gdp-calc",
    "pdf-excel-diff",
    "exceltable-in-ppt",
    "lab-unit-harmonization",
    "paper-anonymizer",
}


def _task_source(task_name: str) -> str:
    """Derive source label from task name."""
    if task_name.startswith("sb-"):
        return "SB-Bench"
    if task_name in _SKILLSBENCH_TASKS:
        return "SkillsBench"
    return "Other"


def render(get_store, project_dir: Path) -> None:
    st.title("Benchmarks")

    results_dir = project_dir / "results"
    df = _load_all_csvs(results_dir)

    if df.empty:
        st.warning("No benchmark results found in `results/`.")
        _render_launch(project_dir)
        return

    # ── Source filter ───────────────────────────────────────────────
    df["_source"] = df["task"].map(_task_source)
    all_sources = sorted(df["_source"].unique())
    source_options = ["All"] + all_sources
    sel_source = st.selectbox("Task source", source_options, key="bench_source_filter")
    if sel_source != "All":
        df = df[df["_source"] == sel_source]

    tab_heatmap, tab_impact, tab_collections, tab_history, tab_launch = st.tabs(
        ["Results Heatmap", "Skill Impact", "Collections", "Run History", "Launch"]
    )

    with tab_heatmap:
        _render_heatmap(df)

    with tab_impact:
        _render_impact(df)

    with tab_collections:
        _render_collections(df)

    with tab_history:
        _render_history(df)

    with tab_launch:
        _render_launch(project_dir)


# ── Load CSVs ───────────────────────────────────────────────────────


def _load_all_csvs(results_dir: Path) -> pd.DataFrame:
    """Load and merge all results.csv files across model directories."""
    if not results_dir.exists():
        return pd.DataFrame()

    frames = []
    for csv_path in sorted(results_dir.rglob("results.csv")):
        # Only pick up results/<model_tag>/results.csv (depth=1)
        # Skip nested CSVs (task input data) and old timestamped dirs
        rel = csv_path.relative_to(results_dir)
        if len(rel.parts) != 2:
            continue  # skip deeper nested CSVs
        model_tag = str(rel.parts[0])
        # Skip old dirs with timestamps in name (e.g. claude-sonnet-4_20260317_234255)
        if re.search(r"_\d{8}_\d{6}$", model_tag):
            continue

        try:
            df = pd.read_csv(csv_path)
        except Exception:
            continue

        if df.empty:
            continue

        df["model_tag"] = model_tag

        # Normalize columns — some old CSVs lack timestamp/skill_version/collection
        if "timestamp" not in df.columns:
            df["timestamp"] = ""
        if "skill_version" not in df.columns:
            df["skill_version"] = ""
        if "collection" not in df.columns:
            df["collection"] = ""

        # Ensure numeric types
        for col in ["passed", "total", "pass_rate", "tokens_in", "tokens_out", "time_ms"]:
            if col in df.columns:
                df[col] = pd.to_numeric(df[col], errors="coerce").fillna(0)

        df["success"] = df["success"].astype(str).str.lower().isin(["true", "1"])

        frames.append(df)

    if not frames:
        return pd.DataFrame()

    return pd.concat(frames, ignore_index=True)


# ── Results Heatmap ─────────────────────────────────────────────────


def _render_heatmap(df: pd.DataFrame, key_prefix: str = "hm", default_all: bool = False) -> None:
    """Interactive heatmap: tasks × models, colored by pass rate."""

    models = sorted(df["model_tag"].unique())
    tasks = sorted(df["task"].unique())
    conditions = sorted(df["condition"].unique())

    default_models = models if default_all else _default_models(models)
    default_tasks = tasks if default_all else _default_tasks(tasks)
    # Pick best default condition
    cond_pref = ["skill-evolved", "with-skill"]
    default_cond_idx = 0
    for pref in cond_pref:
        if pref in conditions:
            default_cond_idx = conditions.index(pref)
            break

    # Filter
    col1, col2, col3 = st.columns(3)
    with col1:
        sel_condition = st.selectbox(
            "Condition",
            conditions,
            index=default_cond_idx,
            key=f"{key_prefix}_condition",
        )
    with col2:
        sel_models = st.multiselect(
            "Models",
            models,
            default=default_models,
            key=f"{key_prefix}_models",
        )
    with col3:
        sel_tasks = st.multiselect(
            "Tasks",
            tasks,
            default=default_tasks,
            key=f"{key_prefix}_tasks",
        )

    if not sel_models or not sel_tasks:
        st.info("Select at least one model and one task.")
        return

    filtered = df[
        (df["condition"] == sel_condition)
        & (df["model_tag"].isin(sel_models))
        & (df["task"].isin(sel_tasks))
    ]

    if filtered.empty:
        st.warning("No data for this selection.")
        return

    # Aggregate: average pass_rate per task × model (across trials/timestamps)
    # NaN for missing combos (model never ran on that task)
    pivot = filtered.groupby(["task", "model_tag"])["pass_rate"].mean().unstack()

    # Reorder models
    pivot = pivot[[m for m in sel_models if m in pivot.columns]]

    import numpy as np
    import plotly.express as px

    # For the heatmap, use NaN-aware text formatting
    values = pivot.values
    text = np.where(
        np.isnan(values),
        "—",
        np.vectorize(lambda v: f"{v:.0%}")(np.nan_to_num(values)),
    )

    fig = px.imshow(
        values,
        x=pivot.columns.tolist(),
        y=pivot.index.tolist(),
        color_continuous_scale="RdYlGn",
        zmin=0,
        zmax=1,
        aspect="auto",
    )
    fig.update_traces(text=text, texttemplate="%{text}")
    fig.update_layout(
        xaxis_title="Model",
        yaxis_title="Task",
        height=max(300, 50 * len(pivot)),
        coloraxis_colorbar_title="Pass Rate",
        coloraxis_colorbar_tickformat=".0%",
    )
    st.plotly_chart(fig, width="stretch")

    # Also show as table
    with st.expander("Raw data"):
        display = pivot.copy()
        display = display.map(lambda v: f"{v:.0%}" if pd.notna(v) else "—")
        st.dataframe(display, width="stretch")


# ── Skill Impact ────────────────────────────────────────────────────


def _render_impact(df: pd.DataFrame, key_prefix: str = "impact", default_all: bool = False) -> None:
    """Bar chart: delta (skill minus no-skill) per task per model."""

    conditions = sorted(df["condition"].unique())
    skill_conditions = [c for c in conditions if c != "no-skill"]

    if "no-skill" not in conditions or not skill_conditions:
        st.warning("Need both 'no-skill' and skill conditions to compute impact.")
        return

    models = sorted(df["model_tag"].unique())
    tasks = sorted(df["task"].unique())

    default_models = models if default_all else _default_models(models)
    default_tasks = tasks if default_all else _default_tasks(tasks)

    col1, col2, col3 = st.columns(3)
    with col1:
        sel_models = st.multiselect(
            "Models",
            models,
            default=default_models,
            key=f"{key_prefix}_models",
        )
    with col2:
        sel_tasks = st.multiselect(
            "Tasks",
            tasks,
            default=default_tasks,
            key=f"{key_prefix}_tasks",
        )
    with col3:
        # Let user pick which skill condition to compare against no-skill
        default_skill = (
            "skill-evolved" if "skill-evolved" in skill_conditions else skill_conditions[-1]
        )
        sel_skill_cond = st.selectbox(
            "Compare vs no-skill",
            skill_conditions,
            index=skill_conditions.index(default_skill) if default_skill in skill_conditions else 0,
            key=f"{key_prefix}_skill_cond",
        )

    if not sel_models or not sel_tasks:
        return

    # Compute average pass_rate per task × model × condition
    agg = (
        df[df["model_tag"].isin(sel_models) & df["task"].isin(sel_tasks)]
        .groupby(["task", "model_tag", "condition"])["pass_rate"]
        .mean()
        .reset_index()
    )

    no_skill = agg[agg["condition"] == "no-skill"].rename(columns={"pass_rate": "baseline"})
    with_skill = agg[agg["condition"] == sel_skill_cond].rename(columns={"pass_rate": "skilled"})

    merged = no_skill.merge(with_skill, on=["task", "model_tag"], suffixes=("", "_ws"))
    merged["delta"] = merged["skilled"] - merged["baseline"]

    if merged.empty:
        st.warning("No overlapping task/model data.")
        return

    import plotly.express as px

    fig = px.bar(
        merged,
        x="task",
        y="delta",
        color="model_tag",
        barmode="group",
        text_auto="+.0%",
        title="Skill Impact (percentage point change)",
    )
    fig.update_layout(
        yaxis_tickformat="+.0%",
        yaxis_title="Delta (pp)",
        xaxis_title="Task",
        height=400,
    )
    fig.add_hline(y=0, line_dash="dash", line_color="gray")
    st.plotly_chart(fig, width="stretch")

    # Table view
    with st.expander("Impact table"):
        table = merged.pivot_table(
            index="task",
            columns="model_tag",
            values="delta",
        )
        st.dataframe(
            table.style.format(lambda v: f"{v:+.0%}" if pd.notna(v) else "—").background_gradient(
                cmap="RdYlGn",
                vmin=-0.5,
                vmax=0.5,
            ),
            width="stretch",
        )


def _expand_conditions(df: pd.DataFrame) -> pd.DataFrame:
    """Split 'with-skill' into 'skill-v1', 'skill-evolved' etc. based on skill_version."""
    df = df.copy()
    mask_skill = df["condition"] == "with-skill"
    sv = df.loc[mask_skill, "skill_version"].fillna("latest")

    # Map skill_version to readable condition name
    def _cond_name(v):
        if v == "v1":
            return "skill-v1"
        elif v in ("latest", ""):
            return "skill-evolved"
        else:
            return f"skill-{v}"

    df.loc[mask_skill, "condition"] = sv.map(_cond_name)
    return df


def _render_collections(df: pd.DataFrame) -> None:
    """Heatmap and skill impact filtered to a specific collection (benchmark run)."""
    st.subheader("Collections")

    # Normalize collection column
    if "collection" not in df.columns:
        df["collection"] = ""
    df["collection"] = df["collection"].fillna("")

    # Find available collections
    available = sorted(set(c for c in df["collection"].unique() if c))

    if not available:
        st.info("No collections yet. Run a benchmark with `--collection <name>` to tag results.")
        return

    sel_collection = st.selectbox("Collection", available, key="coll_select")

    coll_df = df[df["collection"] == sel_collection]

    if coll_df.empty:
        st.warning("No data for this collection.")
        return

    # Expand conditions: with-skill/v1 -> skill-v1, with-skill/latest -> skill-evolved
    coll_df = _expand_conditions(coll_df)

    # Summary metrics
    models = sorted(coll_df["model_tag"].unique())
    tasks = sorted(coll_df["task"].unique())
    conditions = sorted(coll_df["condition"].unique())
    trials = int(coll_df["trial"].max()) if "trial" in coll_df.columns else 1

    cols = st.columns(4)
    cols[0].metric("Models", len(models))
    cols[1].metric("Tasks", len(tasks))
    cols[2].metric("Conditions", ", ".join(conditions))
    cols[3].metric("Trials", trials)

    # Reuse heatmap and impact on the filtered data, defaulting to all models/tasks
    has_evolution = (
        "no-skill" in conditions and "skill-v1" in conditions and "skill-evolved" in conditions
    )
    tabs = ["Results Heatmap", "Skill Impact"]
    if has_evolution:
        tabs.append("Evolution Overview")
    tab_list = st.tabs(tabs)

    with tab_list[0]:
        _render_heatmap(coll_df, key_prefix="coll_hm", default_all=True)

    with tab_list[1]:
        _render_impact(coll_df, key_prefix="coll_imp", default_all=True)

    if has_evolution:
        with tab_list[2]:
            _render_evolution_overview(coll_df)


# ── Evolution Overview ──────────────────────────────────────────────


def _render_evolution_overview(df: pd.DataFrame) -> None:
    """Show no-skill → skill-v1 → skill-evolved progression per model."""
    import plotly.graph_objects as go

    models = sorted(df["model_tag"].unique())
    cond_order = ["no-skill", "skill-v1", "skill-evolved"]
    cond_labels = {"no-skill": "No Skill", "skill-v1": "Skill v1", "skill-evolved": "Skill Evolved"}
    cond_colors = {"no-skill": "#ef5350", "skill-v1": "#ffa726", "skill-evolved": "#66bb6a"}

    # Aggregate: avg pass_rate per model × task × condition
    agg = (
        df[df["condition"].isin(cond_order)]
        .groupby(["model_tag", "task", "condition"])["pass_rate"]
        .mean()
        .reset_index()
    )

    # ── Per-model grouped bar chart ─────────────────────────────────
    st.markdown("### Pass Rate by Model")

    model_avg = agg.groupby(["model_tag", "condition"])["pass_rate"].mean().reset_index()

    fig = go.Figure()
    for cond in cond_order:
        sub = model_avg[model_avg["condition"] == cond].set_index("model_tag")
        sub = sub.reindex(models)
        fig.add_trace(
            go.Bar(
                name=cond_labels[cond],
                x=models,
                y=sub["pass_rate"].values,
                marker_color=cond_colors[cond],
                text=[f"{v:.0%}" if pd.notna(v) else "—" for v in sub["pass_rate"].values],
                textposition="outside",
            )
        )

    fig.update_layout(
        barmode="group",
        yaxis_tickformat=".0%",
        yaxis_range=[0, 1.1],
        height=400,
        legend=dict(orientation="h", yanchor="bottom", y=1.02),
    )
    st.plotly_chart(fig, width="stretch")

    # ── Detailed results per model ──────────────────────────────────
    st.markdown("### Detailed Results")

    sel_model = st.selectbox("Model", models, key="evo_detail_model")

    model_data = agg[agg["model_tag"] == sel_model]
    pivot = model_data.pivot_table(
        index="task",
        columns="condition",
        values="pass_rate",
    )
    # Reorder columns
    pivot = pivot[[c for c in cond_order if c in pivot.columns]]
    pivot.columns = [cond_labels.get(c, c) for c in pivot.columns]

    # Add colored circle markers to distinguish conditions visually
    _col_rename = {
        "No Skill": "🔴 No Skill",
        "Skill v1": "🟠 Skill v1",
        "Skill Evolved": "🟢 Skill Evolved",
    }
    pivot = pivot.rename(columns=_col_rename)

    ns = _col_rename.get("No Skill", "No Skill")
    v1 = _col_rename.get("Skill v1", "Skill v1")
    ev = _col_rename.get("Skill Evolved", "Skill Evolved")

    # Add delta columns
    if ns in pivot.columns and v1 in pivot.columns:
        pivot["v1 Delta"] = pivot[v1] - pivot[ns]
    if ns in pivot.columns and ev in pivot.columns:
        pivot["Evolved Delta"] = pivot[ev] - pivot[ns]
    if v1 in pivot.columns and ev in pivot.columns:
        pivot["Evolution Gain"] = pivot[ev] - pivot[v1]

    # Add averages row
    avg_row = pivot.mean()
    avg_row.name = "AVERAGE"
    pivot = pd.concat([pivot, avg_row.to_frame().T])

    def _fmt_cell(v):
        if pd.isna(v):
            return "—"
        return f"{v:.0%}"

    def _fmt_delta(v):
        if pd.isna(v):
            return "—"
        return f"{v:+.0%}"

    fmt_map = {}
    for col in pivot.columns:
        if "Delta" in col or "Gain" in col:
            fmt_map[col] = _fmt_delta
        else:
            fmt_map[col] = _fmt_cell

    st.dataframe(
        pivot.style.format(fmt_map)
        .background_gradient(
            cmap="RdYlGn",
            vmin=0,
            vmax=1,
            subset=[c for c in pivot.columns if "Delta" not in c and "Gain" not in c],
        )
        .background_gradient(
            cmap="RdYlGn",
            vmin=-0.3,
            vmax=0.3,
            subset=[c for c in pivot.columns if "Delta" in c or "Gain" in c],
        ),
        width="stretch",
    )

    # ── Evolution delta table ───────────────────────────────────────
    st.markdown("### Evolution Impact (v1 → evolved)")

    v1 = agg[agg["condition"] == "skill-v1"].rename(columns={"pass_rate": "v1"})
    evolved = agg[agg["condition"] == "skill-evolved"].rename(columns={"pass_rate": "evolved"})
    baseline = agg[agg["condition"] == "no-skill"].rename(columns={"pass_rate": "baseline"})

    merged = (
        baseline[["task", "model_tag", "baseline"]]
        .merge(
            v1[["task", "model_tag", "v1"]],
            on=["task", "model_tag"],
            how="outer",
        )
        .merge(
            evolved[["task", "model_tag", "evolved"]],
            on=["task", "model_tag"],
            how="outer",
        )
    )
    merged["v1_delta"] = merged["v1"] - merged["baseline"]
    merged["evolved_delta"] = merged["evolved"] - merged["baseline"]
    merged["evolution_gain"] = merged["evolved"] - merged["v1"]

    # Pivot: tasks × models showing evolution_gain
    gain_pivot = merged.pivot_table(
        index="task",
        columns="model_tag",
        values="evolution_gain",
    )
    gain_pivot = gain_pivot[[m for m in models if m in gain_pivot.columns]]

    # Add averages
    avg_row = gain_pivot.mean()
    avg_row.name = "AVERAGE"
    gain_pivot = pd.concat([gain_pivot, avg_row.to_frame().T])

    st.dataframe(
        gain_pivot.style.format(lambda v: f"{v:+.0%}" if pd.notna(v) else "—").background_gradient(
            cmap="RdYlGn", vmin=-0.3, vmax=0.3
        ),
        width="stretch",
    )


# ── Run History ─────────────────────────────────────────────────────


def _render_history(df: pd.DataFrame) -> None:
    """Timeline of runs, filterable by model/task."""
    st.subheader("Run History")

    models = sorted(df["model_tag"].unique())
    tasks = sorted(df["task"].unique())

    col1, col2, col3 = st.columns(3)
    with col1:
        sel_model = st.selectbox("Model", ["All"] + models, key="hist_model")
    with col2:
        sel_task = st.selectbox("Task", ["All"] + tasks, key="hist_task")
    with col3:
        sel_condition = st.selectbox(
            "Condition",
            ["All"] + sorted(df["condition"].unique()),
            key="hist_cond",
        )

    filtered = df.copy()
    if sel_model != "All":
        filtered = filtered[filtered["model_tag"] == sel_model]
    if sel_task != "All":
        filtered = filtered[filtered["task"] == sel_task]
    if sel_condition != "All":
        filtered = filtered[filtered["condition"] == sel_condition]

    if filtered.empty:
        st.warning("No data for this selection.")
        return

    # Show table
    display_cols = [
        "task",
        "condition",
        "model_tag",
        "trial",
        "passed",
        "total",
        "pass_rate",
        "success",
        "tokens_in",
        "tokens_out",
        "time_ms",
    ]
    if "timestamp" in filtered.columns:
        display_cols.insert(0, "timestamp")
    if "skill_version" in filtered.columns:
        display_cols.append("skill_version")

    display_cols = [c for c in display_cols if c in filtered.columns]

    def _color_pass_rate(val):
        try:
            v = float(val)
            if v >= 0.9:
                return "color: #4caf50"
            elif v <= 0.1:
                return "color: #f44336"
        except (ValueError, TypeError):
            pass
        return ""

    st.dataframe(
        filtered[display_cols].style.map(_color_pass_rate, subset=["pass_rate"]),
        width="stretch",
        hide_index=True,
        height=min(600, 35 * len(filtered) + 38),
    )

    st.caption(f"{len(filtered)} rows")


# ── Launch ──────────────────────────────────────────────────────────


def _render_launch(project_dir: Path) -> None:
    """Form to launch a benchmark run."""
    import os
    import subprocess

    st.subheader("Launch Benchmark")

    model_presets = {
        "Claude Sonnet 4": "openrouter/anthropic/claude-sonnet-4",
        "Qwen 3.5 27B": "openrouter/qwen/qwen3.5-27b",
        "Llama 3.1 8B": "openrouter/meta-llama/llama-3.1-8b-instruct",
        "GigaChat": "gigachat",
        "GigaChat Pro": "gigachat-pro",
        "Custom": "",
    }

    col1, col2 = st.columns(2)
    with col1:
        preset = st.selectbox("Model preset", list(model_presets.keys()), key="bench_preset")
    with col2:
        if preset == "Custom":
            model = st.text_input("Model ID", key="bench_model_custom")
        else:
            model = model_presets[preset]
            st.text_input("Model ID", value=model, disabled=True, key="bench_model_display")

    # Task selection
    from evolution.eval.task import discover_tasks

    tasks = discover_tasks(project_dir / "tasks")
    task_names = [t.name for t in tasks]

    sel_tasks = st.multiselect(
        "Tasks (empty = all)",
        task_names,
        default=[],
        key="bench_tasks",
    )

    col3, col4, col5 = st.columns(3)
    with col3:
        trials = st.number_input("Trials", value=1, min_value=1, max_value=10, key="bench_trials")
    with col4:
        max_tokens = st.number_input(
            "Max tokens",
            value=16384,
            min_value=1024,
            max_value=65536,
            step=1024,
            key="bench_tokens",
        )
    with col5:
        no_skill_only = st.checkbox("No-skill only", key="bench_noskill")
        skill_only = st.checkbox("Skill only", key="bench_skillonly")

    if st.button("Run Benchmark", key="bench_run_btn", type="primary", disabled=not model):
        cmd = [
            "python3",
            "runs/bench.py",
            "--model",
            model,
            "--max-tokens",
            str(max_tokens),
            "--trials",
            str(trials),
        ]
        if sel_tasks:
            cmd += ["--tasks"] + sel_tasks
        if no_skill_only:
            cmd.append("--no-skill-only")
        if skill_only:
            cmd.append("--skill-only")

        env = os.environ.copy()

        with st.status("Running benchmark...", expanded=True) as status:
            st.code(f"$ {' '.join(cmd)}", language="bash")

            try:
                result = subprocess.run(
                    cmd,
                    capture_output=True,
                    text=True,
                    timeout=3600,
                    cwd=str(project_dir),
                    env=env,
                )
                output = result.stdout + "\n" + result.stderr

                if result.returncode == 0:
                    status.update(label="Benchmark complete", state="complete")
                else:
                    status.update(label="Benchmark failed", state="error")

                st.code(output, language="text")

            except subprocess.TimeoutExpired:
                status.update(label="Timeout (1h)", state="error")
                st.error("Benchmark timed out after 1 hour.")
