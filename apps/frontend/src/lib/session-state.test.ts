import assert from 'node:assert/strict'
import test from 'node:test'

import {
  clearBrowserSessionState,
  CURRENT_SESSION_REQUEST_OPTIONS,
  createSingleFlight,
  endBrowserSession,
  publishSessionCleared,
  resolveSessionIdentity,
  resolveSessionTransition,
  SESSION_CLEARED_EVENT,
  SESSION_CLEARED_STORAGE_KEY,
} from './session-state'

class MemoryStorage {
  private readonly values = new Map<string, string>()
  readonly removed: string[] = []
  readonly written: Array<[string, string]> = []

  setItem(key: string, value: string) {
    this.values.set(key, value)
    this.written.push([key, value])
  }

  getItem(key: string) {
    return this.values.get(key) ?? null
  }

  removeItem(key: string) {
    this.values.delete(key)
    this.removed.push(key)
  }
}

test('clears browser authentication, organization, and PKCE state', () => {
  const localStorage = new MemoryStorage()
  const sessionStorage = new MemoryStorage()
  localStorage.setItem('access_token', 'access-token')
  localStorage.setItem('refresh_token', 'refresh-token')
  localStorage.setItem('selected_org_id', 'organization-1')
  sessionStorage.setItem('oauth_state', 'oauth-state')
  sessionStorage.setItem('code_verifier', 'code-verifier')

  clearBrowserSessionState({ localStorage, sessionStorage })

  assert.deepEqual(localStorage.removed, [
    'access_token',
    'refresh_token',
    'selected_org_id',
  ])
  assert.deepEqual(sessionStorage.removed, ['oauth_state', 'code_verifier'])
})

test('lets a current-session 401 use the stored refresh token once', () => {
  assert.equal(CURRENT_SESSION_REQUEST_OPTIONS.enableRetry, false)
  assert.equal(CURRENT_SESSION_REQUEST_OPTIONS.timeout, 5_000)
  assert.equal('refreshOnUnauthorized' in CURRENT_SESSION_REQUEST_OPTIONS, false)
})

test('notifies this tab and other tabs when the session is cleared', () => {
  const localStorage = new MemoryStorage()
  const events: string[] = []
  const messages: unknown[] = []
  let closed = false

  publishSessionCleared({
    localStorage,
    dispatch: (eventName) => events.push(eventName),
    createBroadcastChannel: () => ({
      postMessage: (message) => messages.push(message),
      close: () => {
        closed = true
      },
    }),
  })

  assert.deepEqual(events, [SESSION_CLEARED_EVENT])
  assert.deepEqual(messages, [{ type: SESSION_CLEARED_EVENT }])
  assert.equal(closed, true)
  assert.deepEqual(localStorage.written, [])
})

test('falls back to a storage broadcast if BroadcastChannel is unavailable', () => {
  const localStorage = new MemoryStorage()
  const events: string[] = []

  publishSessionCleared({
    localStorage,
    dispatch: (eventName) => events.push(eventName),
  })

  assert.deepEqual(events, [SESSION_CLEARED_EVENT])
  assert.equal(localStorage.written.length, 1)
  assert.equal(localStorage.written[0]?.[0], SESSION_CLEARED_STORAGE_KEY)
  assert.deepEqual(localStorage.removed, [SESSION_CLEARED_STORAGE_KEY])
})

test('clears the local session before a slow server revocation settles', async () => {
  const events: string[] = []
  let resolveRevocation!: () => void
  const logout = endBrowserSession({
    revoke: () => new Promise<void>((resolve) => {
      resolveRevocation = resolve
    }),
    clear: () => events.push('cleared'),
  })

  assert.deepEqual(events, ['cleared'])
  resolveRevocation()
  await logout
})

test('still clears the local session when server revocation fails', async () => {
  const events: string[] = []

  await endBrowserSession({
    revoke: async () => {
      throw new Error('network unavailable')
    },
    clear: () => events.push('cleared'),
  })

  assert.deepEqual(events, ['cleared'])
})

test('fails closed when a successful current-user response is malformed', () => {
  assert.deepEqual(
    resolveSessionIdentity({
      success: true,
      data: { id: 'user-1', username: 'reviewer' },
    }),
    { state: 'unauthenticated', reason: 'invalid_identity' },
  )
})

test('separates unauthenticated, denied, and unavailable current-session outcomes', () => {
  assert.deepEqual(
    resolveSessionIdentity({
      success: false,
      error: 'Session expired',
      apiError: { status: 401 },
    }),
    { state: 'unauthenticated', reason: 'unauthorized' },
  )
  assert.deepEqual(
    resolveSessionIdentity({
      success: false,
      error: 'Insufficient permissions',
      apiError: { status: 403 },
    }),
    { state: 'denied', message: 'Insufficient permissions' },
  )
  assert.deepEqual(
    resolveSessionIdentity({
      success: false,
      error: 'Request timed out',
      apiError: { status: 0 },
    }),
    { state: 'unavailable', message: 'Request timed out' },
  )
})

test('clears browser credentials only for an explicit unauthenticated session outcome', () => {
  assert.deepEqual(
    resolveSessionTransition({
      success: false,
      error: 'Session expired',
      apiError: { status: 401 },
    }),
    { status: 'unauthenticated', clearLocalSession: true },
  )
  assert.deepEqual(
    resolveSessionTransition({
      success: false,
      error: 'User not found',
      apiError: { status: 404 },
    }),
    { status: 'unauthenticated', clearLocalSession: true },
  )
  assert.deepEqual(
    resolveSessionTransition({
      success: false,
      error: 'Request denied',
      apiError: { status: 403 },
    }),
    { status: 'denied', error: 'Request denied', clearLocalSession: false },
  )
  assert.deepEqual(
    resolveSessionTransition({
      success: false,
      error: 'Network unavailable',
      apiError: { status: 0 },
    }),
    { status: 'unavailable', error: 'Network unavailable', clearLocalSession: false },
  )
})

test('deduplicates concurrent current-session loads', async () => {
  const singleFlight = createSingleFlight<string>()
  let resolveLoad!: (value: string) => void
  const pending = new Promise<string>((resolve) => {
    resolveLoad = resolve
  })
  let calls = 0
  const load = () => {
    calls += 1
    return pending
  }

  const first = singleFlight.run(load)
  const second = singleFlight.run(load)

  assert.equal(first, second)
  assert.equal(calls, 1)
  resolveLoad('reviewer')
  assert.equal(await first, 'reviewer')
})
