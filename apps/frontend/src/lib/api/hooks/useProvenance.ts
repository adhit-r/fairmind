/**
 * Provenance API Hooks
 */

import { useState, useEffect } from 'react'
import { apiClient, type ApiResponse } from '../api-client'
import { API_ENDPOINTS } from '../endpoints'

export interface ProvenanceRecord {
  id: string
  modelId: string
  lineage: string[]
  metadata: Record<string, any>
  timestamp: string
}

export function useProvenance(modelId?: string) {
  const [data, setData] = useState<ProvenanceRecord[]>([])
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<Error | null>(null)

  useEffect(() => {
    if (!modelId) {
      setLoading(false)
      return
    }

    const fetchProvenance = async () => {
      try {
        setLoading(true)
        const response: ApiResponse<ProvenanceRecord[]> = await apiClient.get(
          `/api/v1/provenance/${modelId}`
        )
        
        if (response.success && response.data) {
          setData(response.data)
          setError(null)
        } else {
          throw new Error(response.error || 'Failed to fetch provenance')
        }
      } catch (err) {
        setError(err instanceof Error ? err : new Error('Unknown error'))
        setData([])
      } finally {
        setLoading(false)
      }
    }

    fetchProvenance()
  }, [modelId])

  return { data, loading, error }
}

