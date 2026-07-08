"""Tests moved from sirin/ui/visualizers.py demo block."""

import pytest

from sirin.ui.visualizers import score_heatmap


def test_score_heatmap_escapes_html():
    if score_heatmap is None:
        pytest.skip("score_heatmap unavailable because UI helpers could not be imported")
    rendered = score_heatmap('<bad>&ok', [0.9, 0.1])
    assert '&lt;' in rendered
    assert '<bad>' not in rendered
