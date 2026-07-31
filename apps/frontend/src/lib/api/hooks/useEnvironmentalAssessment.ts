'use client'

import { useCallback, useEffect, useState } from 'react'
import { apiClient, type ApiResponse } from '@/lib/api/api-client'
import { API_ENDPOINTS } from '@/lib/api/endpoints'

/**
 * Environmental governance: read + write.
 *
 * The existing useEnvironmentalImpact hook is read-only and can only display an
 * assessment created elsewhere. This hook exposes the full FairMind-E surface so
 * a reviewer can actually run an assessment, attach a mitigation, sign off, and
 * export the disclosure from the product.
 */

export type ProvenanceClass =
  | 'measured'
  | 'tool_estimated'
  | 'vendor_reported'
  | 'manual'
  | 'unknown'

export type LifecyclePhase = 'training' | 'fine_tune' | 'inference' | 'llm_inference'

export type Recommendation = 'go' | 'conditional_go' | 'no_go'

export interface EnvironmentalMetricsInput {
  total_kwh?: number | null
  total_kg_co2e_location?: number | null
  total_kg_co2e_market?: number | null
  kg_co2e_per_1000_requests?: number | null
  kg_co2e_per_1m_tokens?: number | null
  location_carbon_intensity_g_co2e_per_kwh?: number | null
  energy_renewable_pct?: number | null
  pue?: number | null
}

export interface AssessmentInput {
  lifecycle_phase: LifecyclePhase
  functional_unit: string
  boundary?: string
  provenance_class?: ProvenanceClass
  measurement_source?: string
  uncertainty_pct?: number | null
  intensity_vs_baseline?: number | null
  metrics: EnvironmentalMetricsInput
}

export interface MitigationInput {
  description: string
  target_date?: string
  owner?: string
  expected_reduction_pct?: number | null
}

/** Engine result as returned inside a stored assessment record. */
export interface EngineResult {
  recommendation?: Recommendation
  impact_tier?: string
  risk_tier?: string
  confidence_score?: number
  evidence_confidence?: number
  confidence_band?: string
  provenance_class?: string
  coverage?: Record<string, string>
  coverage_rate?: number
  mitigation_blocking?: boolean
  approval_blocking?: boolean
  requires_mitigation?: boolean
  warnings?: string[]
}

export interface AssessmentRecord {
  assessmentId?: string
  id?: string
  version?: number
  createdAt?: string
  recommendation?: Recommendation
  impactTier?: string
  riskTier?: string
  confidenceScore?: number
  confidenceBand?: string
  provenanceClass?: string
  reviewerState?: string
  coverage?: Record<string, string>
  coverageRate?: number
  blockers?: Array<{ code?: string; severity?: string; message?: string }>
  assessment?: Record<string, unknown>
  result?: EngineResult
}

export interface ControlDefinition {
  code: string
  name: string
  governance_test: string
  optional: boolean
}

interface LatestPayload {
  systemId?: string
  latest?: AssessmentRecord | null
  versionTrail?: AssessmentRecord[] | null
  empty?: boolean
}

function errorFrom(response: ApiResponse<unknown>, fallback: string): Error {
  return new Error(response.error || fallback)
}

