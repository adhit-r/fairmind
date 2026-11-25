import assert from 'node:assert/strict'
import test from 'node:test'

import { buildCsp } from './proxy'

test('the policy pins scripts to the request nonce and allows only what the app loads', () => {
  const csp = buildCsp('abc123', false)
  assert.match(csp, /script-src 'self' 'nonce-abc123' 'strict-dynamic';/)
  assert.doesNotMatch(csp, /unsafe-eval/) // development only
  assert.match(csp, /frame-src https:\/\/challenges\.cloudflare\.com/)
  for (const directive of ["object-src 'none'", "base-uri 'self'", "form-action 'self'", "frame-ancestors 'none'"]) {
    assert.ok(csp.includes(directive), directive)
  }
  assert.match(buildCsp('x', true), /'unsafe-eval'/)
})
