'use client'

import { usePathname } from 'next/navigation'

import { AuthGuard } from '@/components/auth/AuthGuard'
import { ScopeBar, isSystemScopedRoute } from '@/components/patterns/ScopeBar'
import { SystemContextProvider } from '@/components/workflow/SystemContext'

/**
 * Dashboard shell content. OrgProvider is mounted by ClientNavigation (so the
 * sidebar and header can read org roles); this layout adds the AI-system
 * context and the compact ScopeBar on system-scoped routes only.
 */
export default function DashboardLayout({
  children,
}: {
  children: React.ReactNode
}) {
  const pathname = usePathname()

  return (
    <AuthGuard>
      <SystemContextProvider>
        {isSystemScopedRoute(pathname) && <ScopeBar />}
        {children}
      </SystemContextProvider>
    </AuthGuard>
  )
}
