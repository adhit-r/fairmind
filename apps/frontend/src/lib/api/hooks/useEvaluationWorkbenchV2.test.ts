import assert from 'node:assert/strict'
import test, { describe } from 'node:test'

import { type ApiResponse } from '../api-client'
import { API_ENDPOINTS } from '../endpoints'
import {
  EvaluationScopeMismatchError,
  StaleEvaluationWorkbenchResultError,
  createEvaluationWorkbenchV2Controller,
  createEvaluationWorkbenchV2ScopeView,
  type EvaluationPlanV2,
  type EvaluationRunV2,
  type EvaluationWorkbenchApiClient,
} from './useEvaluationWorkbenchV2'

type ApiCall = {
  endpoint: string
}

function deferred<T>() {
  let resolve!: (value: T) => void
  let reject!: (reason?: unknown) => void
  const promise = new Promise<T>((resolvePromise, rejectPromise) => {
    resolve = resolvePromise
    reject = rejectPromise
  })
  return { promise, resolve, reject }
}

function plan(overrides: Partial<EvaluationPlanV2> = {}): EvaluationPlanV2 {
  return {
    id: 'plan-1',
    organizationId: 'org-1',
    workspaceId: 'workspace-1',
    systemId: 'system-1',
    contractVersion: '2.0.0',
    name: 'Release assurance',
    targetVersionId: 'target-version-1',
    targetKind: 'llm_application',
    lifecyclePhases: ['pre_deploy'],
    executionDepth: 'hybrid',
    enforcementMode: 'human_approval',
    deliveryMode: 'external_provider',
    trustPolicyVersionId: 'trust-policy-1',
    planContentHash: 'a'.repeat(64),
    suites: [{
      ordinal: 1,
      suiteVersionId: 'suite-version-1',
      ownerScope: 'organization',
      suiteRef: 'fairmind/prompt-safety@2.0.0',
      manifestDigest: 'b'.repeat(64),
      configuration: {},
      configurationHash: 'c'.repeat(64),
    }],
    status: 'active',
    createdBy: 'user-1',
    updatedBy: 'user-1',
    createdAt: '2026-08-08T00:00:00Z',
    updatedAt: '2026-08-08T00:00:00Z',
    ...overrides,
  }
}

function run(overrides: Partial<EvaluationRunV2> = {}): EvaluationRunV2 {
  const base: Omit<EvaluationRunV2, 'envelope'> = {
    id: 'run-1',
    organizationId: 'org-1',
    workspaceId: 'workspace-1',
    systemId: 'system-1',
    planId: 'plan-1',
    contractVersion: '2.0.0',
    trigger: 'manual',
    lifecyclePhase: 'pre_deploy',
    technicalStatus: 'succeeded',
    evidenceOutcome: 'passed_with_limitations',
    overallVerdict: 'review',
    layerVerdictsSchemaVersion: '1.0.0',
    layerVerdicts: {
      suites: { 'suite-version-1': 'review' },
      modalities: {},
      components: {},
      riskDimensions: {},
    },
    suiteExecutions: [{
      id: 'suite-execution-1',
      suiteVersionId: 'suite-version-1',
      ownerScope: 'organization',
      ordinal: 1,
      technicalStatus: 'succeeded',
      evidenceResultStatus: 'passed_with_limitations',
      admissionStatus: 'verified',
      reviewStatus: 'pending',
      freshnessStatus: 'current',
      evidenceTrust: null,
      limitations: ['Boundary coverage is incomplete.'],
      failureCode: null,
      failureMessage: null,
    }],
    envelopeId: 'envelope-1',
    envelopeHash: 'd'.repeat(64),
    verdictVersion: 1,
    requestedBy: 'user-1',
    startedAt: '2026-08-08T00:01:00Z',
    completedAt: '2026-08-08T00:02:00Z',
    failureCode: null,
    failureMessage: null,
    createdAt: '2026-08-08T00:00:00Z',
    updatedAt: '2026-08-08T00:02:00Z',
  }
  const next = { ...base, ...overrides }
  return {
    ...next,
    envelope: overrides.envelope ?? {
      schemaVersion: '2.0.0',
      envelopeId: next.envelopeId,
      runId: next.id,
      organizationId: next.organizationId,
      workspaceId: next.workspaceId,
      systemId: next.systemId,
      planId: next.planId,
      suites: next.suiteExecutions.map((suite) => ({
        suiteExecutionId: suite.id,
        suiteVersionId: suite.suiteVersionId,
        ownerScope: suite.ownerScope,
      })),
    },
  }
}

