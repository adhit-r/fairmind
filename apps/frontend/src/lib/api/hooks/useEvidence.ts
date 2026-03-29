/**
 * Evidence API Hooks — V2
 */

import { useCallback, useEffect, useRef, useState } from 'react'
import { apiClient, type ApiResponse } from '../api-client'
import { API_ENDPOINTS } from '../endpoints'

export interface Evidence {
  id: string
  systemId: string
  type: string
  title: string
  source: string
  status: string
  uploadedBy: string
  capturedAt: string
  content: any
  confidence: number
  metadata: Record<string, any>
  tags: string[]
  folder: string
  artifactKind: string
  fileUrl: string
  fileName: string
  fileSize: number
  timestamp: string
  stale: boolean
  linkedEntityCount: number
  linkedEntities: EvidenceLink[]
  metadataSummary: Record<string, any>
  workflowState: string
}

export interface EvidenceLink {
  id: string
  entityType: string
  entityId: string
  createdAt: string
}

export interface CollectEvidenceInput {
  systemId: string
  type: string
  title?: string
  content: unknown
  confidence: number
  tags?: string[]
  folder?: string
  artifactKind?: string
  fileUrl?: string
  fileName?: string
  fileSize?: number
  uploadedBy?: string
}

export interface EvidenceUpdateInput {
  title?: string
  status?: string
  tags?: string[]
  folder?: string
  artifactKind?: string
  fileUrl?: string
  fileName?: string
  fileSize?: number
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
        apiClient.get<Evidence[]>(API_ENDPOINTS.aiGovernance.evidenceV2(targetSystemId)),
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
      setSummary({ ...EMPTY_SUMMARY, systemId: targetSystemId })
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

  const collectEvidence = useCallback(async (params: CollectEvidenceInput): Promise<Evidence> => {
    setCollecting(true)
    setError(null)
    try {
      const response: ApiResponse<Evidence> = await apiClient.post(
        API_ENDPOINTS.aiGovernance.evidenceCollectV2,
        {
          system_id: params.systemId,
          type: params.type,
          title: params.title || '',
          content: params.content ?? {},
          confidence: params.confidence,
          tags: params.tags || [],
          folder: params.folder || '',
          artifact_kind: params.artifactKind || 'narrative',
          file_url: params.fileUrl || '',
          file_name: params.fileName || '',
          file_size: params.fileSize || 0,
          uploaded_by: params.uploadedBy || '',
        }
      )
      if (response.success && response.data) {
        const item = response.data
        setData((current) => sortEvidence([item, ...current.filter((e) => e.id !== item.id)]))
        void refreshEvidence()
        return item
      }
      throw new Error(response.error || 'Evidence collection failed')
    } catch (err) {
      const e = err instanceof Error ? err : new Error('Evidence collection failed')
      setError(e)
      throw e
    } finally {
      setCollecting(false)
    }
  }, [refreshEvidence])

  const updateEvidence = useCallback(async (evidenceId: string, updates: EvidenceUpdateInput): Promise<Evidence> => {
    const response: ApiResponse<Evidence> = await apiClient.patch(
      API_ENDPOINTS.aiGovernance.evidenceItem(evidenceId),
      {
        title: updates.title,
        status: updates.status,
        tags: updates.tags,
        folder: updates.folder,
        artifact_kind: updates.artifactKind,
        file_url: updates.fileUrl,
        file_name: updates.fileName,
        file_size: updates.fileSize,
      }
    )
    if (response.success && response.data) {
      const updated = response.data
      setData((current) =>
        sortEvidence(current.map((e) => (e.id === evidenceId ? updated : e)))
      )
      return updated
    }
    throw new Error(response.error || 'Update failed')
  }, [])

  const addLink = useCallback(async (evidenceId: string, entityType: string, entityId: string): Promise<EvidenceLink> => {
    const response: ApiResponse<EvidenceLink> = await apiClient.post(
      API_ENDPOINTS.aiGovernance.evidenceItemLinks(evidenceId),
      { entity_type: entityType, entity_id: entityId }
    )
    if (response.success && response.data) {
      const link = response.data
      setData((current) =>
        current.map((e) => {
          if (e.id !== evidenceId) return e
          const newLinks = [...e.linkedEntities, link]
          return { ...e, linkedEntities: newLinks, linkedEntityCount: newLinks.length, workflowState: 'linked' }
        })
      )
      return link
    }
    throw new Error(response.error || 'Failed to add link')
  }, [])

  const removeLink = useCallback(async (evidenceId: string, linkId: string): Promise<void> => {
    const response: ApiResponse<{ deleted: boolean }> = await apiClient.delete(
      API_ENDPOINTS.aiGovernance.evidenceItemLink(evidenceId, linkId)
    )
    if (response.success) {
      setData((current) =>
        current.map((e) => {
          if (e.id !== evidenceId) return e
          const newLinks = e.linkedEntities.filter((l) => l.id !== linkId)
          return { ...e, linkedEntities: newLinks, linkedEntityCount: newLinks.length, workflowState: newLinks.length > 0 ? 'linked' : 'collected' }
        })
      )
      return
    }
    throw new Error(response.error || 'Failed to remove link')
  }, [])

  return {
    data,
    summary,
    loading,
    collecting,
    error,
    collectEvidence,
    updateEvidence,
    addLink,
    removeLink,
    refreshEvidence,
  }
}
