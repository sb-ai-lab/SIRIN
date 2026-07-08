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
