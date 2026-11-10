'use client'

import Link from 'next/link'
import { useLayoutEffect, useRef, useState } from 'react'
import { Bot, Lock } from 'lucide-react'
import { Sheet, SheetContent, SheetDescription, SheetHeader, SheetTitle } from '@/components/ui/sheet'
import { cn } from '@/lib/utils'
import type { Plan, PlanTask, TaskState } from '@/lib/api/hooks/usePlan'

export const COLUMNS: Array<{ key: TaskState; label: string; hint: string }> = [
  { key: 'todo', label: 'To do', hint: 'Waiting on an earlier task' },
  { key: 'needs_you', label: 'Needs you', hint: 'Ready for its owner' },
  { key: 'agent', label: 'Agent working', hint: 'Running now' },
  { key: 'review', label: 'In review', hint: 'Waiting for an approver' },
  { key: 'proven', label: 'Proven', hint: 'Evidence is on file' },
]
const STATE_DOT: Record<TaskState, string> = { todo: 'bg-[#c3c6cc]', needs_you: 'bg-[var(--fm-brand)]', agent: 'bg-[#378ADD]', review: 'bg-[#EF9F27]', proven: 'bg-[#1D9E75]' }
const STATE_LABEL = Object.fromEntries(COLUMNS.map((c) => [c.key, c.label])) as Record<TaskState, string>

function owner(t: PlanTask) {
  return t.owner ? t.owner : t.ownerSuggested ? `Suggested: ${t.ownerSuggested}` : 'No owner yet'
}

function Card({ t, onOpen, compact, names, refCb, dim }: { t: PlanTask; onOpen: () => void; compact?: boolean; names: Record<string, string>; refCb?: (el: HTMLButtonElement | null) => void; dim?: boolean }) {
  const pct = t.progress.total ? Math.round((t.progress.done / t.progress.total) * 100) : 0
  return (
    <button
      ref={refCb}
      type="button"
      onClick={onOpen}
      className={cn(
        'grid w-full gap-1.5 rounded-[12px] border border-[var(--fm-line)] bg-white p-3 text-left shadow-[0_1px_2px_rgba(20,20,30,.04)] transition-opacity hover:border-[var(--fm-ink)]',
        dim && 'opacity-35',
      )}
    >
      <div className="flex items-start gap-2">
        <i aria-hidden className={cn('mt-1.5 h-2 w-2 flex-none rounded-full', STATE_DOT[t.state])} />
        <span className="min-w-0 flex-1 text-[13px] font-semibold leading-snug">{t.title}</span>
        <span className="flex-none text-[11px] tabular-nums text-[var(--fm-ink3)]">#{t.priority}</span>
      </div>
      {!compact && (
        <div className="flex flex-wrap items-center gap-1.5 text-[11px] text-[var(--fm-ink2)]">
          <span>{t.requirements.length} requirements</span>
          {t.bindingCount > 0 && <span className="rounded-full bg-[#fff1ea] px-1.5 py-px text-[#993C1D]">{t.bindingCount} binding</span>}
          {t.by === 'agent' && <span className="inline-flex items-center gap-1 rounded-full bg-[#E6F1FB] px-1.5 py-px text-[#0C447C]"><Bot className="h-3 w-3" aria-hidden />agent</span>}
        </div>
      )}
      {t.progress.total > 1 && (
        <div className="flex items-center gap-2">
          <span className="h-1 flex-1 overflow-hidden rounded-full bg-[var(--fm-line)]"><span className="block h-full bg-[var(--fm-ink)]" style={{ width: `${pct}%` }} /></span>
          <span className="text-[11px] tabular-nums text-[var(--fm-ink3)]">{t.progress.done}/{t.progress.total}</span>
        </div>
      )}
      <div className="truncate text-[11.5px] text-[var(--fm-ink3)]">{owner(t)}</div>
      {!compact && t.state === 'todo' && t.blockedBy && t.blockedBy.length > 0 && (
        <div className="flex items-center gap-1 text-[11px] text-[var(--fm-ink3)]"><Lock className="h-3 w-3" aria-hidden />After {t.blockedBy.map((k) => names[k] ?? k).join(', ')}</div>
      )}
    </button>
  )
}

