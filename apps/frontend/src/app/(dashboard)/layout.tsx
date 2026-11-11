'use client'

import { usePathname } from 'next/navigation'
import { AuthGuard } from '@/components/auth/AuthGuard'
import { SystemContextProvider } from '@/components/workflow/SystemContext'
import { OrgProvider } from '@/context/OrgContext'
import { NeedsYouProvider } from '@/astryx/data/needsYou'
import { SessionProvider } from '@/context/SessionContext'
import { AstryxShell } from '@/astryx/AstryxShell'

// Pages in the new menu are built on Astryx. Any other page is an older tool page: it keeps its own styles inside a padded frame.
const ASTRYX = /^\/(dashboard|needs-you|systems|discovery|plan|frameworks|policies|evaluations|runs|agent-audits|decisions|monitoring|findings|environment|evidence|auditor-packs|autopilot|ask|settings)$|^\/systems\/[^/]+$/

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
            <NeedsYouProvider>
              <AstryxShell>{ASTRYX.test(pathname ?? '') ? children : <div className="fm-legacy">{children}</div>}</AstryxShell>
            </NeedsYouProvider>
          </SystemContextProvider>
        </OrgProvider>
      </AuthGuard>
    </SessionProvider>
  )
}
