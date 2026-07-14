#!/usr/bin/env python
"""PsiloQA span judge evaluation (campaign stage P4).

Drives the SIRIN API judges over the PsiloQA span dataset, mirroring the UI judge path:
each sample is a ``[user, assistant]`` dialogue (passage+question / answer). The token judge
runs reference-aligned ``num_beams`` consensus to produce per-character span scores; the
sequence judge emits a single-token faithfulness verdict with a logprob-derived probability.

Honesty: the judge NEVER sees gold spans or labels. A sample whose generations all fail the
reference-echo check raises ``JudgeAnnotationError`` and is recorded as a failed sample
(``status='no_aligned_annotation'``) in the raw jsonl -- never zero-filled. The raw jsonl (one
line per sample, including the full generations) is the audit trail; metrics are computed by
this driver, which alone knows the gold spans.

This module also hosts the shared judge-driving helpers imported by
``scripts/experiments/longmemeval_span_judge.py``.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import math
import os
import sys
import time
from pathlib import Path
from typing import Any

import numpy as np
import openai
from sklearn.metrics import (
    average_precision_score,
    f1_score,
    precision_recall_curve,
    roc_auc_score,
)

from sirin.metrics.span import (
    f1_optimal_threshold,
    span_classification_metrics,
    span_labels,
)

# Repo root on the path so both `python demo/...` and `import demo....` resolve the sibling
# train script (its prompt-disjoint split is the single source of truth -- imported, not copied).
_REPO_ROOT = str(Path(__file__).resolve().parents[1])
if _REPO_ROOT not in sys.path:
    sys.path.insert(0, _REPO_ROOT)

DEFAULT_BASE_URL = "http://127.0.0.1:8000/v1"
DEFAULT_MODEL = "Qwen/Qwen3.5-4B"
DEFAULT_API_KEY = "EMPTY"
DEFAULT_OUT_DIR = "output/psiloqa_span_qwen35_4b/judge"
# UI token preset temperature: generations must DIFFER so the per-char score is a real consensus.
DEFAULT_TOKEN_TEMPERATURE = 0.7
# vLLM's qwen3 reasoning parser drops content into reasoning_content unless thinking is disabled.
NO_THINKING_EXTRA_BODY = {"chat_template_kwargs": {"enable_thinking": False}}
# Verdict prompt: the UI's faithfulness framing (_build_openai_judge) plus the {sample} slot the
# UI preset omits (without it build_prompt_messages drops the dialogue and the judge scores
# nothing) plus a hard single-digit format clause. The clause matters because the fixed
# SequenceOpenAIJudge reads only the FIRST generated token (max_tokens=1): on LongMemEval's long
# structured prompts the model otherwise opens a JSON '{"reasoning":...}' object, so token 0 is
# '{' and the verdict collapses. Forcing a bare leading digit restores a clean 0/1 distribution.
# System prompt stays the JudgeBaseConfig default ("Output only '1' or '0'").
SEQUENCE_VERDICT_PROMPT = (
    "You verify whether the assistant response is faithful to the provided context. "
    "Reply with 1 if it contains hallucinated, unsupported, or contradicted claims, "
    "otherwise reply with 0.\n"
    'Dialogue: "{sample}"\n'
    "Answer with a SINGLE character that is the digit 1 or the digit 0. Do not output JSON, "
    "quotes, spaces, reasoning, or any other character. Your entire reply must be exactly one "
    "digit: "
)


# --------------------------------------------------------------------------------------
# Shared judge-driving core (also used by the LongMemEval driver)
# --------------------------------------------------------------------------------------


def _sha256(value: Any) -> str:
    return hashlib.sha256(
        json.dumps(value, ensure_ascii=False, sort_keys=True).encode()
    ).hexdigest()


def read_jsonl(path: str | Path) -> list[dict]:
    path = Path(path)
    if not path.exists():
        return []
    return [json.loads(line) for line in path.read_text().splitlines() if line.strip()]


def read_done_ids(path: str | Path) -> set:
    return {record["id"] for record in read_jsonl(path)}


def append_line(path: str | Path, obj: dict) -> None:
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("a") as handle:
        handle.write(json.dumps(obj, ensure_ascii=False) + "\n")


def _build_adapter(base_url: str, model: str, api_key: str, extra_body: dict | None):
    from sirin.inference.adapters import OpenAIModelAdapter
    from sirin.models.inference import OpenAIConfig

    return OpenAIModelAdapter(
        OpenAIConfig(
            model_path=model, api_key=api_key, base_url=base_url, extra_body=extra_body
        )
    )


def build_token_judge(
    base_url: str,
    model: str,
    api_key: str,
    num_beams: int,
    temperature: float,
    extra_body: dict | None = None,
    max_new_tokens: int = 2048,
):
    from sirin.detection.judging import TokenOpenAIJudge
    from sirin.detection.judging.judges.utils.prompts import (
        SPAN_TAG_SYSTEM_PROMPT,
        SPAN_TAG_USER_PROMPT,
    )
    from sirin.models.detection import OpenAIJudgeConfig

    return TokenOpenAIJudge(
        config=OpenAIJudgeConfig(
            system_prompt=SPAN_TAG_SYSTEM_PROMPT,
            user_prompt=SPAN_TAG_USER_PROMPT,
            temperature=float(temperature),
            num_beams=int(num_beams),
            # The judge only echoes the answer + span tags; a big budget overflows an 8k window
            # for long-prompt datasets (LongMemEval). Size this to the answers, not the prompt.
            max_new_tokens=int(max_new_tokens),
        ),
        model_adapter=_build_adapter(base_url, model, api_key, extra_body),
    )


def build_sequence_judge(
    base_url: str,
    model: str,
    api_key: str,
    extra_body: dict | None = None,
):
    from sirin.detection.judging import SequenceOpenAIJudge
    from sirin.models.detection import OpenAIJudgeConfig

    return SequenceOpenAIJudge(
        # temperature 0 keeps the single-token verdict deterministic; the score is its logprob.
        config=OpenAIJudgeConfig(user_prompt=SEQUENCE_VERDICT_PROMPT, temperature=0.0),
        model_adapter=_build_adapter(base_url, model, api_key, extra_body),
    )


class _GenerationCapture:
    """Wrap an adapter's ``sample`` so the last call's raw generations survive even when the
    judge raises (0/n valid) -- needed to write the audit trail for failed samples."""

    def __init__(self, adapter: Any):
        self._orig = adapter.sample
        adapter.sample = self._call
        self.last: Any = None

    def _call(self, *args, **kwargs):
        out = self._orig(*args, **kwargs)
        self.last = out
        return out

    def generations(self) -> list[str]:
        raw = self.last
        if isinstance(raw, tuple):  # (results, logprobs) from the sequence path
            raw = raw[0]
        if not raw:
            return []
        first = raw[0]
        return list(first) if isinstance(first, list) else [first]


def _failed_token_record(status: str, num_beams: int, capture: _GenerationCapture, error) -> dict:
    generations = capture.generations()
    return {
        "status": status,
        "valid": 0,
        "requested": int(num_beams),
        "generations": generations,
        "generations_sha256": _sha256(generations),
        "error": str(error),
    }


def run_token_sample(judge: Any, capture: _GenerationCapture, sample: list[dict]) -> dict:
    """One token-judge annotation. Returns an audit record; failures are recorded, not raised, so
    a bad row never zero-fills a score and never crashes a resumable multi-hundred-row run."""
    from sirin.detection.judging.judges.base import JudgeAnnotationError

    num_beams = judge.config.num_beams
    try:
        char_probs, _, _ = judge.detect([sample])
    except JudgeAnnotationError as error:  # every generation failed the reference-echo check
        return _failed_token_record("no_aligned_annotation", num_beams, capture, error)
    except openai.BadRequestError as error:  # e.g. prompt+budget exceeds the model context window
        return _failed_token_record("api_error", num_beams, capture, error)
    consensus = judge.last_consensus[0]
    generations = capture.generations()
    return {
        "status": "ok",
        "char_scores": [float(score) for score in char_probs[0]],
        "valid": int(consensus["valid"]),
        "requested": int(consensus["requested"]),
        "generations": generations,
        "generations_sha256": _sha256(generations),
    }


def run_sequence_sample(judge: Any, sample: list[dict]) -> dict:
    """One sequence-judge verdict. The judge returns P(hallucinated) read off the class
    token's logprob (renormalized over the class pair when both appear in the top-k), so
    ``prob`` and ``p_hallucination`` are the same number; both keys are kept for the
    stability of the recorded jsonl schema."""
    from sirin.detection.judging.judges.base import JudgeAnnotationError

    try:
        probs, preds, _ = judge.detect([sample])
    except JudgeAnnotationError as error:  # first token was not a class digit (e.g. reasoning)
        return {
            "status": "no_digit_verdict",
            "prob": float("nan"),
            "pred": None,
            "p_hallucination": float("nan"),
            "generation": (judge.last_generations or [None])[0],
            "error": str(error)[:500],
        }
    except openai.BadRequestError as error:  # e.g. prompt exceeds the model context window
        return {
            "status": "api_error",
            "prob": float("nan"),
            "pred": None,
            "p_hallucination": float("nan"),
            "generation": None,
            "error": str(error)[:500],
        }
    prob = float(probs[0])
    pred = int(preds[0])
    if math.isfinite(prob):
        p_hallucination = prob  # already P(hallucinated), no NLL conversion needed
        status = "ok"
    else:
        p_hallucination = float("nan")
        status = "no_logprobs"
    generation = (judge.last_generations or [None])[0]
    return {
        "status": status,
        "prob": prob,
        "pred": pred,
        "p_hallucination": p_hallucination,
        "generation": generation,
    }


def ranker_metrics(labels: list[int], scores: list[float]) -> dict:
    """Threshold-free ranking metrics for a per-answer binary label. F1 is reported at the
    threshold that maximises it ON THIS DATA -- labelled 'oracle' since no held-out fold exists.
    Non-finite scores (e.g. missing logprobs) are dropped and counted."""
    labels_arr = np.asarray(labels, dtype=np.float64)
    scores_arr = np.asarray(scores, dtype=np.float64)
    finite = np.isfinite(scores_arr)
    dropped = int((~finite).sum())
    labels_arr, scores_arr = labels_arr[finite], scores_arr[finite]
    result = {
        "n": int(len(labels_arr)),
        "n_dropped_nonfinite": dropped,
        "positive_rate": float(labels_arr.mean()) if len(labels_arr) else float("nan"),
    }
    if len(np.unique(labels_arr)) < 2:
        # sklearn ranking metrics are undefined with a single class present.
        result.update(
            roc_auc=float("nan"),
            average_precision=float("nan"),
            pr_auc=float("nan"),
            f1_at_oracle_threshold=float("nan"),
            oracle_threshold=float("nan"),
        )
        return result
    precision, recall, thresholds = precision_recall_curve(labels_arr, scores_arr)
    f1_curve = 2 * precision[:-1] * recall[:-1] / np.maximum(
        precision[:-1] + recall[:-1], 1e-12
    )
    best = int(np.argmax(f1_curve))
    oracle_threshold = float(thresholds[best])
    predictions = (scores_arr >= oracle_threshold).astype(np.uint8)
    result.update(
        roc_auc=float(roc_auc_score(labels_arr, scores_arr)),
        average_precision=float(average_precision_score(labels_arr, scores_arr)),
        pr_auc=float(np.trapz(precision[::-1], recall[::-1])),
        f1_at_oracle_threshold=float(f1_score(labels_arr, predictions)),
        oracle_threshold=oracle_threshold,
    )
    return result


def prompts_provenance() -> dict:
    from sirin.detection.judging.judges.utils.prompts import (
        SPAN_TAG_SYSTEM_PROMPT,
        SPAN_TAG_USER_PROMPT,
    )

    def sha(text: str) -> str:
        return hashlib.sha256(text.encode()).hexdigest()

    return {
        "span_system_prompt_sha256": sha(SPAN_TAG_SYSTEM_PROMPT),
        "span_user_prompt_sha256": sha(SPAN_TAG_USER_PROMPT),
        "sequence_verdict_prompt_sha256": sha(SEQUENCE_VERDICT_PROMPT),
    }


def resolve_extra_body(thinking: bool) -> dict | None:
    return None if thinking else NO_THINKING_EXTRA_BODY


def drive_rows(
    rows: list[dict],
    token_judge: Any,
    sequence_judge: Any,
    token_path: str | Path,
    sequence_path: str | Path,
    resume: bool,
    progress_every: int = 50,
) -> None:
    """Judge every row through both judges, appending one audit line per (row, judge).
    Resume skips ids already present in each jsonl. Each row carries ``id`` and ``input``."""
    capture = _GenerationCapture(token_judge.model_adapter)
    done_token = read_done_ids(token_path) if resume else set()
    done_sequence = read_done_ids(sequence_path) if resume else set()
    for index, row in enumerate(rows):
        sample = row["input"]
        if row["id"] not in done_token:
            record = run_token_sample(token_judge, capture, sample)
            record["id"] = row["id"]
            append_line(token_path, record)
        if row["id"] not in done_sequence:
            record = run_sequence_sample(sequence_judge, sample)
            record["id"] = row["id"]
            append_line(sequence_path, record)
        if (index + 1) % progress_every == 0:
            print(f"[judge] {index + 1}/{len(rows)} rows", flush=True)


# --------------------------------------------------------------------------------------
# PsiloQA-specific: dataset loading, metrics, threshold policy
# --------------------------------------------------------------------------------------


def load_psiloqa_rows(dataset_path: str | Path, split: str) -> list[dict]:
    """Rows for the chosen split under the shared prompt-disjoint split (seed 42).
    ``input`` is the probe pipeline's exact [user, assistant] dialogue; ``spans`` are gold."""
    from datasets import load_from_disk

    from demo.train_psiloqa_span_linear import prompt_disjoint_indices

    dataset = load_from_disk(str(dataset_path))
    train_idx, val_idx, test_idx = prompt_disjoint_indices(dataset)
    if split == "validation":
        base, indices = dataset["train"], val_idx
    elif split == "test":
        base, indices = dataset["test"], test_idx
    else:
        raise ValueError(f"unknown split {split!r} (expected test|validation)")
    rows = []
    for index in indices:
        row = base[int(index)]
        rows.append(
            {
                "id": row["id"],
                "input": row["input"],
                "answer": row["input"][-1]["content"],
                "spans": [list(span) for span in row["target"]],
            }
        )
    return rows


