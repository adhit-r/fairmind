'use client'

import '@/astryx/pages/findings.css'
import Link from 'next/link'
import { Fragment, Suspense, useMemo, useState } from 'react'
import { useSearchParams } from 'next/navigation'
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
import { useSystemContext } from '@/components/workflow/SystemContext'
import { useRisks, type Risk } from '@/lib/api/hooks/useRisks'
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
const systemIdOf = (r: Risk) => (r as { system_id?: string }).system_id ?? r.systemId

function Tasks({ risk }: { risk: Risk }) {
  const systemId = systemIdOf(risk)
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

function FindingsView() {
  const focus = useSearchParams().get('system') ?? undefined
  const { systems } = useSystemContext()
  const { data, summary, loading, error } = useRisks()
  const [openId, setOpenId] = useState<string | null>(null)
  const nameOf = (id: string | undefined) => systems.find((s) => s.id === id)?.name ?? (id ? 'Unknown system' : 'No system')

  // The org-wide list is filtered here so one fetch serves every ?system= link.
  const risks = useMemo(() => (focus ? data.filter((r) => systemIdOf(r) === focus) : data), [data, focus])
  const open = risks.find((r) => r.id === openId) ?? null
  const counts = (key: Severity) => (focus ? risks.filter((r) => r.severity === key).length : (summary?.bySeverity[key] ?? 0))

  return (
    <div className="fm-page fm-fnd">
      <VStack gap={5}>
        <VStack gap={1}>
          <Heading level={1}>Findings</Heading>
          <Text color="secondary">
            {focus ? `Findings on ${nameOf(focus)}. ` : 'Everything the checks, the monitoring watch and your reviewers have raised, most serious first. '}
            {focus && <Link href="/findings">Show every system</Link>}
          </Text>
        </VStack>

        {error ? (
          <Banner status="error" title="Findings could not load" description={error.message} />
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
            <ul className="fm-fnd-counts" aria-label="Findings by severity">
              <li>
                <b>{focus ? risks.length : (summary?.total ?? risks.length)}</b>
                <span>All findings</span>
              </li>
              <li>
                <b>{focus ? risks.filter((r) => r.status === 'open').length : (summary?.open ?? 0)}</b>
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
                              <button type="button" className="title" onClick={() => setOpenId(r.id)}>
                                {r.title}
                              </button>
                            </td>
                            <td>{nameOf(systemIdOf(r))}</td>
                            <td>{sourceName(r.source)}</td>
                            <td>
                              <Token size="sm" color={r.status === 'open' ? sev.color : 'default'} label={words(r.status)} />
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

      <Drawer isOpen={open !== null} onOpenChange={(o) => !o && setOpenId(null)} label={open ? `Finding: ${open.title}` : 'Finding'} width={480} padding={5}>
        {open && (
          <VStack gap={5}>
            <VStack gap={2} align="start">
              <Token size="sm" color={SEVERITIES.find((s) => s.key === open.severity)?.color ?? 'default'} label={`${words(open.severity)} severity`} />
              <Heading level={2}>{open.title}</Heading>
            </VStack>
            <MetadataList label={{ width: 110 }}>
              <MetadataListItem label="System">{systemIdOf(open) ? <Link href={`/systems/${encodeURIComponent(systemIdOf(open) as string)}`}>{nameOf(systemIdOf(open))}</Link> : 'Not tied to a system'}</MetadataListItem>
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
              <Text color="secondary">Retest by running the check again on the system file. A finding closes when the next result passes.</Text>
              {systemIdOf(open) && <Button label="Open the system file" variant="secondary" href={`/systems/${encodeURIComponent(systemIdOf(open) as string)}`} />}
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
