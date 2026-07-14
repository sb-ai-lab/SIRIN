#!/usr/bin/env python
"""P2-extras + P3 drivers: the extra probes and the UE baselines for the
PsiloQA-span @ Qwen3.5-4B campaign.

Sibling of ``demo/train_psiloqa_span_linear.py`` (imported, never edited) so the
file the live extraction+sweep has loaded on GPU is left untouched.  Two stages:

  probes : token{CatBoost, TabPFN} + sequence{Linear, CatBoost, TabPFN}
           on the best layer chosen by the linear sweep.  Token Linear is the
           sweep's own job and is intentionally not repeated here.
  ue     : token{MaximumTokenProbability, TokenEntropy}
           + sequence{MeanTokenEntropy, Perplexity} from the stored ue_scalars
           (no training).

Both stages read shards read-only via ``base.shard_bundle`` -> the prompt-disjoint
train/validation/test split is already baked into the shard metadata, so it is
identical to the sweep's.  Thresholds are f1-optimal on the VALIDATION split only.
Token-level metrics come from ``sirin.metrics.span`` (char-flat + mean-per-answer
IoU); sequence-level metrics are plain binary classification against the answer
label "has >=1 gold-span character".  Sequence features = mean-pool over the
answer tokens of the chosen layer.

Each result dir is written atomically (tmp dir -> rename); rerunning skips any
result dir that already carries a metrics.json.
"""

from __future__ import annotations

import argparse
import json
import os
import shutil
import sys
import time
from pathlib import Path

import numpy as np

sys.path.insert(0, str(Path(__file__).resolve().parent))
import train_psiloqa_span_linear as base  # noqa: E402  (same-dir sibling import)

from sirin.metrics.span import (  # noqa: E402
    f1_optimal_threshold,
    span_classification_metrics,
    span_labels,
)
from sklearn.metrics import (  # noqa: E402
    accuracy_score,
    average_precision_score,
    f1_score,
    precision_score,
    recall_score,
    roc_auc_score,
)

BASE_DIR = Path("output/psiloqa_span_qwen35_4b")
PROBE_METHODS = (
    "token_catboost",
    "token_tabpfn",
    "sequence_linear",
    "sequence_catboost",
    "sequence_tabpfn",
)
UE_METHODS = ("MaximumTokenProbability", "TokenEntropy", "MeanTokenEntropy", "Perplexity")
UE_COLUMNS = base.UE_SCALAR_COLUMNS  # ("logp_realized", "max_logp_vocab", "entropy_vocab")


# --------------------------------------------------------------------------- #
# shared helpers
# --------------------------------------------------------------------------- #
def _first_metadata(shard_dir: Path) -> dict:
    return json.loads(next(iter(sorted(shard_dir.glob("rank_*/metadata.json")))).read_text())


def shard_layers(shard_dir: Path) -> list[int]:
    return list(_first_metadata(shard_dir)["layers"])


def shard_model_info(shard_dir: Path, args) -> tuple[str, str]:
    """Authoritative model id/revision from the shard metadata; CLI overrides win."""
    metadata = _first_metadata(shard_dir)
    return (
        args.model_id or metadata.get("model_id", base.MODEL_ID),
        args.revision or metadata.get("model_revision", base.MODEL_REVISION),
    )


def resolve_layer(args) -> tuple[int, int, list[int]]:
    layers = shard_layers(args.shard_dir)
    if str(args.layer) == "best":
        metrics = json.loads(Path(args.experiment_metrics).read_text())
        layer = int(metrics["selected_layer"])
    else:
        layer = int(args.layer)
    if layer not in layers:
        raise ValueError(f"layer {layer} not among extracted layers {layers}")
    return layer, layers.index(layer), layers


def pooled_sequence_features(bundle: base.Bundle) -> np.ndarray:
    """Mean-pool the chosen layer over each answer's tokens -> (n_rows, dim)."""
    pooled = np.empty((len(bundle.rows), bundle.features.shape[1]), dtype=np.float32)
    for index in range(len(bundle.rows)):
        start, end = bundle.starts[index], bundle.starts[index + 1]
        pooled[index] = bundle.features[start:end].astype(np.float32).mean(axis=0)
    return pooled


def sequence_labels(bundle: base.Bundle) -> np.ndarray:
    return np.asarray(
        [int(span_labels(len(row.answer), row.spans).any()) for row in bundle.rows],
        dtype=np.int64,
    )


