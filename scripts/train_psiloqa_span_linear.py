#!/usr/bin/env python
"""Train the demo PsiloQA span probe and package a live SIRIN checkpoint.

The fast first stage retrains hidden-state index 18 from the existing feature
cache.  It publishes a usable checkpoint before the held-out test pass so the
UI can be integrated while evaluation continues.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import os
import shutil
import subprocess
import sys
import time
from concurrent.futures import ThreadPoolExecutor
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Iterable, Sequence

import joblib
import numpy as np
import torch
from datasets import Dataset, DatasetDict, load_from_disk
from sklearn.model_selection import GroupShuffleSplit
from transformers import AutoTokenizer

from sirin.metrics.span import (
    character_scores,
    f1_optimal_threshold,
    span_classification_metrics,
    span_labels,
    token_labels,
)


MODEL_ID = "Qwen/Qwen3-4B"
MODEL_REVISION = "1cfa9a7208912126459214e8b04321603b3df60c"
DATASET_PATH = Path(
    "/home/jovyan/ybelikova/sirin-final/data/datasets/psiloqa_en_span"
)
LEGACY_CACHE = Path(
    "/home/jovyan/ybelikova/sirin-final/data/cache_psiloqa_span/feature_cache"
    "/Qwen/Qwen3-4B"
)
CHECKPOINT_DIR = Path("demo/checkpoints/qwen3_4b_psiloqa_span_linear")
OUTPUT_DIR = Path("output/sirin_a_star_demo/psiloqa_span/experiment")
JANOWO_INDEX = 825
JANOWO_ID = "psiloqa_NousResearch/Nous-Hermes-2-Mistral-7B-DPO_20972"
LAYERS = (6, 12, 18, 24, 30, 36)
SEEDS = (13, 42, 2026)
SHARD_FORMAT_VERSION = 2  # v2 adds per-answer-token UE scalars alongside hidden states
UE_SCALAR_COLUMNS = ("logp_realized", "max_logp_vocab", "entropy_vocab")


def resolve_layers(
    model_id: str, revision: str, layers: str, local_files_only: bool
) -> tuple[int, ...]:
    """Six hidden-state indices to probe. ``auto`` derives round(i*L/6) for i=1..6
    from the model config, tolerating Qwen3.5's nested ``text_config``."""
    if layers != "auto":
        return tuple(int(part) for part in layers.split(","))
    from transformers import AutoConfig

    config = AutoConfig.from_pretrained(
        model_id, revision=revision, local_files_only=local_files_only
    )
    inner = getattr(config, "text_config", config)
    depth = int(inner.num_hidden_layers)
    return tuple(round(index * depth / 6) for index in range(1, 7))


@dataclass(frozen=True)
class Alignment:
    rendered: str
    input_ids: list[int]
    answer_indices: list[int]
    offsets: list[tuple[int, int]]


@dataclass
class RowFeatures:
    dataset_index: int
    sample_id: str
    answer: str
    spans: list[list[int]]
    offsets: list[tuple[int, int]]
    features: np.ndarray
    ue_scalars: np.ndarray | None = None  # (n_answer_tokens, 3) fp32; None for legacy shards


@dataclass
class Bundle:
    name: str
    rows: list[RowFeatures]
    features: np.ndarray
    labels: np.ndarray
    starts: np.ndarray


def prompt(row: dict) -> str:
    return row["input"][0]["content"]


def prompt_disjoint_indices(
    dataset: DatasetDict, seed: int = 42
) -> tuple[list[int], list[int], list[int]]:
    test_prompts = {prompt(row) for row in dataset["test"]}
    eligible = [
        index
        for index, row in enumerate(dataset["train"])
        if prompt(row) not in test_prompts
    ]
    groups = [prompt(dataset["train"][index]) for index in eligible]
    train_pos, val_pos = next(
        GroupShuffleSplit(n_splits=1, test_size=0.1, random_state=seed).split(
            np.arange(len(eligible)), groups=groups
        )
    )
    train = [eligible[int(index)] for index in train_pos]
    val = [eligible[int(index)] for index in val_pos]
    test = list(range(len(dataset["test"])))
    if len(dataset["train"]) == 3000 and (len(train), len(val)) != (2676, 298):
        raise AssertionError(f"unexpected corrected split: {len(train)}/{len(val)}")
    train_prompts = {prompt(dataset["train"][index]) for index in train}
    val_prompts = {prompt(dataset["train"][index]) for index in val}
    if train_prompts & val_prompts or (train_prompts | val_prompts) & test_prompts:
        raise AssertionError("prompt leakage remains after grouped split")
    return train, val, test


def align(tokenizer, sample: list[dict]) -> Alignment:
    encoded_pair = tokenizer(
        *[message["content"] for message in sample],
        padding=False,
        truncation=False,
        add_special_tokens=True,
    )
    rendered = tokenizer.decode(encoded_pair["input_ids"], skip_special_tokens=False)
    answer = sample[-1]["content"]
    answer_start = rendered.rfind(answer)
    if answer_start < 0:
        raise ValueError("assistant answer is absent from Qwen's rendered input")
    answer_end = answer_start + len(answer)
    encoded = tokenizer(
        rendered,
        add_special_tokens=False,
        return_offsets_mapping=True,
    )
    answer_indices: list[int] = []
    offsets: list[tuple[int, int]] = []
    for index, (start, end) in enumerate(encoded["offset_mapping"]):
        if end <= answer_start or start >= answer_end:
            continue
        answer_indices.append(index)
        offsets.append(
            (max(start, answer_start) - answer_start, min(end, answer_end) - answer_start)
        )
    character_scores(answer, offsets, np.zeros(len(offsets)))
    return Alignment(rendered, encoded["input_ids"], answer_indices, offsets)


