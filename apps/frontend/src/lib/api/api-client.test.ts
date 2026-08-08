import assert from 'node:assert/strict'
import test, { afterEach } from 'node:test'

import { ApiClient } from './api-client'

class MemoryStorage {
  private readonly values = new Map<string, string>()

  getItem(key: string) {
    return this.values.get(key) ?? null
  }

  setItem(key: string, value: string) {
    this.values.set(key, value)
  }

  removeItem(key: string) {
    this.values.delete(key)
  }
}

const originalWindow = globalThis.window
const originalFetch = globalThis.fetch

function installBrowser(storage = new MemoryStorage()) {
  Object.defineProperty(globalThis, 'window', {
    configurable: true,
    value: { localStorage: storage },
  })
  return storage
}

function response(status: number, payload: unknown): Response {
  return {
    ok: status >= 200 && status < 300,
    status,
    json: async () => payload,
  } as Response
}

afterEach(() => {
  Object.defineProperty(globalThis, 'window', {
    configurable: true,
    value: originalWindow,
  })
  globalThis.fetch = originalFetch
})

test('does not repopulate an authenticated cache after logout clears an in-flight response', async () => {
  const storage = installBrowser()
  storage.setItem('access_token', 'old-access')
  storage.setItem('refresh_token', 'old-refresh')
  const client = new ApiClient('https://fairmind.test')
  client.setAccessToken('old-access')
  client.setRefreshToken('old-refresh')

  let resolveFirstResponse!: (value: Response) => void
  const firstResponse = new Promise<Response>((resolve) => {
    resolveFirstResponse = resolve
  })
  let requestCount = 0
  globalThis.fetch = (async () => {
    requestCount += 1
    return requestCount === 1
      ? await firstResponse
      : response(200, { models: ['fresh'] })
  }) as typeof fetch

  const staleRequest = client.get<{ models: string[] }>('/api/v1/core/models', {
    enableRetry: false,
    useCache: true,
    cacheKey: 'authenticated-models',
  })
  client.clearSession()
  resolveFirstResponse(response(200, { models: ['stale'] }))

  const staleResult = await staleRequest
  assert.equal(staleResult.success, false)
  assert.equal(storage.getItem('access_token'), null)
  assert.equal(storage.getItem('refresh_token'), null)

  client.setAccessToken('new-access')
  const freshResult = await client.get<{ models: string[] }>('/api/v1/core/models', {
    enableRetry: false,
    useCache: true,
    cacheKey: 'authenticated-models',
  })
  assert.deepEqual(freshResult.data, { models: ['fresh'] })
  assert.equal(requestCount, 2)
})

test('does not restore an access token when logout races an in-flight refresh', async () => {
  const storage = installBrowser()
  storage.setItem('access_token', 'expired-access')
  storage.setItem('refresh_token', 'refresh-token')
  const client = new ApiClient('https://fairmind.test')
  client.setAccessToken('expired-access')
  client.setRefreshToken('refresh-token')

  let resolveRefresh!: (value: Response) => void
  const refreshResponse = new Promise<Response>((resolve) => {
    resolveRefresh = resolve
  })
  let signalRefreshStarted!: () => void
  const refreshStarted = new Promise<void>((resolve) => {
    signalRefreshStarted = resolve
  })
  globalThis.fetch = (async (url) => {
    if (String(url).endsWith('/api/v1/auth/refresh')) {
      signalRefreshStarted()
      return await refreshResponse
    }
    return response(401, { detail: 'expired' })
  }) as typeof fetch

  const request = client.get('/api/v1/auth/me', { enableRetry: false })
  await refreshStarted
  client.clearSession()
  resolveRefresh(response(200, { access_token: 'resurrected-access' }))

  const result = await request
  assert.equal(result.success, false)
  assert.equal(storage.getItem('access_token'), null)
  assert.equal(storage.getItem('refresh_token'), null)
})

test('keeps selected organization out of the current-user endpoint', async () => {
  const storage = installBrowser()
  storage.setItem('selected_org_id', 'organization-1')
  const client = new ApiClient('https://fairmind.test')
  const urls: string[] = []
  globalThis.fetch = (async (url) => {
    urls.push(String(url))
    return response(200, { id: 'user-1', username: 'reviewer', email: 'reviewer@example.com' })
  }) as typeof fetch

  await client.get('/api/v1/auth/me', { enableRetry: false })

  assert.deepEqual(urls, ['https://fairmind.test/api/v1/auth/me'])
})
