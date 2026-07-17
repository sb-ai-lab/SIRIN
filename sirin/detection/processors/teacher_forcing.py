"""Teacher-forced replacement for lm-polygraph's ``GreedyProbsCalculator``.

``GreedyProbsCalculator`` makes the model *re-generate* an answer from the prompt
and scores that fresh generation. When the dataset already carries the response we
want to score (the one a labeller actually judged), regeneration is wrong twice
over: the uncertainty describes a different string than the label refers to, and
for inputs whose second turn is not an answer at all (e.g. query answerability,
where the dialogue is ``[user: context, assistant: question]``) the second turn is
silently dropped and never shown to the model.

This calculator instead runs a single forward pass over
``chat_template(user_turn) + assistant_turn`` and reads the model's distribution at
each position of the *given* assistant tokens. It emits exactly the statistics
``GreedyProbsCalculator`` emits, so RAUQ / MeanTokenEntropy / Focus and the
``EntropyCalculator`` consume it unchanged.

Position bookkeeping mirrors the greedy calculator: ``attention_all[i]`` is a
``(n_layers * n_heads, c, c)`` lower-triangular block covering only the *scored*
tokens, with row ``j`` holding token ``j``'s attention over tokens ``0..j-1``.
"""

from typing import Any, Dict, List, Optional, Tuple

import numpy as np
import torch
from lm_polygraph.stat_calculators.stat_calculator import StatCalculator
from lm_polygraph.utils.factory_stat_calculator import StatCalculatorContainer
from loguru import logger as lg
from omegaconf import OmegaConf

GREEDY_PROBS_CALCULATOR = 'GreedyProbsCalculator'


class TeacherForcedProbsCalculator(StatCalculator):
    """Scores the dataset-provided assistant turn instead of regenerating it."""

    @staticmethod
    def meta_info() -> Tuple[List[str], List[str]]:
        # Same stats as GreedyProbsCalculator so this is a drop-in substitution.
        # `target_texts` is not declared as a dependency: the UEManager seeds it
        # into batch_stats before any calculator runs, and declaring it would send
        # order_calculators looking for a producer that does not exist.
        # Declare exactly what __call__ returns. Do NOT list input_texts/embeddings:
        # they are not produced here, and declaring them makes order_calculators skip
        # scheduling a real producer -> a consuming estimator KeyErrors at run time.
        return [
            'input_tokens',
            'greedy_log_probs',
            'greedy_tokens',
            'greedy_tokens_alternatives',
            'greedy_texts',
            'greedy_log_likelihoods',
            'attention_all',
            'tokenizer',
        ], []

    def __init__(
        self,
        output_attentions: bool = True,
        n_alternatives: int = 10,
        max_response_tokens: Optional[int] = None,
        chat_template_kwargs: Optional[Dict[str, Any]] = None,
    ):
        super().__init__()
        self.output_attentions = output_attentions
        self.n_alternatives = n_alternatives
        self.max_response_tokens = max_response_tokens
        self.chat_template_kwargs = dict(chat_template_kwargs or {})

    def _prompt_ids(self, tokenizer, user_text: str) -> List[int]:
        """Tokenize the user turn through the chat template, ending at the point
        where the assistant's first token would be sampled."""
        if getattr(tokenizer, 'chat_template', None) is None:
            return tokenizer(user_text, add_special_tokens=True)['input_ids']
        chat = [{'role': 'user', 'content': user_text}]
        try:
            text = tokenizer.apply_chat_template(
                chat, add_generation_prompt=True, tokenize=False,
                **self.chat_template_kwargs,
            )
        except TypeError:  # template does not accept the extra kwargs (e.g. enable_thinking)
            text = tokenizer.apply_chat_template(
                chat, add_generation_prompt=True, tokenize=False
            )
        return tokenizer(text, add_special_tokens=False)['input_ids']

    def _response_ids(self, tokenizer, assistant_text: str) -> List[int]:
        ids = tokenizer(assistant_text, add_special_tokens=False)['input_ids']
        if self.max_response_tokens is not None:
            ids = ids[: self.max_response_tokens]
        if not ids:
            # An empty assistant turn has no tokens to score; fall back to a single
            # EOS so downstream estimators see a well-formed length-1 sequence.
            eos = tokenizer.eos_token_id
            ids = [eos if eos is not None else tokenizer.pad_token_id]
        return ids

    def _score_one(
        self, model, user_text: str, assistant_text: str
    ) -> Dict[str, Any]:
        tokenizer = model.tokenizer
        prompt_ids = self._prompt_ids(tokenizer, user_text)
        resp_ids = self._response_ids(tokenizer, assistant_text)

        input_ids = torch.tensor([prompt_ids + resp_ids], device=model.device())
        n_prompt, n_resp = len(prompt_ids), len(resp_ids)

        with torch.no_grad():
            out = model.model(
                input_ids=input_ids,
                attention_mask=torch.ones_like(input_ids),
                output_attentions=self.output_attentions,
                use_cache=False,
            )

        # Position n_prompt-1+j predicts response token j.
        logits = out.logits[0, n_prompt - 1 : n_prompt + n_resp - 1, :]
        log_probs = torch.log_softmax(logits.float(), dim=-1).cpu().numpy()
        ll = [float(log_probs[j, resp_ids[j]]) for j in range(n_resp)]

        alternatives = []
        k = min(self.n_alternatives, log_probs.shape[-1])
        for j in range(n_resp):
            row = log_probs[j]
            realized = int(resp_ids[j])
            best = {int(t) for t in np.argpartition(row, -k)[-k:]}
            best.add(realized)  # the teacher-forced token can fall outside the top-k
            alt = [(t, float(row[t])) for t in best]
            # Realized token first (GreedyProbsCalculator's contract), then by log-prob.
            alt.sort(key=lambda x: (x[0] == realized, x[1]), reverse=True)
            alternatives.append(alt)

        attention = None
        if self.output_attentions:
            attention = self._response_attention(out.attentions, n_prompt, n_resp)

        return dict(
            input_tokens=prompt_ids,
            greedy_log_probs=log_probs,
            greedy_tokens=list(resp_ids),
            greedy_tokens_alternatives=alternatives,
            greedy_texts=tokenizer.decode(resp_ids, skip_special_tokens=True),
            greedy_log_likelihoods=ll,
            attention_all=attention,
        )

    @staticmethod
    def _response_attention(attentions, n_prompt: int, n_resp: int) -> np.ndarray:
        """Stack per-layer attention into (n_layers * n_heads, n_resp, n_resp).

        Row ``j`` keeps only columns ``< j`` — attention of scored token ``j`` over
        the scored tokens that precede it. Attention paid to the prompt is dropped,
        matching what GreedyProbsCalculator retains for generated tokens.
        """
        sl = slice(n_prompt, n_prompt + n_resp)
        blocks = []
        for layer_attn in attentions:  # (batch, heads, seq, seq)
            block = layer_attn[0, :, sl, sl]
            if block.dtype == torch.bfloat16:
                block = block.to(torch.float16)
            blocks.append(block.cpu().numpy())
        attn = np.concatenate(blocks, axis=0)  # (layers*heads, n_resp, n_resp)
        return np.tril(attn, k=-1)

    def __call__(
        self,
        dependencies: Dict[str, np.ndarray],
        texts: List[str],
        model,
        max_new_tokens: int = 100,
    ) -> Dict[str, Any]:
        targets = dependencies.get('target_texts')
        if targets is None:
            raise ValueError(
                'TeacherForcedProbsCalculator needs the assistant turn in '
                '`target_texts`; got none. Pass it as the `y` of lm_polygraph Dataset.'
            )

        scored = [self._score_one(model, u, a) for u, a in zip(texts, targets)]
        return {
            'input_tokens': [s['input_tokens'] for s in scored],
            'greedy_log_probs': [s['greedy_log_probs'] for s in scored],
            'greedy_tokens': [s['greedy_tokens'] for s in scored],
            'greedy_tokens_alternatives': [s['greedy_tokens_alternatives'] for s in scored],
            'greedy_texts': [s['greedy_texts'] for s in scored],
            'greedy_log_likelihoods': [s['greedy_log_likelihoods'] for s in scored],
            'attention_all': [s['attention_all'] for s in scored] if self.output_attentions else [],
            'tokenizer': model.tokenizer,
        }


