from importlib import import_module

from .claim import (
    ClaimLinearProbingDetector,
    ClaimCatboostProbingDetector,
)
from .sequence import (
    SequenceLinearProbingDetector,
    SequenceCatboostProbingDetector,
)
from .token import (
    TokenLinearProbingDetector,
    TokenCatboostProbingDetector,
)

_TABPFN_EXPORTS = {
    'ClaimTabPFNProbingDetector': '.claim.tabpfn',
    'SequenceTabPFNProbingDetector': '.sequence.tabpfn',
    'TokenTabPFNProbingDetector': '.token.tabpfn',
}


def __getattr__(name):
    module_name = _TABPFN_EXPORTS.get(name)
    if module_name is None:
        raise AttributeError(name)
    try:
        value = getattr(import_module(module_name, __name__), name)
    except (ImportError, ModuleNotFoundError) as error:
        raise RuntimeError(f'{name} requires a compatible TabPFN installation.') from error
    globals()[name] = value
    return value