def sequence_classification_metrics(
    labels: np.ndarray, scores: np.ndarray, threshold: float
) -> dict:
    """Answer-level binary metrics mirroring the span metric names."""
    labels = np.asarray(labels)
    scores = np.asarray(scores, dtype=np.float64)
    predictions = (scores > threshold).astype(np.int64)
    single_class = len(np.unique(labels)) < 2
    return {
        "n_rows": int(len(labels)),
        "positive_rate": float(labels.mean()),
        "roc_auc": float("nan") if single_class else float(roc_auc_score(labels, scores)),
        "average_precision": float("nan")
        if single_class
        else float(average_precision_score(labels, scores)),
        "f1": float(f1_score(labels, predictions, zero_division=0)),
        "accuracy": float(accuracy_score(labels, predictions)),
        "precision": float(precision_score(labels, predictions, zero_division=0)),
        "recall": float(recall_score(labels, predictions, zero_division=0)),
    }


def token_char_metrics(bundle: base.Bundle, token_scores: np.ndarray, threshold: float) -> dict:
    per_scores, per_labels = base.char_arrays(bundle, token_scores)
    return span_classification_metrics(per_labels, per_scores, threshold)


def token_char_threshold(bundle: base.Bundle, token_scores: np.ndarray) -> float:
    per_scores, per_labels = base.char_arrays(bundle, token_scores)
    return f1_optimal_threshold(np.concatenate(per_labels), np.concatenate(per_scores))


def flat_ue(bundle: base.Bundle) -> np.ndarray:
    """Per-token ue_scalars concatenated in bundle-row order (aligned to starts)."""
    if any(row.ue_scalars is None for row in bundle.rows):
        raise ValueError("ue_scalars missing (legacy shard_format_version < 2)")
    return np.concatenate([row.ue_scalars for row in bundle.rows]).astype(np.float64)


def per_answer_ue(bundle: base.Bundle, column: int, negate: bool) -> np.ndarray:
    values = np.array(
        [float(row.ue_scalars[:, column].mean()) for row in bundle.rows], dtype=np.float64
    )
    return -values if negate else values


# --------------------------------------------------------------------------- #
# atomic result IO + resume
# --------------------------------------------------------------------------- #
def is_done(result_dir: Path) -> bool:
    return (result_dir / "metrics.json").exists()


def _sha256sums(result_dir: Path) -> None:
    files = sorted(p for p in result_dir.iterdir() if p.name != "SHA256SUMS")
    (result_dir / "SHA256SUMS").write_text(
        "".join(f"{base._sha256(path)}  {path.name}\n" for path in files)
    )


def save_estimator(kind: str, estimator, extras: dict | None, result_dir: Path) -> dict:
    """Persist the fitted model; returns the manifest ``files`` mapping."""
    import joblib

    files: dict[str, str] = {}
    if kind == "catboost":
        estimator.save_model(str(result_dir / "model.cbm"))
        files["model"] = "model.cbm"
    elif kind == "tabpfn":
        from tabpfn.model_loading import save_fitted_tabpfn_model

        save_fitted_tabpfn_model(estimator, str(result_dir / "model.tabpfn_fit"))
        files["model"] = "model.tabpfn_fit"
    else:  # linear / sklearn
        joblib.dump(estimator, result_dir / "model.joblib")
        files["model"] = "model.joblib"
    if extras:
        joblib.dump(extras, result_dir / "preproc.joblib")
        files["preproc"] = "preproc.joblib"
    return files


def write_result(result_dir: Path, payload: dict, model_kind: str, estimator, extras) -> None:
    tmp = result_dir.with_name(result_dir.name + f".tmp-{os.getpid()}")
    shutil.rmtree(tmp, ignore_errors=True)
    tmp.mkdir(parents=True)
    payload["config"]["files"] = (
        save_estimator(model_kind, estimator, extras, tmp) if estimator is not None else {}
    )
    base._json(tmp / "config.json", payload["config"])
    base._json(tmp / "provenance.json", payload["provenance"])
    base._json(tmp / "metrics.json", payload["metrics"])
    _sha256sums(tmp)
    shutil.rmtree(result_dir, ignore_errors=True)
    tmp.rename(result_dir)


