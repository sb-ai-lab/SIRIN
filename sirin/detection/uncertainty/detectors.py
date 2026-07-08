import joblib
from typing import Dict, List, Optional, Tuple, Union

import numpy as np
import torch
from pathlib import Path
from loguru import logger as lg

from sirin.definitions import BASIC_METRICS, INPUT_COL, TARGET_COL, DetectionLevel
from sirin.detection.base import DetectorBase
from sirin.loggers import LoggerBase
from sirin.detection.processors import (
    SequenceUncertaintyFeatureProcessor,
    TokenUncertaintyFeatureProcessor,
    FeatureProcessorBase,
)
from sirin.detection.utils.token import rearrange_token_predictions, convert_spans_to_labels, get_answer_offsets
from sirin.detection.utils.basic import calibrate_threshold
from sirin.detection.utils.torch import InputsDataset
from sirin.metrics import calculate_classification_metrics
from sirin.models.detection import DetectionResult, UncertaintyDetectorConfig
from sirin.utils.config_manager import validate_hydra_config
from sirin.utils.config_serialization import (
    deserialize_uncertainty_detector_config,
    serialize_uncertainty_detector_config,
)


class UncertaintyDetectorBase(DetectorBase):
    """Base class for uncertainty-based detectors with shared functionality"""

    def __init__(
        self, config: UncertaintyDetectorConfig, feature_processor: FeatureProcessorBase
    ):
        super().__init__(config)
        self.feature_processor = feature_processor
        self.feature_processor.setup_extractor()
        self.feature_stats = {}
        self.last_generated_text: str | None = None
        self.last_method_scores: dict[str, float] | None = None

    def setup_model(self):
        """Setup detector model (uncertainty-based detection doesn't need additional models)"""
        pass

    def _aggregate_uncertainties(self, uncertainties: np.ndarray) -> np.ndarray:
        """Aggregate multiple uncertainty scores using configured method"""
        if uncertainties.ndim == 1:
            return uncertainties

        aggregation_method = self.config.aggregation_method

        if aggregation_method == 'mean':
            return np.mean(uncertainties, axis=-1)
        elif aggregation_method == 'max':
            return np.max(uncertainties, axis=-1)
        elif aggregation_method == 'min':
            return np.min(uncertainties, axis=-1)
        elif aggregation_method == 'weighted' and self._has_method_weights():
            return self._weighted_aggregation(uncertainties)
        else:
            return np.mean(uncertainties, axis=-1)

    def _has_method_weights(self) -> bool:
        """Check if method weights are configured"""
        return (
            hasattr(self.config, 'method_weights')
            and self.config.method_weights is not None
        )

    def _weighted_aggregation(self, uncertainties: np.ndarray) -> np.ndarray:
        """Perform weighted aggregation of uncertainties"""
        method_names = self.feature_processor.config.uncertainty_methods or []
        weights = np.array(
            [self.config.method_weights.get(method, 1.0) for method in method_names]
        )
        weights = weights / np.sum(weights)
        return np.average(uncertainties, axis=-1, weights=weights)

    def _get_classification_metrics_config(self):
        """Get classification metrics from config or use defaults"""
        return BASIC_METRICS

    def _flatten_samples(self, samples: List) -> List:
        """Flatten nested list of samples"""
        return [item for sample in samples for item in sample]

    def _save_config(self, save_dir: Path):
        """Save detector configuration"""
        config_dict = serialize_uncertainty_detector_config(
            config=self.config,
            threshold=self.threshold,
            feature_stats=self.feature_stats,
        )
        joblib.dump(config_dict, save_dir / 'config.joblib')
        lg.info(f"Saved config to {save_dir / 'config.joblib'}")

    def _load_config(self, load_dir: Path):
        """Load detector configuration"""
        config_path = load_dir / 'config.joblib'
        if not config_path.exists():
            raise FileNotFoundError(f"Config file not found at: {config_path}")

        config_dict = joblib.load(config_path)
        self.config, self.threshold, self.feature_stats = (
            deserialize_uncertainty_detector_config(config_dict)
        )
        lg.info(f"Loaded config from {config_path}")


