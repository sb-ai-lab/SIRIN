# SIRIN UI changelog

This changelog records user-facing and runtime changes to the canonical Streamlit UI. The static Hugging Face replay deployment is maintained separately.

## 2026-07-14 — paper features and the Qwen3.5-4B campaign

### Added

- **Compare mode**: two detectors score the same answer side by side, with a per-character localization-agreement bar (both/A-only/B-only/neither) and score deltas only when both sides share a calibrated-probability scale — every other pairing states "Different score scales — localization overlap only."
- **Pasted API keys**: masked per-provider key fields for judges and API generators; keys live only in session memory, never persisted, logged, exported, or echoed (sentinel-tested), and never follow a provider switch.
- **Span-level API judge that works**: span-tag annotation prompts, reference-aligned k/n consensus (non-verbatim generations are dropped; zero valid annotations surface as an actionable partial, never a false all-clear), honest `spanAgreement` semantics, and judge disclosures (model, provider, valid/requested, temperature) on every run.
- A second built-in probe preset — **PsiloQA/Qwen3.5-4B token linear** (layer 16, τ = 0.385, SHA-256-verified checkpoint) — plus multi-profile LongMemEval support with SimpleMem/LightMem/Mem0 Qwen3.5-4B profiles, re-curated PsiloQA demo cases, a RAGTruth gallery, and two new recorded-result landing cards (Qwen3.5-4B probe and a token-judge annotation whose spans match the hidden gold exactly).
- Latency strip (generation/detection/total) on live result cards; recorded results honestly show none.
- Per-chunk context heat-bar for sequence detectors and an "Add a detector" guide with import-checked recipes in Diagnostics.
- Campaign metrics summary: [campaign_qwen35_4b.md](campaign_qwen35_4b.md).

### Changed

- Every preset now derives a truthful score meaning (calibrated probability / raw score vs decision threshold / relative within answer / judge agreement / verdict) with distinct card copy; sequence thresholded scores render as a decision band against τ.
- Model loading routes through ModelManager: switching local models evicts the previous one (`SIRIN_UI_MAX_ACTIVE_MODELS`, default 1); stateless API adapters skip the manager.
- The Analyze task is labelled **Hallucination**, matching the paper's "contextual hallucination detection / query answerability" pairing; the portable-JSON task key stays `faithfulness`, so existing exports keep importing.
- Scoring/generating is always the pink primary action, placed right of the secondary **Replay recorded answer** button.
- The workspace content fills the shell's padded width instead of a 960px column; the Runs and Compare layouts share it.
- Background motion is perceptible immediately: larger drift amplitudes, shorter cycles (Subtle 45s, Lively 16s), and each cycle starts at its midpoint instead of an ease-in-out standstill.
- The "Allow external API calls" consent renders directly under the Judge API key whenever a judge preset is active (one session-wide checkbox, unchanged key and semantics).
- The Custom judge provider (trusted-local) defaults to `http://localhost:8000/v1` when `SIRIN_CUSTOM_OPENAI_BASE_URL` is unset and lists the served models from `/v1/models` (1.5s probe, cached per session, silent when nothing is running).
- The span-level API judge preset is discoverable: renamed **Judge — API Span (zero-shot)** (was "Judge — API Token", which never said span) and pinned second in the Detector select, right under the hero probe — it was 8th of 9 and clipped inside the dropdown at 1080p. The judge seed asset's integrity hash was recomputed for the metadata-only label change; answer/message/score hashes are untouched.

### Fixed

- The sequence API judge prompt never embedded the dialogue (missing `{sample}` placeholder) — every verdict scored an empty conversation; it now embeds the dialogue and forces a bare leading digit so the one-token logprob verdict cannot collapse into a JSON opener.
- Empty provider generations count as invalid judge votes instead of crashing detection.
- An API judge on a route that returns no logprobs — or a reasoning model that spends the one-token verdict budget on thinking — no longer fabricates a "supported" verdict or crashes with a generic "detection failed": digit verdicts render honestly without a probability, and non-verdicts surface an actionable message naming the cause.
- The Theme and Background-motion dropdowns open above their trigger, so the last options are reachable at any viewport height (previously clipped below the fold; the old fix only nudged them on ≤720px viewports).
- The Compare picker no longer offers detectors that cannot run as side B (checkpoint-requiring presets with no bundled checkpoint always hit "needs a trained checkpoint directory"); to compare against such a preset, select it as the sidebar detector with its checkpoint directory and pick the other detector as side B — the rejection message now says exactly that.

## 2026-07-14

### Added

