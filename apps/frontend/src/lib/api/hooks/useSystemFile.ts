'use client'

import { useCallback, useEffect, useState } from 'react'
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
  summary: { total: number; open: number; automated: number; bySeverity: Record<'low' | 'medium' | 'high' | 'critical', number> }
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
}

export interface FairnessRunSummary {
  evidenceId: string
  title: string
  rows: number | null
  allChecksPass: boolean | null
  attributes: Array<{ attribute: string; disparateImpactRatio: number; checks: Record<string, boolean> }>
  confidence: number
  createdAt: string
}

export interface CsvInspection {
  rows: number
  columns: Array<{ name: string; dtype: string; distinct: number; sample: string[] }>
  suggested: { outcome: string | null; prediction: string | null; score: string | null; attributes: string[] }
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
    thresholds: { disparate_impact_ratio: number; gap: number }
    attributes: Array<{
      attribute: string
      groups: Record<string, number>
      selection_rates: Record<string, number>
      disparate_impact_ratio: number
      demographic_parity: { value: number; confidence_interval: [number, number]; is_fair: boolean }
      equal_opportunity: { value: number; confidence_interval: [number, number]; is_fair: boolean }
      equalized_odds: { value: number; confidence_interval: [number, number]; is_fair: boolean }
      calibration: { value: number; confidence_interval: [number, number]; is_fair: boolean } | null
      checks: Record<string, boolean>
      small_groups: string[]
    }>
  }
  gate: ReleaseGate
}

export interface SystemFile {
  system: SystemRecord | null
  evidence: EvidenceSummary | null
  approval: ApprovalStatus | null
  remediation: RemediationStatus | null
  risks: RiskStatus | null
  reports: AuditReport[]
  gate: ReleaseGate | null
  fairnessRuns: FairnessRunSummary[]
}

function unwrap<T>(res: ApiResponse<T>, fallback: T): T {
  return res.success && res.data !== undefined ? res.data : fallback
}

/** Everything the system file shows, fetched once per system id from the governance API. */
export function useSystemFile(systemId: string | undefined) {
  const [file, setFile] = useState<SystemFile>({ system: null, evidence: null, approval: null, remediation: null, risks: null, reports: [], gate: null, fairnessRuns: [] })
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)

  const refresh = useCallback(async () => {
    if (!systemId) return
    setLoading(true)
    const sys = await apiClient.get<SystemRecord>(`${GOV}/systems/${systemId}`)
    if (!sys.success || !sys.data) {
      setError(sys.error || 'System not found')
      setFile((f) => ({ ...f, system: null }))
      setLoading(false)
      return
    }
    const q = `system_id=${encodeURIComponent(systemId)}`
    const [evidence, approval, remediation, risks, reports, gate, fairnessRuns] = await Promise.all([
      apiClient.get<EvidenceSummary>(`${GOV}/evidence/${systemId}/summary`),
      apiClient.get<ApprovalStatus>(`${GOV}/approval/system/${systemId}`),
      apiClient.get<RemediationStatus>(`${GOV}/remediation?${q}`),
      apiClient.get<RiskStatus>(`${GOV}/dashboard/risk?${q}`),
      apiClient.get<AuditReport[]>(`${GOV}/reports?${q}`),
      apiClient.get<ReleaseGate>(`${GOV}/systems/${systemId}/gate`),
      apiClient.get<FairnessRunSummary[]>(`${GOV}/systems/${systemId}/fairness-runs`),
    ])
    setFile({
      system: sys.data,
      evidence: unwrap(evidence, null),
      approval: unwrap(approval, null),
      remediation: unwrap(remediation, null),
      risks: unwrap(risks, null),
      reports: unwrap(reports, []),
      gate: unwrap(gate, null),
      fairnessRuns: unwrap(fairnessRuns, []),
    })
    setError(null)
    setLoading(false)
  }, [systemId])

  useEffect(() => {
    void refresh()
  }, [refresh])

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

  const runFairness = async (file: File, mapping: FairnessMapping) => {
    const form = new FormData()
    form.append('file', file)
    form.append('outcome', mapping.outcome)
    form.append('attributes', mapping.attributes.join(','))
    if (mapping.prediction) form.append('prediction', mapping.prediction)
    if (mapping.score) form.append('score', mapping.score)
    if (mapping.favorableLabel) form.append('favorable_label', mapping.favorableLabel)
    const res = await apiClient.post<FairnessRunResult>(`${GOV}/systems/${systemId}/fairness-runs`, form, { enableRetry: false, timeout: 120_000 })
    if (!res.success || !res.data) throw new Error(res.error || 'The run failed')
    await refresh()
    return res.data
  }

  return { ...file, loading, error, refresh, requestDecision, recordDecision, inspectCsv, runFairness }
}
