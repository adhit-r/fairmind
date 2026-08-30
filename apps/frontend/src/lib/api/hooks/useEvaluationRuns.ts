'use client'

import { useCallback, useEffect, useMemo, useRef, useState } from 'react'
import { z } from 'zod'

import { apiClient, type ApiError, type ApiResponse } from '../api-client'
import { API_ENDPOINTS } from '../endpoints'

const evaluationTargetKindSchema = z.enum([
  'predictive_model',
  'llm_application',
  'agent',
  'code_generator',
  'image_generator',
  'audio_model',
  'video_model',
  'multimodal_system',
])
const lifecyclePhaseSchema = z.enum(['pre_deploy', 'realtime', 'post_deploy'])
const executionDepthSchema = z.enum(['inline', 'deep', 'hybrid'])
const enforcementModeSchema = z.enum(['advisory', 'human_approval', 'automatic'])
const deliveryModeSchema = z.enum(['fairmind_worker', 'external_provider', 'imported_report'])
const evaluationTriggerSchema = z.enum(['manual', 'ci', 'scheduled', 'release_gate', 'incident', 'integration_sync'])
const technicalStatusSchema = z.enum(['awaiting_evidence', 'running', 'succeeded', 'failed', 'cancelled'])
const governanceVerdictSchema = z.enum(['approved', 'conditional', 'review', 'blocked', 'insufficient'])
const evaluationComponentSchema = z.enum([
  'model',
  'prompts_rag',
  'output',
  'tools',
  'trajectory',
  'application_controls',
  'deployment_context',
])
const evaluationRiskDimensionSchema = z.enum([
  'safety',
  'security',
  'fairness',
  'privacy',
  'reliability',
  'governance',
])

const evaluationLayerVerdictsSchema = z.strictObject({
  components: z.partialRecord(evaluationComponentSchema, governanceVerdictSchema).optional(),
  dimensions: z.partialRecord(evaluationRiskDimensionSchema, governanceVerdictSchema).optional(),
})

const evaluationPlanSchema = z.strictObject({
  id: z.string(),
  contractVersion: z.literal('1.0.0'),
  orgId: z.string(),
  workspaceId: z.string(),
  systemId: z.string(),
  name: z.string(),
  targetKind: evaluationTargetKindSchema,
  lifecyclePhases: z.array(lifecyclePhaseSchema),
  executionDepth: executionDepthSchema,
  enforcementMode: enforcementModeSchema,
  deliveryMode: deliveryModeSchema,
  suiteRefs: z.array(z.string()),
  status: z.enum(['draft', 'active', 'archived']),
  createdBy: z.string(),
  updatedBy: z.string(),
  createdAt: z.string(),
  updatedAt: z.string(),
})

const evaluationPreflightSchema = z.strictObject({
  planId: z.string(),
  canPrepareRun: z.boolean(),
  fairmindExecutionAvailable: z.boolean(),
  code: z.enum([
    'automatic_enforcement_disabled',
    'executor_unavailable',
    'evidence_link_required',
    'legacy_evidence_linking_disabled',
  ]),
  message: z.string(),
  nextAction: z.string(),
})

const evaluationRunSchema = z.strictObject({
  id: z.string(),
  contractVersion: z.literal('1.0.0'),
  orgId: z.string(),
  workspaceId: z.string(),
  systemId: z.string(),
  planId: z.string(),
  trigger: evaluationTriggerSchema,
  technicalStatus: technicalStatusSchema,
  overallVerdict: governanceVerdictSchema,
  layerVerdicts: evaluationLayerVerdictsSchema,
  linkedEvidenceRunId: z.string().nullable(),
  linkedPassportRevisionId: z.string().nullable(),
  linkedBy: z.string().nullable(),
  linkedAt: z.string().nullable(),
  requestedBy: z.string(),
  startedAt: z.string().nullable(),
  completedAt: z.string().nullable(),
  failureCode: z.string().nullable(),
  failureMessage: z.string().nullable(),
  createdAt: z.string(),
  updatedAt: z.string(),
})

