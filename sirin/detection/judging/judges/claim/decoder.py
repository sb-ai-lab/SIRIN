from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple, Union

import joblib
import numpy as np
import torch
from loguru import logger as lg
from transformers import EvalPrediction

from sirin.definitions import INPUT_COL, TARGET_COL, DetectionLevel, DataCollatorType
from sirin.detection.judging.judges.base import HfJudgeBase
from sirin.detection.judging.judges.utils import (
    format_dialogue_for_training,
    prepare_decoder_inputs_with_labels,
    build_prompt_messages,
)
from sirin.detection.judging.training import SequenceDecoderJudgeTrainer
from sirin.detection.splitters import SplitManager
from sirin.detection.utils.basic import calibrate_threshold
from sirin.inference.adapters import HfModelAdapter, ModelAdapterBase
from sirin.metrics.classification import calculate_classification_metrics
from sirin.models.detection import HfJudgeConfig, SplitConfig
from sirin.utils.hf import get_assistant_prefix


class ClaimDecoderJudge(HfJudgeBase):
    """
    Decoder judge implementation for claim-level hallucination detection.

    Decomposes each response into atomic claims via SplitManager, classifies
    each claim independently using next-token prediction from a generative
    decoder, then re-aggregates per-claim predictions back to response level.
    """

    detection_level = DetectionLevel.CLAIM
    data_collator_type = DataCollatorType.TOKEN
    trainer = SequenceDecoderJudgeTrainer

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
        self.assistant_prefix = get_assistant_prefix(self.model_adapter._model_name)

    def detect(
        self,
        samples: Union[List[str], List[List[Dict]]],
        labels: Optional[np.ndarray] = None,
        **kwargs,
    ) -> Tuple[np.ndarray, np.ndarray, Optional[np.ndarray]]:
        """
        Detects hallucinations at claim level using a generative decoder model.

        Each response is split into atomic claims, then the decoder predicts
        a class token (0, 1, etc.) for each claim independently. Per-claim
        predictions are re-aggregated to response level.
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

        formatted_input = build_prompt_messages(self.config, samples)

        preprocessed_input = self.model_adapter._preprocess_input(formatted_input)
        preprocessed_input = [
            f"{sample}{self.assistant_prefix}" for sample in preprocessed_input
        ]

        inputs = self.model_adapter.tokenizer(
            preprocessed_input,
            return_tensors=self.config.return_tensors,
            truncation=self.model_adapter.config.truncation,
            padding=self.model_adapter.config.padding,
        ).to(self.config.device)

        with torch.no_grad():
            outputs = self.model_adapter.model.generate(
                **inputs,
                max_new_tokens=self.config.max_new_tokens,
                do_sample=False,
                temperature=self.config.temperature,
                top_p=self.config.top_p,
                pad_token_id=self.model_adapter.tokenizer.eos_token_id,
                eos_token_id=self.model_adapter.tokenizer.eos_token_id,
                return_dict_in_generate=True,
                output_scores=True,
            )

        first_token_logits = outputs.scores[0]
        selected_logits = first_token_logits[:, self.class_token_ids]
        probs, preds = self._logits_to_probs_preds(selected_logits)

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
        probs = eval_pred.predictions
        labels = eval_pred.label_ids

        if self.config.num_classification_heads == 2:
            self.threshold = calibrate_threshold(
                probs,
                labels,
                self.config.threshold_method,
                self.config.threshold_percentile,
                self.config.fixed_threshold,
            )
            preds = (probs > self.threshold).astype(int)
        else:
            self.threshold = None
            preds = np.argmax(probs, axis=1)

        metrics = calculate_classification_metrics(
            labels,
            probs,
            preds,
            metrics=self.metrics_to_compute,
        )
        lg.info(f"Evaluation metrics: {metrics}")
        return metrics

    def _preprocess(self, samples: Dict[str, Any]) -> Dict[str, Any]:
        """Preprocess samples for claim-level classification with decoder models."""
        inputs = samples[INPUT_COL]
        targets = samples[TARGET_COL]

        self._check_truncation_warning(inputs)

        formatted_messages = format_dialogue_for_training(
            inputs, targets, self.config, is_token_level=False
        )

        return prepare_decoder_inputs_with_labels(
            formatted_messages, self.model_adapter, self.config
        )

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