export function Kanban({ tasks, onOpen }: { tasks: PlanTask[]; onOpen: (t: PlanTask) => void }) {
  const names = Object.fromEntries(tasks.map((t) => [t.key, t.controlName]))
  return (
    <div className="grid auto-cols-[minmax(240px,1fr)] grid-flow-col gap-3 overflow-x-auto pb-2">
      {COLUMNS.map((c) => {
        const mine = tasks.filter((t) => t.state === c.key)
        return (
          <section key={c.key} aria-label={c.label} className="grid content-start gap-2 rounded-[14px] bg-[rgba(21,23,26,.035)] p-2">
            <header className="flex items-baseline gap-2 px-1 pt-1">
              <i aria-hidden className={cn('h-2 w-2 rounded-full', STATE_DOT[c.key])} />
              <span className="text-[12.5px] font-semibold">{c.label}</span>
              <span className="text-[12px] tabular-nums text-[var(--fm-ink3)]">{mine.length}</span>
            </header>
            {mine.map((t) => <Card key={t.key} t={t} names={names} onOpen={() => onOpen(t)} />)}
            {mine.length === 0 && <p className="px-1 pb-1 text-[11.5px] text-[var(--fm-ink3)]">{c.hint}</p>}
          </section>
        )
      })}
    </div>
  )
}

