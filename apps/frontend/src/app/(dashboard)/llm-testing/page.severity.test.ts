import assert from 'node:assert/strict'
import { readFileSync } from 'node:fs'
import test from 'node:test'

test('an unscored detect run gets no severity instead of "low"', () => {
  const pageSource = readFileSync(new URL('./page.tsx', import.meta.url), 'utf8')

  assert.match(pageSource, /severity: data\.overall_bias_score == null \? undefined\s*:/)
})
