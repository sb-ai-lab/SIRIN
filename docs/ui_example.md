# SIRIN A* Demo Runbook

This is the reproducible script for the two-slide explanation and the live UI
video. Both video scenarios generate a new answer with
`Qwen/Qwen3.5-35B-A3B` from the canonical LongMemEval-S messages and then run
the selected SIRIN detector. The video never opens the offline replay.

The sequence example `07741c44` was used during detector training and is
explicitly labelled in the UI as a **training example approved for a mechanics
demonstration**. It demonstrates the live pipeline; it is not held-out evidence
of generalization. The token uncertainty detector is zero-shot and requires no
training.

## Reproduce the environment

The delivered take used Python 3.13.11 and the exact package versions in:

```text
demo/requirements-demo.txt
output/sirin_a_star_demo/provenance/environment.txt
```

Verify the portable TabPFN checkpoint before starting:

```bash
cd /home/jovyan/parchiev/magistr/repos/SIRIN
cd demo/checkpoints/qwen35_longmemeval_hallucination_tabpfn
sha256sum -c SHA256SUMS
cd ../../..
```

Start the UI with the environment that supports Qwen3.5:

```bash
cd /home/jovyan/parchiev/magistr/repos/SIRIN
CUDA_VISIBLE_DEVICES=0,1,2,3 \
SIRIN_UI_TRUSTED_LOCAL=1 \
SIRIN_UI_MAX_DETECTOR_INPUT_CHARS=30000 \
SIRIN_UI_AUTO_DEVICE_MAP_GPUS=4 \
PYTHONPATH=$PWD \
PYTORCH_ALLOC_CONF=expandable_segments:True \
/home/jovyan/.mlspace/envs/sirin_exps/bin/python -m streamlit run \
  sirin/ui/streamlit_app.py \
  --server.address 0.0.0.0 \
  --server.port 8502 \
  --server.headless true
```

Open `http://localhost:8502`, then use **Analyze**. The unified workspace keeps the same detector and generator setup contract. The publication take used:

| UI field | Value |
| --- | --- |
| Theme | `Light` |
| Background motion | `Static` |
| Browser | Chromium, 1920x1080, 100% zoom |
| Backend | `HF` |
| Model | `Qwen/Qwen3.5-35B-A3B` |
| Device | `cuda` |
| Max tokens | `192` |
| Temperature | `0.0` |

The default preset remains `Probing — Sequence TabPFN (checkpoint)`.

## Scenario 1: Token uncertainty

This scenario shows localization without inventing a token-level hallucination
verdict.

1. Select `Uncertainty — Token (zero-shot)` in the setup sidebar.
2. In **Analyze**, select **Uncertain sports count** (`ef66a6e5`).
3. Click **Run live with selected setup**.
4. Hold on the completed token strip.

The prompt contains 45 retrieved memories. The UI shows the two decisive
excerpts: past competitive tennis and a return to competitive swimming.

- Question: `How many sports have I played competitively in the past?`
- Dataset reference: `two`
- New live answer: `1 sport (tennis)`
- Exact token pieces: `1`, ` sport`, ` (`, `ten`, `nis`, `)`

For each generated token, SIRIN computes chosen-token negative log-likelihood
and full-vocabulary entropy from the same HF generation trace, then takes their
arithmetic mean. Color values are min-max normalized only within this six-token
answer. They are relative inspection signals, not probabilities, evidence, or
verdicts. There is no token threshold because no compatible token-labelled
Qwen3.5-35B LongMemEval calibration was run.

The LongMemEval prompt explicitly requests JSON with `reasoning` and `answer`
fields. The UI parses that response and labels the first field **Prompted
rationale**. It is prompt-requested output, not a hidden model chain of thought.

Exact live artifact:

```text
output/sirin_a_star_demo/provenance/live/ef66a6e5__uncertainty-token-zero-shot.json
artifact SHA-256 012157a7869226f0993deffdcff8f5e8646535abd73324346e846c4a7720ebfa
trace SHA-256    6a3221a89f61a35882e255a5ddbb3832c006fe6ec965b7007d9738b505398df7
```

Prompt SHA-256 is
`e40f335ee8a0db16a8d3b1089a10b14da8ba70b10ede2b063bcfa700c072742b`;
the full message sequence SHA-256 is
`006aaf6b6a218e1fe36e2ce020c4400f059c00fe8363305931d2300871600c00`.

Suggested narration:

> The memory contains two competitive sports, but the agent answers with one.
> SIRIN preserves the exact generation trace and localizes relative uncertainty
> over the generated tokens. The color tells an operator where to inspect; the
> retrieved memory, not the color, establishes that the count is wrong.

## Scenario 2: Sequence probing

This scenario shows temporal confusion: the model substitutes a later storage
plan for the initial state requested by the user.