def _sample_hash(sample: list[dict]) -> str:
    return hashlib.md5(json.dumps(sample, sort_keys=True).encode()).hexdigest()[:12]


def _load_cached_row(item) -> RowFeatures:
    dataset_index, row, alignment, layer, cache_dir = item
    cache_path = cache_dir / f"hidden_{_sample_hash(row['input'])}_layer_{layer}.pkl"
    cached = joblib.load(cache_path)
    full = np.asarray(cached["features"])
    if full.shape[0] != len(alignment.input_ids):
        raise ValueError(
            f"cached/tokenized length mismatch for {row['id']}: "
            f"{full.shape[0]} != {len(alignment.input_ids)}"
        )
    features = full[np.asarray(alignment.answer_indices)].astype(np.float16, copy=True)
    if features.shape != (len(alignment.offsets), 2560):
        raise ValueError(f"unexpected answer feature shape {features.shape} for {row['id']}")
    return RowFeatures(
        dataset_index=dataset_index,
        sample_id=row["id"],
        answer=row["input"][-1]["content"],
        spans=[list(span) for span in row["target"]],
        offsets=alignment.offsets,
        features=features,
    )


def cache_bundle(
    name: str,
    split: Dataset,
    indices: Sequence[int],
    tokenizer,
    layer: int = 18,
    workers: int = 24,
    cache_dir: Path = LEGACY_CACHE,
) -> Bundle:
    started = time.time()
    prepared = []
    for dataset_index in indices:
        row = split[int(dataset_index)]
        prepared.append((int(dataset_index), row, align(tokenizer, row["input"]), layer, cache_dir))
    with ThreadPoolExecutor(max_workers=workers) as pool:
        rows = list(pool.map(_load_cached_row, prepared))
    starts = np.zeros(len(rows) + 1, dtype=np.int64)
    starts[1:] = np.cumsum([len(row.offsets) for row in rows])
    features = np.concatenate([row.features for row in rows])
    labels = np.concatenate([token_labels(row.offsets, row.spans) for row in rows])
    print(
        f"[{name}] loaded {len(rows)} rows/{len(features)} answer tokens from L{layer} "
        f"cache in {time.time() - started:.1f}s",
        flush=True,
    )
    return Bundle(name, rows, features, labels, starts)


def scaler_stats(features: np.ndarray) -> tuple[float, float]:
    values = features.astype(np.float32)
    mean = float(values.mean(dtype=np.float64))
    scale = float(values.std(dtype=np.float64))
    if not np.isfinite(mean) or not np.isfinite(scale) or scale <= 0:
        raise ValueError(f"invalid StandardScaler statistics: mean={mean}, scale={scale}")
    return mean, scale


def train_head(
    train: Bundle,
    mean: float,
    scale: float,
    seed: int,
    device: str,
    epochs: int = 5,
    batch_size: int = 4096,
) -> dict:
    torch.manual_seed(seed)
    torch.cuda.manual_seed_all(seed)
    x = torch.from_numpy(train.features).to(device)
    y = torch.from_numpy(train.labels.astype(np.float32)).to(device)
    model = torch.nn.Linear(x.shape[1], 1).to(device)
    optimizer = torch.optim.Adam(model.parameters(), lr=1e-3)
    loss_fn = torch.nn.BCEWithLogitsLoss()
    generator = torch.Generator(device=device).manual_seed(seed)
    for _ in range(epochs):
        order = torch.randperm(len(x), generator=generator, device=device)
        for start in range(0, len(x), batch_size):
            indices = order[start : start + batch_size]
            logits = model((x[indices].float() - mean) / scale).squeeze(-1)
            loss = loss_fn(logits, y[indices])
            optimizer.zero_grad(set_to_none=True)
            loss.backward()
            optimizer.step()
    return {
        "weight": model.weight.detach().cpu(),
        "bias": model.bias.detach().cpu(),
        "seed": seed,
    }


def token_scores(bundle: Bundle, head: dict, mean: float, scale: float, device: str) -> np.ndarray:
    model = torch.nn.Linear(bundle.features.shape[1], 1).to(device)
    model.weight.data.copy_(head["weight"].to(device))
    model.bias.data.copy_(head["bias"].to(device))
    result = []
    x = torch.from_numpy(bundle.features).to(device)
    with torch.inference_mode():
        for start in range(0, len(x), 8192):
            logits = model((x[start : start + 8192].float() - mean) / scale)
            result.append(torch.sigmoid(logits).squeeze(-1).cpu().numpy())
    return np.concatenate(result).astype(np.float64)


def char_arrays(bundle: Bundle, scores: np.ndarray) -> tuple[list[np.ndarray], list[np.ndarray]]:
    probabilities, labels = [], []
    for index, row in enumerate(bundle.rows):
        row_scores = scores[bundle.starts[index] : bundle.starts[index + 1]]
        probabilities.append(character_scores(row.answer, row.offsets, row_scores))
        labels.append(span_labels(len(row.answer), row.spans))
    return probabilities, labels


