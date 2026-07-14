"""Fast, network-free tests for the PsiloQA (P4) and LongMemEval (L4-span) judge drivers.

A fake OpenAI client returns scripted annotated echoes / verdicts, so the whole judge path runs
without a server. Covers char alignment, the honest ``no_aligned_annotation`` failure record,
resume, and the LongMemEval per-answer aggregates + null-label accounting.
"""

from __future__ import annotations

import json
import math
from types import SimpleNamespace

import pandas as pd
import pytest

from demo import psiloqa_span_judge_eval as pj
from scripts.experiments import longmemeval_span_judge as lm


def _make_patch(monkeypatch, answers: dict):
    """Patch ``openai.OpenAI``/``AsyncOpenAI`` with a scripted fake keyed on the answer text.

    ``answers[text] = {"annotated": <span-tagged echo or paraphrase>, "verdict": "0"|"1",
    "logprob": <logprob of the emitted verdict token>}``.
    """
    import openai

    def script(messages, **kwargs):
        system = messages[0]["content"]
        user = messages[1]["content"]
        entry = next(cfg for text, cfg in answers.items() if text in user)
        if "span annotator" in system.lower():
            n = kwargs.get("n", 1)
            choice = SimpleNamespace(
                message=SimpleNamespace(content=entry["annotated"]), logprobs=None
            )
            return SimpleNamespace(choices=[choice for _ in range(n)])
        logprob = entry["logprob"]
        verdict = entry["verdict"]
        # Only the verdict class appears in the top-k (the runner-up is prose), so the
        # judge's marginal-probability branch reproduces the scripted P exactly:
        # verdict "1" -> exp(logprob); verdict "0" -> 1 - exp(logprob).
        token = SimpleNamespace(
            token=verdict,
            logprob=logprob,
            top_logprobs=[
                SimpleNamespace(token=verdict, logprob=logprob),
                SimpleNamespace(token="the", logprob=logprob - 3.0),
            ],
        )
        choice = SimpleNamespace(
            message=SimpleNamespace(content=entry["verdict"]),
            logprobs=SimpleNamespace(content=[token]),
        )
        return SimpleNamespace(choices=[choice])

    class _Client:
        def __init__(self, **_):
            self.chat = SimpleNamespace(
                completions=SimpleNamespace(create=lambda model, messages, **kw: script(messages, **kw))
            )

    monkeypatch.setattr(openai, "OpenAI", _Client)
    monkeypatch.setattr(openai, "AsyncOpenAI", _Client)


def _raise_patch(monkeypatch):
    import openai

    def _boom(model, messages, **kw):
        raise AssertionError("create must not be called when resuming completed ids")

    class _Client:
        def __init__(self, **_):
            self.chat = SimpleNamespace(completions=SimpleNamespace(create=_boom))

    monkeypatch.setattr(openai, "OpenAI", _Client)
    monkeypatch.setattr(openai, "AsyncOpenAI", _Client)


def _psiloqa_rows():
    return [
        {
            "id": "r1",
            "input": [
                {"role": "user", "content": "passage one. QUESTION_ONE?"},
                {"role": "assistant", "content": "alpha beta gamma delta"},
            ],
            "answer": "alpha beta gamma delta",
            "spans": [[6, 10]],  # "beta"
        },
        {
            "id": "r2",
            "input": [
                {"role": "user", "content": "passage two. QUESTION_TWO?"},
                {"role": "assistant", "content": "one two three"},
            ],
            "answer": "one two three",
            "spans": [],
        },
        {
            "id": "r3",
            "input": [
                {"role": "user", "content": "passage three. QUESTION_THREE?"},
                {"role": "assistant", "content": "failing answer text here"},
            ],
            "answer": "failing answer text here",
            "spans": [[0, 7]],
        },
    ]


_PSILOQA_ANSWERS = {
    "alpha beta gamma delta": {
        "annotated": "alpha [SPAN]beta[/SPAN] gamma delta",
        "verdict": "1",
        "logprob": math.log(0.9),
    },
    "one two three": {
        "annotated": "one two three",
        "verdict": "0",
        "logprob": math.log(0.8),
    },
    "failing answer text here": {
        "annotated": "COMPLETELY DIFFERENT PARAPHRASE",  # never echoes -> 0 valid
        "verdict": "1",
        "logprob": math.log(0.7),
    },
}


def test_psiloqa_driver_alignment_and_failure(monkeypatch, tmp_path):
    _make_patch(monkeypatch, _PSILOQA_ANSWERS)
    monkeypatch.setattr(pj, "load_psiloqa_rows", lambda *a, **k: _psiloqa_rows())

    pj.main(
        [
            "--dataset", "unused",
            "--out-dir", str(tmp_path),
            "--split", "test",
            "--num-beams", "2",
        ]
    )

    token = pj.read_jsonl(tmp_path / "token_judge_test.jsonl")
    assert len(token) == 3
    by_id = {rec["id"]: rec for rec in token}

    r1 = by_id["r1"]
    assert r1["status"] == "ok"
    assert len(r1["char_scores"]) == len("alpha beta gamma delta")
    assert r1["char_scores"][7] == 1.0  # inside "beta"
    assert r1["char_scores"][0] == 0.0  # outside
    assert r1["valid"] == 2 and r1["requested"] == 2
    assert r1["generations_sha256"] and r1["generations"]

    assert by_id["r3"]["status"] == "no_aligned_annotation"
    assert by_id["r3"]["valid"] == 0
    assert by_id["r3"]["generations"]  # audit trail preserved even on failure

    metrics = json.loads((tmp_path / "sirin_metrics.json").read_text())
    assert metrics["failed_samples"] == 1
    assert metrics["threshold_source"] == "default_0.5"
    assert metrics["token_judge"]["n_rows"] == 2  # only the two aligned answers
    assert "mean_per_answer_iou" in metrics["token_judge"]
    seq = metrics["sequence_judge"]
    assert seq["n"] == 3
    assert seq["roc_auc"] == 1.0  # scores 0.9/0.7 (pos) separate from 0.2 (neg)


