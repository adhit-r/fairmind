import assert from 'node:assert/strict'
import { test } from 'node:test'

import type { SystemChange } from '@/lib/api/hooks/useLifecycle'
import type { GateCheck } from '@/lib/api/hooks/useSystemFile'
import { columns } from './versions'

const check = (key: GateCheck['key'], state: GateCheck['state'], reopenedBy?: number): GateCheck =>
  ({ key, label: key, state, confidence: 0, evidenceId: null, detail: null, ...(reopenedBy ? { reopenedBy } : {}) })

const change = (number: number, over: Partial<SystemChange>): SystemChange => ({
  number, parts: ['data'], reopens: ['fairness'], material: true, fromVersion: null, toVersion: null, note: null,
  gateBefore: [{ key: 'fairness', label: 'Fairness', state: 'proven', confidence: 0.9 }], recordedBy: 'a', createdAt: '2026-11-01T00:00:00Z', seal: 'x', ...over,
})

test('each change adds the version before it, and the reopened check shows on the current column', () => {
  const cols = columns([change(1, { fromVersion: 'v2.1', toVersion: 'v2.2' })], [check('fairness', 'open', 1), check('monitoring', 'proven')], true)
  assert.deepEqual(cols.map((c) => [c.title, c.tone]), [['v2.1', 'old'], ['v2.2', 'wait']])
  assert.equal(cols[0].cells.fairness, 'proven')
  assert.equal(cols[1].cells.fairness, 'reopen')
  assert.equal(cols[1].cells.monitoring, 'proven')
  assert.equal(cols[1].pill?.label, 'Data')
})

test('a minor change leaves the current column live and keeps only the last four versions', () => {
  const many = [1, 2, 3, 4, 5].map((n) => change(n, { material: false, reopens: [], parts: ['docs'] }))
  const cols = columns(many, [check('fairness', 'proven')], true)
  assert.equal(cols.length, 4)
  assert.deepEqual(cols.at(-1), { key: 'now', title: 'Now', sub: 'Approved', tone: 'live', pill: { label: 'Docs or owner', material: false }, cells: { fairness: 'proven' } })
})
