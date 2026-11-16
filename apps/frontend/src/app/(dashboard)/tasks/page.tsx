'use client'

import '@/astryx/pages/frameworks.css'
import '@/astryx/pages/tasks.css'
import Link from 'next/link'
import { useRouter, useSearchParams } from 'next/navigation'
import { Suspense, useMemo, useState } from 'react'
import { Banner } from '@astryxdesign/core/Banner'
import { Button } from '@astryxdesign/core/Button'
import { EmptyState } from '@astryxdesign/core/EmptyState'
import { HStack, VStack } from '@astryxdesign/core/Layout'
import { Skeleton } from '@astryxdesign/core/Skeleton'
import { Heading, Text } from '@astryxdesign/core/Text'
import { useSession } from '@/context/SessionContext'
import { useOrg } from '@/context/OrgContext'
import { TaskForm, assigneeFields, initials, personName, useAssignees } from '@/components/tasks/TaskForm'
import { useTask, useTaskActions, useTasks, type Task, type TaskStatus } from '@/lib/api/hooks/useTasks'

type View = 'mine' | 'team' | 'done'
const STATUS_LABEL: Record<TaskStatus, string> = { open: 'Open', in_progress: 'In progress', blocked: 'Blocked', done: 'Done' }
const PRIORITY_LABEL = { high: 'High', medium: 'Medium', low: 'Low' } as const
const SUBJECT_LABEL: Record<string, string> = { requirement: 'Requirement', system: 'AI system', finding: 'Finding', source: 'Source', none: 'Task' }

const today = () => new Date().toISOString().slice(0, 10)
const inDays = (n: number) => new Date(Date.now() + n * 86_400_000).toISOString().slice(0, 10)
const dueLabel = (d: string | null) => (d ? new Date(`${d}T00:00:00`).toLocaleDateString(undefined, { day: 'numeric', month: 'short' }) : 'None')
const isLate = (t: Task) => t.status !== 'done' && !!t.dueDate && t.dueDate < today()

/** Overdue, due this week, later, no date: the order a person works through their list. */
function bucket(t: Task): string {
  if (!t.dueDate) return 'No due date'
  if (isLate(t)) return 'Overdue'
  return t.dueDate <= inDays(7) ? 'Due this week' : 'Later'
}
const BUCKETS = ['Overdue', 'Due this week', 'Later', 'No due date']

function useNames() {
  const { members, agents } = useAssignees()
  return useMemo(() => {
    const people = new Map(members.map((m) => [m.user_id, personName(m)]))
    const robots = new Map(agents.map((a) => [a.key, a.name]))
    return {
      of: (id: string | null | undefined) => (!id ? 'Nobody' : id.startsWith('agent:') ? robots.get(id.slice(6)) ?? 'An agent' : people.get(id) ?? 'A former member'),
      assignee: (t: Task) => (t.assigneeAgent ? robots.get(t.assigneeAgent) ?? t.assigneeAgent : t.assigneeUserId ? people.get(t.assigneeUserId) ?? 'A former member' : null),
    }
  }, [members, agents])
}

function Avatar({ task, names }: { task: Task; names: ReturnType<typeof useNames> }) {
  const who = names.assignee(task)
  if (task.assigneeAgent) return <span className="tk-av agent" title={`Assigned to ${who}`} aria-label={`Assigned to ${who}`}>AI</span>
  if (!who) return <span className="tk-av none" title="Not assigned" aria-label="Not assigned">?</span>
  return <span className="tk-av" title={`Assigned to ${who}`} aria-label={`Assigned to ${who}`}>{initials(who)}</span>
}

function TaskList({ tasks, current, onPick, names }: { tasks: Task[]; current: string | null; onPick: (id: string) => void; names: ReturnType<typeof useNames> }) {
  const groups = BUCKETS.map((b) => ({ b, rows: tasks.filter((t) => bucket(t) === b) })).filter((g) => g.rows.length)
  return (
    <section className="fm-card" style={{ padding: 0, overflow: 'hidden' }} aria-label="Tasks">
      {groups.map((g) => (
        <div key={g.b}>
          <div className={`tk-grp${g.b === 'Overdue' ? ' late' : ''}`}>
            <span>
              {g.b} · {g.rows.length}
            </span>
          </div>
          {g.rows.map((t) => (
            <button key={t.id} type="button" className="tk-row" aria-current={t.id === current ? 'true' : undefined} onClick={() => onPick(t.id)}>
              <span className={`tk-st ${t.status}`} role="img" aria-label={STATUS_LABEL[t.status]} />
              <span style={{ minWidth: 0 }}>
                <span className="t">{t.title}</span>
                <span className="s">
                  <b>{SUBJECT_LABEL[t.subject.type]}</b> {t.subject.label ?? ''}
                </span>
              </span>
              <span className={`tk-due${isLate(t) ? ' late' : ''}`}>{dueLabel(t.dueDate)}</span>
              <span className={`tk-pri ${t.priority}`}>{PRIORITY_LABEL[t.priority]}</span>
              <Avatar task={t} names={names} />
            </button>
          ))}
        </div>
      ))}
    </section>
  )
}

