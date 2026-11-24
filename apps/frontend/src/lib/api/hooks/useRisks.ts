/**
 * Risks API Hooks
 */

import { useMemo } from 'react'
import { apiClient, type ApiResponse } from '../api-client'
import { API_ENDPOINTS } from '../endpoints'
import { useOrgResource } from './usePacks'

/** Statuses that settle a risk; every other status (open, acceptance_pending, ...) still blocks release, matching the backend. */
export const CLOSED_RISK_STATUSES = ['accepted', 'closed', 'resolved', 'mitigated']
export const isOpenRisk = (r: { status: string }) => !CLOSED_RISK_STATUSES.includes(r.status)

export interface Risk {
  id: string
  systemId?: string
  title: string
  severity: 'low' | 'medium' | 'high' | 'critical'
  status: string
  description: string
  mitigation: string
  timestamp: string
  /** "manual_assessment" when a person typed it in; anything else was raised by FairMind. */
  source?: string
  metadata?: {
    pendingAcceptance?: PendingAcceptance
    evaluationId?: string
    evidenceId?: string
    retestEvidenceIds?: string[]
    retestEvidenceId?: string
    latest_snapshot_id?: string
    assessment_id?: string
    analysis_id?: string
  }
}

/** An acceptance one person proposed, waiting for a different person to approve it (status "acceptance_pending"). */
export interface PendingAcceptance {
  rationale: string
  owner: string | null
  proposedBy: string
  proposedById: string
  proposedAt: string
}

/** A general MIT/IBM risk-library entry. Not matched to any system and not a finding. */
export interface SuggestedRisk {
  id: string
  systemId?: string
  title: string
  severity: 'low' | 'medium' | 'high' | 'critical'
  status: string
  description: string
  mitigation: string
  likelihood?: string
  risk_score?: number
  source: 'mit' | 'ibm' | string
  categories?: string[]
}

export interface RiskSummary {
  total: number
  open: number
  automated: number
  suggested: number
  bySeverity: Record<'low' | 'medium' | 'high' | 'critical', number>
}

function validSummary(value: RiskSummary | undefined): value is RiskSummary {
  return Boolean(value && value.bySeverity &&
    [value.total, value.open, value.automated, value.suggested, ...['low', 'medium', 'high', 'critical'].map(
      (severity) => value.bySeverity[severity as Risk['severity']]
    )].every((count) => Number.isInteger(count) && count >= 0))
}

export function useRisks(systemId?: string) {
  const endpoint = API_ENDPOINTS.aiGovernance.riskDashboard
  const path = systemId ? `${endpoint}?system_id=${encodeURIComponent(systemId)}` : endpoint
  const response = useOrgResource<{ risks: Array<Risk & { system_id?: string }>; suggested?: SuggestedRisk[]; summary?: RiskSummary }>(path)
  const { reload } = response
  const result = useMemo(() => {
    const empty = { data: [] as Risk[], suggested: [] as SuggestedRisk[], summary: null }
    if (response.loading) return { ...empty, error: null }
    if (response.error) return { ...empty, error: new Error(response.error) }
    const payload = response.data
    if (!Array.isArray(payload?.risks)) return { ...empty, error: new Error('The findings response was incomplete.') }
    const risks = payload.risks
    if (risks.some((r) => !r || !r.id || typeof r.title !== 'string' || !r.status ||
      !['critical', 'high', 'medium', 'low'].includes(r.severity) ||
      (r.systemId && r.system_id && r.systemId !== r.system_id) ||
      (systemId && (r.systemId ?? r.system_id) !== systemId))) {
      return { ...empty, error: new Error('The findings response was incomplete or included another system.') }
    }
    return {
      data: risks.map((r) => r.systemId || !r.system_id ? r : { ...r, systemId: r.system_id }),
      suggested: Array.isArray(payload.suggested) ? payload.suggested : [],
      summary: validSummary(payload.summary) ? payload.summary : null,
      error: null,
    }
  }, [response.data, response.error, response.loading, systemId])

  // Throws on failure. A failed submit is the caller's to report; it is not a list-load error.
  // On success the list reloads for whichever system is current, rather than merging the new
  // row locally: the user may have switched systems, or a load may still be in flight.
  const assessRisks = async (params: any) => {
    const response: ApiResponse<Risk> = await apiClient.post(
      API_ENDPOINTS.aiGovernance.assessRisks,
      params
    )
    if (!response.success || !response.data) {
      throw new Error(response.error || 'Risk assessment failed')
    }
    reload()
    return response.data
  }

  // A person accepts or mitigates an open finding, with the reason; the server keeps the decision as a record.
  const treatRisk = async (riskId: string, body: { status: 'accepted' | 'mitigated'; rationale: string; owner?: string | null }) => {
    const response: ApiResponse<unknown> = await apiClient.patch(API_ENDPOINTS.aiGovernance.treatRisk(riskId), body)
    if (!response.success) throw new Error(response.error || 'Could not record the decision')
    reload()
  }

  // A different person approves a pending acceptance, or either person withdraws it.
  const settleAcceptance = async (riskId: string, action: 'approve' | 'withdraw') => {
    const response: ApiResponse<unknown> = await apiClient.post(API_ENDPOINTS.aiGovernance.riskAcceptance(riskId, action))
    if (!response.success) throw new Error(response.error || 'Could not record the decision')
    reload()
  }

  return { ...result, loading: response.loading, reload, assessRisks, treatRisk, settleAcceptance }
}
