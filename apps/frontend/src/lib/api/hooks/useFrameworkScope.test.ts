import assert from 'node:assert/strict'
import { mock, test } from 'node:test'

import { apiClient } from '../api-client'
import { acceptSure, confirmScope, nextItem, sortQueue, summaryLine, type ScopeItem, type ScopeView } from './useFrameworkScope'

const item = (systemId: string, over: Partial<ScopeItem> = {}): ScopeItem => ({
  systemId, systemName: systemId, source: 'github', verdict: 'in', reason: 'r', confidence: 'high', evidence: [],
  status: 'draft', decidedVerdict: null, decidedBy: null, decidedAt: null, evidenceId: null, ...over,
})
const view = (items: ScopeItem[], s: Partial<ScopeView['summary']> = {}): ScopeView => ({
  framework: { key: 'EUAIA', name: 'EU AI Act', test: { text: 't', version: '1' } },
  summary: { total: items.length, sure: 0, check: 0, waitingOwner: 0, confirmedIn: 0, confirmedOut: 0, ...s },
  items,
})

test('sortQueue puts sure drafts first, unsure and waiting next, confirmed last', () => {
  const sorted = sortQueue([
    item('conf', { status: 'confirmed' }),
    item('wait', { status: 'waiting_owner' }),
    item('unsure', { verdict: 'unsure' }),
    item('draft'),
  ])
  assert.deepEqual(sorted.map((i) => i.systemId), ['draft', 'wait', 'unsure', 'conf'])
})

test('nextItem moves past the current one, wraps, and ends at null', () => {
  const items = [item('a'), item('b', { status: 'confirmed' }), item('w', { status: 'waiting_owner' }), item('c')]
  assert.equal(nextItem(items)?.systemId, 'a')
  assert.equal(nextItem(items, 'a')?.systemId, 'c')
  assert.equal(nextItem(items, 'c')?.systemId, 'a')
  assert.equal(nextItem(items.map((i) => ({ ...i, status: 'confirmed' as const })), 'a'), null)
})

test('summaryLine reads the counts, and the confirmed line once every system is confirmed', () => {
  assert.equal(summaryLine(view([item('a'), item('b')])), 'We found 2 systems. The agent sorted them for this framework.')
  const done = view([item('a', { status: 'confirmed' })], { confirmedIn: 1, confirmedOut: 2, waitingOwner: 3 })
  assert.equal(summaryLine(done), 'Scope confirmed: 1 in scope, 2 out, 3 waiting on owner')
})

test('confirm posts the verdict and reason to the system path, org-scoped', async () => {
  const post = mock.method(apiClient, 'post', async () => ({ success: true, data: item('s 1') }))
  try {
    await confirmScope('EUAIA', 'org-1', 's 1', 'out', 'not used in the EU')
    const [url, body] = post.mock.calls[0].arguments as unknown as [string, unknown]
    assert.match(url, /\/frameworks\/EUAIA\/scope\/s%201\/confirm\?org_id=org-1$/)
    assert.deepEqual(body, { verdict: 'out', reason: 'not used in the EU' })
  } finally {
    post.mock.restore()
  }
})

test('a failed accept surfaces the server message', async () => {
  const post = mock.method(apiClient, 'post', async () => ({ success: false, error: 'Managers only' }))
  try {
    await assert.rejects(acceptSure('EUAIA', 'org-1'), { message: 'Managers only' })
  } finally {
    post.mock.restore()
  }
})
