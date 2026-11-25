'use client'

import { useEffect, useRef } from 'react'

/** Cloudflare Turnstile site key; without it the check is off and nothing renders. */
export const TURNSTILE_SITE_KEY = process.env.NEXT_PUBLIC_TURNSTILE_SITE_KEY || ''
/** The header config/turnstile.py reads. */
export const TURNSTILE_HEADER = 'X-Turnstile-Token'

type Turnstile = {
  render: (el: HTMLElement, options: Record<string, unknown>) => string
  reset: (id: string) => void
  remove: (id: string) => void
}
declare global {
  interface Window {
    turnstile?: Turnstile
  }
}

let loading: Promise<void> | null = null
function loadScript(): Promise<void> {
  loading ??= new Promise((resolve, reject) => {
    const s = document.createElement('script')
    s.src = 'https://challenges.cloudflare.com/turnstile/v0/api.js?render=explicit'
    s.async = true
    s.onload = () => resolve()
    s.onerror = () => {
      loading = null
      reject(new Error('Turnstile did not load'))
    }
    document.head.appendChild(s)
  })
  return loading
}

/**
 * The human check on public forms. Reports a token (or null when it expires or
 * fails); bump resetKey after each submit, since a token works once.
 */
export function HumanCheck({ onToken, resetKey = 0 }: { onToken: (token: string | null) => void; resetKey?: number }) {
  const box = useRef<HTMLDivElement>(null)
  const widget = useRef<string | null>(null)
  const report = useRef(onToken)
  report.current = onToken

  useEffect(() => {
    if (!TURNSTILE_SITE_KEY) return
    let cancelled = false
    loadScript()
      .then(() => {
        if (cancelled || !box.current || !window.turnstile) return
        widget.current = window.turnstile.render(box.current, {
          sitekey: TURNSTILE_SITE_KEY,
          callback: (t: string) => report.current(t),
          'expired-callback': () => report.current(null),
          'error-callback': () => report.current(null),
        })
      })
      .catch(() => report.current(null))
    return () => {
      cancelled = true
      if (widget.current && window.turnstile) window.turnstile.remove(widget.current)
      widget.current = null
    }
  }, [])

  useEffect(() => {
    if (resetKey && widget.current && window.turnstile) {
      window.turnstile.reset(widget.current)
      report.current(null)
    }
  }, [resetKey])

  if (!TURNSTILE_SITE_KEY) return null
  return <div ref={box} className="flex justify-center" />
}

/** Headers for a request from a form with a human check. */
export const humanCheckHeaders = (token: string | null): Record<string, string> =>
  token ? { [TURNSTILE_HEADER]: token } : {}

/** True when the form must wait for the check before it can submit. */
export const awaitingHumanCheck = (token: string | null) => Boolean(TURNSTILE_SITE_KEY) && !token
