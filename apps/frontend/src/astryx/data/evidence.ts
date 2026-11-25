'use client'

import { useCallback, useEffect, useState } from 'react'
import { apiClient } from '@/lib/api/api-client'
import type { DecisionSeal } from '@/lib/api/hooks/useSystemFile'

/** The seals of one system, newest first. The latest seal's chain head and verification are the evidence chain. */
export function useSystemSeals(systemId: string | undefined) {
  const [seals, setSeals] = useState<DecisionSeal[]>([])
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState<string | null>(null)

  const reload = useCallback(async () => {
    if (!systemId) {
      setSeals([])
      return
    }
    setLoading(true)
    const res = await apiClient.get<DecisionSeal[]>(`/api/v1/ai-governance/systems/${systemId}/seals`)
    setError(res.success ? null : res.error || 'Could not load the seals')
    setSeals(res.success && Array.isArray(res.data) ? res.data : [])
    setLoading(false)
  }, [systemId])

  useEffect(() => {
    void reload()
  }, [reload])

  const latest = [...seals].sort((a, b) => b.createdAt.localeCompare(a.createdAt))[0] ?? null
  return { latest, loading, error, reload }
}