export function useEnvironmentalAssessment(systemId?: string | null) {
  const [latest, setLatest] = useState<AssessmentRecord | null>(null)
  const [history, setHistory] = useState<AssessmentRecord[]>([])
  const [controls, setControls] = useState<ControlDefinition[]>([])
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState<Error | null>(null)
  const [submitting, setSubmitting] = useState(false)

  const refetch = useCallback(async () => {
    if (!systemId) {
      setLatest(null)
      setHistory([])
      return
    }
    setLoading(true)
    setError(null)
    try {
      const response: ApiResponse<LatestPayload> = await apiClient.get(
        API_ENDPOINTS.aiGovernance.environmentalImpact(systemId)
      )
      if (response.success && response.data) {
        setLatest(response.data.latest ?? null)
        setHistory(response.data.versionTrail ?? [])
      } else {
        // A system with no assessment yet is a normal state, not a failure.
        setLatest(null)
        setHistory([])
      }
    } catch (err) {
      setError(err instanceof Error ? err : new Error('Failed to load environmental assessment'))
    } finally {
      setLoading(false)
    }
  }, [systemId])

  const loadControls = useCallback(async () => {
    try {
      const response: ApiResponse<{ controls?: ControlDefinition[] }> = await apiClient.get(
        API_ENDPOINTS.aiGovernance.environmentalControls()
      )
      if (response.success && response.data?.controls) {
        setControls(response.data.controls)
      }
    } catch {
      // Control definitions are reference data; failing to load them must not
      // block the assessment flow.
    }
  }, [])

  useEffect(() => {
    void refetch()
  }, [refetch])

  useEffect(() => {
    void loadControls()
  }, [loadControls])

  const runAssessment = useCallback(
    async (input: AssessmentInput, uploadedBy?: string) => {
      if (!systemId) throw new Error('No governed system selected')
      setSubmitting(true)
      setError(null)
      try {
        const response: ApiResponse<unknown> = await apiClient.post(
          API_ENDPOINTS.aiGovernance.environmentalAssess,
          { system_id: systemId, assessment: input, uploaded_by: uploadedBy }
        )
        if (!response.success) throw errorFrom(response, 'Assessment failed')
        await refetch()
        return response.data
      } catch (err) {
        const wrapped = err instanceof Error ? err : new Error('Assessment failed')
        setError(wrapped)
        throw wrapped
      } finally {
        setSubmitting(false)
      }
    },
    [systemId, refetch]
  )

  const addMitigation = useCallback(
    async (assessmentId: string, mitigation: MitigationInput) => {
      if (!systemId) throw new Error('No governed system selected')
      setSubmitting(true)
      setError(null)
      try {
        const response: ApiResponse<unknown> = await apiClient.put(
          API_ENDPOINTS.aiGovernance.environmentalMitigation(systemId, assessmentId),
          { mitigation }
        )
        if (!response.success) throw errorFrom(response, 'Failed to add mitigation')
        await refetch()
        return response.data
      } catch (err) {
        const wrapped = err instanceof Error ? err : new Error('Failed to add mitigation')
        setError(wrapped)
        throw wrapped
      } finally {
        setSubmitting(false)
      }
    },
    [systemId, refetch]
  )

  const approveAssessment = useCallback(
    async (assessmentId: string, reviewer: string, attestation: string) => {
      if (!systemId) throw new Error('No governed system selected')
      setSubmitting(true)
      setError(null)
      try {
        const response: ApiResponse<unknown> = await apiClient.post(
          API_ENDPOINTS.aiGovernance.environmentalApprove(systemId, assessmentId),
          { reviewer, attestation }
        )
        // The gate returns 409 when the assessment is not approvable; surface
        // that reason verbatim rather than a generic failure.
        if (!response.success) throw errorFrom(response, 'Sign-off was blocked by the environmental gate')
        await refetch()
        return response.data
      } catch (err) {
        const wrapped = err instanceof Error ? err : new Error('Sign-off failed')
        setError(wrapped)
        throw wrapped
      } finally {
        setSubmitting(false)
      }
    },
    [systemId, refetch]
  )

  const exportDisclosure = useCallback(async () => {
    if (!systemId) throw new Error('No governed system selected')
    const response: ApiResponse<Record<string, unknown>> = await apiClient.get(
      API_ENDPOINTS.aiGovernance.environmentalExport(systemId)
    )
    if (!response.success || !response.data) {
      throw errorFrom(response, 'Export failed')
    }
    return response.data
  }, [systemId])

  return {
    latest,
    history,
    controls,
    loading,
    error,
    submitting,
    refetch,
    runAssessment,
    addMitigation,
    approveAssessment,
    exportDisclosure,
  }
}

/** Resolves a model to the governed system that carries its release gate. */
export function useGovernedSystemForModel(modelId?: string | null) {
  const [systemId, setSystemId] = useState<string | null>(null)
  const [systemName, setSystemName] = useState<string | null>(null)
  const [governed, setGoverned] = useState<boolean | null>(null)
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<Error | null>(null)

  const resolve = useCallback(async () => {
    if (!modelId) {
      setLoading(false)
      return
    }
    setLoading(true)
    setError(null)
    try {
      const response: ApiResponse<{
        governed?: boolean
        system?: { id?: string; name?: string } | null
      }> = await apiClient.get(API_ENDPOINTS.aiGovernance.systemForModel(modelId))
      if (response.success && response.data) {
        setGoverned(Boolean(response.data.governed))
        setSystemId(response.data.system?.id ?? null)
        setSystemName(response.data.system?.name ?? null)
      } else {
        setGoverned(false)
      }
    } catch (err) {
      setError(err instanceof Error ? err : new Error('Failed to resolve governed system'))
    } finally {
      setLoading(false)
    }
  }, [modelId])

  useEffect(() => {
    void resolve()
  }, [resolve])

  return { systemId, systemName, governed, loading, error, refetch: resolve }
}