# --------------------------------------------------------------------------- #
# probe trainers  (each returns payload dict + (model_kind, estimator, extras))
# --------------------------------------------------------------------------- #
def _preprocess(train_x, scale: bool, pca_components: int | None, seed: int):
    from sklearn.decomposition import PCA
    from sklearn.preprocessing import StandardScaler

    extras: dict = {}
    x = train_x
    if scale:
        scaler = StandardScaler().fit(x)
        x = scaler.transform(x)
        extras["scaler"] = scaler
    if pca_components:
        n = min(pca_components, x.shape[0] - 1, x.shape[1])
        pca = PCA(n_components=max(1, n), random_state=seed).fit(x)
        x = pca.transform(x)
        extras["pca"] = pca
    return x.astype(np.float32), extras


def _apply(extras: dict, x: np.ndarray) -> np.ndarray:
    if "scaler" in extras:
        x = extras["scaler"].transform(x)
    if "pca" in extras:
        x = extras["pca"].transform(x)
    return x.astype(np.float32)


def _subsample_tokens(bundle: base.Bundle, target: int, cap: int, seed: int) -> np.ndarray:
    rng = np.random.default_rng(seed)
    chosen = []
    for index in range(len(bundle.rows)):
        row_idx = np.arange(bundle.starts[index], bundle.starts[index + 1])
        if len(row_idx) > cap:
            row_idx = rng.choice(row_idx, cap, replace=False)
        chosen.append(row_idx)
    idx = np.concatenate(chosen)
    if len(idx) > target:
        labels = bundle.labels[idx]
        positives, negatives = idx[labels == 1], idx[labels == 0]
        n_pos = min(len(positives), int(round(target * len(positives) / len(idx))))
        n_neg = min(len(negatives), target - n_pos)
        idx = np.concatenate(
            [rng.choice(positives, n_pos, replace=False), rng.choice(negatives, n_neg, replace=False)]
        )
    return np.sort(idx)


def train_token_catboost(train, val, test, args):
    from catboost import CatBoostClassifier

    clf = CatBoostClassifier(
        iterations=args.catboost_iterations, depth=6, learning_rate=0.1,
        task_type="CPU", random_seed=args.seed, verbose=False,
    )
    clf.fit(train.features.astype(np.float32), train.labels)
    val_scores = clf.predict_proba(val.features.astype(np.float32))[:, 1]
    test_scores = clf.predict_proba(test.features.astype(np.float32))[:, 1]
    threshold = token_char_threshold(val, val_scores)
    return (
        {
            "threshold": threshold,
            "validation": token_char_metrics(val, val_scores, threshold),
            "test": token_char_metrics(test, test_scores, threshold),
            "params": {"iterations": args.catboost_iterations, "task_type": "CPU", "depth": 6},
        },
        ("catboost", clf, None),
    )


def train_token_tabpfn(train, val, test, args):
    from tabpfn import TabPFNClassifier
    import sirin.detection.probing.detectors.utils.tabpfn_compat  # noqa: F401  (shim)

    idx = _subsample_tokens(train, args.tabpfn_subsample_tokens, args.tabpfn_per_answer_cap, args.seed)
    sub_x = train.features[idx].astype(np.float32)
    sub_y = train.labels[idx]
    x, extras = _preprocess(sub_x, scale=True, pca_components=args.tabpfn_pca, seed=args.seed)
    clf = TabPFNClassifier(device=args.tabpfn_device, ignore_pretraining_limits=True, random_state=args.seed)
    clf.fit(x, sub_y)
    val_scores = clf.predict_proba(_apply(extras, val.features.astype(np.float32)))[:, 1]
    test_scores = clf.predict_proba(_apply(extras, test.features.astype(np.float32)))[:, 1]
    threshold = token_char_threshold(val, val_scores)
    return (
        {
            "threshold": threshold,
            "validation": token_char_metrics(val, val_scores, threshold),
            "test": token_char_metrics(test, test_scores, threshold),
            "params": {
                "subsample_tokens": int(len(idx)),
                "requested_subsample": args.tabpfn_subsample_tokens,
                "per_answer_cap": args.tabpfn_per_answer_cap,
                "n_rows_contributing": int(len(train.rows)),
                "pca_components": int(extras["pca"].n_components_) if "pca" in extras else None,
            },
        },
        ("tabpfn", clf, extras),
    )


