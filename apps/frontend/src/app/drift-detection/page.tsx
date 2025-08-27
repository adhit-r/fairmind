'use client'

import React, { useState, useEffect } from 'react'

interface DriftMetrics {
  dataDrift: number
  conceptDrift: number
  modelDrift: number
  lastUpdated: string
  totalAlerts: number
  criticalAlerts: number
}

interface DriftAlert {
  id: string
  modelName: string
  driftType: 'data' | 'concept' | 'model'
  severity: 'low' | 'medium' | 'high' | 'critical'
  timestamp: string
  description: string
  status: 'active' | 'resolved' | 'investigating'
}

export default function DriftDetection() {
  const [loading, setLoading] = useState(true)
  const [metrics, setMetrics] = useState<DriftMetrics>({
    dataDrift: 0,
    conceptDrift: 0,
    modelDrift: 0,
    lastUpdated: '',
    totalAlerts: 0,
    criticalAlerts: 0
  })
  const [alerts, setAlerts] = useState<DriftAlert[]>([])
  const [selectedDriftType, setSelectedDriftType] = useState<'all' | 'data' | 'concept' | 'model'>('all')

  useEffect(() => {
    // Simulate loading
    const timer = setTimeout(() => {
      setMetrics({
        dataDrift: 12.5,
        conceptDrift: 8.3,
        modelDrift: 15.7,
        lastUpdated: new Date().toISOString(),
        totalAlerts: 24,
        criticalAlerts: 3
      })
      setAlerts([
        {
          id: '1',
          modelName: 'GPT-4-Financial',
          driftType: 'data',
          severity: 'critical',
          timestamp: '2024-01-15T10:30:00Z',
          description: 'Significant deviation in financial data distribution detected',
          status: 'active'
        },
        {
          id: '2',
          modelName: 'BERT-Sentiment',
          driftType: 'concept',
          severity: 'high',
          timestamp: '2024-01-15T09:15:00Z',
          description: 'Concept drift detected in sentiment analysis patterns',
          status: 'investigating'
        },
        {
          id: '3',
          modelName: 'ResNet-Image',
          driftType: 'model',
          severity: 'medium',
          timestamp: '2024-01-15T08:45:00Z',
          description: 'Model performance degradation observed',
          status: 'resolved'
        }
      ])
      setLoading(false)
    }, 1000)

    return () => clearTimeout(timer)
  }, [])

  const filteredAlerts = alerts.filter(alert => 
    selectedDriftType === 'all' || alert.driftType === selectedDriftType
  )

  const getSeverityColor = (severity: string) => {
    switch (severity) {
      case 'critical': return 'text-red-400 bg-red-500/20'
      case 'high': return 'text-orange-400 bg-orange-500/20'
      case 'medium': return 'text-yellow-400 bg-yellow-500/20'
      case 'low': return 'text-blue-400 bg-blue-500/20'
      default: return 'text-muted-foreground bg-muted'
    }
  }

  const getStatusColor = (status: string) => {
    switch (status) {
      case 'active': return 'text-red-400'
      case 'investigating': return 'text-yellow-400'
      case 'resolved': return 'text-green-400'
      default: return 'text-muted-foreground'
    }
  }

  if (loading) {
    return (
      <div className="space-y-6 p-4 md:p-6 max-w-[2000px] mx-auto">
        <div className="space-y-2">
          <h1 className="text-2xl md:text-3xl font-bold tracking-tight text-gold">
            Drift Detection
          </h1>
          <p className="text-xs md:text-sm text-muted-foreground font-mono">
            Monitoring Model Data & Concept Drift
          </p>
        </div>
        <div className="flex items-center justify-center h-64">
          <div className="text-center">
            <div className="w-8 h-8 border-2 border-gold border-t-transparent rounded-full animate-spin mx-auto mb-4"></div>
            <p className="text-sm text-muted-foreground font-mono">Analyzing Drift Patterns...</p>
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
          Drift Detection
        </h1>
        <p className="text-xs md:text-sm text-muted-foreground font-mono">
          Monitoring Model Data & Concept Drift
        </p>
      </div>

      {/* Metrics Overview */}
      <div className="grid gap-4 sm:grid-cols-2 lg:grid-cols-4">
        <div className="bg-card border border-border rounded-lg p-4">
          <div className="flex items-center justify-between">
            <div>
              <p className="text-xs text-muted-foreground font-mono">Data Drift</p>
              <p className="text-lg font-bold text-foreground">{metrics.dataDrift}%</p>
            </div>
            <div className="flex items-center gap-2">
              <svg className="h-4 w-4 text-gold" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 19v-6a2 2 0 00-2-2H5a2 2 0 00-2 2v6a2 2 0 002 2h2a2 2 0 002-2zm0 0V9a2 2 0 012-2h2a2 2 0 012 2v10m-6 0a2 2 0 002 2h2a2 2 0 002-2m0 0V5a2 2 0 012-2h2a2 2 0 012 2v14a2 2 0 01-2 2h-2a2 2 0 01-2-2z" />
              </svg>
              <div className="flex items-center gap-1">
                <span className="text-xs text-muted-foreground">{metrics.dataDrift > 10 ? 'High Drift' : 'Normal'}</span>
              </div>
            </div>
          </div>
        </div>

        <div className="bg-card border border-border rounded-lg p-4">
          <div className="flex items-center justify-between">
            <div>
              <p className="text-xs text-muted-foreground font-mono">Concept Drift</p>
              <p className="text-lg font-bold text-foreground">{metrics.conceptDrift}%</p>
            </div>
            <div className="flex items-center gap-2">
              <svg className="h-4 w-4 text-gold" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M13 10V3L4 14h7v7l9-11h-7z" />
              </svg>
              <div className="flex items-center gap-1">
                <span className="text-xs text-muted-foreground">{metrics.conceptDrift > 8 ? 'Attention' : 'Stable'}</span>
              </div>
            </div>
          </div>
        </div>

        <div className="bg-card border border-border rounded-lg p-4">
          <div className="flex items-center justify-between">
            <div>
              <p className="text-xs text-muted-foreground font-mono">Model Drift</p>
              <p className="text-lg font-bold text-foreground">{metrics.modelDrift}%</p>
            </div>
            <div className="flex items-center gap-2">
              <svg className="h-4 w-4 text-gold" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9.663 17h4.673M12 3v1m6.364 1.636l-.707.707M21 12h-1M4 12H3m3.343-5.657l-.707-.707m2.828 9.9a5 5 0 117.072 0l-.548.547A3.374 3.374 0 0014 18.469V19a2 2 0 11-4 0v-.531c0-.895-.356-1.754-.988-2.386l-.548-.547z" />
              </svg>
              <div className="flex items-center gap-1">
                <span className="text-xs text-muted-foreground">{metrics.modelDrift > 15 ? 'Critical' : 'Acceptable'}</span>
              </div>
            </div>
          </div>
        </div>

        <div className="bg-card border border-border rounded-lg p-4">
          <div className="flex items-center justify-between">
            <div>
              <p className="text-xs text-muted-foreground font-mono">Critical Alerts</p>
              <p className="text-lg font-bold text-foreground">{metrics.criticalAlerts}</p>
            </div>
            <div className="flex items-center gap-2">
              <svg className="h-4 w-4 text-gold" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 9v2m0 4h.01m-6.938 4h13.856c1.54 0 2.502-1.667 1.732-2.5L13.732 4c-.77-.833-1.964-.833-2.732 0L3.732 16.5c-.77.833.192 2.5 1.732 2.5z" />
              </svg>
              <div className="flex items-center gap-1">
                <span className="text-xs text-muted-foreground">{metrics.criticalAlerts > 0 ? 'Action Required' : 'Clear'}</span>
              </div>
            </div>
          </div>
        </div>
      </div>

      {/* Drift Alerts */}
      <div className="bg-card border border-border rounded-lg overflow-hidden">
        <div className="p-4 border-b border-border">
          <div className="flex items-center justify-between">
            <div>
              <h3 className="text-sm font-bold text-gold">Drift Alerts</h3>
              <p className="text-xs text-muted-foreground font-mono">Active Drift Detections</p>
            </div>
            <div className="flex gap-2">
              <select 
                value={selectedDriftType}
                onChange={(e) => setSelectedDriftType(e.target.value as any)}
                className="bg-background border border-border rounded px-2 py-1 text-xs font-mono"
              >
                <option value="all">All Types</option>
                <option value="data">Data Drift</option>
                <option value="concept">Concept Drift</option>
                <option value="model">Model Drift</option>
              </select>
            </div>
          </div>
        </div>
        <div className="p-4">
          <div className="rounded-md border border-border">
            <table className="w-full">
              <thead>
                <tr className="border-b border-border">
                  <th className="text-left p-3 text-xs font-mono text-foreground">Model</th>
                  <th className="text-left p-3 text-xs font-mono text-foreground">Drift Type</th>
                  <th className="text-left p-3 text-xs font-mono text-foreground">Severity</th>
                  <th className="text-left p-3 text-xs font-mono text-foreground">Status</th>
                  <th className="text-left p-3 text-xs font-mono text-foreground">Timestamp</th>
                  <th className="text-right p-3 text-xs font-mono text-foreground">Actions</th>
                </tr>
              </thead>
              <tbody>
                {filteredAlerts.length > 0 ? (
                  filteredAlerts.map((alert) => (
                    <tr key={alert.id} className="border-b border-border">
                      <td className="p-3 text-xs font-mono text-foreground">{alert.modelName}</td>
                      <td className="p-3 text-xs font-mono text-foreground uppercase">{alert.driftType}_DRIFT</td>
                      <td className="p-3 text-xs font-mono">
                        <span className={`px-2 py-1 rounded text-xs ${getSeverityColor(alert.severity)}`}>
                          {alert.severity.toUpperCase()}
                        </span>
                      </td>
                      <td className="p-3 text-xs font-mono">
                        <span className={getStatusColor(alert.status)}>
                          {alert.status.toUpperCase()}
                        </span>
                      </td>
                      <td className="p-3 text-xs font-mono text-muted-foreground">
                        {new Date(alert.timestamp).toLocaleString()}
                      </td>
                      <td className="p-3 text-xs font-mono text-right">
                        <button className="text-gold hover:text-gold/80 font-bold mr-2">Investigate</button>
                        <button className="text-muted-foreground hover:text-foreground font-bold">Resolve</button>
                      </td>
                    </tr>
                  ))
                ) : (
                  <tr className="border-b border-border">
                    <td className="p-3 text-xs font-mono text-muted-foreground" colSpan={6}>
                      <div className="text-center py-8">
                        <h4 className="text-sm font-bold mb-2 text-foreground">No Drift Alerts</h4>
                        <p className="text-xs text-muted-foreground font-mono">
                          All Models Operating Normally
                        </p>
                      </div>
                    </td>
                  </tr>
                )}
              </tbody>
            </table>
          </div>
        </div>
      </div>

      {/* Drift Analysis Chart */}
      <div className="bg-card border border-border rounded-lg p-4">
        <div className="space-y-4">
          <div>
            <h3 className="text-sm font-bold text-gold">Drift Analysis</h3>
            <p className="text-xs text-muted-foreground font-mono">Trend Analysis Last 30 Days</p>
          </div>
          <div className="grid gap-4 sm:grid-cols-3">
            <div className="space-y-2">
              <div className="flex justify-between text-xs">
                <span className="text-muted-foreground">Data Drift</span>
                <span className="text-foreground">{metrics.dataDrift}%</span>
              </div>
              <div className="w-full bg-muted rounded-full h-2">
                <div 
                  className="bg-gold h-2 rounded-full transition-all duration-300"
                  style={{ width: `${Math.min(metrics.dataDrift, 100)}%` }}
                ></div>
              </div>
            </div>
            <div className="space-y-2">
              <div className="flex justify-between text-xs">
                <span className="text-muted-foreground">Concept Drift</span>
                <span className="text-foreground">{metrics.conceptDrift}%</span>
              </div>
              <div className="w-full bg-muted rounded-full h-2">
                <div 
                  className="bg-gold h-2 rounded-full transition-all duration-300"
                  style={{ width: `${Math.min(metrics.conceptDrift, 100)}%` }}
                ></div>
              </div>
            </div>
            <div className="space-y-2">
              <div className="flex justify-between text-xs">
                <span className="text-muted-foreground">Model Drift</span>
                <span className="text-foreground">{metrics.modelDrift}%</span>
              </div>
              <div className="w-full bg-muted rounded-full h-2">
                <div 
                  className="bg-gold h-2 rounded-full transition-all duration-300"
                  style={{ width: `${Math.min(metrics.modelDrift, 100)}%` }}
                ></div>
              </div>
            </div>
          </div>
        </div>
      </div>
    </div>
  )
}
