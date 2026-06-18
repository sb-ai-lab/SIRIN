from typing import Any, Dict, List, Optional, Tuple, Type

import torch
from loguru import logger as lg

from sirin.detection.processors.attention import AttentionsProcessor
from sirin.detection.processors.base import FeatureProcessorBase
from sirin.detection.processors.hidden import HiddensProcessor
from sirin.detection.processors.logit import LogitsProcessor
from sirin.detection.processors.lookback import LookbacksProcessor
from sirin.detection.processors.sublayer import SublayersProcessor
from sirin.inference.adapters import ModelAdapterBase
from sirin.inference.token_locators import HfTokenLocator
from sirin.models.detection import EnsembleProcessorConfig, ModelStates
from sirin.utils.config_manager import validate_hydra_config


class ProcessorRegistry:
    """Central registry for processor classes and feature type mappings."""

    CONFIG_TO_PROCESSOR: Dict[str, Type[FeatureProcessorBase]] = {
        'HiddensProcessorConfig': HiddensProcessor,
        'LookbacksProcessorConfig': LookbacksProcessor,
        'AttentionsProcessorConfig': AttentionsProcessor,
        'LogitsProcessorConfig': LogitsProcessor,
        'SublayersProcessorConfig': SublayersProcessor,
    }

    FEATURE_TO_ATTRIBUTE: Dict[str, str] = {
        'hidden': 'hiddens',
        'sublayer': 'sublayers',
        'lookback': 'attentions',
        'attention': 'attentions',
    }

    @classmethod
    def get_processor_class(cls, config_type: str) -> Type[FeatureProcessorBase]:
        """Get processor class for a given config type."""
        if config_type not in cls.CONFIG_TO_PROCESSOR:
            raise ValueError(f"Unknown config type: {config_type}")
        return cls.CONFIG_TO_PROCESSOR[config_type]

    @classmethod
    def get_state_attribute(cls, feature_type: str) -> str:
        """Get model state attribute for a given feature type."""
        if feature_type not in cls.FEATURE_TO_ATTRIBUTE:
            raise ValueError(f"Unknown feature type: {feature_type}")
        return cls.FEATURE_TO_ATTRIBUTE[feature_type]


