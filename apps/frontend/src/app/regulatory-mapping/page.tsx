'use client'

import React, { useState, useEffect } from 'react'

interface RegulatoryFramework {
  id: string
  name: string
  type: 'privacy' | 'security' | 'ai-ethics' | 'data-protection' | 'financial' | 'healthcare'
  jurisdiction: string
  status: 'active' | 'draft' | 'proposed' | 'superseded'
  effectiveDate: string
  lastUpdated: string
  description: string
  requirements: RegulatoryRequirement[]
  complianceScore: number
  implementationStatus: 'implemented' | 'partial' | 'not-implemented' | 'in-progress'
  riskLevel: 'low' | 'medium' | 'high' | 'critical'
}

interface RegulatoryRequirement {
  id: string
  name: string
  description: string
  category: 'data-privacy' | 'security' | 'transparency' | 'accountability' | 'bias' | 'safety'
  priority: 'critical' | 'high' | 'medium' | 'low'
  status: 'compliant' | 'non-compliant' | 'partial' | 'not-assessed'
  implementation: string
  evidence: string[]
  lastAssessment: string
  nextReview: string
  riskScore: number
}

interface ComplianceMapping {
  id: string
  frameworkId: string
  frameworkName: string
  requirementId: string
  requirementName: string
  mappedControls: string[]
  mappingStrength: 'strong' | 'moderate' | 'weak' | 'none'
  lastMapped: string
  mappedBy: string
  notes: string
}

interface RegulatoryMetrics {
  totalFrameworks: number
  activeFrameworks: number
  averageCompliance: number
  criticalRequirements: number
  complianceGaps: number
  lastAssessment: string
  nextReview: string
}

