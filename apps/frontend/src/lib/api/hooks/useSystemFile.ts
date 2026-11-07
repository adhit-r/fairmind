'use client'

import { useCallback, useEffect, useState } from 'react'
import { useOrg } from '@/context/OrgContext'
import { evaluationScopeKey, readEvaluationScopeState, writeEvaluationScopeState, type EvaluationScopeState } from '@/lib/evaluation-scope-state'
import { apiClient, type ApiResponse } from '../api-client'

const GOV = '/api/v1/ai-governance'

export type StageKey = 'onboard' | 'assess' | 'govern' | 'remediate' | 'operate'

export interface LifecycleSummary {
  stage: StageKey
  readiness: number
  failedControls: number
  criticalBlockers: number
  missingEvidence: number
  openRisks: number
  activeRemediation: number
  approvalStatus: string | null
}

export interface SystemRecord {
  id: string
  workspaceId: string
  name: string
  owner: string | null
  riskTier: 'low' | 'medium' | 'high' | 'critical'
  lifecycleStage: StageKey
  metadata: Record<string, any>
  createdAt: string
  updatedAt: string
  readiness: number
  lifecycleSummary: LifecycleSummary
  /** The confirmed tier and frameworks; null until a person confirms them. */
  applicability?: import('./useApplicability').ApplicabilityRecord | null
}

export interface EvidenceSummary {
  totalEvidence: number
  linkedEvidence: number
  averageConfidence: number
  highConfidenceEvidence: number
  evidenceTypes: string[]
  workflowState: string
  decisionReadiness: 'empty' | 'collected' | 'linked' | 'review_ready' | 'needs_evidence'
  missingSignals: string[]
  recommendedNextStep: string
}

export interface ApprovalRequestRecord {
  id: string
  status: string
  requestedBy?: string | null
  currentStep?: string | null
  decisionNotes?: string | null
  createdAt?: string
  updatedAt?: string
}

export interface ApprovalStatus {
  systemId: string
  request: ApprovalRequestRecord | null
  decisions: Array<{ id: string; decision: string; decidedBy?: string | null; notes?: string | null; createdAt?: string }>
}

export interface RemediationStatus {
  tasks: Array<{ id: string; title: string; status: string; priority: string; dueDate: string | null }>
  summary: { activeTasks: number; byStatus?: Record<string, number>; byPriority?: Record<string, number> }
}

export interface RiskStatus {
  risks: Array<{ id: string; title?: string; severity: string; status: string; source?: string | null }>
  suggested: Array<{ id: string; title: string; severity: string; source: string }>
  summary: { total: number; open: number; automated: number; suggested: number; bySeverity: Record<'low' | 'medium' | 'high' | 'critical', number> }
}

export interface AuditReport {
  id: string
  reportType: string
  title: string
  createdAt: string
}

export interface GateCheck {
  key: 'fairness' | 'data_governance' | 'human_oversight' | 'monitoring' | 'environmental'
  label: string
  state: 'proven' | 'attested' | 'open'
  confidence: number
  evidenceId: string | null
  detail: { all_checks_pass?: boolean | null; rows?: number; attributes?: string[] } | null
}

export interface ReleaseGate {
  verdict: 'go' | 'conditional_go' | 'no_go'
  confidence: number
  band: 'measured' | 'estimated' | 'unknown'
  checks: GateCheck[]
  reasons: string[]
  proven: number
  attested: number
  open: number
  /** Published policy rules that fail for this system once released. */
  policy?: { blocking: PolicyRuleFailure[]; warnings: PolicyRuleFailure[] }
  /** How the verdict was reached: the tier it was computed on and that tier's row of the decision matrix. */
  explain?: GateExplain
  /** The cheapest steps FairMind can record that move the verdict up, worked out by the gate itself. */
  path?: GatePath
}

export type Verdict = ReleaseGate['verdict']

