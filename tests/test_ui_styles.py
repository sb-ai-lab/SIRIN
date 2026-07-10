"""Tests moved from sirin/ui/styles.py demo block."""

from sirin.ui.styles import inject_global_styles


def test_inject_global_styles_substitutes_placeholders():
    class Stub:
        def __init__(self) -> None:
            self.calls: list[str] = []

        def html(self, s) -> None:
            self.calls.append(s)

    stub = Stub()
    inject_global_styles(stub, motion='subtle')
    captured = stub.calls[0]
    assert isinstance(captured, str) and captured.strip()
    assert '@keyframes sirin-drift-subtle' in captured
    assert 'data:image/jpeg;base64,' in captured
    assert 'stApp' in captured
    assert '@@' not in captured

    stub_static = Stub()
    inject_global_styles(stub_static, motion='static')
    assert 'animation: none' in stub_static.calls[0]


def test_inject_global_styles_light_theme():
    class Stub:
        def __init__(self) -> None:
            self.calls: list[str] = []

        def html(self, s) -> None:
            self.calls.append(s)

    stub = Stub()
    inject_global_styles(stub, theme='light')
    captured = stub.calls[0]
    assert '@@' not in captured
    assert 'color-scheme: light' in captured

    stub_dark = Stub()
    inject_global_styles(stub_dark, theme='dark')
    assert 'color-scheme: dark' in stub_dark.calls[0]


def test_inject_global_styles_keeps_input_caret_visible():
    class Stub:
        def __init__(self) -> None:
            self.calls: list[str] = []

        def html(self, s) -> None:
            self.calls.append(s)

    stub = Stub()
    inject_global_styles(stub, theme='light')

    assert 'caret-color: var(--sirin-text)' in stub.calls[0]


def test_theme_contract_holds():
    from sirin.ui import styles

    keysets = [frozenset(t) for t in styles.THEMES.values()]
    assert keysets and all(k == keysets[0] for k in keysets)  # every theme defines the same tokens
    placeholders = set(styles._THEME_PLACEHOLDER_RE.findall(styles._CSS_TEMPLATE))
    assert placeholders <= (keysets[0] | styles._RUNTIME_KEYS)  # no orphan @@placeholder@@
    styles._validate_theme_contract()  # real themes pass


def test_theme_contract_rejects_partial_theme(monkeypatch):
    import pytest

    from sirin.ui import styles

    monkeypatch.setitem(styles.THEMES, 'bad', {'bg': '#000'})  # missing every other token
    with pytest.raises(ValueError):
        styles._validate_theme_contract()
