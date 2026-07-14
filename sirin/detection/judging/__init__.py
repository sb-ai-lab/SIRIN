def _ensure_transformers_hybrid_cache(transformers_module=None):
    previous_module = None
    if transformers_module is None:
        import sys

        previous_module = sys.modules.get('transformers')
        from transformers import AutoProcessor  # noqa: F401
        transformers_module = sys.modules['transformers']

    if hasattr(transformers_module, 'HybridCache'):
        return

    dynamic_cache = getattr(transformers_module, 'DynamicCache', None)
    if dynamic_cache is None:
        try:
            from transformers import DynamicCache as dynamic_cache
        except ImportError:
            return
    transformers_module.HybridCache = dynamic_cache
    if previous_module is not None and previous_module is not transformers_module:
        previous_module.HybridCache = dynamic_cache


_ensure_transformers_hybrid_cache()

from .judges import (
    SequenceEncoderJudge,
    SequenceDecoderJudge,
    SequenceOpenAIJudge,
    TokenDecoderJudge,
    TokenEncoderJudge,
    TokenOpenAIJudge,
    ClaimDecoderJudge,
    ClaimEncoderJudge,
    ClaimOpenAIJudge,
    HfJudgeBase,
    JudgeAnnotationError,
    OpenAIJudgeBase,
)
from .pipeline import JudgePipeline
