/**
 * AI Governance API Hooks
 */

import { useState, useEffect, useCallback } from 'react'
import { apiClient, type ApiResponse } from '../api-client'
import { API_ENDPOINTS } from '../endpoints'

export interface ComplianceFramework {
  id: string
  name: string
  description: string
  controls: any[]
}

export interface ApprovalDecision {
  id: string
  request_id: string
  decision: 'approved' | 'rejected'
  notes: string
  decided_by?: string | null
  createdAt: string
}

export interface ApprovalRequest {
  id: string
  workflow_id: string
  entity_type: string
  entity_id: string
  requested_by?: string | null
  status: 'pending' | 'approved' | 'rejected'
  current_step: number
  decision_notes: string
  createdAt: string
  updatedAt: string
}

interface SystemApprovalState {
  systemId: string
  request: ApprovalRequest | null
  decisions: ApprovalDecision[]
}

export interface EnvironmentalImpactTotals {
  energyKwh?: number | null
  carbonKgCo2e?: number | null
  computeHours?: number | null
  inferenceCount?: number | null
  trainingRuns?: number | null
}

export interface EnvironmentalImpactCarbon {
  location?: string | null
  market?: string | null
  locationBasedKgCo2e?: number | null
  marketBasedKgCo2e?: number | null
  gridIntensityGCo2eKwh?: number | null
  marketInstrument?: string | null
}

export interface EnvironmentalImpactIntensity {
  gCo2ePerRequest?: number | null
  kgCo2ePerThousandInferences?: number | null
  kwhPerThousandInferences?: number | null
  kgCo2ePerComputeHour?: number | null
}

export interface EnvironmentalImpactUncertainty {
  lower?: number | null
  upper?: number | null
  unit?: string | null
  description?: string | null
}

export interface EnvironmentalImpactProvenance {
  source?: string | null
  methodology?: string | null
  boundary?: string | null
  dataQuality?: string | null
  measurementWindow?: string | null
  uncertainty?: EnvironmentalImpactUncertainty | null
}

export interface EnvironmentalImpactControlCoverage {
  id: string
  label?: string | null
  status?: string | null
  score?: number | null
  evidenceCount?: number | null
  blockerCount?: number | null
  blockers?: string[] | null
}

export interface EnvironmentalImpactBlocker {
  id?: string | null
  title?: string | null
  severity?: string | null
  owner?: string | null
  state?: string | null
  dueDate?: string | null
}

export interface EnvironmentalImpactEvidenceLink {
  id?: string | null
  title?: string | null
  url?: string | null
  href?: string | null
  source?: string | null
  confidence?: number | null
}

export interface EnvironmentalImpactVersion {
  version?: string | null
  createdAt?: string | null
  author?: string | null
  notes?: string | null
}

export interface EnvironmentalImpactMitigation {
  state?: string | null
  owner?: string | null
  dueDate?: string | null
  exceptionState?: string | null
  exceptionReason?: string | null
  acceptedBy?: string | null
}

export interface EnvironmentalImpactReport {
  orgId?: string | null
  systemId?: string | null
  generatedAt?: string | null
  version?: string | null
  totals?: EnvironmentalImpactTotals | null
  carbon?: EnvironmentalImpactCarbon | null
  marketCarbon?: EnvironmentalImpactCarbon | null
  locationMarketCarbon?: EnvironmentalImpactCarbon | null
  intensity?: EnvironmentalImpactIntensity | null
  provenance?: EnvironmentalImpactProvenance | null
  uncertainty?: EnvironmentalImpactUncertainty | null
  confidence?: number | string | null
  recommendation?: string | {
    status?: string | null
    summary?: string | null
    nextStep?: string | null
  } | null
  coverage?: EnvironmentalImpactControlCoverage[] | Record<string, EnvironmentalImpactControlCoverage> | null
  blockers?: Array<EnvironmentalImpactBlocker | string> | null
  mitigation?: EnvironmentalImpactMitigation | null
  exceptions?: EnvironmentalImpactMitigation[] | null
  evidenceLinks?: EnvironmentalImpactEvidenceLink[] | null
  versionTrail?: EnvironmentalImpactVersion[] | null
}

type EnvironmentalImpactPayload = EnvironmentalImpactReport | {
  orgId?: string | null
  org_id?: string | null
  systemId?: string | null
  system_id?: string | null
  environmentalImpact?: EnvironmentalImpactReport | null
  environmental_impact?: EnvironmentalImpactReport | null
  impact?: EnvironmentalImpactReport | null
  data?: EnvironmentalImpactReport | null
  latest?: EnvironmentalImpactReport | null
  versionTrail?: EnvironmentalImpactVersion[] | null
  version_trail?: EnvironmentalImpactVersion[] | null
  empty?: boolean | null
}