def metrics(bundle: Bundle, scores: np.ndarray, threshold: float) -> dict:
    per_scores, per_labels = char_arrays(bundle, scores)
    return span_classification_metrics(per_labels, per_scores, threshold)


def runs(values: np.ndarray) -> list[list[int]]:
    padded = np.pad(values.astype(np.int8), (1, 1))
    edges = np.flatnonzero(np.diff(padded))
    return [[int(start), int(end)] for start, end in edges.reshape(-1, 2)]


def janowo_result(bundle: Bundle, scores: np.ndarray, threshold: float) -> dict:
    if len(bundle.rows) != 1 or bundle.rows[0].sample_id != JANOWO_ID:
        raise ValueError("Janowo bundle contract violated")
    row = bundle.rows[0]
    char_score = character_scores(row.answer, row.offsets, scores)
    truth = span_labels(len(row.answer), row.spans)
    prediction = char_score > threshold
    predicted_runs = runs(prediction)
    true_positive_runs = runs(prediction & truth.astype(bool))
    false_positive_runs = sum(
        not truth[start:end].any() for start, end in predicted_runs
    )
    union = np.logical_or(prediction, truth).sum()
    iou = 1.0 if union == 0 else float(np.logical_and(prediction, truth).sum() / union)
    result = {
        "dataset_index": JANOWO_INDEX,
        "id": row.sample_id,
        "answer_length": len(row.answer),
        "gold_spans": row.spans,
        "predicted_spans": predicted_runs,
        "predicted_span_scores": [
            {
                "span": [start, end],
                "text": row.answer[start:end],
                "mean_score": float(char_score[start:end].mean()),
                "max_score": float(char_score[start:end].max()),
            }
            for start, end in predicted_runs
        ],
        "iou": iou,
        "dominant_true_positive_chars": max(
            (end - start for start, end in true_positive_runs), default=0
        ),
        "false_positive_runs": int(false_positive_runs),
    }
    result["passes_demo_gate"] = bool(
        iou >= 0.85
        and result["dominant_true_positive_chars"] >= 100
        and false_positive_runs <= 2
    )
    return result


def _sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for block in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def _json(path: Path, value: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(value, indent=2, ensure_ascii=False, sort_keys=True) + "\n")


def package_checkpoint(
    head: dict,
    mean: float,
    scale: float,
    layer: int,
    threshold: float,
    provenance: dict,
    result_metrics: dict,
    janowo: dict,
    checkpoint_dir: Path = CHECKPOINT_DIR,
    model_id: str = MODEL_ID,
    model_revision: str = MODEL_REVISION,
    hidden_dim: int = 2560,
) -> None:
    from sirin.definitions import CompressionMethod, ScalingMethod
    from sirin.detection.probing.preprocessing import FeaturePreprocessor
    from sirin.detection.probing.preprocessing.scalers import StandardScaler
    from sirin.models.detection import CompressionConfig, ProbingDetectorConfig
    from sirin.utils.config_serialization import serialize_probing_detector_config

    temp = checkpoint_dir.with_name(checkpoint_dir.name + f".tmp-{os.getpid()}")
    shutil.rmtree(temp, ignore_errors=True)
    temp.mkdir(parents=True)
    torch.save(
        {
            "model_state_dict": {"weight": head["weight"], "bias": head["bias"]},
            "layer_classifiers_dicts": [{}],
        },
        temp / "model.pt",
    )
    config = ProbingDetectorConfig(
        threshold=threshold,
        threshold_method="f1_optimal",
        seed=int(head["seed"]),
        embedding_dim=[hidden_dim],
        num_features=[1],
        attention_pooling=[False],
        ensemble=[],
        compression=CompressionConfig(
            method=CompressionMethod.NONE,
            scaling_method=ScalingMethod.STANDARD,
        ),
    )
    joblib.dump(serialize_probing_detector_config(config, threshold), temp / "config.joblib")
    scaler = StandardScaler()
    scaler.mean_ = np.asarray([[[[mean]]]], dtype=np.float32)
    scaler.scale_ = np.asarray([[[[scale]]]], dtype=np.float32)
    scaler.is_fitted = True
    preprocessor = FeaturePreprocessor(
        method=CompressionMethod.NONE,
        scaling_method=ScalingMethod.STANDARD,
        random_state=int(head["seed"]),
    )
    preprocessor.is_fitted = True
    preprocessor.feature_shapes = [(provenance["split"]["n_train_tokens"], 1, 1, hidden_dim)]
    preprocessor.feature_n_features = [hidden_dim]
    preprocessor.scalers = [scaler]
    preprocessor._compressors = [None]
    preprocessor._needs_compression = False
    preprocessor._scaling_stats_list = []
    preprocessor.save(str(temp / "compressor"))
    manifest = {
        "schema_version": 1,
        "detector": "token_linear_probe",
        "checkpoint_format": "sirin_token_linear_v1",
        "model_id": model_id,
        "model_revision": model_revision,
        "hidden_state_index": int(layer),
        "use_chat_template": False,
        "threshold": float(threshold),
        "threshold_method": "validation_f1_optimal",
        "score_semantics": "sigmoid_score_not_calibrated_probability",
        "dataset": "psiloqa_en_span",
        "selected_seed": int(head["seed"]),
        "janowo": janowo,
        "files": {
            "model": "model.pt",
            "detector_config": "config.joblib",
            "preprocessor_config": "compressor_config.joblib",
            "scaler": "compressor_scaler_0.joblib",
            "provenance": "provenance.json",
            "metrics": "metrics.json",
        },
    }
    _json(temp / "manifest.json", manifest)
    _json(temp / "provenance.json", provenance)
    _json(temp / "metrics.json", result_metrics)
    files = sorted(path for path in temp.iterdir() if path.name != "SHA256SUMS")
    (temp / "SHA256SUMS").write_text(
        "".join(f"{_sha256(path)}  {path.name}\n" for path in files)
    )
    shutil.rmtree(checkpoint_dir, ignore_errors=True)
    temp.rename(checkpoint_dir)


