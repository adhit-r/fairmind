'use client'

import { useCallback, useEffect, useMemo, useRef, useState } from 'react'
import { z } from 'zod'

import type { ApiError, ApiResponse } from '../api-client'

const evaluatorSourceTypeSchema = z.enum(['fairmind_worker', 'external_provider'])
const evaluatorRegistrationStatusSchema = z.enum(['pending', 'approved', 'rejected', 'revoked'])

const evaluatorRegistrationSchema = z.strictObject({
  id: z.string().min(1),
  organizationId: z.string().min(1),
  evaluatorId: z.string().min(1),
  sourceType: evaluatorSourceTypeSchema,
  adapterName: z.string().min(1),
  adapterVersion: z.string().min(1),
  resultContractVersion: z.string().min(1),
  issuerId: z.string().min(1),
  signingKeyId: z.string().min(1),
  bindingHash: z.string().regex(/^[a-f0-9]{64}$/),
  status: evaluatorRegistrationStatusSchema,
  submittedBy: z.string().min(1),
  submittedAt: z.string().min(1),
  reviewedBy: z.string().nullable(),
  reviewedAt: z.string().nullable(),
  reviewRationale: z.string().nullable(),
  revokedBy: z.string().nullable(),
  revokedAt: z.string().nullable(),
  revocationRationale: z.string().nullable(),
})

export type EvaluatorSourceType = z.infer<typeof evaluatorSourceTypeSchema>
export type EvaluatorRegistrationStatus = z.infer<typeof evaluatorRegistrationStatusSchema>
export type EvaluatorRegistration = z.infer<typeof evaluatorRegistrationSchema>

export type EvaluatorCatalogState = 'disabled' | 'loading' | 'empty' | 'ready' | 'denied' | 'unavailable'

export type EvaluatorCatalogDisabledReason = 'feature_disabled' | 'organization_required' | 'catalog_route_disabled'

export const EVALUATOR_CATALOG_PAGE_SIZE = 25

export interface EvaluatorCatalogPageRequest {
  limit: number
  offset: number
}

export interface EvaluatorCatalogPage extends EvaluatorCatalogPageRequest {
  hasMore: boolean
}

export interface EvaluatorCatalogSnapshot {
  state: EvaluatorCatalogState
  organizationId: string | null
  registrations: EvaluatorRegistration[]
  page: EvaluatorCatalogPage | null
  error: Error | null
  disabledReason: EvaluatorCatalogDisabledReason | null
  canRetry: boolean
}

/**
 * A catalog source is deliberately separate from a browser preference. The
 * caller supplies an organization ID only after it has been authorized by the
 * current session, and every response is checked against that exact scope.
 */
export interface EvaluatorCatalogSource {
  list(organizationId: string, page: EvaluatorCatalogPageRequest): Promise<ApiResponse<unknown>>
}

export interface EvaluatorCatalogApiClient {
  get<T>(endpoint: string): Promise<ApiResponse<T>>
}

/**
 * Build the real API-backed source from an explicit route contract. Tests can
 * inject a source directly; runtime callers should use this factory rather
 * than fabricate catalog records locally.
 */
export function createEvaluatorCatalogSource(
  client: EvaluatorCatalogApiClient,
  listEndpoint: (organizationId: string, page: EvaluatorCatalogPageRequest) => string,
): EvaluatorCatalogSource {
  return {
    list: (organizationId, page) => client.get<unknown>(listEndpoint(organizationId, page)),
  }
}

export class EvaluatorCatalogRequestError extends Error {
  readonly status?: number
  readonly code?: string
  readonly detail?: string
  readonly canRetry?: boolean

  constructor(message: string, apiError?: ApiError) {
    super(message)
    this.name = 'EvaluatorCatalogRequestError'
    this.status = apiError?.status
    this.code = apiError?.code
    this.detail = apiError?.detail
    this.canRetry = apiError?.canRetry
  }
}

export class EvaluatorCatalogScopeMismatchError extends Error {
  constructor(reason: string) {
    super(`The evaluator catalog response does not match the active organization scope: ${reason}`)
    this.name = 'EvaluatorCatalogScopeMismatchError'
  }
}

