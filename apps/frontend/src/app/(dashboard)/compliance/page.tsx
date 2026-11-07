'use client'

import Link from 'next/link'
import { useMemo, useState } from 'react'
import {
  useBundles,
  useCatalogue,
  useInstaller,
  useJourneys,
  usePacks,
  type Bundle,
  type JourneySummary,
  type Pack,
} from '@/lib/api/hooks/usePacks'
import { IsoFigure } from '@/components/packs/IsoFigure'
import { packsFigure } from '@/components/packs/figures'
import { BTN, BTN_P, CoverageBar, Empty, ErrorNote, Heading, LABEL, Loading, MUTED, Pill, StatusPill, StagePill, cap } from '@/components/packs/parts'
import { cn } from '@/lib/utils'

type View = 'installed' | 'add' | 'packs' | 'workflows'
const VIEWS: Array<{ id: View; label: string }> = [
  { id: 'installed', label: 'Installed' },
  { id: 'add', label: 'Add a framework' },
  { id: 'packs', label: 'Packs' },
  { id: 'workflows', label: 'Workflows' },
]
/** The board has room for eight slots; plugged-in frameworks come first, then a few suggestions as empty slots. */
const BOARD_SLOTS = 8
const SUGGESTED_SLOTS = 2
/** Plugged-in cards shown before "Show all"; one pack serves many frameworks, so the full list can be long. */
const PLUGGED_SHOWN = 6

const plural = (n: number, one: string, many = `${one}s`) => `${n} ${n === 1 ? one : many}`
const pct = (n: number, total: number) => (total > 0 ? Math.min(100, (n / total) * 100) : 0)

function PackCard({ pack, pillarName, busy, onToggle }: { pack: Pack; pillarName?: string; busy: string | null; onToggle: (remove: boolean) => void }) {
  return (
    <article className="pk-card flex flex-col gap-2.5 p-5">
      <div className="flex flex-wrap items-center gap-2">
        {pack.installed && <Pill tone="done">Installed</Pill>}
        {pack.agentic && <Pill tone="you">Agentic</Pill>}
        {pillarName && <Pill>{pillarName}</Pill>}
      </div>
      <Link href={`/compliance/packs/${pack.id}`} className="text-[15px] font-semibold hover:underline">
        {pack.name}
      </Link>
      <p className={`m-0 flex-grow text-[13px] leading-normal ${MUTED}`}>{pack.description}</p>
      <p className={`m-0 text-[12.5px] ${MUTED}`}>
        {plural(pack.patterns.length, 'pattern')}, {plural(pack.workflowCount, 'workflow')}, {plural(pack.evaluationCount, 'evaluation')}
      </p>
      <div className="flex flex-wrap gap-2">
        <button
          type="button"
          className={pack.installed ? BTN : BTN_P}
          disabled={busy !== null}
          onClick={() => onToggle(pack.installed)}
          aria-label={`${pack.installed ? 'Remove' : 'Install'} ${pack.name}`}
        >
          {busy === pack.id ? (pack.installed ? 'Removing' : 'Installing') : pack.installed ? 'Remove' : 'Install'}
        </button>
        <Link href={`/compliance/packs/${pack.id}`} className={BTN} aria-label={`Open ${pack.name}`}>
          Open
        </Link>
      </div>
    </article>
  )
}

function BundleCard({ bundle, journeyKeys, busy, onInstall }: { bundle: Bundle; journeyKeys: Set<string>; busy: string | null; onInstall: () => void }) {
  const complete = bundle.installedCount >= bundle.packs.length
  return (
    <article className="pk-card flex flex-col gap-3 p-5">
      <div className="flex flex-col gap-1">
        <b className="text-[15px] font-semibold">{bundle.name}</b>
        <p className={`m-0 text-[13px] leading-normal ${MUTED}`}>{bundle.for}</p>
      </div>
      <p className="m-0 text-[13px]">
        <b className="font-semibold tabular-nums">
          {bundle.installedCount} of {bundle.packs.length}
        </b>{' '}
        packs installed
      </p>
      <ul className="m-0 flex list-none flex-col gap-2.5 p-0">
        {bundle.targets.map((t) => (
          <li key={t.key} className="flex flex-col gap-1">
            {journeyKeys.has(t.key) ? (
              <Link href={`/compliance/journeys/${t.key}`} className="text-[13px] font-semibold hover:underline">
                {t.name}
              </Link>
            ) : (
              <span className="text-[13px] font-semibold">{t.name}</span>
            )}
            <CoverageBar label={`${t.name} coverage`} installed={t.coveredInstalled} all={t.coveredAll} total={t.active} allLabel="with this bundle" />
          </li>
        ))}
      </ul>
      <button
        type="button"
        className={`${complete ? BTN : BTN_P} mt-auto self-start`}
        disabled={complete || busy !== null}
        onClick={onInstall}
        aria-label={`Install bundle ${bundle.name}`}
      >
        {complete ? 'Bundle installed' : busy === bundle.id ? 'Installing' : 'Install bundle'}
      </button>
    </article>
  )
}

