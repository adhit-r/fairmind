'use client'

import { useEffect } from 'react'
import { apiClient } from '@/lib/api/api-client'

/** Once per browser session, sends a signed-in person who has not decided yet to FairMind's Olai consent page. */
export function ConsentCheck() {
  useEffect(() => {
    try {
      if (sessionStorage.getItem('fm_consent_checked')) return
      sessionStorage.setItem('fm_consent_checked', '1')
    } catch {
      return
    }
    apiClient.get<{ required: boolean; url?: string }>('/api/v1/consent/status').then((res) => {
      if (res.success && res.data?.required && res.data.url) window.location.assign(res.data.url)
    })
  }, [])
  return null
}
