'use client'

import React, { useState, useEffect } from 'react'

interface FirewallRule {
  id: string
  name: string
  type: 'prompt' | 'response' | 'retrieval' | 'system'
  category: 'security' | 'content' | 'privacy' | 'compliance'
  status: 'active' | 'inactive' | 'testing'
  priority: 'critical' | 'high' | 'medium' | 'low'
  description: string
  patterns: string[]
  actions: string[]
  lastTriggered: string
  triggerCount: number
  falsePositives: number
  effectiveness: number
}

interface ThreatIntelligence {
  id: string
  threatType: 'prompt-injection' | 'data-exfiltration' | 'model-extraction' | 'adversarial' | 'privacy-breach'
  severity: 'critical' | 'high' | 'medium' | 'low'
  description: string
  indicators: string[]
  mitigation: string[]
  lastSeen: string
  frequency: number
  affectedModels: string[]
}

interface FirewallMetrics {
  totalRules: number
  activeRules: number
  blockedRequests: number
  allowedRequests: number
  threatDetections: number
  averageResponseTime: number
  uptime: number
  lastIncident: string
}

export default function LLMFirewall() {
  const [loading, setLoading] = useState(true)
  const [rules, setRules] = useState<FirewallRule[]>([])
  const [threats, setThreats] = useState<ThreatIntelligence[]>([])
  const [metrics, setMetrics] = useState<FirewallMetrics>({
    totalRules: 0,
    activeRules: 0,
    blockedRequests: 0,
    allowedRequests: 0,
    threatDetections: 0,
    averageResponseTime: 0,
    uptime: 0,
    lastIncident: ''
  })
  const [selectedType, setSelectedType] = useState<string>('all')
  const [selectedSeverity, setSelectedSeverity] = useState<string>('all')

  useEffect(() => {
    const timer = setTimeout(() => {
      setLoading(false)
    }, 1000)

    return () => clearTimeout(timer)
  }, [])

  if (loading) {
    return (
      <div className="space-y-6 p-4 md:p-6 max-w-[2000px] mx-auto">
        <div className="space-y-2">
          <h1 className="text-2xl md:text-3xl font-bold tracking-tight text-gold">
            LLM Firewall
          </h1>
          <p className="text-xs md:text-sm text-muted-foreground font-mono">
            AI Security & Protection Systems
          </p>
        </div>
        <div className="flex items-center justify-center h-64">
          <div className="text-center">
            <div className="w-8 h-8 border-2 border-gold border-t-transparent rounded-full animate-spin mx-auto mb-4"></div>
            <p className="text-sm text-muted-foreground font-mono">Loading LLM Firewall...</p>
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
          LLM Firewall
        </h1>
        <p className="text-xs md:text-sm text-muted-foreground font-mono">
          AI Security & Protection Systems
        </p>
      </div>

      {/* Firewall Overview */}
      <div className="bg-card border border-border rounded-lg p-6">
        <div className="flex items-center justify-between mb-6">
          <div>
            <h2 className="text-xl font-bold text-foreground">Firewall Status</h2>
            <p className="text-sm text-muted-foreground font-mono">
              Real-time protection and threat monitoring
            </p>
          </div>
          <div className="text-right">
            <div className="text-3xl font-bold text-green-400">99.98%</div>
            <span className="text-sm text-muted-foreground font-mono">Uptime</span>
          </div>
        </div>
        
        <div className="grid gap-4 sm:grid-cols-2 lg:grid-cols-4">
          <div className="text-center">
            <div className="text-2xl font-bold text-foreground">5</div>
            <div className="text-xs text-muted-foreground font-mono">Total Rules</div>
          </div>
          <div className="text-center">
            <div className="text-2xl font-bold text-foreground">5</div>
            <div className="text-xs text-muted-foreground font-mono">Active Rules</div>
          </div>
          <div className="text-center">
            <div className="text-2xl font-bold text-foreground">947</div>
            <div className="text-xs text-muted-foreground font-mono">Blocked Requests</div>
          </div>
          <div className="text-center">
            <div className="text-2xl font-bold text-foreground">135</div>
            <div className="text-xs text-muted-foreground font-mono">Threat Detections</div>
          </div>
        </div>
      </div>

      {/* Performance Metrics */}
      <div className="grid gap-4 sm:grid-cols-2">
        <div className="bg-card border border-border rounded-lg p-4">
          <h3 className="font-bold text-foreground mb-2">Response Time</h3>
          <div className="text-2xl font-bold text-gold">45ms</div>
          <p className="text-xs text-muted-foreground font-mono">Average processing time</p>
        </div>
        <div className="bg-card border border-border rounded-lg p-4">
          <h3 className="font-bold text-foreground mb-2">Last Incident</h3>
          <div className="text-sm font-bold text-foreground">2024-01-20 15:30:00</div>
          <p className="text-xs text-muted-foreground font-mono">Most recent security event</p>
        </div>
      </div>

      {/* Filters */}
      <div className="flex flex-col sm:flex-row gap-4 items-start sm:items-center justify-between">
        <div className="flex gap-2">
          <select
            value={selectedType}
            onChange={(e) => setSelectedType(e.target.value)}
            className="px-3 py-1 text-sm bg-card border border-border rounded-md font-mono"
          >
            <option value="all">All Types</option>
            <option value="prompt">Prompt Firewall</option>
            <option value="response">Response Firewall</option>
            <option value="retrieval">Retrieval Firewall</option>
            <option value="system">System Firewall</option>
          </select>
          <select
            value={selectedSeverity}
            onChange={(e) => setSelectedSeverity(e.target.value)}
            className="px-3 py-1 text-sm bg-card border border-border rounded-md font-mono"
          >
            <option value="all">All Priorities</option>
            <option value="critical">Critical</option>
            <option value="high">High</option>
            <option value="medium">Medium</option>
            <option value="low">Low</option>
          </select>
        </div>
        <button className="px-4 py-2 bg-gold text-gold-foreground rounded-md font-mono text-sm hover:bg-gold/90 transition-colors">
          Add New Rule
        </button>
      </div>

      {/* Firewall Rules */}
      <div className="space-y-4">
        <h2 className="text-xl font-bold text-foreground">Firewall Rules</h2>
        
        <div className="bg-card border border-border rounded-lg p-6">
          <div className="text-center py-8">
            <div className="text-4xl mb-4">🛡️</div>
            <h3 className="text-lg font-bold text-foreground mb-2">Firewall Rules</h3>
            <p className="text-sm text-muted-foreground font-mono">
              Prompt, response, retrieval, and system protection rules
            </p>
          </div>
        </div>
      </div>

      {/* Threat Intelligence */}
      <div className="space-y-4">
        <h2 className="text-xl font-bold text-foreground">Threat Intelligence</h2>
        
        <div className="bg-card border border-border rounded-lg p-6">
          <div className="text-center py-8">
            <div className="text-4xl mb-4">🔍</div>
            <h3 className="text-lg font-bold text-foreground mb-2">Threat Intelligence</h3>
            <p className="text-sm text-muted-foreground font-mono">
              Real-time threat detection and mitigation strategies
            </p>
          </div>
        </div>
      </div>
    </div>
  )
}
