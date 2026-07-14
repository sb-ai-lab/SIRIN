from __future__ import annotations

import hashlib
import json
import math
from pathlib import Path
from typing import Any


_ASSET_PATH = Path(__file__).with_name('assets') / 'demo_cases.json'
_PSILOQA_SPAN_ASSET_PATH = (
    Path(__file__).with_name('assets') / 'psiloqa_span_demo.json'
)
_PSILOQA_DEMO_CASES_ASSET_PATH = (
    Path(__file__).with_name('assets') / 'psiloqa_demo_cases.json'
)
_RAGTRUTH_DEMO_CASES_ASSET_PATH = (
    Path(__file__).with_name('assets') / 'ragtruth_demo_cases.json'
)
_PSILOQA_SPAN_SEED_ASSET_PATH = (
    Path(__file__).with_name('assets') / 'psiloqa_span_seed.json'
)
_PSILOQA_SPAN_SEED_QWEN35_ASSET_PATH = (
    Path(__file__).with_name('assets') / 'psiloqa_span_seed_qwen35_4b.json'
)
_PSILOQA_SPAN_SEED_FIELDS = {
    'sample_id',
    'example_id',
    'dataset',
    'split',
    'dataset_index',
    'title',
    'question',
    'passage',
    'context',
    'answer',
    'messages',
    'gold_spans',
    'gold_visibility',
    'source_answer_model',
    'representation_model',
    'model_revision',
    'representation_disclosure',
    'selection_disclosure',
    'annotation_disclosure',
    'source_disclosure',
    'why_notable',
    'license',
    'detector',
    'probe',
    'checkpoint_sha256',
    'experiment_source',
    'recorded_run',
    'content_sha256',
    'messages_sha256',
    'answer_sha256',
}
_SEED_RECORDED_RUN_FIELDS = {
    'run_id',
    'exported_sha256',
    'exported_at',
    'origin',
}
_SEED_DETECTOR_FIELDS = {
    'preset',
    'family',
    'level',
    'score_semantics',
    'threshold',
    'threshold_method',
    'selected_layer',
    'selected_seed',
    'scaling',
}
_SEED_PROBE_FIELDS = {
    'metric',
    'normalization',
    'token_offsets',
    'token_scores',
    'predicted_spans',
    'predicted_span_scores',
    'iou',
    'predicted_coverage',
    'predicted_runs',
    'false_positive_runs',
}
_PSILOQA_DEMO_CASE_FIELDS = {
    'case_id',
    'label',
    'why_notable',
    'dataset',
    'split',
    'dataset_index',
    'passage',
    'question',
    'answer',
    'messages',
    'content_sha256',
    'messages_sha256',
    'gold_spans',
    'gold_visibility',
    'source_answer_model',
    'representation_model',
    'representation_disclosure',
    'selection_disclosure',
    'annotation_disclosure',
    'license',
}
_RAGTRUTH_DEMO_CASE_FIELDS = {
    'case_id',
    'label',
    'why_notable',
    'dataset',
    'split',
    'dataset_index',
    'source_id',
    'task_type',
    'context',
    'question',
    'answer',
    'messages',
    'content_sha256',
    'messages_sha256',
    'gold_spans',
    'gold_visibility',
    'source_answer_model',
    'selection_disclosure',
    'annotation_disclosure',
    'source_disclosure',
    'license',
}
_PSILOQA_SPAN_FIELDS = {
    'sample_id',
    'dataset',
    'split',
    'dataset_index',
    'title',
    'question',
    'context',
    'answer',
    'messages',
    'content_sha256',
    'messages_sha256',
    'gold_spans',
    'gold_visibility',
    'source_answer_model',
    'representation_model',
    'representation_disclosure',
    'selection_disclosure',
    'annotation_disclosure',
    'license',
}
_CASE_FIELDS = {
    'sample_id',
    'title',
    'question',
    'answer_prompt',
    'prompt_sha256',
    'system_prompt',
    'messages_sha256',
    'prediction',
    'gold',
    'score',
    'threshold',
    'detector',
    'evidence_excerpts',
    'provenance',
}
_PROVENANCE_FIELDS = {
    'dataset',
    'dataset_variant',
    'source',
    'model',
    'base_url',
    'run',
    'trace',
    'score_source',
    'score_method',
    'score_protocol',
    'fold',
    'probe_layer',
    'generation_temperature',
    'response_format',
    'category',
}
_TOKEN_TRACE_FIELDS = {
    'answer_sha256',
    'metric',
    'normalization',
    'token_pieces',
    'token_offsets',
    'raw_scores',
    'normalized_scores',
    'top20_entropy',
    'source',
    'source_sha256',
}


def generation_messages(case: dict[str, Any]) -> list[dict[str, str]]:
    return [
        {'role': 'system', 'content': case['system_prompt']},
        {'role': 'user', 'content': case['answer_prompt']},
    ]


