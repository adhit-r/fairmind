import assert from 'node:assert/strict'
import { test } from 'node:test'

import type { GateCheck } from '@/lib/api/hooks/useSystemFile'
import { cellKind, checkCell, groupLabelLines, legendKeys, showGroupRows, type MatrixGroup } from './matrix'

const row = (key: string, cells: MatrixGroup['rows'][number]['cells']) => ({ key, label: key, cells })

test('cellKind reads states as themselves, relations as r1 to r3 and nothing as blank', () => {
  assert.equal(cellKind('fails'), 'fails')
  assert.equal(cellKind(3), 'r3')
  assert.equal(cellKind(1), 'r1')
  assert.equal(cellKind(0), '')
  assert.equal(cellKind(null), '')
  assert.equal(cellKind(undefined), '')
})

test('the legend lists only the kinds present, states first in the fixed order, then relations', () => {
  const groups: MatrixGroup[] = [
    { label: 'a', rows: [row('x', ['open', null, 'proven']), row('y', [2, 'stale'])] },
    { label: 'b', rows: [row('z', ['atorg', 3])] },
  ]
  assert.deepEqual(legendKeys(groups), ['proven', 'open', 'stale', 'atorg', 'r3', 'r2'])
  assert.deepEqual(legendKeys([{ label: 'a', rows: [row('x', [null, 0])] }]), [])
})

test('group rows show only with two or more non-empty groups', () => {
  assert.equal(showGroupRows([{ label: 'a', rows: [row('x', [])] }]), false)
  assert.equal(showGroupRows([{ label: 'a', rows: [row('x', [])] }, { label: 'b', rows: [] }]), false)
  assert.equal(showGroupRows([{ label: 'a', rows: [row('x', [])] }, { label: 'b', rows: [row('y', [])] }]), true)
})

type C = Parameters<typeof checkCell>[0]
const check = (over: Partial<GateCheck>): C => ({ state: 'proven', evidenceClass: 'measured', detail: null, ...over })

test('checkCell maps a check the way the backend cell_state does', () => {
  assert.equal(checkCell(check({})), 'proven')
  assert.equal(checkCell(check({ state: 'proven', evidenceClass: 'tool_estimated' })), 'estimated')
  assert.equal(checkCell(check({ state: 'attested', evidenceClass: 'measured' })), 'estimated')
  assert.equal(checkCell(check({ state: 'attested', evidenceClass: 'manual' })), 'attested')
  assert.equal(checkCell(check({ detail: { all_checks_pass: false } })), 'fails')
  assert.equal(checkCell(check({ evidenceClass: 'tool_estimated', fails: true })), 'fails')
  assert.equal(checkCell(check({ state: 'open', evidenceClass: null, stale: true })), 'stale')
  assert.equal(checkCell(check({ state: 'open', evidenceClass: null })), 'open')
})

test('a manual record that says it fails is attested, not fails', () => {
  assert.equal(checkCell(check({ state: 'attested', evidenceClass: 'manual', detail: { all_checks_pass: false } })), 'attested')
})

test('a payload from before evidenceClass falls back to its state', () => {
  assert.equal(checkCell({ state: 'attested' }), 'attested')
  assert.equal(checkCell({ state: 'proven' }), 'proven')
})

test('group labels: narrow groups overflow, and no two neighbours share a line after an overflow', () => {
  const g = (label: string, n: number) => ({ label, cols: Array(n).fill(0) })
  const lines = (gs: ReturnType<typeof g>[]) => groupLabelLines(gs).map((x) => `${x.ov ? 'ov' : 'clip'}:${x.up ? 'up' : 'down'}`)
  // The mockup layout: one-column groups up, wider groups down.
  assert.deepEqual(lines([g('Org', 1), g('Critical', 3), g('High', 1), g('Medium', 2)]), ['ov:up', 'clip:down', 'ov:up', 'ov:down'])
  // One system per tier: the lines alternate.
  assert.deepEqual(lines([g('Org', 1), g('Critical', 1), g('High', 1), g('Medium', 1)]), ['ov:up', 'ov:down', 'ov:up', 'ov:down'])
  // An unlabelled one-column group does not overflow.
  assert.deepEqual(lines([g('FAI', 2), g('', 1), g('GOV', 2)]), ['clip:down', 'clip:down', 'ov:down'])
})
