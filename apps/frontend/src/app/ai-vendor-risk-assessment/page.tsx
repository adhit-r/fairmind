'use client'

import React, { useState, useEffect } from 'react'

interface Vendor {
  id: string
  name: string
  category: 'ai-platform' | 'data-provider' | 'ml-tools' | 'consulting' | 'infrastructure'
  riskLevel: 'low' | 'medium' | 'high' | 'critical'
  complianceScore: number
  securityScore: number
  reliabilityScore: number
  overallScore: number
  status: 'approved' | 'under-review' | 'rejected' | 'monitoring'
  lastAssessment: string
  nextReview: string
  contractValue: string
  criticalIssues: number
  recommendations: string[]
}

interface VendorMetrics {
  totalVendors: number
  approvedVendors: number
  highRiskVendors: number
  criticalVendors: number
  averageScore: number
  totalContractValue: string
  pendingReviews: number
}

export default function AIVendorRiskAssessment() {
  const [loading, setLoading] = useState(true)
  const [vendors, setVendors] = useState<Vendor[]>([])
  const [metrics, setMetrics] = useState<VendorMetrics>({
    totalVendors: 0,
    approvedVendors: 0,
    highRiskVendors: 0,
    criticalVendors: 0,
    averageScore: 0,
    totalContractValue: '$0',
    pendingReviews: 0
  })
  const [selectedCategory, setSelectedCategory] = useState<string>('all')
  const [selectedRiskLevel, setSelectedRiskLevel] = useState<string>('all')
  const [selectedStatus, setSelectedStatus] = useState<string>('all')

  useEffect(() => {
    const timer = setTimeout(() => {
      const mockVendors: Vendor[] = [
        {
          id: '1',
          name: 'OpenAI',
          category: 'ai-platform',
          riskLevel: 'medium',
          complianceScore: 85,
          securityScore: 90,
          reliabilityScore: 88,
          overallScore: 87,
          status: 'approved',
          lastAssessment: '2024-01-10',
          nextReview: '2024-04-10',
          contractValue: '$250,000',
          criticalIssues: 0,
          recommendations: ['Monitor API usage patterns', 'Review data retention policies']
        },
        {
          id: '2',
          name: 'Anthropic',
          category: 'ai-platform',
          riskLevel: 'low',
          complianceScore: 92,
          securityScore: 95,
          reliabilityScore: 90,
          overallScore: 92,
          status: 'approved',
          lastAssessment: '2024-01-08',
          nextReview: '2024-04-08',
          contractValue: '$180,000',
          criticalIssues: 0,
          recommendations: ['Continue monitoring performance', 'Consider expanding partnership']
        },
        {
          id: '3',
          name: 'DataRobot',
          category: 'ml-tools',
          riskLevel: 'high',
          complianceScore: 65,
          securityScore: 70,
          reliabilityScore: 75,
          overallScore: 70,
          status: 'monitoring',
          lastAssessment: '2024-01-12',
          nextReview: '2024-02-12',
          contractValue: '$120,000',
          criticalIssues: 2,
          recommendations: ['Address security vulnerabilities', 'Improve compliance documentation']
        },
        {
          id: '4',
          name: 'Snowflake',
          category: 'infrastructure',
          riskLevel: 'low',
          complianceScore: 88,
          securityScore: 92,
          reliabilityScore: 95,
          overallScore: 92,
          status: 'approved',
          lastAssessment: '2024-01-05',
          nextReview: '2024-04-05',
          contractValue: '$500,000',
          criticalIssues: 0,
          recommendations: ['Monitor data transfer costs', 'Optimize query performance']
        },
        {
          id: '5',
          name: 'Scale AI',
          category: 'data-provider',
          riskLevel: 'critical',
          complianceScore: 45,
          securityScore: 50,
          reliabilityScore: 60,
          overallScore: 52,
          status: 'under-review',
          lastAssessment: '2024-01-15',
          nextReview: '2024-01-30',
          contractValue: '$75,000',
          criticalIssues: 5,
          recommendations: ['Immediate security audit required', 'Review data handling practices', 'Consider alternative vendors']
        },
        {
          id: '6',
          name: 'McKinsey AI',
          category: 'consulting',
          riskLevel: 'medium',
          complianceScore: 80,
          securityScore: 85,
          reliabilityScore: 82,
          overallScore: 82,
          status: 'approved',
          lastAssessment: '2024-01-09',
          nextReview: '2024-04-09',
          contractValue: '$300,000',
          criticalIssues: 1,
          recommendations: ['Clarify IP ownership terms', 'Strengthen confidentiality agreements']
        }
      ]

      setVendors(mockVendors)
      
      const approved = mockVendors.filter(v => v.status === 'approved').length
      const highRisk = mockVendors.filter(v => v.riskLevel === 'high').length
      const critical = mockVendors.filter(v => v.riskLevel === 'critical').length
      const pending = mockVendors.filter(v => v.status === 'under-review').length
      const avgScore = Math.round(mockVendors.reduce((sum, v) => sum + v.overallScore, 0) / mockVendors.length)
      const totalValue = mockVendors.reduce((sum, v) => sum + parseInt(v.contractValue.replace(/[$,]/g, '')), 0)

      setMetrics({
        totalVendors: mockVendors.length,
        approvedVendors: approved,
        highRiskVendors: highRisk,
        criticalVendors: critical,
        averageScore: avgScore,
        totalContractValue: `$${totalValue.toLocaleString()}`,
        pendingReviews: pending
      })
      
      setLoading(false)
    }, 1000)

    return () => clearTimeout(timer)
  }, [])

  const filteredVendors = vendors.filter(vendor => {
    const categoryMatch = selectedCategory === 'all' || vendor.category === selectedCategory
    const riskMatch = selectedRiskLevel === 'all' || vendor.riskLevel === selectedRiskLevel
    const statusMatch = selectedStatus === 'all' || vendor.status === selectedStatus
    return categoryMatch && riskMatch && statusMatch
  })

  const getRiskLevelColor = (level: string) => {
    switch (level) {
      case 'critical': return 'text-red-400 bg-red-500/20'
      case 'high': return 'text-orange-400 bg-orange-500/20'
      case 'medium': return 'text-yellow-400 bg-yellow-500/20'
      case 'low': return 'text-green-400 bg-green-500/20'
      default: return 'text-muted-foreground bg-muted'
    }
  }

  const getStatusColor = (status: string) => {
    switch (status) {
      case 'approved': return 'text-green-400 bg-green-500/20'
      case 'under-review': return 'text-yellow-400 bg-yellow-500/20'
      case 'monitoring': return 'text-orange-400 bg-orange-500/20'
      case 'rejected': return 'text-red-400 bg-red-500/20'
      default: return 'text-muted-foreground bg-muted'
    }
  }

  const getScoreColor = (score: number) => {
    if (score >= 85) return 'text-green-400'
    if (score >= 70) return 'text-yellow-400'
    if (score >= 55) return 'text-orange-400'
    return 'text-red-400'
  }

  if (loading) {
    return (
      <div className="space-y-6 p-4 md:p-6 max-w-[2000px] mx-auto">
        <div className="space-y-2">
          <h1 className="text-2xl md:text-3xl font-bold tracking-tight text-gold">
            AI Vendor Risk Assessment
          </h1>
          <p className="text-xs md:text-sm text-muted-foreground font-mono">
            Third-Party AI Vendor Evaluation & Risk Management
          </p>
        </div>
        <div className="flex items-center justify-center h-64">
          <div className="text-center">
            <div className="w-8 h-8 border-2 border-gold border-t-transparent rounded-full animate-spin mx-auto mb-4"></div>
            <p className="text-sm text-muted-foreground font-mono">Loading Vendor Data...</p>
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
          AI Vendor Risk Assessment
        </h1>
        <p className="text-xs md:text-sm text-muted-foreground font-mono">
          Third-Party AI Vendor Evaluation & Risk Management
        </p>
      </div>

      {/* Vendor Overview */}
      <div className="grid gap-4 sm:grid-cols-2 lg:grid-cols-4">
        <div className="bg-card border border-border rounded-lg p-4">
          <div className="flex items-center justify-between">
            <div>
              <p className="text-xs text-muted-foreground font-mono">Total Vendors</p>
              <p className="text-lg font-bold text-foreground">{metrics.totalVendors}</p>
            </div>
            <svg className="h-4 w-4 text-gold" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M17 20h5v-2a3 3 0 00-5.356-1.857M17 20H7m10 0v-2c0-.656-.126-1.283-.356-1.857M7 20H2v-2a3 3 0 015.356-1.857M7 20v-2c0-.656.126-1.283.356-1.857m0 0a5.002 5.002 0 019.288 0M15 7a3 3 0 11-6 0 3 3 0 016 0zm6 3a2 2 0 11-4 0 2 2 0 014 0zM7 10a2 2 0 11-4 0 2 2 0 014 0z" />
            </svg>
          </div>
        </div>

        <div className="bg-card border border-border rounded-lg p-4">
          <div className="flex items-center justify-between">
            <div>
              <p className="text-xs text-muted-foreground font-mono">Approved Vendors</p>
              <p className="text-lg font-bold text-foreground">{metrics.approvedVendors}</p>
            </div>
            <svg className="h-4 w-4 text-green-400" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M5 13l4 4L19 7" />
            </svg>
          </div>
        </div>

        <div className="bg-card border border-border rounded-lg p-4">
          <div className="flex items-center justify-between">
            <div>
              <p className="text-xs text-muted-foreground font-mono">High Risk</p>
              <p className="text-lg font-bold text-foreground">{metrics.highRiskVendors + metrics.criticalVendors}</p>
            </div>
            <svg className="h-4 w-4 text-red-400" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 9v2m0 4h.01m-6.938 4h13.856c1.54 0 2.502-1.667 1.732-2.5L13.732 4c-.77-.833-1.964-.833-2.732 0L3.732 16.5c-.77.833.192 2.5 1.732 2.5z" />
            </svg>
          </div>
        </div>

        <div className="bg-card border border-border rounded-lg p-4">
          <div className="flex items-center justify-between">
            <div>
              <p className="text-xs text-muted-foreground font-mono">Avg Score</p>
              <p className="text-lg font-bold text-foreground">{metrics.averageScore}%</p>
            </div>
            <svg className="h-4 w-4 text-yellow-400" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 19v-6a2 2 0 00-2-2H5a2 2 0 00-2 2v6a2 2 0 002 2h2a2 2 0 002-2zm0 0V9a2 2 0 012-2h2a2 2 0 012 2v10m-6 0a2 2 0 002 2h2a2 2 0 002-2m0 0V5a2 2 0 012-2h2a2 2 0 012 2v14a2 2 0 01-2 2h-2a2 2 0 01-2-2z" />
            </svg>
          </div>
        </div>
      </div>

      {/* Contract Value & Pending Reviews */}
      <div className="grid gap-4 sm:grid-cols-2">
        <div className="bg-card border border-border rounded-lg p-4">
          <div className="flex items-center justify-between">
            <div>
              <p className="text-xs text-muted-foreground font-mono">Total Contract Value</p>
              <p className="text-lg font-bold text-foreground">{metrics.totalContractValue}</p>
            </div>
            <svg className="h-4 w-4 text-gold" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 8c-1.657 0-3 .895-3 2s1.343 2 3 2 3 .895 3 2-1.343 2-3 2m0-8c1.11 0 2.08.402 2.599 1M12 8V7m0 1v8m0 0v1m0-1c-1.11 0-2.08-.402-2.599-1" />
            </svg>
          </div>
        </div>

        <div className="bg-card border border-border rounded-lg p-4">
          <div className="flex items-center justify-between">
            <div>
              <p className="text-xs text-muted-foreground font-mono">Pending Reviews</p>
              <p className="text-lg font-bold text-foreground">{metrics.pendingReviews}</p>
            </div>
            <svg className="h-4 w-4 text-orange-400" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 8v4l3 3m6-3a9 9 0 11-18 0 9 9 0 0118 0z" />
            </svg>
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
            <option value="ai-platform">AI Platform</option>
            <option value="data-provider">Data Provider</option>
            <option value="ml-tools">ML Tools</option>
            <option value="consulting">Consulting</option>
            <option value="infrastructure">Infrastructure</option>
          </select>
          <select
            value={selectedRiskLevel}
            onChange={(e) => setSelectedRiskLevel(e.target.value)}
            className="px-3 py-1 text-sm bg-card border border-border rounded-md font-mono"
          >
            <option value="all">All Risk Levels</option>
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
            <option value="approved">Approved</option>
            <option value="under-review">Under Review</option>
            <option value="monitoring">Monitoring</option>
            <option value="rejected">Rejected</option>
          </select>
        </div>
        <button className="px-4 py-2 bg-gold text-gold-foreground rounded-md font-mono text-sm hover:bg-gold/90 transition-colors">
          Add New Vendor
        </button>
      </div>

      {/* Vendors Table */}
      <div className="bg-card border border-border rounded-lg overflow-hidden">
        <div className="p-4 border-b border-border">
          <h3 className="text-lg font-bold text-foreground">Vendor Risk Assessment</h3>
        </div>
        <div className="overflow-x-auto">
          <table className="w-full">
            <thead className="bg-muted/50">
              <tr>
                <th className="p-3 text-left text-xs font-mono text-muted-foreground">Vendor</th>
                <th className="p-3 text-left text-xs font-mono text-muted-foreground">Category</th>
                <th className="p-3 text-left text-xs font-mono text-muted-foreground">Risk Level</th>
                <th className="p-3 text-left text-xs font-mono text-muted-foreground">Overall Score</th>
                <th className="p-3 text-left text-xs font-mono text-muted-foreground">Status</th>
                <th className="p-3 text-left text-xs font-mono text-muted-foreground">Contract Value</th>
                <th className="p-3 text-left text-xs font-mono text-muted-foreground">Critical Issues</th>
                <th className="p-3 text-left text-xs font-mono text-muted-foreground">Next Review</th>
                <th className="p-3 text-left text-xs font-mono text-muted-foreground">Actions</th>
              </tr>
            </thead>
            <tbody>
              {filteredVendors.map((vendor) => (
                <tr key={vendor.id} className="border-b border-border hover:bg-muted/30">
                  <td className="p-3">
                    <div>
                      <p className="text-sm font-mono font-medium">{vendor.name}</p>
                      <p className="text-xs text-muted-foreground">ID: {vendor.id}</p>
                    </div>
                  </td>
                  <td className="p-3">
                    <span className="text-xs font-mono capitalize">{vendor.category.replace('-', ' ')}</span>
                  </td>
                  <td className="p-3">
                    <span className={`inline-flex px-2 py-1 rounded text-xs font-mono ${getRiskLevelColor(vendor.riskLevel)}`}>
                      {vendor.riskLevel}
                    </span>
                  </td>
                  <td className="p-3">
                    <span className={`text-sm font-mono font-bold ${getScoreColor(vendor.overallScore)}`}>
                      {vendor.overallScore}%
                    </span>
                  </td>
                  <td className="p-3">
                    <span className={`inline-flex px-2 py-1 rounded text-xs font-mono ${getStatusColor(vendor.status)}`}>
                      {vendor.status.replace('-', ' ')}
                    </span>
                  </td>
                  <td className="p-3">
                    <span className="text-sm font-mono">{vendor.contractValue}</span>
                  </td>
                  <td className="p-3">
                    <span className={`text-sm font-mono ${vendor.criticalIssues > 0 ? 'text-red-400' : 'text-green-400'}`}>
                      {vendor.criticalIssues}
                    </span>
                  </td>
                  <td className="p-3">
                    <span className="text-xs font-mono">{vendor.nextReview}</span>
                  </td>
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

