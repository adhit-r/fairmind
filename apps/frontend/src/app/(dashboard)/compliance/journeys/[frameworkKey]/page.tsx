'use client'

import Link from 'next/link'
import { useParams } from 'next/navigation'
import { useMemo, useState } from 'react'
import { useInstaller, useJourney, usePackNames, type ReqStatus } from '@/lib/api/hooks/usePacks'
import { IsoFigure } from '@/components/packs/IsoFigure'
import { journeyFigure, type FigWorkflow } from '@/components/packs/figures'
import { BTN, BTN_P, CoverageBar, Crumbs, EnginePill, ErrorNote, Heading, LABEL, LINE, Loading, MUTED, Pill, REQ_ORDER, ReqPill, ResultPill, StatusPill, cap, reqHint, reqLabel } from '@/components/packs/parts'
import { cn } from '@/lib/utils'

const TILE: Record<ReqStatus, FigWorkflow['status']> = { covered: 'done', tested: 'tested', available: null, supported: 'supported', gap: 'gap' }
/** Swatches that match the tiles in the figure. */
const SWATCH: Record<ReqStatus, string> = {
  covered: 'bg-[#a9d6bf]',
  tested: 'bg-[#c4d7f1]',
  available: 'border-dashed border-[#8a8f98] bg-white',
  supported: 'bg-white',
  gap: 'bg-[#b0b3b9]',
}
/** Covered and tested both count toward the installed coverage figure. */
const counts = (s: ReqStatus) => s === 'covered' || s === 'tested'
const pct = (n: number, total: number) => (total > 0 ? Math.min(100, (n / total) * 100) : 0)

