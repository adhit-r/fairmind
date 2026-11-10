'use client'

import Link from 'next/link'
import { useSearchParams } from 'next/navigation'
import { Suspense, useEffect, useMemo, useRef, useState } from 'react'
import { STAGES } from '@/components/layout/AppShell'
import { CommandBar } from '@/components/layout/CommandBar'
import { BTN, BTN_P, ErrorNote, Loading, cap } from '@/components/packs/parts'
import { CellDrawer, CellMeaning, classLabel, DrawerBlock, Matrix, checkCell, type MatrixGroup } from '@/components/ui/matrix'
import { useSystemContext } from '@/components/workflow/SystemContext'
import { useEstateGates } from '@/lib/api/hooks/useEstate'
import { useIntegrations } from '@/lib/api/hooks/useIntegrations'
import { usePendingDecisions } from '@/lib/api/hooks/usePendingDecisions'
import { cn } from '@/lib/utils'
import { VERDICT_LABEL, VERDICT_TONE } from '../systems/[id]/VerdictExplainer'
import { CHECKS, CHECK_ACTION, estateGroups, estateNext, sinceLine, stations } from './estate'
import { EstateDemo } from '@/components/stageshow/EstateDemo'
import { Illustration } from '@/components/stageshow/fm'

const LAST_VISIT = 'fairmind:last-visit'
const LAPSED_SEEN = 'fairmind:lapsed-seen'
const SEG_ITEM = 'inline-flex h-7 flex-none items-center whitespace-nowrap rounded-full px-3 text-[12.5px] font-medium text-[var(--fm-ink2)] hover:text-[var(--fm-ink)]'
const SEG_ON = 'bg-[var(--fm-ink)] text-white hover:text-white'
const LINK = 'font-medium text-[var(--fm-ink)] underline-offset-2 hover:underline'
const SMALL = 'h-8 px-3 text-[12px]'

/** The last visit is a per-viewer convenience; storage can be missing or blocked. A first visit records now. */
function readLastVisit(): { at: string | null; seen: string[] } {
  try {
    const at = window.localStorage.getItem(LAST_VISIT)
    if (!at) window.localStorage.setItem(LAST_VISIT, new Date().toISOString())
    const seen = JSON.parse(window.localStorage.getItem(LAPSED_SEEN) || '[]')
    return { at, seen: Array.isArray(seen) ? seen.filter((x): x is string => typeof x === 'string') : [] }
  } catch {
    return { at: null, seen: [] }
  }
}
function writeLastVisit(at: string, seen: string[]) {
  try {
    window.localStorage.setItem(LAST_VISIT, at)
    window.localStorage.setItem(LAPSED_SEEN, JSON.stringify(seen))
  } catch {
    /* storage blocked: the line comes back next visit */
  }
}
const when = (iso: string) => new Date(iso).toLocaleString('en-GB', { weekday: 'short', day: 'numeric', month: 'short', hour: '2-digit', minute: '2-digit' })

