import assert from 'node:assert/strict'
import test, { describe } from 'node:test'

import type { ApiResponse } from '../api-client'
import {
  EvaluatorCatalogRequestError,
  EvaluatorCatalogScopeMismatchError,
  createEvaluatorCatalogController,
  createEvaluatorCatalogSource,
  type EvaluatorCatalogSource,
  type EvaluatorRegistration,
} from './useEvaluatorCatalog'

function deferred<T>() {
  let resolve!: (value: T) => void
  let reject!: (reason?: unknown) => void
  const promise = new Promise<T>((resolvePromise, rejectPromise) => {
    resolve = resolvePromise
    reject = rejectPromise
  })
  return { promise, resolve, reject }
}

function registration(overrides: Partial<EvaluatorRegistration> = {}): EvaluatorRegistration {
  return {
    id: 'registration-1',
    organizationId: 'org-1',
    evaluatorId: 'inspect-agent-safety',
    sourceType: 'external_provider',
    adapterName: 'inspect',
    adapterVersion: '0.3.0',
    resultContractVersion: '1.0.0',
    issuerId: 'issuer-a',
    signingKeyId: 'key-a',
    bindingHash: 'a'.repeat(64),
    status: 'pending',
    submittedBy: 'user-1',
    submittedAt: '2026-08-09T00:00:00Z',
    reviewedBy: null,
    reviewedAt: null,
    reviewRationale: null,
    revokedBy: null,
    revokedAt: null,
    revocationRationale: null,
    ...overrides,
  }
}

function page(items: EvaluatorRegistration[], overrides: Partial<{ limit: number; offset: number; hasMore: boolean }> = {}) {
  return {
    items,
    limit: 25,
    offset: 0,
    hasMore: false,
    ...overrides,
  }
}

function source(
  list: (organizationId: string, pageRequest: { limit: number; offset: number }) => Promise<ApiResponse<unknown>>,
): EvaluatorCatalogSource {
  return { list }
}