const evaluationPlanListSchema = z.array(evaluationPlanSchema)
const evaluationRunListSchema = z.array(evaluationRunSchema)

const createEvaluationPlanInputSchema = z.strictObject({
  name: z.string(),
  targetKind: evaluationTargetKindSchema,
  lifecyclePhases: z.array(lifecyclePhaseSchema),
  executionDepth: executionDepthSchema,
  enforcementMode: enforcementModeSchema,
  deliveryMode: deliveryModeSchema,
  suiteRefs: z.array(z.string()),
})

const passportRevisionLinkInputSchema = z.strictObject({
  evidenceRunId: z.string(),
  passportRevisionId: z.string(),
})

export type EvaluationTargetKind = z.infer<typeof evaluationTargetKindSchema>
export type LifecyclePhase = z.infer<typeof lifecyclePhaseSchema>
export type ExecutionDepth = z.infer<typeof executionDepthSchema>
export type EnforcementMode = z.infer<typeof enforcementModeSchema>
export type DeliveryMode = z.infer<typeof deliveryModeSchema>
export type EvaluationTrigger = z.infer<typeof evaluationTriggerSchema>
export type TechnicalStatus = z.infer<typeof technicalStatusSchema>
export type GovernanceVerdict = z.infer<typeof governanceVerdictSchema>
export type EvaluationComponent = z.infer<typeof evaluationComponentSchema>
export type EvaluationRiskDimension = z.infer<typeof evaluationRiskDimensionSchema>
export type EvaluationLayerVerdicts = z.infer<typeof evaluationLayerVerdictsSchema>
export type EvaluationPlan = z.infer<typeof evaluationPlanSchema>
export type EvaluationPreflight = z.infer<typeof evaluationPreflightSchema>
export type EvaluationRun = z.infer<typeof evaluationRunSchema>
export type CreateEvaluationPlanInput = z.infer<typeof createEvaluationPlanInputSchema>
export type PassportRevisionLinkInput = z.infer<typeof passportRevisionLinkInputSchema>

export interface EvaluationApiClient {
  get<T>(endpoint: string): Promise<ApiResponse<T>>
  post<T>(
    endpoint: string,
    data?: unknown,
    options?: { enableRetry?: boolean },
  ): Promise<ApiResponse<T>>
}

export class EvaluationApiRequestError extends Error {
  readonly status?: number
  readonly code?: string
  readonly detail?: string
  readonly nextAction?: string

  constructor(message: string, apiError?: ApiError) {
    super(message)
    this.name = 'EvaluationApiRequestError'
    this.status = apiError?.status
    this.code = apiError?.code
    this.detail = apiError?.detail
    this.nextAction = apiError?.nextAction
  }
}

export class StaleEvaluationResultError extends Error {
  constructor() {
    super('The evaluation result belongs to a superseded scope or run request.')
    this.name = 'StaleEvaluationResultError'
  }
}

export interface EvaluationRunsSnapshot {
  plans: EvaluationPlan[]
  runs: EvaluationRun[]
  plansLoaded: boolean
  loading: boolean
  error: Error | null
}

export interface EvaluationRunsController {
  getSnapshot(): EvaluationRunsSnapshot
  matchesScope(orgId?: string, systemId?: string): boolean
  subscribe(listener: () => void): () => void
  setScope(orgId?: string, systemId?: string): Promise<void>
  refresh(): Promise<void>
  createPlan(input: CreateEvaluationPlanInput): Promise<EvaluationPlan>
  activatePlan(planId: string): Promise<EvaluationPlan>
  loadPreflight(planId: string): Promise<EvaluationPreflight>
  createRun(planId: string, trigger?: EvaluationTrigger): Promise<EvaluationRun>
  getRun(runId: string): Promise<EvaluationRun>
  linkPassportRevision(runId: string, input: PassportRevisionLinkInput): Promise<EvaluationRun>
}

