"""Shared prompt-render helpers for the cross-round edit strategy.

The evolution loop assembles two cross-round signals per edit round and hands them to the editor
via ``editor_cfg``:
  * ``meta_skill_blob`` — directed-update output #2 (which recent edits improved vs regressed pass
    rates, plus a compact prior-attempts log);
  * ``rejected_attempts`` — the bodies+reasons of edits the delta-gate rejected earlier this round.

These helpers render those signals into prompt text. They live here (not in one adapter) so that
EVERY supported editor — hermes, the gpt-oss ``evolution`` rewriter, and the codex/claude session
editor — is steered by the same signals. Both functions return ``""`` for empty/absent input, so an
editor prompt is byte-identical to its pre-feature form whenever no meta is present.
"""

from __future__ import annotations

import os
from typing import Any

# directed-update output #2, rendered into the editor prompt when editor_cfg["meta_skill_blob"] is set.
_META_SKILL_BLOCK = (
    "## Cross-Round Meta-Guidance (which recent edits improved vs regressed pass rates)\n"
    "{meta}\n"
    "Steer THIS edit by it: repeat what helped, avoid/repair what regressed.\n"
)


def render_meta_skill(editor_cfg: dict[str, Any] | None) -> str:
    """Render the directed-update meta-guidance block from ``editor_cfg['meta_skill_blob']``.

    Empty/absent blob -> ``""`` (prompt unchanged from the pre-feature default).
    """
    blob = str((editor_cfg or {}).get("meta_skill_blob") or "").strip()
    if not blob:
        return ""
    return "\n" + _META_SKILL_BLOCK.format(meta=blob) + "\n"


def render_rejected_attempts(rejected_attempts: list[dict] | None) -> str:
    """Feed bounded feedback for prior rejected edits back to the editor.

    Each entry: ``{attempt, body, reason}``. Empty/absent -> ``""`` (first try, no section).
    """
    if not rejected_attempts:
        return ""
    cap = int(os.environ.get("EVO_HERMES_REJECTED_CHARS", "8000") or "8000")
    n = len(rejected_attempts)
    parts = [
        "## Your previous edit(s) this round were REJECTED by the quality gate\n"
        f"You have already made {n} edit(s) that the gate REJECTED. The gate scores your "
        "edited skill against the unchanged skill on held-out tasks and keeps it only if it "
        "improves them. Do NOT re-submit a near-copy of a rejected edit — diagnose why it "
        "failed and make a DIFFERENT, more general fix that does not remove working content.\n"
    ]
    for rec in rejected_attempts:
        att = rec.get("attempt")
        label = f"attempt {att + 1}" if isinstance(att, int) else "attempt"
        reason = str(rec.get("reason") or "rejected")
        if rec.get("kind") == "edit_brake":
            parts.append(f"\n### Rejected {label} — edit brake\n{reason}\n")
            continue
        body = str(rec.get("body") or "")
        edits = []
        for edit in rec.get("edits") or []:
            if not isinstance(edit, dict):
                continue
            summary = " ".join(
                str(edit.get(key) or "").strip()
                for key in ("op", "target_head", "status", "rationale")
            ).strip()
            if summary:
                edits.append(f"- {summary}")
        if len(body) > cap:
            body = body[: cap // 2] + "\n[... rejected body truncated ...]\n" + body[-cap // 2 :]
        parts.append(
            f"\n### Rejected {label} — {reason}\n"
            + (f"Structured edits:\n{chr(10).join(edits)}\n" if edits else "")
            + "The SKILL.md you submitted (rejected, do not repeat):\n"
            f"```markdown\n{body}\n```\n"
        )
    return "\n".join(parts) + "\n"


def render_editor_meta(editor_cfg: dict[str, Any] | None) -> str:
    """Combined cross-round steering block for a single-slot editor prompt: the meta-guidance
    followed by the prior-rejected-attempt feedback. Returns ``""`` when neither is present.

    Call THIS one function at each editor call site that has a single meta slot, so a newly
    added editor cannot ship having rendered only one of the two halves (or neither) — the exact
    regression this module exists to prevent. Editors whose prompt has two dedicated slots (e.g.
    REFLECT_PROMPT's cross_round / rejected_edits) still call the two halves directly.
    """
    cfg = editor_cfg or {}
    return render_meta_skill(cfg) + render_rejected_attempts(cfg.get("rejected_attempts"))


__all__ = ["render_meta_skill", "render_rejected_attempts", "render_editor_meta"]
