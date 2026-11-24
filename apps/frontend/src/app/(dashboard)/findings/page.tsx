'use client'

import '@/astryx/pages/findings.css'
import Link from 'next/link'
import { Fragment, Suspense, useState } from 'react'
import { useRouter, useSearchParams } from 'next/navigation'
import { Banner } from '@astryxdesign/core/Banner'
import { Button } from '@astryxdesign/core/Button'
import { Drawer } from '@astryxdesign/core/Drawer'
import { EmptyState } from '@astryxdesign/core/EmptyState'
import { Heading, Text } from '@astryxdesign/core/Text'
import { MetadataList, MetadataListItem } from '@astryxdesign/core/MetadataList'
import { Selector } from '@astryxdesign/core/Selector'
import { Skeleton } from '@astryxdesign/core/Skeleton'
import { TextArea } from '@astryxdesign/core/TextArea'
import { TextInput } from '@astryxdesign/core/TextInput'
import { Token } from '@astryxdesign/core/Token'
import { VStack } from '@astryxdesign/core/Layout'
import { evaluationHref, recordParam } from '@/lib/assurance/evaluationLinks'
import { evidenceRecordHref } from '@/lib/assurance/evidenceLinks'
import { useSystemContext } from '@/components/workflow/SystemContext'
import { isOpenRisk, useRisks, type Risk } from '@/lib/api/hooks/useRisks'
import { useRemediation, type RemediationPriority, type RemediationStatus } from '@/lib/api/hooks/useRemediation'

type Severity = Risk['severity']
const SEVERITIES: Array<{ key: Severity; title: string; color: 'red' | 'orange' | 'yellow' | 'default' }> = [
  { key: 'critical', title: 'Critical', color: 'red' },
  { key: 'high', title: 'High', color: 'red' },
  { key: 'medium', title: 'Medium', color: 'orange' },
  { key: 'low', title: 'Low', color: 'default' },
]
const TASK_STATUS = [
  { value: 'open', label: 'Open' },
  { value: 'in_progress', label: 'In progress' },
  { value: 'blocked', label: 'Blocked' },
  { value: 'ready_for_retest', label: 'Fixed, ready for retest' },
  { value: 'resolved', label: 'Resolved' },
  { value: 'closed', label: 'Closed' },
]
const PRIORITY = SEVERITIES.map((s) => ({ value: s.key, label: s.title }))
const words = (s: string) => s.replace(/_/g, ' ').replace(/^./, (c) => c.toUpperCase())
const sourceName = (s: string | undefined) => (!s ? 'Not recorded' : s === 'manual_assessment' ? 'Entered by a person' : s === 'fairmind.watch' ? 'Monitoring watch' : words(s.replace(/\./g, ' ')))
const hasId = (id: unknown): id is string => typeof id === 'string' && id.length > 0 && id === id.trim()

