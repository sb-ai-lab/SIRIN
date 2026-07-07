# SIRIN Streamlit UI

A local chat demo for SIRIN: chat with a model, then inspect hallucination and
answerability signals with a bespoke visualization per detector type — on a
holographic *silk* backdrop (a self-contained baked gradient recreated from the design
reference, no external assets) with dark frosted-glass panels.

## Start

```bash
conda activate sirin_exps
python -m pip install -e '.[ui]'
streamlit run sirin/ui/streamlit_app.py
```

Open the URL Streamlit prints (usually `http://localhost:8501`).

For the OpenAI/OpenRouter judge preset, set the API key first:

```bash
export OPENAI_API_KEY=...
```

## Use

1. In the sidebar, pick a **generator** backend (`HF`, `OpenAI`, `vLLM`), model, and device.
2. Pick a **detector preset** (see below). Checkpoint-based presets show a
   *Checkpoint directory* field.
3. Type a message in the chat box — put the context and question together, e.g.
   `Context: ... \n Question: ...` — or click a suggestion chip.
4. SIRIN generates an answer, runs the selected detector on the
   `[user, assistant]` pair, and renders the analysis inline under the answer.

## Detector presets

Built directly in Python (`sirin/ui/presets.py`), so the UI can reach detectors the
Hydra `train` config cannot:

| Preset | Runs without a checkpoint? | Output |
|--------|---------------------------|--------|
| **Uncertainty — Sequence (zero-shot)** | ✅ local HF model | raw uncertainty score + threshold |
| **Uncertainty — Token (zero-shot)** | ✅ local HF model | per-token uncertainty highlight over the answer |
| **Judge — OpenAI (zero-shot)** | ✅ API (needs `OPENAI_API_KEY`) | verdict + confidence + reasoning |
| **Probing — Sequence TabPFN (checkpoint)** | ❌ needs a trained checkpoint dir | calibrated probability gauge |

Uncertainty and OpenAI-judge scores are **not** calibrated probabilities, so they are
shown as a raw score against the detector's threshold — never as a 0–100% gauge. The
checkpoint presets light up once you point them at a trained SIRIN checkpoint directory
(`config.joblib` + `model.tabpfn_fit`). An **Advanced: Hydra detector** expander keeps the
original config-directory/overrides path for power users.

## Visualizations

- **Sequence** — calibrated probes show a gauge with a threshold marker + verdict badge;
  uncertainty/judge show a raw-score chip + verdict.
- **Token** — a character heatmap over the answer (per-sample min–max normalized for
  uncertainty), plus any highlighted hallucination spans.
- **Claim** — one card per extracted fact (probability + verdict) with an overall verdict.
- **Reasoning** — judge-generated text, when available, in an expander.
- **Per-method uncertainty** and **Debug** (feature-processor shapes) are shown in expanders.

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
conda activate sirin_exps
PYTHONDONTWRITEBYTECODE=1 python -m pytest -q tests/test_streamlit_ui.py
python -m ruff check sirin/ui/
python sirin/ui/styles.py && python sirin/ui/presets.py && python sirin/ui/visualizers.py
PYTHONDONTWRITEBYTECODE=1 python -c "from streamlit.testing.v1 import AppTest; a=AppTest.from_file('sirin/ui/streamlit_app.py'); a.run(timeout=60); assert not a.exception, a.exception"
```