export interface GateExplain {
  tier: string
  effectiveTier: SystemRecord['riskTier']
  impact: 'low' | 'medium' | 'high'
  tierNote: string | null
  tierSource: {
    suggestedTier: SystemRecord['riskTier']
    ruleIds: string[]
    confirmedBy: string
    confirmedAt: string
    tierBelowSuggestion: boolean
    overrideAcceptedBy: string | null
  } | null
  perCheck: number
  row: Array<{ band: ReleaseGate['band']; from: number; to: number | null; verdict: Verdict }>
}

export interface GatePathStep {
  check: GateCheck['key']
  action: 'fairness_run' | 'environmental_assessment' | 'monitoring_snapshot' | 'attest' | 'evidence_upload'
  evidenceClass: 'measured' | 'tool_estimated' | 'manual'
  counts: number
  gain: number
  note: string | null
}

export interface GatePathOption {
  kind: 'measured_first' | 'attestations'
  steps: GatePathStep[]
  confidenceAfter: number
  verdictAfter: Verdict
  approvalReady: boolean
}

export interface GatePath {
  target: 'go' | 'conditional_go' | null
  options: GatePathOption[]
  /** The shortest route to Go when Go is reachable; null when it is not, or when a warning-level policy rule caps the verdict. */
  toGo?: GatePathOption | null
  ceiling: { confidence: number; verdict: Verdict }
  notes: string[]
  approvalBlockers: Array<{ key: string; text: string; met: boolean }>
}

export interface PolicyRuleFailure {
  policyId: string
  policyName: string
  ruleId: string
  ruleTitle: string
  detail: string
}

export interface FairnessRunSummary {
  evidenceId: string
  title: string
  rows: number | null
  allChecksPass: boolean | null
  /** passedOnSignificance: checks that pass with the value past its threshold, because the difference is not significant. */
  attributes: Array<{ attribute: string; disparateImpactRatio: number; checks: Record<string, boolean>; passedOnSignificance: string[] }>
  confidence: number
  createdAt: string
}

/** One measured metric: the value, its threshold, and the permutation test that decides whether a crossing counts. */
export interface FairnessMetric {
  value: number
  confidence_interval: [number, number]
  is_fair: boolean
  threshold: number
  crosses_threshold: boolean
  significant: boolean
  p_value: number
  alpha: number
}

export interface CsvInspection {
  rows: number
  columns: Array<{
    name: string
    dtype: string
    distinct: number
    sample: string[]
    /** ground: the one ground this column covers when ticked, by the server's name and value checks. */
    attribute: { status: 'suggested' | 'possible' | 'too_many_values' | null; basis: string | null; ground: string | null }
  }>
  suggested: { outcome: string | null; prediction: string | null; score: string | null; attributes: string[] }
  /** SHA-256 of the uploaded bytes; a confirmed run sends it back so the server can refuse a changed file. */
  fileSha256: string
  attributeSource: 'inferred' | 'confirmed' | 'none'
  confirmedBy: string | null
  confirmedAt: string | null
  /** The reused attributes come from a run nobody confirmed (older, or sent through the API). */
  previousRunUnconfirmed: boolean
  needsBinning: Array<{ name: string; distinct: number }>
  uncoveredGrounds: string[]
}

/** What the person confirmed with the mapping; the server records it and checks the reasons. */
export interface AttributeConfirmation {
  sha256: string
  removalReason?: string
  uncoveredReason?: string
}

export interface FairnessMapping {
  outcome: string
  prediction?: string
  score?: string
  attributes: string[]
  favorableLabel?: string
}

export interface FairnessRunResult {
  runId: string
  evidenceId: string
  title: string
  result: {
    rows: number
    all_checks_pass: boolean
    smallest_group: number | null
    evidence_confidence: number
    /** alpha: the significance level after the Bonferroni split over `tests` checks. */
    thresholds: { disparate_impact_ratio: number; gap: number; alpha: number; tests: number }
    attributes: Array<{
      attribute: string
      groups: Record<string, number>
      selection_rates: Record<string, number>
      disparate_impact_ratio: number
      disparate_impact: FairnessMetric
      demographic_parity: FairnessMetric
      equal_opportunity: FairnessMetric
      equalized_odds: FairnessMetric
      calibration: FairnessMetric | null
      checks: Record<string, boolean>
      small_groups: string[]
    }>
  }
  /** What the server recorded as confirmed; notTested is the grounds no confirmed attribute covers. */
  confirmation: { confirmed: boolean; by: string | null; at: string | null; attributes: string[]; notTested: string[] } | null
  gate: ReleaseGate
}

