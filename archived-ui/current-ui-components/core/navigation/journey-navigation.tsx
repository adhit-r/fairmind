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
  Brain,
  Clock,
  Folder,
  Link as LinkIcon
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
    if (step.status === 'current') return 'border-blue-500 border-2'
    if (step.status === 'completed') return 'border-green-500 border-2'
    return 'border-gray-300 border-2'
  }

  const getStepTextColor = (step: JourneyStep) => {
    if (step.status === 'current') return 'text-blue-900'
    if (step.status === 'completed') return 'text-green-900'
    return 'text-gray-700'
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
        <h1 className="text-3xl font-black text-gray-900 mb-4 flex items-center justify-center">
          <TrendingUp className="h-8 w-8 mr-3 text-blue-600" />
          AI Governance Implementation
        </h1>
        <p className="text-lg font-bold text-gray-600 max-w-3xl mx-auto">
          Systematic approach to building comprehensive AI governance programs.
          Each phase builds upon the previous one, establishing robust foundations for responsible AI deployment.
        </p>
      </div>

      {/* Progress Overview */}
      <div className="bg-white border-2 border-black rounded-lg p-6 shadow-4px-4px-0px-black">
        <div className="flex items-center justify-between mb-6">
          <h2 className="text-xl font-black text-gray-900">Implementation Progress</h2>
          <div className="flex items-center gap-4">
            <div className="flex items-center gap-2">
              <div className="w-4 h-4 bg-green-500 border border-black rounded-full"></div>
              <span className="text-sm font-bold text-gray-700">Completed</span>
            </div>
            <div className="flex items-center gap-2">
              <div className="w-4 h-4 bg-blue-500 border border-black rounded-full"></div>
              <span className="text-sm font-bold text-gray-700">Current</span>
            </div>
            <div className="flex items-center gap-2">
              <div className="w-4 h-4 bg-gray-300 border border-black rounded-full"></div>
              <span className="text-sm font-bold text-gray-700">Upcoming</span>
            </div>
          </div>
        </div>
        
        <div className="w-full bg-gray-200 border border-black rounded-full h-4 mb-4">
          <div className="bg-gradient-to-r from-green-500 to-blue-500 h-4 rounded-full border border-black" style={{ width: '20%' }}></div>
        </div>
        
        <div className="flex justify-between text-sm font-bold text-gray-700">
          <span>Phase 1 of 5</span>
          <span>20% Complete</span>
        </div>
      </div>

      {/* Journey Steps */}
      <div className="space-y-4">
        {journeySteps.map((step, index) => (
          <div
            key={step.id}
            className={`bg-white border-2 border-black rounded-lg p-6 shadow-4px-4px-0px-black cursor-pointer transition-all duration-300 hover:shadow-6px-6px-0px-black ${getStepBorder(step)}`}
            onClick={() => handleStepClick(step)}
          >
            <div className="flex items-start gap-6">
              {/* Step Number and Icon */}
              <div className="flex-shrink-0">
                <div className={`w-12 h-12 rounded-lg border-2 border-black flex items-center justify-center text-white shadow-2px-2px-0px-black ${getStepStatus(step)}`}>
                  {step.status === 'completed' ? (
                    <CheckCircle className="h-6 w-6" />
                  ) : (
                    <span className="font-black text-lg">{index + 1}</span>
                  )}
                </div>
              </div>

              {/* Step Content */}
              <div className="flex-1">
                <div className="flex items-center gap-3 mb-3">
                  <div className="text-gray-600">
                    {step.icon}
                  </div>
                  <h3 className="text-xl font-black text-gray-900">{step.title}</h3>
                  {step.status === 'current' && (
                    <span className="bg-blue-100 text-blue-800 border border-blue-300 px-3 py-1 rounded-lg text-sm font-bold">Current</span>
                  )}
                  {step.status === 'completed' && (
                    <span className="bg-green-100 text-green-800 border border-green-300 px-3 py-1 rounded-lg text-sm font-bold">Completed</span>
                  )}
                </div>
                
                <p className="text-gray-600 mb-4 font-medium">{step.description}</p>
                
                <div className="flex items-center gap-6 text-sm font-bold text-gray-700">
                  <div className="flex items-center gap-2">
                    <Clock className="h-4 w-4" />
                    <span>{step.estimatedTime}</span>
                  </div>
                  <div className="flex items-center gap-2">
                    <Folder className="h-4 w-4" />
                    <span className="uppercase">{step.category}</span>
                  </div>
                  {step.prerequisites.length > 0 && (
                    <div className="flex items-center gap-2">
                      <LinkIcon className="h-4 w-4" />
                      <span>Requires: {step.prerequisites.join(', ')}</span>
                    </div>
                  )}
                </div>
              </div>

              {/* Action Button */}
              <div className="flex-shrink-0">
                {step.status === 'current' ? (
                  <button className="bg-blue-500 text-white border-2 border-black px-6 py-3 rounded-lg font-bold hover:bg-blue-600 shadow-2px-2px-0px-black transition-all duration-200">
                    <Play className="h-4 w-4 mr-2" />
                    Continue
                  </button>
                ) : step.status === 'upcoming' ? (
                  <button className="bg-gray-100 text-gray-500 border-2 border-gray-300 px-6 py-3 rounded-lg font-bold cursor-not-allowed shadow-2px-2px-0px-black">
                    <ArrowRight className="h-4 w-4 mr-2" />
                    Locked
                  </button>
                ) : (
                  <button className="bg-green-500 text-white border-2 border-black px-6 py-3 rounded-lg font-bold shadow-2px-2px-0px-black">
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
      <div className="bg-white border-2 border-black rounded-lg p-6 shadow-4px-4px-0px-black">
        <h2 className="text-xl font-black text-gray-900 mb-6">Rapid Assessment Tools</h2>
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
          {quickActions.map((action, index) => (
            <div
              key={index}
              className="bg-white border-2 border-black rounded-lg p-4 cursor-pointer hover:bg-gray-50 shadow-2px-2px-0px-black hover:shadow-4px-4px-0px-black transition-all duration-200"
              onClick={() => handleQuickAction(action.path)}
            >
              <div className={`w-12 h-12 ${action.color} rounded-lg border-2 border-black flex items-center justify-center text-white mb-3 shadow-2px-2px-0px-black`}>
                {action.icon}
              </div>
              <h3 className="font-black text-gray-900 mb-2">{action.title}</h3>
              <p className="text-sm font-bold text-gray-600">{action.description}</p>
            </div>
          ))}
        </div>
      </div>

      {/* Implementation Guidelines */}
      <div className="bg-blue-50 border-2 border-blue-300 rounded-lg p-6 shadow-4px-4px-0px-black">
        <div className="flex items-start gap-4">
          <div className="flex-shrink-0">
            <Zap className="h-6 w-6 text-blue-600" />
          </div>
          <div>
            <h3 className="font-black text-gray-900 mb-3">Implementation Guidelines</h3>
            <ul className="space-y-2 text-sm font-bold text-gray-700">
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
