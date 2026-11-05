import assert from 'node:assert/strict'
import { test } from 'node:test'

import { workflow } from './WatchPanel'

test('the monitoring workflow installs the CLI from git, so it runs in any repository', () => {
  const yaml = workflow('sys-1', '0 6 * * 1', ['gender'])
  assert.match(yaml, /pipx install "git\+https:\/\/github\.com\/adhit-r\/fairmind\.git#subdirectory=apps\/cli"/)
  assert.doesNotMatch(yaml, /pipx install \.\/apps\/cli/)
})
