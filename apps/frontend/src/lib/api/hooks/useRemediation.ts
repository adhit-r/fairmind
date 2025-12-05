import { useState, useCallback } from 'react'
import { apiClient } from '../api-client'
import { API_ENDPOINTS } from '../endpoints'

export interface RemediationStrategy {
  strategy: string
  success: boolean
  improved_metrics: Record<string, number>
  original_metrics: Record<string, number>
  improvement_percentage: number
  implementation_code: string
  explanation: string
  warnings: string[]
  threshold_adjustments?: Record<string, number>
}

export interface RemediationRequest {
  test_id: string
  strategies?: string[]
}

export interface RemediationResponse {
  test_id: string
  model_id: string
  strategies: RemediationStrategy[]
  best_strategy: RemediationStrategy
  summary: string
}

export function useRemediation() {
  const [remediation, setRemediation] = useState<RemediationResponse | null>(null)
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState<string | null>(null)

  const getRemediation = useCallback(async (testId: string, strategies?: string[]) => {
    setLoading(true)
    setError(null)
    try {
      const response = await apiClient.post<RemediationResponse>(
        '/api/v1/bias-v2/remediate',
        {
          test_id: testId,
          strategies: strategies || ['reweighting', 'resampling', 'threshold_optimization']
        },
        {
          maxRetries: 2,
          timeout: 30000,
        }
      )

      if (response) {
        setRemediation(response as any)
      } else {
        setError('Failed to get remediation strategies')
      }
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to get remediation strategies')
    } finally {
      setLoading(false)
    }
  }, [])

  return {
    remediation,
    loading,
    error,
    getRemediation,
  }
}
