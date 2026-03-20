/**
 * Evidence API Hooks
 */

import { useCallback, useEffect, useRef, useState } from 'react'
import { apiClient, type ApiResponse } from '../api-client'
import { API_ENDPOINTS } from '../endpoints'

export interface Evidence {
  id: string
  systemId: string
  type: string
  content: any
  confidence: number
  timestamp: string
  metadata: Record<string, any>
}

export interface CollectEvidenceInput {
  systemId: string
  type: string
  content: unknown
  confidence: number
}

export interface EvidenceSummary {
  systemId: string
  totalEvidence: number
  linkedEvidence: number
  averageConfidence: number
  highConfidenceEvidence: number
  evidenceTypes: Array<{ type: string; count: number }>
  metadataSources: Array<{ source: string; count: number }>
  workflowState: string
  decisionReadiness: string
  missingSignals: string[]
  recommendedNextStep: string
}

const EMPTY_SUMMARY: EvidenceSummary = {
  systemId: '',
  totalEvidence: 0,
  linkedEvidence: 0,
  averageConfidence: 0,
  highConfidenceEvidence: 0,
  evidenceTypes: [],
  metadataSources: [],
  workflowState: 'empty',
  decisionReadiness: 'needs_evidence',
  missingSignals: [],
  recommendedNextStep: '',
}

function sortEvidence(records: Evidence[]) {
  return [...records].sort((left, right) => {
    const leftTime = new Date(left.timestamp).getTime()
    const rightTime = new Date(right.timestamp).getTime()

    return rightTime - leftTime
  })
}

function normalizeEvidence(record: Evidence, fallback: CollectEvidenceInput): Evidence {
  return {
    ...record,
    id: record.id || `evidence-${Date.now()}`,
    systemId: record.systemId || fallback.systemId,
    type: record.type || fallback.type,
    content: record.content ?? fallback.content,
    confidence: typeof record.confidence === 'number' ? record.confidence : fallback.confidence,
    timestamp: record.timestamp || new Date().toISOString(),
    metadata: record.metadata || {},
  }
}

export function useEvidence(systemId?: string) {
  const [data, setData] = useState<Evidence[]>([])
  const [summary, setSummary] = useState<EvidenceSummary>(EMPTY_SUMMARY)
  const [loading, setLoading] = useState(true)
  const [collecting, setCollecting] = useState(false)
  const [error, setError] = useState<Error | null>(null)
  const requestVersion = useRef(0)

  const loadEvidence = useCallback(async (targetSystemId: string) => {
    const currentRequest = ++requestVersion.current

    setLoading(true)
    setError(null)

    try {
      const [recordsResponse, summaryResponse] = await Promise.all([
        apiClient.get<Evidence[]>(API_ENDPOINTS.aiGovernance.evidence(targetSystemId)),
        apiClient.get<EvidenceSummary>(API_ENDPOINTS.aiGovernance.evidenceSummary(targetSystemId)),
      ])

      if (currentRequest !== requestVersion.current) {
        return
      }

      if (recordsResponse.success && recordsResponse.data) {
        setData(sortEvidence(recordsResponse.data))
        setSummary(summaryResponse.success && summaryResponse.data ? summaryResponse.data : {
          ...EMPTY_SUMMARY,
          systemId: targetSystemId,
        })
      } else {
        throw new Error(recordsResponse.error || 'Failed to fetch evidence')
      }
    } catch (err) {
      if (currentRequest !== requestVersion.current) {
        return
      }

      setError(err instanceof Error ? err : new Error('Unknown error'))
      setData([])
      setSummary({
        ...EMPTY_SUMMARY,
        systemId: targetSystemId,
      })
    } finally {
      if (currentRequest === requestVersion.current) {
        setLoading(false)
      }
    }
  }, [])

  useEffect(() => {
    if (!systemId) {
      requestVersion.current += 1
      setData([])
      setSummary(EMPTY_SUMMARY)
      setError(null)
      setLoading(false)
      return
    }

    void loadEvidence(systemId)
  }, [loadEvidence, systemId])

  const refreshEvidence = useCallback(() => {
    if (!systemId) {
      requestVersion.current += 1
      setData([])
      setSummary(EMPTY_SUMMARY)
      setError(null)
      setLoading(false)
      return Promise.resolve()
    }

    return loadEvidence(systemId)
  }, [loadEvidence, systemId])

  const collectEvidence = useCallback(async (params: CollectEvidenceInput) => {
    setCollecting(true)
    setError(null)

    try {
      const response: ApiResponse<Evidence> = await apiClient.post(
        API_ENDPOINTS.aiGovernance.evidenceCollect,
        params
      )

      if (response.success && response.data) {
        const nextEvidence = normalizeEvidence(response.data, params)

        setData((current) =>
          sortEvidence([
            nextEvidence,
            ...current.filter((item) => item.id !== nextEvidence.id),
          ])
        )
        void refreshEvidence()

        return nextEvidence
      } else {
        throw new Error(response.error || 'Evidence collection failed')
      }
    } catch (err) {
      const error = err instanceof Error ? err : new Error('Evidence collection failed')
      setError(error)
      throw error
    } finally {
      setCollecting(false)
    }
  }, [])

  return { data, summary, loading, collecting, error, collectEvidence, refreshEvidence }
}