def _token_char_arrays(
    rows: list[dict], token_path: str | Path
) -> tuple[list[np.ndarray], list[np.ndarray], int]:
    """Per-answer (gold char labels, judge char scores) for successfully-judged rows,
    aligned by id. Returns (labels, scores, failed_count)."""
    records = {record["id"]: record for record in read_jsonl(token_path)}
    per_labels, per_scores, failed = [], [], 0
    for row in rows:
        record = records.get(row["id"])
        if record is None:
            continue
        if record["status"] != "ok":
            failed += 1
            continue
        scores = np.asarray(record["char_scores"], dtype=np.float64)
        labels = span_labels(len(row["answer"]), row["spans"])
        if len(scores) != len(labels):
            raise ValueError(
                f"char alignment mismatch for {row['id']}: "
                f"{len(scores)} scores vs {len(labels)} answer chars"
            )
        per_scores.append(scores)
        per_labels.append(labels)
    return per_labels, per_scores, failed


def resolve_threshold(
    dataset_path: str | Path,
    split: str,
    out_dir: Path,
    cli_threshold: float | None,
) -> tuple[float, str]:
    """Decision threshold for the token judge's char F1/IoU. AUC/AP are always threshold-free;
    only F1/IoU need a cut. Priority: explicit --threshold > validation-calibrated f1-optimal
    (when a prior validation run's jsonl is present) > 0.5."""
    if cli_threshold is not None:
        return float(cli_threshold), "cli"
    if split == "test":
        val_path = out_dir / "token_judge_validation.jsonl"
        if val_path.exists():
            val_rows = load_psiloqa_rows(dataset_path, "validation")
            per_labels, per_scores, _ = _token_char_arrays(val_rows, val_path)
            if per_labels:
                threshold = f1_optimal_threshold(
                    np.concatenate(per_labels), np.concatenate(per_scores)
                )
                return float(threshold), "validation_f1_optimal"
    return 0.5, "default_0.5"


