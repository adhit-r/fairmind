import { useCallback, useEffect, useMemo, useRef, useState } from 'react'

import { apiClient, type ApiResponse } from '../api-client'
import { API_ENDPOINTS } from '../endpoints'

export interface FrameworkCatalog {
  frameworkKey: string
  name: string
}

export interface FrameworkVersion {
  id: string
  frameworkKey: string
  name: string
  versionLabel: string
  sourceHash: string
  status: string
}

export interface FrameworkImportResult {
  versionId: string
  frameworkKey: string
  versionLabel: string
  requirementCount: number
  controlCount: number
  sourceHash: string
  created: boolean
}

export interface FrameworkAssignment {
  id: string
  orgId: string
  systemId: string
  frameworkVersionId: string
}

export interface ResolvedFrameworkAssignment {
  assignment: FrameworkAssignment
  framework: FrameworkCatalog
  version: FrameworkVersion
}

export interface ControlAssessment {
  id: string
  externalId: string
  title: string
  statement: string
  applicability: string
  status: string
  owner: string | null
  obligation: string | null
  application: string | null
  acceptedEvidenceCount: number | null
  latestEvaluation: string | null
  latestEvaluationSource: string | null
  latestEvaluationAt: string | null
  freshness: string | null
  openFindings: number | null
  parentRequirementId: string | null
  parentRequirementTitle: string | null
  mappingRationale: string | null
  evidenceTrace: EvidenceTraceItem[] | null
}

export interface EvidenceTraceItem {
  id: string
  label: string
  kind: string
  source: string
  state: string
  capturedAt: string | null
}

export interface ControlAssessmentUpdateResult {
  id: string
  orgId: string
  systemId: string
  frameworkAssignmentId: string
  controlDefinitionId: string
  applicability: string
  status: string
  owner: string | null
  createdAt: string
  updatedAt: string
}

export interface ReadinessSummary {
  applicable: number
  accepted: number
  readyForReview: number
  partial: number
  notStarted: number
  notApplicable: number
  blockingFindings: number
  missingEvidence: number
  staleEvidence: number
}

export interface EvidenceMappingReview {
  state: 'accepted' | 'rejected'
  rationale?: string | null
  reviewedBy?: string
  reviewedAt?: string
}

export interface EvidenceMappingReviewInput {
  state: EvidenceMappingReview['state']
  rationale?: string | null
  reviewVersion: number
}

export interface EvidenceMapping {
  id: string
  evidenceId: string | null
  controlAssessmentId: string
  state: 'candidate' | 'accepted' | 'rejected'
  rationale: string | null
  reviewVersion: number
  reviewHistory: EvidenceMappingReview[]
}

export interface EvidenceRun {
  id: string
  runId: string
  evidenceId: string | null
  contentHash: string
  runContentHash: string
  passportId: string
  latestRevision: number
  latestCanonicalContentHash: string
  capabilityState: string
  result: string
  sourceType: string
  sourceIdentifier: string
  capturedAt: string | null
  suiteName: string | null
  suiteVersion: string | null
  subjectVersion: string | null
  runnerVersion: string | null
  assuranceSource: 'fairmind_internal' | 'company_integration' | 'manual' | 'third_party' | null
  limitations: string[]
  artifacts: EvidenceArtifact[]
  candidateMappings: EvidenceMapping[]
}

export interface EvidenceArtifact {
  artifactId: string
  ordinal: number
  role: string
  uri: string
  sha256: string
  mediaType: string
  sizeBytes: number | null
  containsSensitiveData: boolean
  retentionPolicy: string | null
  redactionNote: string | null
}

type JsonScalar = string | number | boolean | null