/** The governance journey: lanes left to right, each task where it belongs, arrows from what it waits on. */
export function WorkflowView({ tasks, lanes, onOpen }: { tasks: PlanTask[]; lanes: Plan['lanes']; onOpen: (t: PlanTask) => void }) {
  const wrap = useRef<HTMLDivElement>(null)
  const cards = useRef<Record<string, HTMLButtonElement | null>>({})
  const [edges, setEdges] = useState<Array<{ from: string; to: string; d: string }>>([])
  const [size, setSize] = useState({ w: 0, h: 0 })
  const [focus, setFocus] = useState<string | null>(null)
  const names = Object.fromEntries(tasks.map((t) => [t.key, t.controlName]))
  const byKey = Object.fromEntries(tasks.map((t) => [t.key, t]))
  const depths: Record<string, number> = {}
  const depth = (key: string, seen: string[] = []): number => {
    if (key in depths) return depths[key]
    const deps = (byKey[key]?.dependsOn ?? []).filter((d) => byKey[d] && !seen.includes(d))
    depths[key] = deps.length ? 1 + Math.max(...deps.map((d) => depth(d, [...seen, key]))) : 0
    return depths[key]
  }

  useLayoutEffect(() => {
    const draw = () => {
      const box = wrap.current?.getBoundingClientRect()
      if (!box) return
      const next: Array<{ from: string; to: string; d: string }> = []
      for (const t of tasks) {
        for (const dep of t.dependsOn) {
          const a = cards.current[dep]?.getBoundingClientRect()
          const b = cards.current[t.key]?.getBoundingClientRect()
          if (!a || !b) continue
          const sameLane = Math.abs(a.left - b.left) < 4
          const x1 = sameLane ? a.left - box.left + 10 : a.right - box.left
          const y1 = sameLane ? a.bottom - box.top : a.top - box.top + a.height / 2
          const x2 = sameLane ? b.left - box.left + 10 : b.left - box.left
          const y2 = sameLane ? b.top - box.top : b.top - box.top + b.height / 2
          const d = sameLane
            ? `M${x1},${y1} C${x1 - 14},${(y1 + y2) / 2} ${x2 - 14},${(y1 + y2) / 2} ${x2},${y2}`
            : `M${x1},${y1} C${x1 + 28},${y1} ${x2 - 28},${y2} ${x2},${y2}`
          next.push({ from: dep, to: t.key, d })
        }
      }
      setEdges(next)
      setSize({ w: box.width, h: box.height })
    }
    draw()
    const ro = new ResizeObserver(draw)
    if (wrap.current) ro.observe(wrap.current)
    return () => ro.disconnect()
  }, [tasks])

  // The focused task, everything it waits on, and everything waiting on it.
  const related = new Set<string>()
  if (focus) {
    const walk = (key: string, dir: 'up' | 'down') => {
      for (const e of edges) {
        const next = dir === 'up' ? (e.to === key ? e.from : null) : e.from === key ? e.to : null
        if (next && !related.has(next)) {
          related.add(next)
          walk(next, dir)
        }
      }
    }
    related.add(focus)
    walk(focus, 'up')
    walk(focus, 'down')
  }

  return (
    <div className="overflow-x-auto pb-2">
      <div ref={wrap} className="relative grid min-w-[1000px] grid-cols-5 gap-6">
        <svg className="pointer-events-none absolute inset-0" width={size.w} height={size.h} aria-hidden>
          <defs>
            <marker id="plan-arrow" viewBox="0 0 8 8" refX="7" refY="4" markerWidth="7" markerHeight="7" orient="auto-start-reverse">
              <path d="M0,0 L8,4 L0,8 z" fill="#9096a0" />
            </marker>
          </defs>
          {edges.map((e) => {
            const on = focus ? related.has(e.from) && related.has(e.to) : false
            return <path key={`${e.from}-${e.to}`} d={e.d} fill="none" stroke={on ? '#15171a' : '#c3c6cc'} strokeWidth={on ? 1.6 : 1} opacity={focus && !on ? 0.25 : 1} markerEnd="url(#plan-arrow)" />
          })}
        </svg>
        {lanes.map((lane, i) => {
          // Within a lane, what a task waits on sits above it; ties keep priority order.
          const mine = tasks.filter((t) => t.lane === lane.key).sort((a, b) => depth(a.key) - depth(b.key) || a.priority - b.priority)
          const done = mine.filter((t) => t.state === 'proven').length
          return (
            <section key={lane.key} aria-label={lane.label} className="relative grid content-start gap-3">
              <header className="px-0.5">
                <div className="text-[10.5px] font-semibold uppercase tracking-[0.08em] text-[var(--fm-ink3)]">{String(i + 1).padStart(2, '0')}</div>
                <div className="text-[13px] font-semibold">{lane.label}</div>
                <div className="text-[11.5px] tabular-nums text-[var(--fm-ink3)]">{done} of {mine.length} proven</div>
              </header>
              {mine.map((t) => (
                <div key={t.key} onMouseEnter={() => setFocus(t.key)} onMouseLeave={() => setFocus(null)} onFocus={() => setFocus(t.key)} onBlur={() => setFocus(null)}>
                  <Card t={t} compact names={names} refCb={(el) => { cards.current[t.key] = el }} onOpen={() => onOpen(t)} dim={!!focus && !related.has(t.key)} />
                </div>
              ))}
            </section>
          )
        })}
      </div>
    </div>
  )
}

