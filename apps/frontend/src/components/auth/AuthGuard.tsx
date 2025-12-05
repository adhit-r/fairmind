'use client'

import { useEffect, useState } from 'react'
import { useRouter } from 'next/navigation'
import { useAuth } from '@/lib/api/hooks/useAuth'
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
        const token = typeof window !== 'undefined' ? localStorage.getItem('access_token') : null
        if (!token) {
          router.push('/login')
          return
        }

        // Try to get current user
        try {
          await getCurrentUser()
          setIsChecking(false)
        } catch (err) {
          // If getCurrentUser fails, still allow access (might be API issue)
          setIsChecking(false)
        }
      } catch (error) {
        // Not authenticated, redirect to login
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

