"""Mechanical edit-op pipeline: parse, apply, and select structural SKILL.md edits.

Edit ops are a structured alternative to full-body rewrites: a reflector (or
any caller) proposes a small list of targeted `EditOp` instructions, which are
applied to a skill body without any further LLM involvement.
"""

from __future__ import annotations

import difflib
import json
import os
import re
from typing import Literal

from pydantic import BaseModel, Field, ValidationError, model_validator

from evolution.config import train_optimization_enabled
from evolution.evolve.reflection import _extract_json

EditOpKind = Literal["append", "insert_after", "replace", "delete"]


class EditOp(BaseModel):
    """A single mechanical edit instruction against a skill body."""

    op: EditOpKind
    target: str = ""
    content: str = ""
    rationale: str = ""
    evidence_refs: list[str] = Field(default_factory=list)

    @model_validator(mode="after")
    def _check_required_fields(self) -> EditOp:
        if self.op in ("replace", "insert_after", "delete") and not self.target.strip():
            raise ValueError(f"op={self.op!r} requires a non-empty target")
        if self.op in ("append", "insert_after", "replace") and not self.content.strip():
            raise ValueError(f"op={self.op!r} requires non-empty content")
        if self.op == "append" and self.target.strip():
            raise ValueError("op='append' requires an empty target")
        if self.op == "delete" and self.content.strip():
            raise ValueError("op='delete' requires empty content")
        return self


def _coerce_raw_edits(parsed: object) -> tuple[list[object], dict | None]:
    if isinstance(parsed, dict) and "parse_error" in parsed:
        return [], {
            "raw": str(parsed.get("raw_response", ""))[:500],
            "reason": str(parsed["parse_error"]),
        }
    if isinstance(parsed, list):
        return parsed, None
    if isinstance(parsed, dict) and isinstance(parsed.get("edits"), list):
        return parsed["edits"], None
    if isinstance(parsed, dict) and "op" in parsed:
        return [parsed], None
    return [], {
        "raw": str(parsed)[:500],
        "reason": "no 'edits' list or edit object found in parsed JSON",
    }


def parse_edits(text: str) -> tuple[list[EditOp], list[dict]]:
    """Tolerantly extract `EditOp` entries from raw LLM output.

    Returns `(valid_ops, error_records)`; malformed entries are reported as
    error records instead of raising.
    """
    raw_edits, top_error = _coerce_raw_edits(_extract_json(text))

    valid: list[EditOp] = []
    errors: list[dict] = []
    if top_error is not None:
        errors.append(top_error)

    for raw in raw_edits:
        if not isinstance(raw, dict):
            errors.append({"raw": str(raw)[:500], "reason": "edit entry is not a JSON object"})
            continue
        try:
            valid.append(EditOp(**raw))
        except ValidationError as exc:
            errors.append(
                {"raw": json.dumps(raw)[:500], "reason": f"{type(exc).__name__}: {exc!s}"[:500]}
            )

    return valid, errors


_BLOCK_MARKER_PREFIXES = ("#", "**", "```", "- ", "> ")


def _inside_fence(text: str, pos: int) -> bool:
    """Whether `pos` sits inside an unclosed ``` fence opened earlier in `text`."""
    inside = False
    offset = 0
    for line in text.splitlines(keepends=True):
        if offset >= pos:
            break
        if line.lstrip().startswith("```"):
            inside = not inside
        offset += len(line)
    return inside


def _fence_close_end(body: str, pos: int) -> int | None:
    """Offset just past the next ``` line at/after `pos`, or None if there isn't one."""
    offset = pos
    for line in body[pos:].splitlines(keepends=True):
        offset += len(line)
        if line.lstrip().startswith("```"):
            return offset
    return None


def _starts_with_block_marker(content: str) -> bool:
    if content.startswith(_BLOCK_MARKER_PREFIXES):
        return True
    return len(content) >= 3 and content[0].isdigit() and content[1:3] == ". "


