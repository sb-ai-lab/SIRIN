"""Split manifest loading and leakage enforcement.

A *split manifest* partitions a benchmark into train/val/test pools with a
leakage policy attached. Experiment code must load a manifest at the start of
a run and call only its scope-restricted accessors so that test data never
leaks into skill evolution, selection, or stopping.

Typical usage::

    from evolution.splits import SplitManifest

    manifest = SplitManifest.load("evolution/splits/skillsbench/manifests/domain-stratified-v1.json")
    train = manifest.tasks(scope="skill_evolution")   # == train
    dev   = manifest.tasks(scope="dev")               # == train + val
    test  = manifest.tasks(scope="reporting")         # == test

    # Record manifest identity in every run result so reports cannot silently
    # mix splits.
    result["manifest_name"] = manifest.name
    result["manifest_sha"]  = manifest.sha256
"""

from evolution.splits.manifest import (
    LeakageError,
    SplitManifest,
    assert_no_leakage,
    validate_split_references,
)

__all__ = ["SplitManifest", "LeakageError", "assert_no_leakage", "validate_split_references"]
