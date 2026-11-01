'use client'

import { useEffect, useState } from 'react'
import { apiClient, type ApiResponse } from '../api-client'
import { API_ENDPOINTS } from '../endpoints'
import type { ApprovalRequest } from './useAIGovernance'

/** Approval requests for AI systems that still await a decision. */
export function usePendingDecisions() {
  const [requests, setRequests] = useState<ApprovalRequest[]>([])
  const [loading, setLoading] = useState(true)

  useEffect(() => {
    let active = true
    apiClient
      .get<ApprovalRequest[]>(`${API_ENDPOINTS.aiGovernance.approvalRequests}?entity_type=ai_system`)
      .then((res: ApiResponse<ApprovalRequest[]>) => {
        if (!active) return
        setRequests((res.success && res.data ? res.data : []).filter((r) => r.status === 'pending'))
      })
      .catch(() => active && setRequests([]))
      .finally(() => active && setLoading(false))
    return () => {
      active = false
    }
  }, [])

  const pendingSystemIds = new Set(requests.map((r) => r.entity_id))
  return { requests, pendingSystemIds, loading }
}