function TaskPanel({ id, onChanged, names }: { id: string; onChanged: () => void; names: ReturnType<typeof useNames> }) {
  const task = useTask(id)
  const { update, comment, runAgent } = useTaskActions()
  const { options } = useAssignees(task.data?.systemId)
  const me = useSession().user
  const { selectedOrg } = useOrg()
  const [draft, setDraft] = useState('')
  const [busy, setBusy] = useState<string | null>(null)
  const [failure, setFailure] = useState<string | null>(null)
  const t = task.data
  const canEdit = selectedOrg?.role === 'owner' || selectedOrg?.role === 'admin' || selectedOrg?.role === 'editor'
  const isMine = !!t && t.assigneeUserId === me?.id

  async function act(key: string, call: () => Promise<{ success: boolean; error?: string }>) {
    setBusy(key)
    setFailure(null)
    const res = await call()
    setBusy(null)
    if (!res.success) setFailure(res.error || 'That did not work')
    task.reload()
    onChanged()
  }

  if (task.loading && !t) return <Skeleton height={420} />
  if (!t) return <EmptyState title="This task could not load" description={task.error ?? 'It may have been removed.'} />
  const assigneeValue = t.assigneeAgent ? `agent:${t.assigneeAgent}:${t.agentAction}` : t.assigneeUserId ? `user:${t.assigneeUserId}` : ''

  return (
    <aside className="fm-card tk-panel" aria-labelledby="tk-title">
      <HStack gap={2} hAlign="between" vAlign="center">
        <Text type="supporting">
          Task {t.number} · created by {names.of(t.createdBy)} on {new Date(t.createdAt).toLocaleDateString()}
        </Text>
        {t.status !== 'done' && (canEdit || isMine) && (
          <Button size="sm" label={busy === 'done' ? 'Saving' : 'Mark done'} onClick={() => void act('done', () => update(t.id, { status: 'done' }))} />
        )}
      </HStack>
      <Heading level={2} id="tk-title">{t.title}</Heading>
      {failure && <Banner status="error" title={failure} />}
      <dl className="tk-kv">
        <dt>Status</dt>
        <dd>
          <select className="tk-in" aria-label="Status" value={t.status} disabled={!canEdit && !isMine} onChange={(e) => void act('status', () => update(t.id, { status: e.target.value as TaskStatus }))}>
            {Object.entries(STATUS_LABEL).map(([v, l]) => <option key={v} value={v}>{l}</option>)}
          </select>
        </dd>
        <dt>Assignee</dt>
        <dd>
          <select className="tk-in" aria-label="Assignee" value={assigneeValue} disabled={!canEdit} onChange={(e) => void act('assign', () => update(t.id, assigneeFields(e.target.value)))}>
            <option value="">Nobody yet</option>
            {options.map((o) => <option key={o.value} value={o.value}>{o.label}</option>)}
            {assigneeValue && !options.some((o) => o.value === assigneeValue) && <option value={assigneeValue}>{names.assignee(t)}</option>}
          </select>
        </dd>
        <dt>Due</dt>
        <dd>
          <input className="tk-in" type="date" aria-label="Due date" value={t.dueDate ?? ''} disabled={!canEdit} onChange={(e) => void act('due', () => update(t.id, { due_date: e.target.value || '' }))} />
        </dd>
        <dt>Priority</dt>
        <dd>
          <select className="tk-in" aria-label="Priority" value={t.priority} disabled={!canEdit} onChange={(e) => void act('priority', () => update(t.id, { priority: e.target.value as Task['priority'] }))}>
            {Object.entries(PRIORITY_LABEL).map(([v, l]) => <option key={v} value={v}>{l}</option>)}
          </select>
        </dd>
      </dl>
      {t.subject.type !== 'none' && (
        <Link className="tk-about" href={t.systemId ? `/systems/${encodeURIComponent(t.systemId)}` : '#'}>
          <span className="tk-lab">About</span>
          <b>{t.subject.label ?? SUBJECT_LABEL[t.subject.type]}</b>
        </Link>
      )}
      {t.assigneeAgent && canEdit && (
        <Button variant="secondary" size="sm" label={busy === 'run' ? 'Agent working' : 'Run the agent again'} isDisabled={busy !== null} onClick={() => void act('run', () => runAgent(t.id))} />
      )}
      {t.description && (
        <div>
          <span className="tk-lab">Description</span>
          <Text>{t.description}</Text>
        </div>
      )}
      <div>
        <span className="tk-lab">Comments</span>
        <VStack gap={3}>
          {t.comments.length === 0 && <Text type="supporting">No comments yet.</Text>}
          {t.comments.map((c) => {
            const who = names.of(c.author)
            return (
              <div key={c.id} className="tk-cm">
                <span className={`tk-av${c.author.startsWith('agent:') ? ' agent' : ''}`} aria-hidden="true">{c.author.startsWith('agent:') ? 'AI' : initials(who)}</span>
                <div>
                  <b>{who}</b> <Text type="supporting">{new Date(c.createdAt).toLocaleString()}</Text>
                  <p>{c.body}</p>
                </div>
              </div>
            )
          })}
          <HStack gap={2} vAlign="end">
            <textarea className="tk-in" aria-label="Comment" value={draft} onChange={(e) => setDraft(e.target.value)} placeholder="Write a comment" style={{ minHeight: 40 }} />
            <Button variant="secondary" size="sm" label="Send" isDisabled={!draft.trim() || busy !== null} onClick={() => void act('comment', async () => { const r = await comment(t.id, draft.trim()); if (r.success) setDraft(''); return r })} />
          </HStack>
        </VStack>
      </div>
      <div>
        <span className="tk-lab">Activity</span>
        <ul className="tk-act">
          {t.events.map((e, i) => (
            <li key={i}>
              <b>{names.of(e.actor)}</b>{' '}
              {e.kind === 'created' ? 'created it' : e.kind === 'assigned' ? `assigned it to ${names.of(e.detail.to)}` : e.kind === 'status' ? `set status to ${STATUS_LABEL[(e.detail.to ?? 'open') as TaskStatus]}` : e.kind === 'due' ? `set the due date to ${dueLabel(e.detail.to ?? null)}` : `set priority to ${e.detail.to}`}{' '}
              · {new Date(e.createdAt).toLocaleDateString()}
            </li>
          ))}
        </ul>
      </div>
    </aside>
  )
}

