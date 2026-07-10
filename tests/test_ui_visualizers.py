"""Tests moved from sirin/ui/visualizers.py demo block."""

import pytest

from sirin.ui import visualizers
from sirin.ui.visualizers import publication_granularity_html, score_heatmap


def test_score_heatmap_escapes_html():
    if score_heatmap is None:
        pytest.skip("score_heatmap unavailable because UI helpers could not be imported")
    rendered = score_heatmap('<bad>&ok', [0.9, 0.1])
    assert '&lt;' in rendered
    assert '<bad>' not in rendered


def test_publication_granularity_html_renders_token_sentence_and_claim_lanes():
    rendered = publication_granularity_html({
        'answer': 'The treaty was signed in 1809.',
        'norm_scores': [0.05, 0.1, 0.2, 0.35, 0.82, 0.91],
        'scores': [0.05, 0.1, 0.2, 0.35, 0.82, 0.91],
        'predictions': [0, 0, 0, 0, 1, 1],
        'claims': [
            {'fact': 'A treaty was signed.', 'prob': 0.2, 'pred': 0},
            {'fact': 'It was signed in 1809.', 'prob': 0.91, 'pred': 1},
        ],
        'calibrated': True,
        'family': 'probing',
    })

    assert 'Token-level signal' in rendered
    assert 'Sentence-level summary' in rendered
    assert 'Claim-level output' in rendered
    assert 'data-granularity="token"' in rendered
    assert 'data-granularity="sentence"' in rendered
    assert 'data-granularity="claim"' in rendered
    assert 'data-score="0.910"' in rendered
    assert 'higher detector signal' in rendered
    assert 'faithful' not in rendered.lower()
    assert 'unsupported' not in rendered.lower()


def test_publication_granularity_html_renders_sequence_broadcast_with_token_highlights():
    rendered = publication_granularity_html({
        'level': 'token',
        'display_mode': 'sequence-broadcast',
        'answer': 'Visit Red Rocks. Then try Bluebird Theater.',
        'scores': [0.668, 0.668],
        'norm_scores': [0.668, 0.668],
        'calibrated': True,
        'scale_label': 'sequence TabPFN score',
        'signal_note': 'One calibrated sequence score covers the generated answer.',
    })

    assert 'Output · Sequence Attribution' in rendered
    assert 'Highlighted answer tokens' in rendered
    assert 'Sentence coverage' in rendered
    assert 'data-granularity="token"' in rendered
    assert 'data-score="0.668"' in rendered
    assert 'data-index="0"' in rendered
    assert 'data-end="5"' in rendered
    assert 'color:var(--sirin-text)' in rendered
    assert 'box-shadow:inset' in rendered
    assert 'sirin-token-strip' not in rendered


def test_publication_granularity_html_escapes_and_marks_missing_scores():
    rendered = publication_granularity_html({
        'answer': '<bad> A',
        'norm_scores': [0.9],
        'scores': [3.2],
        'calibrated': False,
        'family': 'uncertainty',
    })

    assert '<bad>' not in rendered
    assert '&lt;bad&gt;' in rendered
    assert 'data-score="missing"' in rendered
    assert 'relative detector signal' in rendered
    assert 'not a probability' in rendered


def test_render_result_uses_publication_token_view_by_default():
    class FakeSt:
        def __init__(self):
            self.rendered = []

        def html(self, body):
            self.rendered.append(body)

        def expander(self, *args, **kwargs):
            return self

        def __enter__(self):
            return self

        def __exit__(self, *args):
            return False

        def write(self, body):
            self.rendered.append(body)

    st = FakeSt()

    visualizers.render_result(st, {
        'level': 'token',
        'answer': 'The answer',
        'scores': [0.1, 0.8],
        'norm_scores': [0.1, 0.8],
        'calibrated': True,
        'family': 'probing',
    })

    html = ''.join(st.rendered)
    assert 'Token-level signal' in html
    assert 'Exact span boundary debug' in html