type EvaluationScope = {
  orgId: string
  systemId: string
}

const emptySnapshot = (): EvaluationRunsSnapshot => ({
  plans: [],
  runs: [],
  plansLoaded: false,
  loading: false,
  error: null,
})

export interface EvaluationRunsScopeView {
  readonly snapshot: EvaluationRunsSnapshot
  run<T>(operation: (controller: EvaluationRunsController) => Promise<T>): Promise<T>
}

export function createEvaluationRunsScopeView(
  controller: EvaluationRunsController,
  orgId?: string,
  systemId?: string,
): EvaluationRunsScopeView {
  const inputScopeIsCurrent = () => controller.matchesScope(orgId, systemId)
  return {
    get snapshot() {
      return inputScopeIsCurrent()
        ? controller.getSnapshot()
        : { ...emptySnapshot(), loading: Boolean(orgId && systemId) }
    },
    async run<T>(operation: (scopedController: EvaluationRunsController) => Promise<T>) {
      if (!inputScopeIsCurrent()) throw new StaleEvaluationResultError()
      return operation(controller)
    },
  }
}

function responseData<T>(response: ApiResponse<unknown>, schema: z.ZodType<T>): T {
  if (!response.success || response.data === undefined) {
    throw new EvaluationApiRequestError(
      response.error || response.message || 'Evaluation request failed',
      response.apiError,
    )
  }
  return schema.parse(response.data)
}

function asError(reason: unknown): Error {
  return reason instanceof Error ? reason : new Error('Evaluation request failed')
}

function sameScope(left: EvaluationScope | null, right: EvaluationScope | null) {
  return left?.orgId === right?.orgId && left?.systemId === right?.systemId
}

function requireResponseScope<T extends EvaluationScope>(value: T, scope: EvaluationScope): T {
  if (!sameScope(value, scope)) {
    throw new EvaluationApiRequestError('Evaluation response scope does not match the request.')
  }
  return value
}

function requireResponseId(
  actual: string | null,
  expected: string,
  kind: 'plan' | 'run' | 'evidence run' | 'passport revision',
) {
  if (actual !== expected) {
    throw new EvaluationApiRequestError(`Evaluation response ${kind} does not match the request.`)
  }
}

class DefaultEvaluationRunsController implements EvaluationRunsController {
  private snapshot = emptySnapshot()
  private scope: EvaluationScope | null = null
  private rawOrgId: string | undefined
  private rawSystemId: string | undefined
  private scopeGeneration = 0
  private planGeneration = 0
  private runGeneration = 0
  private detailGeneration = 0
  private fullRefreshGeneration = 0
  private readonly listeners = new Set<() => void>()

  constructor(private readonly client: EvaluationApiClient) {}

  getSnapshot = () => this.snapshot

  matchesScope = (orgId?: string, systemId?: string) => (
    orgId === this.rawOrgId && systemId === this.rawSystemId
  )

  subscribe = (listener: () => void) => {
    this.listeners.add(listener)
    return () => {
      this.listeners.delete(listener)
    }
  }

  private publish(snapshot: EvaluationRunsSnapshot) {
    this.snapshot = snapshot
    for (const listener of this.listeners) listener()
  }

  private requireScope(): EvaluationScope {
    if (!this.scope) {
      throw new EvaluationApiRequestError('Select an organization and AI system before evaluating.')
    }
    return this.scope
  }

  private scopeIsCurrent(scope: EvaluationScope, generation: number) {
    return generation === this.scopeGeneration && sameScope(scope, this.scope)
  }

