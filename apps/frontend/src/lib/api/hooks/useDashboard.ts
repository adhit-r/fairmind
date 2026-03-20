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
      
      let resolvedResponse = response

      // Fallback for deployments where dashboard-stats is unavailable.
      if (!resolvedResponse.success) {
        const fallback = await apiClient.get<any>(
          API_ENDPOINTS.core.metricsSummary,
          {
            enableRetry: false,
            timeout: 8000,
          }
        )
        if (fallback.success) {
          resolvedResponse = {
            success: true,
            data: fallback.data as any,
          }
        }
      }

      if (resolvedResponse.success && resolvedResponse.data) {
        // Transform backend data to frontend format
        const backendData = resolvedResponse.data as any
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
        // Non-fatal fallback for pilot/dev where dashboard endpoints may be partially wired.
        const errorMessage = resolvedResponse.error || 'Failed to fetch dashboard data'
        setError(new Error(errorMessage))
        setData({
          totalModels: 0,
          totalDatasets: 0,
          activeScans: 0,
          systemHealth: {
            status: 'healthy',
            timestamp: new Date().toISOString(),
          },
          recentActivity: [] as ActivityItem[],
        })
      }
    } catch (err) {
      // Hard failure fallback keeps dashboard usable while surfacing the error banner.
      console.error('Dashboard API error:', err)
      setError(err instanceof Error ? err : new Error('Failed to fetch dashboard data'))
      setData({
        totalModels: 0,
        totalDatasets: 0,
        activeScans: 0,
        systemHealth: {
          status: 'healthy',
          timestamp: new Date().toISOString(),
        },
        recentActivity: [] as ActivityItem[],
      })
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
