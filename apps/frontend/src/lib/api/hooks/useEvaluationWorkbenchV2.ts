'use client'

import { useCallback, useEffect, useMemo, useRef, useState } from 'react'
import { z } from 'zod'

import { apiClient, type ApiError, type ApiResponse } from '../api-client'
import { API_ENDPOINTS } from '../endpoints'

const technicalStatusSchema = z.enum([
  'awaiting_evidence',
  'queued',
  'leased',
  'running',
  'succeeded',
  'failed',
  'timed_out',
  'cancelled',
])
const evidenceResultStatusSchema = z.enum([
  'pending',
  'passed',
  'passed_with_limitations',
  'failed',
  'informational',
  'error',
  'unavailable',
  'insufficient_data',
  'unknown',
])
const admissionStatusSchema = z.enum([
  'pending',
  'verified',
  'unverified',
  'expired',
  'superseded',
  'rejected',
  'trust_error',
])
const reviewStatusSchema = z.enum(['pending', 'accepted', 'rejected'])
const freshnessStatusSchema = z.enum(['current', 'expiring', 'stale', 'superseded'])
const governanceVerdictSchema = z.enum(['approved', 'conditional', 'review', 'blocked', 'insufficient'])
const lifecyclePhaseSchema = z.enum(['pre_deploy', 'realtime', 'post_deploy'])
const evaluationTargetKindSchema = z.enum([
  'predictive_model',
  'llm_application',
  'agent',
  'code_generator',
  'image_generator',
  'audio_model',
  'video_model',
  'multimodal_system',
  'vision_model',
])

const planSuiteSchema = z.strictObject({
  ordinal: z.number(),
  suiteVersionId: z.string(),
  ownerScope: z.string(),
  suiteRef: z.string(),
  manifestDigest: z.string(),
  configuration: z.record(z.string(), z.unknown()),
  configurationHash: z.string(),
})

const evaluationPlanV2Schema = z.strictObject({
  id: z.string(),
  organizationId: z.string(),
  workspaceId: z.string(),
  systemId: z.string(),
  contractVersion: z.literal('2.0.0'),
  name: z.string(),
  targetVersionId: z.string(),
  targetKind: evaluationTargetKindSchema,
  lifecyclePhases: z.array(lifecyclePhaseSchema),
  executionDepth: z.enum(['inline', 'deep', 'hybrid']),
  enforcementMode: z.enum(['advisory', 'human_approval', 'automatic']),
  deliveryMode: z.enum(['fairmind_worker', 'external_provider', 'imported_report']),
  trustPolicyVersionId: z.string(),
  planContentHash: z.string(),
  suites: z.array(planSuiteSchema),
  status: z.enum(['draft', 'active', 'archived']),
  createdBy: z.string(),
  updatedBy: z.string(),
  createdAt: z.string(),
  updatedAt: z.string(),
})

const suiteEvidenceTrustSchema = z.strictObject({
  sourceType: z.string().nullable(),
  issuerKey: z.string().nullable(),
  signingKeyId: z.string().nullable(),
  signerKeyId: z.string().nullable(),
  signerAlgorithm: z.string().nullable(),
  effectiveExpiresAt: z.string().nullable(),
  reviewedBy: z.string().nullable(),
  reviewedAt: z.string().nullable(),
  admissionReasons: z.array(z.string()).nullable(),
  signingKeyRevocationReason: z.string().nullable(),
})

const suiteExecutionSchema = z.strictObject({
  id: z.string(),
  suiteVersionId: z.string(),
  ownerScope: z.string(),
  ordinal: z.number(),
  technicalStatus: technicalStatusSchema,
  evidenceResultStatus: evidenceResultStatusSchema,
  admissionStatus: admissionStatusSchema,
  reviewStatus: reviewStatusSchema,
  freshnessStatus: freshnessStatusSchema,
  evidenceTrust: suiteEvidenceTrustSchema.nullable(),
  limitations: z.array(z.unknown()),
  failureCode: z.string().nullable(),
  failureMessage: z.string().nullable(),
})

const executionEnvelopeSuiteIdentitySchema = z.object({
  suiteExecutionId: z.string(),
  suiteVersionId: z.string(),
  ownerScope: z.string(),
}).passthrough()