class EnsembleProcessor(FeatureProcessorBase):
    """Ensemble processor that coordinates multiple feature processors."""

    @validate_hydra_config
    def __init__(
        self,
        config: EnsembleProcessorConfig,
        extractor: ModelAdapterBase,
        cache_dir: str = './outputs',
    ):
        super().__init__(config=config, extractor=extractor, cache_dir=cache_dir)
        self.extractor = extractor
        self.cache_dir = cache_dir
        self._token_locators = [HfTokenLocator(config=cfg.token_locator_config) for cfg in self.config.processor_configs]
        self.processors = self._create_processors_from_configs()

    def _create_processors_from_configs(self) -> List[FeatureProcessorBase]:
        """Create feature processors from their configurations."""
        processors = []

        for config in self.config.processor_configs:
            config_type = type(config).__name__
            processor_class = ProcessorRegistry.get_processor_class(config_type)

            processor = processor_class(
                config=config,
                cache_dir=self.cache_dir,
                extractor=self.extractor,
            )
            processors.append(processor)

        return processors

    def __call__(self, samples: List[List[Dict]]) -> Tuple[torch.Tensor, torch.Tensor]:
        """Process samples and return features and masks."""
        samples_needing_processing, sample_index_map, processor_cache_info = (
            self.check_features(samples)
        )
        features, answer_indices = self.extract_features(
            samples, samples_needing_processing, processor_cache_info, sample_index_map
        )
        return features, answer_indices

    def _unify_processor_args(self) -> Dict[str, Any]:
        """Unify arguments across all processors for efficient feature extraction."""
        configs = [proc.config for proc in self.processors]

        # Layers union
        layers = sorted(
            set().union(*[set(getattr(cfg, 'layers', []) or []) for cfg in configs])
        )

        # Boolean resolution
        padding = any(cfg.padding for cfg in configs)  # enable if any needs it
        truncation = all(cfg.truncation for cfg in configs)  # only if all allow it

        # Numeric resolution
        max_length_vals = [
            cfg.max_length for cfg in configs if cfg.max_length is not None
        ]
        max_length = min(max_length_vals) if max_length_vals else None

        return {
            'layers': layers,
            'padding': padding,
            'truncation': truncation,
            'max_length': max_length,
            'token_locator': self._token_locators,
        }

    def _analyze_processor_requirements(self) -> Dict[str, bool]:
        """Analyze what features are needed across all processors."""
        requirements = {
            'need_hiddens': False,
            'need_attention': False,
            'need_sublayers': False,
        }

        for proc in self.processors:
            if not hasattr(proc, '_feature_type'):
                continue

            feature_type = proc._feature_type
            if feature_type == 'hidden':
                requirements['need_hiddens'] = True
            elif feature_type in ('attention', 'lookback'):
                requirements['need_attention'] = True
            elif feature_type == 'sublayer':
                requirements['need_sublayers'] = True

        return requirements

    def generate_features(self, samples: List[List[Dict]]) -> ModelStates:
        """Generate features that satisfy all processors" needs."""
        requirements = self._analyze_processor_requirements()
        args = self._unify_processor_args()

        # Store unified layers so _extract_processor_features_subset can
        # filter per-processor features from the shared model output.
        self._unified_layers = args['layers']

        model_states = self.extractor.generate_hiddens(
            samples,
            return_hiddens=requirements['need_hiddens'],
            return_attention=requirements['need_attention'],
            return_sublayers=requirements['need_sublayers'],
            **args,
        )

        return model_states

    def _extract_processor_features_subset(
        self,
        processor: FeatureProcessorBase,
        processor_idx: int,
        shared_model_states: ModelStates,
        sample_indices: List[int],
        sample_index_map: Dict[int, int],
    ) -> Dict[str, Any]:
        """Extract feature subset for a specific processor."""
        proc_features_subset = []
        proc_locations_subset = []
        proc_masks_subset = []

        state_attr = ProcessorRegistry.get_state_attribute(processor._feature_type)

        # Build index mapping from unified layers to this processor's layers.
        # The model was called with _unified_layers (union of all processors),
        # but each processor only needs its own subset.
        unified_layers = getattr(self, '_unified_layers', None)
        proc_layers = getattr(processor, 'layers', None)
        layer_indices = None
        if unified_layers and proc_layers:
            layer_indices = [
                unified_layers.index(ly)
                for ly in proc_layers
                if ly in unified_layers
            ]

        for global_idx in sample_indices:
            local_idx = sample_index_map[global_idx]

            # Handle locations
            locations = None
            if (
                hasattr(shared_model_states, 'locations')
                and shared_model_states.locations
            ):
                locations = shared_model_states.locations[processor_idx][local_idx]
                proc_locations_subset.append(locations)

            # Handle features — filter to processor's layers from unified output
            if hasattr(shared_model_states, state_attr):
                features = getattr(shared_model_states, state_attr)
                if features is not None:
                    sample_features = features[local_idx]
                    if layer_indices is not None and isinstance(sample_features, (tuple, list)):
                        if max(layer_indices) >= len(sample_features):
                            raise ValueError(
                                f'{type(processor).__name__} layer_indices {layer_indices} '
                                f'exceed feature count {len(sample_features)} for '
                                f'state "{state_attr}". Ensure ensemble sub-processor '
                                f'layers are within the model\'s {state_attr} output range.'
                            )
                        sample_features = tuple(sample_features[i] for i in layer_indices)
                    proc_features_subset.append(sample_features)
            
            # Handle masks
            if hasattr(shared_model_states, 'masks') and shared_model_states.masks is not None:
                proc_masks_subset.append(shared_model_states.masks[local_idx])

        # Special handling for lookback features
        if processor._feature_type == 'lookback':
            masks_tensor = torch.stack(proc_masks_subset) if proc_masks_subset else None
            proc_features_subset = processor.compute_lookback(
                proc_features_subset, proc_locations_subset, masks_tensor
            )['features']

        return {
            'features': proc_features_subset,
            'locations': proc_locations_subset if proc_locations_subset else None,
        }

    def _extract_features_for_processor(
        self,
        processor: FeatureProcessorBase,
        all_samples: List[List[Dict]],
        samples_to_process: List[List[Dict]],
        cached_results: List[Tuple],
        sample_indices: List[int],
        model_states: Optional[Dict[str, Any]],
    ) -> List[Tuple[torch.Tensor]]:
        """Extract features for a specific processor using cached and new data."""

        # Process new features if needed
        new_located_features = []
        new_answer_indices = []
        if model_states and samples_to_process:
            new_features, locations = (
                model_states['features'],
                model_states['locations'],
            )

            if locations:
                new_located_features, new_answer_indices = processor.locate_features(
                    new_features, locations
                )

            # Cache the new features
            if processor.use_cache and processor.cache_saver:
                self._cache_processor_features(
                    processor, samples_to_process, new_features, locations 
                )

        # Combine cached and new results in the correct order
        all_features = [None] * len(all_samples)
        all_answer_indices = [None] * len(all_samples)
        
        for idx, features, answer_indices in cached_results:
            all_features[idx] = features
            all_answer_indices[idx] = answer_indices

        for idx, features, answer_indices in zip(sample_indices, new_located_features, new_answer_indices):
            all_features[idx] = features
            all_answer_indices[idx] = answer_indices

        if cached_results or new_located_features:
            lg.debug(
                f"Processor {type(processor).__name__}: "
                f'Loaded {len(cached_results)} from cache, '
                f'computed {len(new_located_features)} new features'
            )

        return all_features, all_answer_indices

    def _cache_processor_features(
        self,
        processor: FeatureProcessorBase,
        samples_to_process: List[List[Dict]],
        new_features: List[torch.Tensor],
        locations: Optional[List[Any]],
    ) -> None:
        """Cache features for a processor."""
        for sample, features, location in zip(
            samples_to_process,
            new_features,
            locations if locations else [None] * len(new_features),
        ):
            processor.cache_saver.save_sample_features(
                sample,
                features,
                processor.layers,
                location,
                processor._feature_type,
            )

    def check_features(
        self, samples: List[List[str]], **kwargs
    ) -> Tuple[set, Dict[int, int], List[Dict]]:
        """Check which features need processing and collect cache information."""
        processor_cache_info = []

        for proc in self.processors:
            samples_to_process, sample_indices, cached_results = proc.check_features(
                samples
            )
            processor_cache_info.append(
                {
                    'processor': proc,
                    'samples_to_process': samples_to_process,
                    'cached_results': cached_results,
                    'sample_indices': sample_indices,
                }
            )

        samples_needing_processing = set()
        sample_index_map = {}  # global_idx -> local_batch_idx

        for info in processor_cache_info:
            for global_idx in info['sample_indices']:
                if global_idx not in sample_index_map:
                    sample_index_map[global_idx] = len(sample_index_map)
                samples_needing_processing.add(global_idx)

        return samples_needing_processing, sample_index_map, processor_cache_info

    def extract_features(
        self,
        samples: List[List[str]],
        samples_needing_processing: set,
        processor_cache_info: List[Dict],
        sample_index_map: Dict[int, int],
    ) -> Tuple[List[torch.Tensor], List[torch.Tensor]]:
        """Extract features for all processors."""
        shared_model_states = None
        if samples_needing_processing:
            unique_samples = [samples[i] for i in sorted(samples_needing_processing)]
            lg.debug(f"Processing {len(unique_samples)} unique samples through model.")
            shared_model_states = self.generate_features(unique_samples)

        processor_outputs = []

        for idx, info in enumerate(processor_cache_info):
            proc = info['processor']
            cached_results = info['cached_results']
            sample_indices = info['sample_indices']

            proc_samples_to_process = info['samples_to_process']

            temp_model_states = None
            if shared_model_states and sample_indices:
                temp_model_states = self._extract_processor_features_subset(
                    proc, idx, shared_model_states, sample_indices, sample_index_map
                )

            proc_new_features, proc_new_answer_indices = self._extract_features_for_processor(
                proc,
                samples,
                proc_samples_to_process,
                cached_results,
                sample_indices,
                temp_model_states,
            )

            padded_features = proc.postprocess(proc_new_features)
            processor_outputs.append(padded_features)

        return processor_outputs, proc_new_answer_indices

    def locate_features(self):
        """Locate features - delegates to parent implementation."""
        return super().locate_features()
