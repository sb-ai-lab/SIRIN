from typing import Any, Dict, List, Optional, Tuple

import numpy as np
import torch
import sirin.detection._lm_polygraph_compat  # noqa: F401 — must be before lm-polygraph imports
from lm_polygraph import estimators
from lm_polygraph.defaults.register_default_stat_calculators import (
    register_default_stat_calculators,
)
from lm_polygraph.model_adapters import WhiteboxModelvLLM
from lm_polygraph.utils.builder_enviroment_stat_calculator import BuilderEnvironmentStatCalculator
from lm_polygraph.utils.dataset import Dataset
from lm_polygraph.utils.manager import UEManager
from lm_polygraph.utils.model import BlackboxModel, Model, WhiteboxModel
from loguru import logger as lg

from sirin.definitions import FeatureType
from sirin.detection.processors import (
    FeatureProcessorBase,
    HiddensProcessor,
)
from sirin.inference.adapters import (
    HfModelAdapter,
    ModelAdapterBase,
    OpenAIModelAdapter,
    VllmModelAdapter,
)
from sirin.models.detection import UncertaintyFeatureProcessorConfig
from sirin.utils.config_manager import validate_hydra_config

_ATTENTION_METHODS = frozenset({'RAUQ', 'Focus', 'AttentionScore'})


def _needs_attention(config: UncertaintyFeatureProcessorConfig) -> bool:
    """Check if any configured uncertainty method needs attention weights."""
    if getattr(config, 'output_attentions', False):
        return True
    methods = getattr(config, 'uncertainty_methods', None) or []
    return bool(_ATTENTION_METHODS & set(methods))


def estimate_uncertainty(
    model: Model,
    model_type: str,
    estimators: List[estimators.Estimator],
    user_inputs: List[str],
    assistant_outputs: List[str],
    batch_size: int = 1,
    output_attentions: bool = False,
    top_logprobs: int = 5,
    max_new_tokens: int = 100,
) -> Tuple[List[np.ndarray], List[str], List[List[int]]]:
    blackbox_supports_logprobs = (
        getattr(model, 'supports_logprobs', False) if model_type == 'Blackbox' else False
    )
    man = UEManager(
        Dataset(user_inputs, assistant_outputs, batch_size=batch_size),
        model,
        estimators,
        available_stat_calculators=register_default_stat_calculators(
            model_type=model_type,
            output_hidden_states=not isinstance(model, WhiteboxModelvLLM),
            output_attentions=output_attentions,
            blackbox_supports_logprobs=blackbox_supports_logprobs,
            top_logprobs=top_logprobs,
        ),
        builder_env_stat_calc=BuilderEnvironmentStatCalculator(model),
        generation_metrics=[],
        ue_metrics=[],
        processors=[],
        ignore_exceptions=False,
        verbose=True,
        max_new_tokens=max_new_tokens,
    )
    man()
    ue = [man.estimations[estimator.level, str(estimator)] for estimator in estimators]
    texts = man.stats.get('greedy_texts', None)
    tokens = man.stats.get('greedy_tokens', None)
    if tokens is not None and len(tokens) > 0:
        tokens = [token[:-1] for token in tokens]
    return ue, texts, tokens


