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

/** One assessed control: the Statement of Applicability row, with the evidence a reviewer accepted for it. */
export interface PackControlApplicability {
  framework: string
  version: string
  control: string
  title: string
  applicability: string
  justification: string | null
  status: string
  owner: string | null
  updated_at: string
  accepted_evidence: string[]
}

export interface PackRisk {
  id: string
  title: string
  severity: string
  likelihood: string
  risk_score: number
  status: string
  mitigation: string
  source: string
  created_at: string
  updated_at: string
  // The latest accept or mitigate decision recorded for the risk; absent on older packs.
  // An acceptance also names who proposed it and who approved it; absent on mitigations and older packs.
  decision?: { decision: string; rationale: string; owner: string | null; decidedBy: string; decidedAt: string; proposedBy?: string | null; approvedBy?: string | null } | null
}

export interface PackRemediation {
  id: string
  title: string
  owner: string | null
  priority: string
  status: string
  due_date: string | null
  linked_risk_ids_json: string
  retest_status: string
  created_at: string
  updated_at: string
}

export interface PackControlLink {
  id: string
  evidence_id: string
  entity_type: string
  entity_id: string
  created_at: string
}

/** Packs built before these sections existed leave them out. */
export interface PackSystemEntry {
  system: { id: string; name: string; riskTier: string }
  gate: { verdict: 'go' | 'conditional_go' | 'no_go' | null; confidence: number | null; checks: GateCheck[]; reasons: string[] }
  clauseMap: { frameworks: ClauseMapFramework[] }
  evidence: PackEvidence[]
  chainHead: string
  seals: PackSeal[]
  controlApplicability?: PackControlApplicability[]
  risks?: PackRisk[]
  remediation?: PackRemediation[]
  controlLinks?: PackControlLink[]
}

export interface PackAttestation {
  task_key: string
  statement: string
  reference: string | null
  attested_by: string
  created_at: string
}

/** A done workflow run a reviewer did not reject. */
export interface PackWorkflowRun {
  id: string
  workflow_id: string
  workflow_version: string
  ai_system_id: string | null
  finished_at: string | null
  approval: string | null
  name: string | null
  common_control: string | null
}

export interface PackPolicy {
  id: string
  name: string
  framework: string
  description: string | null
  status: string
  version: number
  owner: string | null
  reviewer: string | null
  approver: string | null
  approved_at: string | null
  created_at: string
  updated_at: string
  versions: { version: number; status: string; description: string | null; changed_by: string | null; change_summary: string | null; created_at: string }[]
}

/** Organisation-level records; attestations only, in packs built before workflows and policies were added. */
export interface PackOrganisation {
  attestations: PackAttestation[]
  workflows?: PackWorkflowRun[]
  policies?: PackPolicy[]
}

export interface PackManifest {
  version: number
  title: string
  organisation?: PackOrganisation
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

  /** The pack as {manifest, manifestHash}, the file `fairmind verify` reads, or as one CSV of its records. Saved as the server's own bytes: re-serialising in the browser would change the numbers the hash covers. */
  const download = useCallback(async (format: 'json' | 'csv' = 'json') => {
    const res = await apiClient.get<Blob>(`${GOV}/packs/${packId}/download?format=${format}`, { responseType: 'blob' })
    if (!res.success || !res.data) return false
    const url = URL.createObjectURL(res.data)
    const link = document.createElement('a')
    link.href = url
    link.download = `inspection-pack-${packId}.${format}`
    link.click()
    URL.revokeObjectURL(url)
    return true
  }, [packId])

  return { pack, loading, error, refresh, share, revoke, download }
}
