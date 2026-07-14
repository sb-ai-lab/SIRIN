import type { ChangeEvent, CSSProperties, FormEvent, ReactNode } from "react"
import { useEffect, useId, useRef, useState } from "react"
import { createRoot } from "react-dom/client"
import type { FrontendRenderer } from "@streamlit/component-v2-lib"
import logoUrl from "../../../assets/logo_demo.png"
import emojiNatureUrl from "./assets/fonts/NotoColorEmoji-nature.woff2?url&no-inline"
import emojiObjectsUrl from "./assets/fonts/NotoColorEmoji-objects.woff2?url&no-inline"
import { componentTokenCss } from "./theme"
import "./styles.css"
import { ORIGIN_LABELS, RECORDED_RESULT_ORIGIN } from "./types"
import type {
  ActionEnvelope,
  ActivityState,
  AnalysisResult,
  AnalyzeDraft,
  AppearanceState,
  Capability,
  ClientDraft,
  CompareAgreement,
  ComparePayload,
  ContextChunkScore,
  DetectorRecipe,
  DiagnosticMetric,
  DownloadTransfer,
  ExampleRecord,
  MotionName,
  RunRecord,
  SetupSummary,
  TaskName,
  WorkspaceFrontendState,
  WorkspaceName,
  WorkspacePayload,
} from "./types"

type WorkspaceAnalyzeDraft = AnalyzeDraft & { prompt: string; sourceRunId: string | null }
type WorkspaceClientDraft = Omit<ClientDraft, "analyze"> & { analyze: WorkspaceAnalyzeDraft }
type WorkspaceExample = ExampleRecord & { prompt?: string }
type WorkspaceViewState = { workspace?: WorkspaceName; appearance?: AppearanceState }
type WorkspacePayloadView = WorkspacePayload & { viewState?: WorkspaceViewState }

let emojiFontsRegistered = false

// The design tokens (palette, type scale, fonts) come from the shared sirin/ui/tokens.json source.
// They must be emitted INTO the component's shadow root because it cannot inherit the host :root vars.
function injectComponentTokens(parentElement: HTMLElement | ShadowRoot): void {
  if (parentElement.querySelector(":scope > style[data-sirin-tokens]")) return
  const style = document.createElement("style")
  style.setAttribute("data-sirin-tokens", "")
  style.textContent = componentTokenCss
  parentElement.prepend(style)
}

function registerEmojiFonts(): void {
  if (emojiFontsRegistered || typeof FontFace === "undefined") return
  emojiFontsRegistered = true
  const faces = [
    new FontFace("Noto Color Emoji", `url(${emojiObjectsUrl})`, { style: "normal", weight: "400", unicodeRange: "U+1F9EA" }),
    new FontFace("Noto Color Emoji", `url(${emojiNatureUrl})`, { style: "normal", weight: "400", unicodeRange: "U+1F984" }),
  ]
  for (const face of faces) {
    document.fonts.add(face)
    void face.load().catch(() => document.fonts.delete(face))
  }
}

const DEFAULT_DRAFT: WorkspaceClientDraft = {
  analyze: {
    task: "faithfulness",
    mode: "generate",
    exampleId: null,
    context: "",
    question: "",
    answer: "",
    prompt: "",
    sourceRunId: null,
  },
  quickPrompt: "",
}
const DEFAULT_APPEARANCE: AppearanceState = { theme: "light", motion: "subtle" }

// One-shot result-reveal choreography, mirroring build/lib/sirin/ui/demo_renderer.py: each graded span
// washes in left→right at --d = 240 + i·180ms, its underline draws 200ms later, the badge fades after
// that, and the footer settles once every span has landed (--reveal-total = 240 + n·180 + 400). Revealed
// run ids live at module scope so tab returns and re-renders (which remount the card) never replay it.
const REVEAL_BASE_MS = 240
const REVEAL_STEP_MS = 180
const REVEAL_FOOTER_LAG_MS = 400
const revealedRunIds = new Set<string>()

// Expected, self-explanatory failures the viewer can act on themselves. Their message already tells
// them what to do, so we do not surface a correlation reference — that noise is reserved for the
// unexpected server-side failures (detection_failed, operation_failed) that a log lookup can chase.
const ACTIONABLE_ERROR_CODES = new Set(["consent_required", "busy", "empty_answer", "generation_unavailable", "judge_no_aligned_annotation"])

type Memory = {
  sequence: number
  draft: WorkspaceClientDraft
  workspace: WorkspaceName
  appearance: AppearanceState
  selectedRunId: string | null
  seenDownload: string | null
  focusWorkspace: WorkspaceName | null
}

const memories = new Map<string, Memory>()

function copyDraft(draft: ClientDraft | WorkspaceClientDraft | null | undefined): WorkspaceClientDraft {
  return draft
    ? { analyze: { ...DEFAULT_DRAFT.analyze, ...draft.analyze, prompt: (draft.analyze as WorkspaceAnalyzeDraft).prompt ?? "", sourceRunId: (draft.analyze as WorkspaceAnalyzeDraft).sourceRunId ?? null }, quickPrompt: draft.quickPrompt ?? "" }
    : { analyze: { ...DEFAULT_DRAFT.analyze }, quickPrompt: "" }
}

function clientId(): string {
  const stored = globalThis.sessionStorage?.getItem("sirin.client.id")
  if (stored) return stored
  const id = globalThis.crypto?.randomUUID?.() ?? `client-${Date.now()}-${Math.random().toString(16).slice(2)}`
  globalThis.sessionStorage?.setItem("sirin.client.id", id)
  return id
}

function actionId(): string {
  return globalThis.crypto?.randomUUID?.() ?? `action-${Date.now()}-${Math.random().toString(16).slice(2)}`
}

function enabled(value: boolean | Capability | undefined, fallback = true): boolean {
  if (typeof value === "boolean") return value
  if (value && typeof value === "object") return value.enabled
  return fallback
}

function disabledReason(value: boolean | Capability | undefined): string | undefined {
  return value && typeof value === "object" ? value.reason ?? undefined : undefined
}

function titleCase(value: string | undefined): string {
  if (!value) return "Unavailable"
  return value.replaceAll("_", " ").replaceAll("-", " ").replace(/\b\w/g, (letter) => letter.toUpperCase())
}

// Display label only: the paper calls the task (contextual) hallucination detection, while
// "faithfulness" stays the protocol-v1 wire value inside exports and digests.
function taskLabel(task: string | undefined): string {
  return task === "faithfulness" ? "Hallucination" : titleCase(task)
}

function finite(value: unknown): number | null {
  return typeof value === "number" && Number.isFinite(value) ? value : null
}

function clamp01(value: number): number {
  return Math.min(1, Math.max(0, value))
}

// Demo score format (build/lib/sirin/ui/demo_renderer.py::_score_label): '1.0' at/above .995,
// otherwise two decimals with the leading zero dropped ('.40', '.95').
function formatSpanScore(value: number): string {
  if (value >= 0.995) return "1.0"
  return value.toFixed(2).replace(/^0+/, "")
}

// Continuous ramp between two tokens.json span endpoints. color-mix(in srgb) is the same channel-wise
// sRGB lerp the demo does with lerp_hex, and it resolves the endpoint vars per active theme, so a single
// expression covers light AND dark.
function rampMix(lowVar: string, highVar: string, t: number): string {
  return `color-mix(in srgb, var(${highVar}) ${Math.round(clamp01(t) * 100)}%, var(${lowVar}))`
}

// Probe risk position of a segment on the [τ, 1] ramp. Suspect segments, or any finite score at/above τ,
// are "above" and get the graded wash; a finite score below τ is a faint secondary cue only.
function segmentAbove(score: number | null, verdict: boolean | null | undefined, tau: number | null): boolean {
  return verdict === true || (score !== null && tau !== null && score >= tau)
}

function rampPosition(score: number, tau: number | null): number {
  const base = tau ?? 0
  return clamp01((score - base) / Math.max(1 - base, 1e-6))
}

function scoreText(score: unknown, semantics?: string): string {
  const value = finite(score)
  if (value === null) return "No score"
  if (["calibrated_probability", "calibratedProbability", "categorical_probabilities", "categoricalProbabilities"].includes(semantics ?? "")) return `${Math.round(value * 100)}%`
  return value.toFixed(value < 10 ? 2 : 1)
}

function scoreLabel(semantics?: string, scaleLabel?: string | null): string | null {
  const explicitLabel = scaleLabel?.trim()
  if (explicitLabel) return explicitLabel
  // One honest, distinct sentence per ScoreSemantics (contracts.derive_score_semantics). Never call an
  // uncalibrated score a probability; never imply cross-run comparability a raw score does not have.
  if (["calibrated_probability", "calibratedProbability"].includes(semantics ?? "")) return "calibrated probability"
  if (["relative_within_answer", "relativeWithinAnswer"].includes(semantics ?? "")) return "relative within this answer — not comparable across runs"
  if (["thresholded_raw_score", "thresholdedRawScore"].includes(semantics ?? "")) return "raw score vs decision threshold τ"
  if (["categorical_probabilities", "categoricalProbabilities"].includes(semantics ?? "")) return "class confidence"
  if (["span_agreement", "spanAgreement"].includes(semantics ?? "")) return "judge agreement"
  if (semantics === "verdict") return "verdict"
  return null
}

