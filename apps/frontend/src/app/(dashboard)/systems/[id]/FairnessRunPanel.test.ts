import assert from 'node:assert/strict'
import { test } from 'node:test'

import type { CsvInspection } from '@/lib/api/hooks/useSystemFile'
import { confirmState, groundOf, listText, needsFavourable, sourceLine, uncoveredGrounds, words } from './FairnessRunPanel'

type Status = CsvInspection['columns'][number]['attribute']['status']
const col = (name: string, sample: string[] = [], distinct = sample.length, status: Status = 'suggested') => ({
  name,
  dtype: 'object',
  distinct,
  sample,
  attribute: { status, basis: null },
})

test('column names split into whole words as the backend splits them', () => {
  assert.deepEqual(words('applicantAgeBand'), ['applicant', 'age', 'band'])
  assert.deepEqual(words('date of birth'), ['date', 'of', 'birth'])
  assert.deepEqual(words('Home_State'), ['home', 'state'])
  assert.deepEqual(words('DOBDate'), ['dob', 'date'])
  assert.deepEqual(words('age2'), ['age', '2'])
})

test('hints match whole words only, so mortgage, statement_date and premium_tier cover nothing', () => {
  for (const name of ['mortgage', 'statement_date', 'usage', 'sussex', 'customer_tier', 'premium_tier']) {
    assert.equal(groundOf(col(name)), null, name)
  }
  assert.equal(groundOf(col('age_band')), 'age')
  assert.equal(groundOf(col('dateOfBirth')), 'age')
  assert.equal(groundOf(col('home_state')), 'region')
  assert.equal(groundOf(col('city_tier')), 'region')
  assert.equal(groundOf(col('tier')), 'region')
  assert.equal(groundOf(col('ethnicity')), null)
})

test('values that look like gender or reservation categories decide the one ground a column covers', () => {
  assert.equal(groundOf(col('grp', ['GEN', 'OBC', 'SC'])), 'caste or social category')
  assert.equal(groundOf(col('applicant_x', ['F', 'M', 'X'])), 'gender')
  // The backend gives a column one ground; reservation values win over a region name.
  assert.equal(groundOf(col('state_group', ['SC', 'ST'])), 'caste or social category')
  // Only five samples reach the browser: a partial sample is not enough to call a column by its values.
  assert.equal(groundOf(col('grp', ['GEN', 'OBC', 'SC', 'ST', 'EWS'], 9)), null)
  // A single value is no group comparison; the backend checks values only from two distinct up.
  assert.equal(groundOf(col('grp', ['F'])), null)
  // A column the inspection mapped as outcome, prediction or score covers nothing on the server.
  assert.equal(groundOf(col('gender', ['F', 'M'], 2, null)), null)
})

test('unticking a column puts its ground back among the uncovered ones', () => {
  const columns = [col('gender', ['F', 'M']), col('age_band', ['18-25']), col('home_state', ['MH', 'KA'])]
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
  const columns = [col('repaid', ['0', '1'], 2, null), col('approved', ['0', '1'], 2, null), col('gender', ['F', 'M']), col('home_state', ['MH', 'KA'])]
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
  const columns = [col('result', ['approved', 'declined'], 2, null), col('approved', ['0', '1'], 2, null), col('gender', ['F', 'M'])]
  const info = inspection(columns, ['gender'])
  const mapping = { outcome: 'result', prediction: 'approved', attributes: ['gender'] }
  const reason = 'Tested in the annual audit'
  assert.equal(confirmState(info, mapping, '', reason).ready, false)
  assert.equal(confirmState(info, { ...mapping, favorableLabel: 'approved' }, '', reason).ready, true)
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
