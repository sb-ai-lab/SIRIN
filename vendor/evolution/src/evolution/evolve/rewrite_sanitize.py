"""Sanitize model-produced ``SKILL.md`` rewrite bodies before audit."""

from __future__ import annotations

import re

_PREAMBLE_RE = re.compile(
    r"^(here\s+is\b|here['’]s\b|sure[,!.]|certainly[,!.]|of\s+course[,!.]|"
    r"absolutely[,!.]|okay[,!.]|ok[,!.]|i['’]ve\s+\w+|i\s+have\s+\w+|"
    r"below\s+is\s+(the\s+)?.*\bskill\b)",
    re.IGNORECASE,
)
_CHANGELOG_HEADING_RE = re.compile(
    r"^#{1,6}\s+(summary\s+of\s+changes|changes\s+made|change\s*log|changelog)"
    r"\s*[:.!]*\s*$",
    re.IGNORECASE,
)
_DOC_WRAPPER_INFOS = {"", "markdown", "md"}


def _is_fence_delimiter(line: str) -> bool:
    s = line.strip()
    if not s.startswith("```"):
        return False
    info = s[3:].strip()
    return "`" not in info and (not info or len(info.split()) == 1)


def _strip_whole_body_fence(text: str) -> str:
    s = text.strip()
    lines = s.split("\n")
    if len(lines) < 2:
        return text
    first = lines[0]
    last = lines[-1]
    if not _is_fence_delimiter(first) or not _is_fence_delimiter(last):
        return text
    if first.strip()[3:].strip().lower() not in _DOC_WRAPPER_INFOS:
        return text
    if last.strip() != "```":
        return text
    inner = lines[1:-1]
    if any(_is_fence_delimiter(line) for line in inner):
        return text
    if not "\n".join(inner).strip():
        return text
    return "\n".join(inner)


def _looks_like_body_start(line: str) -> bool:
    stripped = line.strip()
    return bool(stripped) and (
        stripped == "---" or stripped.startswith("#") or stripped.startswith("```")
    )


def _is_meta_frame_line(stripped: str, lines: list[str], idx: int) -> bool:
    if stripped.rstrip().endswith(":"):
        return True
    if len(stripped) > 80:
        return False
    j = idx + 1
    while j < len(lines) and lines[j].strip() == "":
        j += 1
    return j < len(lines) and _looks_like_body_start(lines[j])


def _strip_leading_preamble(text: str) -> str:
    lines = text.split("\n")
    idx = 0
    skipped_preamble = False
    while idx < len(lines):
        ln = lines[idx]
        s = ln.strip()
        if s == "":
            idx += 1
            continue
        if _looks_like_body_start(ln):
            break
        if _PREAMBLE_RE.match(s) and _is_meta_frame_line(s, lines, idx):
            skipped_preamble = True
            idx += 1
            continue
        break
    if not skipped_preamble:
        return text
    if idx < len(lines) and _looks_like_body_start(lines[idx]):
        return "\n".join(lines[idx:])
    return text


def _looks_like_appended_changelog(section_lines: list[str]) -> bool:
    body = section_lines[1:]
    non_blank = [ln for ln in body if ln.strip()]
    if not non_blank:
        return True
    if any(ln.strip().startswith("#") for ln in non_blank):
        return False
    body_text = "\n".join(body).strip()
    if len(body_text) <= 600:
        return True
    list_like = 0
    for ln in non_blank:
        s = ln.strip()
        if s[:1] in {"-", "*", "+"} or re.match(r"^\d+[.)]\s", s):
            list_like += 1
    return list_like >= 0.60 * len(non_blank)


def _strip_trailing_changelog(text: str) -> str:
    lines = text.split("\n")
    last_idx = None
    for i, ln in enumerate(lines):
        if _CHANGELOG_HEADING_RE.match(ln.strip()):
            last_idx = i
    if last_idx is None or last_idx < len(lines) // 2:
        return text
    if any(ln.strip().startswith("#") for ln in lines[last_idx + 1 :]):
        return text
    if not _looks_like_appended_changelog(lines[last_idx:]):
        return text
    return "\n".join(lines[:last_idx]).rstrip()


def _has_real_body(text: str) -> bool:
    if any(_looks_like_body_start(ln) for ln in text.split("\n")):
        return True
    non_blank = [ln for ln in text.split("\n") if ln.strip()]
    return len(non_blank) >= 3 and not all(_PREAMBLE_RE.match(ln.strip()) for ln in non_blank)


def sanitize_rewritten_body(raw: str, original_body: str | None = None) -> str:
    del original_body
    if raw is None or not str(raw).strip():
        raise ValueError("Rewritten skill body is empty or whitespace-only")

    text = str(raw).strip()
    text = _strip_whole_body_fence(text).strip()
    text = _strip_leading_preamble(text).strip()
    text = _strip_trailing_changelog(text).strip()

    if not text:
        raise ValueError("Rewritten skill body is empty after sanitization")
    if not _has_real_body(text):
        raise ValueError("Rewritten skill body still looks like preamble / has no real body")
    return text