def compute_metrics(
    rows: list[dict],
    token_path: str | Path,
    sequence_path: str | Path,
    threshold: float,
) -> tuple[dict, dict, int]:
    per_labels, per_scores, failed = _token_char_arrays(rows, token_path)
    token_metrics = (
        span_classification_metrics(per_labels, per_scores, threshold)
        if per_labels
        else {"n_rows": 0}
    )
    records = {record["id"]: record for record in read_jsonl(sequence_path)}
    seq_labels, seq_scores = [], []
    for row in rows:
        record = records.get(row["id"])
        if record is None:
            continue
        seq_labels.append(1 if row["spans"] else 0)
        seq_scores.append(record["p_hallucination"])
    sequence_metrics = ranker_metrics(seq_labels, seq_scores)
    return token_metrics, sequence_metrics, failed


def parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    from demo.train_psiloqa_span_linear import DATASET_PATH

    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--dataset", type=Path, default=DATASET_PATH)
    parser.add_argument("--base-url", default=DEFAULT_BASE_URL)
    parser.add_argument("--model", default=DEFAULT_MODEL)
    parser.add_argument("--api-key", default=DEFAULT_API_KEY)
    parser.add_argument("--out-dir", type=Path, default=Path(DEFAULT_OUT_DIR))
    parser.add_argument("--split", choices=("test", "validation"), default="test")
    parser.add_argument("--num-beams", type=int, default=3)
    parser.add_argument(
        "--max-new-tokens", type=int, default=2048,
        help="token-judge output budget (must fit the answer echo + tags within the context "
        "window); PsiloQA prompts are short so 2048 is safe",
    )
    parser.add_argument(
        "--temperature", type=float, default=DEFAULT_TOKEN_TEMPERATURE,
        help="token-judge sampling temperature (UI preset default 0.7); the sequence judge "
        "is always deterministic (0.0)",
    )
    parser.add_argument(
        "--threshold", type=float, default=None,
        help="override the token-judge char F1/IoU decision threshold",
    )
    parser.add_argument("--limit", type=int, default=None)
    parser.add_argument(
        "--resume", action=argparse.BooleanOptionalAction, default=True
    )
    parser.add_argument(
        "--thinking", action=argparse.BooleanOptionalAction, default=False,
        help="enable the endpoint's reasoning mode; default off (vLLM qwen3 parser hides "
        "content when thinking is on)",
    )
    return parser.parse_args(argv)