def update_output(
    provenance: dict,
    result_metrics: dict,
    checkpoint_dir: Path = CHECKPOINT_DIR,
    output_dir: Path = OUTPUT_DIR,
) -> None:
    output_dir.mkdir(parents=True, exist_ok=True)
    _json(output_dir / "provenance.json", provenance)
    _json(output_dir / "metrics.json", result_metrics)
    shutil.copy2(checkpoint_dir / "SHA256SUMS", output_dir / "checkpoint_SHA256SUMS")


def _sweep_records(dataset: DatasetDict) -> list[tuple[str, int, dict]]:
    train, validation, test = prompt_disjoint_indices(dataset)
    return (
        [("train", index, dataset["train"][index]) for index in train]
        + [("validation", index, dataset["train"][index]) for index in validation]
        + [("test", index, dataset["test"][index]) for index in test]
    )


def _ue_scalars(logits_row: torch.Tensor, answer_indices: torch.Tensor, realized: torch.Tensor) -> np.ndarray:
    """Per-answer-token UE scalars from teacher-forced logits (fp32, memory-bounded).

    Token at sequence position p is predicted by logits at p-1; we gather only the
    predictor rows so full-vocab float32 is materialised for the answer span alone.
    Returns (n_answer_tokens, 3): logp_realized, max_logp_vocab, entropy_vocab.
    """
    predictor = answer_indices - 1
    if int(predictor.min()) < 0:
        raise ValueError("answer token at sequence position 0 has no predictor logits")
    logprobs = torch.log_softmax(logits_row[predictor].float(), dim=-1)
    logp_realized = logprobs.gather(-1, realized[:, None]).squeeze(-1)
    max_logp = logprobs.max(dim=-1).values
    entropy = -(logprobs.exp() * logprobs).sum(dim=-1)
    return torch.stack([logp_realized, max_logp, entropy], dim=1).float().cpu().numpy()


def extract_worker(args) -> None:
    from transformers import AutoModelForCausalLM

    torch.set_grad_enabled(False)
    model_id, revision = args.model_id, args.revision
    layers = resolve_layers(model_id, revision, args.layers, args.local_files_only)
    dataset = load_from_disk(str(args.dataset))
    tokenizer = AutoTokenizer.from_pretrained(
        model_id, revision=revision, local_files_only=args.local_files_only
    )
    tokenizer.padding_side = "right"
    records = _sweep_records(dataset)[args.rank :: args.world_size]
    if args.limit is not None:
        records = records[: args.limit]
    prepared = [
        (split, index, row, align(tokenizer, row["input"]))
        for split, index, row in records
    ]
    prepared.sort(key=lambda item: len(item[3].input_ids))
    model = AutoModelForCausalLM.from_pretrained(
        model_id,
        revision=revision,
        local_files_only=args.local_files_only,
        dtype=torch.bfloat16,
        attn_implementation="sdpa",
    ).to("cuda:0")
    model.eval()
    chunks: list[np.ndarray] = []
    ue_chunks: list[np.ndarray] = []
    metadata = []
    cursor = 0
    for batch_start in range(0, len(prepared), args.extraction_batch_size):
        batch = prepared[batch_start : batch_start + args.extraction_batch_size]
        encoded = tokenizer(
            [item[3].rendered for item in batch],
            add_special_tokens=False,
            padding=True,
            return_tensors="pt",
        ).to("cuda:0")
        outputs = model(**encoded, output_hidden_states=True, use_cache=False)
        for row_index, (split, dataset_index, row, alignment) in enumerate(batch):
            valid_ids = encoded["input_ids"][row_index, : len(alignment.input_ids)].tolist()
            if valid_ids != alignment.input_ids:
                raise ValueError(f"batched tokenization changed row {row['id']}")
            answer_indices = torch.as_tensor(
                alignment.answer_indices, dtype=torch.long, device="cuda:0"
            )
            hidden = torch.stack(
                [outputs.hidden_states[layer][row_index, answer_indices] for layer in layers],
                dim=1,
            ).to(dtype=torch.float16, device="cpu").numpy()
            chunks.append(hidden)
            realized = encoded["input_ids"][row_index, answer_indices]
            ue_chunks.append(_ue_scalars(outputs.logits[row_index], answer_indices, realized))
            end = cursor + len(hidden)
            metadata.append(
                {
                    "split": split,
                    "dataset_index": int(dataset_index),
                    "id": row["id"],
                    "answer": row["input"][-1]["content"],
                    "spans": [list(span) for span in row["target"]],
                    "offsets": [list(offset) for offset in alignment.offsets],
                    "start": cursor,
                    "end": end,
                }
            )
            cursor = end
        del outputs, encoded
    shard = args.shard_dir / f"rank_{args.rank:02d}"
    shard.mkdir(parents=True, exist_ok=True)
    np.save(shard / "features.npy", np.concatenate(chunks))
    np.save(shard / "ue_scalars.npy", np.concatenate(ue_chunks))
    _json(
        shard / "metadata.json",
        {
            "shard_format_version": SHARD_FORMAT_VERSION,
            "rank": args.rank,
            "world_size": args.world_size,
            "model_id": model_id,
            "model_revision": revision,
            "layers": list(layers),
            "ue_scalar_columns": list(UE_SCALAR_COLUMNS),
            "rows": metadata,
        },
    )
    print(f"[worker {args.rank}] {len(metadata)} rows/{cursor} tokens", flush=True)


