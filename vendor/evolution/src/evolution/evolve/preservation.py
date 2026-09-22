"""Parent-vs-candidate preservation scoring for audited skill rewrites.

Five metrics, all pure-stdlib (``difflib`` + ``re``):

* ``heading_retention`` — fraction of parent H2/H3 headings that survive
  in the candidate (fuzzy-matched).
* ``section_preservation`` — mass-weighted mean over matched sections of
  the fraction of non-empty parent lines that are byte-identical in the
  candidate (computed from ``SequenceMatcher.get_opcodes()``).
* ``structure_drift`` — number of parent sections without a candidate
  match plus number of candidate sections without a parent match.
* ``frontmatter_semantic_equality`` — Pydantic-normalised frontmatter
  equality, measured **before** reattach so ``False`` is the useful
  "codex tried to mutate frontmatter" signal.
* ``whole_body_seqmatch_ratio`` — historical ``difflib.SequenceMatcher``
  ratio across the full body; kept for back-compat with t34v7 numbers.

Fuzzy heading match uses ``SequenceMatcher.ratio() >= 0.85`` — a
SequenceMatcher ratio threshold, **not** Levenshtein.
"""

from __future__ import annotations

import re
from difflib import SequenceMatcher

_HEADING_RE = re.compile(r"^(##+)\s+(.*?)\s*$", re.MULTILINE)
_FUZZY_HEADING_RATIO = 0.85


def split_skill_body_by_heading(body: str) -> list[tuple[str, str]]:
    """Split ``body`` on H2/H3 markdown headings.

    Returns a list of ``(heading_text, section_body)``.  Lines before the
    first heading land in a leading ``("", prelude)`` entry, which keeps
    section-preservation symmetric when one side has a prelude and the
    other does not.
    """
    if not body:
        return [("", "")]
    matches = list(_HEADING_RE.finditer(body))
    if not matches:
        return [("", body)]
    sections: list[tuple[str, str]] = []
    prelude = body[: matches[0].start()]
    sections.append(("", prelude))
    for i, m in enumerate(matches):
        heading_text = m.group(2).strip()
        start = m.end()
        end = matches[i + 1].start() if i + 1 < len(matches) else len(body)
        section_body = body[start:end]
        sections.append((heading_text, section_body))
    return sections


def _fuzzy_match_heading(a: str, b: str) -> bool:
    """SequenceMatcher ratio threshold for heading equivalence.

    NOT Levenshtein — we deliberately avoid pulling in a third-party
    edit-distance dependency.  ``ratio()`` is monotone enough for the
    section-pairing use case.
    """
    return (
        SequenceMatcher(None, a.strip().lower(), b.strip().lower()).ratio() >= _FUZZY_HEADING_RATIO
    )


def _pair_sections(
    parent: list[tuple[str, str]],
    candidate: list[tuple[str, str]],
) -> tuple[list[tuple[int, int]], list[int], list[int]]:
    """Greedily pair parent sections with candidate sections by heading.

    Returns ``(pairs, unmatched_parent_idx, unmatched_candidate_idx)``.
    Greedy is fine here: section counts are small, and adjacency is
    informative — codex tends to edit-in-place rather than reorder.
    """
    pairs: list[tuple[int, int]] = []
    used_candidate: set[int] = set()
    unmatched_parent: list[int] = []
    for i, (p_head, _) in enumerate(parent):
        match_idx = None
        for j, (c_head, _) in enumerate(candidate):
            if j in used_candidate:
                continue
            if p_head == "" and c_head == "":
                match_idx = j
                break
            if _fuzzy_match_heading(p_head, c_head):
                match_idx = j
                break
        if match_idx is None:
            unmatched_parent.append(i)
        else:
            pairs.append((i, match_idx))
            used_candidate.add(match_idx)
    unmatched_candidate = [j for j in range(len(candidate)) if j not in used_candidate]
    return pairs, unmatched_parent, unmatched_candidate


def heading_retention(
    parent: list[tuple[str, str]],
    candidate: list[tuple[str, str]],
) -> float:
    """Fraction of named (non-prelude) parent headings present in candidate."""
    named_parent = [(i, h) for i, (h, _) in enumerate(parent) if h]
    if not named_parent:
        return 1.0
    named_candidate = [c for c, _ in candidate if c]
    retained = sum(
        1 for _i, h in named_parent if any(_fuzzy_match_heading(h, ch) for ch in named_candidate)
    )
    return retained / len(named_parent)


