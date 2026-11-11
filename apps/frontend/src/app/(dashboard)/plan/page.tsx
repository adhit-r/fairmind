'use client'

import '@/astryx/pages/plan.css'
import Link from 'next/link'
import { useState } from 'react'
import { Banner } from '@astryxdesign/core/Banner'
import { Button } from '@astryxdesign/core/Button'
import { Card } from '@astryxdesign/core/Card'
import { Drawer } from '@astryxdesign/core/Drawer'
import { EmptyState } from '@astryxdesign/core/EmptyState'
import { HStack, VStack } from '@astryxdesign/core/Layout'
import { ProgressBar } from '@astryxdesign/core/ProgressBar'
import { Skeleton } from '@astryxdesign/core/Skeleton'
import { Heading, Text } from '@astryxdesign/core/Text'
import { TextArea } from '@astryxdesign/core/TextArea'
import { TextInput } from '@astryxdesign/core/TextInput'
import { Token } from '@astryxdesign/core/Token'
import { Discovery } from '@/components/plan/Discovery'
import { usePlanBoard } from '@/astryx/data/plan'
import type { PlanTask, TaskState } from '@/lib/api/hooks/usePlan'

const LANES: Array<{ key: TaskState; label: string }> = [
  { key: 'todo', label: 'To do' },
  { key: 'needs_you', label: 'Needs you' },
  { key: 'agent', label: 'Agent working' },
  { key: 'review', label: 'In review' },
  { key: 'proven', label: 'Proven' },
]
const LANE_LABEL = Object.fromEntries(LANES.map((l) => [l.key, l.label])) as Record<TaskState, string>
const shortName = (n: string) => n.split(/[:(]/)[0].trim()
const when = (iso: string) => new Date(iso).toLocaleString('en-GB', { day: 'numeric', month: 'short', hour: '2-digit', minute: '2-digit' })

function TaskCard({ t, onOpen }: { t: PlanTask; onOpen: () => void }) {
  const pct = t.progress.total ? Math.round((t.progress.done / t.progress.total) * 100) : 0
  return (
    <button type="button" className="pl-card" onClick={onOpen}>
      <span className="code">{t.controlId}</span>
      <span className="title">{t.title}</span>
      <span className="owner">{t.owner ?? (t.ownerSuggested ? `Suggested: ${t.ownerSuggested}` : 'No owner yet')}</span>
      {t.frameworks.length > 0 && (
        <span className="tags">
          {t.frameworks.map((f) => (
            <Token key={f} size="sm" label={shortName(f)} />
          ))}
        </span>
      )}
      {t.progress.total > 0 && (
        <span className="prog">
          <span className="bar" aria-hidden>
            <b style={{ width: `${pct}%` }} />
          </span>
          {t.progress.done} of {t.progress.total}
        </span>
      )}
    </button>
  )
}

function TaskDrawer({ t, tasks, onClose, board }: { t: PlanTask | null; tasks: PlanTask[]; onClose: () => void; board: ReturnType<typeof usePlanBoard> }) {
  const [owner, setOwner] = useState('')
  const [note, setNote] = useState<string | null>(null)
  const [statement, setStatement] = useState('')
  const [reference, setReference] = useState('')
  const [busy, setBusy] = useState(false)
  const [failure, setFailure] = useState<string | null>(null)
  const byKey = new Map(tasks.map((x) => [x.key, x]))

  const run = async (fn: () => Promise<unknown>) => {
    setBusy(true)
    setFailure(null)
    try {
      await fn()
    } catch (e) {
      setFailure(e instanceof Error ? e.message : 'Request failed')
    } finally {
      setBusy(false)
    }
  }
  const reset = () => {
    setOwner('')
    setNote(null)
    setStatement('')
    setReference('')
    setFailure(null)
  }
  const close = () => {
    reset()
    onClose()
  }
  const frameworks = t ? Array.from(new Set(t.requirements.map((r) => r.framework))) : []
  const noteValue = note ?? t?.note ?? ''
  const ownerValue = owner.trim() || (t && !t.owner ? t.ownerSuggested ?? '' : '')

  return (
    <Drawer isOpen={t !== null} onOpenChange={(o) => !o && close()} label={t ? `Task: ${t.title}` : 'Task'} width={500} padding={5}>
      {t && (
        <VStack gap={5}>
          <VStack gap={2} align="start">
            <Token size="sm" label={LANE_LABEL[t.state]} color={t.state === 'proven' ? 'green' : t.state === 'needs_you' ? 'orange' : 'gray'} />
            <Heading level={2}>{t.title}</Heading>
            <Text type="supporting">
              {t.controlId} · priority {t.priority}
            </Text>
            {t.objective && <Text color="secondary">{t.objective}</Text>}
          </VStack>

          <VStack gap={2}>
            <Heading level={3}>Owner</Heading>
            <Text>{t.owner ?? (t.ownerSuggested ? `Suggested: ${t.ownerSuggested}` : 'Nobody yet')}</Text>
            {t.ownerReason && <Text type="supporting">{t.ownerReason}</Text>}
            <HStack gap={2} vAlign="end">
              <TextInput label="Assign to" value={owner} onChange={setOwner} placeholder={t.ownerSuggested ?? 'Name or email'} onEnter={() => ownerValue && void run(() => board.update(t.key, { owner: ownerValue }).then(() => setOwner('')))} />
              <Button
                label={owner.trim() || t.owner ? 'Assign' : 'Accept suggestion'}
                variant="secondary"
                isDisabled={busy || !ownerValue}
                onClick={() => void run(() => board.update(t.key, { owner: ownerValue }).then(() => setOwner('')))}
              />
            </HStack>
          </VStack>

          <VStack gap={2}>
            <Heading level={3}>Note</Heading>
            <TextArea label="Note" isLabelHidden rows={3} value={noteValue} onChange={setNote} placeholder="Context for whoever picks this up" />
            <HStack>
              <Button label="Save note" variant="secondary" isDisabled={busy || note === null || note === (t.note ?? '')} onClick={() => void run(() => board.update(t.key, { note: noteValue }).then(() => setNote(null)))} />
            </HStack>
          </VStack>

          {t.systems.length > 0 ? (
            <VStack gap={2}>
              <Heading level={3}>
                Systems, {t.progress.done} of {t.progress.total} done
              </Heading>
              <ul className="pl-list">
                {t.systems.map((s) => (
                  <li key={s.id}>
                    <Link href={`/systems/${encodeURIComponent(s.id)}`}>
                      <span className="grow">{s.name}</span>
                      {s.agent && <Token size="sm" color="blue" label="Agent" />}
                      <small>{s.done ? 'Done' : s.detail}</small>
                    </Link>
                  </li>
                ))}
              </ul>
            </VStack>
          ) : (
            t.kind !== 'org' && (
              <Text color="secondary">
                No systems yet. It fills in as you <Link href="/discovery">find and register systems</Link>.
              </Text>
            )
          )}

          {t.dependsOn.length > 0 && (
            <VStack gap={2}>
              <Heading level={3}>Comes after</Heading>
              <ul className="pl-list">
                {t.dependsOn.map((k) => (
                  <li key={k}>
                    <span className="row">
                      <span className="grow">{byKey.get(k)?.title ?? k}</span>
                      <small>{byKey.get(k) ? LANE_LABEL[byKey.get(k)!.state] : ''}</small>
                    </span>
                  </li>
                ))}
              </ul>
            </VStack>
          )}

          {t.actions.length > 0 && (
            <VStack gap={2}>
              <Heading level={3}>How to do it</Heading>
              <ul className="pl-list">
                {t.actions.map((a) => (
                  <li key={a.id}>
                    <Link href={`/compliance/workflows/${encodeURIComponent(a.id)}`}>
                      <span className="grow">{a.name}</span>
                      <small>
                        {[a.scope, a.approver ? `approver: ${a.approver}` : '', a.installed ? '' : 'pack not installed yet'].filter(Boolean).join(' · ')}
                      </small>
                    </Link>
                  </li>
                ))}
              </ul>
            </VStack>
          )}

          {t.kind === 'org' && (
            <VStack gap={2}>
              <Heading level={3}>Already in place?</Heading>
              {t.attestation ? (
                <Text color="secondary">
                  Attested by {t.attestation.attested_by} on {when(t.attestation.created_at)}: &quot;{t.attestation.statement}&quot;
                  {t.attestation.reference ? ` (${t.attestation.reference})` : ''}. It counts as attested, not measured.
                </Text>
              ) : (
                <VStack gap={2}>
                  <TextArea label="What is in place, and since when" rows={2} value={statement} onChange={setStatement} description="At least 12 characters." />
                  <TextInput label="Where the evidence is" isOptional value={reference} onChange={setReference} placeholder="A link or document name" />
                  <HStack>
                    <Button label="Attest" variant="secondary" isDisabled={busy || statement.trim().length < 12} onClick={() => void run(() => board.attest(t.key, statement.trim(), reference.trim()))} />
                  </HStack>
                </VStack>
              )}
            </VStack>
          )}

          {frameworks.length > 0 && (
            <VStack gap={2}>
              <Heading level={3}>Requirements it closes, {t.requirements.length}</Heading>
              {frameworks.map((fw) => (
                <VStack key={fw} gap={1}>
                  <Text weight="semibold">{fw}</Text>
                  <ul className="pl-req">
                    {t.requirements
                      .filter((r) => r.framework === fw)
                      .slice(0, 12)
                      .map((r) => (
                        <li key={r.key}>
                          <span>{r.control}</span>
                          {r.title}
                        </li>
                      ))}
                  </ul>
                </VStack>
              ))}
            </VStack>
          )}

          {failure && <Banner status="error" title="Could not save" description={failure} />}
        </VStack>
      )}
    </Drawer>
  )
}

export default function PlanPage() {
  const board = usePlanBoard()
  const [openKey, setOpenKey] = useState<string | null>(null)
  const d = board.data

  if (!d) {
    return (
      <div className="fm-page">
        {board.error ? (
          <EmptyState title="The plan could not load" description={board.error} actions={<Button label="Try again" onClick={() => void board.reload()} />} />
        ) : (
          <VStack gap={3} aria-busy="true">
            <Skeleton height={36} />
            <Skeleton height={220} />
          </VStack>
        )}
      </div>
    )
  }

  if (!d.exists || d.status !== 'active') {
    return (
      <div className="fm-page">
        <VStack gap={5} className="pl-narrow">
          <VStack gap={1}>
            <Heading level={1}>Governance plan</Heading>
            <Text color="secondary">Answer a few questions and FairMind builds the plan: which controls apply, who owns them, and what proves each one.</Text>
          </VStack>
          <Card padding={5}>
            <Discovery d={d.discovery} onAnswer={board.answer} onGenerate={board.generate} />
          </Card>
        </VStack>
      </div>
    )
  }

  const tasks = d.tasks ?? []
  const open = tasks.find((t) => t.key === openKey) ?? null
  const proven = d.summary?.proven ?? 0
  const frameworks = d.discovery.map.frameworks

  return (
    <div className="fm-page">
      <VStack gap={5}>
        <HStack gap={4} hAlign="between" vAlign="end" wrap="wrap">
          <VStack gap={2}>
            {frameworks.length > 0 && <Text type="supporting">Governance plan · {frameworks.map((f) => shortName(f.name)).join(', ')}</Text>}
            <Heading level={1}>
              {proven} of {tasks.length} controls proven
            </Heading>
            <div style={{ width: 320, maxWidth: '100%' }}>
              <ProgressBar label="Controls proven" isLabelHidden value={proven} max={Math.max(tasks.length, 1)} />
            </div>
          </VStack>
          <HStack gap={4} wrap="wrap">
            {LANES.filter((l) => l.key !== 'proven').map((l) => (
              <Text key={l.key} color="secondary">
                {d.summary?.[l.key] ?? 0} {l.label.toLowerCase()}
              </Text>
            ))}
            <Button label="Refresh" variant="secondary" onClick={() => void board.reload()} />
          </HStack>
        </HStack>

        {d.changes && d.changes.length > 0 && <Banner status="info" title="What changed" description={`${d.changes[0].summary} (${when(d.changes[0].at)})`} />}

        <div className="pl-lanes">
          {LANES.map((l) => {
            const mine = tasks.filter((t) => t.state === l.key).sort((a, b) => a.priority - b.priority)
            return (
              <section key={l.key} className={`pl-lane ${l.key}`} aria-label={l.label}>
                <header>
                  <i aria-hidden />
                  <b>{l.label}</b>
                  <span>{mine.length}</span>
                </header>
                {mine.length === 0 && <div className="pl-empty">Nothing here.</div>}
                {mine.map((t) => (
                  <TaskCard key={t.key} t={t} onOpen={() => setOpenKey(t.key)} />
                ))}
              </section>
            )
          })}
        </div>
      </VStack>

      <TaskDrawer t={open} tasks={tasks} onClose={() => setOpenKey(null)} board={board} />
    </div>
  )
}
