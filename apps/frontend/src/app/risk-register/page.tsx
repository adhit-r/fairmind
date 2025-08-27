'use client'

import React, { useState, useEffect } from 'react'

interface Risk {
  id: string
  title: string
  description: string
  category: 'technical' | 'operational' | 'compliance' | 'strategic' | 'financial'
  severity: 'low' | 'medium' | 'high' | 'critical'
  probability: 'rare' | 'unlikely' | 'possible' | 'likely' | 'certain'
  impact: 'minimal' | 'minor' | 'moderate' | 'major' | 'catastrophic'
  status: 'identified' | 'assessed' | 'mitigated' | 'monitored' | 'closed'
  owner: string
  assignedTo: string
  createdAt: string
  lastUpdated: string
  mitigationPlan: string
  residualRisk: 'low' | 'medium' | 'high' | 'critical'
}

interface RiskMetrics {
  totalRisks: number
  criticalRisks: number
  highRisks: number
  mediumRisks: number
  lowRisks: number
  mitigatedRisks: number
  openRisks: number
  averageRiskScore: number
}

export default function RiskRegister() {
  const [loading, setLoading] = useState(true)
  const [risks, setRisks] = useState<Risk[]>([])
  const [metrics, setMetrics] = useState<RiskMetrics>({
    totalRisks: 0,
    criticalRisks: 0,
    highRisks: 0,
    mediumRisks: 0,
    lowRisks: 0,
    mitigatedRisks: 0,
    openRisks: 0,
    averageRiskScore: 0
  })
  const [selectedCategory, setSelectedCategory] = useState<string>('all')
  const [selectedSeverity, setSelectedSeverity] = useState<string>('all')
  const [selectedStatus, setSelectedStatus] = useState<string>('all')

  useEffect(() => {
    const timer = setTimeout(() => {
      const mockRisks: Risk[] = [
        {
          id: '1',
          title: 'Model Bias in Financial Decisions',
          description: 'AI model shows systematic bias against certain demographic groups in loan approval decisions',
          category: 'compliance',
          severity: 'critical',
          probability: 'likely',
          impact: 'major',
          status: 'assessed',
          owner: 'AI Governance Team',
          assignedTo: 'Data Science Lead',
          createdAt: '2024-01-10',
          lastUpdated: '2024-01-15',
          mitigationPlan: 'Implement bias detection framework and retrain model with balanced dataset',
          residualRisk: 'medium'
        },
        {
          id: '2',
          title: 'Data Privacy Breach',
          description: 'Potential exposure of sensitive customer data through model inference',
          category: 'operational',
          severity: 'high',
          probability: 'possible',
          impact: 'catastrophic',
          status: 'mitigated',
          owner: 'Security Team',
          assignedTo: 'Security Engineer',
          createdAt: '2024-01-08',
          lastUpdated: '2024-01-14',
          mitigationPlan: 'Implement data anonymization and access controls',
          residualRisk: 'low'
        },
        {
          id: '3',
          title: 'Model Performance Degradation',
          description: 'AI model accuracy declining over time due to data drift',
          category: 'technical',
          severity: 'high',
          probability: 'likely',
          impact: 'moderate',
          status: 'monitored',
          owner: 'ML Engineering Team',
          assignedTo: 'ML Engineer',
          createdAt: '2024-01-12',
          lastUpdated: '2024-01-16',
          mitigationPlan: 'Implement continuous monitoring and retraining pipeline',
          residualRisk: 'medium'
        },
        {
          id: '4',
          title: 'Regulatory Non-Compliance',
          description: 'AI system may not meet EU AI Act requirements for high-risk applications',
          category: 'compliance',
          severity: 'critical',
          probability: 'possible',
          impact: 'major',
          status: 'identified',
          owner: 'Legal Team',
          assignedTo: 'Compliance Officer',
          createdAt: '2024-01-15',
          lastUpdated: '2024-01-15',
          mitigationPlan: 'Conduct comprehensive compliance audit and implement required controls',
          residualRisk: 'high'
        },
        {
          id: '5',
          title: 'Vendor Lock-in Risk',
          description: 'Dependency on single AI model provider creating business continuity risk',
          category: 'strategic',
          severity: 'medium',
          probability: 'unlikely',
          impact: 'major',
          status: 'assessed',
          owner: 'Technology Strategy',
          assignedTo: 'CTO',
          createdAt: '2024-01-09',
          lastUpdated: '2024-01-13',
          mitigationPlan: 'Develop multi-vendor strategy and backup solutions',
          residualRisk: 'low'
        },
        {
          id: '6',
          title: 'Insufficient Model Documentation',
          description: 'Lack of comprehensive model cards and documentation for audit purposes',
          category: 'operational',
          severity: 'medium',
          probability: 'likely',
          impact: 'minor',
          status: 'mitigated',
          owner: 'AI Governance Team',
          assignedTo: 'Technical Writer',
          createdAt: '2024-01-11',
          lastUpdated: '2024-01-15',
          mitigationPlan: 'Implement standardized model documentation process',
          residualRisk: 'low'
        }
      ]

      setRisks(mockRisks)
      
      const critical = mockRisks.filter(r => r.severity === 'critical').length
      const high = mockRisks.filter(r => r.severity === 'high').length
      const medium = mockRisks.filter(r => r.severity === 'medium').length
      const low = mockRisks.filter(r => r.severity === 'low').length
      const mitigated = mockRisks.filter(r => r.status === 'mitigated').length

      setMetrics({
        totalRisks: mockRisks.length,
        criticalRisks: critical,
        highRisks: high,
        mediumRisks: medium,
        lowRisks: low,
        mitigatedRisks: mitigated,
        openRisks: mockRisks.length - mitigated,
        averageRiskScore: Math.round((critical * 4 + high * 3 + medium * 2 + low * 1) / mockRisks.length * 10) / 10
      })
      
      setLoading(false)
    }, 1000)

    return () => clearTimeout(timer)
  }, [])

  const filteredRisks = risks.filter(risk => {
    const categoryMatch = selectedCategory === 'all' || risk.category === selectedCategory
    const severityMatch = selectedSeverity === 'all' || risk.severity === selectedSeverity
    const statusMatch = selectedStatus === 'all' || risk.status === selectedStatus
    return categoryMatch && severityMatch && statusMatch
  })

  const getSeverityColor = (severity: string) => {
    switch (severity) {
      case 'critical': return 'text-red-400 bg-red-500/20'
      case 'high': return 'text-orange-400 bg-orange-500/20'
      case 'medium': return 'text-yellow-400 bg-yellow-500/20'
      case 'low': return 'text-green-400 bg-green-500/20'
      default: return 'text-muted-foreground bg-muted'
    }
  }

  const getStatusColor = (status: string) => {
    switch (status) {
      case 'identified': return 'text-blue-400 bg-blue-500/20'
      case 'assessed': return 'text-yellow-400 bg-yellow-500/20'
      case 'mitigated': return 'text-green-400 bg-green-500/20'
      case 'monitored': return 'text-purple-400 bg-purple-500/20'
      case 'closed': return 'text-gray-400 bg-gray-500/20'
      default: return 'text-muted-foreground bg-muted'
    }
  }

  const getResidualRiskColor = (risk: string) => {
    switch (risk) {
      case 'critical': return 'text-red-400'
      case 'high': return 'text-orange-400'
      case 'medium': return 'text-yellow-400'
      case 'low': return 'text-green-400'
      default: return 'text-muted-foreground'
    }
  }

  const calculateRiskScore = (severity: string, probability: string) => {
    const severityScores = { critical: 4, high: 3, medium: 2, low: 1 }
    const probabilityScores = { certain: 5, likely: 4, possible: 3, unlikely: 2, rare: 1 }
    return severityScores[severity as keyof typeof severityScores] * probabilityScores[probability as keyof typeof probabilityScores]
  }

  if (loading) {
    return (
      <div className="space-y-6 p-4 md:p-6 max-w-[2000px] mx-auto">
        <div className="space-y-2">
          <h1 className="text-2xl md:text-3xl font-bold tracking-tight text-gold">
            Risk Register
          </h1>
          <p className="text-xs md:text-sm text-muted-foreground font-mono">
            AI Risk Identification, Assessment & Mitigation Management
          </p>
        </div>
        <div className="flex items-center justify-center h-64">
          <div className="text-center">
            <div className="w-8 h-8 border-2 border-gold border-t-transparent rounded-full animate-spin mx-auto mb-4"></div>
            <p className="text-sm text-muted-foreground font-mono">Loading Risk Data...</p>
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
          Risk Register
        </h1>
        <p className="text-xs md:text-sm text-muted-foreground font-mono">
          AI Risk Identification, Assessment & Mitigation Management
        </p>
      </div>

      {/* Risk Overview */}
      <div className="grid gap-4 sm:grid-cols-2 lg:grid-cols-4">
        <div className="bg-card border border-border rounded-lg p-4">
          <div className="flex items-center justify-between">
            <div>
              <p className="text-xs text-muted-foreground font-mono">Total Risks</p>
              <p className="text-lg font-bold text-foreground">{metrics.totalRisks}</p>
            </div>
            <svg className="h-4 w-4 text-gold" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 19v-6a2 2 0 00-2-2H5a2 2 0 00-2 2v6a2 2 0 002 2h2a2 2 0 002-2zm0 0V9a2 2 0 012-2h2a2 2 0 012 2v10m-6 0a2 2 0 002 2h2a2 2 0 002-2m0 0V5a2 2 0 012-2h2a2 2 0 012 2v14a2 2 0 01-2 2h-2a2 2 0 01-2-2z" />
            </svg>
          </div>
        </div>

        <div className="bg-card border border-border rounded-lg p-4">
          <div className="flex items-center justify-between">
            <div>
              <p className="text-xs text-muted-foreground font-mono">Critical & High</p>
              <p className="text-lg font-bold text-foreground">{metrics.criticalRisks + metrics.highRisks}</p>
            </div>
            <svg className="h-4 w-4 text-red-400" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 9v2m0 4h.01m-6.938 4h13.856c1.54 0 2.502-1.667 1.732-2.5L13.732 4c-.77-.833-1.964-.833-2.732 0L3.732 16.5c-.77.833.192 2.5 1.732 2.5z" />
            </svg>
          </div>
        </div>

        <div className="bg-card border border-border rounded-lg p-4">
          <div className="flex items-center justify-between">
            <div>
              <p className="text-xs text-muted-foreground font-mono">Mitigated Risks</p>
              <p className="text-lg font-bold text-foreground">{metrics.mitigatedRisks}</p>
            </div>
            <svg className="h-4 w-4 text-green-400" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M5 13l4 4L19 7" />
            </svg>
          </div>
        </div>

        <div className="bg-card border border-border rounded-lg p-4">
          <div className="flex items-center justify-between">
            <div>
              <p className="text-xs text-muted-foreground font-mono">Avg Risk Score</p>
              <p className="text-lg font-bold text-foreground">{metrics.averageRiskScore}</p>
            </div>
            <svg className="h-4 w-4 text-yellow-400" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 19v-6a2 2 0 00-2-2H5a2 2 0 00-2 2v6a2 2 0 002 2h2a2 2 0 002-2zm0 0V9a2 2 0 012-2h2a2 2 0 012 2v10m-6 0a2 2 0 002 2h2a2 2 0 002-2m0 0V5a2 2 0 012-2h2a2 2 0 012 2v14a2 2 0 01-2 2h-2a2 2 0 01-2-2z" />
            </svg>
          </div>
        </div>
      </div>

      {/* Risk Distribution Chart */}
      <div className="bg-card border border-border rounded-lg p-6">
        <div className="flex items-center justify-between mb-4">
          <h3 className="text-lg font-bold text-foreground">Risk Distribution</h3>
        </div>
        <div className="grid gap-4 sm:grid-cols-2 lg:grid-cols-5">
          <div className="text-center">
            <div className="w-16 h-16 mx-auto mb-2 rounded-full bg-red-500/20 flex items-center justify-center">
              <span className="text-red-400 font-bold">{metrics.criticalRisks}</span>
            </div>
            <p className="text-xs text-muted-foreground font-mono">Critical</p>
          </div>
          <div className="text-center">
            <div className="w-16 h-16 mx-auto mb-2 rounded-full bg-orange-500/20 flex items-center justify-center">
              <span className="text-orange-400 font-bold">{metrics.highRisks}</span>
            </div>
            <p className="text-xs text-muted-foreground font-mono">High</p>
          </div>
          <div className="text-center">
            <div className="w-16 h-16 mx-auto mb-2 rounded-full bg-yellow-500/20 flex items-center justify-center">
              <span className="text-yellow-400 font-bold">{metrics.mediumRisks}</span>
            </div>
            <p className="text-xs text-muted-foreground font-mono">Medium</p>
          </div>
          <div className="text-center">
            <div className="w-16 h-16 mx-auto mb-2 rounded-full bg-green-500/20 flex items-center justify-center">
              <span className="text-green-400 font-bold">{metrics.lowRisks}</span>
            </div>
            <p className="text-xs text-muted-foreground font-mono">Low</p>
          </div>
          <div className="text-center">
            <div className="w-16 h-16 mx-auto mb-2 rounded-full bg-blue-500/20 flex items-center justify-center">
              <span className="text-blue-400 font-bold">{metrics.mitigatedRisks}</span>
            </div>
            <p className="text-xs text-muted-foreground font-mono">Mitigated</p>
          </div>
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
            <option value="technical">Technical</option>
            <option value="operational">Operational</option>
            <option value="compliance">Compliance</option>
            <option value="strategic">Strategic</option>
            <option value="financial">Financial</option>
          </select>
          <select
            value={selectedSeverity}
            onChange={(e) => setSelectedSeverity(e.target.value)}
            className="px-3 py-1 text-sm bg-card border border-border rounded-md font-mono"
          >
            <option value="all">All Severities</option>
            <option value="critical">Critical</option>
            <option value="high">High</option>
            <option value="medium">Medium</option>
            <option value="low">Low</option>
          </select>
          <select
            value={selectedStatus}
            onChange={(e) => setSelectedStatus(e.target.value)}
            className="px-3 py-1 text-sm bg-card border border-border rounded-md font-mono"
          >
            <option value="all">All Status</option>
            <option value="identified">Identified</option>
            <option value="assessed">Assessed</option>
            <option value="mitigated">Mitigated</option>
            <option value="monitored">Monitored</option>
            <option value="closed">Closed</option>
          </select>
        </div>
        <button className="px-4 py-2 bg-gold text-gold-foreground rounded-md font-mono text-sm hover:bg-gold/90 transition-colors">
          Add New Risk
        </button>
      </div>

      {/* Risks Table */}
      <div className="bg-card border border-border rounded-lg overflow-hidden">
        <div className="p-4 border-b border-border">
          <h3 className="text-lg font-bold text-foreground">Risk Register</h3>
        </div>
        <div className="overflow-x-auto">
          <table className="w-full">
            <thead className="bg-muted/50">
              <tr>
                <th className="p-3 text-left text-xs font-mono text-muted-foreground">Risk</th>
                <th className="p-3 text-left text-xs font-mono text-muted-foreground">Category</th>
                <th className="p-3 text-left text-xs font-mono text-muted-foreground">Severity</th>
                <th className="p-3 text-left text-xs font-mono text-muted-foreground">Probability</th>
                <th className="p-3 text-left text-xs font-mono text-muted-foreground">Risk Score</th>
                <th className="p-3 text-left text-xs font-mono text-muted-foreground">Status</th>
                <th className="p-3 text-left text-xs font-mono text-muted-foreground">Owner</th>
                <th className="p-3 text-left text-xs font-mono text-muted-foreground">Residual Risk</th>
                <th className="p-3 text-left text-xs font-mono text-muted-foreground">Actions</th>
              </tr>
            </thead>
            <tbody>
              {filteredRisks.map((risk) => (
                <tr key={risk.id} className="border-b border-border hover:bg-muted/30">
                  <td className="p-3">
                    <div>
                      <p className="text-sm font-mono font-medium">{risk.title}</p>
                      <p className="text-xs text-muted-foreground truncate max-w-xs">{risk.description}</p>
                    </div>
                  </td>
                  <td className="p-3">
                    <span className="text-xs font-mono capitalize">{risk.category}</span>
                  </td>
                  <td className="p-3">
                    <span className={`inline-flex px-2 py-1 rounded text-xs font-mono ${getSeverityColor(risk.severity)}`}>
                      {risk.severity}
                    </span>
                  </td>
                  <td className="p-3">
                    <span className="text-xs font-mono capitalize">{risk.probability}</span>
                  </td>
                  <td className="p-3">
                    <span className="text-sm font-mono font-bold">
                      {calculateRiskScore(risk.severity, risk.probability)}
                    </span>
                  </td>
                  <td className="p-3">
                    <span className={`inline-flex px-2 py-1 rounded text-xs font-mono ${getStatusColor(risk.status)}`}>
                      {risk.status}
                    </span>
                  </td>
                  <td className="p-3">
                    <span className="text-xs font-mono">{risk.owner}</span>
                  </td>
                  <td className="p-3">
                    <span className={`text-sm font-mono ${getResidualRiskColor(risk.residualRisk)}`}>
                      {risk.residualRisk}
                    </span>
                  </td>
                  <td className="p-3">
                    <div className="flex gap-2">
                      <button className="px-2 py-1 text-xs bg-card border border-border rounded font-mono hover:bg-accent transition-colors">
                        View
                      </button>
                      <button className="px-2 py-1 text-xs bg-card border border-border rounded font-mono hover:bg-accent transition-colors">
                        Update
                      </button>
                    </div>
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
