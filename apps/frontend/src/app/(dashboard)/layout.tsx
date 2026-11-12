'use client'

import Link from 'next/link'
import { usePathname, useSearchParams } from 'next/navigation'
import { Suspense } from 'react'
import { AuthGuard } from '@/components/auth/AuthGuard'
import { SystemContextProvider, useSystemContext } from '@/components/workflow/SystemContext'
import { OrgProvider } from '@/context/OrgContext'
import { NeedsYouProvider } from '@/astryx/data/needsYou'
import { SessionProvider } from '@/context/SessionContext'
import { AstryxShell } from '@/astryx/AstryxShell'

// Pages in the new menu are built on Astryx. Any other page is an older tool page: it keeps its own styles inside a padded frame.
const ASTRYX = /^\/(dashboard|needs-you|systems|discovery|plan|frameworks|policies|evaluations|runs|agent-audits|decisions|monitoring|findings|environment|evidence|auditor-packs|autopilot|ask|settings)$|^\/systems\/[^/]+$/

/** An older tool page opened from a system file keeps a way back to it. */
function BackToSystem() {
  const id = useSearchParams()?.get('system')
  const { systems } = useSystemContext()
  if (!id) return null
  const name = systems.find((s) => s.id === id)?.name ?? 'the system'
  return (
    <Link href={`/systems/${encodeURIComponent(id)}`} className="fm-legacy-back">
      Back to {name}
    </Link>
  )
}

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
              <AstryxShell>{ASTRYX.test(pathname ?? '') ? children : <div className="fm-legacy"><Suspense fallback={null}><BackToSystem /></Suspense>{children}</div>}</AstryxShell>
            </NeedsYouProvider>
          </SystemContextProvider>
        </OrgProvider>
      </AuthGuard>
    </SessionProvider>
  )
}