function Team({ tasks, names, onPick }: { tasks: Task[]; names: ReturnType<typeof useNames>; onPick: (id: string) => void }) {
  const rows = useMemo(() => {
    const by = new Map<string, Task[]>()
    for (const t of tasks) {
      const key = t.assigneeAgent ? `agent:${t.assigneeAgent}` : t.assigneeUserId ?? ''
      by.set(key, [...(by.get(key) ?? []), t])
    }
    return [...by.entries()].sort((a, b) => (a[0] === '' ? -1 : b[0] === '' ? 1 : b[1].length - a[1].length))
  }, [tasks])
  const [open, setOpen] = useState<string | null>(null)
  return (
    <section className="fm-card fx-scroll" style={{ padding: 0 }} aria-label="Open tasks by person">
      <table className="fx-table" style={{ width: '100%', borderCollapse: 'collapse' }}>
        <thead>
          <tr>
            <th scope="col" style={{ padding: '16px 14px 10px 20px', textAlign: 'start' }}>Person</th>
            <th scope="col" style={{ textAlign: 'start' }}>Open</th>
            <th scope="col" style={{ textAlign: 'start' }}>Overdue</th>
            <th scope="col" style={{ textAlign: 'start' }}>Due this week</th>
            <th scope="col" style={{ textAlign: 'start' }}>Load</th>
            <th scope="col"><span className="sr-only">Show tasks</span></th>
          </tr>
        </thead>
        <tbody>
          {rows.map(([key, list]) => {
            const late = list.filter(isLate).length
            const week = list.filter((t) => bucket(t) === 'Due this week').length
            const who = key === '' ? 'Not assigned' : names.of(key)
            return [
              <tr key={key}>
                <td style={{ padding: '12px 14px 12px 20px' }}>
                  <HStack gap={2} vAlign="center">
                    <span className={`tk-av${key.startsWith('agent:') ? ' agent' : key === '' ? ' none' : ''}`} aria-hidden="true">{key.startsWith('agent:') ? 'AI' : key === '' ? '?' : initials(who)}</span>
                    <b>{who}</b>
                  </HStack>
                </td>
                <td>{list.length}</td>
                <td style={late ? { color: '#b42318', fontWeight: 600 } : undefined}>{late}</td>
                <td>{week}</td>
                <td>
                  <div className="tk-load" role="img" aria-label={`${late} overdue, ${week} due this week, ${list.length - late - week} later`}>
                    {late > 0 && <i className="late" style={{ flex: late }} />}
                    {week > 0 && <i className="week" style={{ flex: week }} />}
                    {list.length - late - week > 0 && <i className="later" style={{ flex: list.length - late - week }} />}
                  </div>
                </td>
                <td style={{ paddingRight: 20, textAlign: 'end' }}>
                  <Button size="sm" variant="secondary" label={open === key ? 'Hide' : 'Show'} onClick={() => setOpen(open === key ? null : key)} />
                </td>
              </tr>,
              open === key && (
                <tr key={`${key}-list`}>
                  <td colSpan={6} style={{ padding: 0 }}>
                    <TaskList tasks={list} current={null} onPick={onPick} names={names} />
                  </td>
                </tr>
              ),
            ]
          })}
        </tbody>
      </table>
    </section>
  )
}

