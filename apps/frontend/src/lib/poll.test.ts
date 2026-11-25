import assert from 'node:assert/strict'
import test, { mock } from 'node:test'

import { pollWhileVisible } from './poll'

test('polls only while visible and catches up on return', () => {
  mock.timers.enable({ apis: ['setInterval'] })
  const listeners: Array<() => void> = []
  const doc = {
    hidden: false,
    addEventListener: (_: string, fn: () => void) => listeners.push(fn),
    removeEventListener: () => {},
  }
  ;(globalThis as { document?: unknown }).document = doc
  let calls = 0
  const stop = pollWhileVisible(() => { calls += 1 }, 1000)

  mock.timers.tick(1000)
  assert.equal(calls, 1)
  doc.hidden = true
  mock.timers.tick(3000)
  assert.equal(calls, 1) // no requests from a hidden tab
  doc.hidden = false
  listeners.forEach((fn) => fn())
  assert.equal(calls, 2) // one catch-up call on return
  stop()
  mock.timers.tick(5000)
  assert.equal(calls, 2)
  mock.timers.reset()
  delete (globalThis as { document?: unknown }).document
})
