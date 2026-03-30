/**
 * Model Inventory API Hook
 */

import { useCallback, useEffect, useState } from 'react'
import { apiClient } from '../api-client'
import { API_ENDPOINTS } from '../endpoints'

export interface LifecycleSummary {
  stage: string
  readiness: number
  failedControls: number
  criticalBlockers: number
  missingEvidence: number
  openRisks: number
  activeRemediation: number
  approvalStatus: string | null
  releaseRecommendation: 'Go' | 'Conditional Go' | 'No-Go'
}

export interface AISystem {
  id: string
  workspaceId: string
  name: string
  owner: string
  riskTier: string
  lifecycleStage: string
  readiness: number
  metadata: Record<string, any>
  createdAt: string
  updatedAt: string
  lifecycleSummary: LifecycleSummary
}

export interface GovernanceRisk {
  id: string
  systemId: string
  title: string
  severity: 'low' | 'medium' | 'high' | 'critical'
  status: string
  description: string
  mitigation: string
  likelihood: string
  riskScore: number
  source: string
  categories: string[]
  metadata: Record<string, any>
  timestamp: string
  updatedAt: string
}

export interface ApprovalDecision {
  id: string
  request_id: string
  decision: 'approved' | 'rejected'
  notes: string
  decided_by: string | null
  createdAt: string
}

export interface SystemApproval {
  id: string
  status: 'pending' | 'approved' | 'rejected'
  requested_by: string | null
  decision_notes: string
  createdAt: string
  updatedAt: string
}

export function useModelInventory() {
  const [systems, setSystems] = useState<AISystem[]>([])
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<Error | null>(null)

  const loadSystems = useCallback(async () => {
    setLoading(true)
    setError(null)
    try {
      const response = await apiClient.get<AISystem[]>(API_ENDPOINTS.aiGovernance.aiSystems)
      if (response.success && response.data) {
        setSystems(response.data)
      } else {
        throw new Error(response.error || 'Failed to fetch systems')
      }
    } catch (err) {
      setError(err instanceof Error ? err : new Error('Unknown error'))
      setSystems([])
    } finally {
      setLoading(false)
    }
  }, [])

  useEffect(() => {
    void loadSystems()
  }, [loadSystems])

  const fetchSystemRisks = useCallback(async (systemId: string): Promise<{ risks: GovernanceRisk[]; summary: any }> => {
    const response = await apiClient.get<{ risks: GovernanceRisk[]; summary: any }>(
      API_ENDPOINTS.aiGovernance.aiSystemRisks(systemId)
    )
    if (response.success && response.data) return response.data
    throw new Error(response.error || 'Failed to fetch risks')
  }, [])

  const fetchSystemApprovals = useCallback(async (systemId: string): Promise<SystemApproval[]> => {
    const response = await apiClient.get<SystemApproval[]>(
      API_ENDPOINTS.aiGovernance.aiSystemApprovals(systemId)
    )
    if (response.success && response.data) return response.data
    return []
  }, [])

  return {
    systems,
    loading,
    error,
    refreshSystems: loadSystems,
    fetchSystemRisks,
    fetchSystemApprovals,
  }
}
