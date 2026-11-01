'use client'

import { useCallback, useEffect, useMemo, useState } from 'react'
import { useOrg } from '@/context/OrgContext'
import { apiClient, type ApiResponse } from '../api-client'
import { API_ENDPOINTS } from '../endpoints'

export type RunStatus = 'queued' | 'running' | 'waiting' | 'blocked' | 'done' | 'failed'
export type StepKind = 'trigger' | 'collect' | 'check' | 'suggest' | 'ask' | 'act' | 'file'

export interface RunSummary {
  id: string
  workflowId: string
  workflowName: string
  status: RunStatus
  currentStep: string | null
  createdAt: string
  updatedAt: string
}

export interface Pack {
  id: string
  name: string
  version: string
  description: string
  installed: boolean
  hasJourney: boolean
  workflowIds: string[]
}

export interface WorkflowRef {
  id: string
  name: string
  stage: string
  latestRun: RunSummary | null
}

export interface Journey {
  packId: string
  name: string
  installed: boolean
  clauses: Array<{ number: string; name: string; workflows: WorkflowRef[] }>
}

export interface Step {
  id: string
  kind: StepKind
  title: string
  detail: string
  systems: string[]
  next: Array<{ to: string; label: string | null }>
}

export interface Control {
  framework: string
  control: string
  relation: 'satisfies' | 'supports'
}

export interface Workflow {
  id: string
  name: string
  version: string
  stage: string
  description: string
  packId: string
  installed: boolean
  steps: Step[]
  controls: Control[]
  latestRun: RunSummary | null
}

export interface RunEvent {
  seq: number
  kind: string
  stepId: string | null
  payload: Record<string, unknown> | null
  prevHash: string | null
  hash: string
  createdAt: string
}

export interface Run extends RunSummary {
  systemId: string | null
  approvalRequestId: string | null
  approval: { status: string; decisionNotes: string | null } | null
  finishedAt: string | null
  events: RunEvent[]
  chainValid: boolean
}

export interface Resource<T> {
  data: T | null
  loading: boolean
  error: string | null
  reload: () => void
}

/** GET a path; a null path stays idle. Reload keeps the old data on screen while it refetches. */
function useResource<T>(path: string | null): Resource<T> {
  const [data, setData] = useState<T | null>(null)
  const [loading, setLoading] = useState(path !== null)
  const [error, setError] = useState<string | null>(null)
  const [tick, setTick] = useState(0)

  useEffect(() => {
    if (path === null) return
    let active = true
    setLoading(true)
    apiClient
      .get<T>(path)
      .then((res) => {
        if (!active) return
        if (res.success && res.data !== undefined) {
          setData(res.data)
          setError(null)
        } else {
          setError(res.error || res.message || 'Request failed')
        }
      })
      .catch((e: unknown) => active && setError(e instanceof Error ? e.message : 'Request failed'))
      .finally(() => active && setLoading(false))
    return () => {
      active = false
    }
  }, [path, tick])

  const reload = useCallback(() => setTick((t) => t + 1), [])
  return { data, loading, error, reload }
}

const withOrg = (path: string, orgId: string) => `${path}${path.includes('?') ? '&' : '?'}org_id=${encodeURIComponent(orgId)}`

/** A GET scoped to the organisation picked in the org switcher; waits while organisations load. */
function useOrgResource<T>(path: string | null): Resource<T> {
  const { selectedOrg, isLoading } = useOrg()
  const res = useResource<T>(path && selectedOrg ? withOrg(path, selectedOrg.id) : null)
  if (path && !selectedOrg) {
    return isLoading
      ? { ...res, loading: true }
      : { ...res, loading: false, error: 'Select an organisation to see its packs.' }
  }
  return res
}

export const usePacks = () => useOrgResource<Pack[]>(API_ENDPOINTS.packs.list)
export const useJourney = (packId: string | undefined) =>
  useOrgResource<Journey>(packId ? API_ENDPOINTS.packs.journey(packId) : null)
export const useWorkflow = (workflowId: string | undefined) =>
  useOrgResource<Workflow>(workflowId ? API_ENDPOINTS.packs.workflow(workflowId) : null)
export const useRun = (runId: string | undefined) =>
  useOrgResource<Run>(runId ? API_ENDPOINTS.packs.run(runId) : null)
/** Every run of the organisation, newest first. */
export const useRuns = () => useOrgResource<RunSummary[]>(API_ENDPOINTS.packs.runs)
export const useWaitingRuns = () => useOrgResource<RunSummary[]>(`${API_ENDPOINTS.packs.runs}?status=waiting`)

export interface MutationResult<T> {
  data: T | null
  error: string | null
}

async function mutate<T>(call: () => Promise<ApiResponse<T>>): Promise<MutationResult<T>> {
  try {
    const res = await call()
    if (res.success && res.data !== undefined) return { data: res.data, error: null }
    return { data: null, error: res.error || res.message || 'Request failed' }
  } catch (e) {
    return { data: null, error: e instanceof Error ? e.message : 'Request failed' }
  }
}

/** Mutations for the selected organisation. Each returns the server's answer or its error; the caller then calls the page's reload. */
export function usePackActions() {
  const { selectedOrg } = useOrg()
  const orgId = selectedOrg?.id
  return useMemo(() => {
    const send = <T,>(path: string, call: (scoped: string) => Promise<ApiResponse<T>>): Promise<MutationResult<T>> =>
      orgId ? mutate<T>(() => call(withOrg(path, orgId))) : Promise.resolve({ data: null, error: 'Select an organisation first.' })
    return {
      installPack: (packId: string) => send<Pack>(API_ENDPOINTS.packs.install(packId), (p) => apiClient.post(p)),
      uninstallPack: (packId: string) => send<Pack>(API_ENDPOINTS.packs.install(packId), (p) => apiClient.delete(p)),
      startRun: (workflowId: string, systemId?: string) =>
        send<Run>(API_ENDPOINTS.packs.startRun(workflowId), (p) => apiClient.post(p, systemId ? { system_id: systemId } : {})),
      decideRun: (runId: string, decision: 'approve' | 'reject', notes?: string) =>
        send<Run>(API_ENDPOINTS.packs.decision(runId), (p) => apiClient.post(p, { decision, ...(notes ? { notes } : {}) })),
    }
  }, [orgId])
}