function Tasks({ risk }: { risk: Risk }) {
  const systemId = risk.systemId
  const { tasks, loading, saving, error, createTask, updateTaskStatus } = useRemediation(systemId)
  const [adding, setAdding] = useState(false)
  const [title, setTitle] = useState('')
  const [description, setDescription] = useState('')
  const [priority, setPriority] = useState<RemediationPriority>(risk.severity)
  const [problem, setProblem] = useState<string | null>(null)

  const act = async (fn: () => Promise<unknown>) => {
    setProblem(null)
    try {
      await fn()
    } catch (e) {
      setProblem(e instanceof Error ? e.message : 'The change was not saved')
    }
  }
  const mine = tasks.filter((t) => t.riskId === risk.id || t.linkedRiskIds.includes(risk.id))
  const others = tasks.length - mine.length

  if (!systemId) return <Text color="secondary">This finding is not tied to a system, so it has no remediation tasks.</Text>
  return (
    <VStack gap={3}>
      <Heading level={3}>Remediation tasks</Heading>
      {(error || problem) && <Banner status="error" title="Remediation" description={problem ?? error?.message} />}
      {loading ? (
        <Skeleton height={48} />
      ) : mine.length === 0 ? (
        <Text color="secondary">No task is linked to this finding yet.{others > 0 ? ` The system has ${others} other task${others === 1 ? '' : 's'}.` : ''}</Text>
      ) : (
        <div>
          {mine.map((t) => (
            <div className="fm-fnd-task" key={t.id}>
              <header>
                <span>{t.title}</span>
                <small>
                  {words(t.priority)} priority{t.owner ? ` · ${t.owner}` : ''}
                  {t.dueDate ? ` · due ${t.dueDate}` : ''}
                </small>
              </header>
              <Selector
                label="Status"
                size="sm"
                options={TASK_STATUS}
                value={t.status}
                isDisabled={saving}
                onChange={(v) => void act(() => updateTaskStatus(t.id, v as RemediationStatus))}
              />
            </div>
          ))}
        </div>
      )}
      {adding ? (
        <VStack gap={3}>
          <TextInput label="Task" value={title} onChange={setTitle} isRequired />
          <TextArea label="What needs to change" value={description} onChange={setDescription} rows={3} />
          <Selector label="Priority" options={PRIORITY} value={priority} onChange={(v) => setPriority(v as RemediationPriority)} />
          <Button
            label="Add task"
            variant="primary"
            isDisabled={!title.trim() || saving}
            onClick={() =>
              void act(async () => {
                await createTask({ title, description, priority, riskId: risk.id, source: 'risk' })
                setTitle('')
                setDescription('')
                setAdding(false)
              })
            }
          />
        </VStack>
      ) : (
        <Button label="Add a remediation task" variant="secondary" onClick={() => setAdding(true)} />
      )}
    </VStack>
  )
}

function Retest({ risk }: { risk: Risk }) {
  const systemId = risk.systemId
  const router = useRouter()
  const params = useSearchParams()
  const historyOpen = params.get('retests') === 'all'
  function toggleHistory() {
    const next = new URLSearchParams(params.toString())
    if (historyOpen) next.delete('retests')
    else next.set('retests', 'all')
    router.replace(`/findings?${next}`, { scroll: false })
  }
  const metadata = risk.metadata
  const { systems, loading, error } = useSystemContext()
  const system = systems.find((item) => item.id === systemId && item.metadata?.source !== 'fallback')
  const canPrepare = Boolean(!loading && !error && system?.stage && system.stage !== 'retired' && isOpenRisk(risk))
  if (!systemId) return <Text color="secondary">No system is recorded for this finding. A retest cannot be scoped.</Text>

  if (risk.source === 'fairmind.eval_engines' && hasId(metadata?.evaluationId)) {
    const evaluationId = metadata.evaluationId
    const history = Array.isArray(metadata.retestEvidenceIds)
      ? metadata.retestEvidenceIds.filter((id) => typeof id === 'string' && id && id !== metadata.evidenceId && id !== metadata.retestEvidenceId)
      : []
    const href = (runId?: string) => evaluationHref(evaluationId, systemId, runId, risk.id)
    return (
      <VStack gap={2} align="start">
        <Text>{evaluationId}</Text>
        {hasId(metadata.evidenceId)
          ? <Link href={href(metadata.evidenceId)}>View original failed run</Link>
          : <Text color="secondary">The original run ID was not recorded.</Text>}
        {hasId(metadata.retestEvidenceId) && metadata.retestEvidenceId !== metadata.evidenceId
          ? <Link href={href(metadata.retestEvidenceId)}>View recorded retest</Link>
          : <Text color="secondary">No separate retest result is linked to this finding.</Text>}
        {history.length > 0 && (
          <details open={historyOpen}>
            <summary onClick={(event) => { event.preventDefault(); toggleHistory() }}>Earlier retests ({history.length})</summary>
            <ol>{history.map((id, index) => <li key={id}><Link href={href(id)}>Retest {index + 1}</Link></li>)}</ol>
          </details>
        )}
        {canPrepare && <Button label="Prepare a retest" variant="secondary" href={href()} />}
      </VStack>
    )
  }
  if (risk.source === 'fairmind.eval_engines' && hasId(metadata?.evidenceId)) {
    return <VStack gap={2} align="start">
      <Link href={evidenceRecordHref(systemId, metadata.evidenceId)}>View original evidence</Link>
      <Text color="secondary">The check ID is missing, so a retest cannot be prepared.</Text>
    </VStack>
  }
  if (risk.source === 'fairmind.watch' && hasId(metadata?.latest_snapshot_id)) {
    return (
      <VStack gap={2} align="start">
        <Link href={evidenceRecordHref(systemId, metadata.latest_snapshot_id)}>View triggering monitoring snapshot</Link>
        <Text color="secondary">Subsequent snapshots do not close this finding automatically.</Text>
        {canPrepare && <Button label="Prepare a monitoring snapshot" variant="secondary" href={`/systems/${encodeURIComponent(systemId)}?${new URLSearchParams({ finding: risk.id })}#operate`} />}
      </VStack>
    )
  }
  if (risk.source === 'environmental_impact' && hasId(metadata?.assessment_id)) {
    return (
      <VStack gap={2} align="start">
        <Text color="secondary">Original assessment ID: {metadata.assessment_id}. No subsequent assessment is linked as a retest.</Text>
        {canPrepare && <Button label="Prepare an environmental assessment" variant="secondary" href={`/environment?${new URLSearchParams({ system: systemId, action: 'assess', finding: risk.id })}`} />}
      </VStack>
    )
  }
  return (
    <Text color="secondary">
      {risk.source?.startsWith('fairmind.bias_analysis:') && hasId(metadata?.analysis_id)
        ? `Original bias analysis ID: ${metadata.analysis_id}. No retest is linked to this analysis.`
        : 'No originating check is recorded for a retest.'}
    </Text>
  )
}