function extractEnvironmentalImpactPayload(payload?: EnvironmentalImpactPayload): EnvironmentalImpactReport | null {
  if (!payload || typeof payload !== 'object' || Array.isArray(payload)) {
    return null
  }

  if ('latest' in payload) {
    if (!payload.latest) return null
    return normalizeBackendEnvironmentalPacket(
      payload.latest,
      payload.versionTrail ?? payload.version_trail ?? []
    )
  }

  if (
    'environmentalImpact' in payload ||
    'environmental_impact' in payload ||
    'impact' in payload ||
    'data' in payload
  ) {
    return payload.environmentalImpact
      ?? payload.environmental_impact
      ?? payload.impact
      ?? payload.data
      ?? null
  }

  return payload as EnvironmentalImpactReport
}

type AnyRecord = Record<string, any>

function asRecord(value: unknown): AnyRecord {
  return value && typeof value === 'object' && !Array.isArray(value) ? value as AnyRecord : {}
}

function asArray(value: unknown): unknown[] {
  return Array.isArray(value) ? value : []
}

function firstString(records: AnyRecord[], keys: string[]): string | null {
  for (const record of records) {
    for (const key of keys) {
      const value = record[key]
      if (typeof value === 'string' && value.trim()) return value
      if (typeof value === 'number') return String(value)
    }
  }
  return null
}

function environmentalImpactResponseMatchesScope(
  payload: EnvironmentalImpactPayload,
  report: EnvironmentalImpactReport | null,
  orgId: string,
  systemId: string,
): boolean {
  const outer = asRecord(payload)
  const inner = asRecord(report)
  const outerOrgId = firstString([outer], ['orgId', 'org_id', 'organizationId', 'organization_id'])
  const outerSystemId = firstString([outer], ['systemId', 'system_id'])
  const innerOrgId = firstString([inner], ['orgId', 'org_id', 'organizationId', 'organization_id'])
  const innerSystemId = firstString([inner], ['systemId', 'system_id'])

  return outerOrgId === orgId
    && outerSystemId === systemId
    && (innerOrgId === null || innerOrgId === orgId)
    && (innerSystemId === null || innerSystemId === systemId)
}

function firstNumber(records: AnyRecord[], keys: string[]): number | null {
  for (const record of records) {
    for (const key of keys) {
      const value = record[key]
      if (typeof value === 'number' && Number.isFinite(value)) return value
      if (typeof value === 'string' && value.trim() && Number.isFinite(Number(value))) return Number(value)
    }
  }
  return null
}

function compactRecord(record: AnyRecord): AnyRecord {
  return Object.fromEntries(Object.entries(record).filter(([, value]) => value !== undefined && value !== null && value !== ''))
}

function formatBoundary(value: unknown): string | null {
  const record = asRecord(value)
  if (Object.keys(record).length === 0) return typeof value === 'string' ? value : null
  return Object.entries(record).map(([key, entry]) => `${key}: ${String(entry)}`).join(', ')
}

