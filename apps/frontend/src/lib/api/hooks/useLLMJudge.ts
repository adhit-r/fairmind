/**
 * Hook for LLM-as-Judge bias evaluation API calls
 * Handles API communication, loading states, and result caching
 */

import { useState, useCallback, useEffect } from 'react'
import { apiClient } from '../api-client'

// ============================================================================
// Types
// ============================================================================

export interface JudgeModel {
  value: string
  label: string
}

export interface BiasEvaluationResult {
  evaluation_id: string
  timestamp: string
  judge_model: string
  bias_category: string
  bias_score: number // 0.0 to 1.0
  confidence: number
  reasoning: string
  detected_biases: string[]
  severity: 'low' | 'medium' | 'high' | 'critical'
  recommendations: string[]
  evidence: string[]
  metadata: Record<string, any>
}

export interface BatchEvaluationResult {
  batch_id: string
  timestamp: string
  target_model: string
  judge_model: string
  results: Record<string, BiasEvaluationResult>
}

export interface MultiJudgeResult {
  timestamp: string
  text_length: number
  judges_used: string[]
  bias_categories: string[]
  results: Record<
    string,
    {
      judge_model: string
      evaluations: Record<
        string,
        {
          bias_score: number
          confidence: number
          severity: string
          reasoning: string
          detected_biases: string[]
        }
      >
    }
  >
}

export interface AvailableModels {
  models: JudgeModel[]
  categories: string[]
}

// ============================================================================
// Cache for Results
// ============================================================================

interface CacheEntry<T> {
  data: T
  timestamp: number
}

// Simple in-memory cache (5 minutes TTL)
const CACHE_TTL_MS = 5 * 60 * 1000
const resultCache = new Map<string, CacheEntry<any>>()

function getCacheKey(type: string, params: Record<string, any>): string {
  return `${type}:${JSON.stringify(params)}`
}

function setCachedResult<T>(key: string, data: T): void {
  resultCache.set(key, {
    data,
    timestamp: Date.now(),
  })
}

function getCachedResult<T>(key: string): T | null {
  const entry = resultCache.get(key)
  if (!entry) return null

  if (Date.now() - entry.timestamp > CACHE_TTL_MS) {
    resultCache.delete(key)
    return null
  }

  return entry.data as T
}

// ============================================================================
// useAvailableModels Hook
// ============================================================================

export function useAvailableModels() {
  const [models, setModels] = useState<JudgeModel[]>([])
  const [categories, setCategories] = useState<string[]>([])
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState<Error | null>(null)

  const fetchModels = useCallback(async () => {
    // Check cache first
    const cacheKey = getCacheKey('available-models', {})
    const cached = getCachedResult<AvailableModels>(cacheKey)
    if (cached) {
      setModels(cached.models)
      setCategories(cached.categories)
      return
    }

    setLoading(true)
    setError(null)

    try {
      const response = await apiClient.get<AvailableModels>('/api/v1/bias/llm-judge/models')
      if (!response.success || !response.data) {
        throw new Error(response.error || 'Failed to fetch available models')
      }
      setModels(response.data.models)
      setCategories(response.data.categories)

      // Cache the result
      setCachedResult(cacheKey, response.data)
    } catch (err) {
      const error = err instanceof Error ? err : new Error('Failed to fetch available models')
      setError(error)
      console.error('Error fetching available models:', error)
    } finally {
      setLoading(false)
    }
  }, [])

  // Fetch on mount
  useEffect(() => {
    fetchModels()
  }, [fetchModels])

  return { models, categories, loading, error, refetch: fetchModels }
}

// ============================================================================
// useEvaluateWithJudge Hook (Single Category)
// ============================================================================

