import assert from 'node:assert/strict'
import { test } from 'node:test'

import type { GatePathStep, ReleaseGate } from '@/lib/api/hooks/useSystemFile'
import { arithmetic, attestationNote, bandRange, bestOption, pathSummary, stepTitle, tierLine, tierOverride } from './VerdictExplainer'

const step = (check: GatePathStep['check'], action: GatePathStep['action'], evidenceClass: GatePathStep['evidenceClass'], counts: number, gain: number): GatePathStep => ({ check, action, evidenceClass, counts, gain, note: null })

const CHECKS: ReleaseGate['checks'] = [
  { key: 'fairness', label: 'Fairness measured', state: 'proven', confidence: 0.95, evidenceId: 'e1', detail: null },
  { key: 'data_governance', label: 'Data governance', state: 'open', confidence: 0, evidenceId: null, detail: null },
  { key: 'human_oversight', label: 'Human oversight', state: 'open', confidence: 0, evidenceId: null, detail: null },
  { key: 'monitoring', label: 'Monitoring', state: 'open', confidence: 0, evidenceId: null, detail: null },
  { key: 'environmental', label: 'Environmental impact', state: 'open', confidence: 0, evidenceId: null, detail: null },
]

// The contract's medium example: one passing run at 0.95, nothing else on file.
const medium: ReleaseGate = {
  verdict: 'no_go',
  confidence: 0.19,
  band: 'unknown',
  checks: CHECKS,
  reasons: ['Nothing on file for: data governance, human oversight, monitoring, environmental impact'],
  proven: 1,
  attested: 0,
  open: 4,
  explain: {
    tier: 'medium',
    effectiveTier: 'medium',
    impact: 'medium',
    tierNote: null,
    tierSource: { suggestedTier: 'medium', ruleIds: ['T3'], confirmedBy: 'reviewer-1', confirmedAt: '2026-11-07T12:00:00Z', tierBelowSuggestion: false, overrideAcceptedBy: null },
    perCheck: 0.2,
    row: [
      { band: 'measured', from: 0.7, to: null, verdict: 'conditional_go' },
      { band: 'estimated', from: 0.35, to: 0.7, verdict: 'conditional_go' },
      { band: 'unknown', from: 0, to: 0.35, verdict: 'no_go' },
    ],
  },
  path: {
    target: 'conditional_go',
    options: [
      { kind: 'measured_first', steps: [step('environmental', 'environmental_assessment', 'tool_estimated', 0.85, 0.17)], confidenceAfter: 0.36, verdictAfter: 'conditional_go', approvalReady: true },
      {
        kind: 'attestations',
        steps: [step('data_governance', 'attest', 'manual', 0.3, 0.06), step('human_oversight', 'attest', 'manual', 0.3, 0.06), step('monitoring', 'attest', 'manual', 0.3, 0.06)],
        confidenceAfter: 0.37,
        verdictAfter: 'conditional_go',
        approvalReady: false,
      },
    ],
    ceiling: { confidence: 0.65, verdict: 'conditional_go' },
    notes: [],
    approvalBlockers: [],
  },
}

test('the arithmetic line reads the tier and counts the gate returned', () => {
  assert.equal(arithmetic(medium), 'Medium tier. Confidence 0.19 is the average of five checks, each worth up to 0.20: 1 proven, 0 attested, 4 open.')
  assert.equal(arithmetic({ ...medium, explain: undefined }), 'Confidence 0.19: 1 proven, 0 attested, 4 open.')
})

test('matrix cells read as confidence ranges', () => {
  assert.deepEqual(medium.explain!.row.map(bandRange), ['0.70 and up', '0.35 to 0.69', 'Below 0.35'])
})

test('the medium example: one assessment reaches conditional go, attestations are not faster', () => {
  const best = bestOption(medium.path)!
  assert.equal(best.kind, 'measured_first')
  assert.equal(stepTitle(best.steps[0], medium), 'Run an environmental assessment')
  assert.equal(pathSummary(medium), 'One step reaches Conditional go: run an environmental assessment.')
  assert.equal(
    attestationNote(medium, best),
    "Attesting data governance, human oversight and monitoring also reaches 0.37, Conditional go. Each is a named person's statement and counts 0.30 at most. Approval would still be blocked by the list below, so it is not faster.",
  )
})

test('a high tier whose ceiling stays below 0.70 says the target is not reachable', () => {
  const high: ReleaseGate = {
    ...medium,
    path: { ...medium.path!, options: [{ ...medium.path!.options[1], verdictAfter: 'no_go', confidenceAfter: 0.37 }], ceiling: { confidence: 0.65, verdict: 'no_go' } },
  }
  assert.equal(bestOption(high.path), null)
  assert.equal(pathSummary(high), 'Conditional go is not reachable with what FairMind records today. Best possible now: 0.65, No go.')
})

test('no path summary when the tier is already at its best verdict', () => {
  assert.equal(pathSummary({ ...medium, path: { ...medium.path!, target: null } }), null)
})

test('the tier line names the rule, the person and the date, or says nobody confirmed it', () => {
  assert.equal(tierLine(medium.explain!), 'Tier Medium, suggested by rule T3, confirmed by reviewer-1 on 7 Nov 2026.')
  assert.equal(tierLine({ ...medium.explain!, tierSource: null }), 'Tier Medium, not confirmed by a person.')
})

test('a lowered tier waits for a second person, then says who accepted it', () => {
  const src = { ...medium.explain!.tierSource!, suggestedTier: 'high' as const, ruleIds: ['T1'], tierBelowSuggestion: true }
  const lowered = { ...medium.explain!, tierSource: src }
  assert.equal(tierLine(lowered), 'Tier Medium, below the High suggested by rule T1, confirmed by reviewer-1 on 7 Nov 2026.')
  assert.deepEqual(tierOverride(lowered), { pending: true, text: 'Tier set below the suggested High. The gate uses High until another person accepts the lower tier.' })
  assert.equal(tierOverride({ ...lowered, tierSource: { ...src, overrideAcceptedBy: 'reviewer-2' } })?.pending, false)
  assert.equal(tierOverride(medium.explain), null)
})
