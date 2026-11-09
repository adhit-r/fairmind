'use client'

import { Card } from '@/components/ui/card'
import { Button } from '@/components/ui/button'
import { Switch } from '@/components/ui/switch'
import { Label } from '@/components/ui/label'
import { SimpleChart } from '@/components/charts/SimpleChart'
import { StatCard } from '@/components/charts/StatCard'
import { Progress } from '@/components/ui/progress'
import { Alert, AlertDescription, AlertTitle } from '@/components/ui/alert'
import { Skeleton } from '@/components/ui/skeleton'
import {
  IconActivity,
  IconTrendingUp,
  IconTrendingDown,
  IconRefresh,
  IconBell,
  IconAlertTriangle,
} from '@tabler/icons-react'
import Link from 'next/link'
import { useState, useMemo } from 'react'
import { useMonitoring } from '@/lib/api/hooks/useMonitoring'
import { useAuditLogs } from '@/lib/api/hooks/useAuditLogs'
import { usePolicyResource, type PolicyAlert } from '@/lib/api/hooks/usePolicies'
import { useOrgId } from '@/lib/api/hooks/useOrgId'
import { when } from '@/components/packs/parts'

export default function MonitoringPage() {
  const [autoRefresh, setAutoRefresh] = useState(true)
  const [notifications, setNotifications] = useState(true)
  const { metrics, loading, error, refetch } = useMonitoring()
  const { data: auditLogs } = useAuditLogs(24) // Last 24 hours
  const policyAlerts = usePolicyResource<PolicyAlert[]>(useOrgId(), '/alerts')
  const openAlerts = (policyAlerts.data ?? []).filter((a) => a.status === 'open')

  // Process audit logs for metrics chart (group by hour)
  const metricsData = useMemo(() => {
    if (!auditLogs || auditLogs.length === 0) {
      const hours = ['00:00', '04:00', '08:00', '12:00', '16:00', '20:00']
      return hours.map(name => ({ name, value: 0 }))
    }
    
    const hourCounts: Record<string, number> = {}
    auditLogs.forEach(log => {
      const date = new Date(log.timestamp || log.created_at || Date.now())
      const hour = `${String(date.getHours()).padStart(2, '0')}:00`
      hourCounts[hour] = (hourCounts[hour] || 0) + 1
    })
    
    const hours = ['00:00', '04:00', '08:00', '12:00', '16:00', '20:00']
    return hours.map(name => ({ name, value: hourCounts[name] || 0 }))
  }, [auditLogs])

  // System performance data from metrics
  const performanceData = useMemo(() => {
    if (!metrics) {
      return [
        { name: 'CPU', value: 0 },
        { name: 'Memory', value: 0 },
        { name: 'Network', value: 0 },
        { name: 'Storage', value: 0 },
      ]
    }
    
    return [
      { name: 'Active Models', value: metrics.active_models || 0 },
      { name: 'Error Rate', value: (metrics.error_rate || 0) * 100 },
      { name: 'Compliance', value: (metrics.compliance_score || 0) * 100 },
      { name: 'Bias Alerts', value: (metrics.bias_alerts || 0) * 10 },
    ]
  }, [metrics])

  if (loading) {
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
      </div>
    )
  }

  if (error && !metrics) {
    return (
      <div className="space-y-6">
        <Alert className="border-2 border-red-500">
          <IconAlertTriangle className="h-4 w-4" />
          <AlertTitle>Error Loading Monitoring Data</AlertTitle>
          <AlertDescription>
            {error.message}
            <br />
            <Button variant="default" className="mt-4" onClick={() => refetch()}>
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
          <h1 className="text-[30px] font-semibold tracking-[-.03em]">Monitoring</h1>
          <p className="text-muted-foreground mt-1">
            Real-time system and model monitoring
          </p>
        </div>
        <div className="flex items-center gap-4">
          <div className="flex items-center gap-2">
            <Switch
              id="auto-refresh"
              checked={autoRefresh}
              onCheckedChange={setAutoRefresh}
            />
            <Label htmlFor="auto-refresh">Auto Refresh</Label>
          </div>
          <div className="flex items-center gap-2">
            <Switch
              id="notifications"
              checked={notifications}
              onCheckedChange={setNotifications}
            />
            <Label htmlFor="notifications">Notifications</Label>
          </div>
          <Button variant="default" onClick={() => refetch()}>
            <IconRefresh className="mr-2 h-4 w-4" />
            Refresh
          </Button>
        </div>
      </div>

      {/* Stats Grid */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
        <StatCard
          title="Active Models"
          value={metrics?.active_models || 0}
          icon={<IconActivity className="h-5 w-5" />}
        />
        <StatCard
          title="Total Predictions"
          value={metrics?.total_predictions?.toLocaleString() || '0'}
          icon={<IconTrendingUp className="h-5 w-5" />}
        />
        <StatCard
          title="Error Rate"
          value={`${((metrics?.error_rate || 0) * 100).toFixed(2)}%`}
          icon={<IconTrendingDown className="h-5 w-5" />}
        />
        <StatCard
          title="Avg Response"
          value={`${metrics?.avg_response_time || 0}ms`}
          icon={<IconActivity className="h-5 w-5" />}
        />
      </div>

      {/* Charts */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        <SimpleChart
          title="Request Metrics (24h)"
          data={metricsData}
          type="line"
          dataKey="value"
        />
        <Card className="p-6 fm-card">
          <h3 className="text-lg font-bold mb-4">System Performance</h3>
          <div className="space-y-4">
            {performanceData.map((item) => (
              <div key={item.name} className="space-y-2">
                <div className="flex items-center justify-between">
                  <Label className="font-medium">{item.name}</Label>
                  <span className="text-sm font-bold">{item.value}%</span>
                </div>
                <Progress value={item.value} className="h-3 border border-[var(--fm-line)]" />
              </div>
            ))}
          </div>
        </Card>
      </div>

      {/* Alerts: open policy alerts, the same records the Policies page lists */}
      <Card className="p-6 fm-card">
        <div className="flex items-center justify-between mb-4">
          <h3 className="text-lg font-bold">Recent Alerts</h3>
          <Button asChild variant="noShadow" size="sm">
            <Link href="/policies#alerts">View All</Link>
          </Button>
        </div>
        {policyAlerts.loading ? (
          <p className="text-sm text-muted-foreground">Loading alerts</p>
        ) : policyAlerts.error ? (
          <p role="alert" className="text-sm text-muted-foreground">Alerts could not be loaded. {policyAlerts.error}</p>
        ) : openAlerts.length === 0 ? (
          <p className="text-sm text-muted-foreground">No open alerts.</p>
        ) : (
          <div className="space-y-3">
            {openAlerts.slice(0, 5).map((alert) => (
              <div key={alert.id} className="flex items-center gap-3 rounded-[10px] border border-[var(--fm-line)] bg-white p-3">
                <IconBell className="h-4 w-4 shrink-0" />
                <div className="min-w-0">
                  <p className="font-medium">{alert.systemName}: {alert.ruleTitle}</p>
                  <p className="text-sm text-muted-foreground">Failing since {when(alert.openedAt)}</p>
                </div>
              </div>
            ))}
          </div>
        )}
      </Card>
    </div>
  )
}