function TasksPage() {
  const params = useSearchParams()
  const router = useRouter()
  const view = (params.get('view') as View) || 'mine'
  const current = params.get('task')
  const { selectedOrg } = useOrg()
  const canCreate = selectedOrg?.role === 'owner' || selectedOrg?.role === 'admin' || selectedOrg?.role === 'editor'
  const mine = useTasks({ mine: true, status: 'open' })
  const team = useTasks({ status: 'open' })
  const done = useTasks({ status: 'done' })
  const names = useNames()
  const [creating, setCreating] = useState(false)
  const go = (next: { view?: View; task?: string | null }) => {
    const q = new URLSearchParams()
    q.set('view', next.view ?? view)
    const task = next.task === undefined ? current : next.task
    if (task) q.set('task', task)
    router.replace(`/tasks?${q.toString()}`)
  }
  const reloadAll = () => { mine.reload(); team.reload(); done.reload() }
  const source = view === 'mine' ? mine : view === 'team' ? team : done
  const list = source.data?.tasks ?? []

  return (
    <div className="fm-page">
      <VStack gap={5}>
        <HStack gap={3} hAlign="between" vAlign="end" wrap="wrap">
          <VStack gap={1}>
            <Heading level={1}>Tasks</Heading>
            <Text color="secondary">Work assigned to people and agents in {selectedOrg?.name ?? 'your organisation'}. Each task points at what it is about.</Text>
          </VStack>
          <HStack gap={2} vAlign="center">
            <nav className="fx-chips" aria-label="View">
              {(['mine', 'team', 'done'] as View[]).map((v) => (
                <Link key={v} className="fx-chip" href={`/tasks?view=${v}`} aria-current={v === view ? 'true' : undefined}>
                  {v === 'mine' ? 'My tasks' : v === 'team' ? 'Team' : 'Done'}
                  <span>{(v === 'mine' ? mine : v === 'team' ? team : done).data?.tasks.length ?? ''}</span>
                </Link>
              ))}
            </nav>
            {canCreate && <Button label="New task" onClick={() => setCreating(true)} />}
          </HStack>
        </HStack>

        {creating && (
          <section className="fm-card" aria-label="New task">
            <TaskForm onDone={(t) => { setCreating(false); reloadAll(); go({ task: t.id }) }} onCancel={() => setCreating(false)} />
          </section>
        )}

        {source.loading && !source.data ? (
          <Skeleton height={300} />
        ) : source.error ? (
          <EmptyState title="Tasks could not load" description={source.error} actions={<Button label="Try again" onClick={() => source.reload()} />} />
        ) : list.length === 0 ? (
          <EmptyState
            title={view === 'mine' ? 'Nothing assigned to you' : view === 'team' ? 'No open tasks' : 'Nothing done yet'}
            description="Tasks come from the Needs work queue on a framework, or from New task. Assign them to a person or to an agent."
            actions={<Button variant="secondary" label="Open Frameworks" href="/frameworks" />}
          />
        ) : (
          <div className="tk-cols">
            {view === 'team' ? <Team tasks={list} names={names} onPick={(id) => go({ task: id })} /> : <TaskList tasks={list} current={current} onPick={(id) => go({ task: id })} names={names} />}
            {current ? <TaskPanel key={current} id={current} onChanged={reloadAll} names={names} /> : <span />}
          </div>
        )}
      </VStack>
    </div>
  )
}

export default function Page() {
  return (
    <Suspense fallback={null}>
      <TasksPage />
    </Suspense>
  )
}
