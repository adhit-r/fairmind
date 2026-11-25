'use client'

import { useParams, useSearchParams } from 'next/navigation'
import { Suspense, useEffect, useState } from 'react'
import { Card } from '@/components/ui/card'
import type { PackManifest } from '@/lib/api/hooks/useEvidencePacks'
import { AuditorReport } from '@/components/evidence-packs/AuditorReport'

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

/** The pack's frame for loading and error states, so a failed link still looks like FairMind. */
function Notice({ title, body, alert = false }: { title: string; body: string; alert?: boolean }) {
  return (
    <Card className="p-6">
      <div className="text-[10.5px] font-semibold uppercase tracking-[0.08em] text-[var(--fm-ink3)]">FairMind inspection pack</div>
      <h1 className="mt-1 text-xl font-semibold tracking-tight text-[var(--fm-ink)]">{title}</h1>
      <p role={alert ? 'alert' : 'status'} className="mt-2 text-sm text-[var(--fm-ink2)]">{body}</p>
    </Card>
  )
}

function AuditorView() {
  const { packId } = useParams<{ packId: string }>()
  const token = useSearchParams().get('t')
  const [pack, setPack] = useState<PublicPack | null>(null)
  // The response exactly as the server wrote it: JSON.stringify would turn 0.0 into 0 and the saved file would not verify.
  const [raw, setRaw] = useState('')
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
        if (res.ok) {
          const body = await res.text()
          if (cancelled) return
          setRaw(body)
          setPack(JSON.parse(body))
        } else setError(REASONS[res.status] || 'The pack could not be loaded. Try again shortly.')
      })
      .catch(() => !cancelled && setError('The pack could not be loaded. Check your connection and try again.'))
    return () => {
      cancelled = true
    }
  }, [packId, token])

  if (error) return <Notice title="This pack cannot be shown" body={error} alert />
  if (!pack) return <Notice title="Loading the inspection pack" body="Checking the link and fetching the manifest." />
  const apiAddress = new URL(API_BASE, window.location.href).href.replace(/\/$/, '')
  const save = () => {
    const url = URL.createObjectURL(new Blob([raw], { type: 'application/json' }))
    const a = document.createElement('a')
    a.href = url
    a.download = 'pack.json'
    a.click()
    URL.revokeObjectURL(url)
  }

  return (
    <AuditorReport
      manifest={pack.manifest}
      manifestHash={pack.manifestHash}
      expiresAt={pack.expiresAt}
      verifyHint={
        <>
          <p className="ar-muted">Or let the CLI fetch this pack from its link and check it locally:</p>
          <pre className="ar-pre">{`fairmind verify "${window.location.href}" --api ${apiAddress}`}</pre>
          <button
            type="button"
            className="inline-flex h-9 w-fit items-center rounded-full border border-[var(--fm-line)] bg-white px-3.5 text-[12.5px] font-medium text-[var(--fm-ink2)] hover:border-[var(--fm-ink)] hover:text-[var(--fm-ink)]"
            onClick={save}
          >
            Save pack.json
          </button>
        </>
      }
    />
  )
}

export default function VerifyPackPage() {
  return (
    <main className="min-h-screen bg-[var(--fm-bg)] px-4 py-10 text-[var(--fm-ink)]">
      <div className="mx-auto max-w-5xl">
        <Suspense fallback={<Notice title="Loading the inspection pack" body="Checking the link and fetching the manifest." />}>
          <AuditorView />
        </Suspense>
      </div>
    </main>
  )
}