export default function JourneyPage() {
  const { frameworkKey } = useParams<{ frameworkKey: string }>()
  const journey = useJourney(frameworkKey)
  const installer = useInstaller(journey.reload)
  const packName = usePackNames()
  const [filter, setFilter] = useState<ReqStatus | null>(null)

  const view = useMemo(() => {
    const groups = journey.data?.groups ?? []
    const counts: Record<ReqStatus, number> = { covered: 0, tested: 0, available: 0, supported: 0, gap: 0 }
    for (const g of groups) for (const r of g.requirements) counts[r.status]++
    const figure = journeyFigure(
      groups.map((g, i) => ({
        tag: `GROUP ${i + 1}`,
        name: g.name,
        workflows: g.requirements.map((r) => r.status).sort((a, b) => REQ_ORDER.indexOf(a) - REQ_ORDER.indexOf(b)).map((s) => ({ status: TILE[s] })),
      })),
    )
    // Installed workflows per requirement group, each once; the same workflow can serve several groups.
    const byGroup = groups
      .map((g) => {
        const seen = new Map<string, (typeof g.requirements)[number]['workflows'][number]>()
        for (const r of g.requirements) for (const w of r.workflows) if (w.installed && !seen.has(w.id)) seen.set(w.id, w)
        return { name: g.name, workflows: [...seen.values()] }
      })
      .filter((g) => g.workflows.length > 0)
    const waiting = new Map<string, { run: NonNullable<(typeof byGroup)[number]['workflows'][number]['latestRun']>; name: string; group: string }>()
    for (const g of byGroup) for (const w of g.workflows) if (w.latestRun?.status === 'waiting' && !waiting.has(w.latestRun.id)) waiting.set(w.latestRun.id, { run: w.latestRun, name: w.name, group: g.name })
    return { groups, counts, figure, total: groups.reduce((n, g) => n + g.requirements.length, 0), byGroup, waiting: [...waiting.values()] }
  }, [journey.data])

  if (journey.loading && !journey.data) return <Loading label="Loading journey" />
  if (journey.error || !journey.data) {
    return (
      <div className="flex flex-col gap-4">
        <Crumbs items={[{ label: 'Frameworks', href: '/compliance' }, { label: 'Journey' }]} />
        <ErrorNote message={`This journey could not be loaded. ${journey.error ?? ''}`} onRetry={journey.reload} />
      </div>
    )
  }

  const j = journey.data
  const meta = [j.version && `Version ${j.version}`, j.binding, j.status].filter((x): x is string => Boolean(x))
  const missing = j.steps.filter((s) => !s.installed)
  const shown = view.groups
    .map((g) => ({ ...g, requirements: filter ? g.requirements.filter((r) => r.status === filter) : g.requirements }))
    .filter((g) => g.requirements.length > 0)

  return (
    <div className="flex flex-col gap-[22px]">
      <Crumbs items={[{ label: 'Frameworks', href: '/compliance' }, { label: j.name }]} />
      <Heading
        title={j.name}
        lead={`Readiness against this framework from the packs you have installed.${view.waiting.length ? ` ${view.waiting.length} ${view.waiting.length === 1 ? 'run is' : 'runs are'} waiting for you.` : ''}`}
      >
        <Link href="/compliance/evaluations" className={BTN}>Browse evaluations</Link>
        {view.waiting.length > 0 && (
          <Link href={`/compliance/runs/${view.waiting[0].run.id}`} className={BTN_P}>
            Review {view.waiting.length} {view.waiting.length === 1 ? 'decision' : 'decisions'}
          </Link>
        )}
      </Heading>
      {meta.length > 0 && (
        <div className="-mt-3 flex flex-wrap gap-2">
          {meta.map((m) => (
            <Pill key={m}>{m}</Pill>
          ))}
        </div>
      )}
      {installer.failure && <ErrorNote message={installer.failure} />}

      <section aria-label="Readiness summary" className="pk-card flex flex-wrap items-stretch gap-[22px] p-[18px]">
        <div className="flex flex-[1_1_280px] flex-col gap-5 px-2 py-2">
          <div className="flex flex-col gap-2">
            <span className={LABEL}>Installed coverage</span>
            <p className="m-0 flex items-baseline gap-2 text-[var(--fm-ink)]">
              <span className="text-[40px] font-semibold leading-none tracking-[-0.03em] tabular-nums">{j.coveredInstalled}</span>
              <span className={cn('text-[15px] tabular-nums', MUTED)}>of {j.active} requirements</span>
            </p>
            <CoverageBar label={`${j.name} coverage`} installed={j.coveredInstalled} all={j.coveredAll} total={j.active} allLabel="with every pack in the catalogue" />
          </div>
          <div className="flex flex-col gap-1.5">
            <span className={LABEL}>By status</span>
            <ul className="m-0 flex list-none flex-col p-0" aria-label="Filter requirements by status">
              {REQ_ORDER.map((s) => (
                <li key={s}>
                  <button
                    type="button"
                    aria-pressed={filter === s}
                    disabled={view.counts[s] === 0}
                    onClick={() => setFilter(filter === s ? null : s)}
                    title={reqHint(s)}
                    className={cn(
                      '-mx-2 flex w-[calc(100%+16px)] items-center gap-2.5 rounded-[10px] px-2 py-1.5 text-left text-[13px] text-[var(--fm-ink)] transition-colors hover:bg-[var(--fm-bg)] disabled:cursor-default disabled:text-[var(--fm-ink3)] disabled:hover:bg-transparent',
                      filter === s && 'bg-[var(--fm-bg)] font-semibold',
                    )}
                  >
                    <span aria-hidden className={`inline-block h-3.5 w-3.5 flex-none rounded border border-[rgba(21,23,26,.12)] ${SWATCH[s]}`} />
                    <span className="flex-grow">{reqLabel(s)}</span>
                    <span className="tabular-nums">{view.counts[s]}</span>
                  </button>
                </li>
              ))}
            </ul>
          </div>
        </div>
        <div className="min-w-0 flex-[999_1_560px]">
          {j.groups.length === 0 ? (
            <p className={`m-0 p-6 text-[13px] ${MUTED}`}>This framework has no active requirements.</p>
          ) : (
            <IsoFigure
              className="p-2.5"
              figure={view.figure}
              label={`Stepped platforms, one per requirement group and at most eight, rising toward a flag. ${view.total} requirements sit on them: ${REQ_ORDER.map((s) => `${view.counts[s]} ${reqLabel(s).toLowerCase()}`).join(', ')}. Each tile stands for requirements of that status; large groups are sampled.`}
            />
          )}
        </div>
      </section>

      <div className="flex flex-wrap items-start gap-[22px]">
        <section aria-labelledby="wait-h" className="pk-card flex min-w-0 flex-[1_1_300px] flex-col gap-3 px-6 py-5">
          <div className="flex flex-col gap-1">
            <h2 id="wait-h" className="m-0 text-base font-semibold text-[var(--fm-ink)]">Waiting for you</h2>
            <p className={cn('m-0 text-[13px]', MUTED)}>The numbers match the agents on the Frameworks board.</p>
          </div>
          {view.waiting.length === 0 ? (
            <p className={cn('m-0 text-[13px]', MUTED)}>Nothing is waiting. Runs pause here when a step needs your input or approval.</p>
          ) : (
            <ol className="m-0 flex list-none flex-col gap-2.5 p-0">
              {view.waiting.map((w, i) => (
                <li key={w.run.id}>
                  <Link href={`/compliance/runs/${w.run.id}`} className="flex items-start gap-3 rounded-xl border border-[#ffd9c4] bg-[#fff7f2] p-3 no-underline">
                    <span className="inline-flex h-[22px] w-[22px] flex-none items-center justify-center rounded-full bg-[var(--fm-brand)] text-xs font-bold text-[var(--fm-ink)]">{i + 1}</span>
                    <span className="flex flex-col gap-0.5">
                      <b className="font-semibold text-[var(--fm-ink)]">{w.name}</b>
                      <span className={cn('text-[13px] leading-snug', MUTED)}>
                        {w.group}. {w.run.waitingFor === 'approval' ? 'Waiting for your approval.' : 'Waiting for you to record a step.'} Nothing changes until you answer.
                      </span>
                    </span>
                  </Link>
                </li>
              ))}
            </ol>
          )}
        </section>

        <section aria-labelledby="clause-h" className="pk-card min-w-0 flex-[2_1_480px] px-6 py-5">
          <div className="mb-1 flex flex-wrap items-baseline justify-between gap-2.5">
            <h2 id="clause-h" className="m-0 text-base font-semibold text-[var(--fm-ink)]">Workflows by clause</h2>
            <span className={cn('text-[12.5px]', MUTED)}>Stage as the catalogue names it, and the latest run</span>
          </div>
          {view.byGroup.length === 0 ? (
            <p className={cn('m-0 mt-2 text-[13px]', MUTED)}>No installed workflow covers this framework yet. Install a pack from the list below.</p>
          ) : (
            <ul className="m-0 list-none p-0">
              {view.byGroup.map((g) =>
                g.workflows.map((w, k) => (
                  <li key={`${g.name}-${w.id}`} className={cn('flex flex-wrap items-center gap-x-3.5 gap-y-1.5 py-2.5', 'border-t', LINE)}>
                    <span className={cn('w-[120px] flex-none text-[12.5px]', MUTED)}>{k === 0 ? g.name : ''}</span>
                    <Link href={`/compliance/workflows/${w.id}`} className="min-w-0 flex-[999_1_200px] font-semibold text-[var(--fm-ink)] hover:underline">
                      {w.name}
                    </Link>
                    <Pill>{cap(w.stage)}</Pill>
                    <StatusPill status={w.latestRun?.status ?? null} />
                  </li>
                )),
              )}
            </ul>
          )}
        </section>
      </div>

      <section aria-labelledby="steps-h" className="pk-card px-6 py-5">
        <div className="mb-3 flex flex-wrap items-baseline justify-between gap-2.5">
          <div className="flex flex-col gap-1">
            <h2 id="steps-h" className="m-0 text-base font-semibold text-[var(--fm-ink)]">How packs add up</h2>
            <p className={cn('m-0 text-[13px]', MUTED)}>In install order. Each bar shows coverage before the pack and what it adds.</p>
          </div>
          <span className={`text-[12.5px] ${MUTED}`}>
            {missing.length === 0 ? 'Every pack on this path is installed.' : `${j.steps.length - missing.length} of ${j.steps.length} installed`}
          </span>
        </div>
        {j.steps.length === 0 ? (
          <p className={`m-0 text-[13px] ${MUTED}`}>No pack adds coverage to this framework.</p>
        ) : (
          <ol className="m-0 list-none p-0">
            {j.steps.map((s, i) => {
              const before = s.cumulative - s.newlyCovered
              return (
                <li
                  key={s.pack}
                  className={cn('grid grid-cols-[24px_minmax(0,1fr)_auto] items-center gap-x-4 gap-y-2 border-t py-3 md:grid-cols-[24px_minmax(180px,1fr)_minmax(220px,1.4fr)_92px]', LINE)}
                >
                  <span className={`text-[12.5px] tabular-nums ${MUTED}`}>{i + 1}</span>
                  <div className="flex min-w-0 flex-col">
                    <Link href={`/compliance/packs/${s.pack}`} className="font-semibold leading-snug text-[var(--fm-ink)] hover:underline">
                      {s.name}
                    </Link>
                    <span className={`text-[12px] tabular-nums ${MUTED}`}>{s.newlyCovered > 0 ? `+${s.newlyCovered} newly covered` : 'No new requirements'}</span>
                  </div>
                  <div className="col-[2/-1] row-start-2 flex flex-col gap-1 md:col-[3/4] md:row-start-1">
                    <div
                      role="progressbar"
                      aria-label={`Coverage after ${s.name}`}
                      aria-valuemin={0}
                      aria-valuemax={j.active}
                      aria-valuenow={s.cumulative}
                      aria-valuetext={`${before} covered before this pack, ${s.cumulative} of ${j.active} once it is installed`}
                      className="relative h-2 w-full overflow-hidden rounded-full bg-[rgba(21,23,26,.06)]"
                    >
                      <div className="absolute inset-y-0 left-0 bg-[rgba(21,23,26,.18)]" style={{ width: `${pct(before, j.active)}%` }} />
                      <div
                        className={cn('absolute inset-y-0', s.installed ? 'bg-[#009869]' : 'bg-[#a9d6bf]')}
                        style={{ left: `${pct(before, j.active)}%`, width: `${pct(s.newlyCovered, j.active)}%` }}
                      />
                    </div>
                    <span className={`text-[12px] tabular-nums ${MUTED}`}>{s.cumulative} of {j.active} with this pack and the ones above</span>
                  </div>
                  <div className="col-start-3 row-start-1 flex justify-end md:col-start-4">
                    {s.installed ? (
                      <Pill tone="done">Installed</Pill>
                    ) : (
                      <button type="button" className={cn(BTN_P, 'h-9 px-4')} disabled={installer.busy !== null} onClick={() => installer.pack(s.pack)} aria-label={`Install ${s.name}`}>
                        {installer.busy === s.pack ? 'Installing' : 'Install'}
                      </button>
                    )}
                  </div>
                </li>
              )
            })}
          </ol>
        )}
      </section>

      <section aria-labelledby="reqs-h" className="flex flex-col gap-4">
        <div className="flex flex-wrap items-baseline justify-between gap-2.5">
          <h2 id="reqs-h" className="m-0 text-lg font-semibold text-[var(--fm-ink)]">Requirements</h2>
          <span aria-live="polite" className={cn('flex items-center gap-2 text-[13px]', MUTED)}>
            {filter ? (
              <>
                Showing {view.counts[filter]} {reqLabel(filter).toLowerCase()} of {view.total}
                <button type="button" onClick={() => setFilter(null)} className="font-semibold text-[var(--fm-ink)] underline">
                  Show all
                </button>
              </>
            ) : (
              `${view.total} requirements in ${view.groups.length} groups`
            )}
          </span>
        </div>
        {shown.map((g) => {
          const all = view.groups.find((x) => x.name === g.name)?.requirements ?? g.requirements
          const done = all.filter((r) => counts(r.status)).length
          return (
            <div key={g.name} className="pk-card px-6 py-5">
              <div className="mb-2 flex flex-wrap items-center justify-between gap-x-4 gap-y-2">
                <h3 className="m-0 text-base font-semibold text-[var(--fm-ink)]">{g.name}</h3>
                <div className="flex min-w-[200px] items-center gap-3">
                  <div aria-hidden className="h-1.5 w-24 overflow-hidden rounded-full bg-[rgba(21,23,26,.06)]">
                    <div className="h-full bg-[#009869]" style={{ width: `${pct(done, all.length)}%` }} />
                  </div>
                  <span className={`text-[12.5px] tabular-nums ${MUTED}`}>{done} of {all.length} covered</span>
                </div>
              </div>
              <div className="overflow-x-auto">
                <table className="w-full min-w-[640px] table-fixed border-collapse text-left text-[13px]">
                  <caption className="sr-only">{g.name} requirements</caption>
                  <colgroup>
                    <col className="w-[40%]" />
                    <col className="w-[116px]" />
                    <col />
                  </colgroup>
                  <thead>
                    <tr className={LABEL}>
                      <th scope="col" className="py-2 pr-3 font-semibold">Requirement</th>
                      <th scope="col" className="py-2 pr-3 font-semibold">Status</th>
                      <th scope="col" className="py-2 font-semibold">Covered or tested by</th>
                    </tr>
                  </thead>
                  <tbody>
                    {g.requirements.map((r) => (
                      <tr key={r.key} className={cn('border-t align-top', LINE)}>
                        <td className="py-[10px] pr-3 text-[var(--fm-ink)]">
                          <span className={cn('mr-1.5 font-mono text-xs', MUTED)}>{r.control}</span>
                          {r.title}
                        </td>
                        <td className="py-[10px] pr-3"><ReqPill status={r.status} /></td>
                        <td className="py-[10px]">
                          {r.workflows.length === 0 && r.evaluations.length === 0 ? (
                            <span className="text-[var(--fm-ink3)]">Nothing in the catalogue yet</span>
                          ) : (
                            <ul className="m-0 flex list-none flex-col gap-1.5 p-0">
                              {r.workflows.map((w) => (
                                <li key={`w${w.id}`} className="flex flex-wrap items-center gap-x-2 gap-y-1">
                                  <Link
                                    href={`/compliance/workflows/${w.id}`}
                                    className={cn('hover:underline', w.installed ? 'font-semibold text-[var(--fm-ink)]' : 'text-[var(--fm-ink2)]')}
                                  >
                                    {w.name}
                                  </Link>
                                  <Pill>{w.relation}</Pill>
                                  {!w.installed && <span className="text-[12px] text-[var(--fm-ink3)]">in {packName(w.pack)}, not installed</span>}
                                </li>
                              ))}
                              {r.evaluations.map((e) => (
                                <li key={`e${e.id}`} className="flex flex-wrap items-center gap-x-2 gap-y-1">
                                  <Link
                                    href={`/compliance/evaluations#${encodeURIComponent(e.id)}`}
                                    className={cn('hover:underline', e.installed ? 'font-semibold text-[var(--fm-ink)]' : 'text-[var(--fm-ink2)]')}
                                  >
                                    {e.name}
                                  </Link>
                                  {e.result ? <ResultPill status={e.result} /> : <EnginePill engine={e.engine} />}
                                  {!e.installed && <span className="text-[12px] text-[var(--fm-ink3)]">in {packName(e.pack)}, not installed</span>}
                                </li>
                              ))}
                            </ul>
                          )}
                        </td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            </div>
          )
        })}
      </section>
    </div>
  )
}
