from dataclasses import dataclass, field
from typing import Any, Dict, Optional, List, Union

from sirin.definitions import ModelType


@dataclass
class TokenLocatorConfig:
    """Configuration for token locators."""

    locate_answer_end: bool = False
    locate_answer_start: bool = True
    locate_answer_middle: bool = False
    locate_eos: bool = False
    locate_substring: bool = False
    n_to_answer_start: int = 0
    n_to_answer_end: int = 0
    substrings: Optional[List[str]] = None
    case_sensitive: bool = True
    n_to_answer_end_overlap_question: bool = True
    first_substring: bool = True


@dataclass
class CleanerConfig:
    name: str
    type: str
    params: Optional[Dict[str, Any]] = None


@dataclass
class ModelAdapterBaseConfig:
    model_path: str
    device: Optional[str] = 'cuda'
    max_length: int = 1024
    batch_size: Optional[int] = 4  # Maximum batch size for processing (None = no limit)


@dataclass
class HFConfig(ModelAdapterBaseConfig):
    """Configuration for HuggingFace inference engine."""

    _target_: str = 'sirin.inference.adapters.HfModelAdapter'
    model_type: ModelType = field(default=ModelType.CAUSAL)
    model_dtype: Optional[str] = 'bf16'
    tokenizer_path: Optional[str] = None
    revision: Optional[str] = None
    model_kwargs: Dict[str, Any] = field(default_factory=dict)
    num_labels: int = 2
    truncation: bool = False
    padding: Union[bool, str] = 'longest'
    padding_side: str = 'right'
    use_chat_template: bool = True
    # Multi-GPU support via Accelerate
    device_map: Optional[Union[str, Dict[str, Any]]] = (
        None  # 'auto', 'balanced', 'balanced_low_0', or custom dict
    )
    max_memory: Optional[Dict[Union[int, str], Union[int, str]]] = (
        None  # e.g., {0: "20GiB", 1: "20GiB"}
    )
    offload_folder: Optional[str] = None  # For CPU offloading
    low_cpu_mem_usage: bool = True  # Recommended for large models
    attn_implementation: str = 'eager'  # 'eager', 'sdpa', 'flash_attention_2'


@dataclass
class VLLMConfig(ModelAdapterBaseConfig):
    """Configuration for vLLM inference engine."""

    _target_: str = 'sirin.inference.adapters.VllmModelAdapter'
    enforce_eager: bool = True
    gpu_memory_utilization: float = 0.8
    model_kwargs: Dict[str, Any] = field(default_factory=dict)


@dataclass
class ModelManagerConfig:
    """Configuration for model manager."""

    max_active_models: int = 1
    auto_unload: bool = True
    memory_threshold: float = 0.8
    retry_on_failure: bool = True
    max_retries: int = 3
    retry_delay: float = 1.0


@dataclass
class OpenAIConfig(ModelAdapterBaseConfig):
    """Configuration for OpenAI model adapter."""

    api_key: Optional[str] = None
    model_path: str = 'gpt-3.5-turbo'
    base_url: Optional[str] = 'https://openrouter.ai/api/v1'
    timeout: int = 30
    max_retries: int = 3
    proxy_url: Optional[str] = None
