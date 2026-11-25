import assert from 'node:assert/strict'
import { test } from 'node:test'

import type { Controls, EstateGate } from '@/lib/api/hooks/useEstate'
import { evidenceGrid } from './grid'

const ISO = { key: 'ISO42001', name: 'ISO/IEC 42001:2023' }
const EU = { key: 'EUAIA', name: 'EU AI Act' }
const check = (key: EstateGate['checks'][number]['key'], evidenceClass: string | null, state: 'proven' | 'attested' | 'open' = 'proven') =>
  ({ key, label: key, state, confidence: 0.9, evidenceId: evidenceClass ? `ev-${key}` : null, evidenceClass })
const controls: Controls = {
  controls: [],
  crosswalk: [
    { commonControl: 'FMC-FAI-01', key: 'ISO42001|6.1', relation: 'Supports' },
    { commonControl: 'FMC-FAI-01', key: 'ISO42001|8.2', relation: 'Satisfies' },
    { commonControl: 'FMC-FAI-01', key: 'ISO42001|8.2', relation: 'Supports' },
    { commonControl: 'FMC-FAI-01', key: 'EUAIA|Art 10', relation: 'Partially satisfies' },
    { commonControl: 'FMC-FAI-01', key: 'EUAIA|Art 15', relation: 'Aligns with' },
    { commonControl: 'FMC-OVS-01', key: 'EUAIA|Art 14', relation: 'Aligns with' },
  ],
}
const systems = [
  { id: 'a', name: 'A', riskTier: 'high' as const },
  { id: 'b', name: 'B', riskTier: 'low' as const },
]
const gates = new Map([
  ['a', { checks: [check('fairness', 'measured'), check('human_oversight', 'manual', 'attested'), check('monitoring', null, 'open')] }],
  ['b', { checks: [check('fairness', 'measured')] }],
])
const confirmed = new Map([
  ['a', [ISO, EU]],
  ['b', [ISO]],
])

test('one row per check with an evidence class, grouped by system', () => {
  const g = evidenceGrid(systems, gates, controls, confirmed)
  assert.deepEqual(g.matrix.groups.map((x) => x.label), ['A · high', 'B · low'])
  assert.deepEqual(g.matrix.groups[0].rows.map((r) => r.code), ['FAIR', 'HUMN'])
  assert.equal(g.items, 3)
  assert.deepEqual(g.systemIds, ['a', 'b'])
  assert.deepEqual(g.frameworks.map((f) => f.key), ['ISO42001', 'EUAIA'])
})

test('a framework cell is the best relation; blank when unconfirmed or out of reach', () => {
  const g = evidenceGrid(systems, gates, controls, confirmed)
  const [fair, humn] = g.matrix.groups[0].rows
  assert.deepEqual(fair.cells, ['proven', 3, 2])
  // "Aligns with" draws blank
  assert.deepEqual(humn.cells, ['attested', null, null])
  const bFair = g.matrix.groups[1].rows[0]
  assert.deepEqual(bFair.cells, ['proven', 3, null])
  assert.equal((bFair.blank as string[])[2], 'Not confirmed for B')
})

test("the requirement count covers only the system's confirmed frameworks", () => {
  const g = evidenceGrid(systems, gates, controls, confirmed)
  assert.equal(g.matrix.groups[0].rows[0].count, 3)
  assert.equal(g.matrix.groups[0].rows[1].count, 0)
  assert.equal(g.matrix.groups[1].rows[0].count, 2)
  assert.deepEqual(g.touched('FMC-FAI-01', 'ISO42001').map((t) => [t.code, t.relation]), [['6.1', 'Supports'], ['8.2', 'Satisfies']])
})

test('no confirmed framework leaves only the Proof column', () => {
  const g = evidenceGrid(systems, gates, controls, new Map())
  assert.deepEqual(g.matrix.colGroups.map((c) => c.label), ['Proof'])
  assert.equal(g.matrix.groups[0].rows[0].count, 0)
})
