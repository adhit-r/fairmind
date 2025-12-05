/**
 * AI Governance API Hooks
 */

import { useState, useEffect } from 'react'
import { apiClient, type ApiResponse } from '../api-client'
import { API_ENDPOINTS } from '../endpoints'

export interface ComplianceFramework {
  id: string
  name: string
  description: string
  controls: any[]
}

export function useAIGovernance() {
  const [frameworks, setFrameworks] = useState<ComplianceFramework[]>([])
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<Error | null>(null)

  useEffect(() => {
    const fetchFrameworks = async () => {
      try {
        setLoading(true)
        const response: ApiResponse<ComplianceFramework[]> = await apiClient.get(
          API_ENDPOINTS.aiGovernance.complianceFrameworks
        )
        
        if (response.success && response.data) {
          setFrameworks(response.data)
          setError(null)
        } else {
          throw new Error(response.error || 'Failed to fetch frameworks')
        }
      } catch (err) {
        setError(err instanceof Error ? err : new Error('Unknown error'))
        setFrameworks([])
      } finally {
        setLoading(false)
      }
    }

    fetchFrameworks()
  }, [])

  const registerModel = async (modelData: any) => {
    try {
      setLoading(true)
      const response: ApiResponse<any> = await apiClient.post(
        API_ENDPOINTS.aiGovernance.registerModel,
        modelData
      )
      if (response.success && response.data) return response.data
      throw new Error(response.error || 'Model registration failed')
    } catch (err) {
      setError(err instanceof Error ? err : new Error('Model registration failed'))
      throw err
    } finally {
      setLoading(false)
    }
  }

  return { frameworks, loading, error, registerModel }
}

