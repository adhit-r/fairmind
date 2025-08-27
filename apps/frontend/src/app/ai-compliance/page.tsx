'use client'

import React, { useState, useEffect } from 'react'

interface ComplianceProject {
  id: string
  name: string
  description: string
  status: 'active' | 'draft' | 'completed' | 'archived'
  frameworks: string[]
  complianceScore: number
  lastUpdated: string
  owner: string
  nextReview: string
}

interface RegulatoryFramework {
  id: string
  name: string
  region: string
  type: 'ai' | 'privacy' | 'sectoral'
  status: 'active' | 'draft' | 'proposed'
  effectiveDate: string
  complianceLevel: 'high' | 'medium' | 'low'
  description: string
  keyRequirements: string[]
}

interface ComplianceMetrics {
  totalProjects: number
  activeProjects: number
  averageComplianceScore: number
  frameworksCovered: number
  upcomingReviews: number
  criticalGaps: number
}

export default function AICompliancePage() {
  const [complianceProjects, setComplianceProjects] = useState<ComplianceProject[]>([])
  const [regulatoryFrameworks, setRegulatoryFrameworks] = useState<RegulatoryFramework[]>([])
  const [metrics, setMetrics] = useState<ComplianceMetrics | null>(null)
  const [loading, setLoading] = useState(true)
  const [activeTab, setActiveTab] = useState<'overview' | 'projects' | 'frameworks' | 'mapping' | 'reports'>('overview')

  useEffect(() => {
    const loadData = async () => {
      setLoading(true)

      // Mock compliance projects
      const mockProjects: ComplianceProject[] = [
        {
          id: '1',
          name: 'EU AI Act Compliance',
          description: 'Comprehensive compliance project for EU AI Act requirements',
          status: 'active',
          frameworks: ['EU AI Act', 'GDPR'],
          complianceScore: 85,
          lastUpdated: '2024-01-15T10:30:00Z',
          owner: 'Sarah Johnson',
          nextReview: '2024-02-15T00:00:00Z'
        },
        {
          id: '2',
          name: 'US AI Executive Order Compliance',
          description: 'Compliance with US Executive Order 14110 on AI',
          status: 'active',
          frameworks: ['US EO 14110', 'NIST AI RMF'],
          complianceScore: 72,
          lastUpdated: '2024-01-14T15:45:00Z',
          owner: 'Michael Chen',
          nextReview: '2024-02-01T00:00:00Z'
        }
      ]

      // Mock regulatory frameworks
      const mockFrameworks: RegulatoryFramework[] = [
        {
          id: '1',
          name: 'EU AI Act',
          region: 'European Union',
          type: 'ai',
          status: 'active',
          effectiveDate: '2024-03-13',
          complianceLevel: 'high',
          description: 'Comprehensive AI regulation framework for the European Union',
          keyRequirements: ['Risk-based classification', 'Transparency requirements', 'Human oversight', 'Data governance']
        },
        {
          id: '2',
          name: 'US Executive Order 14110',
          region: 'United States',
          type: 'ai',
          status: 'active',
          effectiveDate: '2023-10-30',
          complianceLevel: 'high',
          description: 'Executive order for safe, secure, and trustworthy AI development',
          keyRequirements: ['AI safety standards', 'Privacy protection', 'Civil rights protection', 'Worker protection']
        }
      ]

      // Mock metrics
      const mockMetrics: ComplianceMetrics = {
        totalProjects: 5,
        activeProjects: 3,
        averageComplianceScore: 61.6,
        frameworksCovered: 8,
        upcomingReviews: 4,
        criticalGaps: 12
      }

      setComplianceProjects(mockProjects)
      setRegulatoryFrameworks(mockFrameworks)
      setMetrics(mockMetrics)
      setLoading(false)
    }

    loadData()
  }, [])

  const getStatusColor = (status: string) => {
    switch (status) {
      case 'active': return 'text-green-500 bg-green-500/10'
      case 'draft': return 'text-yellow-500 bg-yellow-500/10'
      case 'completed': return 'text-blue-500 bg-blue-500/10'
      case 'archived': return 'text-gray-500 bg-gray-500/10'
      default: return 'text-gray-500 bg-gray-500/10'
    }
  }

  if (loading) {
    return (
      <div className="space-y-6 p-4 md:p-6 max-w-[2000px] mx-auto">
        <div className="space-y-2">
          <h1 className="text-2xl md:text-3xl font-bold tracking-tight text-gold">
            AI_COMPLIANCE_DASHBOARD
          </h1>
          <p className="text-xs md:text-sm text-muted-foreground font-mono">
            COMPREHENSIVE.AI.REGULATORY.COMPLIANCE.MANAGEMENT
          </p>
        </div>
        <div className="flex items-center justify-center h-64">
          <div className="text-center">
            <div className="w-8 h-8 border-2 border-gold border-t-transparent rounded-full animate-spin mx-auto mb-4"></div>
            <p className="text-sm text-muted-foreground font-mono">LOADING_COMPLIANCE_DATA...</p>
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
          AI_COMPLIANCE_DASHBOARD
        </h1>
        <p className="text-xs md:text-sm text-muted-foreground font-mono">
          COMPREHENSIVE.AI.REGULATORY.COMPLIANCE.MANAGEMENT
        </p>
      </div>

      {/* Overview Metrics */}
      {metrics && (
        <div className="grid gap-4 sm:grid-cols-2 lg:grid-cols-4">
          <div className="bg-card border border-border rounded-lg p-4">
            <div className="flex items-center justify-between">
              <div>
                <p className="text-xs text-muted-foreground font-mono">TOTAL_PROJECTS</p>
                <p className="text-lg font-bold text-foreground">{metrics.totalProjects}</p>
              </div>
              <div className="flex items-center gap-2">
                <svg className="h-4 w-4 text-gold" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M19 11H5m14 0a2 2 0 012 2v6a2 2 0 01-2 2H5a2 2 0 01-2-2v-6a2 2 0 012-2m14 0V9a2 2 0 00-2-2M5 11V9a2 2 0 012-2m0 0V5a2 2 0 012-2h6a2 2 0 012 2v2M7 7h10" />
                </svg>
              </div>
            </div>
          </div>

          <div className="bg-card border border-border rounded-lg p-4">
            <div className="flex items-center justify-between">
              <div>
                <p className="text-xs text-muted-foreground font-mono">AVG_COMPLIANCE_SCORE</p>
                <p className="text-lg font-bold text-foreground">{metrics.averageComplianceScore}%</p>
              </div>
              <div className="flex items-center gap-2">
                <svg className="h-4 w-4 text-green-500" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 12l2 2 4-4m5.618-4.016A11.955 11.955 0 0112 2.944a11.955 11.955 0 01-8.618 3.04A12.02 12.02 0 003 9c0 5.591 3.824 10.29 9 11.622 5.176-1.332 9-6.03 9-11.622 0-1.042-.133-2.052-.382-3.016z" />
                </svg>
              </div>
            </div>
          </div>

          <div className="bg-card border border-border rounded-lg p-4">
            <div className="flex items-center justify-between">
              <div>
                <p className="text-xs text-muted-foreground font-mono">FRAMEWORKS_COVERED</p>
                <p className="text-lg font-bold text-foreground">{metrics.frameworksCovered}</p>
              </div>
              <div className="flex items-center gap-2">
                <svg className="h-4 w-4 text-blue-500" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 20l-5.447-2.724A1 1 0 013 16.382V5.618a1 1 0 011.447-.894L9 7m0 13l6-3m-6 3V7m6 10l4.553 2.276A1 1 0 0021 18.382V7.618a1 1 0 00-1.447-.894L15 4m0 13V4m-6 3l6-3" />
                </svg>
              </div>
            </div>
          </div>

          <div className="bg-card border border-border rounded-lg p-4">
            <div className="flex items-center justify-between">
              <div>
                <p className="text-xs text-muted-foreground font-mono">CRITICAL_GAPS</p>
                <p className="text-lg font-bold text-red-500">{metrics.criticalGaps}</p>
              </div>
              <div className="flex items-center gap-2">
                <svg className="h-4 w-4 text-red-500" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 9v2m0 4h.01m-6.938 4h13.856c1.54 0 2.502-1.667 1.732-2.5L13.732 4c-.77-.833-1.964-.833-2.732 0L3.732 16.5c-.77.833.192 2.5 1.732 2.5z" />
                </svg>
              </div>
            </div>
          </div>
        </div>
      )}

      {/* Tab Navigation */}
      <div className="flex space-x-1 bg-accent p-1 rounded-lg">
        {[
          { id: 'overview', label: 'OVERVIEW', icon: '📊' },
          { id: 'projects', label: 'COMPLIANCE_PROJECTS', icon: '📋' },
          { id: 'frameworks', label: 'REGULATORY_FRAMEWORKS', icon: '🏛️' },
          { id: 'mapping', label: 'COMPLIANCE_MAPPING', icon: '🗺️' },
          { id: 'reports', label: 'REPORTS', icon: '📈' }
        ].map((tab) => (
          <button
            key={tab.id}
            onClick={() => setActiveTab(tab.id as any)}
            className={`flex-1 px-3 py-2 rounded-md text-xs font-mono transition-colors ${
              activeTab === tab.id
                ? 'bg-background text-foreground shadow-sm'
                : 'text-muted-foreground hover:text-foreground'
            }`}
          >
            <span className="mr-1">{tab.icon}</span>
            {tab.label}
          </button>
        ))}
      </div>

      {/* Content based on active tab */}
      {activeTab === 'overview' && (
        <div className="space-y-6">
          {/* Compliance Projects Summary */}
          <div className="space-y-4">
            <h2 className="text-xl font-bold tracking-tight text-foreground">
              COMPLIANCE_PROJECTS_SUMMARY
            </h2>
            <div className="grid gap-4 md:grid-cols-2 lg:grid-cols-3">
              {complianceProjects.map((project) => (
                <div key={project.id} className="bg-card border border-border rounded-lg p-4">
                  <div className="flex items-start justify-between mb-3">
                    <h3 className="font-semibold text-foreground">{project.name}</h3>
                    <span className={`px-2 py-1 rounded-full text-xs font-mono ${getStatusColor(project.status)}`}>
                      {project.status.toUpperCase()}
                    </span>
                  </div>
                  <p className="text-sm text-muted-foreground mb-3">{project.description}</p>
                  <div className="space-y-2">
                    <div className="flex items-center justify-between">
                      <span className="text-xs text-muted-foreground font-mono">COMPLIANCE_SCORE</span>
                      <span className="text-sm font-mono font-semibold">{project.complianceScore}%</span>
                    </div>
                    <div className="w-full bg-accent rounded-full h-2">
                      <div 
                        className="bg-gold h-2 rounded-full transition-all duration-300"
                        style={{ width: `${project.complianceScore}%` }}
                      ></div>
                    </div>
                    <div className="flex items-center justify-between text-xs text-muted-foreground">
                      <span>Owner: {project.owner}</span>
                      <span>Next Review: {new Date(project.nextReview).toLocaleDateString()}</span>
                    </div>
                  </div>
                </div>
              ))}
            </div>
          </div>
        </div>
      )}

      {activeTab === 'projects' && (
        <div className="space-y-4">
          <h2 className="text-xl font-bold tracking-tight text-foreground">
            COMPLIANCE_PROJECTS
          </h2>
          <div className="bg-card border border-border rounded-lg overflow-hidden">
            <div className="overflow-x-auto">
              <table className="w-full">
                <thead className="bg-accent/50">
                  <tr>
                    <th className="px-4 py-3 text-left text-xs font-mono text-muted-foreground">PROJECT_NAME</th>
                    <th className="px-4 py-3 text-left text-xs font-mono text-muted-foreground">STATUS</th>
                    <th className="px-4 py-3 text-left text-xs font-mono text-muted-foreground">FRAMEWORKS</th>
                    <th className="px-4 py-3 text-left text-xs font-mono text-muted-foreground">COMPLIANCE_SCORE</th>
                    <th className="px-4 py-3 text-left text-xs font-mono text-muted-foreground">OWNER</th>
                    <th className="px-4 py-3 text-left text-xs font-mono text-muted-foreground">NEXT_REVIEW</th>
                  </tr>
                </thead>
                <tbody className="divide-y divide-border">
                  {complianceProjects.map((project) => (
                    <tr key={project.id} className="hover:bg-accent/20">
                      <td className="px-4 py-3">
                        <div>
                          <p className="text-sm font-mono font-semibold">{project.name}</p>
                          <p className="text-xs text-muted-foreground">{project.description}</p>
                        </div>
                      </td>
                      <td className="px-4 py-3">
                        <span className={`px-2 py-1 rounded-full text-xs font-mono ${getStatusColor(project.status)}`}>
                          {project.status.toUpperCase()}
                        </span>
                      </td>
                      <td className="px-4 py-3">
                        <div className="space-y-1">
                          {project.frameworks.map((framework, index) => (
                            <span key={index} className="inline-block bg-accent px-2 py-1 rounded text-xs font-mono mr-1 mb-1">
                              {framework}
                            </span>
                          ))}
                        </div>
                      </td>
                      <td className="px-4 py-3">
                        <div className="flex items-center gap-2">
                          <span className="text-sm font-mono font-semibold">{project.complianceScore}%</span>
                          <div className="w-16 bg-accent rounded-full h-2">
                            <div 
                              className="bg-gold h-2 rounded-full"
                              style={{ width: `${project.complianceScore}%` }}
                            ></div>
                          </div>
                        </div>
                      </td>
                      <td className="px-4 py-3 text-sm font-mono">{project.owner}</td>
                      <td className="px-4 py-3 text-sm font-mono">{new Date(project.nextReview).toLocaleDateString()}</td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          </div>
        </div>
      )}

      {activeTab === 'frameworks' && (
        <div className="space-y-4">
          <h2 className="text-xl font-bold tracking-tight text-foreground">
            REGULATORY_FRAMEWORKS
          </h2>
          <div className="grid gap-4 md:grid-cols-2 lg:grid-cols-3">
            {regulatoryFrameworks.map((framework) => (
              <div key={framework.id} className="bg-card border border-border rounded-lg p-4">
                <div className="flex items-start justify-between mb-3">
                  <h3 className="font-semibold text-foreground">{framework.name}</h3>
                  <span className="px-2 py-1 rounded-full text-xs font-mono bg-blue-500/10 text-blue-500">
                    {framework.complianceLevel.toUpperCase()}
                  </span>
                </div>
                <p className="text-sm text-muted-foreground mb-3">{framework.description}</p>
                <div className="space-y-2">
                  <div className="flex items-center justify-between">
                    <span className="text-xs text-muted-foreground font-mono">REGION</span>
                    <span className="text-sm font-mono">{framework.region}</span>
                  </div>
                  <div className="flex items-center justify-between">
                    <span className="text-xs text-muted-foreground font-mono">TYPE</span>
                    <span className="px-2 py-1 rounded-full text-xs font-mono bg-purple-500/10 text-purple-500">
                      {framework.type.toUpperCase()}
                    </span>
                  </div>
                  <div className="flex items-center justify-between">
                    <span className="text-xs text-muted-foreground font-mono">STATUS</span>
                    <span className={`px-2 py-1 rounded-full text-xs font-mono ${getStatusColor(framework.status)}`}>
                      {framework.status.toUpperCase()}
                    </span>
                  </div>
                  <div className="flex items-center justify-between">
                    <span className="text-xs text-muted-foreground font-mono">EFFECTIVE_DATE</span>
                    <span className="text-sm font-mono">{framework.effectiveDate}</span>
                  </div>
                </div>
              </div>
            ))}
          </div>
        </div>
      )}

      {activeTab === 'mapping' && (
        <div className="space-y-4">
          <h2 className="text-xl font-bold tracking-tight text-foreground">
            COMPLIANCE_MAPPING
          </h2>
          <p className="text-sm text-muted-foreground">
            Visual mapping of compliance status across different regulatory frameworks and geographic regions.
          </p>
          
          {/* World Map Placeholder */}
          <div className="bg-card border border-border rounded-lg p-8">
            <div className="text-center">
              <div className="w-16 h-16 bg-accent rounded-full flex items-center justify-center mx-auto mb-4">
                <svg className="w-8 h-8 text-muted-foreground" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 20l-5.447-2.724A1 1 0 013 16.382V5.618a1 1 0 011.447-.894L9 7m0 13l6-3m-6 3V7m6 10l4.553 2.276A1 1 0 0021 18.382V7.618a1 1 0 00-1.447-.894L15 4m0 13V4m-6 3l6-3" />
                </svg>
              </div>
              <h3 className="text-lg font-semibold text-foreground mb-2">INTERACTIVE_COMPLIANCE_MAP</h3>
              <p className="text-sm text-muted-foreground">
                Visual representation of global AI regulations and compliance status
              </p>
            </div>
          </div>
        </div>
      )}

      {activeTab === 'reports' && (
        <div className="space-y-4">
          <h2 className="text-xl font-bold tracking-tight text-foreground">
            COMPLIANCE_REPORTS
          </h2>
          <p className="text-sm text-muted-foreground">
            Generate comprehensive compliance reports and executive summaries.
          </p>
          
          <div className="grid gap-4 md:grid-cols-2 lg:grid-cols-3">
            <div className="bg-card border border-border rounded-lg p-4">
              <div className="flex items-center gap-3 mb-3">
                <svg className="w-6 h-6 text-red-500" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 12h6m-6 4h6m2 5H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z" />
                </svg>
                <h3 className="font-semibold text-foreground">EXECUTIVE_SUMMARY</h3>
              </div>
              <p className="text-sm text-muted-foreground mb-3">
                High-level compliance overview for executive stakeholders
              </p>
              <button className="w-full px-3 py-2 bg-gold text-gold-foreground rounded-md text-sm font-mono hover:bg-gold/90 transition-colors">
                GENERATE_PDF
              </button>
            </div>

            <div className="bg-card border border-border rounded-lg p-4">
              <div className="flex items-center gap-3 mb-3">
                <svg className="w-6 h-6 text-blue-500" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 19v-6a2 2 0 00-2-2H5a2 2 0 00-2 2v6a2 2 0 002 2h2a2 2 0 002-2zm0 0V9a2 2 0 012-2h2a2 2 0 012 2v10m-6 0a2 2 0 002 2h2a2 2 0 002-2m0 0V5a2 2 0 012-2h2a2 2 0 012 2v14a2 2 0 01-2 2h-2a2 2 0 01-2-2z" />
                </svg>
                <h3 className="font-semibold text-foreground">DETAILED_REPORT</h3>
              </div>
              <p className="text-sm text-muted-foreground mb-3">
                Comprehensive compliance analysis with detailed findings
              </p>
              <button className="w-full px-3 py-2 bg-gold text-gold-foreground rounded-md text-sm font-mono hover:bg-gold/90 transition-colors">
                GENERATE_PDF
              </button>
            </div>

            <div className="bg-card border border-border rounded-lg p-4">
              <div className="flex items-center gap-3 mb-3">
                <svg className="w-6 h-6 text-green-500" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M13 10V3L4 14h7v7l9-11h-7z" />
                </svg>
                <h3 className="font-semibold text-foreground">PRESENTATION</h3>
              </div>
              <p className="text-sm text-muted-foreground mb-3">
                PowerPoint presentation for stakeholder meetings
              </p>
              <button className="w-full px-3 py-2 bg-gold text-gold-foreground rounded-md text-sm font-mono hover:bg-gold/90 transition-colors">
                GENERATE_PPTX
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  )
}
