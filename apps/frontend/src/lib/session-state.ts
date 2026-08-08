export const SESSION_CLEARED_EVENT = 'fairmind:session-cleared'
export const SESSION_CLEARED_STORAGE_KEY = 'fairmind:session-cleared'
export const SESSION_BROADCAST_CHANNEL = 'fairmind-session'

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

export type SessionIdentityResolution =
  | { state: 'authenticated'; user: SessionIdentity }
  | { state: 'clear'; reason: 'invalid_identity' | 'unauthorized' }
  | { state: 'error'; message: string }

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
      : { state: 'clear', reason: 'invalid_identity' }
  }

  if (response.apiError?.status === 401 || response.apiError?.status === 403) {
    return { state: 'clear', reason: 'unauthorized' }
  }

  return { state: 'error', message: response.error || 'Unable to verify the current session' }
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
