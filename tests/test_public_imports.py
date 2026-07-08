"""Public import smoke tests."""

import os
import subprocess
import sys
from types import SimpleNamespace


def test_hybrid_cache_compat_uses_dynamic_cache():
    from sirin.detection.judging import _ensure_transformers_hybrid_cache

    module = SimpleNamespace(DynamicCache=object())
    _ensure_transformers_hybrid_cache(module)
    assert module.HybridCache is module.DynamicCache


def test_judging_public_import_patches_missing_hybrid_cache():
    env = {**os.environ, 'PYTHONPATH': os.getcwd()}
    script = """
import sys
import transformers

if hasattr(transformers, 'HybridCache'):
    delattr(transformers, 'HybridCache')

for name in list(sys.modules):
    if name == 'peft' or name.startswith('peft.') or name.startswith('sirin.detection.judging'):
        sys.modules.pop(name, None)

from sirin.detection.judging import JudgePipeline, SequenceDecoderJudge, TokenDecoderJudge
assert JudgePipeline and SequenceDecoderJudge and TokenDecoderJudge
assert hasattr(transformers, 'HybridCache')
"""
    result = subprocess.run(
        [sys.executable, '-c', script],
        env=env,
        capture_output=True,
        text=True,
        timeout=60,
    )
    assert result.returncode == 0, result.stderr
