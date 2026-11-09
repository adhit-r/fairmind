import assert from 'node:assert/strict'
import { test } from 'node:test'

import type { Controls, FrameworkSystems } from '@/lib/api/hooks/useEstate'
import type { Journey, JourneyRequirement } from '@/lib/api/hooks/usePacks'
import { confirmedFrameworks, controlGrid, needsWorkInHighCritical, NOT_TRACKED, systemGrid } from './grid'

const req = (control: string, status: JourneyRequirement['status'] = 'gap'): JourneyRequirement => ({
  key: `FW|${control}`,
  control,
  title: `Requirement ${control}`,
  status,
  workflows: [],
  evaluations: [],
})
const journey: Journey = {
  key: 'FW',
  name: 'Framework',
  pillar: 'p',
  version: null,
  type: null,
  binding: null,
  status: null,
  active: 3,
  coveredAll: 0,
  coveredInstalled: 0,
  groups: [
    { name: 'Clause 1', requirements: [req('1.1', 'covered'), req('1.2')] },
    { name: 'Clause 2', requirements: [req('2.1', 'tested')] },
  ],
  steps: [],
}
const cell = (state: NonNullable<FrameworkSystems['requirements'][number]['cells'][number]>['state']) => ({ state, checks: [] })
const fw: FrameworkSystems = {
  framework: { key: 'FW', name: 'Framework' },
  systems: [
    { id: 'low-1', name: 'Low one', riskTier: 'low' },
    { id: 'crit-1', name: 'Critical one', riskTier: 'critical' },
  ],
  unconfirmed: 1,
  notInScope: 0,
  requirements: [
    { key: 'FW|1.1', cells: [cell('proven'), cell('open')] },
    { key: 'FW|2.1', cells: [cell('open'), cell('attested')] },
  ],
}

test('untracked requirements are hidden, then shown with a blank reason', () => {
  const hidden = systemGrid(journey, fw, false)
  assert.deepEqual(hidden.matrix.groups.flatMap((g) => g.rows.map((r) => r.key)), ['FW|1.1', 'FW|2.1'])
  assert.equal(hidden.tracked, 2)
  assert.equal(hidden.total, 3)
  const all = systemGrid(journey, fw, true)
  const untracked = all.matrix.groups[0].rows[1]
  assert.equal(untracked.key, 'FW|1.2')
  assert.deepEqual(untracked.cells, [null, null, null])
  assert.equal(untracked.blank, NOT_TRACKED)
})

test('columns run Org, then systems by tier from Critical down, with cells in that order', () => {
  const { matrix } = systemGrid(journey, fw, false)
  assert.deepEqual(matrix.colGroups.map((g) => g.label), ['Org', 'Critical', 'Low'])
  assert.deepEqual(matrix.groups[0].rows[0].cells, ['atorg', 'open', 'proven'])
  assert.deepEqual(matrix.groups[1].rows[0].cells, ['atorg', 'attested', 'open'])
})

test('the Proven count reads proven, estimated and attested over the systems in scope', () => {
  const { matrix } = systemGrid(journey, fw, false)
  assert.equal(matrix.groups[0].rows[0].count, '1/2')
  assert.equal(matrix.groups[1].rows[0].count, '1/2')
})

test('needs work in High and Critical counts requirements open, failing or stale in at least one such system', () => {
  assert.equal(needsWorkInHighCritical(fw), 1)
  assert.equal(needsWorkInHighCritical({ ...fw, systems: fw.systems.map((s) => ({ ...s, riskTier: 'low' as const })) }), 0)
  const worse = { ...fw, requirements: [{ key: 'FW|1.1', cells: [cell('open'), cell('fails')] }, { key: 'FW|2.1', cells: [cell('open'), cell('stale')] }] }
  assert.equal(needsWorkInHighCritical(worse), 2)
})

