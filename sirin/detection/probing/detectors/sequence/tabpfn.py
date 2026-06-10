from pathlib import Path
from typing import List, Optional, Tuple

import numpy as np
import torch
from loguru import logger as lg
from tabpfn import TabPFNClassifier
from tabpfn.model.loading import load_model_criterion_config
from tabpfn.model_loading import load_fitted_tabpfn_model, save_fitted_tabpfn_model
from torch.utils.data import DataLoader

from sirin.definitions import DetectionLevel, Phase
from sirin.detection.base import LoggerBase
from sirin.detection.probing.detectors.base import ProbingDetectorBase
from sirin.detection.probing.detectors.utils.detection import (
    check_features_for_nan,
    handle_binary_multiclass_probs,
)
from sirin.detection.probing.detectors.utils.training import (
    calibrate_and_evaluate,
    preprocess_dataloader_to_numpy,
)
from sirin.detection.processors import FeatureProcessorBase

# from sirin.detection.tabpfn_wide.tabpfnwide.patches import fit
from sirin.models.detection import (
    ProbingDetectorConfig,
    DetectionResult,
    TrainingArgsConfig,
)


class SequenceTabPFNProbingDetector(ProbingDetectorBase):
    """Enhanced TabPFN detector with robust scaling and compression functionality."""

    detection_level = DetectionLevel.SEQUENCE

    def __init__(
        self, config: ProbingDetectorConfig, feature_processor=FeatureProcessorBase
    ):
        self.state = None
        super().__init__(config=config, feature_processor=feature_processor)

    def detect(
        self, samples: List[str], labels: Optional[np.ndarray] = None, **kwargs
    ) -> Tuple[np.ndarray, np.ndarray, Optional[np.ndarray]]:
        """
        Detect with TabPFN model.

        Uses Transformer-based prior-fitted network with feature slicing to meet model limits.
        """
        samples, group_ids = self._split_context_samples(samples)

        features, _ = self.feature_processor(samples)
        check_features_for_nan(features, samples)

        features, _ = self._process_sequence_features(features)

        # Slice features to meet TabPFN's feature limit
        target_dim = 500
        slice_size = int(target_dim / len(features))
        processed_features = []
        for feature in features:
            flat_feat = feature.reshape(feature.shape[0], -1)
            flat_feat = flat_feat[:, :slice_size]
            processed_features.append(flat_feat)
        features = np.concatenate(processed_features, axis=-1)

        probs = self.model.predict_proba(features)
        probs, preds = handle_binary_multiclass_probs(
            probs, self.threshold, is_binary=(self.config.num_classification_heads <= 2)
        )
        preds, probs = self._aggregate_context_predictions(
            group_ids, preds, probs, binary=(self.config.num_classification_heads <= 2)
        )

        return probs, preds, labels

    def setup_model(self):
        if self.config.model_save_path is None:
            if (
                self.config.checkpoint_path
                and "TabPFN-Wide" in self.config.checkpoint_path
            ):
                self.state, _, _ = load_model_criterion_config(
                    model_path=None,
                    check_bar_distribution_criterion=False,
                    cache_trainset_representation=False,
                    which="classifier",
                    version="v2",
                    download=True,
                )
                self.state.features_per_group = 1
                checkpoint = torch.load(
                    self.config.checkpoint_path,
                    map_location=self.device,
                    weights_only=False,
                )
                self.state.load_state_dict(checkpoint)
                self.model = TabPFNClassifier(
                    n_estimators=1,
                    device=self.device,
                    ignore_pretraining_limits=True,
                    random_state=self.config.seed,
                    **self.config.kwargs,
                )
                # setattr(TabPFNClassifier, "fit", fit)
            else:
                self.model = TabPFNClassifier(
                    model_path=self.config.checkpoint_path,
                    random_state=self.config.seed,
                )
        else:
            self.load(self.config.model_load_path)

    def _save_model(self, save_dir: Path) -> None:
        """Save the TabPFN model to directory."""
        model_path = save_dir / "model.tabpfn_fit"
        save_fitted_tabpfn_model(self.model, model_path)
        lg.info(f"Saved TabPFN model to {model_path}")

    def _load_model(self, load_dir: Path) -> None:
        """Load the TabPFN model from directory."""
        model_path = load_dir / "model.tabpfn_fit"

        if not model_path.exists():
            raise FileNotFoundError(f"Model file not found at: {model_path}")

        self.model = load_fitted_tabpfn_model(model_path, device="cpu")
        lg.info(f"Loaded TabPFN model from {model_path}")

    def _preprocess_data(
        self, data_loader: DataLoader
    ) -> Tuple[np.ndarray, np.ndarray]:
        """Extract and preprocess features with TabPFN feature limit."""
        # TabPFN typically has a 500 feature limit per sample
        max_features_per_layer = int(500 / len(self.config.embedding_dim))
        return preprocess_dataloader_to_numpy(data_loader, max_features_per_layer)

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

        if self.state is not None:
            self.model.fit(X_train_np, y_train_np, model=self.state)
        else:
            self.model.fit(X_train_np, y_train_np)

        val_loader = val_loader or train_loader

        X_val_np, y_val_np = self._preprocess_data(val_loader)
        val_probs_full = self.model.predict_proba(X_val_np)

        val_probs, val_predictions, self.threshold, val_metrics = calibrate_and_evaluate(
            val_probs_full, y_val_np, self.config, cfg.metrics
        )

        if logger:
            logger.log_metrics(val_metrics, -1, prefix="/train")

        return DetectionResult(
            metrics=val_metrics,
            probs=val_probs,
            threshold=self.threshold,
        )
