'use client'

import { useCallback, useEffect, useMemo, useState } from 'react'
import { useOrg } from '@/context/OrgContext'
import { apiClient, type ApiResponse } from '../api-client'
import { API_ENDPOINTS } from '../endpoints'

export type RunStatus = 'queued' | 'running' | 'waiting' | 'blocked' | 'done' | 'failed'
export type StepKind =
  | 'trigger'
  | 'collect'
  | 'check'
  | 'suggest'
  | 'preflight'
  | 'ask'
  | 'exception'
  | 'decide'
  | 'act'
  | 'verify'
  | 'escalate'
  | 'file'
/** Step kinds at which a run stops for a person. */
export const GATE_KINDS: readonly StepKind[] = ['ask', 'exception', 'decide']
/** A person must act at this step: a gate, or a step the catalogue says does not run without approval. */
export const needsPerson = (s: { kind: StepKind; runsWithoutApproval: string | null }) =>
  GATE_KINDS.includes(s.kind) || (s.runsWithoutApproval ?? '').startsWith('No')
export type Decision = 'approve' | 'request_changes' | 'reject'
/** Which branch of a gate each decision takes, matched against the branch label the way the backend does. */
const DECISION_EDGES: Record<Decision, string[]> = {
  approve: ['approved', 'conclusions'],
  request_changes: ['changes asked', 'more drafting'],
  reject: ['rejected', 'risk accepted'],
}
/** The decisions a gate step offers, in the order the buttons show them. */
export const decisionsFor = (step: { next: Array<{ label: string | null }> }): Decision[] =>
  (Object.keys(DECISION_EDGES) as Decision[]).filter((d) =>
    step.next.some((e) => e.label && DECISION_EDGES[d].some((n) => e.label!.toLowerCase().includes(n))),
  )
export type ReqStatus = 'covered' | 'tested' | 'available' | 'supported' | 'gap'
/** As the catalogue spells it; the UI shows "Not found" as "Not built yet". */
export type EngineStatus = 'Engine exists' | 'Partial' | 'Not found'

export interface RunSummary {
  id: string
  workflowId: string
  workflowName: string
  status: RunStatus
  currentStep: string | null
  /** The workflow version the run follows: the catalogue's, or an organisation version like "org-3". */
  version: string
  /** What a waiting run needs: a gate decision, or a person to submit the current step's output. */
  waitingFor: 'approval' | 'input' | null
  createdAt: string
  updatedAt: string
}

export interface CataloguePillar {
  id: string
  name: string
  description: string
  packs: number
  workflows: number
  evaluations: number
  frameworks: number
}

export interface Catalogue {
  version: string
  pillars: CataloguePillar[]
  counts: { packs: number; patterns: number; workflows: number; evaluations: number; frameworks: number; requirements: number }
}

export interface PackPattern {
  id: string
  name: string
  agentic: boolean
  workflowCount: number
  evaluationCount: number
}

export interface Pack {
  id: string
  name: string
  /** Pillar id, as in Catalogue.pillars. */
  pillar: string
  description: string
  installed: boolean
  patterns: PackPattern[]
  workflowCount: number
  evaluationCount: number
  requirementsTouched: number
  agentic: boolean
}

export interface WorkflowRef {
  id: string
  name: string
  autonomy: string
  stage: string
  latestRun: RunSummary | null
}

export interface EvaluationRef {
  id: string
  name: string
  engine: EngineStatus
}

export interface PackDetail extends Omit<Pack, 'patterns'> {
  patterns: Array<{ id: string; name: string; objective: string; agentic: boolean; workflows: WorkflowRef[]; evaluations: EvaluationRef[] }>
  frameworks: Array<{ key: string; name: string; touched: number; covered: number }>
}

/** Requirements covered out of the framework's active requirements. */
export interface TargetCoverage {
  key: string
  name: string
  active: number
  coveredAll: number
  coveredInstalled: number
}

export interface Bundle {
  id: string
  name: string
  for: string
  packs: Array<{ id: string; name: string; installed: boolean }>
  installedCount: number
  targets: TargetCoverage[]
}

