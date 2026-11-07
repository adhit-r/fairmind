import assert from 'node:assert/strict'
import { test } from 'node:test'

import { snapshotLabel, workflow } from './WatchPanel'

test('the monitoring workflow installs the CLI from git, so it runs in any repository', () => {
  const yaml = workflow('sys-1', '0 6 * * 1', ['gender'])
  assert.match(yaml, /pipx install "git\+https:\/\/github\.com\/adhit-r\/fairmind\.git#subdirectory=apps\/cli"/)
  assert.doesNotMatch(yaml, /pipx install \.\/apps\/cli/)
})

test('a snapshot label names the checks that failed, not just the impact ratio', () => {
  const attr = (checks: Record<string, boolean>) => [{ attribute: 'gender', disparateImpactRatio: 0.9, maxRateDrift: 0.2, worstPsi: null, checks }]
  assert.equal(snapshotLabel({ allChecksPass: true, attributes: attr({ disparate_impact: true }) }, 0.9), 'Lowest impact ratio 0.90, all checks within thresholds')
  assert.equal(
    snapshotLabel({ allChecksPass: false, attributes: attr({ disparate_impact: true, selection_rate_stable: false }) }, 0.9),
    'Lowest impact ratio 0.90, outside thresholds: gender selection-rate drift',
  )
  assert.equal(snapshotLabel({ allChecksPass: null, attributes: [] }, null), 'Lowest impact ratio not available, check result not recorded')
})
