/**
 * Risks API Hooks
 */

import { useState, useEffect } from 'react'
import { apiClient, type ApiResponse } from '../api-client'
import { API_ENDPOINTS } from '../endpoints'

export interface Risk {
  id: string
  systemId?: string
  title: string
  severity: 'low' | 'medium' | 'high' | 'critical'
  status: string
  description: string
  mitigation: string
  timestamp: string
}

export interface RiskSummary {
  total: number
  open: number
  automated: number
  bySeverity: Record<'low' | 'medium' | 'high' | 'critical', number>
}

const EMPTY_SUMMARY: RiskSummary = {
  total: 0,
  open: 0,
  automated: 0,
  bySeverity: {
    low: 0,
    medium: 0,
    high: 0,
    critical: 0,
  },
}

export function useRisks(systemId?: string) {
  const [data, setData] = useState<Risk[]>([])
  const [summary, setSummary] = useState<RiskSummary>(EMPTY_SUMMARY)
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<Error | null>(null)

  useEffect(() => {
    const fetchRisks = async () => {
      try {
        setLoading(true)
        const endpoint = systemId
          ? `${API_ENDPOINTS.aiGovernance.riskDashboard}?system_id=${encodeURIComponent(systemId)}`
          : API_ENDPOINTS.aiGovernance.riskDashboard
        const response: ApiResponse<any> = await apiClient.get(
          endpoint
        )
        
        if (response.success && response.data) {
          setData(response.data.risks || [])
          setSummary(response.data.summary || EMPTY_SUMMARY)
          setError(null)
        } else {
          throw new Error(response.error || 'Failed to fetch risks')
        }
      } catch (err) {
        setError(err instanceof Error ? err : new Error('Unknown error'))
        setData([])
        setSummary(EMPTY_SUMMARY)
      } finally {
        setLoading(false)
      }
    }

    fetchRisks()
  }, [systemId])

  const assessRisks = async (params: any) => {
    try {
      setLoading(true)
      const response: ApiResponse<Risk> = await apiClient.post(
        API_ENDPOINTS.aiGovernance.assessRisks,
        params
      )
      if (response.success && response.data) {
        const createdRisk = response.data
        setData((current) => [createdRisk, ...current])
        setSummary((current) => ({
          ...current,
          total: current.total + 1,
          open: current.open + 1,
          bySeverity: {
            ...current.bySeverity,
            [createdRisk.severity]: (current.bySeverity[createdRisk.severity] || 0) + 1,
          },
        }))
        setError(null)
        return createdRisk
      }
      throw new Error(response.error || 'Risk assessment failed')
    } catch (err) {
      setError(err instanceof Error ? err : new Error('Risk assessment failed'))
      throw err
    } finally {
      setLoading(false)
    }
  }

  return { data, summary, loading, error, assessRisks }
}
