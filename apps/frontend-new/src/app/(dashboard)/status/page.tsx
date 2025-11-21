'use client'

import { Card } from '@/components/ui/card'
import { Badge } from '@/components/ui/badge'
import { StatCard } from '@/components/charts/StatCard'
import { Alert, AlertDescription, AlertTitle } from '@/components/ui/alert'
import { Skeleton } from '@/components/ui/skeleton'
import {
  IconActivity,
  IconCheck,
  IconX,
  IconAlertTriangle,
  IconServer,
  IconDatabase,
  IconApi,
} from '@tabler/icons-react'
import { useSystemHealth } from '@/lib/api/hooks/useMonitoring'
import { useMemo } from 'react'

export default function StatusPage() {
  const { health, loading, error } = useSystemHealth()

  // Transform health data to services format
  const services = useMemo(() => {
    if (!health?.services) {
      return []
    }

    return Object.entries(health.services).map(([name, service]: [string, any]) => ({
      name: name.replace(/_/g, ' ').replace(/\b\w/g, l => l.toUpperCase()),
      status: service.status || 'unknown',
      uptime: service.uptime || 'N/A',
      responseTime: service.responseTime || service.response_time || 'N/A',
    }))
  }, [health])

  const getStatusBadge = (status: string) => {
    if (status === 'healthy' || status === 'operational') {
      return <Badge variant="default" className="border-2 border-black bg-green-500">Healthy</Badge>
    } else if (status === 'degraded') {
      return <Badge variant="secondary" className="border-2 border-black bg-yellow-400">Degraded</Badge>
    } else {
      return <Badge variant="destructive" className="border-2 border-black">Down</Badge>
    }
  }

  if (loading) {
    return (
      <div className="space-y-6">
        <Skeleton className="h-10 w-48" />
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
          {[...Array(4)].map((_, i) => (
            <Skeleton key={i} className="h-32" />
          ))}
        </div>
      </div>
    )
  }

  if (error && !health) {
    return (
      <div className="space-y-6">
        <Alert className="border-2 border-red-500 shadow-brutal">
          <IconAlertTriangle className="h-4 w-4" />
          <AlertTitle>Error Loading System Status</AlertTitle>
          <AlertDescription>{error.message}</AlertDescription>
        </Alert>
      </div>
    )
  }

  const overallStatus = health?.status || 'unknown'
  const activeServices = services.filter(s => s.status === 'healthy' || s.status === 'operational').length
  const totalServices = services.length || 0

  return (
    <div className="space-y-6">
      {/* Header */}
      <div>
        <h1 className="text-4xl font-bold">System Status</h1>
        <p className="text-muted-foreground mt-1">
          Monitor system health and service status
        </p>
      </div>

      {/* Overall Stats */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
        <StatCard
          title="Overall Status"
          value={overallStatus === 'healthy' ? 'Operational' : overallStatus}
          icon={<IconCheck className="h-5 w-5" />}
        />
        <StatCard
          title="Active Services"
          value={`${activeServices}/${totalServices}`}
          icon={<IconServer className="h-5 w-5" />}
        />
        <StatCard
          title="Service Count"
          value={totalServices.toString()}
          icon={<IconActivity className="h-5 w-5" />}
        />
        <StatCard
          title="Last Updated"
          value={health?.timestamp ? new Date(health.timestamp).toLocaleTimeString() : 'N/A'}
          icon={<IconApi className="h-5 w-5" />}
        />
      </div>

      {/* Services */}
      <Card className="p-6 border-2 border-black shadow-brutal">
        <h2 className="text-2xl font-bold mb-4">Service Status</h2>
        <div className="space-y-3">
          {services.map((service) => (
            <div
              key={service.name}
              className="p-4 border-2 border-black bg-white flex items-center justify-between"
            >
              <div className="flex items-center gap-4">
                {service.status === 'healthy' ? (
                  <IconCheck className="h-5 w-5 text-green-600" />
                ) : (
                  <IconAlertTriangle className="h-5 w-5 text-yellow-600" />
                )}
                <div>
                  <p className="font-medium">{service.name}</p>
                  <div className="flex gap-4 text-sm text-muted-foreground">
                    <span>Uptime: {service.uptime}</span>
                    <span>Response: {service.responseTime}</span>
                  </div>
                </div>
              </div>
              {getStatusBadge(service.status)}
            </div>
          ))}
        </div>
      </Card>
    </div>
  )
}