export interface EvidencePassportInput {
  schemaVersion: '1.0.0'
  passportId: string
  passportRevision: 1
  claimBoundary: 'supporting_evidence_only'
  organizationId: string
  workspaceId: string
  aiSystem: {
    systemId: string
    name: string
    kind: 'model' | 'agent' | 'composite_application'
    version: string
    identityHash: string
    deploymentId?: string
    ownerId?: string
    intendedUse?: string
  }
  evaluation: {
    sourceType: 'fairmind_evaluation' | 'external_tool_import' | 'company_integration' | 'manual_registration' | 'third_party_assessment'
    sourceIdentifier: string
    runId: string
    capabilityState: 'validated' | 'metadata_only' | 'external_provider' | 'unavailable' | 'insufficient_data'
    assuranceSource: 'fairmind_internal' | 'company_integration' | 'manual' | 'third_party'
    thirdPartyAssessor?: { identity: string; qualifications?: string[]; independenceAssertion: boolean }
    evaluator: {
      name: string; version: string; adapterName: string; adapterVersion: string; runnerVersion: string
      runnerDigest?: string; codeCommit?: string
    }
    suite: { name: string; version: string; taxonomy?: string; trigger?: 'manual' | 'ci' | 'scheduled' | 'release_gate' | 'incident' | 'integration_sync' }
    subject: {
      kind: 'model' | 'agent' | 'composite_application' | 'dataset' | 'prompt_set' | 'pipeline' | 'deployment'
      subjectId: string; name: string; version: string; digest: string; provider?: string; endpoint?: string
    }
    scope: {
      intendedUse: string; inputFingerprint: string; sampleCount: number; exclusions: string[]
      datasetName?: string; datasetVersion?: string; datasetHash?: string; protectedGroups?: string[]; locales?: string[]
    }
    configurationHash: string
    seed?: string | number
    thresholds: Array<{ metric: string; operator: 'lt' | 'lte' | 'eq' | 'gte' | 'gt' | 'between' | 'in'; value: JsonScalar | JsonScalar[]; unit?: string; preRegisteredAt?: string; rationale: string }>
    environment?: { operatingSystem?: string; architecture?: string; runtime?: string; containerDigest?: string; region?: string; hardware?: string }
    result: {
      status: 'passed' | 'passed_with_limitations' | 'failed' | 'informational' | 'error' | 'unavailable' | 'insufficient_data' | 'unknown'
      summary: string
      metrics: Array<{ name: string; value: JsonScalar | JsonScalar[]; unit?: string; slice?: string; thresholdMet?: boolean; confidenceInterval?: { lower: number; upper: number; level: number } }>
      confidence?: number; startedAt: string; endedAt: string; errorCode?: string; errorMessage?: string
    }
    runContentHash: string
    capturedAt: string
    expiresAt?: string
    limitations: string[]
  }
  artifacts: Array<{
    artifactId: string; role: 'raw_output' | 'report' | 'log' | 'dataset_manifest' | 'model_manifest' | 'prompt_manifest' | 'configuration' | 'other'
    uri: string; sha256: string; mediaType: string; sizeBytes?: number; containsSensitiveData: boolean; retentionPolicy?: string; redactionNote?: string
  }>
  frameworkMappings: Array<{
    mappingId: string
    framework: { key: string; versionLabel: string; sourceHash: string; sourceUri?: string }
    control: { externalId: string; assessmentId: string }
    state: 'candidate'
    relation: 'supports' | 'contradicts' | 'limits' | 'supersedes'
    rationale: string
    suggestedBy: { actorType: 'user' | 'service' | 'adapter' | 'external_assessor'; actorId: string; displayName?: string }
    createdAt: string
  }>
  review: { status: 'pending'; reviewVersion: number }
  findings: Array<{ findingId: string; severity: 'informational' | 'low' | 'medium' | 'high' | 'critical'; status: 'open' | 'accepted_risk' | 'in_remediation' | 'resolved' | 'false_positive'; title: string; description: string; artifactIds: string[]; createdAt: string }>
  remediation: Array<{ remediationId: string; findingIds: string[]; status: 'planned' | 'in_progress' | 'blocked' | 'completed' | 'verified'; ownerId: string; action: string; dueAt?: string; completedAt?: string; verificationPassportId?: string }>
  freshness: { status: 'current' | 'expiring' | 'stale' | 'superseded'; policy: string; assessedAt: string; expiresAt?: string; staleReasons: string[]; invalidationKeys: string[]; supersededByPassportId?: string }
  lineage: { predecessorPassportIds: string[]; retestOfPassportIds: string[] }
  createdAt: string
  canonicalContentHash: string
}

export function evidencePassportRequestBody(passport: EvidencePassportInput): EvidencePassportInput {
  return passport
}

export function evidenceRunDisplayName(run: EvidenceRun): string {
  return run.suiteName || run.sourceIdentifier || run.runId
}

export interface GovernanceAssuranceState<T> {
  data: T
  loading: boolean
  error: Error | null
  refresh: () => Promise<void>
}

type GovernanceRecord = Record<string, unknown>

function camelCase(key: string) {
  return key.replace(/_([a-z])/g, (_, character: string) => character.toUpperCase())
}

export function normalizeGovernanceResponse<T>(value: T): T {
  if (Array.isArray(value)) {
    return value.map(normalizeGovernanceResponse) as T
  }
  if (value && typeof value === 'object') {
    return Object.fromEntries(
      Object.entries(value as GovernanceRecord).map(([key, item]) => [camelCase(key), normalizeGovernanceResponse(item)]),
    ) as T
  }
  return value
}

