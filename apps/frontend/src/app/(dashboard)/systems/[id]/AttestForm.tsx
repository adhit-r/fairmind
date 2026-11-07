'use client'

import { useState } from 'react'
import type { AttestableCheck } from '@/lib/api/hooks/useSystemFile'

const CHECK_PROMPT: Record<AttestableCheck, string> = {
  data_governance: 'Where the training and evaluation data came from, its lawful basis, and who owns it.',
  human_oversight: 'Who reviews or can override the system\'s decisions, and when.',
  monitoring: 'How the system is watched in production and who is paged.',
  environmental: 'What is known about the system\'s energy and carbon footprint.',
}

/** A person states that a check is satisfied. Recorded as manual evidence: it attests, it never proves. */
export function AttestForm({ check, onSubmit, onCancel }: { check: AttestableCheck; onSubmit: (statement: string, reference?: string) => Promise<void>; onCancel: () => void }) {
  const [statement, setStatement] = useState('')
  const [reference, setReference] = useState('')
  const [busy, setBusy] = useState(false)
  const [error, setError] = useState<string | null>(null)

  async function submit() {
    setBusy(true)
    setError(null)
    try {
      await onSubmit(statement.trim(), reference.trim() || undefined)
    } catch (e) {
      setError(e instanceof Error ? e.message : 'Could not record the attestation')
      setBusy(false)
    }
  }

  return (
    <div className="mt-2 grid gap-2 rounded-[10px] border border-[var(--fm-line)] bg-white p-3">
      <p className="text-[12px] text-[var(--fm-ink2)]">{CHECK_PROMPT[check]} This is recorded as attested, in the manual confidence band; measured evidence can replace it later.</p>
      {check === 'environmental' && (
        <p className="rounded-[10px] bg-[#fff4d6] px-3 py-2 text-[12px] text-[#8a5a00]">
          An environmental attestation takes the place of an assessment for this check, and approval still needs an assessment on file. Run the assessment instead if you can.
        </p>
      )}
      <textarea
        value={statement}
        onChange={(e) => setStatement(e.target.value)}
        rows={3}
        placeholder="State what is in place, in your own words"
        className="w-full rounded-[10px] border border-[rgba(21,23,26,.14)] px-2.5 py-2 text-[13px] outline-none focus:border-[var(--fm-ink)]"
      />
      <input
        value={reference}
        onChange={(e) => setReference(e.target.value)}
        placeholder="Reference: a document id, policy name or link (optional)"
        className="h-9 w-full rounded-[10px] border border-[rgba(21,23,26,.14)] px-2.5 text-[13px] outline-none focus:border-[var(--fm-ink)]"
      />
      {error && <p className="rounded-[10px] bg-[#fde9ea] px-3 py-2 text-[12.5px] text-[#b4232c]">{error}</p>}
      <div className="flex gap-2">
        <button type="button" disabled={busy || statement.trim().length < 12} onClick={() => void submit()} className="h-8 rounded-full bg-[var(--fm-ink)] px-3.5 text-[12.5px] font-semibold text-white disabled:opacity-60">
          {busy ? 'Recording' : 'Record attestation'}
        </button>
        <button type="button" onClick={onCancel} className="h-8 rounded-full border border-[var(--fm-line)] px-3 text-[12.5px] text-[var(--fm-ink2)]">Cancel</button>
      </div>
    </div>
  )
}
