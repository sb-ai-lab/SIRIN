import gc
from typing import Any, Dict, List, Optional, Tuple, Union

import torch
from loguru import logger as lg

from sirin.models.inference import VLLMConfig
from sirin.inference.adapters import ModelAdapterBase
from sirin.inference.batch_processing import batch_processor
from sirin.inference.model_manager import manage_active_model
from sirin.utils.config_manager import validate_hydra_config

try:
    from vllm import LLM, SamplingParams
    from vllm.distributed.parallel_state import destroy_model_parallel

    VLLM_AVAILABLE = True
except ImportError as e:
    LLM, SamplingParams = None, None
    destroy_model_parallel = None
    VLLM_AVAILABLE = False
    lg.warning(f"VLLM not available: {e}")


class VllmModelAdapter(ModelAdapterBase):
    """VLLM model implementation for high-performance inference."""

    @validate_hydra_config
    def __init__(
        self,
        config: Optional[VLLMConfig] = None,
        model: Optional[LLM] = None,
        tokenizer: Any = None,
    ):
        if not VLLM_AVAILABLE:
            raise ImportError(
                'VLLM is not available. Please install vllm to use VllmModel.'
            )
        super().__init__(config, model, tokenizer)

    def load(self, model: Optional[LLM] = None, tokenizer: Any = None):
        if self._is_loaded:
            lg.warning("Model already loaded")
            return

        if model is not None:
            lg.info(f"Using of preloaded VLLM model.")
            self.model = model
            self.config = None
        else:
            model_kwargs = {
                'model': self.config.model_path,
                'enforce_eager': getattr(self.config, 'enforce_eager', True),
                'max_model_len': getattr(self.config, 'max_length', 10240),
                'gpu_memory_utilization': getattr(self.config, 'gpu_memory_utilization', 0.98),
            }

            if hasattr(self.config, 'model_kwargs'):
                model_kwargs.update(self.config.model_kwargs)

            self.model = LLM(**model_kwargs)
            lg.info(f"Loaded VLLM model: {self.config.model_path}")

        self._is_loaded = True
        self._model_name = self.config.model_path

    @manage_active_model
    @batch_processor(batch_size=None, flatten_results=True, log_progress=True)
    def sample(
        self,
        inputs: Union[List[str], List[List[Dict]]],
        max_tokens: int = 100,
        temperature: float = 1.0,
        top_p: float = 1.0,
        top_k: int = -1,
        frequency_penalty: float = 0.0,
        presence_penalty: float = 0.0,
        stop_sequences: Optional[List[str]] = None,
        return_logprobs: bool = False,
        top_logprobs: int = 10,
        num_return_sequences: int = 1,
        **kwargs: Any,
    ) -> Union[List[str], Tuple[List[str], List[List[List[Tuple[str, float]]]]]]:
        """Generate text using VLLM with sampling parameters."""
        if not self._is_loaded:
            self.load()

        sampling_kwargs = {
            'max_tokens': max_tokens,
            'temperature': temperature,
            'top_p': top_p,
            'frequency_penalty': frequency_penalty,
            'presence_penalty': presence_penalty,
            'n': num_return_sequences,
        }

        if top_k > 0:
            sampling_kwargs['top_k'] = top_k
        if stop_sequences:
            sampling_kwargs['stop'] = stop_sequences
        if 'random_seed' in kwargs:
            sampling_kwargs['seed'] = kwargs.pop('random_seed')
        
        if return_logprobs:
            sampling_kwargs['logprobs'] = top_logprobs
        sampling_kwargs.update(kwargs)
        
        sampling_params = SamplingParams(**sampling_kwargs)

        outputs = self.model.generate(inputs, sampling_params=sampling_params)

        if return_logprobs:
            texts = [[sample.text for sample in samples.outputs] for samples in outputs]
            logprobs = [
                [
                    # [[(val.decoded_token, val.logprob) for val in token.values()] for token in sample.logprobs]
                    [[val.logprob for val in token.values()] for token in sample.logprobs]
                    for sample in samples.outputs
                ]
                for samples in outputs
            ]
            return texts, logprobs
        else:
            generated_texts = [output.outputs[0].text.strip() for output in outputs]
            return generated_texts

    def unload(self):
        """Unload VLLM model and free GPU memory."""
        if self.model is not None:
            self._release_gpu_memory()

        super().unload()
        lg.info("Unloaded VLLM model and freed memory")

    def _release_gpu_memory(self):
        """Release GPU memory used by VLLM."""
        lg.info("Releasing GPU memory...")
        if destroy_model_parallel:
            destroy_model_parallel()

        if hasattr(self.model, 'llm_engine') and hasattr(
            self.model.llm_engine, 'model_executor'
        ):
            if hasattr(self.model.llm_engine.model_executor, 'driver_worker'):
                del self.model.llm_engine.model_executor.driver_worker

        gc.collect()
        if torch.cuda.is_available():
            torch.cuda.empty_cache()

        # Clean up distributed processes if they exist
        if torch.distributed.is_initialized():
            torch.distributed.destroy_process_group()