function normalizeBackendEnvironmentalPacket(
  latest: EnvironmentalImpactReport,
  versionTrail: EnvironmentalImpactVersion[] | null
): EnvironmentalImpactReport {
  const record = asRecord(latest)
  const assessment = asRecord(record.assessment)
  const result = asRecord(record.result)
  const metrics = asRecord(record.metrics ?? assessment.metrics)
  const mitigation = asArray(assessment.mitigations_json ?? assessment.mitigations).map(asRecord)[0] || {}
  const exception = asRecord(record.exception ?? assessment.exception)
  const recommendation = firstString([record, result], ['recommendation']) || null
  const evidenceRefs = asArray(record.evidenceRefs ?? assessment.evidence_refs_json ?? assessment.evidence_refs)

  return {
    ...record,
    version: firstString([record], ['version']) || null,
    generatedAt: firstString([record], ['createdAt', 'created_at']) || null,
    totals: compactRecord({
      energyKwh: firstNumber([metrics], ['total_kwh']),
      carbonKgCo2e: firstNumber([metrics], ['total_kg_co2e_location', 'total_kg_co2e']),
    }),
    carbon: compactRecord({
      location: firstString([assessment, record], ['region', 'location']) || null,
      market: firstString([assessment, record], ['market']) || null,
      locationBasedKgCo2e: firstNumber([metrics], ['total_kg_co2e_location', 'total_kg_co2e']),
      marketBasedKgCo2e: firstNumber([metrics], ['total_kg_co2e_market', 'total_kg_co2e']),
      gridIntensityGCo2eKwh: firstNumber([metrics], ['location_carbon_intensity_g_co2e_per_kwh', 'carbon_intensity_gco2e_kwh']),
      marketInstrument: firstString([metrics], ['carbon_intensity_basis']) || null,
    }),
    intensity: compactRecord({
      kgCo2ePerThousandInferences: firstNumber([metrics], ['kg_co2e_per_1000_requests', 'kg_co2e_per_1k_requests']),
      kgCo2ePerComputeHour: firstNumber([metrics], ['kg_co2e_per_compute_hour']),
    }),
    provenance: compactRecord({
      source: firstString([record, assessment], ['measurementSource', 'measurement_source', 'source']) || null,
      methodology: 'FairMind-E rubric',
      boundary: formatBoundary(assessment.boundary_json ?? assessment.boundary),
      dataQuality: firstString([record, result, assessment], ['provenanceClass', 'provenance_class']) || 'unknown',
      measurementWindow: [
        firstString([assessment], ['period_start']),
        firstString([assessment], ['period_end']),
      ].filter(Boolean).join(' to ') || null,
      uncertainty: compactRecord({
        description: record.uncertaintyPct !== undefined && record.uncertaintyPct !== null
          ? `${record.uncertaintyPct}%`
          : null,
      }),
    }),
    confidence: firstNumber([record, result], ['confidenceScore', 'confidence_score', 'evidence_confidence']),
    recommendation: compactRecord({
      status: recommendation,
      summary: recommendation
        ? `FairMind-E gate returned ${recommendation}.`
        : null,
    }),
    mitigation: compactRecord({
      state: firstString([record, result, assessment], ['mitigationReadiness', 'mitigation_readiness']) || null,
      owner: firstString([mitigation], ['owner']) || null,
      dueDate: firstString([mitigation], ['target_date', 'dueDate', 'due_date']) || null,
      exceptionState: Object.keys(exception).length > 0 ? 'Exception recorded' : null,
      exceptionReason: firstString([exception], ['rationale', 'reason']) || null,
      acceptedBy: firstString([exception], ['owner']) || null,
    }),
    exceptions: Object.keys(exception).length > 0 ? [exception] : [],
    evidenceLinks: evidenceRefs.map((ref, index) => ({
      id: String(ref),
      title: String(ref).replace(/^governance_evidence:/, 'Evidence '),
      source: 'environmental_impact',
      confidence: firstNumber([record, result], ['confidenceScore', 'confidence_score', 'evidence_confidence']),
      url: null,
    })),
    versionTrail: asArray(versionTrail).map((item) => {
      const version = asRecord(item)
      return {
        version: firstString([version], ['version']) || null,
        createdAt: firstString([version], ['createdAt', 'created_at']) || null,
        author: firstString([version], ['reviewerState', 'reviewer_state']) || null,
        notes: firstString([version], ['recommendation']) || null,
      }
    }),
  }
}

export function useAIGovernance() {
  const [frameworks, setFrameworks] = useState<ComplianceFramework[]>([])
  const [loading, setLoading] = useState(true)
  const [approvalLoading, setApprovalLoading] = useState(false)
  const [error, setError] = useState<Error | null>(null)

  useEffect(() => {
    const fetchFrameworks = async () => {
      try {
        setLoading(true)
        const response: ApiResponse<ComplianceFramework[]> = await apiClient.get(
          API_ENDPOINTS.aiGovernance.complianceFrameworks
        )
        
        if (response.success && response.data) {
          setFrameworks(response.data)
          setError(null)
        } else {
          throw new Error(response.error || 'Failed to fetch frameworks')
        }
      } catch (err) {
        setError(err instanceof Error ? err : new Error('Unknown error'))
        setFrameworks([])
      } finally {
        setLoading(false)
      }
    }

    fetchFrameworks()
  }, [])

  const registerModel = async (modelData: any) => {
    try {
      setLoading(true)
      const response: ApiResponse<any> = await apiClient.post(
        API_ENDPOINTS.aiGovernance.registerModel,
        modelData
      )
      if (response.success && response.data) return response.data
      throw new Error(response.error || 'Model registration failed')
    } catch (err) {
      setError(err instanceof Error ? err : new Error('Model registration failed'))
      throw err
    } finally {
      setLoading(false)
    }
  }

  const getSystemApproval = useCallback(async (systemId: string) => {
    setApprovalLoading(true)
    try {
      const response: ApiResponse<SystemApprovalState> = await apiClient.get(
        API_ENDPOINTS.aiGovernance.systemApproval(systemId)
      )
      if (response.success && response.data) {
        return response.data
      }
      throw new Error(response.error || 'Failed to load approval state')
    } finally {
      setApprovalLoading(false)
    }
  }, [])

  const requestSystemApproval = useCallback(async (systemId: string, requestedBy?: string) => {
    setApprovalLoading(true)
    try {
      const response: ApiResponse<SystemApprovalState> = await apiClient.post(
        API_ENDPOINTS.aiGovernance.systemApprovalRequest(systemId),
        { requested_by: requestedBy || null }
      )
      if (response.success && response.data) {
        return response.data
      }
      throw new Error(response.error || 'Failed to create approval request')
    } finally {
      setApprovalLoading(false)
    }
  }, [])

  const decideApprovalRequest = useCallback(
    async (requestId: string, decision: 'approved' | 'rejected', notes: string, decidedBy?: string) => {
      setApprovalLoading(true)
      try {
        const response: ApiResponse<any> = await apiClient.post(
          API_ENDPOINTS.aiGovernance.approvalDecision(requestId),
          {
            decision,
            notes,
            decided_by: decidedBy || null,
          }
        )
        if (response.success && response.data) {
          return response.data
        }
        throw new Error(response.error || 'Failed to record approval decision')
      } finally {
        setApprovalLoading(false)
      }
    },
    []
  )

  return {
    frameworks,
    loading,
    approvalLoading,
    error,
    registerModel,
    getSystemApproval,
    requestSystemApproval,
    decideApprovalRequest,
  }
}

