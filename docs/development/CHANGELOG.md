# SIRIN UI changelog

This changelog records user-facing and runtime changes to the canonical Streamlit UI. The static Hugging Face replay deployment is maintained separately.

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