def load_psiloqa_span_demo_case(
    path: str | Path | None = None,
) -> dict[str, Any]:
    """Load the exact held-out PsiloQA case used by the span-detector demo."""
    asset_path = Path(path) if path is not None else _PSILOQA_SPAN_ASSET_PATH
    with asset_path.open(encoding='utf-8') as file:
        payload = json.load(file)

    if not isinstance(payload, dict) or payload.get('schema_version') != 1:
        raise ValueError('PsiloQA span demo must use schema version 1')
    case = payload.get('case')
    if not isinstance(case, dict):
        raise ValueError('PsiloQA span demo must contain one case object')
    missing = _PSILOQA_SPAN_FIELDS - case.keys()
    if missing:
        raise ValueError(
            f'PsiloQA span demo is missing: {", ".join(sorted(missing))}'
        )

    messages = case['messages']
    if (
        not isinstance(messages, list)
        or len(messages) != 2
        or [message.get('role') for message in messages if isinstance(message, dict)]
        != ['user', 'assistant']
        or any(not isinstance(message.get('content'), str) for message in messages)
    ):
        raise ValueError('PsiloQA span demo messages must be exact user/assistant text')

    content_hashes = case['content_sha256']
    if not isinstance(content_hashes, dict):
        raise ValueError('PsiloQA span demo content SHA-256 values are invalid')
    for message in messages:
        role = message['role']
        actual_hash = hashlib.sha256(message['content'].encode()).hexdigest()
        if content_hashes.get(role) != actual_hash:
            raise ValueError(f'PsiloQA span demo {role} content SHA-256 mismatch')

    canonical_messages = [
        {'role': message['role'], 'content': message['content']}
        for message in messages
    ]
    encoded_messages = json.dumps(
        canonical_messages,
        ensure_ascii=False,
        separators=(',', ':'),
    ).encode()
    if case['messages_sha256'] != hashlib.sha256(encoded_messages).hexdigest():
        raise ValueError('PsiloQA span demo messages SHA-256 mismatch')
    if messages[1]['content'] != case['answer']:
        raise ValueError('PsiloQA span demo answer must match the assistant message')
    if case['context'] not in messages[0]['content']:
        raise ValueError('PsiloQA span demo context must match the user message')
    if case['question'] not in messages[0]['content']:
        raise ValueError('PsiloQA span demo question must match the user message')

    spans = case['gold_spans']
    if (
        not isinstance(spans, list)
        or not spans
        or any(
            not isinstance(span, list)
            or len(span) != 2
            or any(isinstance(offset, bool) or not isinstance(offset, int) for offset in span)
            or not 0 <= span[0] < span[1] <= len(case['answer'])
            for span in spans
        )
    ):
        raise ValueError('PsiloQA span demo gold spans are invalid')
    if case['gold_visibility'] != 'hidden':
        raise ValueError('PsiloQA span demo gold spans must be hidden by default')

    return case


def _is_sha256(value: Any) -> bool:
    return (
        isinstance(value, str)
        and len(value) == 64
        and set(value) <= set('0123456789abcdef')
    )


def _canonical_sha256(value: Any) -> str:
    encoded = json.dumps(
        value, ensure_ascii=False, sort_keys=True, separators=(',', ':')
    ).encode('utf-8')
    return hashlib.sha256(encoded).hexdigest()


def _validate_seed_alignment(case: dict[str, Any]) -> None:
    """Fail loudly unless every probe token aligns to the exact answer characters.

    Misaligned evidence must never reach the UI (docs/ui.md): the recorded per-token
    scores are only trustworthy if their character offsets are contiguous, cover the
    whole answer, and reconstruct the answer string exactly.
    """
    answer = case['answer']
    probe = case['probe']
    offsets = probe['token_offsets']
    scores = probe['token_scores']
    if (
        not isinstance(offsets, list)
        or not offsets
        or not isinstance(scores, list)
        or len(scores) != len(offsets)
    ):
        raise ValueError('PsiloQA span seed token offsets and scores must align')
    cursor = 0
    for offset in offsets:
        if (
            not isinstance(offset, list)
            or len(offset) != 2
            or any(
                isinstance(bound, bool) or not isinstance(bound, int)
                for bound in offset
            )
            or offset != [cursor, cursor + len(answer[cursor:offset[1]])]
            or offset[1] <= offset[0]
        ):
            raise ValueError('PsiloQA span seed token offsets are not contiguous')
        cursor = offset[1]
    if cursor != len(answer):
        raise ValueError('PsiloQA span seed token offsets must cover the answer')
    if ''.join(answer[start:end] for start, end in offsets) != answer:
        raise ValueError('PsiloQA span seed tokens do not reconstruct the answer')
    if any(
        isinstance(score, bool)
        or not isinstance(score, (int, float))
        or not math.isfinite(score)
        or not 0.0 <= score <= 1.0
        for score in scores
    ):
        raise ValueError('PsiloQA span seed token scores must be finite in [0, 1]')

    span_scores = probe['predicted_span_scores']
    if not isinstance(span_scores, list) or not span_scores:
        raise ValueError('PsiloQA span seed must record at least one predicted span')
    for entry in span_scores:
        span = entry.get('span') if isinstance(entry, dict) else None
        if (
            not isinstance(entry, dict)
            or not isinstance(span, list)
            or len(span) != 2
            or any(
                isinstance(bound, bool) or not isinstance(bound, int)
                for bound in span
            )
            or not 0 <= span[0] < span[1] <= len(answer)
            or answer[span[0]:span[1]] != entry.get('text')
            or any(
                isinstance(entry.get(key), bool)
                or not isinstance(entry.get(key), (int, float))
                or not math.isfinite(entry[key])
                for key in ('max_score', 'mean_score')
            )
        ):
            raise ValueError('PsiloQA span seed predicted span is misaligned')


