'use client'

import { useEffect } from 'react'
import { useRouter } from 'next/navigation'
import { Button } from '@/components/ui/button'
import { Skeleton } from '@/components/ui/skeleton'
import { useSession } from '@/context/SessionContext'
import { resolveAuthGuardState } from '@/lib/auth-guard-state'

interface AuthGuardProps {
  children: React.ReactNode
}

export function AuthGuard({ children }: AuthGuardProps) {
  const router = useRouter()
  const { user, status, error, refreshSession } = useSession()
  const guardState = resolveAuthGuardState({ user, status })

  useEffect(() => {
    if (guardState === 'redirect') router.replace('/login')
  }, [guardState, router])

  if (guardState === 'loading') {
    return (
      <div role="status" aria-live="polite" className="flex min-h-[60vh] items-center justify-center">
        <span className="sr-only">Checking your session</span>
        <div className="w-full max-w-md space-y-4 p-6">
          <Skeleton className="h-10 w-full" />
          <Skeleton className="h-10 w-full" />
          <Skeleton className="h-64 w-full" />
        </div>
      </div>
    )
  }

  if (guardState === 'denied' || guardState === 'unavailable') {
    const isDenied = guardState === 'denied'
    const heading = isDenied ? 'Session access denied' : 'Session check unavailable'
    const fallbackMessage = isDenied
      ? 'The session endpoint denied this request. Retry or contact an administrator.'
      : 'We could not verify this session. Check your connection and retry without signing out.'
    const message = isDenied ? fallbackMessage : error?.message || fallbackMessage

    return (
      <div className="flex min-h-[60vh] items-center justify-center p-4">
        <section
          aria-labelledby="auth-guard-state-heading"
          className="w-full max-w-xl rounded-lg border border-border bg-card p-6"
          role="alert"
        >
          <p className="eyebrow mb-2">Session status</p>
          <h1 id="auth-guard-state-heading" className="text-xl font-semibold tracking-tight text-foreground">{heading}</h1>
          <p className="mt-2 text-sm text-muted-foreground">{message}</p>
          <Button className="mt-5" variant="action" onClick={() => { void refreshSession() }} type="button">
            Retry session check
          </Button>
        </section>
      </div>
    )
  }

  if (guardState === 'redirect') {
    return null
  }

  return <>{children}</>
}