function FindingsView() {
  const params = useSearchParams()
  const router = useRouter()
  const systemParam = recordParam(params, 'system')
  const openId = recordParam(params, 'finding')
  const focus = systemParam ?? undefined
  const { systems } = useSystemContext()
  const { data: risks, loading, error, reload } = useRisks(focus)
  function selectFinding(risk: Risk | null) {
    const next = new URLSearchParams(params.toString())
    next.delete('retests')
    if (risk) {
      const system = risk.systemId
      if (system) next.set('system', system)
      next.set('finding', risk.id)
    } else next.delete('finding')
    router.push(next.size ? `/findings?${next}` : '/findings', { scroll: false })
  }
  const nameOf = (id: string | undefined) => systems.find((s) => s.id === id)?.name ?? (id ? 'Unknown system' : 'No system')

  const open = risks.find((r) => r.id === openId && r.systemId === focus) ?? null
  const counts = (key: Severity) => risks.filter((r) => r.severity === key).length

  if (systemParam === null || openId === null) return (
    <div className="fm-page fm-fnd"><Banner status="warning" title="Finding unavailable" description="The link has an empty or repeated system or finding ID." endContent={<Link href="/findings">Show every finding</Link>} /></div>
  )

  return (
    <div className="fm-page fm-fnd">
      <VStack gap={5}>
        <VStack gap={1}>
          <Heading level={1}>Findings</Heading>
          <Text color="secondary">
            {focus ? `Findings on ${nameOf(focus)}. ` : 'Showing up to 50 findings across systems, most serious first. '}
            {focus && <Link href="/findings">Show every system</Link>}
          </Text>
        </VStack>

        {openId && !loading && !error && !open && <Banner status="warning" title="Finding unavailable" description="This finding could not be located in the requested system scope." />}
        {error ? (
          <Banner status="error" title="Findings could not load" description={error.message} endContent={<Button label="Retry findings" onClick={reload} />} />
        ) : loading ? (
          <VStack gap={2}>
            {[0, 1, 2, 3].map((i) => (
              <Skeleton key={i} height={40} />
            ))}
          </VStack>
        ) : risks.length === 0 ? (
          <EmptyState title={focus ? 'No findings on this system' : 'No findings'} description="Findings appear when a check fails, the monitoring watch sees a system keep drifting, or someone records one on a system." actions={<Button label="Open AI systems" href="/systems" />} />
        ) : (
          <>
            <ul className="fm-fnd-counts" aria-label="Findings shown by severity">
              <li>
                <b>{risks.length}</b>
                <span>Findings shown</span>
              </li>
              <li>
                <b>{risks.filter(isOpenRisk).length}</b>
                <span>Open</span>
              </li>
              {SEVERITIES.map((s) => (
                <li key={s.key}>
                  <b>{counts(s.key)}</b>
                  <span>{s.title}</span>
                </li>
              ))}
            </ul>
            <section className="fm-card fm-fnd-scroll" aria-label="Findings grouped by severity">
              <table>
                <thead>
                  <tr>
                    <th scope="col">Finding</th>
                    <th scope="col">System</th>
                    <th scope="col">Source</th>
                    <th scope="col">Status</th>
                  </tr>
                </thead>
                <tbody>
                  {SEVERITIES.map((sev) => {
                    const mine = risks.filter((r) => r.severity === sev.key)
                    if (!mine.length) return null
                    return (
                      <Fragment key={sev.key}>
                        <tr className="sec">
                          <th colSpan={4} scope="rowgroup">
                            {sev.title} <span>{mine.length}</span>
                          </th>
                        </tr>
                        {mine.map((r) => (
                          <tr className="item" key={r.id}>
                            <td>
                              <button type="button" className="title" onClick={() => selectFinding(r)}>
                                {r.title}
                              </button>
                            </td>
                            <td>{nameOf(r.systemId)}</td>
                            <td>{sourceName(r.source)}</td>
                            <td>
                              <Token size="sm" color={isOpenRisk(r) ? sev.color : 'default'} label={words(r.status)} />
                            </td>
                          </tr>
                        ))}
                      </Fragment>
                    )
                  })}
                </tbody>
              </table>
            </section>
          </>
        )}
      </VStack>

      <Drawer isOpen={open !== null} onOpenChange={(o) => !o && selectFinding(null)} label={open ? `Finding: ${open.title}` : 'Finding'} width={480} padding={5}>
        {open && (
          <VStack gap={5}>
            <VStack gap={2} align="start">
              <Token size="sm" color={SEVERITIES.find((s) => s.key === open.severity)?.color ?? 'default'} label={`${words(open.severity)} severity`} />
              <Heading level={2}>{open.title}</Heading>
            </VStack>
            <MetadataList label={{ width: 110 }}>
              <MetadataListItem label="System">{open.systemId ? <Link href={`/systems/${encodeURIComponent(open.systemId)}`}>{nameOf(open.systemId)}</Link> : 'Not tied to a system'}</MetadataListItem>
              <MetadataListItem label="Finding ID"><code className="break-all">{open.id}</code></MetadataListItem>
              <MetadataListItem label="Status">{words(open.status)}</MetadataListItem>
              <MetadataListItem label="Source">{sourceName(open.source)}</MetadataListItem>
              <MetadataListItem label="Categories">{(open as { categories?: string[] }).categories?.length ? (open as { categories?: string[] }).categories?.map(words).join(', ') : 'None recorded'}</MetadataListItem>
            </MetadataList>
            <VStack gap={2}>
              <Heading level={3}>What was found</Heading>
              <p className="fm-fnd-prose">{open.description || 'No description recorded.'}</p>
            </VStack>
            <VStack gap={2}>
              <Heading level={3}>Suggested fix</Heading>
              <p className="fm-fnd-prose">{open.mitigation || 'No mitigation recorded.'}</p>
            </VStack>
            <Tasks key={open.id} risk={open} />
            <VStack gap={2}>
              <Heading level={3}>Retest</Heading>
              {systems.some((system) => system.id === open.systemId && system.stage === 'retired') && <Text color="secondary">This system is retired. Only recorded results are available.</Text>}
              <Retest risk={open} />
            </VStack>
          </VStack>
        )}
      </Drawer>
    </div>
  )
}

export default function FindingsPage() {
  return (
    <Suspense fallback={<div className="fm-page"><Skeleton height={40} /></div>}>
      <FindingsView />
    </Suspense>
  )
}
