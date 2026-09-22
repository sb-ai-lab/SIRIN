"""SplitManifest: load split JSON and enforce leakage scopes.

The manifest JSON is produced by `evolution/splits/<source>/build_splits.py`.
At runtime we only need a small surface:

* read-only accessors for the train/val/test task pools,
* a cryptographic identity (`sha256`) so result files cannot silently mix
  splits,
* guard helpers that raise `LeakageError` when a caller accidentally exposes
  test tasks to skill evolution, selection, or stopping.

This module is intentionally stdlib-only so it can be imported early by the
CLI without pulling in optional evaluation dependencies.
"""

from __future__ import annotations

import hashlib
import json
from collections import Counter
from collections.abc import Iterable, Mapping
from dataclasses import dataclass, field
from pathlib import Path

Scope = str
SKILL_EVOLUTION: Scope = "skill_evolution"  # train-only
DEV: Scope = "dev"  # train + val
REPORTING: Scope = "reporting"  # test-only
ALL: Scope = "all"  # train + val + test


class LeakageError(RuntimeError):
    """Raised when a scope violation is detected at runtime."""


def validate_split_references(
    train: Iterable[str],
    val: Iterable[str],
    test: Iterable[str],
    *,
    require_nonempty: bool = False,
) -> None:
    """Require unique, pairwise-disjoint train/validation/test references."""
    pools = {"train": list(train), "val": list(val), "test": list(test)}
    for split, refs in pools.items():
        duplicates = sorted(ref for ref, count in Counter(refs).items() if count > 1)
        if duplicates:
            raise ValueError(f"Duplicate {split} task reference(s): {duplicates}")
        if require_nonempty and not refs:
            raise ValueError(f"{split} task references must not be empty")
    names = tuple(pools)
    for index, left in enumerate(names):
        for right in names[index + 1 :]:
            overlap = sorted(set(pools[left]) & set(pools[right]))
            if overlap:
                raise ValueError(f"{left}/{right} split overlap: {overlap}")


@dataclass(frozen=True)
class TaskRecord:
    """One task as it appears in a manifest."""

    id: str
    split: str
    domain_original: str
    domain_norm: str
    difficulty: str
    modality: tuple[str, ...]
    skills: tuple[str, ...]
    group: str | None
    tags: tuple[str, ...] = ()

    @classmethod
    def from_dict(cls, d: Mapping) -> TaskRecord:
        return cls(
            id=d["id"],
            split=d["split"],
            domain_original=d.get("domain_original", ""),
            domain_norm=d.get("domain_norm", ""),
            difficulty=d.get("difficulty", ""),
            modality=tuple(d.get("modality", []) or []),
            skills=tuple(d.get("skills", []) or []),
            group=d.get("group"),
            tags=tuple(d.get("tags", []) or []),
        )


