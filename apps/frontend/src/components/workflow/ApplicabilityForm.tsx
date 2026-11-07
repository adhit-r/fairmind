'use client'

import { useEffect, useId, useMemo, useRef, useState, type ReactNode } from 'react'
import { useJourneys } from '@/lib/api/hooks/usePacks'
import {
  EMPTY_ANSWERS,
  MIN_REASON,
  TIERS,
  draftOf,
  suggestApplicability,
  type ApplicabilityAnswers,
  type ApplicabilityConfirmBody,
  type ApplicabilityDraft,
  type ApplicabilityRecord,
  type ApplicabilitySuggestion,
  type Market,
  type Tier,
} from '@/lib/api/hooks/useApplicability'
import { LABEL, MUTED, Pill, cap } from '@/components/packs/parts'
import { cn } from '@/lib/utils'

const field =
  'h-10 w-full rounded-[10px] border border-[rgba(21,23,26,.14)] bg-white px-3 text-[14px] outline-none focus:border-[var(--fm-ink)]'
const label = 'block text-[12.5px] font-medium text-[var(--fm-ink2)]'
const chip = (on: boolean) =>
  cn('rounded-full border px-3 py-1 text-left text-[12.5px]', on ? 'border-[var(--fm-ink)] bg-[var(--fm-ink)] text-white' : 'border-[rgba(21,23,26,.14)] bg-white text-[var(--fm-ink2)] hover:border-[var(--fm-ink)]')

const MARKETS: Array<{ key: Market; label: string }> = [
  { key: 'IN', label: 'India' },
  { key: 'EU', label: 'EU or EEA' },
  { key: 'OTHER', label: 'Elsewhere' },
]

const isTier = (t: string | null | undefined): t is Tier => !!t && (TIERS as string[]).includes(t)

function Toggle({ on, onClick, children }: { on: boolean; onClick: () => void; children: ReactNode }) {
  return (
    <button type="button" aria-pressed={on} onClick={onClick} className={cn(chip(on), 'px-3.5 py-1.5')}>
      {children}
    </button>
  )
}

function Question({ legend, children }: { legend: string; children: ReactNode }) {
  return (
    <fieldset className="min-w-0">
      <legend className={cn(label, 'mb-1.5')}>{legend}</legend>
      <div className="flex flex-wrap gap-1.5">{children}</div>
    </fieldset>
  )
}

/**
 * "What you're shipping": answers that FairMind's fixed rules turn into a suggested tier and frameworks,
 * which the person confirms or changes with a reason. Used on /onboard (embedded, reported through
 * onChange) and inline on the system file (with its own Confirm button).
 */