export function normalizeGovernanceList<T>(value: T[] | undefined | null): T[] {
  return Array.isArray(value) ? normalizeGovernanceResponse(value) : []
}

export function unwrapGovernanceResponse<T>(response: ApiResponse<T>): T {
  if (!response.success) {
    throw new Error(response.error || response.message || 'Governance assurance request failed')
  }
  return normalizeGovernanceResponse(response.data as T)
}

function useGovernanceResource<T>(
  enabled: boolean,
  empty: T,
  load: () => Promise<T>,
): GovernanceAssuranceState<T> {
  const emptyRef = useRef(empty)
  const requestIdRef = useRef(0)
  const [snapshot, setSnapshot] = useState<{
    load: () => Promise<T>
    data: T
    loading: boolean
    error: Error | null
  }>({ load, data: emptyRef.current, loading: enabled, error: null })

  const refresh = useCallback(async () => {
    const requestId = ++requestIdRef.current
    if (!enabled) {
      setSnapshot({ load, data: emptyRef.current, error: null, loading: false })
      return
    }
    setSnapshot((current) => current.load === load
      ? { ...current, error: null, loading: true }
      : { load, data: emptyRef.current, error: null, loading: true })
    try {
      const data = await load()
      if (requestId === requestIdRef.current) {
        setSnapshot({ load, data, error: null, loading: false })
      }
    } catch (reason) {
      if (requestId === requestIdRef.current) {
        setSnapshot({
          load,
          data: emptyRef.current,
          error: reason instanceof Error ? reason : new Error('Governance assurance request failed'),
          loading: false,
        })
      }
    }
  }, [enabled, load])

  useEffect(() => {
    void refresh()
    return () => {
      requestIdRef.current += 1
    }
  }, [refresh])

  const currentScope = snapshot.load === load
  return {
    data: currentScope ? snapshot.data : emptyRef.current,
    loading: enabled && (!currentScope || snapshot.loading),
    error: currentScope ? snapshot.error : null,
    refresh,
  }
}

export function useGovernanceCatalog(orgId?: string) {
  const {
    data: frameworks,
    loading,
    error,
    refresh: refreshFrameworks,
  } = useGovernanceResource(
    Boolean(orgId),
    [] as FrameworkCatalog[],
    useCallback(async () => unwrapGovernanceResponse(await apiClient.get<FrameworkCatalog[]>(API_ENDPOINTS.aiGovernance.frameworks(orgId!))), [orgId]),
  )

  const importFramework = useCallback(async (workbookPath: string) => {
    if (!orgId) throw new Error('An organization is required to import a framework')
    const imported = unwrapGovernanceResponse(await apiClient.post<FrameworkImportResult>(API_ENDPOINTS.aiGovernance.importFramework(orgId), { workbookPath }))
    await refreshFrameworks()
    return imported
  }, [orgId, refreshFrameworks])

  return { data: frameworks, loading, error, refresh: refreshFrameworks, frameworks, importFramework }
}

export function useFrameworkVersions(orgId?: string, frameworkKey?: string) {
  const versions = useGovernanceResource(
    Boolean(orgId && frameworkKey),
    [] as FrameworkVersion[],
    useCallback(async () => unwrapGovernanceResponse(await apiClient.get<FrameworkVersion[]>(API_ENDPOINTS.aiGovernance.frameworkVersions(orgId!, frameworkKey!))), [frameworkKey, orgId]),
  )

  return { ...versions, versions: versions.data }
}

export function resolveFrameworkAssignments(
  frameworks: FrameworkCatalog[],
  versions: FrameworkVersion[],
  assignments: FrameworkAssignment[],
): ResolvedFrameworkAssignment[] {
  const versionById = new Map(versions.map((version) => [version.id, version]))
  const frameworkByKey = new Map(frameworks.map((framework) => [framework.frameworkKey, framework]))

  return assignments.flatMap((assignment) => {
    const version = versionById.get(assignment.frameworkVersionId)
    const framework = version ? frameworkByKey.get(version.frameworkKey) : undefined
    return version && framework ? [{ assignment, framework, version }] : []
  })
}

