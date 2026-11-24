'use client'

import Link from 'next/link'
import { usePathname, useSearchParams } from 'next/navigation'
import { recordParam } from '@/lib/assurance/evaluationLinks'
import { Suspense } from 'react'
import { AuthGuard } from '@/components/auth/AuthGuard'
import { ConsentCheck } from '@/components/auth/ConsentCheck'
import { SystemContextProvider, useSystemContext } from '@/components/workflow/SystemContext'
import { OrgProvider } from '@/context/OrgContext'
import { NeedsYouProvider } from '@/astryx/data/needsYou'
import { SessionProvider } from '@/context/SessionContext'
import { AstryxShell } from '@/astryx/AstryxShell'

// Pages in the new menu are built on Astryx. Any other page is an older tool page: it keeps its own styles inside a padded frame.
const ASTRYX = /^\/(dashboard|needs-you|systems|discovery|shadow-ai|plan|frameworks|policies|evaluations|runs|agent-audits|decisions|monitoring|findings|environment|evidence|auditor-packs|reports(?:\/system)?|autopilot|ask|settings)$|^\/systems\/[^/]+$/

/** An older tool page opened from a system file keeps a way back to it. */
function BackToSystem() {
  const id = recordParam(useSearchParams(), 'system')
  const { systems } = useSystemContext()
  const system = systems.find((s) => s.id === id && s.metadata?.source !== 'fallback')
  if (!system) return null
  return (
    <Link href={`/systems/${encodeURIComponent(system.id)}`} className="fm-legacy-back">
      Back to {system.name}
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
        <ConsentCheck />
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
