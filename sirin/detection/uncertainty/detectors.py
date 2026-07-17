import joblib
from itertools import combinations
from typing import Dict, List, Optional, Tuple, Union

import numpy as np
import torch
from pathlib import Path
from loguru import logger as lg
from sklearn.metrics import roc_auc_score

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

    def fit_score_normalizer(self, uncertainties: np.ndarray) -> None:
        """Fit per-estimator normalization statistics on raw train scores.

        Label-free: only the marginal distribution of each estimator is used. Call
        once on the calibration split before `detect`, otherwise `_normalize_scores`
        passes scores through unchanged.
        """
        if getattr(self.config, 'score_normalization', 'none') == 'none' or uncertainties.ndim == 1:
            return
        if len(uncertainties) < 50:
            # `rank` maps onto the empirical CDF of this sample; with a handful of
            # points every test score collapses onto the same few quantiles and the
            # aggregate goes constant (ROC-AUC 0.5).
            lg.warning(
                f'Fitting score normalization on only {len(uncertainties)} samples; '
                'quantiles will be coarse and scores may tie. Use a larger split.'
            )
        self.feature_stats['score_mean'] = np.nanmean(uncertainties, axis=0)
        std = np.nanstd(uncertainties, axis=0)
        std[std == 0] = 1.0
        self.feature_stats['score_std'] = std
        self.feature_stats['score_median'] = np.nanmedian(uncertainties, axis=0)
        # Sorted train columns are the empirical CDF used by `rank` normalization.
        self.feature_stats['score_sorted'] = np.sort(
            np.where(np.isnan(uncertainties), self.feature_stats['score_median'], uncertainties),
            axis=0,
        )

    def _normalize_scores(self, uncertainties: np.ndarray) -> np.ndarray:
        """Put estimators on a common scale using the fitted train statistics."""
        method = getattr(self.config, 'score_normalization', 'none')
        if method == 'none' or uncertainties.ndim == 1:
            return uncertainties
        if 'score_median' not in self.feature_stats:
            lg.warning(
                f"score_normalization='{method}' but no statistics fitted; "
                'aggregating raw scores. Call fit_score_normalizer on the train split.'
            )
            return uncertainties

        # Focus yields NaN when a response has no keyword (NER/POS) tokens -- its
        # score is undefined there. Impute the train median so it contributes
        # neutrally rather than propagating NaN through the mean.
        median = self.feature_stats['score_median']
        uncertainties = np.where(np.isnan(uncertainties), median, uncertainties)

        if method == 'zscore':
            return (uncertainties - self.feature_stats['score_mean']) / self.feature_stats['score_std']
        if method == 'rank':
            sorted_train = self.feature_stats['score_sorted']
            n = sorted_train.shape[0]
            return np.stack(
                [
                    np.searchsorted(sorted_train[:, i], uncertainties[:, i], side='right') / n
                    for i in range(uncertainties.shape[1])
                ],
                axis=1,
            )
        raise ValueError(f'Unknown score_normalization: {method}')

    # Aggregations searched by `aggregation_method="auto"`. nan-aware: a NaN from one
    # estimator (e.g. Focus on a keyword-less response) must not poison the fused score;
    # an all-NaN row still collapses to NaN, which is the correct "undefined" signal.
    _AUTO_AGGREGATIONS = {
        'mean': lambda a: np.nanmean(a, axis=-1),
        'max': lambda a: np.nanmax(a, axis=-1),
        'min': lambda a: np.nanmin(a, axis=-1),
        'median': lambda a: np.nanmedian(a, axis=-1),
    }

    def fit_score_selection(self, uncertainties: np.ndarray, targets) -> None:
        """Pick the estimator subset + aggregation that maximizes train ROC-AUC.

        Estimators are not interchangeable: some are redundant (RAUQ and Focus are
        both attention-based and correlate strongly), and which one carries signal
        depends on the task. A fixed average over all of them tracks the *middle*
        estimator, not the best. This searches non-empty subsets x aggregations once,
        on train, and freezes the winner. The only labels used are the train targets.
        """
        if self.config.aggregation_method != 'auto' or uncertainties.ndim == 1:
            return
        scores = self._normalize_scores(uncertainties)
        y = np.asarray(targets)
        n_methods = scores.shape[1]

        best = None
        for size in range(1, n_methods + 1):
            for subset in combinations(range(n_methods), size):
                for agg_name, agg in self._AUTO_AGGREGATIONS.items():
                    if size == 1 and agg_name != 'mean':
                        continue  # every aggregation is the identity on one estimator
                    auc = roc_auc_score(y, agg(scores[:, list(subset)]))
                    if best is None or auc > best[0]:
                        best = (auc, list(subset), agg_name)

        auc, subset, agg_name = best
        self.feature_stats['selected_subset'] = subset
        self.feature_stats['selected_aggregation'] = agg_name
        names = list(self.feature_processor.config.uncertainty_methods or [])
        chosen = [names[i] for i in subset] if len(names) == n_methods else subset
        lg.info(f'Selected UE fusion on train: {agg_name} over {chosen} (train ROC-AUC {auc:.3f})')

    def _aggregate_uncertainties(self, uncertainties: np.ndarray) -> np.ndarray:
        """Aggregate multiple uncertainty scores using configured method"""
        if uncertainties.ndim == 1:
            return uncertainties

        uncertainties = self._normalize_scores(uncertainties)
        aggregation_method = self.config.aggregation_method

        if aggregation_method == 'auto':
            if 'selected_subset' not in self.feature_stats:
                lg.warning(
                    "aggregation_method='auto' but no selection fitted; using the mean. "
                    'Call fit_score_selection on the train split.'
                )
                return np.nanmean(uncertainties, axis=-1)
            subset = self.feature_stats['selected_subset']
            agg = self._AUTO_AGGREGATIONS[self.feature_stats['selected_aggregation']]
            return agg(uncertainties[:, subset])

        if aggregation_method == 'mean':
            return np.nanmean(uncertainties, axis=-1)
        elif aggregation_method == 'max':
            return np.nanmax(uncertainties, axis=-1)
        elif aggregation_method == 'min':
            return np.nanmin(uncertainties, axis=-1)
        elif aggregation_method == 'weighted' and self._has_method_weights():
            return self._weighted_aggregation(uncertainties)
        else:
            return np.nanmean(uncertainties, axis=-1)

    def _has_method_weights(self) -> bool:
        """Check if method weights are configured"""
        return (
            hasattr(self.config, 'method_weights')
            and self.config.method_weights is not None
        )

    def _weighted_aggregation(self, uncertainties: np.ndarray) -> np.ndarray:
        """Perform weighted aggregation of uncertainties.

        `method_weights` is keyed by estimator *name*, so the names have to come from
        the feature processor's config — looking weights up by estimator object would
        silently miss every key and make this a plain mean.
        """
        method_names = list(self.feature_processor.config.uncertainty_methods or [])
        unknown = set(self.config.method_weights) - set(method_names)
        if unknown:
            lg.warning(f'method_weights names not among the estimators, ignored: {sorted(unknown)}')
        weights = np.array([self.config.method_weights.get(name, 1.0) for name in method_names])
        total = np.sum(weights)
        if total == 0:
            lg.warning('method_weights sum to zero; falling back to a uniform mean.')
            weights = np.ones_like(weights) / len(weights)
        else:
            weights = weights / total
        return np.average(uncertainties, axis=-1, weights=weights)

    def _get_classification_metrics_config(self):
        """Get classification metrics from config or use defaults"""
        metrics = getattr(self.config, 'classification_metrics', None)
        return BASIC_METRICS if metrics is None else metrics

    def _flatten_samples(self, samples: List) -> List:
        """Flatten nested list of samples"""
        return [item for sample in samples for item in sample]

    @staticmethod
    def _validated_generation_trace(
        samples: List,
        trace: Dict,
        method_names: List[str],
    ) -> Tuple[str, List, List[str], Dict[str, List[float]]]:
        if len(samples) != 1:
            raise ValueError('A generation trace can score exactly one answer at a time.')
        answer = next(
            (
                message['content']
                for message in reversed(samples[0])
                if message['role'] == 'assistant'
            ),
            '',
        )
        text = str(trace.get('text') or '')
        if answer != text:
            raise ValueError(
                'Uncertainty generation trace does not match the displayed answer.'
            )

        offsets = list(trace.get('offsets') or [])
        pieces = list(trace.get('pieces') or [])
        values = {name: list(trace.get(name) or []) for name in method_names}
        lengths = {len(offsets), len(pieces), *(len(items) for items in values.values())}
        if len(lengths) != 1 or not offsets:
            raise ValueError('Uncertainty trace arrays have inconsistent lengths.')
        for piece, offset in zip(pieces, offsets):
            if (
                not isinstance(offset, (list, tuple))
                or len(offset) != 2
                or not 0 <= int(offset[0]) < int(offset[1]) <= len(text)
                or text[int(offset[0]) : int(offset[1])] != piece
            ):
                raise ValueError('Uncertainty trace has invalid text offsets.')
        return text, offsets, pieces, values

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

    def _raw_scores(self, samples) -> Tuple[np.ndarray, Optional[List[int]]]:
        """Per-estimator uncertainty scores, (n_samples, n_estimators), unnormalized."""
        samples, group_ids = self._split_context_samples(samples)
        uncertainty_scores, _ = self.feature_processor(samples)
        self.last_generated_text = getattr(self.feature_processor, 'last_generated_text', None)
        self.last_method_scores = getattr(self.feature_processor, 'last_method_scores', None)
        return np.array(uncertainty_scores[0].flatten(start_dim=1)), group_ids

    def train(
        self,
        train_data: InputsDataset,
        val_data: Optional[InputsDataset] = None,
        logger: Optional[LoggerBase] = None,
    ) -> DetectionResult:
        """Fit score normalization, the fusion rule, and the decision threshold.

        All three are fit on `train_data`, never on the eval split. The normalizer is
        label-free; the fusion rule (`aggregation_method="auto"`) and the threshold
        read train targets. Scores are extracted once and reused, since extraction is
        the only expensive part -- so the thin `val` slice is deliberately not used
        for fitting, where its ~300 samples would make rank quantiles coarse and
        subset selection noisy.
        """
        inputs = train_data[INPUT_COL]
        targets = train_data[TARGET_COL]
        metrics_config = self._get_classification_metrics_config()

        raw_scores, group_ids = self._raw_scores(inputs)
        if group_ids is not None and len(raw_scores) != len(targets):
            # ponytail: context splitting yields one score row per chunk, but the
            # normalizer/selection/threshold are fit against per-sample targets. Rather
            # than silently mis-calibrate ('mean' -> a 0.5 threshold) or crash in
            # roc_auc_score ('auto'), refuse; splitting still applies at detect time.
            raise NotImplementedError(
                'Uncertainty-detector training does not support context splitting: '
                'per-chunk scores cannot be calibrated against per-sample targets. Train '
                'without a context_split_config (splitting still applies at detect time).'
            )
        self.fit_score_normalizer(raw_scores)
        self.fit_score_selection(raw_scores, targets)
        probs = self._aggregate_uncertainties(raw_scores)

        val_targets = np.array(targets)
        self.threshold = calibrate_threshold(
            probs,
            targets,
            self.config.threshold_method,
            self.config.threshold_percentile,
            self.config.fixed_threshold,
        )
        lg.info(f"Set detection threshold to: {self.threshold}")

        preds = (probs > self.threshold).astype(int)
        preds, probs = self._aggregate_context_predictions(
            group_ids,
            preds,
            probs,
            binary=(self.config.num_classification_heads <= 2),
        )
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
        generation_trace = kwargs.get('generation_trace')
        if generation_trace is not None:
            samples, group_ids = self._split_context_samples(samples)
            return self._detect_generation_trace(
                samples, group_ids, generation_trace, labels
            )

        uncertainty_scores, group_ids = self._raw_scores(samples)
        aggregated_scores = self._aggregate_uncertainties(uncertainty_scores)

        predictions = (aggregated_scores > self.threshold).astype(int)

        predictions, aggregated_scores = self._aggregate_context_predictions(
            group_ids,
            predictions,
            aggregated_scores,
            binary=(self.config.num_classification_heads <= 2),
        )

        return aggregated_scores, predictions, labels

    def _detect_generation_trace(
        self,
        samples: List,
        group_ids: List,
        trace: Dict,
        labels: Optional[np.ndarray],
    ) -> Tuple[np.ndarray, np.ndarray, Optional[np.ndarray]]:
        text, _, _, token_values = self._validated_generation_trace(
            samples,
            trace,
            ['MaximumTokenProbability', 'TokenEntropy'],
        )
        available = {
            'MeanTokenEntropy': float(np.mean(token_values['TokenEntropy'])),
            # lm-polygraph's Perplexity estimator is mean chosen-token NLL.
            'Perplexity': float(np.mean(token_values['MaximumTokenProbability'])),
        }
        method_names = list(self.feature_processor.config.uncertainty_methods or [])
        if any(name not in available for name in method_names):
            raise ValueError(
                'Generation trace does not support sequence uncertainty methods: '
                + ', '.join(name for name in method_names if name not in available)
            )
        method_scores = np.array([available[name] for name in method_names])
        score = float(self._aggregate_uncertainties(method_scores[None, :])[0])
        prediction = int(score > self.threshold)
        self.last_generated_text = text
        self.last_generation_trace = trace
        self.last_method_scores = {name: available[name] for name in method_names}
        grouped_preds, grouped_probs = self._aggregate_context_predictions(
            group_ids,
            np.array([prediction]),
            np.array([score]),
            binary=(self.config.num_classification_heads <= 2),
        )
        return grouped_probs, grouped_preds, labels


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
        if getattr(config, 'aggregation_method', 'mean') == 'auto' or (
            getattr(config, 'score_normalization', 'none') != 'none'
        ):
            lg.warning(
                'TokenUncertaintyDetector.train fits only the threshold (never score '
                "normalization or 'auto' selection), so aggregation_method="
                f"{getattr(config, 'aggregation_method', 'mean')!r} / score_normalization="
                f"{getattr(config, 'score_normalization', 'none')!r} falls back to a raw "
                'mean at detect time.'
            )

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

        # Token uncertainty scores exactly one generated answer at a time (detect enforces
        # a single sample), so score the calibration set one sample at a time and collect.
        probs, preds = [], []
        for sample in inputs:
            sample_probs, sample_preds, _ = self.detect([sample])
            probs.extend(sample_probs)
            preds.extend(sample_preds)
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
        generation_trace = kwargs.get('generation_trace')
        if generation_trace is not None:
            return self._detect_generation_trace(
                samples, group_ids, generation_trace, labels
            )

        uncertainty_scores, _ = self.feature_processor(samples)
        self.last_generated_text = getattr(self.feature_processor, 'last_generated_text', None)
        self.last_method_scores = getattr(self.feature_processor, 'last_method_scores', None)
        if len(samples) != 1 or not self.last_generated_text:
            raise ValueError(
                'Token uncertainty must expose the exact generated answer used for scoring.'
            )

        scored_sample = [dict(message) for message in samples[0]]
        assistant_index = next(
            (
                index
                for index in range(len(scored_sample) - 1, -1, -1)
                if scored_sample[index]['role'] == 'assistant'
            ),
            None,
        )
        if assistant_index is None:
            scored_sample.append(
                {'role': 'assistant', 'content': self.last_generated_text}
            )
        else:
            scored_sample[assistant_index]['content'] = self.last_generated_text

        # Scores belong to the detector's generated text, never to a separately
        # supplied answer that merely happens to have the same token count.
        offsets, _, _ = get_answer_offsets(
            [scored_sample], self.feature_processor._extractor
        )
        offsets_cat = torch.cat(
            [torch.tensor(offset, dtype=torch.long) for offset in offsets]
        )

        # Number of reference answer tokens per sample (used for feature alignment)
        ref_token_counts = [len(offset) for offset in offsets]
        all_lengths = [0]
        for count in ref_token_counts:
            all_lengths.append(all_lengths[-1] + count)

        # Refuse lossy truncation/padding: every score must map to one real token.
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

    def _detect_generation_trace(
        self,
        samples: List,
        group_ids: List,
        trace: Dict,
        labels: Optional[np.ndarray],
    ) -> Tuple[np.ndarray, np.ndarray, Optional[np.ndarray]]:
        method_names = list(self.feature_processor.config.uncertainty_methods or [])
        text, offsets, pieces, values = self._validated_generation_trace(
            samples, trace, method_names
        )
        method_values = [values[name] for name in method_names]

        token_features = np.column_stack(method_values)
        token_scores = self._aggregate_uncertainties(token_features)
        token_preds = (token_scores > self.threshold).astype(int)
        char_probs = [0.0] * len(text)
        char_preds = [0] * len(text)
        for (start, end), score, prediction in zip(
            offsets, token_scores, token_preds
        ):
            char_probs[int(start) : int(end)] = [float(score)] * (int(end) - int(start))
            char_preds[int(start) : int(end)] = [int(prediction)] * (int(end) - int(start))

        self.last_generated_text = text
        self.last_generation_trace = trace
        self.last_method_scores = {
            name: float(np.mean(values))
            for name, values in zip(method_names, method_values)
        }
        grouped_preds, grouped_probs = self._aggregate_context_predictions(
            group_ids,
            [char_preds],
            [char_probs],
            binary=(self.config.num_classification_heads <= 2),
        )
        char_labels = (
            convert_spans_to_labels(labels, grouped_probs)
            if labels is not None
            else None
        )
        return grouped_probs, grouped_preds, char_labels

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

            # Alignment is a correctness contract, not a formatting convenience.
            if ref_token_counts is not None:
                n = ref_token_counts[sample_idx]
                if len(token_scores) != n:
                    raise ValueError(
                        'Token uncertainty score/token mismatch: '
                        f'{len(token_scores)} scores for {n} generated tokens.'
                    )

            all_token_probs.extend(token_scores.tolist())
            all_token_preds.extend(token_preds.tolist())

        return all_token_probs, all_token_preds
