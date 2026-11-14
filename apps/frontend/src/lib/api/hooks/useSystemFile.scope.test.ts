import assert from 'node:assert/strict'
import { describe, test } from 'node:test'

import type { ApiResponse } from '../api-client'
import {
  enterSystemFileScope,
  loadSystemFile,
  systemFileAwaitsOrg,
  systemFileScopeKey,
  viewSystemFile,
  type SystemFileState,
} from './useSystemFile'

function deferred<T>() {
  let resolve!: (value: T) => void
  const promise = new Promise<T>((r) => {
    resolve = r
  })
  return { promise, resolve }
}

const SYSTEM_A = systemFileScopeKey('org-1', 'system-a')
const SYSTEM_B = systemFileScopeKey('org-1', 'system-b')
const SYSTEM_A_OTHER_ORG = systemFileScopeKey('org-2', 'system-a')

/** Every governance GET answers with an empty success, except the system record, which waits until released. */
function harness(initialKey: string) {
  let state: SystemFileState = enterSystemFileScope({ scopeKey: '', value: null as never }, initialKey)
  const systems = new Map<string, ReturnType<typeof deferred<ApiResponse<unknown>>>>()
  const get = <T,>(path: string): Promise<ApiResponse<T>> => {
    const match = path.match(/\/systems\/([^/?]+)$/)
    if (match) {
      const d = deferred<ApiResponse<unknown>>()
      systems.set(match[1], d)
      return d.promise as Promise<ApiResponse<T>>
    }
    const gate = path.match(/\/gate\/([^/?]+)$/)
    if (gate) {
      return Promise.resolve({
        success: true,
        data: {
          systemId: gate[1],
          allowed: false,
          blocking: [{ policyId: 'pol-1', policyName: 'Access policy', ruleId: 'rule-1', ruleTitle: 'MFA required', detail: 'MFA is off' }],
          warnings: [],
          runId: 'run-1',
          evaluatedAt: '2026-11-14T00:00:00Z',
        },
      }) as Promise<ApiResponse<T>>
    }
    return Promise.resolve({ success: false, error: 'not found' })
  }
  const update = (next: (s: SystemFileState) => SystemFileState) => {
    state = next(state)
  }
  return {
    get state() {
      return state
    },
    enter: (key: string) => update((s) => enterSystemFileScope(s, key)),
    load: (systemId: string, key: string) => loadSystemFile(get, systemId, key, update),
    release: (systemId: string) =>
      systems.get(systemId)!.resolve({ success: true, data: { id: systemId, name: `System ${systemId}` } }),
  }
}

describe('system file scope', () => {
  test('masks the previous system in the same render once the organisation or system changes', async () => {
    const h = harness(SYSTEM_A)
    const loading = h.load('system-a', SYSTEM_A)
    h.release('system-a')
    await loading
    assert.equal(viewSystemFile(h.state, SYSTEM_A).file.system?.id, 'system-a')

    for (const key of [SYSTEM_B, SYSTEM_A_OTHER_ORG]) {
      const view = viewSystemFile(h.state, key)
      assert.equal(view.file.system, null)
      assert.equal(view.loading, true)
      assert.equal(view.error, null)
    }
  })

  test('drops a late response for a system the page has left', async () => {
    const h = harness(SYSTEM_A)
    const first = h.load('system-a', SYSTEM_A)

    h.enter(SYSTEM_B)
    const second = h.load('system-b', SYSTEM_B)

    h.release('system-a')
    await first
    assert.equal(h.state.scopeKey, SYSTEM_B)
    assert.equal(viewSystemFile(h.state, SYSTEM_B).file.system, null)
    assert.equal(viewSystemFile(h.state, SYSTEM_B).loading, true)

    h.release('system-b')
    await second
    const view = viewSystemFile(h.state, SYSTEM_B)
    assert.equal(view.file.system?.id, 'system-b')
    assert.equal(view.loading, false)
  })

  test('a refresh from a left system cannot pull the state back to it', async () => {
    const h = harness(SYSTEM_A)
    h.enter(SYSTEM_B)
    const stale = h.load('system-a', SYSTEM_A)
    h.release('system-a')
    await stale
    assert.equal(h.state.scopeKey, SYSTEM_B)
    assert.equal(viewSystemFile(h.state, SYSTEM_B).file.system, null)
  })

  test('loads the live policy gate with the system file', async () => {
    const h = harness(SYSTEM_A)
    const loading = h.load('system-a', SYSTEM_A)
    h.release('system-a')
    await loading
    const view = viewSystemFile(h.state, SYSTEM_A)
    assert.equal(view.file.policyGate?.allowed, false)
    assert.equal(view.file.policyGate?.blocking.length, 1)
    assert.equal(view.file.policyGate?.blocking[0].ruleTitle, 'MFA required')
    assert.equal(view.loading, false)
  })

  test('waits for the organisations before fetching, so a cold load fetches the file once', () => {
    assert.equal(systemFileAwaitsOrg(true, null), true)
    assert.equal(systemFileAwaitsOrg(true, 'org-1'), false)
    assert.equal(systemFileAwaitsOrg(false, 'org-1'), false)
    assert.equal(systemFileAwaitsOrg(false, null), false)
  })
})
