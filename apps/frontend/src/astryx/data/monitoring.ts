'use client'

import { useOrgResource } from '@/lib/api/hooks/usePacks'
import type { MonitoringPolicy, MonitoringRunSummary } from '@/lib/api/hooks/useSystemFile'

const GOV = '/api/v1/ai-governance'

/** One system's stored monitoring runs (newest first as the API returns them) and its watch cadence. */
export function useSystemMonitoring(systemId: string) {
  const base = `${GOV}/systems/${encodeURIComponent(systemId)}`
  const snapshots = useOrgResource<MonitoringRunSummary[]>(`${base}/monitoring-runs`)
  const cadence = useOrgResource<MonitoringPolicy>(`${base}/monitoring-policy`)
  const validPolicy = typeof cadence.data?.cadenceHours === 'number'
  return {
    runs: !snapshots.error && Array.isArray(snapshots.data) ? snapshots.data : [],
    policy: !cadence.loading && !cadence.error && validPolicy ? cadence.data : null,
    policyError: cadence.error || (!cadence.loading && !validPolicy ? 'The cadence response was incomplete.' : null),
    loading: snapshots.loading,
    error: snapshots.error || (!snapshots.loading && !Array.isArray(snapshots.data) ? 'The snapshot response was incomplete.' : null),
    reload: () => { snapshots.reload(); cadence.reload() },
  }
}
