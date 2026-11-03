'use client'

import Link from 'next/link'
import { useEffect, useMemo, useState } from 'react'
import { useRouter } from 'next/navigation'
import { Button } from '@/components/ui/button'
import { Card } from '@/components/ui/card'
import { Input } from '@/components/ui/input'
import { useSystemContext } from '@/components/workflow/SystemContext'
import { useEvidencePacks } from '@/lib/api/hooks/useEvidencePacks'
import { formatDate } from '@/components/evidence-packs/PackSummaryView'

// The frameworks a decision record is usually read against; the rest come from the API.
const LEAD_FRAMEWORKS = ['EUAIA', 'ISO42001', 'NISTRMF', 'INDAI']

function Check({ id, label, checked, onChange }: { id: string; label: string; checked: boolean; onChange: (next: boolean) => void }) {
  return (
    <label className="flex cursor-pointer items-start gap-2.5 rounded-[10px] border border-[var(--fm-line)] bg-white px-3 py-2 text-sm text-[var(--fm-ink)] has-[:checked]:border-[var(--fm-ink)]">
      <input type="checkbox" id={id} className="mt-0.5 h-4 w-4 accent-[var(--fm-ink)]" checked={checked} onChange={(e) => onChange(e.target.checked)} />
      <span className="min-w-0">{label}</span>
    </label>
  )
}

export default function InspectionPacksPage() {
  const router = useRouter()
  const { systems } = useSystemContext()
  const { packs, frameworks, loading, error, create } = useEvidencePacks()
  const realSystems = useMemo(() => systems.filter((s) => s.metadata?.source !== 'fallback'), [systems])

  const [open, setOpen] = useState(false)
  const [title, setTitle] = useState('')
  const [pickedFrameworks, setPickedFrameworks] = useState<string[]>([])
  const [pickedSystems, setPickedSystems] = useState<string[]>([])
  const [submitting, setSubmitting] = useState(false)
  const [formError, setFormError] = useState<string | null>(null)

  // Preselect the lead frameworks once the list arrives.
  useEffect(() => {
    setPickedFrameworks((current) => (current.length ? current : frameworks.filter((f) => LEAD_FRAMEWORKS.includes(f.key)).map((f) => f.key)))
  }, [frameworks])

  const toggle = (list: string[], set: (next: string[]) => void, key: string, on: boolean) =>
    set(on ? [...list, key] : list.filter((k) => k !== key))

  const canSubmit = title.trim() && pickedFrameworks.length > 0 && pickedSystems.length > 0 && !submitting

  async function submit(event: React.FormEvent) {
    event.preventDefault()
    setSubmitting(true)
    setFormError(null)
    const res = await create({ title: title.trim(), frameworks: pickedFrameworks, systemIds: pickedSystems })
    setSubmitting(false)
    if (res.success && res.data) router.push(`/evidence/packs/${res.data.id}`)
    else setFormError(res.error || res.message || 'The pack could not be built')
  }

  return (
    <div className="flex flex-col gap-6">
      <div className="flex flex-col gap-3 sm:flex-row sm:items-end sm:justify-between">
        <div>
          <Link href="/evidence" className="text-xs font-medium text-[var(--fm-ink2)] hover:text-[var(--fm-ink)]">Evidence</Link>
          <h1 className="mt-1 text-2xl font-semibold tracking-tight text-[var(--fm-ink)]">Inspection packs</h1>
          <p className="mt-1 max-w-2xl text-sm text-[var(--fm-ink2)]">
            A pack freezes the gate, clause coverage and evidence hashes for chosen systems. Share a read-only link and an auditor can verify it offline.
          </p>
        </div>
        <Button onClick={() => setOpen((v) => !v)} aria-expanded={open}>{open ? 'Close' : 'New pack'}</Button>
      </div>

      {open && (
        <Card className="p-5">
          <form onSubmit={submit} className="flex flex-col gap-5">
            <div>
              <label htmlFor="pack-title" className="text-[10.5px] font-semibold uppercase tracking-[0.08em] text-[var(--fm-ink3)]">Title</label>
              <Input id="pack-title" className="mt-1.5 rounded-[10px]" value={title} onChange={(e) => setTitle(e.target.value)} maxLength={200} />
            </div>
            <fieldset>
              <legend className="text-[10.5px] font-semibold uppercase tracking-[0.08em] text-[var(--fm-ink3)]">Frameworks</legend>
              <div className="mt-1.5 grid gap-2 sm:grid-cols-2">
                {frameworks.map((f) => (
                  <Check key={f.key} id={`fw-${f.key}`} label={f.name} checked={pickedFrameworks.includes(f.key)} onChange={(on) => toggle(pickedFrameworks, setPickedFrameworks, f.key, on)} />
                ))}
              </div>
            </fieldset>
            <fieldset>
              <legend className="text-[10.5px] font-semibold uppercase tracking-[0.08em] text-[var(--fm-ink3)]">Systems</legend>
              {realSystems.length === 0 ? (
                <p className="mt-1.5 text-sm text-[var(--fm-ink2)]">No systems registered yet.</p>
              ) : (
                <div className="mt-1.5 grid gap-2 sm:grid-cols-2">
                  {realSystems.map((s) => (
                    <Check key={s.id} id={`sys-${s.id}`} label={s.name} checked={pickedSystems.includes(s.id)} onChange={(on) => toggle(pickedSystems, setPickedSystems, s.id, on)} />
                  ))}
                </div>
              )}
            </fieldset>
            {formError && <p role="alert" className="text-sm text-[#b4232c]">{formError}</p>}
            <div>
              <Button type="submit" disabled={!canSubmit}>{submitting ? 'Building' : 'Build pack'}</Button>
            </div>
          </form>
        </Card>
      )}

      {error && <p role="alert" className="text-sm text-[#b4232c]">{error}</p>}

      <Card className="overflow-hidden">
        {loading ? (
          <p className="p-5 text-sm text-[var(--fm-ink2)]">Loading packs</p>
        ) : packs.length === 0 ? (
          <p className="p-5 text-sm text-[var(--fm-ink2)]">No inspection packs yet. Build one to hand an auditor.</p>
        ) : (
          <ul>
            {packs.map((p) => (
              <li key={p.id} className="border-t border-[var(--fm-line)] first:border-t-0">
                <Link href={`/evidence/packs/${p.id}`} className="flex flex-col gap-1 px-5 py-4 hover:bg-[var(--fm-bg)] sm:flex-row sm:items-center sm:justify-between">
                  <span className="min-w-0">
                    <span className="block text-sm font-semibold text-[var(--fm-ink)]">{p.title}</span>
                    <span className="block text-xs text-[var(--fm-ink2)]">{p.systemIds.length} {p.systemIds.length === 1 ? 'system' : 'systems'}, {p.frameworks.join(', ')}</span>
                  </span>
                  <span className="flex items-center gap-4 text-xs text-[var(--fm-ink2)]">
                    <span>{p.share.shared ? 'Link active' : p.share.expired ? 'Link expired' : 'Not shared'}</span>
                    <span className="font-mono">{p.manifestHash.slice(0, 12)}</span>
                    <span>{formatDate(p.createdAt)}</span>
                  </span>
                </Link>
              </li>
            ))}
          </ul>
        )}
      </Card>
    </div>
  )
}
