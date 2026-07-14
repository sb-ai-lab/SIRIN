"""Tests moved from sirin/ui/visualizers.py demo block."""

import pytest

from sirin.ui import visualizers
from sirin.ui.visualizers import publication_granularity_html, score_heatmap


def test_score_heatmap_escapes_html():
    if score_heatmap is None:
        pytest.skip(
            "score_heatmap unavailable because UI helpers could not be imported"
        )
    rendered = score_heatmap('<bad>&ok', [0.9, 0.1])
    assert '&lt;' in rendered
    assert '<bad>' not in rendered


def test_publication_granularity_html_renders_token_sentence_and_claim_lanes():
    rendered = publication_granularity_html(
        {
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
        }
    )

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


def test_threshold_span_mode_renders_flowing_merged_predicted_spans():
    answer = 'Safe <fact> then wrong place.'
    scores = [0.08] * len(answer)
    predictions = [0] * len(answer)
    for start, end, score in ((5, 11, 0.72), (17, 28, 0.91)):
        scores[start:end] = [score] * (end - start)
        predictions[start:end] = [1] * (end - start)

    rendered = publication_granularity_html(
        {
            'level': 'token',
            'display_mode': 'threshold-spans',
            'answer': answer,
            'scores': scores,
            'norm_scores': scores,
            'predictions': predictions,
            'threshold': 0.5417775511741638,
            'calibrated': False,
            'family': 'probing',
            'scale_label': 'raw linear-probe score',
        }
    )

    assert rendered.count('data-granularity="predicted-span"') == 2
    assert 'data-index="5" data-end="11"' in rendered
    assert 'data-index="17" data-end="28"' in rendered
    assert 'data-mean-score="0.720" data-max-score="0.720"' in rendered
    assert 'Safe ' in rendered
    assert '&lt;fact&gt;' in rendered
    assert ' then ' in rendered
    assert 'threshold 0.542' in rendered
    assert 'not a calibrated probability' in rendered
    assert 'Token-level signal' not in rendered
    assert 'Sentence-level summary' not in rendered


def test_publication_granularity_html_renders_sequence_broadcast_with_token_highlights():
    rendered = publication_granularity_html(
        {
            'level': 'sequence',
            'display_mode': 'sequence-broadcast',
            'answer': 'Visit Red Rocks. Then try Bluebird Theater.',
            'scores': [0.668, 0.668],
            'norm_scores': [0.668, 0.668],
            'calibrated': True,
            'scale_label': 'sequence TabPFN score',
            'signal_note': 'One calibrated sequence score covers the generated answer.',
        }
    )

    assert 'Response-level assessment' in rendered
    assert '>Answer<' in rendered
    assert 'not localized span evidence' in rendered
    assert 'data-attribution-scope="sequence"' in rendered
    assert 'data-granularity="token"' not in rendered
    assert 'data-score="0.668"' in rendered
    assert 'data-index="0"' in rendered
    assert 'data-end="5"' in rendered
    assert 'color:var(--sirin-text)' in rendered
    assert 'box-shadow:inset' in rendered
    assert 'sirin-token-strip' not in rendered


def test_sequence_broadcast_preserves_small_nonzero_scores():
    rendered = publication_granularity_html(
        {
            'level': 'sequence',
            'display_mode': 'sequence-broadcast',
            'answer': 'Grounded answer.',
            'scores': [0.00021516799441961232],
            'norm_scores': [0.00021516799441961232],
            'calibrated': True,
        }
    )

    assert '0.02%' in rendered


def test_recorded_case_renders_raw_score_without_invented_threshold():
    from sirin.ui.demo_cases import get_demo_case

    rendered = visualizers.publication_case_html(get_demo_case('681a1674'))

    assert 'score 0.9983' in rendered
    assert 'Recorded raw score' in rendered
    assert 'recorded OOF unfaithfulness score' in rendered
    assert 'nested grouped-OOF hidden-state logistic probe' in rendered
    assert 'title="threshold"' not in rendered
    assert 'TabPFN score' not in rendered


def test_live_case_setup_does_not_label_historical_detector_as_live():
    from sirin.ui.demo_cases import get_demo_case

    rendered = visualizers.publication_case_html(
        get_demo_case('07741c44'), include_result=False
    )

    assert 'Live run setup' in rendered
    assert 'detector selected in sidebar' in rendered
    assert 'training example approved for mechanics demonstration' in rendered
    assert 'Nested grouped-OOF hidden-state logistic probe' not in rendered


def test_recorded_token_case_renders_exact_relative_uncertainty_spans():
    case = {
        'sample_id': 'sports',
        'title': 'Competitive sports contradiction',
        'question': 'How many sports did I play competitively?',
        'prediction': '1 sport (tennis)',
        'detector': 'Maximum token probability',
        'evidence_excerpts': [
            {'label': 'Context 1', 'rank': 1, 'content': 'Competitive tennis.'},
            {'label': 'Context 2', 'rank': 2, 'content': 'Competitive swimming.'},
        ],
        'provenance': {'model': 'Qwen', 'run': 'recorded'},
        'token_trace': {
            'token_pieces': ['1', ' sport', ' (', 'ten', 'nis', ')'],
            'token_offsets': [[0, 1], [1, 7], [7, 9], [9, 12], [12, 15], [15, 16]],
            'raw_scores': [0.8, 0.6, 0.2, 0.3, 0.0, 0.1],
            'normalized_scores': [1.0, 0.75, 0.25, 0.375, 0.0, 0.125],
        },
    }

    rendered = visualizers.publication_case_html(case)

    assert rendered.count('data-granularity="token"') == 6
    assert 'data-index="1" data-end="7"' in rendered
    assert 'raw relative token uncertainty' in rendered
    assert 'No threshold or verdict.' in rendered
    assert 'not a probability' in rendered
    assert 'recorded OOF unfaithfulness score' not in rendered
    assert 'title="threshold"' not in rendered


def test_publication_granularity_html_escapes_and_marks_missing_scores():
    rendered = publication_granularity_html(
        {
            'answer': '<bad> A',
            'norm_scores': [0.9],
            'scores': [3.2],
            'calibrated': False,
            'family': 'uncertainty',
        }
    )

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

    visualizers.render_result(
        st,
        {
            'level': 'token',
            'answer': 'The answer',
            'scores': [0.1, 0.8],
            'norm_scores': [0.1, 0.8],
            'calibrated': True,
            'family': 'probing',
        },
    )

    html = ''.join(st.rendered)
    assert 'Token-level signal' in html
    assert 'Exact span boundary debug' in html
