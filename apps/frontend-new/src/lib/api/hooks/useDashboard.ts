/**
 * Dashboard API Hooks
 */

import { useState, useEffect, useCallback } from 'react'
import { apiClient, type ApiResponse } from '../api-client'
import { API_ENDPOINTS } from '../endpoints'
import type { DashboardStats, ActivityItem } from '../types'

export function useDashboard() {
  const [data, setData] = useState<DashboardStats | null>(null)
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<Error | null>(null)

  const fetchDashboard = useCallback(async () => {
    try {
      setLoading(true)
      setError(null)
      
      const response: ApiResponse<DashboardStats> = await apiClient.get(
        API_ENDPOINTS.database.dashboardStats,
        {
          enableRetry: true,
          maxRetries: 3,
          timeout: 10000,
        }
      )
      
      if (response.success && response.data) {
        // Transform backend data to frontend format
        const backendData = response.data as any
        setData({
          totalModels: backendData.total_models || backendData.totalModels || 0,
          totalDatasets: backendData.total_datasets || backendData.totalDatasets || 0,
          activeScans: backendData.active_scans || backendData.activeScans || 0,
          systemHealth: backendData.systemHealth || {
            status: 'healthy' as const,
            timestamp: new Date().toISOString(),
          },
          recentActivity: backendData.recentActivity || backendData.recent_activity || [],
        } as DashboardStats)
        setError(null)
      } else {
        // API call failed - show error, don't use mock data
        const errorMessage = response.error || 'Failed to fetch dashboard data'
        setError(new Error(errorMessage))
        setData(null)
      }
    } catch (err) {
      // Show error, don't use mock data
      console.error('Dashboard API error:', err)
      setError(err instanceof Error ? err : new Error('Failed to fetch dashboard data'))
      setData(null)
    } finally {
      setLoading(false)
    }
  }, [])

  useEffect(() => {
    // Only fetch on client side
    if (typeof window === 'undefined') {
      setLoading(false)
      return
    }

    fetchDashboard()
  }, [fetchDashboard])

  return { data, loading, error, refetch: fetchDashboard }
}

