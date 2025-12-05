/**
 * Models API Hooks
 */

import { useState, useEffect } from 'react'
import { apiClient, type ApiResponse } from '../api-client'
import { API_ENDPOINTS } from '../endpoints'
import type { Model } from '../types'

export function useModels() {
  const [data, setData] = useState<Model[]>([])
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<Error | null>(null)

  const fetchModels = async () => {
    try {
      setLoading(true)
      // Use core.models endpoint which returns mock data when no DB records
      const response: ApiResponse<{ data: Model[], count: number }> = await apiClient.get(
        API_ENDPOINTS.core.models
      )

      if (response.success && response.data) {
        setData(response.data.data || [])
        setError(null)
      } else {
        throw new Error(response.error || 'Failed to fetch models')
      }
    } catch (err) {
      setError(err instanceof Error ? err : new Error('Unknown error'))
      setData([])
    } finally {
      setLoading(false)
    }
  }

  useEffect(() => {
    fetchModels()
  }, [])

  return { data, loading, error, refetch: fetchModels }
}

