"use client"

import { useState } from 'react'
import { useRouter } from 'next/navigation'
import {
  Compass,
  Target,
  Shield,
  BarChart3,
  Trophy,
  Settings,
  ArrowRight,
  CheckCircle,
  Play,
  BookOpen,
  Users,
  Zap,
  Search,
  TestTube,
  Lock,
  Cog,
  Award,
  TrendingUp,
  AlertTriangle,
  FileText,
  Database,
  Brain
} from 'lucide-react'

interface JourneyStep {
  id: string
  title: string
  description: string
  icon: React.ReactNode
  path: string
  status: 'completed' | 'current' | 'upcoming' | 'optional'
  category: 'discovery' | 'assessment' | 'implementation' | 'governance'
  estimatedTime: string
  prerequisites: string[]
}

const journeySteps: JourneyStep[] = [
  // Discovery Phase
  {
    id: 'discover',
    title: 'AI Landscape Assessment',
    description: 'Comprehensive analysis of current AI models and governance requirements. Includes DNA profiling, BOM analysis, and model inventory.',
    icon: <Search className="h-6 w-6" />,
    path: '/journey/discover',
    status: 'current',
    category: 'discovery',
    estimatedTime: '5 min',
    prerequisites: []
  },
  {
    id: 'assess',
    title: 'Risk Assessment & Testing',
    description: 'Comprehensive evaluation of bias, security vulnerabilities, and compliance gaps. Features ethics observatory and circus testing.',
    icon: <TestTube className="h-6 w-6" />,
    path: '/journey/assess',
    status: 'upcoming',
    category: 'assessment',
    estimatedTime: '15 min',
    prerequisites: ['discover']
  },
  {
    id: 'secure',
    title: 'Security Implementation',
    description: 'OWASP security testing and vulnerability assessment implementation',
    icon: <Lock className="h-6 w-6" />,
    path: '/journey/secure',
    status: 'upcoming',
    category: 'assessment',
    estimatedTime: '10 min',
    prerequisites: ['assess']
  },
  {
    id: 'implement',
    title: 'Governance Framework',
    description: 'Establish monitoring, compliance tracking, and governance frameworks. Includes genetic engineering for model optimization.',
    icon: <Cog className="h-6 w-6" />,
    path: '/journey/implement',
    status: 'upcoming',
    category: 'implementation',
    estimatedTime: '20 min',
    prerequisites: ['secure']
  },
  {
    id: 'excel',
    title: 'Governance Excellence',
    description: 'Achieve governance excellence with comprehensive progress tracking and historical analysis via time travel features.',
    icon: <Award className="h-6 w-6" />,
    path: '/journey/excel',
    status: 'upcoming',
    category: 'governance',
    estimatedTime: 'Ongoing',
    prerequisites: ['implement']
  }
]

const quickActions = [
  {
    title: 'Bias Assessment',
    description: 'Comprehensive bias analysis and testing',
    icon: <TestTube className="h-5 w-5" />,
    path: '/journey/assess',
    color: 'bg-red-500'
  },
  {
    title: 'Security Analysis',
    description: 'OWASP security vulnerability assessment',
    icon: <Lock className="h-5 w-5" />,
    path: '/journey/secure',
    color: 'bg-blue-500'
  },
  {
    title: 'Compliance Audit',
    description: 'Regulatory compliance verification',
    icon: <FileText className="h-5 w-5" />,
    path: '/journey/implement',
    color: 'bg-green-500'
  },
  {
    title: 'Model Inventory',
    description: 'Comprehensive AI model registry',
    icon: <Database className="h-5 w-5" />,
    path: '/journey/discover',
    color: 'bg-purple-500'
  },
  {
    title: 'Advanced Features',
    description: 'Specialized AI governance tools',
    icon: <Brain className="h-5 w-5" />,
    path: '/advanced-features',
    color: 'bg-indigo-500'
  }
]

