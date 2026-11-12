import assert from 'node:assert/strict'
import test from 'node:test'

import { readSystemsCsv } from './systemsCsv'

test('reads valid rows and reports bad ones by line', () => {
  const { rows, problems } = readSystemsCsv(
    'Name,Owner,Risk Tier,Stage\nCredit scorer,Risk team,HIGH,\n,x,low,onboard\nChat helper,,medium,launch\nCredit scorer,y,low,assess\nFraud ranker,Ops,critical,operate\n',
  )
  assert.deepEqual(rows.map((r) => [r.name, r.riskTier, r.stage, r.line]), [
    ['Credit scorer', 'high', 'onboard', 2],
    ['Fraud ranker', 'critical', 'operate', 6],
  ])
  assert.deepEqual(problems.map((p) => p.line), [3, 4, 5])
})

test('an empty file is one problem, not zero rows silently', () => {
  assert.equal(readSystemsCsv('').problems.length, 1)
})
