"""Shared helpers for the skill-rewrite backends (text-return / file-edit / session)."""

from __future__ import annotations

import hashlib
import logging
import os
import shutil
from collections import Counter
from difflib import SequenceMatcher
from pathlib import Path
from typing import TYPE_CHECKING, Any

from evolution import config
from evolution.core.models import Skill
from evolution.eval.evidence import sanitize_feedback
from evolution.evolve.preservation import split_skill_body_by_heading
from evolution.evolve.rewrite_guards import (
    actionable_success_reflections,
    scan_leakage,
)
from evolution.evolve.rewrite_outcome import (
    RewriteOutcome,
)

if TYPE_CHECKING:
    pass

logger = logging.getLogger(__name__)


_SEVERITY_RANK = {"critical": 0, "major": 1, "minor": 2, "info": 3}


def _parent_top_headings(body: str) -> list[str]:
    """Return parent's H2+H3 heading lines (verbatim, stripped) for the preserve list."""
    out: list[str] = []
    for heading, _section_body in split_skill_body_by_heading(body):
        h = heading.strip()
        if not h or h.startswith("name:"):
            continue
        out.append(h)
    return out


HEADING_FUZZY_MATCH_RATIO = 0.85


def _candidate_added_new_heading(parent_body: str, candidate_body: str) -> tuple[bool, list[str]]:
    """Detect any candidate heading (``##``/``###``/``####``/…) that does not
    fuzzy-match a parent heading.

    Fuzzy match: SequenceMatcher.ratio() >= 0.85 on lowercased+stripped
    heading text (same threshold as preservation.heading_retention).  Returns
    ``(added, list_of_new_headings)``.  Matches every heading level ≥ ``##``
    (i.e., ``^##+ ``) — adding a new ``#### Sub-step`` under an existing
    section still counts as a new heading.  An empty parent heading list
    permits anything (back-compat: skills without any ``##+`` heading are
    unconstrained).
    """
    parent_headings = _parent_top_headings(parent_body)
    if not parent_headings:
        return (False, [])
    candidate_headings = _parent_top_headings(candidate_body)
    parent_norm = [h.strip().lower() for h in parent_headings]
    added: list[str] = []
    for ch in candidate_headings:
        ch_norm = ch.strip().lower()
        if any(
            SequenceMatcher(None, ch_norm, ph_norm).ratio() >= HEADING_FUZZY_MATCH_RATIO
            for ph_norm in parent_norm
        ):
            continue
        added.append(ch)
    return (bool(added), added)


def _collect_scripts(skill: Skill, max_chars: int = 15000) -> str:
    """Collect scripts/ content from the skill directory."""
    scripts_dir = skill.path / "scripts"
    if not scripts_dir.is_dir():
        return ""

    parts = []
    total = 0
    for f in sorted(scripts_dir.iterdir()):
        if not f.is_file() or f.suffix not in (".py", ".sh", ".md", ".txt"):
            continue
        content = f.read_text(encoding="utf-8", errors="replace")
        if total + len(content) > max_chars:
            break
        parts.append(f"### {f.name}\n```{f.suffix.lstrip('.')}\n{content}\n```")
        total += len(content)

    if not parts:
        return ""
    return (
        "\n\n## Skill Scripts (working reference code from the skill directory)\n\n"
        + "\n\n".join(parts)
    )


def _sanitize_reflections_for_rewriter(reflections: list[dict]) -> list[dict]:
    """Strip oracle literals in general mode before rewriting."""
    if config.train_optimization_enabled() or config.reflect_blind():
        return reflections
    out: list[dict] = []
    for reflection in reflections:
        if not isinstance(reflection, dict):
            out.append(reflection)
            continue
        sanitized = dict(reflection)
        for key in ("root_cause", "skill_gap", "suggested_fix"):
            if sanitized.get(key):
                sanitized[key] = sanitize_feedback(str(sanitized[key]))
        out.append(sanitized)
    return out


def _format_reflections(reflections: list[dict]) -> str:
    text = ""
    for i, r in enumerate(reflections, 1):
        if "error" in r:
            continue
        text += (
            f"\n### Failure {i} "
            f"(model: {r.get('model', '?')}, pass_rate: {r.get('pass_rate', 0):.0%})\n"
        )
        text += f"- **Root cause**: {r.get('root_cause', '?')}\n"
        text += f"- **Skill gap**: {r.get('skill_gap', '?')}\n"
        text += f"- **Suggested fix**: {r.get('suggested_fix', '?')}\n"
        text += f"- **Pattern**: {r.get('pattern', '?')}\n"
    return text


