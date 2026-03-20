/**
 * AI Governance API Hooks
 */

import { useState, useEffect, useCallback } from 'react'
import { apiClient, type ApiResponse } from '../api-client'
import { API_ENDPOINTS } from '../endpoints'

export interface ComplianceFramework {
  id: string
  name: string
  description: string
  controls: any[]
}

export interface ApprovalDecision {
  id: string
  request_id: string
  decision: 'approved' | 'rejected'
  notes: string
  decided_by?: string | null
  createdAt: string
}

export interface ApprovalRequest {
  id: string
  workflow_id: string
  entity_type: string
  entity_id: string
  requested_by?: string | null
  status: 'pending' | 'approved' | 'rejected'
  current_step: number
  decision_notes: string
  createdAt: string
  updatedAt: string
}

interface SystemApprovalState {
  systemId: string
  request: ApprovalRequest | null
  decisions: ApprovalDecision[]
}

export function useAIGovernance() {
  const [frameworks, setFrameworks] = useState<ComplianceFramework[]>([])
  const [loading, setLoading] = useState(true)
  const [approvalLoading, setApprovalLoading] = useState(false)
  const [error, setError] = useState<Error | null>(null)

  useEffect(() => {
    const fetchFrameworks = async () => {
      try {
        setLoading(true)
        const response: ApiResponse<ComplianceFramework[]> = await apiClient.get(
          API_ENDPOINTS.aiGovernance.complianceFrameworks
        )
        
        if (response.success && response.data) {
          setFrameworks(response.data)
          setError(null)
        } else {
          throw new Error(response.error || 'Failed to fetch frameworks')
        }
      } catch (err) {
        setError(err instanceof Error ? err : new Error('Unknown error'))
        setFrameworks([])
      } finally {
        setLoading(false)
      }
    }

    fetchFrameworks()
  }, [])

  const registerModel = async (modelData: any) => {
    try {
      setLoading(true)
      const response: ApiResponse<any> = await apiClient.post(
        API_ENDPOINTS.aiGovernance.registerModel,
        modelData
      )
      if (response.success && response.data) return response.data
      throw new Error(response.error || 'Model registration failed')
    } catch (err) {
      setError(err instanceof Error ? err : new Error('Model registration failed'))
      throw err
    } finally {
      setLoading(false)
    }
  }

  const getSystemApproval = useCallback(async (systemId: string) => {
    setApprovalLoading(true)
    try {
      const response: ApiResponse<SystemApprovalState> = await apiClient.get(
        API_ENDPOINTS.aiGovernance.systemApproval(systemId)
      )
      if (response.success && response.data) {
        return response.data
      }
      throw new Error(response.error || 'Failed to load approval state')
    } finally {
      setApprovalLoading(false)
    }
  }, [])

  const requestSystemApproval = useCallback(async (systemId: string, requestedBy?: string) => {
    setApprovalLoading(true)
    try {
      const response: ApiResponse<SystemApprovalState> = await apiClient.post(
        API_ENDPOINTS.aiGovernance.systemApprovalRequest(systemId),
        { requested_by: requestedBy || null }
      )
      if (response.success && response.data) {
        return response.data
      }
      throw new Error(response.error || 'Failed to create approval request')
    } finally {
      setApprovalLoading(false)
    }
  }, [])

  const decideApprovalRequest = useCallback(
    async (requestId: string, decision: 'approved' | 'rejected', notes: string, decidedBy?: string) => {
      setApprovalLoading(true)
      try {
        const response: ApiResponse<any> = await apiClient.post(
          API_ENDPOINTS.aiGovernance.approvalDecision(requestId),
          {
            decision,
            notes,
            decided_by: decidedBy || null,
          }
        )
        if (response.success && response.data) {
          return response.data
        }
        throw new Error(response.error || 'Failed to record approval decision')
      } finally {
        setApprovalLoading(false)
      }
    },
    []
  )

  return {
    frameworks,
    loading,
    approvalLoading,
    error,
    registerModel,
    getSystemApproval,
    requestSystemApproval,
    decideApprovalRequest,
  }
}
