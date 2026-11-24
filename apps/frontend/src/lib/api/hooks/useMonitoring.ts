import { useEffect } from 'react'
import { pollWhileVisible } from '@/lib/poll'
import { API_ENDPOINTS } from '../endpoints'
import { useOrgResource } from './usePacks'

interface ServiceProbe {
  status?: string
  uptime?: string
  responseTime?: string
  response_time?: string
}

export interface SystemHealth {
  status: string
  timestamp?: string
  services?: Record<string, ServiceProbe | string | null>
}

export function useSystemHealth() {
  const { data, loading, error, reload } = useOrgResource<SystemHealth>(API_ENDPOINTS.aiGovernance.status)
  useEffect(() => pollWhileVisible(reload, 60000), [reload])
  const hasStatus = typeof data?.status === 'string' && data.status.trim().length > 0
  return {
    health: !loading && !error && hasStatus ? data : null,
    loading,
    error: error || (!loading && !hasStatus ? 'The endpoint returned no status.' : null),
    refetch: reload,
  }
}
