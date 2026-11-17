/**
 * Risks API Hooks
 */

import { useState, useEffect } from 'react'
import { apiClient, type ApiResponse } from '../api-client'
import { API_ENDPOINTS } from '../endpoints'

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
  metadata?: { pendingAcceptance?: PendingAcceptance }
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

const EMPTY_SUMMARY: RiskSummary = {
  total: 0,
  open: 0,
  automated: 0,
  suggested: 0,
  bySeverity: {
    low: 0,
    medium: 0,
    high: 0,
    critical: 0,
  },
}

export function useRisks(systemId?: string) {
  const [data, setData] = useState<Risk[]>([])
  const [suggested, setSuggested] = useState<SuggestedRisk[]>([])
  // null = not known (loading or the load failed). Never a stand-in zero.
  const [summary, setSummary] = useState<RiskSummary | null>(null)
  const [loadedFor, setLoadedFor] = useState<string | undefined>(undefined)
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<Error | null>(null)
  // Bumped after a recorded finding so the list and counts reload from the server.
  const [reloads, setReloads] = useState(0)

  useEffect(() => {
    // Set when the system changes or the component unmounts, so a superseded response is ignored.
    let cancelled = false

    const fetchRisks = async () => {
      setLoading(true)
      setError(null)
      // A different system must not show the previous one's findings while it loads.
      setData([])
      setSuggested([])
      setSummary(null)
      try {
        const endpoint = systemId
          ? `${API_ENDPOINTS.aiGovernance.riskDashboard}?system_id=${encodeURIComponent(systemId)}`
          : API_ENDPOINTS.aiGovernance.riskDashboard
        const response: ApiResponse<any> = await apiClient.get(endpoint)
        if (cancelled) return

        if (response.success && response.data) {
          setData(response.data.risks || [])
          setSuggested(response.data.suggested || [])
          setSummary({ ...EMPTY_SUMMARY, ...response.data.summary })
        } else {
          throw new Error(response.error || 'Failed to fetch risks')
        }
      } catch (err) {
        if (cancelled) return
        setError(err instanceof Error ? err : new Error('Unknown error'))
      } finally {
        if (!cancelled) {
          setLoadedFor(systemId)
          setLoading(false)
        }
      }
    }

    fetchRisks()
    return () => {
      cancelled = true
    }
  }, [systemId, reloads])

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
    setReloads((n) => n + 1)
    return response.data
  }

  // A person accepts or mitigates an open finding, with the reason; the server keeps the decision as a record.
  const treatRisk = async (riskId: string, body: { status: 'accepted' | 'mitigated'; rationale: string; owner?: string | null }) => {
    const response: ApiResponse<unknown> = await apiClient.patch(API_ENDPOINTS.aiGovernance.treatRisk(riskId), body)
    if (!response.success) throw new Error(response.error || 'Could not record the decision')
    setReloads((n) => n + 1)
  }

  // A different person approves a pending acceptance, or either person withdraws it.
  const settleAcceptance = async (riskId: string, action: 'approve' | 'withdraw') => {
    const response: ApiResponse<unknown> = await apiClient.post(API_ENDPOINTS.aiGovernance.riskAcceptance(riskId, action))
    if (!response.success) throw new Error(response.error || 'Could not record the decision')
    setReloads((n) => n + 1)
  }

  // Also loading while the data on hand belongs to a different system than the one asked for.
  return { data, suggested, summary, loading: loading || loadedFor !== systemId, error, assessRisks, treatRisk, settleAcceptance }
}
