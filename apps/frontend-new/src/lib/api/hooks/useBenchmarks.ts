/**
 * Benchmarks API Hooks
 */

import { useState, useEffect } from 'react'
import { apiClient, type ApiResponse } from '../api-client'
import { API_ENDPOINTS } from '../endpoints'

export interface Benchmark {
  id: string
  name: string
  type: string
  status: string
  results: any
  timestamp: string
}

export function useBenchmarks() {
  const [data, setData] = useState<Benchmark[]>([])
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<Error | null>(null)

  useEffect(() => {
    const fetchBenchmarks = async () => {
      try {
        setLoading(true)
        const response: ApiResponse<Benchmark[]> = await apiClient.get(
          API_ENDPOINTS.modelPerformanceBenchmarking.benchmarkRuns
        )

        if (response.success && response.data) {
          setData(response.data)
          setError(null)
        } else {
          throw new Error(response.error || 'Failed to fetch benchmarks')
        }
      } catch (err) {
        setError(err instanceof Error ? err : new Error('Unknown error'))
        setData([])
      } finally {
        setLoading(false)
      }
    }

    fetchBenchmarks()
  }, [])

  const runBenchmark = async (params: any) => {
    try {
      setLoading(true)
      const response: ApiResponse<Benchmark> = await apiClient.post(
        API_ENDPOINTS.modelPerformanceBenchmarking.runBenchmark,
        params
      )
      if (response.success && response.data) return response.data
      throw new Error(response.error || 'Benchmark run failed')
    } catch (err) {
      setError(err instanceof Error ? err : new Error('Benchmark run failed'))
      throw err
    } finally {
      setLoading(false)
    }
  }

  return { data, loading, error, runBenchmark }
}

