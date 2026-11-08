import assert from 'node:assert/strict'
import { describe, test } from 'node:test'

import type { ApiResponse } from '../api-client'
import { loadResource, viewResource, type ResourceState } from './usePacks'

type Run = { id: string }

function deferred<T>() {
  let resolve!: (value: T) => void
  const promise = new Promise<T>((r) => {
    resolve = r
  })
  return { promise, resolve }
}

const RUN_A = '/api/v1/packs/runs/run-a?org_id=org-1'
const RUN_B = '/api/v1/packs/runs/run-b?org_id=org-1'
const RUN_A_OTHER_ORG = '/api/v1/packs/runs/run-a?org_id=org-2'

function harness(initialPath: string | null) {
  let state: ResourceState<Run> = { scopeKey: initialPath ?? '', value: { data: null, loading: initialPath !== null, error: null } }
  const pending = new Map<string, ReturnType<typeof deferred<ApiResponse<Run>>>>()
  const get = (path: string) => {
    const d = deferred<ApiResponse<Run>>()
    pending.set(path, d)
    return d.promise
  }
  const update = (next: (s: ResourceState<Run>) => ResourceState<Run>) => {
    state = next(state)
  }
  return {
    get state() {
      return state
    },
    load: (path: string) => loadResource<Run>(get, path, update),
    respond: (path: string, data: Run) => pending.get(path)!.resolve({ success: true, data }),
  }
}

describe('pack resource scope', () => {
  test('masks the previous run in the same render once the path changes', async () => {
    const h = harness(RUN_A)
    const loading = h.load(RUN_A)
    h.respond(RUN_A, { id: 'run-a' })
    await loading
    assert.deepEqual(viewResource(h.state, RUN_A).data, { id: 'run-a' })

    // The route moved to run B (or another organisation) before any fetch for it started.
    assert.deepEqual(viewResource(h.state, RUN_B), { data: null, loading: true, error: null })
    assert.deepEqual(viewResource(h.state, RUN_A_OTHER_ORG), { data: null, loading: true, error: null })
    assert.deepEqual(viewResource(h.state, null), { data: null, loading: false, error: null })
  })

  test('drops a late response for a run the page has left', async () => {
    const h = harness(RUN_A)
    const first = h.load(RUN_A)
    const second = h.load(RUN_B)

    h.respond(RUN_A, { id: 'run-a' })
    await first
    assert.equal(h.state.scopeKey, RUN_B)
    assert.deepEqual(viewResource(h.state, RUN_B), { data: null, loading: true, error: null })

    h.respond(RUN_B, { id: 'run-b' })
    await second
    assert.deepEqual(viewResource(h.state, RUN_B), { data: { id: 'run-b' }, loading: false, error: null })
  })

  test('a reload of the same run keeps its data on screen while it refetches', async () => {
    const h = harness(RUN_A)
    const first = h.load(RUN_A)
    h.respond(RUN_A, { id: 'run-a' })
    await first

    const again = h.load(RUN_A)
    assert.deepEqual(viewResource(h.state, RUN_A), { data: { id: 'run-a' }, loading: true, error: null })
    h.respond(RUN_A, { id: 'run-a' })
    await again
    assert.equal(viewResource(h.state, RUN_A).loading, false)
  })
})