export interface JourneySummary {
  key: string
  name: string
  pillar: string
  active: number
  coveredAll: number
  coveredInstalled: number
  contributingPacks: string[]
  binding: string | null
  /** Workflows of installed packs that map to this framework, with their latest run status. */
  workflows: Array<{ id: string; name: string; stage: string; status: RunStatus | null }>
  /** How many of those workflows have a run waiting for a person. */
  waiting: number
}

export interface JourneyRequirement {
  key: string
  control: string
  title: string
  status: ReqStatus
  workflows: Array<{ id: string; name: string; relation: string; stage: string; pack: string; installed: boolean; latestRun: RunSummary | null }>
  evaluations: Array<{ id: string; name: string; engine: EngineStatus; pack: string; installed: boolean; result: ResultStatus | null }>
}

export interface Journey {
  key: string
  name: string
  pillar: string
  version: string | null
  binding: string | null
  status: string | null
  active: number
  coveredAll: number
  coveredInstalled: number
  groups: Array<{ name: string; requirements: JourneyRequirement[] }>
  steps: Array<{ pack: string; name: string; installed: boolean; newlyCovered: number; cumulative: number }>
}

export type ResultStatus = 'passed' | 'failed' | 'insufficient' | 'not_run'
/** Results FairMind reads for an evaluation: the organisation-wide status and the latest result per AI system. */
export interface EvaluationResults {
  status: ResultStatus
  systems: Array<{ systemId: string; systemName: string; status: Exclude<ResultStatus, 'not_run'>; detail: string; evidenceId: string; at: string }>
  latestAt: string | null
}

export interface EvaluationRow {
  id: string
  name: string
  measures: string
  metric: string
  threshold: string
  appliesTo: string
  pillar: string
  pattern: { id: string; name: string }
  pack: { id: string; name: string }
  engine: EngineStatus
  /** FairMind computes this evaluation itself from files you upload. */
  runnable: boolean
  codeLocation: string | null
  tests: Array<{ key: string; framework: string; control: string; title: string }>
  installed: boolean
  /** Null when FairMind does not record results for this evaluation yet. */
  results: EvaluationResults | null
}

export interface Step {
  id: string
  kind: StepKind
  type: string | null
  title: string
  detail: string
  systems: string[]
  permission: string | null
  /** As the catalogue words it: "Yes", "No", or a condition such as "Yes for routine internal records". */
  runsWithoutApproval: string | null
  next: Array<{ to: string; label: string | null }>
  failure: string | null
  output: string | null
}

export interface Mapping {
  key: string
  framework: string
  control: string
  title: string
  relation: string
  note: string | null
}

export interface Workflow {
  id: string
  name: string
  /** The version new runs use: an organisation version like "org-3", else the catalogue version. */
  version: string
  catalogueVersion: string
  draft: { version: number; updatedAt: string } | null
  stage: string
  description: string
  packId: string
  pack: { id: string; name: string }
  installed: boolean
  pattern: { id: string; name: string }
  pillar: string
  commonControl: string | null
  autonomy: string
  gate: string | null
  gateConditions: string | null
  approver: string | null
  separationOfDuties: string | null
  externalWrite: string | null
  triggers: string[]
  mappings: Mapping[]
  evaluations: EvaluationRef[]
  steps: Step[]
  latestRun: RunSummary | null
}

export interface RunEvent {
  seq: number
  kind: string
  stepId: string | null
  payload: Record<string, unknown> | null
  prevHash: string | null
  hash: string
  createdAt: string
}

export interface Draft {
  workflowId: string
  version: number
  basedOn: string
  steps: Step[]
  /** Why it cannot be published yet; empty when it can. */
  problems: string[]
  updatedAt: string
  updatedBy: string | null
}

/** "org-3" reads as "Version 3"; the catalogue version as "Catalogue 2.3". */
export const versionName = (label: string) => (label.startsWith('org-') ? `Version ${label.slice(4)}` : `Catalogue ${label}`)

