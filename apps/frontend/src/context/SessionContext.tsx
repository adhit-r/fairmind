'use client'

import React, { createContext, useCallback, useContext, useEffect, useMemo, useRef, useState } from 'react'

import { clearLLMJudgeCache } from '@/lib/api/hooks/useLLMJudge'
import { apiClient } from '@/lib/api/api-client'
import { API_ENDPOINTS } from '@/lib/api/endpoints'
import type { User } from '@/lib/api/types'
import {
  clearBrowserSessionState,
  CURRENT_SESSION_REQUEST_OPTIONS,
  createSingleFlight,
  endBrowserSession,
  publishSessionCleared,
  resolveSessionTransition,
  type SessionStatus,
  SESSION_BROADCAST_CHANNEL,
  SESSION_CLEARED_EVENT,
  SESSION_CLEARED_STORAGE_KEY,
} from '@/lib/session-state'

export interface SessionContextValue {
  user: User | null
  loading: boolean
  status: SessionStatus
  error: Error | null
  refreshSession: () => Promise<User | null>
  logout: () => Promise<void>
}

const SessionContext = createContext<SessionContextValue | undefined>(undefined)

export function SessionProvider({ children }: { children: React.ReactNode }) {
  const [user, setUser] = useState<User | null>(null)
  const [loading, setLoading] = useState(true)
  const [status, setStatus] = useState<SessionStatus>('loading')
  const [error, setError] = useState<Error | null>(null)
  const sessionRevision = useRef(0)
  const sessionLoad = useRef(createSingleFlight<User | null>())

  const clearLocalSession = useCallback((notifyOtherTabs: boolean) => {
    sessionRevision.current += 1
    sessionLoad.current.clear()
    apiClient.clearSession()
    clearLLMJudgeCache()

    if (typeof window !== 'undefined') {
      clearBrowserSessionState({
        localStorage: window.localStorage,
        sessionStorage: window.sessionStorage,
      })
    }

    setUser(null)
    setError(null)
    setLoading(false)
    setStatus('unauthenticated')

    if (notifyOtherTabs && typeof window !== 'undefined') {
      publishSessionCleared({
        localStorage: window.localStorage,
        dispatch: (eventName) => window.dispatchEvent(new Event(eventName)),
        createBroadcastChannel: typeof window.BroadcastChannel === 'function'
          ? () => new window.BroadcastChannel(SESSION_BROADCAST_CHANNEL)
          : undefined,
      })
    }
  }, [])

  const refreshSession = useCallback((): Promise<User | null> => {
    return sessionLoad.current.run(async () => {
      if (typeof window === 'undefined') return null

      apiClient.hydrateSession()
      if (!window.localStorage.getItem('access_token')) {
        clearLocalSession(false)
        return null
      }

      const requestRevision = sessionRevision.current
      setLoading(true)
      setStatus('loading')
      setError(null)

      const response = await apiClient.get<User>(
        API_ENDPOINTS.auth.me,
        CURRENT_SESSION_REQUEST_OPTIONS,
      )

      if (sessionRevision.current !== requestRevision) return null

      const transition = resolveSessionTransition(response)
      switch (transition.status) {
        case 'authenticated':
          setUser(transition.user)
          setLoading(false)
          setStatus('authenticated')
          return transition.user
        case 'unauthenticated':
          clearLocalSession(true)
          return null
        case 'denied':
        case 'unavailable':
          setUser(null)
          setError(new Error(transition.error))
          setLoading(false)
          setStatus(transition.status)
          return null
      }
    })
  }, [clearLocalSession])

  const logout = useCallback(async () => {
    await endBrowserSession({
      revoke: () => apiClient.post(API_ENDPOINTS.auth.logout, undefined, {
        enableRetry: false,
        refreshOnUnauthorized: false,
        timeout: 3_000,
      }),
      clear: () => clearLocalSession(true),
    })
  }, [clearLocalSession])

  useEffect(() => {
    void refreshSession()
  }, [refreshSession])

  useEffect(() => {
    if (typeof window === 'undefined') return

    const clearFromExternalSignal = () => clearLocalSession(false)
    const onStorage = (event: StorageEvent) => {
      if (event.key === SESSION_CLEARED_STORAGE_KEY && event.newValue) {
        clearFromExternalSignal()
      }
    }

    window.addEventListener(SESSION_CLEARED_EVENT, clearFromExternalSignal)
    window.addEventListener('storage', onStorage)

    let channel: BroadcastChannel | undefined
    try {
      if (typeof window.BroadcastChannel === 'function') {
        channel = new window.BroadcastChannel(SESSION_BROADCAST_CHANNEL)
        channel.onmessage = (event: MessageEvent<unknown>) => {
          const message = event.data
          if (
            message
            && typeof message === 'object'
            && (message as { type?: unknown }).type === SESSION_CLEARED_EVENT
          ) {
            clearFromExternalSignal()
          }
        }
      }
    } catch {
      channel = undefined
    }

    return () => {
      window.removeEventListener(SESSION_CLEARED_EVENT, clearFromExternalSignal)
      window.removeEventListener('storage', onStorage)
      channel?.close()
    }
  }, [clearLocalSession])

  const value = useMemo<SessionContextValue>(() => ({
    user,
    loading,
    status,
    error,
    refreshSession,
    logout,
  }), [error, loading, logout, refreshSession, status, user])

  return <SessionContext.Provider value={value}>{children}</SessionContext.Provider>
}

export function useSession(): SessionContextValue {
  const context = useContext(SessionContext)
  if (!context) {
    throw new Error('useSession must be used within a SessionProvider')
  }
  return context
}
