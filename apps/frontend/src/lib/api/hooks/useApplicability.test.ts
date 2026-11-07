import assert from 'node:assert/strict'
import { test } from 'node:test'

import { EMPTY_ANSWERS, draftOf, tierBasis, type ApplicabilityRecord, type ApplicabilitySuggestion } from './useApplicability'

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
  assert.notEqual(failed.body, null)
})

test('tier basis names the fired rules, or the reason when set by hand', () => {
  const record = { tier: 'high', suggestedTier: 'high', reason: null, tierRules: [{ id: 'T3', text: 'Decides about people.', cite: null }] } as unknown as ApplicabilityRecord
  assert.equal(tierBasis(null), 'Not confirmed')
  assert.equal(tierBasis(record), 'Rule T3: Decides about people.')
  assert.equal(tierBasis({ ...record, tier: 'medium', reason: 'Analyst reviews every case' }), 'Set by hand: Analyst reviews every case')
})
