"""Language metric import behavior."""

import os
import subprocess
import sys


def test_language_metrics_do_not_download_nltk_data_at_import():
    script = """
import nltk

def fail_download(*args, **kwargs):
    raise AssertionError("nltk.download called at import time")

nltk.download = fail_download
import sirin.metrics.language
"""
    result = subprocess.run(
        [sys.executable, '-c', script],
        env={**os.environ, 'PYTHONPATH': os.getcwd()},
        capture_output=True,
        text=True,
        timeout=60,
    )
    assert result.returncode == 0, result.stderr
