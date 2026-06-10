import json
from itertools import product
from pathlib import Path
from typing import Any, Dict, List, Literal, Optional, Tuple, Union

import mtd.barcodes as mtd
import numpy as np
try:
    import ripserplusplus as rpp_py
    _RIPSERPP_IMPORT_ERROR = None
except Exception as e:
    rpp_py = None
    _RIPSERPP_IMPORT_ERROR = e
import torch
from joblib import Parallel, delayed
from loguru import logger as lg
from tqdm import trange
from sirin.utils.config_manager import validate_hydra_config

from sirin.models.detection import MTopDivProcessorConfig
from sirin.detection.processors.saver import LayerFeatureCacheSaver
from sirin.detection.processors.base import FeatureProcessorBase
from sirin.inference.adapters.base import ModelAdapterBase


class MTopDivFeatureProcessor(FeatureProcessorBase):
    _feature_type: str = 'mtopdiv'

    @validate_hydra_config
    def __init__(
        self,
        config: MTopDivProcessorConfig,
        extractor: ModelAdapterBase,
        cache_dir: Optional[str] = None,
    ):
        if rpp_py is None:
            raise ImportError(
                "ripserplusplus is required for MTopDivFeatureProcessor. "
                "On macOS this dependency is not available; run on Linux with CUDA, "
                "or remove MTopDiv from your pipeline."
            ) from _RIPSERPP_IMPORT_ERROR
        super().__init__(config=config, extractor=extractor, cache_dir=cache_dir)

    def __call__(
        self, 
        samples: List[List[Dict]]
    ) -> Tuple[
        List[Dict[Tuple[int, int], List[float]]],  # MTopDiv values for each head
        List[Dict[Tuple[int, int], List[Any]]]     # Barcodes for each head
    ]:
        """Process samples to extract MTopDiv features."""
        assert self._extractor is not None, 'No feature extractor found.'
        
        samples_to_process, sample_indices, cached_results = self.check_features(
            samples
        )
        
        features = self.extract_features(
            samples, samples_to_process, sample_indices, cached_results
        )
        
        features = self.postprocess(features)
        
        return [features], [None] # not returning labels because no token level detection

    def check_features(
        self, 
        samples: List[List[Dict]]
    ) -> Tuple[
        List[List[Dict]], 
        List[int], 
        List[Tuple[int, Dict[str, Any]]]
    ]:
        """Check cache for existing MTopDiv features."""
        cached_results = []
        samples_to_process = []
        sample_indices = []

        if self.use_cache and self.cache_saver:
            for i, sample in enumerate(samples):
                # Try to load cached MTopDiv features
                cached_data = self.cache_saver.load_all_layers_for_sample(
                    sample,
                    self.config.heads_to_analyze or [],
                    self._feature_type,
                )
                if cached_data[1] is not None:
                    mtopdivs, barcodes = cached_data
                    cached_results.append((i, {
                        'mtopdivs': mtopdivs,
                        'barcodes': barcodes
                    }))
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
        samples_to_process, 
        sample_indices, 
        cached_results
    ) -> List[Dict[str, Any]]:
        """Extract MTopDiv features with caching support."""
        
        # Process uncached samples
        new_features = []
        if samples_to_process:
            # Generate attention weights and locations
            model_states = self.generate_features(samples_to_process)
            attentions = model_states['attentions']
            locations = model_states['locations']
            
            # Calculate MTopDiv features
            new_features_batch = self.locate_features(attentions, locations)
            
            # Cache the new features individually
            if self.use_cache and self.cache_saver:
                for sample, features in zip(
                    samples_to_process,
                    new_features_batch,
                ):
                    self.cache_saver.save_sample_features(
                        sample, 
                        (features['mtopdivs'], features['barcodes']), 
                        self.config.heads_to_analyze or [], 
                        None, 
                        self._feature_type
                    )

            new_features.extend(new_features_batch)

        # Combine cached and new results in the correct order
        all_features = [None] * len(samples)

        for idx, features in cached_results:
            all_features[idx] = features

        for idx, features in zip(sample_indices, new_features):
            all_features[idx] = features

        if len(cached_results) > 0 or len(new_features) > 0:
            lg.debug(
                f"Loaded {len(cached_results)} from cache, computed {len(new_features)} new MTopDiv features"
            )

        return all_features

    def generate_features(self, samples: List[List[Dict]]) -> Dict[str, Any]:
        """Generate attention weights and locations for MTopDiv calculation."""
        lg.info(f"Generating attention weights for {len(samples)} samples...")
        
        model_states = self._extractor.generate_hiddens(
            samples,
            return_hiddens=False,
            return_attention=True,
            layers=self.config.layers if hasattr(self.config, 'layers') else None,
            padding=self.config.padding,
            truncation=self.config.truncation,
            max_length=self.config.max_length,
            token_locator=self._token_locator,
        )
        
        return {
            'attentions': model_states.attentions,
            'locations': model_states.locations,
        }

    def locate_features(
        self,
        attentions: List[Tuple[torch.Tensor]],  # List of (num_layers, num_heads, seq_len, seq_len)
        locations: List[Optional[Dict[str, int]]],
    ) -> List[Dict[str, Any]]:
        """Calculate MTopDiv features from attention weights and locations."""
        lg.info("Calculating MTopDiv features...")
        
        features_list = []
        
        # Determine heads to analyze
        if self.config.heads_to_analyze is None:
            if attentions and len(attentions) > 0:
                first_sample = attentions[0]
                if first_sample and len(first_sample) > 0:
                    num_layers = len(first_sample)
                    num_heads = first_sample[0].shape[0]  # num_heads from attention shape
                    heads_to_analyze = list(product(range(num_layers), range(num_heads)))
                else:
                    heads_to_analyze = []
            else:
                heads_to_analyze = []
        else:
            heads_to_analyze = self.config.heads_to_analyze

        # Group heads by layer for efficient processing
        layer_heads_map = {}
        for layer, head in heads_to_analyze:
            if layer not in layer_heads_map:
                layer_heads_map[layer] = []
            layer_heads_map[layer].append(head)

        for i in trange(len(attentions), desc='MTopDiv processing'):
            attention_maps = attentions[i]
            location = locations[i] if i < len(locations) else None
            
            if location and self.config.separate_token in location:
                response_len = location[self.config.separate_token]
            else:
                # Fallback: use the last position as response start
                response_len = attention_maps[0].shape[-1] // 2 if attention_maps else 0

            mtopdiv_values, barcode_values = self._calculate_sample_mtopdiv(
                attention_maps=attention_maps,
                response_len=response_len,
                layer_heads_map=layer_heads_map,
                zero_out=self.config.zero_out,
                n_jobs=self.config.n_jobs,
                critical_size=self.config.critical_size,
            )
            
            features_list.append({
                'mtopdivs': mtopdiv_values,
                'barcodes': barcode_values,
                'heads_to_analyze': heads_to_analyze
            })

        lg.info("MTopDiv features calculated.")
        return features_list

    def _calculate_sample_mtopdiv(
        self,
        attention_maps: Tuple[torch.Tensor],
        response_len: int,
        layer_heads_map: Dict[int, List[int]],
        zero_out: str = 'prompt',
        n_jobs: Optional[int] = None,
        critical_size: Optional[int] = None,
    ) -> Tuple[Dict[Tuple[int, int], float], Dict[Tuple[int, int], Any]]:
        """Calculate MTopDiv values for all analysis heads for the given sample."""
        if not attention_maps:
            return {}, {}
            
        sample_size = attention_maps[0].shape[-1]
        critical_size = critical_size or 756
        n_jobs = n_jobs if n_jobs and sample_size <= critical_size else 1

        mtopdiv_values = {}
        barcode_values = {}

        for layer, heads in layer_heads_map.items():
            torch.cuda.empty_cache()

            # Select attention maps for specific heads in this layer
            attn_mxs_tmp = torch.index_select(attention_maps[layer], 0, torch.tensor(heads))
            # Transform attention scores to distances
            distance_mxs = transform_attention_scores_to_distances(
                attn_mxs_tmp.to(torch.float32), zero_out, response_len
            )
            
            # Calculate MTopDiv for each head
            barcodes, mtopdiv_parallel = zip(
                *Parallel(n_jobs=n_jobs)(
                    delayed(attn_mx_to_mtopdiv)(distance_mx) for distance_mx in distance_mxs
                )
            )

            for i, head in enumerate(heads):
                mtopdiv_values[(layer, head)] = float(mtopdiv_parallel[i])
                barcode_values[(layer, head)] = barcodes[i]

        return mtopdiv_values, barcode_values

    def _get_side_indices(self, positions: List[int], seq_len: int) -> List[int]:
        """Get indices based on the specified side relative to the positions."""
        if not positions:
            return []

        positions = sorted(positions)
        
        # For MTopDiv, we typically don't need side separation like in other processors
        # But we keep this method for consistency
        return list(range(seq_len))  # Return all indices for MTopDiv calculation

    def postprocess(self, features) -> Tuple[Any, Any]:
        """Process MTopDiv features after extraction."""
        # MTopDiv features are already in the right format
        # Return as-is or apply additional processing if needed
        features = list(features[0]['mtopdivs'].values())

        features = torch.tensor(features)[None, None, None, :]
        masks = (
            features.sum(dim=-1) != 0
        ).long()  # (batch_size, num_layers, seq_len)


        return features, masks


