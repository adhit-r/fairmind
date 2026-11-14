'use client'

import { useCallback, useEffect, useState } from 'react'
import { useOrg } from '@/context/OrgContext'
import { apiClient } from '@/lib/api/api-client'
import type { Plan } from '@/lib/api/hooks/usePlan'

const PLAN = '/api/v1/plan'
const opts = { timeout: 90_000, enableRetry: false }

/** The governance plan with the writes the board needs, including the task note that `usePlan` does not send. */
export function usePlanBoard() {
  const { selectedOrg } = useOrg()
  const orgId = selectedOrg?.id
  const [data, setData] = useState<Plan | null>(null)
  const [error, setError] = useState<string | null>(null)
  const scoped = useCallback((path: string) => `${PLAN}${path}${path.includes('?') ? '&' : '?'}org_id=${encodeURIComponent(orgId ?? '')}`, [orgId])

  const reload = useCallback(async () => {
    if (!orgId) return
    setError(null)
    // The plan reads every system's release gate, so it can take longer than the client default.
    const res = await apiClient.get<Plan>(scoped(''), { timeout: 60_000 })
    if (res.success && res.data) setData(res.data)
    else setError(res.error || 'Could not load the plan')
  }, [orgId, scoped])

  useEffect(() => {
    void reload()
  }, [reload])

  const send = async (call: Promise<{ success: boolean; data?: Plan | null; error?: string }>) => {
    const res = await call
    if (!res.success || !res.data) throw new Error(res.error || 'Request failed')
    setData(res.data)
    setError(null)
    return res.data
  }
  const task = (key: string) => scoped(`/tasks/${encodeURIComponent(key)}`)

  return {
    data,
    error,
    reload,
    answer: (key: string, value: unknown) => send(apiClient.post<Plan>(scoped('/discovery'), { key, value }, opts)),
    generate: () => send(apiClient.post<Plan>(scoped('/generate'), {}, opts)),
    update: (key: string, patch: { owner?: string; note?: string }) => send(apiClient.patch<Plan>(task(key), patch, opts)),
    attest: (key: string, statement: string, reference: string) =>
      send(apiClient.post<Plan>(scoped(`/tasks/${encodeURIComponent(key)}/attest`), { statement, reference: reference || null }, opts)),
  }
}