def _sequence_split(train, val, test):
    return (
        (pooled_sequence_features(train), sequence_labels(train)),
        (pooled_sequence_features(val), sequence_labels(val)),
        (pooled_sequence_features(test), sequence_labels(test)),
    )


def _sequence_payload(val_scores, val_y, test_scores, test_y, params):
    threshold = f1_optimal_threshold(val_y, val_scores)
    return {
        "threshold": threshold,
        "validation": sequence_classification_metrics(val_y, val_scores, threshold),
        "test": sequence_classification_metrics(test_y, test_scores, threshold),
        "params": params,
    }


def train_sequence_linear(train, val, test, args):
    from sklearn.linear_model import LogisticRegression
    from sklearn.preprocessing import StandardScaler

    (tr_x, tr_y), (va_x, va_y), (te_x, te_y) = _sequence_split(train, val, test)
    scaler = StandardScaler().fit(tr_x)
    clf = LogisticRegression(max_iter=1000, C=1.0, random_state=args.seed)
    clf.fit(scaler.transform(tr_x), tr_y)
    val_scores = clf.predict_proba(scaler.transform(va_x))[:, 1]
    test_scores = clf.predict_proba(scaler.transform(te_x))[:, 1]
    payload = _sequence_payload(val_scores, va_y, test_scores, te_y, {"model": "LogisticRegression", "C": 1.0})
    return payload, ("linear", clf, {"scaler": scaler})


def train_sequence_catboost(train, val, test, args):
    from catboost import CatBoostClassifier

    (tr_x, tr_y), (va_x, va_y), (te_x, te_y) = _sequence_split(train, val, test)
    clf = CatBoostClassifier(
        iterations=args.catboost_iterations, depth=6, learning_rate=0.1,
        task_type="CPU", random_seed=args.seed, verbose=False,
    )
    clf.fit(tr_x, tr_y)
    val_scores = clf.predict_proba(va_x)[:, 1]
    test_scores = clf.predict_proba(te_x)[:, 1]
    payload = _sequence_payload(
        val_scores, va_y, test_scores, te_y,
        {"iterations": args.catboost_iterations, "task_type": "CPU", "depth": 6},
    )
    return payload, ("catboost", clf, None)


def train_sequence_tabpfn(train, val, test, args):
    from tabpfn import TabPFNClassifier
    import sirin.detection.probing.detectors.utils.tabpfn_compat  # noqa: F401  (shim)

    (tr_x, tr_y), (va_x, va_y), (te_x, te_y) = _sequence_split(train, val, test)
    x, extras = _preprocess(tr_x, scale=True, pca_components=args.tabpfn_pca, seed=args.seed)
    clf = TabPFNClassifier(device=args.tabpfn_device, ignore_pretraining_limits=True, random_state=args.seed)
    clf.fit(x, tr_y)
    val_scores = clf.predict_proba(_apply(extras, va_x))[:, 1]
    test_scores = clf.predict_proba(_apply(extras, te_x))[:, 1]
    payload = _sequence_payload(
        val_scores, va_y, test_scores, te_y,
        {"pca_components": int(extras["pca"].n_components_) if "pca" in extras else None},
    )
    return payload, ("tabpfn", clf, extras)


PROBE_TRAINERS = {
    "token_catboost": train_token_catboost,
    "token_tabpfn": train_token_tabpfn,
    "sequence_linear": train_sequence_linear,
    "sequence_catboost": train_sequence_catboost,
    "sequence_tabpfn": train_sequence_tabpfn,
}


# --------------------------------------------------------------------------- #
# stage: probes
# --------------------------------------------------------------------------- #
def _split_record(train, val, test, layer, extra: dict) -> dict:
    record = {
        "selected_layer": int(layer),
        "n_train_rows": len(train.rows),
        "n_validation_rows": len(val.rows),
        "n_test_rows": len(test.rows),
        "n_train_tokens": int(len(train.features)),
        "n_validation_tokens": int(len(val.features)),
        "n_test_tokens": int(len(test.features)),
        "split": "prompt_disjoint_from_shard_metadata (seed 42)",
        "threshold_method": "validation_f1_optimal",
    }
    record.update(extra)
    return record


