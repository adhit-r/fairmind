import assert from 'node:assert/strict'
import test from 'node:test'

import { safeNextPath } from './safe-next-path'

const origin = 'https://app.fairmind.xyz'

test('keeps same-site paths', () => {
  assert.equal(safeNextPath('/invitations/abc?x=1#y', origin), '/invitations/abc?x=1#y')
  assert.equal(safeNextPath(null, origin), '/dashboard')
})

test('refuses off-site destinations', () => {
  for (const next of ['//evil.com', '/\\evil.com', '/\t/evil.com', '/\n/evil.com', '/\r/evil.com', 'https://evil.com']) {
    assert.equal(safeNextPath(next, origin), '/dashboard', JSON.stringify(next))
  }
})
