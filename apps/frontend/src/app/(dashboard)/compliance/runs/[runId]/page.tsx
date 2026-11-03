'use client'

import { useParams } from 'next/navigation'
import { useEffect, useMemo, useState, type ReactNode } from 'react'
import { GATE_KINDS, decisionsFor, usePackActions, useRun, useWaitingRuns, useWorkflow, versionName, type Decision, type RunEvent } from '@/lib/api/hooks/usePacks'
import { IsoFigure } from '@/components/packs/IsoFigure'
import { runFigure } from '@/components/packs/figures'
import { BTN, BTN_P, Crumbs, ErrorNote, Heading, LABEL, LINE, Loading, MUTED, Num, Pill, StatusPill, cap, when } from '@/components/packs/parts'
import { cn } from '@/lib/utils'
import { useAuth } from '@/lib/api/hooks/useAuth'

const DECISION_LABEL: Record<Decision, [string, string]> = {
  approve: ['Approve', 'Approving'],
  request_changes: ['Request changes', 'Sending back'],
  reject: ['Reject', 'Rejecting'],
}

/** One line on what an event recorded: a step's submitted output, a decision, or the evidence seal. */
function detailOf(e: RunEvent): string {
  const p = e.payload ?? {}
  if (typeof p.summary === 'string') return typeof p.route === 'string' ? `${p.summary} (${p.route})` : p.summary
  if (typeof p.decision === 'string') {
    const label = DECISION_LABEL[p.decision as Decision]?.[0] ?? p.decision
    return [label, p.notes, p.escalated ? `Escalated after ${p.escalated}` : null, p.selfReview ? 'Decided by the person who recorded the proposal' : null]
      .filter(Boolean)
      .join('. ')
  }
  if (typeof p.sealedHeadHash === 'string') return `Sealed events 1 to ${String(p.sealedThroughSeq)}`
  return ''
}

