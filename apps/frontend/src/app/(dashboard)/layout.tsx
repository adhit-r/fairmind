'use client'

import { usePathname } from 'next/navigation'
import { AuthGuard } from '@/components/auth/AuthGuard'
import {
  SystemContextBar,
  SystemContextProvider,
} from '@/components/workflow/SystemContext'
import { OrgProvider } from '@/context/OrgContext'
import { AppShell } from '@/components/layout/AppShell'

// Pages already rebuilt in the new shell; the legacy context bar stays on the rest until they are.
const NEW_SHELL_PAGES = new Set(['/dashboard', '/onboard', '/integrations'])

export default function DashboardLayout({
  children,
}: {
  children: React.ReactNode
}) {
  const pathname = usePathname()
  return (
    <AuthGuard>
      <OrgProvider>
        <SystemContextProvider>
          <AppShell>
            {!NEW_SHELL_PAGES.has(pathname ?? '') && <SystemContextBar />}
            {children}
          </AppShell>
        </SystemContextProvider>
      </OrgProvider>
    </AuthGuard>
  )
}
