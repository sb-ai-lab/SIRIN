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

        self.use_cache = config.cache_features
        self.cache_saver = None
        if self.use_cache and cache_dir:
            self.cache_saver = LayerFeatureCacheSaver(
                model_name=extractor.config.model_path,
                save_dir=cache_dir,
            )

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
