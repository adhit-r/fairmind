'use client'

import Link from 'next/link'
import { useParams } from 'next/navigation'
import { useState } from 'react'
import { Button } from '@/components/ui/button'
import { Card } from '@/components/ui/card'
import { useEvidencePack } from '@/lib/api/hooks/useEvidencePacks'
import { PackSummaryView, formatDate } from '@/components/evidence-packs/PackSummaryView'

function auditorUrl(packId: string, token: string) {
  return `${window.location.origin}/verify/${packId}?t=${encodeURIComponent(token)}`
}

export default function InspectionPackPage() {
  const { id } = useParams<{ id: string }>()
  const { pack, loading, error, share, revoke, download } = useEvidencePack(id)
  // The link is shown once, straight from the share response, and never stored.
  const [link, setLink] = useState<string | null>(null)
  const [copied, setCopied] = useState(false)
  const [busy, setBusy] = useState(false)
  const [actionError, setActionError] = useState<string | null>(null)

  async function run(action: () => Promise<{ success: boolean; error?: string; message?: string }>) {
    setBusy(true)
    setActionError(null)
    const res = await action()
    setBusy(false)
    if (!res.success) setActionError(res.error || res.message || 'That did not work')
    return res
  }

  async function createLink() {
    const res = await run(share)
    const data = (res as { data?: { token: string } }).data
    if (res.success && data) {
      setLink(auditorUrl(id, data.token))
      setCopied(false)
    }
  }

  async function revokeLink() {
    const res = await run(revoke)
    if (res.success) setLink(null)
  }

  async function copy() {
    if (!link) return
    try {
      await navigator.clipboard.writeText(link)
      setCopied(true)
    } catch {
      setActionError('Copy failed. Select the link and copy it by hand.')
    }
  }

  if (loading && !pack) return <p className="text-sm text-[var(--fm-ink2)]">Loading pack</p>
  if (!pack) return <p role="alert" className="text-sm text-[#b4232c]">{error || 'Pack not found'}</p>

  return (
    <div className="flex flex-col gap-6">
      <div className="flex flex-col gap-3 sm:flex-row sm:items-end sm:justify-between">
        <div>
          <Link href="/evidence/packs" className="text-xs font-medium text-[var(--fm-ink2)] hover:text-[var(--fm-ink)]">Inspection packs</Link>
          <h1 className="mt-1 text-2xl font-semibold tracking-tight text-[var(--fm-ink)]">{pack.title}</h1>
          <p className="mt-1 text-sm text-[var(--fm-ink2)]">Built {formatDate(pack.createdAt)}{pack.createdBy ? ` by ${pack.createdBy}` : ''}</p>
        </div>
        <div className="flex flex-wrap gap-2">
          <Button variant="outline" onClick={() => void run(async () => ({ success: await download() }))} disabled={busy}>Download JSON</Button>
          <Button onClick={createLink} disabled={busy}>{pack.share.shared ? 'Replace auditor link' : 'Create auditor link'}</Button>
          {pack.share.shared && <Button variant="outline" onClick={revokeLink} disabled={busy}>Revoke link</Button>}
        </div>
      </div>

      {actionError && <p role="alert" className="text-sm text-[#b4232c]">{actionError}</p>}

      <Card className="p-5">
        <div className="text-[10.5px] font-semibold uppercase tracking-[0.08em] text-[var(--fm-ink3)]">Auditor link</div>
        {link ? (
          <div className="mt-2 flex flex-col gap-2">
            <p className="text-sm text-[var(--fm-ink2)]">Copy it now. It is shown once and FairMind keeps only a hash of it.</p>
            <div className="flex flex-col gap-2 sm:flex-row">
              <input readOnly value={link} onFocus={(e) => e.currentTarget.select()} aria-label="Auditor link" className="h-10 min-w-0 flex-1 rounded-[10px] border border-[var(--fm-line)] bg-white px-3 font-mono text-xs text-[var(--fm-ink)]" />
              <Button variant="outline" onClick={copy}>{copied ? 'Copied' : 'Copy'}</Button>
            </div>
          </div>
        ) : (
          <p className="mt-2 text-sm text-[var(--fm-ink2)]">
            {pack.share.shared
              ? `A link is active until ${formatDate(pack.share.expiresAt)}. Its address cannot be shown again; replace it to get a new one.`
              : pack.share.expired
                ? 'The last link expired. Create a new one to share this pack.'
                : 'No link yet. An auditor link is read-only and expires after 30 days.'}
          </p>
        )}
      </Card>

      <PackSummaryView manifest={pack.manifest} manifestHash={pack.manifestHash} />
    </div>
  )
}
