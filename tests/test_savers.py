"""Tests for saver compatibility aliases."""


def test_legacy_torch_module_saver_alias_imports():
    from sirin.utils.savers import TorchModuleSaver, TorchModulelSaver

    assert TorchModulelSaver is TorchModuleSaver
