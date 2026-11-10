'use client'

import Link from 'next/link'
import { useEffect, useState } from 'react'
import { ArrowUp, Sparkles } from 'lucide-react'
import { cn } from '@/lib/utils'
import type { Discovery as DiscoveryState, Fact, Question } from '@/lib/api/hooks/usePlan'

const SOURCE: Record<Fact['source'], string> = { answer: 'You said', description: 'From your description', estate: 'From your inventory' }
const LANE_LABEL: Record<string, string> = { foundation: 'Foundation', inventory: 'Inventory and risk', build: 'Build and test', release: 'Release', operate: 'Operate' }
const MATURITY_TONE: Record<string, string> = { none: 'bg-[#E24B4A]', partial: 'bg-[#EF9F27]', established: 'bg-[#1D9E75]' }
const pill = 'rounded-full border px-3 py-1.5 text-[12.5px] font-medium transition-colors'
const pillOn = 'border-[var(--fm-ink)] bg-[var(--fm-ink)] text-white'
const pillOff = 'border-[var(--fm-line)] bg-white text-[var(--fm-ink2)] hover:border-[var(--fm-ink)] hover:text-[var(--fm-ink)]'
const primary = 'inline-flex h-9 items-center rounded-full bg-[var(--fm-ink)] px-4 text-[12.5px] font-semibold text-white disabled:opacity-50'