const executionEnvelopeIdentitySchema = z.object({
  schemaVersion: z.literal('2.0.0'),
  envelopeId: z.string(),
  runId: z.string(),
  organizationId: z.string(),
  workspaceId: z.string(),
  systemId: z.string(),
  planId: z.string(),
  suites: z.array(executionEnvelopeSuiteIdentitySchema),
}).passthrough()

const evaluationRunV2Schema = z.strictObject({
  id: z.string(),
  organizationId: z.string(),
  workspaceId: z.string(),
  systemId: z.string(),
  planId: z.string(),
  contractVersion: z.literal('2.0.0'),
  trigger: z.enum(['manual', 'ci', 'scheduled', 'release_gate', 'incident', 'integration_sync']),
  lifecyclePhase: lifecyclePhaseSchema,
  technicalStatus: technicalStatusSchema,
  evidenceOutcome: evidenceResultStatusSchema,
  overallVerdict: governanceVerdictSchema,
  layerVerdictsSchemaVersion: z.literal('1.0.0'),
  layerVerdicts: z.strictObject({
    suites: z.record(z.string(), governanceVerdictSchema),
    modalities: z.record(z.string(), governanceVerdictSchema),
    components: z.record(z.string(), governanceVerdictSchema),
    riskDimensions: z.record(z.string(), governanceVerdictSchema),
  }),
  suiteExecutions: z.array(suiteExecutionSchema),
  envelopeId: z.string(),
  envelope: executionEnvelopeIdentitySchema,
  envelopeHash: z.string(),
  verdictVersion: z.number(),
  requestedBy: z.string(),
  startedAt: z.string().nullable(),
  completedAt: z.string().nullable(),
  failureCode: z.string().nullable(),
  failureMessage: z.string().nullable(),
  createdAt: z.string(),
  updatedAt: z.string(),
})

export type TechnicalStatusV2 = z.infer<typeof technicalStatusSchema>
export type EvidenceResultStatus = z.infer<typeof evidenceResultStatusSchema>
export type AdmissionStatus = z.infer<typeof admissionStatusSchema>
export type ReviewStatus = z.infer<typeof reviewStatusSchema>
export type FreshnessStatus = z.infer<typeof freshnessStatusSchema>
export type GovernanceVerdictV2 = z.infer<typeof governanceVerdictSchema>
export type EvaluationPlanV2 = z.infer<typeof evaluationPlanV2Schema>
export type SuiteExecutionV2 = z.infer<typeof suiteExecutionSchema>
export type EvaluationRunV2 = z.infer<typeof evaluationRunV2Schema>

export interface EvaluationWorkbenchApiClient {
  get<T>(endpoint: string): Promise<ApiResponse<T>>
}

export class EvaluationWorkbenchRequestError extends Error {
  readonly status?: number
  readonly code?: string
  readonly detail?: string

  constructor(message: string, apiError?: ApiError) {
    super(message)
    this.name = 'EvaluationWorkbenchRequestError'
    this.status = apiError?.status
    this.code = apiError?.code
    this.detail = apiError?.detail
  }
}

export class StaleEvaluationWorkbenchResultError extends Error {
  constructor() {
    super('The evaluation workbench request belongs to a superseded scope.')
    this.name = 'StaleEvaluationWorkbenchResultError'
  }
}

export class EvaluationScopeMismatchError extends Error {
  constructor(resource: 'plan' | 'run', reason: string) {
    super(`The ${resource} response does not match the active evaluation scope: ${reason}`)
    this.name = 'EvaluationScopeMismatchError'
  }
}

type EvaluationWorkbenchScope = {
  orgId: string
  workspaceId: string
  systemId: string
}

export interface EvaluationWorkbenchSnapshot {
  plans: EvaluationPlanV2[]
  runs: EvaluationRunV2[]
  plansLoaded: boolean
  runsLoaded: boolean
  loading: boolean
  error: Error | null
}

export interface EvaluationWorkbenchV2Controller {
  getSnapshot(): EvaluationWorkbenchSnapshot
  matchesScope(orgId?: string, workspaceId?: string, systemId?: string): boolean
  subscribe(listener: () => void): () => void
  setScope(orgId?: string, workspaceId?: string, systemId?: string): Promise<void>
  refresh(): Promise<void>
  getPlan(planId: string): Promise<EvaluationPlanV2>
  getRun(runId: string): Promise<EvaluationRunV2>
}

