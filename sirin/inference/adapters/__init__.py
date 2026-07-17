"""Lazy adapter exports.

Importing a concrete adapter pulls a heavy backend (``VllmModelAdapter`` -> ``import vllm`` is a
minute-scale cold start; the HF path pulls torch/transformers). Load each submodule on first attribute
access (PEP 562) so ``from sirin.inference.adapters import HfModelAdapter`` keeps working while the bare
package import stays cheap.
"""

from importlib import import_module
from typing import TYPE_CHECKING, Any

if TYPE_CHECKING:
    from .base import ModelAdapterBase
    from .hf_adapter import HfModelAdapter
    from .openai_adapter import OpenAIModelAdapter
    from .vllm_adapter import VllmModelAdapter

_EXPORTS = {
    'ModelAdapterBase': 'base',
    'HfModelAdapter': 'hf_adapter',
    'VllmModelAdapter': 'vllm_adapter',
    'OpenAIModelAdapter': 'openai_adapter',
}

__all__ = [
    'ModelAdapterBase',
    'HfModelAdapter',
    'VllmModelAdapter',
    'OpenAIModelAdapter',
]


def __getattr__(name: str) -> Any:
    module_name = _EXPORTS.get(name)
    if module_name is None:
        raise AttributeError(f'module {__name__!r} has no attribute {name!r}')
    value = getattr(import_module(f'.{module_name}', __name__), name)
    globals()[name] = value
    return value