type EnvironmentalImpactSnapshot = {
  scopeKey: string | null
  data: EnvironmentalImpactReport | null
  loading: boolean
  error: Error | null
  emptyReason: string | null
}

function environmentalImpactScopeKey(orgId: string | undefined, systemId: string | undefined) {
  return orgId && systemId ? JSON.stringify([orgId, systemId]) : null
}

function emptyEnvironmentalImpactSnapshot(
  scopeKey: string | null,
  orgId: string | undefined,
  systemId: string | undefined,
): EnvironmentalImpactSnapshot {
  return {
    scopeKey,
    data: null,
    loading: Boolean(scopeKey),
    error: null,
    emptyReason: scopeKey
      ? null
      : !orgId
        ? 'No organization is selected.'
        : !systemId
          ? 'No AI system is selected.'
          : null,
  }
}

export function useEnvironmentalImpact(orgId: string | undefined, systemId: string | undefined) {
  const scopeKey = environmentalImpactScopeKey(orgId, systemId)
  const [snapshot, setSnapshot] = useState<EnvironmentalImpactSnapshot>(() =>
    emptyEnvironmentalImpactSnapshot(scopeKey, orgId, systemId),
  )
  const currentSnapshot = scopeKey && snapshot.scopeKey === scopeKey
    ? snapshot
    : emptyEnvironmentalImpactSnapshot(scopeKey, orgId, systemId)

  useEffect(() => {
    const emptySnapshot = emptyEnvironmentalImpactSnapshot(scopeKey, orgId, systemId)
    if (!orgId || !systemId) {
      setSnapshot(emptySnapshot)
      return
    }

    let active = true
    setSnapshot(emptySnapshot)

    const fetchEnvironmentalImpact = async () => {
      try {
        const response: ApiResponse<EnvironmentalImpactPayload> = await apiClient.get(
          API_ENDPOINTS.aiGovernance.environmentalImpact(orgId, systemId),
          {
            enableRetry: false,
            timeout: 8000,
          }
        )

        if (!active) return

        if (response.success) {
          const report = extractEnvironmentalImpactPayload(response.data)
          if (!response.data || !environmentalImpactResponseMatchesScope(response.data, report, orgId, systemId)) {
            setSnapshot({
              scopeKey,
              data: null,
              loading: false,
              error: new Error('Environmental impact response scope did not match the requested organization and system.'),
              emptyReason: null,
            })
            return
          }

          if (report && Object.keys(report).length > 0) {
            setSnapshot({
              scopeKey,
              data: report,
              loading: false,
              error: null,
              emptyReason: null,
            })
          } else {
            setSnapshot({
              scopeKey,
              data: null,
              loading: false,
              error: null,
              emptyReason: 'No environmental impact packet has been returned for this AI system yet.',
            })
          }
          return
        }

        const message = response.error || 'Failed to load environmental impact data'
        if (/endpoint not found|not found|404/i.test(message)) {
          setSnapshot({
            scopeKey,
            data: null,
            loading: false,
            error: null,
            emptyReason: 'The environmental impact API is not available yet.',
          })
          return
        }
        setSnapshot({
          scopeKey,
          data: null,
          loading: false,
          error: new Error(message),
          emptyReason: null,
        })
      } catch (err) {
        if (!active) return
        setSnapshot({
          scopeKey,
          data: null,
          loading: false,
          error: err instanceof Error ? err : new Error('Failed to load environmental impact data'),
          emptyReason: null,
        })
      }
    }

    void fetchEnvironmentalImpact()

    return () => {
      active = false
    }
  }, [orgId, scopeKey, systemId])

  return {
    data: currentSnapshot.data,
    loading: currentSnapshot.loading,
    error: currentSnapshot.error,
    emptyReason: currentSnapshot.emptyReason,
  }
}
