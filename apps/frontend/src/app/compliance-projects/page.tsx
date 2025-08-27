'use client'

import React, { useState, useEffect } from 'react'

interface ComplianceProject {
  id: string
  name: string
  type: 'implementation' | 'assessment' | 'remediation' | 'audit' | 'training' | 'documentation'
  priority: 'critical' | 'high' | 'medium' | 'low'
  status: 'planning' | 'in-progress' | 'review' | 'completed' | 'on-hold' | 'cancelled'
  description: string
  framework: string
  owner: string
  team: string[]
  startDate: string
  dueDate: string
  completionDate?: string
  progress: number
  budget: number
  actualCost: number
  tasks: ProjectTask[]
  risks: ProjectRisk[]
  milestones: ProjectMilestone[]
}

interface ProjectTask {
  id: string
  name: string
  description: string
  assignee: string
  status: 'not-started' | 'in-progress' | 'review' | 'completed' | 'blocked'
  priority: 'critical' | 'high' | 'medium' | 'low'
  estimatedHours: number
  actualHours: number
  startDate: string
  dueDate: string
  completionDate?: string
  dependencies: string[]
}

interface ProjectRisk {
  id: string
  name: string
  description: string
  probability: 'low' | 'medium' | 'high'
  impact: 'low' | 'medium' | 'high'
  status: 'open' | 'mitigated' | 'accepted' | 'closed'
  mitigation: string
  owner: string
  lastUpdated: string
}

interface ProjectMilestone {
  id: string
  name: string
  description: string
  dueDate: string
  status: 'upcoming' | 'in-progress' | 'completed' | 'overdue'
  deliverables: string[]
  completionDate?: string
}

interface ComplianceMetrics {
  totalProjects: number
  activeProjects: number
  completedProjects: number
  averageProgress: number
  overdueProjects: number
  totalBudget: number
  actualSpend: number
  lastUpdate: string
  nextReview: string
}