/** One line on where a framework's installed workflows stand, from their latest runs. */
function workflowLine(j: JourneySummary): string {
  const n = (s: string) => j.workflows.filter((w) => w.status === s).length
  const parts = [
    n('done') && `${n('done')} done`,
    n('running') && `${n('running')} running`,
    n('waiting') && `${n('waiting')} waiting`,
    n('blocked') + n('failed') && `${n('blocked') + n('failed')} blocked`,
  ].filter(Boolean)
  const notRun = j.workflows.filter((w) => !w.status).length
  return `${plural(j.workflows.length, 'workflow')}${parts.length ? `: ${parts.join(', ')}` : ''}${notRun ? `${parts.length ? ',' : ':'} ${notRun} not run yet` : ''}.`
}

function PluggedCard({ j, primary }: { j: JourneySummary; primary: boolean }) {
  return (
    <div className="flex flex-col gap-2 rounded-xl border border-[var(--fm-line)] p-3.5">
      <div className="flex items-center justify-between gap-2">
        <b className="font-semibold">{j.name}</b>
        {j.waiting > 0 && <Pill tone="you" dot>{j.waiting} waiting</Pill>}
      </div>
      <span className={cn('text-[13px] leading-snug', MUTED)}>
        {j.coveredInstalled} of {j.active} requirements covered. {workflowLine(j)}
      </span>
      <div
        className="h-1.5 overflow-hidden rounded-full bg-[rgba(21,23,26,.08)]"
        role="img"
        aria-label={`${j.coveredInstalled} of ${j.active} requirements covered`}
      >
        <div className="h-full bg-[#009869]" style={{ width: `${pct(j.coveredInstalled, j.active)}%` }} />
      </div>
      <Link href={`/compliance/journeys/${j.key}`} className={cn(primary ? BTN_P : BTN, 'self-start')}>
        Open journey
      </Link>
    </div>
  )
}

