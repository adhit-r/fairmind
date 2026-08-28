export const SESSION_CLEARED_EVENT = 'fairmind:session-cleared'
export const SESSION_CLEARED_STORAGE_KEY = 'fairmind:session-cleared'
export const SESSION_BROADCAST_CHANNEL = 'fairmind-session'

/**
 * Do not retry transient request failures here, but allow ApiClient to perform
 * its single stored-refresh recovery when /auth/me returns an expired-token
 * 401. A final 401 is then safe to treat as terminal session loss.
 */
export const CURRENT_SESSION_REQUEST_OPTIONS = {
  enableRetry: false,
  timeout: 5_000,
} as const

type StorageLike = Pick<Storage, 'removeItem' | 'setItem'>

type SessionBroadcastChannel = {
  postMessage: (message: unknown) => void
  close: () => void
}

export interface BrowserSessionState {
  localStorage?: StorageLike
  sessionStorage?: Pick<Storage, 'removeItem'>
}

export interface SessionClearNotification {
  localStorage?: StorageLike
  dispatch: (eventName: string) => void
  createBroadcastChannel?: () => SessionBroadcastChannel
}

export interface BrowserSessionEnd {
  revoke: () => Promise<unknown>
  clear: () => void
}

export interface SessionIdentity {
  id: string
  username: string
  email: string
  role?: string
}

export interface SessionResponseLike {
  success: boolean
  data?: unknown
  error?: string
  apiError?: { status?: number }
}

export type SessionStatus =
  | 'loading'
  | 'authenticated'
  | 'unauthenticated'
  | 'denied'
  | 'unavailable'

export type SessionIdentityResolution =
  | { state: 'authenticated'; user: SessionIdentity }
  | { state: 'unauthenticated'; reason: 'invalid_identity' | 'unauthorized' | 'user_not_found' }
  | { state: 'denied'; message: string }
  | { state: 'unavailable'; message: string }

export type SessionTransition =
  | { status: 'authenticated'; user: SessionIdentity; clearLocalSession: false }
  | { status: 'unauthenticated'; clearLocalSession: true }
  | { status: 'denied'; error: string; clearLocalSession: false }
  | { status: 'unavailable'; error: string; clearLocalSession: false }

export interface SingleFlight<T> {
  run: (load: () => Promise<T>) => Promise<T>
  clear: () => void
}

/**
 * Shares one in-flight request with every caller, including React Strict Mode
 * effect replays, without retaining its result after the request settles.
 */
export function createSingleFlight<T>(): SingleFlight<T> {
  let pending: Promise<T> | null = null

  return {
    run(load) {
      if (pending) return pending

      let request: Promise<T>
      try {
        request = load()
      } catch (error) {
        request = Promise.reject(error)
      }
      pending = request
      void request.then(
        () => {
          if (pending === request) pending = null
        },
        () => {
          if (pending === request) pending = null
        },
      )
      return request
    },
    clear() {
      pending = null
    },
  }
}

function isSessionIdentity(value: unknown): value is SessionIdentity {
  if (!value || typeof value !== 'object') return false
  const user = value as Partial<SessionIdentity>
  return typeof user.id === 'string'
    && user.id.length > 0
    && typeof user.username === 'string'
    && user.username.length > 0
    && typeof user.email === 'string'
    && user.email.length > 0
}

/**
 * Treat malformed identity payloads as a terminal session state. Displaying a
 * partially-shaped account is less safe than requiring a fresh sign-in.
 */
export function resolveSessionIdentity(response: SessionResponseLike): SessionIdentityResolution {
  if (response.success) {
    return isSessionIdentity(response.data)
      ? { state: 'authenticated', user: response.data }
      : { state: 'unauthenticated', reason: 'invalid_identity' }
  }

  if (response.apiError?.status === 401) {
    return { state: 'unauthenticated', reason: 'unauthorized' }
  }

  // This resolver is only used for /auth/me. Its 404 contract means the JWT
  // subject no longer resolves to a user, so retaining credentials would leave
  // a deleted session looking recoverable.
  if (response.apiError?.status === 404) {
    return { state: 'unauthenticated', reason: 'user_not_found' }
  }

  if (response.apiError?.status === 403) {
    return { state: 'denied', message: response.error || 'The session endpoint denied this request' }
  }

  return { state: 'unavailable', message: response.error || 'Unable to verify the current session' }
}

/**
 * Keeps credential removal tied to a confirmed unauthenticated response. A
 * denied or unavailable current-session request remains visible to the guard
 * without erasing recoverable browser credentials.
 */
export function resolveSessionTransition(response: SessionResponseLike): SessionTransition {
  const identity = resolveSessionIdentity(response)

  switch (identity.state) {
    case 'authenticated':
      return { status: 'authenticated', user: identity.user, clearLocalSession: false }
    case 'unauthenticated':
      return { status: 'unauthenticated', clearLocalSession: true }
    case 'denied':
      return { status: 'denied', error: identity.message, clearLocalSession: false }
    case 'unavailable':
      return { status: 'unavailable', error: identity.message, clearLocalSession: false }
  }
}

/**
 * Removes only state that can identify an authenticated browser session.
 * Preferences remain intact so a logout never erases unrelated local settings.
 */
export function clearBrowserSessionState({
  localStorage,
  sessionStorage,
}: BrowserSessionState): void {
  localStorage?.removeItem('access_token')
  localStorage?.removeItem('refresh_token')
  localStorage?.removeItem('selected_org_id')
  sessionStorage?.removeItem('oauth_state')
  sessionStorage?.removeItem('code_verifier')
}

/**
 * Clears same-tab consumers and sends a best-effort message to sibling tabs.
 * The localStorage fallback covers browsers without BroadcastChannel support.
 */
export function publishSessionCleared({
  localStorage,
  dispatch,
  createBroadcastChannel,
}: SessionClearNotification): void {
  dispatch(SESSION_CLEARED_EVENT)

  try {
    const channel = createBroadcastChannel?.()
    if (channel) {
      channel.postMessage({ type: SESSION_CLEARED_EVENT })
      channel.close()
      return
    }
  } catch {
    // The storage event below remains a cross-tab fallback.
  }

  try {
    const eventId = `${Date.now()}-${Math.random().toString(36).slice(2)}`
    localStorage?.setItem(SESSION_CLEARED_STORAGE_KEY, eventId)
    localStorage?.removeItem(SESSION_CLEARED_STORAGE_KEY)
  } catch {
    // Storage may be disabled; the current tab was already notified.
  }
}

/**
 * Local cleanup is deliberately terminal: a failed best-effort revocation
 * must never leave the browser with a usable-looking session.
 */
export async function endBrowserSession({ revoke, clear }: BrowserSessionEnd): Promise<void> {
  let revocation: Promise<unknown> | undefined
  try {
    revocation = revoke()
  } catch {
    // A synchronous failure still reaches local cleanup below.
  }

  clear()

  try {
    await revocation
  } catch {
    // The caller can continue to the sign-in screen after local cleanup.
  }
}
