from typing import Any, Dict, List, Optional, Tuple

import torch

from sirin.definitions import FeatureType
from sirin.detection.processors.hidden import HiddensProcessor
from sirin.detection.utils.basic import flatten_array
from sirin.inference.adapters.base import ModelAdapterBase
from sirin.models.detection import LogitsProcessorConfig
from sirin.utils.config_manager import validate_hydra_config


class LogitsProcessor(HiddensProcessor):
    _feature_type: str = FeatureType.LOGIT.value

    @validate_hydra_config
    def __init__(
        self,
        config: LogitsProcessorConfig,
        extractor: ModelAdapterBase,
        cache_dir: Optional[str] = None,
    ):
        super().__init__(config=config, extractor=extractor, cache_dir=cache_dir)
        # Override layers since logits don't use layers concept
        self.layers = [0]  # Single layer for logits

    def generate_features(self, samples: List[List[Dict]]) -> Dict[str, Any]:
        """Generate logits features."""
        model_states = self._extractor.generate_hiddens(
            samples,
            padding=self.config.padding,
            truncation=self.config.truncation,
            max_length=self.config.max_length,
            return_logits=True,
            return_hiddens=False,
            token_locator=self._token_locator,
        )
        return {
            'features': model_states.logits,
            'locations': model_states.locations,
        }

    def locate_features(
        self,
        logits: List[Tuple[torch.Tensor]],
        locations: List[Optional[Dict[str, int]]],
    ) -> List[Tuple[torch.Tensor]]:
        """Extract logits at specific token locations."""
        located_features = []

        for logit_tuple, location in zip(logits, locations):
            # Handle both tuple and single tensor formats
            logit = logit_tuple[0] if isinstance(logit_tuple, tuple) else logit_tuple

            if location:
                if self.config.separate:
                    # Get sequence length from the logit tensor
                    seq_len = logit.shape[1]
                    positions = flatten_array(list(location.values()), drop_none=True)
                    side_indices = self._get_side_indices(positions, seq_len)

                    if side_indices:
                        located_logit = (logit[:, side_indices],)
                    else:
                        # No indices on the specified return empty tensor
                        vocab_size = logit.shape[-1]
                        located_logit = (torch.empty(0, vocab_size),)
                else:
                    # Original behavior: extract logits at exact positions
                    positions = flatten_array(list(location.values()), drop_none=True)
                    located_logit = (logit[positions],)
            else:
                # No locations found, return empty tensor
                vocab_size = logit.shape[-1]
                located_logit = (torch.empty(0, vocab_size),)

            located_features.append(located_logit)

        return located_features
