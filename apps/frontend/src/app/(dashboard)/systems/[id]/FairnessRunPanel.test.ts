import assert from 'node:assert/strict'
import { test } from 'node:test'

import type { CsvInspection } from '@/lib/api/hooks/useSystemFile'
import { MIXED_ENCODING, confirmState, listText, needsFavourable, sourceLine, uncoveredGrounds } from './FairnessRunPanel'

type Status = CsvInspection['columns'][number]['attribute']['status']
const col = (name: string, sample: string[] = [], distinct = sample.length, status: Status = 'suggested', ground: string | null = null) => ({
  name,
  dtype: 'object',
  distinct,
  sample,
  attribute: { status, basis: null, ground },
})

test('coverage reads the ground the server gave each ticked column, with no value checks of its own', () => {
  // Six reservation values: the browser sees five, the server checked all six and says the column covers caste.
  const category = col('category', ['GEN', 'OBC', 'SC', 'ST', 'EWS'], 6, 'suggested', 'caste or social category')
  const columns = [col('gender', ['F', 'M'], 2, 'suggested', 'gender'), category, col('grp', ['F', 'M'], 2, 'possible', null)]
  assert.ok(!uncoveredGrounds(columns, ['category']).includes('caste or social category'))
  // A column the server gave no ground covers nothing, whatever its values look like.
  assert.ok(uncoveredGrounds(columns, ['grp']).includes('gender'))
})

test('unticking a column puts its ground back among the uncovered ones', () => {
  const columns = [col('gender', ['F', 'M'], 2, 'suggested', 'gender'), col('age_band', ['18-25'], 1, 'suggested', 'age'), col('home_state', ['MH', 'KA'], 2, 'suggested', 'region')]
  const all = ['gender', 'age_band', 'home_state']
  assert.deepEqual(uncoveredGrounds(columns, all), ['caste or social category', 'religion', 'disability', 'language', 'marital status'])
  assert.ok(uncoveredGrounds(columns, ['gender', 'age_band']).includes('region'))
})

test('a favourable value is asked for only when the backend would not read the outcome as binary', () => {
  assert.equal(needsFavourable(['0', '1']), false)
  assert.equal(needsFavourable(['True', 'False']), false)
  assert.equal(needsFavourable(['yes', 'no']), false)
  assert.equal(needsFavourable(['Yes', 'No']), false)
  assert.equal(needsFavourable(['YES', 'NO']), true)
  assert.equal(needsFavourable(['approved', 'declined']), true)
})

const inspection = (columns: ReturnType<typeof col>[], attributes: string[]): CsvInspection => ({
  rows: 100,
  columns,
  suggested: { outcome: 'repaid', prediction: 'approved', score: null, attributes },
  fileSha256: 'ab'.repeat(32),
  attributeSource: 'inferred',
  confirmedBy: null,
  confirmedAt: null,
  previousRunUnconfirmed: false,
  needsBinning: [],
  uncoveredGrounds: [],
})

test('the run needs a reason for every unticked suggestion and every uncovered ground', () => {
  const columns = [col('repaid', ['0', '1'], 2, null), col('approved', ['0', '1'], 2, null), col('gender', ['F', 'M'], 2, 'suggested', 'gender'), col('home_state', ['MH', 'KA'], 2, 'suggested', 'region')]
  const info = inspection(columns, ['gender', 'home_state'])
  const mapping = { outcome: 'repaid', prediction: 'approved', attributes: ['gender'] }
  const missing = confirmState(info, mapping, '', '')
  assert.deepEqual(missing.removed, ['home_state'])
  assert.ok(missing.uncovered.includes('region'))
  assert.equal(missing.ready, false)
  assert.equal(confirmState(info, mapping, 'Routing only, not a decision input', '').ready, false)
  assert.equal(confirmState(info, mapping, 'too short', 'Tested in the annual audit').ready, false)
  assert.equal(confirmState(info, mapping, 'Routing only, not a decision input', 'Tested in the annual audit').ready, true)
})

test('a column picked as outcome, prediction or score is not sent as a protected attribute', () => {
  const columns = [col('gender', ['F', 'M']), col('approved', ['0', '1'], 2, null)]
  const state = confirmState(inspection(columns, ['gender']), { outcome: 'gender', prediction: 'approved', attributes: ['gender'] }, '', '')
  assert.deepEqual(state.attributes, [])
  assert.deepEqual(state.removed, ['gender'])
  assert.equal(state.ready, false)
})

