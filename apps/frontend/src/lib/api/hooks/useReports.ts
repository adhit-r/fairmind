/**
 * Reports API Hooks
 */

import { useState, useEffect } from 'react'
import { apiClient, type ApiResponse } from '../api-client'
import { API_ENDPOINTS } from '../endpoints'

export interface Report {
  id: string
  type: string
  title: string
  status: string
  createdAt: string
  data: any
}

export function useReports() {
  const [data, setData] = useState<Report[]>([])
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<Error | null>(null)

  useEffect(() => {
    const fetchReports = async () => {
      try {
        setLoading(true)
        const response: ApiResponse<Report[]> = await apiClient.get(
          API_ENDPOINTS.database.reports
        )
        
        if (response.success && response.data) {
          setData(response.data)
          setError(null)
        } else {
          throw new Error(response.error || 'Failed to fetch reports')
        }
      } catch (err) {
        setError(err instanceof Error ? err : new Error('Unknown error'))
        setData([])
      } finally {
        setLoading(false)
      }
    }

    fetchReports()
  }, [])

  const generateReport = async (params: any) => {
    try {
      setLoading(true)
      const response: ApiResponse<Report> = await apiClient.post(
        API_ENDPOINTS.aiGovernance.generateReport,
        params
      )
      if (response.success && response.data) return response.data
      throw new Error(response.error || 'Report generation failed')
    } catch (err) {
      setError(err instanceof Error ? err : new Error('Report generation failed'))
      throw err
    } finally {
      setLoading(false)
    }
  }

  return { data, loading, error, generateReport }
}

