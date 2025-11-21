/**
 * Risks API Hooks
 */

import { useState, useEffect } from 'react'
import { apiClient, type ApiResponse } from '../api-client'
import { API_ENDPOINTS } from '../endpoints'

export interface Risk {
  id: string
  title: string
  severity: 'low' | 'medium' | 'high' | 'critical'
  status: string
  description: string
  mitigation: string
  timestamp: string
}

export function useRisks() {
  const [data, setData] = useState<Risk[]>([])
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<Error | null>(null)

  useEffect(() => {
    const fetchRisks = async () => {
      try {
        setLoading(true)
        const response: ApiResponse<any> = await apiClient.get(
          API_ENDPOINTS.aiGovernance.riskDashboard
        )
        
        if (response.success && response.data) {
          setData(response.data.risks || [])
          setError(null)
        } else {
          throw new Error(response.error || 'Failed to fetch risks')
        }
      } catch (err) {
        setError(err instanceof Error ? err : new Error('Unknown error'))
        setData([])
      } finally {
        setLoading(false)
      }
    }

    fetchRisks()
  }, [])

  const assessRisks = async (params: any) => {
    try {
      setLoading(true)
      const response: ApiResponse<Risk> = await apiClient.post(
        API_ENDPOINTS.aiGovernance.assessRisks,
        params
      )
      if (response.success && response.data) return response.data
      throw new Error(response.error || 'Risk assessment failed')
    } catch (err) {
      setError(err instanceof Error ? err : new Error('Risk assessment failed'))
      throw err
    } finally {
      setLoading(false)
    }
  }

  return { data, loading, error, assessRisks }
}

