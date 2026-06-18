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
    check_features_for_nan_with_indices,
    compute_token_cumulative_lengths,
    handle_binary_multiclass_probs,
)
from sirin.detection.utils.token import rearrange_token_predictions, convert_spans_to_labels
from sirin.detection.probing.detectors.utils.training import (
    calibrate_and_evaluate,
    preprocess_dataloader_to_numpy,
)
from sirin.detection.processors import FeatureProcessorBase

# from sirin.detection.tabpfn_wide.tabpfnwide.patches import fit
from sirin.models.detection import (
    DetectionResult,
    ProbingDetectorConfig,
    TrainingArgsConfig,
)


class TokenTabPFNProbingDetector(ProbingDetectorBase):
    """Enhanced TabPFN detector with robust scaling and compression functionality."""

    detection_level = DetectionLevel.TOKEN

    def __init__(
        self, config: ProbingDetectorConfig, feature_processor=FeatureProcessorBase
    ):
        super().__init__(config=config, feature_processor=feature_processor)

    def detect(
        self,
        samples: List[str],
        labels: Optional[np.ndarray] = None,
        **kwargs,
    ) -> Tuple[np.ndarray, np.ndarray, Optional[np.ndarray]]:
        """Detect with proper scaling and compression handling."""
        samples, group_ids = self._split_context_samples(samples)

        features, answer_indices = self.feature_processor(samples)
        check_features_for_nan_with_indices(features, samples, answer_indices)

        # Compute cumulative token lengths for slicing
        all_lengths = compute_token_cumulative_lengths(features)

        features, _, offsets, _ = self._process_token_features(
            features, samples, answer_indices, labels
        )

        target_dim = 500
        slice_size = max(1, int(target_dim / len(features)))

        processed_features = []
        for feature in features:
            flat_feat = feature.reshape(feature.shape[0], -1).cpu().numpy()
            flat_feat = flat_feat[:, :slice_size]
            processed_features.append(flat_feat)

        features = np.concatenate(processed_features, axis=-1)

        token_probs = self.model.predict_proba(features)
        token_probs, token_preds = handle_binary_multiclass_probs(
            token_probs, self.threshold,
            is_binary=(self.config.num_classification_heads <= 2)
        )

        # Rearrange token predictions to character-level per sample
        char_probs, char_preds = rearrange_token_predictions(
            token_probs, token_preds, offsets, all_lengths
        )

        char_preds, char_probs = self._aggregate_context_predictions(
            group_ids, char_preds, char_probs,
            binary=(self.config.num_classification_heads <= 2)
        )

        # Convert hallucination spans to character-level labels (no token-level conversion)
        if labels is not None:
            char_labels = convert_spans_to_labels(labels, char_probs)
        else:
            char_labels = None

        return char_probs, char_preds, char_labels

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
                    ignore_pretraining_limits=True,
                    **self.config.kwargs,
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
        max_features_per_layer = max(1, int(500 / len(self.config.embedding_dim)))
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

        self.model.fit(X_train_np[:50000], y_train_np[:50000])

        val_loader = val_loader or train_loader
        X_val_np, y_val_np = self._preprocess_data(val_loader)

        val_probs_list = []
        batch_size = 1000
        for i in range(0, len(X_val_np), batch_size):
            batch_probs = self.model.predict_proba(X_val_np[i : i + batch_size])
            val_probs_list.append(batch_probs)
        val_probs_full = np.concatenate(val_probs_list, axis=0)

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