def load_psiloqa_span_seed(
    path: str | Path | None = None,
) -> dict[str, Any]:
    """Load the census/Llanbadoc seed case with its verified recorded probe outputs.

    The asset embeds a SHA-256 over its own payload plus per-message and per-answer
    hashes; all are verified here, and the recorded per-token/per-span scores are
    checked for exact character alignment. Any mismatch raises rather than shipping
    misattributed or misaligned evidence.
    """
    asset_path = (
        Path(path) if path is not None else _PSILOQA_SPAN_SEED_ASSET_PATH
    )
    with asset_path.open(encoding='utf-8') as file:
        payload = json.load(file)

    if not isinstance(payload, dict) or payload.get('schema_version') != 1:
        raise ValueError('PsiloQA span seed must use schema version 1')
    case = payload.get('case')
    if not isinstance(case, dict):
        raise ValueError('PsiloQA span seed must contain one case object')
    if case.keys() != _PSILOQA_SPAN_SEED_FIELDS:
        raise ValueError('PsiloQA span seed case fields do not match the schema')

    integrity = payload.get('integrity')
    if (
        not isinstance(integrity, dict)
        or integrity.get('algorithm') != 'sha256'
        or not _is_sha256(integrity.get('sha256'))
    ):
        raise ValueError('PsiloQA span seed integrity metadata is invalid')
    if integrity['sha256'] != _canonical_sha256(case):
        raise ValueError('PsiloQA span seed payload SHA-256 mismatch')

    messages = case['messages']
    if (
        not isinstance(messages, list)
        or len(messages) != 2
        or [message.get('role') for message in messages if isinstance(message, dict)]
        != ['user', 'assistant']
        or any(not isinstance(message.get('content'), str) for message in messages)
    ):
        raise ValueError('PsiloQA span seed messages must be exact user/assistant text')
    content_hashes = case['content_sha256']
    if not isinstance(content_hashes, dict):
        raise ValueError('PsiloQA span seed content SHA-256 values are invalid')
    for message in messages:
        role = message['role']
        actual_hash = hashlib.sha256(message['content'].encode()).hexdigest()
        if content_hashes.get(role) != actual_hash:
            raise ValueError(f'PsiloQA span seed {role} content SHA-256 mismatch')
    canonical_messages = [
        {'role': message['role'], 'content': message['content']}
        for message in messages
    ]
    if case['messages_sha256'] != _canonical_sha256(canonical_messages):
        raise ValueError('PsiloQA span seed messages SHA-256 mismatch')

    answer = case['answer']
    if messages[1]['content'] != answer:
        raise ValueError('PsiloQA span seed answer must match the assistant message')
    if case['answer_sha256'] != hashlib.sha256(answer.encode()).hexdigest():
        raise ValueError('PsiloQA span seed answer SHA-256 mismatch')
    if case['context'] != messages[0]['content']:
        raise ValueError('PsiloQA span seed context must match the user message')
    if build_psiloqa_prompt(case['passage'], case['question']) != case['context']:
        raise ValueError('PsiloQA span seed passage/question do not rebuild the prompt')

    spans = case['gold_spans']
    if (
        not isinstance(spans, list)
        or not spans
        or any(
            not isinstance(span, list)
            or len(span) != 2
            or any(isinstance(bound, bool) or not isinstance(bound, int) for bound in span)
            or not 0 <= span[0] < span[1] <= len(answer)
            for span in spans
        )
    ):
        raise ValueError('PsiloQA span seed gold spans are invalid')
    if case['gold_visibility'] != 'hidden':
        raise ValueError('PsiloQA span seed gold spans must be hidden by default')

    detector = case['detector']
    if not isinstance(detector, dict) or detector.keys() != _SEED_DETECTOR_FIELDS:
        raise ValueError('PsiloQA span seed detector fields do not match the schema')
    threshold = detector['threshold']
    if (
        isinstance(threshold, bool)
        or not isinstance(threshold, (int, float))
        or not 0.0 < threshold < 1.0
    ):
        raise ValueError('PsiloQA span seed threshold must be within (0, 1)')
    if (
        isinstance(detector['selected_layer'], bool)
        or not isinstance(detector['selected_layer'], int)
        or detector['selected_layer'] < 0
    ):
        raise ValueError('PsiloQA span seed selected layer must be a non-negative int')
    if detector['score_semantics'] != 'thresholdedRawScore':
        raise ValueError('PsiloQA span seed probe scores are thresholded raw scores')

    probe = case['probe']
    if not isinstance(probe, dict) or probe.keys() != _SEED_PROBE_FIELDS:
        raise ValueError('PsiloQA span seed probe fields do not match the schema')
    _validate_seed_alignment(case)

    checkpoint = case['checkpoint_sha256']
    if (
        not isinstance(checkpoint, dict)
        or not checkpoint
        or any(not _is_sha256(value) for value in checkpoint.values())
    ):
        raise ValueError('PsiloQA span seed checkpoint SHA-256 values are invalid')
    if not isinstance(case['experiment_source'], str) or not case['experiment_source']:
        raise ValueError('PsiloQA span seed must attribute an experiment source')

    recorded = case['recorded_run']
    if recorded is not None:
        if (
            not isinstance(recorded, dict)
            or recorded.keys() != _SEED_RECORDED_RUN_FIELDS
            or not isinstance(recorded['run_id'], str)
            or not recorded['run_id']
            or not _is_sha256(recorded['exported_sha256'])
            or not isinstance(recorded['exported_at'], str)
            or not recorded['exported_at']
            or recorded['origin'] != 'recordedAnswerLiveDetection'
        ):
            raise ValueError('PsiloQA span seed recorded-run attribution is invalid')

    return case


