#!/usr/bin/env python
"""LongMemEval span judge evaluation (campaign stage L4-span).

Drives the SIRIN API judges over a LongMemEval TrustMem parquet. There are NO gold spans here,
so the token judge's per-character span scores are aggregated PER ANSWER (max and mean character
agreement) and each aggregate is scored as a ranker against the row's ``hallucination_strict``
label. The sequence judge's logprob-derived P(hallucination) is scored likewise.

Dialogue reconstruction: the parquet ships the exact answering prompt in ``prompt_user`` (the
"Answer the user's question based on the provided context" prompt, already containing the
question and the retrieved memories) and the recorded answer in ``prompt_assistant``. The judge
sample is therefore ``[{user: prompt_user}, {assistant: prompt_assistant}]`` -- no reconstruction
from raw memory columns is needed. Rows whose ``hallucination_strict`` label is null are skipped
for metrics and counted (the judge still runs on them; only scoring needs the label).

Honesty mirrors the PsiloQA driver: 0/n-valid token samples are recorded as
``no_aligned_annotation`` in the raw jsonl, never zero-filled; the raw jsonl is the audit trail.
"""

from __future__ import annotations

import argparse
import json
import sys
import time
from pathlib import Path

import numpy as np
import pandas as pd

_REPO_ROOT = str(Path(__file__).resolve().parents[2])
if _REPO_ROOT not in sys.path:
    sys.path.insert(0, _REPO_ROOT)

from demo.psiloqa_span_judge_eval import (  # noqa: E402  (path insert must precede import)
    DEFAULT_API_KEY,
    DEFAULT_BASE_URL,
    DEFAULT_MODEL,
    DEFAULT_TOKEN_TEMPERATURE,
    build_sequence_judge,
    build_token_judge,
    drive_rows,
    prompts_provenance,
    ranker_metrics,
    read_jsonl,
    resolve_extra_body,
)


def _strict_label(labels_json: str | None):
    """The row's hallucination_strict label (0/1) or None when absent/unparsable."""
    if not labels_json:
        return None
    try:
        value = json.loads(labels_json).get("hallucination_strict")
    except (json.JSONDecodeError, TypeError):
        return None
    return None if value is None or (isinstance(value, float) and np.isnan(value)) else int(value)


def load_longmemeval_rows(parquet_path: str | Path) -> list[dict]:
    frame = pd.read_parquet(parquet_path)
    required = {"sample_id", "prompt_user", "prompt_assistant", "labels"}
    missing = required - set(frame.columns)
    if missing:
        raise ValueError(f"parquet missing required columns: {sorted(missing)}")
    rows = []
    for record in frame.to_dict("records"):
        rows.append(
            {
                "id": str(record["sample_id"]),
                "input": [
                    {"role": "user", "content": str(record["prompt_user"])},
                    {"role": "assistant", "content": str(record["prompt_assistant"])},
                ],
                "strict": _strict_label(record.get("labels")),
            }
        )
    return rows


def _token_aggregates(
    rows: list[dict], token_path: str | Path
) -> tuple[list[int], list[float], list[float], int, int]:
    """Per-answer (labels, max-agreement, mean-agreement) for rows that are both judged-ok and
    strict-labelled. Returns (labels, max_scores, mean_scores, failed, skipped_null_label)."""
    records = {record["id"]: record for record in read_jsonl(token_path)}
    labels, max_scores, mean_scores = [], [], []
    failed = skipped_null = 0
    for row in rows:
        record = records.get(row["id"])
        if record is None:
            continue
        if record["status"] != "ok":
            failed += 1
            continue
        if row["strict"] is None:
            skipped_null += 1
            continue
        scores = np.asarray(record["char_scores"], dtype=np.float64)
        labels.append(int(row["strict"]))
        max_scores.append(float(scores.max()) if len(scores) else 0.0)
        mean_scores.append(float(scores.mean()) if len(scores) else 0.0)
    return labels, max_scores, mean_scores, failed, skipped_null


def _sequence_scores(
    rows: list[dict], sequence_path: str | Path
) -> tuple[list[int], list[float]]:
    records = {record["id"]: record for record in read_jsonl(sequence_path)}
    labels, scores = [], []
    for row in rows:
        record = records.get(row["id"])
        if record is None or row["strict"] is None:
            continue
        labels.append(int(row["strict"]))
        scores.append(record["p_hallucination"])
    return labels, scores


def parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--dataset-parquet", type=Path, required=True)
    parser.add_argument("--out-dir", type=Path, required=True)
    parser.add_argument("--base-url", default=DEFAULT_BASE_URL)
    parser.add_argument("--model", default=DEFAULT_MODEL)
    parser.add_argument("--api-key", default=DEFAULT_API_KEY)
    parser.add_argument("--num-beams", type=int, default=3)
    parser.add_argument(
        "--max-new-tokens", type=int, default=256,
        help="token-judge output budget; LongMemEval answers are short (<=~60 tokens) but "
        "prompts are large, so keep this small to stay inside the model context window",
    )
    parser.add_argument(
        "--temperature", type=float, default=DEFAULT_TOKEN_TEMPERATURE,
        help="token-judge sampling temperature; the sequence judge is always deterministic",
    )
    parser.add_argument("--limit", type=int, default=None)
    parser.add_argument("--resume", action=argparse.BooleanOptionalAction, default=True)
    parser.add_argument(
        "--thinking", action=argparse.BooleanOptionalAction, default=False,
        help="enable the endpoint's reasoning mode; default off",
    )
    return parser.parse_args(argv)


def main(argv: list[str] | None = None) -> None:
    args = parse_args(argv)
    started = time.time()
    out_dir = Path(args.out_dir)
    out_dir.mkdir(parents=True, exist_ok=True)
    token_path = out_dir / "token_judge.jsonl"
    sequence_path = out_dir / "sequence_judge.jsonl"

    rows = load_longmemeval_rows(args.dataset_parquet)
    if args.limit is not None:
        rows = rows[: args.limit]
    n_null = sum(1 for row in rows if row["strict"] is None)
    print(
        f"[longmemeval-judge] {len(rows)} rows ({n_null} null strict labels) -> {out_dir}",
        flush=True,
    )

    extra_body = resolve_extra_body(args.thinking)
    token_judge = build_token_judge(
        args.base_url, args.model, args.api_key, args.num_beams, args.temperature,
        extra_body, args.max_new_tokens,
    )
    sequence_judge = build_sequence_judge(args.base_url, args.model, args.api_key, extra_body)
    drive_rows(rows, token_judge, sequence_judge, token_path, sequence_path, args.resume)

    labels, max_scores, mean_scores, failed, skipped_null = _token_aggregates(rows, token_path)
    seq_labels, seq_scores = _sequence_scores(rows, sequence_path)
    metrics = {
        "token_judge_max": ranker_metrics(labels, max_scores),
        "token_judge_mean": ranker_metrics(labels, mean_scores),
        "sequence_judge": ranker_metrics(seq_labels, seq_scores),
        "failed_samples": failed,
        "n_null_strict_label": n_null,
        "params": {
            "num_beams": args.num_beams,
            "max_new_tokens": args.max_new_tokens,
            "temperature": args.temperature,
            "limit": args.limit,
            "thinking": args.thinking,
        },
        "provenance": {
            "dataset_parquet": str(args.dataset_parquet),
            "model": args.model,
            "base_url": args.base_url,
            "n_rows": len(rows),
            "prompt_reconstruction": "prompt_user (question + retrieved memories) as user; "
            "prompt_assistant as answer",
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
