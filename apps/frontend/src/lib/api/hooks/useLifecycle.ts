'use client'

import { useCallback, useEffect, useState } from 'react'
import { apiClient } from '../api-client'
import type { GateCheck, ReleaseGate } from './useSystemFile'

const GOV = '/api/v1/ai-governance'

export type PartKey = 'data' | 'model' | 'tools' | 'threshold' | 'use' | 'docs'
export type RetireReason = 'replaced' | 'not_needed' | 'failed_review' | 'rule_changed'
export type CheckKey = GateCheck['key']

export interface Part { key: PartKey; label: string; reopens: CheckKey[] }
export interface CheckSnapshot { key: CheckKey; label: string; state: GateCheck['state']; confidence: number }
export interface Chain { status: 'intact' | 'broken'; head?: string | null; at?: string }

export interface SystemChange {
  number: number
  parts: PartKey[]
  reopens: CheckKey[]
  material: boolean
  fromVersion: string | null
  toVersion: string | null
  note: string | null
  gateBefore: CheckSnapshot[]
  recordedBy: string
  createdAt: string
  seal: string
}

export interface RetireTask { key: string; label: string; who: 'person' | 'fairmind'; column: 'wind_down' | 'clean_up' | 'close_out'; done: boolean | null; by?: string }

export interface Retirement {
  reason: RetireReason
  replacedBy: string | null
  lastDay: string
  tasks: RetireTask[]
  retainUntil: string
  retainBasis: string | null
  note: string | null
  gateSnapshot: CheckSnapshot[]
  retiredBy: string
  retiredAt: string
  seal: string
}

export interface ChangesPayload { parts: Part[]; changes: SystemChange[]; chain: Chain }
export interface RetirementPayload { retired: Retirement | null; tasks: RetireTask[]; retention: { years: number; basis: string } | null; chain: Chain }

function useGet<T>(path: string | null) {
  const [data, setData] = useState<T | null>(null)
  const [error, setError] = useState<string | null>(null)
  const [loading, setLoading] = useState(Boolean(path))
  const refresh = useCallback(async () => {
    if (!path) return
    setLoading(true)
    const res = await apiClient.get<T>(path)
    if (res.success && res.data) {
      setData(res.data)
      setError(null)
    } else {
      setError(res.error || 'Could not load')
    }
    setLoading(false)
  }, [path])
  useEffect(() => { void refresh() }, [refresh])
  return { data, error, loading, refresh }
}

/** The parts a change can name, what each reopens, and the changes on file. */
export function useSystemChanges(systemId: string | undefined) {
  const q = useGet<ChangesPayload>(systemId ? `${GOV}/systems/${systemId}/changes` : null)
  const record = async (body: { parts: PartKey[]; toVersion?: string; note?: string }) => {
    const res = await apiClient.post<{ change: SystemChange; gate: ReleaseGate }>(`${GOV}/systems/${systemId}/changes`, body, { enableRetry: false })
    if (!res.success || !res.data) throw new Error(res.error || 'Could not record the change')
    await q.refresh()
    return res.data
  }
  return { ...q, record }
}

/** The retirement on file, or the closing tasks for the chosen reason and the suggested retention. */
export function useRetirement(systemId: string | undefined, reason?: RetireReason, replacedBy?: string) {
  const params = new URLSearchParams()
  if (reason) params.set('reason', reason)
  if (replacedBy) params.set('replacedBy', replacedBy)
  const qs = params.toString()
  const q = useGet<RetirementPayload>(systemId ? `${GOV}/systems/${systemId}/retirement${qs ? `?${qs}` : ''}` : null)
  const retire = async (body: { reason: RetireReason; replacedBy?: string; lastDay: string; retainYears: number; confirmed: string[]; note?: string }) => {
    const res = await apiClient.post<{ retired: Retirement }>(`${GOV}/systems/${systemId}/retire`, body, { enableRetry: false })
    if (!res.success || !res.data) throw new Error(res.error || 'Could not retire the system')
    return res.data.retired
  }
  return { ...q, retire }
}
