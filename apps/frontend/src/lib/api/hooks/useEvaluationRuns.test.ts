import assert from 'node:assert/strict'
import test, { afterEach, describe } from 'node:test'

import { ApiClient, type ApiResponse } from '../api-client'
import { API_ENDPOINTS } from '../endpoints'
import {
  EvaluationApiRequestError,
  StaleEvaluationResultError,
  createEvaluationRunsScopeView,
  createEvaluationRunsController,
  type CreateEvaluationPlanInput,
  type EvaluationApiClient,
  type EvaluationPlan,
  type EvaluationPreflight,
  type EvaluationRun,
} from './useEvaluationRuns'

type ApiCall = {
  method: 'GET' | 'POST'
  endpoint: string
  data?: unknown
  options?: { enableRetry?: boolean }
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

function plan(overrides: Partial<EvaluationPlan> = {}): EvaluationPlan {
  return {
    id: 'plan-1',
    orgId: 'org-1',
    workspaceId: 'workspace-1',
    systemId: 'system-1',
    name: 'Release assurance',
    targetKind: 'llm_application',
    lifecyclePhases: ['pre_deploy', 'realtime'],
    executionDepth: 'hybrid',
    enforcementMode: 'human_approval',
    deliveryMode: 'external_provider',
    suiteRefs: ['fairmind/prompt-safety@1.0.0'],
    status: 'active',
    createdBy: 'user-1',
    updatedBy: 'user-1',
    createdAt: '2026-07-19T00:00:00Z',
    updatedAt: '2026-07-19T00:00:00Z',
    ...overrides,
  }
}

function run(overrides: Partial<EvaluationRun> = {}): EvaluationRun {
  return {
    id: 'run-1',
    orgId: 'org-1',
    workspaceId: 'workspace-1',
    systemId: 'system-1',
    planId: 'plan-1',
    trigger: 'manual',
    technicalStatus: 'awaiting_evidence',
    overallVerdict: 'insufficient',
    layerVerdicts: {},
    linkedEvidenceRunId: null,
    linkedPassportRevisionId: null,
    linkedBy: null,
    linkedAt: null,
    requestedBy: 'user-1',
    startedAt: null,
    completedAt: null,
    failureCode: null,
    failureMessage: null,
    createdAt: '2026-07-19T00:00:00Z',
    updatedAt: '2026-07-19T00:00:00Z',
    ...overrides,
  }
}

function preflight(overrides: Partial<EvaluationPreflight> = {}): EvaluationPreflight {
  return {
    planId: 'plan-1',
    canPrepareRun: true,
    fairmindExecutionAvailable: false,
    code: 'evidence_link_required',
    message: 'Prepare the run and link externally generated evidence.',
    nextAction: 'Run the suite externally, ingest its Passport, and link the revision.',
    ...overrides,
  }
}

function fakeClient(
  getImpl: (endpoint: string) => Promise<ApiResponse<unknown>>,
  postImpl: (
    endpoint: string,
    data?: unknown,
    options?: { enableRetry?: boolean },
  ) => Promise<ApiResponse<unknown>>,
) {
  const calls: ApiCall[] = []
  const client: EvaluationApiClient = {
    async get<T>(endpoint: string) {
      calls.push({ method: 'GET', endpoint })
      return await getImpl(endpoint) as ApiResponse<T>
    },
    async post<T>(endpoint: string, data?: unknown, options?: { enableRetry?: boolean }) {
      calls.push({ method: 'POST', endpoint, data, ...(options ? { options } : {}) })
      return await postImpl(endpoint, data, options) as ApiResponse<T>
    },
  }
  return { client, calls }
}

function successfulClient() {
  return fakeClient(
    async (endpoint) => {
      if (endpoint.endsWith('/preflight')) return { success: true, data: preflight() }
      if (endpoint.endsWith('/evaluation-plans')) return { success: true, data: [plan()] }
      if (endpoint.endsWith('/evaluation-runs')) return { success: true, data: [run()] }
      if (endpoint.includes('/evaluation-runs/')) return { success: true, data: run({ id: endpoint.split('/').at(-1) }) }
      throw new Error(`Unexpected GET ${endpoint}`)
    },
    async (endpoint) => {
      if (endpoint.endsWith('/activate')) return { success: true, data: plan({ status: 'active' }) }
      if (endpoint.endsWith('/evaluation-plans')) return { success: true, data: plan({ status: 'draft' }) }
      if (endpoint.endsWith('/runs')) return { success: true, data: run() }
      if (endpoint.endsWith('/evidence-passport-link')) {
        return {
          success: true,
          data: run({
            technicalStatus: 'succeeded',
            overallVerdict: 'review',
            linkedEvidenceRunId: 'evidence-run-1',
            linkedPassportRevisionId: 'revision-1',
          }),
        }
      }
      throw new Error(`Unexpected POST ${endpoint}`)
    },
  )
}

const createPlanInput: CreateEvaluationPlanInput = {
  name: 'Release assurance',
  targetKind: 'llm_application',
  lifecyclePhases: ['pre_deploy', 'realtime'],
  executionDepth: 'hybrid',
  enforcementMode: 'human_approval',
  deliveryMode: 'external_provider',
  suiteRefs: ['fairmind/prompt-safety@1.0.0'],
}

describe('evaluation endpoint contract', () => {
  test('builds every Task 2 endpoint with organization and system scope', () => {
    assert.equal(API_ENDPOINTS.aiGovernance.evaluationPlans('org-1', 'system-2'),
      '/api/v1/ai-governance/organizations/org-1/systems/system-2/evaluation-plans',
    )
    assert.equal(API_ENDPOINTS.aiGovernance.evaluationPlanActivation('org-1', 'system-2', 'plan-3'),
      '/api/v1/ai-governance/organizations/org-1/systems/system-2/evaluation-plans/plan-3/activate',
    )
    assert.equal(API_ENDPOINTS.aiGovernance.evaluationPlanPreflight('org-1', 'system-2', 'plan-3'),
      '/api/v1/ai-governance/organizations/org-1/systems/system-2/evaluation-plans/plan-3/preflight',
    )
    assert.equal(API_ENDPOINTS.aiGovernance.evaluationPlanRuns('org-1', 'system-2', 'plan-3'),
      '/api/v1/ai-governance/organizations/org-1/systems/system-2/evaluation-plans/plan-3/runs',
    )
    assert.equal(API_ENDPOINTS.aiGovernance.evaluationRuns('org-1', 'system-2'),
      '/api/v1/ai-governance/organizations/org-1/systems/system-2/evaluation-runs',
    )
    assert.equal(API_ENDPOINTS.aiGovernance.evaluationRun('org-1', 'system-2', 'run-4'),
      '/api/v1/ai-governance/organizations/org-1/systems/system-2/evaluation-runs/run-4',
    )
    assert.equal(API_ENDPOINTS.aiGovernance.evaluationRunPassportLink('org-1', 'system-2', 'run-4'),
      '/api/v1/ai-governance/organizations/org-1/systems/system-2/evaluation-runs/run-4/evidence-passport-link',
    )
  })
})

describe('evaluation runs controller', () => {
  test('issues no request until both scope identifiers exist', async () => {
    const { client, calls } = successfulClient()
    const controller = createEvaluationRunsController(client)

    await controller.setScope(undefined, undefined)
    await controller.setScope('org-1', undefined)
    await controller.setScope(undefined, 'system-1')

    assert.deepEqual(calls, [])
    assert.deepEqual(controller.getSnapshot(), {
      plans: [], runs: [], plansLoaded: false, loading: false, error: null,
    })
  })

  test('loads scoped plan and run lists together and exposes loading separately from empty', async () => {
    const plansResponse = deferred<ApiResponse<unknown>>()
    const runsResponse = deferred<ApiResponse<unknown>>()
    const { client, calls } = fakeClient(
      async (endpoint) => endpoint.endsWith('/evaluation-plans') ? plansResponse.promise : runsResponse.promise,
      async () => { throw new Error('No POST expected') },
    )
    const controller = createEvaluationRunsController(client)

    const loading = controller.setScope('org-1', 'system-1')
    assert.deepEqual(controller.getSnapshot(), {
      plans: [], runs: [], plansLoaded: false, loading: true, error: null,
    })
    assert.deepEqual(calls.map(({ method, endpoint }) => [method, endpoint]), [
      ['GET', '/api/v1/ai-governance/organizations/org-1/systems/system-1/evaluation-plans'],
      ['GET', '/api/v1/ai-governance/organizations/org-1/systems/system-1/evaluation-runs'],
    ])

    plansResponse.resolve({ success: true, data: [plan()] })
    runsResponse.resolve({ success: true, data: [run()] })
    await loading

    assert.deepEqual(controller.getSnapshot(), {
      plans: [plan()], runs: [run()], plansLoaded: true, loading: false, error: null,
    })
  })

  test('invalidates stale list responses when either scope identifier changes', async () => {
    const oldPlans = deferred<ApiResponse<unknown>>()
    const oldRuns = deferred<ApiResponse<unknown>>()
    const { client } = fakeClient(
      async (endpoint) => {
        if (endpoint.includes('/org-old/')) {
          return endpoint.endsWith('/evaluation-plans') ? oldPlans.promise : oldRuns.promise
        }
        const scopedPlan = plan({ id: 'plan-new', orgId: 'org-new', systemId: 'system-old' })
        const scopedRun = run({ id: 'run-new', orgId: 'org-new', systemId: 'system-old' })
        return { success: true, data: endpoint.endsWith('/evaluation-plans') ? [scopedPlan] : [scopedRun] }
      },
      async () => { throw new Error('No POST expected') },
    )
    const controller = createEvaluationRunsController(client)

    const staleLoad = controller.setScope('org-old', 'system-old')
    await controller.setScope('org-new', 'system-old')
    oldPlans.resolve({ success: true, data: [plan({ id: 'stale-plan', orgId: 'org-old', systemId: 'system-old' })] })
    oldRuns.resolve({ success: true, data: [run({ id: 'stale-run', orgId: 'org-old', systemId: 'system-old' })] })
    await staleLoad

    assert.deepEqual(controller.getSnapshot().plans.map(({ id }) => id), ['plan-new'])
    assert.deepEqual(controller.getSnapshot().runs.map(({ id }) => id), ['run-new'])
  })

  test('masks the previous scope and blocks its actions during the render before scope effects run', async () => {
    const { client, calls } = successfulClient()
    const controller = createEvaluationRunsController(client)
    await controller.setScope('org-1', 'system-1')
    calls.length = 0

    const nextRender = createEvaluationRunsScopeView(
      controller,
      'org-1',
      'system-2',
    )

    assert.deepEqual(nextRender.snapshot, {
      plans: [], runs: [], plansLoaded: false, loading: true, error: null,
    })
    await assert.rejects(
      nextRender.run((scopedController) => scopedController.createRun('plan-1')),
      StaleEvaluationResultError,
    )
    assert.deepEqual(calls, [])
  })

  test('keeps server errors distinct from loading and empty success', async () => {
    const { client } = fakeClient(
      async (endpoint) => endpoint.endsWith('/evaluation-plans')
        ? { success: false, error: 'Evaluation plans unavailable' }
        : { success: true, data: [] },
      async () => { throw new Error('No POST expected') },
    )
    const controller = createEvaluationRunsController(client)

    await controller.setScope('org-1', 'system-1')

    assert.equal(controller.getSnapshot().loading, false)
    assert.equal(controller.getSnapshot().plansLoaded, false)
    assert.deepEqual(controller.getSnapshot().plans, [])
    assert.deepEqual(controller.getSnapshot().runs, [])
    assert.equal(controller.getSnapshot().error?.message, 'Evaluation plans unavailable')
  })

  test('keeps a targeted plan refresh terminal and prevents an older full refresh from overwriting it', async () => {
    const fullPlans = deferred<ApiResponse<unknown>>()
    const fullRuns = deferred<ApiResponse<unknown>>()
    const targetedPlans = deferred<ApiResponse<unknown>>()
    const targetedRequested = deferred<void>()
    const committedPlan = plan({ id: 'plan-committed', updatedAt: '2026-07-19T03:00:00Z' })
    let phase: 'initial' | 'overlap' = 'initial'
    let overlappingPlanReads = 0
    const { client } = fakeClient(
      async (endpoint) => {
        if (phase === 'initial') {
          return endpoint.endsWith('/evaluation-plans')
            ? { success: true, data: [plan()] }
            : { success: true, data: [run()] }
        }
        if (endpoint.endsWith('/evaluation-plans')) {
          overlappingPlanReads += 1
          if (overlappingPlanReads === 1) return fullPlans.promise
          targetedRequested.resolve(undefined)
          return targetedPlans.promise
        }
        return fullRuns.promise
      },
      async (endpoint) => endpoint.endsWith('/activate')
        ? { success: true, data: committedPlan }
        : { success: false, error: `Unexpected POST ${endpoint}` },
    )
    const controller = createEvaluationRunsController(client)
    await controller.setScope('org-1', 'system-1')
    phase = 'overlap'

    const fullRefresh = controller.refresh()
    const activation = controller.activatePlan('plan-1')
    await targetedRequested.promise
    targetedPlans.resolve({ success: true, data: [committedPlan] })

    assert.equal((await activation).id, 'plan-committed')
    assert.equal(controller.getSnapshot().loading, false)
    assert.deepEqual(controller.getSnapshot().plans.map(({ id }) => id), ['plan-committed'])
    assert.deepEqual(controller.getSnapshot().runs.map(({ id }) => id), ['run-1'])

    fullPlans.resolve({ success: true, data: [plan({ id: 'plan-stale' })] })
    fullRuns.resolve({ success: true, data: [run({ id: 'run-from-full-refresh' })] })
    await fullRefresh

    assert.equal(controller.getSnapshot().loading, false)
    assert.deepEqual(controller.getSnapshot().plans.map(({ id }) => id), ['plan-committed'])
    assert.deepEqual(controller.getSnapshot().runs.map(({ id }) => id), ['run-from-full-refresh'])
  })

  test('keeps a committed run truthful when its overlapping targeted refresh fails', async () => {
    const fullPlans = deferred<ApiResponse<unknown>>()
    const fullRuns = deferred<ApiResponse<unknown>>()
    const targetedRuns = deferred<ApiResponse<unknown>>()
    const targetedRequested = deferred<void>()
    const committedRun = run({ id: 'run-committed' })
    let phase: 'initial' | 'overlap' = 'initial'
    let overlappingRunReads = 0
    const { client } = fakeClient(
      async (endpoint) => {
        if (phase === 'initial') {
          return endpoint.endsWith('/evaluation-plans')
            ? { success: true, data: [plan()] }
            : { success: true, data: [run()] }
        }
        if (endpoint.endsWith('/evaluation-runs')) {
          overlappingRunReads += 1
          if (overlappingRunReads === 1) return fullRuns.promise
          targetedRequested.resolve(undefined)
          return targetedRuns.promise
        }
        return fullPlans.promise
      },
      async (endpoint) => endpoint.endsWith('/runs')
        ? { success: true, data: committedRun }
        : { success: false, error: `Unexpected POST ${endpoint}` },
    )
    const controller = createEvaluationRunsController(client)
    await controller.setScope('org-1', 'system-1')
    phase = 'overlap'

    const fullRefresh = controller.refresh()
    const creation = controller.createRun('plan-1')
    await targetedRequested.promise
    targetedRuns.resolve({ success: false, error: 'Run list refresh failed after commit.' })

    assert.equal((await creation).id, 'run-committed')
    assert.equal(controller.getSnapshot().loading, false)
    assert.equal(controller.getSnapshot().error?.message, 'Run list refresh failed after commit.')
    assert.deepEqual(controller.getSnapshot().runs.map(({ id }) => id), ['run-1'])

    fullPlans.resolve({ success: true, data: [plan({ id: 'plan-from-full-refresh' })] })
    fullRuns.resolve({ success: true, data: [run({ id: 'run-stale' })] })
    await fullRefresh

    assert.equal(controller.getSnapshot().loading, false)
    assert.equal(controller.getSnapshot().error?.message, 'Run list refresh failed after commit.')
    assert.deepEqual(controller.getSnapshot().plans.map(({ id }) => id), ['plan-from-full-refresh'])
    assert.deepEqual(controller.getSnapshot().runs.map(({ id }) => id), ['run-1'])
  })

  test('returns a committed plan while exposing a failed follow-up list refresh without optimistic data', async () => {
    const committedPlan = plan({ id: 'plan-committed', status: 'draft' })
    let planReads = 0
    const { client } = fakeClient(
      async (endpoint) => {
        if (endpoint.endsWith('/evaluation-plans')) {
          planReads += 1
          if (planReads > 1) return { success: false, error: 'Plan refresh unavailable.' }
          return { success: true, data: [plan()] }
        }
        return { success: true, data: [run()] }
      },
      async () => ({ success: true, data: committedPlan }),
    )
    const controller = createEvaluationRunsController(client)
    await controller.setScope('org-1', 'system-1')

    const created = await controller.createPlan(createPlanInput)

    assert.equal(created.id, 'plan-committed')
    assert.equal(controller.getSnapshot().loading, false)
    assert.equal(controller.getSnapshot().error?.message, 'Plan refresh unavailable.')
    assert.deepEqual(controller.getSnapshot().plans.map(({ id }) => id), ['plan-1'])
  })

  test('does not swallow stale scope changes when a post-commit refresh rejects', async () => {
    const oldRefresh = deferred<ApiResponse<unknown>>()
    const oldRefreshRequested = deferred<void>()
    let oldPlanReads = 0
    const { client } = fakeClient(
      async (endpoint) => {
        if (endpoint.includes('/org-2/')) {
          return endpoint.endsWith('/evaluation-plans')
            ? { success: true, data: [plan({ orgId: 'org-2', systemId: 'system-2' })] }
            : { success: true, data: [run({ orgId: 'org-2', systemId: 'system-2' })] }
        }
        if (endpoint.endsWith('/evaluation-plans')) {
          oldPlanReads += 1
          if (oldPlanReads > 1) {
            oldRefreshRequested.resolve(undefined)
            return oldRefresh.promise
          }
          return { success: true, data: [plan()] }
        }
        return { success: true, data: [run()] }
      },
      async () => ({ success: true, data: plan({ id: 'plan-committed', status: 'draft' }) }),
    )
    const controller = createEvaluationRunsController(client)
    await controller.setScope('org-1', 'system-1')

    const creation = controller.createPlan(createPlanInput)
    await oldRefreshRequested.promise
    await controller.setScope('org-2', 'system-2')
    oldRefresh.reject(new Error('Old scope network failure'))

    await assert.rejects(creation, StaleEvaluationResultError)
    assert.deepEqual(controller.getSnapshot().plans.map(({ orgId }) => orgId), ['org-2'])
  })

  test('uses exact mutation endpoints and refreshes only the affected list after success', async () => {
    const { client, calls } = successfulClient()
    const controller = createEvaluationRunsController(client)
    await controller.setScope('org-1', 'system-1')
    calls.length = 0

    await controller.createPlan(createPlanInput)
    assert.deepEqual(calls.splice(0), [
      {
        method: 'POST',
        endpoint: API_ENDPOINTS.aiGovernance.evaluationPlans('org-1', 'system-1'),
        data: createPlanInput,
        options: { enableRetry: false },
      },
      { method: 'GET', endpoint: API_ENDPOINTS.aiGovernance.evaluationPlans('org-1', 'system-1') },
    ])

    await controller.activatePlan('plan-1')
    assert.deepEqual(calls.splice(0), [
      { method: 'POST', endpoint: API_ENDPOINTS.aiGovernance.evaluationPlanActivation('org-1', 'system-1', 'plan-1'), data: undefined },
      { method: 'GET', endpoint: API_ENDPOINTS.aiGovernance.evaluationPlans('org-1', 'system-1') },
    ])

    await controller.loadPreflight('plan-1')
    assert.deepEqual(calls.splice(0), [
      { method: 'GET', endpoint: API_ENDPOINTS.aiGovernance.evaluationPlanPreflight('org-1', 'system-1', 'plan-1') },
    ])

    await controller.createRun('plan-1', 'release_gate')
    assert.deepEqual(calls.splice(0), [
      {
        method: 'POST',
        endpoint: API_ENDPOINTS.aiGovernance.evaluationPlanRuns('org-1', 'system-1', 'plan-1'),
        data: { trigger: 'release_gate' },
        options: { enableRetry: false },
      },
      { method: 'GET', endpoint: API_ENDPOINTS.aiGovernance.evaluationRuns('org-1', 'system-1') },
    ])

    const linkInput = { evidenceRunId: 'evidence-run-1', passportRevisionId: 'revision-1' }
    await controller.linkPassportRevision('run-1', linkInput)
    assert.deepEqual(calls.splice(0), [
      { method: 'POST', endpoint: API_ENDPOINTS.aiGovernance.evaluationRunPassportLink('org-1', 'system-1', 'run-1'), data: linkInput },
      { method: 'GET', endpoint: API_ENDPOINTS.aiGovernance.evaluationRuns('org-1', 'system-1') },
    ])
  })

  test('preserves actionable executor conflicts and never inserts a fake run', async () => {
    const { client, calls } = fakeClient(
      async (endpoint) => endpoint.endsWith('/evaluation-plans')
        ? { success: true, data: [plan()] }
        : { success: true, data: [] },
      async () => ({
        success: false,
        error: 'No FairMind executor is configured for this delivery mode.',
        apiError: {
          message: 'No FairMind executor is configured for this delivery mode.',
          status: 409,
          type: 'client',
          canRetry: false,
          code: 'executor_unavailable',
          detail: 'No FairMind executor is configured for this delivery mode.',
          nextAction: 'Select external_provider or imported_report.',
        },
      }),
    )
    const controller = createEvaluationRunsController(client)
    await controller.setScope('org-1', 'system-1')
    calls.length = 0

    try {
      await controller.createRun('plan-1')
      throw new Error('Expected createRun to reject')
    } catch (error) {
      assert.ok(error instanceof EvaluationApiRequestError)
      assert.deepEqual({
        status: error.status,
        code: error.code,
        nextAction: error.nextAction,
      }, {
        status: 409,
        code: 'executor_unavailable',
        nextAction: 'Select external_provider or imported_report.',
      })
    }

    assert.deepEqual(controller.getSnapshot().runs, [])
    assert.deepEqual(calls, [
      {
        method: 'POST',
        endpoint: API_ENDPOINTS.aiGovernance.evaluationPlanRuns('org-1', 'system-1', 'plan-1'),
        data: { trigger: 'manual' },
        options: { enableRetry: false },
      },
    ])
  })

  test('does not retry create-plan or create-run POSTs after timeout, network, or server failures', async () => {
    const originalWindow = Object.getOwnPropertyDescriptor(globalThis, 'window')
    const originalLocalStorage = Object.getOwnPropertyDescriptor(globalThis, 'localStorage')
    const originalNavigator = Object.getOwnPropertyDescriptor(globalThis, 'navigator')
    const originalFetch = Object.getOwnPropertyDescriptor(globalThis, 'fetch')
    const setGlobal = (key: PropertyKey, value: unknown) => {
      Object.defineProperty(globalThis, key, { configurable: true, writable: true, value })
    }
    const restoreGlobal = (key: PropertyKey, descriptor: PropertyDescriptor | undefined) => {
      if (descriptor) Object.defineProperty(globalThis, key, descriptor)
      else delete (globalThis as Record<PropertyKey, unknown>)[key]
    }
    const failures = [
      {
        name: 'timeout',
        response: () => {
          const error = new Error('Request timed out')
          error.name = 'AbortError'
          throw error
        },
      },
      {
        name: 'network',
        response: () => { throw new Error('Connection reset') },
      },
      {
        name: 'server',
        response: () => new Response(JSON.stringify({ detail: 'Evaluation service unavailable' }), {
          status: 503,
          headers: { 'Content-Type': 'application/json' },
        }),
      },
    ]

    try {
      for (const failure of failures) {
        for (const mutation of ['createPlan', 'createRun'] as const) {
          let attempts = 0
          setGlobal('window', {})
          setGlobal('localStorage', { getItem: () => null })
          setGlobal('navigator', { onLine: undefined })
          setGlobal('fetch', async () => {
            attempts += 1
            return failure.response()
          })
          const transport = new ApiClient('https://fairmind.test')
          const controller = createEvaluationRunsController({
            async get<T>(endpoint: string) {
              const data = endpoint.endsWith('/evaluation-plans') ? [plan()] : [run()]
              return { success: true, data } as ApiResponse<T>
            },
            async post<T>(
              endpoint: string,
              data?: unknown,
              options?: { enableRetry?: boolean },
            ) {
              return transport.post<T>(endpoint, data, { ...options, retryDelay: 0 })
            },
          })
          await controller.setScope('org-1', 'system-1')

          await assert.rejects(
            mutation === 'createPlan'
              ? controller.createPlan(createPlanInput)
              : controller.createRun('plan-1'),
            EvaluationApiRequestError,
            `${mutation} should expose the ${failure.name} failure`,
          )
          assert.equal(attempts, 1, `${mutation} retried the ${failure.name} failure`)
        }
      }
    } finally {
      restoreGlobal('window', originalWindow)
      restoreGlobal('localStorage', originalLocalStorage)
      restoreGlobal('navigator', originalNavigator)
      restoreGlobal('fetch', originalFetch)
    }
  })

  test('scopes details and rejects stale detail results after run or scope changes', async () => {
    const firstDetail = deferred<ApiResponse<unknown>>()
    const scopedDetail = deferred<ApiResponse<unknown>>()
    const { client, calls } = fakeClient(
      async (endpoint) => {
        if (endpoint.endsWith('/evaluation-plans')) return { success: true, data: [plan()] }
        if (endpoint.endsWith('/evaluation-runs')) return { success: true, data: [run()] }
        if (endpoint.endsWith('/run-old')) return firstDetail.promise
        if (endpoint.includes('/org-1/') && endpoint.endsWith('/run-scope')) return scopedDetail.promise
        return { success: true, data: run({ id: 'run-new' }) }
      },
      async () => { throw new Error('No POST expected') },
    )
    const controller = createEvaluationRunsController(client)
    await controller.setScope('org-1', 'system-1')
    calls.length = 0

    const staleByRun = controller.getRun('run-old')
    assert.equal((await controller.getRun('run-new')).id, 'run-new')
    firstDetail.reject(new Error('The superseded detail request failed.'))
    await assert.rejects(staleByRun, StaleEvaluationResultError)

    const staleByScope = controller.getRun('run-scope')
    await controller.setScope('org-1', 'system-2')
    scopedDetail.resolve({ success: true, data: run({ id: 'run-scope' }) })
    await assert.rejects(staleByScope, StaleEvaluationResultError)

    assert.deepEqual(calls[0], {
      method: 'GET',
      endpoint: API_ENDPOINTS.aiGovernance.evaluationRun('org-1', 'system-1', 'run-old'),
    })
    assert.deepEqual(calls[1], {
      method: 'GET',
      endpoint: API_ENDPOINTS.aiGovernance.evaluationRun('org-1', 'system-1', 'run-new'),
    })
  })

  test('preserves the original rejection for the current detail request', async () => {
    const networkFailure = new Error('Current detail network failure')
    const { client } = fakeClient(
      async (endpoint) => {
        if (endpoint.endsWith('/evaluation-plans')) return { success: true, data: [plan()] }
        if (endpoint.endsWith('/evaluation-runs')) return { success: true, data: [run()] }
        throw networkFailure
      },
      async () => { throw new Error('No POST expected') },
    )
    const controller = createEvaluationRunsController(client)
    await controller.setScope('org-1', 'system-1')

    await assert.rejects(controller.getRun('run-current'), (reason) => reason === networkFailure)
  })

  test('rejects unknown and snake_case backend vocabularies instead of trusting compiled unions', async () => {
    const invalidPlan = { ...plan(), targetKind: 'foundation_model' }
    const { client } = fakeClient(
      async (endpoint) => endpoint.endsWith('/evaluation-plans')
        ? { success: true, data: [invalidPlan] }
        : { success: true, data: [{ ...run(), technical_status: 'succeeded', technicalStatus: undefined }] },
      async () => { throw new Error('No POST expected') },
    )
    const controller = createEvaluationRunsController(client)

    await controller.setScope('org-1', 'system-1')

    assert.deepEqual(controller.getSnapshot().plans, [])
    assert.deepEqual(controller.getSnapshot().runs, [])
    assert.match(controller.getSnapshot().error?.message || '', /targetKind|foundation_model/)
  })

  test('accepts partial component and risk verdict maps', async () => {
    const layeredRun = run({
      layerVerdicts: {
        components: { output: 'conditional' },
        dimensions: { safety: 'review', fairness: 'approved' },
      },
    })
    const { client } = fakeClient(
      async (endpoint) => endpoint.endsWith('/evaluation-plans')
        ? { success: true, data: [plan()] }
        : { success: true, data: [layeredRun] },
      async () => { throw new Error('No POST expected') },
    )
    const controller = createEvaluationRunsController(client)

    await controller.setScope('org-1', 'system-1')

    assert.deepEqual(controller.getSnapshot().runs[0]?.layerVerdicts, layeredRun.layerVerdicts)
  })
})

describe('API workflow error decoding', () => {
  const descriptors = new Map<PropertyKey, PropertyDescriptor | undefined>()

  function replaceGlobal(key: PropertyKey, value: unknown) {
    if (!descriptors.has(key)) descriptors.set(key, Object.getOwnPropertyDescriptor(globalThis, key))
    Object.defineProperty(globalThis, key, { configurable: true, writable: true, value })
  }

  afterEach(() => {
    for (const [key, descriptor] of descriptors) {
      if (descriptor) Object.defineProperty(globalThis, key, descriptor)
      else delete (globalThis as Record<PropertyKey, unknown>)[key]
    }
    descriptors.clear()
  })

  test('keeps a string error and structured status, code, detail, and next action', async () => {
    replaceGlobal('window', {})
    replaceGlobal('localStorage', { getItem: () => null })
    replaceGlobal('navigator', { onLine: undefined })
    replaceGlobal('fetch', async () => new Response(JSON.stringify({
      detail: {
        code: 'executor_unavailable',
        message: 'No FairMind executor is configured.',
        nextAction: 'Choose an external delivery mode.',
      },
    }), { status: 409, headers: { 'Content-Type': 'application/json' } }))
    const client = new ApiClient('https://fairmind.test')

    const response = await client.post('/api/v1/evaluation', {}, { enableRetry: false })

    assert.equal(response.error, 'No FairMind executor is configured.')
    assert.equal(typeof response.error, 'string')
    assert.deepEqual({
      status: response.apiError?.status,
      type: response.apiError?.type,
      code: response.apiError?.code,
      detail: response.apiError?.detail,
      nextAction: response.apiError?.nextAction,
    }, {
      status: 409,
      type: 'client',
      code: 'executor_unavailable',
      detail: 'No FairMind executor is configured.',
      nextAction: 'Choose an external delivery mode.',
    })
  })

  test('keeps legacy FastAPI detail errors as strings without inventing workflow fields', async () => {
    replaceGlobal('window', {})
    replaceGlobal('localStorage', { getItem: () => null })
    replaceGlobal('navigator', { onLine: undefined })
    replaceGlobal('fetch', async () => new Response(JSON.stringify({ detail: 'Plan not found' }), {
      status: 404,
      headers: { 'Content-Type': 'application/json' },
    }))
    const client = new ApiClient('https://fairmind.test')

    const response = await client.get('/api/v1/evaluation', { enableRetry: false })

    assert.equal(response.error, 'Plan not found')
    assert.equal(typeof response.error, 'string')
    assert.equal(response.apiError?.status, 404)
    assert.equal(response.apiError?.detail, 'Plan not found')
    assert.equal(response.apiError?.code, undefined)
    assert.equal(response.apiError?.nextAction, undefined)
  })

  test('preserves workflow status for validation-class HTTP failures', async () => {
    replaceGlobal('window', {})
    replaceGlobal('localStorage', { getItem: () => null })
    replaceGlobal('navigator', { onLine: undefined })
    replaceGlobal('fetch', async () => new Response(JSON.stringify({
      detail: {
        code: 'target_kind_unverifiable',
        message: 'The Passport target cannot be verified for this modality.',
        nextAction: 'Use a compatible evidence target.',
      },
    }), { status: 422, headers: { 'Content-Type': 'application/json' } }))
    const client = new ApiClient('https://fairmind.test')

    const response = await client.post('/api/v1/evaluation', {}, { enableRetry: false })

    assert.equal(response.apiError?.status, 422)
    assert.equal(response.apiError?.type, 'client')
    assert.equal(response.apiError?.code, 'target_kind_unverifiable')
  })

  test('accepts only the documented structured workflow error codes', async () => {
    const codes = [
      'executor_unavailable',
      'fairmind_worker_delivery_disabled',
      'plan_inactive',
      'plan_archived',
      'passport_link_conflict',
      'passport_scope_mismatch',
      'suite_mismatch',
      'target_kind_mismatch',
      'target_kind_unverifiable',
      'passport_snapshot_invalid',
      'evaluation_persistence_failed',
    ] as const
    let responseIndex = 0
    replaceGlobal('window', {})
    replaceGlobal('localStorage', { getItem: () => null })
    replaceGlobal('navigator', { onLine: undefined })
    replaceGlobal('fetch', async () => new Response(JSON.stringify({
      detail: {
        code: codes[responseIndex++],
        message: 'Documented workflow failure.',
        nextAction: 'Follow the documented recovery action.',
      },
    }), { status: 409, headers: { 'Content-Type': 'application/json' } }))
    const client = new ApiClient('https://fairmind.test')

    for (const code of codes) {
      const response = await client.post('/api/v1/evaluation', {}, { enableRetry: false })
      assert.equal(response.apiError?.code, code)
      assert.equal(response.apiError?.nextAction, 'Follow the documented recovery action.')
    }
  })

  test('falls back to non-actionable string errors for malformed structured envelopes', async () => {
    const malformedDetails = [
      {
        code: 'unknown_workflow_code',
        message: 'Malformed workflow failure.',
        nextAction: 'Do not trust this action.',
      },
      {
        code: 'executor_unavailable',
        message: 'Malformed workflow failure.',
        nextAction: 'Do not trust this action.',
        debug: true,
      },
      {
        code: 'executor_unavailable',
        message: 'Malformed workflow failure.',
      },
      {
        code: 'executor_unavailable',
        message: 'Malformed workflow failure.',
        nextAction: 42,
      },
      {
        code: 'executor_unavailable',
        message: 'Malformed workflow failure.',
        next_action: 'Wrong wire casing.',
      },
    ]
    let responseIndex = 0
    replaceGlobal('window', {})
    replaceGlobal('localStorage', { getItem: () => null })
    replaceGlobal('navigator', { onLine: undefined })
    replaceGlobal('fetch', async () => new Response(JSON.stringify({
      detail: malformedDetails[responseIndex++],
    }), { status: 409, headers: { 'Content-Type': 'application/json' } }))
    const client = new ApiClient('https://fairmind.test')

    for (const _detail of malformedDetails) {
      const response = await client.post('/api/v1/evaluation', {}, { enableRetry: false })
      assert.equal(response.error, 'Malformed workflow failure.')
      assert.equal(response.apiError?.status, 409)
      assert.equal(response.apiError?.detail, 'Malformed workflow failure.')
      assert.equal(response.apiError?.code, undefined)
      assert.equal(response.apiError?.nextAction, undefined)
    }
  })
})