class TokenUncertaintyFeatureProcessor(HiddensProcessor):
    _feature_type: str = FeatureType.TOKEN_UNCERTAINTY.value

    @validate_hydra_config
    def __init__(
        self,
        config: UncertaintyFeatureProcessorConfig,
        extractor: ModelAdapterBase,
        cache_dir: Optional[str] = None,
    ):
        super().__init__(config=config, extractor=extractor, cache_dir=cache_dir)
        self.uncertainty_methods = self._initialize_uncertainty_methods()
        self.model_wrapper = None
        self.model_type = None
        self.last_generated_text: str | None = None
        self.last_method_scores: dict[str, float] | None = None

    def setup_extractor(self):
        """Setup the model wrapper for uncertainty estimation"""
        super().setup_extractor()

        if isinstance(self._extractor, OpenAIModelAdapter):
            self.model_wrapper = BlackboxModel.from_openai(
                openai_api_key=getattr(self._extractor.config, 'openai_api_key', None)
                or getattr(self._extractor.config, 'api_key', None),
                model_path=self._extractor.config.model_path,
                supports_logprobs=self.config.supports_logprobs,
                base_url=self._extractor.config.base_url,
                **self.config.model_kwargs,
            )
            self.model_type = 'Blackbox'
        elif isinstance(self._extractor, HfModelAdapter):
            self.model_wrapper = WhiteboxModel(
                self._extractor.model,
                self._extractor.tokenizer,
                **self.config.model_kwargs,
            )
            self.model_type = 'Whitebox'
        elif isinstance(self._extractor, VllmModelAdapter):
            self.model_wrapper = WhiteboxModelvLLM(
                self._extractor.model,
                **self.config.model_kwargs,
            )
            self.model_type = 'Whitebox'
        else:
            raise NotImplementedError

    def __call__(
        self, samples: List[List[Dict]]
    ) -> Tuple[List[torch.Tensor], List[torch.Tensor]]:
        assert self._extractor is not None, 'No feature extractor found.'
        samples_to_process, sample_indices, cached_results = self.check_features(
            samples
        )
        features, answer_indices = self.extract_features(
            samples,
            samples_to_process,
            sample_indices,
            cached_results,
        )

        pooled_features = self.postprocess(features)
        self._set_last_debug(features=pooled_features, answer_indices=answer_indices)
        return [pooled_features], answer_indices

    def _initialize_uncertainty_methods(self) -> Dict[str, Any]:
        """Initialize uncertainty estimation methods"""
        methods = {}
        method_map = {
            'TokenEntropy': estimators.TokenEntropy,
            'MaximumTokenProbability': estimators.MaximumTokenProbability,
            'EPTtu': estimators.EPTtu,
            'EPTdu': estimators.EPTdu,
            'EPTmi': estimators.EPTmi,
            'EPTrmi': estimators.EPTrmi,
            'EPTepkl': estimators.EPTepkl,
            'EPTent5': estimators.EPTent5,
            'EPTent10': estimators.EPTent10,
            'EPTent15': estimators.EPTent15,
            'PETtu': estimators.PETtu,
            'PETdu': estimators.PETdu,
            'PETmi': estimators.PETmi,
            'PETrmi': estimators.PETrmi,
            'PETepkl': estimators.PETepkl,
            'PETent5': estimators.PETent5,
            'PETent10': estimators.PETent10,
            'PETent15': estimators.PETent15,
        }

        methods = [
            method_map[method_name]() for method_name in self.config.uncertainty_methods
        ]

        return methods

    def generate_features(self, samples: List[List[Dict]]) -> Dict[str, Any]:
        # Process uncached samples in batch for efficiency
        user_inputs, assistant_outputs = zip(
            *[(sample[0]['content'], sample[1]['content']) for sample in samples]
        )

        batch_size = getattr(self.config, 'feature_extraction_batch_size', 1)
        uncertainty, generation_texts, generation_tokens = estimate_uncertainty(
            self.model_wrapper,
            self.model_type,
            self.uncertainty_methods,
            list(user_inputs),
            list(assistant_outputs),
            batch_size=batch_size,
            output_attentions=_needs_attention(self.config),
            top_logprobs=getattr(self.config, 'top_logprobs', 5),
            max_new_tokens=getattr(self.config, 'max_new_tokens', 256),
        )
        self.last_generated_text = generation_texts[0] if generation_texts is not None and len(generation_texts) else None  # current UI scores one sample.
        self.last_method_scores = {str(method): float(np.asarray(scores[0], dtype=float).mean()) for method, scores in zip(self.uncertainty_methods, uncertainty) if scores is not None and len(scores)} if uncertainty else None  # expose per-method means without changing outputs.

        token_features = [
            np.stack([ue[i] for ue in uncertainty]).astype(float)
            for i in range(len(generation_texts))
        ]
        # BATCH_SIZE, NUM_ESTIMATORS, NUM_TOKENS
        token_features = [
            torch.tensor(feature).unsqueeze(-1).swapaxes(0, -1)
            for feature in token_features
        ]

        locations = []
        if self._token_locator is not None:
            locations = list(
                map(
                    lambda sample, tokenized_sample: self._token_locator.locate(
                        tokenized_sample, self._extractor.tokenizer, sample
                    ),
                    generation_texts,
                    generation_tokens,
                )
            )

        return {
            'features': token_features,
            'locations': locations,
        }