def launch_extraction(args) -> None:
    shutil.rmtree(args.shard_dir, ignore_errors=True)
    args.shard_dir.mkdir(parents=True)
    processes = []
    script = str(Path(__file__).resolve())
    for rank, gpu in enumerate(args.gpus.split(",")):
        log_path = args.shard_dir / f"worker_{rank:02d}.log"
        log = log_path.open("w")
        command = [
            sys.executable,
            "-u",
            script,
            "--stage",
            "extract-worker",
            "--dataset",
            str(args.dataset),
            "--model-id",
            args.model_id,
            "--revision",
            args.revision,
            "--layers",
            args.layers,
            "--rank",
            str(rank),
            "--world-size",
            str(len(args.gpus.split(","))),
            "--shard-dir",
            str(args.shard_dir),
            "--extraction-batch-size",
            str(args.extraction_batch_size),
        ]
        if args.limit is not None:
            command += ["--limit", str(args.limit)]
        if args.local_files_only:
            command.append("--local-files-only")
        else:
            command.append("--no-local-files-only")
        environment = os.environ.copy()
        environment["CUDA_VISIBLE_DEVICES"] = gpu
        processes.append((rank, gpu, subprocess.Popen(command, stdout=log, stderr=subprocess.STDOUT, env=environment), log, log_path))
    pending = processes[:]
    while pending:
        time.sleep(2)
        for item in pending[:]:
            rank, gpu, process, log, log_path = item
            if process.poll() is None:
                continue
            log.close()
            pending.remove(item)
            if process.returncode:
                raise RuntimeError(
                    f"GPU {gpu} extraction worker {rank} failed; see {log_path}"
                )
            print(f"[extract] worker {rank}/GPU {gpu} complete", flush=True)


def shard_bundle(name: str, shard_dir: Path, layer_position: int) -> Bundle:
    rows: list[RowFeatures] = []
    arrays = []
    for metadata_path in sorted(shard_dir.glob("rank_*/metadata.json")):
        metadata = json.loads(metadata_path.read_text())
        features = np.load(metadata_path.with_name("features.npy"), mmap_mode="r")
        ue_path = metadata_path.with_name("ue_scalars.npy")
        ue_all = np.load(ue_path, mmap_mode="r") if ue_path.exists() else None
        for item in metadata["rows"]:
            if item["split"] != name:
                continue
            selected = np.asarray(
                features[item["start"] : item["end"], layer_position],
                dtype=np.float16,
            ).copy()
            arrays.append(selected)
            ue_row = (
                np.asarray(ue_all[item["start"] : item["end"]], dtype=np.float32).copy()
                if ue_all is not None
                else None
            )
            rows.append(
                RowFeatures(
                    dataset_index=item["dataset_index"],
                    sample_id=item["id"],
                    answer=item["answer"],
                    spans=item["spans"],
                    offsets=[tuple(offset) for offset in item["offsets"]],
                    features=selected,
                    ue_scalars=ue_row,
                )
            )
    order = np.argsort([row.dataset_index for row in rows], kind="stable")
    rows = [rows[int(index)] for index in order]
    arrays = [arrays[int(index)] for index in order]
    starts = np.zeros(len(rows) + 1, dtype=np.int64)
    starts[1:] = np.cumsum([len(array) for array in arrays])
    features = np.concatenate(arrays)
    labels = np.concatenate([token_labels(row.offsets, row.spans) for row in rows])
    return Bundle(name, rows, features, labels, starts)


