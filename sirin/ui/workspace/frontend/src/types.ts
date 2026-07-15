export type RunOriginName =
  | "generatedNow"
  | "recordedAnswerLiveDetection"
  | "recordedResultVerified"
  | "importedSnapshot"
  | "suppliedAnswerLiveDetection"
  | "rerunFromImportedRun"
  | "answerabilityLiveDetection"

export type RunModeName =
  | "generateAndScore"
  | "answerability"
  | "scoreSuppliedAnswer"
  | "recordedReplay"
  | "recordedResult"
  | "quickPrompt"

export const RECORDED_RESULT_ORIGIN: RunOriginName = "recordedResultVerified"

// Origin → the honest one-line provenance label. The recorded-result seed is SHA-256 verified but
// its detection did NOT run live, so it must never read as "live detection" (docs/ui.md labelling rule).
export const ORIGIN_LABELS: Record<RunOriginName, string> = {
  generatedNow: "Generated now",
  recordedAnswerLiveDetection: "Recorded answer · live detection",
  recordedResultVerified: "Recorded result · verified — detection not live",
  importedSnapshot: "Imported snapshot",
  suppliedAnswerLiveDetection: "Supplied answer · live detection",
  rerunFromImportedRun: "Rerun from imported run",
  answerabilityLiveDetection: "Answerability · live detection",
}

export type WorkspaceName = "analyze" | "runs" | "diagnostics" | "compare"
export type ThemeName = "light" | "dark"
export type MotionName = "static" | "subtle" | "lively"
export type TaskName = "faithfulness" | "answerability"
export type AnalyzeMode = "generate" | "supplied"

export interface AppearanceState {
  theme: ThemeName
  motion: MotionName
}

export interface AnalyzeDraft {
  task: TaskName
  mode: AnalyzeMode
  exampleId: string | null
  context: string
  question: string
  answer: string
}

export interface ClientDraft {
  analyze: AnalyzeDraft
  quickPrompt: string
}

export interface ActionEnvelope {
  protocolVersion: string | number
  clientInstanceId: string
  sequence: number
  actionId: string
  type: string
  expectedSetupRevision: number
  expectedRunsRevision: number
  payload: Record<string, unknown>
}

export interface WorkspaceFrontendState {
  [key: string]: unknown
  action: ActionEnvelope | null
  draft: ClientDraft | null
  viewState: { workspace?: WorkspaceName; appearance?: AppearanceState }
  appearance: AppearanceState
  selectedRunId: string | null
}

export interface Capability {
  enabled: boolean
  reason?: string | null
}

export interface Capabilities {
  canGenerate?: boolean
  canImport?: boolean
  canExport?: boolean
  trustedLocal?: boolean
  detailedDiagnostics?: boolean
}

export interface SetupSummary {
  detectorPreset?: string
  modelId?: string | null
  providerLabel?: string | null
  detectorLevel?: string
  detectorLabel?: string
  detector?: string
  modelLabel?: string
  model?: string
  device?: string
  layer?: string | number | null
  threshold?: number | null
  detectorFamily?: string
  scoreSemantics?: string
  calibrated?: boolean
}

export interface ExampleRecord {
  id: string
  label: string
  task?: TaskName
  context?: string
  question?: string
  answer?: string
  recordedAnswer?: string
  description?: string
  whyNotable?: string | null
  disabledReason?: string | null
}

export interface TextSegment {
  text: string
  startCodePoint?: number
  endCodePoint?: number
  score?: number | null
  prediction?: boolean | number | string | null
  suspect?: boolean
  label?: string
  verdict?: boolean | null
}

export interface EvidenceSpan {
  text: string
  startCodePoint?: number
  endCodePoint?: number
  score?: number | null
  verdict?: string
  scoreKind?: string
}

export interface ClaimResult {
  text?: string
  claim?: string
  score?: number | null
  verdict?: string | boolean | null
  supported?: boolean
  rationale?: string
}

export interface ClassScore {
  label: string
  score: number
}

export interface ContextChunkScore {
  index: number
  score: number
  chars: [number, number] | number[]
}

