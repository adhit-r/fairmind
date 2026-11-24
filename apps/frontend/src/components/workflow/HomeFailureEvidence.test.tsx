import assert from 'node:assert/strict'
import { test } from 'node:test'
import { renderToStaticMarkup } from 'react-dom/server'
import { HomeFailureBreakdown } from './HomeFailureEvidence'

const record = { id: 'original', systemId: 'scoring', title: 'Recorded fairness result', type: 'fairness_test' }
const ratio = {
  attribute: 'age_cat',
  checks: { disparate_impact: false },
  disparate_impact: { value: 0.5, threshold: 0.8, is_fair: false },
  selection_rates: { Older: 0.8, Younger: 0.4 },
}
function chart(attributes: unknown[], rows?: number) {
  return renderToStaticMarkup(<HomeFailureBreakdown systemName="Scoring system" record={{ ...record, content: { attributes, rows } }} />)
}

test('group rates use the failed attribute from the same record, with supplied counts and a common scale', () => {
  const passing = { ...ratio, attribute: 'region', checks: { disparate_impact: true }, selection_rates: { North: 0.65, South: 0.8 } }
  const html = chart([passing, { ...ratio, groups: { Older: 350, Younger: 850 } }], 1200)
  assert.match(html, /Selection rate by age group/)
  assert.match(html, /Scoring system · 1,200 records/)
  assert.match(html, /Younger[\s\S]*850 records[\s\S]*40\.0%[\s\S]*Older[\s\S]*350 records[\s\S]*80\.0%/)
  assert.doesNotMatch(html, /North|South/)
})

test('incomplete or out-of-range rates omit the chart, and absent counts stay absent', () => {
  for (const selection_rates of [{ A: 0.2 }, { A: 0.2, B: null }, { A: 0.2, B: 1.1 }]) {
    assert.equal(chart([{ ...ratio, selection_rates }]), '')
  }
  assert.equal(chart([{ ...ratio, checks: { disparate_impact: true } }]), '')
  assert.doesNotMatch(chart([ratio]), /records|NaN/)
})
