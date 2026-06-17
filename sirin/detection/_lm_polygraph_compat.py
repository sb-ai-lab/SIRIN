import sys
import types

from transformers import AutoProcessor, GenerationConfig
import transformers
transformers = sys.modules['transformers']

from transformers.generation.utils import (
    GenerateBeamDecoderOnlyOutput,
    GenerateDecoderOnlyOutput,
)

gen_utils = sys.modules['transformers.generation.utils']

# ensemble_beam.py: from transformers.generation.beam_search import BeamScorer
# Module was removed in transformers 5.x
if 'transformers.generation.beam_search' not in sys.modules:
    try:
        from transformers.utils.dummy_pt_objects import BeamScorer as _BeamScorer
    except ImportError:
        _BeamScorer = None

    if _BeamScorer is not None:
        beam_search_mod = types.ModuleType('transformers.generation.beam_search')
        beam_search_mod.BeamScorer = _BeamScorer
        sys.modules['transformers.generation.beam_search'] = beam_search_mod

# ensemble_beam.py: BeamSearchOutput, BeamSearchDecoderOnlyOutput
if not hasattr(gen_utils, 'BeamSearchOutput'):
    gen_utils.BeamSearchOutput = GenerateBeamDecoderOnlyOutput
if not hasattr(gen_utils, 'BeamSearchDecoderOnlyOutput'):
    gen_utils.BeamSearchDecoderOnlyOutput = GenerateBeamDecoderOnlyOutput

# ensemble_greedy.py: GreedySearchOutput, GreedySearchDecoderOnlyOutput
if not hasattr(gen_utils, 'GreedySearchOutput'):
    gen_utils.GreedySearchOutput = GenerateDecoderOnlyOutput
if not hasattr(gen_utils, 'GreedySearchDecoderOnlyOutput'):
    gen_utils.GreedySearchDecoderOnlyOutput = GenerateDecoderOnlyOutput

# ensemble_sample.py: SampleOutput, SampleDecoderOnlyOutput
if not hasattr(gen_utils, 'SampleOutput'):
    gen_utils.SampleOutput = GenerateDecoderOnlyOutput
if not hasattr(gen_utils, 'SampleDecoderOnlyOutput'):
    gen_utils.SampleDecoderOnlyOutput = GenerateDecoderOnlyOutput

# visual_whitebox_model.py: AutoModelForVision2Seq
if not hasattr(transformers, 'AutoModelForVision2Seq'):
    transformers.AutoModelForVision2Seq = transformers.AutoModelForImageTextToText


# greedy_probs.py: out.scores are raw logits, not log-probabilities.
# GreedyProbsCalculator treats them as log-probs, so Perplexity/MaxSequenceProb
# get garbage values (and inf from -inf logits in MoE models).
# VisualWhiteboxModel has a _ScoresProcessor that applies log_softmax, but
# WhiteboxModelBasic does not.
import torch as _torch
from lm_polygraph.model_adapters.whitebox_model_basic import WhiteboxModelBasic

_original_wb_generate = WhiteboxModelBasic.generate


def _patched_wb_generate(self, *args, **kwargs):
    out = _original_wb_generate(self, *args, **kwargs)
    if hasattr(out, 'scores') and out.scores is not None:
        out.scores = tuple(s.log_softmax(dim=-1) for s in out.scores)
    return out


WhiteboxModelBasic.generate = _patched_wb_generate


import openai as _openai
from lm_polygraph.utils.model import BlackboxModel

_original_blackbox_init = BlackboxModel.__init__


def _patched_blackbox_init(self, openai_api_key=None, model_path=None,
                           hf_api_token=None, generation_parameters=None,
                           supports_logprobs=False, base_url=None):
    if generation_parameters is None:
        from lm_polygraph.utils.generation_parameters import GenerationParameters
        generation_parameters = GenerationParameters()
    _original_blackbox_init(
        self,
        openai_api_key=openai_api_key,
        model_path=model_path,
        hf_api_token=hf_api_token,
        generation_parameters=generation_parameters,
        supports_logprobs=supports_logprobs,
    )
    self.base_url = base_url
    if openai_api_key is not None and base_url is not None:
        self.openai_api = _openai.OpenAI(api_key=openai_api_key, base_url=base_url)


BlackboxModel.__init__ = _patched_blackbox_init


@staticmethod
def _patched_from_openai(openai_api_key=None, model_path=None,
                         supports_logprobs=False, **kwargs):
    from lm_polygraph.utils.generation_parameters import GenerationParameters
    generation_parameters = kwargs.pop('generation_parameters', GenerationParameters())
    base_url = kwargs.pop('base_url', None)
    return BlackboxModel(
        openai_api_key=openai_api_key,
        model_path=model_path,
        supports_logprobs=supports_logprobs,
        generation_parameters=generation_parameters,
        base_url=base_url,
    )


BlackboxModel.from_openai = _patched_from_openai


def load_stat_calculator(cfg, env):
    from lm_polygraph.stat_calculators.greedy_probs_blackbox import BlackboxGreedyTextsCalculator
    top_logprobs = cfg.get('top_logprobs', 5)
    return BlackboxGreedyTextsCalculator(top_logprobs=top_logprobs)



from lm_polygraph.defaults import register_default_stat_calculators as _reg_module

_original_register = _reg_module.register_default_stat_calculators


def _patched_register(model_type, language='en', hf_cache=None,
                      blackbox_supports_logprobs=False, top_logprobs=5,
                      output_attentions=True, output_hidden_states=True,
                      deberta_batch_size=10):
    result = _original_register(
        model_type=model_type,
        language=language,
        hf_cache=hf_cache,
        blackbox_supports_logprobs=blackbox_supports_logprobs,
        output_attentions=output_attentions,
        output_hidden_states=output_hidden_states,
        deberta_batch_size=deberta_batch_size,
    )

    for container in result:
        if container.name == 'BlackboxGreedyTextsCalculator':
            from omegaconf import OmegaConf
            cfg = OmegaConf.to_container(container.cfg, resolve=True)
            cfg['top_logprobs'] = top_logprobs
            container.cfg = OmegaConf.create(cfg)
            container.builder = 'sirin.detection._lm_polygraph_compat'
    return result


_reg_module.register_default_stat_calculators = _patched_register


# greedy_alternatives_nli.py: deberta.deberta_tokenizer.batch_encode_plus(...)
# DebertaTokenizer removed batch_encode_plus in transformers 5.x.
# Patch: add it back as a wrapper around __call__ (same semantics).
from transformers import DebertaTokenizer as _DebertaTokenizer

if not hasattr(_DebertaTokenizer, 'batch_encode_plus'):
    def _batch_encode_plus(self, *args, **kwargs):
        return self(*args, **kwargs)
    _DebertaTokenizer.batch_encode_plus = _batch_encode_plus
