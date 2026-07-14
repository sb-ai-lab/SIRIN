
 Proposed Plan

# Unified SIRIN UI Redesign

## Summary

- Replace the fragmented current UI with one canonical app launched through sirin/ui/streamlit_app.py.
- Retain a compact native Streamlit setup sidebar while a package-based Streamlit Components v2 React/TypeScript component owns the full Analyze, Runs, and Diagnostics workspace.
- Reuse the PsiloQA demo’s centered editorial composition, silk atmosphere, staged result card, typography hierarchy, and semantic highlights without duplicating its renderer.
- Preserve current detectors, providers, LongMemEval/PsiloQA fixtures, attention tools, failure behavior, path restrictions, and provenance.
- Add portable single-run and session JSON import/export.
- Retire sirin/ui/demo_app.py and its duplicate renderer only after unified parity passes.
- Defer paper-only Compare, agreement matrix, context heat bar, latency breakdown, Add Detector guide, RAGTruth/Mu-SHROOM expansion, memory controls, and 6–8-model warm pooling.

## Architecture and Public Interfaces

- First prove a minimal package-based Components v2 mount and trigger round-trip on Streamlit 1.58 before refactoring the application. Follow the official package-based Components v2 contract
  (https://docs.streamlit.io/develop/concepts/custom-components/components-v2/package-based).
- Add a cohesive sirin/ui/workspace/ package for contracts, presentation normalization, run execution, session control, component registration, and frontend source/build assets.
- Keep Python authoritative for detector semantics, example resolution, setup validation, model/provider execution, trust checks, error sanitization, provenance, and persistence.
- Keep React authoritative for navigation, drafts, layout, animation, result visualization, disclosures, keyboard behavior, and local optimistic state.
- Use one stable component key and Shadow DOM style isolation. Do not mount legacy and v2 workspaces simultaneously.
- Keep textarea values local to React; checkpoint only on blur/navigation and always include the complete draft in submit actions.
- Use Pydantic models as the canonical runtime schema, explicit camelCase serialization aliases, mirrored TypeScript interfaces, and shared golden JSON conformance fixtures. Do not add schema-generation
  infrastructure.

  def render_workspace(
      payload: WorkspacePayload,
      *,
      key: str = "sirin.workspace.v2",
  ) -> WorkspaceEvent:
      ...

   Contract            Required content
  ━━━━━━━━━━━━━━━━━━  ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
   WorkspacePayload    Protocol/server/setup/runs revisions, capabilities, safe setup summary, activity, examples, run summaries, selected detail, diagnostics summary, notices, action receipt, optional
                       download transfer
  ──────────────────  ──────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────
   ActionEnvelope      Protocol version, client instance ID, monotonically increasing sequence, UUID, action discriminator, full submitted data, expected setup or runs revision
  ──────────────────  ──────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────
   RunRecord           Immutable setup snapshot, task/mode/origin/status, inputs, answer, typed analysis, stage results, safe timings, provenance, digests, warnings, sanitized error
  ──────────────────  ──────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────
   AnalysisResult      Sequence, token/span, claim, multiclass, judge, uncertainty, or unavailable result with explicit semantics
  ──────────────────  ──────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────
   ScoreSemantics      calibrated_probability, thresholded_raw_score, relative_within_answer, categorical_probabilities, verdict, or unavailable
  ──────────────────  ──────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────
   ActionReceipt       Accepted, rejected, or duplicate result for a specific action sequence and payload digest

  Execution handshake:

1. React immediately shows an honest local busy state and emits one action.
2. Python validates the action after the component mount, reserves a run ID, stores QUEUED, records a receipt, and reruns.
3. The next run stores RUNNING, mounts that state, then executes generation/detection synchronously.
4. Python stores SUCCEEDED, PARTIAL, or FAILED and reruns with the terminal record.
5. A later invocation finding an abandoned RUNNING record marks it INTERRUPTED; it never silently repeats a potentially billable operation.
6. Exactly-once protection is guaranteed only within the live Streamlit session using client sequence high-water marks, recent action receipts, and payload digests.

  Live generated answers are not guaranteed to stream into the component. If Streamlit cannot deliver same-instance chunks, keep the full workspace component and show one truthful busy state followed by the
  complete or partial answer. Do not add jobs, polling, fake progress, or simulated live tokens.

## Implementation Changes

### Product behavior

   Workspace      Behavior
  ━━━━━━━━━━━━━  ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
   Analyze        Default landing page, centered like the demo: task selector, gallery, context, question, action, reserved status/result card, provenance
  ─────────────  ──────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────
   Runs           Independent quick-prompt composer plus chronological terminal run cards; no conversational memory
  ─────────────  ──────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────
   Diagnostics    Safe runtime overview everywhere; cached/live attention, Hydra, paths, unload, detailed failures, and capture actions only in trusted-local mode

- Default Analyze task is Faithfulness; default mode is live Generate & score.
- Faithfulness also offers Score supplied answer.
- Answerability accepts only (context, question), invokes no generator, filters to compatible presets, and uses answerability-specific labels.
- Incompatible task/detector combinations remain visible but disabled with a concrete reason.
- Example selection only fills fields; it never runs automatically.
- Curated examples use live generation as the primary action and explicit recorded replay as the secondary action.
- Replay uses the exact server-resolved stored messages, reveals the recorded answer over 0.6–1.5s, and runs detection live. Reduced motion displays the answer immediately.
- Runs automatically records terminal successes, partial results, failures, and catchable interruptions. In-progress activity is not a history row.
- Detection failure after successful generation preserves the answer and offers a new explicit retry action.
- Setup changes never relabel historical results; each run retains its setup snapshot and receives a stale-setup badge where applicable.
- Imported runs are immutable recorded snapshots. Rerun with current setup creates a linked draft/new run and repeats all validation and consent checks.

### Result presentation

- Lead with verdict, detector-typed score, calibration/threshold status, readable answer or evidence, and concise provenance.
- Collapse rationale, raw values, debug information, and detailed method outputs by default.
- Never label an uncalibrated confidence, logit, uncertainty, or probe output as probability.
- Never broadcast a sequence score across tokens or visually imply localization that does not exist.
- Build token/span results from Python-produced ordered text segments whose concatenation exactly equals the answer.
- Name offsets startCodePoint and endCodePoint; React must not slice strings with them because JavaScript uses UTF-16 indexing.
- Make suspect spans keyboard-focusable and provide an equivalent span list containing text, offsets, score kind, value, threshold, and verdict.
- Provide equivalent tables/lists for token heat, claims, multiclass scores, and attention matrices.
- Distinguish Generated now, Recorded answer · live detection, Imported snapshot, Supplied answer · live detection, and Rerun from imported run.
- Describe checksum verification as artifact integrity, never answer truthfulness.

### Visual system

- Use locally bundled Manrope Variable for interface/display text and IBM Plex Mono for scores, hashes, layers, and configuration.
- Use #F7F4F2 canvas, rgba(255,254,252,.94) surfaces, #221B24 ink, #6F6670 muted text, #B91B63 functional brand, #FBE4EF brand wash, #086A60 safe ink, #81520C warning ink, #A52E35 risk ink, and #1B6ED1
  focus.
- Retain a dark theme using #151116 canvas, #211A22 surfaces, #F9F5F7 text, and #FF6BA5 brand.
- Keep the existing silk asset at reduced contrast; text always sits on opaque or contrast-stable surfaces.
- Use a 304px docked setup rail on desktop and an overlay/collapsed rail on tablet.
- Keep Analyze as the demo-like centered single column, capped near 960px, with the result below the inputs rather than beside them.
- Use 44px primary controls, 16px card radii, 10px control radii, and restrained borders/shadows.
- Default to explicit Light + Subtle; preserve Dark, Static, and Lively.
- Add an always-reachable Pause motion action; OS reduced motion overrides every animation choice.
- Use approximately 120–240ms interaction transitions, 220ms shell entrance, 140ms workspace crossfade, and a terminal result reveal completing within about 420ms.
- Formal visual targets are 1920×1080, 1440×900, 1024×768, and 768×1024. A 390px layout must remain functional but is not a formal visual-design target.
- Target WCAG 2.2 AA semantics, contrast, focus, keyboard behavior, status announcements, zoom/reflow, and non-color cues without claiming external certification.

### Runtime, security, and portability

- Treat “shared-safe” as private single-user redaction/resource hardening, not authentication or hostile multi-tenant isolation. Deploy behind authenticated TLS with the raw Streamlit port private.
- Wrap model resolution, load, generation, detection, mutable trace reads, unload, and live diagnostics in one process-wide nonblocking lock. Concurrent work returns Busy; there is no queue.
- Keep the existing ModelManager as the only cache owner: one active model and the existing 0.8 GPU-pressure threshold.
- Keep the existing 30,000 combined detector-character guard and current generation-token ranges.
- Restrict model identifiers to 256 printable characters.
- Disable trust_remote_code for browser-selected models. Trusted-local custom code requires an operator startup allowlist.
- Require explicit confirmation before a remote model download, resolve a commit revision, enforce safetensors/resource metadata caps, and never expose unrestricted local model paths outside trusted-local
  mode.
- Preserve provider-specific keys, per-destination external-call consent, trusted path roots, and server-side capability checks.
- Return sanitized error codes/messages plus correlation IDs; never send raw CUDA/provider errors, stack traces, credentials, environment values, absolute paths, or response bodies to React.
- Render all external content as React text nodes; prohibit dangerouslySetInnerHTML, remote runtime assets, eval, and user-supplied SVG/HTML.
- Make filesystem provenance capture an explicit trusted-local post-run action using server-selected roots, generated filenames, atomic writes, and restrictive permissions.

  Portable formats:

   Format                     Limit and behavior
  ━━━━━━━━━━━━━━━━━━━━━━━━━  ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
   sirin.run, version 1       Plain UTF-8 JSON, maximum 5 MiB, one immutable run
  ─────────────────────────  ──────────────────────────────────────────────────────────────────────────────────────────
   sirin.bundle, version 1    Plain UTF-8 JSON, maximum 10 MiB, maximum 50 runs
  ─────────────────────────  ──────────────────────────────────────────────────────────────────────────────────────────
   Session history            Latest 50 terminal records; session/process loss clears them unless exported or captured

- Use plain JSON, not ZIP or compressed archives.
- Include inputs, visible answer/result, typed evidence, safe setup snapshot, timestamps, hashes, and provenance.
- Exclude secrets, absolute paths, consent state, hidden reasoning, traces, tensors, model objects, Hydra targets, and raw exceptions.
- Canonicalize JSON with sorted keys and finite numeric values, compute SHA-256 excluding the integrity object, and describe a match only as integrity verification.
- Reject duplicate keys, unknown versions/fields, excessive depth, invalid Unicode, non-finite values, invalid spans, ID collisions, and unsupported archive magic.
- Allocate a new local ID for imported runs while retaining sourceRunId and original UTC time.

### Migration sequence

1. Pin streamlit>=1.58,<2, add the package-based v2 component, Node 24 build configuration, lockfile, committed bundle, package data, and clean wheel trigger smoke.
2. Keep the legacy UI intact behind SIRIN_UI_WORKSPACE=legacy|v2; extract only execution, setup validation, result normalization, and example registry seams.
3. Deliver one GPU-free PsiloQA replay through Analyze as the first end-to-end component slice.
4. Migrate all six curated PsiloQA cases and current LongMemEval artifacts with exact hashes and disclosures.
5. Add live generation, supplied-answer scoring, answerability, quick runs, partial failure, and setup revision behavior.
6. Add Runs history, single/bundle import/export, replay links, filtering, and explicit rerun preparation.
7. Convert current cached/live attention tools and trusted-local actions into bounded Diagnostics DTOs and component views.
8. Apply the complete visual, responsive, motion, accessibility, and dark-theme system.
9. Flip v2 to default only after the parity matrix passes; then remove the legacy rendering path, standalone demo app/renderer, duplicate CSS/HTML helpers, and obsolete tests in the same release.
10. Update README.md, docs/ui.md, and the publication runbook; leave deploy/hf-static and verified fixture/media bytes unchanged.

## Test Plan

- Platform gate: clean Node 24 build, committed-bundle consistency, wheel/sdist contents, and clean Python 3.11/3.13 installs that mount the component without Node or network access.
- Contract tests: Python/TypeScript golden fixtures, camelCase aliases, revisions, action receipts, deduplication, stale actions, interruption recovery, unknown fields/versions, JS-safe numbers, and UTC
  timestamps.
- Engine tests: live generation, supplied answer, answerability without generation, quick prompt, exact recorded replay, partial generation, detector failure, OOM, size guard, provider consent, model
  mismatch, and capture warnings.
- Security tests: XSS payloads, malformed Unicode, emoji offsets, duplicate JSON keys, oversized/deep imports, forged actions, secret/path/error redaction, remote-code rejection, model caps, provider URL
  policy, and lock release after exceptions.
- Controller tests: terminal history, 50-run eviction, immutable imports, explicit rerun linkage, setup/runs revisions, download acknowledgment, double-click deduplication, and one-run-plus-Busy
  concurrency.
- Frontend tests: task/mode compatibility, draft retention, Analyze/Runs/Diagnostics navigation, replay timing, all result kinds, provenance labels, keyboard focus, live-region messages, dark theme, Static/
  Lively modes, and reduced motion.
- Streamlit AppTest: app boots without model loading, native setup defaults work, trust capabilities are enforced, and the v2 component mounts under the feature flag.
- Browser acceptance: Playwright plus axe at all formal viewports, 200% zoom, tablet sidebar open/closed, functional 390px fallback, long inputs/results, no page overflow, stable focus after reruns, and no
  serious/critical app-authored accessibility violations.
- Visual/video gate: deterministic Census replay at 1920×1080, stable shell, immediate busy feedback, brief labelled replay type-on, live scoring disclosure, one staged result reveal, preserved geometry,
  and a final state matching the reference’s visual quality rather than pixel identity.
- Optional GPU gate: Qwen3-4B PsiloQA and current LongMem live runs, one resident adapter, correct layer/threshold/provenance, no duplicate model, bounded VRAM, Busy concurrency behavior, unload/reload
  recovery, and answer preservation after detection failure.
- No implementation tests or runtime validation were performed during this planning pass.

## Assumptions and Deferred Work

- The canonical product is the unified general app; the old PsiloQA Streamlit app is removed after parity.
- The static Hugging Face replay deployment remains separate and unchanged.
- Runtime users receive committed frontend assets; Node is build-time only.
- Source/container installation is the delivery target; making the entire repository independently PyPI-publishable is separate packaging work.
- Real browser token streaming and cancellation are not promised in this milestone.
- Formal design support starts at tablet width, with a functional but non-polished phone fallback.
- The current seven presets, provider integrations, attention tools, replay assets, path policy, model reuse, and failure guarantees remain supported.
- Paper-only Compare, agreement/difference panels, context-chunk heat, detailed latency stages, Add Detector documentation, expanded datasets, new memory controls, and multi-model warm pooling remain
  explicitly deferred.
