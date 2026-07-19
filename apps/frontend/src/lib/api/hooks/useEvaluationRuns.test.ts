import assert from 'node:assert/strict'
import test, { afterEach, describe } from 'node:test'

import { ApiClient, type ApiResponse } from '../api-client'
import { API_ENDPOINTS } from '../endpoints'
import {
  EvaluationApiRequestError,
  StaleEvaluationResultError,
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
  postImpl: (endpoint: string, data?: unknown) => Promise<ApiResponse<unknown>>,
) {
  const calls: ApiCall[] = []
  const client: EvaluationApiClient = {
    async get<T>(endpoint: string) {
      calls.push({ method: 'GET', endpoint })
      return await getImpl(endpoint) as ApiResponse<T>
    },
    async post<T>(endpoint: string, data?: unknown) {
      calls.push({ method: 'POST', endpoint, data })
      return await postImpl(endpoint, data) as ApiResponse<T>
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
    assert.deepEqual(controller.getSnapshot(), { plans: [], runs: [], loading: false, error: null })
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
    assert.deepEqual(controller.getSnapshot(), { plans: [], runs: [], loading: true, error: null })
    assert.deepEqual(calls.map(({ method, endpoint }) => [method, endpoint]), [
      ['GET', '/api/v1/ai-governance/organizations/org-1/systems/system-1/evaluation-plans'],
      ['GET', '/api/v1/ai-governance/organizations/org-1/systems/system-1/evaluation-runs'],
    ])

    plansResponse.resolve({ success: true, data: [plan()] })
    runsResponse.resolve({ success: true, data: [run()] })
    await loading

    assert.deepEqual(controller.getSnapshot(), { plans: [plan()], runs: [run()], loading: false, error: null })
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
    assert.deepEqual(controller.getSnapshot().plans, [])
    assert.deepEqual(controller.getSnapshot().runs, [])
    assert.equal(controller.getSnapshot().error?.message, 'Evaluation plans unavailable')
  })

  test('uses exact mutation endpoints and refreshes only the affected list after success', async () => {
    const { client, calls } = successfulClient()
    const controller = createEvaluationRunsController(client)
    await controller.setScope('org-1', 'system-1')
    calls.length = 0

    await controller.createPlan(createPlanInput)
    assert.deepEqual(calls.splice(0), [
      { method: 'POST', endpoint: API_ENDPOINTS.aiGovernance.evaluationPlans('org-1', 'system-1'), data: createPlanInput },
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
      { method: 'POST', endpoint: API_ENDPOINTS.aiGovernance.evaluationPlanRuns('org-1', 'system-1', 'plan-1'), data: { trigger: 'release_gate' } },
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
      },
    ])
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
    firstDetail.resolve({ success: false, error: 'The superseded detail request failed.' })
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
})
