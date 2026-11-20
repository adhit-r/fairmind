'use client'

import { useEffect, useState } from 'react'
import {
  clearProhibitedScreen,
  getProhibitedQuestions,
  getProhibitedScreen,
  saveProhibitedScreen,
  type ProhibitedQuestion,
  type ProhibitedScreenRecord,
  type ScreenAnswer,
} from '@/lib/api/hooks/useProhibitedScreen'
import { BTN, BTN_P, ErrorNote, MUTED, Pill, when } from '@/components/packs/parts'
import { cn } from '@/lib/utils'

const MIN_REASON = 12
const OUTCOME_LABEL = { indicated: 'May be prohibited', needs_legal_review: 'Cannot conclude', clear: 'No prohibition indicated' } as const
const OUTCOME_TONE = { indicated: 'block', needs_legal_review: 'warn', clear: 'done' } as const
const CHOICES: Array<{ value: ScreenAnswer; label: string }> = [
  { value: 'no', label: 'No' },
  { value: 'unsure', label: 'Unsure' },
  { value: 'yes', label: 'Yes' },
]
const chip = (on: boolean) =>
  cn('rounded-full border px-3 py-1 text-[12.5px]', on ? 'border-[var(--fm-ink)] bg-[var(--fm-ink)] text-white' : 'border-[rgba(21,23,26,.14)] bg-white text-[var(--fm-ink2)] hover:border-[var(--fm-ink)]')

/** EU AI Act Art 5 screen: eight questions a person answers, a conservative result, and a recorded clearance by legal counsel. */
export function ProhibitedScreenPanel({ systemId, onChanged }: { systemId: string; onChanged: () => void | Promise<void> }) {
  const [questions, setQuestions] = useState<ProhibitedQuestion[]>([])
  const [record, setRecord] = useState<ProhibitedScreenRecord | null>(null)
  const [answers, setAnswers] = useState<Record<string, ScreenAnswer>>({})
  const [reason, setReason] = useState('')
  const [busy, setBusy] = useState<'save' | 'clear' | null>(null)
  const [failure, setFailure] = useState<string | null>(null)
  const [loaded, setLoaded] = useState(false)

  useEffect(() => {
    let live = true
    Promise.all([getProhibitedQuestions(), getProhibitedScreen(systemId)])
      .then(([q, s]) => {
        if (!live) return
        setQuestions(q)
        setRecord(s.screen)
        setAnswers(Object.fromEntries((s.screen?.answers ?? []).filter((a) => a.answer).map((a) => [a.key, a.answer as ScreenAnswer])))
      })
      .catch((e: unknown) => live && setFailure(e instanceof Error ? e.message : 'Request failed'))
      .finally(() => live && setLoaded(true))
    return () => {
      live = false
    }
  }, [systemId])

  async function run(kind: 'save' | 'clear') {
    setBusy(kind)
    setFailure(null)
    try {
      const next = kind === 'save' ? await saveProhibitedScreen(systemId, answers) : await clearProhibitedScreen(systemId, reason.trim())
      setRecord(next)
      setReason('')
      await onChanged()
    } catch (e) {
      setFailure(e instanceof Error ? e.message : 'Request failed')
    } finally {
      setBusy(null)
    }
  }

  if (!loaded) return <p className={cn('text-[13px]', MUTED)}>Loading</p>
  const unresolved = record && record.outcome !== 'clear' && !record.clearance

  return (
    <div className="flex flex-col gap-4">
      <p className={cn('text-[13px]', MUTED)}>
        A screening aid for EU AI Act Art 5(1)(a) to (h). It records what you answer and flags what needs legal counsel. It is not a legal conclusion and never says a system is lawful.
      </p>
      {record && (
        <div className="flex flex-col gap-1.5 rounded-[14px] border border-[var(--fm-line)] bg-white p-4">
          <div className="flex flex-wrap items-center gap-2">
            <Pill tone={OUTCOME_TONE[record.outcome]}>{OUTCOME_LABEL[record.outcome]}</Pill>
            {record.clearance && <Pill tone="done">Cleared by a person</Pill>}
          </div>
          <p className="text-[13px] text-[var(--fm-ink)]">{record.summary}</p>
          <p className={cn('text-xs', MUTED)}>Screened by {record.screenedBy} {when(record.screenedAt)}</p>
          {record.clearance && (
            <p className={cn('text-xs', MUTED)}>
              Cleared by {record.clearance.by} {when(record.clearance.at)}: {record.clearance.reason}
              {record.clearance.selfReview && ' (the same person ran the screen)'}
            </p>
          )}
          {unresolved && <p className="text-[12.5px] font-semibold text-[var(--fm-ink)]">{record.outcome === 'indicated' ? 'The release gate is held at no go until this is cleared.' : 'Release approval is blocked until this is cleared.'}</p>}
        </div>
      )}
      <ol className="flex flex-col gap-3">
        {questions.map((q) => (
          <li key={q.key}>
            <fieldset className="min-w-0">
              <legend className="text-[13px] font-semibold text-[var(--fm-ink)]">
                {q.clause} · {q.title}
              </legend>
              <p className={cn('mt-0.5 text-[12.5px]', MUTED)}>{q.question}</p>
              {q.note && <p className={cn('mt-0.5 text-xs italic', MUTED)}>{q.note}</p>}
              <div className="mt-1.5 flex gap-1.5">
                {CHOICES.map((c) => (
                  <button key={c.value} type="button" aria-pressed={answers[q.key] === c.value} className={chip(answers[q.key] === c.value)} onClick={() => setAnswers((a) => ({ ...a, [q.key]: c.value }))}>
                    {c.label}
                  </button>
                ))}
              </div>
            </fieldset>
          </li>
        ))}
      </ol>
      {failure && <ErrorNote message={failure} />}
      <div>
        <button type="button" className={BTN_P} disabled={busy !== null} onClick={() => void run('save')}>
          {busy === 'save' ? 'Saving' : record ? 'Save and screen again' : 'Save and screen'}
        </button>
        {record && <span className={cn('ml-2 text-xs', MUTED)}>A new screen replaces any earlier clearance.</span>}
      </div>
      {unresolved && (
        <div className="flex flex-col gap-1.5 border-t border-[var(--fm-line)] pt-4">
          <label htmlFor="art5-reason" className="text-[13px] font-semibold text-[var(--fm-ink)]">Legal counsel: record a clearance</label>
          <textarea
            id="art5-reason"
            className="w-full rounded-[10px] border border-[var(--fm-line)] bg-white px-3 py-2 text-sm focus:border-[var(--fm-ink)] focus:outline-none"
            rows={3}
            value={reason}
            onChange={(e) => setReason(e.target.value)}
            placeholder="Why no prohibition applies, naming any exception relied on"
          />
          <div>
            <button type="button" className={BTN} disabled={busy !== null || reason.trim().length < MIN_REASON} onClick={() => void run('clear')}>
              {busy === 'clear' ? 'Recording' : 'Record clearance'}
            </button>
            <span className={cn('ml-2 text-xs', MUTED)}>At least {MIN_REASON} characters. Recorded with your name.</span>
          </div>
        </div>
      )}
    </div>
  )
}