export interface MonitoringRunSummary {
  evidenceId: string
  title: string
  rows: number | null
  allChecksPass: boolean | null
  overallPsi: number | null
  attributes: Array<{ attribute: string; disparateImpactRatio: number; maxRateDrift: number | null; worstPsi: number | null; checks: Record<string, boolean> }>
  confidence: number
  createdAt: string
}

export interface MonitoringMapping {
  prediction?: string
  score?: string
  attributes: string[]
}

export interface MonitoringPolicy {
  cadenceHours: number
  driftWindow: number
  updatedBy: string | null
  updatedAt: string | null
  isDefault: boolean
}

export interface MonitoringWatch {
  policy: MonitoringPolicy
  consecutiveDrifting: number
  findingId: string | null
  findingOpened: boolean
}

export interface MonitoringRunResult {
  evidenceId: string
  title: string
  watch: MonitoringWatch
  result: {
    rows: number
    all_checks_pass: boolean
    overall_psi: number | null
    evidence_confidence: number
    baseline: { present: boolean; rows: number | null }
    thresholds: { disparate_impact_ratio: number; rate_drift: number; psi_moderate: number; psi_significant: number }
    attributes: Array<{
      attribute: string
      groups: Record<string, number>
      selection_rates: Record<string, number>
      baseline_selection_rates: Record<string, number>
      rate_drift: Record<string, number>
      max_rate_drift: number | null
      disparate_impact_ratio: number
      psi_by_group: Record<string, number | null>
      worst_psi: number | null
      checks: Record<string, boolean>
    }>
  }
  gate: ReleaseGate
}

export interface DecisionSeal {
  id: string
  requestId: string
  decision: 'approved' | 'rejected'
  chainHead: string
  evidenceCount: number
  gate: { verdict?: string; confidence?: number }
  sealedBy: string | null
  createdAt: string
  verification: { status: 'intact' | 'broken'; changed: string[]; missing: string[]; addedSince: number }
}

export interface ClauseMapFramework {
  key: string
  name: string
  counts: { proven: number; attested: number; open: number; total: number }
  clauses: Array<{
    key: string
    control: string
    title: string
    group: string | null
    state: 'proven' | 'attested' | 'open'
    checks: Array<{ check: string; label: string; state: 'proven' | 'attested' | 'open'; confidence: number; evidenceId: string | null; relation: string }>
  }>
}

export interface ClauseMap {
  verdict: string | null
  confidence: number | null
  frameworks: ClauseMapFramework[]
  /** True when the map is limited to the frameworks confirmed for this system. */
  scoped?: boolean
  /** The confirmed frameworks, including any with no clause mapped to a gate check. */
  confirmed?: Array<{ key: string; name: string }>
}

/** Environmental is not attested from the UI: an attestation would shadow any later assessment. */
export type AttestableCheck = 'data_governance' | 'human_oversight' | 'monitoring'

export interface SystemFile {
  system: SystemRecord | null
  evidence: EvidenceSummary | null
  approval: ApprovalStatus | null
  remediation: RemediationStatus | null
  risks: RiskStatus | null
  reports: AuditReport[]
  gate: ReleaseGate | null
  fairnessRuns: FairnessRunSummary[]
  monitoringRuns: MonitoringRunSummary[]
  monitoringPolicy: MonitoringPolicy | null
  seals: DecisionSeal[]
  clauseMap: ClauseMap | null
}

function unwrap<T>(res: ApiResponse<T>, fallback: T): T {
  return res.success && res.data !== undefined ? res.data : fallback
}

