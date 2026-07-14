"""Lazy inference exports.

Eagerly importing the adapters or ``ModelManager`` pulls torch/vllm/transformers (minute-scale cold
start). Resolve each name on first attribute access (PEP 562) so ``sirin.inference`` submodules can be
imported without loading any ML backend.
"""

from importlib import import_module
from typing import TYPE_CHECKING, Any

if TYPE_CHECKING:
    from .adapters import HfModelAdapter, ModelAdapterBase, OpenAIModelAdapter, VllmModelAdapter
    from .model_manager import ModelManager
    from .token_locators import HfTokenLocator

_EXPORTS = {
    'ModelAdapterBase': 'adapters',
    'VllmModelAdapter': 'adapters',
    'HfModelAdapter': 'adapters',
    'OpenAIModelAdapter': 'adapters',
    'ModelManager': 'model_manager',
    'HfTokenLocator': 'token_locators',
}

__all__ = [
    'ModelAdapterBase',
    'VllmModelAdapter',
    'HfModelAdapter',
    'OpenAIModelAdapter',
    'ModelManager',
    'HfTokenLocator',
]


def __getattr__(name: str) -> Any:
    module_name = _EXPORTS.get(name)
    if module_name is None:
        raise AttributeError(f'module {__name__!r} has no attribute {name!r}')
    value = getattr(import_module(f'.{module_name}', __name__), name)
    globals()[name] = value
    return value
