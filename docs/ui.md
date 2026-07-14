
# SIRIN Streamlit UI

SIRIN has one canonical Streamlit entrypoint and a unified component workspace:

- **Analyze** generates and scores an answer, scores a supplied answer, or runs answerability.
- **Runs** keeps terminal run records and supports a separate quick-prompt composer.
- **Diagnostics** summarizes the runtime; sensitive attention, capture, path, and unload controls are available only in trusted-local mode.

The native Streamlit sidebar remains authoritative for generator, detector, provider consent, and appearance. Theme and background motion are set only in the sidebar; the workspace header stays compact and the component mirrors the canonical server-side appearance state. Python owns execution and validation, while the component owns workspace navigation, drafts, and result presentation.

## Start

```bash
python -m pip install -e '.[ui]'
python -m streamlit run sirin/ui/streamlit_app.py
```

The unified workspace uses the `sirin.workspace.v2` session namespace. Historical runs retain the setup snapshot used to produce them.

The new workspace is unconditional; no `SIRIN_UI_WORKSPACE` feature flag is required. Runtime wheels include the compiled component assets.

For API-backed generation or judges, paste the provider key into the masked sidebar field and confirm the destination. A pasted key is held only in this browser session — never persisted, logged, exported, or echoed — and is keyed per provider, so it never follows a provider switch. If no key is pasted, the run falls back to the provider-specific environment variable (`OPENAI_API_KEY`, `OPENROUTER_API_KEY`, or `ANTHROPIC_API_KEY`); the sidebar caption shows which of the three states applies. When the judge and generator target the same provider, one pasted key serves both. Keys never fall back between providers.

## Analyze

Faithfulness is the default task. Enter context and a question, then use **Generate & score**. Faithfulness also supports **Score supplied answer**. Answerability accepts only context and question and does not invoke a generator. Incompatible detector/task combinations remain unavailable rather than being relabelled.

Curated examples fill the editor but do not run automatically. A recorded replay uses the exact verified stored answer and messages, then runs detection live. It is labelled **Recorded answer · live detection** and is distinct from **Generated now**, **Supplied answer · live detection**, and **Imported snapshot**. SHA-256 verification establishes artifact integrity, not answer truthfulness. When a curated example is selected, replaying its verified answer becomes the primary action and generation steps back to secondary; with no example selected, generation stays primary.

A fresh shared-safe faithfulness session lands on a seeded **Recorded result** card, not an empty editor. It shows the census span-probe result — graded spans, threshold, and layer recorded once on 2026-07-14 by running the live probe over the verified held-out PsiloQA answer through the product detect path, with the same-day recorded-replay export attributed alongside the stored per-character trace — so a first-time viewer sees a full graded result immediately. Because its scores were recorded, not computed live, it is labelled **Recorded result · verified — detection not live** and is deliberately distinct from **Recorded answer · live detection**: SHA-256 checks (payload, messages, and exact per-token character alignment) establish artifact integrity, never live detection. The seed is a first-class run — exportable, immutable, and rerunnable — and its **Run it live** action starts the real recorded replay (verified answer, live probe) for the same case. It is created once per new session and is never recreated after it is cleared, deleted, or once any other run exists; it is not added to imported sessions.

Execution uses a queued/running/terminal controller handshake. The browser shows an immediate honest busy state while Python performs synchronous generation and detection. Browser delivery of live token chunks is not guaranteed; a run may move directly from busy to a complete or partial answer. A successful generation is retained if detection fails, and retrying detection is a new explicit action.

Invalid detector setup is rejected before a run is queued, so generation is not started when scoring cannot run. Unexpected detector failures preserve a generated answer and emit the same correlation reference in the UI and server log.

## Appearance and motion

The Streamlit host owns a single theme-matched silk background — `silk_bg.jpg` on Light, a purpose-graded `silk_bg_dark.jpg` on Dark — behind a radial readability scrim. The component canvas is transparent; compact token-based glass surfaces provide contrast behind dense text and controls without rendering a second background image. One design-token source (`sirin/ui/tokens.json`) drives both the host CSS and the component theme.

Light and dark modes style both the component and native Streamlit controls. Motion supports **Static**, **Subtle**, and **Lively** — background drift is compositor-only and result reveals play once per run — with `prefers-reduced-motion` respected. Appearance state is server-owned and mirrored by the component, so appearance changes never create rerun feedback loops.

## Runs and portable JSON

Runs records successful, partial, failed, and catchably interrupted terminal runs for the current Streamlit session. Each record retains the setup snapshot used at execution time. Imported records are immutable; rerunning one creates a linked new run under the current setup.

Portable data is plain UTF-8 JSON:

