'use client'

import React, { useState, useEffect } from 'react'

interface ComplianceFramework {
  id: string
  name: string
  region: string
  status: 'compliant' | 'non-compliant' | 'in-progress' | 'not-applicable'
  lastAssessment: string
  nextReview: string
  riskLevel: 'low' | 'medium' | 'high' | 'critical'
  coverage: number
}

interface ComplianceMetric {
  totalFrameworks: number
  compliantFrameworks: number
  nonCompliantFrameworks: number
  inProgressFrameworks: number
  overallCompliance: number
  highRiskItems: number
  pendingActions: number
}

export default function Compliance() {
  const [loading, setLoading] = useState(true)
  const [frameworks, setFrameworks] = useState<ComplianceFramework[]>([])
  const [metrics, setMetrics] = useState<ComplianceMetric>({
    totalFrameworks: 0,
    compliantFrameworks: 0,
    nonCompliantFrameworks: 0,
    inProgressFrameworks: 0,
    overallCompliance: 0,
    highRiskItems: 0,
    pendingActions: 0
  })
  const [selectedRegion, setSelectedRegion] = useState<string>('all')
  const [selectedStatus, setSelectedStatus] = useState<string>('all')

  useEffect(() => {
    const timer = setTimeout(() => {
      const mockFrameworks: ComplianceFramework[] = [
        {
          id: '1',
          name: 'EU AI Act',
          region: 'Europe',
          status: 'compliant',
          lastAssessment: '2024-01-10',
          nextReview: '2024-04-10',
          riskLevel: 'low',
          coverage: 95
        },
        {
          id: '2',
          name: 'GDPR',
          region: 'Europe',
          status: 'compliant',
          lastAssessment: '2024-01-05',
          nextReview: '2024-07-05',
          riskLevel: 'low',
          coverage: 98
        },
        {
          id: '3',
          name: 'CCPA/CPRA',
          region: 'United States',
          status: 'in-progress',
          lastAssessment: '2024-01-15',
          nextReview: '2024-02-15',
          riskLevel: 'medium',
          coverage: 75
        },
        {
          id: '4',
          name: 'NIST AI RMF',
          region: 'United States',
          status: 'non-compliant',
          lastAssessment: '2024-01-12',
          nextReview: '2024-01-26',
          riskLevel: 'high',
          coverage: 45
        },
        {
          id: '5',
          name: 'Singapore AI Governance',
          region: 'Asia',
          status: 'not-applicable',
          lastAssessment: '2024-01-08',
          nextReview: '2024-04-08',
          riskLevel: 'low',
          coverage: 0
        },
        {
          id: '6',
          name: 'Canada AIDA',
          region: 'Canada',
          status: 'in-progress',
          lastAssessment: '2024-01-14',
          nextReview: '2024-03-14',
          riskLevel: 'medium',
          coverage: 60
        }
      ]

      setFrameworks(mockFrameworks)
      
      const compliant = mockFrameworks.filter(f => f.status === 'compliant').length
      const nonCompliant = mockFrameworks.filter(f => f.status === 'non-compliant').length
      const inProgress = mockFrameworks.filter(f => f.status === 'in-progress').length
      const highRisk = mockFrameworks.filter(f => f.riskLevel === 'high' || f.riskLevel === 'critical').length

      setMetrics({
        totalFrameworks: mockFrameworks.length,
        compliantFrameworks: compliant,
        nonCompliantFrameworks: nonCompliant,
        inProgressFrameworks: inProgress,
        overallCompliance: Math.round((compliant / mockFrameworks.length) * 100),
        highRiskItems: highRisk,
        pendingActions: nonCompliant + inProgress
      })
      
      setLoading(false)
    }, 1000)

    return () => clearTimeout(timer)
  }, [])

  const filteredFrameworks = frameworks.filter(framework => {
    const regionMatch = selectedRegion === 'all' || framework.region === selectedRegion
    const statusMatch = selectedStatus === 'all' || framework.status === selectedStatus
    return regionMatch && statusMatch
  })

  const getStatusColor = (status: string) => {
    switch (status) {
      case 'compliant': return 'text-green-400 bg-green-500/20'
      case 'non-compliant': return 'text-red-400 bg-red-500/20'
      case 'in-progress': return 'text-yellow-400 bg-yellow-500/20'
      case 'not-applicable': return 'text-gray-400 bg-gray-500/20'
      default: return 'text-muted-foreground bg-muted'
    }
  }

  const getRiskColor = (risk: string) => {
    switch (risk) {
      case 'low': return 'text-green-400'
      case 'medium': return 'text-yellow-400'
      case 'high': return 'text-orange-400'
      case 'critical': return 'text-red-400'
      default: return 'text-muted-foreground'
    }
  }

  const getCoverageColor = (coverage: number) => {
    if (coverage >= 90) return 'text-green-400'
    if (coverage >= 70) return 'text-yellow-400'
    if (coverage >= 50) return 'text-orange-400'
    return 'text-red-400'
  }

  if (loading) {
    return (
      <div className="space-y-6 p-4 md:p-6 max-w-[2000px] mx-auto">
        <div className="space-y-2">
          <h1 className="text-2xl md:text-3xl font-bold tracking-tight text-gold">
            Compliance
          </h1>
          <p className="text-xs md:text-sm text-muted-foreground font-mono">
            AI Governance & Regulatory Compliance Management
          </p>
        </div>
        <div className="flex items-center justify-center h-64">
          <div className="text-center">
            <div className="w-8 h-8 border-2 border-gold border-t-transparent rounded-full animate-spin mx-auto mb-4"></div>
            <p className="text-sm text-muted-foreground font-mono">Loading Compliance Data...</p>
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
          Compliance
        </h1>
        <p className="text-xs md:text-sm text-muted-foreground font-mono">
          AI Governance & Regulatory Compliance Management
        </p>
      </div>

      {/* Compliance Overview */}
      <div className="grid gap-4 sm:grid-cols-2 lg:grid-cols-4">
        <div className="bg-card border border-border rounded-lg p-4">
          <div className="flex items-center justify-between">
            <div>
              <p className="text-xs text-muted-foreground font-mono">Overall Compliance</p>
              <p className="text-lg font-bold text-foreground">{metrics.overallCompliance}%</p>
            </div>
            <svg className="h-4 w-4 text-gold" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 12l2 2 4-4m5.618-4.016A11.955 11.955 0 0112 2.944a11.955 11.955 0 01-8.618 3.04A12.02 12.02 0 003 9c0 5.591 3.824 10.29 9 11.622 5.176-1.332 9-6.03 9-11.622 0-1.042-.133-2.052-.382-3.016z" />
            </svg>
          </div>
        </div>

        <div className="bg-card border border-border rounded-lg p-4">
          <div className="flex items-center justify-between">
            <div>
              <p className="text-xs text-muted-foreground font-mono">Compliant Frameworks</p>
              <p className="text-lg font-bold text-foreground">{metrics.compliantFrameworks}/{metrics.totalFrameworks}</p>
            </div>
            <svg className="h-4 w-4 text-green-400" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M5 13l4 4L19 7" />
            </svg>
          </div>
        </div>

        <div className="bg-card border border-border rounded-lg p-4">
          <div className="flex items-center justify-between">
            <div>
              <p className="text-xs text-muted-foreground font-mono">High Risk Items</p>
              <p className="text-lg font-bold text-foreground">{metrics.highRiskItems}</p>
            </div>
            <svg className="h-4 w-4 text-red-400" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 9v2m0 4h.01m-6.938 4h13.856c1.54 0 2.502-1.667 1.732-2.5L13.732 4c-.77-.833-1.964-.833-2.732 0L3.732 16.5c-.77.833.192 2.5 1.732 2.5z" />
            </svg>
          </div>
        </div>

        <div className="bg-card border border-border rounded-lg p-4">
          <div className="flex items-center justify-between">
            <div>
              <p className="text-xs text-muted-foreground font-mono">Pending Actions</p>
              <p className="text-lg font-bold text-foreground">{metrics.pendingActions}</p>
            </div>
            <svg className="h-4 w-4 text-yellow-400" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 8v4l3 3m6-3a9 9 0 11-18 0 9 9 0 0118 0z" />
            </svg>
          </div>
        </div>
      </div>

      {/* Compliance Progress Chart */}
      <div className="bg-card border border-border rounded-lg p-6">
        <div className="flex items-center justify-between mb-4">
          <h3 className="text-lg font-bold text-foreground">Compliance Status Overview</h3>
        </div>
        <div className="grid gap-4 sm:grid-cols-2 lg:grid-cols-4">
          <div className="text-center">
            <div className="w-16 h-16 mx-auto mb-2 rounded-full bg-green-500/20 flex items-center justify-center">
              <span className="text-green-400 font-bold">{metrics.compliantFrameworks}</span>
            </div>
            <p className="text-xs text-muted-foreground font-mono">Compliant</p>
          </div>
          <div className="text-center">
            <div className="w-16 h-16 mx-auto mb-2 rounded-full bg-yellow-500/20 flex items-center justify-center">
              <span className="text-yellow-400 font-bold">{metrics.inProgressFrameworks}</span>
            </div>
            <p className="text-xs text-muted-foreground font-mono">In Progress</p>
          </div>
          <div className="text-center">
            <div className="w-16 h-16 mx-auto mb-2 rounded-full bg-red-500/20 flex items-center justify-center">
              <span className="text-red-400 font-bold">{metrics.nonCompliantFrameworks}</span>
            </div>
            <p className="text-xs text-muted-foreground font-mono">Non-Compliant</p>
          </div>
          <div className="text-center">
            <div className="w-16 h-16 mx-auto mb-2 rounded-full bg-gray-500/20 flex items-center justify-center">
              <span className="text-gray-400 font-bold">{metrics.totalFrameworks - metrics.compliantFrameworks - metrics.inProgressFrameworks - metrics.nonCompliantFrameworks}</span>
            </div>
            <p className="text-xs text-muted-foreground font-mono">Not Applicable</p>
          </div>
        </div>
      </div>

      {/* Filters */}
      <div className="flex flex-col sm:flex-row gap-4 items-start sm:items-center justify-between">
        <div className="flex gap-2">
          <select
            value={selectedRegion}
            onChange={(e) => setSelectedRegion(e.target.value)}
            className="px-3 py-1 text-sm bg-card border border-border rounded-md font-mono"
          >
            <option value="all">All Regions</option>
            <option value="Europe">Europe</option>
            <option value="United States">United States</option>
            <option value="Canada">Canada</option>
            <option value="Asia">Asia</option>
          </select>
          <select
            value={selectedStatus}
            onChange={(e) => setSelectedStatus(e.target.value)}
            className="px-3 py-1 text-sm bg-card border border-border rounded-md font-mono"
          >
            <option value="all">All Status</option>
            <option value="compliant">Compliant</option>
            <option value="non-compliant">Non-Compliant</option>
            <option value="in-progress">In Progress</option>
            <option value="not-applicable">Not Applicable</option>
          </select>
        </div>
        <button className="px-4 py-2 bg-gold text-gold-foreground rounded-md font-mono text-sm hover:bg-gold/90 transition-colors">
          Run Compliance Assessment
        </button>
      </div>

      {/* Frameworks Table */}
      <div className="bg-card border border-border rounded-lg overflow-hidden">
        <div className="p-4 border-b border-border">
          <h3 className="text-lg font-bold text-foreground">Regulatory Frameworks</h3>
        </div>
        <div className="overflow-x-auto">
          <table className="w-full">
            <thead className="bg-muted/50">
              <tr>
                <th className="p-3 text-left text-xs font-mono text-muted-foreground">Framework</th>
                <th className="p-3 text-left text-xs font-mono text-muted-foreground">Region</th>
                <th className="p-3 text-left text-xs font-mono text-muted-foreground">Status</th>
                <th className="p-3 text-left text-xs font-mono text-muted-foreground">Risk Level</th>
                <th className="p-3 text-left text-xs font-mono text-muted-foreground">Coverage</th>
                <th className="p-3 text-left text-xs font-mono text-muted-foreground">Last Assessment</th>
                <th className="p-3 text-left text-xs font-mono text-muted-foreground">Next Review</th>
                <th className="p-3 text-left text-xs font-mono text-muted-foreground">Actions</th>
              </tr>
            </thead>
            <tbody>
              {filteredFrameworks.map((framework) => (
                <tr key={framework.id} className="border-b border-border hover:bg-muted/30">
                  <td className="p-3 text-sm font-mono">{framework.name}</td>
                  <td className="p-3 text-sm">{framework.region}</td>
                  <td className="p-3">
                    <span className={`inline-flex px-2 py-1 rounded text-xs font-mono ${getStatusColor(framework.status)}`}>
                      {framework.status.replace('-', ' ')}
                    </span>
                  </td>
                  <td className="p-3">
                    <span className={`text-sm font-mono ${getRiskColor(framework.riskLevel)}`}>
                      {framework.riskLevel}
                    </span>
                  </td>
                  <td className="p-3">
                    <span className={`text-sm font-mono ${getCoverageColor(framework.coverage)}`}>
                      {framework.coverage}%
                    </span>
                  </td>
                  <td className="p-3 text-sm font-mono">{new Date(framework.lastAssessment).toLocaleDateString()}</td>
                  <td className="p-3 text-sm font-mono">{new Date(framework.nextReview).toLocaleDateString()}</td>
                  <td className="p-3">
                    <div className="flex gap-2">
                      <button className="px-2 py-1 text-xs bg-card border border-border rounded font-mono hover:bg-accent transition-colors">
                        View
                      </button>
                      <button className="px-2 py-1 text-xs bg-card border border-border rounded font-mono hover:bg-accent transition-colors">
                        Assess
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
