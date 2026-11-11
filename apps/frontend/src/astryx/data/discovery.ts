'use client'

import { useCallback, useEffect, useState } from 'react'
import { apiClient, type ApiResponse } from '@/lib/api/api-client'
import type { DiscoveredAsset, Integration, IntegrationKind } from '@/lib/api/hooks/useIntegrations'

export type { DiscoveredAsset, Integration, IntegrationKind }

const BASE = '/api/v1/integrations'

/** How each source reads on screen. */
export const SOURCE_LABEL: Record<string, string> = { mlflow: 'MLflow', github: 'GitHub', huggingface: 'Hugging Face' }
export const KIND_LABEL: Record<string, string> = { ml_model: 'Model', llm_app: 'LLM app', ai_assisted_dev: 'AI-assisted development' }

function unwrap<T>(res: ApiResponse<T>): T {
  if (res.success && res.data !== undefined) return res.data
  throw new Error(res.error || 'Request failed')
}

/** Connectors and every discovered item (new, promoted and ignored), with the write actions. */
export function useDiscovery() {
  const [integrations, setIntegrations] = useState<Integration[]>([])
  const [discovered, setDiscovered] = useState<DiscoveredAsset[]>([])
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)

  const refresh = useCallback(async () => {
    try {
      const [i, d] = await Promise.all([
        apiClient.get<Integration[]>(BASE),
        apiClient.get<DiscoveredAsset[]>(`${BASE}/discovered?status=all`),
      ])
      setIntegrations(unwrap(i))
      setDiscovered(unwrap(d))
      setError(null)
    } catch (e) {
      setError(e instanceof Error ? e.message : 'Could not load discovery')
    } finally {
      setLoading(false)
    }
  }, [])

  useEffect(() => {
    void refresh()
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
  const promote = async (id: string) => {
    const out = unwrap(await apiClient.post<{ systemId: string }>(`${BASE}/discovered/${id}/promote`, {}))
    await refresh()
    return out
  }
  const ignore = async (id: string) => {
    unwrap(await apiClient.post<{ status: string }>(`${BASE}/discovered/${id}/ignore`, {}))
    await refresh()
  }

  return { integrations, discovered, loading, error, refresh, create, remove, sync, promote, ignore }
}

export function when(iso: string | null | undefined): string {
  return iso ? new Date(iso).toLocaleString('en-GB', { day: 'numeric', month: 'short', hour: '2-digit', minute: '2-digit' }) : 'never'
}
