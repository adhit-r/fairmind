import assert from 'node:assert/strict'
import { test } from 'node:test'

import type { EstateGate } from '@/lib/api/hooks/useEstate'
import { estateGroups, estateNext, sinceLine } from './estate'

const STAGES = [
  { key: 'onboard', label: 'Onboard' },
  { key: 'assess', label: 'Assess' },
  { key: 'govern', label: 'Govern' },
  { key: 'remediate', label: 'Remediate' },
  { key: 'operate', label: 'Operate' },
]
type S = { id: string; name: string; stage: 'onboard' | 'assess' | 'govern' | 'remediate' | 'operate'; createdAt?: string }
const sys = (id: string, stage: S['stage'], createdAt?: string): S => ({ id, name: `System ${id}`, stage, createdAt })
const gate = (systemId: string, verdict: EstateGate['verdict'], confidence: number, checks: EstateGate['checks'] = []): EstateGate => ({
  systemId,
  verdict,
  confidence,
  band: 'unknown',
  approvalStatus: 'not_requested',
  checks,
})
const gates = (...g: EstateGate[]) => new Map(g.map((x) => [x.systemId, x]))

test('empty stage groups are dropped and labels carry the station number and count', () => {
  const groups = estateGroups([sys('a', 'govern'), sys('b', 'govern'), sys('c', 'operate')], new Map(), new Set(), STAGES)
  assert.deepEqual(groups.map((g) => g.label), ['03 Govern · 2', '06 Operate · 1'])
})

test('a system with a pending decision moves to Decision', () => {
  const groups = estateGroups([sys('a', 'govern'), sys('b', 'remediate')], new Map(), new Set(['b']), STAGES)
  assert.deepEqual(groups.map((g) => [g.key, g.systems.map((s) => s.id)]), [['govern', ['a']], ['decision', ['b']]])
  assert.deepEqual(estateGroups([sys('a', 'govern'), sys('b', 'remediate')], new Map(), new Set(['b']), STAGES, { filter: 'decision' }).map((g) => g.key), ['decision'])
})

test('sorting by confidence puts the weakest first within a group', () => {
  const groups = estateGroups([sys('a', 'govern'), sys('b', 'govern')], gates(gate('a', 'go', 0.9), gate('b', 'no_go', 0.2)), new Set(), STAGES, { sort: true })
  assert.deepEqual(groups[0].systems.map((s) => s.id), ['b', 'a'])
})

test('the next action is pending decisions, then the weakest No go, then nothing', () => {
  const systems = [sys('a', 'govern'), sys('b', 'remediate'), sys('c', 'operate')]
  const g = gates(gate('a', 'no_go', 0.4), gate('b', 'no_go', 0.1), gate('c', 'go', 0.9))
  const decide = estateNext(systems, g, new Set(['c']))
  assert.equal(decide.title, '1 decision waits for you')
  assert.equal(decide.primary?.href, '/systems/c')
  const raise = estateNext(systems, g, new Set())
  assert.equal(raise.title, 'Raise System b from No go')
  assert.equal(raise.stage, 'remediate')
  assert.deepEqual(estateNext([systems[2]], g, new Set()), { title: 'Nothing needs you' })
})

const stale: EstateGate['checks'][number] = { key: 'monitoring', label: 'Monitoring', state: 'open', confidence: 0, evidenceId: null, evidenceClass: null, stale: true }

test('sinceLine is null with no earlier visit or no change', () => {
  assert.equal(sinceLine(null, [sys('a', 'govern', '2026-11-08T10:00:00Z')], new Map(), []), null)
  assert.equal(sinceLine('2026-11-09T00:00:00Z', [sys('a', 'govern', '2026-11-08T10:00:00Z')], new Map(), []), null)
})

test('sinceLine counts new systems, lapsed monitoring and agent finds since the last visit', () => {
  const s = sinceLine(
    '2026-11-08T18:20:00Z',
    [sys('a', 'govern', '2026-11-09T08:00:00Z'), sys('b', 'operate', '2026-10-01T00:00:00Z')],
    gates(gate('b', 'no_go', 0.5, [stale])),
    [
      { id: 'd1', name: 'Ranker', source: 'mlflow', discoveredAt: '2026-11-09T07:00:00Z' },
      { id: 'd2', name: 'Old find', source: 'github', discoveredAt: '2026-11-01T07:00:00Z' },
    ],
  )
  assert.deepEqual(s?.parts, ['1 new system', '1 monitoring check lapsed', '1 found by the agent'])
  assert.deepEqual(s?.rows.map((r) => r.key), ['new:a', 'lapsed:b', 'found:d1'])
})

test('a lapse seen at the last dismissal does not bring the line back', () => {
  const g = gates(gate('b', 'no_go', 0.5, [stale]))
  assert.equal(sinceLine('2026-11-08T18:20:00Z', [sys('b', 'operate')], g, [], ['b']), null)
  assert.deepEqual(sinceLine('2026-11-08T18:20:00Z', [sys('b', 'operate')], g, [])?.parts, ['1 monitoring check lapsed'])
})