export function useEvaluateWithJudge() {
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState<Error | null>(null)
  const [result, setResult] = useState<BiasEvaluationResult | null>(null)

  const evaluate = useCallback(
    async (
      text: string,
      judgeModel: string,
      biasCategories?: string[],
      targetModel: string = 'unknown'
    ): Promise<BiasEvaluationResult | null> => {
      setLoading(true)
      setError(null)
      setResult(null)

      try {
        const cacheKey = getCacheKey('evaluate', {
          text,
          judgeModel,
          biasCategories,
          targetModel,
        })

        // Check cache
        const cached = getCachedResult<BiasEvaluationResult>(cacheKey)
        if (cached) {
          setResult(cached)
          return cached
        }

        // Call API
        const response = await apiClient.post<BiasEvaluationResult>('/api/v1/bias/llm-judge/evaluate', {
          text,
          judge_model: judgeModel,
          bias_categories: biasCategories,
          target_model: targetModel,
        })
        if (!response.success || !response.data) {
          throw new Error(response.error || 'Bias evaluation failed')
        }

        setResult(response.data)
        setCachedResult(cacheKey, response.data)
        return response.data
      } catch (err) {
        const error = err instanceof Error ? err : new Error('Bias evaluation failed')
        setError(error)
        console.error('Error evaluating bias:', error)
        return null
      } finally {
        setLoading(false)
      }
    },
    []
  )

  const clearResult = useCallback(() => {
    setResult(null)
    setError(null)
  }, [])

  return {
    evaluate,
    result,
    loading,
    error,
    clearResult,
  }
}

// ============================================================================
// useBatchEvaluate Hook (Multiple Categories)
// ============================================================================

export function useBatchEvaluate() {
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState<Error | null>(null)
  const [result, setResult] = useState<BatchEvaluationResult | null>(null)

  const evaluateBatch = useCallback(
    async (
      text: string,
      judgeModel: string,
      biasCategories: string[],
      targetModel: string = 'unknown'
    ): Promise<BatchEvaluationResult | null> => {
      setLoading(true)
      setError(null)
      setResult(null)

      try {
        const cacheKey = getCacheKey('batch-evaluate', {
          text,
          judgeModel,
          biasCategories,
          targetModel,
        })

        // Check cache
        const cached = getCachedResult<BatchEvaluationResult>(cacheKey)
        if (cached) {
          setResult(cached)
          return cached
        }

        // Call API
        const response = await apiClient.post<BatchEvaluationResult>('/api/v1/bias/llm-judge/evaluate-batch', {
          text,
          judge_model: judgeModel,
          bias_categories: biasCategories,
          target_model: targetModel,
        })
        if (!response.success || !response.data) {
          throw new Error(response.error || 'Batch evaluation failed')
        }

        setResult(response.data)
        setCachedResult(cacheKey, response.data)
        return response.data
      } catch (err) {
        const error = err instanceof Error ? err : new Error('Batch evaluation failed')
        setError(error)
        console.error('Error in batch evaluation:', error)
        return null
      } finally {
        setLoading(false)
      }
    },
    []
  )

  const clearResult = useCallback(() => {
    setResult(null)
    setError(null)
  }, [])

  return {
    evaluateBatch,
    result,
    loading,
    error,
    clearResult,
  }
}

// ============================================================================
// useMultiJudgeEvaluation Hook
// ============================================================================

export function useMultiJudgeEvaluation() {
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState<Error | null>(null)
  const [result, setResult] = useState<MultiJudgeResult | null>(null)

  const evaluateWithMultipleJudges = useCallback(
    async (
      text: string,
      judgeModels: string[],
      biasCategories: string[]
    ): Promise<MultiJudgeResult | null> => {
      setLoading(true)
      setError(null)
      setResult(null)

      try {
        const cacheKey = getCacheKey('multi-judge-evaluate', {
          text,
          judgeModels,
          biasCategories,
        })

        // Check cache
        const cached = getCachedResult<MultiJudgeResult>(cacheKey)
        if (cached) {
          setResult(cached)
          return cached
        }

        // Call API
        const response = await apiClient.post<MultiJudgeResult>(
          '/api/v1/bias/llm-judge/evaluate-with-multiple-judges',
          {
            text,
            judge_models: judgeModels,
            bias_categories: biasCategories,
          }
        )
        if (!response.success || !response.data) {
          throw new Error(response.error || 'Multi-judge evaluation failed')
        }

        setResult(response.data)
        setCachedResult(cacheKey, response.data)
        return response.data
      } catch (err) {
        const error = err instanceof Error ? err : new Error('Multi-judge evaluation failed')
        setError(error)
        console.error('Error in multi-judge evaluation:', error)
        return null
      } finally {
        setLoading(false)
      }
    },
    []
  )

  const clearResult = useCallback(() => {
    setResult(null)
    setError(null)
  }, [])

  return {
    evaluateWithMultipleJudges,
    result,
    loading,
    error,
    clearResult,
  }
}

// ============================================================================
// Utility function to clear all cache
// ============================================================================

export function clearLLMJudgeCache(): void {
  resultCache.clear()
}
