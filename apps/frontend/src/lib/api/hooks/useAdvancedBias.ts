/**
 * Advanced Bias Detection API Hooks
 */

import { useState } from 'react'
import { apiClient, type ApiResponse } from '../api-client'
import { API_ENDPOINTS } from '../endpoints'

export interface AdvancedBiasAnalysis {
  id: string
  type: 'causal' | 'counterfactual' | 'intersectional' | 'adversarial' | 'temporal' | 'contextual'
  results: any
  timestamp: string
}

export function useAdvancedBias() {
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState<Error | null>(null)

  const runCausalAnalysis = async (params: any) => {
    try {
      setLoading(true)
      const response: ApiResponse<AdvancedBiasAnalysis> = await apiClient.post(
        API_ENDPOINTS.advancedBiasDetection.causalAnalysis,
        params
      )
      if (response.success && response.data) return response.data
      throw new Error(response.error || 'Causal analysis failed')
    } catch (err) {
      setError(err instanceof Error ? err : new Error('Causal analysis failed'))
      throw err
    } finally {
      setLoading(false)
    }
  }

  const runCounterfactualAnalysis = async (params: any) => {
    try {
      setLoading(true)
      const response: ApiResponse<AdvancedBiasAnalysis> = await apiClient.post(
        API_ENDPOINTS.advancedBiasDetection.counterfactualAnalysis,
        params
      )
      if (response.success && response.data) return response.data
      throw new Error(response.error || 'Counterfactual analysis failed')
    } catch (err) {
      setError(err instanceof Error ? err : new Error('Counterfactual analysis failed'))
      throw err
    } finally {
      setLoading(false)
    }
  }

  const runIntersectionalAnalysis = async (params: any) => {
    try {
      setLoading(true)
      const response: ApiResponse<AdvancedBiasAnalysis> = await apiClient.post(
        API_ENDPOINTS.advancedBiasDetection.intersectionalAnalysis,
        params
      )
      if (response.success && response.data) return response.data
      throw new Error(response.error || 'Intersectional analysis failed')
    } catch (err) {
      setError(err instanceof Error ? err : new Error('Intersectional analysis failed'))
      throw err
    } finally {
      setLoading(false)
    }
  }

  const runAdversarialTesting = async (params: any) => {
    try {
      setLoading(true)
      const response: ApiResponse<AdvancedBiasAnalysis> = await apiClient.post(
        API_ENDPOINTS.advancedBiasDetection.adversarialTesting,
        params
      )
      if (response.success && response.data) return response.data
      throw new Error(response.error || 'Adversarial testing failed')
    } catch (err) {
      setError(err instanceof Error ? err : new Error('Adversarial testing failed'))
      throw err
    } finally {
      setLoading(false)
    }
  }

  return {
    runCausalAnalysis,
    runCounterfactualAnalysis,
    runIntersectionalAnalysis,
    runAdversarialTesting,
    loading,
    error,
  }
}