export class StaleEvaluatorCatalogResultError extends Error {
  constructor() {
    super('The evaluator catalog request belongs to a superseded organization scope.')
    this.name = 'StaleEvaluatorCatalogResultError'
  }
}

export interface EvaluatorCatalogLoadOptions {
  organizationId?: string
  enabled: boolean
  authorized: boolean
  source?: EvaluatorCatalogSource
}

export interface EvaluatorCatalogController {
  getSnapshot(): EvaluatorCatalogSnapshot
  matchesScope(options: EvaluatorCatalogLoadOptions): boolean
  subscribe(listener: () => void): () => void
  setScope(options: EvaluatorCatalogLoadOptions): Promise<void>
  refresh(): Promise<void>
  nextPage(): Promise<void>
  previousPage(): Promise<void>
}

type EvaluatorCatalogScope = {
  organizationId: string
}

type EvaluatorCatalogConfiguration = {
  enabled: boolean
  authorized: boolean
  source?: EvaluatorCatalogSource
}

function emptySnapshot(
  organizationId: string | null = null,
  overrides: Partial<EvaluatorCatalogSnapshot> = {},
): EvaluatorCatalogSnapshot {
  return {
    state: 'disabled',
    organizationId,
    registrations: [],
    page: null,
    error: null,
    disabledReason: null,
    canRetry: false,
    ...overrides,
  }
}

const evaluatorCatalogPageSchema = z.strictObject({
  items: z.array(evaluatorRegistrationSchema),
  limit: z.number().int().positive(),
  offset: z.number().int().nonnegative(),
  hasMore: z.boolean(),
})

type EvaluatorCatalogResponsePage = z.infer<typeof evaluatorCatalogPageSchema>

function responseData(response: ApiResponse<unknown>): EvaluatorCatalogResponsePage {
  if (!response.success || response.data === undefined) {
    throw new EvaluatorCatalogRequestError(
      response.error || response.message || 'Evaluator catalog request failed.',
      response.apiError,
    )
  }

  return evaluatorCatalogPageSchema.parse(response.data)
}

function asError(reason: unknown): Error {
  return reason instanceof Error ? reason : new Error('Evaluator catalog request failed.')
}

function sameConfiguration(
  left: EvaluatorCatalogConfiguration | null,
  right: EvaluatorCatalogConfiguration,
): boolean {
  return left?.enabled === right.enabled
    && left?.authorized === right.authorized
    && left?.source === right.source
}

function assertResponseScope(
  registrations: EvaluatorRegistration[],
  scope: EvaluatorCatalogScope,
) {
  for (const registration of registrations) {
    if (registration.organizationId !== scope.organizationId) {
      throw new EvaluatorCatalogScopeMismatchError('organization identifier')
    }
  }
}

function assertResponsePage(
  response: EvaluatorCatalogResponsePage,
  requestedPage: EvaluatorCatalogPageRequest,
) {
  if (response.limit !== requestedPage.limit) {
    throw new EvaluatorCatalogScopeMismatchError('page limit')
  }
  if (response.offset !== requestedPage.offset) {
    throw new EvaluatorCatalogScopeMismatchError('page offset')
  }
  if (response.items.length === 0 && response.hasMore) {
    throw new EvaluatorCatalogScopeMismatchError('empty page with more records')
  }
}

class DefaultEvaluatorCatalogController implements EvaluatorCatalogController {
  private snapshot = emptySnapshot()
  private scope: EvaluatorCatalogScope | null = null
  private configuration: EvaluatorCatalogConfiguration | null = null
  private rawOrganizationId: string | undefined
  private pageRequest: EvaluatorCatalogPageRequest = {
    limit: EVALUATOR_CATALOG_PAGE_SIZE,
    offset: 0,
  }
  private scopeGeneration = 0
  private listGeneration = 0
  private readonly listeners = new Set<() => void>()

  getSnapshot = () => this.snapshot

  matchesScope = (options: EvaluatorCatalogLoadOptions) => (
    this.rawOrganizationId === options.organizationId
      && sameConfiguration(this.configuration, options)
  )

