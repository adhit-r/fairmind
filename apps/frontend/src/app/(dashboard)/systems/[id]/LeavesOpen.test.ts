import assert from 'node:assert/strict'
import { test } from 'node:test'

import type { CellState } from '@/components/ui/matrix'
import type { Journey, JourneyRequirement } from '@/lib/api/hooks/usePacks'
import type { ClauseMap, ClauseMapFramework } from '@/lib/api/hooks/useSystemFile'
import { leavesOpen } from './LeavesOpen'

const clause = (fw: string, n: number, cell: CellState): ClauseMapFramework['clauses'][number] => ({ key: `${fw}|${n}`, control: `${n}`, title: `Req ${n}`, group: null, state: 'open', cell, checks: [] })
const fw = (key: string, cells: CellState[]): ClauseMapFramework => ({ key, name: `${key} name`, counts: { proven: 0, attested: 0, open: 0, total: cells.length }, clauses: cells.map((c, i) => clause(key, i, c)) })
const map = (...frameworks: ClauseMapFramework[]): ClauseMap => ({ verdict: null, confidence: null, scoped: true, frameworks })
const journey = (key: string, covered: number[]): Journey => ({
  key, name: key, pillar: 'governance', version: null, type: null, binding: null, status: null, active: 0, coveredAll: 0, coveredInstalled: 0, steps: [],
  groups: [{ name: 'G', requirements: covered.map((n): JourneyRequirement => ({ key: `${key}|${n}`, control: `${n}`, title: '', status: 'covered', workflows: [], evaluations: [] })) }],
})
const keys = (v: ReturnType<typeof leavesOpen>) => v.groups.map((g) => [g.label, g.rows.map((r) => r.key)])

test('only open and failing clauses, grouped by framework with failures first', () => {
  const v = leavesOpen(map(fw('A', ['open', 'proven', 'fails']), fw('B', ['attested', 'open'])), [journey('A', [0])])
  assert.equal(v.n, 3)
  assert.deepEqual(keys(v), [['A name', ['A|2', 'A|0']], ['B name', ['B|1']]])
  assert.deepEqual(v.groups[0].rows[1].cells, ['open', 'atorg'])
  assert.deepEqual(v.groups[1].rows[0].blank, [undefined, 'Organisation status not loaded'])
  assert.equal(v.more.n, 0)
})

test('the cap keeps failures, then what the organisation does not hold, and counts the rest', () => {
  const v = leavesOpen(map(fw('A', Array(10).fill('open')), fw('B', ['open', 'open', 'fails', 'open'])), [journey('A', [0, 1, 2, 3])])
  assert.equal(v.n, 14)
  const rows = v.groups.flatMap((g) => g.rows.map((r) => r.key))
  assert.equal(rows.length, 12)
  assert.equal(rows[rows.length - 4], 'B|2')
  assert.ok(!rows.includes('A|2') && !rows.includes('A|3'))
  assert.deepEqual(v.more, { n: 2, href: '/frameworks/A' })
})

test('nothing open is nothing', () => {
  assert.equal(leavesOpen(map(fw('A', ['proven'])), []).n, 0)
  assert.equal(leavesOpen(null, []).n, 0)
})

test('an unscoped map (no confirmed frameworks) leaves nothing open', () => {
  assert.equal(leavesOpen({ ...map(fw('A', ['open', 'fails'])), scoped: false }, []).n, 0)
})
