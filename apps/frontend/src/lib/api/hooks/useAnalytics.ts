/**
 * Analytics API Hooks
 */

import { useState, useEffect, useCallback } from 'react'
import { apiClient, type ApiResponse } from '../api-client'
import { API_ENDPOINTS } from '../endpoints'

export interface GovernanceMetrics {
  totalAnalyses?: number
  biasDetected?: number
  activeUsers?: number
  avgScore?: number
  euCompliance?: number
  nistCompliance?: number
  gdprCompliance?: number
}

export interface BiasTrend {
  name: string
  value: number
  detected?: number
}

export function useAnalytics() {
  const [metrics, setMetrics] = useState<GovernanceMetrics | null>(null)
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<Error | null>(null)

  const fetchMetrics = useCallback(async () => {
    try {
      setLoading(true)
      setError(null)
      
      const response: ApiResponse<GovernanceMetrics> = await apiClient.get(
        API_ENDPOINTS.core.governanceMetrics,
        {
          enableRetry: true,
          maxRetries: 3,
          timeout: 10000,
        }
      )
      
      if (response.success && response.data) {
        setMetrics(response.data)
        setError(null)
      } else {
        const errorMessage = response.error || 'Failed to fetch analytics metrics'
        setError(new Error(errorMessage))
        setMetrics(null)
      }
    } catch (err) {
      console.error('Analytics API error:', err)
      setError(err instanceof Error ? err : new Error('Failed to fetch analytics metrics'))
      setMetrics(null)
    } finally {
      setLoading(false)
    }
  }, [])

  useEffect(() => {
    if (typeof window === 'undefined') {
      setLoading(false)
      return
    }

    fetchMetrics()
  }, [fetchMetrics])

  return { metrics, loading, error, refetch: fetchMetrics }
}

