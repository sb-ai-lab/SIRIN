"""Live LookbackLens attention — generate an answer with Qwen3.5-4B in-process and read its
per-answer-token attention-to-context ratio per layer, rendered as a layer x token heatmap.

Unlike the offline ``attention_explorer`` (which reads a feature cache off disk), this view loads
the model on a free GPU, greedily generates, and captures the real softmax attention live. Three
facts about qwen3_5 shape the implementation:

* It is a HYBRID model — only 8 of 32 decoder layers do softmax attention (``layer_types ==
  'full_attention'``); the other 24 are linear-attention and expose no attention matrix. Model-layer
  indices for the 4B checkpoint are [3, 7, 11, 15, 19, 23, 27, 31].
* ``output_attentions`` is a no-op for qwen3_5 (the modeling code discards the weights), so we read
  the attention via a forward hook on ``self_attn`` under ``attn_implementation='eager'``, where
  ``Qwen3_5Attention.forward`` returns ``(attn_output, attn_weights)`` with the real (1, 16, S, S)
  softmax.
* The decoder layers live at ``model.model.language_model.layers`` (NOT ``model.model.layers``).

The ratio is a line-for-line port of ``LookbacksProcessor._compute_layer_lookback`` (a MEAN over
each span, not a softmax-mass fraction). The pure helpers (layer selection, the ratio, head-mean,
label cleanup) are ``st``/model-free so they can be unit-tested — see tests/test_ui_live_attention.py.
"""

from __future__ import annotations

from typing import Any

import numpy as np
import torch

MODEL_PATH = 'Qwen/Qwen3.5-4B'
DEFAULT_DEVICE = 'cuda:6'
MAX_TOTAL_TOKENS = 1536
IM_END = '<|im_end|>'

# The 4B checkpoint's full-attention (softmax) model-layer indices — the only layers that expose an
# attention matrix. Derivable at runtime via full_attention_layers(config...); hardcoded here so the
# sidebar can offer the choice without loading the (heavy) model.
FULL_ATTENTION_LAYERS_4B = [3, 7, 11, 15, 19, 23, 27, 31]


# --- pure helpers (testable; no model / GPU / streamlit) ---------------------

def full_attention_layers(layer_types: list[str]) -> list[int]:
    """Indices of the softmax-attention layers (the rest are linear-attention, no matrix)."""
    return [i for i, t in enumerate(layer_types) if t == 'full_attention']


def layer_lookback_ratio(attn: torch.Tensor, context_len: int, token_len: int) -> torch.Tensor:
    """Per-answer-token attention-to-context ratio: one row per generated token, one col per head.

    Line-for-line port of ``LookbacksProcessor._compute_layer_lookback``: for each answer token
    ``t`` in ``[context_len, token_len)`` the ratio is the MEAN attention over context key positions
    divided by (that mean + the MEAN over the generated-so-far keys, incl. self) — NOT a softmax-mass
    fraction. ``attn`` is (H, S, S); returns (n_answer_tokens, H)."""
    num_heads = attn.shape[0]
    ratio = torch.zeros((token_len - context_len, num_heads), dtype=torch.float32)
    for offset, tok_idx in enumerate(range(context_len, token_len)):
        attn_on_context = attn[:, tok_idx, :context_len].mean(-1)
        attn_on_new = attn[:, tok_idx, context_len:tok_idx + 1].mean(-1)
        ratio[offset] = attn_on_context / (attn_on_context + attn_on_new + 1e-10)
    return ratio


def lookback_layer_token_matrix(
    attn_by_layer: list[torch.Tensor], context_len: int, token_len: int
) -> np.ndarray:
    """Head-mean lookback ratio per (layer, answer token) -> (n_layers, n_answer_tokens)."""
    return np.stack([
        layer_lookback_ratio(attn, context_len, token_len).mean(dim=1).numpy()
        for attn in attn_by_layer
    ])


def clean_token_labels(pieces: list[str]) -> list[str]:
    """Byte-BPE sentinels -> readable text (same cleanup as attention_explorer._try_tokenize)."""
    return [p.replace('Ġ', ' ').replace('Ċ', '\n').replace('▁', ' ') for p in pieces]


# --- model I/O (thin; heavy imports kept inside so the module imports without transformers) ------