def load_psiloqa_span_seed_qwen35(
    path: str | Path | None = None,
) -> dict[str, Any] | None:
    """Load the Qwen3.5-4B probe landing seed, or None when its asset is absent (silent by design).

    Reuses ``load_psiloqa_span_seed`` (same SHA-256 and character-alignment discipline); an absent
    asset returns None so the landing falls back to the Qwen3-4B hero probe seed alone.
    """
    asset_path = (
        Path(path) if path is not None else _PSILOQA_SPAN_SEED_QWEN35_ASSET_PATH
    )
    if not asset_path.is_file():
        return None
    return load_psiloqa_span_seed(asset_path)


def build_psiloqa_prompt(passage: str, question: str) -> str:
    return (
        'Answer the question based on the passage.'
        f'\nPassage: {passage}\nQuestion: {question}\n'
    )


# ---------------------------------------------------------------------------------------------
# Judge span-tag landing seed — asset contract (schema_version 1)
#
# THE GPU CAMPAIGN EMITS THIS FILE. The fixture in tests/test_judge_span_seed.py is the contract;
# a real, verified asset dropped at ``assets/judge_span_seed.json`` makes the landing show a second
# recorded-result card (the token API judge run) beside the census probe card. Every field below is
# validated on load; any mismatch raises (never ships misattributed evidence), an absent file returns
# None (landing = probe seed only).
#
# Top level:
#   schema_version : int == 1
#   case           : object with EXACTLY the keys in ``_JUDGE_SPAN_SEED_FIELDS``
#   integrity      : {algorithm: 'sha256', sha256: canonical-sha256 over ``case``}
#
# case:
#   sample_id, example_id      : stable identifiers for the case
#   dataset, split             : provenance of the source answer
#   question, passage          : rebuild ``context`` via build_psiloqa_prompt(passage, question)
#   context                    : the user prompt == messages[0].content
#   answer                     : the assistant answer == messages[1].content; char scores align to it
#   messages                   : [ {role:'user',...}, {role:'assistant',...} ] verbatim text
#   content_sha256             : {user, assistant} sha256 of each message content
#   messages_sha256            : canonical-sha256 over the [{role,content},...] list
#   answer_sha256              : sha256 of ``answer``
#   gold_spans                 : PsiloQA gold char spans [[start,end],...] within the answer
#   gold_visibility            : must be 'hidden' (gold is never auto-revealed in the demo)
#   source_answer_model        : model that produced the answer
#   why_notable, license       : demo copy + license string
#   detector: {
#     preset            : the UI preset name (e.g. 'Judge — API Token (zero-shot)')
#     family            : must be 'judge'
#     level             : must be 'token'
#     score_semantics   : must be 'spanAgreement' (k/n agreement, NOT a calibrated probability)
#     judge_model       : the judge model id (disclosed; never a key or base_url)
#     provider_label    : the judge provider label (e.g. 'OpenRouter'; never the base_url)
#     temperature       : sampling temperature, finite in (0, 2]
#     requested         : judge samples requested, int >= 1
#     valid             : verbatim-aligned samples that voted, int with 0 < valid <= requested
#   }
#   judge: {
#     char_scores        : list[float] length == len(answer); each the k/n agreement in [0, 1]
#     predicted_spans    : [[start,end],...] char-offset-exact == maximal runs of char_scores > 0
#     generations_sha256 : sha256 attributing the recorded raw judge generations (not stored verbatim)
#   }
#   experiment_source          : portable path/id of the run that recorded these scores
# ---------------------------------------------------------------------------------------------
_JUDGE_SPAN_SEED_ASSET_PATH = (
    Path(__file__).with_name('assets') / 'judge_span_seed.json'
)
_JUDGE_SPAN_SEED_FIELDS = {
    'sample_id',
    'example_id',
    'dataset',
    'split',
    'question',
    'passage',
    'context',
    'answer',
    'messages',
    'content_sha256',
    'messages_sha256',
    'answer_sha256',
    'gold_spans',
    'gold_visibility',
    'source_answer_model',
    'why_notable',
    'license',
    'detector',
    'judge',
    'experiment_source',
}
_JUDGE_SEED_DETECTOR_FIELDS = {
    'preset',
    'family',
    'level',
    'score_semantics',
    'judge_model',
    'provider_label',
    'temperature',
    'requested',
    'valid',
}
_JUDGE_SEED_JUDGE_FIELDS = {'char_scores', 'predicted_spans', 'generations_sha256'}


def judge_seed_predicted_spans(char_scores: list[float]) -> list[list[int]]:
    """Maximal contiguous runs of tagged (score > 0) characters, as [start, end] char offsets."""
    spans: list[list[int]] = []
    start: int | None = None
    for index, score in enumerate(char_scores):
        if score > 0:
            if start is None:
                start = index
        elif start is not None:
            spans.append([start, index])
            start = None
    if start is not None:
        spans.append([start, len(char_scores)])
    return spans