def run_probes(args) -> None:
    started = time.time()
    layer, layer_position, layers = resolve_layer(args)
    model_id, revision = shard_model_info(args.shard_dir, args)
    train = base.shard_bundle("train", args.shard_dir, layer_position)
    val = base.shard_bundle("validation", args.shard_dir, layer_position)
    test = base.shard_bundle("test", args.shard_dir, layer_position)
    probes_dir = args.probes_dir
    probes_dir.mkdir(parents=True, exist_ok=True)
    selected = [m for m in PROBE_METHODS if m in args.methods]
    combined: dict[str, dict] = {}
    for name in selected:
        result_dir = probes_dir / name
        if is_done(result_dir):
            combined[name] = json.loads((result_dir / "metrics.json").read_text())
            print(f"[probes] skip {name} (already complete)", flush=True)
            continue
        payload_metrics, (kind, estimator, extras) = PROBE_TRAINERS[name](train, val, test, args)
        provenance = {
            "method": name,
            "model_id": model_id,
            "model_revision": revision,
            "dataset": "psiloqa_en_span",
            "shard_dir": str(args.shard_dir),
            "hidden_state_candidates": layers,
            "seed": args.seed,
            "split": _split_record(train, val, test, layer, {"params": payload_metrics["params"]}),
        }
        config = {
            "method": name,
            "model_kind": kind,
            "threshold": float(payload_metrics["threshold"]),
            "threshold_method": "validation_f1_optimal",
            "selected_layer": int(layer),
        }
        write_result(
            result_dir,
            {"metrics": payload_metrics, "provenance": provenance, "config": config},
            kind, estimator, extras,
        )
        combined[name] = payload_metrics
        print(
            f"[probes] {name} test="
            + json.dumps(payload_metrics["test"], sort_keys=True),
            flush=True,
        )
    base._json(
        probes_dir / "sirin_metrics.json",
        {
            "status": "ok",
            "selected_layer": int(layer),
            "methods": {name: combined[name] for name in selected if name in combined},
            "seconds": round(time.time() - started, 3),
        },
    )
    print(f"[probes] done -> {probes_dir / 'sirin_metrics.json'}", flush=True)


# --------------------------------------------------------------------------- #
# stage: ue
# --------------------------------------------------------------------------- #
def _ue_token_scores(bundle: base.Bundle, method: str) -> np.ndarray:
    ue = flat_ue(bundle)
    if method == "MaximumTokenProbability":
        return -ue[:, UE_COLUMNS.index("logp_realized")]  # -log p(realized)
    if method == "TokenEntropy":
        return ue[:, UE_COLUMNS.index("entropy_vocab")]
    raise ValueError(method)


def _ue_sequence_scores(bundle: base.Bundle, method: str) -> np.ndarray:
    if method == "MeanTokenEntropy":
        return per_answer_ue(bundle, UE_COLUMNS.index("entropy_vocab"), negate=False)
    if method == "Perplexity":
        return per_answer_ue(bundle, UE_COLUMNS.index("logp_realized"), negate=True)
    raise ValueError(method)


UE_FORMULAS = {
    "MaximumTokenProbability": "token: -logp_realized  (lm_polygraph -greedy_log_likelihoods[:-1])",
    "TokenEntropy": "token: entropy_vocab  (lm_polygraph entropy[:-1])",
    "MeanTokenEntropy": "sequence: mean(entropy_vocab)  (lm_polygraph mean(entropy))",
    "Perplexity": "sequence: -mean(logp_realized)  (lm_polygraph -mean(greedy_log_likelihoods); mean-NLL, no exp)",
}
UE_LEVEL = {
    "MaximumTokenProbability": "token",
    "TokenEntropy": "token",
    "MeanTokenEntropy": "sequence",
    "Perplexity": "sequence",
}