/** One task: why it exists, what it covers per system, who owns it, what to do next. */
export function TaskDrawer({ t, tasks, onClose, onAssign, onAttest }: {
  t: PlanTask | null
  tasks: PlanTask[]
  onClose: () => void
  onAssign: (key: string, owner: string) => Promise<unknown>
  onAttest: (key: string, statement: string, reference: string) => Promise<unknown>
}) {
  const [ownerv, setOwner] = useState('')
  const [statement, setStatement] = useState('')
  const [reference, setReference] = useState('')
  const [busy, setBusy] = useState(false)
  const [failure, setFailure] = useState<string | null>(null)
  const byKey = Object.fromEntries(tasks.map((x) => [x.key, x]))
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
  const frameworks = t ? Array.from(new Set(t.requirements.map((r) => r.framework))) : []
  const label = 'text-[10.5px] font-semibold uppercase tracking-[0.08em] text-[var(--fm-ink3)]'
  const input = 'h-9 min-w-0 flex-1 rounded-[10px] border border-[var(--fm-line)] bg-white px-2.5 text-[13px] outline-none focus:border-[var(--fm-ink)]'

  return (
    <Sheet open={!!t} onOpenChange={(o) => { if (!o) { onClose(); setOwner(''); setStatement(''); setReference(''); setFailure(null) } }}>
      <SheetContent className="flex w-full flex-col gap-5 overflow-y-auto border-l border-[var(--fm-line)] bg-white p-6 text-[var(--fm-ink)] sm:max-w-[500px]">
        {t && (
          <>
            <SheetHeader className="space-y-1 text-left">
              <span className="flex items-center gap-2 text-[11.5px] text-[var(--fm-ink2)]">
                <i aria-hidden className={cn('h-2 w-2 rounded-full', STATE_DOT[t.state])} />{STATE_LABEL[t.state]} · priority {t.priority} · {t.controlId}
              </span>
              <SheetTitle className="text-[18px] font-semibold leading-snug tracking-[-0.01em] text-[var(--fm-ink)]">{t.title}</SheetTitle>
              <SheetDescription className="text-[13px] text-[var(--fm-ink2)]">{t.objective}</SheetDescription>
            </SheetHeader>

            <div className="grid gap-1.5">
              <div className={label}>Owner</div>
              <div className="text-[13px]">{t.owner ?? <span className="text-[var(--fm-ink2)]">{t.ownerSuggested ? `Suggested: ${t.ownerSuggested}` : 'Nobody yet'}</span>}</div>
              <div className="text-[12px] text-[var(--fm-ink3)]">{t.ownerReason}</div>
              <form className="flex gap-2" onSubmit={(e) => { e.preventDefault(); const v = ownerv.trim() || (t.owner ? '' : t.ownerSuggested) || ''; if (v) void run(() => onAssign(t.key, v).then(() => setOwner(''))) }}>
                <input value={ownerv} onChange={(e) => setOwner(e.target.value)} placeholder={t.ownerSuggested ?? 'Name or email'} aria-label="Owner" className={input} />
                <button type="submit" disabled={busy || !(ownerv.trim() || (t.ownerSuggested && !t.owner))} className="h-9 rounded-full bg-[var(--fm-ink)] px-3.5 text-[12.5px] font-semibold text-white disabled:opacity-50">
                  {ownerv.trim() || t.owner ? 'Assign' : 'Accept suggestion'}
                </button>
              </form>
            </div>

            {t.systems.length > 0 && (
              <div className="grid gap-1.5">
                <div className={label}>Systems · {t.progress.done} of {t.progress.total} done</div>
                <ul className="grid gap-1">
                  {t.systems.map((s) => (
                    <li key={s.id}>
                      <Link href={`/systems/${encodeURIComponent(s.id)}`} className="flex items-center gap-2 rounded-[10px] border border-[var(--fm-line)] px-2.5 py-1.5 text-[12.5px] hover:border-[var(--fm-ink)]">
                        <i aria-hidden className={cn('h-2 w-2 flex-none rounded-full', s.done ? 'bg-[#1D9E75]' : s.detail === 'fails' ? 'bg-[#E24B4A]' : 'bg-[#c3c6cc]')} />
                        <span className="min-w-0 flex-1 truncate font-medium">{s.name}</span>
                        {s.agent && <span className="inline-flex items-center gap-1 text-[11px] text-[#0C447C]"><Bot className="h-3 w-3" aria-hidden />agent</span>}
                        <span className="text-[11.5px] text-[var(--fm-ink3)]">{s.detail}</span>
                      </Link>
                    </li>
                  ))}
                </ul>
              </div>
            )}
            {t.kind !== 'org' && t.systems.length === 0 && <p className="text-[12.5px] text-[var(--fm-ink2)]">No systems yet. It fills in as you <Link href="/onboard" className="underline underline-offset-2">register systems</Link>.</p>}

            {t.dependsOn.length > 0 && (
              <div className="grid gap-1.5">
                <div className={label}>Comes after</div>
                <ul className="grid gap-1 text-[12.5px]">
                  {t.dependsOn.map((k) => (
                    <li key={k} className="flex items-center gap-2"><i aria-hidden className={cn('h-2 w-2 rounded-full', STATE_DOT[byKey[k]?.state ?? 'todo'])} />{byKey[k]?.title ?? k}</li>
                  ))}
                </ul>
              </div>
            )}

            {t.actions.length > 0 && (
              <div className="grid gap-1.5">
                <div className={label}>How to do it</div>
                <ul className="grid gap-1">
                  {t.actions.map((a) => (
                    <li key={a.id}>
                      <Link href={`/compliance/workflows/${a.id}`} className="grid rounded-[10px] border border-[var(--fm-line)] px-2.5 py-1.5 text-[12.5px] hover:border-[var(--fm-ink)]">
                        <span className="font-medium">{a.name}</span>
                        <span className="text-[11.5px] text-[var(--fm-ink3)]">{a.scope}{a.approver ? ` · approver: ${a.approver}` : ''}{a.installed ? '' : ' · pack not installed yet'}</span>
                      </Link>
                    </li>
                  ))}
                </ul>
              </div>
            )}

            {t.kind === 'org' && (
              <div className="grid gap-1.5">
                <div className={label}>Already in place?</div>
                {t.attestation ? (
                  <p className="text-[12.5px] text-[var(--fm-ink2)]">Attested by {t.attestation.attested_by}: &quot;{t.attestation.statement}&quot;{t.attestation.reference ? ` (${t.attestation.reference})` : ''}. It counts as attested, not measured.</p>
                ) : (
                  <form className="grid gap-2" onSubmit={(e) => { e.preventDefault(); if (statement.trim().length >= 12) void run(() => onAttest(t.key, statement.trim(), reference.trim())) }}>
                    <textarea value={statement} onChange={(e) => setStatement(e.target.value)} rows={2} placeholder="What is in place, and since when" aria-label="Attestation"
                      className="rounded-[10px] border border-[var(--fm-line)] p-2.5 text-[13px] outline-none focus:border-[var(--fm-ink)]" />
                    <div className="flex gap-2">
                      <input value={reference} onChange={(e) => setReference(e.target.value)} placeholder="Where the evidence is (a link or document)" aria-label="Reference" className={input} />
                      <button type="submit" disabled={busy || statement.trim().length < 12} className="h-9 rounded-full border border-[var(--fm-line)] bg-white px-3.5 text-[12.5px] font-medium hover:border-[var(--fm-ink)] disabled:opacity-50">Attest</button>
                    </div>
                  </form>
                )}
              </div>
            )}

            <div className="grid gap-1.5">
              <div className={label}>Requirements it closes · {t.requirements.length}</div>
              {frameworks.map((fw) => (
                <div key={fw}>
                  <div className="text-[12px] font-semibold">{fw}</div>
                  <ul className="grid gap-0.5">
                    {t.requirements.filter((r) => r.framework === fw).slice(0, 12).map((r) => (
                      <li key={r.key} className="text-[12px] text-[var(--fm-ink2)]"><span className="tabular-nums text-[var(--fm-ink3)]">{r.control}</span> {r.title}</li>
                    ))}
                  </ul>
                </div>
              ))}
            </div>
            {failure && <div className="rounded-[10px] border border-red-200 bg-red-50 px-3 py-2 text-[12.5px] text-red-700">{failure}</div>}
          </>
        )}
      </SheetContent>
    </Sheet>
  )
}
