import { apiClient } from '@/lib/api/api-client'
import type { PackManifest, PackShareResult } from '@/lib/api/hooks/useEvidencePacks'

const GOV = '/api/v1/ai-governance'

/** Saves a pack as {manifest, manifestHash}, the file `fairmind verify` reads. */
export async function downloadPack(packId: string): Promise<string | null> {
  const res = await apiClient.get<{ manifest: PackManifest; manifestHash: string }>(`${GOV}/packs/${packId}/download`)
  if (!res.success || !res.data) return res.error || 'The pack could not be downloaded'
  const url = URL.createObjectURL(new Blob([JSON.stringify(res.data, null, 2)], { type: 'application/json' }))
  const link = document.createElement('a')
  link.href = url
  link.download = `inspection-pack-${packId}.json`
  link.click()
  URL.revokeObjectURL(url)
  return null
}

export async function sharePack(packId: string) {
  return apiClient.post<PackShareResult>(`${GOV}/packs/${packId}/share`)
}

export async function stopSharingPack(packId: string) {
  return apiClient.delete<{ packId: string; shared: boolean }>(`${GOV}/packs/${packId}/share`)
}
