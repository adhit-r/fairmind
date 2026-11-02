'use client'

import Link from 'next/link'
import { useParams } from 'next/navigation'
import { useMemo } from 'react'
import { useInstaller, useJourney, usePackNames, type ReqStatus } from '@/lib/api/hooks/usePacks'
import { IsoFigure } from '@/components/packs/IsoFigure'
import { journeyFigure, type FigWorkflow } from '@/components/packs/figures'
import { BTN, BTN_P, CoverageBar, Crumbs, EnginePill, ErrorNote, Heading, Loading, MUTED, Pill, REQ_ORDER, ReqPill, reqHint, reqLabel } from '@/components/packs/parts'

const TILE: Record<ReqStatus, FigWorkflow['status']> = { covered: 'done', tested: 'tested', available: null, supported: 'supported', gap: 'gap' }
/** Swatches that match the tiles in the figure. */
const SWATCH: Record<ReqStatus, string> = {
  covered: 'bg-[#a9d6bf]',
  tested: 'bg-[#c4d7f1]',
  available: 'border-dashed border-[#8a8f98] bg-white',
  supported: 'bg-white',
  gap: 'bg-[#b0b3b9]',
}

export default function JourneyPage() {
  const { frameworkKey } = useParams<{ frameworkKey: string }>()
  const journey = useJourney(frameworkKey)
  const installer = useInstaller(journey.reload)
  const packName = usePackNames()

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
    return { groups, counts, figure, total: groups.reduce((n, g) => n + g.requirements.length, 0) }
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

  return (
    <div className="flex flex-col gap-[22px]">
      <Crumbs items={[{ label: 'Frameworks', href: '/compliance' }, { label: j.name }]} />
      <Heading
        title={`${j.name} readiness`}
        lead={`${j.coveredInstalled} of ${j.active} requirements are covered by the packs you have installed. Installing every pack in the catalogue would cover ${j.coveredAll}.`}
      >
        <Link href="/compliance/evaluations" className={BTN}>Browse evaluations</Link>
      </Heading>
      {meta.length > 0 && (
        <div className="-mt-3 flex flex-wrap gap-2">
          {meta.map((m) => (
            <Pill key={m}>{m}</Pill>
          ))}
        </div>
      )}
      {installer.failure && <ErrorNote message={installer.failure} />}

      <section aria-label="Journey overview" className="pk-card flex flex-wrap items-stretch gap-[22px] p-[18px]">
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
        <div className="flex flex-[1_1_280px] flex-col gap-[18px] px-1 py-1.5">
          <div className="flex flex-col gap-2">
            <h2 className="m-0 text-base font-semibold">Installed coverage</h2>
            <CoverageBar label={`${j.name} coverage`} installed={j.coveredInstalled} all={j.coveredAll} total={j.active} />
          </div>
          <ul className="m-0 mt-auto flex list-none flex-col gap-2 border-t border-[#15171a14] p-0 pt-3">
            {REQ_ORDER.map((s) => (
              <li key={s} className="flex items-center gap-2.5 text-[13px]" title={reqHint(s)}>
                <span aria-hidden className={`inline-block h-3.5 w-3.5 flex-none rounded border border-[#15171a1f] ${SWATCH[s]}`} />
                <span className="flex-grow">{reqLabel(s)}</span>
                <span className="tabular-nums">{view.counts[s]}</span>
              </li>
            ))}
          </ul>
        </div>
      </section>

      <section aria-labelledby="steps-h" className="pk-card px-6 py-5">
        <div className="mb-1.5 flex flex-wrap items-baseline justify-between gap-2.5">
          <h2 id="steps-h" className="m-0 text-base font-semibold">How packs add up</h2>
          <span className={`text-[12.5px] ${MUTED}`}>
            {missing.length === 0 ? 'Every pack on this path is installed.' : `${missing.length} ${missing.length === 1 ? 'pack is' : 'packs are'} not installed.`}
          </span>
        </div>
        {j.steps.length === 0 ? (
          <p className={`m-0 text-[13px] ${MUTED}`}>No pack adds coverage to this framework.</p>
        ) : (
          <ol className="m-0 list-none p-0">
            {j.steps.map((s, i) => (
              <li key={s.pack} className="flex flex-wrap items-center gap-x-4 gap-y-2 border-t border-[#15171a14] py-3">
                <span className={`w-6 text-[12.5px] tabular-nums ${MUTED}`}>{i + 1}</span>
                <Link href={`/compliance/packs/${s.pack}`} className="min-w-[180px] flex-[1_1_220px] font-semibold hover:underline">
                  {s.name}
                </Link>
                <span className={`text-[12.5px] tabular-nums ${MUTED}`}>{s.newlyCovered > 0 ? `+${s.newlyCovered} newly covered` : 'No new requirements'}</span>
                <div className="min-w-[160px] flex-[1_1_200px]">
                  <div
                    role="progressbar"
                    aria-label={`Coverage after ${s.name}`}
                    aria-valuemin={0}
                    aria-valuemax={j.active}
                    aria-valuenow={s.cumulative}
                    aria-valuetext={`${s.cumulative} of ${j.active} requirements covered once this pack and the ones before it are installed`}
                    className="h-2 w-full overflow-hidden rounded-full bg-[#eceef1]"
                  >
                    <div className="h-full bg-[#009869]" style={{ width: `${j.active > 0 ? Math.min(100, Math.round((s.cumulative / j.active) * 100)) : 0}%` }} />
                  </div>
                  <span className={`text-[12px] tabular-nums ${MUTED}`}>{s.cumulative} of {j.active} with this pack and the ones above</span>
                </div>
                {s.installed ? (
                  <Pill tone="done">Installed</Pill>
                ) : (
                  <button type="button" className={BTN_P} disabled={installer.busy !== null} onClick={() => installer.pack(s.pack)} aria-label={`Install ${s.name}`}>
                    {installer.busy === s.pack ? 'Installing' : 'Install'}
                  </button>
                )}
              </li>
            ))}
          </ol>
        )}
      </section>

      <section aria-labelledby="reqs-h" className="flex flex-col gap-4">
        <h2 id="reqs-h" className="m-0 text-lg font-semibold">Requirements</h2>
        {view.groups.map((g) => (
          <div key={g.name} className="pk-card px-6 py-5">
            <div className="overflow-x-auto">
              <table className="w-full border-collapse text-left text-[13px]">
                <caption className="mb-1.5 text-left text-base font-semibold">{g.name}</caption>
                <thead>
                  <tr className={`text-[12px] ${MUTED}`}>
                    <th scope="col" className="py-2 pr-3 font-semibold">Requirement</th>
                    <th scope="col" className="py-2 pr-3 font-semibold">Status</th>
                    <th scope="col" className="py-2 font-semibold">Covered or tested by</th>
                  </tr>
                </thead>
                <tbody>
                  {g.requirements.map((r) => (
                    <tr key={r.key} className="border-t border-[#15171a14] align-top">
                      <td className="min-w-[220px] py-[10px] pr-3">
                        <span className="font-mono text-xs">{r.control}</span> <span>{r.title}</span>
                      </td>
                      <td className="py-[10px] pr-3"><ReqPill status={r.status} /></td>
                      <td className="min-w-[260px] py-[10px]">
                        {r.workflows.length === 0 && r.evaluations.length === 0 ? (
                          <span className={MUTED}>Nothing yet</span>
                        ) : (
                          <ul className="m-0 flex list-none flex-col gap-1.5 p-0">
                            {r.workflows.map((w) => (
                              <li key={`w${w.id}`} className="flex flex-wrap items-center gap-x-2 gap-y-1">
                                <Link href={`/compliance/workflows/${w.id}`} className="font-semibold hover:underline">{w.name}</Link>
                                <Pill>{w.relation}</Pill>
                                {!w.installed && <span className={`text-[12px] ${MUTED}`}>in {packName(w.pack)}, not installed</span>}
                              </li>
                            ))}
                            {r.evaluations.map((e) => (
                              <li key={`e${e.id}`} className="flex flex-wrap items-center gap-x-2 gap-y-1">
                                <Link href={`/compliance/evaluations#${encodeURIComponent(e.id)}`} className="font-semibold hover:underline">{e.name}</Link>
                                <EnginePill engine={e.engine} />
                                {!e.installed && <span className={`text-[12px] ${MUTED}`}>in {packName(e.pack)}, not installed</span>}
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
        ))}
      </section>
    </div>
  )
}
