from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple, Union

import joblib
import numpy as np
from loguru import logger as lg
from transformers import EvalPrediction, Trainer

from sirin.definitions import INPUT_COL, TARGET_COL, DetectionLevel, DataCollatorType
from sirin.detection.judging.judges.base import HfJudgeBase
from sirin.detection.judging.judges.utils import (
    process_logits_to_probs,
    calibrate_and_compute_metrics,
)
from sirin.detection.splitters import SplitManager
from sirin.inference.adapters import HfModelAdapter, ModelAdapterBase
from sirin.models.detection import HfJudgeConfig, SplitConfig


class ClaimEncoderJudge(HfJudgeBase):
    """
    Encoder judge implementation for claim-level hallucination detection.

    Decomposes each response into atomic claims via SplitManager, classifies
    each claim independently using an encoder classification head, then
    re-aggregates per-claim predictions back to response level.
    """

    detection_level = DetectionLevel.CLAIM
    data_collator_type = DataCollatorType.PADDING
    trainer = Trainer

    def __init__(
        self,
        config: HfJudgeConfig,
        model_adapter: HfModelAdapter,
        response_splitter_config: SplitConfig,
        split_model: Optional[ModelAdapterBase] = None,
    ):
        super().__init__(config=config, model_adapter=model_adapter)
        self.response_splitter_config = response_splitter_config
        self.response_splitter = SplitManager(config=response_splitter_config)
        self.split_model = split_model or model_adapter
        self.device = self.config.device
        if self.model_adapter.tokenizer.pad_token is None:
            self.model_adapter.tokenizer.pad_token = (
                self.model_adapter.tokenizer.eos_token
            )

    def detect(
        self,
        samples: Union[List[str], List[List[Dict]]],
        labels: Optional[np.ndarray] = None,
        **kwargs,
    ) -> Tuple[np.ndarray, np.ndarray, Optional[np.ndarray]]:
        """
        Detects hallucinations at claim level using encoder embeddings.

        Each response is split into atomic claims, classified independently,
        then predictions are re-aggregated to response level.
        """
        original_samples = list(samples)

        samples_fact_splits = self.response_splitter.split_inputs(
            samples, self.split_model
        )
        response_group_ids = []
        for index, splits in enumerate(samples_fact_splits):
            response_group_ids.extend([index] * len(splits))
        samples = [split for splits in samples_fact_splits for split in splits]

        samples, group_ids = self._split_context_samples(samples)

        self._check_truncation_warning(samples)

        model_states = self.model_adapter.generate_hiddens(
            inputs=samples,
            return_hiddens=False,
            return_logits=True,
        )

        logits = model_states.logits

        probs, preds = self._logits_to_probs_preds(logits)

        probs = probs.tolist()
        preds = preds.tolist()

        preds, probs = self._aggregate_context_predictions(
            group_ids, preds, probs, binary=(self.config.num_classification_heads <= 2)
        )

        overall_preds, overall_probs = self.response_splitter.aggregate_predictions(
            response_group_ids,
            preds,
            probs,
            binary=(self.config.num_classification_heads <= 2),
        )

        results = []
        for sample_idx, sample in enumerate(original_samples):
            sample_mask = [
                i for i, gid in enumerate(response_group_ids) if gid == sample_idx
            ]
            splitted_samples = samples_fact_splits[sample_idx]
            sample_probs = [probs[i] for i in sample_mask]
            sample_preds = [preds[i] for i in sample_mask]
            facts = [
                {"fact": split[1]["content"], "pred": pred, "prob": prob}
                for split, pred, prob in zip(splitted_samples, sample_probs, sample_preds)
            ]
            results.append(
                {
                    "sample": sample,
                    "overall_pred": overall_preds[sample_idx],
                    "overall_prob": overall_probs[sample_idx],
                    "facts": facts,
                }
            )
        self.claim_results = results

        return overall_probs, overall_preds, labels

    def _compute_metrics(self, eval_pred: EvalPrediction) -> Dict[str, Any]:
        """Compute metrics for claim-level classification."""
        logits, labels = eval_pred

        probs, _ = process_logits_to_probs(logits, labels, filter_padding=False)

        is_binary = logits.shape[-1] <= 2
        metrics, threshold = calibrate_and_compute_metrics(
            probs, labels, self.config, self.metrics_to_compute, is_binary
        )
        self.threshold = threshold

        return metrics

    def _preprocess(self, samples: Dict[str, Any]) -> Dict[str, Any]:
        """Preprocess samples for claim-level classification."""
        inputs = samples[INPUT_COL]
        targets = samples[TARGET_COL]

        self._check_truncation_warning(inputs)

        processed_inputs = self.model_adapter._preprocess_input(inputs)

        tokenized = self.model_adapter.tokenizer(
            processed_inputs,
            padding=False,
            truncation=self.model_adapter.config.truncation,
            add_special_tokens=False,
        )

        tokenized["labels"] = targets

        return tokenized

    def _save_config(self, save_dir: Path):
        super()._save_config(save_dir)
        joblib.dump(self.response_splitter_config, save_dir / "splitter_config.joblib")
        lg.info(f"Saved splitter config to {save_dir / 'splitter_config.joblib'}")

    def _load_config(self, load_dir: Path):
        super()._load_config(load_dir)
        splitter_config_path = load_dir / "splitter_config.joblib"
        if splitter_config_path.exists():
            self.response_splitter_config = joblib.load(splitter_config_path)
            self.response_splitter = SplitManager(config=self.response_splitter_config)
            lg.info(f"Loaded splitter config from {splitter_config_path}")
