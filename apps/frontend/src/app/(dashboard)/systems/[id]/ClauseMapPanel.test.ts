import assert from 'node:assert/strict'
import { test } from 'node:test'

import type { ClauseMap, ClauseMapFramework } from '@/lib/api/hooks/useSystemFile'
import { scopeLine } from './ClauseMapPanel'

const euaia: ClauseMapFramework = { key: 'EUAIA', name: 'EU AI Act (Reg. 2024/1689)', counts: { proven: 1, attested: 0, open: 2, total: 3 }, clauses: [] }
const atlas = { key: 'ATLAS', name: 'MITRE ATLAS: Adversarial Threat Landscape' }
const map = (frameworks: ClauseMapFramework[], confirmed: ClauseMap['confirmed'], scoped = true): ClauseMap => ({ verdict: null, confidence: null, frameworks, scoped, confirmed })

test('the scoped subtitle names every confirmed framework, including one with no mapped clause', () => {
  assert.equal(scopeLine(map([euaia], [{ key: 'EUAIA', name: euaia.name }, atlas])), 'For the frameworks this system answers to: EU AI Act, MITRE ATLAS.')
})

test('a scoped map with nothing mapped says so instead of disappearing', () => {
  assert.equal(scopeLine(map([], [atlas])), 'For the frameworks this system answers to: MITRE ATLAS. None of these frameworks map to the gate checks yet.')
})

test('an unscoped map has no scoped subtitle', () => {
  assert.equal(scopeLine(map([euaia], [], false)), null)
})
