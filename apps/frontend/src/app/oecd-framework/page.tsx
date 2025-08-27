'use client'

import React, { useState, useEffect } from 'react'

interface OECDPrinciple {
  id: string
  name: string
  description: string
  category: 'inclusive-growth' | 'human-centered' | 'transparency' | 'robustness' | 'accountability'
  status: 'implemented' | 'in-progress' | 'planned' | 'not-started'
  complianceScore: number
  implementationLevel: 'basic' | 'intermediate' | 'advanced' | 'exemplary'
  lastAssessment: string
  nextReview: string
  requirements: string[]
  evidence: string[]
}

interface OECDMetrics {
  totalPrinciples: number
  implementedPrinciples: number
  averageCompliance: number
  highComplianceAreas: number
  lowComplianceAreas: number
  nextMilestone: string
  globalAlignment: number
}

export default function OECDFramework() {
  const [loading, setLoading] = useState(true)
  const [principles, setPrinciples] = useState<OECDPrinciple[]>([])
  const [metrics, setMetrics] = useState<OECDMetrics>({
    totalPrinciples: 0,
    implementedPrinciples: 0,
    averageCompliance: 0,
    highComplianceAreas: 0,
    lowComplianceAreas: 0,
    nextMilestone: '',
    globalAlignment: 0
  })
  const [selectedCategory, setSelectedCategory] = useState<string>('all')
  const [selectedStatus, setSelectedStatus] = useState<string>('all')

  useEffect(() => {
    const timer = setTimeout(() => {
      const mockPrinciples: OECDPrinciple[] = [
        {
          id: '1',
          name: 'Inclusive Growth, Sustainable Development and Well-being',
          description: 'AI should benefit people and the planet by driving inclusive growth, sustainable development and well-being',
          category: 'inclusive-growth',
          status: 'implemented',
          complianceScore: 85,
          implementationLevel: 'advanced',
          lastAssessment: '2024-01-10',
          nextReview: '2024-04-10',
          requirements: [
            'AI systems promote economic growth and social progress',
            'Environmental impact assessment conducted',
            'Benefits distributed equitably across society'
          ],
          evidence: [
            'ESG impact reports available',
            'Economic benefit analysis completed',
            'Stakeholder engagement documented'
          ]
        },
        {
          id: '2',
          name: 'Human-Centered Values and Fairness',
          description: 'AI systems should be designed in a way that respects the rule of law, human rights, democratic values and diversity',
          category: 'human-centered',
          status: 'implemented',
          complianceScore: 90,
          implementationLevel: 'exemplary',
          lastAssessment: '2024-01-08',
          nextReview: '2024-04-08',
          requirements: [
            'Human rights impact assessment completed',
            'Fairness metrics implemented and monitored',
            'Diversity and inclusion considerations integrated'
          ],
          evidence: [
            'Bias detection framework operational',
            'Human rights compliance audit passed',
            'Fairness monitoring dashboard active'
          ]
        },
        {
          id: '3',
          name: 'Transparency and Explainability',
          description: 'There should be transparency and responsible disclosure around AI systems to ensure that people understand AI-based outcomes',
          category: 'transparency',
          status: 'in-progress',
          complianceScore: 70,
          implementationLevel: 'intermediate',
          lastAssessment: '2024-01-12',
          nextReview: '2024-02-12',
          requirements: [
            'Model explainability tools implemented',
            'Decision rationale documentation available',
            'Transparency reports published regularly'
          ],
          evidence: [
            'Explainability framework deployed',
            'Documentation standards established',
            'Transparency dashboard in development'
          ]
        },
        {
          id: '4',
          name: 'Robustness, Security and Safety',
          description: 'AI systems should function in a robust, secure and safe way throughout their life cycles and potential risks should be continually assessed and managed',
          category: 'robustness',
          status: 'implemented',
          complianceScore: 88,
          implementationLevel: 'advanced',
          lastAssessment: '2024-01-05',
          nextReview: '2024-04-05',
          requirements: [
            'Security testing protocols established',
            'Safety monitoring systems operational',
            'Risk assessment framework implemented'
          ],
          evidence: [
            'Security audit completed',
            'Safety monitoring dashboard active',
            'Incident response plan tested'
          ]
        },
        {
          id: '5',
          name: 'Accountability',
          description: 'Organizations and individuals developing, deploying or operating AI systems should be accountable for their proper functioning',
          category: 'accountability',
          status: 'in-progress',
          complianceScore: 75,
          implementationLevel: 'intermediate',
          lastAssessment: '2024-01-15',
          nextReview: '2024-02-15',
          requirements: [
            'Clear accountability framework established',
            'Responsibility matrix defined',
            'Oversight mechanisms implemented'
          ],
          evidence: [
            'Accountability framework documented',
            'Role responsibilities defined',
            'Oversight committee established'
          ]
        }
      ]

      setPrinciples(mockPrinciples)
      
      const implemented = mockPrinciples.filter(p => p.status === 'implemented').length
      const avgCompliance = Math.round(mockPrinciples.reduce((sum, p) => sum + p.complianceScore, 0) / mockPrinciples.length)
      const highCompliance = mockPrinciples.filter(p => p.complianceScore >= 80).length
      const lowCompliance = mockPrinciples.filter(p => p.complianceScore < 70).length

      setMetrics({
        totalPrinciples: mockPrinciples.length,
        implementedPrinciples: implemented,
        averageCompliance: avgCompliance,
        highComplianceAreas: highCompliance,
        lowComplianceAreas: lowCompliance,
        nextMilestone: 'Achieve 90% average compliance across all principles',
        globalAlignment: Math.round((implemented / mockPrinciples.length) * 100)
      })
      
      setLoading(false)
    }, 1000)

    return () => clearTimeout(timer)
  }, [])

  const filteredPrinciples = principles.filter(principle => {
    const categoryMatch = selectedCategory === 'all' || principle.category === selectedCategory
    const statusMatch = selectedStatus === 'all' || principle.status === selectedStatus
    return categoryMatch && statusMatch
  })

  const getStatusColor = (status: string) => {
    switch (status) {
      case 'implemented': return 'text-green-400 bg-green-500/20'
      case 'in-progress': return 'text-yellow-400 bg-yellow-500/20'
      case 'planned': return 'text-blue-400 bg-blue-500/20'
      case 'not-started': return 'text-gray-400 bg-gray-500/20'
      default: return 'text-muted-foreground bg-muted'
    }
  }

  const getLevelColor = (level: string) => {
    switch (level) {
      case 'exemplary': return 'text-green-400'
      case 'advanced': return 'text-blue-400'
      case 'intermediate': return 'text-yellow-400'
      case 'basic': return 'text-orange-400'
      default: return 'text-muted-foreground'
    }
  }

  const getComplianceColor = (score: number) => {
    if (score >= 85) return 'text-green-400'
    if (score >= 70) return 'text-yellow-400'
    if (score >= 55) return 'text-orange-400'
    return 'text-red-400'
  }

  const getCategoryIcon = (category: string) => {
    switch (category) {
      case 'inclusive-growth': return '🌱'
      case 'human-centered': return '👥'
      case 'transparency': return '🔍'
      case 'robustness': return '🛡️'
      case 'accountability': return '⚖️'
      default: return '📋'
    }
  }

  if (loading) {
    return (
      <div className="space-y-6 p-4 md:p-6 max-w-[2000px] mx-auto">
        <div className="space-y-2">
          <h1 className="text-2xl md:text-3xl font-bold tracking-tight text-gold">
            OECD Framework
          </h1>
          <p className="text-xs md:text-sm text-muted-foreground font-mono">
            International AI Governance & Interoperability Framework
          </p>
        </div>
        <div className="flex items-center justify-center h-64">
          <div className="text-center">
            <div className="w-8 h-8 border-2 border-gold border-t-transparent rounded-full animate-spin mx-auto mb-4"></div>
            <p className="text-sm text-muted-foreground font-mono">Loading OECD Framework...</p>
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
          OECD Framework
        </h1>
        <p className="text-xs md:text-sm text-muted-foreground font-mono">
          International AI Governance & Interoperability Framework
        </p>
      </div>

      {/* Framework Overview */}
      <div className="bg-card border border-border rounded-lg p-6">
        <div className="flex items-center justify-between mb-6">
          <div>
            <h2 className="text-xl font-bold text-foreground">OECD AI Principles Compliance</h2>
            <p className="text-sm text-muted-foreground font-mono">
              Alignment with international AI governance standards
            </p>
          </div>
          <div className="text-right">
            <div className="text-3xl font-bold text-gold">{metrics.averageCompliance}%</div>
            <span className="text-sm text-muted-foreground font-mono">Average Compliance</span>
          </div>
        </div>
        
        <div className="w-full bg-muted rounded-full h-3 mb-4">
          <div 
            className="h-3 rounded-full transition-all duration-500 bg-gold"
            style={{ width: `${metrics.averageCompliance}%` }}
          ></div>
        </div>
        
        <div className="grid gap-4 sm:grid-cols-2 lg:grid-cols-4">
          <div className="text-center">
            <div className="text-2xl font-bold text-foreground">{metrics.totalPrinciples}</div>
            <div className="text-xs text-muted-foreground font-mono">Total Principles</div>
          </div>
          <div className="text-center">
            <div className="text-2xl font-bold text-foreground">{metrics.implementedPrinciples}</div>
            <div className="text-xs text-muted-foreground font-mono">Implemented</div>
          </div>
          <div className="text-center">
            <div className="text-2xl font-bold text-foreground">{metrics.highComplianceAreas}</div>
            <div className="text-xs text-muted-foreground font-mono">High Compliance</div>
          </div>
          <div className="text-center">
            <div className="text-2xl font-bold text-foreground">{metrics.globalAlignment}%</div>
            <div className="text-xs text-muted-foreground font-mono">Global Alignment</div>
          </div>
        </div>
      </div>

      {/* Next Milestone */}
      <div className="bg-card border border-border rounded-lg p-4">
        <div className="flex items-center justify-between">
          <div>
            <h3 className="text-lg font-bold text-foreground">Next Milestone</h3>
            <p className="text-sm text-muted-foreground font-mono">{metrics.nextMilestone}</p>
          </div>
          <button className="px-4 py-2 bg-gold text-gold-foreground rounded-md font-mono text-sm hover:bg-gold/90 transition-colors">
            Update Assessment
          </button>
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
            <option value="inclusive-growth">Inclusive Growth</option>
            <option value="human-centered">Human-Centered</option>
            <option value="transparency">Transparency</option>
            <option value="robustness">Robustness</option>
            <option value="accountability">Accountability</option>
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
          Generate Compliance Report
        </button>
      </div>

      {/* OECD Principles */}
      <div className="space-y-4">
        <h2 className="text-xl font-bold text-foreground">OECD AI Principles</h2>
        
        <div className="grid gap-4">
          {filteredPrinciples.map((principle) => (
            <div key={principle.id} className="bg-card border border-border rounded-lg p-6">
              <div className="flex items-start justify-between mb-4">
                <div className="flex-1">
                  <div className="flex items-center gap-3 mb-2">
                    <span className="text-2xl">{getCategoryIcon(principle.category)}</span>
                    <h3 className="text-lg font-bold text-foreground">{principle.name}</h3>
                    <span className={`inline-flex px-2 py-1 rounded text-xs font-mono ${getStatusColor(principle.status)}`}>
                      {principle.status.replace('-', ' ').toUpperCase()}
                    </span>
                    <span className={`text-sm font-mono ${getLevelColor(principle.implementationLevel)}`}>
                      {principle.implementationLevel.toUpperCase()}
                    </span>
                  </div>
                  <p className="text-sm text-muted-foreground font-mono mb-3">{principle.description}</p>
                  
                  <div className="flex items-center gap-4 mb-4">
                    <div className="flex items-center gap-2">
                      <span className="text-sm font-mono">Compliance:</span>
                      <span className={`text-lg font-bold ${getComplianceColor(principle.complianceScore)}`}>
                        {principle.complianceScore}%
                      </span>
                    </div>
                    <div className="flex-1 max-w-xs">
                      <div className="w-full bg-muted rounded-full h-2">
                        <div 
                          className={`h-2 rounded-full transition-all duration-500 ${getComplianceColor(principle.complianceScore).replace('text-', 'bg-')}`}
                          style={{ width: `${principle.complianceScore}%` }}
                        ></div>
                      </div>
                    </div>
                  </div>
                </div>
              </div>

              <div className="grid gap-4 sm:grid-cols-2">
                <div>
                  <h4 className="text-sm font-bold text-foreground mb-2">Requirements</h4>
                  <ul className="space-y-1">
                    {principle.requirements.map((req, index) => (
                      <li key={index} className="text-sm text-muted-foreground font-mono flex items-start gap-2">
                        <span className="text-gold mt-1">•</span>
                        {req}
                      </li>
                    ))}
                  </ul>
                </div>
                
                <div>
                  <h4 className="text-sm font-bold text-foreground mb-2">Evidence</h4>
                  <ul className="space-y-1">
                    {principle.evidence.map((ev, index) => (
                      <li key={index} className="text-sm text-muted-foreground font-mono flex items-start gap-2">
                        <span className="text-green-400 mt-1">✓</span>
                        {ev}
                      </li>
                    ))}
                  </ul>
                </div>
              </div>
              
              <div className="flex items-center justify-between pt-4 border-t border-border mt-4">
                <div className="flex gap-4 text-xs text-muted-foreground font-mono">
                  <span>Last assessed: {principle.lastAssessment}</span>
                  <span>Next review: {principle.nextReview}</span>
                </div>
                <div className="flex gap-2">
                  <button className="px-3 py-1 text-xs bg-card border border-border rounded font-mono hover:bg-accent transition-colors">
                    View Details
                  </button>
                  <button className="px-3 py-1 text-xs bg-card border border-border rounded font-mono hover:bg-accent transition-colors">
                    Update Status
                  </button>
                </div>
              </div>
            </div>
          ))}
        </div>
      </div>

      {/* Interoperability Framework */}
      <div className="bg-card border border-border rounded-lg p-6">
        <h2 className="text-xl font-bold text-foreground mb-4">Interoperability Framework</h2>
        <div className="grid gap-4 sm:grid-cols-2 lg:grid-cols-3">
          <div className="p-4 border border-border rounded-lg">
            <h3 className="font-bold text-foreground mb-2">National Alignment</h3>
            <p className="text-sm text-muted-foreground font-mono mb-3">
              Alignment with national AI strategies and regulations
            </p>
            <div className="text-2xl font-bold text-gold">92%</div>
          </div>
          <div className="p-4 border border-border rounded-lg">
            <h3 className="font-bold text-foreground mb-2">Regional Cooperation</h3>
            <p className="text-sm text-muted-foreground font-mono mb-3">
              Participation in regional AI governance initiatives
            </p>
            <div className="text-2xl font-bold text-gold">78%</div>
          </div>
          <div className="p-4 border border-border rounded-lg">
            <h3 className="font-bold text-foreground mb-2">Global Standards</h3>
            <p className="text-sm text-muted-foreground font-mono mb-3">
              Adoption of international AI standards and best practices
            </p>
            <div className="text-2xl font-bold text-gold">85%</div>
          </div>
        </div>
      </div>
    </div>
  )
}
