/**
 * Compliance API Hooks
 */

import { useState, useEffect, useCallback } from 'react'
import { apiClient, type ApiResponse } from '../api-client'
import { API_ENDPOINTS } from '../endpoints'

export interface ComplianceFramework {
  name: string
  compliance: number
  status: 'compliant' | 'partial' | 'non-compliant'
}

export interface ComplianceControl {
  id: string
  name: string
  status: 'compliant' | 'partial' | 'non-compliant'
  framework: string
}

export interface ComplianceData {
  frameworks: ComplianceFramework[]
  controls: ComplianceControl[]
}

export function useCompliance() {
  const [data, setData] = useState<ComplianceData | null>(null)
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<Error | null>(null)

  const fetchCompliance = useCallback(async () => {
    try {
      setLoading(true)
      setError(null)
      
      // Fetch compliance frameworks
      const frameworksResponse: ApiResponse<ComplianceFramework[]> = await apiClient.get(
        API_ENDPOINTS.aiGovernance.complianceFrameworks,
        {
          enableRetry: true,
          maxRetries: 3,
          timeout: 10000,
        }
      )
      
      if (frameworksResponse.success && frameworksResponse.data) {
        // Transform backend data to frontend format
        const frameworks = frameworksResponse.data.map((fw: any) => ({
          name: fw.name || fw.framework_name,
          compliance: fw.compliance_score || fw.compliance || 0,
          status: (fw.compliance_score || 0) >= 90 ? 'compliant' as const :
                 (fw.compliance_score || 0) >= 70 ? 'partial' as const :
                 'non-compliant' as const,
        }))
        
        // For now, controls are derived from frameworks
        // In the future, this could come from a separate endpoint
        const controls: ComplianceControl[] = frameworks.flatMap(fw => [
          {
            id: `${fw.name}-1`,
            name: `${fw.name} Compliance Controls`,
            status: fw.status,
            framework: fw.name,
          },
        ])
        
        setData({ frameworks, controls })
        setError(null)
      } else {
        const errorMessage = frameworksResponse.error || 'Failed to fetch compliance data'
        setError(new Error(errorMessage))
        setData(null)
      }
    } catch (err) {
      console.error('Compliance API error:', err)
      setError(err instanceof Error ? err : new Error('Failed to fetch compliance data'))
      setData(null)
    } finally {
      setLoading(false)
    }
  }, [])

  useEffect(() => {
    if (typeof window === 'undefined') {
      setLoading(false)
      return
    }

    fetchCompliance()
  }, [fetchCompliance])

  return { data, loading, error, refetch: fetchCompliance }
}

