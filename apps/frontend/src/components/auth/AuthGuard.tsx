'use client'

import { useEffect, useState } from 'react'
import { useRouter } from 'next/navigation'
import { useAuth } from '@/lib/api/hooks/useAuth'
import { apiClient } from '@/lib/api/api-client'
import { Skeleton } from '@/components/ui/skeleton'

interface AuthGuardProps {
  children: React.ReactNode
}

export function AuthGuard({ children }: AuthGuardProps) {
  const router = useRouter()
  const { user, getCurrentUser, loading } = useAuth()
  const [isChecking, setIsChecking] = useState(true)

  useEffect(() => {
    const checkAuth = async () => {
      try {
        // The backend decides whether this session is signed in (a stored token,
        // or the local-development sign-in); a 401 sends us to /login.
        await getCurrentUser()
        setIsChecking(false)
      } catch {
        // Whatever token we held is not accepted; drop it so the next load starts clean.
        apiClient.clearSession()
        router.push('/login')
      }
    }

    checkAuth()
  }, [router, getCurrentUser])

  if (isChecking || loading) {
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

  if (!user) {
    return null // Will redirect
  }

  return <>{children}</>
}