const emptySnapshot = (): EvaluationWorkbenchSnapshot => ({
  plans: [],
  runs: [],
  plansLoaded: false,
  runsLoaded: false,
  loading: false,
  error: null,
})

function responseData<T>(response: ApiResponse<unknown>, schema: z.ZodType<T>): T {
  if (!response.success || response.data === undefined) {
    throw new EvaluationWorkbenchRequestError(
      response.error || response.message || 'Evaluation workbench request failed',
      response.apiError,
    )
  }
  return schema.parse(response.data)
}

function asError(reason: unknown): Error {
  return reason instanceof Error ? reason : new Error('Evaluation workbench request failed')
}

function sameScope(left: EvaluationWorkbenchScope | null, right: EvaluationWorkbenchScope | null) {
  return left?.orgId === right?.orgId
    && left?.workspaceId === right?.workspaceId
    && left?.systemId === right?.systemId
}

function assertPlanScope(
  plan: EvaluationPlanV2,
  scope: EvaluationWorkbenchScope,
  expectedPlanId?: string,
) {
  if (plan.organizationId !== scope.orgId) throw new EvaluationScopeMismatchError('plan', 'organization')
  if (plan.workspaceId !== scope.workspaceId) throw new EvaluationScopeMismatchError('plan', 'workspace')
  if (plan.systemId !== scope.systemId) throw new EvaluationScopeMismatchError('plan', 'system')
  if (expectedPlanId && plan.id !== expectedPlanId) throw new EvaluationScopeMismatchError('plan', 'plan identifier')
}

function assertRunScope(
  run: EvaluationRunV2,
  scope: EvaluationWorkbenchScope,
  expectedRunId?: string,
) {
  if (run.organizationId !== scope.orgId) throw new EvaluationScopeMismatchError('run', 'organization')
  if (run.workspaceId !== scope.workspaceId) throw new EvaluationScopeMismatchError('run', 'workspace')
  if (run.systemId !== scope.systemId) throw new EvaluationScopeMismatchError('run', 'system')
  if (expectedRunId && run.id !== expectedRunId) throw new EvaluationScopeMismatchError('run', 'run identifier')
  const envelope = run.envelope
  if (envelope.envelopeId !== run.envelopeId) throw new EvaluationScopeMismatchError('run', 'envelope identifier')
  if (envelope.runId !== run.id) throw new EvaluationScopeMismatchError('run', 'envelope run identifier')
  if (envelope.organizationId !== run.organizationId) throw new EvaluationScopeMismatchError('run', 'envelope organization')
  if (envelope.workspaceId !== run.workspaceId) throw new EvaluationScopeMismatchError('run', 'envelope workspace')
  if (envelope.systemId !== run.systemId) throw new EvaluationScopeMismatchError('run', 'envelope system')
  if (envelope.planId !== run.planId) throw new EvaluationScopeMismatchError('run', 'envelope plan identifier')

  const envelopeSuites = new Map(envelope.suites.map((suite) => [suite.suiteExecutionId, suite]))
  if (envelopeSuites.size !== envelope.suites.length) {
    throw new EvaluationScopeMismatchError('run', 'duplicate envelope suite execution')
  }
  if (envelopeSuites.size !== run.suiteExecutions.length) {
    throw new EvaluationScopeMismatchError('run', 'envelope suite execution count')
  }
  for (const execution of run.suiteExecutions) {
    const envelopeSuite = envelopeSuites.get(execution.id)
    if (!envelopeSuite) throw new EvaluationScopeMismatchError('run', 'envelope suite execution identifier')
    if (envelopeSuite.suiteVersionId !== execution.suiteVersionId) {
      throw new EvaluationScopeMismatchError('run', 'envelope suite version')
    }
    if (envelopeSuite.ownerScope !== execution.ownerScope) {
      throw new EvaluationScopeMismatchError('run', 'envelope suite owner scope')
    }
  }
}