export function ApplicabilityForm({
  record = null,
  currentTier,
  submitLabel = 'Confirm',
  onSubmit,
  onCancel,
  onChange,
}: {
  record?: ApplicabilityRecord | null
  /** The stored tier, used when suggestions cannot be loaded. */
  currentTier?: string
  submitLabel?: string
  onSubmit?: (body: ApplicabilityConfirmBody) => Promise<void>
  onCancel?: () => void
  onChange?: (draft: ApplicabilityDraft) => void
}) {
  const ids = useId()
  const journeys = useJourneys()
  // intendedPurpose is kept apart so typing in it does not ask for a new suggestion.
  const [answers, setAnswers] = useState<ApplicabilityAnswers>({ ...(record?.answers ?? EMPTY_ANSWERS), intendedPurpose: null })
  const [purpose, setPurpose] = useState(record?.answers.intendedPurpose ?? '')
  const [tierChoice, setTierChoice] = useState<Tier | null>(record && record.tier !== record.suggestedTier ? record.tier : null)
  const [removed, setRemoved] = useState<string[]>(record?.removed ?? [])
  const [added, setAdded] = useState<string[]>(record?.added ?? [])
  const [reason, setReason] = useState(record?.reason ?? '')
  const [suggestion, setSuggestion] = useState<ApplicabilitySuggestion | null>(null)
  const [loading, setLoading] = useState(true)
  const [failed, setFailed] = useState<string | null>(null)
  const [busy, setBusy] = useState(false)
  const seq = useRef(0)

  // Answers are discrete clicks, so no debounce; the counter drops responses to earlier answers.
  useEffect(() => {
    const n = ++seq.current
    setLoading(true)
    suggestApplicability(answers)
      .then((s) => {
        if (n !== seq.current) return
        setSuggestion(s)
        setFailed(null)
      })
      .catch((e: unknown) => n === seq.current && setFailed(e instanceof Error ? e.message : 'Request failed'))
      .finally(() => n === seq.current && setLoading(false))
  }, [answers])

  const fallback = isTier(record?.tier) ? record.tier : isTier(currentTier) ? currentTier : 'medium'
  const tier = tierChoice ?? suggestion?.tier ?? fallback
  const full = useMemo(() => ({ ...answers, intendedPurpose: purpose.trim() ? purpose : null }), [answers, purpose])
  const draft = useMemo(
    () => draftOf({ answers: full, tier, removed, added, reason }, suggestion, { loading, failed: failed !== null }),
    [full, tier, removed, added, reason, suggestion, loading, failed],
  )

  useEffect(() => {
    onChange?.(draft)
  }, [draft, onChange])

  const set = (patch: Partial<ApplicabilityAnswers>) => setAnswers((a) => ({ ...a, ...patch }))
  const toggleMarket = (m: Market) => set({ markets: answers.markets.includes(m) ? answers.markets.filter((x) => x !== m) : [...answers.markets, m] })
  const toggleRemoved = (key: string) => {
    setRemoved((r) => (r.includes(key) ? r.filter((k) => k !== key) : [...r, key]))
    setAdded((a) => a.filter((k) => k !== key))
  }
  const add = (key: string) => {
    if (!key) return
    if (removed.includes(key)) toggleRemoved(key)
    else setAdded((a) => (a.includes(key) ? a : [...a, key]))
  }
  const nameOf = (key: string) => journeys.data?.find((j) => j.key === key)?.name ?? record?.frameworks.find((f) => f.key === key)?.name ?? key

  // The tier the rules suggest now; null while suggestions are unavailable or the first two questions are open.
  const suggestedTier = failed ? null : suggestion?.tier ?? null
  const canConfirm = !busy && (draft.ready || (draft.failed && draft.body !== null))

  async function submit() {
    if (!onSubmit || !draft.body) return
    setBusy(true)
    try {
      await onSubmit(draft.body)
    } finally {
      setBusy(false)
    }
  }

  return (
    <div className="grid gap-4">
      <div>
        <label className={label} htmlFor={`${ids}-use`}>What does it decide or do?</label>
        <select
          id={`${ids}-use`}
          value={answers.use ?? ''}
          onChange={(e) => set({ use: e.target.value || null })}
          disabled={!suggestion}
          className={cn(field, 'mt-1')}
        >
          <option value="">{suggestion ? 'Choose one' : loading ? 'Loading' : 'Not available'}</option>
          {(suggestion?.uses ?? []).map((u) => (
            <option key={u.key} value={u.key}>{u.label}</option>
          ))}
        </select>
      </div>

      <Question legend="Does it make or shape decisions about individual people?">
        <Toggle on={answers.decidesAboutPeople === true} onClick={() => set({ decidesAboutPeople: true })}>Yes</Toggle>
        <Toggle on={answers.decidesAboutPeople === false} onClick={() => set({ decidesAboutPeople: false, humanReview: null })}>No</Toggle>
      </Question>

      {answers.decidesAboutPeople && (
        <Question legend="Before a decision takes effect">
          <Toggle on={answers.humanReview === 'each'} onClick={() => set({ humanReview: 'each' })}>A person reviews each one</Toggle>
          <Toggle on={answers.humanReview === 'automatic'} onClick={() => set({ humanReview: 'automatic' })}>It takes effect automatically</Toggle>
        </Question>
      )}

      <Question legend="Where are the people it affects?">
        {MARKETS.map((m) => (
          <Toggle key={m.key} on={answers.markets.includes(m.key)} onClick={() => toggleMarket(m.key)}>{m.label}</Toggle>
        ))}
      </Question>

      <div className="grid gap-4 sm:grid-cols-2">
        <Question legend="Is your organisation regulated by the RBI?">
          <Toggle on={answers.rbiRegulated === 'yes'} onClick={() => set({ rbiRegulated: 'yes' })}>Yes</Toggle>
          <Toggle on={answers.rbiRegulated === 'no'} onClick={() => set({ rbiRegulated: 'no' })}>No</Toggle>
          <Toggle on={answers.rbiRegulated === 'unsure'} onClick={() => set({ rbiRegulated: 'unsure' })}>Not sure</Toggle>
        </Question>
        <Question legend="Does it use personal data of people in India?">
          <Toggle on={answers.personalDataIndia === true} onClick={() => set({ personalDataIndia: true })}>Yes</Toggle>
          <Toggle on={answers.personalDataIndia === false} onClick={() => set({ personalDataIndia: false })}>No</Toggle>
        </Question>
      </div>

      <div>
        <label className={label} htmlFor={`${ids}-purpose`}>
          Intended purpose, in your words <span className="font-normal text-[var(--fm-ink3)]">(optional, kept verbatim for the audit record)</span>
        </label>
        <textarea
          id={`${ids}-purpose`}
          value={purpose}
          onChange={(e) => setPurpose(e.target.value)}
          rows={2}
          maxLength={1000}
          className="mt-1 w-full rounded-[10px] border border-[rgba(21,23,26,.14)] bg-white px-3 py-2.5 text-[14px] outline-none focus:border-[var(--fm-ink)]"
        />
      </div>

      {failed ? (
        <p role="alert" className="rounded-[10px] bg-[#fde9ea] px-3 py-2 text-[13px] text-[#b4232c]">
          Could not load suggestions: {failed}.{onSubmit ? '' : ' You can still register; confirm the tier and rules on the system file.'}
        </p>
      ) : (
        <div className="grid gap-3.5 rounded-[12px] border border-[var(--fm-line)] bg-[var(--fm-bg)] p-4">
          <div className="flex items-center gap-2">
            <div className={LABEL}>FairMind suggests</div>
            {loading && <span role="status" className={cn('text-[12px]', MUTED)}>Working it out</span>}
          </div>
          {suggestion && suggestion.tier === null && <p className={cn('text-[13px]', MUTED)}>Answer the first two questions to see a suggestion</p>}
          {suggestion?.tier && (
            <div>
              <div className="text-[16px] font-semibold">{cap(suggestion.tier)} risk tier</div>
              <ul className="mt-1.5 list-disc pl-[18px] text-[13px] leading-normal text-[var(--fm-ink2)]">
                {suggestion.tierRules.map((r) => (
                  <li key={r.id}>
                    <span className="font-semibold text-[var(--fm-ink)]">Rule {r.id}</span> · {r.text}
                    {r.cite && <span className="text-[var(--fm-ink3)]" title={r.cite.key}> Cites {r.cite.key.split('|').pop()}: {r.cite.title}</span>}
                  </li>
                ))}
              </ul>
            </div>
          )}
          {suggestion && (
            <div>
              <div className="text-[12.5px] font-semibold">Rules it answers to</div>
              <ul className="mt-2 grid gap-2">
                {suggestion.frameworks.map((f) => {
                  const kept = !removed.includes(f.key)
                  return (
                    <li key={f.key} className="flex flex-wrap items-baseline gap-2">
                      {f.available ? (
                        <button type="button" aria-pressed={kept} onClick={() => toggleRemoved(f.key)} className={chip(kept)}>
                          {f.name} · {kept ? 'suggested' : 'removed'}
                        </button>
                      ) : (
                        <>
                          <span className="rounded-full border border-dashed border-[rgba(21,23,26,.2)] bg-white px-3 py-1 text-[12.5px] text-[var(--fm-ink3)]">{f.name}</span>
                          <Pill>Coming soon</Pill>
                        </>
                      )}
                      <span className={cn('text-[12.5px]', MUTED)}>
                        Rule {f.rule.id}: {f.rule.text}
                        {f.binding && <span className="text-[var(--fm-ink3)]"> · {f.binding}</span>}
                      </span>
                    </li>
                  )
                })}
                {added.filter((k) => !suggestion.frameworks.some((f) => f.key === k)).map((k) => (
                  <li key={k}>
                    <button type="button" aria-pressed onClick={() => setAdded((a) => a.filter((x) => x !== k))} className={chip(true)}>
                      {nameOf(k)} · added
                    </button>
                  </li>
                ))}
                {suggestion.frameworks.length + added.length === 0 && <li className={cn('text-[12.5px]', MUTED)}>None suggested from these answers.</li>}
              </ul>
              <div className="mt-3 max-w-[360px]">
                <label className={label} htmlFor={`${ids}-add`}>Add a framework from the catalogue</label>
                <select id={`${ids}-add`} value="" onChange={(e) => add(e.target.value)} disabled={!journeys.data} className={cn(field, 'mt-1')}>
                  <option value="">{journeys.data ? 'Choose a framework' : journeys.error ? `Catalogue unavailable: ${journeys.error}` : 'Loading the catalogue'}</option>
                  {(journeys.data ?? [])
                    .filter((j) => !draft.frameworks.includes(j.key))
                    .map((j) => (
                      <option key={j.key} value={j.key}>{j.name}</option>
                    ))}
                </select>
              </div>
            </div>
          )}
          {suggestion && (
            <details className="text-[12.5px]">
              <summary className="cursor-pointer font-medium text-[var(--fm-ink2)]">How FairMind suggests these</summary>
              <p className={cn('mt-1.5', MUTED)}>Fixed rules, version {suggestion.rulesVersion}. No AI model is involved.</p>
              <ul className={cn('mt-1 grid gap-1', MUTED)}>
                {suggestion.rules.map((r) => (
                  <li key={r.id}>
                    <span className="font-semibold text-[var(--fm-ink)]">{r.id}</span> · {r.text}
                  </li>
                ))}
                <li className="flex flex-wrap items-center gap-2">
                  Prohibited-practice screening (EU AI Act Art 5) <Pill>Coming soon</Pill>
                </li>
              </ul>
            </details>
          )}
        </div>
      )}

      <div className="grid gap-4 sm:grid-cols-[220px_minmax(0,1fr)] sm:items-start">
        <div>
          <label className={label} htmlFor={`${ids}-tier`}>Risk tier</label>
          <select
            id={`${ids}-tier`}
            value={tier}
            onChange={(e) => {
              const t = e.target.value as Tier
              setTierChoice(t === suggestedTier ? null : t)
            }}
            className={cn(field, 'mt-1')}
          >
            {TIERS.map((t) => (
              <option key={t} value={t}>{cap(t)}{t === suggestedTier ? ' (suggested)' : ''}</option>
            ))}
          </select>
        </div>
        {suggestedTier && (
          <p className="text-[12.5px] leading-normal text-[var(--fm-ink2)] sm:mt-[22px]">
            Choose a different tier or drop a suggested framework and you will be asked why. Your name and reason are saved, and sealed with the release decision.
          </p>
        )}
      </div>

      {(draft.needsReason || (draft.failed && draft.body)) && (
        <div>
          <label className={label} htmlFor={`${ids}-reason`}>Why you are changing the suggestion</label>
          <textarea
            id={`${ids}-reason`}
            value={reason}
            onChange={(e) => setReason(e.target.value)}
            rows={2}
            required={draft.needsReason}
            minLength={draft.needsReason ? MIN_REASON : undefined}
            className="mt-1 w-full rounded-[10px] border border-[rgba(21,23,26,.14)] bg-white px-3 py-2.5 text-[14px] outline-none focus:border-[var(--fm-ink)]"
          />
          <p className="mt-1 text-[12px] text-[var(--fm-ink3)]">Recorded with your name and sealed with the release decision. {MIN_REASON} characters or more.</p>
        </div>
      )}

      {onSubmit && (
        <div className="flex gap-2">
          <button
            type="button"
            disabled={!canConfirm}
            onClick={() => void submit()}
            className="h-8 rounded-full bg-[var(--fm-ink)] px-3.5 text-[12.5px] font-semibold text-white disabled:opacity-60"
          >
            {busy ? 'Saving' : submitLabel}
          </button>
          {onCancel && (
            <button type="button" onClick={onCancel} className="h-8 rounded-full border border-[var(--fm-line)] px-3 text-[12.5px] text-[var(--fm-ink2)]">Cancel</button>
          )}
        </div>
      )}
    </div>
  )
}