def load_lookback_model(model_path: str = MODEL_PATH, device: str = DEFAULT_DEVICE):
    """Load Qwen3.5-4B under EAGER attention. Eager is required: ``output_attentions`` is a no-op for
    qwen3_5, so the live attention only exists because eager returns ``(output, weights)`` that the
    forward hook can read."""
    from transformers import AutoTokenizer, Qwen3_5ForConditionalGeneration

    tok = AutoTokenizer.from_pretrained(model_path)
    model = Qwen3_5ForConditionalGeneration.from_pretrained(
        model_path,
        dtype=torch.bfloat16,
        attn_implementation='eager',
        device_map={'': device},
        low_cpu_mem_usage=True,
    ).eval()
    # Fail loud if eager did not stick — any other implementation silently discards attn weights.
    assert model.config.text_config._attn_implementation == 'eager', (
        model.config.text_config._attn_implementation
    )
    return model, tok


def _chat_ids(tok, context_question: str):
    """Prompt token ids WITH the assistant generation prompt. Its length is the context boundary:
    everything up to here is the prompt (the LookbackLens "context"), tokens generated after it are the
    answer. Chosen over offset_mapping, which is unreliable across the chat template."""
    messages = [{'role': 'user', 'content': context_question}]
    # thinking DISABLED so the model answers directly (the offline fixture also ran thinking-off; with
    # it on, a 4B emits a long <think> block and the heatmap covers reasoning, not the answer).
    # transformers 5.x apply_chat_template returns a BatchEncoding (not a bare tensor) -> take input_ids.
    prompt = tok.apply_chat_template(
        messages, add_generation_prompt=True, enable_thinking=False,
        return_tensors='pt', return_dict=True)
    return prompt['input_ids']


def _mk_attn_hook(store: dict, model_layer_idx: int):
    """Forward hook that captures the eager (1, 16, S, S) softmax weights (``output[1]``) for a layer."""
    def hook(_module, _inputs, output):
        if isinstance(output, tuple) and len(output) > 1:
            weights = output[1]
            if torch.is_tensor(weights) and weights.dim() == 4:
                store[model_layer_idx] = weights.detach().to(torch.float32).cpu()
    return hook


def generate_and_capture(model, tok, context_question, max_new_tokens, display_layers):
    """Greedily generate an answer, then one hooked forward pass to capture the softmax attention.

    Returns ``{'attn': [(H, S, S) per requested layer], 'context_len', 'token_len', 'answer_ids'}``."""
    device = model.device
    prompt_ids = _chat_ids(tok, context_question)
    context_len = prompt_ids.shape[1]
    # Fail fast BEFORE the expensive generate: oversized prompt, or a layer with no softmax matrix.
    if context_len + max_new_tokens > MAX_TOTAL_TOKENS:
        raise ValueError(
            f'Prompt ({context_len}) + max_new_tokens ({max_new_tokens}) exceeds '
            f'MAX_TOTAL_TOKENS={MAX_TOTAL_TOKENS}; shorten the context or lower max_new_tokens.'
        )
    full_attn = set(full_attention_layers(model.config.text_config.layer_types))
    bad = [i for i in display_layers if i not in full_attn]
    if bad:
        raise ValueError(
            f'Layers {bad} are linear-attention (no softmax matrix to capture); '
            f'pick from full-attention layers {sorted(full_attn)}.'
        )
    im_end = tok.convert_tokens_to_ids(IM_END)

    prompt_ids = prompt_ids.to(device)
    with torch.no_grad():
        generated = model.generate(
            prompt_ids,
            attention_mask=torch.ones_like(prompt_ids),
            do_sample=False,
            max_new_tokens=max_new_tokens,
            eos_token_id=im_end,
            pad_token_id=im_end,
        )
    full_ids = generated[0]
    token_len = full_ids.shape[0]  # <= context_len + max_new_tokens, bounded by the guard above

    store: dict[int, torch.Tensor] = {}
    layers = model.model.language_model.layers  # decoder layers live under language_model, not model.
    handles = [
        layers[i].self_attn.register_forward_hook(_mk_attn_hook(store, i))
        for i in display_layers
    ]
    try:
        with torch.no_grad():
            model(
                input_ids=full_ids[None].to(device),
                attention_mask=torch.ones((1, token_len), dtype=torch.long, device=device),
                use_cache=False,
            )
    finally:
        for handle in handles:
            handle.remove()

    if len(store) != len(display_layers):
        raise ValueError(
            f'Captured {len(store)} attention layers, expected {len(display_layers)} '
            f'({list(display_layers)}) — are these full_attention layers under eager attention?'
        )

    return {
        'attn': [store[i][0] for i in display_layers],  # (1, 16, S, S) -> (16, S, S)
        'context_len': context_len,
        'token_len': token_len,
        'answer_ids': full_ids[context_len:token_len],
    }


