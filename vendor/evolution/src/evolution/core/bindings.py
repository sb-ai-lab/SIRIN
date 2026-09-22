"""Resolve exact skill content while keeping lineage state at the skill root."""

from __future__ import annotations

from collections.abc import Iterable
from dataclasses import dataclass, replace
from pathlib import Path

from evolution.core.models import ContainerSkillRef, Skill
from evolution.core.parser import load_skill
from evolution.core.store import SkillStore
from evolution.lineage.tracker import LineageTracker
from evolution.lineage.version import VersionStore, hash_managed_tree


@dataclass(frozen=True)
class SkillBinding:
    """Exact injected skill plus its canonical owner and provenance."""

    name: str
    skill: Skill
    owner: Skill
    version: str
    sha256: str
    source: str
    container: str | None = None
    snapshot: str | None = None

    @classmethod
    def current(cls, owner: Skill, *, name: str | None = None) -> SkillBinding:
        version = LineageTracker(owner).current_version
        versions = VersionStore(owner)
        if not versions.exists(version):
            raise KeyError(
                f"Skill {name or owner.path.name!r} active version {version!r} has no snapshot; "
                "commit it first or explicitly select working content"
            )
        return cls.pinned(owner, version, name=name, source="active")

    @classmethod
    def working(cls, skill: Skill, *, name: str | None = None) -> SkillBinding:
        digest = hash_managed_tree(skill.path)
        return cls(
            name or skill.path.name,
            skill,
            skill,
            f"working@{digest[:12]}",
            digest,
            "working",
        )

    @classmethod
    def pinned(
        cls,
        owner: Skill,
        version: str,
        *,
        name: str | None = None,
        source: str = "version",
        container: str | None = None,
        snapshot: str | None = None,
        expected_sha256: str | None = None,
    ) -> SkillBinding:
        versions = VersionStore(owner)
        selected = versions.load(version)
        digest = versions.digest(version)
        if expected_sha256 is not None and expected_sha256 != digest:
            raise ValueError(
                f"Skill {name or owner.path.name!r} version {version!r} hash mismatch: "
                f"expected {expected_sha256}, got {digest}"
            )
        return cls(
            name or owner.path.name,
            selected,
            owner,
            version,
            digest,
            source,
            container,
            snapshot,
        )

    @classmethod
    def from_skill(cls, skill: Skill) -> SkillBinding:
        """Adapt explicit content while retaining a snapshot's canonical owner."""

        if skill.path.parent.name == "versions" and skill.path.parent.parent.name == ".evolution":
            owner = load_skill(skill.path.parent.parent.parent)
            return cls.pinned(owner, skill.path.name, name=owner.path.name)
        return cls.working(skill, name=skill.path.name)

    def provenance(self) -> dict[str, str]:
        data = {
            "name": self.name,
            "version": self.version,
            "sha256": self.sha256,
            "source": self.source,
        }
        if self.container:
            data["container"] = self.container
        if self.snapshot:
            data["snapshot"] = self.snapshot
        return data


def resolve_skill_bindings(
    requirements: Iterable[str | ContainerSkillRef],
    *,
    store: SkillStore,
    project_dir: str | Path,
    user_dir: str | Path | None = None,
    snapshot: str | None = None,
    skill_version: str | None = None,
    working: bool = False,
) -> list[SkillBinding]:
    """Resolve skill or container requirements to exact content."""

    refs = [
        item if isinstance(item, ContainerSkillRef) else ContainerSkillRef(name=str(item))
        for item in requirements
    ]
    from evolution.core.containers import ContainerStore

    containers = ContainerStore(project_dir=project_dir, user_dir=user_dir)
    selectors = sum(
        (bool(working), bool(snapshot), bool(skill_version), any(ref.version for ref in refs))
    )
    if selectors > 1:
        raise ValueError("version, snapshot, and working selectors cannot be combined")
    if skill_version and (len(refs) != 1 or containers.has(refs[0].name)):
        raise ValueError("skill_version requires exactly one individual skill")

    bindings: list[SkillBinding] = []
    for requirement in refs:
        if containers.has(requirement.name):
            if requirement.version:
                raise ValueError("a version selector requires an individual skill")
            for ref in containers.skill_refs(requirement.name, snapshot_label=snapshot):
                owner = store.get(ref.name)
                if ref.version:
                    bindings.append(
                        SkillBinding.pinned(
                            owner,
                            ref.version,
                            name=ref.name,
                            source="container-snapshot" if snapshot else "container-version",
                            container=requirement.name,
                            snapshot=snapshot,
                            expected_sha256=ref.sha256,
                        )
                    )
                else:
                    binding = (
                        SkillBinding.working(owner, name=ref.name)
                        if working
                        else SkillBinding.current(owner, name=ref.name)
                    )
                    bindings.append(
                        replace(
                            binding,
                            source="container-working" if working else "container-active",
                            container=requirement.name,
                        )
                    )
            continue

        if snapshot:
            raise ValueError(
                f"Snapshot {snapshot!r} requires a container; {requirement.name!r} is a skill"
            )
        owner = store.get(requirement.name)
        version = skill_version or requirement.version
        bindings.append(
            SkillBinding.working(owner, name=requirement.name)
            if working
            else SkillBinding.pinned(
                owner,
                version,
                name=requirement.name,
                expected_sha256=requirement.sha256,
            )
            if version
            else SkillBinding.current(owner, name=requirement.name)
        )

    unique: list[SkillBinding] = []
    by_owner: dict[Path, SkillBinding] = {}
    for binding in bindings:
        owner_path = binding.owner.path.resolve()
        previous = by_owner.get(owner_path)
        if previous is None:
            by_owner[owner_path] = binding
            unique.append(binding)
            continue
        if previous.version != binding.version or previous.sha256 != binding.sha256:
            raise ValueError(
                f"Conflicting pins for skill {binding.name!r}: "
                f"{previous.version}@{previous.sha256[:12]} and "
                f"{binding.version}@{binding.sha256[:12]}"
            )
    return unique
