'use client'

import React, { useState, useEffect } from 'react'

interface AttestationResult {
  id: string
  name: string
  type: 'audit' | 'certification' | 'assessment' | 'review' | 'validation'
  framework: string
  status: 'passed' | 'failed' | 'conditional' | 'pending' | 'in-progress'
  auditor: string
  auditDate: string
  expiryDate: string
  score: number
  maxScore: number
  findings: AuditFinding[]
  recommendations: string[]
  evidence: string[]
  scope: string
  description: string
  nextReview: string
}

interface AuditFinding {
  id: string
  severity: 'critical' | 'high' | 'medium' | 'low' | 'informational'
  category: 'compliance' | 'security' | 'privacy' | 'operational' | 'technical'
  title: string
  description: string
  recommendation: string
  status: 'open' | 'in-progress' | 'resolved' | 'accepted'
  dueDate: string
  assignedTo: string
  evidence: string[]
  lastUpdated: string
}

interface Certification {
  id: string
  name: string
  issuer: string
  type: 'iso' | 'soc' | 'pci' | 'gdpr' | 'custom'
  status: 'active' | 'expired' | 'suspended' | 'pending'
  issueDate: string
  expiryDate: string
  scope: string
  description: string
  requirements: string[]
  evidence: string[]
  nextAudit: string
}

interface AttestationMetrics {
  totalAttestations: number
  passedAttestations: number
  failedAttestations: number
  averageScore: number
  activeCertifications: number
  openFindings: number
  lastAudit: string
  nextAudit: string
}

