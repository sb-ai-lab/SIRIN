"""Regression guard: the Streamlit shell must import without loading the ML stack.

Cold-starting the UI used to pay for ``import vllm``/``torch``/``transformers`` (tens of seconds)
before rendering anything. The heavy backends must load lazily, on first real model use only.
"""

import json
import subprocess
import sys
from pathlib import Path


_REPO_ROOT = Path(__file__).resolve().parents[1]

_PROBE = """
import json
import sys

import sirin
import sirin.ui.streamlit_app
import sirin.ui.workspace
from sirin.ui.workspace import RunEngine, WorkspaceController  # lazy exports must stay light
import sirin.inference.adapters  # bare package import must not pull any backend

heavy = sorted(m for m in ('torch', 'vllm', 'transformers') if m in sys.modules)
print(json.dumps({'sirin_file': sirin.__file__, 'heavy': heavy}))
"""


def test_ui_shell_imports_without_ml_stack():
    result = subprocess.run(
        [sys.executable, '-c', _PROBE],
        cwd=_REPO_ROOT,  # ensure this repo's sirin wins over any site-packages install
        capture_output=True,
        text=True,
        timeout=300,
    )

    assert result.returncode == 0, result.stderr
    report = json.loads(result.stdout.strip().splitlines()[-1])
    assert Path(report['sirin_file']).is_relative_to(_REPO_ROOT), (
        'probe imported a sirin from outside this repo: ' + report['sirin_file']
    )
    assert report['heavy'] == [], (
        'importing the UI shell loaded heavy ML modules: ' + ', '.join(report['heavy'])
    )