export default function CompliancePage() {
  const catalogue = useCatalogue()
  const packs = usePacks()
  const bundles = useBundles()
  const journeys = useJourneys()
  const [view, setView] = useState<View>('installed')
  const [pillar, setPillar] = useState<string>('')
  const [allPlugged, setAllPlugged] = useState(false)
  const installer = useInstaller(() => {
    packs.reload()
    bundles.reload()
    journeys.reload()
  })

  const pillars = catalogue.data?.pillars ?? []
  const pillarName = (id: string) => pillars.find((p) => p.id === id)?.name ?? cap(id.toLowerCase())
  const allPacks = packs.data ?? []
  const allJourneys = journeys.data ?? []
  const installedCount = allPacks.filter((p) => p.installed).length
  const journeyKeys = useMemo(() => new Set(allJourneys.map((j) => j.key)), [allJourneys])

  const board = useMemo(() => {
    // Frameworks with runs waiting for you first, then the most covered.
    const plugged = allJourneys
      .filter((j) => j.coveredInstalled > 0)
      .sort((a, b) => b.waiting - a.waiting || pct(b.coveredInstalled, b.active) - pct(a.coveredInstalled, a.active))
    const open = allJourneys.filter((j) => j.coveredInstalled === 0).sort((a, b) => b.coveredAll - a.coveredAll)
    const shown = plugged.slice(0, BOARD_SLOTS - Math.min(SUGGESTED_SLOTS, open.length))
    const suggested = open.slice(0, BOARD_SLOTS - shown.length).slice(0, SUGGESTED_SLOTS)
    // A workflow serves several frameworks, so its waiting run keeps one number wherever it appears.
    const waitNo = new Map<string, number>()
    for (const j of shown) for (const w of j.workflows) if (w.status === 'waiting' && !waitNo.has(w.id)) waitNo.set(w.id, waitNo.size + 1)
    const figure = packsFigure([
      ...shown.map((j) => ({
        label: j.name,
        installed: true,
        workflows: j.workflows.slice(0, 12).map((w) => ({ status: w.status, waitNo: waitNo.get(w.id) })),
      })),
      ...suggested.map((j) => ({ label: j.name, installed: false, workflows: [] })),
    ])
    return { plugged, open, shown, suggested, figure }
  }, [allJourneys])

  const workflows = useMemo(() => {
    const byId = new Map<string, JourneySummary['workflows'][number] & { frameworks: string[] }>()
    for (const j of allJourneys) {
      for (const w of j.workflows) byId.set(w.id, { ...w, frameworks: [...(byId.get(w.id)?.frameworks ?? []), j.name] })
    }
    const order = { waiting: 0, running: 1, blocked: 2, failed: 2, queued: 3, done: 4 } as Record<string, number>
    return [...byId.values()].sort((a, b) => (order[a.status ?? ''] ?? 5) - (order[b.status ?? ''] ?? 5) || a.name.localeCompare(b.name))
  }, [allJourneys])

  if (packs.loading && !packs.data) return <Loading label="Loading frameworks" />
  if (packs.error && !packs.data) return <ErrorNote message={`Frameworks could not be loaded. ${packs.error}`} onRetry={packs.reload} />

  const shownPacks = pillar ? allPacks.filter((p) => p.pillar === pillar) : allPacks
  const figureLabel = `Your AI management system drawn as a board. ${board.shown.length} ${board.shown.length === 1 ? 'framework is' : 'frameworks are'} plugged in${
    board.shown.length ? `: ${board.shown.map((j) => j.name).join(', ')}` : ''
  }; their tops show one tile per workflow, coloured by its latest run, with agents above the ones that are running or waiting. ${board.suggested.length} empty ${
    board.suggested.length === 1 ? 'slot suggests a framework' : 'slots suggest frameworks'
  } to add.`

  return (
    <div className="flex flex-col gap-[22px]">
      <Heading
        title="Frameworks"
        lead={`${plural(installedCount, 'pack is', 'packs are')} installed. Agents run their workflows and file the evidence; you approve anything that would change a system.`}
      >
        <Link href="/compliance/evaluations" className={BTN}>Browse evaluations</Link>
      </Heading>

      {installer.failure && <ErrorNote message={installer.failure} />}
      {journeys.error && !journeys.data && <ErrorNote message={`Frameworks could not be loaded. ${journeys.error}`} onRetry={journeys.reload} />}

      <div role="tablist" aria-label="Frameworks views" className="flex w-max max-w-full gap-1 overflow-x-auto rounded-full bg-[#ebebe8] p-1">
        {VIEWS.map((v) => (
          <button
            key={v.id}
            type="button"
            role="tab"
            id={`tab-${v.id}`}
            aria-selected={view === v.id}
            aria-controls={`panel-${v.id}`}
            onClick={() => setView(v.id)}
            className={cn(
              'flex h-[34px] items-center whitespace-nowrap rounded-full px-4 text-[13px] font-semibold text-[var(--fm-ink2)]',
              view === v.id && 'bg-white text-[var(--fm-ink)] shadow-[0_1px_2px_rgba(20,20,30,.08)]',
            )}
          >
            {v.label}
          </button>
        ))}
      </div>

      {view === 'installed' && (
        <section id="panel-installed" role="tabpanel" aria-labelledby="tab-installed" className="pk-card flex flex-wrap items-stretch gap-[22px] p-[18px]">
          <div className="min-w-0 flex-[999_1_560px] rounded-xl bg-[#f7f6f3]">
            <IsoFigure figure={board.figure} label={figureLabel} className="p-2.5" />
          </div>
          <div className="flex flex-[1_1_280px] flex-col gap-3.5 px-1 py-1.5">
            <h2 className="m-0 text-base font-semibold">Plugged in</h2>
            {journeys.loading && !journeys.data ? (
              <Loading label="Loading frameworks" />
            ) : board.plugged.length === 0 ? (
              <>
                <p className={cn('m-0 text-[13px] leading-normal', MUTED)}>
                  No framework is plugged in yet. Adding one installs the packs whose workflows cover it.
                </p>
                <button type="button" className={cn(BTN_P, 'self-start')} onClick={() => setView('add')}>
                  Add a framework
                </button>
              </>
            ) : (
              <>
                {(allPlugged ? board.plugged : board.plugged.slice(0, PLUGGED_SHOWN)).map((j, i) => (
                  <PluggedCard key={j.key} j={j} primary={i === 0} />
                ))}
                {board.plugged.length > PLUGGED_SHOWN && (
                  <button type="button" className={cn(BTN, 'self-start')} onClick={() => setAllPlugged(!allPlugged)} aria-expanded={allPlugged}>
                    {allPlugged ? 'Show fewer' : `Show all ${board.plugged.length}`}
                  </button>
                )}
                <p className={cn('m-0 text-[13px]', MUTED)}>
                  {plural(board.open.length, 'framework')} not started.{' '}
                  <button type="button" onClick={() => setView('add')} className="font-semibold text-[var(--fm-ink)] underline">
                    Add a framework
                  </button>
                </p>
              </>
            )}
          </div>
        </section>
      )}

      {view === 'add' && (
        <div id="panel-add" role="tabpanel" aria-labelledby="tab-add" className="flex flex-col gap-[26px]">
          <section aria-labelledby="add-h" className="flex flex-col gap-3.5">
            <div className="flex flex-wrap items-baseline justify-between gap-2.5">
              <h2 id="add-h" className="m-0 text-lg font-semibold">Add a framework</h2>
              <span className={cn('text-[13px]', MUTED)}>Adding installs every pack that covers or tests it; its journey then shows how far you are.</span>
            </div>
            {journeys.loading && !journeys.data ? (
              <Loading label="Loading frameworks" />
            ) : allJourneys.length === 0 ? (
              <Empty>No frameworks have a journey yet.</Empty>
            ) : (
              <div className="grid grid-cols-[repeat(auto-fill,minmax(250px,1fr))] gap-4">
                {[...board.open, ...board.plugged].map((j) => {
                  const plugged = j.coveredInstalled > 0
                  const complete = j.contributingPacks.every((id) => allPacks.find((p) => p.id === id)?.installed)
                  return (
                    <article key={j.key} className="pk-card flex flex-col gap-2 p-5">
                      <span className={LABEL}>{pillarName(j.pillar)}</span>
                      <b className="text-[15px] font-semibold">{j.name}</b>
                      <p className={cn('m-0 flex-grow text-[13px] leading-normal', MUTED)}>
                        {[j.type, j.binding].filter(Boolean).map((x) => `${x}. `).join('')}
                        {plugged ? `${j.coveredInstalled} of ${j.active} requirements covered now; ` : ''}
                        {plural(j.contributingPacks.length, 'pack')} cover {j.coveredAll} of {j.active} requirements.
                      </p>
                      <div className="flex flex-wrap gap-2">
                        {!complete && (
                          <button
                            type="button"
                            className={BTN_P}
                            disabled={installer.busy !== null}
                            onClick={() => installer.framework(j.key)}
                            aria-label={`Add ${j.name}`}
                          >
                            {installer.busy === j.key ? 'Adding' : plugged ? 'Add the rest' : 'Add framework'}
                          </button>
                        )}
                        <Link href={`/compliance/journeys/${j.key}`} className={BTN} aria-label={`Open the ${j.name} journey`}>
                          {plugged ? 'Open journey' : 'Preview'}
                        </Link>
                      </div>
                    </article>
                  )
                })}
              </div>
            )}
          </section>

          <section aria-labelledby="bundles-h" className="flex flex-col gap-3.5">
            <div className="flex flex-wrap items-baseline justify-between gap-2.5">
              <h2 id="bundles-h" className="m-0 text-lg font-semibold">Or start from a kind of system</h2>
              <span className={cn('text-[13px]', MUTED)}>A bundle installs every pack that kind of system needs.</span>
            </div>
            {bundles.loading && !bundles.data ? (
              <Loading label="Loading bundles" />
            ) : bundles.error && !bundles.data ? (
              <ErrorNote message={`Bundles could not be loaded. ${bundles.error}`} onRetry={bundles.reload} />
            ) : (
              <div className="grid grid-cols-[repeat(auto-fill,minmax(300px,1fr))] gap-4">
                {(bundles.data ?? []).map((b) => (
                  <BundleCard key={b.id} bundle={b} journeyKeys={journeyKeys} busy={installer.busy} onInstall={() => installer.bundle(b.id)} />
                ))}
              </div>
            )}
          </section>
        </div>
      )}

      {view === 'packs' && (
        <section id="panel-packs" role="tabpanel" aria-labelledby="tab-packs" className="flex flex-col gap-3.5">
          <div className="flex flex-wrap items-center justify-between gap-3">
            <p className={cn('m-0 text-[13px]', MUTED)}>Packs are what you install: workflows and evaluations that each serve many frameworks.</p>
            <label className="flex items-center gap-2 text-[13px] font-semibold">
              Pillar
              <select value={pillar} onChange={(e) => setPillar(e.target.value)} className="h-10 rounded-full border border-[#15171a24] bg-white px-4 text-[13px] font-semibold">
                <option value="">All pillars</option>
                {pillars.map((p) => (
                  <option key={p.id} value={p.id}>{p.name}</option>
                ))}
              </select>
            </label>
          </div>
          {shownPacks.length === 0 ? (
            <Empty>No packs in this pillar.</Empty>
          ) : (
            <div className="grid grid-cols-[repeat(auto-fill,minmax(260px,1fr))] gap-4">
              {shownPacks.map((p) => (
                <PackCard key={p.id} pack={p} pillarName={pillarName(p.pillar)} busy={installer.busy} onToggle={(remove) => installer.pack(p.id, remove)} />
              ))}
            </div>
          )}
        </section>
      )}

      {view === 'workflows' && (
        <section id="panel-workflows" role="tabpanel" aria-labelledby="tab-workflows" className="pk-card px-6 py-5">
          <div className="mb-2 flex flex-wrap items-baseline justify-between gap-2.5">
            <h2 className="m-0 text-base font-semibold">Workflows of your installed packs</h2>
            <span className={cn('text-[12.5px]', MUTED)}>Waiting and running first. Stage is where it runs in the lifecycle.</span>
          </div>
          {workflows.length === 0 ? (
            <Empty>Install a pack or add a framework to get workflows.</Empty>
          ) : (
            <div className="overflow-x-auto">
              <table className="w-full min-w-[640px] border-collapse text-left text-[13px]">
                <thead>
                  <tr className={LABEL}>
                    <th scope="col" className="py-2 pr-3 font-semibold">Workflow</th>
                    <th scope="col" className="py-2 pr-3 font-semibold">Stage</th>
                    <th scope="col" className="py-2 pr-3 font-semibold">Latest run</th>
                    <th scope="col" className="py-2 font-semibold">Counts toward</th>
                  </tr>
                </thead>
                <tbody>
                  {workflows.map((w) => (
                    <tr key={w.id} className="border-t border-[var(--fm-line)] align-top">
                      <td className="py-2.5 pr-3">
                        <Link href={`/compliance/workflows/${w.id}`} className="font-semibold hover:underline">{w.name}</Link>
                      </td>
                      <td className="py-2.5 pr-3"><StagePill stage={w.stage} /></td>
                      <td className="py-2.5 pr-3"><StatusPill status={w.status} /></td>
                      <td className={cn('py-2.5 text-[12.5px]', MUTED)}>{w.frameworks.join(', ')}</td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          )}
        </section>
      )}

      <details className="pk-card px-[22px] py-[18px]">
        <summary className="cursor-pointer font-semibold">How packs, journeys and workflows fit together</summary>
        <div className={cn('mt-3 flex max-w-[70ch] flex-col gap-2 leading-relaxed', MUTED)}>
          <p className="m-0">
            A <b className="text-[var(--fm-ink)]">workflow</b> does one job end to end, such as reviewing who has access. Each of its steps collects, checks, suggests, asks you or files evidence.
          </p>
          <p className="m-0">
            A <b className="text-[var(--fm-ink)]">pack</b> is what you install: a set of workflows and evaluations. One pack serves many frameworks, so a run counts toward all of them.
          </p>
          <p className="m-0">
            A <b className="text-[var(--fm-ink)]">journey</b> shows one framework requirement by requirement: which installed workflows cover it and what is left. Adding a framework installs the packs it needs.
          </p>
        </div>
      </details>
    </div>
  )
}
