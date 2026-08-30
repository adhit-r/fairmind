import assert from 'node:assert/strict'
import { describe, test } from 'node:test'

import {
  evaluationScopeKey,
  readEvaluationScopeState,
  writeEvaluationScopeState,
  type EvaluationScopeState,
} from './evaluation-scope-state'

describe('evaluation scope state', () => {
  const currentScope = {
    organizationId: 'org-1',
    workspaceId: 'workspace-1',
    systemId: 'system-1',
    planId: 'plan-1',
    runId: 'run-1',
  }
  const currentKey = evaluationScopeKey(currentScope)
  const state: EvaluationScopeState<{ status: string }> = {
    scopeKey: currentKey,
    value: { status: 'trusted-current-state' },
  }

  test('returns state only for the exact organization, workspace, system, plan, and run', () => {
    assert.deepEqual(readEvaluationScopeState(state, currentKey, { status: 'masked' }), {
      status: 'trusted-current-state',
    })

    for (const [field, value] of Object.entries({
      organizationId: 'org-2',
      workspaceId: 'workspace-2',
      systemId: 'system-2',
      planId: 'plan-2',
      runId: 'run-2',
    })) {
      assert.deepEqual(readEvaluationScopeState(
        state,
        evaluationScopeKey({ ...currentScope, [field]: value }),
        { status: 'masked' },
      ), { status: 'masked' })
    }
  })

  test('does not alias scope identifiers that contain separators', () => {
    assert.notEqual(evaluationScopeKey({ organizationId: 'org:1', systemId: 'system-1' }),
      evaluationScopeKey({ organizationId: 'org', systemId: '1:system-1' }),
    )
  })

  test('ignores an async write after another scope becomes current', () => {
    const nextScopeKey = evaluationScopeKey({
      ...currentScope,
      workspaceId: 'workspace-2',
      systemId: 'system-2',
      runId: 'run-2',
    })
    const nextState: EvaluationScopeState<{ status: string }> = {
      scopeKey: nextScopeKey,
      value: { status: 'next-scope-loading' },
    }

    assert.equal(
      writeEvaluationScopeState(nextState, currentKey, { status: 'stale-retry-error' }),
      nextState,
    )
    assert.deepEqual(
      writeEvaluationScopeState(nextState, nextScopeKey, { status: 'next-scope-complete' }),
      { scopeKey: nextScopeKey, value: { status: 'next-scope-complete' } },
    )
  })
})