class SequenceUncertaintyFeatureProcessor(FeatureProcessorBase):
    _feature_type = FeatureType.SEQUENCE_UNCERTAINTY.value

    @validate_hydra_config
    def __init__(
        self,
        config: UncertaintyFeatureProcessorConfig,
        extractor: ModelAdapterBase,
        cache_dir: Optional[str] = None,
    ):
        super().__init__(config=config, extractor=extractor, cache_dir=cache_dir)
        self.layers = (
            config.layers if hasattr(config, 'layers') and config.layers else [-1]
        )
        self.uncertainty_methods = self._initialize_uncertainty_methods()
        self.model_wrapper = None
        self.last_generated_text: str | None = None
        self.last_method_scores: dict[str, float] | None = None

    def _initialize_uncertainty_methods(self) -> Dict[str, Any]:
        """Initialize uncertainty estimation methods"""
        methods = {}
        method_map = {
            'MonteCarloSequenceEntropy': estimators.MonteCarloSequenceEntropy,
            'MonteCarloNormalizedSequenceEntropy': estimators.MonteCarloNormalizedSequenceEntropy,
            'MaximumSequenceProbability': estimators.MaximumSequenceProbability,
            'MeanTokenEntropy': estimators.MeanTokenEntropy,
            'Perplexity': estimators.Perplexity,
            'LexicalSimilarity': estimators.LexicalSimilarity,
            'ClaimConditionedProbability': estimators.ClaimConditionedProbability,
            'RAUQ': estimators.RAUQ,
            'SAR': estimators.SAR,
            # Experimental features:
            'TokenSAR': estimators.TokenSAR,
            'SentenceSAR': estimators.SentenceSAR,
            'EigValLaplacian': estimators.EigValLaplacian,
            'DegMat': estimators.DegMat,
            'Eccentricity': estimators.Eccentricity,
            'LexicalSimilarity': estimators.LexicalSimilarity,
            'EigenScore': estimators.EigenScore,
            'AttentionScore': estimators.AttentionScore,
            'PTrue': estimators.PTrue,
            'FisherRao': estimators.FisherRao,
            'SelfCertainty': estimators.SelfCertainty,
        }

        methods = [
            method_map[method_name]() for method_name in self.config.uncertainty_methods
        ]

        return methods

    def setup_extractor(self):
        """Setup the model wrapper for uncertainty estimation"""
        super().setup_extractor()

        if isinstance(self._extractor, OpenAIModelAdapter):
            self.model_wrapper = BlackboxModel.from_openai(
                openai_api_key=getattr(self._extractor.config, 'openai_api_key', None)
                or getattr(self._extractor.config, 'api_key', None),
                model_path=self._extractor.config.model_path,
                supports_logprobs=self.config.supports_logprobs,
                base_url=self._extractor.config.base_url,
            )
            self.model_type = 'Blackbox'
        elif isinstance(self._extractor, HfModelAdapter):
            self.model_wrapper = WhiteboxModel(
                self._extractor.model,
                self._extractor.tokenizer,
                **self.config.model_kwargs,
            )
            self.model_type = 'Whitebox'
        elif isinstance(self._extractor, VllmModelAdapter):
            self.model_wrapper = WhiteboxModelvLLM(
                self._extractor.model,
                **self.config.model_kwargs,
            )
            self.model_type = 'Whitebox'
        else:
            raise NotImplementedError

    def __call__(
        self, samples: List[List[Dict]]
    ) -> Tuple[List[torch.Tensor], List[torch.Tensor]]:
        assert self._extractor is not None, 'No feature extractor found.'
        samples_to_process, sample_indices, cached_results = self.check_features(
            samples
        )
        features = self.extract_features(
            samples, samples_to_process, sample_indices, cached_results
        )

        padded_features, masks = self.postprocess(features)
        self._set_last_debug(features=padded_features, masks=masks)
        return [padded_features], [masks]

    def postprocess(self, features) -> Tuple[torch.Tensor, torch.Tensor]:
        features = torch.stack(features)
        masks = (features.sum(dim=-1) != 0).long()  # (batch_size, num_layers, seq_len)

        return features, masks

    def check_features(
        self, samples: List[List[Dict]]
    ) -> Tuple[
        List[List[Dict]], List[int], List[Tuple[int, List[Tuple[torch.Tensor]]]]
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
                    features, _ = cached_data
                    # Check whether all locations are cached
                    cached_results.append((i, features))
                else:
                    samples_to_process.append(sample)
                    sample_indices.append(i)
        else:
            samples_to_process = samples
            sample_indices = list(range(len(samples)))

        return samples_to_process, sample_indices, cached_results

    def extract_features(
        self,
        samples: List[List[Dict]],
        samples_to_process,
        sample_indices,
        cached_results,
    ) -> List[Tuple[torch.Tensor]]:
        """Get features with caching support."""

        new_features = []
        if samples_to_process:
            model_states = self.generate_features(samples_to_process)
            new_features = model_states['features']

            # Cache the new features individually
            if self.use_cache and self.cache_saver:
                for sample, features in zip(
                    samples_to_process,
                    new_features,
                ):
                    self.cache_saver.save_sample_features(
                        sample, features, self.layers, None, self._feature_type
                    )

        # Combine cached and new results in the correct order
        all_features = [None] * len(samples)

        for idx, features in cached_results:
            all_features[idx] = features

        for idx, features in zip(sample_indices, new_features):
            all_features[idx] = features

        if len(cached_results) > 0 or len(new_features) > 0:
            lg.debug(
                f'Loaded {len(cached_results)} from cache, computed {len(new_features)} new features'
            )

        return all_features

    def generate_features(self, samples: List[List[Dict]]) -> Dict[str, Any]:
        user_inputs, assistant_outputs = zip(
            *[(sample[0]['content'], sample[1]['content']) for sample in samples]
        )
        batch_size = getattr(self.config, 'feature_extraction_batch_size', 1)
        uncertainty, generation_texts, _ = estimate_uncertainty(  # keep scored text for UI.
            self.model_wrapper,
            self.model_type,
            self.uncertainty_methods,
            list(user_inputs),
            list(assistant_outputs),
            batch_size=batch_size,
            output_attentions=_needs_attention(self.config),
            top_logprobs=getattr(self.config, 'top_logprobs', 5),
            max_new_tokens=getattr(self.config, 'max_new_tokens', 256),
        )
        self.last_generated_text = generation_texts[0] if generation_texts is not None and len(generation_texts) else None  # current UI scores one sample.
        self.last_method_scores = {str(method): float(np.asarray(scores[0], dtype=float).mean()) for method, scores in zip(self.uncertainty_methods, uncertainty) if scores is not None and len(scores)} if uncertainty else None  # expose per-method means without changing outputs.

        sequence_features = torch.tensor(
            np.array(uncertainty).astype(float),
            dtype=torch.float32,
        ).T[:, None, None, :]

        return {
            'features': sequence_features,
            'locations': None,
        }

    def locate_features(self):
        return super().locate_features()
