/**
 * Monitoring API Hooks
 */

import { useState, useEffect, useCallback } from 'react'
import { apiClient, type ApiResponse } from '../api-client'
import { API_ENDPOINTS } from '../endpoints'


export interface SystemHealth {
  status: 'healthy' | 'degraded' | 'unhealthy'
  timestamp: string
  services?: Record<string, {
    status: string
    uptime?: string
    responseTime?: string
  }>
}


export function useSystemHealth() {
  const [health, setHealth] = useState<SystemHealth | null>(null)
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<Error | null>(null)

  const fetchHealth = useCallback(async () => {
    try {
      setLoading(true)
      setError(null)
      
      const response: ApiResponse<SystemHealth> = await apiClient.get(
        API_ENDPOINTS.aiGovernance.status,
        {
          enableRetry: true,
          maxRetries: 3,
          timeout: 10000,
        }
      )
      
      if (response.success && response.data) {
        setHealth(response.data)
        setError(null)
      } else {
        const errorMessage = response.error || 'Failed to fetch system health'
        setError(new Error(errorMessage))
        setHealth(null)
      }
    } catch (err) {
      console.error('System health API error:', err)
      setError(err instanceof Error ? err : new Error('Failed to fetch system health'))
      setHealth(null)
    } finally {
      setLoading(false)
    }
  }, [])

  useEffect(() => {
    if (typeof window === 'undefined') {
      setLoading(false)
      return
    }

    fetchHealth()
    
    // Auto-refresh every 60 seconds
    const interval = setInterval(fetchHealth, 60000)
    return () => clearInterval(interval)
  }, [fetchHealth])

  return { health, loading, error, refetch: fetchHealth }
}

