from loguru import logger as lg

from .attention import AttentionsProcessor
from .base import FeatureProcessorBase
from .ensemble import EnsembleProcessor
from .hidden import HiddensProcessor
from .logit import LogitsProcessor
from .lookback import LookbacksProcessor
from .saver import LayerFeatureCacheSaver
from .sublayer import SublayersProcessor

# Optional processor with extra dependencies
try:
    from .mtopdiv import MTopDivFeatureProcessor
except Exception as e:
    MTopDivFeatureProcessor = None
    lg.warning(f"MTopDivFeatureProcessor unavailable: {e}")

from .uncertainty import (
    SequenceUncertaintyFeatureProcessor,
    TokenUncertaintyFeatureProcessor,
)
