"""Tasks page — browse tasks, view instructions, inspect inputs, launch solves."""

from __future__ import annotations

from pathlib import Path

import streamlit as st


def _get_container_store(project_dir: Path, task=None):
    """Get ContainerStore, trying project_dir first then inferring from task path."""
    try:
        from evolution.core.containers import ContainerStore

        cstore = ContainerStore(project_dir=project_dir, user_dir=Path.home())
        if cstore.list():
            return cstore
        # Fallback: infer project root from task path
        if task is not None:
            alt_root = task.path.parent.parent
            if (alt_root / ".agents" / "containers").is_dir():
                return ContainerStore(project_dir=alt_root, user_dir=Path.home())
        return cstore
    except Exception:
        return None


def render(get_store, project_dir: Path) -> None:
    from evolution.eval.task import discover_tasks

    tasks_dir = project_dir / "tasks"
    tasks = discover_tasks(tasks_dir)

    if not tasks:
        st.title("Tasks")
        st.warning("No tasks found.")
        return

    # ── Header metrics ──────────────────────────────────────────────
    st.title("Tasks")

    # ── Source filter ───────────────────────────────────────────────
    _SOURCE_LABELS = {"": "Custom", "skillsbench": "SkillsBench", "sb-bench": "SB-Bench"}
    sources = sorted(set(t.source or "" for t in tasks))
    source_options = ["All"] + [_SOURCE_LABELS.get(s, s) for s in sources]
    selected_source = st.selectbox("Source", source_options, key="task_source_filter")

    if selected_source != "All":
        # Reverse-map label to source value
        source_val = next(
            (k for k, v in _SOURCE_LABELS.items() if v == selected_source), selected_source
        )
        tasks = [t for t in tasks if (t.source or "") == source_val]

    by_diff: dict[str | None, list] = {}
    for t in tasks:
        by_diff.setdefault(t.difficulty, []).append(t)

    cols = st.columns(4)
    cols[0].metric("Total Tasks", len(tasks))
    cols[1].metric("Easy", len(by_diff.get("easy", [])))
    cols[2].metric("Medium", len(by_diff.get("medium", [])))
    cols[3].metric("Hard", len(by_diff.get("hard", [])))

    # ── Task table ──────────────────────────────────────────────────
    import pandas as pd

    # Resolve containers for skill display
    cstore = _get_container_store(project_dir, tasks[0] if tasks else None)

    rows = []
    for t in tasks:
        inputs_dir = t.path / "inputs"
        input_files = list(inputs_dir.glob("*")) if inputs_dir.exists() else []
        total_size = sum(f.stat().st_size for f in input_files if f.is_file())

        # Resolve skills: if first required is a container, show container + skills
        skill_ref = t.skills_required[0] if t.skills_required else ""
        is_container = cstore and cstore.has(skill_ref) if skill_ref else False
        if is_container:
            container = cstore.get(skill_ref)
            skills_display = ", ".join(container.skills)
            skill_type = f"📦 {skill_ref}"
        else:
            skills_display = ", ".join(t.skills_required)
            skill_type = ""

        rows.append(
            {
                "Name": t.name,
                "Difficulty": t.difficulty,
                "Container": skill_type,
                "Skills": skills_display,
                "Source": _SOURCE_LABELS.get(t.source or "", t.source or "Custom"),
                "Category": t.category,
                "Inputs": len(input_files),
                "Size": _fmt_size(total_size),
            }
        )

    df = pd.DataFrame(rows)

    def _color_difficulty(val):
        colors = {"easy": "#4caf50", "medium": "#ff9800", "hard": "#f44336"}
        return f"color: {colors.get(val, '')}"

    st.dataframe(
        df.style.map(_color_difficulty, subset=["Difficulty"]),
        width="stretch",
        hide_index=True,
    )

    # ── Task detail ─────────────────────────────────────────────────
    st.divider()

    task_names = [t.name for t in tasks]
    selected = st.selectbox("Select task", task_names, key="task_select")
    task = next(t for t in tasks if t.name == selected)

    tab_instruction, tab_inputs, tab_tests, tab_solve = st.tabs(
        ["Instruction", "Input Files", "Tests", "Solve"]
    )

    with tab_instruction:
        _render_instruction(task, cstore=cstore)

    with tab_inputs:
        _render_inputs(task)

    with tab_tests:
        _render_tests(task)

    with tab_solve:
        _render_solve(task, get_store, project_dir)


