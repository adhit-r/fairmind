import { useState, useEffect, useCallback } from 'react'
import { apiClient } from '../api-client'
import { API_ENDPOINTS } from '../endpoints'

export interface TestResult {
    test_id: string
    model_id: string
    dataset_id?: string
    test_type: 'ml_bias' | 'llm_bias'
    timestamp: string
    overall_risk: 'low' | 'medium' | 'high' | 'critical'
    metrics_passed: number
    metrics_failed: number
    summary: string
    created_at: string
}

export interface TestHistoryResponse {
    tests: TestResult[]
    total: number
    limit: number
    offset: number
}

export interface TestStatistics {
    total_tests: number
    ml_tests: number
    llm_tests: number
    risk_distribution: {
        low: number
        medium: number
        high: number
        critical: number
    }
    pass_rate: number
    recent_tests: TestResult[]
}

export function useTestHistory(modelId?: string, testType?: string) {
    const [tests, setTests] = useState<TestResult[]>([])
    const [loading, setLoading] = useState(false)
    const [error, setError] = useState<string | null>(null)
    const [total, setTotal] = useState(0)

    const fetchTests = useCallback(async (limit = 50, offset = 0) => {
        setLoading(true)
        setError(null)
        try {
            const params = new URLSearchParams({
                limit: limit.toString(),
                offset: offset.toString(),
            })
            if (modelId) params.append('model_id', modelId)
            if (testType) params.append('test_type', testType)

            const response = await apiClient.get<TestHistoryResponse>(
                `${API_ENDPOINTS.biasV2.history}?${params.toString()}`,
                {
                    maxRetries: 2,
                    timeout: 10000,
                }
            )

            if (response) {
                const data = response as any
                setTests(data.tests || [])
                setTotal(data.total || 0)
            } else {
                setError('Failed to fetch test history')
                setTests([])
            }
        } catch (err) {
            setError(err instanceof Error ? err.message : 'Failed to fetch test history')
            setTests([])
        } finally {
            setLoading(false)
        }
    }, [modelId, testType])

    useEffect(() => {
        fetchTests()
    }, [fetchTests])

    return {
        tests,
        loading,
        error,
        total,
        fetchTests,
        refetch: () => fetchTests(),
    }
}

export function useTestStatistics(modelId?: string) {
    const [statistics, setStatistics] = useState<TestStatistics | null>(null)
    const [loading, setLoading] = useState(false)
    const [error, setError] = useState<string | null>(null)

    const fetchStatistics = useCallback(async () => {
        setLoading(true)
        setError(null)
        try {
            const params = modelId ? `?model_id=${modelId}` : ''
            const response = await apiClient.get<TestStatistics>(
                `${API_ENDPOINTS.biasV2.statistics}${params}`,
                {
                    maxRetries: 2,
                    timeout: 10000,
                }
            )

            if (response) {
                setStatistics(response as any)
            } else {
                setError('Failed to fetch statistics')
            }
        } catch (err) {
            setError(err instanceof Error ? err.message : 'Failed to fetch statistics')
        } finally {
            setLoading(false)
        }
    }, [modelId])

    useEffect(() => {
        fetchStatistics()
    }, [fetchStatistics])

    return {
        statistics,
        loading,
        error,
        refetch: fetchStatistics,
    }
}

export function useTestDetail(testId: string) {
    const [testDetail, setTestDetail] = useState<any | null>(null)
    const [loading, setLoading] = useState(false)
    const [error, setError] = useState<string | null>(null)

    const fetchTestDetail = useCallback(async () => {
        if (!testId) return

        setLoading(true)
        setError(null)
        try {
            const response = await apiClient.get(
                API_ENDPOINTS.biasV2.getTest(testId),
                {
                    maxRetries: 2,
                    timeout: 10000,
                }
            )

            if (response) {
                setTestDetail(response)
            } else {
                setError('Failed to fetch test details')
            }
        } catch (err) {
            setError(err instanceof Error ? err.message : 'Failed to fetch test details')
        } finally {
            setLoading(false)
        }
    }, [testId])

    useEffect(() => {
        fetchTestDetail()
    }, [fetchTestDetail])

    return {
        testDetail,
        loading,
        error,
        refetch: fetchTestDetail,
    }
}
