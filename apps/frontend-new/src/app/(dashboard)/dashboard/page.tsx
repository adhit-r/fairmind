'use client'

import { useDashboard } from '@/lib/api/hooks/useDashboard'
import { useAuditLogs } from '@/lib/api/hooks/useAuditLogs'
import { StatCard, SimpleChart } from '@/components/charts'
import { Card } from '@/components/ui/card'
import { Button } from '@/components/ui/button'
import { Alert, AlertDescription, AlertTitle } from '@/components/ui/alert'
import { Skeleton } from '@/components/ui/skeleton'
import {
  IconBrain,
  IconShield,
  IconUsers,
  IconChartBar,
  IconAlertTriangle,
  IconRefresh,
  IconActivity,
} from '@tabler/icons-react'
import { useToast } from '@/hooks/use-toast'
import { useState, useEffect, useMemo } from 'react'

export default function DashboardPage() {
  const { data, loading, error, refetch } = useDashboard()
  const { data: auditLogs, loading: logsLoading } = useAuditLogs(7) // Last 7 days
  const { toast } = useToast()
  
  // Process audit logs for activity chart (group by day)
  const activityData = useMemo(() => {
    if (!auditLogs || auditLogs.length === 0) {
      // Return empty data structure if no logs
      const days = ['Mon', 'Tue', 'Wed', 'Thu', 'Fri', 'Sat', 'Sun']
      return days.map(name => ({ name, value: 0 }))
    }
    
    // Group logs by day of week
    const dayCounts: Record<string, number> = {}
    const days = ['Sun', 'Mon', 'Tue', 'Wed', 'Thu', 'Fri', 'Sat']
    days.forEach(day => dayCounts[day] = 0)
    
    auditLogs.forEach(log => {
      const date = new Date(log.timestamp || log.created_at || Date.now())
      const dayName = days[date.getDay()]
      dayCounts[dayName] = (dayCounts[dayName] || 0) + 1
    })
    
    return days.map(day => ({ name: day, value: dayCounts[day] || 0 }))
  }, [auditLogs])

  // Process bias trends from bias analyses (if available)
  const biasData = useMemo(() => {
    // For now, return empty structure - will be populated when bias analyses endpoint is connected
    const months = ['Jan', 'Feb', 'Mar', 'Apr', 'May']
    return months.map(name => ({ name, value: 0 }))
  }, [])

  const handleRefresh = () => {
    refetch()
    toast({
      title: "Refreshing data...",
      description: "Dashboard data will be updated shortly.",
    })
  }

  if (loading || logsLoading) {
    return (
      <div className="space-y-6">
        <div className="flex items-center justify-between">
          <Skeleton className="h-10 w-48" />
          <Skeleton className="h-10 w-32" />
        </div>
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
          {[...Array(4)].map((_, i) => (
            <Skeleton key={i} className="h-32" />
          ))}
        </div>
        <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
          <Skeleton className="h-80" />
          <Skeleton className="h-80" />
        </div>
      </div>
    )
  }

  if (error && !data) {
    return (
      <div className="space-y-6">
        <Alert className="border-2 border-red-500 shadow-brutal">
          <IconAlertTriangle className="h-4 w-4" />
          <AlertTitle>Error Loading Dashboard</AlertTitle>
          <AlertDescription>
            {error.message}
            <br />
            <Button
              variant="default"
              className="mt-4"
              onClick={handleRefresh}
            >
              <IconRefresh className="mr-2 h-4 w-4" />
              Retry
            </Button>
          </AlertDescription>
        </Alert>
      </div>
    )
  }

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-4xl font-bold">Dashboard</h1>
          <p className="text-muted-foreground mt-1">
            Overview of your AI governance platform
          </p>
        </div>
        <Button variant="default" onClick={handleRefresh}>
          <IconRefresh className="mr-2 h-4 w-4" />
          Refresh
        </Button>
      </div>

      {/* Stats Grid */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
        <StatCard
          title="Total Models"
          value={data?.totalModels ?? 0}
          icon={<IconBrain className="h-5 w-5" />}
          trend={{ value: 12, label: 'vs last month', isPositive: true }}
        />
        <StatCard
          title="Total Datasets"
          value={data?.totalDatasets || 0}
          icon={<IconChartBar className="h-5 w-5" />}
          trend={{ value: 8, label: 'vs last month', isPositive: true }}
        />
        <StatCard
          title="Active Scans"
          value={data?.activeScans || 0}
          icon={<IconShield className="h-5 w-5" />}
          trend={{ value: -3, label: 'vs last week', isPositive: false }}
        />
        <StatCard
          title="System Health"
          value={data?.systemHealth?.status === 'healthy' ? '✓ Healthy' : '✗ Unhealthy'}
          icon={<IconActivity className="h-5 w-5" />}
        />
      </div>

      {/* Charts Grid */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        <SimpleChart
          title="Recent Activity"
          data={activityData}
          type="line"
          dataKey="value"
        />
        <SimpleChart
          title="Bias Detection Trends"
          data={biasData}
          type="bar"
          dataKey="value"
        />
      </div>

      {/* Recent Activity */}
      {data?.recentActivity && data.recentActivity.length > 0 && (
        <Card className="p-6 border-2 border-black shadow-brutal">
          <h3 className="text-lg font-bold mb-4">Recent Activity</h3>
          <div className="space-y-3">
            {data.recentActivity.slice(0, 5).map((activity, index) => (
              <div
                key={index}
                className="flex items-center justify-between p-3 border-2 border-black bg-white"
              >
                <div className="flex items-center gap-3">
                  <div className="p-2 border-2 border-black bg-orange">
                    <IconActivity className="h-4 w-4" />
                  </div>
                  <div>
                    <p className="font-medium">{activity.description}</p>
                    <p className="text-sm text-muted-foreground">
                      {new Date(activity.timestamp).toLocaleString()}
                    </p>
                  </div>
                </div>
                {activity.user && (
                  <div className="flex items-center gap-2">
                    <IconUsers className="h-4 w-4 text-muted-foreground" />
                    <span className="text-sm">{activity.user}</span>
                  </div>
                )}
              </div>
            ))}
          </div>
        </Card>
      )}
    </div>
  )
}
