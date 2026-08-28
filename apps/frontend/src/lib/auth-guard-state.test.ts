import assert from 'node:assert/strict'
import test from 'node:test'

import { resolveAuthGuardState } from './auth-guard-state'

const user = {
  id: 'user-1',
  username: 'reviewer',
  email: 'reviewer@fairmind.test',
}

test('keeps indeterminate session checks out of the login redirect path', () => {
  assert.equal(resolveAuthGuardState({ user: null, status: 'loading' }), 'loading')
  assert.equal(resolveAuthGuardState({ user: null, status: 'unavailable' }), 'unavailable')
  assert.equal(resolveAuthGuardState({ user: null, status: 'denied' }), 'denied')
  assert.equal(resolveAuthGuardState({ user: null, status: 'unauthenticated' }), 'redirect')
  assert.equal(resolveAuthGuardState({ user, status: 'authenticated' }), 'authenticated')
})