# --- streamlit render --------------------------------------------------------

def render(st: Any) -> None:
    """Sidebar controls + a LIVE layer x token LookbackLens heatmap over a freshly generated answer.

    Loads Qwen3.5-4B in-process (eager attention) on the chosen GPU — heavy; needs the model env."""
    with st.sidebar:
        st.header(':material/bolt: Live attention')
        device = st.text_input(
            'Device', value=DEFAULT_DEVICE, help='CUDA device for the in-process model, e.g. cuda:6.'
        )
        max_new_tokens = int(
            st.number_input('Max new tokens', min_value=16, max_value=512, value=256, step=16)
        )
        display_layers = st.multiselect(
            'Attention layers',
            options=FULL_ATTENTION_LAYERS_4B,
            default=[11, 15, 19, 23],
            help='Model-layer indices that do softmax attention (hybrid model: only 8 of 32).',
        )

    st.subheader('Live LookbackLens attention')
    st.caption(
        'Generate an answer with Qwen3.5-4B in-process and read its per-token attention-to-context '
        'ratio per layer (head-mean). Colour shows low-context attention intensity (1 - ratio), '
        'a diagnostic signal, not a calibrated hallucination probability.'
    )

    context_question = st.text_area(
        'Context + question',
        height=200,
        placeholder='Paste the context passage and question exactly as the model should see them.',
    )
    if not st.button('Generate + capture attention', type='primary'):
        return
    if not context_question.strip():
        st.warning('Enter a context + question first.')
        return
    if not display_layers:
        st.warning('Select at least one attention layer.')
        return

    try:
        with st.spinner(f'Loading Qwen3.5-4B on {device} and generating...'):
            model, tok = _load_cached(device=device)
            out = generate_and_capture(
                model, tok, context_question, max_new_tokens, list(display_layers)
            )
    except Exception as error:  # noqa: BLE001 - bad device / OOM / capture failure -> friendly message
        st.error(f'Live attention run failed: {error}')
        return

    mat = lookback_layer_token_matrix(out['attn'], out['context_len'], out['token_len'])
    cells = clean_token_labels(tok.convert_ids_to_tokens(out['answer_ids'].tolist()))
    risk = 1.0 - mat

    answer_text = tok.decode(out['answer_ids'], skip_special_tokens=True)
    st.caption(
        f'Model {MODEL_PATH} · device {device} · {out["token_len"]} tokens total '
        f'({len(cells)} generated answer tokens, thinking disabled).'
    )
    with st.expander('Generated answer', expanded=True):
        st.markdown(answer_text or '_(empty generation)_')

    from sirin.ui.visualizers import layer_token_heatmap
    from sirin.ui.styles import colorbar_html
    from sirin.ui.attention_explorer import normalize01

    relative = st.toggle(
        'Scale colours relative to this answer',
        value=False,
        key='live_lb_relative',
        help="Off (default): absolute 0–1 risk, comparable across runs. "
             "On: min-max stretched to THIS answer's range.",
    )
    if relative:
        shown = normalize01(risk)
        caption = f"relative low-context-attention intensity; raw ratio range {float(mat.min()):.4f}-{float(mat.max()):.4f}"
    else:
        shown = risk
        caption = 'fixed 0-1 low-context-attention intensity (1 - attention-to-context ratio)'
    st.html(colorbar_html(0.0, 1.0, label=caption))
    st.html(layer_token_heatmap(display_layers, cells, mat, shown))


def _cache_resource(func):
    try:
        import streamlit as st

        return st.cache_resource(show_spinner='Loading Qwen3.5-4B (eager attention)...')(func)
    except Exception:  # noqa: BLE001 - streamlit absent (tests) -> run uncached
        return func


_load_cached = _cache_resource(load_lookback_model)