function Overview() {
  const { systems, loading, refreshSystems } = useSystemContext()
  const real = useMemo(() => systems.filter((s) => s.metadata?.source !== 'fallback'), [systems])
  const { requests: allRequests } = usePendingDecisions()
  // Approval requests are not org-scoped yet; keep only those for systems in this estate.
  const pending = useMemo(() => new Set(allRequests.filter((r) => real.some((s) => s.id === r.entity_id)).map((r) => r.entity_id)), [allRequests, real])
  const gatesRes = useEstateGates()
  const gates = useMemo(() => new Map((gatesRes.data ?? []).map((g) => [g.systemId, g])), [gatesRes.data])
  const integrations = useIntegrations()
  const stage = useSearchParams().get('stage')
  const [sort, setSort] = useState(false)
  const [cell, setCell] = useState<{ row: string; col: string } | null>(null)
  const [foundOpen, setFoundOpen] = useState(false)
  const [sinceOpen, setSinceOpen] = useState(false)
  const [lastVisit, setLastVisit] = useState<{ at: string | null; seen: string[] }>({ at: null, seen: [] })
  const visitRead = useRef(false)
  const [acting, setActing] = useState<string | null>(null)
  const [actError, setActError] = useState<string | null>(null)
  useEffect(() => {
    // Read once: a second run (React strict mode) would see the visit the first run just recorded.
    if (visitRead.current) return
    visitRead.current = true
    setLastVisit(readLastVisit())
  }, [])

  const next = estateNext(real, gates, pending)
  const settled = !loading && !gatesRes.loading && !integrations.loading
  const since = settled ? sinceLine(lastVisit.at, real, gates, integrations.discovered, lastVisit.seen) : null
  const groupsAll = estateGroups(real, gates, pending, STAGES)
  const shown = estateGroups(real, gates, pending, STAGES, { filter: stage, sort })
  const blank = gatesRes.loading ? 'Loading the release gate' : gatesRes.error ? `Release gate unavailable: ${gatesRes.error}` : 'No release gate for this system yet'
  const groups: MatrixGroup[] = shown.map((g) => ({
    label: g.label,
    rows: g.systems.map((s) => {
      const gate = gates.get(s.id)
      const red = gate?.verdict === 'no_go' && (s.stage === 'remediate' || s.stage === 'operate')
      return {
        key: s.id,
        label: s.name,
        title: `${cap(s.riskTier)} · ${s.owner}`,
        href: `/systems/${s.id}`,
        cells: CHECKS.map((c) => {
          const check = gate?.checks.find((x) => x.key === c.key)
          return check ? checkCell(check) : null
        }),
        blank,
        tail: [
          gate ? (
            <span className="inline-flex items-baseline gap-2">
              <b className={cn('text-[12px] font-semibold', gate.verdict === 'no_go' && !red ? 'text-[var(--fm-ink)]' : VERDICT_TONE[gate.verdict])}>{VERDICT_LABEL[gate.verdict]}</b>
              <span className="font-mono text-[11.5px] text-[var(--fm-ink2)]">{gate.confidence.toFixed(2)}</span>
            </span>
          ) : null,
        ],
      }
    }),
  }))
  const shownCount = shown.reduce((n, g) => n + g.systems.length, 0)
  const counts = Object.fromEntries(groupsAll.map((g) => [g.key, g.systems.length]))

  const act = async (id: string, run: () => Promise<unknown>) => {
    setActing(id)
    setActError(null)
    try {
      await run()
      await refreshSystems()
      gatesRes.reload()
    } catch (e) {
      setActError(e instanceof Error ? e.message : 'The action failed')
    } finally {
      setActing(null)
    }
  }

  if (!loading && real.length === 0) {
    return (
      <section className="fm-card grid min-h-[420px] place-items-center p-9 text-center">
        <div className="max-w-md">
          <Illustration className="mb-7" label="The Estate grid once sources are connected: each system's five release checks and its gate verdict">
            <EstateDemo />
          </Illustration>
          <h1 className="text-[28px] font-semibold tracking-tight">No AI systems under governance yet</h1>
          <p className="mt-3 text-[15px] text-[var(--fm-ink2)]">
            Register the first system to start the lifecycle. Evidence, decisions and framework coverage build from there.
          </p>
          <div className="mt-6 flex flex-wrap items-center justify-center gap-3">
            <Link href="/integrations" className={BTN_P}>
              Connect MLflow or GitHub
            </Link>
            <Link href="/onboard" className={BTN}>
              Register manually
            </Link>
          </div>
        </div>
      </section>
    )
  }

  const picked = cell ? { s: real.find((x) => x.id === cell.row), c: CHECKS.find((x) => x.key === cell.col) } : null
  const pickedCheck = picked?.s && picked.c ? gates.get(picked.s.id)?.checks.find((x) => x.key === picked.c!.key) : undefined

  return (
    <div className="grid grid-cols-[minmax(0,1fr)] gap-4">
      <CommandBar stage={next.stage} title={next.title} reason={next.reason} primary={next.primary} />

      {since && lastVisit.at && (
        <div className="flex flex-wrap items-center gap-x-2 gap-y-1 px-1 text-[12.5px] text-[var(--fm-ink2)]">
          <span>
            Since {when(lastVisit.at)} · {since.parts.join(' · ')}
          </span>
          <button type="button" className={LINK} aria-expanded={sinceOpen} onClick={() => setSinceOpen((v) => !v)}>
            {sinceOpen ? 'Hide' : 'Show'}
          </button>
          <button
            type="button"
            className="ml-auto text-[12px] text-[var(--fm-ink3)] hover:text-[var(--fm-ink)]"
            onClick={() => {
              const now = { at: new Date().toISOString(), seen: real.filter((x) => gates.get(x.id)?.checks.some((c) => c.stale)).map((x) => x.id) }
              writeLastVisit(now.at, now.seen)
              setLastVisit(now)
            }}
          >
            Dismiss
          </button>
          {sinceOpen && (
            <ul className="grid basis-full gap-1 pt-1">
              {since.rows.map((r) => (
                <li key={r.key} className="flex min-w-0 gap-2">
                  {r.href ? (
                    <Link href={r.href} className={cn(LINK, 'truncate')}>
                      {r.label}
                    </Link>
                  ) : (
                    <b className="truncate font-medium text-[var(--fm-ink)]">{r.label}</b>
                  )}
                  <span className="truncate text-[var(--fm-ink3)]">{r.detail}</span>
                </li>
              ))}
            </ul>
          )}
        </div>
      )}

      <section className="fm-card overflow-hidden" aria-label="Estate">
        <div className="flex flex-wrap items-center gap-x-3 gap-y-2 px-[18px] pb-3 pt-4">
          <h2 className="text-[15px] font-semibold tracking-[-0.01em]">Estate</h2>
          <nav aria-label="Stage" className="fm-strip flex min-w-0 max-w-full gap-0.5 overflow-x-auto rounded-full border border-[var(--fm-line)] bg-white p-0.5">
            <Link href="/dashboard" className={cn(SEG_ITEM, !stage && SEG_ON)} aria-current={!stage ? 'page' : undefined}>
              All {real.length}
            </Link>
            {stations(STAGES).map((s) => (
              <Link key={s.key} href={`/dashboard?stage=${s.key}`} className={cn(SEG_ITEM, stage === s.key && SEG_ON)} aria-current={stage === s.key ? 'page' : undefined}>
                {s.label} {counts[s.key] ?? 0}
              </Link>
            ))}
          </nav>
          <button type="button" className={cn(LINK, 'ml-auto text-[12.5px]')} aria-pressed={sort} onClick={() => setSort((v) => !v)}>
            Sort by confidence{sort ? ', lowest first' : ''}
          </button>
        </div>

        {loading ? (
          <div className="px-[18px] pb-[18px]">
            <Loading label="Loading the estate" />
          </div>
        ) : shownCount === 0 ? (
          <p className="px-[18px] pb-[18px] text-[12.5px] text-[var(--fm-ink2)]">No systems at this stage.</p>
        ) : (
          <Matrix
            id="estate"
            head={`${shownCount} system${shownCount === 1 ? '' : 's'}`}
            colGroups={[{ label: 'Release checks', cols: CHECKS.map((c) => ({ key: c.key, label: c.label })) }]}
            groups={groups}
            tail={[{ key: 'verdict', label: 'Verdict' }]}
            onCell={(row, col) => setCell({ row, col })}
          />
        )}
        {gatesRes.error && (
          <div className="px-[18px] pb-3">
            <ErrorNote message={`Release gates did not load: ${gatesRes.error}`} onRetry={gatesRes.reload} />
          </div>
        )}

        {integrations.discovered.length > 0 && (
          <div className="border-t border-[var(--fm-line)]">
            <button
              type="button"
              aria-expanded={foundOpen}
              onClick={() => setFoundOpen((v) => !v)}
              className="flex w-full items-center gap-2 px-[18px] py-2.5 text-left text-[12.5px] text-[var(--fm-ink2)]"
            >
              <i aria-hidden className="h-1.5 w-1.5 flex-none rounded-full bg-[var(--fm-brand)]" />
              {integrations.discovered.length} system{integrations.discovered.length === 1 ? '' : 's'} found by the agent ·{' '}
              <span className={LINK}>{foundOpen ? 'Hide' : 'Review'}</span>
            </button>
            {foundOpen && (
              <div className="grid">
                {actError && (
                  <div className="px-[18px] pb-2">
                    <ErrorNote message={actError} />
                  </div>
                )}
                {integrations.discovered.map((d) => (
                  <div key={d.id} className="flex flex-wrap items-center gap-x-3 gap-y-1 border-t border-[var(--fm-line)] px-[18px] py-2">
                    <b className="min-w-0 truncate text-[13px] font-medium">{d.name}</b>
                    <span className="text-[12px] text-[var(--fm-ink3)]">
                      {cap(d.source)} · suggested {d.suggestedTier}
                    </span>
                    <span className="ml-auto flex gap-2">
                      <button type="button" className={cn(BTN_P, SMALL)} disabled={acting !== null} onClick={() => act(d.id, () => integrations.promote(d.id))}>
                        Add
                      </button>
                      <button type="button" className={cn(BTN, SMALL)} disabled={acting !== null} onClick={() => act(d.id, () => integrations.ignore(d.id))}>
                        Ignore
                      </button>
                    </span>
                  </div>
                ))}
              </div>
            )}
          </div>
        )}
      </section>

      <CellDrawer
        open={!!(picked?.s && picked.c)}
        onClose={() => setCell(null)}
        label={picked?.s ? `${picked.s.name} · release check` : 'Release check'}
        title={picked?.c?.label ?? ''}
      >
        {picked?.s && picked.c && (
          <>
            <DrawerBlock label="State">
              <CellMeaning cell={pickedCheck ? checkCell(pickedCheck) : null} />
            </DrawerBlock>
            <DrawerBlock label="Confidence">
              <span>
                <span className="font-mono">{(pickedCheck?.confidence ?? 0).toFixed(2)}</span>
                <span className="text-[var(--fm-ink2)]"> · {pickedCheck?.evidenceClass ? classLabel(pickedCheck.evidenceClass) : 'nothing current on file'}</span>
              </span>
            </DrawerBlock>
            <DrawerBlock label="Produced by">
              <span>{CHECK_ACTION[picked.c.key]}</span>
            </DrawerBlock>
            <Link href={`/systems/${picked.s.id}`} className={cn(BTN_P, 'self-start')}>
              Open system
            </Link>
          </>
        )}
      </CellDrawer>
    </div>
  )
}

export default function DashboardPage() {
  return (
    <Suspense fallback={null}>
      <Overview />
    </Suspense>
  )
}