def ranked_cases(
    bundle: Bundle, scores: np.ndarray, threshold: float, dataset: Dataset
) -> list[dict]:
    reports = []
    for index, row in enumerate(bundle.rows):
        row_token_scores = scores[bundle.starts[index] : bundle.starts[index + 1]]
        char_score = character_scores(row.answer, row.offsets, row_token_scores)
        truth = span_labels(len(row.answer), row.spans).astype(bool)
        prediction = char_score > threshold
        predicted_runs = runs(prediction)
        true_positive_runs = runs(prediction & truth)
        union = np.logical_or(prediction, truth).sum()
        iou = 1.0 if union == 0 else float(np.logical_and(prediction, truth).sum() / union)
        false_positives = sum(
            not truth[start:end].any() for start, end in predicted_runs
        )
        dominant = max((end - start for start, end in true_positive_runs), default=0)
        if len(row.answer) < 450 or iou < 0.85 or dominant < 100 or false_positives > 2:
            continue
        raw = dataset[row.dataset_index]
        reports.append(
            {
                "dataset_index": row.dataset_index,
                "id": row.sample_id,
                "input": raw["input"],
                "context": raw["input"][0]["content"],
                "question": raw["question"],
                "answer": row.answer,
                "answer_length": len(row.answer),
                "gold_spans": row.spans,
                "predicted_spans": predicted_runs,
                "predicted_span_scores": [
                    {
                        "span": [start, end],
                        "text": row.answer[start:end],
                        "mean_score": float(char_score[start:end].mean()),
                        "max_score": float(char_score[start:end].max()),
                    }
                    for start, end in predicted_runs
                ],
                "token_offsets": [list(offset) for offset in row.offsets],
                "token_scores": [float(score) for score in row_token_scores],
                "iou": iou,
                "dominant_true_positive_chars": int(dominant),
                "false_positive_runs": int(false_positives),
                "predicted_runs": len(predicted_runs),
                "predicted_coverage": float(prediction.mean()),
            }
        )
    localized = [
        report
        for report in reports
        if 0.15 <= report["predicted_coverage"] <= 0.75
        and report["predicted_runs"] <= 4
    ]
    key = lambda report: (
        -report["false_positive_runs"],
        -report["predicted_runs"],
        report["iou"],
        min(report["answer_length"], 900),
        report["dominant_true_positive_chars"],
    )
    localized.sort(key=key, reverse=True)
    remaining = sorted(
        (report for report in reports if report not in localized),
        key=key,
        reverse=True,
    )
    return localized + remaining


def run_sweep(args) -> None:
    started = time.time()
    layers = resolve_layers(args.model_id, args.revision, args.layers, args.local_files_only)
    if not args.skip_extraction:
        launch_extraction(args)
    dataset = load_from_disk(str(args.dataset))
    layer_candidates = []
    for layer_position, layer in enumerate(layers):
        train = shard_bundle("train", args.shard_dir, layer_position)
        validation = shard_bundle("validation", args.shard_dir, layer_position)
        mean, scale = scaler_stats(train.features)
        seed_candidates = []
        for seed in SEEDS:
            head = train_head(train, mean, scale, seed, args.device, args.epochs)
            scores = token_scores(validation, head, mean, scale, args.device)
            per_scores, per_labels = char_arrays(validation, scores)
            threshold = f1_optimal_threshold(
                np.concatenate(per_labels), np.concatenate(per_scores)
            )
            seed_candidates.append(
                {
                    "head": head,
                    "threshold": threshold,
                    "validation": metrics(validation, scores, threshold),
                }
            )
        layer_candidates.append(
            {
                "layer": layer,
                "mean": mean,
                "scale": scale,
                "seeds": seed_candidates,
                "mean_ap": float(
                    np.mean([item["validation"]["average_precision"] for item in seed_candidates])
                ),
                "mean_iou": float(
                    np.mean([item["validation"]["mean_per_answer_iou"] for item in seed_candidates])
                ),
            }
        )
        print(
            f"[sweep L{layer}] mean validation AP={layer_candidates[-1]['mean_ap']:.6f} "
            f"IoU={layer_candidates[-1]['mean_iou']:.6f}",
            flush=True,
        )
        del train, validation
    selected_layer = max(
        layer_candidates,
        key=lambda item: (item["mean_ap"], item["mean_iou"], -item["layer"]),
    )
    selected = max(
        selected_layer["seeds"],
        key=lambda item: (
            item["validation"]["average_precision"],
            item["validation"]["mean_per_answer_iou"],
            -item["head"]["seed"],
        ),
    )
    layer_position = layers.index(selected_layer["layer"])
    test = shard_bundle("test", args.shard_dir, layer_position)
    test_scores = token_scores(
        test, selected["head"], selected_layer["mean"], selected_layer["scale"], args.device
    )
    test_metrics = metrics(test, test_scores, selected["threshold"])
    janowo_position = next(
        index for index, row in enumerate(test.rows) if row.dataset_index == JANOWO_INDEX
    )
    janowo_bundle = Bundle(
        "janowo",
        [test.rows[janowo_position]],
        test.features[test.starts[janowo_position] : test.starts[janowo_position + 1]],
        test.labels[test.starts[janowo_position] : test.starts[janowo_position + 1]],
        np.asarray([0, test.starts[janowo_position + 1] - test.starts[janowo_position]]),
    )
    janowo_scores = test_scores[test.starts[janowo_position] : test.starts[janowo_position + 1]]
    janowo_report = janowo_result(janowo_bundle, janowo_scores, selected["threshold"])
    ranked = ranked_cases(test, test_scores, selected["threshold"], dataset["test"])
    split = prompt_disjoint_indices(dataset)
    provenance = {
        "status": "ok",
        "dataset_path": str(args.dataset),
        "dataset": "psiloqa_en_span",
        "model_id": args.model_id,
        "model_revision": args.revision,
        "use_chat_template": False,
        "hidden_state_candidates": list(layers),
        "completed_hidden_state_candidates": list(layers),
        "selected_hidden_state_index": selected_layer["layer"],
        "head_seeds": list(SEEDS),
        "selected_seed": selected["head"]["seed"],
        "selection": "layer_mean_validation_character_AP_then_IoU; seed_validation_character_AP_then_IoU_then_lowest_seed",
        "threshold_method": "validation_f1_optimal",
        "alignment": "absolute_half_open_answer_character_offsets; exact_coverage_required",
        "scaling": {
            "method": "StandardScaler",
            "mean": selected_layer["mean"],
            "scale": selected_layer["scale"],
        },
        "compression": "none",
        "training": {"optimizer": "Adam", "learning_rate": 0.001, "epochs": args.epochs},
        "split": {
            "strategy": "drop_test_prompt_matches_then_group_shuffle_split",
            "split_seed": 42,
            "n_removed_test_prompt_matches": 26,
            "n_train": len(split[0]),
            "n_validation": len(split[1]),
            "n_test": len(split[2]),
            "n_train_tokens": int(sum(
                item["end"] - item["start"]
                for path in args.shard_dir.glob("rank_*/metadata.json")
                for item in json.loads(path.read_text())["rows"]
                if item["split"] == "train"
            )),
        },
        "gpus": args.gpus.split(","),
        "seconds": round(time.time() - started, 3),
    }
    result_metrics = {
        "status": "ok",
        "selected_layer": selected_layer["layer"],
        "selected_seed": selected["head"]["seed"],
        "threshold": selected["threshold"],
        "layer_selection": {
            str(item["layer"]): {
                "mean_validation_average_precision": item["mean_ap"],
                "mean_validation_iou": item["mean_iou"],
                "seeds": {
                    str(seed["head"]["seed"]): seed["validation"] for seed in item["seeds"]
                },
            }
            for item in layer_candidates
        },
        "validation": selected["validation"],
        "test": test_metrics,
        "janowo": janowo_report,
        "selected_demo_case": ranked[0] if ranked else None,
    }
    checkpoint_dir = (
        args.checkpoint_dir
        if args.promote
        else args.checkpoint_dir.with_name(args.checkpoint_dir.name + "_candidate")
    )
    package_checkpoint(
        selected["head"], selected_layer["mean"], selected_layer["scale"],
        selected_layer["layer"], selected["threshold"], provenance,
        result_metrics, janowo_report, checkpoint_dir,
        model_id=args.model_id, model_revision=args.revision,
        hidden_dim=test.features.shape[1],
    )
    update_output(provenance, result_metrics, checkpoint_dir, args.output_dir)
    _json(
        args.output_dir / "top5_demo_cases.json",
        {
            "threshold": selected["threshold"],
            "selected_layer": selected_layer["layer"],
            "ranking_policy": "held-out; answer>=450; IoU>=.85; dominant TP>=100; FP<=2; localized 15-75% first, then fewer FP/runs, IoU/length",
            "top5": ranked[:5],
        },
    )
    print(json.dumps({
        "selected_layer": selected_layer["layer"],
        "selected_seed": selected["head"]["seed"],
        "threshold": selected["threshold"],
        "test": test_metrics,
        "selected_case": ranked[0]["id"] if ranked else None,
    }, indent=2), flush=True)


