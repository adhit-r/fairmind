'use client'

import { useCallback, useEffect, useState } from 'react'
import { apiClient } from '../api-client'

const GOV = '/api/v1/ai-governance'

export type AutopilotMode = 'off' | 'ask' | 'run'
export type DataPurpose = 'fairness' | 'monitoring'

export interface AutopilotStep {
  check: string
  action: 'fairness_run' | 'monitoring_snapshot' | 'environmental_assessment' | 'attest' | 'evidence_upload' | 'request_release'
  label: string
  evidenceClass: 'measured' | 'tool_estimated' | 'manual' | null
  gain: number
  note: string | null
  by: 'agent' | 'person'
  needs: string | null
  upkeep?: boolean
}

export interface DataSource {
  kind: 'upload' | 'url'
  url: string | null
  fileName: string | null
  attributes: string[]
  createdBy: string | null
  updatedAt: string
}

export interface AutopilotEvent {
  check: string
  action: string
  status: 'done' | 'failed'
  detail: string
  evidenceId: string | null
  actor: string
  at: string
}

export interface Autopilot {
  systemId: string
  owner: string | null
  mode: AutopilotMode
  lastRunAt: string | null
  gate: { verdict: string; confidence: number; approvalStatus: string | null }
  target: { verdict: string; confidence: number } | null
  afterAgent: number
  notes: string[]
  steps: AutopilotStep[]
  sources: Record<DataPurpose, DataSource | null>
  canConnect: boolean
  events: AutopilotEvent[]
}

export interface EstateAutopilot {
  systems: number
  doneThisWeek: number
  needsPerson: number
}

/** One system's release autopilot: its route, mode, data sources and trace. `reloadKey` refetches when the system file changes. */
export function useAutopilot(systemId: string | undefined, reloadKey?: unknown) {
  const [data, setData] = useState<Autopilot | null>(null)
  const [error, setError] = useState<string | null>(null)
  const base = systemId ? `${GOV}/systems/${encodeURIComponent(systemId)}` : null

  const load = useCallback(async () => {
    if (!base) return
    const res = await apiClient.get<Autopilot>(`${base}/autopilot`)
    if (res.success && res.data) setData(res.data)
    else setError(res.error || 'Could not load the autopilot')
  }, [base])

  useEffect(() => {
    void load()
  }, [load, reloadKey])

  // Each change returns the new view; a failure throws its message for the caller to show.
  const send = async (call: Promise<{ success: boolean; data?: Autopilot | null; error?: string }>) => {
    const res = await call
    if (!res.success || !res.data) throw new Error(res.error || 'Request failed')
    setData(res.data)
    setError(null)
    return res.data
  }

  return {
    data,
    error,
    reload: load,
    setMode: (mode: AutopilotMode) => send(apiClient.put<Autopilot>(`${base}/autopilot`, { mode }, { timeout: 120_000 })),
    // Runs fetch data and compute metrics; the client's 10s default is too short.
    runNow: (action?: string) =>
      send(apiClient.post<Autopilot>(`${base}/autopilot/run${action ? `?action=${action}` : ''}`, {}, { timeout: 120_000, enableRetry: false })),
    setSource: (purpose: DataPurpose, url: string) => send(apiClient.put<Autopilot>(`${base}/data-sources/${purpose}`, { url })),
    removeSource: (purpose: DataPurpose) => send(apiClient.delete<Autopilot>(`${base}/data-sources/${purpose}`)),
  }
}

export function useEstateAutopilot() {
  const [data, setData] = useState<EstateAutopilot | null>(null)
  useEffect(() => {
    void apiClient.get<EstateAutopilot>(`${GOV}/estate/autopilot`).then((res) => res.success && res.data && setData(res.data))
  }, [])
  return data
}