def _splice_with_hygiene(
    body: str, insert_at: int, content: str, *, force_block: bool = False
) -> str:
    if force_block or _starts_with_block_marker(content):
        if body[insert_at - 1 : insert_at] != "\n":
            content = "\n" + content
        if not content.endswith("\n") and body[insert_at : insert_at + 1] not in ("", "\n"):
            content += "\n"
    return body[:insert_at] + content + body[insert_at:]


def apply_edits(
    body: str, edits: list[EditOp], *, insert_fallback: bool = True
) -> tuple[str, list[dict]]:
    """Sequentially apply `edits` to `body`; later edits see earlier results.

    `insert_fallback=False` classifies a missed `insert_after` anchor as
    `skipped_target_not_found` (so it can enter the repair round) instead of
    appending at the end of the body.
    """
    report: list[dict] = []
    for edit in edits:
        if edit.op == "append":
            body = f"{body}\n\n{edit.content}" if body else edit.content
            status = "applied_append"
        elif edit.op == "insert_after":
            idx = body.find(edit.target)
            if idx == -1:
                if insert_fallback:
                    body = f"{body}\n\n{edit.content}" if body else edit.content
                    status = "fallback_append"
                else:
                    status = "skipped_target_not_found"
            else:
                insert_at = idx + len(edit.target)
                if _inside_fence(body, insert_at):
                    relocated = _fence_close_end(body, insert_at)
                    if relocated is None:
                        body = f"{body}\n\n{edit.content}" if body else edit.content
                        status = "fallback_append"
                    else:
                        body = _splice_with_hygiene(body, relocated, edit.content, force_block=True)
                        status = "applied_insert_after_relocated_fence"
                else:
                    body = _splice_with_hygiene(body, insert_at, edit.content)
                    status = "applied_insert_after"
        elif edit.op == "replace":
            idx = body.find(edit.target)
            if idx == -1:
                status = "skipped_target_not_found"
            else:
                body = body[:idx] + edit.content + body[idx + len(edit.target) :]
                status = "applied_replace"
        else:
            idx = body.find(edit.target)
            if idx == -1:
                status = "skipped_target_not_found"
            else:
                body = body[:idx] + body[idx + len(edit.target) :]
                status = "applied_delete"
        report.append(
            {
                "op": edit.op,
                "target_head": edit.target[:60],
                "status": status,
                "rationale": edit.rationale[:120],
            }
        )
    return body, report


def edit_budget() -> int:
    """Max edits admitted per selection pass.

    `EVO_EDIT_BUDGET` overrides the default, which is 6 for train optimization
    and 4 otherwise.
    """
    raw = os.environ.get("EVO_EDIT_BUDGET")
    if raw is None or raw == "":
        return 6 if train_optimization_enabled() else 4
    try:
        budget = int(raw)
    except ValueError as exc:
        raise ValueError(f"EVO_EDIT_BUDGET {raw!r} is not an integer") from exc
    if budget < 0:
        raise ValueError(f"EVO_EDIT_BUDGET must be non-negative, got {budget}")
    return budget


def edit_repair_insert_enabled() -> bool:
    """Route missed insert_after anchors into repair.

    `EVO_EDIT_REPAIR_INSERT` overrides the default, which is on for train
    optimization and off otherwise.
    """
    raw = os.environ.get("EVO_EDIT_REPAIR_INSERT")
    if raw is None or raw == "":
        return train_optimization_enabled()
    return raw.strip() == "1"


def edit_dedup_body_threshold() -> float | None:
    """Body-duplicate-content guard threshold (`EVO_EDIT_DEDUP_BODY`).

    Float in (0, 1]. Unset defaults to 0.90 for train optimization and disables
    the guard otherwise. Empty/non-numeric/non-positive values disable the guard.
    """
    raw = os.environ.get("EVO_EDIT_DEDUP_BODY")
    if raw is None or raw == "":
        return 0.90 if train_optimization_enabled() else None
    try:
        value = float(raw)
    except ValueError:
        return None
    if not (0 < value <= 1):
        return None
    return value


