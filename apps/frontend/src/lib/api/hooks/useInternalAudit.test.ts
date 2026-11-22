import assert from 'node:assert/strict'
import { mock, test } from 'node:test'

import { apiClient } from '../api-client'
import { blockingConflict, canConclude, warningFor, canIssue, concludeCheck, createAudit, needsOverride, uploadPlan, type AreaView, type AuditView } from './useInternalAudit'

const area = (over: Partial<AreaView['area']> = {}) => ({ auditorId: 'u1', status: 'fieldwork', auditStatus: 'fieldwork', ...over }) as AreaView['area']

test('only the area auditor concludes, and only in fieldwork', () => {
  assert.equal(canConclude(area(), 'u1'), true)
  assert.equal(canConclude(area(), 'u2'), false)
  assert.equal(canConclude(area({ status: 'sent_to_lead' }), 'u1'), false)
  assert.equal(canConclude(area(), undefined), false)
})

test('only blocking conflicts are blocking; unverifiable is a warning', () => {
  const cs = [{ areaId: 'a', blocking: false, kind: 'unverifiable', detail: 'x' }, { areaId: 'b', blocking: true, detail: 'y' }]
  assert.equal(blockingConflict(cs, 'a'), undefined)
  assert.equal(warningFor(cs, 'a')?.kind, 'unverifiable')
  assert.equal(blockingConflict(cs, 'b')?.detail, 'y')
})

test('issue waits until every area is accepted', () => {
  const v = (statuses: string[]) => ({ audit: { status: 'fieldwork' }, areas: statuses.map((status) => ({ status })) }) as AuditView
  assert.equal(canIssue(v(['accepted', 'accepted'])), true)
  assert.equal(canIssue(v(['accepted', 'fieldwork'])), false)
  assert.equal(canIssue(v([])), false)
})

test('a grade other than the suggested one needs a reason', () => {
  assert.equal(needsOverride('major_nc', 'minor_nc'), true)
  assert.equal(needsOverride('minor_nc', 'minor_nc'), false)
  assert.equal(needsOverride('minor_nc', null), false)
})

test('create sends snake_case fields to the org-scoped path', async () => {
  const post = mock.method(apiClient, 'post', async () => ({ success: true, data: { id: 'a1' } }))
  try {
    await createAudit('org-1', { title: ' Q4 ', periodStart: '2026-07-01', periodEnd: '2026-09-30', leadAuditorId: 'u1' })
    const [url, body] = post.mock.calls[0].arguments as unknown as [string, Record<string, unknown>]
    assert.match(url, /\/internal-audits\?org_id=org-1$/)
    assert.equal(body.title, 'Q4')
    assert.equal(body.lead_auditor_id, 'u1')
    assert.equal('fieldwork_start' in body, false)
  } finally {
    post.mock.restore()
  }
})

test('plan upload posts multipart form data', async () => {
  const post = mock.method(apiClient, 'post', async () => ({ success: true, data: { areas: 1, checks: 2, unmatchedLines: [] } }))
  try {
    await uploadPlan('org-1', 'a 1', new File(['area'], 'plan.csv'))
    const [url, body] = post.mock.calls[0].arguments as unknown as [string, FormData]
    assert.match(url, /internal-audits\/a%201\/plan\?org_id=org-1$/)
    assert.ok(body instanceof FormData && body.get('file'))
  } finally {
    post.mock.restore()
  }
})

test('a failed conclude surfaces the server message', async () => {
  const post = mock.method(apiClient, 'post', async () => ({ success: false, error: 'Independence conflict' }))
  try {
    await assert.rejects(concludeCheck('org-1', 'c1', 'conformity', 's'), { message: 'Independence conflict' })
  } finally {
    post.mock.restore()
  }
})
