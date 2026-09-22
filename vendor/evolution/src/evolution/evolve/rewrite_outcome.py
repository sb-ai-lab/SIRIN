"""Structured outcome returned by :func:`rewrite_skill_with_audit`.

The CLI and workflow adapters consume :class:`RewriteOutcome` and write the
``rewrite-audit-v1`` JSON sidecar so callers can read the rejection reason
directly rather than scraping stdout.
"""

from __future__ import annotations

from dataclasses import dataclass

# Controlled candidate outcomes — adapter trusts the audit JSON, evo
# rewrite exits 0.  Any value not in this set is treated by the CLI as an
# internal contract violation and triggers rc!=0.
PROMOTED_ELIGIBLE = "promoted_eligible"
NO_OP_TEXT = "no_op_text"
NO_OP_FILE_EDIT = "no_op_file_edit"
LOW_CONFIDENCE_REFLECTION = "low_confidence_reflection"
LEAK_REJECTED = "leak_rejected"
SIZE_VIOLATION = "size_violation"
SANITIZE_ERROR = "sanitize_error"
TRUNCATED_REWRITE = "truncated_rewrite"
CANDIDATE_INVALID_EXTRA_FILES = "candidate_invalid_extra_files"
CANDIDATE_INVALID_SYMLINK = "candidate_invalid_symlink"
CANDIDATE_INVALID_HIDDEN_FILE = "candidate_invalid_hidden_file"
CANDIDATE_INVALID_PATH_ESCAPE = "candidate_invalid_path_escape"
CANDIDATE_INVALID_FRONTMATTER_CORRUPT = "candidate_invalid_frontmatter_corrupt"
CANDIDATE_INVALID_NEW_HEADING = "candidate_invalid_new_heading"
CANDIDATE_EDIT_BUDGET_EXCEEDED = "candidate_edit_budget_exceeded"
EDIT_OPS_PARSE_ERROR = "edit_ops_parse_error"
REWRITE_ERROR_CODEX = "rewrite_error_codex"
REWRITE_ERROR_BACKEND = "rewrite_error_backend"

# Internal contract violation — CLI raises and exits rc!=0.
REWRITE_ERROR_INTERNAL = "rewrite_error_internal"

CONTROLLED_STATUSES: frozenset[str] = frozenset(
    {
        PROMOTED_ELIGIBLE,
        NO_OP_TEXT,
        NO_OP_FILE_EDIT,
        LOW_CONFIDENCE_REFLECTION,
        LEAK_REJECTED,
        SIZE_VIOLATION,
        SANITIZE_ERROR,
        TRUNCATED_REWRITE,
        CANDIDATE_INVALID_EXTRA_FILES,
        CANDIDATE_INVALID_SYMLINK,
        CANDIDATE_INVALID_HIDDEN_FILE,
        CANDIDATE_INVALID_PATH_ESCAPE,
        CANDIDATE_INVALID_FRONTMATTER_CORRUPT,
        CANDIDATE_INVALID_NEW_HEADING,
        CANDIDATE_EDIT_BUDGET_EXCEEDED,
        EDIT_OPS_PARSE_ERROR,
        REWRITE_ERROR_CODEX,
        REWRITE_ERROR_BACKEND,
    }
)


@dataclass(slots=True)
class RewriteOutcome:
    """Structured result of one rewrite invocation.

    ``body`` is what the caller commits — the candidate body on a
    controlled success, the parent body on any rejection.
    ``candidate_status`` is the single source of truth for what
    happened; the CLI mirrors it to ``gate_reason`` in the audit JSON.
    """

    body: str
    candidate_status: str
    reason: str
    preservation: dict | None
    codex_usage: dict | None
    candidate_debug_dir: str | None
    model_id: str
    parent_body: str
    candidate_body_raw: str | None
    codex_diagnostics: dict | None = None
    tokens_used: int | None = None
    # t34v10 quality-spike provenance — populated by the file-edit path so
    # downstream analysis cannot confuse the rewrite's actual parent with an
    # unrelated _roots version. Optional on text-return path (fields stay
    # None when the rewriter didn't compute them).
    parent_skill_path: str | None = None
    parent_body_sha256: str | None = None
    candidate_body_sha256: str | None = None
    computed_churn: float | None = None
    new_headings: list[str] | None = None
    edit_budget_frac: float | None = None
    # Additive rewrite-audit-v1 evidence.  Older audit readers can ignore it.
    edit_brake: dict | None = None
    rewrite_attempts: list[dict] | None = None
    raw_body_sha256: str | None = None