def _validate_judge_seed(case: dict[str, Any]) -> None:
    """Fail loudly unless the recorded judge scores align exactly to the answer characters."""
    answer = case['answer']
    detector = case['detector']
    if not isinstance(detector, dict) or detector.keys() != _JUDGE_SEED_DETECTOR_FIELDS:
        raise ValueError('Judge span seed detector fields do not match the schema')
    if detector['family'] != 'judge' or detector['level'] != 'token':
        raise ValueError('Judge span seed detector must be a token-level judge')
    if detector['score_semantics'] != 'spanAgreement':
        raise ValueError('Judge span seed scores must be span-agreement semantics')
    temperature = detector['temperature']
    if (
        isinstance(temperature, bool)
        or not isinstance(temperature, (int, float))
        or not math.isfinite(temperature)
        or not 0.0 < temperature <= 2.0
    ):
        raise ValueError('Judge span seed temperature must be finite in (0, 2]')
    requested, valid = detector['requested'], detector['valid']
    if (
        isinstance(requested, bool)
        or not isinstance(requested, int)
        or requested < 1
        or isinstance(valid, bool)
        or not isinstance(valid, int)
        or not 0 < valid <= requested
    ):
        raise ValueError('Judge span seed requested/valid counts are invalid')
    for field in ('preset', 'judge_model', 'provider_label'):
        if not isinstance(detector[field], str) or not detector[field]:
            raise ValueError(f'Judge span seed detector {field} must be text')

    judge = case['judge']
    if not isinstance(judge, dict) or judge.keys() != _JUDGE_SEED_JUDGE_FIELDS:
        raise ValueError('Judge span seed judge fields do not match the schema')
    scores = judge['char_scores']
    if not isinstance(scores, list) or len(scores) != len(answer):
        raise ValueError('Judge span seed char scores must align to the answer length')
    if any(
        isinstance(score, bool)
        or not isinstance(score, (int, float))
        or not math.isfinite(score)
        or not 0.0 <= score <= 1.0
        for score in scores
    ):
        raise ValueError('Judge span seed char scores must be finite in [0, 1]')
    spans = judge['predicted_spans']
    if (
        not isinstance(spans, list)
        or any(
            not isinstance(span, list)
            or len(span) != 2
            or any(isinstance(bound, bool) or not isinstance(bound, int) for bound in span)
            for span in spans
        )
        or spans != judge_seed_predicted_spans(scores)
    ):
        raise ValueError('Judge span seed predicted spans are not char-offset-exact')
    if not _is_sha256(judge['generations_sha256']):
        raise ValueError('Judge span seed generations SHA-256 is invalid')
    if not isinstance(case['experiment_source'], str) or not case['experiment_source']:
        raise ValueError('Judge span seed must attribute an experiment source')


def load_judge_span_seed(
    path: str | Path | None = None,
) -> dict[str, Any] | None:
    """Load the token-judge landing seed, or return None when the asset is absent.

    Mirrors ``load_psiloqa_span_seed``'s SHA-256 discipline: payload/message/answer hashes are
    verified and the recorded per-character judge scores are checked for exact character
    alignment. Any mismatch raises; an absent asset returns None so the landing falls back to the
    probe seed alone.
    """
    asset_path = (
        Path(path) if path is not None else _JUDGE_SPAN_SEED_ASSET_PATH
    )
    if not asset_path.is_file():
        return None
    with asset_path.open(encoding='utf-8') as file:
        payload = json.load(file)

    if not isinstance(payload, dict) or payload.get('schema_version') != 1:
        raise ValueError('Judge span seed must use schema version 1')
    case = payload.get('case')
    if not isinstance(case, dict):
        raise ValueError('Judge span seed must contain one case object')
    if case.keys() != _JUDGE_SPAN_SEED_FIELDS:
        raise ValueError('Judge span seed case fields do not match the schema')

    integrity = payload.get('integrity')
    if (
        not isinstance(integrity, dict)
        or integrity.get('algorithm') != 'sha256'
        or not _is_sha256(integrity.get('sha256'))
    ):
        raise ValueError('Judge span seed integrity metadata is invalid')
    if integrity['sha256'] != _canonical_sha256(case):
        raise ValueError('Judge span seed payload SHA-256 mismatch')

    messages = case['messages']
    if (
        not isinstance(messages, list)
        or len(messages) != 2
        or [message.get('role') for message in messages if isinstance(message, dict)]
        != ['user', 'assistant']
        or any(not isinstance(message.get('content'), str) for message in messages)
    ):
        raise ValueError('Judge span seed messages must be exact user/assistant text')
    content_hashes = case['content_sha256']
    if not isinstance(content_hashes, dict):
        raise ValueError('Judge span seed content SHA-256 values are invalid')
    for message in messages:
        role = message['role']
        actual_hash = hashlib.sha256(message['content'].encode()).hexdigest()
        if content_hashes.get(role) != actual_hash:
            raise ValueError(f'Judge span seed {role} content SHA-256 mismatch')
    canonical_messages = [
        {'role': message['role'], 'content': message['content']}
        for message in messages
    ]
    if case['messages_sha256'] != _canonical_sha256(canonical_messages):
        raise ValueError('Judge span seed messages SHA-256 mismatch')

    answer = case['answer']
    if messages[1]['content'] != answer:
        raise ValueError('Judge span seed answer must match the assistant message')
    if case['answer_sha256'] != hashlib.sha256(answer.encode()).hexdigest():
        raise ValueError('Judge span seed answer SHA-256 mismatch')
    if case['context'] != messages[0]['content']:
        raise ValueError('Judge span seed context must match the user message')
    if build_psiloqa_prompt(case['passage'], case['question']) != case['context']:
        raise ValueError('Judge span seed passage/question do not rebuild the prompt')

    spans = case['gold_spans']
    if (
        not isinstance(spans, list)
        or not spans
        or any(
            not isinstance(span, list)
            or len(span) != 2
            or any(isinstance(bound, bool) or not isinstance(bound, int) for bound in span)
            or not 0 <= span[0] < span[1] <= len(answer)
            for span in spans
        )
    ):
        raise ValueError('Judge span seed gold spans are invalid')
    if case['gold_visibility'] != 'hidden':
        raise ValueError('Judge span seed gold spans must be hidden by default')

    _validate_judge_seed(case)
    return case


