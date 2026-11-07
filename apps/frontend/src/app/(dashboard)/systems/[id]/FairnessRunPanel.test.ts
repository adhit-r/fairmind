import assert from 'node:assert/strict'
import { test } from 'node:test'

import { groundsOf, listText, needsFavourable, sourceLine, uncoveredGrounds, words } from './FairnessRunPanel'

const col = (name: string, sample: string[] = [], distinct = sample.length) => ({
  name,
  dtype: 'object',
  distinct,
  sample,
  attribute: { status: null, basis: null },
})

test('column names split into whole words, camelCase included', () => {
  assert.deepEqual(words('applicantAgeBand'), ['applicant', 'age', 'band'])
  assert.deepEqual(words('date of birth'), ['date', 'of', 'birth'])
  assert.deepEqual(words('Home_State'), ['home', 'state'])
})

test('hints match whole words only, so mortgage, statement_date and premium_tier cover nothing', () => {
  for (const name of ['mortgage', 'statement_date', 'usage', 'sussex', 'customer_tier', 'premium_tier']) {
    assert.deepEqual(groundsOf(col(name)), [], name)
  }
  assert.deepEqual(groundsOf(col('age_band')), ['age'])
  assert.deepEqual(groundsOf(col('dateOfBirth')), ['age'])
  assert.deepEqual(groundsOf(col('home_state')), ['region'])
  assert.deepEqual(groundsOf(col('city_tier')), ['region'])
  assert.deepEqual(groundsOf(col('tier')), ['region'])
})

test('values that look like gender or reservation categories cover those grounds', () => {
  assert.deepEqual(groundsOf(col('grp', ['GEN', 'OBC', 'SC'])), ['caste or social category'])
  assert.deepEqual(groundsOf(col('applicant_x', ['F', 'M', 'X'])), ['gender'])
  // Only five samples reach the browser: a partial sample is not enough to call a column by its values.
  assert.deepEqual(groundsOf(col('grp', ['GEN', 'OBC', 'SC', 'ST', 'EWS'], 9)), [])
})

test('unticking a column puts its ground back among the uncovered ones', () => {
  const columns = [col('gender', ['F', 'M']), col('age_band', ['18-25']), col('home_state', ['MH', 'KA'])]
  const all = ['gender', 'age_band', 'home_state']
  assert.deepEqual(uncoveredGrounds(columns, all), ['caste or social category', 'religion', 'disability', 'language', 'marital status'])
  assert.ok(uncoveredGrounds(columns, ['gender', 'age_band']).includes('region'))
})

test('a favourable value is asked for only when the outcome is not 0/1, true/false or yes/no', () => {
  assert.equal(needsFavourable(['0', '1']), false)
  assert.equal(needsFavourable(['True', 'False']), false)
  assert.equal(needsFavourable(['yes', 'no']), false)
  assert.equal(needsFavourable(['approved', 'declined']), true)
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
