'use client'

import Link from 'next/link'
import { useSystemContext } from '@/components/workflow/SystemContext'

const STAGE_LABEL: Record<string, string> = {
  onboard: 'Onboard',
  assess: 'Assess',
  govern: 'Govern',
  remediate: 'Remediate',
  operate: 'Operate',
}

/**
 * One line above every legacy tool page: which system the page acts on, a way
 * back to its system file, and a way to switch. Replaces the old context bar.
 */
export function SystemBreadcrumb() {
  const { systems, selectedSystem, setSelectedSystemId, loading } = useSystemContext()
  const hasSystem = Boolean(selectedSystem?.id) && selectedSystem.metadata?.source !== 'fallback'

  if (loading && !hasSystem) return null

  if (!hasSystem) {
    return (
      <div className="mb-4 flex flex-wrap items-center gap-2 text-[12.5px] text-[var(--fm-ink2)]">
        <span>No system selected.</span>
        <Link href="/integrations" className="font-medium text-[var(--fm-ink)] underline-offset-2 hover:underline">
          Connect a source
        </Link>
        <span>or</span>
        <Link href="/onboard" className="font-medium text-[var(--fm-ink)] underline-offset-2 hover:underline">
          register one
        </Link>
      </div>
    )
  }

  return (
    <div className="mb-4 flex flex-wrap items-center gap-x-3 gap-y-2 text-[12.5px] text-[var(--fm-ink2)]">
      <Link
        href={`/systems/${selectedSystem.id}`}
        className="inline-flex items-center gap-1.5 rounded-full border border-[var(--fm-line)] bg-white px-3 py-1 font-medium text-[var(--fm-ink)] hover:border-[var(--fm-ink)]"
      >
        <span aria-hidden="true">&larr;</span> System file
      </Link>
      <span className="font-semibold text-[var(--fm-ink)]">{selectedSystem.name}</span>
      <span className="capitalize">{selectedSystem.riskTier} tier</span>
      <span>{STAGE_LABEL[selectedSystem.stage] ?? selectedSystem.stage}</span>
      {systems.length > 1 && (
        <label className="ml-auto flex items-center gap-2">
          <span className="sr-only">Switch system</span>
          <select
            value={selectedSystem.id}
            onChange={(e) => setSelectedSystemId(e.target.value)}
            className="h-8 rounded-[8px] border border-[var(--fm-line)] bg-white px-2 text-[12.5px] text-[var(--fm-ink)]"
          >
            {systems.map((s) => (
              <option key={s.id} value={s.id}>{s.name}</option>
            ))}
          </select>
        </label>
      )}
    </div>
  )
}
