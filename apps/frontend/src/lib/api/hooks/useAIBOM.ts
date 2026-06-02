/**
 * AI BOM API Hooks
 */

import { useState, useEffect, useCallback } from 'react'
import { apiClient, type ApiResponse } from '../api-client'
import { API_ENDPOINTS } from '../endpoints'

type RawObject = Record<string, unknown>
export type AIBOMRiskLevel = 'none' | 'low' | 'medium' | 'high' | 'critical' | 'unknown'

export interface BOMComponent {
  id: string
  name: string
  version: string
  type: string
  vendor?: string
  license?: string
  status?: 'active' | 'deprecated' | 'vulnerable' | 'updated'
  riskLevel: AIBOMRiskLevel
  complianceStatus?: string
  lastUpdated?: string
  dependencies?: string[]
  vulnerabilities?: number
  compliance?: string
  description?: string
  componentMetadata?: RawObject
  createdAt?: string
  updatedAt?: string
}

export interface BOMStats {
  totalComponents?: number
  vulnerableComponents?: number
  outdatedComponents?: number
  complianceScore?: number
  licenseIssues?: number
  lastScan?: string
}

export interface BOMDocument {
  id: string
  name?: string
  version?: string
  description?: string
  projectName: string
  organization?: string
  components: BOMComponent[]
  createdAt?: string
  updatedAt?: string
  riskLevel: AIBOMRiskLevel
  complianceStatus?: string
  totalComponents?: number
  tags?: string[]
}

export interface FairnessEvidenceProfile {
  profile_id: string
  profile_version: string
  bom_ref: string
  system_name: string
  system_domain: string
  generated_at: string
  components: FairnessEvidenceComponent[]
  risk_summary: {
    overall_severity: string
    key_risks: string[]
    unknown_count: number
    stale_evidence_count: number
    simulated_evidence_count: number
    reviewer_action: string
  }
  review_summary: {
    status: string
    reviewer?: string | null
    reviewed_at?: string | null
    notes: string
    pending_actions: string[]
  }
  limitations: string[]
}

export interface FairnessEvidenceComponent {
  component_id: string
  component_type: string
  component_name: string
  version: string
  upstream_components: string[]
  downstream_components: string[]
  validation_state: string
  review_status: string
  protected_attributes_tested: string[]
  subgroup_coverage: {
    evaluated_groups: string[]
    missing_groups: string[]
    coverage_notes: string
  }
  fairness_metrics: Array<{
    metric: string
    value?: number | string | null
    threshold?: number | string | null
    affected_groups: string[]
    evidence_state: string
  }>
  bias_tests_run: Array<{
    test_name: string
    test_type: string
    result: string
    evidence_state: string
    evidence_ref: string
  }>
  known_bias_risks: Array<{
    risk_id: string
    description: string
    affected_groups: string[]
    severity: string
    evidence_state: string
  }>
  remediation_history: Array<{
    remediation_id: string
    description: string
    status: string
    validation_state: string
    evidence_ref: string
  }>
  evidence_refs: string[]
  evidence_freshness: {
    last_updated?: string | null
    expires_at?: string | null
    staleness_rule: string
    evidence_state: string
  }
  regulatory_mapping: Array<{
    framework: string
    control: string
    claim: string
    evidence_state: string
  }>
  unknowns: string[]
  risk_summary: {
    overall_severity: string
    key_risks: string[]
    unknown_count: number
    stale_evidence_count: number
    simulated_evidence_count: number
    reviewer_action: string
  }
}

const isRecord = (value: unknown): value is RawObject =>
  typeof value === 'object' && value !== null && !Array.isArray(value)

const asString = (value: unknown, fallback = ''): string => {
  if (typeof value === 'string') return value
  if (typeof value === 'number' || typeof value === 'boolean') return String(value)
  return fallback
}

const asOptionalString = (value: unknown): string | undefined => {
  const text = asString(value)
  return text || undefined
}

const asOptionalNumber = (value: unknown): number | undefined => {
  if (typeof value === 'number' && Number.isFinite(value)) return value
  if (typeof value === 'string' && value.trim() !== '') {
    const parsed = Number(value)
    return Number.isFinite(parsed) ? parsed : undefined
  }
  return undefined
}

const asStringArray = (value: unknown): string[] => {
  if (!Array.isArray(value)) return []
  return value
    .map((item) => asString(item))
    .filter((item) => item.length > 0)
}

