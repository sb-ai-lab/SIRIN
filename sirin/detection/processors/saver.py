import hashlib
import json
from dataclasses import dataclass
from pathlib import Path
from typing import Dict, List, Optional, Tuple

import joblib
import torch
from loguru import logger as lg

from sirin.definitions import SAVE_FEAT_TEMPLATE


@dataclass
class CachedLayerFeature:
    """Container for cached feature data for a single layer."""

    layer_idx: int
    features: torch.Tensor
    locations: Optional[Dict[str, int]] = None
    sample_hash: Optional[str] = None

    def to_dict(self) -> Dict:
        """Convert to dictionary for saving."""
        return {
            'layer_idx': self.layer_idx,
            'features': self.features.cpu().to(torch.float32).numpy(),
            'locations': self.locations,
            'sample_hash': self.sample_hash,
        }

    @classmethod
    def from_dict(cls, data: Dict) -> 'CachedLayerFeature':
        """Create from dictionary."""
        return cls(
            layer_idx=data['layer_idx'],
            features=torch.from_numpy(data['features']),
            locations=data.get('locations'),
            sample_hash=data.get('sample_hash'),
        )


class LayerFeatureCacheSaver:
    """Specialized saver for layer-wise feature caching."""

    def __init__(
        self,
        model_name: str,
        save_dir: str,
        save_template: str = SAVE_FEAT_TEMPLATE,
        create_dir: bool = True,
    ):
        self.model_name = model_name
        self.save_dir = Path(save_dir)
        self.save_template = save_template

        self.cache_base_dir = (
            self.save_dir / 'feature_cache' / model_name
        )
        if create_dir:
            self.cache_base_dir.mkdir(parents=True, exist_ok=True)

    def get_sample_hash(self, sample: List[Dict]) -> str:
        # sample.append({'model_name' : self.model_name})
        sample_str = json.dumps(sample, sort_keys=True)
        return hashlib.md5(sample_str.encode()).hexdigest()[:12]  # For readability

    def get_layer_cache_path(
        self, sample_hash: str, layer_idx: int, feature_type: str
    ) -> Path:
        filename = self.save_template.format(
            feature_type=feature_type, sample_hash=sample_hash, layer_idx=layer_idx
        )
        return self.cache_base_dir / filename

    def save_layer_features(
        self,
        sample: List[Dict],
        layer_idx: int,
        features: torch.Tensor,
        locations: Optional[Dict[str, int]] = None,
        feature_type: str = 'hidden',
    ):
        sample_hash = self.get_sample_hash(sample)

        cached_layer = CachedLayerFeature(
            layer_idx=layer_idx,
            features=features,
            locations=locations,
            sample_hash=sample_hash,
        )

        cache_path = self.get_layer_cache_path(sample_hash, layer_idx, feature_type)
        joblib.dump(cached_layer.to_dict(), cache_path)
        lg.debug(f"Saved layer {layer_idx} features to {cache_path.name}")

    def load_layer_features(
        self, sample: List[Dict], layer_idx: int, feature_type: str
    ) -> Optional[CachedLayerFeature]:
        sample_hash = self.get_sample_hash(sample)
        cache_path = self.get_layer_cache_path(sample_hash, layer_idx, feature_type)

        if cache_path.exists():
            try:
                data = joblib.load(cache_path)
                return CachedLayerFeature.from_dict(data)
            except Exception as e:
                lg.warning(f"Failed to load cached features from {cache_path}: {e}")
                return None
        return None

    def check_layers_cached(
        self, sample: List[Dict], required_layers: List[int], feature_type: str
    ) -> bool:
        sample_hash = self.get_sample_hash(sample)

        for layer_idx in required_layers:
            cache_path = self.get_layer_cache_path(sample_hash, layer_idx, feature_type)
            if not cache_path.exists():
                return False
        return True

    def load_all_layers_for_sample(
        self,
        sample: List[Dict],
        layers: List[int],
        feature_type: str = 'hidden',
    ) -> Optional[Tuple[Tuple[torch.Tensor], Optional[Dict]]]:
        # First check if all required layers are available
        if not self.check_layers_cached(sample, layers, feature_type):
            return None

        layer_features = []
        locations = None

        for layer_idx in layers:
            cached_layer = self.load_layer_features(sample, layer_idx, feature_type)
            if cached_layer is None:
                return None  # This shouldn't happen after check_layers_cached
            layer_features.append(cached_layer.features)
            if cached_layer.locations:
                locations = cached_layer.locations

        return tuple(layer_features), locations

    def save_sample_features(
        self,
        sample: List[Dict],
        features: Tuple[torch.Tensor],
        layers: List[int],
        locations: Optional[Dict[str, int]] = None,
        feature_type: str = 'hidden',
    ):
        if len(features) != len(layers):
            raise ValueError(
                f"Number of features ({len(features)}) doesn\'t match number of layers ({len(layers)})"
            )

        for layer_idx, layer_features in zip(layers, features):
            self.save_layer_features(
                sample, layer_idx, layer_features, locations, feature_type
            )

    def get_cached_samples_info(self) -> Dict[str, List[int]]:
        cached_info = {}

        if not self.cache_base_dir.exists():
            return cached_info

        for cache_file in self.cache_base_dir.glob(
            self.save_template.format(sample_hash='*', layer_idx='*')
        ):
            # Parse filename
            parts = cache_file.stem.split('_')
            sample_hash = parts[1]
            layer_idx = int(parts[3])

            if sample_hash not in cached_info:
                cached_info[sample_hash] = []
            cached_info[sample_hash].append(layer_idx)

        # Sort layers for each sample
        for sample_hash in cached_info:
            cached_info[sample_hash].sort()

        return cached_info
