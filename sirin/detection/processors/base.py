from abc import ABC, abstractmethod
from typing import Any, Dict, List, Optional

from sirin.inference.adapters import ModelAdapterBase
from sirin.inference.model_manager import ModelManager
from sirin.inference.token_locators import HfTokenLocator
from sirin.detection.processors.saver import LayerFeatureCacheSaver
from sirin.models.detection import (
    FeatureProcessorBaseConfig,
    ModelStates,
    TokenLocatorConfig,
)


class FeatureProcessorBase(ABC):
    def __init__(self, config: FeatureProcessorBaseConfig, extractor: ModelAdapterBase, cache_dir: Optional[str] = None):
        self.config = config
        self._extractor = extractor
        self._token_locator = HfTokenLocator(
            self.config.token_locator_config or TokenLocatorConfig()
        )
        self.last_debug = None

        self.use_cache = config.cache_features
        self.cache_saver = None
        if self.use_cache and cache_dir:
            self.cache_saver = LayerFeatureCacheSaver(
                model_name=extractor.config.model_path,
                save_dir=cache_dir,
            )

    def _debug_shape(self, value):
        if hasattr(value, 'shape'):
            return list(value.shape)
        if isinstance(value, tuple):
            value = list(value)
        if isinstance(value, list):
            if not value:
                return [0]
            child = self._debug_shape(value[0])
            return [len(value)] + (child or [])
        return None

    def _set_last_debug(self, **artifacts):
        self.last_debug = {
            'processor': type(self).__name__,
            'feature_type': getattr(self, '_feature_type', None),
        }
        for key, value in artifacts.items():
            if key == 'children':
                self.last_debug[key] = value
                continue
            shape = self._debug_shape(value)
            if shape is not None:
                self.last_debug[f'{key}_shape'] = shape

    def setup_extractor(self):
        self._extractor = ModelManager.load_model(self._extractor)

    @abstractmethod
    def __call__(self, samples: List[List[Dict]]) -> Any:
        pass

    @abstractmethod
    def extract_features(self, sample: List[str], **kwargs) -> Dict[str, Any]:
        pass

    @abstractmethod
    def generate_features(self, sample: List[str], **kwargs) -> ModelStates:
        pass

    @abstractmethod
    def locate_features(self) -> Any:
        pass

    @abstractmethod
    def check_features(self, sample: List[str], **kwargs) -> Any:
        pass