def load_psiloqa_demo_cases(
    path: str | Path | None = None,
) -> list[dict[str, Any]]:
    """Load the verified curated PsiloQA cases for the span demo app."""
    asset_path = (
        Path(path) if path is not None else _PSILOQA_DEMO_CASES_ASSET_PATH
    )
    with asset_path.open(encoding='utf-8') as file:
        payload = json.load(file)

    if not isinstance(payload, dict) or payload.get('schema_version') != 1:
        raise ValueError('PsiloQA demo cases must use schema version 1')
    cases = payload.get('cases')
    if not isinstance(cases, list) or not cases:
        raise ValueError('PsiloQA demo cases must contain a non-empty cases list')

    loaded: list[dict[str, Any]] = []
    seen_ids: set[str] = set()
    seen_labels: set[str] = set()
    for index, case in enumerate(cases):
        if not isinstance(case, dict):
            raise ValueError(f'PsiloQA demo case {index} must be an object')
        missing = _PSILOQA_DEMO_CASE_FIELDS - case.keys()
        if missing:
            raise ValueError(
                f'PsiloQA demo case {index} is missing: {", ".join(sorted(missing))}'
            )

        case_id = case['case_id']
        if not isinstance(case_id, str) or not case_id:
            raise ValueError(f'PsiloQA demo case {index} has an invalid case_id')
        if case_id in seen_ids:
            raise ValueError(f'Duplicate PsiloQA demo case: {case_id}')
        seen_ids.add(case_id)

        label = case['label']
        if not isinstance(label, str) or not label:
            raise ValueError(f'PsiloQA demo case {case_id} has an invalid label')
        if label in seen_labels:
            raise ValueError(f'Duplicate PsiloQA demo case label: {label}')
        seen_labels.add(label)

        messages = case['messages']
        if (
            not isinstance(messages, list)
            or len(messages) != 2
            or [message.get('role') for message in messages if isinstance(message, dict)]
            != ['user', 'assistant']
            or any(not isinstance(message.get('content'), str) for message in messages)
        ):
            raise ValueError(
                f'PsiloQA demo case {case_id} messages must be exact user/assistant text'
            )

        content_hashes = case['content_sha256']
        if not isinstance(content_hashes, dict):
            raise ValueError(
                f'PsiloQA demo case {case_id} content SHA-256 values are invalid'
            )
        for message in messages:
            role = message['role']
            actual_hash = hashlib.sha256(message['content'].encode()).hexdigest()
            if content_hashes.get(role) != actual_hash:
                raise ValueError(
                    f'PsiloQA demo case {case_id} {role} content SHA-256 mismatch'
                )

        canonical_messages = [
            {'role': message['role'], 'content': message['content']}
            for message in messages
        ]
        encoded_messages = json.dumps(
            canonical_messages,
            ensure_ascii=False,
            separators=(',', ':'),
        ).encode()
        if case['messages_sha256'] != hashlib.sha256(encoded_messages).hexdigest():
            raise ValueError(
                f'PsiloQA demo case {case_id} messages SHA-256 mismatch'
            )

        if messages[1]['content'] != case['answer']:
            raise ValueError(
                f'PsiloQA demo case {case_id} answer must match the assistant message'
            )
        for field in ('passage', 'question'):
            if not isinstance(case[field], str) or not case[field]:
                raise ValueError(
                    f'PsiloQA demo case {case_id} field {field} must be text'
                )
        rebuilt_prompt = build_psiloqa_prompt(case['passage'], case['question'])
        if rebuilt_prompt != messages[0]['content']:
            raise ValueError(
                f'PsiloQA demo case {case_id} passage/question do not rebuild '
                'the user prompt'
            )

        spans = case['gold_spans']
        if (
            not isinstance(spans, list)
            or not spans
            or any(
                not isinstance(span, list)
                or len(span) != 2
                or any(
                    isinstance(offset, bool) or not isinstance(offset, int)
                    for offset in span
                )
                or not 0 <= span[0] < span[1] <= len(case['answer'])
                for span in spans
            )
        ):
            raise ValueError(f'PsiloQA demo case {case_id} gold spans are invalid')
        if case['gold_visibility'] != 'hidden':
            raise ValueError(
                f'PsiloQA demo case {case_id} gold spans must be hidden by default'
            )

        loaded.append(case)

    return loaded