export default function RegulatoryMapping() {
  const [loading, setLoading] = useState(true)
  const [frameworks, setFrameworks] = useState<RegulatoryFramework[]>([])
  const [mappings, setMappings] = useState<ComplianceMapping[]>([])
  const [metrics, setMetrics] = useState<RegulatoryMetrics>({
    totalFrameworks: 0,
    activeFrameworks: 0,
    averageCompliance: 0,
    criticalRequirements: 0,
    complianceGaps: 0,
    lastAssessment: '',
    nextReview: ''
  })
  const [selectedType, setSelectedType] = useState<string>('all')
  const [selectedStatus, setSelectedStatus] = useState<string>('all')

  useEffect(() => {
    const timer = setTimeout(() => {
      const mockFrameworks: RegulatoryFramework[] = [
        {
          id: '1',
          name: 'GDPR (General Data Protection Regulation)',
          type: 'privacy',
          jurisdiction: 'European Union',
          status: 'active',
          effectiveDate: '2018-05-25',
          lastUpdated: '2024-01-15',
          description: 'Comprehensive data protection regulation for EU citizens',
          complianceScore: 87,
          implementationStatus: 'partial',
          riskLevel: 'high',
          requirements: [
            {
              id: 'req1',
              name: 'Data Processing Lawfulness',
              description: 'Ensure all data processing has a legal basis',
              category: 'data-privacy',
              priority: 'critical',
              status: 'compliant',
              implementation: 'Legal basis assessment framework implemented',
              evidence: ['Data processing register', 'Legal basis documentation', 'Consent management system'],
              lastAssessment: '2024-01-10',
              nextReview: '2024-04-10',
              riskScore: 15
            },
            {
              id: 'req2',
              name: 'Data Subject Rights',
              description: 'Implement mechanisms for data subject rights',
              category: 'data-privacy',
              priority: 'high',
              status: 'partial',
              implementation: 'Basic rights framework in place, automation pending',
              evidence: ['Rights request process', 'Data portability tool', 'Deletion mechanism'],
              lastAssessment: '2024-01-12',
              nextReview: '2024-03-12',
              riskScore: 35
            }
          ]
        },
        {
          id: '2',
          name: 'EU AI Act',
          type: 'ai-ethics',
          jurisdiction: 'European Union',
          status: 'active',
          effectiveDate: '2024-01-01',
          lastUpdated: '2024-01-20',
          description: 'Comprehensive AI regulation framework',
          complianceScore: 72,
          implementationStatus: 'in-progress',
          riskLevel: 'critical',
          requirements: [
            {
              id: 'req3',
              name: 'High-Risk AI System Requirements',
              description: 'Implement requirements for high-risk AI systems',
              category: 'safety',
              priority: 'critical',
              status: 'partial',
              implementation: 'Risk assessment framework developed',
              evidence: ['Risk classification system', 'Safety assessment process', 'Documentation framework'],
              lastAssessment: '2024-01-18',
              nextReview: '2024-02-18',
              riskScore: 65
            }
          ]
        },
        {
          id: '3',
          name: 'CCPA (California Consumer Privacy Act)',
          type: 'privacy',
          jurisdiction: 'California, USA',
          status: 'active',
          effectiveDate: '2020-01-01',
          lastUpdated: '2024-01-08',
          description: 'Consumer privacy protection for California residents',
          complianceScore: 91,
          implementationStatus: 'implemented',
          riskLevel: 'medium',
          requirements: [
            {
              id: 'req4',
              name: 'Consumer Rights Disclosure',
              description: 'Provide clear disclosure of consumer rights',
              category: 'transparency',
              priority: 'high',
              status: 'compliant',
              implementation: 'Comprehensive privacy notice and rights disclosure',
              evidence: ['Privacy policy', 'Rights disclosure', 'Contact mechanisms'],
              lastAssessment: '2024-01-05',
              nextReview: '2024-04-05',
              riskScore: 20
            }
          ]
        },
        {
          id: '4',
          name: 'NIST AI Risk Management Framework',
          type: 'ai-ethics',
          jurisdiction: 'United States',
          status: 'active',
          effectiveDate: '2023-01-26',
          lastUpdated: '2024-01-10',
          description: 'Voluntary framework for AI risk management',
          complianceScore: 78,
          implementationStatus: 'partial',
          riskLevel: 'medium',
          requirements: [
            {
              id: 'req5',
              name: 'AI Risk Assessment',
              description: 'Conduct comprehensive AI risk assessments',
              category: 'safety',
              priority: 'high',
              status: 'partial',
              implementation: 'Risk assessment methodology implemented',
              evidence: ['Risk assessment process', 'Documentation templates', 'Review procedures'],
              lastAssessment: '2024-01-15',
              nextReview: '2024-03-15',
              riskScore: 45
            }
          ]
        }
      ]

      const mockMappings: ComplianceMapping[] = [
        {
          id: 'map1',
          frameworkId: '1',
          frameworkName: 'GDPR',
          requirementId: 'req1',
          requirementName: 'Data Processing Lawfulness',
          mappedControls: ['Data Classification Policy', 'Consent Management System', 'Legal Basis Assessment'],
          mappingStrength: 'strong',
          lastMapped: '2024-01-10',
          mappedBy: 'Compliance Team',
          notes: 'Strong alignment with existing data governance controls'
        },
        {
          id: 'map2',
          frameworkId: '2',
          frameworkName: 'EU AI Act',
          requirementId: 'req3',
          requirementName: 'High-Risk AI System Requirements',
          mappedControls: ['AI Risk Assessment Framework', 'Model Documentation System'],
          mappingStrength: 'moderate',
          lastMapped: '2024-01-18',
          mappedBy: 'AI Governance Team',
          notes: 'Additional controls needed for full compliance'
        }
      ]

      setFrameworks(mockFrameworks)
      setMappings(mockMappings)
      
      const activeFrameworks = mockFrameworks.filter(f => f.status === 'active').length
      const avgCompliance = Math.round(mockFrameworks.reduce((sum, f) => sum + f.complianceScore, 0) / mockFrameworks.length)
      const criticalRequirements = mockFrameworks.reduce((sum, f) => 
        sum + f.requirements.filter(r => r.priority === 'critical').length, 0)
      const complianceGaps = mockFrameworks.reduce((sum, f) => 
        sum + f.requirements.filter(r => r.status === 'non-compliant').length, 0)

      setMetrics({
        totalFrameworks: mockFrameworks.length,
        activeFrameworks: activeFrameworks,
        averageCompliance: avgCompliance,
        criticalRequirements: criticalRequirements,
        complianceGaps: complianceGaps,
        lastAssessment: '2024-01-20 16:00:00',
        nextReview: '2024-02-20'
      })
      
      setLoading(false)
    }, 1000)

    return () => clearTimeout(timer)
  }, [])

  const filteredFrameworks = frameworks.filter(framework => {
    const typeMatch = selectedType === 'all' || framework.type === selectedType
    const statusMatch = selectedStatus === 'all' || framework.status === selectedStatus
    return typeMatch && statusMatch
  })

  const getStatusColor = (status: string) => {
    switch (status) {
      case 'active': return 'text-green-400 bg-green-500/20'
      case 'draft': return 'text-blue-400 bg-blue-500/20'
      case 'proposed': return 'text-yellow-400 bg-yellow-500/20'
      case 'superseded': return 'text-gray-400 bg-gray-500/20'
      default: return 'text-muted-foreground bg-muted'
    }
  }

  const getRiskColor = (risk: string) => {
    switch (risk) {
      case 'critical': return 'text-red-400'
      case 'high': return 'text-orange-400'
      case 'medium': return 'text-yellow-400'
      case 'low': return 'text-green-400'
      default: return 'text-muted-foreground'
    }
  }

  const getImplementationColor = (status: string) => {
    switch (status) {
      case 'implemented': return 'text-green-400'
      case 'partial': return 'text-yellow-400'
      case 'not-implemented': return 'text-red-400'
      case 'in-progress': return 'text-blue-400'
      default: return 'text-muted-foreground'
    }
  }

  const getRequirementStatusColor = (status: string) => {
    switch (status) {
      case 'compliant': return 'text-green-400 bg-green-500/20'
      case 'non-compliant': return 'text-red-400 bg-red-500/20'
      case 'partial': return 'text-yellow-400 bg-yellow-500/20'
      case 'not-assessed': return 'text-gray-400 bg-gray-500/20'
      default: return 'text-muted-foreground bg-muted'
    }
  }

  const getMappingStrengthColor = (strength: string) => {
    switch (strength) {
      case 'strong': return 'text-green-400'
      case 'moderate': return 'text-yellow-400'
      case 'weak': return 'text-orange-400'
      case 'none': return 'text-red-400'
      default: return 'text-muted-foreground'
    }
  }

  const getTypeIcon = (type: string) => {
    switch (type) {
      case 'privacy': return '🔒'
      case 'security': return '🛡️'
      case 'ai-ethics': return '🤖'
      case 'data-protection': return '📊'
      case 'financial': return '💰'
      case 'healthcare': return '🏥'
      default: return '📋'
    }
  }

  if (loading) {
    return (
      <div className="space-y-6 p-4 md:p-6 max-w-[2000px] mx-auto">
        <div className="space-y-2">
          <h1 className="text-2xl md:text-3xl font-bold tracking-tight text-gold">
            Regulatory Mapping
          </h1>
          <p className="text-xs md:text-sm text-muted-foreground font-mono">
            Compliance Mapping & Regulatory Tracking
          </p>
        </div>
        <div className="flex items-center justify-center h-64">
          <div className="text-center">
            <div className="w-8 h-8 border-2 border-gold border-t-transparent rounded-full animate-spin mx-auto mb-4"></div>
            <p className="text-sm text-muted-foreground font-mono">Loading Regulatory Mapping...</p>
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
          Regulatory Mapping
        </h1>
        <p className="text-xs md:text-sm text-muted-foreground font-mono">
          Compliance Mapping & Regulatory Tracking
        </p>
      </div>

      {/* Regulatory Overview */}
      <div className="bg-card border border-border rounded-lg p-6">
        <div className="flex items-center justify-between mb-6">
          <div>
            <h2 className="text-xl font-bold text-foreground">Regulatory Overview</h2>
            <p className="text-sm text-muted-foreground font-mono">
              Framework compliance and regulatory alignment
            </p>
          </div>
          <div className="text-right">
            <div className="text-3xl font-bold text-gold">{metrics.averageCompliance}%</div>
            <span className="text-sm text-muted-foreground font-mono">Average Compliance</span>
          </div>
        </div>
        
        <div className="grid gap-4 sm:grid-cols-2 lg:grid-cols-4">
          <div className="text-center">
            <div className="text-2xl font-bold text-foreground">{metrics.totalFrameworks}</div>
            <div className="text-xs text-muted-foreground font-mono">Total Frameworks</div>
          </div>
          <div className="text-center">
            <div className="text-2xl font-bold text-foreground">{metrics.activeFrameworks}</div>
            <div className="text-xs text-muted-foreground font-mono">Active Frameworks</div>
          </div>
          <div className="text-center">
            <div className="text-2xl font-bold text-foreground">{metrics.criticalRequirements}</div>
            <div className="text-xs text-muted-foreground font-mono">Critical Requirements</div>
          </div>
          <div className="text-center">
            <div className="text-2xl font-bold text-foreground">{metrics.complianceGaps}</div>
            <div className="text-xs text-muted-foreground font-mono">Compliance Gaps</div>
          </div>
        </div>
      </div>

      {/* Regulatory Status */}
      <div className="grid gap-4 sm:grid-cols-2">
        <div className="bg-card border border-border rounded-lg p-4">
          <h3 className="font-bold text-foreground mb-2">Last Assessment</h3>
          <div className="text-sm font-bold text-foreground">{metrics.lastAssessment}</div>
          <p className="text-xs text-muted-foreground font-mono">Comprehensive regulatory assessment</p>
        </div>
        <div className="bg-card border border-border rounded-lg p-4">
          <h3 className="font-bold text-foreground mb-2">Next Review</h3>
          <div className="text-sm font-bold text-foreground">{metrics.nextReview}</div>
          <p className="text-xs text-muted-foreground font-mono">Scheduled compliance review</p>
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
            <option value="privacy">Privacy</option>
            <option value="security">Security</option>
            <option value="ai-ethics">AI Ethics</option>
            <option value="data-protection">Data Protection</option>
            <option value="financial">Financial</option>
            <option value="healthcare">Healthcare</option>
          </select>
          <select
            value={selectedStatus}
            onChange={(e) => setSelectedStatus(e.target.value)}
            className="px-3 py-1 text-sm bg-card border border-border rounded-md font-mono"
          >
            <option value="all">All Status</option>
            <option value="active">Active</option>
            <option value="draft">Draft</option>
            <option value="proposed">Proposed</option>
            <option value="superseded">Superseded</option>
          </select>
        </div>
        <button className="px-4 py-2 bg-gold text-gold-foreground rounded-md font-mono text-sm hover:bg-gold/90 transition-colors">
          Add Framework
        </button>
      </div>

      {/* Regulatory Frameworks */}
      <div className="space-y-4">
        <h2 className="text-xl font-bold text-foreground">Regulatory Frameworks</h2>
        
        <div className="grid gap-4">
          {filteredFrameworks.map((framework) => (
            <div key={framework.id} className="bg-card border border-border rounded-lg p-6">
              <div className="flex items-start justify-between mb-4">
                <div className="flex-1">
                  <div className="flex items-center gap-3 mb-2">
                    <span className="text-2xl">{getTypeIcon(framework.type)}</span>
                    <h3 className="text-lg font-bold text-foreground">{framework.name}</h3>
                    <span className={`inline-flex px-2 py-1 rounded text-xs font-mono ${getStatusColor(framework.status)}`}>
                      {framework.status.toUpperCase()}
                    </span>
                    <span className={`text-sm font-mono ${getRiskColor(framework.riskLevel)}`}>
                      {framework.riskLevel.toUpperCase()} RISK
                    </span>
                    <span className={`text-sm font-mono ${getImplementationColor(framework.implementationStatus)}`}>
                      {framework.implementationStatus.replace('-', ' ').toUpperCase()}
                    </span>
                  </div>
                  <p className="text-sm text-muted-foreground font-mono mb-3">{framework.description}</p>
                  
                  <div className="grid gap-4 sm:grid-cols-2 lg:grid-cols-4 mb-4">
                    <div>
                      <span className="text-xs text-muted-foreground font-mono">Jurisdiction</span>
                      <div className="text-sm font-bold text-foreground">{framework.jurisdiction}</div>
                    </div>
                    <div>
                      <span className="text-xs text-muted-foreground font-mono">Compliance</span>
                      <div className="text-lg font-bold text-green-400">{framework.complianceScore}%</div>
                    </div>
                    <div>
                      <span className="text-xs text-muted-foreground font-mono">Requirements</span>
                      <div className="text-sm font-bold text-foreground">{framework.requirements.length}</div>
                    </div>
                    <div>
                      <span className="text-xs text-muted-foreground font-mono">Effective Date</span>
                      <div className="text-sm font-bold text-foreground">{framework.effectiveDate}</div>
                    </div>
                  </div>
                </div>
              </div>

              {/* Requirements */}
              <div className="space-y-3 mb-4">
                <h4 className="text-sm font-bold text-foreground">Regulatory Requirements</h4>
                {framework.requirements.map((requirement) => (
                  <div key={requirement.id} className="border border-border rounded-lg p-4">
                    <div className="flex items-start justify-between mb-3">
                      <div className="flex-1">
                        <div className="flex items-center gap-2 mb-1">
                          <h5 className="text-sm font-bold text-foreground">{requirement.name}</h5>
                          <span className={`inline-flex px-1 py-0.5 rounded text-xs font-mono ${getRequirementStatusColor(requirement.status)}`}>
                            {requirement.status.toUpperCase()}
                          </span>
                          <span className="text-xs font-mono text-muted-foreground">{requirement.category}</span>
                        </div>
                        <p className="text-xs text-muted-foreground font-mono mb-2">{requirement.description}</p>
                        <p className="text-xs text-muted-foreground font-mono mb-2">
                          <strong>Implementation:</strong> {requirement.implementation}
                        </p>
                      </div>
                      <div className="text-right">
                        <div className="text-sm font-bold text-orange-400">{requirement.riskScore}</div>
                        <div className="text-xs text-muted-foreground font-mono">Risk Score</div>
                      </div>
                    </div>
                    
                    <div className="grid gap-2 sm:grid-cols-2">
                      <div>
                        <span className="text-xs text-muted-foreground font-mono">Evidence:</span>
                        <ul className="text-xs text-muted-foreground font-mono mt-1">
                          {requirement.evidence.map((ev, index) => (
                            <li key={index} className="flex items-start gap-1">
                              <span className="text-green-400 mt-0.5">✓</span>
                              {ev}
                            </li>
                          ))}
                        </ul>
                      </div>
                      <div className="text-right">
                        <div className="text-xs text-muted-foreground font-mono">
                          Next Review: {requirement.nextReview}
                        </div>
                      </div>
                    </div>
                  </div>
                ))}
              </div>
              
              <div className="flex items-center justify-between pt-4 border-t border-border">
                <div className="flex gap-4 text-xs text-muted-foreground font-mono">
                  <span>Type: {framework.type}</span>
                  <span>Risk Level: {framework.riskLevel}</span>
                  <span>Last Updated: {framework.lastUpdated}</span>
                </div>
                <div className="flex gap-2">
                  <button className="px-3 py-1 text-xs bg-card border border-border rounded font-mono hover:bg-accent transition-colors">
                    Map Requirements
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

      {/* Compliance Mappings */}
      <div className="space-y-4">
        <h2 className="text-xl font-bold text-foreground">Compliance Mappings</h2>
        
        <div className="grid gap-4">
          {mappings.map((mapping) => (
            <div key={mapping.id} className="bg-card border border-border rounded-lg p-6">
              <div className="flex items-start justify-between mb-4">
                <div className="flex-1">
                  <div className="flex items-center gap-3 mb-2">
                    <h3 className="text-lg font-bold text-foreground">
                      {mapping.frameworkName} → {mapping.requirementName}
                    </h3>
                    <span className={`text-sm font-mono ${getMappingStrengthColor(mapping.mappingStrength)}`}>
                      {mapping.mappingStrength.toUpperCase()} MAPPING
                    </span>
                  </div>
                  
                  <div className="grid gap-4 sm:grid-cols-2 mb-4">
                    <div>
                      <span className="text-xs text-muted-foreground font-mono">Mapped Controls</span>
                      <ul className="text-xs text-muted-foreground font-mono mt-1">
                        {mapping.mappedControls.map((control, index) => (
                          <li key={index} className="flex items-start gap-1">
                            <span className="text-blue-400 mt-0.5">🔗</span>
                            {control}
                          </li>
                        ))}
                      </ul>
                    </div>
                    <div>
                      <span className="text-xs text-muted-foreground font-mono">Notes</span>
                      <p className="text-xs text-muted-foreground font-mono mt-1">{mapping.notes}</p>
                    </div>
                  </div>
                </div>
              </div>
              
              <div className="flex items-center justify-between pt-4 border-t border-border">
                <div className="flex gap-4 text-xs text-muted-foreground font-mono">
                  <span>Mapped by: {mapping.mappedBy}</span>
                  <span>Last mapped: {mapping.lastMapped}</span>
                </div>
                <div className="flex gap-2">
                  <button className="px-3 py-1 text-xs bg-card border border-border rounded font-mono hover:bg-accent transition-colors">
                    Update Mapping
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