def run_l18(args) -> None:
    started = time.time()
    layers = resolve_layers(args.model_id, args.revision, args.layers, args.local_files_only)
    dataset = load_from_disk(str(args.dataset))
    train_indices, val_indices, test_indices = prompt_disjoint_indices(dataset)
    tokenizer = AutoTokenizer.from_pretrained(
        args.model_id, revision=args.revision, local_files_only=args.local_files_only
    )
    train = cache_bundle(
        "train", dataset["train"], train_indices, tokenizer,
        workers=args.workers, cache_dir=args.feature_cache_dir,
    )
    val = cache_bundle(
        "validation", dataset["train"], val_indices, tokenizer,
        workers=args.workers, cache_dir=args.feature_cache_dir,
    )
    janowo = cache_bundle(
        "janowo", dataset["test"], [JANOWO_INDEX], tokenizer,
        workers=1, cache_dir=args.feature_cache_dir,
    )
    if janowo.rows[0].sample_id != JANOWO_ID:
        raise AssertionError(f"test index {JANOWO_INDEX} is no longer Janowo")
    mean, scale = scaler_stats(train.features)
    candidates = []
    for seed in SEEDS:
        head = train_head(train, mean, scale, seed, args.device, args.epochs)
        val_scores = token_scores(val, head, mean, scale, args.device)
        val_char_scores, val_char_labels = char_arrays(val, val_scores)
        flat_scores = np.concatenate(val_char_scores)
        flat_labels = np.concatenate(val_char_labels)
        threshold = f1_optimal_threshold(flat_labels, flat_scores)
        candidate = {
            "head": head,
            "threshold": threshold,
            "validation": metrics(val, val_scores, threshold),
        }
        candidates.append(candidate)
        print(
            f"[L18 seed={seed}] validation AP={candidate['validation']['average_precision']:.6f} "
            f"IoU={candidate['validation']['mean_per_answer_iou']:.6f} "
            f"threshold={threshold:.9f}",
            flush=True,
        )
    selected = max(
        candidates,
        key=lambda item: (
            item["validation"]["average_precision"],
            item["validation"]["mean_per_answer_iou"],
            -item["head"]["seed"],
        ),
    )
    janowo_scores = token_scores(janowo, selected["head"], mean, scale, args.device)
    janowo_report = janowo_result(janowo, janowo_scores, selected["threshold"])
    split_record = {
        "strategy": "drop_test_prompt_matches_then_group_shuffle_split",
        "split_seed": 42,
        "n_removed_test_prompt_matches": 26,
        "n_train": len(train_indices),
        "n_validation": len(val_indices),
        "n_test": len(test_indices),
        "n_train_tokens": len(train.features),
        "n_validation_tokens": len(val.features),
    }
    provenance = {
        "status": "checkpoint_ready_test_pending",
        "dataset_path": str(args.dataset),
        "dataset": "psiloqa_en_span",
        "model_id": args.model_id,
        "model_revision": args.revision,
        "use_chat_template": False,
        "hidden_state_candidates": list(layers),
        "completed_hidden_state_candidates": [18],
        "selected_hidden_state_index": 18,
        "head_seeds": list(SEEDS),
        "selected_seed": int(selected["head"]["seed"]),
        "selection": "layer_mean_validation_character_AP_then_IoU; seed_validation_character_AP_then_IoU_then_lowest_seed",
        "threshold_method": "validation_f1_optimal",
        "alignment": "absolute_half_open_answer_character_offsets; exact_coverage_required",
        "scaling": {"method": "StandardScaler", "mean": mean, "scale": scale},
        "compression": "none",
        "training": {"optimizer": "Adam", "learning_rate": 0.001, "epochs": args.epochs},
        "split": split_record,
        "started_unix": started,
    }
    result_metrics = {
        "status": "checkpoint_ready_test_pending",
        "selected_layer": 18,
        "selected_seed": int(selected["head"]["seed"]),
        "threshold": float(selected["threshold"]),
        "validation_by_seed": {
            str(item["head"]["seed"]): item["validation"] for item in candidates
        },
        "validation": selected["validation"],
        "janowo": janowo_report,
    }
    package_checkpoint(
        selected["head"], mean, scale, 18, selected["threshold"], provenance,
        result_metrics, janowo_report, args.checkpoint_dir,
        model_id=args.model_id, model_revision=args.revision,
        hidden_dim=train.features.shape[1],
    )
    update_output(provenance, result_metrics, args.checkpoint_dir, args.output_dir)
    print(f"[CHECKPOINT_READY] {args.checkpoint_dir.resolve()}", flush=True)

    test = cache_bundle(
        "test", dataset["test"], test_indices, tokenizer,
        workers=args.workers, cache_dir=args.feature_cache_dir,
    )
    test_scores = token_scores(test, selected["head"], mean, scale, args.device)
    result_metrics["test"] = metrics(test, test_scores, selected["threshold"])
    result_metrics["status"] = "ok_l18_interim"
    provenance["status"] = "ok_l18_interim"
    provenance["split"]["n_test_tokens"] = len(test.features)
    provenance["seconds"] = round(time.time() - started, 3)
    package_checkpoint(
        selected["head"], mean, scale, 18, selected["threshold"], provenance,
        result_metrics, janowo_report, args.checkpoint_dir,
        model_id=args.model_id, model_revision=args.revision,
        hidden_dim=train.features.shape[1],
    )
    update_output(provenance, result_metrics, args.checkpoint_dir, args.output_dir)
    print(json.dumps(result_metrics, indent=2), flush=True)