export function useAllFrameworkVersions(orgId?: string, frameworks: FrameworkCatalog[] = []) {
  const frameworkKey = frameworks.map((framework) => framework.frameworkKey).sort().join(',')
  const versions = useGovernanceResource(
    Boolean(orgId && frameworkKey),
    [] as FrameworkVersion[],
    useCallback(async () => {
      const keys = frameworkKey.split(',').filter(Boolean)
      const responses = await Promise.all(keys.map((key) =>
        apiClient.get<FrameworkVersion[]>(API_ENDPOINTS.aiGovernance.frameworkVersions(orgId!, key)),
      ))
      return responses.flatMap((response) => unwrapGovernanceResponse(response))
    }, [frameworkKey, orgId]),
  )

  return { ...versions, versions: versions.data }
}

export function useFrameworkAssignments(orgId?: string, systemId?: string) {
  const {
    data: assignments,
    loading,
    error,
    refresh: refreshAssignments,
  } = useGovernanceResource(
    Boolean(orgId && systemId),
    [] as FrameworkAssignment[],
    useCallback(async () => unwrapGovernanceResponse(await apiClient.get<FrameworkAssignment[]>(API_ENDPOINTS.aiGovernance.frameworkAssignments(orgId!, systemId!))), [orgId, systemId]),
  )

  const assign = useCallback(async (frameworkVersionId: string) => {
    if (!orgId || !systemId) throw new Error('An organization and AI system are required to assign a framework')
    const assignment = unwrapGovernanceResponse(await apiClient.post<FrameworkAssignment>(API_ENDPOINTS.aiGovernance.frameworkAssignments(orgId, systemId), { frameworkVersionId }))
    await refreshAssignments()
    return assignment
  }, [orgId, refreshAssignments, systemId])

  return { data: assignments, loading, error, refresh: refreshAssignments, assignments, assign }
}

export function useFrameworkAssignmentControls(orgId?: string, assignmentId?: string) {
  const {
    data: controls,
    loading: controlsLoading,
    error: controlsError,
    refresh: refreshControls,
  } = useGovernanceResource(
    Boolean(orgId && assignmentId),
    [] as ControlAssessment[],
    useCallback(async () => unwrapGovernanceResponse(await apiClient.get<ControlAssessment[]>(API_ENDPOINTS.aiGovernance.assignmentControls(orgId!, assignmentId!))), [assignmentId, orgId]),
  )
  const {
    data: readiness,
    loading: readinessLoading,
    error: readinessError,
    refresh: refreshReadiness,
  } = useGovernanceResource(
    Boolean(orgId && assignmentId),
    null as ReadinessSummary | null,
    useCallback(async () => unwrapGovernanceResponse(await apiClient.get<ReadinessSummary>(API_ENDPOINTS.aiGovernance.assignmentReadiness(orgId!, assignmentId!))), [assignmentId, orgId]),
  )

  const updateAssessment = useCallback(async (
    assessmentId: string,
    update: Partial<Pick<ControlAssessment, 'applicability' | 'status' | 'owner'>>,
  ) => {
    if (!orgId) throw new Error('An organization is required to update a control assessment')
    const assessment = unwrapGovernanceResponse(await apiClient.patch<ControlAssessmentUpdateResult>(API_ENDPOINTS.aiGovernance.controlAssessment(orgId, assessmentId), update))
    await Promise.all([refreshControls(), refreshReadiness()])
    return assessment
  }, [orgId, refreshControls, refreshReadiness])

  const refresh = useCallback(async () => {
    await Promise.all([refreshControls(), refreshReadiness()])
  }, [refreshControls, refreshReadiness])

  return {
    controls,
    readiness,
    readinessLoading,
    loading: controlsLoading || readinessLoading,
    error: controlsError || readinessError,
    refresh,
    updateAssessment,
  }
}

export function useAllFrameworkAssignmentControls(orgId?: string, assignmentIds: string[] = []) {
  const assignmentKey = [...assignmentIds].sort().join(',')
  const controls = useGovernanceResource(
    Boolean(orgId && assignmentKey),
    [] as ControlAssessment[],
    useCallback(async () => {
      const ids = assignmentKey.split(',').filter(Boolean)
      const responses = await Promise.all(ids.map((assignmentId) =>
        apiClient.get<ControlAssessment[]>(API_ENDPOINTS.aiGovernance.assignmentControls(orgId!, assignmentId)),
      ))
      return responses.flatMap((response) => unwrapGovernanceResponse(response))
    }, [assignmentKey, orgId]),
  )

  return { ...controls, controls: controls.data }
}