# ── Instruction tab ─────────────────────────────────────────────────


def _render_instruction(task, cstore=None):
    """Show task metadata and instruction."""
    col1, col2 = st.columns([1, 2])

    with col1:
        st.markdown("**Metadata**")
        st.markdown(f"- **Difficulty:** {task.difficulty}")
        st.markdown(f"- **Category:** {task.category}")

        # Show container + skills if applicable
        skill_ref = task.skills_required[0] if task.skills_required else ""
        if cstore and skill_ref and cstore.has(skill_ref):
            container = cstore.get(skill_ref)
            st.markdown(f"- **Container:** 📦 {skill_ref}")
            st.markdown(f"- **Skills:** {', '.join(container.skills)}")
        else:
            st.markdown(f"- **Skills:** {', '.join(task.skills_required)}")

        if task.tags:
            st.markdown(f"- **Tags:** {', '.join(task.tags)}")
        st.markdown(f"- **Timeout:** {task.timeout_sec}s")
        if task.source:
            st.markdown(f"- **Source:** {task.source}")

    with col2:
        st.markdown("**Instruction**")
        st.markdown(task.instruction)


# ── Inputs tab ──────────────────────────────────────────────────────


def _render_inputs(task):
    """Show input files with previews."""
    inputs_dir = task.path / "inputs"
    if not inputs_dir.exists():
        st.info("No inputs directory.")
        return

    files = sorted(f for f in inputs_dir.iterdir() if f.is_file())
    if not files:
        st.info("No input files.")
        return

    for f in files:
        size = f.stat().st_size
        ext = f.suffix.lower()

        with st.expander(f"{f.name} ({_fmt_size(size)})", expanded=False):
            if ext in (".csv", ".tsv"):
                _preview_csv(f, ext)
            elif ext in (".xlsx", ".xls"):
                _preview_excel(f)
            elif ext in (".json",):
                _preview_json(f)
            elif ext in (".txt", ".md", ".py", ".toml"):
                _preview_text(f)
            elif ext == ".pdf":
                st.caption(f"PDF file — {_fmt_size(size)}")
                _preview_pdf(f)
            elif ext in (".docx",):
                st.caption(f"Word document — {_fmt_size(size)}")
            elif ext in (".pptx",):
                st.caption(f"PowerPoint — {_fmt_size(size)}")
            else:
                st.caption(f"Binary file — {_fmt_size(size)}")


def _preview_csv(path: Path, ext: str):
    import pandas as pd

    try:
        sep = "\t" if ext == ".tsv" else ","
        df = pd.read_csv(path, sep=sep, nrows=20)
        st.dataframe(df, width="stretch", hide_index=True)
        total = sum(1 for _ in open(path)) - 1
        if total > 20:
            st.caption(f"Showing 20 of {total} rows")
    except Exception as e:
        st.error(f"Cannot preview: {e}")


def _preview_excel(path: Path):
    import pandas as pd

    try:
        xls = pd.ExcelFile(path)
        sheets = xls.sheet_names
        if len(sheets) > 1:
            sheet = st.selectbox("Sheet", sheets, key=f"sheet_{path.name}")
        else:
            sheet = sheets[0]
        df = pd.read_excel(path, sheet_name=sheet, nrows=20)
        st.dataframe(df, width="stretch", hide_index=True)
        full_df = pd.read_excel(path, sheet_name=sheet)
        if len(full_df) > 20:
            st.caption(f"Showing 20 of {len(full_df)} rows")
    except Exception as e:
        st.error(f"Cannot preview: {e}")


def _preview_json(path: Path):
    import json

    try:
        data = json.loads(path.read_text(encoding="utf-8"))
        st.json(data)
    except Exception as e:
        st.error(f"Cannot preview: {e}")


def _preview_text(path: Path):
    try:
        content = path.read_text(encoding="utf-8")
        lines = content.splitlines()
        if len(lines) > 50:
            st.code("\n".join(lines[:50]), language=_lang_for(path))
            st.caption(f"Showing 50 of {len(lines)} lines")
        else:
            st.code(content, language=_lang_for(path))
    except Exception as e:
        st.error(f"Cannot preview: {e}")


def _preview_pdf(path: Path):
    try:
        import fitz

        doc = fitz.open(str(path))
        st.caption(f"{len(doc)} pages")
        # Show first page as image
        if len(doc) > 0:
            page = doc[0]
            pix = page.get_pixmap(matrix=fitz.Matrix(1.5, 1.5))
            st.image(pix.tobytes("png"), caption="Page 1", width="stretch")
        doc.close()
    except ImportError:
        st.caption("Install PyMuPDF (fitz) for PDF preview")
    except Exception as e:
        st.error(f"Cannot preview: {e}")