export interface Run extends RunSummary {
  /** The steps of the version this run follows, which may differ from the workflow's current ones. */
  steps: Step[]
  systemId: string | null
  approvalRequestId: string | null
  approval: { status: string; decisionNotes: string | null } | null
  /** Who recorded the step output now up for approval; deciding on your own proposal is allowed but recorded. */
  proposalBy: string | null
  finishedAt: string | null
  events: RunEvent[]
  chainValid: boolean
}

export interface Resource<T> {
  data: T | null
  loading: boolean
  error: string | null
  reload: () => void
}

/** GET a path; a null path stays idle. Reload keeps the old data on screen while it refetches. */
function useResource<T>(path: string | null): Resource<T> {
  const [data, setData] = useState<T | null>(null)
  const [loading, setLoading] = useState(path !== null)
  const [error, setError] = useState<string | null>(null)
  const [tick, setTick] = useState(0)

  useEffect(() => {
    if (path === null) return
    let active = true
    setLoading(true)
    apiClient
      .get<T>(path)
      .then((res) => {
        if (!active) return
        if (res.success && res.data !== undefined) {
          setData(res.data)
          setError(null)
        } else {
          setError(res.error || res.message || 'Request failed')
        }
      })
      .catch((e: unknown) => active && setError(e instanceof Error ? e.message : 'Request failed'))
      .finally(() => active && setLoading(false))
    return () => {
      active = false
    }
  }, [path, tick])

  const reload = useCallback(() => setTick((t) => t + 1), [])
  return { data, loading, error, reload }
}

const withOrg = (path: string, orgId: string) => `${path}${path.includes('?') ? '&' : '?'}org_id=${encodeURIComponent(orgId)}`

/** A GET scoped to the organisation picked in the org switcher; waits while organisations load. */
function useOrgResource<T>(path: string | null): Resource<T> {
  const { selectedOrg, isLoading } = useOrg()
  const res = useResource<T>(path && selectedOrg ? withOrg(path, selectedOrg.id) : null)
  if (path && !selectedOrg) {
    return isLoading
      ? { ...res, loading: true }
      : { ...res, loading: false, error: 'Select an organisation to see its packs.' }
  }
  return res
}

export const useCatalogue = () => useOrgResource<Catalogue>(API_ENDPOINTS.packs.catalogue)
export const usePacks = () => useOrgResource<Pack[]>(API_ENDPOINTS.packs.list)
export const usePackDetail = (packId: string | undefined) =>
  useOrgResource<PackDetail>(packId ? API_ENDPOINTS.packs.detail(packId) : null)
/** Pack id -> name, from the pack list; an id with no match shows as itself. */
export function usePackNames() {
  const packs = usePacks()
  return useMemo(() => {
    const names = new Map((packs.data ?? []).map((p) => [p.id, p.name]))
    return (id: string) => names.get(id) ?? id
  }, [packs.data])
}
export const useBundles = () => useOrgResource<Bundle[]>(API_ENDPOINTS.packs.bundles)
export const useJourneys = () => useOrgResource<JourneySummary[]>(API_ENDPOINTS.packs.journeys)
export const useJourney = (frameworkKey: string | undefined) =>
  useOrgResource<Journey>(frameworkKey ? API_ENDPOINTS.packs.journey(frameworkKey) : null)
/** The evaluation catalogue; filters are optional and applied by the server. */
export function useEvaluations(filters: { pillar?: string; engine?: string; q?: string } = {}) {
  const qs = new URLSearchParams()
  for (const [k, v] of Object.entries(filters)) if (v) qs.set(k, v)
  const q = qs.toString()
  return useOrgResource<EvaluationRow[]>(q ? `${API_ENDPOINTS.packs.evaluations}?${q}` : API_ENDPOINTS.packs.evaluations)
}
export const useWorkflow = (workflowId: string | undefined) =>
  useOrgResource<Workflow>(workflowId ? API_ENDPOINTS.packs.workflow(workflowId) : null)
export const useDraft = (workflowId: string | undefined) =>
  useOrgResource<Draft>(workflowId ? API_ENDPOINTS.packs.draft(workflowId) : null)
