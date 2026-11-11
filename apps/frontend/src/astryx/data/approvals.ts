'use client'

import { useCallback, useEffect, useState } from 'react'
import { apiClient } from '@/lib/api/api-client'
import { API_ENDPOINTS } from '@/lib/api/endpoints'
import type { ApprovalDecision, ApprovalRequest } from '@/lib/api/hooks/useAIGovernance'
import type { DecisionSeal, SystemRecord } from '@/lib/api/hooks/useSystemFile'

const GOV = '/api/v1/ai-governance'

/** A small GET with reload; `path` null keeps it idle. */
function useGet<T>(path: string | null) {
  const [state, setState] = useState<{ data: T | null; loading: boolean; error: string | null }>({ data: null, loading: !!path, error: null })
  const reload = useCallback(async () => {
    if (!path) return
    const res = await apiClient.get<T>(path)
    if (res.success && res.data !== undefined) setState({ data: res.data, loading: false, error: null })
    else setState((s) => ({ data: s.data, loading: false, error: res.error || 'Request failed' }))
  }, [path])
  useEffect(() => {
    setState((s) => ({ ...s, loading: !!path }))
    void reload()
  }, [path, reload])
  return { ...state, reload }
}

/** Every approval request for AI systems, any status. The caller keeps only its own estate's systems. */
export const useApprovalRequests = () => useGet<ApprovalRequest[]>(`${API_ENDPOINTS.aiGovernance.approvalRequests}?entity_type=ai_system`)

export const useApprovalDecisions = (requestId: string | null) =>
  useGet<ApprovalDecision[]>(requestId ? `${API_ENDPOINTS.aiGovernance.approvalRequest(requestId)}/decisions` : null)

export const useSystemSeals = (systemId: string | null) =>
  useGet<DecisionSeal[]>(systemId ? `${GOV}/systems/${encodeURIComponent(systemId)}/seals` : null)

/** Full system records (they carry the tier applicability the summary list leaves out). */
export const useSystemRecords = () => useGet<SystemRecord[]>(API_ENDPOINTS.aiGovernance.systems)

/** Record a decision on a pending request. Returns an error message, or null on success. */
export async function decideRequest(requestId: string, decision: 'approved' | 'rejected', notes: string): Promise<string | null> {
  const res = await apiClient.post(API_ENDPOINTS.aiGovernance.approvalDecision(requestId), { decision, notes }, { enableRetry: false })
  return res.success ? null : res.error || 'Could not record the decision'
}