# ── Tests tab ───────────────────────────────────────────────────────


def _render_tests(task):
    """Show the test file source."""
    test_path = task.test_path
    if not test_path.exists():
        st.warning(f"Test file not found: {test_path}")
        return

    content = test_path.read_text(encoding="utf-8")
    st.code(content, language="python")


# ── Solve tab ───────────────────────────────────────────────────────


def _render_solve(task, get_store, project_dir):
    """Launch a solve run."""
    st.markdown("Run the solver: LLM generates code → execute → evaluate.")

    col1, col2 = st.columns(2)

    with col1:
        model = st.text_input(
            "Model",
            value="openrouter/anthropic/claude-sonnet-4",
            key="solve_model",
        )

    with col2:
        no_skill = st.checkbox("No skill (baseline)", key="solve_no_skill")

    col3, col4 = st.columns(2)
    with col3:
        max_tokens = st.number_input(
            "Max tokens",
            value=16384,
            min_value=1024,
            max_value=65536,
            step=1024,
            key="solve_max_tokens",
        )
    with col4:
        timeout = st.number_input(
            "Timeout (sec)",
            value=int(task.timeout_sec),
            min_value=30,
            max_value=max(900, int(task.timeout_sec)),
            key="solve_timeout",
        )

    # Show which skill(s) will be used
    if not no_skill and task.skills_required:
        store = get_store()
        skill_ref = task.skills_required[0]
        # Check containers first
        try:
            solve_cstore = _get_container_store(project_dir, task)
            if solve_cstore and solve_cstore.has(skill_ref):
                container = solve_cstore.get(skill_ref)
                names = ", ".join(container.skills)
                st.info(f"Will use container **{skill_ref}** ({names})")
            elif store.has(skill_ref):
                skill = store.get(skill_ref)
                from evolution.lineage.tracker import LineageTracker

                tracker = LineageTracker(skill)
                st.info(f"Will use skill **{skill_ref}** ({tracker.current_version})")
            else:
                st.warning(f"Skill/container **{skill_ref}** not found — will run without skill")
        except Exception:
            if store.has(skill_ref):
                st.info(f"Will use skill **{skill_ref}**")
            else:
                st.warning(f"Skill **{skill_ref}** not found — will run without skill")

    if st.button("Run Solve", key="solve_btn", type="primary"):
        _run_solve(task, model, no_skill, max_tokens, timeout, get_store, project_dir)


def _run_solve(task, model, no_skill, max_tokens, timeout, get_store, project_dir):
    """Execute solve via subprocess (same as CLI)."""
    import os
    import subprocess

    # Build command
    cmd = [
        "evo",
        "solve",
        task.name,
        "-m",
        model,
        "--max-tokens",
        str(max_tokens),
        "--timeout",
        str(timeout),
    ]
    if no_skill:
        cmd.append("--no-skill")

    env = os.environ.copy()

    with st.status("Running solver...", expanded=True) as status:
        st.text(f"$ {' '.join(cmd)}")

        try:
            result = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                timeout=timeout + 60,  # extra time for LLM call
                cwd=str(project_dir),
                env=env,
            )

            output = result.stdout + "\n" + result.stderr

            if result.returncode == 0:
                status.update(label="Solve completed", state="complete")
            else:
                status.update(label="Solve failed", state="error")

            st.code(output, language="text")

        except subprocess.TimeoutExpired:
            status.update(label="Timeout", state="error")
            st.error(f"Solve timed out after {timeout + 60}s")
        except FileNotFoundError:
            status.update(label="Error", state="error")
            st.error("'evo' command not found. Make sure the package is installed.")


# ── Helpers ─────────────────────────────────────────────────────────


def _fmt_size(size_bytes: int) -> str:
    if size_bytes < 1024:
        return f"{size_bytes}B"
    elif size_bytes < 1024 * 1024:
        return f"{size_bytes / 1024:.0f}KB"
    else:
        return f"{size_bytes / (1024 * 1024):.1f}MB"


def _lang_for(path: Path) -> str:
    return {
        ".py": "python",
        ".toml": "toml",
        ".json": "json",
        ".md": "markdown",
    }.get(path.suffix.lower(), "text")
