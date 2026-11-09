import assert from 'node:assert/strict'
import { test } from 'node:test'

import type { ApplicabilityRecord } from '@/lib/api/hooks/useApplicability'
import type { Journey, JourneyRequirement } from '@/lib/api/hooks/usePacks'
import type { ReleaseGate } from '@/lib/api/hooks/useSystemFile'
import { afterSteps, aiRead, planGrid, planPacks } from './plan'

const wf = (pack: string, relation: string) => ({ id: `${pack}-${relation}`, name: `${pack} workflow`, relation, stage: 'govern', pack, installed: false, latestRun: null })
const req = (fw: string, control: string, workflows: JourneyRequirement['workflows'] = []): JourneyRequirement => ({ key: `${fw}|${control}`, control, title: `Req ${control}`, status: 'gap', workflows, evaluations: [] })
const journey = (key: string, steps: Journey['steps'], requirements: JourneyRequirement[]): Journey => ({
  key, name: key, pillar: 'governance', version: null, type: null, binding: null, status: null, active: requirements.length, coveredAll: 0, coveredInstalled: 0,
  groups: [{ name: 'G', requirements }], steps,
})
const step = (pack: string, newlyCovered: number, installed = false) => ({ pack, name: `Pack ${pack}`, installed, newlyCovered, cumulative: 0 })

const a = journey('A', [step('p2', 1), step('p1', 2, true)], [req('A', '1', [wf('p1', 'Supports'), wf('p2', 'Satisfies')]), req('A', '2', [wf('p1', 'Aligns with')])])
const b = journey('B', [step('p3', 1), step('p2', 1)], [req('B', '1', [wf('p3', 'Partially satisfies')])])

test('packs are listed once, in catalogue order, newly covered summed', () => {
  const packs = planPacks([a, b], ['p1', 'p2', 'p3'])
  assert.deepEqual(packs.map((p) => [p.pack, p.newlyCovered, p.installed]), [['p1', 2, true], ['p2', 2, false], ['p3', 1, false]])
})

test('Best is over ticked packs only and unticked columns are off', () => {
  const packs = planPacks([a, b], ['p1', 'p2', 'p3'])
  const all = planGrid([a, b], packs, new Set(['p1', 'p2', 'p3']), false)
  assert.deepEqual(all.groups[0].rows[0].cells, [1, 3, null])
  assert.equal(all.groups[0].rows[0].best, 3)
  const noP2 = planGrid([a, b], packs, new Set(['p1', 'p3']), false)
  assert.equal(noP2.groups[0].rows[0].best, 1)
  assert.deepEqual(noP2.grid.colGroups[0].cols.map((c) => c.off), [false, true, false])
})

test('untouched rows hide until Show all', () => {
  const packs = planPacks([a, b], ['p1', 'p2', 'p3'])
  const some = planGrid([a, b], packs, new Set(), false)
  assert.equal(some.total, 3)
  assert.equal(some.shown, 2)
  assert.equal(some.groups[0].rows[0].best, null)
  assert.equal(planGrid([a, b], packs, new Set(), true).shown, 3)
})

test('what the AI read: answers, rules, integration source', () => {
  const rec = {
    answers: { use: 'credit_scoring', decidesAboutPeople: true, humanReview: 'each', markets: ['IN', 'EU'], rbiRegulated: 'unsure', personalDataIndia: false, intendedPurpose: null },
    tierRules: [{ id: 'T1', text: 'Decides about credit', cite: null }],
  } as unknown as ApplicabilityRecord
  const rows = aiRead(rec, 'mlflow')
  assert.deepEqual(rows.map((r) => r.value), ['Credit scoring', 'Yes', 'A person reviews each one', 'India, EU or EEA', 'Not sure', 'No', 'Decides about credit', 'MLflow registry'])
  assert.deepEqual(aiRead(null, 'manual'), [])
})

test('the top line is worded after the steps run', () => {
  const gate = {
    checks: [], verdict: 'no_go',
    path: { target: 'conditional_go', options: [{ kind: 'measured_first', steps: [{ check: 'environmental', action: 'environmental_assessment', gain: 0.1, counts: 0.8 }], confidenceAfter: 0.72, verdictAfter: 'conditional_go', approvalReady: true }], ceiling: { confidence: 0.9, verdict: 'go' }, notes: [], approvalBlockers: [] },
  } as unknown as ReleaseGate
  assert.equal(afterSteps(gate)?.text, 'After the steps run: Conditional go, 0.72')
  assert.equal(afterSteps(gate)?.title, 'One step reaches Conditional go: run an environmental assessment.')
  assert.equal(afterSteps(null), null)
})