  subscribe = (listener: () => void) => {
    this.listeners.add(listener)
    return () => this.listeners.delete(listener)
  }

  private publish(snapshot: EvaluatorCatalogSnapshot) {
    this.snapshot = snapshot
    for (const listener of this.listeners) listener()
  }

  private scopeIsCurrent(scope: EvaluatorCatalogScope, generation: number) {
    return generation === this.scopeGeneration && this.scope?.organizationId === scope.organizationId
  }

  private currentConfiguration(): EvaluatorCatalogConfiguration {
    return this.configuration ?? { enabled: false, authorized: false }
  }

  async setScope(options: EvaluatorCatalogLoadOptions): Promise<void> {
    if (this.matchesScope(options)) return

    this.rawOrganizationId = options.organizationId
    this.configuration = {
      enabled: options.enabled,
      authorized: options.authorized,
      source: options.source,
    }
    this.scopeGeneration += 1
    this.listGeneration += 1
    this.scope = options.organizationId ? { organizationId: options.organizationId } : null
    this.pageRequest = { limit: EVALUATOR_CATALOG_PAGE_SIZE, offset: 0 }

    if (!options.enabled) {
      this.publish(emptySnapshot(this.scope?.organizationId ?? null, {
        state: 'disabled',
        disabledReason: 'feature_disabled',
      }))
      return
    }

    if (!this.scope) {
      this.publish(emptySnapshot(null, {
        state: 'disabled',
        disabledReason: 'organization_required',
      }))
      return
    }

    if (!options.authorized) {
      this.publish(emptySnapshot(this.scope.organizationId, {
        state: 'denied',
        error: new EvaluatorCatalogRequestError('Evaluator catalog access is denied for this organization.'),
      }))
      return
    }

    if (!options.source) {
      this.publish(emptySnapshot(this.scope.organizationId, {
        state: 'unavailable',
        error: new EvaluatorCatalogRequestError('The evaluator catalog API is not configured for this deployment.'),
      }))
      return
    }

    await this.refresh()
  }

  async refresh(): Promise<void> {
    const scope = this.scope
    const configuration = this.currentConfiguration()
    const source = configuration.source
    if (!scope || !configuration.enabled || !configuration.authorized || !source) return

    const scopeGeneration = this.scopeGeneration
    const listGeneration = ++this.listGeneration
    const pageRequest = this.pageRequest
    this.publish(emptySnapshot(scope.organizationId, {
      state: 'loading',
      page: { ...pageRequest, hasMore: false },
    }))

    try {
      const response = await source.list(scope.organizationId, pageRequest)
      if (!this.scopeIsCurrent(scope, scopeGeneration) || listGeneration !== this.listGeneration) return

      const responsePage = responseData(response)
      assertResponsePage(responsePage, pageRequest)
      assertResponseScope(responsePage.items, scope)
      this.publish({
        state: responsePage.items.length === 0 ? 'empty' : 'ready',
        organizationId: scope.organizationId,
        registrations: responsePage.items,
        page: {
          limit: responsePage.limit,
          offset: responsePage.offset,
          hasMore: responsePage.hasMore,
        },
        error: null,
        disabledReason: null,
        canRetry: false,
      })
    } catch (reason) {
      if (!this.scopeIsCurrent(scope, scopeGeneration) || listGeneration !== this.listGeneration) return

      const error = asError(reason)
      const denied = error instanceof EvaluatorCatalogRequestError && error.status === 403
      const routeDisabled = error instanceof EvaluatorCatalogRequestError
        && error.status === 404
        && error.code === 'assurance_feature_disabled'
      this.publish(emptySnapshot(scope.organizationId, {
        state: denied ? 'denied' : routeDisabled ? 'disabled' : 'unavailable',
        error,
        disabledReason: routeDisabled ? 'catalog_route_disabled' : null,
        canRetry: !denied && !routeDisabled && (!(error instanceof EvaluatorCatalogRequestError) || error.canRetry !== false),
      }))
    }
  }