def _non_empty_lines(text: str) -> list[str]:
    return [ln for ln in text.splitlines() if ln.strip()]


def section_preservation(
    parent: list[tuple[str, str]],
    candidate: list[tuple[str, str]],
) -> float:
    """Mass-weighted mean of equal-line fraction across matched sections.

    For each parent section paired with a candidate section, run
    ``SequenceMatcher.get_opcodes()`` on the non-empty-line lists; count
    ``equal`` opcodes' parent-side line count; divide by total
    non-empty parent lines in that section.  Mass-weight the
    per-section ratios by parent non-empty line count.

    Returns 1.0 for an empty parent (nothing to preserve = vacuously
    preserved) and 0.0 if no sections match.
    """
    pairs, _, _ = _pair_sections(parent, candidate)
    if not pairs:
        return 0.0
    total_lines = 0
    equal_lines = 0
    for p_idx, c_idx in pairs:
        p_lines = _non_empty_lines(parent[p_idx][1])
        c_lines = _non_empty_lines(candidate[c_idx][1])
        if not p_lines:
            continue
        total_lines += len(p_lines)
        opcodes = SequenceMatcher(None, p_lines, c_lines).get_opcodes()
        for tag, i1, i2, _j1, _j2 in opcodes:
            if tag == "equal":
                equal_lines += i2 - i1
    if total_lines == 0:
        return 1.0
    return equal_lines / total_lines


def structure_drift(
    parent: list[tuple[str, str]],
    candidate: list[tuple[str, str]],
) -> int:
    """Count of unmatched parent + unmatched candidate sections."""
    _pairs, unmatched_parent, unmatched_candidate = _pair_sections(parent, candidate)
    # Prelude entries with empty headings on both sides are not real "sections"
    # for drift accounting; filter them out.
    drift_parent = sum(1 for i in unmatched_parent if parent[i][0])
    drift_candidate = sum(1 for j in unmatched_candidate if candidate[j][0])
    return drift_parent + drift_candidate


def frontmatter_semantic_equality(parent_fm: dict, candidate_fm: dict) -> bool:
    """Equality of frontmatter field sets after Pydantic normalisation.

    Both inputs go through ``SkillFrontmatter.model_validate(...).model_dump(mode="python")``;
    the resulting dicts are compared verbatim.  Pydantic drops unknown
    keys, so this metric only catches *known-field* drift — the
    intentional gap is documented in the unit test
    ``test_frontmatter_raw_keyset_diff_before_normalisation``.

    Measured BEFORE any reattach so ``False`` is the useful "codex tried
    to mutate frontmatter" signal.  The runtime safety net (frontmatter
    reattach) is independent of this metric.
    """
    from evolution.core.models import SkillFrontmatter

    try:
        p_norm = SkillFrontmatter.model_validate(parent_fm).model_dump(mode="python")
        c_norm = SkillFrontmatter.model_validate(candidate_fm).model_dump(mode="python")
    except Exception:
        # Either side unparseable → not equal in any useful sense.
        return False
    return p_norm == c_norm


def whole_body_seqmatch_ratio(parent_body: str, candidate_body: str) -> float:
    """``SequenceMatcher.ratio()`` across the full body strings."""
    if not parent_body and not candidate_body:
        return 1.0
    return SequenceMatcher(None, parent_body, candidate_body).ratio()


def score_preservation(
    parent_body: str,
    candidate_body: str,
    parent_fm: dict,
    candidate_fm: dict,
) -> dict:
    """Five-field preservation score matching the rewrite-audit-v1 schema.

    ``candidate_fm`` MUST be the frontmatter as observed BEFORE any
    reattach to the parent's frontmatter.
    """
    parent_sections = split_skill_body_by_heading(parent_body)
    candidate_sections = split_skill_body_by_heading(candidate_body)
    return {
        "heading_retention": heading_retention(parent_sections, candidate_sections),
        "section_preservation": section_preservation(parent_sections, candidate_sections),
        "structure_drift": structure_drift(parent_sections, candidate_sections),
        "frontmatter_semantic_equality": frontmatter_semantic_equality(parent_fm, candidate_fm),
        "whole_body_seqmatch_ratio": whole_body_seqmatch_ratio(parent_body, candidate_body),
    }
