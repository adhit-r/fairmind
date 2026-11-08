import assert from 'node:assert/strict'
import { test } from 'node:test'

import { apiClient } from '../api-client'
import { runHook, stub } from './runHookForTest'
import { GovernanceScopeMismatchError } from './useGovernanceAssurance'
import { useRemediation } from './useRemediation'

// useRemediation state order: tasks, loading, saving, error
const TASKS = 0
const ERROR = 3

function task(id: string, systemId: string) {
  return { id, systemId, title: 'Rebalance training data', status: 'open', priority: 'high' }
}

test('remediation tasks for another system surface as an error, never as data', async () => {
  const get = stub(apiClient, 'get', async () => ({
    success: true,
    data: { tasks: [task('task-1', 'system-1'), task('task-2', 'system-2')] },
  }))
  try {
    const { result, states } = runHook(() => useRemediation('system-1'))
    await result.refreshTasks()
    assert.ok(states[ERROR] instanceof GovernanceScopeMismatchError)
    assert.deepEqual(states[TASKS], [])
  } finally {
    get()
  }
})

test('matching remediation scope loads normally', async () => {
  const get = stub(apiClient, 'get', async () => ({ success: true, data: { tasks: [task('task-1', 'system-1')] } }))
  try {
    const { result, states } = runHook(() => useRemediation('system-1'))
    await result.refreshTasks()
    assert.equal(states[ERROR], null)
    assert.equal(states[TASKS].length, 1)
  } finally {
    get()
  }
})

test('created or updated remediation tasks for another system or record are rejected', async () => {
  const post = stub(apiClient, 'post', async () => ({ success: true, data: task('task-1', 'system-2') }))
  const patch = stub(apiClient, 'patch', async () => ({ success: true, data: task('task-other', 'system-1') }))
  try {
    const { result, states } = runHook(() => useRemediation('system-1'))
    await assert.rejects(result.createTask({ title: 'Fix', description: '', priority: 'high' }), /requested systemId/)
    assert.ok(states[ERROR] instanceof GovernanceScopeMismatchError)
    states[ERROR] = null
    await assert.rejects(result.updateTaskStatus('task-1', 'done'), /requested id/)
    assert.ok(states[ERROR] instanceof GovernanceScopeMismatchError)
    assert.deepEqual(states[TASKS], [])
  } finally {
    post()
    patch()
  }
})
