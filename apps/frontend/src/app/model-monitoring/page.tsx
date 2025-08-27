'use client'

import React, { useState, useEffect } from 'react'

interface ModelMetrics {
  id: string
  name: string
  status: 'healthy' | 'warning' | 'critical' | 'offline'
  accuracy: number
  latency: number
  throughput: number
  errorRate: number
  lastUpdated: string
  uptime: number
  requests: number
}

export default function ModelMonitoring() {
  const [loading, setLoading] = useState(true)
  const [models, setModels] = useState<ModelMetrics[]>([])
  const [selectedStatus, setSelectedStatus] = useState<string>('all')

  useEffect(() => {
    const timer = setTimeout(() => {
      setModels([
        {
          id: '1',
          name: 'GPT-4-Financial',
          status: 'healthy',
          accuracy: 94.2,
          latency: 245,
          throughput: 1250,
          errorRate: 0.8,
          lastUpdated: new Date().toISOString(),
          uptime: 99.7,
          requests: 15420
        },
        {
          id: '2',
          name: 'BERT-Sentiment',
          status: 'warning',
          accuracy: 87.5,
          latency: 89,
          throughput: 3200,
          errorRate: 2.1,
          lastUpdated: new Date().toISOString(),
          uptime: 98.9,
          requests: 8920
        }
      ])
      setLoading(false)
    }, 1000)

    return () => clearTimeout(timer)
  }, [])

  const filteredModels = models.filter(model =>
    selectedStatus === 'all' || model.status === selectedStatus
  )

  const getStatusColor = (status: string) => {
    switch (status) {
      case 'healthy': return 'text-green-400 bg-green-500/20'
      case 'warning': return 'text-yellow-400 bg-yellow-500/20'
      case 'critical': return 'text-red-400 bg-red-500/20'
      case 'offline': return 'text-gray-400 bg-gray-500/20'
      default: return 'text-muted-foreground bg-muted'
    }
  }

  if (loading) {
    return (
      <div className="space-y-6 p-4 md:p-6 max-w-[2000px] mx-auto">
        <div className="space-y-2">
          <h1 className="text-2xl md:text-3xl font-bold tracking-tight text-gold">
            Model Monitoring
          </h1>
          <p className="text-xs md:text-sm text-muted-foreground font-mono">
            Real-Time Model Performance Monitoring
          </p>
        </div>
        <div className="flex items-center justify-center h-64">
          <div className="text-center">
            <div className="w-8 h-8 border-2 border-gold border-t-transparent rounded-full animate-spin mx-auto mb-4"></div>
            <p className="text-sm text-muted-foreground font-mono">Loading Model Metrics...</p>
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
          Model Monitoring
        </h1>
        <p className="text-xs md:text-sm text-muted-foreground font-mono">
          Real-Time Model Performance Monitoring
        </p>
      </div>

      {/* Overview Metrics */}
      <div className="grid gap-4 sm:grid-cols-2 lg:grid-cols-4">
        <div className="bg-card border border-border rounded-lg p-4">
          <div className="flex items-center justify-between">
            <div>
              <p className="text-xs text-muted-foreground font-mono">TOTAL_MODELS</p>
              <p className="text-lg font-bold text-foreground">{models.length}</p>
            </div>
            <svg className="h-4 w-4 text-gold" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M19 11H5m14 0a2 2 0 012 2v6a2 2 0 01-2 2H5a2 2 0 01-2-2v-6a2 2 0 012-2m14 0V9a2 2 0 00-2-2M5 11V9a2 2 0 012-2m0 0V5a2 2 0 012-2h6a2 2 0 012 2v2M7 7h10" />
            </svg>
          </div>
        </div>

        <div className="bg-card border border-border rounded-lg p-4">
          <div className="flex items-center justify-between">
            <div>
              <p className="text-xs text-muted-foreground font-mono">HEALTHY_MODELS</p>
              <p className="text-lg font-bold text-foreground">
                {models.filter(m => m.status === 'healthy').length}
              </p>
            </div>
            <svg className="h-4 w-4 text-gold" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 12l2 2 4-4m5.618-4.016A11.955 11.955 0 0112 2.944a11.955 11.955 0 01-8.618 3.04A12.02 12.02 0 003 9c0 5.591 3.824 10.29 9 11.622 5.176-1.332 9-6.03 9-11.622 0-1.042-.133-2.052-.382-3.016z" />
            </svg>
          </div>
        </div>

        <div className="bg-card border border-border rounded-lg p-4">
          <div className="flex items-center justify-between">
            <div>
              <p className="text-xs text-muted-foreground font-mono">AVG_ACCURACY</p>
              <p className="text-lg font-bold text-foreground">
                {(models.reduce((acc, m) => acc + m.accuracy, 0) / models.length).toFixed(1)}%
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
              <p className="text-xs text-muted-foreground font-mono">TOTAL_REQUESTS</p>
              <p className="text-lg font-bold text-foreground">
                {models.reduce((acc, m) => acc + m.requests, 0).toLocaleString()}
              </p>
            </div>
            <svg className="h-4 w-4 text-gold" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M13 10V3L4 14h7v7l9-11h-7z" />
            </svg>
          </div>
        </div>
      </div>

      {/* Model Metrics Table */}
      <div className="bg-card border border-border rounded-lg overflow-hidden">
        <div className="p-4 border-b border-border">
          <div className="flex items-center justify-between">
            <div>
              <h3 className="text-sm font-bold text-gold">MODEL_METRICS</h3>
              <p className="text-xs text-muted-foreground font-mono">REAL_TIME_PERFORMANCE_DATA</p>
            </div>
            <select
              value={selectedStatus}
              onChange={(e) => setSelectedStatus(e.target.value)}
              className="bg-background border border-border rounded px-2 py-1 text-xs font-mono"
            >
              <option value="all">ALL_STATUS</option>
              <option value="healthy">HEALTHY</option>
              <option value="warning">WARNING</option>
              <option value="critical">CRITICAL</option>
              <option value="offline">OFFLINE</option>
            </select>
          </div>
        </div>
        <div className="p-4">
          <div className="rounded-md border border-border">
            <table className="w-full">
              <thead>
                <tr className="border-b border-border">
                  <th className="text-left p-3 text-xs font-mono text-foreground">MODEL</th>
                  <th className="text-left p-3 text-xs font-mono text-foreground">STATUS</th>
                  <th className="text-left p-3 text-xs font-mono text-foreground">ACCURACY</th>
                  <th className="text-left p-3 text-xs font-mono text-foreground">LATENCY</th>
                  <th className="text-left p-3 text-xs font-mono text-foreground">THROUGHPUT</th>
                  <th className="text-left p-3 text-xs font-mono text-foreground">ERROR_RATE</th>
                  <th className="text-left p-3 text-xs font-mono text-foreground">UPTIME</th>
                  <th className="text-right p-3 text-xs font-mono text-foreground">ACTIONS</th>
                </tr>
              </thead>
              <tbody>
                {filteredModels.map((model) => (
                  <tr key={model.id} className="border-b border-border">
                    <td className="p-3 text-xs font-mono text-foreground">{model.name}</td>
                    <td className="p-3 text-xs font-mono">
                      <span className={`px-2 py-1 rounded text-xs ${getStatusColor(model.status)}`}>
                        {model.status.toUpperCase()}
                      </span>
                    </td>
                    <td className="p-3 text-xs font-mono text-foreground">{model.accuracy}%</td>
                    <td className="p-3 text-xs font-mono text-foreground">{model.latency}ms</td>
                    <td className="p-3 text-xs font-mono text-foreground">{model.throughput}/s</td>
                    <td className="p-3 text-xs font-mono text-foreground">{model.errorRate}%</td>
                    <td className="p-3 text-xs font-mono text-foreground">{model.uptime}%</td>
                    <td className="p-3 text-xs font-mono text-right">
                      <button className="text-gold hover:text-gold/80 font-bold mr-2">VIEW</button>
                      <button className="text-muted-foreground hover:text-foreground font-bold">CONFIGURE</button>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </div>
      </div>
    </div>
  )
}
