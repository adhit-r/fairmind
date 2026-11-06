import assert from 'node:assert/strict'
import test, { afterEach } from 'node:test'

import { POST } from './route'

const originalFetch = globalThis.fetch
afterEach(() => {
  globalThis.fetch = originalFetch
})

const post = (headers?: Record<string, string>) =>
  POST(new Request('http://localhost/api/live-notes', { method: 'POST', headers }))

test('refuses callers without a session the backend accepts, and never serves notes to those it does', async () => {
  const calls: Array<{ url: string; authorization: string | null }> = []
  let meStatus = 401
  globalThis.fetch = (async (url, init) => {
    calls.push({ url: String(url), authorization: new Headers(init?.headers).get('authorization') })
    return new Response('{}', { status: meStatus })
  }) as typeof fetch

  assert.equal((await post()).status, 401)
  assert.equal(calls.length, 0)

  assert.equal((await post({ Authorization: 'Bearer expired' })).status, 401)
  assert.ok(calls[0].url.endsWith('/api/v1/auth/me'))
  assert.equal(calls[0].authorization, 'Bearer expired')

  meStatus = 200
  assert.equal((await post({ Authorization: 'Bearer valid' })).status, 501)
})