class DefaultEvaluationWorkbenchV2Controller implements EvaluationWorkbenchV2Controller {
  private snapshot = emptySnapshot()
  private scope: EvaluationWorkbenchScope | null = null
  private rawOrgId: string | undefined
  private rawWorkspaceId: string | undefined
  private rawSystemId: string | undefined
  private scopeGeneration = 0
  private listGeneration = 0
  private planDetailGeneration = 0
  private runDetailGeneration = 0
  private readonly listeners = new Set<() => void>()

  constructor(private readonly client: EvaluationWorkbenchApiClient) {}

  getSnapshot = () => this.snapshot

  matchesScope = (orgId?: string, workspaceId?: string, systemId?: string) => (
    orgId === this.rawOrgId
      && workspaceId === this.rawWorkspaceId
      && systemId === this.rawSystemId
  )

  subscribe = (listener: () => void) => {
    this.listeners.add(listener)
    return () => this.listeners.delete(listener)
  }

  private publish(snapshot: EvaluationWorkbenchSnapshot) {
    this.snapshot = snapshot
    for (const listener of this.listeners) listener()
  }

  private requireScope(): EvaluationWorkbenchScope {
    if (!this.scope) {
      throw new EvaluationWorkbenchRequestError(
        'Select an organization, workspace, and AI system before loading evaluation evidence.',
      )
    }
    return this.scope
  }

  private scopeIsCurrent(scope: EvaluationWorkbenchScope, generation: number) {
    return generation === this.scopeGeneration && sameScope(scope, this.scope)
  }

  async setScope(orgId?: string, workspaceId?: string, systemId?: string): Promise<void> {
    if (this.matchesScope(orgId, workspaceId, systemId)) return

    this.rawOrgId = orgId
    this.rawWorkspaceId = workspaceId
    this.rawSystemId = systemId
    this.scopeGeneration += 1
    this.listGeneration += 1
    this.planDetailGeneration += 1
    this.runDetailGeneration += 1
    this.scope = orgId && workspaceId && systemId ? { orgId, workspaceId, systemId } : null
    this.publish(emptySnapshot())

    if (this.scope) await this.refresh()
  }

  async refresh(): Promise<void> {
    const scope = this.requireScope()
    const scopeGeneration = this.scopeGeneration
    const listGeneration = ++this.listGeneration
    this.publish({ ...this.snapshot, loading: true, error: null })

    const [plansResult, runsResult] = await Promise.allSettled([
      this.client.get<unknown>(API_ENDPOINTS.aiGovernance.evaluationV2Plans(scope.orgId, scope.systemId)),
      this.client.get<unknown>(API_ENDPOINTS.aiGovernance.evaluationV2Runs(scope.orgId, scope.systemId)),
    ])
    if (!this.scopeIsCurrent(scope, scopeGeneration) || listGeneration !== this.listGeneration) return

    let nextSnapshot = this.snapshot
    let nextError: Error | null = null
    try {
      if (plansResult.status === 'rejected') throw plansResult.reason
      const plans = responseData(plansResult.value, z.array(evaluationPlanV2Schema))
      plans.forEach((plan) => assertPlanScope(plan, scope))
      nextSnapshot = { ...nextSnapshot, plans, plansLoaded: true }
    } catch (reason) {
      nextSnapshot = { ...nextSnapshot, plans: [], plansLoaded: false }
      nextError = asError(reason)
    }

    try {
      if (runsResult.status === 'rejected') throw runsResult.reason
      const runs = responseData(runsResult.value, z.array(evaluationRunV2Schema))
      runs.forEach((run) => assertRunScope(run, scope))
      nextSnapshot = { ...nextSnapshot, runs, runsLoaded: true }
    } catch (reason) {
      nextSnapshot = { ...nextSnapshot, runs: [], runsLoaded: false }
      nextError ||= asError(reason)
    }

    this.publish({ ...nextSnapshot, loading: false, error: nextError })
  }

