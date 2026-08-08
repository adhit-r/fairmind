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

test('refreshes an expired current-user request once before returning its authenticated response', async () => {
  const storage = installBrowser()
  storage.setItem('access_token', 'expired-access')
  storage.setItem('refresh_token', 'refresh-token')
  const client = new ApiClient('https://fairmind.test')
  client.setAccessToken('expired-access')
  client.setRefreshToken('refresh-token')
  const urls: string[] = []
  let currentUserCalls = 0
  globalThis.fetch = (async (url) => {
    const target = String(url)
    urls.push(target)
    if (target.endsWith('/api/v1/auth/refresh')) {
      return response(200, { access_token: 'refreshed-access' })
    }
    currentUserCalls += 1
    return currentUserCalls === 1
      ? response(401, { detail: 'expired' })
      : response(200, { id: 'user-1', username: 'reviewer', email: 'reviewer@fairmind.test' })
  }) as typeof fetch

  const result = await client.get('/api/v1/auth/me', { enableRetry: false })

  assert.equal(result.success, true)
  assert.deepEqual(result.data, { id: 'user-1', username: 'reviewer', email: 'reviewer@fairmind.test' })
  assert.equal(storage.getItem('access_token'), 'refreshed-access')
  assert.deepEqual(urls, [
    'https://fairmind.test/api/v1/auth/me',
    'https://fairmind.test/api/v1/auth/refresh',
    'https://fairmind.test/api/v1/auth/me',
  ])
})

test('does not turn UI organization selection into API query authority', async () => {
  const storage = installBrowser()
  storage.setItem('selected_org_id', 'organization-1')
  const client = new ApiClient('https://fairmind.test')
  const urls: string[] = []
  globalThis.fetch = (async (url) => {
    urls.push(String(url))
    return response(200, { id: 'user-1', username: 'reviewer', email: 'reviewer@example.com' })
  }) as typeof fetch

  await client.get('/api/v1/auth/me', { enableRetry: false })
  await client.get('/api/v1/core/models', { enableRetry: false })
  await client.get(
    '/api/v1/ai-governance/organizations/organization-from-path/systems/system-1/evaluation-v2/plans',
    { enableRetry: false },
  )

  assert.deepEqual(urls, [
    'https://fairmind.test/api/v1/auth/me',
    'https://fairmind.test/api/v1/core/models',
    'https://fairmind.test/api/v1/ai-governance/organizations/organization-from-path/systems/system-1/evaluation-v2/plans',
  ])
})

test('preserves an explicitly supplied legacy organization query without replacing it', async () => {
  const storage = installBrowser()
  storage.setItem('selected_org_id', 'ui-selection-org')
  const client = new ApiClient('https://fairmind.test')
  const urls: string[] = []
  globalThis.fetch = (async (url) => {
    urls.push(String(url))
    return response(200, { data: [] })
  }) as typeof fetch

  await client.get('/api/v1/core/models?org_id=legacy-query-org', { enableRetry: false })

  assert.deepEqual(urls, ['https://fairmind.test/api/v1/core/models?org_id=legacy-query-org'])
})

test('preserves the catalog feature-disabled code from the real API error envelope', async () => {
  installBrowser()
  const client = new ApiClient('https://fairmind.test')
  globalThis.fetch = (async () => response(404, {
    detail: {
      code: 'assurance_feature_disabled',
      message: 'Evaluator catalog administration is not enabled.',
    },
  })) as typeof fetch

  const result = await client.get(
    '/api/v1/ai-governance/organizations/org-1/evaluation-v2/evaluator-catalog/registrations',
    { enableRetry: false },
  )

  assert.equal(result.success, false)
  assert.equal(result.apiError?.status, 404)
  assert.equal(result.apiError?.code, 'assurance_feature_disabled')
  assert.equal(result.error, 'Evaluator catalog administration is not enabled.')
})

test('preserves the exact catalog permission code from the real API error envelope', async () => {
  installBrowser()
  const client = new ApiClient('https://fairmind.test')
  globalThis.fetch = (async () => response(403, {
    detail: {
      code: 'evaluation_catalog_admin_forbidden',
      message: 'The evaluation:catalog:admin permission is required.',
    },
  })) as typeof fetch

  const result = await client.get(
    '/api/v1/ai-governance/organizations/org-1/evaluation-v2/evaluator-catalog/registrations',
    { enableRetry: false },
  )

  assert.equal(result.success, false)
  assert.equal(result.apiError?.status, 403)
  assert.equal(result.apiError?.code, 'evaluation_catalog_admin_forbidden')
  assert.equal(result.error, 'The evaluation:catalog:admin permission is required.')
})

test('does not treat a workflow code without nextAction as a decoded workflow envelope', async () => {
  installBrowser()
  const client = new ApiClient('https://fairmind.test')
  globalThis.fetch = (async () => response(409, {
    detail: {
      code: 'plan_archived',
      message: 'This plan is archived.',
    },
  })) as typeof fetch

  const result = await client.get('/api/v1/ai-governance/workflow', { enableRetry: false })

  assert.equal(result.success, false)
  assert.equal(result.error, 'This plan is archived.')
  assert.equal(result.apiError?.code, undefined)
  assert.equal(result.apiError?.nextAction, undefined)
})
