'use client'

import { Card } from '@/components/ui/card'
import { SimpleChart } from '@/components/charts/SimpleChart'
import { StatCard } from '@/components/charts/StatCard'
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/ui/tabs'
import { Alert, AlertDescription, AlertTitle } from '@/components/ui/alert'
import { Skeleton } from '@/components/ui/skeleton'
import {
  IconChartBar,
  IconTrendingUp,
  IconUsers,
  IconTarget,
  IconAlertTriangle,
} from '@tabler/icons-react'
import { useAnalytics } from '@/lib/api/hooks/useAnalytics'
import { useModels } from '@/lib/api/hooks/useModels'
import { useMemo } from 'react'

export default function AnalyticsPage() {
  const { metrics, loading, error } = useAnalytics()
  const { data: models } = useModels()

  // Process bias trends from metrics
  const biasTrends = useMemo(() => {
    // For now, return empty structure - will be populated when bias trends endpoint is available
    const months = ['Jan', 'Feb', 'Mar', 'Apr', 'May']
    return months.map(name => ({ name, value: 0, detected: 0 }))
  }, [])

  // Process model performance from models data
  const modelPerformance = useMemo(() => {
    if (!models || models.length === 0) {
      return []
    }
    
    return models.slice(0, 4).map((model: any) => ({
      name: model.name || model.id,
      value: Math.round((model.accuracy || model.fairness_score || 0) * 100),
    }))
  }, [models])

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

  if (error && !metrics) {
    return (
      <div className="space-y-6">
        <Alert className="border-2 border-red-500 shadow-brutal">
          <IconAlertTriangle className="h-4 w-4" />
          <AlertTitle>Error Loading Analytics</AlertTitle>
          <AlertDescription>{error.message}</AlertDescription>
        </Alert>
      </div>
    )
  }

  return (
    <div className="space-y-6">
      {/* Header */}
      <div>
        <h1 className="text-4xl font-bold">Analytics</h1>
        <p className="text-muted-foreground mt-1">
          Insights and analytics for your AI governance platform
        </p>
      </div>

      {/* Stats Grid */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
        <StatCard
          title="Total Analyses"
          value={metrics?.totalAnalyses || 0}
          icon={<IconChartBar className="h-5 w-5" />}
        />
        <StatCard
          title="Bias Detected"
          value={metrics?.biasDetected || 0}
          icon={<IconTarget className="h-5 w-5" />}
        />
        <StatCard
          title="Active Users"
          value={metrics?.activeUsers || 0}
          icon={<IconUsers className="h-5 w-5" />}
        />
        <StatCard
          title="Avg Score"
          value={`${Math.round((metrics?.avgScore || 0) * 100)}%`}
          icon={<IconTrendingUp className="h-5 w-5" />}
        />
      </div>

      {/* Charts Tabs */}
      <Tabs defaultValue="bias" className="space-y-4">
        <TabsList className="border-2 border-black">
          <TabsTrigger value="bias" className="border-r-2 border-black">Bias Trends</TabsTrigger>
          <TabsTrigger value="performance">Model Performance</TabsTrigger>
          <TabsTrigger value="usage">Usage Analytics</TabsTrigger>
        </TabsList>
        
        <TabsContent value="bias" className="space-y-4">
          <SimpleChart
            title="Bias Detection Trends"
            data={biasTrends}
            type="line"
            dataKey="value"
          />
        </TabsContent>
        
        <TabsContent value="performance" className="space-y-4">
          <SimpleChart
            title="Model Performance Scores"
            data={modelPerformance}
            type="bar"
            dataKey="value"
          />
        </TabsContent>
        
        <TabsContent value="usage" className="space-y-4">
          <Card className="p-6 border-2 border-black shadow-brutal">
            <h3 className="text-lg font-bold mb-4">Usage Statistics</h3>
            <p className="text-muted-foreground">Usage analytics coming soon...</p>
          </Card>
        </TabsContent>
      </Tabs>
    </div>
  )
}