@dataclass
class SplitManifest:
    """A loaded split manifest with scope-restricted accessors.

    Prefer `SplitManifest.load()` over constructing directly.
    """

    path: Path
    raw: dict
    sha256: str
    _records: list[TaskRecord] = field(default_factory=list)

    # ------------------------------------------------------------------
    # Construction
    # ------------------------------------------------------------------

    @classmethod
    def load(cls, path: str | Path) -> SplitManifest:
        p = Path(path).resolve()
        if not p.exists():
            raise FileNotFoundError(f"Manifest not found: {p}")
        text = p.read_text(encoding="utf-8")
        sha = hashlib.sha256(text.encode("utf-8")).hexdigest()
        raw = json.loads(text)
        if not isinstance(raw, dict):
            raise ValueError("Manifest root must be an object")
        if "tasks" not in raw:
            raise ValueError("Manifest must contain 'tasks'")
        tasks = raw["tasks"]
        if not isinstance(tasks, list):
            raise ValueError("Manifest 'tasks' must be a list")

        records: list[TaskRecord] = []
        seen: set[str] = set()
        actual = {"train": 0, "val": 0, "test": 0}
        for index, item in enumerate(tasks):
            if not isinstance(item, dict):
                raise ValueError(f"Manifest task at index {index} must be an object")
            task_id = item.get("id")
            if not isinstance(task_id, str) or not task_id.strip():
                raise ValueError("Manifest task IDs must be non-empty strings")
            if task_id in seen:
                raise ValueError(f"Duplicate manifest task ID: {task_id!r}")
            seen.add(task_id)
            split = item.get("split")
            if not isinstance(split, str) or split not in actual:
                raise ValueError(
                    f"Unknown split {split!r} for task {task_id!r}; expected train, val, or test"
                )
            actual[split] += 1
            records.append(TaskRecord.from_dict(item))

        if "counts" not in raw:
            raise ValueError("Manifest must contain 'counts'")
        declared = raw["counts"]
        if not isinstance(declared, dict):
            raise ValueError("Manifest 'counts' must be an object")
        for split, actual_count in actual.items():
            if split not in declared:
                continue
            declared_count = declared[split]
            if (
                isinstance(declared_count, bool)
                or not isinstance(declared_count, int)
                or declared_count < 0
            ):
                raise ValueError(f"Manifest count for {split!r} must be a non-negative integer")
            if declared_count != actual_count:
                raise ValueError(
                    f"Manifest count for {split!r} is {declared_count}, "
                    f"but {actual_count} task record(s) were found"
                )
        if not actual.keys() <= declared.keys():
            raise ValueError("Manifest counts must declare train, val, and test")
        return cls(path=p, raw=raw, sha256=sha, _records=records)

    # ------------------------------------------------------------------
    # Identity / metadata
    # ------------------------------------------------------------------

    @property
    def name(self) -> str:
        return self.raw.get("name", self.path.stem)

    @property
    def source(self) -> str:
        return self.raw.get("source", "")

    @property
    def source_commit(self) -> str:
        return self.raw.get("source_commit", "")

    @property
    def seed(self) -> int:
        return int(self.raw.get("seed", 0))

    @property
    def counts(self) -> dict[str, int]:
        return dict(self.raw.get("counts", {}))

    @property
    def policy(self) -> dict:
        return dict(self.raw.get("policy", {}))

    @property
    def excluded_tasks(self) -> list[dict]:
        return list(self.raw.get("excluded_tasks", []) or [])

    # ------------------------------------------------------------------
    # Scope-restricted accessors
    # ------------------------------------------------------------------

    def train_ids(self) -> set[str]:
        return {r.id for r in self._records if r.split == "train"}

    def val_ids(self) -> set[str]:
        return {r.id for r in self._records if r.split == "val"}

    def test_ids(self) -> set[str]:
        return {r.id for r in self._records if r.split == "test"}

    def all_ids(self) -> set[str]:
        return {r.id for r in self._records}

    def ids(self, scope: Scope = ALL) -> set[str]:
        if scope == SKILL_EVOLUTION:
            return self.train_ids()
        if scope == DEV:
            return self.train_ids() | self.val_ids()
        if scope == REPORTING:
            return self.test_ids()
        if scope == ALL:
            return self.all_ids()
        raise ValueError(
            f"Unknown scope {scope!r}; use 'skill_evolution', 'dev', 'reporting', or 'all'."
        )

    def records(self, scope: Scope = ALL) -> list[TaskRecord]:
        allowed = self.ids(scope)
        return [r for r in self._records if r.id in allowed]

    def tasks(self, scope: Scope = ALL) -> list[str]:
        """Sorted list of task ids in the requested scope."""
        return sorted(self.ids(scope))

    def record(self, task_id: str) -> TaskRecord:
        for r in self._records:
            if r.id == task_id:
                return r
        raise KeyError(f"Task {task_id!r} not in manifest {self.name!r}")

    # ------------------------------------------------------------------
    # Leakage guards
    # ------------------------------------------------------------------

    def assert_no_leakage(
        self,
        candidate_ids: Iterable[str],
        *,
        scope: Scope,
        context: str = "",
    ) -> None:
        """Fail if `candidate_ids` contains any task outside the given scope.

        Call this at the boundary of any code path that consumes task rewards
        (skill evolution, selection, stopping). Wrap the call site so the
        error message names the violator:

            manifest.assert_no_leakage(
                evolution_task_ids,
                scope="skill_evolution",
                context="evolution loop",
            )
        """
        assert_no_leakage(self, candidate_ids, scope=scope, context=context)

    # ------------------------------------------------------------------
    # Pretty-printing for logs
    # ------------------------------------------------------------------

    def summary(self) -> dict:
        return {
            "name": self.name,
            "source": self.source,
            "source_commit": self.source_commit,
            "sha256": self.sha256,
            "counts": self.counts,
            "policy": self.policy,
        }


def assert_no_leakage(
    manifest: SplitManifest,
    candidate_ids: Iterable[str],
    *,
    scope: Scope,
    context: str = "",
) -> None:
    """Free-function form of `SplitManifest.assert_no_leakage`."""
    allowed = manifest.ids(scope)
    illegal = [cid for cid in candidate_ids if cid not in allowed]
    if not illegal:
        return
    # Categorize by split for a more actionable error message.
    train, val, test = manifest.train_ids(), manifest.val_ids(), manifest.test_ids()
    by_split: dict[str, list[str]] = {"train": [], "val": [], "test": [], "unknown": []}
    for cid in illegal:
        if cid in train:
            by_split["train"].append(cid)
        elif cid in val:
            by_split["val"].append(cid)
        elif cid in test:
            by_split["test"].append(cid)
        else:
            by_split["unknown"].append(cid)
    parts = []
    for split, ids_ in by_split.items():
        if ids_:
            parts.append(f"{split}={sorted(ids_)}")
    raise LeakageError(
        f"Manifest {manifest.name!r} ({manifest.sha256[:12]}) scope={scope!r}"
        + (f" context={context!r}" if context else "")
        + f": {len(illegal)} out-of-scope task id(s): "
        + "; ".join(parts)
    )
