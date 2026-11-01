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

export interface SystemFile {
  system: SystemRecord | null
  evidence: EvidenceSummary | null
  approval: ApprovalStatus | null
  remediation: RemediationStatus | null
  risks: RiskStatus | null
  reports: AuditReport[]
}

function unwrap<T>(res: ApiResponse<T>, fallback: T): T {
  return res.success && res.data !== undefined ? res.data : fallback
}

/** Everything the system file shows, fetched once per system id from the governance API. */
export function useSystemFile(systemId: string | undefined) {
  const [file, setFile] = useState<SystemFile>({ system: null, evidence: null, approval: null, remediation: null, risks: null, reports: [] })
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
    const [evidence, approval, remediation, risks, reports] = await Promise.all([
      apiClient.get<EvidenceSummary>(`${GOV}/evidence/${systemId}/summary`),
      apiClient.get<ApprovalStatus>(`${GOV}/approval/system/${systemId}`),
      apiClient.get<RemediationStatus>(`${GOV}/remediation?${q}`),
      apiClient.get<RiskStatus>(`${GOV}/dashboard/risk?${q}`),
      apiClient.get<AuditReport[]>(`${GOV}/reports?${q}`),
    ])
    setFile({
      system: sys.data,
      evidence: unwrap(evidence, null),
      approval: unwrap(approval, null),
      remediation: unwrap(remediation, null),
      risks: unwrap(risks, null),
      reports: unwrap(reports, []),
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

  return { ...file, loading, error, refresh, requestDecision, recordDecision }
}
