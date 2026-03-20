/**
 * Remediation API Hooks
 */

import { useCallback, useEffect, useMemo, useRef, useState } from 'react'

import { apiClient, type ApiResponse } from '../api-client'
import { API_ENDPOINTS } from '../endpoints'

export type RemediationPriority = 'low' | 'medium' | 'high' | 'critical'
export type RemediationStatus = 'open' | 'in_progress' | 'blocked' | 'done'
export type RetestStatus = 'not_started' | 'pending' | 'passed' | 'failed'

export interface RemediationTask {
  id: string
  systemId: string
  title: string
  description: string
  sourceType: string
  sourceId: string
  linkedRiskIds: string[]
  owner: string
  priority: RemediationPriority
  dueDate: string | null
  status: RemediationStatus
  retestRequired: boolean
  retestStatus: RetestStatus
  notes: string
  createdAt: string
  updatedAt: string
  riskId?: string
  source: 'risk' | 'manual'
  evidenceNeeded: string[]
  nextAction: string
}

export interface RemediationSummary {
  systemId: string
  total: number
  active: number
  completed: number
  retestRequiredTasks: number
  linkedRiskReferences: number
  byStatus: Record<string, number>
  byPriority: Record<string, number>
}

interface RemediationListResponse {
  tasks: RemediationTask[]
  summary: RemediationSummary
}

export interface CreateRemediationTaskInput {
  riskId?: string
  title: string
  description: string
  priority: RemediationPriority
  owner?: string
  evidenceNeeded?: string[]
}

const EMPTY_SUMMARY: RemediationSummary = {
  systemId: '',
  total: 0,
  active: 0,
  completed: 0,
  retestRequiredTasks: 0,
  linkedRiskReferences: 0,
  byStatus: {},
  byPriority: {},
}

function normalizeStringArray(value: unknown) {
  if (!Array.isArray(value)) {
    return []
  }

  return value.map((item) => String(item)).filter(Boolean)
}

function deriveEvidenceNeeded(notes: string) {
  return notes
    .split('\n')
    .map((entry) => entry.trim())
    .filter(Boolean)
}

function deriveNextAction(task: Pick<RemediationTask, 'status' | 'retestRequired' | 'retestStatus'>) {
  if (task.status === 'blocked') {
    return 'Remove the blocking dependency and move the task back into progress.'
  }

  if (task.status === 'in_progress') {
    return task.retestRequired && task.retestStatus !== 'passed'
      ? 'Finish the change, run the re-test, and attach the new result.'
      : 'Finish the change and record the closure evidence.'
  }

  if (task.status === 'done') {
    return task.retestRequired && task.retestStatus !== 'passed'
      ? 'Review whether approval can accept this without a passing re-test.'
      : 'Use the completed task as approval evidence.'
  }

  return 'Assign the owner and start the corrective action.'
}

function normalizeTask(task: Partial<RemediationTask>): RemediationTask {
  const linkedRiskIds = normalizeStringArray(task.linkedRiskIds)
  const notes = String(task.notes || '')
  const retestRequired = Boolean(task.retestRequired)
  const retestStatus = (task.retestStatus as RetestStatus) || 'not_started'
  const status = (task.status as RemediationStatus) || 'open'
  const sourceType = String(task.sourceType || 'manual')
  const riskId = linkedRiskIds[0] || (sourceType === 'risk' ? String(task.sourceId || '') : '')

  return {
    id: String(task.id || ''),
    systemId: String(task.systemId || ''),
    title: String(task.title || 'Untitled remediation task'),
    description: String(task.description || ''),
    sourceType,
    sourceId: String(task.sourceId || ''),
    linkedRiskIds,
    owner: String(task.owner || ''),
    priority: (task.priority as RemediationPriority) || 'medium',
    dueDate: task.dueDate ? String(task.dueDate) : null,
    status,
    retestRequired,
    retestStatus,
    notes,
    createdAt: String(task.createdAt || new Date().toISOString()),
    updatedAt: String(task.updatedAt || task.createdAt || new Date().toISOString()),
    riskId: riskId || undefined,
    source: sourceType === 'risk' ? 'risk' : 'manual',
    evidenceNeeded: deriveEvidenceNeeded(notes),
    nextAction: deriveNextAction({ status, retestRequired, retestStatus }),
  }
}

function sortTasks(tasks: RemediationTask[]) {
  const priorityRank: Record<RemediationPriority, number> = {
    critical: 4,
    high: 3,
    medium: 2,
    low: 1,
  }
  const statusRank: Record<RemediationStatus, number> = {
    blocked: 4,
    open: 3,
    in_progress: 2,
    done: 1,
  }

  return [...tasks].sort((left, right) => {
    const priorityDelta = priorityRank[right.priority] - priorityRank[left.priority]
    if (priorityDelta !== 0) {
      return priorityDelta
    }

    const statusDelta = statusRank[right.status] - statusRank[left.status]
    if (statusDelta !== 0) {
      return statusDelta
    }

    return new Date(right.updatedAt).getTime() - new Date(left.updatedAt).getTime()
  })
}

