'use client'

import { useCallback, useEffect, useState } from 'react'
import { apiClient } from '../api-client'
import type { ClauseMapFramework, GateCheck } from './useSystemFile'

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

/** Version 1 packs carry neither the sealed gate, the decision id nor the approver's notes. */
export interface PackSeal {
  id: string
  decisionId?: string
  decision: 'approved' | 'rejected'
  chainHead: string
  evidenceCount: number
  gate?: { verdict?: string | null; riskTier?: string | null; effectiveTier?: string | null; reasons?: string[]; applicabilityEvidenceId?: string | null }
  sealedBy: string | null
  createdAt: string
  notes?: string | null
  verification: { status: 'intact' | 'broken'; changed: string[]; missing: string[]; addedSince: number }
}

/** From version 2 each record carries the fields its hash covers; content and metadata are the stored JSON text. */
export interface PackEvidence {
  id: string
  type: string
  hash: string
  createdAt: string
  title?: string | null
  source?: string | null
  content?: string
  confidence?: number | null
  status?: string | null
  metadata?: string | null
}

export interface PackSystemEntry {
  system: { id: string; name: string; riskTier: string }
  gate: { verdict: 'go' | 'conditional_go' | 'no_go' | null; confidence: number | null; checks: GateCheck[]; reasons: string[] }
  clauseMap: { frameworks: ClauseMapFramework[] }
  evidence: PackEvidence[]
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

  /** The pack as {manifest, manifestHash}, the file `fairmind verify` reads. Saved as the server's own bytes: re-serialising in the browser would change the numbers the hash covers. */
  const download = useCallback(async () => {
    const res = await apiClient.get<Blob>(`${GOV}/packs/${packId}/download`, { responseType: 'blob' })
    if (!res.success || !res.data) return false
    const url = URL.createObjectURL(res.data)
    const link = document.createElement('a')
    link.href = url
    link.download = `inspection-pack-${packId}.json`
    link.click()
    URL.revokeObjectURL(url)
    return true
  }, [packId])

  return { pack, loading, error, refresh, share, revoke, download }
}
