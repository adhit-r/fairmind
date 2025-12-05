/**
 * Modern Bias Detection API Hooks
 */

import { useState, useCallback } from 'react'
import { apiClient, type ApiResponse } from '../api-client'
import { API_ENDPOINTS } from '../endpoints'

export interface ModernBiasTestResult {
  testName: string
  testType: 'weat' | 'seat' | 'minimal-pairs' | 'stereoset' | 'bbq'
  biasScore: number
  confidence: number
  pValue?: number
  effectSize?: number
  isBiased: boolean
  details?: Record<string, any>
  recommendations?: string[]
  timestamp: string
}

export interface ComprehensiveEvaluationResult {
  overallBiasScore: number
  testResults: ModernBiasTestResult[]
  biasBreakdown: Record<string, number>
  recommendations: string[]
  timestamp: string
}

export function useModernBias() {
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState<Error | null>(null)

  const runComprehensiveEvaluation = async (params: {
    modelId: string
    datasetId: string
    testTypes?: string[]
    evaluationDatasets?: string[]
  }) => {
    try {
      setLoading(true)
      setError(null)

      const response: ApiResponse<ComprehensiveEvaluationResult> = await apiClient.post(
        API_ENDPOINTS.modernBiasDetection.comprehensiveEvaluation,
        params,
        {
          enableRetry: true,
          maxRetries: 3,
          timeout: 30000, // Longer timeout for comprehensive evaluation
        }
      )

      if (response.success && response.data) {
        return response.data
      } else {
        throw new Error(response.error || 'Comprehensive evaluation failed')
      }
    } catch (err) {
      const error = err instanceof Error ? err : new Error('Comprehensive evaluation failed')
      setError(error)
      throw error
    } finally {
      setLoading(false)
    }
  }

  const runWEATTest = async (params: {
    targetWords: string[]
    attributeWordsA: string[]
    attributeWordsB: string[]
    embeddings: Record<string, number[]>
  }) => {
    try {
      setLoading(true)
      setError(null)

      const response: ApiResponse<ModernBiasTestResult> = await apiClient.post(
        API_ENDPOINTS.biasDetection.testWeat,
        {
          target_words: params.targetWords,
          attribute_words_a: params.attributeWordsA,
          attribute_words_b: params.attributeWordsB,
          embeddings: JSON.stringify(params.embeddings),
        },
        {
          enableRetry: true,
          maxRetries: 3,
        }
      )

      if (response.success && response.data) {
        return response.data
      } else {
        throw new Error(response.error || 'WEAT test failed')
      }
    } catch (err) {
      const error = err instanceof Error ? err : new Error('WEAT test failed')
      setError(error)
      throw error
    } finally {
      setLoading(false)
    }
  }

  const getBiasTests = async () => {
    try {
      setLoading(true)
      setError(null)

      const response: ApiResponse<any> = await apiClient.get(
        API_ENDPOINTS.modernBiasDetection.biasTests,
        {
          enableRetry: true,
          maxRetries: 3,
        }
      )

      if (response.success && response.data) {
        return response.data
      } else {
        throw new Error(response.error || 'Failed to fetch bias tests')
      }
    } catch (err) {
      const error = err instanceof Error ? err : new Error('Failed to fetch bias tests')
      setError(error)
      throw error
    } finally {
      setLoading(false)
    }
  }

  const getBiasCategories = async () => {
    try {
      setLoading(true)
      setError(null)

      const response: ApiResponse<any> = await apiClient.get(
        API_ENDPOINTS.modernBiasDetection.biasCategories,
        {
          enableRetry: true,
          maxRetries: 3,
        }
      )

      if (response.success && response.data) {
        return response.data
      } else {
        throw new Error(response.error || 'Failed to fetch bias categories')
      }
    } catch (err) {
      const error = err instanceof Error ? err : new Error('Failed to fetch bias categories')
      setError(error)
      throw error
    } finally {
      setLoading(false)
    }
  }

  return {
    runComprehensiveEvaluation,
    runWEATTest,
    getBiasTests,
    getBiasCategories,
    loading,
    error,
  }
}