class SequenceUncertaintyDetector(UncertaintyDetectorBase):
    """Sequence-level detector using uncertainty estimation for hallucination detection"""

    detection_level = DetectionLevel.SEQUENCE

    @validate_hydra_config
    def __init__(
        self,
        config: UncertaintyDetectorConfig,
        feature_processor: SequenceUncertaintyFeatureProcessor,
    ):
        super().__init__(config, feature_processor)

    def train(
        self,
        train_data: InputsDataset,
        val_data: Optional[InputsDataset] = None,
        logger: Optional[LoggerBase] = None,
    ) -> DetectionResult:
        """Fit the detector using uncertainty features"""

        # only threshold calibration
        inputs = val_data[INPUT_COL] if val_data is not None else train_data[INPUT_COL]
        targets = val_data[TARGET_COL] if val_data is not None else train_data[TARGET_COL]
        metrics_config = self._get_classification_metrics_config()

        probs, preds, _ = self.detect(inputs)
        val_targets = np.array(targets)
        self.threshold = calibrate_threshold(
            probs,
            targets,
            self.config.threshold_method,
            self.config.threshold_percentile,
            self.config.fixed_threshold,
        )
        lg.info(f"Set detection threshold to: {self.threshold}")
        result_metrics = calculate_classification_metrics(
            val_targets, probs, preds, metrics=metrics_config
        )
        result_probs = probs.tolist()

        if logger:
            logger.log_metrics(result_metrics, -1, prefix='/train')

        return DetectionResult(
            metrics=result_metrics,
            probs=result_probs,
            threshold=self.threshold,
        )

    def detect(
        self,
        samples: Union[List[str], List[List[Dict]]],
        labels: Optional[np.ndarray] = None,
        **kwargs,
    ) -> Tuple[np.ndarray, np.ndarray, Optional[np.ndarray]]:
        """Detect hallucinations at sequence level using uncertainty scores"""
        samples, group_ids = self._split_context_samples(samples)

        uncertainty_scores, _ = self.feature_processor(samples)
        self.last_generated_text = getattr(self.feature_processor, 'last_generated_text', None)
        self.last_method_scores = getattr(self.feature_processor, 'last_method_scores', None)

        uncertainty_scores = np.array(uncertainty_scores[0].flatten(start_dim=1))
        aggregated_scores = self._aggregate_uncertainties(uncertainty_scores)

        predictions = (aggregated_scores > self.threshold).astype(int)

        predictions, aggregated_scores = self._aggregate_context_predictions(
            group_ids,
            predictions,
            aggregated_scores,
            binary=(self.config.num_classification_heads <= 2),
        )

        return aggregated_scores, predictions, labels


