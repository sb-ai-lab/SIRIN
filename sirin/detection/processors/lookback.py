from typing import Any, Dict, List, Optional, Tuple

import torch

from sirin.definitions import FeatureType, TokenLocation
from sirin.detection.processors.hidden import HiddensProcessor
from sirin.inference.adapters.base import ModelAdapterBase
from sirin.models.detection import LookbacksProcessorConfig
from sirin.utils.config_manager import validate_hydra_config


class LookbacksProcessor(HiddensProcessor):
    _feature_type: str = FeatureType.LOOKBACK.value

    @validate_hydra_config
    def __init__(
        self,
        config: LookbacksProcessorConfig,
        extractor: ModelAdapterBase,
        cache_dir: Optional[str] = None,
    ):
        super().__init__(config=config, extractor=extractor, cache_dir=cache_dir)
        # Override layers with attention-specific layers
        self.layers = (
            config.layers if hasattr(config, 'layers') and config.layers else [-1]
        )
        self.border = config.border

    def postprocess(self, features):
        reshaped_features = [torch.cat(feature, dim=-1) for feature in features]
        pooled_samples = []
        for sample in reshaped_features:
            if sample.shape[0] == 0:
                raise ValueError(
                    f'Empty lookback span (border {self.border.value} absent, e.g. missing in '
                    f'a split chunk). Refusing to impute a zero feature into metrics — fix '
                    f'locator/border coverage or exclude such samples upstream.'
                )
            elif self.config.pooling_type == 'mean':
                pooled_sample = sample.mean(dim=0)[None, :].tolist()
            elif self.config.pooling_type == 'max':
                pooled_sample = sample.amax(dim=0)[None, :].tolist()
            elif self.config.pooling_type == 'last':
                pooled_sample = sample[-1, :][None, :].tolist()
            else:
                pooled_sample = sample.tolist()
            pooled_samples.append(pooled_sample)
        padded_features = [[feature] for feature in pooled_samples]

        return padded_features

    def _compute_layer_lookback(
        self,
        attention_layer: torch.Tensor,
        context_length: int,
        token_length: int,
    ) -> torch.Tensor:
        num_heads = attention_layer.shape[0]
        lookback_ratio = torch.zeros((num_heads, token_length), dtype=torch.float32)

        for tok_idx in range(context_length, token_length):
            attn_on_context = attention_layer[:, tok_idx, :context_length].mean(-1)
            attn_on_new_tokens = attention_layer[
                :, tok_idx, context_length : tok_idx + 1
            ].mean(-1)

            denom = attn_on_context + attn_on_new_tokens + 1e-10
            lookback_ratio[:, tok_idx] = attn_on_context / denom

        lookback_ratio = lookback_ratio.transpose(0, 1)  # (seq_len, num_heads)

        # Filter to selected attention heads (e.g., one per KV group in GQA models)
        if hasattr(self.config, 'attention_heads') and self.config.attention_heads is not None:
            head_indices = self.config.attention_heads
            lookback_ratio = lookback_ratio[:, head_indices]

        return lookback_ratio.cpu().to(dtype=torch.float32)

    def generate_features(self, samples: List[List[Dict]]) -> Dict[str, Any]:
        """Generate attention features."""
        model_states = self._extractor.generate_hiddens(
            samples,
            return_hiddens=False,
            return_attention=True,
            layers=self.layers,
            padding=self.config.padding,
            max_length=self.config.max_length,
            truncation=self.config.truncation,
            token_locator=self._token_locator,
        )

        model_states = self.compute_lookback(
            model_states.attentions, model_states.locations, model_states.masks
        )

        return model_states

    def compute_lookback(self, attentions, locations, masks) -> List[Tuple[torch.Tensor]]:
        if locations:
            lookback_ratios = []
            for i, loc in enumerate(locations):
                # Get the first substring as a border
                border = self.border.value + '_0' if self.border == TokenLocation.SUBSTRING else self.border.value
                border_idx = loc.get(border)
                if not border_idx:
                    raise ValueError(
                        f'No border `{self.border}` found for lookback calculation'
                    )
                context_length = (
                    border_idx[-1] if isinstance(border_idx, list) else border_idx
                )
                # (batch_size, num_layers, num_heads, seq_len, seq_len)
                token_length = masks[i].sum(dim=-1)

                # (batch_size, num_layers(seq_len, num_heads))
                lookback_ratios.append(
                    [
                        self._compute_layer_lookback(
                            attention_layer, context_length, token_length
                        )
                        for attention_layer in attentions[i]
                    ]
                )

        else:
            raise ValueError(
                f'No border `{self.border}` found for lookback calculation. Locations are empty'
            )

        return {
            'features': lookback_ratios,
            'locations': locations,
        }
