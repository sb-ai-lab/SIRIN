from typing import Any, Dict, List, Optional, Tuple

import torch
from loguru import logger as lg

from sirin.models.detection import HiddensProcessorConfig
from sirin.detection.processors.base import FeatureProcessorBase
from sirin.detection.processors.saver import LayerFeatureCacheSaver
from sirin.detection.utils.basic import flatten_array
from sirin.definitions import FeatureType, SideType
from sirin.inference.adapters.base import ModelAdapterBase
from sirin.utils.config_manager import validate_hydra_config


class HiddensProcessor(FeatureProcessorBase):
    _feature_type: str = FeatureType.HIDDEN.value

    @validate_hydra_config
    def __init__(
        self,
        config: HiddensProcessorConfig,
        extractor: ModelAdapterBase,
        cache_dir: Optional[str] = None,
    ):
        super().__init__(config=config, extractor=extractor, cache_dir=cache_dir)
        self.layers = (
            config.layers if hasattr(config, 'layers') and config.layers else [-1]
        )
        

    def __call__(
        self, samples: List[List[Dict]]
    ) -> Tuple[
        List[torch.Tensor], List[torch.Tensor]
    ]:
        assert self._extractor is not None, 'No feature extractor found.'
        samples_to_process, sample_indices, cached_results = (
            self.check_features(samples)
        )
        features, answer_indices = self.extract_features(
            samples,
            samples_to_process,
            sample_indices,
            cached_results,
        )

        features = self.postprocess(features)
        self._set_last_debug(features=features, answer_indices=answer_indices)
        return [features], answer_indices

    def postprocess(self, features) -> Tuple[torch.Tensor, torch.Tensor]:
        pooled_features = []
        for feature in features:  # list-num_layers(seq_len, embedding_dim)
            pooled_layers = []
            for layer in feature:
                if layer.shape[0] == 0:
                    raise ValueError(
                        'Empty located span in HiddensProcessor.postprocess: the token '
                        'locator matched no tokens for a sample (e.g. border absent in a split '
                        'chunk). Refusing to impute a zero feature into metrics — fix '
                        'locator/border coverage or exclude such samples upstream.'
                    )
                elif self.config.pooling_type == 'mean':
                    pooled_layer = layer.mean(dim=0)[None, :]
                elif self.config.pooling_type == 'max':
                    pooled_layer = layer.amax(dim=0)[None, :]
                elif self.config.pooling_type == 'last':
                    pooled_layer = layer[-1, :][None, :]
                else:
                    pooled_layer = layer
                pooled_layers.append(pooled_layer.tolist())
            pooled_features.append(pooled_layers)
        # (batch_size, num_layers, seq_len, embedding_dim)

        return pooled_features

    def check_features(
        self,
        samples: List[List[Dict]],
    ) -> Tuple[
        List[List[Dict]],
        List[int],
        List[Tuple[int, List[Tuple[torch.Tensor]]]],
    ]:
        # Check cache first
        cached_results = []
        samples_to_process = []
        sample_indices = []

        if self.use_cache and self.cache_saver:
            for i, sample in enumerate(samples):
                cached_data = self.cache_saver.load_all_layers_for_sample(
                    sample,
                    self.layers,
                    self._feature_type,
                )
                if cached_data is not None:
                    features, all_locations = cached_data
                    # Check whether all locations are cached
                    locations = {}
                    for tokloc in self._token_locator.tokens_to_locate:
                        if all_locations and tokloc in all_locations:
                            locations[tokloc] = all_locations[tokloc]
                        else:
                            locations = None
                            break

                    if locations:
                        location_result = self.locate_features(
                            [features], [locations]
                        ) 
                        located_features, token_labels = location_result[0][0], location_result[1][0] # To process an individual sample
                        cached_results.append((i, located_features, token_labels))
                        continue

                samples_to_process.append(sample)
                sample_indices.append(i)
        else:
            samples_to_process = samples
            sample_indices = list(range(len(samples)))

        return samples_to_process, sample_indices, cached_results

    def extract_features(
        self,
        samples: List[List[Dict]],
        samples_to_process: List[List[Dict]],
        sample_indices,
        cached_results,
    ) -> List[Tuple[torch.Tensor]]:
        """Get features with caching support."""

        # Process uncached samples
        new_located_features = []
        new_answer_indices = []
        if samples_to_process:
            model_states = self.generate_features(samples_to_process)
            new_features, locations = (
                model_states['features'],
                model_states['locations'],
            )
            
            if locations:
                new_located_features, new_answer_indices = self.locate_features(
                    new_features, locations
                )

            # Cache the new features individually
            if self.use_cache and self.cache_saver:
                for sample, features, location in zip(
                    samples_to_process,
                    new_features,
                    locations if locations else [None] * len(new_features),
                ):
                    if isinstance(features, (tuple, list)) and len(features) != len(self.layers):
                        # Attention-based subclasses (AttentionsProcessor,
                        # LookbacksProcessor) on MoE/hybrid-attention models
                        # may receive fewer tensors than requested layers —
                        # the adapter filters out-of-range attention indices.
                        # Skip caching to avoid mapping features to wrong layers.
                        lg.warning(
                            f'Feature count ({len(features)}) != configured layers '
                            f'({len(self.layers)}). Skipping cache for this sample.'
                        )
                        continue
                    self.cache_saver.save_sample_features(
                        sample,
                        features,
                        self.layers,
                        location,
                        self._feature_type,
                    )

        # Combine cached and new results in the correct order
        all_features = [None] * len(samples)
        all_answer_indices = [None] * len(samples)

        for idx, features, answer_indices in cached_results:
            all_features[idx] = features
            all_answer_indices[idx] = answer_indices

        for idx, features, answer_indices in zip(sample_indices, new_located_features, new_answer_indices):
            all_features[idx] = features
            all_answer_indices[idx] = answer_indices

        if len(cached_results) > 0 or len(new_located_features) > 0:
            lg.debug(
                f"Loaded {len(cached_results)} from cache, computed {len(new_located_features)} new features"
            )

        return all_features, all_answer_indices

    def generate_features(self, samples: List[List[Dict]]) -> Dict[str, Any]:
        # Process uncached samples in batch for efficiency
        model_states = self._extractor.generate_hiddens(
            samples,
            return_hiddens=True,
            layers=self.layers,
            padding=self.config.padding,
            truncation=self.config.truncation,
            max_length=self.config.max_length,
            token_locator=self._token_locator,
        )
        return {
            'features': model_states.hiddens,
            'locations': model_states.locations,
        }

    def _get_side_indices(self, positions: List[int], seq_len: int) -> List[int]:
        """Get indices based on the specified self.config.side relative to the positions."""
        if not positions:
            return []

        positions = sorted(positions)

        if self.config.side == SideType.LEFT:
            # Get indices to the left of the rightmost position
            return list(range(0, positions[-1]))
        elif self.config.side == SideType.RIGHT:
            # Get indices to the right of the leftmost position
            return list(range(positions[0], seq_len))
        elif self.config.side == SideType.INNER:
            # Get indices between the first and last positions (exclusive)
            if len(positions) < 2:
                return []
            return list(range(positions[0] + 1, positions[-1]))
        elif self.config.side == SideType.OUTER:
            # Get indices outside the range (left of first + right of last)
            left_indices = list(range(0, positions[0]))
            right_indices = list(range(positions[-1] + 1, seq_len))
            return left_indices + right_indices
        else:
            raise ValueError(
                f"Invalid self.config.side: {self.config.side}. Must be one of: left, right, inner, outer"
            )

    def locate_features(
        self,
        hiddens: List[Tuple[torch.Tensor]],
        locations: List[Optional[Dict[str, int]]],
    ) -> Tuple[List[Tuple[torch.Tensor]], List[List[int]]]:
        """Extract features at specific token locations."""

        located_features = []
        answer_indices = []

        for hidden, location in zip(
            hiddens, locations
        ):
            if location:
                if self.config.separate:
                    # Get sequence length from the first layer
                    seq_len = hidden[0].shape[0] if hidden is not None else 0
                    positions = flatten_array(list(location.values()), drop_none=True)
                    side_indices = self._get_side_indices(positions, seq_len)

                    if side_indices:
                        located_hidden = tuple(layer[side_indices] for layer in hidden)
                        indices = side_indices
                    else:
                        # No indices on the specified return empty tensors
                        located_hidden = tuple(
                            torch.empty(0, layer.shape[-1]) for layer in hidden
                        )
                        indices = []
                else:
                    # Original behavior: extract features at exact positions
                    positions = flatten_array(list(location.values()), drop_none=True)
                    located_hidden = tuple(
                        layer[positions] for layer in hidden
                    )
                    indices = positions
            else:
                # No locations found, return empty tensors
                located_hidden = tuple(
                    torch.empty(0, layer.shape[-1]) for layer in hidden
                )
                indices = []
            located_features.append(located_hidden)
            answer_indices.append(indices)

        return located_features, answer_indices