export interface AnalysisResult {
  kind?: "sequence" | "token" | "span" | "claim" | "multiclass" | "judge" | "uncertainty" | "unavailable" | string
  verdict?: string | boolean | null
  label?: string
  score?: number | null
  confidence?: number | null
  threshold?: number | null
  scoreSemantics?: string
  scaleLabel?: string | null
  calibrated?: boolean
  summary?: string
  rationale?: string
  segments?: TextSegment[]
  spans?: EvidenceSpan[]
  claims?: ClaimResult[]
  classes?: ClassScore[] | Record<string, number>
  categories?: ClassScore[]
  contextChunkScores?: ContextChunkScore[]
  values?: number[]
  unavailableReason?: string
  note?: string | null
}

// RunRecord.timings (contracts.SafeTimings). Only total_seconds is guaranteed; generation/detection are
// present per stage that actually ran, and exclude_none drops absent fields (recorded seeds ship none).
export interface RunTimings {
  totalSeconds: number
  generationSeconds?: number | null
  detectionSeconds?: number | null
}

export interface RunRecord {
  id: string
  sourceRunId?: string | null
  status: string
  task?: string
  mode?: string
  origin?: string
  title?: string
  createdAt?: string
  completedAt?: string
  context?: string
  question?: string
  prompt?: string
  answer?: string
  verdict?: string | boolean | null
  score?: number | null
  scoreSemantics?: string
  scaleLabel?: string | null
  setup?: SetupSummary
  setupSnapshot?: SetupSummary
  inputs?: { context?: string; question?: string; suppliedAnswer?: string; prompt?: string; exampleId?: string | null }
  analysis?: AnalysisResult
  result?: AnalysisResult
  provenance?: Record<string, unknown>
  timings?: RunTimings
  warnings?: string[]
  error?: { code?: string; message?: string; correlationId?: string } | string | null
  staleSetup?: boolean
  immutable?: boolean
}

export interface ActivityState {
  status?: "idle" | "queued" | "running" | string
  runId?: string
  title?: string
  detail?: string
  stage?: string
  label?: string
}

export interface Notice {
  kind?: "info" | "success" | "warning" | "error" | string
  title?: string
  message: string
  level?: "info" | "warning" | "error"
}

export interface ActionReceipt {
  actionId?: string
  sequence?: number
  status: "accepted" | "rejected" | "duplicate" | string
  message?: string
}

export interface DiagnosticMetric {
  label: string
  value: string | number | boolean | null
  detail?: string
  status?: string
}

export interface AttentionData {
  title?: string
  rowLabels?: string[]
  columnLabels?: string[]
  values?: Array<Array<number | null>>
  note?: string
}

export interface DiagnosticsSummary {
  status?: string
  metrics?: DiagnosticMetric[] | Record<string, unknown>
  warnings?: string[]
  attention?: AttentionData
  details?: Record<string, unknown>
  runtime?: string
  device?: string
  modelLoaded?: boolean
  activeModel?: string | null
  attentionAvailable?: boolean
  message?: string | null
}

export interface DownloadTransfer {
  fileName: string
  mimeType?: string
  content: string
}

export interface DetectorRecipe {
  id: string
  title: string
  description: string
  code: string
  reference?: string | null
}

export interface CompareAgreement {
  both: number
  aOnly: number
  bOnly: number
  neither: number
}

export interface ComparePayload {
  runA?: RunRecord | null
  runB?: RunRecord | null
  presetA?: string | null
  presetB?: string | null
  agreement?: CompareAgreement | null
  agreementNote?: string | null
  deltaScore?: number | null
  deltaNote?: string
}

export interface ReplayTarget {
  exampleId: string
  preset: string
  context: string
  question: string
  answer: string
}

export interface WorkspacePayload {
  protocolVersion: string | number
  serverInstanceId?: string
  setupRevision: number
  runsRevision: number
  capabilities?: Capabilities
  setup?: SetupSummary
  activity?: ActivityState | null
  examples?: ExampleRecord[]
  runs?: RunRecord[]
  selectedRun?: RunRecord | null
  diagnostics?: DiagnosticsSummary | null
  notices?: Notice[]
  actionReceipt?: ActionReceipt | null
  download?: DownloadTransfer | null
  draft?: ClientDraft | null
  compare?: ComparePayload | null
  availablePresets?: string[]
  recipes?: DetectorRecipe[]
  replayTarget?: ReplayTarget | null
  ui?: { title?: string; subtitle?: string }
}
