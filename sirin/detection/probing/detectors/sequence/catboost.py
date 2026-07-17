from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

import numpy as np
from loguru import logger as lg
from catboost import CatBoostClassifier
from torch.utils.data import DataLoader

from sirin.definitions import DetectionLevel, Phase
from sirin.loggers import LoggerBase
from sirin.detection.probing.detectors.base import ProbingDetectorBase
from sirin.detection.probing.detectors.utils.detection import (
    check_features_for_nan,
    handle_binary_multiclass_probs,
)
from sirin.detection.probing.detectors.utils.training import (
    calibrate_and_evaluate,
    preprocess_dataloader_to_numpy,
)
from sirin.detection.probing.training.callbacks import CatBoostLoggerCallback
from sirin.detection.processors import FeatureProcessorBase
from sirin.models.detection import (
    ProbingDetectorConfig,
    DetectionResult,
    TrainingArgsConfig,
)


class SequenceCatboostProbingDetector(ProbingDetectorBase):
    """Catboost detector implementation with compression support."""

    detection_level = DetectionLevel.SEQUENCE

    def __init__(
        self, config: ProbingDetectorConfig, feature_processor: FeatureProcessorBase
    ):
        super().__init__(config=config, feature_processor=feature_processor)

    def detect(
        self,
        samples: List[Dict[Any, str]],
        labels: Optional[np.ndarray] = None,
        **kwargs,
    ) -> Tuple[np.ndarray, np.ndarray, Optional[np.ndarray]]:
        """
        Detect with CatBoost model.

        Uses gradient boosting trees for classification on pooled hidden features.
        """
        samples, group_ids = self._split_context_samples(samples)

        features, _ = self.feature_processor(samples)
        check_features_for_nan(features, samples)

        features, masks = self._process_sequence_features(features)
        features = [feature.reshape(feature.shape[0], -1) for feature in features]
        features = np.concatenate(features, axis=-1)

        probs = self.model.predict_proba(features)
        probs, preds = handle_binary_multiclass_probs(
            probs, self.threshold, is_binary=(self.config.num_classification_heads <= 2)
        )

        preds, probs = self._aggregate_context_predictions(
            group_ids, preds, probs, binary=(self.config.num_classification_heads <= 2)
        )

        return probs, preds, labels

    def setup_model(self):
        """Setup the CatBoost model."""
        self.model = CatBoostClassifier(
            random_state=self.config.seed, **self.config.kwargs
        )

    def _preprocess_data(
        self, data_loader: DataLoader
    ) -> Tuple[np.ndarray, np.ndarray]:
        """Extract and preprocess features from DataLoader."""
        return preprocess_dataloader_to_numpy(data_loader)

    def _train_metamodel(
        self,
        cfg: TrainingArgsConfig,
        train_loader: DataLoader,
        val_loader: Optional[DataLoader] = None,
        group_ids: Optional[List[int]] = None,
        logger: Optional[LoggerBase] = None,
        **kwargs,
    ) -> DetectionResult:
        """Train the metamodel with proper scaling and compression handling."""

        X_train_np, y_train_np = self._preprocess_data(train_loader)

        val_loader = val_loader or train_loader
        X_val_np, y_val_np = self._preprocess_data(val_loader)

        callbacks = [CatBoostLoggerCallback(logger)] if logger else []
        self.model.fit(
            X_train_np, y_train_np,
            eval_set=(X_val_np, y_val_np),
            verbose=False,
            callbacks=callbacks,
        )

        val_probs_full = self.model.predict_proba(X_val_np)

        val_probs, val_predictions, self.threshold, val_metrics = calibrate_and_evaluate(
            val_probs_full, y_val_np, self.config, cfg.metrics
        )

        if logger:
            logger.log_metrics(val_metrics, -1, prefix='/train')

        return DetectionResult(
            metrics=val_metrics,
            probs=val_probs,
            threshold=self.threshold,
        )

    def _save_model(self, save_dir: Path) -> None:
        """Save the CatBoost model to directory."""
        model_path = save_dir / 'catboost_model'
        self.model.save_model(str(model_path))
        lg.info(f"Saved CatBoost model to {model_path}")

    def _load_model(self, load_dir: Path) -> None:
        """Load the CatBoost model from directory."""
        model_path = load_dir / 'catboost_model'

        if not model_path.exists():
            raise FileNotFoundError(f"Model file not found at: {model_path}")

        self.model = CatBoostClassifier(random_state=self.config.seed).load_model(
            str(model_path)
        )
        lg.info(f"Loaded CatBoost model from {model_path}")
