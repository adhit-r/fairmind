/**
 * Evidence API Hooks
 */

import { useState, useEffect } from 'react'
import { apiClient, type ApiResponse } from '../api-client'
import { API_ENDPOINTS } from '../endpoints'

export interface Evidence {
  id: string
  systemId: string
  type: string
  content: any
  confidence: number
  timestamp: string
  metadata: Record<string, any>
}

export function useEvidence(systemId?: string) {
  const [data, setData] = useState<Evidence[]>([])
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<Error | null>(null)

  useEffect(() => {
    if (!systemId) {
      setLoading(false)
      return
    }

    const fetchEvidence = async () => {
      try {
        setLoading(true)
        const response: ApiResponse<Evidence[]> = await apiClient.get(
          API_ENDPOINTS.aiGovernance.evidence(systemId)
        )
        
        if (response.success && response.data) {
          setData(response.data)
          setError(null)
        } else {
          throw new Error(response.error || 'Failed to fetch evidence')
        }
      } catch (err) {
        setError(err instanceof Error ? err : new Error('Unknown error'))
        setData([])
      } finally {
        setLoading(false)
      }
    }

    fetchEvidence()
  }, [systemId])

  const collectEvidence = async (params: any) => {
    try {
      setLoading(true)
      const response: ApiResponse<Evidence> = await apiClient.post(
        API_ENDPOINTS.aiGovernance.evidenceCollect,
        params
      )
      
      if (response.success && response.data) {
        return response.data
      } else {
        throw new Error(response.error || 'Evidence collection failed')
      }
    } catch (err) {
      const error = err instanceof Error ? err : new Error('Evidence collection failed')
      setError(error)
      throw error
    } finally {
      setLoading(false)
    }
  }

  return { data, loading, error, collectEvidence }
}