export default function RunPage() {
  const { runId } = useParams<{ runId: string }>()
  const { getCurrentUser } = useAuth()
  const [me, setMe] = useState<string | null>(null)
  useEffect(() => {
    getCurrentUser().then((u) => setMe(u?.id ?? null)).catch(() => setMe(null))
  }, [getCurrentUser])
  const run = useRun(runId)
  const { decideRun, submitStepOutput } = usePackActions()
  const workflow = useWorkflow(run.data?.workflowId)
  const waiting = useWaitingRuns()
  const [notes, setNotes] = useState('')
  const [deciding, setDeciding] = useState<Decision | null>(null)
  const [output, setOutput] = useState('')
  const [route, setRoute] = useState('')
  const [submitting, setSubmitting] = useState(false)
  const [failure, setFailure] = useState<string | null>(null)

  const view = useMemo(() => {
    const r = run.data
    if (!r) return null
    const steps = r.steps
    const completed = new Set(r.events.filter((e) => e.kind === 'step.completed' && e.stepId).map((e) => e.stepId))
    // A gate is any step where the run stops for a person: ask, exception or decide.
    const gateIds = new Set(steps.filter((s) => GATE_KINDS.includes(s.kind)).map((s) => s.id))
    const reachedAsk = r.waitingFor === 'approval' || r.events.some((e) => e.stepId !== null && gateIds.has(e.stepId))
    const approved = r.approval?.status.toLowerCase().startsWith('approv') ?? false
    const rank = (waiting.data ?? []).findIndex((x) => x.id === r.id) + 1
    const waitNo = rank || 1
    return {
      waitNo,
      figure: runFigure({
        systems: [...new Set(steps.flatMap((s) => s.systems))],
        steps: steps.map((s) => ({ status: completed.has(s.id) ? 'done' : r.currentStep === s.id ? 'current' : 'next' })),
        gate: !reachedAsk ? 'none' : approved ? 'open' : 'closed',
        waitNo,
        agent: r.status === 'waiting' ? 'need' : r.status === 'blocked' ? 'held' : 'idle',
        sealed: r.events.filter((e) => e.payload?.sealedHeadHash).length,
      }),
      sealed: r.events.filter((e) => e.payload?.sealedHeadHash).length,
      stepNo: steps.findIndex((s) => s.id === r.currentStep) + 1,
      current: steps.find((s) => s.id === r.currentStep) ?? null,
      titleOf: (id: string | null) => (id ? steps.find((s) => s.id === id)?.title ?? id : ''),
    }
  }, [run.data, workflow.data, waiting.data])

  async function submit() {
    if (!run.data?.currentStep) return
    setSubmitting(true)
    setFailure(null)
    const res = await submitStepOutput(runId, run.data.currentStep, output.trim(), route || undefined)
    setSubmitting(false)
    if (res.error) setFailure(res.error)
    else {
      setOutput('')
      setRoute('')
    }
    run.reload()
    waiting.reload()
  }

  async function decide(decision: Decision) {
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
  const branches = view.current && view.current.next.length > 1 ? view.current.next : []
  const decisions = view.current ? decisionsFor(view.current) : []
  const stage = workflow.data ? cap(workflow.data.stage) : null
  const stepsTotal = r.steps.length

  return (
    <div className="flex flex-col gap-[22px]">
      <Crumbs items={[{ label: 'Frameworks', href: '/compliance' }, { label: r.workflowName, href: `/compliance/workflows/${r.workflowId}` }, { label: 'Run' }]} />
      <div className="flex max-w-[760px] flex-col gap-2">
        <div className="flex flex-wrap gap-2">
          <StatusPill status={r.status} />
          {isWaiting && view.stepNo > 0 && <Pill tone="you">At step {view.stepNo} of {stepsTotal}</Pill>}
          {stage && <Pill>{stage}</Pill>}
          <Pill>{versionName(r.version)}</Pill>
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
            label={`The agent for ${r.workflowName}. ${stepsTotal} step tiles show progress; status is ${r.status}. ${view.sealed} evidence records are sealed on the ledger.${r.waitingFor === 'approval' ? ' A gate is closed and the agent waits for your decision.' : r.waitingFor === 'input' ? ' The agent waits for you to record this step.' : ''}`}
          />
        </div>
        <div className="flex flex-[1_1_300px] flex-col gap-3.5 px-1 py-1.5">
          <div className="flex items-center gap-2.5">
            {isWaiting && <Num n={view.waitNo} />}
            <h2 className="m-0 text-base font-semibold text-[var(--fm-ink)]">{r.waitingFor === 'approval' ? 'Your decision' : r.waitingFor === 'input' ? 'Your step' : 'Where it stands'}</h2>
          </div>
          {r.waitingFor === 'input' && view.current ? (
            <form
              className="flex flex-col gap-3.5"
              onSubmit={(e) => {
                e.preventDefault()
                submit()
              }}
            >
              <p className="m-0 leading-normal text-[var(--fm-ink)]">
                The run is at <b className="font-semibold">{view.current.title}</b>. FairMind does not do this step itself yet, so record what you did and found. It goes on the ledger as a manual entry.
              </p>
              {view.current.detail && <p className={`m-0 text-[13px] leading-normal ${MUTED}`}>{view.current.detail}</p>}
              <dl className="m-0 flex flex-col gap-2.5 text-[13px]">
                {([
                  ['Expected output', view.current.output],
                  ['Systems', view.current.systems.join(', ')],
                  ['If it fails', view.current.failure],
                ] as const)
                  .filter(([, v]) => v)
                  .map(([k, v]) => (
                    <div key={k} className="flex flex-col gap-0.5">
                      <dt className={LABEL}>{k}</dt>
                      <dd className="m-0 leading-snug text-[var(--fm-ink)]">{v}</dd>
                    </div>
                  ))}
              </dl>
              {branches.length > 0 && (
                <fieldset className="m-0 flex flex-col gap-1.5 border-0 p-0">
                  <legend className="mb-1.5 text-[13px] font-semibold text-[var(--fm-ink)]">Where next</legend>
                  {branches.map((b) => (
                    <label key={b.to} className="flex items-center gap-2 text-sm text-[var(--fm-ink)]">
                      <input type="radio" name="route" value={b.label ?? ''} checked={route === b.label} onChange={() => setRoute(b.label ?? '')} required />
                      {cap(b.label ?? view.titleOf(b.to))}
                    </label>
                  ))}
                </fieldset>
              )}
              <div className="flex flex-col gap-1.5">
                <label htmlFor="output" className="text-[13px] font-semibold text-[var(--fm-ink)]">What you did and found</label>
                <textarea
                  id="output"
                  value={output}
                  onChange={(e) => setOutput(e.target.value)}
                  rows={4}
                  required
                  className="resize-y rounded-[10px] border border-[var(--fm-line)] bg-white p-2.5 text-sm text-[var(--fm-ink)] focus:border-[var(--fm-ink)] focus:outline-none"
                />
              </div>
              {failure && <ErrorNote message={failure} />}
              <div>
                <button type="submit" className={BTN_P} disabled={submitting || !output.trim() || (branches.length > 0 && !route)}>
                  {submitting ? 'Recording' : 'Record and continue'}
                </button>
              </div>
            </form>
          ) : r.waitingFor === 'approval' ? (
            <>
              <p className="m-0 leading-normal text-[var(--fm-ink)]">
                The agent is holding at {view.titleOf(r.currentStep) ? <b className="font-semibold">{view.titleOf(r.currentStep)}</b> : 'the gate'}. Nothing in your systems changes until you decide.
              </p>
              {view.current?.detail && <p className={`m-0 text-[13px] leading-normal ${MUTED}`}>{view.current.detail}</p>}
              {workflow.data && (workflow.data.approver || workflow.data.gateConditions || workflow.data.separationOfDuties) && (
                <dl className="m-0 flex flex-col gap-2.5 text-[13px]">
                  {([
                    ['Approver', workflow.data.approver],
                    ['Gate conditions', workflow.data.gateConditions],
                    ['Separation of duties', workflow.data.separationOfDuties],
                  ] as const)
                    .filter(([, v]) => v)
                    .map(([k, v]) => (
                      <div key={k} className="flex flex-col gap-0.5">
                        <dt className={LABEL}>{k}</dt>
                        <dd className="m-0 leading-snug text-[var(--fm-ink)]">{v}</dd>
                      </div>
                    ))}
                </dl>
              )}
              <div className="flex flex-col gap-1.5">
                <label htmlFor="notes" className="text-[13px] font-semibold text-[var(--fm-ink)]">Notes (optional)</label>
                <textarea
                  id="notes"
                  value={notes}
                  onChange={(e) => setNotes(e.target.value)}
                  rows={3}
                  className="resize-y rounded-[10px] border border-[var(--fm-line)] bg-white p-2.5 text-sm text-[var(--fm-ink)] focus:border-[var(--fm-ink)] focus:outline-none"
                />
              </div>
              {me && r.proposalBy === me && (
                <p role="note" className="m-0 rounded-[10px] border border-[#f3d38a] bg-[#fff8e6] px-3 py-2.5 text-[13px] leading-snug text-[#7a5200]">
                  You recorded the proposal this decision is about.
                  {workflow.data?.separationOfDuties ? ` The workflow asks: ${workflow.data.separationOfDuties.replace(/\.$/, '')}.` : ''} You can still decide; the ledger will show it was a self-review.
                </p>
              )}
              {failure && <ErrorNote message={failure} />}
              <div className="flex flex-wrap gap-2.5">
                {decisions.map((d, i) => (
                  <button key={d} type="button" className={i === 0 ? BTN_P : BTN} disabled={deciding !== null} onClick={() => decide(d)}>
                    {DECISION_LABEL[d][deciding === d ? 1 : 0]}
                  </button>
                ))}
              </div>
            </>
          ) : (
            <>
              <dl className="m-0 flex flex-col gap-3 text-[13px]">
                {([
                  ['Status', <StatusPill key="s" status={r.status} />],
                  ['Current step', view.current ? `${view.stepNo} of ${stepsTotal}: ${view.current.title}` : null],
                  ['Started', when(r.createdAt)],
                  ['Finished', r.finishedAt ? when(r.finishedAt) : null],
                  ['Decision on record', r.approval ? `${cap(r.approval.status)}${r.approval.decisionNotes ? `. ${r.approval.decisionNotes}` : ''}` : null],
                ] as Array<[string, ReactNode]>)
                  .filter(([, v]) => v)
                  .map(([k, v]) => (
                    <div key={k} className="flex flex-col gap-1">
                      <dt className={LABEL}>{k}</dt>
                      <dd className="m-0 leading-snug text-[var(--fm-ink)]">{v}</dd>
                    </div>
                  ))}
              </dl>
              {r.status !== 'done' && <p className={`m-0 text-[13px] leading-normal ${MUTED}`}>Nothing to decide until the agent reaches a gate.</p>}
              {failure && <ErrorNote message={failure} />}
            </>
          )}
        </div>
      </section>

      <section aria-labelledby="ledger" className="pk-card px-6 py-5">
        <div className="mb-3 flex flex-wrap items-start justify-between gap-2.5">
          <div className="flex max-w-[640px] flex-col gap-1">
            <h2 id="ledger" className="m-0 text-base font-semibold text-[var(--fm-ink)]">On the ledger</h2>
            <p className={cn('m-0 text-[13px] leading-normal', MUTED)}>
              Every event carries the hash of the one before it, so changing any past event breaks the chain from that point on.
            </p>
          </div>
          {r.chainValid ? <Pill tone="done" dot>Chain valid</Pill> : <Pill tone="block" dot>Chain broken</Pill>}
        </div>
        {r.events.length === 0 ? (
          <p className={`m-0 text-[13px] ${MUTED}`}>No events have been recorded yet.</p>
        ) : (
          <div className="overflow-x-auto">
            <table className="w-full min-w-[860px] border-collapse text-left text-[13px] text-[var(--fm-ink)]">
              <thead>
                <tr className={LABEL}>
                  <th scope="col" className="w-12 py-2 pr-3 font-semibold">No.</th>
                  <th scope="col" className="py-2 pr-3 font-semibold">Event</th>
                  <th scope="col" className="py-2 pr-3 font-semibold">Step</th>
                  <th scope="col" className="py-2 pr-3 font-semibold">Recorded</th>
                  <th scope="col" className="py-2 pr-3 font-semibold">Time</th>
                  <th scope="col" className="py-2 pr-3 font-semibold">Previous</th>
                  <th scope="col" className="py-2 font-semibold">Hash</th>
                </tr>
              </thead>
              <tbody>
                {r.events.map((e) => (
                  <tr key={e.seq} className={cn('border-t', LINE)}>
                    <td className={`py-[9px] pr-3 tabular-nums ${MUTED}`}>{e.seq}</td>
                    <td className="py-[9px] pr-3 font-mono text-xs">{e.kind}</td>
                    <td className="py-[9px] pr-3">{view.titleOf(e.stepId) || <span className="text-[var(--fm-ink3)]">Run</span>}</td>
                    <td className="max-w-[280px] py-[9px] pr-3 leading-snug" title={detailOf(e) || undefined}>
                      <span className="line-clamp-2">{detailOf(e)}</span>
                    </td>
                    <td className={`whitespace-nowrap py-[9px] pr-3 ${MUTED}`}>{when(e.createdAt)}</td>
                    <td className="py-[9px] pr-3 font-mono text-xs text-[var(--fm-ink3)]" title={e.prevHash ?? undefined}>{e.prevHash ? e.prevHash.slice(0, 10) : 'Genesis'}</td>
                    <td className="py-[9px] font-mono text-xs" title={e.hash}>{e.hash.slice(0, 10)}</td>
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
