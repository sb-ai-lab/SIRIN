from importlib import import_module

from .detectors import (
    ClaimLinearProbingDetector,
    ClaimCatboostProbingDetector,
    SequenceLinearProbingDetector,
    SequenceCatboostProbingDetector,
    TokenLinearProbingDetector,
    TokenCatboostProbingDetector,
)
from .pipeline import ProbingPipeline

_TABPFN_EXPORTS = {
    'ClaimTabPFNProbingDetector': '.detectors.claim.tabpfn',
    'SequenceTabPFNProbingDetector': '.detectors.sequence.tabpfn',
    'TokenTabPFNProbingDetector': '.detectors.token.tabpfn',
}


def __getattr__(name):
    module_name = _TABPFN_EXPORTS.get(name)
    if module_name is None:
        raise AttributeError(name)
    try:
        value = getattr(import_module(module_name, __name__), name)
    except (ImportError, ModuleNotFoundError) as error:
        raise RuntimeError(
            f'{name} requires a compatible TabPFN installation; ordinary probing '
            'detectors remain available without it.'
        ) from error
    globals()[name] = value
    return value
