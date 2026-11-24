'use client'

import type { DecisionSeal } from '@/lib/api/hooks/useSystemFile'
import { useOrgResource } from '@/lib/api/hooks/usePacks'

/** The seals of one system, newest first. The latest seal's chain head and verification are the evidence chain. */
export function useSystemSeals(systemId: string | undefined) {
  const { data, loading, error: requestError, reload } = useOrgResource<DecisionSeal[]>(
    systemId ? `/api/v1/ai-governance/systems/${encodeURIComponent(systemId)}/seals` : null,
  )
  const error = requestError || (systemId && !loading && !Array.isArray(data) ? 'Could not load the seals' : null)
  const latest = !error && Array.isArray(data) ? [...data].sort((a, b) => b.createdAt.localeCompare(a.createdAt))[0] ?? null : null
  return { latest, loading, error, reload }
}
