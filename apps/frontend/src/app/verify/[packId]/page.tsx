'use client'

import { useParams, useSearchParams } from 'next/navigation'
import { Suspense, useEffect, useState } from 'react'
import { Card } from '@/components/ui/card'
import type { PackManifest } from '@/lib/api/hooks/useEvidencePacks'
import { PackSummaryView, formatDate } from '@/components/evidence-packs/PackSummaryView'

interface PublicPack {
  id: string
  title: string
  manifestHash: string
  manifest: PackManifest
  expiresAt: string | null
}

const API_BASE = process.env.NEXT_PUBLIC_API_URL || '/api/proxy'

const REASONS: Record<number, string> = {
  404: 'This link is not valid. It may have been revoked, or the address is incomplete.',
  410: 'This link has expired. Ask the sender for a new one.',
}

function AuditorView() {
  const { packId } = useParams<{ packId: string }>()
  const token = useSearchParams().get('t')
  const [pack, setPack] = useState<PublicPack | null>(null)
  const [error, setError] = useState<string | null>(null)

  useEffect(() => {
    if (!token) {
      setError(REASONS[404])
      return
    }
    let cancelled = false
    fetch(`${API_BASE}/api/v1/public/packs/${encodeURIComponent(packId)}?t=${encodeURIComponent(token)}`, { headers: { Accept: 'application/json' }, referrerPolicy: 'no-referrer' })
      .then(async (res) => {
        if (cancelled) return
        if (res.ok) setPack(await res.json())
        else setError(REASONS[res.status] || 'The pack could not be loaded. Try again shortly.')
      })
      .catch(() => !cancelled && setError('The pack could not be loaded. Check your connection and try again.'))
    return () => {
      cancelled = true
    }
  }, [packId, token])

  if (error) return <p role="alert" className="text-sm text-[#b4232c]">{error}</p>
  if (!pack) return <p className="text-sm text-[var(--fm-ink2)]">Loading pack</p>

  return (
    <div className="flex flex-col gap-6">
      <div>
        <div className="text-[10.5px] font-semibold uppercase tracking-[0.08em] text-[var(--fm-ink3)]">Inspection pack, read only</div>
        <h1 className="mt-1 text-2xl font-semibold tracking-tight text-[var(--fm-ink)]">{pack.title}</h1>
        {pack.expiresAt && <p className="mt-1 text-sm text-[var(--fm-ink2)]">This link works until {formatDate(pack.expiresAt)}.</p>}
      </div>
      <PackSummaryView manifest={pack.manifest} manifestHash={pack.manifestHash} />
      <Card className="p-5">
        <h2 className="text-base font-semibold tracking-tight text-[var(--fm-ink)]">Verify offline</h2>
        <p className="mt-1 text-sm text-[var(--fm-ink2)]">
          You do not have to trust this page. Save the pack as <span className="font-mono">pack.json</span> (the file holds the manifest and its hash), then check it on your own machine with no network.
        </p>
        <pre className="mt-3 overflow-x-auto rounded-[10px] bg-[var(--fm-bg)] p-3 font-mono text-xs text-[var(--fm-ink)]">{`# from a checkout of the FairMind repository
pipx install ./apps/cli
fairmind verify pack.json`}</pre>
        <p className="mt-3 text-sm text-[var(--fm-ink2)]">
          The command recomputes the SHA-256 of the canonical manifest and each system&apos;s evidence chain head, prints what it found, and exits 0 only when both match.
        </p>
        <button
          type="button"
          className="mt-3 inline-flex h-9 items-center rounded-full border border-[var(--fm-line)] bg-white px-3.5 text-[12.5px] font-medium text-[var(--fm-ink2)] hover:border-[var(--fm-ink)] hover:text-[var(--fm-ink)]"
          onClick={() => {
            const url = URL.createObjectURL(new Blob([JSON.stringify({ manifest: pack.manifest, manifestHash: pack.manifestHash }, null, 2)], { type: 'application/json' }))
            const a = document.createElement('a')
            a.href = url
            a.download = 'pack.json'
            a.click()
            URL.revokeObjectURL(url)
          }}
        >
          Save pack.json
        </button>
      </Card>
    </div>
  )
}

export default function VerifyPackPage() {
  return (
    <main className="min-h-screen bg-[var(--fm-bg)] px-4 py-10 text-[var(--fm-ink)]">
      <div className="mx-auto max-w-4xl">
        <Suspense fallback={<p className="text-sm text-[var(--fm-ink2)]">Loading pack</p>}>
          <AuditorView />
        </Suspense>
      </div>
    </main>
  )
}
