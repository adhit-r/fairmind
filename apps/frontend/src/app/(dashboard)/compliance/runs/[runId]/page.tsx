'use client'

import { useParams } from 'next/navigation'
import { useMemo, useState } from 'react'
import { usePackActions, useRun, useWaitingRuns, useWorkflow } from '@/lib/api/hooks/usePacks'
import { IsoFigure } from '@/components/packs/IsoFigure'
import { runFigure } from '@/components/packs/figures'
import { BTN, BTN_P, Crumbs, ErrorNote, Heading, Loading, MUTED, Num, Pill, StatusPill, when } from '@/components/packs/parts'

export default function RunPage() {
  const { runId } = useParams<{ runId: string }>()
  const run = useRun(runId)
  const { decideRun } = usePackActions()
  const workflow = useWorkflow(run.data?.workflowId)
  const waiting = useWaitingRuns()
  const [notes, setNotes] = useState('')
  const [deciding, setDeciding] = useState<'approve' | 'reject' | null>(null)
  const [failure, setFailure] = useState<string | null>(null)

  const view = useMemo(() => {
    const r = run.data
    const steps = workflow.data?.steps ?? []
    if (!r) return null
    const completed = new Set(r.events.filter((e) => e.kind === 'step.completed' && e.stepId).map((e) => e.stepId))
    const askIds = new Set(steps.filter((s) => s.kind === 'ask').map((s) => s.id))
    const reachedAsk = r.status === 'waiting' || r.events.some((e) => e.stepId !== null && askIds.has(e.stepId))
    const approved = r.approval?.status.toLowerCase().startsWith('approv') ?? false
    const rank = (waiting.data ?? []).findIndex((x) => x.id === r.id) + 1
    const waitNo = rank || 1
    return {
      waitNo,
      figure: runFigure({
        systems: [...new Set(steps.filter((s) => s.kind === 'collect').flatMap((s) => s.systems))],
        steps: steps.map((s) => ({ status: completed.has(s.id) ? 'done' : r.currentStep === s.id ? 'current' : 'next' })),
        gate: !reachedAsk ? 'none' : approved ? 'open' : 'closed',
        waitNo,
        agent: r.status === 'waiting' ? 'need' : r.status === 'blocked' ? 'held' : 'idle',
        sealed: r.events.filter((e) => e.kind === 'evidence.sealed').length,
      }),
      sealed: r.events.filter((e) => e.kind === 'evidence.sealed').length,
      stepNo: steps.findIndex((s) => s.id === r.currentStep) + 1,
      titleOf: (id: string | null) => (id ? steps.find((s) => s.id === id)?.title ?? id : ''),
    }
  }, [run.data, workflow.data, waiting.data])

  async function decide(decision: 'approve' | 'reject') {
    setDeciding(decision)
    setFailure(null)
    const res = await decideRun(runId, decision, notes.trim() || undefined)
    setDeciding(null)
    if (res.error) setFailure(res.error)
    else setNotes('')
    run.reload()
    waiting.reload()
  }

  if (run.loading && !run.data) return <Loading label="Loading run" />
  if (run.error || !run.data || !view) {
    return (
      <div className="flex flex-col gap-4">
        <Crumbs items={[{ label: 'Frameworks', href: '/compliance' }, { label: 'Run' }]} />
        <ErrorNote message={`This run could not be loaded. ${run.error ?? ''}`} onRetry={run.reload} />
      </div>
    )
  }

  const r = run.data
  const isWaiting = r.status === 'waiting'
  const stage = workflow.data ? workflow.data.stage.charAt(0).toUpperCase() + workflow.data.stage.slice(1) : null
  const stepsTotal = workflow.data?.steps.length ?? 0

  return (
    <div className="flex flex-col gap-[22px]">
      <Crumbs items={[{ label: 'Frameworks', href: '/compliance' }, { label: r.workflowName, href: `/compliance/workflows/${r.workflowId}` }, { label: 'Run' }]} />
      <div className="flex max-w-[760px] flex-col gap-2">
        <div className="flex flex-wrap gap-2">
          <StatusPill status={r.status} />
          {isWaiting && view.stepNo > 0 && <Pill tone="you">At step {view.stepNo} of {stepsTotal}</Pill>}
          {stage && <Pill>{stage}</Pill>}
        </div>
        <Heading
          title={r.workflowName}
          lead={`Started ${when(r.createdAt)}. ${r.events.length} ${r.events.length === 1 ? 'event is' : 'events are'} on the ledger${view.sealed ? `, ${view.sealed} sealed as evidence` : ''}.`}
        />
      </div>
      {workflow.error && <ErrorNote message={`The workflow steps could not be loaded, so the picture is incomplete. ${workflow.error}`} onRetry={workflow.reload} />}

      <section aria-label="Run overview" className="pk-card flex flex-wrap items-stretch gap-[22px] p-[18px]">
        <div className="min-w-0 flex-[999_1_560px]">
          <IsoFigure
            className="p-2.5"
            figure={view.figure}
            label={`The agent for ${r.workflowName}. ${stepsTotal} step tiles show progress; status is ${r.status}. ${view.sealed} evidence records are sealed on the ledger.${isWaiting ? ' A gate is closed and the agent waits for your decision.' : ''}`}
          />
        </div>
        <div className="flex flex-[1_1_300px] flex-col gap-3.5 px-1 py-1.5">
          <div className="flex items-center gap-2.5">
            {isWaiting && <Num n={view.waitNo} />}
            <h2 className="m-0 text-base font-semibold">Your decision</h2>
          </div>
          {isWaiting ? (
            <>
              <p className="m-0 leading-normal">
                The agent is holding at {view.titleOf(r.currentStep) ? <b className="font-semibold">{view.titleOf(r.currentStep)}</b> : 'the gate'}. Nothing in your systems changes until you decide.
              </p>
              <div className="flex flex-col gap-1.5">
                <label htmlFor="notes" className="text-[13px] font-semibold">Notes (optional)</label>
                <textarea
                  id="notes"
                  value={notes}
                  onChange={(e) => setNotes(e.target.value)}
                  rows={3}
                  className="resize-y rounded-[10px] border border-[#15171a24] bg-white p-2.5 text-sm"
                />
              </div>
              {failure && <ErrorNote message={failure} />}
              <div className="flex flex-wrap gap-2.5">
                <button type="button" className={BTN_P} disabled={deciding !== null} onClick={() => decide('approve')}>
                  {deciding === 'approve' ? 'Approving' : 'Approve'}
                </button>
                <button type="button" className={BTN} disabled={deciding !== null} onClick={() => decide('reject')}>
                  {deciding === 'reject' ? 'Rejecting' : 'Reject'}
                </button>
              </div>
            </>
          ) : (
            <>
              <p className={`m-0 leading-normal ${MUTED}`}>This run is not at a gate, so there is nothing to decide.</p>
              {r.approval && (
                <p className="m-0 text-[13px] leading-normal">
                  Decision on record: <b className="font-semibold">{r.approval.status}</b>
                  {r.approval.decisionNotes ? `. ${r.approval.decisionNotes}` : ''}
                </p>
              )}
              {failure && <ErrorNote message={failure} />}
            </>
          )}
        </div>
      </section>

      <section aria-labelledby="ledger" className="pk-card px-6 py-5">
        <div className="mb-2 flex flex-wrap items-center justify-between gap-2.5">
          <h2 id="ledger" className="m-0 text-base font-semibold">On the ledger</h2>
          {r.chainValid ? <Pill tone="done">Chain valid</Pill> : <Pill tone="block">Chain broken</Pill>}
        </div>
        {r.events.length === 0 ? (
          <p className={`m-0 text-[13px] ${MUTED}`}>No events have been recorded yet.</p>
        ) : (
          <div className="overflow-x-auto">
            <table className="w-full border-collapse text-left text-[13px]">
              <thead>
                <tr className={`text-[12px] ${MUTED}`}>
                  <th scope="col" className="py-2 pr-3 font-semibold">No.</th>
                  <th scope="col" className="py-2 pr-3 font-semibold">Event</th>
                  <th scope="col" className="py-2 pr-3 font-semibold">Step</th>
                  <th scope="col" className="py-2 pr-3 font-semibold">Time</th>
                  <th scope="col" className="py-2 font-semibold">Hash</th>
                </tr>
              </thead>
              <tbody>
                {r.events.map((e) => (
                  <tr key={e.seq} className="border-t border-[#15171a14]">
                    <td className="py-[9px] pr-3 tabular-nums">{e.seq}</td>
                    <td className="py-[9px] pr-3 font-mono text-xs">{e.kind}</td>
                    <td className="py-[9px] pr-3">{view.titleOf(e.stepId)}</td>
                    <td className={`py-[9px] pr-3 ${MUTED}`}>{when(e.createdAt)}</td>
                    <td className="py-[9px] font-mono text-xs">{e.hash.slice(0, 8)}</td>
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