  async setScope(orgId?: string, systemId?: string): Promise<void> {
    if (orgId === this.rawOrgId && systemId === this.rawSystemId) return

    this.rawOrgId = orgId
    this.rawSystemId = systemId
    this.scopeGeneration += 1
    this.planGeneration += 1
    this.runGeneration += 1
    this.detailGeneration += 1
    this.fullRefreshGeneration += 1
    this.scope = orgId && systemId ? { orgId, systemId } : null
    this.publish(emptySnapshot())

    if (this.scope) await this.refresh()
  }

  async refresh(): Promise<void> {
    if (!this.scope) {
      this.publish(emptySnapshot())
      return
    }

    const scope = this.scope
    const scopeGeneration = this.scopeGeneration
    const planGeneration = ++this.planGeneration
    const runGeneration = ++this.runGeneration
    const fullRefreshGeneration = ++this.fullRefreshGeneration
    this.publish({ ...this.snapshot, loading: true, error: null })

    const [plansResult, runsResult] = await Promise.allSettled([
      this.client.get<unknown>(API_ENDPOINTS.aiGovernance.evaluationPlans(scope.orgId, scope.systemId)),
      this.client.get<unknown>(API_ENDPOINTS.aiGovernance.evaluationRuns(scope.orgId, scope.systemId)),
    ])
    if (
      !this.scopeIsCurrent(scope, scopeGeneration)
      || fullRefreshGeneration !== this.fullRefreshGeneration
    ) return

    let nextSnapshot = this.snapshot
    let nextError = nextSnapshot.error
    if (planGeneration === this.planGeneration) {
      try {
        if (plansResult.status === 'rejected') throw plansResult.reason
        const plans = responseData(plansResult.value, evaluationPlanListSchema)
          .map((plan) => requireResponseScope(plan, scope))
        nextSnapshot = { ...nextSnapshot, plans, plansLoaded: true }
      } catch (reason) {
        nextSnapshot = { ...nextSnapshot, plans: [], plansLoaded: false }
        nextError ||= asError(reason)
      }
    }
    if (runGeneration === this.runGeneration) {
      try {
        if (runsResult.status === 'rejected') throw runsResult.reason
        const runs = responseData(runsResult.value, evaluationRunListSchema)
          .map((run) => requireResponseScope(run, scope))
        nextSnapshot = { ...nextSnapshot, runs }
      } catch (reason) {
        nextSnapshot = { ...nextSnapshot, runs: [] }
        nextError ||= asError(reason)
      }
    }
    this.publish({ ...nextSnapshot, loading: false, error: nextError })
  }

  private async refreshPlans(scope: EvaluationScope, scopeGeneration: number): Promise<void> {
    const generation = ++this.planGeneration
    try {
      const response = await this.client.get<unknown>(
        API_ENDPOINTS.aiGovernance.evaluationPlans(scope.orgId, scope.systemId),
      )
      const plans = responseData(response, evaluationPlanListSchema)
        .map((plan) => requireResponseScope(plan, scope))
      if (!this.scopeIsCurrent(scope, scopeGeneration) || generation !== this.planGeneration) {
        throw new StaleEvaluationResultError()
      }
      this.publish({ ...this.snapshot, plans, plansLoaded: true, loading: false, error: null })
    } catch (reason) {
      if (!this.scopeIsCurrent(scope, scopeGeneration) || generation !== this.planGeneration) {
        throw new StaleEvaluationResultError()
      }
      const error = asError(reason)
      this.publish({ ...this.snapshot, plansLoaded: false, loading: false, error })
      throw error
    }
  }

  private async refreshRuns(scope: EvaluationScope, scopeGeneration: number): Promise<void> {
    const generation = ++this.runGeneration
    try {
      const response = await this.client.get<unknown>(
        API_ENDPOINTS.aiGovernance.evaluationRuns(scope.orgId, scope.systemId),
      )
      const runs = responseData(response, evaluationRunListSchema)
        .map((run) => requireResponseScope(run, scope))
      if (!this.scopeIsCurrent(scope, scopeGeneration) || generation !== this.runGeneration) {
        throw new StaleEvaluationResultError()
      }
      this.publish({ ...this.snapshot, runs, loading: false, error: null })
    } catch (reason) {
      if (!this.scopeIsCurrent(scope, scopeGeneration) || generation !== this.runGeneration) {
        throw new StaleEvaluationResultError()
      }
      const error = asError(reason)
      this.publish({ ...this.snapshot, loading: false, error })
      throw error
    }
  }

