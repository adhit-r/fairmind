'use client'

import Link from 'next/link'
import { useEffect, useMemo, useState } from 'react'
import { useCatalogue, useEvaluations, type EngineStatus } from '@/lib/api/hooks/usePacks'
import { Crumbs, EnginePill, Empty, ErrorNote, Heading, Loading, MUTED, Pill, cap } from '@/components/packs/parts'

const ENGINES: Array<{ value: EngineStatus; label: string }> = [
  { value: 'Engine exists', label: 'Engine exists' },
  { value: 'Partial', label: 'Partial' },
  { value: 'Not found', label: 'Not built yet' },
]
const FIELD = 'h-10 rounded-full border border-[#15171a24] bg-white px-4 text-[13px] font-semibold'

export default function EvaluationsPage() {
  const evals = useEvaluations()
  const catalogue = useCatalogue()
  const [q, setQ] = useState('')
  const [pillar, setPillar] = useState('')
  const [engine, setEngine] = useState('')
  const [installedOnly, setInstalledOnly] = useState(false)

  const rows = useMemo(() => {
    const needle = q.trim().toLowerCase()
    return (evals.data ?? []).filter(
      (e) =>
        (!pillar || e.pillar === pillar) &&
        (!engine || e.engine === engine) &&
        (!installedOnly || e.installed) &&
        (!needle || [e.name, e.measures, e.metric, e.appliesTo, e.id].some((t) => t?.toLowerCase().includes(needle))),
    )
  }, [evals.data, q, pillar, engine, installedOnly])

  // A pack page links here with the evaluation id in the hash; scroll to it once the table exists.
  useEffect(() => {
    if (!evals.data || typeof window === 'undefined' || !window.location.hash) return
    document.getElementById(decodeURIComponent(window.location.hash.slice(1)))?.scrollIntoView({ block: 'center' })
  }, [evals.data])

  if (evals.loading && !evals.data) return <Loading label="Loading evaluations" />
  if (evals.error && !evals.data) {
    return (
      <div className="flex flex-col gap-4">
        <Crumbs items={[{ label: 'Frameworks', href: '/compliance' }, { label: 'Evaluations' }]} />
        <ErrorNote message={`Evaluations could not be loaded. ${evals.error}`} onRetry={evals.reload} />
      </div>
    )
  }

  const all = evals.data ?? []
  const built = all.filter((e) => e.engine === 'Engine exists').length

  return (
    <div className="flex flex-col gap-[22px]">
      <Crumbs items={[{ label: 'Frameworks', href: '/compliance' }, { label: 'Evaluations' }]} />
      <Heading
        title="Evaluations"
        lead={`${all.length} evaluations measure how your AI systems behave. ${built} have an engine that runs today; the rest are partly built or not built yet.`}
      />

      <section aria-label="Filters" className="pk-card flex flex-wrap items-center gap-3 px-5 py-4">
        <label className="flex min-w-[220px] flex-[1_1_260px] flex-col gap-1 text-[12.5px] font-semibold">
          Search
          <input
            type="search"
            value={q}
            onChange={(e) => setQ(e.target.value)}
            placeholder="Name, metric or what it applies to"
            className={`${FIELD} w-full font-normal`}
          />
        </label>
        <label className="flex flex-col gap-1 text-[12.5px] font-semibold">
          Pillar
          <select value={pillar} onChange={(e) => setPillar(e.target.value)} className={FIELD}>
            <option value="">All pillars</option>
            {(catalogue.data?.pillars ?? []).map((p) => (
              <option key={p.id} value={p.id}>{p.name}</option>
            ))}
          </select>
        </label>
        <label className="flex flex-col gap-1 text-[12.5px] font-semibold">
          Engine
          <select value={engine} onChange={(e) => setEngine(e.target.value)} className={FIELD}>
            <option value="">Any engine status</option>
            {ENGINES.map((e) => (
              <option key={e.value} value={e.value}>{e.label}</option>
            ))}
          </select>
        </label>
        <label className="flex items-center gap-2 self-end pb-2.5 text-[13px] font-semibold">
          <input type="checkbox" checked={installedOnly} onChange={(e) => setInstalledOnly(e.target.checked)} className="h-[18px] w-[18px] accent-[#15171a]" />
          Installed packs only
        </label>
      </section>

      <section aria-labelledby="eval-h" className="pk-card px-6 py-5">
        <div className="mb-2 flex flex-wrap items-baseline justify-between gap-2.5">
          <h2 id="eval-h" className="m-0 text-base font-semibold">
            {rows.length} of {all.length} shown
          </h2>
          {evals.error && <ErrorNote message={evals.error} onRetry={evals.reload} />}
        </div>
        {rows.length === 0 ? (
          <Empty>{all.length === 0 ? 'The catalogue has no evaluations.' : 'No evaluation matches these filters.'}</Empty>
        ) : (
          <div className="overflow-x-auto">
            <table className="w-full border-collapse text-left text-[13px]">
              <thead>
                <tr className={`text-[12px] ${MUTED}`}>
                  <th scope="col" className="py-2 pr-3 font-semibold">Evaluation</th>
                  <th scope="col" className="py-2 pr-3 font-semibold">Metric</th>
                  <th scope="col" className="py-2 pr-3 font-semibold">Default threshold</th>
                  <th scope="col" className="py-2 pr-3 font-semibold">Engine</th>
                  <th scope="col" className="py-2 pr-3 font-semibold">Pattern and pack</th>
                  <th scope="col" className="py-2 font-semibold">Requirements tested</th>
                </tr>
              </thead>
              <tbody>
                {rows.map((e) => (
                  <tr key={e.id} id={e.id} className="scroll-mt-24 border-t border-[#15171a14] align-top">
                    <td className="max-w-[300px] py-[10px] pr-3">
                      <b className="font-semibold">{e.name}</b>
                      <div className={`mt-0.5 text-[12.5px] leading-snug ${MUTED}`}>{e.measures}</div>
                      <div className="mt-1 flex flex-wrap gap-1.5">
                        <Pill>{cap((catalogue.data?.pillars.find((p) => p.id === e.pillar)?.name ?? e.pillar.toLowerCase()))}</Pill>
                        {!e.installed && <Pill>Pack not installed</Pill>}
                      </div>
                    </td>
                    <td className="max-w-[200px] py-[10px] pr-3">{e.metric}</td>
                    <td className="max-w-[200px] py-[10px] pr-3">{e.threshold}</td>
                    <td className="py-[10px] pr-3">
                      <EnginePill engine={e.engine} />
                      {e.codeLocation && <div className="mt-1 break-all font-mono text-[11px]">{e.codeLocation}</div>}
                    </td>
                    <td className="max-w-[220px] py-[10px] pr-3">
                      <div>{e.pattern.name}</div>
                      <Link href={`/compliance/packs/${e.pack.id}`} className="text-[12.5px] font-semibold hover:underline">
                        {e.pack.name}
                      </Link>
                    </td>
                    <td className="min-w-[200px] py-[10px]">
                      {e.tests.length === 0 ? (
                        <span className={MUTED}>None</span>
                      ) : (
                        <details>
                          <summary className="cursor-pointer font-semibold">{e.tests.length} {e.tests.length === 1 ? 'requirement' : 'requirements'}</summary>
                          <ul className="m-0 mt-1.5 flex list-none flex-col gap-1.5 p-0">
                            {e.tests.map((t) => (
                              <li key={t.key} className="text-[12.5px] leading-snug">
                                <span className="font-mono text-[11.5px]">{t.framework} {t.control}</span> {t.title}
                              </li>
                            ))}
                          </ul>
                        </details>
                      )}
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        )}
      </section>
    </div>
  )
}