def transform_attention_scores_to_distances(
    attn_mxs: torch.Tensor,
    zero_out: Literal['prompt', 'response'],
    len_answer: int,
    lower_bound: float = 0.0,
) -> torch.Tensor:
    """Transform attention matrix to the matrix of distances between tokens.

    Parameters
    ----------
    attn_mxs : torch.Tensor
        Attention matrixes of one sample (n_heads x n_tokens x n_tokens).
    zero_out : Literal["prompt", "response"]
        Determines whether to zero out distances between prompt tokens or response tokens.
    len_answer : int
        Length of the response.

    Returns
    -------
    torch.Tensor
        Distance matrix.

    """
    n_tokens = attn_mxs.shape[1]
    distance_mx = 1 - torch.clamp(
        attn_mxs, min=lower_bound,
    )  # torch.where(attn_mx > lower_bound, attn_mx, 0.0)
    zero_diag = torch.ones(n_tokens, n_tokens) - torch.eye(n_tokens)
    distance_mx *= zero_diag.to(attn_mxs.device).expand_as(
        distance_mx
    )  # torch.diag(torch.diag(distance_mx))
    distance_mx = torch.minimum(distance_mx.transpose(1, 2), distance_mx)

    if zero_out == 'prompt':
        len_prompt = n_tokens - len_answer
        distance_mx[:, :len_prompt, :len_prompt] = 0
    elif zero_out == 'response':
        distance_mx[:, -len_answer:, -len_answer:] = 0
    else:
        raise ValueError(f"Unsupported zero_out parameter: {zero_out}")

    return distance_mx.cpu().numpy()


def attn_mx_to_mtopdiv(distance_mx: np.ndarray) -> tuple[np.ndarray, float]:
    """Calculate barcodes and MTopDiv value for the given attention matrix."""
    if rpp_py is None:
        raise ImportError(
            "ripserplusplus is required for MTopDivFeatureProcessor, but it is not installed."
        ) from _RIPSERPP_IMPORT_ERROR
    barcodes = rpp_py.run('--format distance --dim 1', distance_mx)
    barcodes = mtd.barc2array(barcodes)
    mtopdiv = mtd.get_score(barcodes, 0, 'sum_length')
    return barcodes, mtopdiv