function riskClass(verdict?: unknown): string {
  if (typeof verdict !== "string") return "neutral"
  const word = verdict.trim().toLowerCase().replaceAll("_", " ").replaceAll("-", " ")
  if (["risk", "suspect", "unsupported", "hallucinated", "hallucination", "failed", "error", "unanswerable", "unsafe"].includes(word)) return "risk"
  if (["safe", "supported", "faithful", "answerable", "passed", "grounded", "healthy"].includes(word)) return "safe"
  return "neutral"
}

function setupValue(setup: SetupSummary | undefined, preferred: keyof SetupSummary, fallback: keyof SetupSummary): string {
  const value = setup?.[preferred] ?? setup?.[fallback]
  return value === null || value === undefined || value === "" ? "Not configured" : String(value)
}

function StatusDot({ status }: { status?: unknown }) {
  return <span className={`status-dot ${riskClass(status)}`} aria-hidden="true" />
}

function Icon({ name }: { name: "analyze" | "runs" | "diagnostics" | "arrow" | "spark" | "download" | "upload" }) {
  const paths: Record<typeof name, ReactNode> = {
    analyze: <><path d="M4 17.5 9 12l3 3 7-8" /><path d="M15 7h4v4" /></>,
    runs: <><path d="M6 5h12M6 12h12M6 19h12" /><path d="M3 5h.01M3 12h.01M3 19h.01" /></>,
    diagnostics: <><path d="M4 14h3l2-7 4 11 2-7h5" /></>,
    arrow: <><path d="m9 18 6-6-6-6" /></>,
    spark: <><path d="m12 3 1.6 4.4L18 9l-4.4 1.6L12 15l-1.6-4.4L6 9l4.4-1.6Z" /><path d="m18 15 .7 2.3L21 18l-2.3.7L18 21l-.7-2.3L15 18l2.3-.7Z" /></>,
    download: <><path d="M12 3v12m-5-5 5 5 5-5" /><path d="M5 21h14" /></>,
    upload: <><path d="M12 21V9m-5 5 5-5 5 5" /><path d="M5 3h14" /></>,
  }
  return <svg className="icon" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.8" strokeLinecap="round" strokeLinejoin="round" aria-hidden="true">{paths[name]}</svg>
}

function ShellHeader({
  workspace,
  onWorkspace,
  setup,
  title,
  subtitle,
}: {
  workspace: WorkspaceName
  onWorkspace: (value: WorkspaceName) => void
  setup?: SetupSummary
  title?: string
  subtitle?: string
}) {
  const [open, setOpen] = useState(false)
  const popoverId = useId()
  useEffect(() => {
    if (!open) return
    const closeOnEscape = (event: KeyboardEvent) => { if (event.key === "Escape") setOpen(false) }
    globalThis.addEventListener("keydown", closeOnEscape)
    return () => globalThis.removeEventListener("keydown", closeOnEscape)
  }, [open])
  return <>
    <header className="shell-header">
      <button className="brand" type="button" onClick={() => onWorkspace("analyze")} aria-label="SIRIN Analyze home">
        <img src={logoUrl} alt="" />
        <span><b>SIRIN</b><small>Honesty, made visible.</small></span>
      </button>
      <nav className="workspace-tabs" aria-label="Workspace">
        {(["analyze", "runs", "diagnostics"] as Array<"analyze" | "runs" | "diagnostics">).map((item) => <button type="button" key={item} data-workspace-tab={item} className={workspace === item ? "active" : ""} aria-current={workspace === item ? "page" : undefined} onClick={() => onWorkspace(item)}><Icon name={item} />{titleCase(item)}</button>)}
      </nav>
      <button className="setup-chip" type="button" onClick={() => setOpen((value) => !value)} aria-expanded={open} aria-controls={popoverId}>
        <span className="setup-summary"><small>Detector</small><b>{setupValue(setup, "detectorPreset", "detectorLabel")}</b></span>
        <Icon name="arrow" />
      </button>
    </header>
    {open && <div className="setup-popover" id={popoverId} role="region" aria-label="Active setup">
      <p className="eyebrow">Active setup</p>
      <dl>
        <div><dt>Detector</dt><dd>{setupValue(setup, "detectorPreset", "detectorLabel")}</dd></div>
        <div><dt>Generator</dt><dd>{setup?.providerLabel ?? setup?.modelId ?? setupValue(setup, "modelLabel", "model")}</dd></div>
        <div><dt>Device</dt><dd>{setup?.device ?? "Automatic"}</dd></div>
        {setup?.layer !== undefined && setup.layer !== null && <div><dt>Layer</dt><dd>{setup.layer}</dd></div>}
        {setup?.threshold !== undefined && setup.threshold !== null && <div><dt>Threshold</dt><dd>{setup.threshold}</dd></div>}
      </dl>
    </div>}
    <section className="page-head">
      <p className="eyebrow">{workspace === "analyze" ? "Evidence workspace" : titleCase(workspace)}</p>
      <h1>{title ?? (workspace === "analyze" ? "See where an answer leaves the evidence." : workspace === "runs" ? "Every result, with its receipts." : workspace === "compare" ? "Two detectors, one answer, side by side." : "Know what SIRIN is running.")}</h1>
      <p>{subtitle ?? (workspace === "analyze" ? "Generate or supply an answer. SIRIN checks it against context and makes uncertainty legible." : workspace === "runs" ? "Review immutable outcomes and carry portable records between sessions." : workspace === "compare" ? "Both detectors score the same answer. Localization overlap is comparable; scores are only compared when their scales are." : "Inspect the active runtime without exposing sensitive internals.")}</p>
    </section>
  </>
}

function Field({ label, hint, children }: { label: string; hint?: string; children: ReactNode }) {
  return <label className="field"><span>{label}{hint && <small>{hint}</small>}</span>{children}</label>
}

// Native <select> kept for a11y/keyboard, wrapped so appearance:none removes OS chrome and a real
// inline-SVG chevron (currentColor, pointer-events:none) replaces the OS arrow in both themes.
function Select({ value, onChange, ariaLabel, children }: { value: string; onChange: (event: ChangeEvent<HTMLSelectElement>) => void; ariaLabel?: string; children: ReactNode }) {
  return <span className="select-wrap"><select value={value} aria-label={ariaLabel} onChange={onChange}>{children}</select><svg className="select-chevron" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.8" strokeLinecap="round" strokeLinejoin="round" aria-hidden="true"><path d="m6 9 6 6 6-6" /></svg></span>
}

function ExampleGallery({ examples, selected, onSelect }: { examples: WorkspaceExample[]; selected: string | null; onSelect: (example: WorkspaceExample) => void }) {
  if (!examples.length) return null
  return <div className="examples"><span>Try an example</span><div className="example-list">{examples.map((example) => <button type="button" key={example.id} disabled={Boolean(example.disabledReason)} title={example.disabledReason ?? example.description} className={selected === example.id ? "selected" : ""} onClick={() => onSelect(example)}>{example.label}</button>)}</div></div>
}

// Honest busy-state staging. The backend Activity DTO (sirin/ui/workspace/contracts.py::Activity) exposes
// only run_id + status and the controller advances queued→running→terminal across reruns, so the card
// surfaces exactly those observable phases and never invents a percentage. The running label is
// specialised from the active run's origin: a generating run reads "Generating…", a supplied/recorded
// answer reads "Scoring…", answerability reads "Checking answerability…".
function describeActivity(activity: ActivityState | null | undefined, runs: RunRecord[]): { label: string; detail: string } {
  const status = activity?.status
  const active = activity?.runId ? runs.find((run) => run.id === activity.runId) : undefined
  const signature = `${active?.origin ?? ""} ${active?.mode ?? ""} ${active?.task ?? ""}`
  if (status === "running") {
    if (/answerability/i.test(signature)) return { label: "Checking answerability…", detail: "Judging whether the question is answerable from the context." }
    if (/generat|quickPrompt/i.test(signature)) return { label: "Generating…", detail: "The model is drafting an answer, then SIRIN scores it against the context." }
    return { label: "Scoring…", detail: "Running the detector over the answer." }
  }
  if (status === "queued") return { label: "Queued…", detail: "Waiting for the runtime to pick up this run." }
  return { label: "Working…", detail: "The result will appear here when the operation finishes." }
}

function ActivityCard({ activity, runs = [] }: { activity?: ActivityState | null; runs?: RunRecord[] }) {
  const { label, detail } = describeActivity(activity, runs)
  return <section className="result-card activity-card" aria-live="polite" aria-busy="true">
    <div className="activity-status"><p className="eyebrow">Working</p><h2>{label}</h2><p>{detail}</p></div>
    <div className="skeleton-lines" aria-hidden="true"><i /><i /><i /><i /></div>
  </section>
}

function ReplayAnswer({ answer, onComplete }: { answer: string; onComplete: () => void }) {
  const complete = useRef(onComplete)
  complete.current = onComplete
  const [shown, setShown] = useState("")
  useEffect(() => {
    setShown("")
    const pieces = answer.match(/\S+\s*/g) ?? [answer]
    let index = 0
    const interval = globalThis.setInterval(() => {
      index += 1
      setShown(pieces.slice(0, index).join(""))
      if (index >= pieces.length) { globalThis.clearInterval(interval); complete.current() }
    }, Math.max(24, Math.min(70, 900 / Math.max(pieces.length, 1))))
    return () => globalThis.clearInterval(interval)
  }, [answer])
  return <p className="answer-copy">{shown}<span className={shown.length < answer.length ? "caret" : "caret hidden"} aria-hidden="true" /></p>
}

