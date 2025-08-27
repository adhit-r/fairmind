'use client'

import React, { useState, useEffect } from 'react'

interface Report {
  id: string
  name: string
  type: 'executive' | 'compliance' | 'security' | 'risk' | 'performance' | 'audit'
  status: 'draft' | 'review' | 'published' | 'archived'
  author: string
  createdAt: string
  lastUpdated: string
  scheduledDate?: string
  description: string
  audience: string[]
  sections: ReportSection[]
  metrics: ReportMetric[]
  recommendations: string[]
  attachments: string[]
  tags: string[]
}

interface ReportSection {
  id: string
  title: string
  content: string
  type: 'summary' | 'metrics' | 'analysis' | 'findings' | 'recommendations'
  order: number
  data?: any
}

interface ReportMetric {
  name: string
  value: number
  unit: string
  trend: 'up' | 'down' | 'stable'
  change: number
  target: number
  status: 'on-track' | 'at-risk' | 'off-track'
}

interface ReportTemplate {
  id: string
  name: string
  type: string
  description: string
  sections: string[]
  lastUsed: string
  usageCount: number
}

interface ReportMetrics {
  totalReports: number
  publishedReports: number
  draftReports: number
  scheduledReports: number
  averageCompletionTime: number
  lastGenerated: string
  nextScheduled: string
}

