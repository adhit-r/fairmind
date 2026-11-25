import { apiClient } from '@/lib/api/api-client'
import type { PackShareResult } from '@/lib/api/hooks/useEvidencePacks'

const GOV = '/api/v1/ai-governance'

/** Saves a pack as {manifest, manifestHash}, the file `fairmind verify` reads. Saved as the server's own bytes: re-serialising in the browser would change the numbers the hash covers. */
export async function downloadPack(packId: string): Promise<string | null> {
  const res = await apiClient.get<Blob>(`${GOV}/packs/${packId}/download`, { responseType: 'blob' })
  if (!res.success || !res.data) return res.error || 'The pack could not be downloaded'
  const url = URL.createObjectURL(res.data)
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
