'use client'

import { usePathname } from 'next/navigation'
import { AuthGuard } from '@/components/auth/AuthGuard'
import { SystemContextProvider } from '@/components/workflow/SystemContext'
import { OrgProvider } from '@/context/OrgContext'
import { SessionProvider } from '@/context/SessionContext'
import { AppShell } from '@/components/layout/AppShell'
import { SystemBreadcrumb } from '@/components/layout/SystemBreadcrumb'

// Pages rebuilt in the new shell carry their own context. Every other page is a
// legacy tool page and gets a one-line breadcrumb back to the system file.
const NEW_SHELL_PAGES = new Set(['/dashboard', '/onboard', '/integrations'])
const inNewShell = (pathname: string) =>
  NEW_SHELL_PAGES.has(pathname) || pathname.startsWith('/systems/') || pathname === '/frameworks' || pathname.startsWith('/frameworks/')

export default function DashboardLayout({
  children,
}: {
  children: React.ReactNode
}) {
  const pathname = usePathname()
  return (
    <SessionProvider>
      <AuthGuard>
        <OrgProvider>
          <SystemContextProvider>
            <AppShell>
              {!inNewShell(pathname ?? '') && <SystemBreadcrumb />}
              {children}
            </AppShell>
          </SystemContextProvider>
        </OrgProvider>
      </AuthGuard>
    </SessionProvider>
  )
}
