from typing import Any, Dict, List

from sirin.detection.processors.hidden import HiddensProcessor
from sirin.definitions import FeatureType


class SublayersProcessor(HiddensProcessor):
    _feature_type: str = FeatureType.SUBLAYER.value
    
    def generate_features(self, samples: List[List[Dict]]) -> Dict[str, Any]:
        # Process uncached samples in batch for efficiency
        model_states = self._extractor.generate_hiddens(
            samples,
            return_hiddens=False,
            return_sublayers=True,
            layers=self.layers,
            padding=self.config.padding,
            max_length=self.config.max_length,
            truncation=self.config.truncation,
            token_locator=self._token_locator,
        )

        return {
            'features': model_states.sublayers,
            'locations': model_states.locations,
        }
