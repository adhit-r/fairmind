'use client'

import { useCallback, useEffect, useState } from 'react'
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

export const usePacks = () => useResource<Pack[]>(API_ENDPOINTS.packs.list)
export const useJourney = (packId: string | undefined) =>
  useResource<Journey>(packId ? API_ENDPOINTS.packs.journey(packId) : null)
export const useWorkflow = (workflowId: string | undefined) =>
  useResource<Workflow>(workflowId ? API_ENDPOINTS.packs.workflow(workflowId) : null)
export const useRun = (runId: string | undefined) =>
  useResource<Run>(runId ? API_ENDPOINTS.packs.run(runId) : null)
/** Every run of the organisation, newest first. */
export const useRuns = () => useResource<RunSummary[]>(API_ENDPOINTS.packs.runs)
export const useWaitingRuns = () => useResource<RunSummary[]>(`${API_ENDPOINTS.packs.runs}?status=waiting`)

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

/** Mutations return the server's answer or its error; the caller then calls the page's reload. */
export const installPack = (packId: string) => mutate<Pack>(() => apiClient.post(API_ENDPOINTS.packs.install(packId)))

export const uninstallPack = (packId: string) => mutate<Pack>(() => apiClient.delete(API_ENDPOINTS.packs.install(packId)))

export const startRun = (workflowId: string, systemId?: string) =>
  mutate<Run>(() => apiClient.post(API_ENDPOINTS.packs.startRun(workflowId), systemId ? { system_id: systemId } : {}))

export const decideRun = (runId: string, decision: 'approve' | 'reject', notes?: string) =>
  mutate<Run>(() => apiClient.post(API_ENDPOINTS.packs.decision(runId), { decision, ...(notes ? { notes } : {}) }))
