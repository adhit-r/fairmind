'use client'

import { useOrg } from '@/context/OrgContext'
import { apiClient } from '../api-client'
import { useOrgResource, withOrg } from './usePacks'

export type TaskStatus = 'open' | 'in_progress' | 'blocked' | 'done'
export type TaskPriority = 'high' | 'medium' | 'low'
export type SubjectType = 'requirement' | 'system' | 'finding' | 'source' | 'none'

export interface Task {
  id: string
  number: number
  title: string
  description: string
  status: TaskStatus
  priority: TaskPriority
  assigneeUserId: string | null
  assigneeAgent: string | null
  agentAction: string | null
  createdBy: string
  dueDate: string | null
  subject: { type: SubjectType; id: string | null; label: string | null }
  systemId: string | null
  createdAt: string
  updatedAt: string
  completedAt: string | null
}

export interface TaskDetail extends Task {
  comments: Array<{ id: string; author: string; body: string; createdAt: string }>
  events: Array<{ actor: string; kind: string; detail: Record<string, string | null>; createdAt: string }>
}

export interface Agent {
  key: string
  name: string
  actions: Array<{ key: string; label: string }>
}

export interface NewTask {
  title: string
  description?: string
  priority?: TaskPriority
  due_date?: string | null
  assignee_user_id?: string | null
  assignee_agent?: string | null
  agent_action?: string | null
  subject_type?: SubjectType
  subject_id?: string | null
  subject_label?: string | null
  system_id?: string | null
  notify?: boolean
}

export type TaskPatch = Partial<Pick<NewTask, 'title' | 'description' | 'priority' | 'due_date' | 'assignee_user_id' | 'assignee_agent' | 'agent_action'>> & {
  status?: TaskStatus
}

const TASKS = '/api/v1/tasks'
const query = (params: Record<string, string | undefined>) => {
  const q = Object.entries(params).filter(([, v]) => v).map(([k, v]) => `${k}=${encodeURIComponent(v!)}`).join('&')
  return q ? `?${q}` : ''
}

/** Tasks in the selected organisation; `mine` keeps the caller's, `status` 'open' hides done ones. */
export const useTasks = (params: { mine?: boolean; status?: string; subject_type?: SubjectType; system_id?: string } = {}) =>
  useOrgResource<{ tasks: Task[] }>(
    `${TASKS}${query({ mine: params.mine ? 'true' : undefined, status: params.status, subject_type: params.subject_type, system_id: params.system_id })}`,
  )
export const useTask = (id: string | null) => useOrgResource<TaskDetail>(id ? `${TASKS}/${encodeURIComponent(id)}` : null)
export const useAgents = () => useOrgResource<Agent[]>(`${TASKS}/agents`)

/** Writes against the selected organisation; each returns the client's { success, data, error }. */
export function useTaskActions() {
  const { selectedOrg } = useOrg()
  const scoped = (path: string) => withOrg(path, selectedOrg?.id ?? '')
  return {
    create: (body: NewTask) => apiClient.post<Task>(scoped(TASKS), body, { enableRetry: false }),
    update: (id: string, body: TaskPatch) => apiClient.patch<Task>(scoped(`${TASKS}/${encodeURIComponent(id)}`), body, { enableRetry: false }),
    comment: (id: string, body: string) => apiClient.post(scoped(`${TASKS}/${encodeURIComponent(id)}/comments`), { body }, { enableRetry: false }),
    runAgent: (id: string) => apiClient.post<Task>(scoped(`${TASKS}/${encodeURIComponent(id)}/run`), {}, { enableRetry: false }),
  }
}