// Per-segment risk gradation, matching the recovered demo (demo_renderer.py::_span_html). Above-τ
// segments carry a continuous wash + underline lerped over the tokens.json ramp with a trailing mono
// score badge; the 2px→3px underline step and the numeric badge are non-color channels so evidence never
// relies on color alone (docs/ui.md). τ arrives per result as AnalysisResult.threshold.
function SegmentAnswer({ answer, result }: { answer: string; result: AnalysisResult }) {
  if (!result.segments?.length) return <p className="answer-copy">{answer || "No answer was returned."}</p>
  const tau = finite(result.threshold)
  // Peak = the highest-risk graded span; it carries the Lively single pulse. A verdict-only span (no
  // finite score) reads as top risk. gradedIndex feeds the per-span reveal delay (--d), counting graded
  // spans only so the stagger tracks demo_renderer's 240 + i·180ms regardless of the plain text between.
  const risks = result.segments.map((segment) => {
    const value = finite(segment.score)
    return segmentAbove(value, segment.verdict, tau) ? (value ?? 1) : -1
  })
  const peakIndex = risks.indexOf(Math.max(...risks))
  let gradedIndex = 0
  return <p className="answer-copy segmented">{result.segments.map((segment, index) => {
    const value = finite(segment.score)
    const above = segmentAbove(value, segment.verdict, tau)
    const offsets = segment.startCodePoint !== undefined ? `characters ${segment.startCodePoint}–${segment.endCodePoint}` : "text segment"
    const detail = [offsets, value !== null ? `score ${value.toFixed(2)}` : null, tau !== null ? `τ ${tau.toFixed(3)}` : null, "probe confidence, not calibrated"].filter(Boolean).join(" · ")
    if (above) {
      const t = value !== null ? rampPosition(value, tau) : 1
      const line = rampMix("--span-line-low", "--span-line-high", t)
      // Wash + line ride inline CSS vars (never the `background`/`border-color` shorthands) so the reveal
      // rule can animate background-size and border-bottom-color without clobbering the resolved color-mix.
      const style = { "--seg-wash": rampMix("--span-wash-low", "--span-wash-high", t), "--seg-line": line, borderBottomWidth: t >= 0.5 ? "3px" : "2px", "--d": `${REVEAL_BASE_MS + gradedIndex * REVEAL_STEP_MS}ms` } as CSSProperties
      const className = index === peakIndex ? "evidence graded is-peak" : "evidence graded"
      gradedIndex += 1
      return <span key={`${offsets}-${index}`} className={className} style={style} tabIndex={0} aria-label={`${segment.text}, ${detail}`} title={detail}>{segment.text}{value !== null && <sup className="evidence-badge">{formatSpanScore(value)}</sup>}</span>
    }
    if (value !== null) return <span key={`${offsets}-${index}`} className="evidence below" title={detail}>{segment.text}</span>
    return <span key={`${offsets}-${index}`} className="evidence">{segment.text}</span>
  })}</p>
}

// Per-chunk context heat-bar (PR-11). A long context split into chunks for a sequence detector yields
// one pre-aggregation score per chunk (AnalysisResult.contextChunkScores). The presenter only attaches
// them to sequence/uncertainty results, so this NEVER localizes within the answer — cells are colored by
// each chunk's RANK among the others (min-max within this bar), matching the "relative within answer"
// honesty of an uncalibrated sequence score; the tooltip states the chunk index, raw score, and scale.
function ContextHeatBar({ chunks, semantics }: { chunks: ContextChunkScore[]; semantics?: string }) {
  if (!chunks || chunks.length < 2) return null
  const values = chunks.map((chunk) => finite(chunk.score)).filter((value): value is number => value !== null)
  if (!values.length) return null
  const min = Math.min(...values)
  const span = Math.max(...values) - min
  const label = scoreLabel(semantics) ?? "relative within this answer"
  return <div className="context-heatbar" role="group" aria-label="Per-chunk context scores">
    <span className="context-heatbar-title">Context chunks</span>
    <div className="context-heatbar-cells">
      {chunks.map((chunk, index) => {
        const value = finite(chunk.score)
        const t = value === null || span <= 0 ? 0.5 : clamp01((value - min) / span)
        const detail = `Chunk ${(finite(chunk.index) ?? index) + 1} of ${chunks.length}${value !== null ? ` · score ${value.toFixed(2)}` : ""} · ${label}`
        return <span key={index} className="context-heatbar-cell" style={{ "--seg-wash": rampMix("--span-wash-low", "--span-wash-high", t), "--seg-line": rampMix("--span-line-low", "--span-line-high", t) } as CSSProperties} tabIndex={0} title={detail} aria-label={detail} />
      })}
    </div>
  </div>
}

// Card footer for span-capable results (demo_renderer.py::_footer_html): ramp-colored verdict dot +
// "N suspect spans · max risk X" on the left, and a τ→1.00 gradient risk legend on the right. Replaces
// the sequence-level score orb for span results; the orb is kept only for single-score sequence results.
function SpanFooter({ result }: { result: AnalysisResult }) {
  const tau = finite(result.threshold)
  const above = (result.segments ?? []).filter((segment) => segmentAbove(finite(segment.score), segment.verdict, tau))
  const scores = above.map((segment) => finite(segment.score)).filter((value): value is number => value !== null)
  const maxRisk = scores.length ? Math.max(...scores) : null
  const dotColor = above.length ? rampMix("--span-line-low", "--span-line-high", maxRisk !== null ? rampPosition(maxRisk, tau) : 1) : "var(--span-safe)"
  const verdict = above.length ? `${above.length} suspect ${above.length === 1 ? "span" : "spans"}${maxRisk !== null ? ` · max risk ${maxRisk.toFixed(2)}` : ""}` : "No spans above threshold"
  return <div className="span-footer">
    <div className="span-verdict"><span className="span-verdict-dot" style={{ background: dotColor }} aria-hidden="true" />{verdict}</div>
    <div className="span-legend"><span className="span-legend-word">risk</span>{tau !== null && <span className="span-legend-num">τ&nbsp;{tau.toFixed(2)}</span>}<span className="span-legend-bar" aria-hidden="true" /><span className="span-legend-num">1.00</span></div>
  </div>
}

function EvidenceDetails({ result }: { result: AnalysisResult }) {
  const spans = result.spans?.length ? result.spans : (result.segments ?? []).filter((segment) => segment.verdict === true).map((segment) => ({ text: segment.text, startCodePoint: segment.startCodePoint, endCodePoint: segment.endCodePoint, score: segment.score, scoreKind: result.scoreSemantics, verdict: "suspect" }))
  const classes = result.categories ?? (Array.isArray(result.classes) ? result.classes : Object.entries(result.classes ?? {}).map(([label, score]) => ({ label, score })))
  const hasDetails = Boolean(spans.length || result.claims?.length || classes.length || result.rationale || result.values?.length)
  if (!hasDetails) return null
  return <details className="evidence-details"><summary>Evidence details</summary>
    {spans.length ? <div className="evidence-list" aria-label="Suspect spans">{spans.map((span, index) => <article key={`${span.startCodePoint}-${index}`}><div><b>{span.text}</b><small>{span.startCodePoint !== undefined ? `Characters ${span.startCodePoint}–${span.endCodePoint}` : "Span evidence"}</small></div><span>{finite(span.score) !== null ? formatSpanScore(finite(span.score) as number) : scoreText(span.score, span.scoreKind)} · {span.verdict ?? "scored"}</span></article>)}</div> : null}
    {result.claims?.length ? <div className="claim-list">{result.claims.map((claim, index) => <article key={index} className={riskClass(claim.verdict)}><StatusDot status={claim.supported === true ? "safe" : claim.supported === false ? "risk" : claim.verdict} /><div><b>{claim.text ?? claim.claim ?? `Claim ${index + 1}`}</b>{claim.rationale && <p>{claim.rationale}</p>}</div><span>{claim.verdict ?? scoreText(claim.score)}</span></article>)}</div> : null}
    {classes.length ? <div className="class-list" aria-label="Class scores">{classes.map((item) => <div key={item.label}><span>{titleCase(item.label)}</span><i><b style={{ width: `${Math.max(0, Math.min(100, item.score * 100))}%` }} /></i><strong>{scoreText(item.score, "categorical_probabilities")}</strong></div>)}</div> : null}
    {result.values?.length ? <><div className="mini-bars" aria-hidden="true">{result.values.map((value, index) => <i key={index} style={{ height: `${10 + Math.max(0, Math.min(1, value)) * 54}px` }} />)}</div><ol className="sr-only" aria-label="Relative token scores">{result.values.map((value, index) => <li key={index}>Item {index + 1}: {value.toFixed(3)}</li>)}</ol></> : null}
    {(result.rationale || result.note) && <p className="rationale">{result.rationale ?? result.note}</p>}
  </details>
}

