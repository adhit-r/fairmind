'use client'

import React, { useState, useEffect } from 'react'

interface GovernancePolicy {
  id: string
  name: string
  category: 'data-privacy' | 'model-governance' | 'security' | 'compliance' | 'ethics' | 'operational'
  status: 'active' | 'draft' | 'review' | 'deprecated' | 'archived'
  priority: 'critical' | 'high' | 'medium' | 'low'
  description: string
  rules: PolicyRule[]
  enforcement: 'automatic' | 'manual' | 'semi-automatic'
  lastUpdated: string
  nextReview: string
  complianceRate: number
  violations: number
  effectiveness: number
}

interface PolicyRule {
  id: string
  name: string
  condition: string
  action: string
  severity: 'critical' | 'high' | 'medium' | 'low'
  status: 'active' | 'inactive' | 'testing'
  triggers: number
  lastTriggered: string
  successRate: number
}

interface GovernanceEvent {
  id: string
  timestamp: string
  type: 'policy-violation' | 'rule-trigger' | 'compliance-check' | 'policy-update' | 'automation'
  severity: 'critical' | 'high' | 'medium' | 'low'
  description: string
  affectedPolicy: string
  status: 'open' | 'resolved' | 'investigating' | 'false-positive'
  resolution: string
  automated: boolean
}

interface GovernanceMetrics {
  totalPolicies: number
  activePolicies: number
  automatedPolicies: number
  complianceRate: number
  averageEffectiveness: number
  totalViolations: number
  lastAudit: string
  nextReview: string
}

