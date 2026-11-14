import assert from 'node:assert/strict'
import { test } from 'node:test'

import type { Journey, JourneyRequirement } from '@/lib/api/hooks/usePacks'
import type { ClauseMap } from '@/lib/api/hooks/useSystemFile'
import { requirementsGrid } from './RequirementsTab'

const wf = (pack: string, relation: string) => ({ id: `${pack}-${relation}`, name: `${pack} workflow`, relation, stage: 'govern', pack, installed: true, latestRun: null })
const req = (control: string, status: JourneyRequirement['status'], workflows: JourneyRequirement['workflows'] = []): JourneyRequirement => ({ key: `FW|${control}`, control, title: `Req ${control}`, status, workflows, evaluations: [] })
const journey: Journey = {
  key: 'FW', name: 'Framework', pillar: 'governance', version: null, type: null, binding: null, status: null, active: 2, coveredAll: 0, coveredInstalled: 0,
  groups: [{ name: 'G', requirements: [req('1', 'covered', [wf('p1', 'Supports'), wf('p1', 'Satisfies'), wf('p2', 'Aligns with')]), req('2', 'gap')] }],
  steps: [
    { pack: 'p1', name: 'Pack one', installed: true, newlyCovered: 1, cumulative: 1 },
    { pack: 'p2', name: 'Pack two', installed: true, newlyCovered: 0, cumulative: 1 },
    { pack: 'p3', name: 'Pack three', installed: false, newlyCovered: 1, cumulative: 2 },
  ],
}
const clauseMap: ClauseMap = {
  verdict: null, confidence: null, scoped: true,
  frameworks: [{ key: 'FW', name: 'Framework', counts: { proven: 1, attested: 0, open: 0, total: 1 }, clauses: [{ key: 'FW|1', control: '1', title: 'Req 1', group: 'G', state: 'proven', cell: 'proven', checks: [] }] }],
}

test('columns are Org, one per installed pack, then this system', () => {
  const g = requirementsGrid(journey, clauseMap)
  assert.deepEqual(g.colGroups.map((c) => [c.label, c.cols.map((x) => x.key)]), [['Org', ['org']], ['Packs', ['p1', 'p2']], ['This system', ['state']]])
})

test('a pack cell is its best relation; Aligns with draws blank', () => {
  const [r1] = requirementsGrid(journey, clauseMap).groups[0].rows
  assert.deepEqual(r1.cells, ['atorg', 3, null, 'proven'])
})

test('an untracked requirement is blank with its reason, and a gap is not at organisation', () => {
  const [, r2] = requirementsGrid(journey, clauseMap).groups[0].rows
  assert.deepEqual(r2.cells, [null, null, null, null])
  assert.equal((r2.blank as string[])[3], 'Not tracked per system yet')
})

test('no installed pack drops the Packs group', () => {
  const g = requirementsGrid({ ...journey, steps: [] }, null)
  assert.deepEqual(g.colGroups.map((c) => c.label), ['Org', 'This system'])
})