export function useEvidenceRuns(orgId?: string, systemId?: string) {
  const {
    data: runs,
    loading,
    error,
    refresh: refreshRuns,
  } = useGovernanceResource(
    Boolean(orgId && systemId),
    [] as EvidenceRun[],
    useCallback(async () => unwrapGovernanceResponse(await apiClient.get<EvidenceRun[]>(API_ENDPOINTS.aiGovernance.evidenceRuns(orgId!, systemId!))), [orgId, systemId]),
  )

  const ingestRun = useCallback(async (passport: EvidencePassportInput) => {
    if (!orgId || !systemId) throw new Error('An organization and AI system are required to ingest evidence')
    const evidenceRun = unwrapGovernanceResponse(await apiClient.post<EvidenceRun>(API_ENDPOINTS.aiGovernance.evidenceRuns(orgId, systemId), evidencePassportRequestBody(passport)))
    await refreshRuns()
    return evidenceRun
  }, [orgId, refreshRuns, systemId])

  return { data: runs, loading, error, refresh: refreshRuns, runs, ingestRun }
}

export function useEvidenceMappingReview(orgId?: string) {
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState<Error | null>(null)

  const execute = useCallback(async <T,>(request: () => Promise<ApiResponse<T>>) => {
    setLoading(true)
    try {
      const result = unwrapGovernanceResponse(await request())
      setError(null)
      return result
    } catch (reason) {
      const nextError = reason instanceof Error ? reason : new Error('Governance assurance request failed')
      setError(nextError)
      throw nextError
    } finally {
      setLoading(false)
    }
  }, [])

  const createMapping = useCallback(async (evidenceId: string, controlAssessmentId: string, rationale?: string) => {
    if (!orgId) throw new Error('An organization is required to map evidence')
    return execute(() => apiClient.post<EvidenceMapping>(API_ENDPOINTS.aiGovernance.evidenceMappings(orgId, evidenceId), { controlAssessmentId, rationale }))
  }, [execute, orgId])

  const reviewMapping = useCallback(async (
    mappingId: string,
    review: EvidenceMappingReviewInput,
  ) => {
    if (!orgId) throw new Error('An organization is required to review evidence mappings')
    return execute(() => apiClient.post<EvidenceMapping>(API_ENDPOINTS.aiGovernance.reviewEvidenceMapping(orgId, mappingId), review))
  }, [execute, orgId])

  return { loading, error, createMapping, reviewMapping }
}

export function useGovernanceAssurance(orgId?: string, systemId?: string, assignmentId?: string) {
  const {
    frameworks,
    loading: catalogLoading,
    error: catalogError,
    refresh: refreshCatalog,
    importFramework,
  } = useGovernanceCatalog(orgId)
  const {
    assignments,
    loading: assignmentsLoading,
    error: assignmentsError,
    refresh: refreshAssignments,
    assign,
  } = useFrameworkAssignments(orgId, systemId)
  const {
    versions,
    loading: versionsLoading,
    error: versionsError,
    refresh: refreshVersions,
  } = useAllFrameworkVersions(orgId, frameworks)
  const {
    controls,
    readiness,
    readinessLoading,
    loading: assessmentLoading,
    error: assessmentError,
    refresh: refreshAssessment,
    updateAssessment,
  } = useFrameworkAssignmentControls(orgId, assignmentId)
  const {
    runs: evidenceRuns,
    loading: evidenceLoading,
    error: evidenceError,
    refresh: refreshEvidence,
    ingestRun,
  } = useEvidenceRuns(orgId, systemId)
  const {
    loading: mappingsLoading,
    error: mappingsError,
    createMapping,
    reviewMapping,
  } = useEvidenceMappingReview(orgId)

  const refresh = useCallback(async () => {
    await Promise.all([refreshCatalog(), refreshAssignments(), refreshVersions(), refreshAssessment(), refreshEvidence()])
  }, [refreshAssessment, refreshAssignments, refreshCatalog, refreshEvidence, refreshVersions])

  const resolvedAssignments = useMemo(
    () => resolveFrameworkAssignments(frameworks, versions, assignments),
    [assignments, frameworks, versions],
  )
  const unresolvedAssignments = useMemo(
    () => assignments.filter((assignment) =>
      !resolvedAssignments.some((resolved) => resolved.assignment.id === assignment.id),
    ),
    [assignments, resolvedAssignments],
  )

  return {
    frameworks,
    versions,
    assignments,
    resolvedAssignments,
    unresolvedAssignments,
    controls,
    readiness,
    readinessLoading,
    evidenceRuns,
    loading: catalogLoading || assignmentsLoading || versionsLoading || assessmentLoading || evidenceLoading || mappingsLoading,
    error: catalogError || assignmentsError || versionsError || assessmentError || evidenceError || mappingsError,
    refresh,
    importFramework,
    assign,
    updateAssessment,
    ingestRun,
    createMapping,
    reviewMapping,
  }
}
