'use client'

import React, { useState, useEffect } from 'react'

interface ReadinessDimension {
  id: string
  name: string
  description: string
  score: number
  maxScore: number
  status: 'not-started' | 'in-progress' | 'completed' | 'excellent'
  priority: 'low' | 'medium' | 'high' | 'critical'
  recommendations: string[]
  lastAssessed: string
}

interface ReadinessMetrics {
  overallScore: number
  totalDimensions: number
  completedDimensions: number
  criticalGaps: number
  readinessLevel: 'beginner' | 'developing' | 'intermediate' | 'advanced' | 'expert'
  nextMilestone: string
  estimatedTimeline: string
}

export default function AIReadinessAssessment() {
  const [loading, setLoading] = useState(true)
  const [dimensions, setDimensions] = useState<ReadinessDimension[]>([])
  const [metrics, setMetrics] = useState<ReadinessMetrics>({
    overallScore: 0,
    totalDimensions: 0,
    completedDimensions: 0,
    criticalGaps: 0,
    readinessLevel: 'beginner',
    nextMilestone: '',
    estimatedTimeline: ''
  })

  useEffect(() => {
    const timer = setTimeout(() => {
      const mockDimensions: ReadinessDimension[] = [
        {
          id: '1',
          name: 'Data Infrastructure',
          description: 'Quality, availability, and governance of data assets',
          score: 75,
          maxScore: 100,
          status: 'completed',
          priority: 'high',
          recommendations: ['Implement data quality monitoring', 'Establish data lineage tracking'],
          lastAssessed: '2024-01-15'
        },
        {
          id: '2',
          name: 'Technology Stack',
          description: 'AI/ML platforms, tools, and technical capabilities',
          score: 60,
          maxScore: 100,
          status: 'in-progress',
          priority: 'critical',
          recommendations: ['Upgrade ML infrastructure', 'Implement MLOps pipeline'],
          lastAssessed: '2024-01-12'
        },
        {
          id: '3',
          name: 'Talent & Skills',
          description: 'AI expertise, training programs, and organizational knowledge',
          score: 45,
          maxScore: 100,
          status: 'in-progress',
          priority: 'high',
          recommendations: ['Hire senior AI engineers', 'Develop internal training program'],
          lastAssessed: '2024-01-10'
        }
      ]

      setDimensions(mockDimensions)
      
      const totalScore = mockDimensions.reduce((sum, d) => sum + d.score, 0)
      const avgScore = Math.round(totalScore / mockDimensions.length)
      const completed = mockDimensions.filter(d => d.status === 'completed' || d.status === 'excellent').length
      const critical = mockDimensions.filter(d => d.priority === 'critical').length

      let readinessLevel: ReadinessMetrics['readinessLevel'] = 'beginner'
      if (avgScore >= 80) readinessLevel = 'expert'
      else if (avgScore >= 65) readinessLevel = 'advanced'
      else if (avgScore >= 50) readinessLevel = 'intermediate'
      else if (avgScore >= 35) readinessLevel = 'developing'

      setMetrics({
        overallScore: avgScore,
        totalDimensions: mockDimensions.length,
        completedDimensions: completed,
        criticalGaps: critical,
        readinessLevel,
        nextMilestone: 'Achieve 75% overall readiness score',
        estimatedTimeline: '6-8 months'
      })
      
      setLoading(false)
    }, 1000)

    return () => clearTimeout(timer)
  }, [])

  const getStatusColor = (status: string) => {
    switch (status) {
      case 'excellent': return 'text-green-400 bg-green-500/20'
      case 'completed': return 'text-blue-400 bg-blue-500/20'
      case 'in-progress': return 'text-yellow-400 bg-yellow-500/20'
      case 'not-started': return 'text-gray-400 bg-gray-500/20'
      default: return 'text-muted-foreground bg-muted'
    }
  }

  const getPriorityColor = (priority: string) => {
    switch (priority) {
      case 'critical': return 'text-red-400'
      case 'high': return 'text-orange-400'
      case 'medium': return 'text-yellow-400'
      case 'low': return 'text-green-400'
      default: return 'text-muted-foreground'
    }
  }

  const getReadinessLevelColor = (level: string) => {
    switch (level) {
      case 'expert': return 'text-green-400 bg-green-500/20'
      case 'advanced': return 'text-blue-400 bg-blue-500/20'
      case 'intermediate': return 'text-yellow-400 bg-yellow-500/20'
      case 'developing': return 'text-orange-400 bg-orange-500/20'
      case 'beginner': return 'text-red-400 bg-red-500/20'
      default: return 'text-muted-foreground bg-muted'
    }
  }

  const getProgressColor = (score: number) => {
    if (score >= 80) return 'bg-green-500'
    if (score >= 60) return 'bg-blue-500'
    if (score >= 40) return 'bg-yellow-500'
    return 'bg-red-500'
  }

  if (loading) {
    return (
      <div className="space-y-6 p-4 md:p-6 max-w-[2000px] mx-auto">
        <div className="space-y-2">
          <h1 className="text-2xl md:text-3xl font-bold tracking-tight text-gold">
            AI Readiness Assessment
          </h1>
          <p className="text-xs md:text-sm text-muted-foreground font-mono">
            Organizational AI Capability & Maturity Evaluation
          </p>
        </div>
        <div className="flex items-center justify-center h-64">
          <div className="text-center">
            <div className="w-8 h-8 border-2 border-gold border-t-transparent rounded-full animate-spin mx-auto mb-4"></div>
            <p className="text-sm text-muted-foreground font-mono">Evaluating AI Readiness...</p>
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
          AI Readiness Assessment
        </h1>
        <p className="text-xs md:text-sm text-muted-foreground font-mono">
          Organizational AI Capability & Maturity Evaluation
        </p>
      </div>

      {/* Overall Assessment */}
      <div className="bg-card border border-border rounded-lg p-6">
        <div className="flex items-center justify-between mb-6">
          <div>
            <h2 className="text-xl font-bold text-foreground">Overall AI Readiness</h2>
            <p className="text-sm text-muted-foreground font-mono">
              Comprehensive evaluation of organizational AI capabilities
            </p>
          </div>
          <div className="text-right">
            <div className="text-3xl font-bold text-gold">{metrics.overallScore}%</div>
            <span className={`inline-flex px-3 py-1 rounded-full text-xs font-mono ${getReadinessLevelColor(metrics.readinessLevel)}`}>
              {metrics.readinessLevel.toUpperCase()}
            </span>
          </div>
        </div>
        
        <div className="w-full bg-muted rounded-full h-3 mb-4">
          <div 
            className={`h-3 rounded-full transition-all duration-500 ${getProgressColor(metrics.overallScore)}`}
            style={{ width: `${metrics.overallScore}%` }}
          ></div>
        </div>
        
        <div className="grid gap-4 sm:grid-cols-2 lg:grid-cols-4">
          <div className="text-center">
            <div className="text-2xl font-bold text-foreground">{metrics.totalDimensions}</div>
            <div className="text-xs text-muted-foreground font-mono">Dimensions</div>
          </div>
          <div className="text-center">
            <div className="text-2xl font-bold text-foreground">{metrics.completedDimensions}</div>
            <div className="text-xs text-muted-foreground font-mono">Completed</div>
          </div>
          <div className="text-center">
            <div className="text-2xl font-bold text-foreground">{metrics.criticalGaps}</div>
            <div className="text-xs text-muted-foreground font-mono">Critical Gaps</div>
          </div>
          <div className="text-center">
            <div className="text-2xl font-bold text-foreground">{metrics.estimatedTimeline}</div>
            <div className="text-xs text-muted-foreground font-mono">Timeline</div>
          </div>
        </div>
      </div>

      {/* Readiness Dimensions */}
      <div className="space-y-4">
        <div className="flex items-center justify-between">
          <h2 className="text-xl font-bold text-foreground">Readiness Dimensions</h2>
          <button className="px-4 py-2 bg-gold text-gold-foreground rounded-md font-mono text-sm hover:bg-gold/90 transition-colors">
            Update Assessment
          </button>
        </div>

        <div className="grid gap-4">
          {dimensions.map((dimension) => (
            <div key={dimension.id} className="bg-card border border-border rounded-lg p-6">
              <div className="flex items-start justify-between mb-4">
                <div className="flex-1">
                  <div className="flex items-center gap-3 mb-2">
                    <h3 className="text-lg font-bold text-foreground">{dimension.name}</h3>
                    <span className={`inline-flex px-2 py-1 rounded text-xs font-mono ${getStatusColor(dimension.status)}`}>
                      {dimension.status.replace('-', ' ').toUpperCase()}
                    </span>
                    <span className={`text-sm font-mono ${getPriorityColor(dimension.priority)}`}>
                      {dimension.priority.toUpperCase()} PRIORITY
                    </span>
                  </div>
                  <p className="text-sm text-muted-foreground font-mono mb-3">{dimension.description}</p>
                  
                  <div className="flex items-center gap-4 mb-4">
                    <div className="flex items-center gap-2">
                      <span className="text-sm font-mono">Score:</span>
                      <span className="text-lg font-bold text-foreground">{dimension.score}/{dimension.maxScore}</span>
                    </div>
                    <div className="flex-1 max-w-xs">
                      <div className="w-full bg-muted rounded-full h-2">
                        <div 
                          className={`h-2 rounded-full transition-all duration-500 ${getProgressColor(dimension.score)}`}
                          style={{ width: `${(dimension.score / dimension.maxScore) * 100}%` }}
                        ></div>
                      </div>
                    </div>
                  </div>
                </div>
              </div>

              <div className="space-y-3">
                <div>
                  <h4 className="text-sm font-bold text-foreground mb-2">Key Recommendations</h4>
                  <ul className="space-y-1">
                    {dimension.recommendations.map((rec, index) => (
                      <li key={index} className="text-sm text-muted-foreground font-mono flex items-start gap-2">
                        <span className="text-gold mt-1">•</span>
                        {rec}
                      </li>
                    ))}
                  </ul>
                </div>
                
                <div className="flex items-center justify-between pt-3 border-t border-border">
                  <span className="text-xs text-muted-foreground font-mono">
                    Last assessed: {dimension.lastAssessed}
                  </span>
                  <div className="flex gap-2">
                    <button className="px-3 py-1 text-xs bg-card border border-border rounded font-mono hover:bg-accent transition-colors">
                      View Details
                    </button>
                    <button className="px-3 py-1 text-xs bg-card border border-border rounded font-mono hover:bg-accent transition-colors">
                      Update Score
                    </button>
                  </div>
                </div>
              </div>
            </div>
          ))}
        </div>
      </div>
    </div>
  )
}
