import assert from 'node:assert/strict'
import { mock, test } from 'node:test'

import { apiClient } from '../api-client'
import { EMPTY_ANSWERS, acceptOverride, draftOf, shortFrameworkName, tierBasis, type ApplicabilityRecord, type ApplicabilitySuggestion } from './useApplicability'

const answered = { ...EMPTY_ANSWERS, use: 'credit', decidesAboutPeople: true, markets: ['IN' as const] }

const suggestion: ApplicabilitySuggestion = {
  rulesVersion: '2026-11.1',
  tier: 'high',
  tierRules: [{ id: 'T1', text: 'High-impact use.', cite: null }],
  frameworks: [
    { key: 'INDAI', name: 'India AI Governance Guidelines', available: true, rule: { id: 'F2', text: 'People in India are affected.' }, binding: 'Voluntary' },
    { key: 'NITI', name: 'NITI Aayog Responsible AI', available: false, rule: { id: 'F5', text: 'Applies in India.' }, binding: null },
  ],
  uses: [],
  rules: [],
}
const idle = { loading: false, failed: false }
const keep = { removed: [], added: [], reason: '' }

test('no body until use and decidesAboutPeople are answered', () => {
  const d = draftOf({ ...keep, answers: { ...EMPTY_ANSWERS, use: 'credit' }, tier: 'medium' }, { ...suggestion, tier: null }, idle)
  assert.equal(d.body, null)
  assert.equal(d.ready, false)
})

test('accepting the suggestion sends the available suggested frameworks and needs no reason', () => {
  const d = draftOf({ ...keep, answers: answered, tier: 'high' }, suggestion, idle)
  assert.equal(d.needsReason, false)
  assert.equal(d.ready, true)
  assert.deepEqual(d.body, { answers: answered, tier: 'high', frameworks: ['INDAI'] })
})

test('another tier needs a reason of 12 characters or more, sent trimmed', () => {
  const short = draftOf({ ...keep, answers: answered, tier: 'medium', reason: 'too short' }, suggestion, idle)
  assert.equal(short.needsReason, true)
  assert.equal(short.ready, false)
  const ok = draftOf({ ...keep, answers: answered, tier: 'medium', reason: '  reviewed by the credit committee ' }, suggestion, idle)
  assert.equal(ok.ready, true)
  assert.equal(ok.body?.reason, 'reviewed by the credit committee')
})

test('a reason left from an earlier change is not sent once the choice matches the suggestion', () => {
  const d = draftOf({ ...keep, answers: answered, tier: 'high', reason: 'reviewed by the credit committee' }, suggestion, idle)
  assert.equal(d.needsReason, false)
  assert.equal(d.body?.reason, undefined)
})

test('dropping a suggested framework needs a reason; added ones are appended once', () => {
  const d = draftOf({ answers: answered, tier: 'high', removed: ['INDAI'], added: ['EUAIA', 'EUAIA'], reason: '' }, suggestion, idle)
  assert.equal(d.needsReason, true)
  assert.deepEqual(d.frameworks, ['EUAIA'])
})

test('not ready while a suggestion is loading or after it failed', () => {
  assert.equal(draftOf({ ...keep, answers: answered, tier: 'high' }, suggestion, { loading: true, failed: false }).ready, false)
  const failed = draftOf({ ...keep, answers: answered, tier: 'high' }, suggestion, { loading: false, failed: true })
  assert.equal(failed.ready, false)
  assert.equal(failed.failed, true)
})

test('after a failed suggest nothing is sent, so no tier or framework comes from a stale or missing suggestion', () => {
  const failed = { loading: false, failed: true }
  // The last good suggestion is still in hand; the person changed an answer and that request failed.
  const stale = draftOf({ answers: answered, tier: 'medium', removed: [], added: ['EUAIA'], reason: 'reviewed by the credit committee' }, suggestion, failed)
  assert.equal(stale.body, null)
  assert.equal(stale.needsReason, false)
  // No suggestion ever loaded, answers prefilled from the record: still nothing to send.
  assert.equal(draftOf({ ...keep, answers: answered, tier: 'high' }, null, failed).body, null)
})

test('accepting a lower tier names the record the person is looking at', async () => {
  const post = mock.method(apiClient, 'post', async () => ({ success: true, data: { applicability: {}, gate: {} } }))
  try {
    await acceptOverride('sys-1', 'ev-42')
    const [url, body] = post.mock.calls[0].arguments as unknown as [string, unknown]
    assert.match(url, /\/systems\/sys-1\/applicability\/accept-override$/)
    assert.deepEqual(body, { evidenceId: 'ev-42' })
  } finally {
    post.mock.restore()
  }
})

test('a 409 from accepting a lower tier surfaces the server message', async () => {
  const message = 'The tier changed since you looked; review it again'
  const post = mock.method(apiClient, 'post', async () => ({ success: false, error: message }))
  try {
    await assert.rejects(acceptOverride('sys-1', 'ev-old'), { message })
  } finally {
    post.mock.restore()
  }
})

test('tier basis names the fired rules, or the reason when set by hand', () => {
  const record = { tier: 'high', suggestedTier: 'high', reason: null, tierRules: [{ id: 'T3', text: 'Decides about people.', cite: null }] } as unknown as ApplicabilityRecord
  assert.equal(tierBasis(null), 'Not confirmed')
  assert.equal(tierBasis(record), 'Rule T3: Decides about people.')
  assert.equal(tierBasis({ ...record, tier: 'medium', reason: 'Analyst reviews every case' }), 'Set by hand: Analyst reviews every case')
})

test('framework names are shortened to the part before a colon or bracket', () => {
  assert.equal(shortFrameworkName('RBI FREE-AI: Framework for Responsible and Ethical Enablement of AI in the Financial Sector'), 'RBI FREE-AI')
  assert.equal(shortFrameworkName('EU AI Act (Reg. 2024/1689) as amended by Digital Omnibus (Reg. 2026/1744)'), 'EU AI Act')
  assert.equal(shortFrameworkName('India AI Governance Guidelines'), 'India AI Governance Guidelines')
})
