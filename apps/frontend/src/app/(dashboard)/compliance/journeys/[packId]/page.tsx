'use client'

import Link from 'next/link'
import { useParams } from 'next/navigation'
import { useMemo } from 'react'
import { useJourney, useWaitingRuns } from '@/lib/api/hooks/usePacks'
import { IsoFigure } from '@/components/packs/IsoFigure'
import { journeyFigure } from '@/components/packs/figures'
import { BTN, BTN_P, Crumbs, ErrorNote, Heading, Loading, MUTED, Num, Pill, StatusPill } from '@/components/packs/parts'

const LEGEND: Array<{ label: string; cls: string }> = [
  { label: 'Done and sealed', cls: 'bg-[#a9d6bf]' },
  { label: 'Agent working', cls: 'border-[#3d4048] bg-[#3d4048] shadow-[inset_0_0_0_4px_#3d4048,inset_0_0_0_7px_#3ee0a1]' },
  { label: 'Agent paused for you', cls: 'bg-[#ff6b35]' },
  { label: 'Blocked', cls: 'bg-[#b0b3b9]' },
  { label: 'Queued', cls: 'border-dashed border-[#8a8f98] bg-white' },
]

export default function JourneyPage() {
  const { packId } = useParams<{ packId: string }>()
  const journey = useJourney(packId)
  const waiting = useWaitingRuns()

  const view = useMemo(() => {
    const clauses = journey.data?.clauses ?? []
    // Waiting workflows are numbered in clause order; the same numbers appear on the agents in the figure.
    const waitNo = new Map<string, number>()
    let n = 0
    for (const c of clauses) for (const w of c.workflows) if (w.latestRun?.status === 'waiting') waitNo.set(w.id, ++n)
    const flat = clauses.flatMap((c) => c.workflows.map((w) => ({ clause: c, w })))
    return {
      clauses,
      flat,
      waitNo,
      done: flat.filter((x) => x.w.latestRun?.status === 'done').length,
      figure: journeyFigure(
        clauses.map((c) => ({
          number: c.number,
          name: c.name,
          workflows: c.workflows.map((w) => ({ status: w.latestRun?.status ?? null, waitNo: waitNo.get(w.id) })),
        })),
      ),
    }
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
  const mine = new Set(view.flat.map((x) => x.w.id))
  const waitingRuns = (waiting.data ?? [])
    .filter((r) => mine.has(r.workflowId))
    .map((r) => ({ r, no: view.waitNo.get(r.workflowId), x: view.flat.find((f) => f.w.id === r.workflowId) }))
    .sort((a, b) => (a.no ?? 99) - (b.no ?? 99))

  return (
    <div className="flex flex-col gap-[22px]">
      <Crumbs items={[{ label: 'Frameworks', href: '/compliance' }, { label: j.name }]} />
      <Heading
        title={`${j.name} readiness`}
        lead={
          !j.installed
            ? 'This pack is not installed, so nothing here runs yet. Install it from Frameworks.'
            : `Agents are climbing clause by clause toward the audit. ${view.done} of ${view.flat.length} workflows are done; ${view.waitNo.size} ${view.waitNo.size === 1 ? 'is' : 'are'} waiting for you.`
        }
      >
        <button type="button" className={BTN} disabled title="Coming soon">Export audit pack (coming soon)</button>
        {waitingRuns[0] && (
          <Link href={`/compliance/runs/${waitingRuns[0].r.id}`} className={BTN_P}>
            Review {waitingRuns.length} {waitingRuns.length === 1 ? 'decision' : 'decisions'}
          </Link>
        )}
      </Heading>

      <section aria-label="Journey overview" className="pk-card flex flex-wrap items-stretch gap-[22px] p-[18px]">
        <div className="min-w-0 flex-[999_1_560px]">
          <IsoFigure
            className="p-2.5"
            figure={view.figure}
            label={`${view.clauses.length} stepped platforms, one per clause from ${view.clauses[0]?.number ?? ''} to ${view.clauses[view.clauses.length - 1]?.number ?? ''}, rising toward a flag. ${view.flat.length} workflows sit on them; ${view.done} are done and ${view.waitNo.size} wait for a person.`}
          />
        </div>
        <div className="flex flex-[1_1_280px] flex-col gap-[18px] px-1 py-1.5">
          <div className="flex flex-col gap-1">
            <h2 className="m-0 text-base font-semibold">Waiting for you</h2>
            <p className={`m-0 text-[13px] ${MUTED}`}>The numbers match the agents in the picture.</p>
          </div>
          {waiting.error && <ErrorNote message={`Decisions could not be loaded. ${waiting.error}`} onRetry={waiting.reload} />}
          {!waiting.error && !waiting.loading && waitingRuns.length === 0 && <p className={`m-0 text-[13px] ${MUTED}`}>Nothing is waiting for you.</p>}
          {waitingRuns.map(({ r, no, x }) => (
            <Link
              key={r.id}
              href={`/compliance/runs/${r.id}`}
              className="flex items-start gap-3 rounded-xl border border-[#ffd9c4] bg-[#fff7f2] p-3 no-underline"
            >
              {no !== undefined && <Num n={no} />}
              <span className="flex flex-col gap-[3px]">
                <b className="font-semibold">{r.workflowName}</b>
                <span className={`text-[13px] leading-snug ${MUTED}`}>
                  {x ? `Clause ${x.clause.number}. ` : ''}Nothing changes until you answer.
                </span>
              </span>
            </Link>
          ))}
          <ul className="m-0 mt-auto flex list-none flex-col gap-2 border-t border-[#15171a14] p-0 pt-1.5">
            {LEGEND.map((l) => (
              <li key={l.label} className="flex items-center gap-2.5 text-[13px]">
                <span aria-hidden className={`inline-block h-3.5 w-3.5 flex-none rounded border border-[#15171a1f] ${l.cls}`} />
                {l.label}
              </li>
            ))}
          </ul>
        </div>
      </section>

      <section aria-labelledby="by-clause" className="pk-card px-6 py-5">
        <div className="mb-1.5 flex flex-wrap items-baseline justify-between gap-2.5">
          <h2 id="by-clause" className="m-0 text-base font-semibold">Workflows by clause</h2>
          <span className={`text-[12.5px] ${MUTED}`}>Each runs in a lifecycle stage on the left</span>
        </div>
        <ul className="m-0 list-none p-0">
          {view.clauses.flatMap((c) =>
            c.workflows.length === 0
              ? [
                  <li key={`c${c.number}`} className="flex flex-wrap items-center gap-x-3.5 gap-y-2 border-t border-[#15171a14] py-3">
                    <span className={`w-[90px] text-[12.5px] ${MUTED}`}>Clause {c.number}</span>
                    <b className="flex-[999_1_220px] font-semibold">{c.name}</b>
                    <Pill>Coming soon</Pill>
                  </li>,
                ]
              : c.workflows.map((w) => (
                  <li key={w.id} className="flex flex-wrap items-center gap-x-3.5 gap-y-2 border-t border-[#15171a14] py-3">
                    <span className={`w-[90px] text-[12.5px] ${MUTED}`}>Clause {c.number}</span>
                    <Link href={`/compliance/workflows/${w.id}`} className="flex-[999_1_220px] font-semibold hover:underline">
                      {w.name}
                    </Link>
                    <Pill>{w.stage.charAt(0).toUpperCase() + w.stage.slice(1)}</Pill>
                    <StatusPill status={w.latestRun?.status} />
                  </li>
                )),
          )}
        </ul>
      </section>
    </div>
  )
}
