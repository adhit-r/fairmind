/**
 * Single Model API Hook
 */

import { useState, useEffect, useCallback } from 'react'
import { apiClient, type ApiResponse } from '../api-client'
import { API_ENDPOINTS } from '../endpoints'
import type { Model } from '../types'

interface TestResult {
    analysis_id: string
    model_id: string
    score: number
    metrics: any
    recommendations: string[]
}

export interface TestConfig {
    dataset_id?: string
    target_column?: string
    sensitive_attributes?: string[]
}

export function useModel(id: string) {
    const [model, setModel] = useState<Model | null>(null)
    const [loading, setLoading] = useState(true)
    const [error, setError] = useState<Error | null>(null)

    // Test state
    const [testing, setTesting] = useState(false)
    const [testResult, setTestResult] = useState<TestResult | null>(null)
    const [testError, setTestError] = useState<Error | null>(null)

    const fetchModel = useCallback(async () => {
        if (!id) return

        try {
            setLoading(true)
            const response: ApiResponse<{ model: Model }> = await apiClient.get(
                API_ENDPOINTS.core.model(id)
            )

            if (response.success && response.data) {
                setModel(response.data.model)
                setError(null)
            } else {
                throw new Error(response.error || 'Failed to fetch model')
            }
        } catch (err) {
            setError(err instanceof Error ? err : new Error('Unknown error'))
            setModel(null)
        } finally {
            setLoading(false)
        }
    }, [id])

    const runTest = async (config?: TestConfig) => {
        if (!id) return

        try {
            setTesting(true)
            setTestError(null)

            const response: ApiResponse<TestResult> = await apiClient.post(
                API_ENDPOINTS.core.modelTest(id),
                config || {}
            )

            if (response.success && response.data) {
                setTestResult(response.data)
                // Refresh model to get updated scores
                fetchModel()
            } else {
                throw new Error(response.error || 'Test failed')
            }
        } catch (err) {
            setTestError(err instanceof Error ? err : new Error('Unknown error'))
        } finally {
            setTesting(false)
        }
    }

    useEffect(() => {
        fetchModel()
    }, [fetchModel])

    return {
        model,
        loading,
        error,
        refetch: fetchModel,
        runTest,
        testing,
        testResult,
        testError
    }
}
