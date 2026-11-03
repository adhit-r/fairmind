'use client'

import { useState } from 'react'

/** Approving on a conditional go: the approver states the conditions they accept, recorded as the decision notes. */
export function ConditionsForm({ onSubmit, onCancel }: { onSubmit: (conditions: string) => Promise<void>; onCancel: () => void }) {
  const [conditions, setConditions] = useState('')
  const [busy, setBusy] = useState(false)
  const [error, setError] = useState<string | null>(null)

  async function submit() {
    setBusy(true)
    setError(null)
    try {
      await onSubmit(conditions.trim())
    } catch (e) {
      setError(e instanceof Error ? e.message : 'Could not record the decision')
      setBusy(false)
    }
  }

  return (
    <div className="mt-2 grid gap-2 rounded-[10px] border border-[var(--fm-line)] bg-white p-3">
      <label htmlFor="release-conditions" className="text-[11px] font-semibold uppercase tracking-[.08em] text-[var(--fm-ink3)]">Conditions you accept</label>
      <p className="text-[12px] text-[var(--fm-ink2)]">The gate reads conditional go. Say what has to hold for this release to stay approved; it is recorded with your decision.</p>
      <textarea
        id="release-conditions"
        value={conditions}
        onChange={(e) => setConditions(e.target.value)}
        rows={3}
        required
        placeholder="For example: re-run the fairness test after 30 days of production traffic"
        className="w-full rounded-[10px] border border-[rgba(21,23,26,.14)] px-2.5 py-2 text-[13px] outline-none focus:border-[var(--fm-ink)]"
      />
      {error && <p className="rounded-[10px] bg-[#fde9ea] px-3 py-2 text-[12.5px] text-[#b4232c]">{error}</p>}
      <div className="flex gap-2">
        <button type="button" disabled={busy || conditions.trim().length === 0} onClick={() => void submit()} className="h-8 rounded-full bg-[var(--fm-ink)] px-3.5 text-[12.5px] font-semibold text-white disabled:opacity-60">
          {busy ? 'Recording' : 'Approve with these conditions'}
        </button>
        <button type="button" onClick={onCancel} className="h-8 rounded-full border border-[var(--fm-line)] px-3 text-[12.5px] text-[var(--fm-ink2)]">Cancel</button>
      </div>
    </div>
  )
}
