/**
 * AI BOM API Hooks
 */

import { useState, useEffect, useCallback } from 'react'
import { apiClient, type ApiResponse } from '../api-client'
import { API_ENDPOINTS } from '../endpoints'

export interface BOMComponent {
  id: string
  name: string
  version: string
  type: 'model' | 'dataset' | 'library' | 'framework' | 'tool'
  vendor?: string
  license?: string
  status?: 'active' | 'deprecated' | 'vulnerable' | 'updated'
  riskLevel?: 'low' | 'medium' | 'high' | 'critical'
  lastUpdated?: string
  dependencies?: string[]
  vulnerabilities?: number
  compliance?: string
  description?: string
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
  projectName: string
  components: BOMComponent[]
  createdAt: string
  updatedAt: string
  riskLevel?: string
  complianceStatus?: string
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
  validation_state: string
  review_status: string
  protected_attributes_tested: string[]
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

export function useAIBOM() {
  const [documents, setDocuments] = useState<BOMDocument[]>([])
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<Error | null>(null)

  const fetchDocuments = useCallback(async () => {
    try {
      setLoading(true)
      setError(null)
      
      const response: ApiResponse<{ documents?: BOMDocument[], data?: BOMDocument[] }> = await apiClient.get(
        API_ENDPOINTS.aiBOM.documents,
        {
          enableRetry: true,
          maxRetries: 3,
          timeout: 10000,
        }
      )
      
      if (response.success && response.data) {
        const data = response.data as any
        setDocuments(data.documents || data.data || [])
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
      const response: ApiResponse<BOMDocument> = await apiClient.post(
        API_ENDPOINTS.aiBOM.create,
        request,
        {
          enableRetry: true,
          maxRetries: 3,
        }
      )
      
      if (response.success && response.data) {
        await fetchDocuments() // Refresh list
        return response.data
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
      
      const response: ApiResponse<BOMStats> = await apiClient.get(
        endpoint,
        {
          enableRetry: true,
          maxRetries: 3,
          timeout: 10000,
        }
      )
      
      if (response.success && response.data) {
        setStats(response.data)
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