1. Select `Probing — Sequence TabPFN (checkpoint)` in the setup sidebar.
2. In **Analyze**, select **Initial sneaker location** (`07741c44`).
3. Confirm the portable checkpoint path in the sidebar.
4. Click **Run live with selected setup**.
5. Hold on the completed response-level assessment.

The prompt contains 38 retrieved memories. The two decisive excerpts are dated
and labelled as a later storage plan and the initial storage state.

- Question: `Where do I initially keep my old sneakers?`
- Dataset reference: `under my bed`
- New live answer: `In a shoe rack`
- Raw probe score: `0.8529232144355774`
- Decision threshold: `0.09885282069444656`
- Decision: `Flagged for review`
- Scope: training example approved for a mechanics demonstration

This is one response-level score. It is shown uniformly across the answer
because sequence probing does not localize individual words. The score is not a
calibrated probability. Higher values indicate greater review risk, and the
decision is `score > threshold`.

The threshold was selected with the checkpoint's `optimal` method on its
LongMemEval-S `hallucination_strict` validation split. The live extractor uses
Qwen3.5 hidden-state layers `[20, 35, 36, 37, 38, 39]`, RIGHT-side answer-start
features, mean pooling, and checkpoint feature shape `[6, 1, 2048]`.

Portable checkpoint and manifest:

```text
demo/checkpoints/qwen35_longmemeval_hallucination_tabpfn/
demo/checkpoints/qwen35_longmemeval_hallucination_tabpfn/SHA256SUMS
```

Exact live artifact:

```text
output/sirin_a_star_demo/provenance/live/07741c44__probing-sequence-tabpfn-checkpoint.json
artifact SHA-256 34ed1a9d945f6d91a6f661bccbcaf4939b3de5e68680c33973797367890993e2
```

Prompt SHA-256 is
`63bb447f5605de1c8f54eacc2b6d6c22d1d1e01422e660862b60eb35992d6696`;
the full message sequence SHA-256 is
`612eca3593bf1ea264f4fb0b82cefd953d8a210157057d14760059ddeeafcd33`.

Suggested narration:

> The question asks for the initial location, but the model copies a later plan.
> SIRIN probes the hidden states of the answer that was just generated. The raw
> score crosses the validation-selected checkpoint threshold, so the agent can
> retry, retrieve more carefully, or abstain before serving the answer.

## Runtime contract

Both artifacts pin model revision:

```text
Qwen/Qwen3.5-35B-A3B
59d61f3ce65a6d9863b86d2e96597125219dc754
```

The profile `sirin/ui/assets/longmemeval_qwen35.json` records the model revision,
all LongMemEval checkpoint paths, the sequence-probe threshold, and the fact
that no token threshold exists. The unrelated sequence-uncertainty experiment
threshold is intentionally not reused for token coloring or this sequence
probe.

The v2 controller reports queued, running, and terminal states around synchronous Python execution. Browser delivery of token-by-token generation is not guaranteed: captures may show an honest busy state followed by the complete or partial answer. This does not change the exact messages, detector input, generated answer, or provenance artifact.

## Delivered video

| Time | Visible action |
| --- | --- |
| `0:00-0:01` | Token case setup and live-run click. |
| `0:01-0:14` | Structured Qwen rationale and answer stream. |
| `0:14-0:20.5` | Reference, generated answer, trace hash, and six-token signal. |
| `0:20.5-0:21` | Clean crossfade to the sequence case setup. |
| `0:21-0:36` | Sequence-case generation streams. |
| `0:36-0:42` | SIRIN extracts hidden states and runs the packaged probe. |
| `0:42-0:49.52` | Raw score, threshold, risk direction, answer, and verdict hold. |

The delivered file is silent H.264 High, 1920x1080, 25 fps, 49.52 seconds:

```text
output/sirin_a_star_demo/sirin_longmemeval_live_demo.mp4
SHA-256 7480a2a2f5aa5fa23cbd02be63edb4f5a77ebb4e27c79c13997dd4fe27b5fc86
```

The untrimmed live captures are retained as:

```text
output/sirin_a_star_demo/videos/token_live_final.webm
output/sirin_a_star_demo/videos/sequence_live_final.webm
```

The final edit removes idle time and adds one 0.5-second crossfade. It does not
replace either generation or detector result. Frame-by-frame join checks and
contact sheets are in `output/playwright/video_review/`.

## Slide assets

- Slide source: `demo/slides/sirin_a_star_demo.js`
- PowerPoint: `output/sirin_a_star_demo/sirin_a_star_demo.pptx`
- Rendered previews: `output/sirin_a_star_demo/rendered/`
- UI video: `output/sirin_a_star_demo/sirin_longmemeval_live_demo.mp4`

Slide 1 reuses paper Figure 1 to distinguish Judge, Probing, and Uncertainty.
Slide 2 reuses the memory-loop figure and completed Qwen rows from Table 5. The
`76.6` result is served-set accuracy at `67.2%` coverage, not unconditional
accuracy.
