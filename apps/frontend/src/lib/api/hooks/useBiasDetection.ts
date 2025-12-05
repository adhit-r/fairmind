/**
 * Bias Detection API Hooks
 */

import { useState } from 'react'
import { apiClient, type ApiResponse } from '../api-client'
import { API_ENDPOINTS } from '../endpoints'
import type { BiasTestRequest, BiasTestResponse } from '../types'

export function useBiasDetection() {
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState<Error | null>(null)

  const runBiasTest = async (request: BiasTestRequest) => {
    try {
      setLoading(true)
      setError(null)
      
      const response: ApiResponse<BiasTestResponse> = await apiClient.post(
        API_ENDPOINTS.biasDetection.detect,
        request
      )
      
      if (response.success && response.data) {
        return response.data
      } else {
        throw new Error(response.error || 'Bias test failed')
      }
    } catch (err) {
      const error = err instanceof Error ? err : new Error('Bias test failed')
      setError(error)
      throw error
    } finally {
      setLoading(false)
    }
  }

  return { runBiasTest, loading, error }
}

