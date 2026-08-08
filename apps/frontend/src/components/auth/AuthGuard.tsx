'use client'

import { useEffect } from 'react'
import { useRouter } from 'next/navigation'
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
      <div className="flex items-center justify-center min-h-screen">
        <div className="space-y-4 w-full max-w-md p-6">
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
      <main className="flex min-h-screen items-center justify-center bg-[#F7F4EC] p-6">
        <section
          aria-labelledby="auth-guard-state-heading"
          className="w-full max-w-xl border-2 border-black bg-white p-6 shadow-[8px_8px_0_#111111]"
          role="alert"
        >
          <p className="mb-3 text-xs font-black uppercase tracking-[0.18em] text-[#0B6E69]">Session status</p>
          <h1 id="auth-guard-state-heading" className="text-2xl font-black tracking-tight text-black">{heading}</h1>
          <p className="mt-3 text-sm font-semibold leading-6 text-[#34312D]">{message}</p>
          <button
            className="mt-6 border-2 border-black bg-[#F47B20] px-4 py-2 text-sm font-black text-black shadow-[3px_3px_0_#111111] transition-transform hover:-translate-y-0.5 focus-visible:outline focus-visible:outline-2 focus-visible:outline-offset-4 focus-visible:outline-[#0B6E69]"
            onClick={() => { void refreshSession() }}
            type="button"
          >
            Retry session check
          </button>
        </section>
      </main>
    )
  }

  if (guardState === 'redirect') {
    return null
  }

  return <>{children}</>
}