export default function AdaptiveGovernance() {
  const [loading, setLoading] = useState(true)
  const [policies, setPolicies] = useState<GovernancePolicy[]>([])
  const [events, setEvents] = useState<GovernanceEvent[]>([])
  const [metrics, setMetrics] = useState<GovernanceMetrics>({
    totalPolicies: 0,
    activePolicies: 0,
    automatedPolicies: 0,
    complianceRate: 0,
    averageEffectiveness: 0,
    totalViolations: 0,
    lastAudit: '',
    nextReview: ''
  })
  const [selectedCategory, setSelectedCategory] = useState<string>('all')
  const [selectedStatus, setSelectedStatus] = useState<string>('all')

  useEffect(() => {
    const timer = setTimeout(() => {
      const mockPolicies: GovernancePolicy[] = [
        {
          id: '1',
          name: 'Data Privacy Protection Policy',
          category: 'data-privacy',
          status: 'active',
          priority: 'critical',
          description: 'Ensures compliance with data protection regulations and privacy requirements',
          enforcement: 'automatic',
          lastUpdated: '2024-01-15',
          nextReview: '2024-04-15',
          complianceRate: 95,
          violations: 3,
          effectiveness: 92,
          rules: [
            {
              id: 'r1',
              name: 'Personal Data Encryption',
              condition: 'IF data_type = "personal" THEN encrypt = true',
              action: 'Automatically encrypt personal data before storage',
              severity: 'critical',
              status: 'active',
              triggers: 156,
              lastTriggered: '2024-01-20 14:30:00',
              successRate: 98.5
            },
            {
              id: 'r2',
              name: 'Data Retention Compliance',
              condition: 'IF retention_period > max_retention THEN flag_for_deletion',
              action: 'Flag data for deletion when retention period exceeds limits',
              severity: 'high',
              status: 'active',
              triggers: 89,
              lastTriggered: '2024-01-20 12:15:00',
              successRate: 96.2
            }
          ]
        },
        {
          id: '2',
          name: 'Model Bias Detection Policy',
          category: 'ethics',
          status: 'active',
          priority: 'high',
          description: 'Automatically detects and mitigates bias in AI models',
          enforcement: 'semi-automatic',
          lastUpdated: '2024-01-12',
          nextReview: '2024-03-12',
          complianceRate: 88,
          violations: 7,
          effectiveness: 85,
          rules: [
            {
              id: 'r3',
              name: 'Bias Threshold Monitoring',
              condition: 'IF bias_score > 0.1 THEN require_review',
              action: 'Flag model for bias review when threshold exceeded',
              severity: 'high',
              status: 'active',
              triggers: 23,
              lastTriggered: '2024-01-20 10:45:00',
              successRate: 91.3
            }
          ]
        },
        {
          id: '3',
          name: 'Security Access Control Policy',
          category: 'security',
          status: 'active',
          priority: 'critical',
          description: 'Manages access controls and security permissions for AI systems',
          enforcement: 'automatic',
          lastUpdated: '2024-01-10',
          nextReview: '2024-04-10',
          complianceRate: 97,
          violations: 1,
          effectiveness: 96,
          rules: [
            {
              id: 'r4',
              name: 'Multi-Factor Authentication',
              condition: 'IF access_level = "admin" THEN require_mfa = true',
              action: 'Enforce MFA for administrative access',
              severity: 'critical',
              status: 'active',
              triggers: 445,
              lastTriggered: '2024-01-20 16:00:00',
              successRate: 99.8
            }
          ]
        },
        {
          id: '4',
          name: 'Model Performance Monitoring Policy',
          category: 'model-governance',
          status: 'active',
          priority: 'high',
          description: 'Monitors model performance and triggers alerts for degradation',
          enforcement: 'automatic',
          lastUpdated: '2024-01-08',
          nextReview: '2024-03-08',
          complianceRate: 91,
          violations: 5,
          effectiveness: 89,
          rules: [
            {
              id: 'r5',
              name: 'Performance Degradation Alert',
              condition: 'IF accuracy < threshold * 0.9 THEN alert_team',
              action: 'Send alert to ML team for performance review',
              severity: 'high',
              status: 'active',
              triggers: 12,
              lastTriggered: '2024-01-20 13:20:00',
              successRate: 94.7
            }
          ]
        }
      ]

      const mockEvents: GovernanceEvent[] = [
        {
          id: '1',
          timestamp: '2024-01-20 16:15:00',
          type: 'policy-violation',
          severity: 'medium',
          description: 'Data retention policy violation detected for user dataset',
          affectedPolicy: 'Data Privacy Protection Policy',
          status: 'investigating',
          resolution: 'Under investigation by compliance team',
          automated: true
        },
        {
          id: '2',
          timestamp: '2024-01-20 15:30:00',
          type: 'rule-trigger',
          severity: 'low',
          description: 'Bias detection rule triggered for credit scoring model',
          affectedPolicy: 'Model Bias Detection Policy',
          status: 'resolved',
          resolution: 'Model reviewed and bias mitigation applied',
          automated: true
        },
        {
          id: '3',
          timestamp: '2024-01-20 14:45:00',
          type: 'compliance-check',
          severity: 'high',
          description: 'Automated compliance check completed for all active policies',
          affectedPolicy: 'All Policies',
          status: 'resolved',
          resolution: 'Compliance rate: 92.8% - within acceptable range',
          automated: true
        }
      ]

      setPolicies(mockPolicies)
      setEvents(mockEvents)
      
      const activePolicies = mockPolicies.filter(p => p.status === 'active').length
      const automatedPolicies = mockPolicies.filter(p => p.enforcement === 'automatic').length
      const avgCompliance = Math.round(mockPolicies.reduce((sum, p) => sum + p.complianceRate, 0) / mockPolicies.length)
      const avgEffectiveness = Math.round(mockPolicies.reduce((sum, p) => sum + p.effectiveness, 0) / mockPolicies.length)
      const totalViolations = mockPolicies.reduce((sum, p) => sum + p.violations, 0)

      setMetrics({
        totalPolicies: mockPolicies.length,
        activePolicies: activePolicies,
        automatedPolicies: automatedPolicies,
        complianceRate: avgCompliance,
        averageEffectiveness: avgEffectiveness,
        totalViolations: totalViolations,
        lastAudit: '2024-01-20 16:00:00',
        nextReview: '2024-02-20'
      })
      
      setLoading(false)
    }, 1000)

    return () => clearTimeout(timer)
  }, [])

  const filteredPolicies = policies.filter(policy => {
    const categoryMatch = selectedCategory === 'all' || policy.category === selectedCategory
    const statusMatch = selectedStatus === 'all' || policy.status === selectedStatus
    return categoryMatch && statusMatch
  })

  const getStatusColor = (status: string) => {
    switch (status) {
      case 'active': return 'text-green-400 bg-green-500/20'
      case 'draft': return 'text-blue-400 bg-blue-500/20'
      case 'review': return 'text-yellow-400 bg-yellow-500/20'
      case 'deprecated': return 'text-gray-400 bg-gray-500/20'
      case 'archived': return 'text-purple-400 bg-purple-500/20'
      default: return 'text-muted-foreground bg-muted'
    }
  }

  const getPriorityColor = (priority: string) => {
    switch (priority) {
      case 'critical': return 'text-red-400'
      case 'high': return 'text-orange-400'
      case 'medium': return 'text-yellow-400'
      case 'low': return 'text-blue-400'
      default: return 'text-muted-foreground'
    }
  }

  const getSeverityColor = (severity: string) => {
    switch (severity) {
      case 'critical': return 'text-red-400 bg-red-500/20'
      case 'high': return 'text-orange-400 bg-orange-500/20'
      case 'medium': return 'text-yellow-400 bg-yellow-500/20'
      case 'low': return 'text-blue-400 bg-blue-500/20'
      default: return 'text-muted-foreground bg-muted'
    }
  }

  const getCategoryIcon = (category: string) => {
    switch (category) {
      case 'data-privacy': return '🔒'
      case 'model-governance': return '🤖'
      case 'security': return '🛡️'
      case 'compliance': return '📋'
      case 'ethics': return '⚖️'
      case 'operational': return '⚙️'
      default: return '📋'
    }
  }

  const getEnforcementIcon = (enforcement: string) => {
    switch (enforcement) {
      case 'automatic': return '🤖'
      case 'manual': return '👤'
      case 'semi-automatic': return '🔄'
      default: return '⚙️'
    }
  }

  if (loading) {
    return (
      <div className="space-y-6 p-4 md:p-6 max-w-[2000px] mx-auto">
        <div className="space-y-2">
          <h1 className="text-2xl md:text-3xl font-bold tracking-tight text-gold">
            Adaptive Governance
          </h1>
          <p className="text-xs md:text-sm text-muted-foreground font-mono">
            Policy Management & Governance Automation
          </p>
        </div>
        <div className="flex items-center justify-center h-64">
          <div className="text-center">
            <div className="w-8 h-8 border-2 border-gold border-t-transparent rounded-full animate-spin mx-auto mb-4"></div>
            <p className="text-sm text-muted-foreground font-mono">Loading Adaptive Governance...</p>
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
          Adaptive Governance
        </h1>
        <p className="text-xs md:text-sm text-muted-foreground font-mono">
          Policy Management & Governance Automation
        </p>
      </div>

      {/* Governance Overview */}
      <div className="bg-card border border-border rounded-lg p-6">
        <div className="flex items-center justify-between mb-6">
          <div>
            <h2 className="text-xl font-bold text-foreground">Governance Overview</h2>
            <p className="text-sm text-muted-foreground font-mono">
              Automated policy management and compliance monitoring
            </p>
          </div>
          <div className="text-right">
            <div className="text-3xl font-bold text-gold">{metrics.complianceRate}%</div>
            <span className="text-sm text-muted-foreground font-mono">Compliance Rate</span>
          </div>
        </div>
        
        <div className="grid gap-4 sm:grid-cols-2 lg:grid-cols-4">
          <div className="text-center">
            <div className="text-2xl font-bold text-foreground">{metrics.totalPolicies}</div>
            <div className="text-xs text-muted-foreground font-mono">Total Policies</div>
          </div>
          <div className="text-center">
            <div className="text-2xl font-bold text-foreground">{metrics.activePolicies}</div>
            <div className="text-xs text-muted-foreground font-mono">Active Policies</div>
          </div>
          <div className="text-center">
            <div className="text-2xl font-bold text-foreground">{metrics.automatedPolicies}</div>
            <div className="text-xs text-muted-foreground font-mono">Automated Policies</div>
          </div>
          <div className="text-center">
            <div className="text-2xl font-bold text-foreground">{metrics.averageEffectiveness}%</div>
            <div className="text-xs text-muted-foreground font-mono">Avg Effectiveness</div>
          </div>
        </div>
      </div>

      {/* Governance Status */}
      <div className="grid gap-4 sm:grid-cols-2">
        <div className="bg-card border border-border rounded-lg p-4">
          <h3 className="font-bold text-foreground mb-2">Total Violations</h3>
          <div className="text-2xl font-bold text-gold">{metrics.totalViolations}</div>
          <p className="text-xs text-muted-foreground font-mono">Policy violations in last 30 days</p>
        </div>
        <div className="bg-card border border-border rounded-lg p-4">
          <h3 className="font-bold text-foreground mb-2">Next Review</h3>
          <div className="text-sm font-bold text-foreground">{metrics.nextReview}</div>
          <p className="text-xs text-muted-foreground font-mono">Scheduled policy review</p>
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
            <option value="data-privacy">Data Privacy</option>
            <option value="model-governance">Model Governance</option>
            <option value="security">Security</option>
            <option value="compliance">Compliance</option>
            <option value="ethics">Ethics</option>
            <option value="operational">Operational</option>
          </select>
          <select
            value={selectedStatus}
            onChange={(e) => setSelectedStatus(e.target.value)}
            className="px-3 py-1 text-sm bg-card border border-border rounded-md font-mono"
          >
            <option value="all">All Status</option>
            <option value="active">Active</option>
            <option value="draft">Draft</option>
            <option value="review">Review</option>
            <option value="deprecated">Deprecated</option>
            <option value="archived">Archived</option>
          </select>
        </div>
        <button className="px-4 py-2 bg-gold text-gold-foreground rounded-md font-mono text-sm hover:bg-gold/90 transition-colors">
          Create New Policy
        </button>
      </div>

      {/* Governance Policies */}
      <div className="space-y-4">
        <h2 className="text-xl font-bold text-foreground">Governance Policies</h2>
        
        <div className="grid gap-4">
          {filteredPolicies.map((policy) => (
            <div key={policy.id} className="bg-card border border-border rounded-lg p-6">
              <div className="flex items-start justify-between mb-4">
                <div className="flex-1">
                  <div className="flex items-center gap-3 mb-2">
                    <span className="text-2xl">{getCategoryIcon(policy.category)}</span>
                    <h3 className="text-lg font-bold text-foreground">{policy.name}</h3>
                    <span className={`inline-flex px-2 py-1 rounded text-xs font-mono ${getStatusColor(policy.status)}`}>
                      {policy.status.toUpperCase()}
                    </span>
                    <span className={`text-sm font-mono ${getPriorityColor(policy.priority)}`}>
                      {policy.priority.toUpperCase()}
                    </span>
                    <span className="text-sm font-mono text-muted-foreground">
                      {getEnforcementIcon(policy.enforcement)} {policy.enforcement}
                    </span>
                  </div>
                  <p className="text-sm text-muted-foreground font-mono mb-3">{policy.description}</p>
                  
                  <div className="grid gap-4 sm:grid-cols-2 lg:grid-cols-4 mb-4">
                    <div>
                      <span className="text-xs text-muted-foreground font-mono">Compliance</span>
                      <div className="text-lg font-bold text-green-400">{policy.complianceRate}%</div>
                    </div>
                    <div>
                      <span className="text-xs text-muted-foreground font-mono">Effectiveness</span>
                      <div className="text-lg font-bold text-blue-400">{policy.effectiveness}%</div>
                    </div>
                    <div>
                      <span className="text-xs text-muted-foreground font-mono">Violations</span>
                      <div className="text-lg font-bold text-orange-400">{policy.violations}</div>
                    </div>
                    <div>
                      <span className="text-xs text-muted-foreground font-mono">Rules</span>
                      <div className="text-sm font-bold text-foreground">{policy.rules.length}</div>
                    </div>
                  </div>
                </div>
              </div>

              {/* Policy Rules */}
              <div className="space-y-3 mb-4">
                <h4 className="text-sm font-bold text-foreground">Policy Rules</h4>
                {policy.rules.map((rule) => (
                  <div key={rule.id} className="border border-border rounded-lg p-4">
                    <div className="flex items-start justify-between mb-3">
                      <div className="flex-1">
                        <div className="flex items-center gap-2 mb-1">
                          <h5 className="text-sm font-bold text-foreground">{rule.name}</h5>
                          <span className={`inline-flex px-1 py-0.5 rounded text-xs font-mono ${getSeverityColor(rule.severity)}`}>
                            {rule.severity.toUpperCase()}
                          </span>
                          <span className={`text-xs font-mono ${
                            rule.status === 'active' ? 'text-green-400' : 
                            rule.status === 'inactive' ? 'text-gray-400' : 
                            'text-yellow-400'
                          }`}>
                            {rule.status.toUpperCase()}
                          </span>
                        </div>
                        <p className="text-xs text-muted-foreground font-mono mb-2">
                          <strong>Condition:</strong> {rule.condition}
                        </p>
                        <p className="text-xs text-muted-foreground font-mono mb-2">
                          <strong>Action:</strong> {rule.action}
                        </p>
                      </div>
                      <div className="text-right">
                        <div className="text-sm font-bold text-green-400">{rule.successRate}%</div>
                        <div className="text-xs text-muted-foreground font-mono">Success Rate</div>
                      </div>
                    </div>
                    
                    <div className="grid gap-2 sm:grid-cols-2">
                      <div>
                        <span className="text-xs text-muted-foreground font-mono">Triggers</span>
                        <div className="text-sm font-bold text-foreground">{rule.triggers}</div>
                      </div>
                      <div>
                        <span className="text-xs text-muted-foreground font-mono">Last Triggered</span>
                        <div className="text-sm font-bold text-foreground">{rule.lastTriggered}</div>
                      </div>
                    </div>
                  </div>
                ))}
              </div>
              
              <div className="flex items-center justify-between pt-4 border-t border-border">
                <div className="flex gap-4 text-xs text-muted-foreground font-mono">
                  <span>Category: {policy.category}</span>
                  <span>Enforcement: {policy.enforcement}</span>
                  <span>Next Review: {policy.nextReview}</span>
                </div>
                <div className="flex gap-2">
                  <button className="px-3 py-1 text-xs bg-card border border-border rounded font-mono hover:bg-accent transition-colors">
                    Edit Policy
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

      {/* Governance Events */}
      <div className="space-y-4">
        <h2 className="text-xl font-bold text-foreground">Governance Events</h2>
        
        <div className="grid gap-4">
          {events.map((event) => (
            <div key={event.id} className="bg-card border border-border rounded-lg p-6">
              <div className="flex items-start justify-between mb-4">
                <div className="flex-1">
                  <div className="flex items-center gap-3 mb-2">
                    <h3 className="text-lg font-bold text-foreground">
                      {event.type.replace('-', ' ').toUpperCase()}
                    </h3>
                    <span className={`inline-flex px-2 py-1 rounded text-xs font-mono ${getSeverityColor(event.severity)}`}>
                      {event.severity.toUpperCase()}
                    </span>
                    <span className={`text-sm font-mono ${
                      event.status === 'resolved' ? 'text-green-400' : 
                      event.status === 'open' ? 'text-red-400' : 
                      'text-yellow-400'
                    }`}>
                      {event.status.toUpperCase()}
                    </span>
                    <span className="text-sm font-mono text-muted-foreground">
                      {event.automated ? '🤖 Automated' : '👤 Manual'}
                    </span>
                  </div>
                  <p className="text-sm text-muted-foreground font-mono mb-3">{event.description}</p>
                  
                  <div className="grid gap-4 sm:grid-cols-2 mb-4">
                    <div>
                      <span className="text-xs text-muted-foreground font-mono">Affected Policy</span>
                      <div className="text-sm font-bold text-foreground">{event.affectedPolicy}</div>
                    </div>
                    <div>
                      <span className="text-xs text-muted-foreground font-mono">Timestamp</span>
                      <div className="text-sm font-bold text-foreground">{event.timestamp}</div>
                    </div>
                  </div>
                </div>
              </div>

              <div className="mb-4">
                <h4 className="text-sm font-bold text-foreground mb-2">Resolution</h4>
                <p className="text-sm text-muted-foreground font-mono">{event.resolution}</p>
              </div>
              
              <div className="flex items-center justify-between pt-4 border-t border-border">
                <div className="text-xs text-muted-foreground font-mono">
                  Event ID: {event.id}
                </div>
                <div className="flex gap-2">
                  <button className="px-3 py-1 text-xs bg-card border border-border rounded font-mono hover:bg-accent transition-colors">
                    Update Status
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
