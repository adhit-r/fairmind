'use client'

import React, { useState, useEffect } from 'react'

interface DataFlow {
  id: string
  name: string
  source: string
  destination: string
  dataType: 'training' | 'inference' | 'personal' | 'sensitive' | 'public'
  status: 'active' | 'monitoring' | 'blocked' | 'warning'
  volume: number
  frequency: string
  lastActivity: string
  securityScore: number
  complianceStatus: 'compliant' | 'non-compliant' | 'review' | 'pending'
  encryption: boolean
  anonymization: boolean
  retention: string
}

interface SecurityEvent {
  id: string
  timestamp: string
  type: 'unauthorized-access' | 'data-leak' | 'encryption-failure' | 'compliance-violation' | 'anomaly'
  severity: 'critical' | 'high' | 'medium' | 'low'
  description: string
  affectedFlow: string
  status: 'open' | 'investigating' | 'resolved' | 'false-positive'
  resolution: string
}

interface MonitoringMetrics {
  totalFlows: number
  activeFlows: number
  blockedFlows: number
  securityEvents: number
  averageSecurityScore: number
  complianceRate: number
  dataVolume: number
  lastScan: string
}

export default function DataFlowMonitoring() {
  const [loading, setLoading] = useState(true)
  const [flows, setFlows] = useState<DataFlow[]>([])
  const [events, setEvents] = useState<SecurityEvent[]>([])
  const [metrics, setMetrics] = useState<MonitoringMetrics>({
    totalFlows: 0,
    activeFlows: 0,
    blockedFlows: 0,
    securityEvents: 0,
    averageSecurityScore: 0,
    complianceRate: 0,
    dataVolume: 0,
    lastScan: ''
  })
  const [selectedDataType, setSelectedDataType] = useState<string>('all')
  const [selectedStatus, setSelectedStatus] = useState<string>('all')

  useEffect(() => {
    const timer = setTimeout(() => {
      const mockFlows: DataFlow[] = [
        {
          id: '1',
          name: 'Training Data Pipeline',
          source: 'Data Warehouse',
          destination: 'ML Training Cluster',
          dataType: 'training',
          status: 'active',
          volume: 1500000,
          frequency: 'Daily',
          lastActivity: '2024-01-20 16:30:00',
          securityScore: 95,
          complianceStatus: 'compliant',
          encryption: true,
          anonymization: true,
          retention: '7 years'
        },
        {
          id: '2',
          name: 'User Query Processing',
          source: 'API Gateway',
          destination: 'Inference Engine',
          dataType: 'inference',
          status: 'active',
          volume: 50000,
          frequency: 'Real-time',
          lastActivity: '2024-01-20 16:29:45',
          securityScore: 88,
          complianceStatus: 'compliant',
          encryption: true,
          anonymization: false,
          retention: '30 days'
        },
        {
          id: '3',
          name: 'Personal Data Export',
          source: 'User Database',
          destination: 'Analytics Platform',
          dataType: 'personal',
          status: 'warning',
          volume: 25000,
          frequency: 'Weekly',
          lastActivity: '2024-01-20 15:45:00',
          securityScore: 72,
          complianceStatus: 'review',
          encryption: true,
          anonymization: true,
          retention: '1 year'
        },
        {
          id: '4',
          name: 'Sensitive Data Backup',
          source: 'Production Database',
          destination: 'Backup Storage',
          dataType: 'sensitive',
          status: 'monitoring',
          volume: 500000,
          frequency: 'Daily',
          lastActivity: '2024-01-20 14:00:00',
          securityScore: 98,
          complianceStatus: 'compliant',
          encryption: true,
          anonymization: false,
          retention: '10 years'
        },
        {
          id: '5',
          name: 'Public Data Sync',
          source: 'Public API',
          destination: 'Cache Layer',
          dataType: 'public',
          status: 'active',
          volume: 100000,
          frequency: 'Hourly',
          lastActivity: '2024-01-20 16:00:00',
          securityScore: 85,
          complianceStatus: 'compliant',
          encryption: false,
          anonymization: false,
          retention: '7 days'
        }
      ]

      const mockEvents: SecurityEvent[] = [
        {
          id: '1',
          timestamp: '2024-01-20 16:15:00',
          type: 'anomaly',
          severity: 'medium',
          description: 'Unusual data volume detected in training pipeline',
          affectedFlow: 'Training Data Pipeline',
          status: 'investigating',
          resolution: 'Under investigation'
        },
        {
          id: '2',
          timestamp: '2024-01-20 15:30:00',
          type: 'compliance-violation',
          severity: 'high',
          description: 'Personal data export missing required anonymization',
          affectedFlow: 'Personal Data Export',
          status: 'open',
          resolution: 'Pending compliance review'
        },
        {
          id: '3',
          timestamp: '2024-01-20 14:45:00',
          type: 'encryption-failure',
          severity: 'critical',
          description: 'Encryption key rotation failed for sensitive data backup',
          affectedFlow: 'Sensitive Data Backup',
          status: 'resolved',
          resolution: 'Encryption restored, backup completed successfully'
        }
      ]

      setFlows(mockFlows)
      setEvents(mockEvents)
      
      const activeFlows = mockFlows.filter(f => f.status === 'active').length
      const blockedFlows = mockFlows.filter(f => f.status === 'blocked').length
      const avgSecurityScore = Math.round(mockFlows.reduce((sum, f) => sum + f.securityScore, 0) / mockFlows.length)
      const complianceRate = Math.round((mockFlows.filter(f => f.complianceStatus === 'compliant').length / mockFlows.length) * 100)
      const totalVolume = mockFlows.reduce((sum, f) => sum + f.volume, 0)

      setMetrics({
        totalFlows: mockFlows.length,
        activeFlows: activeFlows,
        blockedFlows: blockedFlows,
        securityEvents: mockEvents.length,
        averageSecurityScore: avgSecurityScore,
        complianceRate: complianceRate,
        dataVolume: totalVolume,
        lastScan: '2024-01-20 16:30:00'
      })
      
      setLoading(false)
    }, 1000)

    return () => clearTimeout(timer)
  }, [])

  const filteredFlows = flows.filter(flow => {
    const typeMatch = selectedDataType === 'all' || flow.dataType === selectedDataType
    const statusMatch = selectedStatus === 'all' || flow.status === selectedStatus
    return typeMatch && statusMatch
  })

  const getStatusColor = (status: string) => {
    switch (status) {
      case 'active': return 'text-green-400 bg-green-500/20'
      case 'monitoring': return 'text-blue-400 bg-blue-500/20'
      case 'blocked': return 'text-red-400 bg-red-500/20'
      case 'warning': return 'text-yellow-400 bg-yellow-500/20'
      default: return 'text-muted-foreground bg-muted'
    }
  }

  const getComplianceColor = (status: string) => {
    switch (status) {
      case 'compliant': return 'text-green-400'
      case 'non-compliant': return 'text-red-400'
      case 'review': return 'text-yellow-400'
      case 'pending': return 'text-blue-400'
      default: return 'text-muted-foreground'
    }
  }

  const getSeverityColor = (severity: string) => {
    switch (severity) {
      case 'critical': return 'text-red-400 bg-red-500/20'
      case 'high': return 'text-orange-400 bg-orange-500/20'
      case 'medium': return 'text-yellow-400 bg-yellow-500/20'
      case 'low': return 'text-blue-400 bg-blue-500/20'
      default: return 'text-muted-foreground bg-muted'
    }
  }

  const getDataTypeIcon = (type: string) => {
    switch (type) {
      case 'training': return '🎯'
      case 'inference': return '⚡'
      case 'personal': return '👤'
      case 'sensitive': return '🔒'
      case 'public': return '🌐'
      default: return '📊'
    }
  }

  const formatVolume = (volume: number) => {
    if (volume >= 1000000) return `${(volume / 1000000).toFixed(1)}M`
    if (volume >= 1000) return `${(volume / 1000).toFixed(1)}K`
    return volume.toString()
  }

  if (loading) {
    return (
      <div className="space-y-6 p-4 md:p-6 max-w-[2000px] mx-auto">
        <div className="space-y-2">
          <h1 className="text-2xl md:text-3xl font-bold tracking-tight text-gold">
            Data Flow Monitoring
          </h1>
          <p className="text-xs md:text-sm text-muted-foreground font-mono">
            Real-time Data Security & Compliance Tracking
          </p>
        </div>
        <div className="flex items-center justify-center h-64">
          <div className="text-center">
            <div className="w-8 h-8 border-2 border-gold border-t-transparent rounded-full animate-spin mx-auto mb-4"></div>
            <p className="text-sm text-muted-foreground font-mono">Loading Data Flow Monitoring...</p>
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
          Data Flow Monitoring
        </h1>
        <p className="text-xs md:text-sm text-muted-foreground font-mono">
          Real-time Data Security & Compliance Tracking
        </p>
      </div>

      {/* Monitoring Overview */}
      <div className="bg-card border border-border rounded-lg p-6">
        <div className="flex items-center justify-between mb-6">
          <div>
            <h2 className="text-xl font-bold text-foreground">Data Flow Overview</h2>
            <p className="text-sm text-muted-foreground font-mono">
              Real-time monitoring and security assessment
            </p>
          </div>
          <div className="text-right">
            <div className="text-3xl font-bold text-gold">{metrics.averageSecurityScore}%</div>
            <span className="text-sm text-muted-foreground font-mono">Average Security Score</span>
          </div>
        </div>
        
        <div className="grid gap-4 sm:grid-cols-2 lg:grid-cols-4">
          <div className="text-center">
            <div className="text-2xl font-bold text-foreground">{metrics.totalFlows}</div>
            <div className="text-xs text-muted-foreground font-mono">Total Flows</div>
          </div>
          <div className="text-center">
            <div className="text-2xl font-bold text-foreground">{metrics.activeFlows}</div>
            <div className="text-xs text-muted-foreground font-mono">Active Flows</div>
          </div>
          <div className="text-center">
            <div className="text-2xl font-bold text-foreground">{metrics.complianceRate}%</div>
            <div className="text-xs text-muted-foreground font-mono">Compliance Rate</div>
          </div>
          <div className="text-center">
            <div className="text-2xl font-bold text-foreground">{formatVolume(metrics.dataVolume)}</div>
            <div className="text-xs text-muted-foreground font-mono">Total Data Volume</div>
          </div>
        </div>
      </div>

      {/* Security Metrics */}
      <div className="grid gap-4 sm:grid-cols-2">
        <div className="bg-card border border-border rounded-lg p-4">
          <h3 className="font-bold text-foreground mb-2">Security Events</h3>
          <div className="text-2xl font-bold text-gold">{metrics.securityEvents}</div>
          <p className="text-xs text-muted-foreground font-mono">Events in last 24 hours</p>
        </div>
        <div className="bg-card border border-border rounded-lg p-4">
          <h3 className="font-bold text-foreground mb-2">Last Scan</h3>
          <div className="text-sm font-bold text-foreground">{metrics.lastScan}</div>
          <p className="text-xs text-muted-foreground font-mono">Comprehensive security scan</p>
        </div>
      </div>

      {/* Filters */}
      <div className="flex flex-col sm:flex-row gap-4 items-start sm:items-center justify-between">
        <div className="flex gap-2">
          <select
            value={selectedDataType}
            onChange={(e) => setSelectedDataType(e.target.value)}
            className="px-3 py-1 text-sm bg-card border border-border rounded-md font-mono"
          >
            <option value="all">All Data Types</option>
            <option value="training">Training Data</option>
            <option value="inference">Inference Data</option>
            <option value="personal">Personal Data</option>
            <option value="sensitive">Sensitive Data</option>
            <option value="public">Public Data</option>
          </select>
          <select
            value={selectedStatus}
            onChange={(e) => setSelectedStatus(e.target.value)}
            className="px-3 py-1 text-sm bg-card border border-border rounded-md font-mono"
          >
            <option value="all">All Status</option>
            <option value="active">Active</option>
            <option value="monitoring">Monitoring</option>
            <option value="blocked">Blocked</option>
            <option value="warning">Warning</option>
          </select>
        </div>
        <button className="px-4 py-2 bg-gold text-gold-foreground rounded-md font-mono text-sm hover:bg-gold/90 transition-colors">
          Add Data Flow
        </button>
      </div>

      {/* Data Flows */}
      <div className="space-y-4">
        <h2 className="text-xl font-bold text-foreground">Data Flows</h2>
        
        <div className="grid gap-4">
          {filteredFlows.map((flow) => (
            <div key={flow.id} className="bg-card border border-border rounded-lg p-6">
              <div className="flex items-start justify-between mb-4">
                <div className="flex-1">
                  <div className="flex items-center gap-3 mb-2">
                    <span className="text-2xl">{getDataTypeIcon(flow.dataType)}</span>
                    <h3 className="text-lg font-bold text-foreground">{flow.name}</h3>
                    <span className={`inline-flex px-2 py-1 rounded text-xs font-mono ${getStatusColor(flow.status)}`}>
                      {flow.status.toUpperCase()}
                    </span>
                    <span className={`text-sm font-mono ${getComplianceColor(flow.complianceStatus)}`}>
                      {flow.complianceStatus.toUpperCase()}
                    </span>
                  </div>
                  <p className="text-sm text-muted-foreground font-mono mb-3">
                    {flow.source} → {flow.destination}
                  </p>
                  
                  <div className="grid gap-4 sm:grid-cols-2 lg:grid-cols-4 mb-4">
                    <div>
                      <span className="text-xs text-muted-foreground font-mono">Volume</span>
                      <div className="text-lg font-bold text-foreground">{formatVolume(flow.volume)}</div>
                    </div>
                    <div>
                      <span className="text-xs text-muted-foreground font-mono">Security Score</span>
                      <div className="text-lg font-bold text-green-400">{flow.securityScore}%</div>
                    </div>
                    <div>
                      <span className="text-xs text-muted-foreground font-mono">Frequency</span>
                      <div className="text-sm font-bold text-foreground">{flow.frequency}</div>
                    </div>
                    <div>
                      <span className="text-xs text-muted-foreground font-mono">Last Activity</span>
                      <div className="text-sm font-bold text-foreground">{flow.lastActivity}</div>
                    </div>
                  </div>
                </div>
              </div>

              <div className="grid gap-4 sm:grid-cols-2 lg:grid-cols-3">
                <div className="flex items-center gap-2">
                  <span className="text-sm font-mono">Encryption:</span>
                  <span className={flow.encryption ? 'text-green-400' : 'text-red-400'}>
                    {flow.encryption ? '✓' : '✗'}
                  </span>
                </div>
                <div className="flex items-center gap-2">
                  <span className="text-sm font-mono">Anonymization:</span>
                  <span className={flow.anonymization ? 'text-green-400' : 'text-red-400'}>
                    {flow.anonymization ? '✓' : '✗'}
                  </span>
                </div>
                <div className="flex items-center gap-2">
                  <span className="text-sm font-mono">Retention:</span>
                  <span className="text-sm font-bold text-foreground">{flow.retention}</span>
                </div>
              </div>
              
              <div className="flex items-center justify-between pt-4 border-t border-border mt-4">
                <div className="flex gap-4 text-xs text-muted-foreground font-mono">
                  <span>Type: {flow.dataType}</span>
                  <span>Status: {flow.status}</span>
                </div>
                <div className="flex gap-2">
                  <button className="px-3 py-1 text-xs bg-card border border-border rounded font-mono hover:bg-accent transition-colors">
                    View Details
                  </button>
                  <button className="px-3 py-1 text-xs bg-card border border-border rounded font-mono hover:bg-accent transition-colors">
                    Monitor Flow
                  </button>
                </div>
              </div>
            </div>
          ))}
        </div>
      </div>

      {/* Security Events */}
      <div className="space-y-4">
        <h2 className="text-xl font-bold text-foreground">Security Events</h2>
        
        <div className="grid gap-4">
          {events.map((event) => (
            <div key={event.id} className="bg-card border border-border rounded-lg p-6">
              <div className="flex items-start justify-between mb-4">
                <div className="flex-1">
                  <div className="flex items-center gap-3 mb-2">
                    <h3 className="text-lg font-bold text-foreground">
                      {event.type.replace('-', ' ').toUpperCase()}
                    </h3>
                    <span className={`inline-flex px-2 py-1 rounded text-xs font-mono ${getSeverityColor(event.severity)}`}>
                      {event.severity.toUpperCase()}
                    </span>
                    <span className={`text-sm font-mono ${
                      event.status === 'resolved' ? 'text-green-400' : 
                      event.status === 'open' ? 'text-red-400' : 
                      'text-yellow-400'
                    }`}>
                      {event.status.toUpperCase()}
                    </span>
                  </div>
                  <p className="text-sm text-muted-foreground font-mono mb-3">{event.description}</p>
                  
                  <div className="grid gap-4 sm:grid-cols-2 mb-4">
                    <div>
                      <span className="text-xs text-muted-foreground font-mono">Affected Flow</span>
                      <div className="text-sm font-bold text-foreground">{event.affectedFlow}</div>
                    </div>
                    <div>
                      <span className="text-xs text-muted-foreground font-mono">Timestamp</span>
                      <div className="text-sm font-bold text-foreground">{event.timestamp}</div>
                    </div>
                  </div>
                </div>
              </div>

              <div className="mb-4">
                <h4 className="text-sm font-bold text-foreground mb-2">Resolution</h4>
                <p className="text-sm text-muted-foreground font-mono">{event.resolution}</p>
              </div>
              
              <div className="flex items-center justify-between pt-4 border-t border-border">
                <div className="text-xs text-muted-foreground font-mono">
                  Event ID: {event.id}
                </div>
                <div className="flex gap-2">
                  <button className="px-3 py-1 text-xs bg-card border border-border rounded font-mono hover:bg-accent transition-colors">
                    Update Status
                  </button>
                  <button className="px-3 py-1 text-xs bg-card border border-border rounded font-mono hover:bg-accent transition-colors">
                    View Details
                  </button>
                </div>
              </div>
            </div>
          ))}
        </div>
      </div>
    </div>
  )
}
