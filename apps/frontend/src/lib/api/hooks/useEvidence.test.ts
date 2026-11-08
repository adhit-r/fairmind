import assert from 'node:assert/strict'
import { test } from 'node:test'

import { apiClient } from '../api-client'
import { runHook, stub } from './runHookForTest'
import { useEvidence } from './useEvidence'
import { GovernanceScopeMismatchError } from './useGovernanceAssurance'

// useEvidence state order: data, summary, dataSystemId, loading, collecting, error
const DATA = 0
const SUMMARY = 1
const ERROR = 5

function evidenceRecord(systemId: string) {
  return { id: `evidence-${systemId}`, systemId, timestamp: '2026-07-17T00:00:00Z', linkedEntities: [] }
}

function respondWith(records: unknown[], summarySystemId: string) {
  return stub(apiClient, 'get', async (url: string) => ({
    success: true,
    data: url.endsWith('/summary') ? { systemId: summarySystemId, totalEvidence: records.length } : records,
  }))
}

test('evidence records from another system surface as an error, never as data', async () => {
  const get = respondWith([evidenceRecord('system-1'), evidenceRecord('system-2')], 'system-1')
  try {
    const { result, states } = runHook(() => useEvidence('system-1'))
    await result.refreshEvidence()
    assert.ok(states[ERROR] instanceof GovernanceScopeMismatchError)
    assert.deepEqual(states[DATA], [])
  } finally {
    get()
  }
})

test('an evidence summary for another system surfaces as an error', async () => {
  const get = respondWith([evidenceRecord('system-1')], 'system-2')
  try {
    const { result, states } = runHook(() => useEvidence('system-1'))
    await result.refreshEvidence()
    assert.ok(states[ERROR] instanceof GovernanceScopeMismatchError)
    assert.deepEqual(states[DATA], [])
    assert.equal(states[SUMMARY].totalEvidence, 0)
  } finally {
    get()
  }
})

test('matching evidence scope loads normally', async () => {
  const get = respondWith([evidenceRecord('system-1')], 'system-1')
  try {
    const { result, states } = runHook(() => useEvidence('system-1'))
    await result.refreshEvidence()
    assert.equal(states[ERROR], null)
    assert.equal(states[DATA].length, 1)
    assert.equal(states[SUMMARY].totalEvidence, 1)
  } finally {
    get()
  }
})

test('collected or updated evidence for another system or record is rejected', async () => {
  const post = stub(apiClient, 'post', async () => ({ success: true, data: evidenceRecord('system-2') }))
  const patch = stub(apiClient, 'patch', async () => ({ success: true, data: evidenceRecord('system-1') }))
  try {
    const { result } = runHook(() => useEvidence('system-1'))
    await assert.rejects(
      result.collectEvidence({ systemId: 'system-1', type: 'document', content: {}, confidence: 1 }),
      /requested systemId/,
    )
    await assert.rejects(result.updateEvidence('evidence-other', { title: 'Model card' }), /requested id/)
  } finally {
    post()
    patch()
  }
})

test('an evidence link for another entity is rejected', async () => {
  const post = stub(apiClient, 'post', async () => ({
    success: true,
    data: { id: 'link-1', entityType: 'control', entityId: 'control-other' },
  }))
  try {
    const { result } = runHook(() => useEvidence('system-1'))
    await assert.rejects(result.addLink('evidence-system-1', 'control', 'control-1'), /requested entityId/)
  } finally {
    post()
  }
})

test('a summary reload for another system after a link surfaces as an error', async () => {
  const post = stub(apiClient, 'post', async () => ({
    success: true,
    data: { id: 'link-1', entityType: 'control', entityId: 'control-1' },
  }))
  const get = respondWith([], 'system-2')
  try {
    const { result, states } = runHook(() => useEvidence('system-1'))
    await result.addLink('evidence-system-1', 'control', 'control-1')
    await new Promise((resolve) => setTimeout(resolve, 0))
    assert.ok(states[ERROR] instanceof GovernanceScopeMismatchError)
    assert.equal(states[SUMMARY].totalEvidence, 0)
  } finally {
    post()
    get()
  }
})
