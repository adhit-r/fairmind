'use client'

import { useCallback, useEffect, useState } from 'react'
import { useOrg } from '@/context/OrgContext'
import { apiClient } from '../api-client'

const PLAN = '/api/v1/plan'

export type TaskState = 'todo' | 'needs_you' | 'agent' | 'review' | 'proven'
export type Options = Record<string, string>

export interface Question {
  key: string
  kind: 'text' | 'single' | 'multi' | 'maturity' | 'people' | 'frameworks'
  text: string
  why: string
  placeholder?: string
  options?: Options
  suggestedValue?: string[]
  suggestedBasis?: string
  controls?: Array<{ id: string; name: string; value: string | null }>
  suggested?: Array<{ key: string; name: string; reason: string }>
  selected?: string[]
  all?: Array<{ key: string; name: string; jurisdiction?: string }>
}

export interface Fact {
  key: string
  label: string
  value: unknown
  display: string
  source: 'answer' | 'description' | 'estate'
  basis?: string
}

export interface Discovery {
  status: 'discovery' | 'active'
  agent: 'llm' | 'rules'
  next: Question | null
  progress: { answered: number; total: number }
  transcript: Array<{ role: 'agent' | 'user'; key: string; text: string; at: string }>
  facts: Fact[]
  map: {
    frameworks: Array<{ key: string; name: string; reason: string; requirements: number }>
    controls: Array<{ id: string; name: string; lane: string; requirements: number; maturity: string | null }>
    outOfScope: Array<{ id: string; name: string; why: string }>
    systems: Array<{ id: string; name: string; riskTier: string; owner: string | null; confirmed: boolean }>
    owners: Array<{ role: string; label: string; person: string | null }>
  }
}

export interface PlanTask {
  key: string
  controlId: string
  controlName: string
  objective?: string
  title: string
  kind: 'org' | 'gate' | 'inventory' | 'system'
  lane: string
  requirements: Array<{ key: string; framework: string; control: string; title: string }>
  frameworks: string[]
  bindingCount: number
  dependsOn: string[]
  blockedBy?: string[]
  maturity: string | null
  by: 'agent' | 'person'
  owner: string | null
  ownerSuggested: string | null
  ownerReason: string
  note: string | null
  progress: { done: number; total: number }
  systems: Array<{ id: string; name: string; done: boolean; detail: string; agent: boolean }>
  actions: Array<{ id: string; name: string; scope?: string; approver?: string; installed: boolean }>
  attestation: { statement: string; reference: string | null; attested_by: string; created_at: string } | null
  state: TaskState
  priority: number
}

export interface Plan {
  exists: boolean
  status: 'discovery' | 'active'
  discovery: Discovery
  lanes: Array<{ key: string; label: string }>
  tasks?: PlanTask[]
  summary?: Record<TaskState, number>
  changes?: Array<{ summary: string; at: string }>
}

/** The organisation's governance plan: discovery until it is generated, then the board. */
export function usePlan() {
  const { selectedOrg } = useOrg()
  const orgId = selectedOrg?.id
  const [data, setData] = useState<Plan | null>(null)
  const [error, setError] = useState<string | null>(null)
  const scoped = useCallback((path: string) => `${PLAN}${path}${path.includes('?') ? '&' : '?'}org_id=${encodeURIComponent(orgId ?? '')}`, [orgId])

  const load = useCallback(async () => {
    if (!orgId) return
    // Computing the plan reads every system's release gate; give it longer than the client's 10s default.
    const res = await apiClient.get<Plan>(scoped(''), { timeout: 60_000 })
    if (res.success && res.data) setData(res.data)
    else setError(res.error || 'Could not load the plan')
  }, [orgId, scoped])

  useEffect(() => {
    void load()
  }, [load])

  const send = async (call: Promise<{ success: boolean; data?: Plan | null; error?: string }>) => {
    const res = await call
    if (!res.success || !res.data) throw new Error(res.error || 'Request failed')
    setData(res.data)
    setError(null)
    return res.data
  }
  const opts = { timeout: 90_000, enableRetry: false }

  return {
    data,
    error,
    reload: load,
    // Free text may be read by the organisation's model, which takes a while.
    answer: (key: string, value: unknown) => send(apiClient.post<Plan>(scoped('/discovery'), { key, value }, opts)),
    generate: () => send(apiClient.post<Plan>(scoped('/generate'), {}, opts)),
    assign: (key: string, owner: string) => send(apiClient.patch<Plan>(scoped(`/tasks/${encodeURIComponent(key)}`), { owner }, opts)),
    attest: (key: string, statement: string, reference: string) =>
      send(apiClient.post<Plan>(scoped(`/tasks/${encodeURIComponent(key)}/attest`), { statement, reference: reference || null }, opts)),
  }
}