def parse_args():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--stage", choices=("l18", "sweep", "extract-worker"), default="l18")
    parser.add_argument("--dataset", type=Path, default=DATASET_PATH)
    parser.add_argument("--model-id", default=MODEL_ID)
    parser.add_argument("--revision", default=MODEL_REVISION)
    parser.add_argument(
        "--layers", default="auto",
        help="'auto' derives round(i*L/6) for i=1..6 from the model config, else a comma list",
    )
    parser.add_argument("--feature-cache-dir", type=Path, default=LEGACY_CACHE)
    parser.add_argument("--checkpoint-dir", type=Path, default=CHECKPOINT_DIR)
    parser.add_argument("--output-dir", type=Path, default=OUTPUT_DIR)
    parser.add_argument("--device", default="cuda:0")
    parser.add_argument("--epochs", type=int, default=5)
    parser.add_argument("--workers", type=int, default=24)
    parser.add_argument("--gpus", default="0,1,2,3,4,5,6,7")
    parser.add_argument("--rank", type=int, default=0)
    parser.add_argument("--world-size", type=int, default=8)
    parser.add_argument("--limit", type=int, default=None, help="cap records per worker (smoke tests)")
    parser.add_argument(
        "--shard-dir", type=Path, default=OUTPUT_DIR / "feature_shards"
    )
    parser.add_argument("--extraction-batch-size", type=int, default=8)
    parser.add_argument("--skip-extraction", action="store_true")
    parser.add_argument("--promote", action=argparse.BooleanOptionalAction, default=True)
    parser.add_argument("--local-files-only", action=argparse.BooleanOptionalAction, default=True)
    return parser.parse_args()


if __name__ == "__main__":
    arguments = parse_args()
    if arguments.stage == "l18":
        run_l18(arguments)
    elif arguments.stage == "extract-worker":
        extract_worker(arguments)
    else:
        run_sweep(arguments)
