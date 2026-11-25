'use client'

import Link from 'next/link'
import { useParams } from 'next/navigation'
import { AuthGuard } from '@/components/auth/AuthGuard'
import { OrgProvider } from '@/context/OrgContext'
import { SessionProvider } from '@/context/SessionContext'
import { AuditorReport } from '@/components/evidence-packs/AuditorReport'
import { useEvidencePack } from '@/lib/api/hooks/useEvidencePacks'

/** A built pack exactly as the auditor portal shows it, for the people who built it, before or after they share it. */
function Preview() {
  const { packId } = useParams<{ packId: string }>()
  const { pack, loading, error } = useEvidencePack(packId)
  return (
    <main className="min-h-screen bg-[var(--fm-bg)] px-4 py-6 text-[var(--fm-ink)]">
      <div className="mx-auto flex max-w-5xl flex-col gap-6">
        <div role="status" className="flex flex-wrap items-center justify-between gap-3 rounded-[14px] bg-[var(--fm-ink)] px-5 py-3 text-sm text-white">
          <span>Preview: this is what your auditor sees. Nothing here is shared until you share the link.</span>
          <Link href="/auditor-packs" className="font-medium text-white underline">Back to packs</Link>
        </div>
        {loading && !pack ? (
          <p className="text-sm text-[var(--fm-ink2)]">Loading the pack.</p>
        ) : error || !pack ? (
          <p role="alert" className="text-sm text-[var(--fm-ink2)]">{error || 'The pack could not be loaded.'}</p>
        ) : (
          <AuditorReport manifest={pack.manifest} manifestHash={pack.manifestHash} expiresAt={pack.share.shared ? pack.share.expiresAt : null} />
        )}
      </div>
    </main>
  )
}

export default function AuditorPreviewPage() {
  return (
    // the dashboard's providers without its shell: the page shows exactly what the auditor portal shows
    <SessionProvider>
      <AuthGuard>
        <OrgProvider>
          <Preview />
        </OrgProvider>
      </AuthGuard>
    </SessionProvider>
  )
}
