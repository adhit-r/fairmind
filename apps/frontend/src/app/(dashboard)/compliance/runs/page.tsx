'use client'

import Link from 'next/link'
import { useState } from 'react'
import { useRuns } from '@/lib/api/hooks/usePacks'
import { Crumbs, Empty, ErrorNote, Heading, LABEL, Loading, MUTED, Pill, StatusPill, when } from '@/components/packs/parts'
import { cn } from '@/lib/utils'

/** Every workflow run of the organisation; the Decision station in the lifecycle opens it on the runs waiting for a person. */
export default function RunsPage() {
  const runs = useRuns()
  const [all, setAll] = useState(false)

  if (runs.loading && !runs.data) return <Loading label="Loading runs" />
  if (runs.error && !runs.data) {
    return (
      <div className="flex flex-col gap-4">
        <Crumbs items={[{ label: 'Frameworks', href: '/compliance' }, { label: 'Runs' }]} />
        <ErrorNote message={`Runs could not be loaded. ${runs.error}`} onRetry={runs.reload} />
      </div>
    )
  }

  const every = runs.data ?? []
  const waiting = every.filter((r) => r.status === 'waiting')
  const shown = all ? every : waiting

  return (
    <div className="flex flex-col gap-[22px]">
      <Crumbs items={[{ label: 'Frameworks', href: '/compliance' }, { label: 'Runs' }]} />
      <Heading
        title="Decisions"
        lead={
          waiting.length
            ? `${waiting.length} ${waiting.length === 1 ? 'run is' : 'runs are'} waiting for you: a step to record or a change to approve. Nothing changes until you answer.`
            : 'No run is waiting for you. Runs pause here when a step needs your input or approval.'
        }
      />
      <section aria-labelledby="runs-h" className="pk-card px-6 py-5">
        <div className="mb-2 flex flex-wrap items-center justify-between gap-2.5">
          <h2 id="runs-h" className="m-0 text-base font-semibold">{all ? 'All runs' : 'Waiting for you'}</h2>
          <label className="flex items-center gap-2 text-[13px] font-semibold">
            <input type="checkbox" checked={all} onChange={(e) => setAll(e.target.checked)} className="h-[18px] w-[18px] accent-[#15171a]" />
            Show every run
          </label>
        </div>
        {shown.length === 0 ? (
          <Empty>{all ? 'No workflow has run yet. Start one from a workflow page.' : 'Nothing is waiting for you.'}</Empty>
        ) : (
          <div className="overflow-x-auto">
            <table className="w-full min-w-[620px] border-collapse text-left text-[13px]">
              <thead>
                <tr className={LABEL}>
                  <th scope="col" className="py-2 pr-3 font-semibold">Workflow</th>
                  <th scope="col" className="py-2 pr-3 font-semibold">Status</th>
                  <th scope="col" className="py-2 pr-3 font-semibold">Needs</th>
                  <th scope="col" className="py-2 font-semibold">Updated</th>
                </tr>
              </thead>
              <tbody>
                {shown.map((r) => (
                  <tr key={r.id} className="border-t border-[var(--fm-line)]">
                    <td className="py-2.5 pr-3">
                      <Link href={`/compliance/runs/${r.id}`} className="font-semibold hover:underline">{r.workflowName}</Link>
                    </td>
                    <td className="py-2.5 pr-3"><StatusPill status={r.status} /></td>
                    <td className="py-2.5 pr-3">
                      {r.waitingFor === 'approval' ? <Pill tone="you">Your approval</Pill> : r.waitingFor === 'input' ? <Pill tone="you">A step recorded</Pill> : <span className={MUTED}>Nothing</span>}
                    </td>
                    <td className={cn('whitespace-nowrap py-2.5', MUTED)}>{when(r.updatedAt)}</td>
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