/** One question, drawn for its kind; `onAnswer` sends the value. */
function Ask({ q, busy, onAnswer }: { q: Question; busy: boolean; onAnswer: (value: unknown) => void }) {
  const [textv, setText] = useState('')
  const [multi, setMulti] = useState<string[]>(q.suggestedValue ?? [])
  const [levels, setLevels] = useState<Record<string, string>>(() => Object.fromEntries((q.controls ?? []).filter((c) => c.value).map((c) => [c.id, c.value as string])))
  const [people, setPeople] = useState<Record<string, string>>({})
  const [frameworks, setFrameworks] = useState<string[]>(q.selected ?? [])
  const [adding, setAdding] = useState('')
  useEffect(() => {
    setMulti(q.suggestedValue ?? [])
    setFrameworks(q.selected ?? [])
  }, [q.key, q.suggestedValue, q.selected])
  const toggle = (list: string[], v: string) => (list.includes(v) ? list.filter((x) => x !== v) : [...list, v])

  if (q.kind === 'text')
    return (
      <form onSubmit={(e) => { e.preventDefault(); if (textv.trim().length >= 10) onAnswer(textv.trim()) }} className="grid grid-cols-[minmax(0,1fr)] gap-2">
        <textarea value={textv} onChange={(e) => setText(e.target.value)} rows={4} placeholder={q.placeholder} aria-label={q.text}
          className="w-full rounded-[10px] border border-[var(--fm-line)] bg-white p-3 text-[13px] outline-none placeholder:text-[var(--fm-ink3)] focus:border-[var(--fm-ink)]" />
        <div className="flex items-center gap-3">
          <button type="submit" disabled={busy || textv.trim().length < 10} className={primary}><ArrowUp className="mr-1.5 h-4 w-4" aria-hidden />Send</button>
          {textv.trim().length > 0 && textv.trim().length < 10 && <span className="text-[12px] text-[var(--fm-ink3)]">A sentence or two helps me fill in more</span>}
        </div>
      </form>
    )
  if (q.kind === 'single')
    return (
      <div className="flex flex-wrap gap-2">
        {Object.entries(q.options ?? {}).map(([k, label]) => (
          <button key={k} type="button" disabled={busy} onClick={() => onAnswer(k)} className={cn(pill, pillOff)}>{label}</button>
        ))}
      </div>
    )
  if (q.kind === 'multi')
    return (
      <div className="grid grid-cols-[minmax(0,1fr)] gap-3">
        {q.suggestedValue && <p className="text-[12px] text-[var(--fm-ink3)]">I ticked what {q.suggestedBasis?.toLowerCase() ?? 'your inventory'} shows. Add anything it misses.</p>}
        <div className="flex flex-wrap gap-2">
          {Object.entries(q.options ?? {}).map(([k, label]) => (
            <button key={k} type="button" aria-pressed={multi.includes(k)} onClick={() => setMulti((m) => toggle(m, k))} className={cn(pill, multi.includes(k) ? pillOn : pillOff)}>{label}</button>
          ))}
        </div>
        <div><button type="button" disabled={busy || multi.length === 0} onClick={() => onAnswer(multi)} className={primary}>Continue</button></div>
      </div>
    )
  if (q.kind === 'maturity') {
    const all = (q.controls ?? []).every((c) => levels[c.id])
    return (
      <div className="grid grid-cols-[minmax(0,1fr)] gap-1.5">
        {(q.controls ?? []).map((c) => (
          <div key={c.id} className="flex flex-wrap items-center gap-2 border-t border-[var(--fm-line)] py-2 first:border-t-0">
            <span className="min-w-[200px] flex-1 text-[13px]">{c.name}</span>
            <div role="radiogroup" aria-label={c.name} className="flex gap-0.5 rounded-full bg-[var(--fm-bg)] p-[3px]">
              {Object.entries(q.options ?? {}).map(([k, label]) => (
                <button key={k} type="button" role="radio" aria-checked={levels[c.id] === k} onClick={() => setLevels((l) => ({ ...l, [c.id]: k }))}
                  className={cn('rounded-full px-2.5 py-1 text-[12px] font-medium text-[var(--fm-ink2)]', levels[c.id] === k && 'bg-[var(--fm-ink)] text-white')}>{label}</button>
              ))}
            </div>
          </div>
        ))}
        <div className="pt-2"><button type="button" disabled={busy || !all} onClick={() => onAnswer(levels)} className={primary}>Continue</button></div>
      </div>
    )
  }
  if (q.kind === 'people')
    return (
      <div className="grid grid-cols-[minmax(0,1fr)] gap-2">
        <div className="grid gap-2 sm:grid-cols-2">
          {Object.entries(q.options ?? {}).map(([k, label]) => (
            <label key={k} className="grid gap-1 text-[12px] text-[var(--fm-ink2)]">
              {label}
              <input value={people[k] ?? ''} onChange={(e) => setPeople((p) => ({ ...p, [k]: e.target.value }))} placeholder="Name or email"
                className="h-9 rounded-[10px] border border-[var(--fm-line)] bg-white px-2.5 text-[13px] text-[var(--fm-ink)] outline-none focus:border-[var(--fm-ink)]" />
            </label>
          ))}
        </div>
        <div className="pt-1"><button type="button" disabled={busy} onClick={() => onAnswer(people)} className={primary}>Continue</button></div>
      </div>
    )
  // frameworks
  const names = Object.fromEntries((q.all ?? []).map((f) => [f.key, f.name]))
  const reasons = Object.fromEntries((q.suggested ?? []).map((f) => [f.key, f.reason]))
  const shown = Array.from(new Set([...(q.suggested ?? []).map((f) => f.key), ...frameworks]))
  return (
    <div className="grid grid-cols-[minmax(0,1fr)] gap-2">
      {shown.map((k) => (
        <label key={k} className="flex items-start gap-2.5 rounded-[10px] border border-[var(--fm-line)] bg-white px-3 py-2">
          <input type="checkbox" checked={frameworks.includes(k)} onChange={() => setFrameworks((f) => toggle(f, k))} className="mt-0.5 h-4 w-4 accent-[var(--fm-ink)]" />
          <span className="min-w-0">
            <b className="block text-[13px] font-semibold">{names[k] ?? k}</b>
            <span className="text-[12px] text-[var(--fm-ink2)]">{reasons[k] ?? 'You added it'}</span>
          </span>
        </label>
      ))}
      <div className="flex flex-wrap items-center gap-2">
        <select value={adding} onChange={(e) => setAdding(e.target.value)} aria-label="Add a framework"
          className="h-9 min-w-0 max-w-full flex-1 rounded-[10px] border border-[var(--fm-line)] bg-white px-2 text-[12.5px]">
          <option value="">Add another framework</option>
          {(q.all ?? []).filter((f) => !shown.includes(f.key)).map((f) => <option key={f.key} value={f.key}>{f.name}</option>)}
        </select>
        <button type="button" disabled={!adding} onClick={() => { setFrameworks((f) => [...f, adding]); setAdding('') }} className={cn(pill, pillOff)}>Add</button>
      </div>
      <div className="pt-1"><button type="button" disabled={busy || frameworks.length === 0} onClick={() => onAnswer(frameworks)} className={primary}>Confirm frameworks</button></div>
    </div>
  )
}

