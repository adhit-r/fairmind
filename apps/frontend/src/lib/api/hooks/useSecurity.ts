/**
 * Security API Hooks
 */

import { useState, useEffect } from 'react'
import { apiClient, type ApiResponse } from '../api-client'
import { API_ENDPOINTS } from '../endpoints'
import type { SecurityScanResponse, SecurityResults } from '../types'

export function useSecurityScans() {
  const [scans, setScans] = useState<SecurityScanResponse[]>([])
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<Error | null>(null)

  useEffect(() => {
    const fetchScans = async () => {
      try {
        setLoading(true)
        const response: ApiResponse<SecurityScanResponse[]> = await apiClient.get(
          API_ENDPOINTS.security.scansHistory
        )
        
        if (response.success && response.data) {
          setScans(response.data)
          setError(null)
        } else {
          throw new Error(response.error || 'Failed to fetch security scans')
        }
      } catch (err) {
        setError(err instanceof Error ? err : new Error('Unknown error'))
        setScans([])
      } finally {
        setLoading(false)
      }
    }

    fetchScans()
  }, [])

  return { scans, loading, error }
}

export function useSecurityScan(scanId: string) {
  const [scan, setScan] = useState<SecurityScanResponse | null>(null)
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<Error | null>(null)

  useEffect(() => {
    if (!scanId) {
      setLoading(false)
      return
    }

    const fetchScan = async () => {
      try {
        setLoading(true)
        const response: ApiResponse<SecurityScanResponse> = await apiClient.get(
          API_ENDPOINTS.security.scanDetails(scanId)
        )
        
        if (response.success && response.data) {
          setScan(response.data)
          setError(null)
        } else {
          throw new Error(response.error || 'Failed to fetch scan details')
        }
      } catch (err) {
        setError(err instanceof Error ? err : new Error('Unknown error'))
        setScan(null)
      } finally {
        setLoading(false)
      }
    }

    fetchScan()
  }, [scanId])

  return { scan, loading, error }
}