test('a text outcome needs its favourable value before the run', () => {
  const columns = [col('result', ['approved', 'declined'], 2, null), col('model_result', ['declined', 'approved'], 2, null), col('gender', ['F', 'M'])]
  const info = inspection(columns, ['gender'])
  const mapping = { outcome: 'result', prediction: 'model_result', attributes: ['gender'] }
  const reason = 'Tested in the annual audit'
  assert.equal(confirmState(info, mapping, '', reason).ready, false)
  assert.equal(confirmState(info, { ...mapping, favorableLabel: 'approved' }, '', reason).ready, true)
})

test('a favourable value is asked for once, and only when the outcome and prediction are coded alike', () => {
  const columns = [
    col('decision', ['approved', 'rejected'], 2, null),
    col('model_decision', ['rejected', 'approved'], 2, null),
    col('model_label', ['yes_pred', 'no_pred'], 2, null),
    col('repaid', ['0', '1'], 2, null),
    col('approved', ['0', '1'], 2, null),
    col('gender', ['F', 'M']),
  ]
  const info = inspection(columns, ['gender'])
  const state = (outcome: string, prediction?: string) => confirmState(info, { outcome, prediction, attributes: ['gender'], favorableLabel: 'approved' }, '', 'Tested in the annual audit')
  // Text outcome with a 0/1 prediction, or the reverse: the one favourable value cannot read both, so the run is blocked.
  for (const [o, p] of [['decision', 'approved'], ['repaid', 'model_decision'], ['decision', 'model_label']]) {
    assert.equal(state(o, p).mixed, true, `${o}/${p}`)
    assert.equal(state(o, p).favourable, false)
    assert.equal(state(o, p).ready, false)
  }
  // Both text with the same values: one select covers both.
  assert.deepEqual([state('decision', 'model_decision').mixed, state('decision', 'model_decision').favourable, state('decision', 'model_decision').ready], [false, true, true])
  // Both 0/1, or a text outcome with a score: nothing mixed.
  assert.equal(state('repaid', 'approved').mixed, false)
  assert.equal(state('repaid', 'approved').favourable, false)
  assert.equal(state('decision').mixed, false)
  assert.equal(state('decision').favourable, true)
  assert.match(MIXED_ENCODING, /^The outcome and prediction columns use different values\./)
})

test('a ticked or suggested column keeps its row however many values it has', () => {
  const branch = col('branch_code', ['B1', 'B2', 'B3', 'B4', 'B5'], 60)
  const columns = [col('repaid', ['0', '1'], 2, null), col('approved', ['0', '1'], 2, null), branch, col('txn_id', ['t1'], 900, null), col('pincode', ['1'], 400, 'too_many_values')]
  const names = (attributes: string[], suggested: string[]) => confirmState(inspection(columns, suggested), { outcome: 'repaid', prediction: 'approved', attributes }, '', '').rows.map((c) => c.name)
  assert.deepEqual(names(['branch_code'], ['branch_code']), ['branch_code', 'pincode'])
  assert.deepEqual(names([], ['branch_code']), ['branch_code', 'pincode'])
  assert.deepEqual(names(['branch_code'], []), ['branch_code', 'pincode'])
  assert.deepEqual(names([], []), ['pincode'])
})

test('reuse from an unconfirmed run never claims a person confirmed it', () => {
  const base = { confirmedBy: null, confirmedAt: null, previousRunUnconfirmed: false }
  assert.equal(sourceLine({ ...base, attributeSource: 'inferred' }), 'Suggested from column names and values. Check every row.')
  assert.equal(sourceLine({ ...base, attributeSource: 'none' }), 'No column looks like a protected attribute. Choose them.')
  assert.equal(sourceLine({ ...base, attributeSource: 'confirmed', confirmedBy: 'reviewer-1', previousRunUnconfirmed: true }), 'Using the attributes from the last run.')
  assert.match(
    sourceLine({ attributeSource: 'confirmed', confirmedBy: 'reviewer-1', confirmedAt: '2026-11-02T10:00:00Z', previousRunUnconfirmed: false }),
    /^Using the attributes reviewer-1 confirmed on 2 Nov 2026\. Change them if this file differs\.$/,
  )
})

test('lists read as prose', () => {
  assert.equal(listText(['gender']), 'gender')
  assert.equal(listText(['gender', 'age']), 'gender and age')
  assert.equal(listText(['gender', 'age', 'region']), 'gender, age and region')
})
