/**
 * Audit Logs API Hooks
 */

import { useState, useEffect, useCallback } from 'react'
import { apiClient, type ApiResponse } from '../api-client'
import { API_ENDPOINTS } from '../endpoints'

export interface AuditLog {
  id: string
  timestamp?: string
  created_at?: string
  type?: string
  description?: string
  user?: string
  action?: string
  resource?: string
  metadata?: Record<string, any>
}

export function useAuditLogs(limit: number = 10) {
  const [data, setData] = useState<AuditLog[]>([])
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<Error | null>(null)

  const fetchAuditLogs = useCallback(async () => {
    try {
      setLoading(true)
      setError(null)
      
      const response: ApiResponse<AuditLog[]> = await apiClient.get(
        `${API_ENDPOINTS.database.auditLogs}?limit=${limit}`,
        {
          enableRetry: true,
          maxRetries: 3,
          timeout: 10000,
        }
      )
      
      if (response.success && response.data) {
        setData(response.data)
        setError(null)
      } else {
        const errorMessage = response.error || 'Failed to fetch audit logs'
        setError(new Error(errorMessage))
        setData([])
      }
    } catch (err) {
      console.error('Audit logs API error:', err)
      setError(err instanceof Error ? err : new Error('Failed to fetch audit logs'))
      setData([])
    } finally {
      setLoading(false)
    }
  }, [limit])

  useEffect(() => {
    if (typeof window === 'undefined') {
      setLoading(false)
      return
    }

    fetchAuditLogs()
  }, [fetchAuditLogs])

  return { data, loading, error, refetch: fetchAuditLogs }
}

