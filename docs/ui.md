# SIRIN Streamlit UI

A local chat demo for SIRIN: chat with a model, then inspect hallucination and
answerability signals with a bespoke visualization per detector type — on a
holographic *silk* backdrop (a self-contained baked gradient recreated from the design
reference, no external assets) with dark frosted-glass panels.

## Start

Activate your preferred Python environment first, then:

```bash
python -m pip install -e '.[ui]'
python -m streamlit run sirin/ui/streamlit_app.py
```

Open the URL Streamlit prints (usually `http://localhost:8501`).

For API-backed generation or judge presets, set the matching provider key first:

```bash
export OPENAI_API_KEY=...      # OpenAI provider
export OPENROUTER_API_KEY=...  # OpenRouter provider
export ANTHROPIC_API_KEY=...   # Anthropic provider
```

## Use

1. In the sidebar, pick a **generator** backend (`HF`, `OpenAI`, `OpenRouter`, `Anthropic`, `vLLM`), model, and device.
2. Pick a **detector preset** (see below). Checkpoint-based presets show a
   *Checkpoint directory* field.
3. Type a message in the chat box — put the context and question together, e.g.
   `Context: ... \n Question: ...` — or click a suggestion chip.
4. SIRIN generates an answer, runs the selected detector on the
   `[user, assistant]` pair, and renders the analysis inline under the answer.
5. Use **Attention tools** in the sidebar only when you need diagnostics:
   **Cached explorer** opens offline feature-cache inspection, and **Live capture**
   opens the GPU-backed Qwen attention capture path.

## Detector presets

Built directly in Python (`sirin/ui/presets.py`), so the UI can reach detectors the
Hydra `train` config cannot:

| Preset | Runs without a checkpoint? | Output |
|--------|---------------------------|--------|
| **Uncertainty — Sequence (zero-shot)** | ✅ local HF model | raw uncertainty score + threshold |
| **Uncertainty — Token (zero-shot)** | ✅ local HF model | per-token uncertainty highlight over the answer |
| **Judge — API (zero-shot)** | ✅ API (needs provider key) | verdict + confidence + reasoning |
| **Probing — Sequence TabPFN (checkpoint)** | ❌ needs a trained checkpoint dir | calibrated probability gauge |

Uncertainty and OpenAI-judge scores are **not** calibrated probabilities, so they are
shown as a raw score against the detector's threshold — never as a 0–100% gauge. The
checkpoint presets light up once you point them at a trained SIRIN checkpoint directory
(`config.joblib` + `model.tabpfn_fit`).

## Shared-Safe Defaults

The UI defaults to shared-safe controls:

- OpenAI uses only `OPENAI_API_KEY` and `https://api.openai.com/v1`.
- OpenRouter uses only `OPENROUTER_API_KEY` and `https://openrouter.ai/api/v1`.
- Anthropic uses only `ANTHROPIC_API_KEY` and `https://api.anthropic.com/v1/`.
- API keys never fall back across providers.
- External API calls require a per-session sidebar confirmation because prompts, generated
  answers, and judge prompts may leave the server.
- Provider base URLs, device, tokenizer, Hydra, and raw path controls are limited by
  default; API and local model names remain editable.
- Set `SIRIN_OPENAI_MODEL`, `SIRIN_OPENROUTER_MODEL`, or `SIRIN_ANTHROPIC_MODEL`
  to choose API model defaults without editing code.
- `Max tokens` remains user-controlled and uncapped.

For single-user local development, trusted mode restores the sharp controls:

```bash
export SIRIN_UI_TRUSTED_LOCAL=1
```

Trusted mode allows custom OpenAI-compatible generator endpoints, arbitrary local
model/device/tokenizer fields, raw Explorer paths, checkpoint paths, and the Advanced
Hydra detector expander.
Use it only when the Streamlit server is not exposed to untrusted users.

In shared-safe mode, local files must be under explicit roots:

```bash
export SIRIN_UI_DATA_ROOTS=/path/to/datasets:/path/to/feature_caches
export SIRIN_UI_CHECKPOINT_ROOTS=/path/to/checkpoints
```

## Visualizations

- **Sequence** — calibrated probes show a gauge with a threshold marker + verdict badge;
  uncertainty/judge show a raw-score chip + verdict.
- **Token** — a character heatmap over the answer (per-sample min–max normalized for
  uncertainty) rendered as inline evidence chips with hover metadata. Missing score
  coverage is neutral, not green.
- **Claim** — one card per extracted fact (probability + verdict) with an overall verdict.
- **Attention tools** — LookbackLens matrices show low-context-attention intensity as
  a diagnostic signal. They are not calibrated hallucination probabilities unless a
  detector explicitly produced calibrated token scores.
- **Reasoning** — judge-generated text, when available, in an expander.
- **Per-method uncertainty** and **Debug** (feature-processor shapes) are shown in expanders.

Chat is the default app surface. Explorer and Live Capture are sidebar-launched tools,
not a three-way top-level view switch. If the tool surface grows beyond the sidebar
launcher, move those tools to native Streamlit pages as the fallback navigation model.

## Appearance

The **Appearance → Background motion** control in the sidebar switches the silk backdrop
between **Subtle** (default gentle drift), **Static** (no animation — lightest for low-power
devices), and **Lively**. The app also honours the OS `prefers-reduced-motion` setting
(forces static). All accent colours are defined once in `sirin/ui/styles.py` (`PALETTE`) and
reused by the result visualizers, so the whole app stays on one palette.

## Notes

- Uncertainty detectors re-generate and score their own answer (lm-polygraph), so the token
  heatmap is drawn over the text the detector actually scored (`last_generated_text`), which
  can differ from an answer you edited by hand.
- The generator model and the detector's feature extractor are shared when both use the HF
  backend (one model in VRAM).

## Smoke checks

```bash
PYTHONDONTWRITEBYTECODE=1 python -m pytest -q tests/test_streamlit_ui.py
python -m ruff check sirin/ui/
python sirin/ui/styles.py && python sirin/ui/presets.py && python sirin/ui/visualizers.py
PYTHONDONTWRITEBYTECODE=1 python -c "from streamlit.testing.v1 import AppTest; a=AppTest.from_file('sirin/ui/streamlit_app.py'); a.run(timeout=60); assert not a.exception, a.exception"
```