test('untracked rows carry no Proven count, and the footer totals only the rows drawn', () => {
  const hidden = systemGrid(journey, fw, false)
  assert.equal(hidden.totals.atorg, 2)
  const all = systemGrid(journey, fw, true)
  assert.equal(all.matrix.groups[0].rows[1].count, undefined)
  assert.equal(all.totals.atorg, 2)
  const covered = systemGrid({ ...journey, groups: [{ name: 'C', requirements: [req('1.1', 'covered'), req('1.2', 'covered')] }] }, fw, false)
  assert.equal(covered.totals.atorg, 1)
})

const controls: Controls = {
  controls: [
    { id: 'FMC-FAI-01', name: 'Fairness testing', objective: null, workflows: [] },
    { id: 'FMC-GOV-01', name: 'Scope', objective: null, workflows: [] },
    { id: 'FMC-FAI-02', name: 'Bias remediation', objective: null, workflows: [] },
    { id: 'FMC-MON-01', name: 'Monitoring', objective: null, workflows: [] },
    { id: 'FMC-RSK-01', name: 'Risk register', objective: null, workflows: [] },
  ],
  crosswalk: [
    { commonControl: 'FMC-FAI-01', key: 'FW|1.1', relation: 'Satisfies' },
    { commonControl: 'FMC-FAI-02', key: 'FW|1.2', relation: 'Partially satisfies' },
    { commonControl: 'FMC-GOV-01', key: 'FW|2.1', relation: 'Aligns with' },
    { commonControl: 'FMC-GOV-01', key: 'FW|1.2', relation: 'Supports' },
    { commonControl: 'FMC-FAI-01', key: 'FW|2.1', relation: 'Aligns with' },
    { commonControl: 'FMC-RSK-01', key: 'FW|2.1', relation: 'Aligns with' },
    { commonControl: 'FMC-MON-01', key: 'OTHER|1', relation: 'Satisfies' },
  ],
}

test('controls that touch no requirement of the framework, or only align with it, are dropped', () => {
  const g = controlGrid(journey, controls)
  assert.equal(g.used, 3)
  assert.equal(g.total, 5)
  const keys = g.matrix.colGroups.flatMap((x) => x.cols).map((c) => c.key)
  assert.ok(!keys.includes('FMC-MON-01'))
  assert.ok(!keys.includes('FMC-RSK-01'))
})

test('controls group by id family, labelled only when a family has two or more', () => {
  const g = controlGrid(journey, controls)
  assert.deepEqual(
    g.matrix.colGroups.map((x) => [x.label, x.cols.map((c) => c.key)]),
    [
      ['FAI', ['FMC-FAI-01', 'FMC-FAI-02']],
      ['', ['FMC-GOV-01']],
    ],
  )
})

test('Aligns with draws blank and names itself in the title', () => {
  const g = controlGrid(journey, controls)
  const row = g.matrix.groups[1].rows[0]
  assert.deepEqual(row.cells, [null, null, null])
  assert.deepEqual(row.blank, ['Aligns with', 'Not in the crosswalk', 'Aligns with'])
  assert.equal(row.count, 0)
  assert.deepEqual(g.matrix.groups[0].rows[0].cells, [3, null, null])
  assert.equal(g.matrix.groups[0].rows[0].count, 1)
  assert.deepEqual(g.matrix.groups[0].rows[1].cells, [null, 2, 1])
  assert.equal(g.relationOf('FW|2.1', 'FMC-GOV-01'), 'Aligns with')
  assert.equal(g.relationOf('FW|2.1', 'FMC-RSK-01'), 'Aligns with')
})

test('confirmed frameworks come from each system applicability, once each, in system order', () => {
  const sys = (fws: string[] | null) => ({ metadata: fws ? { applicability: { frameworks: fws.map((k) => ({ key: k, name: `${k} name` })) } } : {} })
  assert.deepEqual(confirmedFrameworks([sys(['B', 'A']), sys(null), sys(['A', 'C'])]).map((f) => f.key), ['B', 'A', 'C'])
})