  private async settlePostCommitRefresh(refresh: Promise<void>): Promise<void> {
    try {
      await refresh
    } catch (reason) {
      if (reason instanceof StaleEvaluationResultError) throw reason
    }
  }

  async createPlan(input: CreateEvaluationPlanInput): Promise<EvaluationPlan> {
    const scope = this.requireScope()
    const scopeGeneration = this.scopeGeneration
    const payload = createEvaluationPlanInputSchema.parse(input)
    const response = await this.client.post<unknown>(
      API_ENDPOINTS.aiGovernance.evaluationPlans(scope.orgId, scope.systemId),
      payload,
      { enableRetry: false },
    )
    const created = responseData(response, evaluationPlanSchema)
    if (!this.scopeIsCurrent(scope, scopeGeneration)) throw new StaleEvaluationResultError()
    requireResponseScope(created, scope)
    await this.settlePostCommitRefresh(this.refreshPlans(scope, scopeGeneration))
    return created
  }

  async activatePlan(planId: string): Promise<EvaluationPlan> {
    const scope = this.requireScope()
    const scopeGeneration = this.scopeGeneration
    const response = await this.client.post<unknown>(
      API_ENDPOINTS.aiGovernance.evaluationPlanActivation(scope.orgId, scope.systemId, planId),
    )
    const activated = responseData(response, evaluationPlanSchema)
    if (!this.scopeIsCurrent(scope, scopeGeneration)) throw new StaleEvaluationResultError()
    requireResponseScope(activated, scope)
    requireResponseId(activated.id, planId, 'plan')
    await this.settlePostCommitRefresh(this.refreshPlans(scope, scopeGeneration))
    return activated
  }

  async loadPreflight(planId: string): Promise<EvaluationPreflight> {
    const scope = this.requireScope()
    const scopeGeneration = this.scopeGeneration
    const response = await this.client.get<unknown>(
      API_ENDPOINTS.aiGovernance.evaluationPlanPreflight(scope.orgId, scope.systemId, planId),
    )
    const result = responseData(response, evaluationPreflightSchema)
    if (!this.scopeIsCurrent(scope, scopeGeneration)) throw new StaleEvaluationResultError()
    requireResponseId(result.planId, planId, 'plan')
    return result
  }

  async createRun(planId: string, trigger: EvaluationTrigger = 'manual'): Promise<EvaluationRun> {
    const scope = this.requireScope()
    const scopeGeneration = this.scopeGeneration
    const payload = { trigger: evaluationTriggerSchema.parse(trigger) }
    const response = await this.client.post<unknown>(
      API_ENDPOINTS.aiGovernance.evaluationPlanRuns(scope.orgId, scope.systemId, planId),
      payload,
      { enableRetry: false },
    )
    const created = responseData(response, evaluationRunSchema)
    if (!this.scopeIsCurrent(scope, scopeGeneration)) throw new StaleEvaluationResultError()
    requireResponseScope(created, scope)
    requireResponseId(created.planId, planId, 'plan')
    await this.settlePostCommitRefresh(this.refreshRuns(scope, scopeGeneration))
    return created
  }