class TokenUncertaintyDetector(UncertaintyDetectorBase):
    """Token-level detector using uncertainty estimation for hallucination detection"""

    detection_level = DetectionLevel.TOKEN

    @validate_hydra_config
    def __init__(
        self,
        config: UncertaintyDetectorConfig,
        feature_processor: TokenUncertaintyFeatureProcessor,
    ):
        super().__init__(config, feature_processor)

    def train(
        self,
        train_data: InputsDataset,
        val_data: Optional[InputsDataset] = None,
        logger: Optional[LoggerBase] = None,
    ) -> DetectionResult:
        """Fit the detector using token-level uncertainty features"""

        # only threshold calibration
        inputs = val_data[INPUT_COL] if val_data is not None else train_data[INPUT_COL]
        targets = val_data[TARGET_COL] if val_data is not None else train_data[TARGET_COL]
        metrics_config = self._get_classification_metrics_config()

        probs, preds, _ = self.detect(inputs)
        flat_probs, flat_preds, flat_labels = self._flatten_token_predictions(
            probs, preds, targets
        )
        self.threshold = calibrate_threshold(
            flat_probs,
            flat_labels,
            self.config.threshold_method,
            self.config.threshold_percentile,
            self.config.fixed_threshold,
        )
        lg.info(f"Set detection threshold to: {self.threshold}")
        result_metrics = calculate_classification_metrics(
            flat_labels, flat_probs, flat_preds, metrics=metrics_config
        )
        result_probs = flat_probs.tolist()

        if logger:
            logger.log_metrics(result_metrics, -1, prefix='/train')

        return DetectionResult(
            metrics=result_metrics,
            probs=result_probs,
            threshold=self.threshold,
        )

    def _flatten_token_predictions(
        self, probs: List[List[float]], preds: List[List[int]], targets: List
    ) -> Tuple[np.ndarray, np.ndarray, np.ndarray]:
        """Flatten token-level predictions and labels for metrics calculation"""
        flat_probs = []
        flat_preds = []
        flat_labels = []

        for i, (sample_probs, sample_preds) in enumerate(zip(probs, preds)):
            flat_probs.extend(sample_probs)
            flat_preds.extend(sample_preds)

            target = targets[i]
            if isinstance(target, list):
                flat_labels.extend(target)
            else:
                flat_labels.extend([target] * len(sample_probs))

        return np.array(flat_probs), np.array(flat_preds), np.array(flat_labels)

    def detect(
        self,
        samples: List[str],
        labels: Optional[np.ndarray] = None,
        **kwargs,
    ) -> Tuple[np.ndarray, np.ndarray, Optional[np.ndarray]]:
        """Detect hallucinations at token level using uncertainty scores"""
        samples, group_ids = self._split_context_samples(samples)

        uncertainty_scores, _ = self.feature_processor(samples)
        self.last_generated_text = getattr(self.feature_processor, 'last_generated_text', None)
        self.last_method_scores = getattr(self.feature_processor, 'last_method_scores', None)

        # Get answer offsets from the reference answer tokens — these define the
        # character-level output space and drive all_lengths.
        offsets, _, _ = get_answer_offsets(samples, self.feature_processor._extractor)
        offsets_cat = torch.cat(
            [torch.tensor(offset, dtype=torch.long) for offset in offsets]
        )

        # Number of reference answer tokens per sample (used for feature alignment)
        ref_token_counts = [len(offset) for offset in offsets]
        all_lengths = [0]
        for count in ref_token_counts:
            all_lengths.append(all_lengths[-1] + count)

        # Process features aligned to the reference token count per sample so that
        # all_token_probs and offsets_cat have the same total length.
        all_token_probs, all_token_preds = self._process_token_features(
            uncertainty_scores[0], ref_token_counts
        )

        # Convert to numpy arrays
        all_token_probs = np.array(all_token_probs)
        all_token_preds = np.array(all_token_preds)

        # Rearrange token predictions to character-level per sample using standard utility
        char_probs, char_preds = rearrange_token_predictions(
            all_token_probs, all_token_preds, offsets_cat, all_lengths
        )

        char_preds, char_probs = self._aggregate_context_predictions(
            group_ids,
            char_preds,
            char_probs,
            binary=(self.config.num_classification_heads <= 2),
        )

        # Convert hallucination spans to character-level labels (no token-level conversion)
        if labels is not None:
            char_labels = convert_spans_to_labels(labels, char_probs)
        else:
            char_labels = None

        return char_probs, char_preds, char_labels

    def _process_token_features(
        self,
        features: List[torch.Tensor],
        ref_token_counts: Optional[List[int]] = None,
    ) -> Tuple[List[float], List[int]]:
        all_token_probs = []
        all_token_preds = []

        for sample_idx, sample_features in enumerate(features):
            sample_features = torch.tensor(sample_features)

            # Aggregate across layers if needed
            if len(sample_features.shape) == 3:
                sample_features = sample_features.mean(dim=0)

            # Aggregate across features per token
            token_scores = self._aggregate_uncertainties(sample_features.numpy())
            token_preds = (token_scores > self.threshold).astype(int)

            # Align to reference answer token count when provided
            if ref_token_counts is not None:
                n = ref_token_counts[sample_idx]
                if len(token_scores) >= n:
                    token_scores = token_scores[:n]
                    token_preds = token_preds[:n]
                else:
                    # Pad with zeros if generated sequence is shorter
                    pad = n - len(token_scores)
                    token_scores = np.concatenate([token_scores, np.zeros(pad)])
                    token_preds = np.concatenate(
                        [token_preds, np.zeros(pad, dtype=int)]
                    )

            all_token_probs.extend(token_scores.tolist())
            all_token_preds.extend(token_preds.tolist())

        return all_token_probs, all_token_preds