function Provenance({ run }: { run: RunRecord }) {
  const provenance = run.provenance ?? {}
  const recordedResult = run.origin === RECORDED_RESULT_ORIGIN
  // The recorded-result seed carries the trained-probe checkpoint hash; surface it as its own chip so
  // it is always visible, not truncated away behind the three generic provenance entries below.
  const checkpoint = recordedResult && typeof provenance.integritySha256 === "string" ? provenance.integritySha256 : null
  const entries = Object.entries(provenance).filter(([key, value]) => key !== (checkpoint ? "integritySha256" : "") && (typeof value === "string" || typeof value === "number" || typeof value === "boolean"))
  return <div className="provenance">
    <span>{recordedResult ? "Recorded result · verified" : titleCase(run.origin ?? run.mode ?? "live run")}</span>
    {(run.setupSnapshot ?? run.setup) && <span>{setupValue(run.setupSnapshot ?? run.setup, "detectorPreset", "detectorLabel")}</span>}
    {run.staleSetup && <span className="warning">Different setup</span>}
    {run.sourceRunId && <span>Source {run.sourceRunId}</span>}
    {checkpoint && <span title={checkpoint}>Checkpoint {checkpoint.slice(0, 12)}…</span>}
    {entries.slice(0, 3).map(([key, value]) => <span key={key}>{titleCase(key)}: {String(value)}</span>)}
  </div>
}

// Latency strip (RunRecord.timings → contracts.SafeTimings). Renders only the stages the payload
// actually carries, one decimal, mono numerals; stage names are exactly generation/detection/total.
// Recorded-result seeds ship no timings (exclude_none drops the field), so nothing renders.
function LatencyStrip({ timings }: { timings?: RunRecord["timings"] }) {
  if (!timings) return null
  const stages: Array<[string, unknown]> = [["generation", timings.generationSeconds], ["detection", timings.detectionSeconds], ["total", timings.totalSeconds]]
  const parts = stages.map(([stage, value]) => [stage, finite(value)] as const).filter(([, value]) => value !== null)
  if (!parts.length) return null
  return <div className="latency-strip" aria-label="Run latency">{parts.map(([stage, value], index) => <span key={stage}>{index > 0 ? "· " : ""}{stage} <b>{(value as number).toFixed(1)}s</b></span>)}</div>
}

function ResultCard({ run, motion, onAction, onPrepareRerun }: { run: RunRecord; motion: MotionName; onAction: (type: string, payload: Record<string, unknown>) => void; onPrepareRerun: (run: RunRecord) => void }) {
  const result = run.analysis ?? run.result ?? {}
  const semantics = result.scoreSemantics ?? run.scoreSemantics
  const score = result.score ?? result.confidence ?? run.score
  const metricLabel = scoreLabel(semantics, result.scaleLabel ?? run.scaleLabel)
  // Span-capable results (per-segment score or verdict) surface the risk footer instead of the
  // sequence-level score orb, matching the demo card.
  const isSpanResult = (result.segments ?? []).some((segment) => finite(segment.score) !== null || segment.verdict === true)
  const verdictValue = result.verdict ?? run.verdict
  const verdict = result.label ?? (typeof verdictValue === "string" ? verdictValue : null) ?? (run.status === "failed" ? "Failed" : "Result")
  // The recorded-result seed is a settled, verified result — never a live replay. It must NOT take the
  // recorded-answer typewriter or the "live detection" label, even though its origin contains "recorded".
  const recordedResult = run.origin === RECORDED_RESULT_ORIGIN
  const replay = !recordedResult && /replay|recorded/i.test(`${run.origin ?? ""} ${run.mode ?? ""}`)
  const reducedMotion = globalThis.matchMedia?.("(prefers-reduced-motion: reduce)").matches ?? false
  // One-shot: capture at mount whether THIS run id is appearing for the first time ever, then record it.
  // A tab return or re-select remounts the card, finds the id already seen, and renders the fully-settled
  // result with neither the recorded-answer typewriter nor the span reveal replaying.
  const [firstAppearance] = useState(() => {
    const first = !revealedRunIds.has(run.id)
    revealedRunIds.add(run.id)
    return first
  })
  const animate = motion !== "static" && !reducedMotion && firstAppearance
  const stageReplay = replay && animate
  const [replayFinished, setReplayFinished] = useState(!stageReplay)
  // Span cards get the staggered wash reveal on first appearance; Static/reduced-motion withhold .is-reveal
  // so the card renders complete. --reveal-total = 240 + n·180 + 400ms gates the footer's closing fade.
  const tau = finite(result.threshold)
  const gradedCount = (result.segments ?? []).filter((segment) => segmentAbove(finite(segment.score), segment.verdict, tau)).length
  const reveal = isSpanResult && animate
  const revealTotalMs = REVEAL_BASE_MS + gradedCount * REVEAL_STEP_MS + REVEAL_FOOTER_LAG_MS
  const error = typeof run.error === "string" ? run.error : run.error?.message
  const errorDetails = run.error && typeof run.error === "object" ? run.error : null
  return <section className={`result-card ${riskClass(verdictValue ?? verdict)}${reveal ? " is-reveal" : ""}`} style={reveal ? ({ "--reveal-total": `${revealTotalMs}ms` } as CSSProperties) : undefined} aria-live="polite">
    <div className="result-heading">
      <div><p className="eyebrow">Outcome</p><h2>{verdict}</h2><p>{result.summary ?? (run.status === "partial" ? "The answer was preserved, but part of analysis did not complete." : "Evidence is shown in the answer and details below.")}</p></div>
      {!isSpanResult && finite(score) !== null && metricLabel && <div className="score-orb"><strong>{scoreText(score, semantics)}</strong><span>{metricLabel}</span>{["thresholded_raw_score", "thresholdedRawScore"].includes(semantics ?? "") && tau !== null && <small className="decision-band">vs τ&nbsp;{tau.toFixed(2)}</small>}</div>}
    </div>
    <div className="answer-block">
      <div className="answer-label"><span>Answer</span><small>{recordedResult ? ORIGIN_LABELS.recordedResultVerified : replay ? "Recorded answer · live detection" : run.origin === "importedSnapshot" || run.origin === "imported" ? "Imported snapshot" : /answerability/i.test(run.origin ?? run.mode ?? "") ? "Answerability · live detection" : /supplied/i.test(run.origin ?? run.mode ?? "") ? "Supplied answer · live detection" : "Generated now"}</small></div>
      {!isSpanResult && (result.contextChunkScores?.length ?? 0) > 1 && <ContextHeatBar chunks={result.contextChunkScores!} semantics={semantics} />}
      {stageReplay && !replayFinished ? <ReplayAnswer answer={run.answer ?? ""} onComplete={() => setReplayFinished(true)} /> : <><SegmentAnswer answer={run.answer ?? ""} result={result} />{isSpanResult && <SpanFooter result={result} />}</>}
    </div>
    {result.unavailableReason && <div className="inline-notice warning"><b>Analysis unavailable</b><span>{result.unavailableReason}</span></div>}
    {error && <div className="inline-notice error"><b>{run.status === "partial" ? "Detection did not finish" : "Run failed"}</b><span>{error}</span>{errorDetails?.correlationId && !ACTIONABLE_ERROR_CODES.has(errorDetails.code ?? "") && <small>Reference {errorDetails.correlationId}</small>}</div>}
    {run.warnings?.map((warning, index) => <div className="inline-notice warning" key={index}>{warning}</div>)}
    <EvidenceDetails result={result} />
    <Provenance run={run} />
    <LatencyStrip timings={run.timings} />
    <div className="result-actions">
      {recordedResult && run.inputs?.exampleId && <button type="button" className="primary" title="Replays the verified answer and runs the probe live. Loads the model." onClick={() => onAction("submit", { task: "faithfulness", mode: "recordedReplay", context: run.inputs?.context ?? "", question: run.inputs?.question ?? "", suppliedAnswer: run.answer ?? "", prompt: "", exampleId: run.inputs?.exampleId })}><Icon name="spark" />Run it live</button>}
      {(run.status === "partial" || run.status === "failed") && run.answer && <button type="button" className="secondary" onClick={() => onAction("retryDetection", { runId: run.id })}>Retry detection</button>}
      {(run.origin === "importedSnapshot" || run.origin === "imported" || run.immutable) && <button type="button" className="secondary" onClick={() => onPrepareRerun(run)}>Rerun with current setup</button>}
      <button type="button" className="quiet" onClick={() => onAction("exportRun", { runId: run.id })}><Icon name="download" />Export run</button>
    </div>
  </section>
}