def load_ragtruth_demo_cases(
    path: str | Path | None = None,
) -> list[dict[str, Any]]:
    """Load the verified curated RAGTruth QA cases, or [] when the asset is absent.

    Absence is silent by design so shared deployments that do not ship the asset
    still boot. When the asset is present every message/answer hash is verified and
    the gold spans are checked for exact bounds; any mismatch raises rather than
    surfacing tampered or misattributed content. Gold spans may be empty (a
    clearly-supported answer carries none).
    """
    asset_path = (
        Path(path) if path is not None else _RAGTRUTH_DEMO_CASES_ASSET_PATH
    )
    if not asset_path.is_file():
        return []
    with asset_path.open(encoding='utf-8') as file:
        payload = json.load(file)

    if not isinstance(payload, dict) or payload.get('schema_version') != 1:
        raise ValueError('RAGTruth demo cases must use schema version 1')
    cases = payload.get('cases')
    if not isinstance(cases, list) or not cases:
        raise ValueError('RAGTruth demo cases must contain a non-empty cases list')

    loaded: list[dict[str, Any]] = []
    seen_ids: set[str] = set()
    seen_labels: set[str] = set()
    for index, case in enumerate(cases):
        if not isinstance(case, dict):
            raise ValueError(f'RAGTruth demo case {index} must be an object')
        missing = _RAGTRUTH_DEMO_CASE_FIELDS - case.keys()
        if missing:
            raise ValueError(
                f'RAGTruth demo case {index} is missing: {", ".join(sorted(missing))}'
            )

        case_id = case['case_id']
        if not isinstance(case_id, str) or not case_id:
            raise ValueError(f'RAGTruth demo case {index} has an invalid case_id')
        if case_id in seen_ids:
            raise ValueError(f'Duplicate RAGTruth demo case: {case_id}')
        seen_ids.add(case_id)

        label = case['label']
        if not isinstance(label, str) or not label:
            raise ValueError(f'RAGTruth demo case {case_id} has an invalid label')
        if label in seen_labels:
            raise ValueError(f'Duplicate RAGTruth demo case label: {label}')
        seen_labels.add(label)

        messages = case['messages']
        if (
            not isinstance(messages, list)
            or len(messages) != 2
            or [message.get('role') for message in messages if isinstance(message, dict)]
            != ['user', 'assistant']
            or any(not isinstance(message.get('content'), str) for message in messages)
        ):
            raise ValueError(
                f'RAGTruth demo case {case_id} messages must be exact user/assistant text'
            )

        content_hashes = case['content_sha256']
        if not isinstance(content_hashes, dict):
            raise ValueError(
                f'RAGTruth demo case {case_id} content SHA-256 values are invalid'
            )
        for message in messages:
            role = message['role']
            actual_hash = hashlib.sha256(message['content'].encode()).hexdigest()
            if content_hashes.get(role) != actual_hash:
                raise ValueError(
                    f'RAGTruth demo case {case_id} {role} content SHA-256 mismatch'
                )

        canonical_messages = [
            {'role': message['role'], 'content': message['content']}
            for message in messages
        ]
        encoded_messages = json.dumps(
            canonical_messages,
            ensure_ascii=False,
            separators=(',', ':'),
        ).encode()
        if case['messages_sha256'] != hashlib.sha256(encoded_messages).hexdigest():
            raise ValueError(
                f'RAGTruth demo case {case_id} messages SHA-256 mismatch'
            )

        if messages[1]['content'] != case['answer']:
            raise ValueError(
                f'RAGTruth demo case {case_id} answer must match the assistant message'
            )
        prompt = messages[0]['content']
        for field in ('context', 'question'):
            value = case[field]
            if not isinstance(value, str) or not value:
                raise ValueError(
                    f'RAGTruth demo case {case_id} field {field} must be text'
                )
            if value not in prompt:
                raise ValueError(
                    f'RAGTruth demo case {case_id} {field} does not appear in the prompt'
                )

        spans = case['gold_spans']
        if not isinstance(spans, list) or any(
            not isinstance(span, list)
            or len(span) != 2
            or any(
                isinstance(offset, bool) or not isinstance(offset, int)
                for offset in span
            )
            or not 0 <= span[0] < span[1] <= len(case['answer'])
            for span in spans
        ):
            raise ValueError(f'RAGTruth demo case {case_id} gold spans are invalid')
        if case['gold_visibility'] != 'hidden':
            raise ValueError(
                f'RAGTruth demo case {case_id} gold spans must be hidden by default'
            )

        loaded.append(case)

    return loaded