def test_psiloqa_driver_resume_skips_completed(monkeypatch, tmp_path):
    _make_patch(monkeypatch, _PSILOQA_ANSWERS)
    monkeypatch.setattr(pj, "load_psiloqa_rows", lambda *a, **k: _psiloqa_rows())
    argv = ["--dataset", "unused", "--out-dir", str(tmp_path), "--split", "test", "--num-beams", "2"]
    pj.main(argv)
    first = (tmp_path / "token_judge_test.jsonl").read_text()

    _raise_patch(monkeypatch)  # any create call now fails
    pj.main(argv)  # must be a no-op for the judges (all ids done)

    assert (tmp_path / "token_judge_test.jsonl").read_text() == first
    assert len(pj.read_jsonl(tmp_path / "sequence_judge_test.jsonl")) == 3


_LONGMEM_ANSWERS = {
    "ANSWER_ONE": {"annotated": "ANSWER_ONE", "verdict": "0", "logprob": math.log(0.8)},
    "ANSWER_TWO": {"annotated": "[SPAN]ANSWER_TWO[/SPAN]", "verdict": "1", "logprob": math.log(0.9)},
    "ANSWER_THREE": {"annotated": "ANSWER_THREE", "verdict": "0", "logprob": math.log(0.8)},
    "ANSWER_FOUR": {"annotated": "ANSWER_FOUR [SPAN]tail[/SPAN]", "verdict": "1", "logprob": math.log(0.9)},
    "ANSWER_FIVE": {"annotated": "[SPAN]ANSWER_FIVE[/SPAN]", "verdict": "1", "logprob": math.log(0.9)},
}


def _write_parquet(path):
    rows = [
        ("s1", "context one", "ANSWER_ONE", 0),
        ("s2", "context two", "ANSWER_TWO", 1),
        ("s3", "context three", "ANSWER_THREE", 0),
        ("s4", "context four", "ANSWER_FOUR tail", 1),
        ("s5", "context five", "ANSWER_FIVE", None),  # null strict -> excluded from metrics
    ]
    frame = pd.DataFrame(
        {
            "sample_id": [r[0] for r in rows],
            "prompt_user": [r[1] for r in rows],
            "prompt_assistant": [r[2] for r in rows],
            "labels": [json.dumps({"hallucination_strict": r[3]}) for r in rows],
        }
    )
    frame.to_parquet(path)


def test_longmemeval_driver_aggregates_and_null_accounting(monkeypatch, tmp_path):
    _make_patch(monkeypatch, _LONGMEM_ANSWERS)
    parquet = tmp_path / "trustmem_dataset.parquet"
    _write_parquet(parquet)
    out = tmp_path / "judge_span"

    lm.main(["--dataset-parquet", str(parquet), "--out-dir", str(out)])

    metrics = json.loads((out / "sirin_metrics.json").read_text())
    assert metrics["n_null_strict_label"] == 1
    assert metrics["failed_samples"] == 0
    for key in ("token_judge_max", "token_judge_mean", "sequence_judge"):
        assert metrics[key]["n"] == 4  # 5 rows minus the one null strict label
        assert metrics[key]["positive_rate"] == 0.5
    assert metrics["token_judge_max"]["roc_auc"] == 1.0
    assert metrics["sequence_judge"]["roc_auc"] == 1.0

    token = pj.read_jsonl(out / "token_judge.jsonl")
    assert len(token) == 5  # judged all rows, including the null-label one
    s2 = next(rec for rec in token if rec["id"] == "s2")
    assert max(s2["char_scores"]) == 1.0  # fully span-tagged answer


def test_token_context_overflow_recorded_not_raised(monkeypatch, tmp_path):
    """A prompt that overflows the context window is recorded as a failed sample, not raised,
    so a long row can never crash a resumable run."""
    import httpx
    import openai

    def _boom(model, messages, **kw):
        response = httpx.Response(400, request=httpx.Request("POST", "http://x/v1"))
        raise openai.BadRequestError("maximum context length", response=response, body=None)

    class _Client:
        def __init__(self, **_):
            self.chat = SimpleNamespace(completions=SimpleNamespace(create=_boom))

    monkeypatch.setattr(openai, "OpenAI", _Client)
    monkeypatch.setattr(openai, "AsyncOpenAI", _Client)

    judge = pj.build_token_judge("http://x/v1", "m", "EMPTY", 2, 0.7, None, 64)
    capture = pj._GenerationCapture(judge.model_adapter)
    record = pj.run_token_sample(
        judge, capture, [{"role": "user", "content": "u"}, {"role": "assistant", "content": "a"}]
    )
    assert record["status"] == "api_error"
    assert record["valid"] == 0
    assert "context length" in record["error"]