export interface SystemFileView {
  file: SystemFile
  loading: boolean
  error: string | null
}
/** System file state keyed by organisation and system. */
export type SystemFileState = EvaluationScopeState<SystemFileView>

const EMPTY_FILE: SystemFile = { system: null, evidence: null, approval: null, remediation: null, risks: null, reports: [], gate: null, fairnessRuns: [], monitoringRuns: [], monitoringPolicy: null, seals: [], clauseMap: null }
const PENDING: SystemFileView = { file: EMPTY_FILE, loading: true, error: null }

export const systemFileScopeKey = (organizationId: string | null | undefined, systemId: string | undefined) =>
  evaluationScopeKey({ organizationId, systemId })

/** What a scope shows: its own state, or an empty loading file while the state still belongs to the previous scope. */
export const viewSystemFile = (state: SystemFileState, scopeKey: string) => readEvaluationScopeState(state, scopeKey, PENDING)

/** Move the state to a new scope, dropping the previous scope's file. */
export const enterSystemFileScope = (state: SystemFileState, scopeKey: string): SystemFileState =>
  state.scopeKey === scopeKey ? state : { scopeKey, value: PENDING }

type Get = <T>(path: string) => Promise<ApiResponse<T>>

/** Fetch one system's file into its scope; every write is dropped once the state has moved to another scope. */
export async function loadSystemFile(get: Get, systemId: string, scopeKey: string, update: (next: (s: SystemFileState) => SystemFileState) => void) {
  const write = (next: (v: SystemFileView) => SystemFileView) => update((s) => writeEvaluationScopeState(s, scopeKey, next(s.value)))
  write((v) => ({ ...v, loading: true }))
  const sys = await get<SystemRecord>(`${GOV}/systems/${systemId}`)
  if (!sys.success || !sys.data) {
    write((v) => ({ file: { ...v.file, system: null }, loading: false, error: sys.error || 'System not found' }))
    return
  }
  const q = `system_id=${encodeURIComponent(systemId)}`
  const [evidence, approval, remediation, risks, reports, gate, fairnessRuns, monitoringRuns, monitoringPolicy, seals, clauseMap] = await Promise.all([
    get<EvidenceSummary>(`${GOV}/evidence/${systemId}/summary`),
    get<ApprovalStatus>(`${GOV}/approval/system/${systemId}`),
    get<RemediationStatus>(`${GOV}/remediation?${q}`),
    get<RiskStatus>(`${GOV}/dashboard/risk?${q}`),
    get<AuditReport[]>(`${GOV}/reports?${q}`),
    get<ReleaseGate>(`${GOV}/systems/${systemId}/gate`),
    get<FairnessRunSummary[]>(`${GOV}/systems/${systemId}/fairness-runs`),
    get<MonitoringRunSummary[]>(`${GOV}/systems/${systemId}/monitoring-runs`),
    get<MonitoringPolicy>(`${GOV}/systems/${systemId}/monitoring-policy`),
    get<DecisionSeal[]>(`${GOV}/systems/${systemId}/seals`),
    get<ClauseMap>(`${GOV}/systems/${systemId}/clause-map`),
  ])
  const file: SystemFile = {
    system: sys.data,
    evidence: unwrap(evidence, null),
    approval: unwrap(approval, null),
    remediation: unwrap(remediation, null),
    risks: unwrap(risks, null),
    reports: unwrap(reports, []),
    gate: unwrap(gate, null),
    fairnessRuns: unwrap(fairnessRuns, []),
    monitoringRuns: unwrap(monitoringRuns, []),
    monitoringPolicy: unwrap(monitoringPolicy, null),
    seals: unwrap(seals, []),
    clauseMap: unwrap(clauseMap, null),
  }
  write(() => ({ file, loading: false, error: null }))
}