def run_ue(args) -> None:
    started = time.time()
    layer, layer_position, layers = resolve_layer(args)
    model_id, revision = shard_model_info(args.shard_dir, args)
    train = base.shard_bundle("train", args.shard_dir, layer_position)  # for split record only
    val = base.shard_bundle("validation", args.shard_dir, layer_position)
    test = base.shard_bundle("test", args.shard_dir, layer_position)
    ue_dir = args.ue_dir
    ue_dir.mkdir(parents=True, exist_ok=True)
    selected = [m for m in UE_METHODS if m in args.methods]
    val_seq_labels, test_seq_labels = sequence_labels(val), sequence_labels(test)
    combined: dict[str, dict] = {}
    for name in selected:
        result_dir = ue_dir / name
        if is_done(result_dir):
            combined[name] = json.loads((result_dir / "metrics.json").read_text())
            print(f"[ue] skip {name} (already complete)", flush=True)
            continue
        if UE_LEVEL[name] == "token":
            val_scores = _ue_token_scores(val, name)
            test_scores = _ue_token_scores(test, name)
            threshold = token_char_threshold(val, val_scores)
            payload_metrics = {
                "threshold": threshold,
                "validation": token_char_metrics(val, val_scores, threshold),
                "test": token_char_metrics(test, test_scores, threshold),
            }
        else:
            val_scores = _ue_sequence_scores(val, name)
            test_scores = _ue_sequence_scores(test, name)
            threshold = f1_optimal_threshold(val_seq_labels, val_scores)
            payload_metrics = {
                "threshold": threshold,
                "validation": sequence_classification_metrics(val_seq_labels, val_scores, threshold),
                "test": sequence_classification_metrics(test_seq_labels, test_scores, threshold),
            }
        provenance = {
            "method": name,
            "level": UE_LEVEL[name],
            "formula": UE_FORMULAS[name],
            "lm_polygraph_matched": True,
            "ue_scalar_columns": list(UE_COLUMNS),
            "model_id": model_id,
            "model_revision": revision,
            "shard_dir": str(args.shard_dir),
            "split": _split_record(train, val, test, layer, {}),
        }
        config = {
            "method": name,
            "level": UE_LEVEL[name],
            "threshold": float(threshold),
            "threshold_method": "validation_f1_optimal",
            "higher_is_more_uncertain": True,
        }
        write_result(
            result_dir,
            {"metrics": payload_metrics, "provenance": provenance, "config": config},
            "ue", None, None,
        )
        combined[name] = payload_metrics
        print(f"[ue] {name} test=" + json.dumps(payload_metrics["test"], sort_keys=True), flush=True)
    base._json(
        ue_dir / "sirin_metrics.json",
        {
            "status": "ok",
            "selected_layer": int(layer),
            "formulas": UE_FORMULAS,
            "methods": {name: combined[name] for name in selected if name in combined},
            "seconds": round(time.time() - started, 3),
        },
    )
    print(f"[ue] done -> {ue_dir / 'sirin_metrics.json'}", flush=True)


# --------------------------------------------------------------------------- #
def parse_args():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--stage", choices=("probes", "ue"), required=True)
    parser.add_argument("--base-dir", type=Path, default=BASE_DIR)
    parser.add_argument("--shard-dir", type=Path, default=None)
    parser.add_argument("--probes-dir", type=Path, default=None)
    parser.add_argument("--ue-dir", type=Path, default=None)
    parser.add_argument("--experiment-metrics", type=Path, default=None)
    parser.add_argument("--layer", default="best", help="'best' reads selected_layer from the sweep metrics, else an int")
    parser.add_argument("--methods", default="all", help="comma list to restrict which methods run")
    parser.add_argument("--seed", type=int, default=42)
    parser.add_argument("--model-id", default=None, help="override; default reads shard metadata")
    parser.add_argument("--revision", default=None, help="override; default reads shard metadata")
    parser.add_argument("--catboost-iterations", type=int, default=500)
    parser.add_argument("--tabpfn-subsample-tokens", type=int, default=50000)
    parser.add_argument("--tabpfn-per-answer-cap", type=int, default=128)
    parser.add_argument("--tabpfn-pca", type=int, default=100)
    parser.add_argument(
        "--tabpfn-device", default="cpu",
        help="TabPFN inference device; 50k-context prediction is hours on CPU, minutes on cuda",
    )
    args = parser.parse_args()
    args.shard_dir = args.shard_dir or args.base_dir / "feature_shards"
    args.probes_dir = args.probes_dir or args.base_dir / "probes"
    args.ue_dir = args.ue_dir or args.base_dir / "ue"
    args.experiment_metrics = args.experiment_metrics or args.base_dir / "experiment" / "metrics.json"
    everything = PROBE_METHODS if args.stage == "probes" else UE_METHODS
    args.methods = set(everything) if args.methods == "all" else set(args.methods.split(","))
    return args


if __name__ == "__main__":
    arguments = parse_args()
    if arguments.stage == "probes":
        run_probes(arguments)
    else:
        run_ue(arguments)
