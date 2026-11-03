'use client'

import { useCallback, useEffect, useState } from 'react'
import { apiClient, type ApiResponse } from '../api-client'

const BASE = '/api/v1/integrations'

export type IntegrationKind = 'mlflow' | 'github' | 'huggingface'

export interface Integration {
  id: string
  kind: IntegrationKind
  name: string
  config: Record<string, unknown>
  hasToken: boolean
  lastSyncedAt: string | null
  lastSync: { found?: number; created?: number; updated?: number; error?: string; at: string } | null
  createdAt: string
}

export interface DiscoveredAsset {
  id: string
  integrationId: string
  source: IntegrationKind
  externalId: string
  name: string
  kind: 'ml_model' | 'llm_app' | 'ai_assisted_dev'
  metadata: Record<string, any>
  suggestedTier: 'low' | 'medium' | 'high' | 'critical'
  suggestedStage: 'onboard' | 'assess' | 'govern' | 'remediate' | 'operate'
  status: 'new' | 'promoted' | 'ignored'
  systemId: string | null
  discoveredAt: string
}

function unwrap<T>(res: ApiResponse<T>): T {
  if (res.success && res.data !== undefined) return res.data
  throw new Error(res.error || 'Request failed')
}

export function useIntegrations() {
  const [integrations, setIntegrations] = useState<Integration[]>([])
  const [discovered, setDiscovered] = useState<DiscoveredAsset[]>([])
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)

  const refresh = useCallback(async () => {
    try {
      const [i, d] = await Promise.all([
        apiClient.get<Integration[]>(BASE),
        apiClient.get<DiscoveredAsset[]>(`${BASE}/discovered?status=new`),
      ])
      setIntegrations(unwrap(i))
      setDiscovered(unwrap(d))
      setError(null)
    } catch (e) {
      setError(e instanceof Error ? e.message : 'Failed to load integrations')
    } finally {
      setLoading(false)
    }
  }, [])

  useEffect(() => {
    refresh()
  }, [refresh])

  const create = async (body: { kind: IntegrationKind; name: string; config: Record<string, unknown>; token?: string }) => {
    unwrap(await apiClient.post<Integration>(BASE, body))
    await refresh()
  }
  const remove = async (id: string) => {
    unwrap(await apiClient.delete<null>(`${BASE}/${id}`))
    await refresh()
  }
  const sync = async (id: string) => {
    try {
      return unwrap(await apiClient.post<Integration['lastSync']>(`${BASE}/${id}/sync`, {}))
    } finally {
      await refresh()
    }
  }
  const promote = async (
    id: string,
    body: { risk_tier?: string; lifecycle_stage?: string; business_line?: string; owner?: string } = {},
  ) => {
    const out = unwrap(await apiClient.post<{ systemId: string }>(`${BASE}/discovered/${id}/promote`, body))
    await refresh()
    return out
  }
  const ignore = async (id: string) => {
    unwrap(await apiClient.post<{ status: string }>(`${BASE}/discovered/${id}/ignore`, {}))
    await refresh()
  }

  return { integrations, discovered, loading, error, refresh, create, remove, sync, promote, ignore }
}