/** Everything the system file shows, fetched once per organisation and system from the governance API. */
export function useSystemFile(systemId: string | undefined) {
  const { selectedOrg } = useOrg()
  const scopeKey = systemFileScopeKey(selectedOrg?.id, systemId)
  const [state, setState] = useState<SystemFileState>(() => ({ scopeKey, value: PENDING }))
  const { file, loading, error } = viewSystemFile(state, scopeKey)

  const refresh = useCallback(async () => {
    if (!systemId) return
    await loadSystemFile((path) => apiClient.get(path), systemId, scopeKey, setState)
  }, [scopeKey, systemId])

  useEffect(() => {
    setState((s) => enterSystemFileScope(s, scopeKey))
    void refresh()
  }, [refresh, scopeKey])

  const requestDecision = async () => {
    if (!systemId) return
    const res = await apiClient.post<ApprovalRequestRecord>(`${GOV}/approval/system/${systemId}/request`, {})
    if (!res.success) throw new Error(res.error || 'Could not request a decision')
    await refresh()
  }

  const recordDecision = async (requestId: string, decision: 'approved' | 'rejected', notes = '') => {
    const res = await apiClient.post<ApprovalRequestRecord>(`${GOV}/approval-requests/${requestId}/decision`, { decision, notes })
    if (!res.success) throw new Error(res.error || 'Could not record the decision')
    await refresh()
  }

  const inspectCsv = async (file: File) => {
    const form = new FormData()
    form.append('file', file)
    const res = await apiClient.post<CsvInspection>(`${GOV}/systems/${systemId}/fairness-runs/inspect`, form, { enableRetry: false })
    if (!res.success || !res.data) throw new Error(res.error || 'Could not read the file')
    return res.data
  }

  const runFairness = async (file: File, mapping: FairnessMapping, confirmation?: AttributeConfirmation) => {
    const form = new FormData()
    form.append('file', file)
    form.append('outcome', mapping.outcome)
    form.append('attributes', mapping.attributes.join(','))
    if (mapping.prediction) form.append('prediction', mapping.prediction)
    if (mapping.score) form.append('score', mapping.score)
    if (mapping.favorableLabel) form.append('favorable_label', mapping.favorableLabel)
    if (confirmation) {
      form.append('confirm', '1')
      form.append('confirm_sha256', confirmation.sha256)
      if (confirmation.removalReason) form.append('removal_reason', confirmation.removalReason)
      if (confirmation.uncoveredReason) form.append('uncovered_reason', confirmation.uncoveredReason)
    }
    const res = await apiClient.post<FairnessRunResult>(`${GOV}/systems/${systemId}/fairness-runs`, form, { enableRetry: false, timeout: 120_000 })
    if (!res.success || !res.data) throw new Error(res.error || 'The run failed')
    await refresh()
    return res.data
  }

  const runMonitoring = async (file: File, mapping: MonitoringMapping) => {
    const form = new FormData()
    form.append('file', file)
    form.append('attributes', mapping.attributes.join(','))
    if (mapping.prediction) form.append('prediction', mapping.prediction)
    if (mapping.score) form.append('score', mapping.score)
    const res = await apiClient.post<MonitoringRunResult>(`${GOV}/systems/${systemId}/monitoring-runs`, form, { enableRetry: false, timeout: 120_000 })
    if (!res.success || !res.data) throw new Error(res.error || 'The monitoring run failed')
    await refresh()
    return res.data
  }

  const saveMonitoringPolicy = async (policy: { cadenceHours?: number; driftWindow?: number }) => {
    const res = await apiClient.put<MonitoringPolicy>(`${GOV}/systems/${systemId}/monitoring-policy`, policy)
    if (!res.success || !res.data) throw new Error(res.error || 'Could not save the monitoring cadence')
    await refresh()
    return res.data
  }

  const attest = async (check: AttestableCheck, statement: string, reference?: string) => {
    const res = await apiClient.post<{ evidenceId: string }>(`${GOV}/systems/${systemId}/attestations`, { check, statement, reference: reference || null })
    if (!res.success || !res.data) throw new Error(res.error || 'Could not record the attestation')
    await refresh()
    return res.data
  }

  return { ...file, loading, error, refresh, requestDecision, recordDecision, inspectCsv, runFairness, runMonitoring, saveMonitoringPolicy, attest }
}