function AnalyzeWorkspace({ payload, draft, setDraft, busy, motion, onAction, onPrepareRerun, onCompare }: { payload: WorkspacePayload; draft: WorkspaceAnalyzeDraft; setDraft: (draft: WorkspaceAnalyzeDraft, checkpoint?: boolean) => void; busy: boolean; motion: MotionName; onAction: (type: string, payload: Record<string, unknown>) => void; onPrepareRerun: (run: RunRecord) => void; onCompare: (presetB: string, inputs: Record<string, unknown>) => void }) {
  const capabilities = payload.capabilities ?? {}
  const extendedCapabilities = capabilities as typeof capabilities & { canAnswerability?: boolean | Capability }
  const setupTask = String((payload.setup as (SetupSummary & { task?: TaskName }) | undefined)?.task ?? "faithfulness") as TaskName
  const detectorCapability: boolean | Capability = setupTask === draft.task ? true : { enabled: false, reason: `The active detector supports ${taskLabel(setupTask)}, not ${taskLabel(draft.task)}.` }
  const taskCapability = draft.task === "answerability" ? (extendedCapabilities.canAnswerability ?? detectorCapability) : detectorCapability
  const generationCapability = draft.task === "faithfulness" && draft.mode === "generate" ? capabilities.canGenerate : true
  const hasGroundingInput = draft.prompt.trim().length > 0 || (draft.context.trim().length > 0 && draft.question.trim().length > 0)
  const canSubmit = enabled(taskCapability) && enabled(generationCapability) && hasGroundingInput && (draft.task === "answerability" || draft.mode === "generate" || draft.answer.trim().length > 0)
  const availablePresets = payload.availablePresets ?? []
  const [compareOpen, setCompareOpen] = useState(false)
  const [presetB, setPresetB] = useState("")
  const runComparison = () => {
    const chosen = presetB || availablePresets[0]
    if (!chosen || !canSubmit || busy) return
    onCompare(chosen, {
      task: draft.task,
      context: draft.context,
      question: draft.question,
      suppliedAnswer: draft.mode === "supplied" ? draft.answer : "",
      prompt: draft.prompt,
      exampleId: draft.exampleId,
    })
  }
  const examples = (payload.examples ?? []) as WorkspaceExample[]
  const selectedExample = examples.find((item) => item.id === draft.exampleId)
  const recordedCta = Boolean(selectedExample && (selectedExample.recordedAnswer || selectedExample.answer))
  const chooseExample = (example: WorkspaceExample) => setDraft({
    task: example.task ?? draft.task,
    mode: draft.mode,
    exampleId: example.id,
    context: example.context ?? "",
    question: example.question ?? "",
    answer: example.answer ?? example.recordedAnswer ?? "",
    prompt: example.prompt ?? "",
    sourceRunId: null,
  }, true)
  const submit = (event: FormEvent) => {
    event.preventDefault()
    if (!canSubmit || busy) return
    const mode = draft.task === "answerability" ? "answerability" : draft.sourceRunId && draft.prompt && !draft.context && !draft.question ? "quickPrompt" : draft.mode === "generate" ? "generateAndScore" : "scoreSuppliedAnswer"
    onAction("submit", {
      task: draft.task,
      mode,
      context: draft.context,
      question: draft.question,
      suppliedAnswer: draft.mode === "supplied" ? draft.answer : "",
      prompt: draft.prompt,
      exampleId: draft.exampleId,
      ...(draft.sourceRunId ? { sourceRunId: draft.sourceRunId } : {}),
    })
    if (draft.sourceRunId) setDraft({ ...draft, sourceRunId: null })
  }
  return <main className="workspace-content analyze-workspace">
    <ExampleGallery examples={examples.filter((example) => !example.task || example.task === draft.task)} selected={draft.exampleId} onSelect={chooseExample} />
    <form className="analysis-form" onSubmit={submit}>
      <div className="form-row">
        <Field label="Task"><Select value={draft.task} onChange={(event) => { const task = event.target.value as TaskName; setDraft({ ...draft, task, mode: task === "answerability" ? "generate" : draft.mode }, true) }}><option value="faithfulness" disabled={setupTask !== "faithfulness"}>Hallucination</option><option value="answerability" disabled={!enabled(extendedCapabilities.canAnswerability ?? (setupTask === "answerability"))}>Answerability</option></Select></Field>
        {draft.task === "faithfulness" && <Field label="Answer source"><Select value={draft.mode} onChange={(event) => setDraft({ ...draft, mode: event.target.value as AnalyzeDraft["mode"] }, true)}><option value="generate" disabled={!enabled(capabilities.canGenerate)}>Generate an answer</option><option value="supplied">Score supplied answer</option></Select></Field>}
      </div>
      {draft.prompt && <details className="prompt-disclosure"><summary><svg className="disclosure-chevron" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.8" strokeLinecap="round" strokeLinejoin="round" aria-hidden="true"><path d="m9 18 6-6-6-6" /></svg><span>Exact model prompt</span><span className="disclosure-count">{draft.prompt.length.toLocaleString()} characters</span></summary><Field label="Prompt"><textarea rows={5} value={draft.prompt} placeholder="Verified example or imported prompt…" onChange={(event) => setDraft({ ...draft, prompt: event.target.value, exampleId: null })} onBlur={() => setDraft(draft, true)} /></Field></details>}
      <Field label="Context" hint={`${draft.context.length.toLocaleString()} characters`}><textarea rows={7} value={draft.context} placeholder="Paste the source material the answer must stay grounded in…" onChange={(event) => setDraft({ ...draft, context: event.target.value })} onBlur={() => setDraft(draft, true)} /></Field>
      <Field label="Question"><textarea rows={2} value={draft.question} placeholder="What should the model answer from this context?" onChange={(event) => setDraft({ ...draft, question: event.target.value })} onBlur={() => setDraft(draft, true)} /></Field>
      {draft.task === "faithfulness" && draft.mode === "supplied" && <Field label="Answer to score"><textarea rows={4} value={draft.answer} placeholder="Paste the answer that should be checked…" onChange={(event) => setDraft({ ...draft, answer: event.target.value })} onBlur={() => setDraft(draft, true)} /></Field>}
      {!enabled(taskCapability) && <p className="field-error">{disabledReason(taskCapability) ?? "The active detector does not support this task."}</p>}
      {!enabled(generationCapability) && <p className="field-error">{disabledReason(generationCapability) ?? "Generation is not available with the active setup."}</p>}
      {draft.sourceRunId && <div className="inline-notice info"><b>Imported run prepared</b><span>Review these inputs, then submit explicitly with the current setup.</span></div>}
      <div className="form-actions">
        {/* Scoring/generating is always the pink primary CTA, placed right of the replay button;
            replaying a selected example's verified answer is the secondary path. */}
        {recordedCta && <button type="button" className="secondary" disabled={busy} onClick={() => onAction("submit", { task: selectedExample?.task ?? "faithfulness", mode: "recordedReplay", context: draft.context, question: draft.question, suppliedAnswer: selectedExample?.recordedAnswer ?? selectedExample?.answer ?? "", prompt: "", exampleId: selectedExample?.id })}><Icon name="spark" />Replay recorded answer</button>}
        <button className="primary" type="submit" disabled={!canSubmit || busy}><Icon name="spark" />{draft.task === "answerability" ? "Check answerability" : draft.mode === "supplied" ? "Score answer" : "Generate & score"}</button>
        {/* Compare: side A is the sidebar detector, side B is a preset from the same catalog. Both score
            the SAME answer A produces/receives — the honest, apples-to-apples comparison. */}
        {availablePresets.length > 0 && <button type="button" className="quiet" disabled={busy} aria-expanded={compareOpen} onClick={() => setCompareOpen((value) => !value)}>Compare detectors…</button>}
      </div>
      {compareOpen && availablePresets.length > 0 && <div className="compare-picker">
        <Field label="Second detector (B)" hint="scores the same answer"><Select ariaLabel="Second detector for comparison" value={presetB || availablePresets[0]} onChange={(event) => setPresetB(event.target.value)}>{availablePresets.map((name) => <option key={name} value={name}>{name}</option>)}</Select></Field>
        <button type="button" className="primary" disabled={!canSubmit || busy} onClick={runComparison}><Icon name="spark" />Run comparison</button>
        {!canSubmit && <p className="field-error">Enter a context and question (or an answer to score) first.</p>}
      </div>}
    </form>
    {busy ? <ActivityCard activity={payload.activity} runs={payload.runs ?? []} /> : payload.selectedRun ? <ResultCard key={payload.selectedRun.id} run={payload.selectedRun} motion={motion} onAction={onAction} onPrepareRerun={onPrepareRerun} /> : <section className="result-placeholder"><div><Icon name="spark" /></div><h2>Your evidence map will appear here.</h2><p>Results lead with the outcome, then reveal only the detail each detector can honestly support.</p></section>}
  </main>
}

// Compare mode (PR-8/9). Localization agreement is comparable across ANY detector types, so the
// 4-segment bar always renders when both sides expose per-character verdicts; a numeric Δscore only
// renders when both sides share the one absolute scale (calibrated probability), else the honest note.
function AgreementBar({ agreement }: { agreement: CompareAgreement }) {
  const parts: Array<{ key: string; label: string; count: number; color: string }> = [
    { key: "both", label: "Both flag", count: agreement.both, color: "var(--span-line-high)" },
    { key: "aOnly", label: "A only", count: agreement.aOnly, color: "var(--span-line-low)" },
    { key: "bOnly", label: "B only", count: agreement.bOnly, color: "var(--brand)" },
    { key: "neither", label: "Neither", count: agreement.neither, color: "var(--safe)" },
  ]
  const total = parts.reduce((sum, part) => sum + part.count, 0)
  const denom = total || 1
  const pct = (count: number) => Math.round((count / denom) * 100)
  return <div className="agreement">
    <p className="eyebrow">Localization agreement · {total} characters</p>
    <div className="agreement-bar" role="img" aria-label={parts.map((part) => `${part.label} ${part.count}`).join(", ")}>
      {parts.map((part) => part.count > 0 ? <span key={part.key} style={{ width: `${(part.count / denom) * 100}%`, background: part.color }} title={`${part.label}: ${part.count} (${pct(part.count)}%)`} /> : null)}
    </div>
    <div className="agreement-legend">{parts.map((part) => <span key={part.key}><i style={{ background: part.color }} aria-hidden="true" />{part.label} <b>{part.count}</b> <em>{pct(part.count)}%</em></span>)}</div>
  </div>
}

function CompareVerdict({ compare }: { compare: ComparePayload }) {
  const delta = finite(compare.deltaScore)
  return <section className="compare-verdict">
    {compare.agreement ? <AgreementBar agreement={compare.agreement} /> : <div className="compare-note"><p className="eyebrow">Localization agreement</p><p>{compare.agreementNote ?? "No per-character overlap is available for these detectors."}</p></div>}
    <div className="compare-delta">{delta !== null ? <><span className="compare-delta-value">{delta > 0 ? "+" : ""}{delta.toFixed(2)}</span><span>{compare.deltaNote}</span></> : <span className="compare-note-line">{compare.deltaNote || "Different score scales — localization overlap only."}</span>}</div>
  </section>
}

function CompareColumn({ label, preset, run, motion, onAction, onPrepareRerun }: { label: string; preset?: string | null; run?: RunRecord | null; motion: MotionName; onAction: (type: string, payload: Record<string, unknown>) => void; onPrepareRerun: (run: RunRecord) => void }) {
  const semantics = run?.analysis?.scoreSemantics ?? (run?.setupSnapshot as (SetupSummary & { scoreSemantics?: string }) | undefined)?.scoreSemantics
  const scale = scoreLabel(semantics)
  const busy = run ? ["queued", "running"].includes(run.status) : false
  return <section className="compare-column">
    <header className="compare-col-head"><p className="eyebrow">{label}</p><h3>{preset ?? "Detector"}</h3>{scale && <small>{scale}</small>}</header>
    {!run ? <div className="result-placeholder compact"><h2>Waiting…</h2><p>This side scores the same answer once it is available.</p></div>
      : busy ? <div className="result-placeholder compact"><h2>Scoring…</h2><p>Running this detector over the shared answer.</p></div>
      : <ResultCard key={run.id} run={run} motion={motion} onAction={onAction} onPrepareRerun={onPrepareRerun} />}
  </section>
}

function CompareWorkspace({ payload, motion, onAction, onPrepareRerun, onBack }: { payload: WorkspacePayload; motion: MotionName; onAction: (type: string, payload: Record<string, unknown>) => void; onPrepareRerun: (run: RunRecord) => void; onBack: () => void }) {
  const compare = payload.compare
  return <main className="workspace-content compare-workspace">
    <div className="compare-head"><button type="button" className="quiet" onClick={onBack}>← Back to Analyze</button></div>
    {!compare ? <section className="result-placeholder"><div><Icon name="spark" /></div><h2>No comparison yet.</h2><p>Open “Compare detectors…” in Analyze to score one answer with two detectors side by side.</p></section>
      : <><CompareVerdict compare={compare} /><div className="compare-grid"><CompareColumn label="Detector A" preset={compare.presetA} run={compare.runA} motion={motion} onAction={onAction} onPrepareRerun={onPrepareRerun} /><CompareColumn label="Detector B" preset={compare.presetB} run={compare.runB} motion={motion} onAction={onAction} onPrepareRerun={onPrepareRerun} /></div></>}
  </main>
}

function formatTime(value?: string): string {
  if (!value) return "Time unavailable"
  const date = new Date(value)
  return Number.isNaN(date.valueOf()) ? value : new Intl.DateTimeFormat(undefined, { dateStyle: "medium", timeStyle: "short" }).format(date)
}

function RunList({ runs, selectedId, onSelect, onAnalyze }: { runs: RunRecord[]; selectedId: string | null; onSelect: (run: RunRecord) => void; onAnalyze: () => void }) {
  const [query, setQuery] = useState("")
  const [status, setStatus] = useState("all")
  const filtered = runs.filter((run) => (status === "all" || run.status === status) && `${run.title ?? ""} ${run.question ?? ""} ${run.prompt ?? ""} ${run.answer ?? ""}`.toLowerCase().includes(query.toLowerCase()))
  return <section className="run-browser">
    <div className="section-heading"><div><p className="eyebrow">History</p><h2>{runs.length} {runs.length === 1 ? "run" : "runs"}</h2></div><div className="filters"><input type="search" aria-label="Search runs" value={query} placeholder="Search runs" onChange={(event) => setQuery(event.target.value)} /><Select ariaLabel="Filter runs by status" value={status} onChange={(event) => setStatus(event.target.value)}><option value="all">All outcomes</option><option value="succeeded">Succeeded</option><option value="partial">Partial</option><option value="failed">Failed</option><option value="interrupted">Interrupted</option></Select></div></div>
    <div className="run-list">{filtered.length ? filtered.map((run) => <button type="button" key={run.id} className={selectedId === run.id ? "selected" : ""} onClick={() => onSelect(run)}><StatusDot status={run.status} /><span><b>{run.title ?? run.question ?? run.prompt ?? `Run ${run.id}`}</b><small>{formatTime(run.completedAt ?? run.createdAt)} · {taskLabel(run.task)} · {titleCase(run.status)}</small></span><strong>{typeof run.verdict === "boolean" ? run.task === "answerability" ? run.verdict ? "Answerable" : "Unanswerable" : run.verdict ? "Unsupported" : "Supported" : run.verdict ?? scoreText(run.score, run.scoreSemantics)}</strong><Icon name="arrow" /></button>) : runs.length === 0 ? <div className="empty-list">No runs yet — <button type="button" className="empty-link" onClick={onAnalyze}>analyze a case</button> to get started.</div> : <div className="empty-list">No runs match these filters.</div>}</div>
  </section>
}

function ImportControl({ disabled, onImport }: { disabled: boolean; onImport: (jsonText: string, fileName: string) => void }) {
  const input = useRef<HTMLInputElement>(null)
  const [error, setError] = useState("")
  const pick = async (file?: File) => {
    if (!file) return
    if (file.size > 10 * 1024 * 1024) { setError("Portable bundles must be 10 MiB or smaller."); return }
    setError("")
    onImport(await file.text(), file.name)
    if (input.current) input.current.value = ""
  }
  return <><input ref={input} hidden type="file" accept="application/json,.json" onChange={(event) => void pick(event.target.files?.[0])} /><button type="button" className="secondary" disabled={disabled} onClick={() => input.current?.click()}><Icon name="upload" />Import JSON</button>{error && <span className="field-error" role="alert">{error}</span>}</>
}

function RunsWorkspace({ payload, quickPrompt, setQuickPrompt, selectedId, setSelectedId, busy, motion, onAction, onPrepareRerun, onAnalyze }: { payload: WorkspacePayload; quickPrompt: string; setQuickPrompt: (value: string, checkpoint?: boolean) => void; selectedId: string | null; setSelectedId: (value: string | null) => void; busy: boolean; motion: MotionName; onAction: (type: string, payload: Record<string, unknown>) => void; onPrepareRerun: (run: RunRecord) => void; onAnalyze: () => void }) {
  const runs = payload.runs ?? []
  const selected = payload.selectedRun ?? runs.find((run) => run.id === selectedId) ?? null
  const faithfulnessSetup = String((payload.setup as (SetupSummary & { task?: TaskName }) | undefined)?.task ?? "faithfulness") === "faithfulness"
  return <main className="workspace-content runs-workspace">
    <form className="quick-run" onSubmit={(event) => { event.preventDefault(); if (quickPrompt.trim() && !busy && faithfulnessSetup) onAction("submit", { task: "faithfulness", mode: "quickPrompt", context: "", question: "", suppliedAnswer: "", prompt: quickPrompt, exampleId: null }) }}>
      <div><p className="eyebrow">Quick run</p><h2>Ask without building a thread.</h2><p>Each prompt becomes an independent, auditable run.</p></div>
      <Field label="Prompt"><textarea rows={3} value={quickPrompt} placeholder="Ask the active generator…" onChange={(event) => setQuickPrompt(event.target.value)} onBlur={() => setQuickPrompt(quickPrompt, true)} /></Field>
      <div className="form-actions"><button type="submit" className="primary" title={faithfulnessSetup ? undefined : "Quick Run requires a hallucination detector."} disabled={!quickPrompt.trim() || busy || !enabled(payload.capabilities?.canGenerate) || !faithfulnessSetup}><Icon name="spark" />Run prompt</button><ImportControl disabled={!enabled(payload.capabilities?.canImport)} onImport={(content) => onAction("import", { json: content })} /><button type="button" className="quiet" disabled={!runs.length || !enabled(payload.capabilities?.canExport)} onClick={() => onAction("exportBundle", {})}><Icon name="download" />Export session</button></div>
    </form>
    {busy && <ActivityCard activity={payload.activity} runs={payload.runs ?? []} />}
    <div className="runs-grid">
      <RunList runs={runs} selectedId={selected?.id ?? selectedId} onSelect={(run) => { setSelectedId(run.id); onAction("selectRun", { runId: run.id }) }} onAnalyze={onAnalyze} />
      <aside className="run-detail">{selected ? <ResultCard key={selected.id} run={selected} motion={motion} onAction={onAction} onPrepareRerun={onPrepareRerun} /> : <div className="result-placeholder compact"><h2>Select a run</h2><p>Its outcome, evidence, and provenance will appear here.</p></div>}</aside>
    </div>
  </main>
}

function metricsOf(metrics?: DiagnosticMetric[] | Record<string, unknown>): DiagnosticMetric[] {
  if (!metrics) return []
  return Array.isArray(metrics) ? metrics : Object.entries(metrics).map(([label, value]) => ({ label: titleCase(label), value: typeof value === "object" ? JSON.stringify(value) : value as string | number | boolean | null }))
}

function AttentionTable({ diagnostics }: { diagnostics: WorkspacePayload["diagnostics"] }) {
  const attention = diagnostics?.attention
  if (!attention?.values?.length) return <div className="result-placeholder compact"><h2>No attention summary yet</h2><p>Attention summaries appear here when the active detector captures them.</p></div>
  return <section className="attention-card"><div className="section-heading"><div><p className="eyebrow">Attention</p><h2>{attention.title ?? "Bounded attention summary"}</h2></div></div><div className="table-scroll"><table><thead><tr><th>Token</th>{(attention.columnLabels ?? []).map((label) => <th key={label}>{label}</th>)}</tr></thead><tbody>{attention.values.map((row, rowIndex) => <tr key={rowIndex}><th>{attention.rowLabels?.[rowIndex] ?? rowIndex + 1}</th>{row.map((value, columnIndex) => <td key={columnIndex} style={value === null ? undefined : ({ "--attention": String(Math.max(0, Math.min(1, value))) } as CSSProperties)}><span>{value === null ? "—" : value.toFixed(2)}</span></td>)}</tr>)}</tbody></table></div>{attention.note && <p className="caption">{attention.note}</p>}</section>
}

// "Add a detector" recipes (PR-12). Static, copy-paste starting points sourced from the payload
// (sirin/ui/workspace/recipes.py), so copy edits never touch this component. Rendered as a Diagnostics
// section rather than a fourth top-level tab — developer-facing extension docs sit naturally beside the
// runtime view, and it needs no new routing.
function RecipeCard({ recipe }: { recipe: DetectorRecipe }) {
  const [copied, setCopied] = useState(false)
  const copy = () => {
    globalThis.navigator?.clipboard?.writeText(recipe.code).then(
      () => { setCopied(true); globalThis.setTimeout(() => setCopied(false), 1500) },
      () => {},
    )
  }
  return <article className="recipe-card">
    <div className="recipe-head">
      <div><h3>{recipe.title}</h3><p>{recipe.description}</p></div>
      <button type="button" className="quiet" onClick={copy} aria-label={`Copy the ${recipe.title} snippet`}>{copied ? "Copied" : "Copy"}</button>
    </div>
    {recipe.reference && <p className="recipe-reference">Reference: <code>{recipe.reference}</code></p>}
    <pre className="recipe-code"><code>{recipe.code}</code></pre>
  </article>
}

function AddDetectorRecipes({ recipes }: { recipes: DetectorRecipe[] }) {
  if (!recipes.length) return null
  return <section className="recipes-section">
    <div className="section-heading"><div><p className="eyebrow">Extend</p><h2>Add a detector</h2><p>Copy-paste starting points — each snippet is real SIRIN API you can adapt.</p></div></div>
    <div className="recipe-list">{recipes.map((recipe) => <RecipeCard key={recipe.id} recipe={recipe} />)}</div>
  </section>
}

function DiagnosticsWorkspace({ payload, busy, onAction }: { payload: WorkspacePayload; busy: boolean; onAction: (type: string, payload: Record<string, unknown>) => void }) {
  const diagnostics = payload.diagnostics
  const capabilities = (payload.capabilities ?? {}) as NonNullable<WorkspacePayload["capabilities"]> & { canRefreshDiagnostics?: boolean | Capability; canOpenCachedAttention?: boolean | Capability; canOpenLiveAttention?: boolean | Capability; canUnloadModels?: boolean | Capability }
  const metrics = diagnostics?.metrics ? metricsOf(diagnostics.metrics) : [
    { label: "Runtime", value: diagnostics?.runtime ?? "Python" },
    { label: "Device", value: diagnostics?.device ?? "Loads on first run" },
    { label: "Model", value: diagnostics?.activeModel ?? (diagnostics?.modelLoaded ? "Loaded" : "Loads on first run") },
    { label: "Attention", value: diagnostics?.attentionAvailable ? "Available" : "Not captured in this mode" },
  ]
  const trusted = Boolean(payload.capabilities?.trustedLocal)
  return <main className="workspace-content diagnostics-workspace">
    {!trusted && <div className="privacy-banner"><div><b>Shared-safe diagnostics</b><span>Sensitive paths, traces, provider responses, and raw runtime errors remain hidden.</span></div></div>}
    {busy && <ActivityCard activity={payload.activity} runs={payload.runs ?? []} />}
    {trusted && (enabled(capabilities.canRefreshDiagnostics, false) || enabled(capabilities.canOpenCachedAttention, false) || enabled(capabilities.canOpenLiveAttention, false) || enabled(capabilities.canUnloadModels, false)) && <div className="diagnostic-actions">
      {enabled(capabilities.canRefreshDiagnostics, false) && <button type="button" className="secondary" disabled={busy} onClick={() => onAction("refreshDiagnostics", {})}>Refresh runtime</button>}
      {enabled(capabilities.canOpenCachedAttention, false) && <button type="button" className="secondary" disabled={busy} onClick={() => onAction("openCachedAttention", {})}>Cached attention explorer</button>}
      {enabled(capabilities.canOpenLiveAttention, false) && <button type="button" className="secondary" disabled={busy} onClick={() => onAction("openLiveAttention", {})}>Live attention capture</button>}
      {enabled(capabilities.canUnloadModels, false) && <button type="button" className="quiet" disabled={busy} onClick={() => onAction("unloadModels", {})}>Unload models</button>}
    </div>}
    <section className="metric-grid">{metrics.length ? metrics.map((metric) => <article key={metric.label} className={riskClass(metric.status)}><span>{metric.label}</span><strong>{metric.value === null ? "Not captured in this mode" : String(metric.value)}</strong>{metric.detail && <small>{metric.detail}</small>}</article>) : <article><span>Runtime status</span><strong>{diagnostics?.status ?? "Ready"}</strong><small>Refresh to request a safe server summary.</small></article>}</section>
    {diagnostics?.message && <div className="inline-notice info">{diagnostics.message}</div>}
    <AttentionTable diagnostics={diagnostics} />
    {trusted && diagnostics?.details && <details className="diagnostic-details"><summary>Trusted-local details</summary><dl>{Object.entries(diagnostics.details).map(([key, value]) => <div key={key}><dt>{titleCase(key)}</dt><dd>{typeof value === "object" ? JSON.stringify(value) : String(value)}</dd></div>)}</dl></details>}
    <AddDetectorRecipes recipes={payload.recipes ?? []} />
  </main>
}

function saveDownload(download: DownloadTransfer): boolean {
  try {
    const url = URL.createObjectURL(new Blob([download.content], { type: download.mimeType ?? "application/json" }))
    const anchor = document.createElement("a")
    anchor.href = url
    anchor.download = download.fileName
    anchor.click()
    URL.revokeObjectURL(url)
    return true
  } catch {
    // The backend remains authoritative for transfer validity; malformed data is ignored.
    return false
  }
}

function WorkspaceApp({ componentKey, payload, setStateValue, setTriggerValue }: { componentKey: string; payload: WorkspacePayload; setStateValue: (name: keyof WorkspaceFrontendState, value: WorkspaceFrontendState[keyof WorkspaceFrontendState]) => void; setTriggerValue: (name: keyof WorkspaceFrontendState, value: WorkspaceFrontendState[keyof WorkspaceFrontendState]) => void }) {
  const viewState = (payload as WorkspacePayloadView).viewState
  const remembered = memories.get(componentKey) ?? { sequence: 0, draft: copyDraft(payload.draft), workspace: viewState?.workspace ?? "analyze" as WorkspaceName, appearance: viewState?.appearance ?? DEFAULT_APPEARANCE, selectedRunId: null, seenDownload: null, focusWorkspace: null }
  if (!memories.has(componentKey)) memories.set(componentKey, remembered)
  const [workspace, setWorkspaceLocal] = useState(remembered.workspace)
  const [appearance, setAppearanceLocal] = useState(remembered.appearance)
  const [draft, setDraftLocal] = useState(remembered.draft)
  const [selectedRunId, setSelectedRunIdLocal] = useState(remembered.selectedRunId)
  const [optimisticBusy, setOptimisticBusy] = useState(false)
  const workspaceRootRef = useRef<HTMLDivElement>(null)
  const latestReceipt = payload.actionReceipt?.sequence
  useEffect(() => setOptimisticBusy(false), [latestReceipt, payload.activity?.status, payload.runsRevision])
  useEffect(() => {
    if (viewState?.workspace && viewState.workspace !== remembered.workspace) { remembered.workspace = viewState.workspace; setWorkspaceLocal(viewState.workspace) }
    if (viewState?.appearance && (viewState.appearance.theme !== remembered.appearance.theme || viewState.appearance.motion !== remembered.appearance.motion)) { remembered.appearance = viewState.appearance; setAppearanceLocal(viewState.appearance) }
  }, [viewState?.workspace, viewState?.appearance?.theme, viewState?.appearance?.motion, remembered])
  useEffect(() => {
    // Components v2 renders into a shadow root of the HOST document, so the host silk layer can be
    // switched synchronously via html[data-sirin-motion] instead of waiting a full server round-trip.
    // Server state stays canonical: the transient appearance event still reconciles on the next rerun,
    // and the host CSS prefers-reduced-motion kill-switch overrides this dataset either way.
    document.documentElement.dataset.sirinMotion = appearance.motion
  }, [appearance.motion])
  useEffect(() => {
    const focusWorkspace = remembered.focusWorkspace
    if (!focusWorkspace || viewState?.workspace !== focusWorkspace) return
    const tab = workspaceRootRef.current?.querySelector<HTMLButtonElement>(`[data-workspace-tab="${focusWorkspace}"]`)
    if (tab) { tab.focus(); remembered.focusWorkspace = null }
  }, [viewState?.workspace, remembered])
  useEffect(() => {
    if (!payload.download) { remembered.seenDownload = null; return }
    const downloadKey = payload.download ? `${payload.download.fileName}:${payload.download.content.length}` : null
    if (payload.download && downloadKey !== remembered.seenDownload) {
      remembered.seenDownload = downloadKey
      if (saveDownload(payload.download)) {
        remembered.sequence += 1
        const acknowledgement: ActionEnvelope = { protocolVersion: payload.protocolVersion, clientInstanceId: clientId(), sequence: remembered.sequence, actionId: actionId(), type: "clearDownload", expectedSetupRevision: payload.setupRevision, expectedRunsRevision: payload.runsRevision, payload: {} }
        setTriggerValue("action", acknowledgement)
      }
    }
  }, [payload.download, payload.protocolVersion, payload.setupRevision, payload.runsRevision, remembered, setTriggerValue])
  const busy = optimisticBusy || ["queued", "running"].includes(payload.activity?.status ?? "")
  const setWorkspace = (value: WorkspaceName) => { remembered.workspace = value; remembered.focusWorkspace = value; setWorkspaceLocal(value); setTriggerValue("viewState", { workspace: value, appearance: remembered.appearance }) }
  const setAnalyzeDraft = (analyze: WorkspaceAnalyzeDraft, checkpoint = false) => { const next = { ...draft, analyze }; remembered.draft = next; setDraftLocal(next); if (checkpoint) setStateValue("draft", next) }
  const setQuickPrompt = (quickPrompt: string, checkpoint = false) => { const next = { ...draft, quickPrompt }; remembered.draft = next; setDraftLocal(next); if (checkpoint) setStateValue("draft", next) }
  const setSelectedRunId = (value: string | null) => { remembered.selectedRunId = value; setSelectedRunIdLocal(value); setStateValue("selectedRunId", value) }
  const prepareRerun = (run: RunRecord) => {
    const inputs = run.inputs ?? {}
    const task = ((run.setupSnapshot as (SetupSummary & { task?: TaskName }) | undefined)?.task ?? run.task ?? "faithfulness") as TaskName
    const analyze: WorkspaceAnalyzeDraft = { task, mode: inputs.suppliedAnswer ? "supplied" : "generate", exampleId: null, context: inputs.context ?? "", question: inputs.question ?? "", answer: inputs.suppliedAnswer ?? "", prompt: inputs.prompt ?? "", sourceRunId: run.id }
    setAnalyzeDraft(analyze, true)
    setWorkspace("analyze")
  }
  const emit = (type: string, actionPayload: Record<string, unknown>) => {
    if (busy) return
    remembered.sequence += 1
    const envelope: ActionEnvelope = { protocolVersion: payload.protocolVersion, clientInstanceId: clientId(), sequence: remembered.sequence, actionId: actionId(), type, expectedSetupRevision: payload.setupRevision, expectedRunsRevision: payload.runsRevision, payload: actionPayload }
    setOptimisticBusy(!["selectRun"].includes(type))
    setTriggerValue("action", envelope)
  }
  // Compare opens its own workspace optimistically (so the client's viewState trigger reflects it and
  // survives the action rerun) and fires runCompare in the same click.
  const startCompare = (presetB: string, inputs: Record<string, unknown>) => {
    setWorkspace("compare")
    emit("runCompare", { inputs, presetB })
  }
  const notices = payload.notices ?? []
  return <div ref={workspaceRootRef} className="sirin-workspace" data-theme={appearance.theme} data-motion={appearance.motion}>
    <div className="shell">
      <ShellHeader workspace={workspace} onWorkspace={setWorkspace} setup={payload.setup} title={payload.ui?.title} subtitle={payload.ui?.subtitle} />
      {notices.length > 0 && <div className="notice-stack" aria-live="polite">{notices.map((notice, index) => <div className={`inline-notice ${notice.level ?? notice.kind ?? "info"}`} key={index}>{notice.title && <b>{notice.title}</b>}<span>{notice.message}</span></div>)}</div>}
      {payload.actionReceipt?.status === "rejected" && <div className="inline-notice error receipt" role="alert"><b>Action rejected</b><span>{payload.actionReceipt.message ?? "The request could not be accepted."}</span></div>}
      {workspace === "analyze" && <AnalyzeWorkspace payload={payload} draft={draft.analyze} setDraft={setAnalyzeDraft} busy={busy} motion={appearance.motion} onAction={emit} onPrepareRerun={prepareRerun} onCompare={startCompare} />}
      {workspace === "runs" && <RunsWorkspace payload={payload} quickPrompt={draft.quickPrompt} setQuickPrompt={setQuickPrompt} selectedId={selectedRunId} setSelectedId={setSelectedRunId} busy={busy} motion={appearance.motion} onAction={emit} onPrepareRerun={prepareRerun} onAnalyze={() => setWorkspace("analyze")} />}
      {workspace === "compare" && <CompareWorkspace payload={payload} motion={appearance.motion} onAction={emit} onPrepareRerun={prepareRerun} onBack={() => setWorkspace("analyze")} />}
      {workspace === "diagnostics" && <DiagnosticsWorkspace payload={payload} busy={busy} onAction={emit} />}
      <footer><span>SIRIN — <a href="https://github.com/sb-ai-lab/SIRIN" target="_blank" rel="noreferrer">github.com/sb-ai-lab/SIRIN</a></span><span>Detector confidence is not automatically a calibrated probability.</span></footer>
    </div>
  </div>
}

type ReactRoot = ReturnType<typeof createRoot>
type RootEntry = { container: HTMLElement; root: ReactRoot }

// Streamlit re-invokes this renderer with the SAME parentElement (the component's shadow root) on
// every payload. Persisting one React root per parentElement lets each new payload reconcile in
// place; the visible tab/theme flash was caused by unmounting and rebuilding the whole tree on
// every rerun.
const rootsByParent = new WeakMap<HTMLElement | ShadowRoot, RootEntry>()

// `memories` is keyed by Streamlit's frontend component key and outlives the React tree so a
// remount can recover a draft. This sibling map pairs each key with its live container so
// disconnected instances can be evicted — bounding growth and clearing the element-replacement
// edge case where Streamlit swaps out the shadow root.
const memoryContainers = new Map<string, HTMLElement>()

function evictDeadMemories(keepKey: string): void {
  for (const [key, container] of memoryContainers) {
    if (key !== keepKey && !container.isConnected) {
      memories.delete(key)
      memoryContainers.delete(key)
    }
  }
}

const renderer: FrontendRenderer<WorkspaceFrontendState, WorkspacePayload> = ({ data, key, parentElement, setStateValue, setTriggerValue }) => {
  registerEmojiFonts()
  injectComponentTokens(parentElement)
  let entry = rootsByParent.get(parentElement)
  if (entry && (!entry.container.isConnected || entry.container.parentNode !== parentElement)) {
    // A rerun replaced the container inside this shadow root, so its root is orphaned.
    try {
      entry.root.unmount()
    } catch {
      // The detached tree may already be gone; discarding the dead entry is enough.
    }
    entry.container.remove()
    rootsByParent.delete(parentElement)
    entry = undefined
  }
  if (!entry) {
    parentElement.querySelectorAll<HTMLElement>(".sirin-component-root").forEach((stray) => stray.remove())
    const container = document.createElement("div")
    container.className = "sirin-component-root"
    parentElement.append(container)
    entry = { container, root: createRoot(container) }
    rootsByParent.set(parentElement, entry)
  }
  memoryContainers.set(key, entry.container)
  evictDeadMemories(key)
  const activeEntry = entry
  activeEntry.root.render(<WorkspaceApp componentKey={key} payload={data} setStateValue={setStateValue} setTriggerValue={setTriggerValue} />)
  return () => {
    if (rootsByParent.get(parentElement) !== activeEntry) return
    rootsByParent.delete(parentElement)
    if (memoryContainers.get(key) === activeEntry.container) memoryContainers.delete(key)
    activeEntry.root.unmount()
    activeEntry.container.remove()
  }
}

export default renderer