- `sirin.run`, version 1: one run, maximum 5 MiB.
- `sirin.bundle`, version 1: up to 50 runs, maximum 10 MiB.

Exports include inputs, visible answers/results, safe setup, timestamps, hashes, and provenance. They exclude secrets, absolute paths, provider consent, hidden reasoning, tensors, traces, model objects, Hydra targets, and raw exceptions. Import validation rejects unknown versions or fields, duplicate keys, excessive nesting, invalid Unicode or spans, non-finite numbers, and ID collisions.

## Detector and score semantics

Presets are built from `sirin/ui/presets.py`. Sequence, token/span, claim, multiclass, judge, and uncertainty results retain their native semantics. Uncalibrated confidence, logits, probe scores, and uncertainty values are never presented as probabilities. A sequence score is not copied across tokens to imply localization. Token and span evidence is accompanied by equivalent readable details rather than relying on color alone.

Every result card states exactly one honest score meaning drawn from `contracts.derive_score_semantics`, and each maps to a distinct display treatment: `calibratedProbability` reads as a percentage labelled "calibrated probability"; `thresholdedRawScore` reads as a decision band showing the score together with its threshold τ (the sequence score orb adds a `vs τ` readout, the span footer a `risk τ … 1.00` legend); `relativeWithinAnswer` is labelled "relative within this answer — not comparable across runs"; and `spanAgreement` is labelled "judge agreement". Every preset yields a non-`unavailable` meaning from its own family/level (`tests/test_ui_presets.py`).

A compact latency strip on the result card shows only the run stages the payload carries (`generation`/`detection`/`total`, one decimal); recorded-result seeds carry no timings, so the strip renders nothing and the recorded card stays honestly timing-free.

Fresh shared-safe sessions default to **Probing — Token Linear · PsiloQA/Qwen3-4B** with the bundled PsiloQA checkpoint and pinned Qwen3-4B revision. The Sequence TabPFN preset remains available, but requires a trained checkpoint directory. Presets with incomplete setup disable generation and detection until corrected.

Token evidence is accepted only when feature scores, predictions, tokenizer offsets, and displayed answer text align exactly. Answer-token indices and character offsets come from the same full rendered tokenization, including prompt/answer boundary tokens. Alignment failures are detection failures, never silent successful runs with an empty result.

The live UI keeps the existing 30,000-character combined detector-input guard and current generation-token controls. Exact verified demo prompts retain their existing exception. Setup changes do not mutate historical result labels.

## Trust and provenance

Shared-safe mode is a private single-user redaction and resource-hardening profile, not authentication or hostile multi-tenant isolation. Put deployments behind authenticated TLS and keep the raw Streamlit port private.

- External calls require per-destination, per-session consent.
- Arbitrary local paths, custom endpoints, Hydra controls, live attention capture, filesystem provenance capture, and unload actions require `SIRIN_UI_TRUSTED_LOCAL=1`.
- Trusted-local Custom judge endpoints (`SIRIN_CUSTOM_OPENAI_BASE_URL`) get thinking disabled by default for verdict/annotation stability; set `SIRIN_CUSTOM_JUDGE_THINKING=1` to re-enable it.
- Shared-safe paths remain constrained by `SIRIN_UI_DATA_ROOTS` and `SIRIN_UI_CHECKPOINT_ROOTS`.
- Browser errors are sanitized; raw provider/CUDA errors, stack traces, credentials, response bodies, environment values, and absolute paths are not component payloads.
- Model/checkpoint provenance and score semantics travel with each run.

Do not expose trusted-local mode to untrusted users.

## Component development and packaging

Runtime wheels contain the component manifest and committed Vite build, so users do not need Node or network access to start the UI. Contributors rebuilding the component use Node 20 or newer:

```bash
cd sirin/ui/workspace/frontend
npm ci
npm run build
```

Commit the generated `build/` assets together with frontend source changes. The package-data configuration includes the component manifest, npm manifests, and recursive build assets. Global Streamlit CSS uses purposeful local font fallbacks; the component remains style-isolated.

User-facing UI changes are recorded in the [development UI changelog](development/CHANGELOG.md).

## Deferred paper features

Compare views (with the localization-agreement bar and scale-gated score deltas), context heat bars, latency breakdowns, the Add-a-detector guide, the RAGTruth gallery, and multi-model pooling (ModelManager-owned loading, `SIRIN_UI_MAX_ACTIVE_MODELS`) have shipped. Still intentionally deferred: SimpleMem serve/retry/abstain memory controls (the LongMemEval profiles and per-variant detector artifacts that feed them are bundled) and a Mu-SHROOM gallery (no verified local dataset). The static Hugging Face replay deployment remains separate and unchanged.
