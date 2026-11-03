'use client'

import { useCallback, useEffect, useState } from 'react'
import { apiClient } from '../api-client'
import type { GateCheck } from './useSystemFile'

const GOV = '/api/v1/ai-governance'

export interface PackShare {
  shared: boolean
  expiresAt: string | null
  expired: boolean
}

export interface PackSummary {
  id: string
  title: string
  frameworks: string[]
  systemIds: string[]
  manifestHash: string
  createdBy: string | null
  createdAt: string
  share: PackShare
}

export interface PackSeal {
  id: string
  decision: 'approved' | 'rejected'
  chainHead: string
  evidenceCount: number
  sealedBy: string | null
  createdAt: string
  verification: { status: 'intact' | 'broken'; changed: string[]; missing: string[]; addedSince: number }
}

export interface PackClauseFramework {
  key: string
  name: string
  counts: { proven: number; attested: number; open: number; total: number }
}

export interface PackSystemEntry {
  system: { id: string; name: string; riskTier: string }
  gate: { verdict: 'go' | 'conditional_go' | 'no_go' | null; confidence: number | null; checks: GateCheck[]; reasons: string[] }
  clauseMap: { frameworks: PackClauseFramework[] }
  evidence: Array<{ id: string; type: string; hash: string; createdAt: string }>
  chainHead: string
  seals: PackSeal[]
}

export interface PackManifest {
  version: number
  title: string
  frameworks: string[]
  createdAt: string
  createdBy: string | null
  systems: PackSystemEntry[]
}

export interface PackDetail extends PackSummary {
  manifest: PackManifest
}

export interface PackFramework {
  key: string
  name: string
}

export interface PackShareResult {
  packId: string
  token: string
  expiresAt: string
}

/** The pack list and creation for the caller's organisation. */
export function useEvidencePacks() {
  const [packs, setPacks] = useState<PackSummary[]>([])
  const [frameworks, setFrameworks] = useState<PackFramework[]>([])
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)

  const refresh = useCallback(async () => {
    setLoading(true)
    const [list, fw] = await Promise.all([
      apiClient.get<PackSummary[]>(`${GOV}/packs`),
      apiClient.get<PackFramework[]>(`${GOV}/packs/frameworks`),
    ])
    setError(list.success ? null : list.error || 'Could not load inspection packs')
    setPacks(list.success && list.data ? list.data : [])
    setFrameworks(fw.success && fw.data ? fw.data : [])
    setLoading(false)
  }, [])

  useEffect(() => {
    void refresh()
  }, [refresh])

  const create = useCallback(
    async (input: { title: string; frameworks: string[]; systemIds: string[] }) => {
      const res = await apiClient.post<PackSummary>(`${GOV}/packs`, { title: input.title, frameworks: input.frameworks, system_ids: input.systemIds })
      if (res.success && res.data) await refresh()
      return res
    },
    [refresh],
  )

  return { packs, frameworks, loading, error, refresh, create }
}

/** One pack with its manifest, plus share, revoke and download. */
export function useEvidencePack(packId: string | undefined) {
  const [pack, setPack] = useState<PackDetail | null>(null)
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)

  const refresh = useCallback(async () => {
    if (!packId) return
    setLoading(true)
    const res = await apiClient.get<PackDetail>(`${GOV}/packs/${packId}`)
    setError(res.success ? null : res.error || 'Could not load this pack')
    setPack(res.success && res.data ? res.data : null)
    setLoading(false)
  }, [packId])

  useEffect(() => {
    void refresh()
  }, [refresh])

  const share = useCallback(async () => {
    const res = await apiClient.post<PackShareResult>(`${GOV}/packs/${packId}/share`)
    if (res.success) await refresh()
    return res
  }, [packId, refresh])

  const revoke = useCallback(async () => {
    const res = await apiClient.delete<{ packId: string; shared: boolean }>(`${GOV}/packs/${packId}/share`)
    if (res.success) await refresh()
    return res
  }, [packId, refresh])

  /** The pack as {manifest, manifestHash}, the file `fairmind verify` reads. */
  const download = useCallback(async () => {
    const res = await apiClient.get<{ manifest: PackManifest; manifestHash: string }>(`${GOV}/packs/${packId}/download`)
    if (!res.success || !res.data) return false
    const url = URL.createObjectURL(new Blob([JSON.stringify(res.data, null, 2)], { type: 'application/json' }))
    const link = document.createElement('a')
    link.href = url
    link.download = `inspection-pack-${packId}.json`
    link.click()
    URL.revokeObjectURL(url)
    return true
  }, [packId])

  return { pack, loading, error, refresh, share, revoke, download }
}