describe('evaluator catalog scope authority', () => {
  test('keeps the feature default-off and does not request registrations', async () => {
    const calls: string[] = []
    const controller = createEvaluatorCatalogController()

    await controller.setScope({
      organizationId: 'org-1',
      enabled: false,
      authorized: true,
      source: source(async (organizationId) => {
        calls.push(organizationId)
        return { success: true, data: page([]) }
      }),
    })

    assert.equal(controller.getSnapshot().state, 'disabled')
    assert.equal(controller.getSnapshot().disabledReason, 'feature_disabled')
    assert.deepEqual(controller.getSnapshot().registrations, [])
    assert.deepEqual(calls, [])
  })

  test('does not request records without the exact catalog authorization', async () => {
    const calls: string[] = []
    const controller = createEvaluatorCatalogController()

    await controller.setScope({
      organizationId: 'org-1',
      enabled: true,
      authorized: false,
      source: source(async (organizationId) => {
        calls.push(organizationId)
        return { success: true, data: page([]) }
      }),
    })

    assert.equal(controller.getSnapshot().state, 'denied')
    assert.deepEqual(controller.getSnapshot().registrations, [])
    assert.deepEqual(calls, [])
  })

  test('represents an authorized empty catalog without synthetic registrations', async () => {
    const controller = createEvaluatorCatalogController()

    await controller.setScope({
      organizationId: 'org-1',
      enabled: true,
      authorized: true,
      source: source(async () => ({ success: true, data: page([]) })),
    })

    assert.equal(controller.getSnapshot().state, 'empty')
    assert.equal(controller.getSnapshot().organizationId, 'org-1')
    assert.deepEqual(controller.getSnapshot().registrations, [])
    assert.equal(controller.getSnapshot().error, null)
  })

  test('represents a server permission response as denied and displays no records', async () => {
    const controller = createEvaluatorCatalogController()

    await controller.setScope({
      organizationId: 'org-1',
      enabled: true,
      authorized: true,
      source: source(async () => ({
        success: false,
        error: 'Evaluator catalog access is forbidden.',
        apiError: {
          message: 'Evaluator catalog access is forbidden.',
          status: 403,
          type: 'client',
          canRetry: false,
          code: 'evaluation_catalog_admin_forbidden',
        },
      })),
    })

    assert.equal(controller.getSnapshot().state, 'denied')
    assert.deepEqual(controller.getSnapshot().registrations, [])
    assert.equal(controller.getSnapshot().canRetry, false)
    assert.equal((controller.getSnapshot().error as EvaluatorCatalogRequestError).code, 'evaluation_catalog_admin_forbidden')
  })

  test('maps a feature-gated catalog route response to disabled rather than unavailable', async () => {
    const controller = createEvaluatorCatalogController()

    await controller.setScope({
      organizationId: 'org-1',
      enabled: true,
      authorized: true,
      source: source(async () => ({
        success: false,
        error: 'Evaluator catalog administration is not enabled.',
        apiError: {
          message: 'Evaluator catalog administration is not enabled.',
          status: 404,
          type: 'client',
          canRetry: false,
          code: 'assurance_feature_disabled',
        },
      })),
    })

    assert.equal(controller.getSnapshot().state, 'disabled')
    assert.equal(controller.getSnapshot().disabledReason, 'catalog_route_disabled')
    assert.deepEqual(controller.getSnapshot().registrations, [])
  })

  test('keeps an unrelated 404 unavailable instead of calling the catalog disabled', async () => {
    const controller = createEvaluatorCatalogController()

    await controller.setScope({
      organizationId: 'org-1',
      enabled: true,
      authorized: true,
      source: source(async () => ({
        success: false,
        error: 'The evaluator registration was not found in this organization.',
        apiError: {
          message: 'The evaluator registration was not found in this organization.',
          status: 404,
          type: 'client',
          canRetry: false,
          code: 'evaluator_registration_not_found',
        },
      })),
    })

    assert.equal(controller.getSnapshot().state, 'unavailable')
    assert.equal(controller.getSnapshot().disabledReason, null)
    assert.deepEqual(controller.getSnapshot().registrations, [])
  })

  test('rejects a schema-valid registration from another organization', async () => {
    const controller = createEvaluatorCatalogController()

    await controller.setScope({
      organizationId: 'org-1',
      enabled: true,
      authorized: true,
      source: source(async () => ({
        success: true,
        data: page([registration({ organizationId: 'org-other' })]),
      })),
    })

    assert.equal(controller.getSnapshot().state, 'unavailable')
    assert.deepEqual(controller.getSnapshot().registrations, [])
    assert.ok(controller.getSnapshot().error instanceof EvaluatorCatalogScopeMismatchError)
  })

  test('does not allow a late prior-organization response to replace the active catalog', async () => {
    const first = deferred<ApiResponse<unknown>>()
    const second = deferred<ApiResponse<unknown>>()
    const controller = createEvaluatorCatalogController()
    const catalog = source(async (organizationId) => {
      if (organizationId === 'org-1') return first.promise
      return second.promise
    })

    const firstScope = controller.setScope({
      organizationId: 'org-1',
      enabled: true,
      authorized: true,
      source: catalog,
    })
    const secondScope = controller.setScope({
      organizationId: 'org-2',
      enabled: true,
      authorized: true,
      source: catalog,
    })

    second.resolve({ success: true, data: page([registration({ organizationId: 'org-2', id: 'registration-2' })]) })
    await secondScope
    first.resolve({ success: true, data: page([registration()]) })
    await firstScope

    assert.equal(controller.getSnapshot().state, 'ready')
    assert.equal(controller.getSnapshot().organizationId, 'org-2')
    assert.deepEqual(controller.getSnapshot().registrations.map((item) => item.id), ['registration-2'])
  })

  test('uses the returned bounded page and does not accept a response for another offset', async () => {
    const controller = createEvaluatorCatalogController()

    await controller.setScope({
      organizationId: 'org-1',
      enabled: true,
      authorized: true,
      source: source(async () => ({
        success: true,
        data: page([registration()], { offset: 25 }),
      })),
    })

    assert.equal(controller.getSnapshot().state, 'unavailable')
    assert.deepEqual(controller.getSnapshot().registrations, [])
    assert.ok(controller.getSnapshot().error instanceof EvaluatorCatalogScopeMismatchError)
  })

  test('exposes bounded page navigation without presenting a partial response as the whole catalog', async () => {
    const calls: Array<{ organizationId: string; limit: number; offset: number }> = []
    const controller = createEvaluatorCatalogController()
    const catalog = source(async (organizationId, pageRequest) => {
      calls.push({ organizationId, ...pageRequest })
      if (pageRequest.offset === 0) {
        return { success: true, data: page([registration()], { hasMore: true }) }
      }
      return {
        success: true,
        data: page([registration({ id: 'registration-2' })], { offset: 25, hasMore: false }),
      }
    })

    await controller.setScope({
      organizationId: 'org-1',
      enabled: true,
      authorized: true,
      source: catalog,
    })
    assert.deepEqual(controller.getSnapshot().page, { limit: 25, offset: 0, hasMore: true })

    await controller.nextPage()
    assert.deepEqual(controller.getSnapshot().page, { limit: 25, offset: 25, hasMore: false })
    assert.deepEqual(controller.getSnapshot().registrations.map((item) => item.id), ['registration-2'])

    await controller.previousPage()
    assert.deepEqual(controller.getSnapshot().page, { limit: 25, offset: 0, hasMore: true })
    assert.deepEqual(calls, [
      { organizationId: 'org-1', limit: 25, offset: 0 },
      { organizationId: 'org-1', limit: 25, offset: 25 },
      { organizationId: 'org-1', limit: 25, offset: 0 },
    ])
  })

  test('keeps real API routes explicit in the production source factory', async () => {
    const endpoints: string[] = []
    const catalog = createEvaluatorCatalogSource({
      async get<T>(endpoint: string) {
        endpoints.push(endpoint)
        return { success: true, data: page([]) as T }
      },
    }, (organizationId, pageRequest) => `/api/v1/ai-governance/organizations/${organizationId}/evaluation-v2/evaluator-catalog/registrations?limit=${pageRequest.limit}&offset=${pageRequest.offset}`)

    await catalog.list('org-1', { limit: 25, offset: 0 })

    assert.deepEqual(endpoints, [
      '/api/v1/ai-governance/organizations/org-1/evaluation-v2/evaluator-catalog/registrations?limit=25&offset=0',
    ])
  })

  test('retains a server conflict code in the unavailable state without retaining data', async () => {
    const controller = createEvaluatorCatalogController()

    await controller.setScope({
      organizationId: 'org-1',
      enabled: true,
      authorized: true,
      source: source(async () => ({
        success: false,
        error: 'The registration changed before this request completed.',
        apiError: {
          message: 'The registration changed before this request completed.',
          status: 409,
          type: 'client',
          canRetry: false,
          code: 'evaluator_registration_transition_invalid',
        },
      })),
    })

    assert.equal(controller.getSnapshot().state, 'unavailable')
    assert.deepEqual(controller.getSnapshot().registrations, [])
    assert.equal((controller.getSnapshot().error as EvaluatorCatalogRequestError).code, 'evaluator_registration_transition_invalid')
  })
})
