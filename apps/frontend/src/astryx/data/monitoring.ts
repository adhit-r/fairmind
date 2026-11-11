'use client'

import { useCallback, useEffect, useState } from 'react'
import { apiClient } from '@/lib/api/api-client'
import type { MonitoringPolicy, MonitoringRunSummary } from '@/lib/api/hooks/useSystemFile'

const GOV = '/api/v1/ai-governance'

/** One system's stored monitoring runs (newest first as the API returns them) and its watch cadence. */
export function useSystemMonitoring(systemId: string) {
  const [state, setState] = useState<{ runs: MonitoringRunSummary[]; policy: MonitoringPolicy | null; loading: boolean; error: string | null }>({
    runs: [],
    policy: null,
    loading: true,
    error: null,
  })
  const load = useCallback(async () => {
    setState((s) => ({ ...s, loading: true, error: null }))
    const [runs, policy] = await Promise.all([
      apiClient.get<MonitoringRunSummary[]>(`${GOV}/systems/${encodeURIComponent(systemId)}/monitoring-runs`),
      apiClient.get<MonitoringPolicy>(`${GOV}/systems/${encodeURIComponent(systemId)}/monitoring-policy`),
    ])
    setState({
      runs: runs.success && Array.isArray(runs.data) ? runs.data : [],
      policy: policy.success ? (policy.data ?? null) : null,
      loading: false,
      error: runs.success ? null : runs.error || 'Could not load the monitoring runs',
    })
  }, [systemId])
  useEffect(() => {
    void load()
  }, [load])
  return { ...state, reload: load }
}
