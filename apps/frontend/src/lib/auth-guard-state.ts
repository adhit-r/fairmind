import type { SessionStatus } from './session-state'

export type AuthGuardState =
  | 'loading'
  | 'authenticated'
  | 'redirect'
  | 'denied'
  | 'unavailable'

export interface AuthGuardSession {
  user: unknown | null
  status: SessionStatus
}

/**
 * Only an explicit unauthenticated outcome may enter the login redirect path.
 * A failed session check is indeterminate, not a signal to discard the
 * browser session or send the user to sign in again.
 */
export function resolveAuthGuardState({ user, status }: AuthGuardSession): AuthGuardState {
  if (status === 'loading') return 'loading'
  if (status === 'unavailable') return 'unavailable'
  if (status === 'denied') return 'denied'
  if (status === 'authenticated' && user) return 'authenticated'
  return 'redirect'
}
