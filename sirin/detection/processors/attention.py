from typing import Any, Dict, List, Optional, Tuple

import torch

from sirin.models.detection import AttentionsProcessorConfig
from sirin.detection.processors.hidden import HiddensProcessor
from sirin.inference.adapters.base import ModelAdapterBase
from sirin.detection.utils.basic import flatten_array
from sirin.definitions import FeatureType
from sirin.utils.config_manager import validate_hydra_config


class AttentionsProcessor(HiddensProcessor):
    _feature_type: str = FeatureType.ATTENTION.value

    @validate_hydra_config
    def __init__(
        self,
        config: AttentionsProcessorConfig,
        extractor: ModelAdapterBase,
        cache_dir: Optional[str] = None,
    ):
        super().__init__(config=config, extractor=extractor, cache_dir=cache_dir)
        # Override layers with attention-specific layers
        self.layers = config.layers if config.layers else [-1]

    def generate_features(self, samples: List[List[Dict]]) -> Dict[str, Any]:
        """Generate attention features."""
        model_states = self._extractor.generate_hiddens(
            samples,
            return_hiddens=False,
            return_attention=True,
            layers=self.layers,
            padding=self.config.padding,
            truncation=self.config.truncation,
            max_length=self.config.max_length,
            token_locator=self._token_locator,
        )
        return {
            'features': model_states.attentions,
            'locations': model_states.locations,
        }

    def locate_features(
        self,
        attentions: List[Tuple[torch.Tensor]],
        locations: List[Optional[Dict[str, int]]],
    ) -> List[Tuple[torch.Tensor]]:
        """Extract attention weights at specific token locations."""
        located_features = []
        answer_indices = []

        for attention, location in zip(attentions, locations):
            if location:
                if self.config.separate:
                    # Get sequence length from the first attention layer
                    seq_len = (
                        attention[0].shape[-1]
                        if attention and len(attention) > 0
                        else 0
                    )
                    positions = flatten_array(list(location.values()), drop_none=True)
                    side_indices = self._get_side_indices(positions, seq_len)

                    if side_indices:
                        # For attention: extract query positions (middle dimension) from specified self.config.side
                        located_attention = tuple(
                            layer[:, side_indices, :] for layer in attention
                        )
                        indices = side_indices
                    else:
                        # No indices on the specified return empty tensors
                        if attention and len(attention) > 0:
                            num_heads = attention[0].shape[0]
                            seq_len = attention[0].shape[-1]
                        else:
                            num_heads, seq_len = 1, 0

                        located_attention = tuple(
                            torch.empty(num_heads, 0, seq_len) for _ in attention
                        )
                        indices = []
                else:
                    # Original behavior: extract attention at exact query positions
                    positions = flatten_array(list(location.values()), drop_none=True)
                    located_attention = tuple(
                        layer[:, positions, :] for layer in attention
                    )
                    indices = positions
            else:
                # No locations found, return empty tensors
                if attention and len(attention) > 0:
                    num_heads = (
                        attention[0].shape[0] if len(attention[0].shape) > 0 else 1
                    )
                    seq_len = (
                        attention[0].shape[-1] if len(attention[0].shape) > 2 else 0
                    )
                else:
                    num_heads, seq_len = 1, 0

                located_attention = tuple(
                    torch.empty(num_heads, 0, seq_len) for _ in attention
                )
                indices = []
            located_attention = tuple(torch.flatten(layer, -2, -1).transpose(0, 1) for layer in located_attention)
            located_features.append(located_attention)
            answer_indices.append(indices)

        return located_features, answer_indices