const asObject = (value: unknown): RawObject | undefined =>
  isRecord(value) ? value : undefined

const normalizeRiskLevel = (value: unknown): AIBOMRiskLevel => {
  const normalized = asString(value).toLowerCase()
  if (['none', 'low', 'medium', 'high', 'critical'].includes(normalized)) {
    return normalized as AIBOMRiskLevel
  }
  return 'unknown'
}

const normalizeComponentStatus = (value: unknown): BOMComponent['status'] | undefined => {
  const normalized = asString(value).toLowerCase()
  if (['active', 'deprecated', 'vulnerable', 'updated'].includes(normalized)) {
    return normalized as BOMComponent['status']
  }
  return undefined
}

const normalizeBOMComponent = (component: unknown, index: number): BOMComponent => {
  const raw = isRecord(component) ? component : {}
  const fallbackId = `component-${index + 1}`
  const name = asString(raw.name, fallbackId)
  const componentMetadata = asObject(raw.componentMetadata) || asObject(raw.component_metadata)

  return {
    id: asString(raw.id, fallbackId),
    name,
    version: asString(raw.version, 'unknown'),
    type: asString(raw.type, 'unknown'),
    vendor: asOptionalString(raw.vendor),
    license: asOptionalString(raw.license),
    status: normalizeComponentStatus(raw.status),
    riskLevel: normalizeRiskLevel(raw.riskLevel ?? raw.risk_level),
    complianceStatus: asOptionalString(raw.complianceStatus ?? raw.compliance_status),
    lastUpdated: asOptionalString(raw.lastUpdated ?? raw.last_updated ?? raw.updated_at),
    dependencies: asStringArray(raw.dependencies),
    vulnerabilities: asOptionalNumber(raw.vulnerabilities),
    compliance: asOptionalString(raw.compliance ?? raw.compliance_status),
    description: asOptionalString(raw.description),
    componentMetadata,
    createdAt: asOptionalString(raw.createdAt ?? raw.created_at),
    updatedAt: asOptionalString(raw.updatedAt ?? raw.updated_at),
  }
}

const normalizeBOMDocument = (document: unknown, index: number): BOMDocument => {
  const raw = isRecord(document) ? document : {}
  const components = Array.isArray(raw.components)
    ? raw.components.map((component, componentIndex) => normalizeBOMComponent(component, componentIndex))
    : []
  const fallbackId = `bom-${index + 1}`
  const name = asOptionalString(raw.name)

  return {
    id: asString(raw.id, fallbackId),
    name,
    version: asOptionalString(raw.version),
    description: asOptionalString(raw.description),
    projectName: asString(raw.projectName ?? raw.project_name ?? raw.name, fallbackId),
    organization: asOptionalString(raw.organization),
    components,
    createdAt: asOptionalString(raw.createdAt ?? raw.created_at),
    updatedAt: asOptionalString(raw.updatedAt ?? raw.updated_at),
    riskLevel: normalizeRiskLevel(raw.riskLevel ?? raw.overall_risk_level),
    complianceStatus: asOptionalString(raw.complianceStatus ?? raw.overall_compliance_status),
    totalComponents: asOptionalNumber(raw.totalComponents ?? raw.total_components) ?? components.length,
    tags: asStringArray(raw.tags),
  }
}

const extractBOMDocuments = (payload: unknown): BOMDocument[] => {
  if (!isRecord(payload)) return []
  const documents = payload.documents ?? payload.data
  if (!Array.isArray(documents)) return []
  return documents.map((document, index) => normalizeBOMDocument(document, index))
}

const normalizeBOMStats = (stats: unknown): BOMStats => {
  const raw = isRecord(stats) ? stats : {}

  return {
    totalComponents: asOptionalNumber(raw.totalComponents ?? raw.total_components),
    vulnerableComponents: asOptionalNumber(raw.vulnerableComponents ?? raw.vulnerable_components),
    outdatedComponents: asOptionalNumber(raw.outdatedComponents ?? raw.outdated_components),
    complianceScore: asOptionalNumber(raw.complianceScore ?? raw.compliance_score),
    licenseIssues: asOptionalNumber(raw.licenseIssues ?? raw.license_issues),
    lastScan: asOptionalString(raw.lastScan ?? raw.last_scan),
  }
}