export const useRun = (runId: string | undefined) =>
  useOrgResource<Run>(runId ? API_ENDPOINTS.packs.run(runId) : null)
/** Every run of the organisation, newest first. */
export const useRuns = () => useOrgResource<RunSummary[]>(API_ENDPOINTS.packs.runs)
export const useWaitingRuns = () => useOrgResource<RunSummary[]>(`${API_ENDPOINTS.packs.runs}?status=waiting`)

/** A model provider the organisation can bring its own key for. */
export interface AIProviderOption {
  id: string
  name: string
  kind: 'anthropic' | 'openai'
  needs: Array<'baseUrl' | 'endpoint' | 'region'>
  key: 'required' | 'optional'
  default_model: string
  model_hint: string
  lists_models: boolean
  docs: string
}

/** The organisation's saved provider. The key itself never comes back, only its last four characters. */
export interface AIProviderConfig {
  provider: string
  providerName: string
  model: string
  baseUrl?: string
  endpoint?: string
  region?: string
  hasKey: boolean
  keyHint: string | null
  keyReadable: boolean
  enabled: boolean
  testedOk: boolean | null
  testedAt: string | null
  testMessage: string | null
  updatedAt: string
}

export interface AIProviderBody {
  provider: string
  model: string
  apiKey?: string
  baseUrl?: string
  endpoint?: string
  region?: string
  enabled: boolean
}

export interface AIProviderTest {
  ok: boolean
  message: string
  models: string[]
  latencyMs: number | null
}

export const useAIProviders = () => useOrgResource<AIProviderOption[]>(API_ENDPOINTS.packs.aiProviders)
export const useAIProvider = () => useOrgResource<{ config: AIProviderConfig | null }>(API_ENDPOINTS.packs.aiProvider)

/** What an evaluation engine reads: one file per slot and optional settings. */
export interface EngineSpec {
  id: string
  method: string
  slots: Array<{ name: string; label: string; help: string; kind: 'csv' | 'text' | 'json' | 'binary'; required: boolean }>
  params: Array<{ name: string; label: string; help: string; kind: 'text' | 'number' | 'json'; default: unknown; required: boolean }>
}

export interface EngineRun {
  id: string
  evaluationId: string
  systemId: string
  systemName: string
  status: Exclude<ResultStatus, 'not_run'>
  summary: string
  metrics: Record<string, number | string | null>
  files: Record<string, string>
  createdAt: string
  createdBy: string | null
  params?: Record<string, unknown>
  detail?: Array<Record<string, unknown>>
  detailTotal?: number
}

export const useEvaluation = (evaluationId: string | undefined) =>
  useOrgResource<EvaluationRow>(evaluationId ? API_ENDPOINTS.packs.evaluation(evaluationId) : null)
export const useEngine = (evaluationId: string | undefined, runnable: boolean) =>
  useOrgResource<EngineSpec>(evaluationId && runnable ? API_ENDPOINTS.packs.evaluationEngine(evaluationId) : null)
export const useEngineRuns = (evaluationId: string | undefined, runnable: boolean) =>
  useOrgResource<EngineRun[]>(evaluationId && runnable ? API_ENDPOINTS.packs.evaluationRuns(evaluationId) : null)
export const useEngineRun = (runId: string | null) => useOrgResource<EngineRun>(runId ? API_ENDPOINTS.packs.evaluationRun(runId) : null)

export interface MutationResult<T> {
  data: T | null
  error: string | null
}

async function mutate<T>(call: () => Promise<ApiResponse<T>>): Promise<MutationResult<T>> {
  try {
    const res = await call()
    if (res.success && res.data !== undefined) return { data: res.data, error: null }
    return { data: null, error: res.error || res.message || 'Request failed' }
  } catch (e) {
    return { data: null, error: e instanceof Error ? e.message : 'Request failed' }
  }
}

