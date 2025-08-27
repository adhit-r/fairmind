'use client'

import React, { useState, useEffect } from 'react'

interface NISTFunction {
  id: string
  name: string
  category: 'identify' | 'protect' | 'detect' | 'respond' | 'recover'
  description: string
  status: 'implemented' | 'in-progress' | 'planned' | 'not-started'
  maturityLevel: 1 | 2 | 3 | 4 | 5
  lastAssessment: string
  nextReview: string
  riskScore: number
  complianceScore: number
}

interface SecurityAssessment {
  id: string
  timestamp: string
  type: 'vulnerability' | 'penetration' | 'compliance' | 'risk'
  severity: 'critical' | 'high' | 'medium' | 'low'
  description: string
  affectedFunction: string
  status: 'open' | 'investigating' | 'resolved' | 'false-positive'
  remediation: string
}

interface NISTMetrics {
  totalFunctions: number
  implementedFunctions: number
  averageMaturity: number
  overallCompliance: number
  criticalControls: number
  activeAssessments: number
  lastFrameworkUpdate: string
  nextAssessment: string
}

export default function NISTSecurity() {
  const [loading, setLoading] = useState(true)
  const [functions, setFunctions] = useState<NISTFunction[]>([])
  const [assessments, setAssessments] = useState<SecurityAssessment[]>([])
  const [metrics, setMetrics] = useState<NISTMetrics>({
    totalFunctions: 0,
    implementedFunctions: 0,
    averageMaturity: 0,
    overallCompliance: 0,
    criticalControls: 0,
    activeAssessments: 0,
    lastFrameworkUpdate: '',
    nextAssessment: ''
  })
  const [selectedCategory, setSelectedCategory] = useState<string>('all')
  const [selectedStatus, setSelectedStatus] = useState<string>('all')

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
            NIST Security
          </h1>
          <p className="text-xs md:text-sm text-muted-foreground font-mono">
            Cybersecurity Framework Implementation
          </p>
        </div>
        <div className="flex items-center justify-center h-64">
          <div className="text-center">
            <div className="w-8 h-8 border-2 border-gold border-t-transparent rounded-full animate-spin mx-auto mb-4"></div>
            <p className="text-sm text-muted-foreground font-mono">Loading NIST Security Framework...</p>
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
          NIST Security
        </h1>
        <p className="text-xs md:text-sm text-muted-foreground font-mono">
          Cybersecurity Framework Implementation
        </p>
      </div>

      {/* Framework Overview */}
      <div className="bg-card border border-border rounded-lg p-6">
        <div className="flex items-center justify-between mb-6">
          <div>
            <h2 className="text-xl font-bold text-foreground">NIST Cybersecurity Framework</h2>
            <p className="text-sm text-muted-foreground font-mono">
              Comprehensive cybersecurity risk management
            </p>
          </div>
          <div className="text-right">
            <div className="text-3xl font-bold text-gold">85%</div>
            <span className="text-sm text-muted-foreground font-mono">Overall Compliance</span>
          </div>
        </div>
        
        <div className="grid gap-4 sm:grid-cols-2 lg:grid-cols-4">
          <div className="text-center">
            <div className="text-2xl font-bold text-foreground">5</div>
            <div className="text-xs text-muted-foreground font-mono">Framework Functions</div>
          </div>
          <div className="text-center">
            <div className="text-2xl font-bold text-foreground">4</div>
            <div className="text-xs text-muted-foreground font-mono">Implemented</div>
          </div>
          <div className="text-center">
            <div className="text-2xl font-bold text-foreground">3.6</div>
            <div className="text-xs text-muted-foreground font-mono">Avg Maturity Level</div>
          </div>
          <div className="text-center">
            <div className="text-2xl font-bold text-foreground">8</div>
            <div className="text-xs text-muted-foreground font-mono">Critical Controls</div>
          </div>
        </div>
      </div>

      {/* Framework Status */}
      <div className="grid gap-4 sm:grid-cols-2">
        <div className="bg-card border border-border rounded-lg p-4">
          <h3 className="font-bold text-foreground mb-2">Active Assessments</h3>
          <div className="text-2xl font-bold text-gold">2</div>
          <p className="text-xs text-muted-foreground font-mono">Ongoing security assessments</p>
        </div>
        <div className="bg-card border border-border rounded-lg p-4">
          <h3 className="font-bold text-foreground mb-2">Next Assessment</h3>
          <div className="text-sm font-bold text-foreground">2024-02-15</div>
          <p className="text-xs text-muted-foreground font-mono">Scheduled framework review</p>
        </div>
      </div>

      {/* Filters */}
      <div className="flex flex-col sm:flex-row gap-4 items-start sm:items-center justify-between">
        <div className="flex gap-2">
          <select
            value={selectedCategory}
            onChange={(e) => setSelectedCategory(e.target.value)}
            className="px-3 py-1 text-sm bg-card border border-border rounded-md font-mono"
          >
            <option value="all">All Categories</option>
            <option value="identify">Identify</option>
            <option value="protect">Protect</option>
            <option value="detect">Detect</option>
            <option value="respond">Respond</option>
            <option value="recover">Recover</option>
          </select>
          <select
            value={selectedStatus}
            onChange={(e) => setSelectedStatus(e.target.value)}
            className="px-3 py-1 text-sm bg-card border border-border rounded-md font-mono"
          >
            <option value="all">All Status</option>
            <option value="implemented">Implemented</option>
            <option value="in-progress">In Progress</option>
            <option value="planned">Planned</option>
            <option value="not-started">Not Started</option>
          </select>
        </div>
        <button className="px-4 py-2 bg-gold text-gold-foreground rounded-md font-mono text-sm hover:bg-gold/90 transition-colors">
          Run Assessment
        </button>
      </div>

      {/* NIST Functions */}
      <div className="space-y-4">
        <h2 className="text-xl font-bold text-foreground">Framework Functions</h2>
        
        <div className="bg-card border border-border rounded-lg p-6">
          <div className="text-center py-8">
            <div className="text-4xl mb-4">🛡️</div>
            <h3 className="text-lg font-bold text-foreground mb-2">NIST Framework Functions</h3>
            <p className="text-sm text-muted-foreground font-mono">
              Identify, Protect, Detect, Respond, and Recover functions
            </p>
          </div>
        </div>
      </div>

      {/* Security Assessments */}
      <div className="space-y-4">
        <h2 className="text-xl font-bold text-foreground">Security Assessments</h2>
        
        <div className="bg-card border border-border rounded-lg p-6">
          <div className="text-center py-8">
            <div className="text-4xl mb-4">🔍</div>
            <h3 className="text-lg font-bold text-foreground mb-2">Security Assessments</h3>
            <p className="text-sm text-muted-foreground font-mono">
              Vulnerability, penetration, compliance, and risk assessments
            </p>
          </div>
        </div>
      </div>
    </div>
  )
}
