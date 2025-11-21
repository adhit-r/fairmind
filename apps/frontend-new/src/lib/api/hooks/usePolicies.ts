/**
 * Policies API Hooks
 */

import { useState, useEffect } from 'react'
import { apiClient, type ApiResponse } from '../api-client'
import { API_ENDPOINTS } from '../endpoints'

export interface Policy {
  id: string
  name: string
  framework: string
  description: string
  rules: any[]
  status: string
  createdAt: string
}

export function usePolicies(framework?: string) {
  const [data, setData] = useState<Policy[]>([])
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<Error | null>(null)

  useEffect(() => {
    const fetchPolicies = async () => {
      try {
        setLoading(true)
        const url = framework 
          ? `${API_ENDPOINTS.aiGovernance.policies}?framework=${framework}`
          : API_ENDPOINTS.aiGovernance.policies
        const response: ApiResponse<Policy[]> = await apiClient.get(url)
        
        if (response.success && response.data) {
          setData(response.data)
          setError(null)
        } else {
          throw new Error(response.error || 'Failed to fetch policies')
        }
      } catch (err) {
        setError(err instanceof Error ? err : new Error('Unknown error'))
        setData([])
      } finally {
        setLoading(false)
      }
    }

    fetchPolicies()
  }, [framework])

  const createPolicy = async (policyData: any) => {
    try {
      setLoading(true)
      const response: ApiResponse<Policy> = await apiClient.post(
        API_ENDPOINTS.aiGovernance.policies,
        policyData
      )
      if (response.success && response.data) return response.data
      throw new Error(response.error || 'Policy creation failed')
    } catch (err) {
      setError(err instanceof Error ? err : new Error('Policy creation failed'))
      throw err
    } finally {
      setLoading(false)
    }
  }

  return { data, loading, error, createPolicy }
}