def _validate_token_trace(case: dict[str, Any]) -> None:
    sample_id = case['sample_id']
    trace = case.get('token_trace')
    if trace is None:
        if isinstance(case['score'], bool) or not isinstance(
            case['score'], (int, float)
        ):
            raise ValueError(f'Demo case {sample_id} field score must be numeric')
        return
    if not isinstance(trace, dict) or not _TOKEN_TRACE_FIELDS <= trace.keys():
        raise ValueError(f'Demo case {sample_id} has an incomplete token trace')
    if case['score'] is not None:
        raise ValueError(
            f'Demo case {sample_id} token uncertainty must not claim a summary score'
        )

    pieces = trace['token_pieces']
    offsets = trace['token_offsets']
    arrays = [trace['raw_scores'], trace['normalized_scores'], trace['top20_entropy']]
    if not isinstance(pieces, list) or not pieces or not all(
        isinstance(piece, str) for piece in pieces
    ):
        raise ValueError(f'Demo case {sample_id} has invalid token pieces')
    if not isinstance(offsets, list) or len(offsets) != len(pieces):
        raise ValueError(f'Demo case {sample_id} token arrays must have equal lengths')
    if not all(isinstance(values, list) and len(values) == len(pieces) for values in arrays):
        raise ValueError(f'Demo case {sample_id} token arrays must have equal lengths')
    if not all(
        isinstance(value, (int, float))
        and not isinstance(value, bool)
        and math.isfinite(value)
        for values in arrays
        for value in values
    ):
        raise ValueError(f'Demo case {sample_id} token arrays must be finite numbers')
    if any(not 0.0 <= value <= 1.0 for value in trace['normalized_scores']):
        raise ValueError(f'Demo case {sample_id} normalized token scores must be in [0, 1]')

    cursor = 0
    for piece, offset in zip(pieces, offsets):
        end = cursor + len(piece)
        if offset != [cursor, end]:
            raise ValueError(f'Demo case {sample_id} token offsets are not contiguous')
        cursor = end
    if ''.join(pieces) != case['prediction']:
        raise ValueError(f'Demo case {sample_id} token pieces do not reconstruct answer')
    if trace['answer_sha256'] != hashlib.sha256(case['prediction'].encode()).hexdigest():
        raise ValueError(f'Demo case {sample_id} answer SHA-256 mismatch')
    if not isinstance(trace['source'], str) or Path(trace['source']).is_absolute():
        raise ValueError(f'Demo case {sample_id} token trace path must be portable')
    source_sha256 = trace['source_sha256']
    if (
        not isinstance(source_sha256, str)
        or len(source_sha256) != 64
        or not set(source_sha256) <= set('0123456789abcdef')
    ):
        raise ValueError(f'Demo case {sample_id} token trace SHA-256 is invalid')


def load_demo_cases(path: str | Path | None = None) -> dict[str, dict[str, Any]]:
    """Load and verify the portable recorded demo cases."""
    asset_path = Path(path) if path is not None else _ASSET_PATH
    with asset_path.open(encoding='utf-8') as file:
        payload = json.load(file)

    if not isinstance(payload, dict) or payload.get('schema_version') != 2:
        raise ValueError('Demo cases must use schema version 2')
    cases = payload.get('cases')
    if not isinstance(cases, list):
        raise ValueError('Demo cases must contain a cases list')

    loaded: dict[str, dict[str, Any]] = {}
    for index, case in enumerate(cases):
        if not isinstance(case, dict):
            raise ValueError(f'Demo case {index} must be an object')
        missing = _CASE_FIELDS - case.keys()
        if missing:
            raise ValueError(
                f'Demo case {index} is missing: {", ".join(sorted(missing))}'
            )

        sample_id = case['sample_id']
        if not isinstance(sample_id, str) or not sample_id:
            raise ValueError(f'Demo case {index} has an invalid sample_id')
        if sample_id in loaded:
            raise ValueError(f'Duplicate demo case: {sample_id}')

        for field in _CASE_FIELDS - {
            'score',
            'threshold',
            'evidence_excerpts',
            'provenance',
        }:
            if not isinstance(case[field], str):
                raise ValueError(f'Demo case {sample_id} field {field} must be text')
        _validate_token_trace(case)
        if case['threshold'] is not None:
            raise ValueError(
                f'Demo case {sample_id} recorded score must not claim a threshold'
            )

        expected_hash = hashlib.sha256(case['answer_prompt'].encode()).hexdigest()
        if case['prompt_sha256'] != expected_hash:
            raise ValueError(f'Demo case {sample_id} prompt SHA-256 mismatch')
        encoded_messages = json.dumps(
            generation_messages(case),
            ensure_ascii=False,
            separators=(',', ':'),
        ).encode()
        if case['messages_sha256'] != hashlib.sha256(encoded_messages).hexdigest():
            raise ValueError(f'Demo case {sample_id} messages SHA-256 mismatch')

        excerpts = case['evidence_excerpts']
        if not isinstance(excerpts, list) or not excerpts:
            raise ValueError(f'Demo case {sample_id} must include evidence excerpts')
        for excerpt in excerpts:
            if (
                not isinstance(excerpt, dict)
                or not {'label', 'rank', 'content'} <= excerpt.keys()
            ):
                raise ValueError(
                    f'Demo case {sample_id} has an invalid evidence excerpt'
                )

        provenance = case['provenance']
        if (
            not isinstance(provenance, dict)
            or not _PROVENANCE_FIELDS <= provenance.keys()
        ):
            raise ValueError(f'Demo case {sample_id} has incomplete provenance')
        for field in ('trace', 'score_source'):
            if (
                not isinstance(provenance[field], str)
                or Path(provenance[field]).is_absolute()
            ):
                raise ValueError(f'Demo case {sample_id} {field} path must be portable')

        loaded[sample_id] = case

    return loaded


def get_demo_case(sample_id: str) -> dict[str, Any]:
    return load_demo_cases()[sample_id]
