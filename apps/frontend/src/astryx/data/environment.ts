'use client'

import { useCallback, useEffect, useState } from 'react'
import { apiClient } from '@/lib/api/api-client'

const root = (orgId: string, systemId: string) =>
  `/api/v1/ai-governance/organizations/${encodeURIComponent(orgId)}/systems/${encodeURIComponent(systemId)}/environmental-impact`

/** One stored environmental assessment as the API returns it (snake_case lives inside `result`). */
export interface EnvAssessment {
  assessmentId: string
  version: number | string
  createdAt: string
  impactTier?: string | null
  riskTier?: string | null
  confidenceBand?: string | null
  confidenceScore?: number | null
  recommendation?: string | null
  reviewerState?: string | null
  mitigationReadiness?: string | null
  measurementSource?: string | null
  provenanceClass?: string | null
  lifecyclePhase?: string | null
  metrics?: Record<string, number | null | undefined>
  result?: { requires_mitigation?: boolean; mitigation_blocking?: boolean; approval_blocking?: boolean } | null
}

interface EnvPayload {
  latest: EnvAssessment | null
  versionTrail: EnvAssessment[]
  empty?: boolean
}

/** Latest assessment and the version trail for one system. */
export function useEnvAssessments(orgId: string | undefined, systemId: string) {
  const [state, setState] = useState<{ latest: EnvAssessment | null; history: EnvAssessment[]; loading: boolean; error: string | null }>({
    latest: null,
    history: [],
    loading: true,
    error: null,
  })
  const load = useCallback(async () => {
    if (!orgId) return
    setState((s) => ({ ...s, loading: true, error: null }))
    const res = await apiClient.get<EnvPayload>(root(orgId, systemId), { enableRetry: false })
    if (res.success && res.data) {
      setState({ latest: res.data.latest ?? null, history: res.data.versionTrail ?? [], loading: false, error: null })
    } else {
      setState({ latest: null, history: [], loading: false, error: res.error || 'Could not load the environmental assessment' })
    }
  }, [orgId, systemId])
  useEffect(() => {
    void load()
  }, [load])
  return { ...state, reload: load }
}

/** POST /assess with the assessment body; throws the API's message on failure. */
export async function runEnvAssessment(orgId: string, systemId: string, assessment: Record<string, unknown>) {
  const res = await apiClient.post<unknown>(`${root(orgId, systemId)}/assess`, { assessment })
  if (!res.success) throw new Error(res.error || 'The assessment was not saved')
  return res
}

/** Fetches the CSRD (ESRS E1) disclosure and hands it to the browser as a JSON file. */
export async function downloadCsrd(orgId: string, systemId: string, name: string) {
  const res = await apiClient.get<Record<string, unknown>>(`${root(orgId, systemId)}/export`, { enableRetry: false })
  if (!res.success || !res.data) throw new Error(res.error || 'Nothing to export')
  const url = URL.createObjectURL(new Blob([JSON.stringify(res.data, null, 2)], { type: 'application/json' }))
  const a = document.createElement('a')
  a.href = url
  a.download = `csrd-${name.toLowerCase().replace(/[^a-z0-9]+/g, '-')}.json`
  a.click()
  URL.revokeObjectURL(url)
}

export interface EnvBenchmarks {
  provisional: boolean
  thresholds: Record<string, { metric: string; unit: string; low_max: number; high_min: number }>
}

export function useEnvBenchmarks() {
  const [state, setState] = useState<{ data: EnvBenchmarks | null; loading: boolean; error: string | null }>({ data: null, loading: true, error: null })
  useEffect(() => {
    let live = true
    void apiClient.get<EnvBenchmarks>('/api/v1/environment/benchmarks', { enableRetry: false }).then((res) => {
      if (live) setState({ data: res.success ? (res.data ?? null) : null, loading: false, error: res.success ? null : res.error || 'Could not load the thresholds' })
    })
    return () => {
      live = false
    }
  }, [])
  return state
}
