from abc import abstractmethod
from typing import Dict, List, Optional, Tuple
from pathlib import Path

import torch
import joblib
from loguru import logger as lg
from torch.utils.data import DataLoader
import numpy as np

from sirin.definitions import DetectionLevel, CompressionMethod
from sirin.detection.base import DetectorBase
from sirin.loggers import LoggerBase
from sirin.detection.probing.preprocessing import FeaturePreprocessor
from sirin.detection.processors import FeatureProcessorBase
from sirin.detection.utils.token import get_token_labels, get_answer_offsets
from sirin.models.detection import (
    DetectionResult,
    ProbingDetectorConfig,
    TrainingArgsConfig,
)
from sirin.utils.config_manager import validate_hydra_config
from sirin.utils.config_serialization import (
    serialize_probing_detector_config,
    deserialize_probing_detector_config,
)


class ProbingDetectorBase(DetectorBase):
    detection_level: DetectionLevel

    @validate_hydra_config
    def __init__(
        self,
        config: ProbingDetectorConfig,
        feature_processor: Optional[FeatureProcessorBase] = None,
    ):
        super().__init__(config=config)
        self.feature_processor = feature_processor
        self.feature_processor.setup_extractor()
        self._cold_run()

        compression_config = getattr(config, 'compression', {})
        self.compressor = FeaturePreprocessor(
            method=compression_config.method,
            scaling_method=compression_config.scaling_method,
            compression_threshold=compression_config.threshold,
            target_dimensions=compression_config.target_dimensions,
            random_state=self.config.seed,
            **compression_config.kwargs,
        )

        self.setup_model()

    def _cold_run(self) -> Tuple[List[int], List[int]]:
        batch = [
            [
                {'content': "This is cold run sample", 'role': 'user'},
                {'content': "Yeah this is it", 'role': 'assistant'},
            ]
        ]

        locators = [getattr(self.feature_processor, '_token_locator', None)]
        locators.extend(
            getattr(proc, '_token_locator', None)
            for proc in getattr(self.feature_processor, 'processors', [])
        )
        substrings = []
        for locator in locators:
            cfg = getattr(locator, 'config', None)
            if cfg is not None and cfg.locate_substring and cfg.substrings:
                substrings.extend(cfg.substrings)
        if substrings:
            batch[0][0]['content'] += ' ' + ' '.join(substrings)
        features, _ = self.feature_processor(batch)

        embedding_dim = [torch.tensor(feature[0]).shape[-1] for feature in features]
        num_features = [torch.tensor(feature[0]).shape[0] for feature in features]

        self.config.embedding_dim = embedding_dim
        self.config.num_features = num_features

        if self.config.compression.method != CompressionMethod.NONE:
            if self.detection_level == DetectionLevel.SEQUENCE:
                # (batch, num_layers, max_length, emb_dim)
                n_features = sum(torch.tensor(f[0]).numel() for f in features)
            else:
                # (total_tokens, num_layers, 1, emb_dim) after unsqueeze
                n_features = sum(
                    torch.tensor(f[0]).shape[0] * torch.tensor(f[0]).shape[-1]
                    for f in features
                )
            dims = []
            for feature in features:
                num_layers, num_tokens, emb_dim = torch.tensor(feature[0]).shape
                feature_ratio = num_layers * emb_dim / n_features
                if self.detection_level == DetectionLevel.SEQUENCE:
                    feature_ratio *= num_tokens
                target_dims = max(
                    1,
                    int(
                        self.config.compression.target_dimensions
                        * feature_ratio
                        / num_layers
                    ),
                )
                dims.append(target_dims)
            self.config.embedding_dim = dims

    def train(
        self,
        cfg: TrainingArgsConfig,
        train_loader: DataLoader,
        val_loader: Optional[DataLoader] = None,
        group_ids: Optional[List[int]] = None,
        logger: Optional[LoggerBase] = None,
        **kwargs,
    ) -> DetectionResult:
        return self._train_metamodel(
            cfg=cfg,
            train_loader=train_loader,
            val_loader=val_loader,
            group_ids=group_ids,
            logger=logger,
            **kwargs,
        )

    @abstractmethod
    def _train_metamodel(
        self,
        cfg: TrainingArgsConfig,
        train_loader: DataLoader,
        val_loader: Optional[DataLoader] = None,
        group_ids: Optional[List[int]] = None,
        logger: Optional[LoggerBase] = None,
        **kwargs,
    ) -> DetectionResult:
        pass

    def _process_sequence_features(
        self, features: List[torch.Tensor]
    ) -> Tuple[torch.Tensor, torch.Tensor]:
        """Sequence-specific feature processing."""
        features, masks = self.pad_sequence_features(features)
        features = self.sequence_scale_compress(features, masks)

        return features, masks

    def _process_token_features(
        self,
        features: List[torch.Tensor],
        samples: List[List[Dict]],
        answer_indices: List[List[int]],
        labels: Optional[List[List[Tuple[int, int]]]] = None,
    ) -> Tuple[torch.Tensor, torch.Tensor, torch.Tensor, torch.Tensor]:
        """Token-specific feature processing."""

        offsets, _, _ = get_answer_offsets(samples, self.feature_processor._extractor)

        if labels is not None:
            labels = get_token_labels(offsets, labels)

        features, masks, offsets, labels = self.flatten_token_features(
            features, offsets, labels
        )

        features = self.token_scale_compress(features, masks)

        return features, masks, offsets, labels

    def _logits_to_probs_preds(
        self, logits: torch.Tensor
    ) -> Tuple[np.ndarray, np.ndarray]:
        probs, preds = super()._logits_to_probs_preds(logits)
        return probs.detach().cpu().numpy(), preds.detach().cpu().numpy()

    def flatten_token_features(
        self,
        features: List[torch.Tensor],
        offsets: List[List[Tuple[int, int]]],
        labels: Optional[List[torch.Tensor]] = None,
    ) -> Tuple[
        List[torch.Tensor],
        List[torch.Tensor],
        List[List[Tuple[int, int]]],
        Optional[List[torch.Tensor]],
    ]:
        all_masks = []
        all_hiddens = []

        for index in range(len(features)):
            reshaped_hiddens = []
            reshaped_mask = []
            for hidden in features[index]:
                hidden = torch.tensor(hidden).permute(1, 0, 2)
                new_mask = (hidden.sum(dim=-1) != 0).long()
                reshaped_hiddens.append(hidden)
                reshaped_mask.append(new_mask)
            all_hiddens.append(torch.cat(reshaped_hiddens))
            all_masks.append(torch.cat(reshaped_mask))

        if labels is not None:
            labels = torch.cat(
                [torch.tensor(label) for label in labels]
            )  # may be better

        offsets = torch.cat(
            [torch.tensor(offset, dtype=torch.long) for offset in offsets]
        )

        return all_hiddens, all_masks, offsets, labels

    def token_scale_compress(
        self, features: List[torch.Tensor], masks: List[torch.Tensor]
    ) -> List[torch.Tensor]:
        features = [feature.unsqueeze(-2).float() for feature in features]
        masks = [mask.unsqueeze(-2) for mask in masks]

        if self.compressor.is_fitted:
            new_features = self.compressor.transform(
                [feature.numpy() for feature in features]
            )
        else:
            new_features = self.compressor.fit_transform(
                [feature.numpy() for feature in features],
                [mask.unsqueeze(-1).numpy() for mask in masks],
            )

        new_features = [torch.tensor(feature) for feature in new_features]

        return new_features

    def pad_sequence_features(
        self, features: List[torch.Tensor]
    ) -> Tuple[List[torch.Tensor], List[torch.Tensor]]:
        all_masks = []
        all_features = []
        for feature in features:
            padded_features = []
            for hidden in feature:
                hidden = torch.tensor(hidden)

                if self.config.truncation_side == 'right':
                    hidden = hidden[:, : self.config.max_length]
                else:
                    hidden = hidden[:, -self.config.max_length :]

                if hidden.shape[1] < self.config.max_length:
                    if self.config.padding_side == 'right':
                        pad = (0, 0, 0, self.config.max_length - hidden.shape[1])
                    else:
                        pad = (0, 0, self.config.max_length - hidden.shape[1], 0)
                    hidden = torch.nn.functional.pad(
                        input=hidden,
                        pad=pad,
                        mode='constant',
                        value=0,
                    )
                padded_features.append(hidden)
            padded_features = torch.stack(padded_features)

            mask = (
                padded_features.sum(dim=-1) != 0
            ).long()  # (batch_size, num_layers, seq_len)
            all_features.append(padded_features)
            all_masks.append(mask)

        return all_features, all_masks

    def sequence_scale_compress(
        self, features: List[torch.Tensor], masks: List[torch.Tensor]
    ) -> List[torch.Tensor]:
        if self.compressor.is_fitted:
            new_features = self.compressor.transform(
                [feature.float().numpy() for feature in features]
            )
        else:
            new_features = self.compressor.fit_transform(
                [feature.float().numpy() for feature in features],
                [mask.unsqueeze(-1).numpy() for mask in masks],
            )

        new_features = [torch.tensor(feature) for feature in new_features]

        return new_features

    def _save_config(self, save_dir: Path):
        config_dict = serialize_probing_detector_config(self.config, self.threshold)
        joblib.dump(config_dict, save_dir / 'config.joblib')
        lg.info(f"Saved config to {save_dir / 'config.joblib'}")

    def _load_config(self, load_dir: Path):
        config_path = load_dir / 'config.joblib'
        if not config_path.exists():
            raise FileNotFoundError(f"Config file not found at: {config_path}")

        config_dict = joblib.load(config_path)
        self.config, self.threshold = deserialize_probing_detector_config(config_dict)
        lg.info(f"Loaded config from {config_path}")

    def _save_compressor(self, save_dir: Path):
        if hasattr(self, 'compressor') and self.compressor.is_fitted:
            compressor_path = save_dir / 'compressor'
            self.compressor.save(str(compressor_path))
            lg.info(f"Saved compressor to {compressor_path}")

    def _load_compressor(self, load_dir: Path):
        compressor_path = load_dir / 'compressor'
        compressor_config_path = load_dir / 'compressor_config.joblib'

        if compressor_config_path.exists():
            self.compressor = FeaturePreprocessor.load(str(compressor_path))
            lg.info(f"Loaded compressor from {compressor_path}")
        else:
            # Initialize empty compressor if not found
            self.compressor = FeaturePreprocessor(
                random_state=getattr(self.config, 'seed', 42),
            )
            lg.info("No saved compressor found, initialized empty compressor")

    @abstractmethod
    def _save_model(self, save_dir: Path):
        pass

    @abstractmethod
    def _load_model(self, load_dir: Path):
        pass

    def _save_additional_components(self, save_dir: Path):
        self._save_model(save_dir)
        self._save_compressor(save_dir)

    def _load_additional_components(self, load_dir: Path):
        self._load_model(load_dir)
        self._load_compressor(load_dir)