- Single design-token source (`sirin/ui/tokens.json`) generating both the host CSS variables and the component theme, with unified Manrope/IBM Plex Mono served as static assets.
- Graded continuous span highlighting: per-span wash and underline colors interpolate with the recorded risk score, with monospace numeric risk badges, an underline-thickness step as a non-color channel, and a span footer showing the suspect-span count, maximum risk, and a threshold→1.00 risk gradient bar.
- One-shot staggered result reveal (wash sweep, underline draw, badge fade, footer) that plays once per run; Static, Subtle, and Lively modes stay distinct and `prefers-reduced-motion` disables all of it.
- Full dark variant with a purpose-graded dark silk background asset, dark-tuned readability scrim, and verified contrast (body ink 15.7:1, wordmark 4.7:1 over silk).

### Changed

- Cold start dropped from minutes to seconds: the app shell renders without importing torch/vLLM (lazy adapter imports), and styles, example registries, and payloads are cached instead of rebuilt per rerun.
- Background motion is compositor-only (transform on an oversized fixed layer) and stacked backdrop-filters were removed; idle frame times hold 60fps (p95 ≤ 16.8 ms) in every motion mode, light and dark.
- Appearance controls (theme, background motion) consolidated into the native sidebar; workspace headers are compact eyebrow/title/subtitle rows instead of hero blocks.
- Detector and generator sidebar sections use census-style small-caps headings with one-line monospace metadata, and the built-in PsiloQA preset no longer shows an empty checkpoint-directory input.
- Copy pass: humane empty states, de-jargoned Diagnostics, actionable consent and size-limit messages.

### Fixed

- Tab and theme switches no longer remount the component (persistent React root, client-side tabs).
- 1280 px layouts no longer clip or overlap; the "Paused" motion alias was unified to Static.

### Removed

- Dead styling and assembly code; the score-semantics ladder now lives in one shared helper used by the run engine, presenter, and app shell.

### Validation

- Python regression: 255 passed, 0 failed. rAF sampling: p95 16.7–16.8 ms, zero frames over 33 ms across Static/Subtle/Lively in light and dark at 1920×1080.

## 2026-07-13

### Added

- First-run **Recorded result** landing card: a fresh shared-safe faithfulness session is seeded once with the verified census span-probe result (per-character scores, threshold, and layer recorded from a one-shot live probe replay of the held-out answer), labelled **Recorded result · verified — detection not live** and upgradable in one click via **Run it live**.
- Unified **Analyze**, **Runs**, and **Diagnostics** workspace built with Streamlit Components v2.
- Generated, supplied, recorded-replay, imported-snapshot, and answerability workflows with explicit provenance.
- Portable versioned run and session JSON with bounded, strict import validation.
- Responsive light and dark themes, Static/Subtle/Lively motion, reduced-motion support, keyboard navigation, and visible focus states.
- Local Manrope, IBM Plex Mono, and Noto Color Emoji assets with bundled licenses.
- Correlation logging that uses the same reference displayed for unexpected detector failures.

### Changed

- The host now renders one animated `silk_bg.jpg`; the component remains transparent and uses localized glass surfaces for contrast.
- Fresh shared-safe sessions now default to the bundled PsiloQA token-linear detector and pinned `Qwen/Qwen3-4B` instead of an unusable Sequence TabPFN configuration without a checkpoint.
- Invalid detector configuration now disables incompatible actions and rejects submission before generation or run creation.
- Appearance controls in the sidebar and workspace header now share one canonical server state.
- Streamlit's native light palette now matches the SIRIN Light theme, including built-in dialogs.

### Fixed

- Removed the duplicate component background and visible host/component boundary.
- Fixed dark borders around the native Max tokens number input on Light.
- Kept every Background motion option visible and reachable in short viewports.
- Fixed the endless appearance rerun loop and stale motion reversion.
- Added a compact glass strip for detector-confidence footer copy over the silk background.
- Fixed stale Diagnostics navigation after a component-triggered rerun.
- Fixed repeated export acknowledgement and one-click recorded replay behavior.
- Fixed token evidence disappearing as `No score` when a tokenizer merges the prompt's final character with the answer's first character. Feature indices and offsets now derive from the same full tokenization and are validated strictly.
- Fixed native **Clear caches** confirmation rendering as an unreadable dark dialog in Light mode.

### Removed

- Removed the legacy Streamlit workspace, standalone demo renderer, compatibility flag, and legacy-only tests.
- Removed persistent component appearance state that could override newer server values.

### Validation

- Affected Python regression: 154 passed, 0 failed.
- Frontend TypeScript check and Vite production build passed.
- Browser validation covered 1280x668 and 1920x1080 layouts, one React root, zero console errors, no horizontal overflow, two-way appearance synchronization, repeated exports, and native dialogs.
- Exact 630-character supplied-answer validation produced 18 contiguous evidence segments covering every character with a live score and provenance.
