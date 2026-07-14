"""Stage (and optionally push) the hosted-demo Hugging Face Space tree.

Copies the exact repo subset the CPU Space needs into a staging directory, with
the deploy/hf-space files at the Space root, then self-checks the tree. Push
uploads the staged tree to the Space with huggingface_hub (HF_TOKEN from env).

    python scripts/dev/make_space.py --out /tmp/sirin-space
    python scripts/dev/make_space.py --out /tmp/sirin-space --push parchiev/SIRIN
"""
from __future__ import annotations

import argparse
import shutil
import subprocess
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parents[2]

# Runtime needs the package source (run-from-source dodges the wheel packaging
# gaps), the Streamlit theme config, and the packaging metadata for the
# editable no-deps install. lm-polygraph is uncertainty-only (hidden on the
# hosted profile) and 100+MB; checkpoints are probing-only (hidden).
IGNORE = shutil.ignore_patterns(
    '__pycache__', '*.pyc', 'lm-polygraph', 'node_modules', '.git'
)


def stage(out: Path) -> None:
    if out.exists():
        shutil.rmtree(out)
    out.mkdir(parents=True)
    shutil.copytree(REPO / 'sirin', out / 'sirin', ignore=IGNORE)
    shutil.copytree(REPO / '.streamlit', out / '.streamlit')
    shutil.copy2(REPO / 'pyproject.toml', out / 'pyproject.toml')
    for name in ('Dockerfile', 'requirements.txt', 'README.md', '.dockerignore'):
        shutil.copy2(REPO / 'deploy/hf-space' / name, out / name)
    # Repo files can carry mode 600/700; the Space's non-root user must read them.
    for path in out.rglob('*'):
        path.chmod(0o755 if path.is_dir() else 0o644)


def self_check(out: Path) -> None:
    required = [
        'sirin/ui/tokens.json',
        'sirin/ui/static/silk_bg.jpg',
        'sirin/ui/assets/psiloqa_span_seed_qwen35_4b.json',
        'sirin/ui/assets/judge_span_seed.json',
        'sirin/ui/assets/psiloqa_demo_cases.json',
        'sirin/ui/assets/ragtruth_demo_cases.json',
        'sirin/ui/assets/demo_cases.json',
        '.streamlit/config.toml',
        'Dockerfile',
        'requirements.txt',
    ]
    missing = [rel for rel in required if not (out / rel).exists()]
    assert not missing, f'staged tree is missing: {missing}'
    assert any((out / 'sirin/ui/workspace/frontend/build').glob('index-*.js')), (
        'component build assets missing'
    )
    assert not (out / 'sirin/detection/lm-polygraph').exists(), 'lm-polygraph leaked'
    # The staged tree must import without the repo on sys.path.
    probe = (
        'import sys; sys.path.insert(0, "."); '
        'import sirin.ui.demo_cases as d; '
        'assert len(d.load_demo_cases()) == 3'
    )
    subprocess.run(
        [sys.executable, '-c', probe], cwd=out, check=True
    )
    print(f'self-check ok: {sum(1 for _ in out.rglob("*") if _.is_file())} files staged')


def push(out: Path, space_id: str) -> None:
    from huggingface_hub import HfApi

    api = HfApi()  # HF_TOKEN from env
    api.upload_folder(
        repo_id=space_id,
        repo_type='space',
        folder_path=str(out),
        commit_message='Sync hosted demo (hosted profile + curated galleries)',
        delete_patterns=['sirin/**', '.streamlit/**'],
    )
    print(f'pushed to https://huggingface.co/spaces/{space_id}')


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--out', type=Path, required=True)
    parser.add_argument('--push', metavar='SPACE_ID', default=None)
    args = parser.parse_args()
    stage(args.out)
    self_check(args.out)
    if args.push:
        push(args.out, args.push)


if __name__ == '__main__':
    main()
