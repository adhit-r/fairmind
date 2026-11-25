'use client'

import { useCallback, useEffect, useState } from 'react'
import { apiClient } from '@/lib/api/api-client'

/** One item of a release, from its GitHub notes: "Name: what it does", and an app path when the notes link one. */
export interface ReleaseItem { name: string; text: string; href: string | null }
export interface Release {
  tag: string
  version: string
  title: string
  lead: string
  publishedAt: string | null
  url: string | null
  sections: Array<{ name: string; items: ReleaseItem[] }>
  changes: number
}
export interface WhatsNew { releases: Release[]; seen: string | null; emails: boolean }
export interface Announcements { releases: Array<Release & { sent: { sent_by: string; sent_at: string; recipients: number } | null }>; optedIn: number }

const message = (r: { error?: string; message?: string }) => r.error || r.message || 'Request failed'

/** FairMind's release notes and this person's read state and email choice. Not tied to an organisation. */
export function useWhatsNew() {
  const [data, setData] = useState<WhatsNew | null>(null)
  const [error, setError] = useState<string | null>(null)
  const load = useCallback(async () => {
    const r = await apiClient.get<WhatsNew>('/api/v1/whats-new')
    if (r.success && r.data) setData(r.data)
    else setError(message(r))
  }, [])
  useEffect(() => { void load() }, [load])
  const latest = data?.releases?.[0] ?? null // a reply without releases must not take the whole shell down
  return {
    data,
    error,
    unread: !!latest && data?.seen !== latest.tag,
    markSeen: async (tag: string) => {
      setData((d) => (d ? { ...d, seen: tag } : d))
      await apiClient.post('/api/v1/whats-new/seen', { tag })
    },
    setEmails: async (on: boolean): Promise<string | null> => {
      const r = await apiClient.put<{ emails: boolean }>('/api/v1/whats-new/emails', { on })
      if (!r.success) return message(r)
      setData((d) => (d ? { ...d, emails: on } : d))
      return null
    },
  }
}

/** Platform admin: recent releases, whether each was emailed, and how many people asked for release emails. */
export function useAnnouncements() {
  const [data, setData] = useState<Announcements | null>(null)
  const [error, setError] = useState<string | null>(null)
  const load = useCallback(async () => {
    const r = await apiClient.get<Announcements>('/api/v1/whats-new/announcements')
    if (r.success && r.data) setData(r.data)
    else setError(message(r))
  }, [])
  useEffect(() => { void load() }, [load])
  return {
    data,
    error,
    reload: load,
    announce: async (tag: string): Promise<string | null> => {
      const r = await apiClient.post<{ sent: number; of: number }>('/api/v1/whats-new/announce', { tag })
      await load()
      return r.success ? null : message(r)
    },
  }
}