function buildSummary(systemId: string, tasks: RemediationTask[]): RemediationSummary {
  return tasks.reduce<RemediationSummary>(
    (accumulator, task) => {
      accumulator.total += 1
      accumulator.byStatus[task.status] = (accumulator.byStatus[task.status] || 0) + 1
      accumulator.byPriority[task.priority] = (accumulator.byPriority[task.priority] || 0) + 1
      accumulator.linkedRiskReferences += task.linkedRiskIds.length

      if (task.status === 'done') {
        accumulator.completed += 1
      } else {
        accumulator.active += 1
      }

      if (task.retestRequired) {
        accumulator.retestRequiredTasks += 1
      }

      return accumulator
    },
    {
      ...EMPTY_SUMMARY,
      systemId,
      byStatus: {},
      byPriority: {},
    }
  )
}

export function useRemediation(systemId?: string) {
  const [tasks, setTasks] = useState<RemediationTask[]>([])
  const [loading, setLoading] = useState(true)
  const [saving, setSaving] = useState(false)
  const [error, setError] = useState<Error | null>(null)
  const requestVersion = useRef(0)

  const loadTasks = useCallback(async (targetSystemId: string) => {
    const currentRequest = ++requestVersion.current

    setLoading(true)
    setError(null)

    try {
      const response: ApiResponse<RemediationListResponse> = await apiClient.get(
        `${API_ENDPOINTS.aiGovernance.remediation}?system_id=${encodeURIComponent(targetSystemId)}`
      )

      if (currentRequest !== requestVersion.current) {
        return
      }

      if (!response.success || !response.data) {
        throw new Error(response.error || 'Failed to load remediation tasks')
      }

      const normalizedTasks = sortTasks((response.data.tasks || []).map(normalizeTask))
      setTasks(normalizedTasks)
    } catch (err) {
      if (currentRequest !== requestVersion.current) {
        return
      }

      setTasks([])
      setError(err instanceof Error ? err : new Error('Unknown error'))
    } finally {
      if (currentRequest === requestVersion.current) {
        setLoading(false)
      }
    }
  }, [])

  useEffect(() => {
    if (!systemId) {
      requestVersion.current += 1
      setTasks([])
      setError(null)
      setLoading(false)
      return
    }

    void loadTasks(systemId)
  }, [loadTasks, systemId])

  const refreshTasks = useCallback(() => {
    if (!systemId) {
      requestVersion.current += 1
      setTasks([])
      setError(null)
      setLoading(false)
      return Promise.resolve()
    }

    return loadTasks(systemId)
  }, [loadTasks, systemId])

  const createTask = useCallback(
    async (input: CreateRemediationTaskInput) => {
      if (!systemId) {
        throw new Error('Select an AI system before creating remediation work')
      }

      if (!input.title.trim()) {
        throw new Error('Task title is required')
      }

      setSaving(true)
      setError(null)

      try {
        const response: ApiResponse<RemediationTask> = await apiClient.post(
          API_ENDPOINTS.aiGovernance.remediation,
          {
            system_id: systemId,
            title: input.title.trim(),
            description: input.description.trim(),
            source_type: input.riskId ? 'risk' : 'manual',
            source_id: input.riskId || '',
            linked_risk_ids: input.riskId ? [input.riskId] : [],
            owner: input.owner?.trim() || '',
            priority: input.priority,
            due_date: null,
            retest_required: true,
            notes: (input.evidenceNeeded || []).join('\n'),
          }
        )

        if (!response.success || !response.data) {
          throw new Error(response.error || 'Failed to create remediation task')
        }

        const nextTask = normalizeTask(response.data)
        setTasks((current) => sortTasks([nextTask, ...current.filter((task) => task.id !== nextTask.id)]))
        return nextTask
      } catch (err) {
        const nextError = err instanceof Error ? err : new Error('Failed to create remediation task')
        setError(nextError)
        throw nextError
      } finally {
        setSaving(false)
      }
    },
    [systemId]
  )

  const updateTaskStatus = useCallback(
    async (taskId: string, status: RemediationStatus, notes?: string) => {
      setSaving(true)
      setError(null)

      try {
        const response: ApiResponse<RemediationTask> = await apiClient.patch(
          API_ENDPOINTS.aiGovernance.updateRemediation(taskId),
          {
            status,
            ...(typeof notes === 'string' ? { notes } : {}),
          }
        )

        if (!response.success || !response.data) {
          throw new Error(response.error || 'Failed to update remediation task')
        }

        const nextTask = normalizeTask(response.data)
        setTasks((current) => sortTasks(current.map((task) => (task.id === taskId ? nextTask : task))))
        return nextTask
      } catch (err) {
        const nextError = err instanceof Error ? err : new Error('Failed to update remediation task')
        setError(nextError)
        throw nextError
      } finally {
        setSaving(false)
      }
    },
    []
  )

  const summary = useMemo(
    () => buildSummary(systemId || '', tasks),
    [systemId, tasks]
  )

  return {
    tasks,
    summary,
    loading,
    saving,
    error,
    createTask,
    updateTaskStatus,
    refreshTasks,
  }
}