function fakeClient(
  getImpl: (endpoint: string) => Promise<ApiResponse<unknown>>,
): { client: EvaluationWorkbenchApiClient; calls: ApiCall[] } {
  const calls: ApiCall[] = []
  return {
    client: {
      async get<T>(endpoint: string) {
        calls.push({ endpoint })
        return await getImpl(endpoint) as ApiResponse<T>
      },
    },
    calls,
  }
}

describe('evaluation workbench v2 scope authority', () => {
  test('uses the mounted organization/system route and validates workspace in responses', () => {
    assert.equal(
      API_ENDPOINTS.aiGovernance.evaluationV2Plans('org-1', 'system-1'),
      '/api/v1/ai-governance/organizations/org-1/systems/system-1/evaluation-v2/plans',
    )
    assert.equal(
      API_ENDPOINTS.aiGovernance.evaluationV2Plan('org-1', 'system-1', 'plan-1'),
      '/api/v1/ai-governance/organizations/org-1/systems/system-1/evaluation-v2/plans/plan-1',
    )
    assert.equal(
      API_ENDPOINTS.aiGovernance.evaluationV2Runs('org-1', 'system-1'),
      '/api/v1/ai-governance/organizations/org-1/systems/system-1/evaluation-v2/runs',
    )
    assert.equal(
      API_ENDPOINTS.aiGovernance.evaluationV2Run('org-1', 'system-1', 'run-1'),
      '/api/v1/ai-governance/organizations/org-1/systems/system-1/evaluation-v2/runs/run-1',
    )
  })

  test('clears both list segments when returned records belong to another workspace', async () => {
    const { client } = fakeClient(async (endpoint) => {
      if (endpoint.endsWith('/plans')) {
        return { success: true, data: [plan({ workspaceId: 'workspace-other' })] }
      }
      return { success: true, data: [run({ workspaceId: 'workspace-other' })] }
    })
    const controller = createEvaluationWorkbenchV2Controller(client)

    await controller.setScope('org-1', 'workspace-1', 'system-1')

    assert.deepEqual(controller.getSnapshot().plans, [])
    assert.deepEqual(controller.getSnapshot().runs, [])
    assert.equal(controller.getSnapshot().plansLoaded, false)
    assert.equal(controller.getSnapshot().runsLoaded, false)
    assert.ok(controller.getSnapshot().error instanceof EvaluationScopeMismatchError)
  })

  test('rejects a run detail whose response ID differs from the requested run and leaves the old scope empty', async () => {
    const { client } = fakeClient(async (endpoint) => {
      if (endpoint.endsWith('/plans')) return { success: true, data: [] }
      if (endpoint.endsWith('/runs')) return { success: true, data: [] }
      return { success: true, data: run({ id: 'run-from-another-request' }) }
    })
    const controller = createEvaluationWorkbenchV2Controller(client)
    await controller.setScope('org-1', 'workspace-1', 'system-1')

    await assert.rejects(
      controller.getRun('run-requested'),
      EvaluationScopeMismatchError,
    )
    assert.deepEqual(controller.getSnapshot().runs, [])
  })

  test('rejects a plan detail whose response ID differs from the requested plan', async () => {
    const { client } = fakeClient(async (endpoint) => {
      if (endpoint.endsWith('/plans/plan-requested')) {
        return { success: true, data: plan({ id: 'plan-from-another-request' }) }
      }
      return { success: true, data: [] }
    })
    const controller = createEvaluationWorkbenchV2Controller(client)
    await controller.setScope('org-1', 'workspace-1', 'system-1')

    await assert.rejects(
      controller.getPlan('plan-requested'),
      EvaluationScopeMismatchError,
    )
  })

  test('clears run list data when a schema-valid envelope binds the run to another plan', async () => {
    const mismatchedEnvelopeRun = run({
      envelope: {
        schemaVersion: '2.0.0',
        envelopeId: 'envelope-1',
        runId: 'run-1',
        organizationId: 'org-1',
        workspaceId: 'workspace-1',
        systemId: 'system-1',
        planId: 'plan-other',
        suites: [{
          suiteExecutionId: 'suite-execution-1',
          suiteVersionId: 'suite-version-1',
          ownerScope: 'organization',
        }],
      },
    })
    const { client } = fakeClient(async (endpoint) => endpoint.endsWith('/plans')
      ? { success: true, data: [] }
      : { success: true, data: [mismatchedEnvelopeRun] })
    const controller = createEvaluationWorkbenchV2Controller(client)

    await controller.setScope('org-1', 'workspace-1', 'system-1')

    assert.deepEqual(controller.getSnapshot().runs, [])
    assert.equal(controller.getSnapshot().runsLoaded, false)
    assert.ok(controller.getSnapshot().error instanceof EvaluationScopeMismatchError)
  })

  test('clears run list data when an envelope suite binding differs from its suite execution', async () => {
    const mismatchedEnvelopeRun = run({
      envelope: {
        schemaVersion: '2.0.0',
        envelopeId: 'envelope-1',
        runId: 'run-1',
        organizationId: 'org-1',
        workspaceId: 'workspace-1',
        systemId: 'system-1',
        planId: 'plan-1',
        suites: [{
          suiteExecutionId: 'suite-execution-1',
          suiteVersionId: 'suite-version-other',
          ownerScope: 'organization',
        }],
      },
    })
    const { client } = fakeClient(async (endpoint) => endpoint.endsWith('/plans')
      ? { success: true, data: [] }
      : { success: true, data: [mismatchedEnvelopeRun] })
    const controller = createEvaluationWorkbenchV2Controller(client)

    await controller.setScope('org-1', 'workspace-1', 'system-1')

    assert.deepEqual(controller.getSnapshot().runs, [])
    assert.equal(controller.getSnapshot().runsLoaded, false)
    assert.ok(controller.getSnapshot().error instanceof EvaluationScopeMismatchError)
  })

  test('converts a rejected run detail superseded by a new scope into a stale result', async () => {
    const delayedDetail = deferred<ApiResponse<unknown>>()
    const { client } = fakeClient(async (endpoint) => {
      if (endpoint.endsWith('/runs/run-1')) return delayedDetail.promise
      return { success: true, data: [] }
    })
    const controller = createEvaluationWorkbenchV2Controller(client)
    await controller.setScope('org-1', 'workspace-1', 'system-1')

    const pendingDetail = controller.getRun('run-1')
    await controller.setScope('org-1', 'workspace-2', 'system-2')
    delayedDetail.reject(new Error('The superseded request failed.'))

    await assert.rejects(pendingDetail, StaleEvaluationWorkbenchResultError)
  })

  test('converts an older run-detail failure into stale after a newer run detail is requested', async () => {
    const delayedFirstDetail = deferred<ApiResponse<unknown>>()
    const { client } = fakeClient(async (endpoint) => {
      if (endpoint.endsWith('/runs/run-1')) return delayedFirstDetail.promise
      if (endpoint.endsWith('/runs/run-2')) return { success: true, data: run({ id: 'run-2' }) }
      return { success: true, data: [] }
    })
    const controller = createEvaluationWorkbenchV2Controller(client)
    await controller.setScope('org-1', 'workspace-1', 'system-1')

    const firstDetail = controller.getRun('run-1')
    assert.equal((await controller.getRun('run-2')).id, 'run-2')
    delayedFirstDetail.reject(new Error('The old run request failed.'))

    await assert.rejects(firstDetail, StaleEvaluationWorkbenchResultError)
  })

  test('masks a previous workspace snapshot before the next workspace list resolves', async () => {
    const oldPlans = deferred<ApiResponse<unknown>>()
    const oldRuns = deferred<ApiResponse<unknown>>()
    const { client } = fakeClient(async (endpoint) => {
      if (endpoint.includes('/systems/system-old/')) {
        return endpoint.endsWith('/plans') ? oldPlans.promise : oldRuns.promise
      }
      return endpoint.endsWith('/plans')
        ? { success: true, data: [plan({ id: 'plan-new', workspaceId: 'workspace-new', systemId: 'system-new' })] }
        : { success: true, data: [run({ id: 'run-new', workspaceId: 'workspace-new', systemId: 'system-new' })] }
    })
    const controller = createEvaluationWorkbenchV2Controller(client)

    const oldLoad = controller.setScope('org-1', 'workspace-old', 'system-old')
    const nextRender = createEvaluationWorkbenchV2ScopeView(
      controller,
      'org-1',
      'workspace-new',
      'system-new',
    )
    assert.deepEqual(nextRender.snapshot.plans, [])
    assert.deepEqual(nextRender.snapshot.runs, [])
    assert.equal(nextRender.snapshot.loading, true)

    await controller.setScope('org-1', 'workspace-new', 'system-new')
    oldPlans.resolve({ success: true, data: [plan({ workspaceId: 'workspace-old', systemId: 'system-old' })] })
    oldRuns.resolve({ success: true, data: [run({ workspaceId: 'workspace-old', systemId: 'system-old' })] })
    await oldLoad

    assert.deepEqual(controller.getSnapshot().plans.map((item) => item.id), ['plan-new'])
    assert.deepEqual(controller.getSnapshot().runs.map((item) => item.id), ['run-new'])
  })
})
