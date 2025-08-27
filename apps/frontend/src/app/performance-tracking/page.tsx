'use client'

import React, { useState, useEffect } from 'react'

interface PerformanceMetrics {
  id: string
  modelName: string
  accuracy: number
  precision: number
  recall: number
  f1Score: number
  latency: number
  throughput: number
  errorRate: number
  uptime: number
  lastUpdated: string
  trend: 'improving' | 'stable' | 'declining'
}

interface PerformanceChart {
  timestamp: string
  accuracy: number
  latency: number
  throughput: number
}

export default function PerformanceTracking() {
  const [loading, setLoading] = useState(true)
  const [metrics, setMetrics] = useState<PerformanceMetrics[]>([])
  const [selectedModel, setSelectedModel] = useState<string>('all')
  const [chartData, setChartData] = useState<PerformanceChart[]>([])
  const [timeRange, setTimeRange] = useState<'1h' | '24h' | '7d' | '30d'>('24h')

  useEffect(() => {
    const timer = setTimeout(() => {
      setMetrics([
        {
          id: '1',
          modelName: 'GPT-4-Financial',
          accuracy: 94.2,
          precision: 92.8,
          recall: 95.1,
          f1Score: 93.9,
          latency: 245,
          throughput: 1250,
          errorRate: 0.8,
          uptime: 99.7,
          lastUpdated: new Date().toISOString(),
          trend: 'improving'
        },
        {
          id: '2',
          modelName: 'BERT-Sentiment',
          accuracy: 87.5,
          precision: 89.2,
          recall: 85.8,
          f1Score: 87.4,
          latency: 89,
          throughput: 3200,
          errorRate: 2.1,
          uptime: 98.9,
          lastUpdated: new Date().toISOString(),
          trend: 'stable'
        },
        {
          id: '3',
          modelName: 'ResNet-Image',
          accuracy: 96.8,
          precision: 97.1,
          recall: 96.5,
          f1Score: 96.8,
          latency: 156,
          throughput: 2100,
          errorRate: 0.5,
          uptime: 99.9,
          lastUpdated: new Date().toISOString(),
          trend: 'declining'
        }
      ])

      // Generate mock chart data
      const mockChartData: PerformanceChart[] = []
      const now = new Date()
      for (let i = 23; i >= 0; i--) {
        const time = new Date(now.getTime() - i * 60 * 60 * 1000)
        mockChartData.push({
          timestamp: time.toISOString(),
          accuracy: 90 + Math.random() * 8,
          latency: 100 + Math.random() * 200,
          throughput: 1000 + Math.random() * 1500
        })
      }
      setChartData(mockChartData)
      setLoading(false)
    }, 1000)

    return () => clearTimeout(timer)
  }, [])

  const filteredMetrics = metrics.filter(metric =>
    selectedModel === 'all' || metric.modelName === selectedModel
  )

  const getTrendColor = (trend: string) => {
    switch (trend) {
      case 'improving': return 'text-green-400 bg-green-500/20'
      case 'stable': return 'text-yellow-400 bg-yellow-500/20'
      case 'declining': return 'text-red-400 bg-red-500/20'
      default: return 'text-muted-foreground bg-muted'
    }
  }

  const getTrendIcon = (trend: string) => {
    switch (trend) {
      case 'improving': return '↗'
      case 'stable': return '→'
      case 'declining': return '↘'
      default: return '→'
    }
  }

  if (loading) {
    return (
      <div className="space-y-6 p-4 md:p-6 max-w-[2000px] mx-auto">
        <div className="space-y-2">
          <h1 className="text-2xl md:text-3xl font-bold tracking-tight text-gold">
            Performance Tracking
          </h1>
          <p className="text-xs md:text-sm text-muted-foreground font-mono">
            Real-Time Model Performance Monitoring & Analytics
          </p>
        </div>
        <div className="flex items-center justify-center h-64">
          <div className="text-center">
            <div className="w-8 h-8 border-2 border-gold border-t-transparent rounded-full animate-spin mx-auto mb-4"></div>
            <p className="text-sm text-muted-foreground font-mono">Loading Performance Data...</p>
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
          Performance Tracking
        </h1>
        <p className="text-xs md:text-sm text-muted-foreground font-mono">
          Real-Time Model Performance Monitoring & Analytics
        </p>
      </div>

      {/* Controls */}
      <div className="flex flex-col sm:flex-row gap-4 items-start sm:items-center justify-between">
        <div className="flex gap-2">
          <select
            value={selectedModel}
            onChange={(e) => setSelectedModel(e.target.value)}
            className="px-3 py-1 text-sm bg-card border border-border rounded-md font-mono"
          >
            <option value="all">All Models</option>
            {metrics.map(metric => (
              <option key={metric.id} value={metric.modelName}>
                {metric.modelName}
              </option>
            ))}
          </select>
        </div>
        <div className="flex gap-2">
          {(['1h', '24h', '7d', '30d'] as const).map(range => (
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

      {/* Performance Overview */}
      <div className="grid gap-4 sm:grid-cols-2 lg:grid-cols-4">
        <div className="bg-card border border-border rounded-lg p-4">
          <div className="flex items-center justify-between">
            <div>
              <p className="text-xs text-muted-foreground font-mono">Average Accuracy</p>
              <p className="text-lg font-bold text-foreground">
                {(filteredMetrics.reduce((sum, m) => sum + m.accuracy, 0) / filteredMetrics.length).toFixed(1)}%
              </p>
            </div>
            <svg className="h-4 w-4 text-gold" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 19v-6a2 2 0 00-2-2H5a2 2 0 00-2 2v6a2 2 0 002 2h2a2 2 0 002-2zm0 0V9a2 2 0 012-2h2a2 2 0 012 2v10m-6 0a2 2 0 002 2h2a2 2 0 002-2m0 0V5a2 2 0 012-2h2a2 2 0 012 2v14a2 2 0 01-2 2h-2a2 2 0 01-2-2z" />
            </svg>
          </div>
        </div>

        <div className="bg-card border border-border rounded-lg p-4">
          <div className="flex items-center justify-between">
            <div>
              <p className="text-xs text-muted-foreground font-mono">Average Latency</p>
              <p className="text-lg font-bold text-foreground">
                {Math.round(filteredMetrics.reduce((sum, m) => sum + m.latency, 0) / filteredMetrics.length)}ms
              </p>
            </div>
            <svg className="h-4 w-4 text-gold" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M13 10V3L4 14h7v7l9-11h-7z" />
            </svg>
          </div>
        </div>

        <div className="bg-card border border-border rounded-lg p-4">
          <div className="flex items-center justify-between">
            <div>
              <p className="text-xs text-muted-foreground font-mono">Total Throughput</p>
              <p className="text-lg font-bold text-foreground">
                {filteredMetrics.reduce((sum, m) => sum + m.throughput, 0).toLocaleString()}/s
              </p>
            </div>
            <svg className="h-4 w-4 text-gold" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M16 8v8m-4-5v5m-4-2v2m-2 4h12a2 2 0 002-2V6a2 2 0 00-2-2H6a2 2 0 00-2 2v12a2 2 0 002 2z" />
            </svg>
          </div>
        </div>

        <div className="bg-card border border-border rounded-lg p-4">
          <div className="flex items-center justify-between">
            <div>
              <p className="text-xs text-muted-foreground font-mono">Average Uptime</p>
              <p className="text-lg font-bold text-foreground">
                {(filteredMetrics.reduce((sum, m) => sum + m.uptime, 0) / filteredMetrics.length).toFixed(1)}%
              </p>
            </div>
            <svg className="h-4 w-4 text-gold" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 12l2 2 4-4m5.618-4.016A11.955 11.955 0 0112 2.944a11.955 11.955 0 01-8.618 3.04A12.02 12.02 0 003 9c0 5.591 3.824 10.29 9 11.622 5.176-1.332 9-6.03 9-11.622 0-1.042-.133-2.052-.382-3.016z" />
            </svg>
          </div>
        </div>
      </div>

      {/* Performance Chart */}
      <div className="bg-card border border-border rounded-lg p-6">
        <div className="flex items-center justify-between mb-4">
          <h3 className="text-lg font-bold text-foreground">Performance Trends</h3>
          <div className="text-xs text-muted-foreground font-mono">
            Last {timeRange === '1h' ? 'hour' : timeRange === '24h' ? '24 hours' : timeRange === '7d' ? '7 days' : '30 days'}
          </div>
        </div>
        <div className="h-64 flex items-end justify-between gap-1">
          {chartData.map((point, index) => (
            <div key={index} className="flex-1 flex flex-col items-center">
              <div className="w-full bg-gold/20 rounded-t-sm" style={{ height: `${(point.accuracy - 85) * 2}%` }}></div>
              <div className="w-full bg-blue-500/20 rounded-t-sm mt-1" style={{ height: `${point.latency / 10}%` }}></div>
            </div>
          ))}
        </div>
        <div className="flex justify-between text-xs text-muted-foreground mt-2">
          <span>Accuracy (%)</span>
          <span>Latency (ms)</span>
        </div>
      </div>

      {/* Detailed Metrics Table */}
      <div className="bg-card border border-border rounded-lg overflow-hidden">
        <div className="p-4 border-b border-border">
          <h3 className="text-lg font-bold text-foreground">Model Performance Details</h3>
        </div>
        <div className="overflow-x-auto">
          <table className="w-full">
            <thead className="bg-muted/50">
              <tr>
                <th className="p-3 text-left text-xs font-mono text-muted-foreground">Model</th>
                <th className="p-3 text-left text-xs font-mono text-muted-foreground">Accuracy</th>
                <th className="p-3 text-left text-xs font-mono text-muted-foreground">F1 Score</th>
                <th className="p-3 text-left text-xs font-mono text-muted-foreground">Latency</th>
                <th className="p-3 text-left text-xs font-mono text-muted-foreground">Throughput</th>
                <th className="p-3 text-left text-xs font-mono text-muted-foreground">Error Rate</th>
                <th className="p-3 text-left text-xs font-mono text-muted-foreground">Uptime</th>
                <th className="p-3 text-left text-xs font-mono text-muted-foreground">Trend</th>
              </tr>
            </thead>
            <tbody>
              {filteredMetrics.map((metric) => (
                <tr key={metric.id} className="border-b border-border hover:bg-muted/30">
                  <td className="p-3 text-sm font-mono">{metric.modelName}</td>
                  <td className="p-3 text-sm">{metric.accuracy.toFixed(1)}%</td>
                  <td className="p-3 text-sm">{metric.f1Score.toFixed(1)}%</td>
                  <td className="p-3 text-sm">{metric.latency}ms</td>
                  <td className="p-3 text-sm">{metric.throughput.toLocaleString()}/s</td>
                  <td className="p-3 text-sm">{metric.errorRate}%</td>
                  <td className="p-3 text-sm">{metric.uptime}%</td>
                  <td className="p-3">
                    <span className={`inline-flex items-center gap-1 px-2 py-1 rounded text-xs font-mono ${getTrendColor(metric.trend)}`}>
                      {getTrendIcon(metric.trend)} {metric.trend}
                    </span>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </div>
    </div>
  )
}