/** Mutations for the selected organisation. Each returns the server's answer or its error; the caller then calls the page's reload. */
export function usePackActions() {
  const { selectedOrg } = useOrg()
  const orgId = selectedOrg?.id
  return useMemo(() => {
    const send = <T,>(path: string, call: (scoped: string) => Promise<ApiResponse<T>>): Promise<MutationResult<T>> =>
      orgId ? mutate<T>(() => call(withOrg(path, orgId))) : Promise.resolve({ data: null, error: 'Select an organisation first.' })
    return {
      installPack: (packId: string) => send<Pack>(API_ENDPOINTS.packs.install(packId), (p) => apiClient.post(p)),
      uninstallPack: (packId: string) => send<Pack>(API_ENDPOINTS.packs.install(packId), (p) => apiClient.delete(p)),
      installBundle: (bundleId: string) => send<Bundle>(API_ENDPOINTS.packs.installBundle(bundleId), (p) => apiClient.post(p)),
      installFramework: (frameworkKey: string) => send<{ installed: string[] }>(API_ENDPOINTS.packs.installFramework(frameworkKey), (p) => apiClient.post(p)),
      startRun: (workflowId: string, systemId?: string) =>
        send<Run>(API_ENDPOINTS.packs.startRun(workflowId), (p) => apiClient.post(p, systemId ? { system_id: systemId } : {})),
      decideRun: (runId: string, decision: Decision, notes?: string) =>
        send<Run>(API_ENDPOINTS.packs.decision(runId), (p) => apiClient.post(p, { decision, ...(notes ? { notes } : {}) })),
      createDraft: (workflowId: string) => send<Draft>(API_ENDPOINTS.packs.draft(workflowId), (p) => apiClient.post(p)),
      saveDraft: (workflowId: string, steps: Step[]) => send<Draft>(API_ENDPOINTS.packs.draft(workflowId), (p) => apiClient.put(p, { steps })),
      discardDraft: (workflowId: string) => send<{ discarded: number }>(API_ENDPOINTS.packs.draft(workflowId), (p) => apiClient.delete(p)),
      publishDraft: (workflowId: string) => send<Workflow>(API_ENDPOINTS.packs.publishDraft(workflowId), (p) => apiClient.post(p)),
      submitStepOutput: (runId: string, stepId: string, summary: string, route?: string) =>
        send<Run>(API_ENDPOINTS.packs.stepOutput(runId, stepId), (p) => apiClient.post(p, { summary, ...(route ? { route } : {}) })),
      runEvaluation: (evaluationId: string, form: FormData) =>
        send<EngineRun>(API_ENDPOINTS.packs.evaluationRuns(evaluationId), (p) => apiClient.post(p, form)),
      runAgent: (runId: string, stepId: string) => send<Run>(API_ENDPOINTS.packs.agentStep(runId, stepId), (p) => apiClient.post(p)),
      saveAIProvider: (body: AIProviderBody) =>
        send<{ config: AIProviderConfig | null }>(API_ENDPOINTS.packs.aiProvider, (p) => apiClient.put(p, body)),
      deleteAIProvider: () => send<{ config: null }>(API_ENDPOINTS.packs.aiProvider, (p) => apiClient.delete(p)),
      testAIProvider: (body: AIProviderBody) => send<AIProviderTest>(API_ENDPOINTS.packs.aiProviderTest, (p) => apiClient.post(p, body)),
    }
  }, [orgId])
}

/** Install, remove and bundle-install with one busy id and one failure message; `onDone` runs after every attempt so pages can reload. */
export function useInstaller(onDone: () => void) {
  const { installPack, uninstallPack, installBundle, installFramework } = usePackActions()
  const [busy, setBusy] = useState<string | null>(null)
  const [failure, setFailure] = useState<string | null>(null)
  async function run(id: string, call: () => Promise<MutationResult<unknown>>) {
    setBusy(id)
    setFailure(null)
    const res = await call()
    setBusy(null)
    if (res.error) setFailure(res.error)
    onDone()
  }
  return {
    busy,
    failure,
    pack: (id: string, remove = false) => run(id, () => (remove ? uninstallPack(id) : installPack(id))),
    bundle: (id: string) => run(id, () => installBundle(id)),
    framework: (key: string) => run(key, () => installFramework(key)),
  }
}