/** Agentic onboarding: the agent asks, reads what you write, fills in what the estate shows, and maps it live. */
export function Discovery({ d, onAnswer, onGenerate }: { d: DiscoveryState; onAnswer: (key: string, value: unknown) => Promise<unknown>; onGenerate: () => Promise<unknown> }) {
  const [busy, setBusy] = useState(false)
  const [failure, setFailure] = useState<string | null>(null)
  const run = async (fn: () => Promise<unknown>) => {
    setBusy(true)
    setFailure(null)
    try {
      await fn()
    } catch (e) {
      setFailure(e instanceof Error ? e.message : 'Request failed')
    } finally {
      setBusy(false)
    }
  }
  const q = d.next
  const byLane = Object.keys(LANE_LABEL).map((lane) => ({ lane, controls: d.map.controls.filter((c) => c.lane === lane) })).filter((g) => g.controls.length)
  const pct = Math.round((d.progress.answered / Math.max(d.progress.total, 1)) * 100)

  return (
    <div className="grid gap-4 lg:grid-cols-[minmax(0,1fr)_380px]">
      <section className="fm-card grid min-w-0 grid-cols-[minmax(0,1fr)] content-start gap-4 p-5" aria-label="Discovery">
        <div className="flex items-center gap-2">
          <Sparkles className="h-4 w-4 text-[var(--fm-brand)]" aria-hidden />
          <h1 className="text-[17px] font-semibold tracking-[-0.01em]">Set up your governance plan</h1>
          <span className="ml-auto text-[12px] text-[var(--fm-ink3)]">{d.agent === 'llm' ? 'Reading with your AI provider' : <>Keyword reading. <Link href="/org-admin/settings" className="underline underline-offset-2">Add a provider</Link> for better reading</>}</span>
        </div>
        <div className="h-1.5 overflow-hidden rounded-full bg-[var(--fm-line)]" aria-label={`${pct}% of discovery done`}><span className="block h-full bg-[var(--fm-ink)]" style={{ width: `${pct}%` }} /></div>

        <ol className="grid gap-2.5">
          {d.transcript.map((m, i) => (
            <li key={i} className={cn('max-w-[85%] rounded-[12px] px-3 py-2 text-[13px] leading-relaxed', m.role === 'user' ? 'justify-self-end border border-[var(--fm-line)] bg-white' : 'bg-[var(--fm-bg)] text-[var(--fm-ink)]')}>
              {m.text}
            </li>
          ))}
        </ol>

        {q ? (
          <div className="grid grid-cols-[minmax(0,1fr)] gap-3 rounded-[12px] border border-[var(--fm-line)] p-4">
            <div>
              <div className="text-[15px] font-semibold">{q.text}</div>
              <div className="mt-0.5 text-[12.5px] text-[var(--fm-ink2)]">{q.why}</div>
            </div>
            <Ask key={q.key} q={q} busy={busy} onAnswer={(v) => void run(() => onAnswer(q.key, v))} />
          </div>
        ) : (
          <div className="grid grid-cols-[minmax(0,1fr)] gap-3 rounded-[12px] border border-[var(--fm-line)] p-4">
            <div className="text-[15px] font-semibold">I have what I need</div>
            <p className="text-[12.5px] text-[var(--fm-ink2)]">
              {d.map.controls.length} controls from {d.map.frameworks.length} frameworks apply to you. I will turn each into a task, order them, suggest owners and keep the plan in step with your estate.
            </p>
            <div><button type="button" disabled={busy} onClick={() => void run(onGenerate)} className={primary}>{busy ? 'Building' : 'Build my plan'}</button></div>
          </div>
        )}
        {busy && q?.kind === 'text' && <p className="text-[12.5px] text-[var(--fm-ink3)]">Reading what you wrote…</p>}
        {failure && <div className="rounded-[10px] border border-red-200 bg-red-50 px-3 py-2 text-[12.5px] text-red-700">{failure}</div>}
      </section>

      <aside className="fm-card grid min-w-0 grid-cols-[minmax(0,1fr)] content-start gap-4 p-5" aria-label="What is mapped so far">
        <div className="text-[10.5px] font-semibold uppercase tracking-[0.08em] text-[var(--fm-ink3)]">What I have mapped</div>
        {d.facts.length > 0 && (
          <ul className="grid grid-cols-[minmax(0,1fr)] gap-1.5">
            {d.facts.map((f) => (
              <li key={f.key} className="text-[12.5px]">
                <span className="text-[var(--fm-ink2)]">{f.label.replace(/\?$/, '')}</span>
                <b className={cn('block break-words font-semibold', f.key === 'about' && 'line-clamp-2 font-medium')} title={f.key === 'about' ? f.display : undefined}>{f.display}</b>
                <span className="text-[11px] text-[var(--fm-ink3)]" title={f.basis}>{SOURCE[f.source] ?? f.source}</span>
              </li>
            ))}
          </ul>
        )}
        <div>
          <div className="mb-1 text-[12px] font-semibold">Frameworks</div>
          <ul className="grid gap-1">
            {d.map.frameworks.map((f) => (
              <li key={f.key} className="flex items-baseline gap-2 text-[12.5px]" title={f.reason}>
                <span className="min-w-0 flex-1 truncate">{f.name}</span>
                <span className="flex-none tabular-nums text-[var(--fm-ink3)]">{f.requirements} req</span>
              </li>
            ))}
          </ul>
        </div>
        <div>
          <div className="mb-1 text-[12px] font-semibold">Controls in scope · {d.map.controls.length}</div>
          {byLane.map((g) => (
            <div key={g.lane} className="mb-1.5">
              <div className="text-[11px] text-[var(--fm-ink3)]">{LANE_LABEL[g.lane]}</div>
              <div className="flex flex-wrap gap-1">
                {g.controls.map((c) => (
                  <span key={c.id} title={`${c.name}: ${c.requirements} requirements${c.maturity ? `, ${c.maturity}` : ''}`}
                    className="inline-flex items-center gap-1 rounded-full border border-[var(--fm-line)] bg-white px-2 py-0.5 text-[11px] text-[var(--fm-ink2)]">
                    <i aria-hidden className={cn('h-1.5 w-1.5 rounded-full', c.maturity ? MATURITY_TONE[c.maturity] : 'bg-[#c3c6cc]')} />
                    {c.name}
                  </span>
                ))}
              </div>
            </div>
          ))}
          {d.map.outOfScope.length > 0 && <p className="text-[11.5px] text-[var(--fm-ink3)]">Left out: {d.map.outOfScope.map((c) => `${c.name} (${c.why.toLowerCase()})`).join('; ')}</p>}
        </div>
        <div className="text-[12.5px]">
          <div className="mb-1 text-[12px] font-semibold">Systems · {d.map.systems.length}</div>
          {d.map.systems.length === 0 ? (
            <span className="text-[var(--fm-ink2)]">None yet. <Link href="/onboard" className="underline underline-offset-2">Register one</Link> or connect an integration.</span>
          ) : (
            <span className="text-[var(--fm-ink2)]">{d.map.systems.filter((s) => s.confirmed).length} with a confirmed tier</span>
          )}
        </div>
        <div>
          <div className="mb-1 text-[12px] font-semibold">Owners</div>
          <ul className="grid gap-0.5 text-[12.5px]">
            {d.map.owners.filter((o) => o.person).map((o) => <li key={o.role}><span className="text-[var(--fm-ink2)]">{o.label}:</span> {o.person}</li>)}
            {!d.map.owners.some((o) => o.person) && <li className="text-[var(--fm-ink3)]">None named yet</li>}
          </ul>
        </div>
      </aside>
    </div>
  )
}