def _format_success_preserve(reflections: list[dict]) -> str:
    """Render success-kind reflections as a 'preserve these sections' block.

    Returns ``""`` when no actionable successes; otherwise a
    ``## Success Patterns to Preserve`` block listing helpful sections + the
    reinforcement pattern from each success reflection.
    """
    successes = actionable_success_reflections(reflections)
    if not successes:
        return ""
    lines: list[str] = ["", "## Success Patterns to Preserve"]
    for i, r in enumerate(successes, 1):
        helpful = r.get("helpful_sections") or []
        if isinstance(helpful, list):
            sections = ", ".join(str(h) for h in helpful if h) or "(unspecified)"
        else:
            sections = str(helpful)
        pat = r.get("reinforcement_pattern", "?")
        transfer = r.get("transferability", "?")
        lines.append(
            f"- Success {i} (pattern={pat}, transferability={transfer}): "
            f"keep `{sections}` substantially intact."
        )
    lines.append("")
    return "\n".join(lines)


def _pattern_summary(reflections: list[dict]) -> str:
    patterns = Counter(r.get("pattern", "unknown") for r in reflections if "error" not in r)
    summary = "| Pattern | Count |\n|---------|-------|\n"
    for pat, cnt in patterns.most_common():
        summary += f"| {pat} | {cnt} |\n"
    return summary


def _reject_leaked_rewrite(skill: Skill, body: str, corpus: str) -> bool:
    if os.environ.get("EVO_DISABLE_LEAK_SCANNER", "").strip().lower() in {"1", "true", "yes"}:
        return False
    findings = scan_leakage(body, corpus)
    if not findings:
        return False
    reject = not config.train_optimization_enabled()
    logger.warning(
        "rewrite for %s copied train-provenance text (%s); %s",
        skill.name,
        "; ".join(findings[:5]),
        "keeping parent version" if reject else "reporting only under train-oracle policy",
    )
    return reject


def _candidate_root() -> Path:
    """Resolve the temp root under which per-row candidate dirs live."""
    return Path(os.environ.get("EVO_C1_CANDIDATE_ROOT") or "/tmp")


def _non_empty_line_churn(parent_body: str, candidate_body: str) -> float:
    """Edit-budget churn as a fraction of parent non-empty lines."""
    p_lines = [ln for ln in parent_body.splitlines() if ln.strip()]
    c_lines = [ln for ln in candidate_body.splitlines() if ln.strip()]
    if not p_lines:
        return 1.0 if c_lines else 0.0
    opcodes = SequenceMatcher(None, p_lines, c_lines).get_opcodes()
    churn = 0
    for tag, i1, i2, j1, j2 in opcodes:
        if tag == "insert":
            churn += j2 - j1
        elif tag == "delete":
            churn += i2 - i1
        elif tag == "replace":
            churn += max(i2 - i1, j2 - j1)
    return churn / len(p_lines)


def _rewrite_provenance(skill: Skill) -> tuple[float | None, dict[str, Any]]:
    """Build parent provenance and the shared base-budget field.

    Used by both the file-edit and agentic-session paths so every audit
    RewriteOutcome records which parent the guards ran against.
    """
    from evolution.evolve.edit_brake import resolve_base_budget

    budget_frac = resolve_base_budget()
    base_prov: dict[str, Any] = {
        "parent_skill_path": str(skill.skill_md_path.resolve()),
        "parent_body_sha256": hashlib.sha256(skill.body.encode("utf-8")).hexdigest(),
        "edit_budget_frac": budget_frac,
    }
    return budget_frac, base_prov


def _cleanup_candidate(
    candidate_dir: Path,
    audit_root: Path | None,
    row_id: str,
    debug_archive: bool,
    outcome: RewriteOutcome,
) -> None:
    """Either archive the candidate dir for postmortem or delete it.

    Mutates ``outcome.candidate_debug_dir`` when archiving succeeds.
    """
    if not candidate_dir.exists():
        return
    if debug_archive and audit_root is not None and row_id:
        try:
            dest = audit_root / "c1_candidates" / row_id
            dest.parent.mkdir(parents=True, exist_ok=True)
            if dest.exists():
                shutil.rmtree(dest)
            shutil.move(str(candidate_dir), str(dest))
            outcome.candidate_debug_dir = str(dest)
            return
        except Exception as exc:
            logger.warning("EVO_DEBUG_C1 archive failed (%s); deleting candidate dir", exc)
    shutil.rmtree(candidate_dir, ignore_errors=True)