  async nextPage(): Promise<void> {
    const page = this.snapshot.page
    if (!page?.hasMore) return
    this.pageRequest = { limit: page.limit, offset: page.offset + page.limit }
    await this.refresh()
  }

  async previousPage(): Promise<void> {
    const page = this.snapshot.page
    if (!page || page.offset === 0) return
    this.pageRequest = { limit: page.limit, offset: Math.max(0, page.offset - page.limit) }
    await this.refresh()
  }
}

export function createEvaluatorCatalogController(): EvaluatorCatalogController {
  return new DefaultEvaluatorCatalogController()
}

export interface EvaluatorCatalogScopeView {
  readonly snapshot: EvaluatorCatalogSnapshot
  refresh(): Promise<void>
  nextPage(): Promise<void>
  previousPage(): Promise<void>
}

function pendingScopeSnapshot(options: EvaluatorCatalogLoadOptions): EvaluatorCatalogSnapshot {
  if (!options.enabled) {
    return emptySnapshot(options.organizationId ?? null, {
      state: 'disabled',
      disabledReason: 'feature_disabled',
    })
  }
  if (!options.organizationId) {
    return emptySnapshot(null, {
      state: 'disabled',
      disabledReason: 'organization_required',
    })
  }
  if (!options.authorized) {
    return emptySnapshot(options.organizationId, {
      state: 'denied',
      error: new EvaluatorCatalogRequestError('Evaluator catalog access is denied for this organization.'),
    })
  }
  if (!options.source) {
    return emptySnapshot(options.organizationId, {
      state: 'unavailable',
      error: new EvaluatorCatalogRequestError('The evaluator catalog API is not configured for this deployment.'),
    })
  }
  return emptySnapshot(options.organizationId, {
    state: 'loading',
    page: { limit: EVALUATOR_CATALOG_PAGE_SIZE, offset: 0, hasMore: false },
  })
}

export function createEvaluatorCatalogScopeView(
  controller: EvaluatorCatalogController,
  options: EvaluatorCatalogLoadOptions,
): EvaluatorCatalogScopeView {
  const inputScopeIsCurrent = () => controller.matchesScope(options)
  return {
    get snapshot() {
      return inputScopeIsCurrent() ? controller.getSnapshot() : pendingScopeSnapshot(options)
    },
    async refresh() {
      if (!inputScopeIsCurrent()) throw new StaleEvaluatorCatalogResultError()
      await controller.refresh()
    },
    async nextPage() {
      if (!inputScopeIsCurrent()) throw new StaleEvaluatorCatalogResultError()
      await controller.nextPage()
    },
    async previousPage() {
      if (!inputScopeIsCurrent()) throw new StaleEvaluatorCatalogResultError()
      await controller.previousPage()
    },
  }
}

export function useEvaluatorCatalog(options: EvaluatorCatalogLoadOptions) {
  const controllerRef = useRef<EvaluatorCatalogController | null>(null)
  if (!controllerRef.current) controllerRef.current = createEvaluatorCatalogController()
  const controller = controllerRef.current
  const [, setSnapshot] = useState<EvaluatorCatalogSnapshot>(controller.getSnapshot())
  const stableOptions = useMemo(() => ({
    organizationId: options.organizationId,
    enabled: options.enabled,
    authorized: options.authorized,
    source: options.source,
  }), [options.authorized, options.enabled, options.organizationId, options.source])
  const scopeView = useMemo(
    () => createEvaluatorCatalogScopeView(controller, stableOptions),
    [controller, stableOptions],
  )

  useEffect(() => controller.subscribe(() => setSnapshot(controller.getSnapshot())), [controller])
  useEffect(() => {
    void controller.setScope(stableOptions)
  }, [controller, stableOptions])

  const refresh = useCallback(() => scopeView.refresh(), [scopeView])
  const nextPage = useCallback(() => scopeView.nextPage(), [scopeView])
  const previousPage = useCallback(() => scopeView.previousPage(), [scopeView])

  return {
    ...scopeView.snapshot,
    refresh,
    nextPage,
    previousPage,
  }
}