export default function Reports() {
  const [loading, setLoading] = useState(true)
  const [reports, setReports] = useState<Report[]>([])
  const [templates, setTemplates] = useState<ReportTemplate[]>([])
  const [metrics, setMetrics] = useState<ReportMetrics>({
    totalReports: 0,
    publishedReports: 0,
    draftReports: 0,
    scheduledReports: 0,
    averageCompletionTime: 0,
    lastGenerated: '',
    nextScheduled: ''
  })
  const [selectedType, setSelectedType] = useState<string>('all')
  const [selectedStatus, setSelectedStatus] = useState<string>('all')

  useEffect(() => {
    const timer = setTimeout(() => {
      const mockReports: Report[] = [
        {
          id: '1',
          name: 'Q4 2023 Executive Compliance Summary',
          type: 'executive',
          status: 'published',
          author: 'Sarah Johnson',
          createdAt: '2024-01-15',
          lastUpdated: '2024-01-20',
          description: 'Comprehensive executive summary of Q4 2023 compliance performance and key metrics',
          audience: ['C-Suite', 'Board of Directors', 'Compliance Team'],
          tags: ['executive', 'compliance', 'quarterly'],
          sections: [
            {
              id: 'sec1',
              title: 'Executive Summary',
              content: 'Q4 2023 demonstrated strong compliance performance with 94% overall compliance rate across all frameworks. Key achievements include successful GDPR implementation and ISO 27001 certification.',
              type: 'summary',
              order: 1
            },
            {
              id: 'sec2',
              title: 'Key Performance Metrics',
              content: 'Compliance rate improved by 8% compared to Q3, with significant progress in data privacy and security controls.',
              type: 'metrics',
              order: 2,
              data: {
                complianceRate: 94,
                securityScore: 89,
                privacyScore: 92,
                riskScore: 78
              }
            },
            {
              id: 'sec3',
              title: 'Risk Assessment',
              content: 'Identified 3 high-priority risks requiring immediate attention, with mitigation plans in progress.',
              type: 'analysis',
              order: 3
            }
          ],
          metrics: [
            {
              name: 'Overall Compliance Rate',
              value: 94,
              unit: '%',
              trend: 'up',
              change: 8,
              target: 90,
              status: 'on-track'
            },
            {
              name: 'Security Score',
              value: 89,
              unit: '%',
              trend: 'up',
              change: 5,
              target: 85,
              status: 'on-track'
            },
            {
              name: 'Risk Score',
              value: 78,
              unit: '%',
              trend: 'down',
              change: -3,
              target: 80,
              status: 'at-risk'
            }
          ],
          recommendations: [
            'Implement automated compliance monitoring system',
            'Enhance security awareness training program',
            'Establish quarterly risk review process'
          ],
          attachments: [
            'Q4_Compliance_Report.pdf',
            'Compliance_Metrics_Dashboard.xlsx',
            'Risk_Assessment_Matrix.pdf'
          ]
        },
        {
          id: '2',
          name: 'AI Governance Framework Assessment',
          type: 'compliance',
          status: 'review',
          author: 'David Rodriguez',
          createdAt: '2024-01-18',
          lastUpdated: '2024-01-19',
          description: 'Assessment of AI governance framework implementation and EU AI Act compliance',
          audience: ['AI Team', 'Legal Team', 'Compliance Team'],
          tags: ['ai-governance', 'eu-ai-act', 'assessment'],
          sections: [
            {
              id: 'sec4',
              title: 'Framework Overview',
              content: 'Comprehensive assessment of AI governance framework against EU AI Act requirements.',
              type: 'summary',
              order: 1
            },
            {
              id: 'sec5',
              title: 'Compliance Analysis',
              content: 'Detailed analysis of current compliance status and gap identification.',
              type: 'analysis',
              order: 2
            }
          ],
          metrics: [
            {
              name: 'AI Governance Score',
              value: 72,
              unit: '%',
              trend: 'up',
              change: 12,
              target: 80,
              status: 'at-risk'
            },
            {
              name: 'EU AI Act Compliance',
              value: 68,
              unit: '%',
              trend: 'up',
              change: 15,
              target: 75,
              status: 'at-risk'
            }
          ],
          recommendations: [
            'Implement AI risk assessment framework',
            'Enhance model documentation processes',
            'Establish AI ethics review board'
          ],
          attachments: [
            'AI_Governance_Assessment.pdf',
            'EU_AI_Act_Compliance_Matrix.xlsx'
          ]
        },
        {
          id: '3',
          name: 'Security Posture Analysis',
          type: 'security',
          status: 'draft',
          author: 'Jennifer Lee',
          createdAt: '2024-01-20',
          lastUpdated: '2024-01-20',
          description: 'Comprehensive security posture analysis and vulnerability assessment',
          audience: ['Security Team', 'IT Team', 'CISO'],
          tags: ['security', 'vulnerability', 'assessment'],
          sections: [
            {
              id: 'sec6',
              title: 'Security Overview',
              content: 'Analysis of current security posture and identified vulnerabilities.',
              type: 'summary',
              order: 1
            }
          ],
          metrics: [
            {
              name: 'Security Score',
              value: 85,
              unit: '%',
              trend: 'stable',
              change: 0,
              target: 90,
              status: 'at-risk'
            },
            {
              name: 'Vulnerability Count',
              value: 12,
              unit: '',
              trend: 'down',
              change: -5,
              target: 10,
              status: 'at-risk'
            }
          ],
          recommendations: [
            'Implement advanced threat detection',
            'Enhance access control mechanisms',
            'Establish security monitoring dashboard'
          ],
          attachments: [
            'Security_Analysis_Draft.pdf',
            'Vulnerability_Assessment.xlsx'
          ]
        }
      ]

      const mockTemplates: ReportTemplate[] = [
        {
          id: 'template1',
          name: 'Executive Summary Template',
          type: 'executive',
          description: 'Standard template for executive-level compliance summaries',
          sections: ['Executive Summary', 'Key Metrics', 'Risk Assessment', 'Recommendations'],
          lastUsed: '2024-01-15',
          usageCount: 24
        },
        {
          id: 'template2',
          name: 'Compliance Assessment Template',
          type: 'compliance',
          description: 'Template for detailed compliance assessments and gap analysis',
          sections: ['Framework Overview', 'Compliance Analysis', 'Gap Assessment', 'Remediation Plan'],
          lastUsed: '2024-01-18',
          usageCount: 15
        },
        {
          id: 'template3',
          name: 'Security Report Template',
          type: 'security',
          description: 'Template for security posture analysis and vulnerability reports',
          sections: ['Security Overview', 'Vulnerability Analysis', 'Risk Assessment', 'Security Recommendations'],
          lastUsed: '2024-01-20',
          usageCount: 8
        }
      ]

      setReports(mockReports)
      setTemplates(mockTemplates)
      
      const publishedReports = mockReports.filter(r => r.status === 'published').length
      const draftReports = mockReports.filter(r => r.status === 'draft').length
      const scheduledReports = mockReports.filter(r => r.scheduledDate).length

      setMetrics({
        totalReports: mockReports.length,
        publishedReports: publishedReports,
        draftReports: draftReports,
        scheduledReports: scheduledReports,
        averageCompletionTime: 3.5,
        lastGenerated: '2024-01-20 16:00:00',
        nextScheduled: '2024-02-01'
      })
      
      setLoading(false)
    }, 1000)

    return () => clearTimeout(timer)
  }, [])

  const filteredReports = reports.filter(report => {
    const typeMatch = selectedType === 'all' || report.type === selectedType
    const statusMatch = selectedStatus === 'all' || report.status === selectedStatus
    return typeMatch && statusMatch
  })

  const getStatusColor = (status: string) => {
    switch (status) {
      case 'published': return 'text-green-400 bg-green-500/20'
      case 'review': return 'text-yellow-400 bg-yellow-500/20'
      case 'draft': return 'text-blue-400 bg-blue-500/20'
      case 'archived': return 'text-gray-400 bg-gray-500/20'
      default: return 'text-muted-foreground bg-muted'
    }
  }

  const getMetricStatusColor = (status: string) => {
    switch (status) {
      case 'on-track': return 'text-green-400'
      case 'at-risk': return 'text-yellow-400'
      case 'off-track': return 'text-red-400'
      default: return 'text-muted-foreground'
    }
  }

  const getTrendIcon = (trend: string) => {
    switch (trend) {
      case 'up': return '↗️'
      case 'down': return '↘️'
      case 'stable': return '→'
      default: return '→'
    }
  }

  const getTypeIcon = (type: string) => {
    switch (type) {
      case 'executive': return '📊'
      case 'compliance': return '📋'
      case 'security': return '🛡️'
      case 'risk': return '⚠️'
      case 'performance': return '📈'
      case 'audit': return '🔍'
      default: return '📄'
    }
  }

  if (loading) {
    return (
      <div className="space-y-6 p-4 md:p-6 max-w-[2000px] mx-auto">
        <div className="space-y-2">
          <h1 className="text-2xl md:text-3xl font-bold tracking-tight text-gold">
            Reports
          </h1>
          <p className="text-xs md:text-sm text-muted-foreground font-mono">
            Executive Summaries & Comprehensive Reporting
          </p>
        </div>
        <div className="flex items-center justify-center h-64">
          <div className="text-center">
            <div className="w-8 h-8 border-2 border-gold border-t-transparent rounded-full animate-spin mx-auto mb-4"></div>
            <p className="text-sm text-muted-foreground font-mono">Loading Reports...</p>
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
          Reports
        </h1>
        <p className="text-xs md:text-sm text-muted-foreground font-mono">
          Executive Summaries & Comprehensive Reporting
        </p>
      </div>

      {/* Reports Overview */}
      <div className="bg-card border border-border rounded-lg p-6">
        <div className="flex items-center justify-between mb-6">
          <div>
            <h2 className="text-xl font-bold text-foreground">Reports Overview</h2>
            <p className="text-sm text-muted-foreground font-mono">
              Report generation and management dashboard
            </p>
          </div>
          <div className="text-right">
            <div className="text-3xl font-bold text-gold">{metrics.publishedReports}</div>
            <span className="text-sm text-muted-foreground font-mono">Published Reports</span>
          </div>
        </div>
        
        <div className="grid gap-4 sm:grid-cols-2 lg:grid-cols-4">
          <div className="text-center">
            <div className="text-2xl font-bold text-foreground">{metrics.totalReports}</div>
            <div className="text-xs text-muted-foreground font-mono">Total Reports</div>
          </div>
          <div className="text-center">
            <div className="text-2xl font-bold text-green-400">{metrics.publishedReports}</div>
            <div className="text-xs text-muted-foreground font-mono">Published</div>
          </div>
          <div className="text-center">
            <div className="text-2xl font-bold text-blue-400">{metrics.draftReports}</div>
            <div className="text-xs text-muted-foreground font-mono">Draft</div>
          </div>
          <div className="text-center">
            <div className="text-2xl font-bold text-foreground">{metrics.scheduledReports}</div>
            <div className="text-xs text-muted-foreground font-mono">Scheduled</div>
          </div>
        </div>
      </div>

      {/* Report Status */}
      <div className="grid gap-4 sm:grid-cols-2">
        <div className="bg-card border border-border rounded-lg p-4">
          <h3 className="font-bold text-foreground mb-2">Last Generated</h3>
          <div className="text-sm font-bold text-foreground">{metrics.lastGenerated}</div>
          <p className="text-xs text-muted-foreground font-mono">Most recent report generation</p>
        </div>
        <div className="bg-card border border-border rounded-lg p-4">
          <h3 className="font-bold text-foreground mb-2">Next Scheduled</h3>
          <div className="text-sm font-bold text-foreground">{metrics.nextScheduled}</div>
          <p className="text-xs text-muted-foreground font-mono">Next scheduled report generation</p>
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
            <option value="executive">Executive</option>
            <option value="compliance">Compliance</option>
            <option value="security">Security</option>
            <option value="risk">Risk</option>
            <option value="performance">Performance</option>
            <option value="audit">Audit</option>
          </select>
          <select
            value={selectedStatus}
            onChange={(e) => setSelectedStatus(e.target.value)}
            className="px-3 py-1 text-sm bg-card border border-border rounded-md font-mono"
          >
            <option value="all">All Status</option>
            <option value="published">Published</option>
            <option value="review">Review</option>
            <option value="draft">Draft</option>
            <option value="archived">Archived</option>
          </select>
        </div>
        <button className="px-4 py-2 bg-gold text-gold-foreground rounded-md font-mono text-sm hover:bg-gold/90 transition-colors">
          Generate New Report
        </button>
      </div>

      {/* Reports */}
      <div className="space-y-4">
        <h2 className="text-xl font-bold text-foreground">Reports</h2>
        
        <div className="grid gap-4">
          {filteredReports.map((report) => (
            <div key={report.id} className="bg-card border border-border rounded-lg p-6">
              <div className="flex items-start justify-between mb-4">
                <div className="flex-1">
                  <div className="flex items-center gap-3 mb-2">
                    <span className="text-2xl">{getTypeIcon(report.type)}</span>
                    <h3 className="text-lg font-bold text-foreground">{report.name}</h3>
                    <span className={`inline-flex px-2 py-1 rounded text-xs font-mono ${getStatusColor(report.status)}`}>
                      {report.status.toUpperCase()}
                    </span>
                    <span className="text-sm font-mono text-muted-foreground">{report.type}</span>
                  </div>
                  <p className="text-sm text-muted-foreground font-mono mb-3">{report.description}</p>
                  
                  <div className="grid gap-4 sm:grid-cols-2 lg:grid-cols-4 mb-4">
                    <div>
                      <span className="text-xs text-muted-foreground font-mono">Author</span>
                      <div className="text-sm font-bold text-foreground">{report.author}</div>
                    </div>
                    <div>
                      <span className="text-xs text-muted-foreground font-mono">Created</span>
                      <div className="text-sm font-bold text-foreground">{report.createdAt}</div>
                    </div>
                    <div>
                      <span className="text-xs text-muted-foreground font-mono">Last Updated</span>
                      <div className="text-sm font-bold text-foreground">{report.lastUpdated}</div>
                    </div>
                    <div>
                      <span className="text-xs text-muted-foreground font-mono">Sections</span>
                      <div className="text-sm font-bold text-foreground">{report.sections.length}</div>
                    </div>
                  </div>
                </div>
              </div>

              {/* Key Metrics */}
              <div className="space-y-3 mb-4">
                <h4 className="text-sm font-bold text-foreground">Key Metrics</h4>
                <div className="grid gap-3 sm:grid-cols-2 lg:grid-cols-3">
                  {report.metrics.map((metric, index) => (
                    <div key={index} className="border border-border rounded-lg p-3">
                      <div className="flex items-center justify-between mb-2">
                        <h5 className="text-sm font-bold text-foreground">{metric.name}</h5>
                        <span className="text-lg">{getTrendIcon(metric.trend)}</span>
                      </div>
                      <div className="text-lg font-bold text-foreground">{metric.value}{metric.unit}</div>
                      <div className="flex items-center justify-between text-xs text-muted-foreground font-mono">
                        <span className={`${getMetricStatusColor(metric.status)}`}>
                          {metric.status.replace('-', ' ').toUpperCase()}
                        </span>
                        <span>Target: {metric.target}{metric.unit}</span>
                      </div>
                    </div>
                  ))}
                </div>
              </div>

              {/* Report Sections */}
              <div className="space-y-3 mb-4">
                <h4 className="text-sm font-bold text-foreground">Report Sections</h4>
                <div className="grid gap-3">
                  {report.sections.map((section) => (
                    <div key={section.id} className="border border-border rounded-lg p-3">
                      <div className="flex items-center justify-between mb-2">
                        <h5 className="text-sm font-bold text-foreground">{section.title}</h5>
                        <span className="text-xs font-mono text-muted-foreground">{section.type}</span>
                      </div>
                      <p className="text-xs text-muted-foreground font-mono">{section.content}</p>
                    </div>
                  ))}
                </div>
              </div>

              {/* Recommendations */}
              <div className="space-y-3 mb-4">
                <h4 className="text-sm font-bold text-foreground">Recommendations</h4>
                <ul className="space-y-2">
                  {report.recommendations.map((rec, index) => (
                    <li key={index} className="flex items-start gap-2">
                      <span className="text-blue-400 mt-0.5">•</span>
                      <span className="text-sm text-muted-foreground font-mono">{rec}</span>
                    </li>
                  ))}
                </ul>
              </div>

              {/* Attachments */}
              <div className="space-y-3 mb-4">
                <h4 className="text-sm font-bold text-foreground">Attachments</h4>
                <div className="grid gap-2 sm:grid-cols-2">
                  {report.attachments.map((attachment, index) => (
                    <div key={index} className="flex items-center gap-2">
                      <span className="text-green-400">📎</span>
                      <span className="text-sm text-muted-foreground font-mono">{attachment}</span>
                    </div>
                  ))}
                </div>
              </div>
              
              <div className="flex items-center justify-between pt-4 border-t border-border">
                <div className="flex gap-4 text-xs text-muted-foreground font-mono">
                  <span>Type: {report.type}</span>
                  <span>Audience: {report.audience.join(', ')}</span>
                  <span>Tags: {report.tags.join(', ')}</span>
                </div>
                <div className="flex gap-2">
                  <button className="px-3 py-1 text-xs bg-card border border-border rounded font-mono hover:bg-accent transition-colors">
                    View Report
                  </button>
                  <button className="px-3 py-1 text-xs bg-card border border-border rounded font-mono hover:bg-accent transition-colors">
                    Download PDF
                  </button>
                </div>
              </div>
            </div>
          ))}
        </div>
      </div>

      {/* Report Templates */}
      <div className="space-y-4">
        <h2 className="text-xl font-bold text-foreground">Report Templates</h2>
        
        <div className="grid gap-4 sm:grid-cols-2 lg:grid-cols-3">
          {templates.map((template) => (
            <div key={template.id} className="bg-card border border-border rounded-lg p-4">
              <div className="flex items-start justify-between mb-3">
                <div className="flex-1">
                  <h3 className="text-sm font-bold text-foreground mb-1">{template.name}</h3>
                  <p className="text-xs text-muted-foreground font-mono mb-2">{template.description}</p>
                  <div className="text-xs text-muted-foreground font-mono mb-2">
                    Type: {template.type.toUpperCase()}
                  </div>
                </div>
              </div>

              {/* Template Sections */}
              <div className="space-y-2 mb-3">
                <h4 className="text-xs font-bold text-foreground">Sections</h4>
                <ul className="space-y-1">
                  {template.sections.map((section, index) => (
                    <li key={index} className="flex items-center gap-1">
                      <span className="text-blue-400 text-xs">•</span>
                      <span className="text-xs text-muted-foreground font-mono">{section}</span>
                    </li>
                  ))}
                </ul>
              </div>

              <div className="flex items-center justify-between pt-3 border-t border-border">
                <div className="text-xs text-muted-foreground font-mono">
                  Used {template.usageCount} times
                </div>
                <div className="flex gap-2">
                  <button className="px-2 py-1 text-xs bg-card border border-border rounded font-mono hover:bg-accent transition-colors">
                    Use Template
                  </button>
                  <button className="px-2 py-1 text-xs bg-card border border-border rounded font-mono hover:bg-accent transition-colors">
                    Edit
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
