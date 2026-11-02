'use client'

import Link from 'next/link'
import { useParams } from 'next/navigation'
import { useCatalogue, useInstaller, usePackDetail } from '@/lib/api/hooks/usePacks'
import { BTN, BTN_P, Crumbs, EnginePill, ErrorNote, Heading, Loading, MUTED, Pill, StatusPill, cap } from '@/components/packs/parts'

const plural = (n: number, one: string, many = `${one}s`) => `${n} ${n === 1 ? one : many}`

export default function PackPage() {
  const { packId } = useParams<{ packId: string }>()
  const pack = usePackDetail(packId)
  const catalogue = useCatalogue()
  const installer = useInstaller(pack.reload)

  if (pack.loading && !pack.data) return <Loading label="Loading pack" />
  if (pack.error || !pack.data) {
    return (
      <div className="flex flex-col gap-4">
        <Crumbs items={[{ label: 'Frameworks', href: '/compliance' }, { label: 'Pack' }]} />
        <ErrorNote message={`This pack could not be loaded. ${pack.error ?? ''}`} onRetry={pack.reload} />
      </div>
    )
  }

  const p = pack.data
  const pillar = catalogue.data?.pillars.find((x) => x.id === p.pillar)?.name ?? cap(p.pillar.toLowerCase())
  const busy = installer.busy === p.id

  return (
    <div className="flex flex-col gap-[22px]">
      <Crumbs items={[{ label: 'Frameworks', href: '/compliance' }, { label: pillar, href: '/compliance' }, { label: p.name }]} />
      <Heading title={p.name} lead={p.description}>
        <button
          type="button"
          className={p.installed ? BTN : BTN_P}
          disabled={installer.busy !== null}
          onClick={() => installer.pack(p.id, p.installed)}
          aria-label={`${p.installed ? 'Remove' : 'Install'} ${p.name}`}
        >
          {busy ? (p.installed ? 'Removing' : 'Installing') : p.installed ? 'Remove' : 'Install'}
        </button>
      </Heading>
      <div className="-mt-3 flex flex-wrap items-center gap-2">
        <Pill tone={p.installed ? 'done' : 'plain'}>{p.installed ? 'Installed' : 'Not installed'}</Pill>
        <Pill>{pillar}</Pill>
        {p.agentic && <Pill tone="you">Agentic</Pill>}
        <Pill>{plural(p.patterns.length, 'pattern')}</Pill>
        <Pill>{plural(p.workflowCount, 'workflow')}</Pill>
        <Pill>{plural(p.evaluationCount, 'evaluation')}</Pill>
        <Pill>{plural(p.requirementsTouched, 'requirement')} touched</Pill>
      </div>
      {installer.failure && <ErrorNote message={installer.failure} />}
      {!p.installed && (
        <p className={`m-0 text-[13px] ${MUTED}`}>Workflows in this pack cannot start a run until it is installed.</p>
      )}

      <div className="flex flex-wrap items-start gap-5">
        <section aria-labelledby="patterns-h" className="flex min-w-0 flex-[3_1_480px] flex-col gap-4">
          <h2 id="patterns-h" className="m-0 text-lg font-semibold">Patterns</h2>
          {p.patterns.length === 0 ? (
            <p className={`pk-card m-0 px-6 py-5 text-[13px] ${MUTED}`}>This pack has no patterns.</p>
          ) : (
            p.patterns.map((pt) => (
              <article key={pt.id} className="pk-card flex flex-col gap-3 px-6 py-5">
                <div className="flex flex-col gap-1">
                  <div className="flex flex-wrap items-center gap-2">
                    <h3 className="m-0 text-base font-semibold">{pt.name}</h3>
                    {pt.agentic && <Pill tone="you">Agentic</Pill>}
                  </div>
                  <p className={`m-0 text-[13px] leading-normal ${MUTED}`}>{pt.objective}</p>
                </div>
                <div className="flex flex-col">
                  <h4 className={`m-0 mb-1 text-[12px] font-semibold uppercase tracking-[0.06em] ${MUTED}`}>Workflows</h4>
                  {pt.workflows.length === 0 ? (
                    <p className={`m-0 border-t border-[#15171a14] py-2.5 text-[13px] ${MUTED}`}>No workflows in this pattern.</p>
                  ) : (
                    <ul className="m-0 list-none p-0">
                      {pt.workflows.map((w) => (
                        <li key={w.id} className="flex flex-wrap items-center gap-x-3 gap-y-1.5 border-t border-[#15171a14] py-2.5">
                          <Link href={`/compliance/workflows/${w.id}`} className="min-w-[180px] flex-[1_1_220px] text-[13.5px] font-semibold hover:underline">
                            {w.name}
                          </Link>
                          <span title={w.autonomy}><Pill>Autonomy {w.autonomy.split(/\s/)[0]}</Pill></span>
                          <Pill>{cap(w.stage)}</Pill>
                          <StatusPill status={w.latestRun?.status} />
                        </li>
                      ))}
                    </ul>
                  )}
                </div>
                <div className="flex flex-col">
                  <h4 className={`m-0 mb-1 text-[12px] font-semibold uppercase tracking-[0.06em] ${MUTED}`}>Evaluations</h4>
                  {pt.evaluations.length === 0 ? (
                    <p className={`m-0 border-t border-[#15171a14] py-2.5 text-[13px] ${MUTED}`}>No evaluations in this pattern.</p>
                  ) : (
                    <ul className="m-0 list-none p-0">
                      {pt.evaluations.map((e) => (
                        <li key={e.id} className="flex flex-wrap items-center gap-x-3 gap-y-1.5 border-t border-[#15171a14] py-2.5">
                          <Link href={`/compliance/evaluations#${encodeURIComponent(e.id)}`} className="min-w-[180px] flex-[1_1_220px] text-[13.5px] font-semibold hover:underline">
                            {e.name}
                          </Link>
                          <EnginePill engine={e.engine} />
                        </li>
                      ))}
                    </ul>
                  )}
                </div>
              </article>
            ))
          )}
        </section>

        <section aria-labelledby="fw-h" className="pk-card min-w-0 flex-[1_1_300px] px-[22px] py-5">
          <h2 id="fw-h" className="m-0 mb-1 text-base font-semibold">Frameworks this pack touches</h2>
          <p className={`m-0 mb-2 text-[13px] ${MUTED}`}>Requirements it covers or tests, out of those it touches.</p>
          {p.frameworks.length === 0 ? (
            <p className={`m-0 text-[13px] ${MUTED}`}>This pack is not mapped to any framework.</p>
          ) : (
            <ul className="m-0 list-none p-0">
              {p.frameworks.map((f) => (
                <li key={f.key} className="flex items-center justify-between gap-2.5 border-t border-[#15171a14] py-[9px] text-[13px]">
                  <Link href={`/compliance/journeys/${f.key}`} className="font-semibold hover:underline">
                    {f.name}
                  </Link>
                  <span className="tabular-nums">
                    {f.covered} of {f.touched}
                  </span>
                </li>
              ))}
            </ul>
          )}
        </section>
      </div>
    </div>
  )
}
