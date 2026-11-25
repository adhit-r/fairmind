import assert from 'node:assert/strict'
import { test } from 'node:test'

import { axisPct, cellReadiness, heatZone, sankey, waterfall } from './geometry'

test('waterfall keeps running totals and an axis that holds every value', () => {
  const w = waterfall(62, [5, 4, 3], 74)
  assert.deepEqual(w.rows.map((r) => [r.from, r.to]), [[62, 67], [67, 71], [71, 74]])
  assert.equal(w.end, 74)
  assert.equal(w.lo, 55)
  assert.equal(w.hi, 80)
  assert.deepEqual(w.ticks, [55, 60, 65, 70, 75, 80])
})

test('waterfall with no steps still has a usable axis', () => {
  const w = waterfall(40, [], 40)
  assert.ok(w.hi > w.lo)
  assert.ok(axisPct(40, w.lo, w.hi) >= 0)
})

test('axisPct maps the ends to 0 and 100', () => {
  assert.equal(axisPct(55, 55, 85), 0)
  assert.equal(axisPct(85, 55, 85), 100)
})

test('sankey ribbons fill their nodes exactly', () => {
  const s = sankey([[2, 1], [0, 3]], 100, 10)
  assert.equal(s.total, 6)
  const into = (j: number) => s.ribbons.filter((r) => r.target === j).reduce((a, r) => a + r.h, 0)
  assert.ok(Math.abs(into(0) - s.targets[0].h) < 1e-9)
  assert.ok(Math.abs(into(1) - s.targets[1].h) < 1e-9)
  assert.equal(s.ribbons.length, 3)
  assert.ok(s.sources[1].y > s.sources[0].y)
})

test('sankey with no links does not divide by zero', () => {
  const s = sankey([[0, 0]], 100, 10)
  assert.equal(s.ribbons.length, 0)
  assert.equal(s.sources[0].h, 0)
})

test('heat zones follow likelihood times impact', () => {
  assert.equal(heatZone(1, 1), 1)
  assert.equal(heatZone(2, 3), 2)
  assert.equal(heatZone(3, 4), 3)
  assert.equal(heatZone(5, 4), 4)
  assert.equal(heatZone(5, 3), 4)
})

test('cell states read as met, progress, attention or not started', () => {
  assert.equal(cellReadiness('proven'), 'met')
  assert.equal(cellReadiness('excluded'), 'met')
  assert.equal(cellReadiness('planned'), 'progress')
  assert.equal(cellReadiness('stale'), 'attention')
  assert.equal(cellReadiness('open'), 'notstarted')
  assert.equal(cellReadiness('anything else'), 'notstarted')
})