  async getPlan(planId: string): Promise<EvaluationPlanV2> {
    const scope = this.requireScope()
    const scopeGeneration = this.scopeGeneration
    const detailGeneration = ++this.planDetailGeneration
    let response: ApiResponse<unknown>
    try {
      response = await this.client.get<unknown>(
        API_ENDPOINTS.aiGovernance.evaluationV2Plan(scope.orgId, scope.systemId, planId),
      )
    } catch (reason) {
      if (!this.scopeIsCurrent(scope, scopeGeneration) || detailGeneration !== this.planDetailGeneration) {
        throw new StaleEvaluationWorkbenchResultError()
      }
      throw reason
    }
    if (!this.scopeIsCurrent(scope, scopeGeneration) || detailGeneration !== this.planDetailGeneration) {
      throw new StaleEvaluationWorkbenchResultError()
    }
    const plan = responseData(response, evaluationPlanV2Schema)
    assertPlanScope(plan, scope, planId)
    return plan
  }

  async getRun(runId: string): Promise<EvaluationRunV2> {
    const scope = this.requireScope()
    const scopeGeneration = this.scopeGeneration
    const detailGeneration = ++this.runDetailGeneration
    let response: ApiResponse<unknown>
    try {
      response = await this.client.get<unknown>(
        API_ENDPOINTS.aiGovernance.evaluationV2Run(scope.orgId, scope.systemId, runId),
      )
    } catch (reason) {
      if (!this.scopeIsCurrent(scope, scopeGeneration) || detailGeneration !== this.runDetailGeneration) {
        throw new StaleEvaluationWorkbenchResultError()
      }
      throw reason
    }
    if (!this.scopeIsCurrent(scope, scopeGeneration) || detailGeneration !== this.runDetailGeneration) {
      throw new StaleEvaluationWorkbenchResultError()
    }
    const run = responseData(response, evaluationRunV2Schema)
    assertRunScope(run, scope, runId)
    return run
  }
}

export interface EvaluationWorkbenchV2ScopeView {
  readonly snapshot: EvaluationWorkbenchSnapshot
  run<T>(operation: (controller: EvaluationWorkbenchV2Controller) => Promise<T>): Promise<T>
}

export function createEvaluationWorkbenchV2ScopeView(
  controller: EvaluationWorkbenchV2Controller,
  orgId?: string,
  workspaceId?: string,
  systemId?: string,
): EvaluationWorkbenchV2ScopeView {
  const inputScopeIsCurrent = () => controller.matchesScope(orgId, workspaceId, systemId)
  return {
    get snapshot() {
      return inputScopeIsCurrent()
        ? controller.getSnapshot()
        : { ...emptySnapshot(), loading: Boolean(orgId && workspaceId && systemId) }
    },
    async run<T>(operation: (scopedController: EvaluationWorkbenchV2Controller) => Promise<T>) {
      if (!inputScopeIsCurrent()) throw new StaleEvaluationWorkbenchResultError()
      return operation(controller)
    },
  }
}

export function createEvaluationWorkbenchV2Controller(
  client: EvaluationWorkbenchApiClient = apiClient,
): EvaluationWorkbenchV2Controller {
  return new DefaultEvaluationWorkbenchV2Controller(client)
}

export function useEvaluationWorkbenchV2(orgId?: string, workspaceId?: string, systemId?: string) {
  const controllerRef = useRef<EvaluationWorkbenchV2Controller | null>(null)
  if (!controllerRef.current) controllerRef.current = createEvaluationWorkbenchV2Controller()
  const controller = controllerRef.current
  const [, setSnapshot] = useState<EvaluationWorkbenchSnapshot>(controller.getSnapshot())
  const scopeView = useMemo(
    () => createEvaluationWorkbenchV2ScopeView(controller, orgId, workspaceId, systemId),
    [controller, orgId, workspaceId, systemId],
  )

  useEffect(() => controller.subscribe(() => setSnapshot(controller.getSnapshot())), [controller])
  useEffect(() => {
    void controller.setScope(orgId, workspaceId, systemId)
  }, [controller, orgId, workspaceId, systemId])

  const refresh = useCallback(() => scopeView.run((scopedController) => scopedController.refresh()), [scopeView])
  const getPlan = useCallback(
    (planId: string) => scopeView.run((scopedController) => scopedController.getPlan(planId)),
    [scopeView],
  )
  const getRun = useCallback(
    (runId: string) => scopeView.run((scopedController) => scopedController.getRun(runId)),
    [scopeView],
  )

  return {
    ...scopeView.snapshot,
    refresh,
    getPlan,
    getRun,
  }
}
