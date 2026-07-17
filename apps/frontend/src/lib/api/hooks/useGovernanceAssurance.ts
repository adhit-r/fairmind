import { useCallback, useEffect, useRef, useState } from 'react'

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

export interface ControlAssessment {
  id: string
  externalId: string
  title: string
  statement: string
  applicability: string
  status: string
  owner: string | null
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
  evidenceId: string
  controlAssessmentId: string
  state: 'candidate' | 'accepted' | 'rejected'
  rationale: string | null
  reviewVersion: number
  reviewHistory: EvidenceMappingReview[]
}

export interface EvidenceRun {
  id: string
  runId: string
  evidenceId: string
  contentHash: string
  result: string
  sourceType: string
  sourceIdentifier: string
  capturedAt: string | null
  candidateMappings: EvidenceMapping[]
}

export interface EvidenceRunInput {
  sourceType: string
  sourceIdentifier: string
  runId: string
  result?: string
  capturedAt?: string
  expiresAt?: string
  suiteName?: string
  suiteVersion?: string
  trigger?: string
  subjectVersion?: string
  datasetHash?: string
  configurationHash?: string
  thresholds?: Record<string, unknown>
  seed?: string | number
  runnerVersion?: string
  runnerDigest?: string
  summary?: Record<string, unknown>
  limitations?: string[]
  artifactReferences?: Array<{ uri: string; sha256: string }>
  retention?: string
  assuranceSource?: 'fairmind_internal' | 'company_integration' | 'manual' | 'third_party'
  thirdPartyAssessor?: { identity: string; independenceAssertion: boolean }
  controlExternalIds?: string[]
  evaluationTags?: string[]
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
  const [data, setData] = useState<T>(emptyRef.current)
  const [loading, setLoading] = useState(enabled)
  const [error, setError] = useState<Error | null>(null)

  const refresh = useCallback(async () => {
    if (!enabled) {
      setData(emptyRef.current)
      setError(null)
      setLoading(false)
      return
    }
    setLoading(true)
    try {
      setData(await load())
      setError(null)
    } catch (reason) {
      setData(emptyRef.current)
      setError(reason instanceof Error ? reason : new Error('Governance assurance request failed'))
    } finally {
      setLoading(false)
    }
  }, [enabled, load])

  useEffect(() => {
    void refresh()
  }, [refresh])

  return { data, loading, error, refresh }
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
    loading: controlsLoading || readinessLoading,
    error: controlsError || readinessError,
    refresh,
    updateAssessment,
  }
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

  const ingestRun = useCallback(async (run: EvidenceRunInput) => {
    if (!orgId || !systemId) throw new Error('An organization and AI system are required to ingest evidence')
    const evidenceRun = unwrapGovernanceResponse(await apiClient.post<EvidenceRun>(API_ENDPOINTS.aiGovernance.evidenceRuns(orgId, systemId), run))
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
    controls,
    readiness,
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
    await Promise.all([refreshCatalog(), refreshAssignments(), refreshAssessment(), refreshEvidence()])
  }, [refreshAssessment, refreshAssignments, refreshCatalog, refreshEvidence])

  return {
    frameworks,
    assignments,
    controls,
    readiness,
    evidenceRuns,
    loading: catalogLoading || assignmentsLoading || assessmentLoading || evidenceLoading || mappingsLoading,
    error: catalogError || assignmentsError || assessmentError || evidenceError || mappingsError,
    refresh,
    importFramework,
    assign,
    updateAssessment,
    ingestRun,
    createMapping,
    reviewMapping,
  }
}
