from pathlib import Path

import pytest

from sirin.ui import path_policy


def test_ui_path_policy_allows_configured_root(monkeypatch, tmp_path):
    root = tmp_path / 'root'
    root.mkdir()
    data = root / 'dataset.parquet'
    data.touch()
    monkeypatch.setenv('SIRIN_UI_DATA_ROOTS', str(root))
    monkeypatch.delenv('SIRIN_UI_TRUSTED_LOCAL', raising=False)

    assert path_policy.require_data_path(str(data)) == str(data.resolve())


def test_ui_path_policy_rejects_sibling_escape(monkeypatch, tmp_path):
    root = tmp_path / 'root'
    other = tmp_path / 'other'
    root.mkdir()
    other.mkdir()
    data = other / 'dataset.parquet'
    data.touch()
    monkeypatch.setenv('SIRIN_UI_DATA_ROOTS', str(root))
    monkeypatch.delenv('SIRIN_UI_TRUSTED_LOCAL', raising=False)

    with pytest.raises(ValueError, match='outside allowed UI data roots'):
        path_policy.require_data_path(str(root / '..' / 'other' / 'dataset.parquet'))


def test_ui_path_policy_rejects_symlink_escape(monkeypatch, tmp_path):
    root = tmp_path / 'root'
    other = tmp_path / 'other'
    root.mkdir()
    other.mkdir()
    target = other / 'dataset.parquet'
    target.touch()
    link = root / 'link.parquet'
    link.symlink_to(target)
    monkeypatch.setenv('SIRIN_UI_DATA_ROOTS', str(root))
    monkeypatch.delenv('SIRIN_UI_TRUSTED_LOCAL', raising=False)

    with pytest.raises(ValueError, match='outside allowed UI data roots'):
        path_policy.require_data_path(str(link))


def test_ui_path_policy_trusted_mode_bypasses_roots(monkeypatch, tmp_path):
    data = tmp_path / 'dataset.parquet'
    data.touch()
    monkeypatch.delenv('SIRIN_UI_DATA_ROOTS', raising=False)
    monkeypatch.setenv('SIRIN_UI_TRUSTED_LOCAL', '1')

    assert path_policy.require_data_path(str(data)) == str(data.resolve())


def test_ui_path_policy_blank_optional_path_stays_blank(monkeypatch):
    monkeypatch.delenv('SIRIN_UI_DATA_ROOTS', raising=False)
    monkeypatch.delenv('SIRIN_UI_TRUSTED_LOCAL', raising=False)

    assert path_policy.require_data_path('') == ''


def test_ui_path_policy_requires_checkpoint_root(monkeypatch, tmp_path):
    ckpt = tmp_path / 'ckpt'
    ckpt.mkdir()
    monkeypatch.delenv('SIRIN_UI_TRUSTED_LOCAL', raising=False)
    monkeypatch.delenv('SIRIN_UI_CHECKPOINT_ROOTS', raising=False)

    with pytest.raises(ValueError, match='No allowed roots configured'):
        path_policy.require_checkpoint_path(str(ckpt))
