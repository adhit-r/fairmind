/**
 * Monitoring API Hooks
 */

import { useState, useEffect, useCallback } from 'react'
import { apiClient, type ApiResponse } from '../api-client'
import { API_ENDPOINTS } from '../endpoints'

export interface MonitoringMetrics {
  system_health?: string
  active_models?: number
  total_predictions?: number
  avg_response_time?: number
  error_rate?: number
  bias_alerts?: number
  compliance_score?: number
  requests_per_minute?: number
  active_users?: number
}

export interface SystemHealth {
  status: 'healthy' | 'degraded' | 'unhealthy'
  timestamp: string
  services?: Record<string, {
    status: string
    uptime?: string
    responseTime?: string
  }>
}

export function useMonitoring() {
  const [metrics, setMetrics] = useState<MonitoringMetrics | null>(null)
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<Error | null>(null)

  const fetchMetrics = useCallback(async () => {
    try {
      setLoading(true)
      setError(null)
      
      const response: ApiResponse<MonitoringMetrics> = await apiClient.get(
        API_ENDPOINTS.database.monitoringMetrics,
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
        const errorMessage = response.error || 'Failed to fetch monitoring metrics'
        setError(new Error(errorMessage))
        setMetrics(null)
      }
    } catch (err) {
      console.error('Monitoring API error:', err)
      setError(err instanceof Error ? err : new Error('Failed to fetch monitoring metrics'))
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
    
    // Auto-refresh every 30 seconds
    const interval = setInterval(fetchMetrics, 30000)
    return () => clearInterval(interval)
  }, [fetchMetrics])

  return { metrics, loading, error, refetch: fetchMetrics }
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