def edit_dedup_topic_enabled() -> bool:
    """Whether heading/topic duplicate suppression is active."""
    raw = os.environ.get("EVO_EDIT_DEDUP_TOPIC")
    if raw is None or raw == "":
        return train_optimization_enabled()
    return raw.strip().lower() in {"1", "true", "yes", "on"}


_TOPIC_HEADING_RE = re.compile(r"^\s{0,3}#{2,6}\s+(.+?)\s*$")


def _normalize_topic(text: str) -> str:
    text = re.sub(r"`([^`]*)`", r"\1", text).lower()
    text = re.sub(r"[^a-z0-9]+", " ", text)
    return " ".join(text.split())


def _content_topic_key(content: str) -> str:
    for line in content.splitlines():
        match = _TOPIC_HEADING_RE.match(line)
        if match:
            return _normalize_topic(match.group(1))
    return ""


def _body_topic_keys(body: str) -> set[str]:
    topics: set[str] = set()
    for line in body.splitlines():
        match = _TOPIC_HEADING_RE.match(line)
        if not match:
            continue
        topic = _normalize_topic(match.group(1))
        if topic:
            topics.add(topic)
    return topics


def _max_body_line_similarity(content: str, body: str) -> float:
    content_lines = content.splitlines()
    if len(content_lines) < 2:
        return 0.0
    body_lines = body.splitlines()
    window_len = len(content_lines)
    if len(body_lines) < window_len:
        return 0.0
    best = 0.0
    for start in range(len(body_lines) - window_len + 1):
        window = body_lines[start : start + window_len]
        ratio = difflib.SequenceMatcher(a=window, b=content_lines).ratio()
        if ratio > best:
            best = ratio
    return best


_CONTENT_ADDING_OPS = ("append", "insert_after")


def select_edits(
    proposals: list[EditOp], budget: int, *, body: str | None = None
) -> tuple[list[EditOp], list[dict]]:
    """Drop exact duplicates and clip to `budget`, preserving input order.

    When `edit_dedup_body_threshold()` is configured and `body` is given,
    content-adding edits (append/insert_after) whose content nearly matches an
    existing same-length window of `body` are also dropped as
    `skipped_duplicate_content` — replace/delete are exempt since they remove
    or rewrite content rather than adding it.
    """
    if budget < 0:
        raise ValueError(f"edit budget must be non-negative, got {budget}")
    threshold = edit_dedup_body_threshold()
    topic_guard = edit_dedup_topic_enabled() and body is not None
    existing_topics = _body_topic_keys(body or "") if topic_guard else set()
    seen_topics: set[str] = set()
    seen: set[tuple[str, str, str]] = set()
    deduped: list[EditOp] = []
    report: list[dict] = []

    for edit in proposals:
        key = (edit.op, edit.target, edit.content)
        if key in seen:
            report.append(
                {
                    "op": edit.op,
                    "target_head": edit.target[:60],
                    "status": "skipped_duplicate",
                    "rationale": edit.rationale[:120],
                }
            )
            continue
        seen.add(key)
        if topic_guard and edit.op in _CONTENT_ADDING_OPS:
            topic = _content_topic_key(edit.content)
            if topic and (topic in existing_topics or topic in seen_topics):
                report.append(
                    {
                        "op": edit.op,
                        "target_head": edit.target[:60],
                        "status": "skipped_duplicate_topic",
                        "rationale": edit.rationale[:120],
                    }
                )
                continue
            if topic:
                seen_topics.add(topic)
        if (
            threshold is not None
            and body is not None
            and edit.op in _CONTENT_ADDING_OPS
            and _max_body_line_similarity(edit.content, body) >= threshold
        ):
            report.append(
                {
                    "op": edit.op,
                    "target_head": edit.target[:60],
                    "status": "skipped_duplicate_content",
                    "rationale": edit.rationale[:120],
                }
            )
            continue
        deduped.append(edit)

    selected = deduped[:budget]
    for edit in deduped[budget:]:
        report.append(
            {
                "op": edit.op,
                "target_head": edit.target[:60],
                "status": "skipped_over_budget",
                "rationale": edit.rationale[:120],
            }
        )

    return selected, report
