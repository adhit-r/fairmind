'use client'

import '@/astryx/pages/runs.css'
import Link from 'next/link'
import { useRouter, useSearchParams } from 'next/navigation'
import { Suspense, useMemo, useState } from 'react'
import { Banner } from '@astryxdesign/core/Banner'
import { Button } from '@astryxdesign/core/Button'
import { Divider } from '@astryxdesign/core/Divider'
import { EmptyState } from '@astryxdesign/core/EmptyState'
import { HStack, VStack } from '@astryxdesign/core/Layout'
import { MetadataList, MetadataListItem } from '@astryxdesign/core/MetadataList'
import { SegmentedControl, SegmentedControlItem } from '@astryxdesign/core/SegmentedControl'
import { Skeleton } from '@astryxdesign/core/Skeleton'
import { Heading, Text } from '@astryxdesign/core/Text'
import { TextArea } from '@astryxdesign/core/TextArea'
import { Token } from '@astryxdesign/core/Token'
import {
  GATE_KINDS,
  decisionsFor,
  usePackActions,
  useRun,
  useRuns,
  versionName,
  type Decision,
  type RunStatus,
  type RunSummary,
} from '@/lib/api/hooks/usePacks'
import { fmtWhen } from '@/astryx/data/evaluations'

const STATUS_WORD: Record<RunStatus, string> = {
  queued: 'Queued',
  running: 'Running',
  waiting: 'Waiting',
  blocked: 'Blocked',
  done: 'Done',
  failed: 'Failed',
}
const STATUS_COLOR: Record<RunStatus, 'blue' | 'yellow' | 'red' | 'green' | 'gray'> = {
  queued: 'gray',
  running: 'blue',
  waiting: 'yellow',
  blocked: 'red',
  done: 'green',
  failed: 'red',
}
const DECISION_LABEL: Record<Decision, string> = { approve: 'Approve', request_changes: 'Request changes', reject: 'Reject' }
const cap = (s: string) => s.charAt(0).toUpperCase() + s.slice(1)

