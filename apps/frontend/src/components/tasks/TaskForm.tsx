'use client'

import '@/astryx/pages/tasks.css'
import { useState } from 'react'
import { Banner } from '@astryxdesign/core/Banner'
import { Button } from '@astryxdesign/core/Button'
import { HStack, VStack } from '@astryxdesign/core/Layout'
import { Text } from '@astryxdesign/core/Text'
import { useOrg } from '@/context/OrgContext'
import { useMembers } from '@/astryx/data/settings'
import { useAgents, useTaskActions, type NewTask, type Task } from '@/lib/api/hooks/useTasks'

export const personName = (m: { name: string | null; email: string | null; user_id: string }) => m.name || m.email || m.user_id
export const initials = (text: string) =>
  text.split(/[\s@._-]+/).filter(Boolean).slice(0, 2).map((w) => w[0]!.toUpperCase()).join('') || '?'

/** Who a task can go to: active members, and the agents that can work on the task's system. */
export function useAssignees(systemId?: string | null) {
  const { selectedOrg } = useOrg()
  const members = useMembers(selectedOrg?.id)
  const agents = useAgents()
  const people = members.data.filter((m) => m.status === 'active').map((m) => ({ value: `user:${m.user_id}`, label: `${personName(m)} (${m.role})` }))
  const robots = systemId
    ? (agents.data ?? []).flatMap((a) => a.actions.map((x) => ({ value: `agent:${a.key}:${x.key}`, label: `${a.name}: ${x.label.split(' from ')[0].toLowerCase()}` })))
    : []
  return { options: [...people, ...robots], members: members.data, agents: agents.data ?? [] }
}

/** "user:<id>" or "agent:<key>:<action>" as the create/patch fields. */
export function assigneeFields(value: string): Pick<NewTask, 'assignee_user_id' | 'assignee_agent' | 'agent_action'> {
  if (value.startsWith('user:')) return { assignee_user_id: value.slice(5), assignee_agent: null, agent_action: null }
  if (value.startsWith('agent:')) {
    const [, agent, action] = value.split(':')
    return { assignee_user_id: null, assignee_agent: agent, agent_action: action }
  }
  return { assignee_user_id: null, assignee_agent: null, agent_action: null }
}

/** Create a task; `about` fixes what it is about (a requirement on a system, say) when it comes from another page. */
export function TaskForm({
  about,
  defaultTitle = '',
  onDone,
  onCancel,
}: {
  about?: Pick<NewTask, 'subject_type' | 'subject_id' | 'subject_label' | 'system_id'>
  defaultTitle?: string
  onDone: (task: Task) => void
  onCancel?: () => void
}) {
  const { create } = useTaskActions()
  const { options } = useAssignees(about?.system_id)
  const [title, setTitle] = useState(defaultTitle)
  const [assignee, setAssignee] = useState('')
  const [due, setDue] = useState('')
  const [priority, setPriority] = useState<'high' | 'medium' | 'low'>('medium')
  const [note, setNote] = useState('')
  const [notify, setNotify] = useState(true)
  const [busy, setBusy] = useState(false)
  const [failure, setFailure] = useState<string | null>(null)
  const toAgent = assignee.startsWith('agent:')

  async function submit() {
    setBusy(true)
    setFailure(null)
    const res = await create({ title: title.trim(), description: note, priority, due_date: due || null, notify, ...assigneeFields(assignee), ...about })
    setBusy(false)
    if (res.success && res.data) onDone(res.data)
    else setFailure(res.error || 'The task could not be created')
  }

  return (
    <VStack gap={3}>
      {about?.subject_label && (
        <span className="tk-about">
          <span className="tk-lab">About</span>
          <b>{about.subject_label}</b>
        </span>
      )}
      {failure && <Banner status="error" title={failure} />}
      <div className="tk-form">
        <label className="wide">
          Title
          <input className="tk-in" value={title} onChange={(e) => setTitle(e.target.value)} maxLength={300} />
        </label>
        <label>
          Assignee
          <select className="tk-in" value={assignee} onChange={(e) => setAssignee(e.target.value)}>
            <option value="">Nobody yet</option>
            {options.map((o) => (
              <option key={o.value} value={o.value}>{o.label}</option>
            ))}
          </select>
        </label>
        <label>
          Due
          <input className="tk-in" type="date" value={due} onChange={(e) => setDue(e.target.value)} />
        </label>
        <label>
          Priority
          <select className="tk-in" value={priority} onChange={(e) => setPriority(e.target.value as typeof priority)}>
            <option value="high">High</option>
            <option value="medium">Medium</option>
            <option value="low">Low</option>
          </select>
        </label>
        <label className="wide">
          Note
          <textarea className="tk-in" value={note} onChange={(e) => setNote(e.target.value)} placeholder="What good looks like, or where to start" />
        </label>
      </div>
      {toAgent ? (
        <Text type="supporting">The agent starts as soon as you create the task and reports back on it: done with the evidence, or blocked with why.</Text>
      ) : (
        assignee && (
          <label style={{ display: 'flex', gap: 8, alignItems: 'center', fontSize: 13 }}>
            <input type="checkbox" checked={notify} onChange={(e) => setNotify(e.target.checked)} /> Email them about it
          </label>
        )
      )}
      <HStack gap={2}>
        <Button label={busy ? (toAgent ? 'Agent working' : 'Creating') : 'Create task'} isDisabled={busy || !title.trim()} onClick={() => void submit()} />
        {onCancel && <Button variant="ghost" label="Cancel" onClick={onCancel} />}
      </HStack>
    </VStack>
  )
}