def main(argv: list[str] | None = None) -> None:
    args = parse_args(argv)
    started = time.time()
    out_dir = Path(args.out_dir)
    out_dir.mkdir(parents=True, exist_ok=True)
    token_path = out_dir / f"token_judge_{args.split}.jsonl"
    sequence_path = out_dir / f"sequence_judge_{args.split}.jsonl"

    rows = load_psiloqa_rows(args.dataset, args.split)
    if args.limit is not None:
        rows = rows[: args.limit]
    print(f"[psiloqa-judge] {len(rows)} {args.split} rows -> {out_dir}", flush=True)

    extra_body = resolve_extra_body(args.thinking)
    token_judge = build_token_judge(
        args.base_url, args.model, args.api_key, args.num_beams, args.temperature,
        extra_body, args.max_new_tokens,
    )
    sequence_judge = build_sequence_judge(args.base_url, args.model, args.api_key, extra_body)
    drive_rows(rows, token_judge, sequence_judge, token_path, sequence_path, args.resume)

    threshold, threshold_source = resolve_threshold(
        args.dataset, args.split, out_dir, args.threshold
    )
    token_metrics, sequence_metrics, failed = compute_metrics(
        rows, token_path, sequence_path, threshold
    )
    metrics = {
        "token_judge": token_metrics,
        "sequence_judge": sequence_metrics,
        "failed_samples": failed,
        "threshold": threshold,
        "threshold_source": threshold_source,
        "params": {
            "split": args.split,
            "num_beams": args.num_beams,
            "max_new_tokens": args.max_new_tokens,
            "temperature": args.temperature,
            "limit": args.limit,
            "thinking": args.thinking,
        },
        "provenance": {
            "dataset_path": str(args.dataset),
            "model": args.model,
            "base_url": args.base_url,
            "n_rows": len(rows),
            "prompts": prompts_provenance(),
            "started_unix": started,
            "finished_unix": time.time(),
        },
    }
    metrics_path = out_dir / "sirin_metrics.json"
    metrics_path.write_text(json.dumps(metrics, indent=2, ensure_ascii=False) + "\n")
    print(json.dumps(metrics, indent=2, ensure_ascii=False), flush=True)


if __name__ == "__main__":
    main()
