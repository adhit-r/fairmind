'use client'

import React, { useState, useEffect } from 'react'

interface AnalyticsMetric {
  id: string
  name: string
  value: number
  change: number
  trend: 'up' | 'down' | 'stable'
  category: 'performance' | 'security' | 'compliance' | 'usage'
}

interface AnalyticsChart {
  timestamp: string
  models: number
  requests: number
  errors: number
  compliance: number
}

interface TopModel {
  id: string
  name: string
  requests: number
  accuracy: number
  latency: number
  usage: number
}

export default function Analytics() {
  const [loading, setLoading] = useState(true)
  const [metrics, setMetrics] = useState<AnalyticsMetric[]>([])
  const [chartData, setChartData] = useState<AnalyticsChart[]>([])
  const [topModels, setTopModels] = useState<TopModel[]>([])
  const [selectedCategory, setSelectedCategory] = useState<string>('all')
  const [timeRange, setTimeRange] = useState<'7d' | '30d' | '90d'>('30d')

  useEffect(() => {
    const timer = setTimeout(() => {
      setMetrics([
        {
          id: '1',
          name: 'Total Model Requests',
          value: 15420,
          change: 12.5,
          trend: 'up',
          category: 'usage'
        },
        {
          id: '2',
          name: 'Average Response Time',
          value: 245,
          change: -8.3,
          trend: 'down',
          category: 'performance'
        },
        {
          id: '3',
          name: 'Security Incidents',
          value: 3,
          change: -25.0,
          trend: 'down',
          category: 'security'
        },
        {
          id: '4',
          name: 'Compliance Score',
          value: 94.2,
          change: 2.1,
          trend: 'up',
          category: 'compliance'
        },
        {
          id: '5',
          name: 'Model Accuracy',
          value: 92.8,
          change: 1.5,
          trend: 'up',
          category: 'performance'
        },
        {
          id: '6',
          name: 'Data Processing Volume',
          value: 1250,
          change: 18.7,
          trend: 'up',
          category: 'usage'
        }
      ])

      // Generate mock chart data
      const mockChartData: AnalyticsChart[] = []
      const now = new Date()
      for (let i = 29; i >= 0; i--) {
        const time = new Date(now.getTime() - i * 24 * 60 * 60 * 1000)
        mockChartData.push({
          timestamp: time.toISOString(),
          models: 5 + Math.floor(Math.random() * 3),
          requests: 400 + Math.random() * 200,
          errors: Math.random() * 10,
          compliance: 90 + Math.random() * 8
        })
      }
      setChartData(mockChartData)

      setTopModels([
        {
          id: '1',
          name: 'GPT-4-Financial',
          requests: 5420,
          accuracy: 94.2,
          latency: 245,
          usage: 35.2
        },
        {
          id: '2',
          name: 'BERT-Sentiment',
          requests: 3890,
          accuracy: 87.5,
          latency: 89,
          usage: 25.2
        },
        {
          id: '3',
          name: 'ResNet-Image',
          requests: 3240,
          accuracy: 96.8,
          latency: 156,
          usage: 21.0
        },
        {
          id: '4',
          name: 'T5-Text',
          requests: 1870,
          accuracy: 91.3,
          latency: 189,
          usage: 12.1
        },
        {
          id: '5',
          name: 'YOLO-Object',
          requests: 1000,
          accuracy: 89.7,
          latency: 78,
          usage: 6.5
        }
      ])

      setLoading(false)
    }, 1000)

    return () => clearTimeout(timer)
  }, [])

  const filteredMetrics = metrics.filter(metric =>
    selectedCategory === 'all' || metric.category === selectedCategory
  )

  const getTrendColor = (trend: string) => {
    switch (trend) {
      case 'up': return 'text-green-400'
      case 'down': return 'text-red-400'
      case 'stable': return 'text-yellow-400'
      default: return 'text-muted-foreground'
    }
  }

  const getTrendIcon = (trend: string) => {
    switch (trend) {
      case 'up': return '↗'
      case 'down': return '↘'
      case 'stable': return '→'
      default: return '→'
    }
  }

  const getCategoryColor = (category: string) => {
    switch (category) {
      case 'performance': return 'text-blue-400'
      case 'security': return 'text-red-400'
      case 'compliance': return 'text-green-400'
      case 'usage': return 'text-purple-400'
      default: return 'text-muted-foreground'
    }
  }

  if (loading) {
    return (
      <div className="space-y-6 p-4 md:p-6 max-w-[2000px] mx-auto">
        <div className="space-y-2">
          <h1 className="text-2xl md:text-3xl font-bold tracking-tight text-gold">
            Analytics
          </h1>
          <p className="text-xs md:text-sm text-muted-foreground font-mono">
            AI Platform Analytics & Performance Insights
          </p>
        </div>
        <div className="flex items-center justify-center h-64">
          <div className="text-center">
            <div className="w-8 h-8 border-2 border-gold border-t-transparent rounded-full animate-spin mx-auto mb-4"></div>
            <p className="text-sm text-muted-foreground font-mono">Loading Analytics Data...</p>
          </div>
        </div>
      </div>
    )
  }

  return (
    <div className="space-y-6 p-4 md:p-6 max-w-[2000px] mx-auto">
      {/* Header */}
      <div className="space-y-2">
        <h1 className="text-2xl md:text-3xl font-bold tracking-tight text-gold">
          Analytics
        </h1>
        <p className="text-xs md:text-sm text-muted-foreground font-mono">
          AI Platform Analytics & Performance Insights
        </p>
      </div>

      {/* Controls */}
      <div className="flex flex-col sm:flex-row gap-4 items-start sm:items-center justify-between">
        <div className="flex gap-2">
          <select
            value={selectedCategory}
            onChange={(e) => setSelectedCategory(e.target.value)}
            className="px-3 py-1 text-sm bg-card border border-border rounded-md font-mono"
          >
            <option value="all">All Categories</option>
            <option value="performance">Performance</option>
            <option value="security">Security</option>
            <option value="compliance">Compliance</option>
            <option value="usage">Usage</option>
          </select>
        </div>
        <div className="flex gap-2">
          {(['7d', '30d', '90d'] as const).map(range => (
            <button
              key={range}
              onClick={() => setTimeRange(range)}
              className={`px-3 py-1 text-xs font-mono rounded-md transition-colors ${
                timeRange === range
                  ? 'bg-gold text-gold-foreground'
                  : 'bg-card border border-border text-muted-foreground hover:text-foreground'
              }`}
            >
              {range}
            </button>
          ))}
        </div>
      </div>

      {/* Key Metrics */}
      <div className="grid gap-4 sm:grid-cols-2 lg:grid-cols-3">
        {filteredMetrics.map((metric) => (
          <div key={metric.id} className="bg-card border border-border rounded-lg p-4">
            <div className="flex items-center justify-between mb-2">
              <p className="text-xs text-muted-foreground font-mono">{metric.name}</p>
              <span className={`text-xs font-mono ${getCategoryColor(metric.category)}`}>
                {metric.category}
              </span>
            </div>
            <div className="flex items-center justify-between">
              <p className="text-lg font-bold text-foreground">
                {metric.value.toLocaleString()}
                {metric.name.includes('Score') || metric.name.includes('Accuracy') ? '%' : ''}
                {metric.name.includes('Time') ? 'ms' : ''}
              </p>
              <div className="flex items-center gap-1">
                <span className={`text-xs font-mono ${getTrendColor(metric.trend)}`}>
                  {getTrendIcon(metric.trend)} {Math.abs(metric.change)}%
                </span>
              </div>
            </div>
          </div>
        ))}
      </div>

      {/* Analytics Charts */}
      <div className="grid gap-6 lg:grid-cols-2">
        {/* Usage Trends */}
        <div className="bg-card border border-border rounded-lg p-6">
          <div className="flex items-center justify-between mb-4">
            <h3 className="text-lg font-bold text-foreground">Usage Trends</h3>
            <div className="text-xs text-muted-foreground font-mono">
              Last {timeRange === '7d' ? '7 days' : timeRange === '30d' ? '30 days' : '90 days'}
            </div>
          </div>
          <div className="h-64 flex items-end justify-between gap-1">
            {chartData.slice(-7).map((point, index) => (
              <div key={index} className="flex-1 flex flex-col items-center">
                <div className="w-full bg-gold/20 rounded-t-sm" style={{ height: `${(point.requests / 600) * 100}%` }}></div>
                <div className="w-full bg-blue-500/20 rounded-t-sm mt-1" style={{ height: `${(point.models / 8) * 100}%` }}></div>
              </div>
            ))}
          </div>
          <div className="flex justify-between text-xs text-muted-foreground mt-2">
            <span>Requests</span>
            <span>Active Models</span>
          </div>
        </div>

        {/* Performance Metrics */}
        <div className="bg-card border border-border rounded-lg p-6">
          <div className="flex items-center justify-between mb-4">
            <h3 className="text-lg font-bold text-foreground">Performance Metrics</h3>
          </div>
          <div className="h-64 flex items-end justify-between gap-1">
            {chartData.slice(-7).map((point, index) => (
              <div key={index} className="flex-1 flex flex-col items-center">
                <div className="w-full bg-green-500/20 rounded-t-sm" style={{ height: `${point.compliance - 85}%` }}></div>
                <div className="w-full bg-red-500/20 rounded-t-sm mt-1" style={{ height: `${point.errors * 5}%` }}></div>
              </div>
            ))}
          </div>
          <div className="flex justify-between text-xs text-muted-foreground mt-2">
            <span>Compliance (%)</span>
            <span>Errors</span>
          </div>
        </div>
      </div>

      {/* Top Models */}
      <div className="bg-card border border-border rounded-lg overflow-hidden">
        <div className="p-4 border-b border-border">
          <h3 className="text-lg font-bold text-foreground">Top Performing Models</h3>
        </div>
        <div className="overflow-x-auto">
          <table className="w-full">
            <thead className="bg-muted/50">
              <tr>
                <th className="p-3 text-left text-xs font-mono text-muted-foreground">Model</th>
                <th className="p-3 text-left text-xs font-mono text-muted-foreground">Requests</th>
                <th className="p-3 text-left text-xs font-mono text-muted-foreground">Accuracy</th>
                <th className="p-3 text-left text-xs font-mono text-muted-foreground">Latency</th>
                <th className="p-3 text-left text-xs font-mono text-muted-foreground">Usage %</th>
                <th className="p-3 text-left text-xs font-mono text-muted-foreground">Trend</th>
              </tr>
            </thead>
            <tbody>
              {topModels.map((model, index) => (
                <tr key={model.id} className="border-b border-border hover:bg-muted/30">
                  <td className="p-3 text-sm font-mono">{model.name}</td>
                  <td className="p-3 text-sm">{model.requests.toLocaleString()}</td>
                  <td className="p-3 text-sm">{model.accuracy.toFixed(1)}%</td>
                  <td className="p-3 text-sm">{model.latency}ms</td>
                  <td className="p-3 text-sm">{model.usage.toFixed(1)}%</td>
                  <td className="p-3">
                    <div className="flex items-center gap-2">
                      <div className="w-16 h-2 bg-muted rounded-full overflow-hidden">
                        <div 
                          className="h-full bg-gold rounded-full" 
                          style={{ width: `${model.usage}%` }}
                        ></div>
                      </div>
                      <span className="text-xs text-muted-foreground">
                        #{index + 1}
                      </span>
                    </div>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </div>

      {/* Insights */}
      <div className="grid gap-4 sm:grid-cols-2 lg:grid-cols-3">
        <div className="bg-card border border-border rounded-lg p-4">
          <div className="flex items-center gap-2 mb-2">
            <svg className="h-4 w-4 text-green-400" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M13 7h8m0 0v8m0-8l-8 8-4-4-6 6" />
            </svg>
            <h4 className="text-sm font-bold text-foreground">Performance Insight</h4>
          </div>
          <p className="text-xs text-muted-foreground font-mono">
            Average response time improved by 8.3% over the last 30 days, indicating better model optimization.
          </p>
        </div>

        <div className="bg-card border border-border rounded-lg p-4">
          <div className="flex items-center gap-2 mb-2">
            <svg className="h-4 w-4 text-blue-400" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 19v-6a2 2 0 00-2-2H5a2 2 0 00-2 2v6a2 2 0 002 2h2a2 2 0 002-2zm0 0V9a2 2 0 012-2h2a2 2 0 012 2v10m-6 0a2 2 0 002 2h2a2 2 0 002-2m0 0V5a2 2 0 012-2h2a2 2 0 012 2v14a2 2 0 01-2 2h-2a2 2 0 01-2-2z" />
            </svg>
            <h4 className="text-sm font-bold text-foreground">Usage Trend</h4>
          </div>
          <p className="text-xs text-muted-foreground font-mono">
            GPT-4-Financial model usage increased by 35.2%, showing growing demand for financial AI services.
          </p>
        </div>

        <div className="bg-card border border-border rounded-lg p-4">
          <div className="flex items-center gap-2 mb-2">
            <svg className="h-4 w-4 text-yellow-400" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 9v2m0 4h.01m-6.938 4h13.856c1.54 0 2.502-1.667 1.732-2.5L13.732 4c-.77-.833-1.964-.833-2.732 0L3.732 16.5c-.77.833.192 2.5 1.732 2.5z" />
            </svg>
            <h4 className="text-sm font-bold text-foreground">Security Alert</h4>
          </div>
          <p className="text-xs text-muted-foreground font-mono">
            Security incidents decreased by 25%, but continuous monitoring is recommended for emerging threats.
          </p>
        </div>
      </div>
    </div>
  )
}
