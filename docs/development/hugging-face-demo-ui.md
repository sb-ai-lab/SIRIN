# Hugging Face demo UI architecture

Status: recommended target, not yet implemented. This note was checked against
commit `51573b7e1bd73705c4ff096c0b723a31f41e6cd2` on 2026-07-13; ignored
`output/` artifacts and uncommitted UI experiments are outside its code claims.

## Decision

Build the polished hosted demo as a **Hugging Face Gradio SDK Space** with:

- `gradio.Server` for the Python API, queue, concurrency control, and streaming;
- a custom **React + TypeScript + Vite** frontend with plain CSS;
- `@gradio/client` for calls from the browser;
- the existing SIRIN/PyTorch inference code behind a thin adapter; and
- one shared HF model for generation and feature extraction when the selected
  detector permits it, matching the reuse already present in
  [`presets.py`](../../sirin/ui/presets.py).

This is the best balance between the visual control of a normal web app and the
deployment machinery of Gradio Spaces. Gradio documents `Server` as a FastAPI
server intended for custom React/HTML frontends while retaining queuing,
streaming, ZeroGPU, and Spaces support. With ZeroGPU, browser requests must go
through `@gradio/client` because it forwards the Hugging Face iframe headers used
for quota handling ([Gradio Server mode](https://www.gradio.app/guides/server-mode)).

```text
React/TypeScript/Vite + plain CSS
  -> @gradio/client
  -> gradio.Server API (queue + SSE)
  -> thin demo adapter
  -> SIRIN generator + detector
  -> pinned HF model + pinned probe artifact
```

## Current committed baseline

The repository currently ships a Streamlit app
([`streamlit_app.py`](../../sirin/ui/streamlit_app.py)) with custom result HTML,
detector-specific views, and extensive CSS in
[`styles.py`](../../sirin/ui/styles.py). That proves the desired visual language
and SIRIN flow, but it is not the recommended hosted shell: some styling depends
on Streamlit DOM selectors, and Streamlit owns layout and interaction details.
Preserve the behavior and design tokens; do not port Streamlit widget code.

## API and interaction contract

Expose two semantic operations and put both in one GPU concurrency group with a
limit of one until measurement proves parallel inference is safe:

```python
@app.api(
    name="run_case",
    concurrency_id="sirin_gpu",
    concurrency_limit=1,
    stream_every=0.1,
)
@spaces.GPU(duration=15)
def run_case(case_id: str):
    yield frame

@app.api(
    name="run_custom",
    concurrency_id="sirin_gpu",
    concurrency_limit=1,
    stream_every=0.1,
)
@spaces.GPU(duration=estimate_duration)
def run_custom(context: str, question: str, max_new_tokens: int = 128):
    yield frame
```

Generator functions stream over SSE, and `app.api()` exposes concurrency and
streaming controls ([Gradio Server mode](https://www.gradio.app/guides/server-mode)).
Return structured frames rather than server-rendered HTML or detector objects:

```ts
type RunFrame = {
  phase: "warming" | "generating" | "scoring" | "complete" | "error";
  answer: string;
  segments: Array<{ text: string; risk: number | null; suspect: boolean }>;
  provenance: Record<string, string | number> | null;
};
```

Return text segments, not character offsets: Python code-point indices and
JavaScript UTF-16 indices can disagree. Keep detector metadata explicit, and do
not label an uncalibrated score as a probability.

For curated cases, animate the stored answer in the browser and call the GPU only
for live scoring. Do not hold a ZeroGPU allocation while sleeping to imitate token
streaming. For custom input, generate and score inside the GPU operation and stream
real phase/result updates.

## Space layout and hardware

Use one source tree in two Spaces if both access profiles are needed:

1. **Showcase:** dedicated 1x L4 for predictable startup and latency. Hugging Face
   currently lists the L4 with 24 GB VRAM
   ([GPU Spaces](https://huggingface.co/docs/hub/spaces-gpus)).
2. **Public mirror:** ZeroGPU `large` for lower idle cost and casual traffic.
   ZeroGPU currently provides 48 GB for `large`, but has quotas and queues; it is
   available only to Gradio SDK Spaces
   ([ZeroGPU](https://huggingface.co/docs/hub/spaces-zerogpu)).

Start with this dated compatibility lock, then freeze only after a golden-case
generation and detector-output check:

```text
Python 3.12.12
PyTorch 2.9.1
Gradio 6.20.0
Transformers 5.3.0
```

Python 3.12.12 and PyTorch 2.9.1 are in the current ZeroGPU supported set
([ZeroGPU](https://huggingface.co/docs/hub/spaces-zerogpu)); Gradio 6.20.0 was the
current PyPI release when this note was written
([PyPI](https://pypi.org/project/gradio/)). Transformers 5.3.0 is a provisional
choice within SIRIN's committed `>=4.56.0,<5.4.0` constraint, not a claim of
validated numerical equivalence.

A Space README can begin with:

```yaml
---
title: SIRIN Span-level Hallucination Detection
emoji: 🦄
sdk: gradio
sdk_version: 6.20.0
python_version: 3.12.12
app_file: app.py
fullWidth: true
header: mini
models:
  - Qwen/Qwen3-4B
  - <org>/<versioned-probe-repository>
---
```

These fields are defined by the
[Spaces configuration reference](https://huggingface.co/docs/hub/spaces-config-reference).

## Packaging rules

- Build `web/dist` in CI and include the static output in the Space revision;
  startup should run Python, not install Node or compile the frontend.
- Give the Space a lean dependency set for serving only. Do not install SIRIN's
  training, vLLM, or topology stack unless the selected inference path imports it.
- Store the probe separately in a versioned Hub model repository and pin both the
  model and probe to immutable revisions. Public artifacts may be downloaded at
  build time with `preload_from_hub`, including a commit SHA
  ([Spaces configuration reference](https://huggingface.co/docs/hub/spaces-config-reference)).
- Validate the pinned environment with a small set of golden curated cases before
  publishing either Space.

## Why not the alternatives?

| Option | Use when | Why it is not the target |
|---|---|---|
| Current Streamlit app | Local research UI and fastest iteration | Good baseline, but less control over stable, pixel-level layout and interactions |
| Native Gradio Blocks | A functional demo matters more than exact art direction | Simplest HF path, but built-in components constrain the screenshot-level design |
| Gradio SDK + `gradio.Server` | High-polish UI plus HF/ZeroGPU deployment | **Recommended** |
| Docker Space + custom FastAPI | System packages or runtime control require Docker, and dedicated hardware is acceptable | ZeroGPU is currently Gradio-SDK-only |
| Plain custom FastAPI deployment | The application is moving beyond Spaces | Rebuilds queueing, streaming, and HF quota/auth integration already supplied by Gradio |

Do not add Next.js, Tailwind, Redux, Nginx, Redis, Celery, a database, or a custom
full-page Gradio component until a measured requirement needs one. React, Vite,
plain CSS, `gradio.Server`, and the existing Python runtime cover this demo.
