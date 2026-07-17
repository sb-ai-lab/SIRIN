"""Guards for the static 'Add a detector' recipes (PR-12): the code samples must be real."""

import os
import subprocess
import sys
from pathlib import Path

from sirin.ui.workspace.recipes import detector_recipes

REPO_ROOT = Path(__file__).resolve().parents[1]


def test_every_recipe_code_sample_compiles():
    for recipe in detector_recipes():
        # compile() is the import-check: a syntax error in a copy-paste snippet ships broken docs.
        compile(recipe.code, f'<recipe:{recipe.id}>', 'exec')


def test_recipes_reference_the_real_public_api():
    recipes = {recipe.id: recipe for recipe in detector_recipes()}

    judge = recipes['wrap_openai_judge'].code
    assert 'from sirin.detection.judging import SequenceOpenAIJudge' in judge
    assert 'OpenAIConfig(' in judge
    # The wrapped judge prompt must carry the {sample} slot (same class of bug PR-10 fixed upstream).
    assert '{sample}' in judge

    probe = recipes['train_token_probe'].code
    assert 'from sirin.metrics.span import' in probe
    assert 'character_scores(' in probe

    preset = recipes['register_preset'].code
    assert 'from sirin.ui.presets import PRESETS, Preset' in preset
    assert 'PRESETS[' in preset


def test_training_recipe_flags_exist_in_the_cli_help():
    recipe = next(r for r in detector_recipes() if r.id == 'train_token_probe')
    assert recipe.reference is not None
    script = REPO_ROOT / recipe.reference
    assert script.is_file(), script

    env = {**os.environ, 'PYTHONPATH': str(REPO_ROOT), 'CUDA_VISIBLE_DEVICES': ''}
    result = subprocess.run(
        [sys.executable, str(script), '--help'],
        cwd=str(REPO_ROOT),
        env=env,
        capture_output=True,
        text=True,
        timeout=300,
    )
    help_text = result.stdout + result.stderr

    for flag in ('--dataset', '--model-id', '--layers', '--checkpoint-dir'):
        assert flag in recipe.code, flag  # the recipe uses it
        assert flag in help_text, flag  # and the script actually defines it