export function JourneyNavigation() {
  const [currentStep, setCurrentStep] = useState('discover')
  const router = useRouter()

  const getStepStatus = (step: JourneyStep) => {
    if (step.status === 'completed') return 'bg-green-500'
    if (step.status === 'current') return 'bg-blue-500'
    if (step.status === 'optional') return 'bg-gray-500'
    return 'bg-gray-300'
  }

  const getStepBorder = (step: JourneyStep) => {
    if (step.status === 'current') return 'border-blue-500 border-4'
    if (step.status === 'completed') return 'border-green-500 border-2'
    return 'border-gray-300 border-2'
  }

  const handleStepClick = (step: JourneyStep) => {
    setCurrentStep(step.id)
    router.push(step.path)
  }

  const handleQuickAction = (path: string) => {
    router.push(path)
  }

  return (
    <div className="space-y-8">
      {/* Journey Header */}
      <div className="text-center mb-8">
        <h1 className="neo-heading neo-heading--xl mb-4">
          <TrendingUp className="h-8 w-8 inline mr-3" />
          AI Governance Implementation
        </h1>
        <p className="neo-text text-xl max-w-3xl mx-auto">
          Systematic approach to building comprehensive AI governance programs.
          Each phase builds upon the previous one, establishing robust foundations for responsible AI deployment.
        </p>
      </div>

      {/* Progress Overview */}
      <div className="neo-card">
        <div className="flex items-center justify-between mb-6">
          <h2 className="neo-heading neo-heading--lg">Implementation Progress</h2>
          <div className="flex items-center gap-2">
            <div className="w-4 h-4 bg-green-500 rounded-full"></div>
            <span className="neo-text text-sm">Completed</span>
            <div className="w-4 h-4 bg-blue-500 rounded-full ml-4"></div>
            <span className="neo-text text-sm">Current</span>
            <div className="w-4 h-4 bg-gray-300 rounded-full ml-4"></div>
            <span className="neo-text text-sm">Upcoming</span>
          </div>
        </div>
        
        <div className="w-full bg-gray-200 rounded-full h-3 mb-4">
          <div className="bg-gradient-to-r from-green-500 to-blue-500 h-3 rounded-full" style={{ width: '20%' }}></div>
        </div>
        
        <div className="flex justify-between text-sm">
          <span>Phase 1 of 5</span>
          <span>20% Complete</span>
        </div>
      </div>

      {/* Journey Steps */}
      <div className="space-y-6">
        {journeySteps.map((step, index) => (
          <div
            key={step.id}
            className={`neo-card cursor-pointer transition-all duration-300 hover:scale-105 ${getStepBorder(step)}`}
            onClick={() => handleStepClick(step)}
          >
            <div className="flex items-start gap-6">
              {/* Step Number and Icon */}
              <div className="flex-shrink-0">
                <div className={`w-12 h-12 rounded-full flex items-center justify-center text-white ${getStepStatus(step)}`}>
                  {step.status === 'completed' ? (
                    <CheckCircle className="h-6 w-6" />
                  ) : (
                    <span className="font-bold text-lg">{index + 1}</span>
                  )}
                </div>
              </div>

              {/* Step Content */}
              <div className="flex-1">
                <div className="flex items-center gap-3 mb-2">
                  <div className="text-gray-600">
                    {step.icon}
                  </div>
                  <h3 className="neo-heading neo-heading--md">{step.title}</h3>
                  {step.status === 'current' && (
                    <span className="neo-badge neo-badge--info">Current</span>
                  )}
                  {step.status === 'completed' && (
                    <span className="neo-badge neo-badge--success">Completed</span>
                  )}
                </div>
                
                <p className="neo-text mb-3">{step.description}</p>
                
                <div className="flex items-center gap-4 text-sm neo-text">
                  <span>⏱️ {step.estimatedTime}</span>
                  <span>📁 {step.category}</span>
                  {step.prerequisites.length > 0 && (
                    <span>🔗 Requires: {step.prerequisites.join(', ')}</span>
                  )}
                </div>
              </div>

              {/* Action Button */}
              <div className="flex-shrink-0">
                {step.status === 'current' ? (
                  <button className="neo-button neo-button--primary">
                    <Play className="h-4 w-4 mr-2" />
                    Continue
                  </button>
                ) : step.status === 'upcoming' ? (
                  <button className="neo-button neo-button--secondary" disabled>
                    <ArrowRight className="h-4 w-4 mr-2" />
                    Locked
                  </button>
                ) : (
                  <button className="neo-button neo-button--success">
                    <CheckCircle className="h-4 w-4 mr-2" />
                    Completed
                  </button>
                )}
              </div>
            </div>
          </div>
        ))}
      </div>

      {/* Quick Actions */}
      <div className="neo-card">
        <h2 className="neo-heading neo-heading--lg mb-6">Rapid Assessment Tools</h2>
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
          {quickActions.map((action, index) => (
            <div
              key={index}
              className="neo-card cursor-pointer hover:scale-105 transition-all duration-300"
              onClick={() => handleQuickAction(action.path)}
            >
              <div className={`w-12 h-12 ${action.color} rounded-lg flex items-center justify-center text-white mb-3`}>
                {action.icon}
              </div>
              <h3 className="neo-text neo-text--bold mb-2">{action.title}</h3>
              <p className="neo-text text-sm">{action.description}</p>
            </div>
          ))}
        </div>
      </div>

      {/* Implementation Guidelines */}
      <div className="neo-card neo-card--info">
        <div className="flex items-start gap-4">
          <div className="flex-shrink-0">
            <Zap className="h-6 w-6" />
          </div>
          <div>
            <h3 className="neo-text neo-text--bold mb-2">Implementation Guidelines</h3>
            <ul className="space-y-2 text-sm">
              <li>• Each phase requires 5-20 minutes for completion</li>
              <li>• Previous phases can be revisited for updates and reviews</li>
              <li>• Utilize rapid assessment tools for immediate analysis</li>
              <li>• Monitor progress through the Governance Center</li>
            </ul>
          </div>
        </div>
      </div>
    </div>
  )
}