function RunDetail({ runId, onChanged }: { runId: string; onChanged: () => void }) {
  const run = useRun(runId)
  const { decideRun, submitStepOutput, runAgent } = usePackActions()
  const [notes, setNotes] = useState('')
  const [output, setOutput] = useState('')
  const [route, setRoute] = useState('')
  const [busy, setBusy] = useState<string | null>(null)
  const [failure, setFailure] = useState<string | null>(null)

  const r = run.data
  const view = useMemo(() => {
    if (!r) return null
    const completed = new Set(r.events.filter((e) => e.kind === 'step.completed' && e.stepId).map((e) => e.stepId))
    return {
      completed,
      current: r.steps.find((s) => s.id === r.currentStep) ?? null,
      titleOf: (id: string | null) => (id ? r.steps.find((s) => s.id === id)?.title ?? id : ''),
    }
  }, [r])

  async function act(key: string, call: () => Promise<{ error: string | null }>, clear?: () => void) {
    setBusy(key)
    setFailure(null)
    const res = await call()
    setBusy(null)
    if (res.error) setFailure(res.error)
    else clear?.()
    run.reload()
    onChanged()
  }

  if (run.loading && !r) return <Skeleton height={320} />
  if (run.error || !r || !view) {
    return (
      <Banner
        status="error"
        title="This run could not be loaded"
        description={run.error ?? undefined}
        endContent={<Button label="Try again" size="sm" variant="secondary" onClick={run.reload} />}
      />
    )
  }

  const { current } = view
  const branches = current && current.next.length > 1 ? current.next : []
  const decisions = current ? decisionsFor(current) : []

  return (
    <VStack gap={4}>
      <VStack gap={2}>
        <HStack gap={2} vAlign="center" wrap="wrap">
          <Token size="sm" color={STATUS_COLOR[r.status]} label={STATUS_WORD[r.status]} />
          <Text type="supporting" color="secondary">{versionName(r.version)}</Text>
        </HStack>
        <Heading level={2}>{r.workflowName}</Heading>
      </VStack>

      <MetadataList columns="single" label={{ position: 'start', width: 110 }}>
        <MetadataListItem label="Started">{fmtWhen(r.createdAt) || 'Unknown'}</MetadataListItem>
        <MetadataListItem label="Updated">{fmtWhen(r.updatedAt) || 'Unknown'}</MetadataListItem>
        {r.finishedAt && <MetadataListItem label="Finished">{fmtWhen(r.finishedAt)}</MetadataListItem>}
        <MetadataListItem label="Current step">{current ? current.title : 'None'}</MetadataListItem>
        <MetadataListItem label="Approval">
          {r.approval ? `${cap(r.approval.status)}${r.approval.decisionNotes ? `. ${r.approval.decisionNotes}` : ''}` : 'No decision on record'}
        </MetadataListItem>
        {r.systemId && (
          <MetadataListItem label="System">
            <Link href={`/systems/${r.systemId}`}>Open the system file</Link>
          </MetadataListItem>
        )}
      </MetadataList>

      {failure && <Banner status="error" title="That did not go through" description={failure} />}

      {r.waitingFor === 'approval' && (
        <>
          <Divider />
          <VStack gap={3}>
            <Heading level={3}>Needs a decision</Heading>
            <Text color="secondary">
              The run is holding at {current ? current.title : 'the gate'}. Nothing changes in your systems until you decide.
            </Text>
            {current?.detail && <Text type="supporting" color="secondary">{current.detail}</Text>}
            <TextArea label="Notes (optional)" value={notes} onChange={setNotes} rows={3} />
            <HStack gap={2} wrap="wrap">
              {decisions.map((d, i) => (
                <Button
                  key={d}
                  label={DECISION_LABEL[d]}
                  variant={i === 0 ? 'primary' : 'secondary'}
                  size="sm"
                  isLoading={busy === d}
                  isDisabled={busy !== null}
                  onClick={() => act(d, () => decideRun(r.id, d, notes.trim() || undefined), () => setNotes(''))}
                />
              ))}
            </HStack>
            {decisions.length === 0 && (
              <Text type="supporting" color="secondary">This step offers no decision buttons. Open the workflow to see how it proceeds.</Text>
            )}
          </VStack>
        </>
      )}

      {r.waitingFor === 'input' && current && (
        <>
          <Divider />
          <VStack gap={3}>
            <Heading level={3}>This step needs output</Heading>
            <Text color="secondary">{current.title}. {current.detail}</Text>
            {current.output && <Text type="supporting" color="secondary">Expected: {current.output}</Text>}
            <div className="fm-rn-box">
              <Text type="supporting" color="secondary">The agent can draft this step. It goes on the ledger with who did it, and every decision still waits for a person.</Text>
              <div>
                <Button
                  label="Let the agent draft this step"
                  size="sm"
                  isLoading={busy === 'agent'}
                  isDisabled={busy !== null}
                  onClick={() => act('agent', () => runAgent(r.id, current.id))}
                />
              </div>
            </div>
            <Text weight="bold">Or record it yourself</Text>
            {branches.length > 0 && (
              <fieldset className="fm-rn-branches">
                <legend>Where next</legend>
                {branches.map((b) => (
                  <label key={b.to}>
                    <input type="radio" name="route" checked={route === (b.label ?? '')} onChange={() => setRoute(b.label ?? '')} />
                    {cap(b.label ?? view.titleOf(b.to))}
                  </label>
                ))}
              </fieldset>
            )}
            <TextArea label="What you did and found" value={output} onChange={setOutput} rows={4} />
            <div>
              <Button
                label="Record and continue"
                variant="secondary"
                size="sm"
                isLoading={busy === 'submit'}
                isDisabled={busy !== null || !output.trim() || (branches.length > 0 && !route)}
                onClick={() =>
                  act('submit', () => submitStepOutput(r.id, current.id, output.trim(), route || undefined), () => {
                    setOutput('')
                    setRoute('')
                  })
                }
              />
            </div>
          </VStack>
        </>
      )}

      <Divider />
      <VStack gap={2}>
        <Heading level={3}>Steps</Heading>
        <ol className="fm-rn-steps">
          {r.steps.map((s) => {
            const state = view.completed.has(s.id) ? 'done' : r.currentStep === s.id ? 'current' : 'next'
            return (
              <li key={s.id} className={state === 'current' ? 'is-current' : undefined}>
                <span className={`fm-rn-dot ${state}`} aria-hidden />
                <div>
                  <div className="fm-rn-step-title">{s.title}</div>
                  <div className="fm-rn-sub">
                    {state === 'done' ? 'Done' : state === 'current' ? 'Current step' : 'Not reached'}
                    {GATE_KINDS.includes(s.kind) ? ', a person decides' : ''}
                  </div>
                </div>
              </li>
            )
          })}
        </ol>
      </VStack>

      <Divider />
      <VStack gap={2}>
        <HStack gap={2} hAlign="between" vAlign="center">
          <Heading level={3}>Ledger</Heading>
          <Token size="sm" color={r.chainValid ? 'green' : 'red'} label={r.chainValid ? 'Chain intact' : 'Chain broken'} />
        </HStack>
        {r.events.length === 0 ? (
          <Text type="supporting" color="secondary">No events have been recorded yet.</Text>
        ) : (
          <div className="fm-rn-ledger-wrap">
            <table className="fm-rn-ledger">
              <thead>
                <tr>
                  <th scope="col">No.</th>
                  <th scope="col">Event</th>
                  <th scope="col">Step</th>
                  <th scope="col">Previous</th>
                  <th scope="col">Hash</th>
                </tr>
              </thead>
              <tbody>
                {r.events.map((e) => (
                  <tr key={e.seq}>
                    <td>{e.seq}</td>
                    <td className="fm-rn-code">{e.kind}</td>
                    <td>{view.titleOf(e.stepId) || 'Run'}</td>
                    <td className="fm-rn-code" title={e.prevHash ?? undefined}>{e.prevHash ? e.prevHash.slice(0, 8) : 'Genesis'}</td>
                    <td className="fm-rn-code" title={e.hash}>{e.hash.slice(0, 8)}</td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        )}
      </VStack>

      <Text type="supporting" color="secondary">
        <Link href={`/compliance/runs/${r.id}`}>Open the full run page</Link>
      </Text>
    </VStack>
  )
}

function RunsView() {
  const router = useRouter()
  const params = useSearchParams()
  const runs = useRuns()
  const [status, setStatus] = useState<'all' | RunStatus>('all')
  const selectedId = params.get('run')

  const all: RunSummary[] = runs.data ?? []
  const present = useMemo(() => (Object.keys(STATUS_WORD) as RunStatus[]).filter((s) => all.some((r) => r.status === s)), [all])
  const visible = status === 'all' ? all : all.filter((r) => r.status === status)
  const waitingOnPerson = all.filter((r) => r.status === 'waiting').length
  const select = (id: string) => router.replace(`/runs?run=${encodeURIComponent(id)}`, { scroll: false })

  return (
    <div className="fm-page">
      <VStack gap={5}>
        <HStack gap={4} hAlign="between" vAlign="end" wrap="wrap">
          <VStack gap={1}>
            <Heading level={1}>Runs</Heading>
            <Text color="secondary">
              {runs.loading && !runs.data
                ? 'Loading runs.'
                : `${all.length} run${all.length === 1 ? '' : 's'}, ${waitingOnPerson} waiting on a person.`}
            </Text>
          </VStack>
          {all.length > 0 && (
            <SegmentedControl label="Filter by status" value={status} onChange={(v) => setStatus(v as 'all' | RunStatus)} size="sm">
              <SegmentedControlItem label="All" value="all" />
              {present.map((s) => (
                <SegmentedControlItem key={s} label={STATUS_WORD[s]} value={s} />
              ))}
            </SegmentedControl>
          )}
        </HStack>

        {runs.error && (
          <Banner
            status="error"
            title="Runs could not be loaded"
            description={runs.error}
            endContent={<Button label="Try again" size="sm" variant="secondary" onClick={runs.reload} />}
          />
        )}

        {runs.loading && !runs.data ? (
          <Skeleton height={320} />
        ) : runs.data && all.length === 0 ? (
          <EmptyState
            title="No runs yet"
            description="A run starts when a workflow is started from a framework or a system. Open Frameworks to start one."
            actions={<Button label="Open frameworks" variant="secondary" href="/frameworks" />}
          />
        ) : runs.data ? (
          <div className="fm-rn-split">
            <div className="fm-rn-list">
              {visible.length === 0 ? (
                <EmptyState title="No matching runs" description="Pick another status." isCompact />
              ) : (
                <ul>
                  {visible.map((r) => (
                    <li key={r.id}>
                      <button type="button" className={`fm-rn-item${r.id === selectedId ? ' is-selected' : ''}`} onClick={() => select(r.id)}>
                        <span className="fm-rn-item-top">
                          <span className="fm-rn-item-name">{r.workflowName}</span>
                          <Token size="sm" color={STATUS_COLOR[r.status]} label={STATUS_WORD[r.status]} />
                        </span>
                        <span className="fm-rn-sub">
                          {r.waitingFor === 'approval' ? 'Waiting for a decision' : r.waitingFor === 'input' ? 'Waiting for step output' : STATUS_WORD[r.status]}
                          {fmtWhen(r.updatedAt) ? `, updated ${fmtWhen(r.updatedAt)}` : ''}
                        </span>
                      </button>
                    </li>
                  ))}
                </ul>
              )}
            </div>
            <div className="fm-card">
              {selectedId ? (
                <RunDetail key={selectedId} runId={selectedId} onChanged={runs.reload} />
              ) : (
                <EmptyState title="No run selected" description="Pick a run to see its steps, approval and ledger." isCompact />
              )}
            </div>
          </div>
        ) : null}
      </VStack>
    </div>
  )
}

export default function RunsPage() {
  return (
    <Suspense fallback={<div className="fm-page"><Skeleton height={320} /></div>}>
      <RunsView />
    </Suspense>
  )
}