def load_stat_calculator(config, environment):
    """Builder hook used by lm_polygraph's FactoryStatCalculator."""
    return TeacherForcedProbsCalculator(
        output_attentions=config.get('output_attentions', True),
        n_alternatives=config.get('n_alternatives', 10),
        max_response_tokens=config.get('max_response_tokens', None),
        chat_template_kwargs=OmegaConf.to_container(
            config.get('chat_template_kwargs', OmegaConf.create({})), resolve=True
        ),
    )


def use_teacher_forcing(
    containers: List[StatCalculatorContainer],
    output_attentions: bool = True,
    n_alternatives: int = 10,
    max_response_tokens: Optional[int] = None,
    chat_template_kwargs: Optional[Dict[str, Any]] = None,
) -> List[StatCalculatorContainer]:
    """Swap GreedyProbsCalculator for the teacher-forced one, in place in the list.

    Order matters: UEManager maps stat -> last container declaring it, so the
    replacement must sit where GreedyProbsCalculator sat, not be appended.
    """
    stats, deps = TeacherForcedProbsCalculator.meta_info()
    cfg = OmegaConf.create(
        dict(
            output_attentions=output_attentions,
            n_alternatives=n_alternatives,
            max_response_tokens=max_response_tokens,
            chat_template_kwargs=dict(chat_template_kwargs or {}),
        )
    )
    out, swapped = [], False
    for container in containers:
        if container.name == GREEDY_PROBS_CALCULATOR:
            out.append(
                StatCalculatorContainer(
                    name=TeacherForcedProbsCalculator.__name__,
                    stats=stats,
                    dependencies=deps,
                    builder='sirin.detection.processors.teacher_forcing',
                    cfg=cfg,
                )
            )
            swapped = True
        else:
            out.append(container)
    if not swapped:
        raise RuntimeError(
            f'{GREEDY_PROBS_CALCULATOR} not found among stat calculators; '
            'cannot enable teacher forcing.'
        )
    lg.debug('Uncertainty: scoring provided responses (teacher-forced), not regenerating.')
    return out