export default function AttestationResults() {
  const [loading, setLoading] = useState(true)
  const [attestations, setAttestations] = useState<AttestationResult[]>([])
  const [certifications, setCertifications] = useState<Certification[]>([])
  const [metrics, setMetrics] = useState<AttestationMetrics>({
    totalAttestations: 0,
    passedAttestations: 0,
    failedAttestations: 0,
    averageScore: 0,
    activeCertifications: 0,
    openFindings: 0,
    lastAudit: '',
    nextAudit: ''
  })
  const [selectedType, setSelectedType] = useState<string>('all')
  const [selectedStatus, setSelectedStatus] = useState<string>('all')

  useEffect(() => {
    const timer = setTimeout(() => {
      const mockAttestations: AttestationResult[] = [
        {
          id: '1',
          name: 'GDPR Compliance Audit',
          type: 'audit',
          framework: 'GDPR',
          status: 'passed',
          auditor: 'Deloitte & Touche',
          auditDate: '2024-01-15',
          expiryDate: '2025-01-15',
          score: 87,
          maxScore: 100,
          scope: 'All EU data processing activities',
          description: 'Comprehensive GDPR compliance audit covering data processing, rights management, and security controls',
          nextReview: '2024-07-15',
          findings: [
            {
              id: 'finding1',
              severity: 'medium',
              category: 'privacy',
              title: 'Data Retention Policy Inconsistency',
              description: 'Some systems have inconsistent data retention policies that may not align with GDPR requirements',
              recommendation: 'Standardize data retention policies across all systems and implement automated retention management',
              status: 'in-progress',
              dueDate: '2024-03-15',
              assignedTo: 'Data Governance Team',
              evidence: ['Retention policy review', 'System inventory'],
              lastUpdated: '2024-01-20'
            },
            {
              id: 'finding2',
              severity: 'low',
              category: 'operational',
              title: 'Documentation Updates Required',
              description: 'Privacy impact assessments need to be updated for recent system changes',
              recommendation: 'Update PIAs for all systems and establish regular review schedule',
              status: 'open',
              dueDate: '2024-04-15',
              assignedTo: 'Privacy Team',
              evidence: ['PIA templates', 'System change logs'],
              lastUpdated: '2024-01-18'
            }
          ],
          recommendations: [
            'Implement automated data retention management system',
            'Establish quarterly privacy impact assessment reviews',
            'Enhance data subject rights automation'
          ],
          evidence: [
            'Data processing register',
            'Privacy impact assessments',
            'Data subject rights procedures',
            'Security controls documentation'
          ]
        },
        {
          id: '2',
          name: 'ISO 27001 Information Security Assessment',
          type: 'certification',
          framework: 'ISO 27001',
          status: 'conditional',
          auditor: 'BSI Group',
          auditDate: '2024-01-10',
          expiryDate: '2024-12-31',
          score: 78,
          maxScore: 100,
          scope: 'Information security management system',
          description: 'ISO 27001 certification audit for information security management system',
          nextReview: '2024-06-10',
          findings: [
            {
              id: 'finding3',
              severity: 'high',
              category: 'security',
              title: 'Access Control Deficiencies',
              description: 'Some systems lack proper access control mechanisms and monitoring',
              recommendation: 'Implement comprehensive access control framework with monitoring and alerting',
              status: 'open',
              dueDate: '2024-02-28',
              assignedTo: 'Security Team',
              evidence: ['Access control audit', 'System security review'],
              lastUpdated: '2024-01-15'
            }
          ],
          recommendations: [
            'Implement comprehensive access control framework',
            'Enhance security monitoring and alerting',
            'Establish regular security awareness training'
          ],
          evidence: [
            'Information security policy',
            'Risk assessment reports',
            'Security controls documentation',
            'Training records'
          ]
        },
        {
          id: '3',
          name: 'SOC 2 Type II Assessment',
          type: 'assessment',
          framework: 'SOC 2',
          status: 'passed',
          auditor: 'PwC',
          auditDate: '2023-12-01',
          expiryDate: '2024-11-30',
          score: 92,
          maxScore: 100,
          scope: 'Cloud infrastructure and data processing services',
          description: 'SOC 2 Type II assessment covering security, availability, and confidentiality controls',
          nextReview: '2024-05-01',
          findings: [],
          recommendations: [
            'Continue monitoring and improving security controls',
            'Maintain regular control testing schedule',
            'Enhance incident response procedures'
          ],
          evidence: [
            'SOC 2 report',
            'Control testing results',
            'Incident response procedures',
            'Security monitoring logs'
          ]
        }
      ]

      const mockCertifications: Certification[] = [
        {
          id: 'cert1',
          name: 'ISO 27001:2013',
          issuer: 'BSI Group',
          type: 'iso',
          status: 'active',
          issueDate: '2023-06-01',
          expiryDate: '2024-12-31',
          scope: 'Information Security Management System',
          description: 'International standard for information security management',
          requirements: [
            'Information security policy',
            'Risk assessment and treatment',
            'Security controls implementation',
            'Regular monitoring and review'
          ],
          evidence: [
            'ISO 27001 certificate',
            'Audit reports',
            'Control documentation'
          ],
          nextAudit: '2024-06-01'
        },
        {
          id: 'cert2',
          name: 'SOC 2 Type II',
          issuer: 'PwC',
          type: 'soc',
          status: 'active',
          issueDate: '2023-12-01',
          expiryDate: '2024-11-30',
          scope: 'Cloud Infrastructure Services',
          description: 'Service Organization Control 2 certification for security, availability, and confidentiality',
          requirements: [
            'Security controls',
            'Availability controls',
            'Confidentiality controls',
            'Processing integrity controls'
          ],
          evidence: [
            'SOC 2 report',
            'Control testing results',
            'Monitoring procedures'
          ],
          nextAudit: '2024-05-01'
        }
      ]

      setAttestations(mockAttestations)
      setCertifications(mockCertifications)
      
      const passedAttestations = mockAttestations.filter(a => a.status === 'passed').length
      const failedAttestations = mockAttestations.filter(a => a.status === 'failed').length
      const avgScore = Math.round(mockAttestations.reduce((sum, a) => sum + a.score, 0) / mockAttestations.length)
      const activeCertifications = mockCertifications.filter(c => c.status === 'active').length
      const openFindings = mockAttestations.reduce((sum, a) => 
        sum + a.findings.filter(f => f.status === 'open' || f.status === 'in-progress').length, 0)

      setMetrics({
        totalAttestations: mockAttestations.length,
        passedAttestations: passedAttestations,
        failedAttestations: failedAttestations,
        averageScore: avgScore,
        activeCertifications: activeCertifications,
        openFindings: openFindings,
        lastAudit: '2024-01-15',
        nextAudit: '2024-02-15'
      })
      
      setLoading(false)
    }, 1000)

    return () => clearTimeout(timer)
  }, [])

  const filteredAttestations = attestations.filter(attestation => {
    const typeMatch = selectedType === 'all' || attestation.type === selectedType
    const statusMatch = selectedStatus === 'all' || attestation.status === selectedStatus
    return typeMatch && statusMatch
  })

  const getStatusColor = (status: string) => {
    switch (status) {
      case 'passed': return 'text-green-400 bg-green-500/20'
      case 'failed': return 'text-red-400 bg-red-500/20'
      case 'conditional': return 'text-yellow-400 bg-yellow-500/20'
      case 'pending': return 'text-blue-400 bg-blue-500/20'
      case 'in-progress': return 'text-purple-400 bg-purple-500/20'
      default: return 'text-muted-foreground bg-muted'
    }
  }

  const getSeverityColor = (severity: string) => {
    switch (severity) {
      case 'critical': return 'text-red-400 bg-red-500/20'
      case 'high': return 'text-orange-400 bg-orange-500/20'
      case 'medium': return 'text-yellow-400 bg-yellow-500/20'
      case 'low': return 'text-blue-400 bg-blue-500/20'
      case 'informational': return 'text-gray-400 bg-gray-500/20'
      default: return 'text-muted-foreground bg-muted'
    }
  }

  const getFindingStatusColor = (status: string) => {
    switch (status) {
      case 'resolved': return 'text-green-400'
      case 'in-progress': return 'text-blue-400'
      case 'open': return 'text-red-400'
      case 'accepted': return 'text-gray-400'
      default: return 'text-muted-foreground'
    }
  }

  const getCertificationStatusColor = (status: string) => {
    switch (status) {
      case 'active': return 'text-green-400 bg-green-500/20'
      case 'expired': return 'text-red-400 bg-red-500/20'
      case 'suspended': return 'text-yellow-400 bg-yellow-500/20'
      case 'pending': return 'text-blue-400 bg-blue-500/20'
      default: return 'text-muted-foreground bg-muted'
    }
  }

  const getTypeIcon = (type: string) => {
    switch (type) {
      case 'audit': return '🔍'
      case 'certification': return '🏆'
      case 'assessment': return '📋'
      case 'review': return '📝'
      case 'validation': return '✅'
      default: return '📋'
    }
  }

  const getCertificationTypeIcon = (type: string) => {
    switch (type) {
      case 'iso': return '🏆'
      case 'soc': return '📊'
      case 'pci': return '💳'
      case 'gdpr': return '🔒'
      case 'custom': return '⚙️'
      default: return '📋'
    }
  }

  if (loading) {
    return (
      <div className="space-y-6 p-4 md:p-6 max-w-[2000px] mx-auto">
        <div className="space-y-2">
          <h1 className="text-2xl md:text-3xl font-bold tracking-tight text-gold">
            Attestation Results
          </h1>
          <p className="text-xs md:text-sm text-muted-foreground font-mono">
            Audit Results & Certification Tracking
          </p>
        </div>
        <div className="flex items-center justify-center h-64">
          <div className="text-center">
            <div className="w-8 h-8 border-2 border-gold border-t-transparent rounded-full animate-spin mx-auto mb-4"></div>
            <p className="text-sm text-muted-foreground font-mono">Loading Attestation Results...</p>
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
          Attestation Results
        </h1>
        <p className="text-xs md:text-sm text-muted-foreground font-mono">
          Audit Results & Certification Tracking
        </p>
      </div>

      {/* Attestation Overview */}
      <div className="bg-card border border-border rounded-lg p-6">
        <div className="flex items-center justify-between mb-6">
          <div>
            <h2 className="text-xl font-bold text-foreground">Attestation Overview</h2>
            <p className="text-sm text-muted-foreground font-mono">
              Audit results and certification status tracking
            </p>
          </div>
          <div className="text-right">
            <div className="text-3xl font-bold text-gold">{metrics.averageScore}%</div>
            <span className="text-sm text-muted-foreground font-mono">Average Score</span>
          </div>
        </div>
        
        <div className="grid gap-4 sm:grid-cols-2 lg:grid-cols-4">
          <div className="text-center">
            <div className="text-2xl font-bold text-foreground">{metrics.totalAttestations}</div>
            <div className="text-xs text-muted-foreground font-mono">Total Attestations</div>
          </div>
          <div className="text-center">
            <div className="text-2xl font-bold text-green-400">{metrics.passedAttestations}</div>
            <div className="text-xs text-muted-foreground font-mono">Passed</div>
          </div>
          <div className="text-center">
            <div className="text-2xl font-bold text-foreground">{metrics.activeCertifications}</div>
            <div className="text-xs text-muted-foreground font-mono">Active Certifications</div>
          </div>
          <div className="text-center">
            <div className="text-2xl font-bold text-orange-400">{metrics.openFindings}</div>
            <div className="text-xs text-muted-foreground font-mono">Open Findings</div>
          </div>
        </div>
      </div>

      {/* Audit Status */}
      <div className="grid gap-4 sm:grid-cols-2">
        <div className="bg-card border border-border rounded-lg p-4">
          <h3 className="font-bold text-foreground mb-2">Last Audit</h3>
          <div className="text-sm font-bold text-foreground">{metrics.lastAudit}</div>
          <p className="text-xs text-muted-foreground font-mono">Most recent audit completion</p>
        </div>
        <div className="bg-card border border-border rounded-lg p-4">
          <h3 className="font-bold text-foreground mb-2">Next Audit</h3>
          <div className="text-sm font-bold text-foreground">{metrics.nextAudit}</div>
          <p className="text-xs text-muted-foreground font-mono">Scheduled audit date</p>
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
            <option value="audit">Audit</option>
            <option value="certification">Certification</option>
            <option value="assessment">Assessment</option>
            <option value="review">Review</option>
            <option value="validation">Validation</option>
          </select>
          <select
            value={selectedStatus}
            onChange={(e) => setSelectedStatus(e.target.value)}
            className="px-3 py-1 text-sm bg-card border border-border rounded-md font-mono"
          >
            <option value="all">All Status</option>
            <option value="passed">Passed</option>
            <option value="failed">Failed</option>
            <option value="conditional">Conditional</option>
            <option value="pending">Pending</option>
            <option value="in-progress">In Progress</option>
          </select>
        </div>
        <button className="px-4 py-2 bg-gold text-gold-foreground rounded-md font-mono text-sm hover:bg-gold/90 transition-colors">
          Schedule Audit
        </button>
      </div>

      {/* Attestation Results */}
      <div className="space-y-4">
        <h2 className="text-xl font-bold text-foreground">Attestation Results</h2>
        
        <div className="grid gap-4">
          {filteredAttestations.map((attestation) => (
            <div key={attestation.id} className="bg-card border border-border rounded-lg p-6">
              <div className="flex items-start justify-between mb-4">
                <div className="flex-1">
                  <div className="flex items-center gap-3 mb-2">
                    <span className="text-2xl">{getTypeIcon(attestation.type)}</span>
                    <h3 className="text-lg font-bold text-foreground">{attestation.name}</h3>
                    <span className={`inline-flex px-2 py-1 rounded text-xs font-mono ${getStatusColor(attestation.status)}`}>
                      {attestation.status.toUpperCase()}
                    </span>
                    <span className="text-sm font-mono text-muted-foreground">{attestation.framework}</span>
                  </div>
                  <p className="text-sm text-muted-foreground font-mono mb-3">{attestation.description}</p>
                  
                  <div className="grid gap-4 sm:grid-cols-2 lg:grid-cols-4 mb-4">
                    <div>
                      <span className="text-xs text-muted-foreground font-mono">Auditor</span>
                      <div className="text-sm font-bold text-foreground">{attestation.auditor}</div>
                    </div>
                    <div>
                      <span className="text-xs text-muted-foreground font-mono">Score</span>
                      <div className="text-lg font-bold text-green-400">{attestation.score}/{attestation.maxScore}</div>
                    </div>
                    <div>
                      <span className="text-xs text-muted-foreground font-mono">Audit Date</span>
                      <div className="text-sm font-bold text-foreground">{attestation.auditDate}</div>
                    </div>
                    <div>
                      <span className="text-xs text-muted-foreground font-mono">Expiry Date</span>
                      <div className="text-sm font-bold text-foreground">{attestation.expiryDate}</div>
                    </div>
                  </div>
                </div>
              </div>

              {/* Findings */}
              {attestation.findings.length > 0 && (
                <div className="space-y-3 mb-4">
                  <h4 className="text-sm font-bold text-foreground">Audit Findings</h4>
                  <div className="grid gap-3">
                    {attestation.findings.map((finding) => (
                      <div key={finding.id} className="border border-border rounded-lg p-4">
                        <div className="flex items-start justify-between mb-3">
                          <div className="flex-1">
                            <div className="flex items-center gap-2 mb-1">
                              <h5 className="text-sm font-bold text-foreground">{finding.title}</h5>
                              <span className={`inline-flex px-1 py-0.5 rounded text-xs font-mono ${getSeverityColor(finding.severity)}`}>
                                {finding.severity.toUpperCase()}
                              </span>
                              <span className={`text-xs font-mono ${getFindingStatusColor(finding.status)}`}>
                                {finding.status.toUpperCase()}
                              </span>
                              <span className="text-xs font-mono text-muted-foreground">{finding.category}</span>
                            </div>
                            <p className="text-xs text-muted-foreground font-mono mb-2">{finding.description}</p>
                            <p className="text-xs text-muted-foreground font-mono mb-2">
                              <strong>Recommendation:</strong> {finding.recommendation}
                            </p>
                          </div>
                        </div>
                        
                        <div className="grid gap-2 sm:grid-cols-2">
                          <div>
                            <span className="text-xs text-muted-foreground font-mono">Assigned To</span>
                            <div className="text-sm font-bold text-foreground">{finding.assignedTo}</div>
                          </div>
                          <div>
                            <span className="text-xs text-muted-foreground font-mono">Due Date</span>
                            <div className="text-sm font-bold text-foreground">{finding.dueDate}</div>
                          </div>
                        </div>
                      </div>
                    ))}
                  </div>
                </div>
              )}

              {/* Recommendations */}
              <div className="space-y-3 mb-4">
                <h4 className="text-sm font-bold text-foreground">Recommendations</h4>
                <ul className="space-y-2">
                  {attestation.recommendations.map((rec, index) => (
                    <li key={index} className="flex items-start gap-2">
                      <span className="text-blue-400 mt-0.5">•</span>
                      <span className="text-sm text-muted-foreground font-mono">{rec}</span>
                    </li>
                  ))}
                </ul>
              </div>

              {/* Evidence */}
              <div className="space-y-3 mb-4">
                <h4 className="text-sm font-bold text-foreground">Evidence</h4>
                <div className="grid gap-2 sm:grid-cols-2">
                  {attestation.evidence.map((ev, index) => (
                    <div key={index} className="flex items-center gap-2">
                      <span className="text-green-400">✓</span>
                      <span className="text-sm text-muted-foreground font-mono">{ev}</span>
                    </div>
                  ))}
                </div>
              </div>
              
              <div className="flex items-center justify-between pt-4 border-t border-border">
                <div className="flex gap-4 text-xs text-muted-foreground font-mono">
                  <span>Type: {attestation.type}</span>
                  <span>Scope: {attestation.scope}</span>
                  <span>Next Review: {attestation.nextReview}</span>
                </div>
                <div className="flex gap-2">
                  <button className="px-3 py-1 text-xs bg-card border border-border rounded font-mono hover:bg-accent transition-colors">
                    View Report
                  </button>
                  <button className="px-3 py-1 text-xs bg-card border border-border rounded font-mono hover:bg-accent transition-colors">
                    Download Certificate
                  </button>
                </div>
              </div>
            </div>
          ))}
        </div>
      </div>

      {/* Certifications */}
      <div className="space-y-4">
        <h2 className="text-xl font-bold text-foreground">Active Certifications</h2>
        
        <div className="grid gap-4">
          {certifications.map((certification) => (
            <div key={certification.id} className="bg-card border border-border rounded-lg p-6">
              <div className="flex items-start justify-between mb-4">
                <div className="flex-1">
                  <div className="flex items-center gap-3 mb-2">
                    <span className="text-2xl">{getCertificationTypeIcon(certification.type)}</span>
                    <h3 className="text-lg font-bold text-foreground">{certification.name}</h3>
                    <span className={`inline-flex px-2 py-1 rounded text-xs font-mono ${getCertificationStatusColor(certification.status)}`}>
                      {certification.status.toUpperCase()}
                    </span>
                    <span className="text-sm font-mono text-muted-foreground">{certification.issuer}</span>
                  </div>
                  <p className="text-sm text-muted-foreground font-mono mb-3">{certification.description}</p>
                  
                  <div className="grid gap-4 sm:grid-cols-2 lg:grid-cols-4 mb-4">
                    <div>
                      <span className="text-xs text-muted-foreground font-mono">Issue Date</span>
                      <div className="text-sm font-bold text-foreground">{certification.issueDate}</div>
                    </div>
                    <div>
                      <span className="text-xs text-muted-foreground font-mono">Expiry Date</span>
                      <div className="text-sm font-bold text-foreground">{certification.expiryDate}</div>
                    </div>
                    <div>
                      <span className="text-xs text-muted-foreground font-mono">Type</span>
                      <div className="text-sm font-bold text-foreground">{certification.type.toUpperCase()}</div>
                    </div>
                    <div>
                      <span className="text-xs text-muted-foreground font-mono">Next Audit</span>
                      <div className="text-sm font-bold text-foreground">{certification.nextAudit}</div>
                    </div>
                  </div>
                </div>
              </div>

              {/* Requirements */}
              <div className="space-y-3 mb-4">
                <h4 className="text-sm font-bold text-foreground">Requirements</h4>
                <ul className="space-y-2">
                  {certification.requirements.map((req, index) => (
                    <li key={index} className="flex items-start gap-2">
                      <span className="text-blue-400 mt-0.5">•</span>
                      <span className="text-sm text-muted-foreground font-mono">{req}</span>
                    </li>
                  ))}
                </ul>
              </div>

              {/* Evidence */}
              <div className="space-y-3 mb-4">
                <h4 className="text-sm font-bold text-foreground">Evidence</h4>
                <div className="grid gap-2 sm:grid-cols-2">
                  {certification.evidence.map((ev, index) => (
                    <div key={index} className="flex items-center gap-2">
                      <span className="text-green-400">✓</span>
                      <span className="text-sm text-muted-foreground font-mono">{ev}</span>
                    </div>
                  ))}
                </div>
              </div>
              
              <div className="flex items-center justify-between pt-4 border-t border-border">
                <div className="flex gap-4 text-xs text-muted-foreground font-mono">
                  <span>Type: {certification.type}</span>
                  <span>Scope: {certification.scope}</span>
                  <span>Issuer: {certification.issuer}</span>
                </div>
                <div className="flex gap-2">
                  <button className="px-3 py-1 text-xs bg-card border border-border rounded font-mono hover:bg-accent transition-colors">
                    View Certificate
                  </button>
                  <button className="px-3 py-1 text-xs bg-card border border-border rounded font-mono hover:bg-accent transition-colors">
                    Download Report
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
