/**
 * Lifecycle API Hooks
 */

import { useState } from 'react'
import { apiClient, type ApiResponse } from '../api-client'
import { API_ENDPOINTS } from '../endpoints'

export interface LifecycleStage {
  id: string
  systemId: string
  stage: string
  status: string
  timestamp: string
  metadata: Record<string, any>
}

export interface LifecycleSummary {
  systemId: string
  currentStage: string
  stages: LifecycleStage[]
  checks: any[]
}

export function useLifecycle() {
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState<Error | null>(null)

  const processStage = async (data: any) => {
    try {
      setLoading(true)
      setError(null)
      
      const response: ApiResponse<any> = await apiClient.post(
        API_ENDPOINTS.aiGovernance.lifecycleProcess,
        data
      )
      
      if (response.success && response.data) {
        return response.data
      } else {
        throw new Error(response.error || 'Lifecycle processing failed')
      }
    } catch (err) {
      const error = err instanceof Error ? err : new Error('Lifecycle processing failed')
      setError(error)
      throw error
    } finally {
      setLoading(false)
    }
  }

  const getSummary = async (systemId: string) => {
    try {
      setLoading(true)
      const response: ApiResponse<LifecycleSummary> = await apiClient.get(
        API_ENDPOINTS.aiGovernance.lifecycleSummary(systemId)
      )
      
      if (response.success && response.data) {
        return response.data
      } else {
        throw new Error(response.error || 'Failed to fetch lifecycle summary')
      }
    } catch (err) {
      const error = err instanceof Error ? err : new Error('Failed to fetch lifecycle summary')
      setError(error)
      throw error
    } finally {
      setLoading(false)
    }
  }

  return { processStage, getSummary, loading, error }
}

