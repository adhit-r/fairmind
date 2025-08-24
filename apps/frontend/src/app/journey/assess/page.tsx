"use client"

import { useState } from 'react'
import { useRouter } from 'next/navigation'
import {
  NeoContainer,
  NeoGrid,
  NeoHeading,
  NeoText,
  NeoAlert,
  NeoCard,
  NeoButton,
  NeoBadge,
  NeoProgress
} from "@/components/ui/common/neo-components"
import {
  Target,
  Shield,
  CheckCircle,
  AlertTriangle,
  Upload,
  Play,
  ArrowRight,
  Eye,
  BarChart3,
  Zap,
  Brain,
  Database,
  TestTube,
  ExternalLink
} from 'lucide-react'

export default function AssessPage() {
  const router = useRouter()
  const [currentAssessment, setCurrentAssessment] = useState('bias')
  const [assessmentResults, setAssessmentResults] = useState({
    bias: { completed: false, score: 0, issues: [] },
    security: { completed: false, score: 0, issues: [] },
    compliance: { completed: false, score: 0, issues: [] }
  })

  const assessments = [
    {
      id: 'bias',
      title: 'Bias Detection',
      description: 'Test your models for bias against protected groups',
      icon: <Target className="h-6 w-6" />,
      color: 'bg-red-500',
      estimatedTime: '5 min',
      tests: [
        'Statistical Parity Difference',
        'Equal Opportunity Difference',
        'Demographic Parity',
        'Individual Fairness',
        'Group Fairness'
      ],
      action: 'Run Real Analysis',
      link: '/bias-detection'
    },
    {
      id: 'security',
      title: 'Security Testing',
      description: 'OWASP Top 10 AI/LLM security vulnerability assessment',
      icon: <Shield className="h-6 w-6" />,
      color: 'bg-blue-500',
      estimatedTime: '8 min',
      tests: [
        'Prompt Injection',
        'Insecure Output Handling',
        'Training Data Poisoning',
        'Model Denial of Service',
        'Supply Chain Vulnerabilities'
      ],
      action: 'Run Security Tests',
      link: '/owasp-security'
    },
    {
      id: 'compliance',
      title: 'Compliance Check',
      description: 'Verify compliance with regulatory frameworks',
      icon: <CheckCircle className="h-6 w-6" />,
      color: 'bg-green-500',
      estimatedTime: '3 min',
      tests: [
        'GDPR Compliance',
        'CCPA Compliance',
        'HIPAA Compliance',
        'SOX Compliance',
        'ISO 27001 Compliance'
      ],
      action: 'Check Compliance',
      link: '/compliance'
    }
  ]

  const handleAssessmentClick = (assessmentId: string) => {
    setCurrentAssessment(assessmentId)
  }

  const handleRunAssessment = (assessment: any) => {
    // Navigate to the actual assessment page
    if (assessment.link) {
      router.push(assessment.link)
    }
  }

  const handleContinue = () => {
    router.push('/journey/secure')
  }

  const getAssessmentStatus = (assessmentId: string) => {
    const result = assessmentResults[assessmentId as keyof typeof assessmentResults]
    if (result.completed) {
      if (result.score >= 90) return { status: 'success', color: 'bg-green-500', text: 'Excellent' }
      if (result.score >= 80) return { status: 'info', color: 'bg-blue-500', text: 'Good' }
      if (result.score >= 70) return { status: 'warning', color: 'bg-yellow-500', text: 'Fair' }
      return { status: 'danger', color: 'bg-red-500', text: 'Needs Improvement' }
    }
    return { status: 'info', color: 'bg-gray-300', text: 'Not Started' }
  }

  return (
    <div className="space-y-8">
      {/* Header */}
      <div className="text-center mb-8">
        <NeoHeading size="xl" className="mb-4">
          <TestTube className="h-8 w-8 inline mr-3" />
          Assess Model Risks
        </NeoHeading>
        <NeoText className="text-xl max-w-3xl mx-auto">
          Test your AI models for bias, security vulnerabilities, and compliance gaps.
          Identify potential issues before they become problems.
        </NeoText>
      </div>

      {/* Assessment Overview */}
      <NeoCard>
        <div className="flex items-center justify-between mb-6">
          <h2 className="neo-heading neo-heading--lg">Assessment Progress</h2>
          <div className="flex items-center gap-2">
            <div className="w-4 h-4 bg-green-500 rounded-full"></div>
            <span className="neo-text text-sm">Completed</span>
            <div className="w-4 h-4 bg-blue-500 rounded-full ml-4"></div>
            <span className="neo-text text-sm">In Progress</span>
            <div className="w-4 h-4 bg-gray-300 rounded-full ml-4"></div>
            <span className="neo-text text-sm">Pending</span>
          </div>
        </div>
        
        <div className="w-full bg-gray-200 rounded-full h-3 mb-4">
          <div 
            className="bg-gradient-to-r from-green-500 to-blue-500 h-3 rounded-full" 
            style={{ width: `${(Object.values(assessmentResults).filter(r => r.completed).length / 3) * 100}%` }}
          ></div>
        </div>
        
        <div className="flex justify-between text-sm">
          <span>{Object.values(assessmentResults).filter(r => r.completed).length} of 3 Assessments</span>
          <span>{Math.round((Object.values(assessmentResults).filter(r => r.completed).length / 3) * 100)}% Complete</span>
        </div>
      </NeoCard>

      {/* Assessment Options */}
      <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
        {assessments.map((assessment) => {
          const status = getAssessmentStatus(assessment.id)
          const isActive = currentAssessment === assessment.id
          
          return (
            <div
              key={assessment.id}
              className={`neo-card cursor-pointer transition-all duration-300 hover:scale-105 ${
                isActive ? 'border-blue-500 border-4' : ''
              }`}
              onClick={() => handleAssessmentClick(assessment.id)}
            >
              <div className="flex items-start gap-4">
                <div className={`w-12 h-12 ${assessment.color} rounded-lg flex items-center justify-center text-white`}>
                  {assessment.icon}
                </div>
                
                <div className="flex-1">
                  <h3 className="neo-heading neo-heading--md mb-2">{assessment.title}</h3>
                  <p className="neo-text neo-text--muted mb-3">{assessment.description}</p>
                  
                  <div className="flex items-center gap-4 mb-3">
                    <div className="flex items-center gap-1">
                      <span className="neo-text text-sm">⏱️ {assessment.estimatedTime}</span>
                    </div>
                    <div className="flex items-center gap-1">
                      <span className="neo-text text-sm">🧪 {assessment.tests.length} tests</span>
                    </div>
                  </div>
                  
                  <div className="space-y-1 mb-4">
                    {assessment.tests.slice(0, 3).map((test, index) => (
                      <div key={index} className="flex items-center gap-2">
                        <div className="w-1 h-1 bg-gray-400 rounded-full"></div>
                        <span className="neo-text text-xs">{test}</span>
                      </div>
                    ))}
                    {assessment.tests.length > 3 && (
                      <div className="flex items-center gap-2">
                        <div className="w-1 h-1 bg-gray-400 rounded-full"></div>
                        <span className="neo-text text-xs">+{assessment.tests.length - 3} more tests</span>
                      </div>
                    )}
                  </div>
                  
                  <NeoButton 
                    className="w-full neo-button--primary"
                    onClick={() => {
                      handleRunAssessment(assessment)
                    }}
                  >
                    <Play className="h-4 w-4 mr-2" />
                    {assessment.action}
                    <ExternalLink className="h-4 w-4 ml-2" />
                  </NeoButton>
                </div>
              </div>
            </div>
          )
        })}
      </div>

      {/* Current Assessment Details */}
      {currentAssessment && (
        <NeoCard>
          <div className="flex items-center justify-between mb-4">
            <h2 className="neo-heading neo-heading--lg">
              {assessments.find(a => a.id === currentAssessment)?.title} Assessment
            </h2>
            <NeoBadge variant={getAssessmentStatus(currentAssessment).status as "success" | "warning" | "info" | "danger"}>
              {getAssessmentStatus(currentAssessment).text}
            </NeoBadge>
          </div>
          
          <p className="neo-text neo-text--muted mb-6">
            {assessments.find(a => a.id === currentAssessment)?.description}
          </p>
          
          <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
            <div>
              <h3 className="neo-heading neo-heading--sm mb-3">Test Coverage</h3>
              <div className="space-y-2">
                {assessments.find(a => a.id === currentAssessment)?.tests.map((test, index) => (
                  <div key={index} className="flex items-center gap-2">
                    <CheckCircle className="h-4 w-4 text-green-500" />
                    <span className="neo-text text-sm">{test}</span>
                  </div>
                ))}
              </div>
            </div>
            
            <div>
              <h3 className="neo-heading neo-heading--sm mb-3">Quick Actions</h3>
              <div className="space-y-2">
                <NeoButton 
                  className="w-full neo-button--secondary"
                  onClick={() => handleRunAssessment(assessments.find(a => a.id === currentAssessment)!)}
                >
                  <Play className="h-4 w-4 mr-2" />
                  Run {assessments.find(a => a.id === currentAssessment)?.title} Analysis
                </NeoButton>
                <NeoButton className="w-full neo-button--outline">
                  <Eye className="h-4 w-4 mr-2" />
                  View Sample Results
                </NeoButton>
              </div>
            </div>
          </div>
        </NeoCard>
      )}

      {/* Navigation */}
      <div className="flex justify-between">
        <NeoButton 
          className="neo-button--secondary"
          onClick={() => router.push('/journey/discover')}
        >
          <ArrowRight className="h-4 w-4 mr-2 rotate-180" />
          Back to Discover
        </NeoButton>
        
        <NeoButton 
          className="neo-button--primary"
          onClick={handleContinue}
        >
          Continue to Secure
          <ArrowRight className="h-4 w-4 ml-2" />
        </NeoButton>
      </div>
    </div>
  )
}