  async getRun(runId: string): Promise<EvaluationRun> {
    const scope = this.requireScope()
    const scopeGeneration = this.scopeGeneration
    const detailGeneration = ++this.detailGeneration
    let response: ApiResponse<unknown>
    try {
      response = await this.client.get<unknown>(
        API_ENDPOINTS.aiGovernance.evaluationRun(scope.orgId, scope.systemId, runId),
      )
    } catch (reason) {
      if (
        !this.scopeIsCurrent(scope, scopeGeneration)
        || detailGeneration !== this.detailGeneration
      ) {
        throw new StaleEvaluationResultError()
      }
      throw reason
    }
    if (
      !this.scopeIsCurrent(scope, scopeGeneration)
      || detailGeneration !== this.detailGeneration
    ) {
      throw new StaleEvaluationResultError()
    }
    const result = requireResponseScope(responseData(response, evaluationRunSchema), scope)
    requireResponseId(result.id, runId, 'run')
    return result
  }

  async linkPassportRevision(runId: string, input: PassportRevisionLinkInput): Promise<EvaluationRun> {
    const scope = this.requireScope()
    const scopeGeneration = this.scopeGeneration
    const payload = passportRevisionLinkInputSchema.parse(input)
    const response = await this.client.post<unknown>(
      API_ENDPOINTS.aiGovernance.evaluationRunPassportLink(scope.orgId, scope.systemId, runId),
      payload,
    )
    const linked = responseData(response, evaluationRunSchema)
    if (!this.scopeIsCurrent(scope, scopeGeneration)) throw new StaleEvaluationResultError()
    requireResponseScope(linked, scope)
    requireResponseId(linked.id, runId, 'run')
    requireResponseId(linked.linkedEvidenceRunId, payload.evidenceRunId, 'evidence run')
    requireResponseId(linked.linkedPassportRevisionId, payload.passportRevisionId, 'passport revision')
    await this.settlePostCommitRefresh(this.refreshRuns(scope, scopeGeneration))
    return linked
  }
}

export function createEvaluationRunsController(
  client: EvaluationApiClient = apiClient,
): EvaluationRunsController {
  return new DefaultEvaluationRunsController(client)
}

export function useEvaluationRuns(orgId?: string, systemId?: string) {
  const controllerRef = useRef<EvaluationRunsController | null>(null)
  if (!controllerRef.current) controllerRef.current = createEvaluationRunsController()
  const controller = controllerRef.current
  const [, setSnapshot] = useState<EvaluationRunsSnapshot>(controller.getSnapshot())
  const scopeView = useMemo(
    () => createEvaluationRunsScopeView(controller, orgId, systemId),
    [controller, orgId, systemId],
  )

  useEffect(() => controller.subscribe(() => setSnapshot(controller.getSnapshot())), [controller])
  useEffect(() => {
    void controller.setScope(orgId, systemId)
  }, [controller, orgId, systemId])

  const refresh = useCallback(() => scopeView.run((scopedController) => scopedController.refresh()), [scopeView])
  const createPlan = useCallback(
    (input: CreateEvaluationPlanInput) => scopeView.run((scopedController) => scopedController.createPlan(input)),
    [scopeView],
  )
  const activatePlan = useCallback(
    (planId: string) => scopeView.run((scopedController) => scopedController.activatePlan(planId)),
    [scopeView],
  )
  const loadPreflight = useCallback(
    (planId: string) => scopeView.run((scopedController) => scopedController.loadPreflight(planId)),
    [scopeView],
  )
  const createRun = useCallback(
    (planId: string, trigger?: EvaluationTrigger) => scopeView.run(
      (scopedController) => scopedController.createRun(planId, trigger),
    ),
    [scopeView],
  )
  const getRun = useCallback(
    (runId: string) => scopeView.run((scopedController) => scopedController.getRun(runId)),
    [scopeView],
  )
  const linkPassportRevision = useCallback(
    (runId: string, input: PassportRevisionLinkInput) => scopeView.run(
      (scopedController) => scopedController.linkPassportRevision(runId, input),
    ),
    [scopeView],
  )

  return {
    ...scopeView.snapshot,
    refresh,
    createPlan,
    activatePlan,
    loadPreflight,
    createRun,
    getRun,
    linkPassportRevision,
  }
}