export default function ComplianceProjects() {
  const [loading, setLoading] = useState(true)
  const [projects, setProjects] = useState<ComplianceProject[]>([])
  const [metrics, setMetrics] = useState<ComplianceMetrics>({
    totalProjects: 0,
    activeProjects: 0,
    completedProjects: 0,
    averageProgress: 0,
    overdueProjects: 0,
    totalBudget: 0,
    actualSpend: 0,
    lastUpdate: '',
    nextReview: ''
  })
  const [selectedType, setSelectedType] = useState<string>('all')
  const [selectedStatus, setSelectedStatus] = useState<string>('all')

  useEffect(() => {
    const timer = setTimeout(() => {
      const mockProjects: ComplianceProject[] = [
        {
          id: '1',
          name: 'GDPR Implementation Project',
          type: 'implementation',
          priority: 'critical',
          status: 'in-progress',
          description: 'Implement comprehensive GDPR compliance across all systems and processes',
          framework: 'GDPR',
          owner: 'Sarah Johnson',
          team: ['Legal Team', 'IT Team', 'Data Team'],
          startDate: '2024-01-01',
          dueDate: '2024-06-30',
          progress: 65,
          budget: 150000,
          actualCost: 95000,
          tasks: [
            {
              id: 'task1',
              name: 'Data Inventory Assessment',
              description: 'Complete comprehensive data inventory across all systems',
              assignee: 'Mike Chen',
              status: 'completed',
              priority: 'high',
              estimatedHours: 80,
              actualHours: 75,
              startDate: '2024-01-01',
              dueDate: '2024-02-15',
              completionDate: '2024-02-10',
              dependencies: []
            },
            {
              id: 'task2',
              name: 'Privacy Policy Updates',
              description: 'Update privacy policies to meet GDPR requirements',
              assignee: 'Lisa Wang',
              status: 'in-progress',
              priority: 'high',
              estimatedHours: 60,
              actualHours: 35,
              startDate: '2024-02-01',
              dueDate: '2024-03-15',
              dependencies: ['task1']
            }
          ],
          risks: [
            {
              id: 'risk1',
              name: 'Data Subject Rights Implementation Delay',
              description: 'Risk of delays in implementing automated data subject rights processes',
              probability: 'medium',
              impact: 'high',
              status: 'open',
              mitigation: 'Engage external consultants for technical implementation',
              owner: 'Sarah Johnson',
              lastUpdated: '2024-01-20'
            }
          ],
          milestones: [
            {
              id: 'milestone1',
              name: 'Data Inventory Complete',
              description: 'Complete data inventory and mapping exercise',
              dueDate: '2024-02-15',
              status: 'completed',
              deliverables: ['Data inventory report', 'Data flow diagrams', 'Processing register'],
              completionDate: '2024-02-10'
            },
            {
              id: 'milestone2',
              name: 'Privacy Policy Implementation',
              description: 'Implement updated privacy policies and consent mechanisms',
              dueDate: '2024-03-15',
              status: 'in-progress',
              deliverables: ['Updated privacy policy', 'Consent management system', 'User interface updates']
            }
          ]
        },
        {
          id: '2',
          name: 'EU AI Act Compliance Assessment',
          type: 'assessment',
          priority: 'high',
          status: 'planning',
          description: 'Assess current AI systems against EU AI Act requirements',
          framework: 'EU AI Act',
          owner: 'David Rodriguez',
          team: ['AI Team', 'Compliance Team', 'Legal Team'],
          startDate: '2024-02-01',
          dueDate: '2024-05-31',
          progress: 15,
          budget: 75000,
          actualCost: 12000,
          tasks: [
            {
              id: 'task3',
              name: 'AI System Classification',
              description: 'Classify all AI systems according to EU AI Act risk levels',
              assignee: 'Alex Thompson',
              status: 'in-progress',
              priority: 'critical',
              estimatedHours: 40,
              actualHours: 20,
              startDate: '2024-02-01',
              dueDate: '2024-03-01',
              dependencies: []
            }
          ],
          risks: [
            {
              id: 'risk2',
              name: 'High-Risk Classification',
              description: 'Risk that existing AI systems may be classified as high-risk',
              probability: 'high',
              impact: 'high',
              status: 'open',
              mitigation: 'Prepare compliance roadmap for high-risk systems',
              owner: 'David Rodriguez',
              lastUpdated: '2024-01-25'
            }
          ],
          milestones: [
            {
              id: 'milestone3',
              name: 'System Classification Complete',
              description: 'Complete classification of all AI systems',
              dueDate: '2024-03-01',
              status: 'in-progress',
              deliverables: ['Classification report', 'Risk assessment', 'Compliance gap analysis']
            }
          ]
        },
        {
          id: '3',
          name: 'Security Framework Implementation',
          type: 'implementation',
          priority: 'high',
          status: 'completed',
          description: 'Implement NIST cybersecurity framework across organization',
          framework: 'NIST CSF',
          owner: 'Jennifer Lee',
          team: ['Security Team', 'IT Team'],
          startDate: '2023-09-01',
          dueDate: '2024-01-31',
          completionDate: '2024-01-25',
          progress: 100,
          budget: 200000,
          actualCost: 185000,
          tasks: [
            {
              id: 'task4',
              name: 'Security Controls Implementation',
              description: 'Implement security controls across all systems',
              assignee: 'Jennifer Lee',
              status: 'completed',
              priority: 'critical',
              estimatedHours: 200,
              actualHours: 190,
              startDate: '2023-09-01',
              dueDate: '2024-01-31',
              completionDate: '2024-01-25',
              dependencies: []
            }
          ],
          risks: [],
          milestones: [
            {
              id: 'milestone4',
              name: 'Framework Implementation Complete',
              description: 'Complete implementation of NIST CSF framework',
              dueDate: '2024-01-31',
              status: 'completed',
              deliverables: ['Security controls documentation', 'Training materials', 'Audit report'],
              completionDate: '2024-01-25'
            }
          ]
        }
      ]

      setProjects(mockProjects)
      
      const activeProjects = mockProjects.filter(p => p.status === 'in-progress' || p.status === 'planning').length
      const completedProjects = mockProjects.filter(p => p.status === 'completed').length
      const avgProgress = Math.round(mockProjects.reduce((sum, p) => sum + p.progress, 0) / mockProjects.length)
      const overdueProjects = mockProjects.filter(p => {
        if (p.status === 'completed') return false
        const dueDate = new Date(p.dueDate)
        const today = new Date()
        return dueDate < today
      }).length
      const totalBudget = mockProjects.reduce((sum, p) => sum + p.budget, 0)
      const actualSpend = mockProjects.reduce((sum, p) => sum + p.actualCost, 0)

      setMetrics({
        totalProjects: mockProjects.length,
        activeProjects: activeProjects,
        completedProjects: completedProjects,
        averageProgress: avgProgress,
        overdueProjects: overdueProjects,
        totalBudget: totalBudget,
        actualSpend: actualSpend,
        lastUpdate: '2024-01-20 16:00:00',
        nextReview: '2024-02-20'
      })
      
      setLoading(false)
    }, 1000)

    return () => clearTimeout(timer)
  }, [])

  const filteredProjects = projects.filter(project => {
    const typeMatch = selectedType === 'all' || project.type === selectedType
    const statusMatch = selectedStatus === 'all' || project.status === selectedStatus
    return typeMatch && statusMatch
  })

  const getStatusColor = (status: string) => {
    switch (status) {
      case 'completed': return 'text-green-400 bg-green-500/20'
      case 'in-progress': return 'text-blue-400 bg-blue-500/20'
      case 'planning': return 'text-yellow-400 bg-yellow-500/20'
      case 'review': return 'text-purple-400 bg-purple-500/20'
      case 'on-hold': return 'text-gray-400 bg-gray-500/20'
      case 'cancelled': return 'text-red-400 bg-red-500/20'
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

  const getTaskStatusColor = (status: string) => {
    switch (status) {
      case 'completed': return 'text-green-400 bg-green-500/20'
      case 'in-progress': return 'text-blue-400 bg-blue-500/20'
      case 'review': return 'text-purple-400 bg-purple-500/20'
      case 'blocked': return 'text-red-400 bg-red-500/20'
      case 'not-started': return 'text-gray-400 bg-gray-500/20'
      default: return 'text-muted-foreground bg-muted'
    }
  }

  const getRiskColor = (probability: string, impact: string) => {
    if (probability === 'high' && impact === 'high') return 'text-red-400 bg-red-500/20'
    if (probability === 'high' || impact === 'high') return 'text-orange-400 bg-orange-500/20'
    if (probability === 'medium' && impact === 'medium') return 'text-yellow-400 bg-yellow-500/20'
    return 'text-blue-400 bg-blue-500/20'
  }

  const getMilestoneStatusColor = (status: string) => {
    switch (status) {
      case 'completed': return 'text-green-400 bg-green-500/20'
      case 'in-progress': return 'text-blue-400 bg-blue-500/20'
      case 'overdue': return 'text-red-400 bg-red-500/20'
      case 'upcoming': return 'text-gray-400 bg-gray-500/20'
      default: return 'text-muted-foreground bg-muted'
    }
  }

  const getTypeIcon = (type: string) => {
    switch (type) {
      case 'implementation': return '🚀'
      case 'assessment': return '📋'
      case 'remediation': return '🔧'
      case 'audit': return '🔍'
      case 'training': return '🎓'
      case 'documentation': return '📚'
      default: return '📋'
    }
  }

  if (loading) {
    return (
      <div className="space-y-6 p-4 md:p-6 max-w-[2000px] mx-auto">
        <div className="space-y-2">
          <h1 className="text-2xl md:text-3xl font-bold tracking-tight text-gold">
            Compliance Projects
          </h1>
          <p className="text-xs md:text-sm text-muted-foreground font-mono">
            Project Management for Compliance Initiatives
          </p>
        </div>
        <div className="flex items-center justify-center h-64">
          <div className="text-center">
            <div className="w-8 h-8 border-2 border-gold border-t-transparent rounded-full animate-spin mx-auto mb-4"></div>
            <p className="text-sm text-muted-foreground font-mono">Loading Compliance Projects...</p>
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
          Compliance Projects
        </h1>
        <p className="text-xs md:text-sm text-muted-foreground font-mono">
          Project Management for Compliance Initiatives
        </p>
      </div>

      {/* Project Overview */}
      <div className="bg-card border border-border rounded-lg p-6">
        <div className="flex items-center justify-between mb-6">
          <div>
            <h2 className="text-xl font-bold text-foreground">Project Overview</h2>
            <p className="text-sm text-muted-foreground font-mono">
              Compliance project management and tracking
            </p>
          </div>
          <div className="text-right">
            <div className="text-3xl font-bold text-gold">{metrics.averageProgress}%</div>
            <span className="text-sm text-muted-foreground font-mono">Average Progress</span>
          </div>
        </div>
        
        <div className="grid gap-4 sm:grid-cols-2 lg:grid-cols-4">
          <div className="text-center">
            <div className="text-2xl font-bold text-foreground">{metrics.totalProjects}</div>
            <div className="text-xs text-muted-foreground font-mono">Total Projects</div>
          </div>
          <div className="text-center">
            <div className="text-2xl font-bold text-foreground">{metrics.activeProjects}</div>
            <div className="text-xs text-muted-foreground font-mono">Active Projects</div>
          </div>
          <div className="text-center">
            <div className="text-2xl font-bold text-foreground">{metrics.completedProjects}</div>
            <div className="text-xs text-muted-foreground font-mono">Completed Projects</div>
          </div>
          <div className="text-center">
            <div className="text-2xl font-bold text-foreground">{metrics.overdueProjects}</div>
            <div className="text-xs text-muted-foreground font-mono">Overdue Projects</div>
          </div>
        </div>
      </div>

      {/* Budget Overview */}
      <div className="grid gap-4 sm:grid-cols-2">
        <div className="bg-card border border-border rounded-lg p-4">
          <h3 className="font-bold text-foreground mb-2">Budget Overview</h3>
          <div className="space-y-2">
            <div className="flex justify-between">
              <span className="text-sm text-muted-foreground font-mono">Total Budget</span>
              <span className="text-sm font-bold text-foreground">${metrics.totalBudget.toLocaleString()}</span>
            </div>
            <div className="flex justify-between">
              <span className="text-sm text-muted-foreground font-mono">Actual Spend</span>
              <span className="text-sm font-bold text-foreground">${metrics.actualSpend.toLocaleString()}</span>
            </div>
            <div className="flex justify-between">
              <span className="text-sm text-muted-foreground font-mono">Remaining</span>
              <span className="text-sm font-bold text-foreground">${(metrics.totalBudget - metrics.actualSpend).toLocaleString()}</span>
            </div>
          </div>
        </div>
        <div className="bg-card border border-border rounded-lg p-4">
          <h3 className="font-bold text-foreground mb-2">Next Review</h3>
          <div className="text-sm font-bold text-foreground">{metrics.nextReview}</div>
          <p className="text-xs text-muted-foreground font-mono">Scheduled project review</p>
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
            <option value="implementation">Implementation</option>
            <option value="assessment">Assessment</option>
            <option value="remediation">Remediation</option>
            <option value="audit">Audit</option>
            <option value="training">Training</option>
            <option value="documentation">Documentation</option>
          </select>
          <select
            value={selectedStatus}
            onChange={(e) => setSelectedStatus(e.target.value)}
            className="px-3 py-1 text-sm bg-card border border-border rounded-md font-mono"
          >
            <option value="all">All Status</option>
            <option value="planning">Planning</option>
            <option value="in-progress">In Progress</option>
            <option value="review">Review</option>
            <option value="completed">Completed</option>
            <option value="on-hold">On Hold</option>
            <option value="cancelled">Cancelled</option>
          </select>
        </div>
        <button className="px-4 py-2 bg-gold text-gold-foreground rounded-md font-mono text-sm hover:bg-gold/90 transition-colors">
          Create New Project
        </button>
      </div>

      {/* Compliance Projects */}
      <div className="space-y-4">
        <h2 className="text-xl font-bold text-foreground">Compliance Projects</h2>
        
        <div className="grid gap-4">
          {filteredProjects.map((project) => (
            <div key={project.id} className="bg-card border border-border rounded-lg p-6">
              <div className="flex items-start justify-between mb-4">
                <div className="flex-1">
                  <div className="flex items-center gap-3 mb-2">
                    <span className="text-2xl">{getTypeIcon(project.type)}</span>
                    <h3 className="text-lg font-bold text-foreground">{project.name}</h3>
                    <span className={`inline-flex px-2 py-1 rounded text-xs font-mono ${getStatusColor(project.status)}`}>
                      {project.status.replace('-', ' ').toUpperCase()}
                    </span>
                    <span className={`text-sm font-mono ${getPriorityColor(project.priority)}`}>
                      {project.priority.toUpperCase()}
                    </span>
                  </div>
                  <p className="text-sm text-muted-foreground font-mono mb-3">{project.description}</p>
                  
                  <div className="grid gap-4 sm:grid-cols-2 lg:grid-cols-4 mb-4">
                    <div>
                      <span className="text-xs text-muted-foreground font-mono">Framework</span>
                      <div className="text-sm font-bold text-foreground">{project.framework}</div>
                    </div>
                    <div>
                      <span className="text-xs text-muted-foreground font-mono">Owner</span>
                      <div className="text-sm font-bold text-foreground">{project.owner}</div>
                    </div>
                    <div>
                      <span className="text-xs text-muted-foreground font-mono">Progress</span>
                      <div className="text-lg font-bold text-green-400">{project.progress}%</div>
                    </div>
                    <div>
                      <span className="text-xs text-muted-foreground font-mono">Due Date</span>
                      <div className="text-sm font-bold text-foreground">{project.dueDate}</div>
                    </div>
                  </div>

                  {/* Progress Bar */}
                  <div className="w-full bg-muted rounded-full h-2 mb-4">
                    <div 
                      className="bg-gold h-2 rounded-full transition-all duration-300"
                      style={{ width: `${project.progress}%` }}
                    ></div>
                  </div>
                </div>
              </div>

              {/* Tasks */}
              <div className="space-y-3 mb-4">
                <h4 className="text-sm font-bold text-foreground">Project Tasks</h4>
                <div className="grid gap-3">
                  {project.tasks.map((task) => (
                    <div key={task.id} className="border border-border rounded-lg p-3">
                      <div className="flex items-start justify-between mb-2">
                        <div className="flex-1">
                          <div className="flex items-center gap-2 mb-1">
                            <h5 className="text-sm font-bold text-foreground">{task.name}</h5>
                            <span className={`inline-flex px-1 py-0.5 rounded text-xs font-mono ${getTaskStatusColor(task.status)}`}>
                              {task.status.replace('-', ' ').toUpperCase()}
                            </span>
                            <span className="text-xs font-mono text-muted-foreground">{task.assignee}</span>
                          </div>
                          <p className="text-xs text-muted-foreground font-mono mb-2">{task.description}</p>
                        </div>
                        <div className="text-right">
                          <div className="text-sm font-bold text-foreground">{task.actualHours}h / {task.estimatedHours}h</div>
                          <div className="text-xs text-muted-foreground font-mono">Hours</div>
                        </div>
                      </div>
                      <div className="grid gap-2 sm:grid-cols-2 text-xs text-muted-foreground font-mono">
                        <div>Due: {task.dueDate}</div>
                        {task.completionDate && <div>Completed: {task.completionDate}</div>}
                      </div>
                    </div>
                  ))}
                </div>
              </div>

              {/* Risks */}
              {project.risks.length > 0 && (
                <div className="space-y-3 mb-4">
                  <h4 className="text-sm font-bold text-foreground">Project Risks</h4>
                  <div className="grid gap-3">
                    {project.risks.map((risk) => (
                      <div key={risk.id} className="border border-border rounded-lg p-3">
                        <div className="flex items-start justify-between mb-2">
                          <div className="flex-1">
                            <div className="flex items-center gap-2 mb-1">
                              <h5 className="text-sm font-bold text-foreground">{risk.name}</h5>
                              <span className={`inline-flex px-1 py-0.5 rounded text-xs font-mono ${getRiskColor(risk.probability, risk.impact)}`}>
                                {risk.probability.toUpperCase()} / {risk.impact.toUpperCase()}
                              </span>
                              <span className="text-xs font-mono text-muted-foreground">{risk.status}</span>
                            </div>
                            <p className="text-xs text-muted-foreground font-mono mb-2">{risk.description}</p>
                            <p className="text-xs text-muted-foreground font-mono">
                              <strong>Mitigation:</strong> {risk.mitigation}
                            </p>
                          </div>
                        </div>
                        <div className="text-xs text-muted-foreground font-mono">
                          Owner: {risk.owner} | Updated: {risk.lastUpdated}
                        </div>
                      </div>
                    ))}
                  </div>
                </div>
              )}

              {/* Milestones */}
              <div className="space-y-3 mb-4">
                <h4 className="text-sm font-bold text-foreground">Project Milestones</h4>
                <div className="grid gap-3">
                  {project.milestones.map((milestone) => (
                    <div key={milestone.id} className="border border-border rounded-lg p-3">
                      <div className="flex items-start justify-between mb-2">
                        <div className="flex-1">
                          <div className="flex items-center gap-2 mb-1">
                            <h5 className="text-sm font-bold text-foreground">{milestone.name}</h5>
                            <span className={`inline-flex px-1 py-0.5 rounded text-xs font-mono ${getMilestoneStatusColor(milestone.status)}`}>
                              {milestone.status.toUpperCase()}
                            </span>
                          </div>
                          <p className="text-xs text-muted-foreground font-mono mb-2">{milestone.description}</p>
                          <div className="text-xs text-muted-foreground font-mono">
                            <strong>Deliverables:</strong> {milestone.deliverables.join(', ')}
                          </div>
                        </div>
                      </div>
                      <div className="text-xs text-muted-foreground font-mono">
                        Due: {milestone.dueDate}
                        {milestone.completionDate && ` | Completed: ${milestone.completionDate}`}
                      </div>
                    </div>
                  ))}
                </div>
              </div>
              
              <div className="flex items-center justify-between pt-4 border-t border-border">
                <div className="flex gap-4 text-xs text-muted-foreground font-mono">
                  <span>Type: {project.type}</span>
                  <span>Team: {project.team.join(', ')}</span>
                  <span>Budget: ${project.budget.toLocaleString()}</span>
                </div>
                <div className="flex gap-2">
                  <button className="px-3 py-1 text-xs bg-card border border-border rounded font-mono hover:bg-accent transition-colors">
                    Update Project
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