export function useAIBOM() {
  const [documents, setDocuments] = useState<BOMDocument[]>([])
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<Error | null>(null)

  const fetchDocuments = useCallback(async () => {
    try {
      setLoading(true)
      setError(null)
      
      const response: ApiResponse<unknown> = await apiClient.get(
        API_ENDPOINTS.aiBOM.documents,
        {
          enableRetry: true,
          maxRetries: 3,
          timeout: 10000,
        }
      )
      
      if (response.success && response.data) {
        setDocuments(extractBOMDocuments(response.data))
        setError(null)
      } else {
        const errorMessage = response.error || 'Failed to fetch AI BOM documents'
        setError(new Error(errorMessage))
        setDocuments([])
      }
    } catch (err) {
      console.error('AI BOM API error:', err)
      setError(err instanceof Error ? err : new Error('Failed to fetch AI BOM documents'))
      setDocuments([])
    } finally {
      setLoading(false)
    }
  }, [])

  useEffect(() => {
    if (typeof window === 'undefined') {
      setLoading(false)
      return
    }

    fetchDocuments()
  }, [fetchDocuments])

  const createBOM = async (request: any) => {
    try {
      setLoading(true)
      const response: ApiResponse<unknown> = await apiClient.post(
        API_ENDPOINTS.aiBOM.create,
        request,
        {
          enableRetry: true,
          maxRetries: 3,
        }
      )
      
      if (response.success && response.data) {
        await fetchDocuments() // Refresh list
        return normalizeBOMDocument(response.data, 0)
      } else {
        throw new Error(response.error || 'Failed to create AI BOM')
      }
    } catch (err) {
      setError(err instanceof Error ? err : new Error('Failed to create AI BOM'))
      throw err
    } finally {
      setLoading(false)
    }
  }

  return { documents, loading, error, refetch: fetchDocuments, createBOM }
}

export function useAIBOMFairnessProfile(documentId?: string) {
  const [profile, setProfile] = useState<FairnessEvidenceProfile | null>(null)
  const [loading, setLoading] = useState(Boolean(documentId))
  const [error, setError] = useState<Error | null>(null)

  const fetchProfile = useCallback(async () => {
    if (!documentId) {
      setProfile(null)
      setError(null)
      setLoading(false)
      return
    }

    try {
      setLoading(true)
      setError(null)

      const response: ApiResponse<FairnessEvidenceProfile> = await apiClient.get(
        API_ENDPOINTS.aiBOM.fairnessEvidenceProfile(documentId),
        {
          enableRetry: true,
          maxRetries: 2,
          timeout: 10000,
        }
      )

      if (response.success && response.data) {
        setProfile(response.data)
        setError(null)
      } else {
        const errorMessage = response.error || 'Failed to fetch fairness evidence profile'
        setError(new Error(errorMessage))
        setProfile(null)
      }
    } catch (err) {
      console.error('AI BOM fairness evidence profile API error:', err)
      setError(err instanceof Error ? err : new Error('Failed to fetch fairness evidence profile'))
      setProfile(null)
    } finally {
      setLoading(false)
    }
  }, [documentId])

  useEffect(() => {
    if (typeof window === 'undefined') {
      setLoading(false)
      return
    }

    fetchProfile()
  }, [fetchProfile])

  return { profile, loading, error, refetch: fetchProfile }
}

export function useAIBOMStats(documentId?: string) {
  const [stats, setStats] = useState<BOMStats | null>(null)
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<Error | null>(null)

  const fetchStats = useCallback(async () => {
    try {
      setLoading(true)
      setError(null)
      
      const endpoint = documentId 
        ? API_ENDPOINTS.aiBOM.metrics(documentId)
        : API_ENDPOINTS.aiBOM.stats
      
      const response: ApiResponse<unknown> = await apiClient.get(
        endpoint,
        {
          enableRetry: true,
          maxRetries: 3,
          timeout: 10000,
        }
      )
      
      if (response.success && response.data) {
        setStats(normalizeBOMStats(response.data))
        setError(null)
      } else {
        const errorMessage = response.error || 'Failed to fetch AI BOM stats'
        setError(new Error(errorMessage))
        setStats(null)
      }
    } catch (err) {
      console.error('AI BOM stats API error:', err)
      setError(err instanceof Error ? err : new Error('Failed to fetch AI BOM stats'))
      setStats(null)
    } finally {
      setLoading(false)
    }
  }, [documentId])

  useEffect(() => {
    if (typeof window === 'undefined') {
      setLoading(false)
      return
    }

    fetchStats()
  }, [fetchStats])

  return { stats, loading, error, refetch: fetchStats }
}
