import { NextRequest, NextResponse } from 'next/server'

/**
 * A full Content Security Policy with a fresh script nonce per request (audit S3).
 *
 * Sent as Content-Security-Policy-Report-Only for now: browsers report what the
 * policy would block in the console and block nothing. Next.js reads the nonce
 * from this header and puts it on its own scripts. Once the console stays clean
 * in production, rename the header to Content-Security-Policy to enforce it.
 * next.config.js keeps enforcing the directives that need no nonce.
 */
const origin = (url: string | undefined) => {
  try {
    return url ? new URL(url).origin : ''
  } catch {
    return ''
  }
}

// Origins the browser talks to besides this one: an API on another origin (local
// development), Neon realtime, and Cloudflare Turnstile.
const API = origin(process.env.NEXT_PUBLIC_API_URL)
const REALTIME = origin(process.env.NEXT_PUBLIC_NEON_REALTIME_URL)
const TURNSTILE = 'https://challenges.cloudflare.com'

export const CSP_HEADER = 'Content-Security-Policy-Report-Only'

export function buildCsp(nonce: string, dev: boolean): string {
  return [
    "default-src 'self'",
    // strict-dynamic lets the nonce'd bundles load the chunks and the Turnstile script they add.
    `script-src 'self' 'nonce-${nonce}' 'strict-dynamic'${dev ? " 'unsafe-eval'" : ''}`,
    // Astryx and Tailwind set inline style attributes, which nonces cannot cover.
    "style-src 'self' 'unsafe-inline'",
    "img-src 'self' blob: data: https:",
    "font-src 'self' data:",
    `connect-src 'self' ${[...new Set([API, REALTIME, REALTIME.replace(/^http/, 'ws'), TURNSTILE])].filter(Boolean).join(' ')}`,
    `frame-src ${TURNSTILE}`,
    "worker-src 'self' blob:",
    "object-src 'none'",
    "base-uri 'self'",
    "form-action 'self'",
    "frame-ancestors 'none'",
  ].join('; ')
}

export function proxy(request: NextRequest) {
  const nonce = Buffer.from(crypto.randomUUID()).toString('base64')
  const csp = buildCsp(nonce, process.env.NODE_ENV === 'development')

  const requestHeaders = new Headers(request.headers)
  requestHeaders.set('x-nonce', nonce)
  requestHeaders.set(CSP_HEADER, csp)

  const response = NextResponse.next({ request: { headers: requestHeaders } })
  response.headers.set(CSP_HEADER, csp)
  return response
}

export const config = {
  // Pages only: not the API proxy, Next's static assets or files in public/.
  matcher: ['/((?!api/|_next/static|_next/image|favicon.ico|.*\\.(?:png|jpg|jpeg|svg|ico|webp|txt|xml)$).*)'],
}
