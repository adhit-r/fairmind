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
  Cog,
  FileText,
  CheckCircle,
  AlertTriangle,
  Play,
  ArrowRight,
  Eye,
  Zap,
  Shield,
  BarChart3,
  Users,
  Settings
} from 'lucide-react'

export default function ImplementPage() {
  const router = useRouter()
  const [currentFramework, setCurrentFramework] = useState('monitoring')
  const [frameworkStatus, setFrameworkStatus] = useState({
    monitoring: { completed: false, score: 0, components: [] },
    compliance: { completed: false, score: 0, components: [] },
    governance: { completed: false, score: 0, components: [] },
    reporting: { completed: false, score: 0, components: [] }
  })

  const frameworks = [
    {
      id: 'monitoring',
      title: 'Monitoring Framework',
      description: 'Real-time AI model monitoring and performance tracking',
      icon: <BarChart3 className="h-6 w-6" />,
      color: 'bg-blue-500',
      estimatedTime: '10 min',
      category: 'Performance & Drift'
    },
    {
      id: 'compliance',
      title: 'Compliance Tracking',
      description: 'Regulatory compliance monitoring and audit trails',
      icon: <FileText className="h-6 w-6" />,
      color: 'bg-green-500',
      estimatedTime: '8 min',
      category: 'Regulatory & Legal'
    },
    {
      id: 'governance',
      title: 'Governance Policies',
      description: 'AI governance policies and decision frameworks',
      icon: <Shield className="h-6 w-6" />,
      color: 'bg-purple-500',
      estimatedTime: '12 min',
      category: 'Policy & Control'
    },
    {
      id: 'reporting',
      title: 'Reporting System',
      description: 'Automated reporting and stakeholder communication',
      icon: <Users className="h-6 w-6" />,
      color: 'bg-orange-500',
      estimatedTime: '6 min',
      category: 'Communication'
    }
  ]

  const handleFrameworkClick = (frameworkId: string) => {
    setCurrentFramework(frameworkId)
  }

  const handleImplementFramework = () => {
    // Simulate framework implementation
    setTimeout(() => {
      const results = {
        ...frameworkStatus,
        [currentFramework]: {
          completed: true,
          score: Math.floor(Math.random() * 25) + 75, // 75-100
          components: [
            'Framework components successfully deployed',
            'Monitoring dashboards configured',
            'Alert systems activated'
          ]
        }
      }
      setFrameworkStatus(results)
    }, 3000)
  }

  const handleContinue = () => {
    router.push('/journey/excel')
  }

  const getFrameworkStatus = (frameworkId: string) => {
    const result = frameworkStatus[frameworkId as keyof typeof frameworkStatus]
    if (result.completed) {
      if (result.score >= 95) return { status: 'excellent', color: 'bg-green-500', text: 'Excellent' }
      if (result.score >= 85) return { status: 'good', color: 'bg-blue-500', text: 'Good' }
      if (result.score >= 75) return { status: 'fair', color: 'bg-yellow-500', text: 'Fair' }
      return { status: 'poor', color: 'bg-red-500', text: 'Needs Improvement' }
    }
    return { status: 'pending', color: 'bg-gray-300', text: 'Not Started' }
  }

  return (
    <div className="space-y-8">
      {/* Header */}
      <div className="text-center mb-8">
        <NeoHeading size="xl" className="mb-4">
          <Cog className="h-8 w-8 inline mr-3" />
          Governance Framework
        </NeoHeading>
        <NeoText className="text-xl max-w-3xl mx-auto">
          Establish monitoring, compliance tracking, and governance frameworks.
          Build robust foundations for responsible AI deployment.
        </NeoText>
      </div>

      {/* Framework Overview */}
      <NeoCard>
        <div className="flex items-center justify-between mb-6">
          <h2 className="neo-heading neo-heading--lg">Framework Implementation Progress</h2>
          <div className="flex items-center gap-2">
            <div className="w-4 h-4 bg-green-500 rounded-full"></div>
            <span className="neo-text text-sm">Implemented</span>
            <div className="w-4 h-4 bg-blue-500 rounded-full ml-4"></div>
            <span className="neo-text text-sm">In Progress</span>
            <div className="w-4 h-4 bg-gray-300 rounded-full ml-4"></div>
            <span className="neo-text text-sm">Pending</span>
          </div>
        </div>
        
        <div className="w-full bg-gray-200 rounded-full h-3 mb-4">
          <div 
            className="bg-gradient-to-r from-green-500 to-blue-500 h-3 rounded-full" 
            style={{ width: `${(Object.values(frameworkStatus).filter(f => f.completed).length / 4) * 100}%` }}
          ></div>
        </div>
        
        <div className="flex justify-between text-sm">
          <span>{Object.values(frameworkStatus).filter(f => f.completed).length} of 4 Frameworks</span>
          <span>{Math.round((Object.values(frameworkStatus).filter(f => f.completed).length / 4) * 100)}% Complete</span>
        </div>
      </NeoCard>

      {/* Framework Options */}
      <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
        {frameworks.map((framework) => {
          const status = getFrameworkStatus(framework.id)
          const isActive = currentFramework === framework.id
          
          return (
            <div
              key={framework.id}
              className={`neo-card cursor-pointer transition-all duration-300 hover:scale-105 ${
                isActive ? 'border-blue-500 border-4' : ''
              }`}
              onClick={() => handleFrameworkClick(framework.id)}
            >
              <div className="flex items-start gap-4">
                <div className={`w-12 h-12 ${framework.color} rounded-lg flex items-center justify-center text-white`}>
                  {framework.icon}
                </div>
                
                <div className="flex-1">
                  <div className="flex items-center justify-between mb-2">
                    <h3 className="neo-heading neo-heading--md">{framework.title}</h3>
                    <NeoBadge variant={status.status === 'excellent' ? 'success' : status.status === 'good' ? 'info' : status.status === 'fair' ? 'warning' : 'danger'}>
                      {status.text}
                    </NeoBadge>
                  </div>
                  
                  <p className="neo-text text-gray-600 mb-3">{framework.description}</p>
                  
                  <div className="space-y-2 text-sm text-gray-500">
                    <div>⏱️ {framework.estimatedTime}</div>
                    <div>📋 {framework.category}</div>
                    {frameworkStatus[framework.id as keyof typeof frameworkStatus].completed && (
                      <div>📊 Score: {frameworkStatus[framework.id as keyof typeof frameworkStatus].score}/100</div>
                    )}
                  </div>
                </div>
              </div>
            </div>
          )
        })}
      </div>

      {/* Current Framework Details */}
      {currentFramework && (
        <NeoCard>
          <div className="flex items-center gap-4 mb-6">
            <div className={`w-12 h-12 ${frameworks.find(f => f.id === currentFramework)?.color} rounded-lg flex items-center justify-center text-white`}>
              {frameworks.find(f => f.id === currentFramework)?.icon}
            </div>
            <div>
              <h3 className="neo-heading neo-heading--lg">
                {frameworks.find(f => f.id === currentFramework)?.title} Implementation
              </h3>
              <p className="neo-text text-gray-600">
                {frameworks.find(f => f.id === currentFramework)?.description}
              </p>
            </div>
          </div>

          {!frameworkStatus[currentFramework as keyof typeof frameworkStatus].completed ? (
            <div className="space-y-6">
              <div>
                <h4 className="neo-heading neo-heading--md mb-4">Implementation Steps:</h4>
                <div className="grid grid-cols-1 md:grid-cols-2 gap-3">
                  <div className="flex items-center gap-3 p-3 bg-gray-50 rounded-lg">
                    <div className="w-6 h-6 bg-gray-300 rounded-full flex items-center justify-center text-xs">1</div>
                    <NeoText className="text-sm">Framework configuration</NeoText>
                  </div>
                  <div className="flex items-center gap-3 p-3 bg-gray-50 rounded-lg">
                    <div className="w-6 h-6 bg-gray-300 rounded-full flex items-center justify-center text-xs">2</div>
                    <NeoText className="text-sm">Component deployment</NeoText>
                  </div>
                  <div className="flex items-center gap-3 p-3 bg-gray-50 rounded-lg">
                    <div className="w-6 h-6 bg-gray-300 rounded-full flex items-center justify-center text-xs">3</div>
                    <NeoText className="text-sm">Integration testing</NeoText>
                  </div>
                  <div className="flex items-center gap-3 p-3 bg-gray-50 rounded-lg">
                    <div className="w-6 h-6 bg-gray-300 rounded-full flex items-center justify-center text-xs">4</div>
                    <NeoText className="text-sm">Validation & activation</NeoText>
                  </div>
                </div>
              </div>

              <div className="flex justify-center">
                <NeoButton
                  variant="primary"
                  onClick={handleImplementFramework}
                  className="px-8 py-3"
                >
                  <Play className="h-5 w-5 mr-2" />
                  Implement Framework
                </NeoButton>
              </div>
            </div>
          ) : (
            <div className="space-y-6">
              <div className="text-center">
                <div className="text-4xl font-bold text-green-600 mb-2">
                  {frameworkStatus[currentFramework as keyof typeof frameworkStatus].score}/100
                </div>
                <NeoText className="text-lg">Framework Implementation Complete</NeoText>
              </div>

              <div>
                <h4 className="neo-heading neo-heading--md mb-4">Components Deployed:</h4>
                <div className="space-y-3">
                  {frameworkStatus[currentFramework as keyof typeof frameworkStatus].components.map((component, index) => (
                    <div key={index} className="flex items-start gap-3 p-3 bg-green-50 border-l-4 border-green-400 rounded">
                      <CheckCircle className="h-5 w-5 text-green-600 mt-0.5" />
                      <NeoText className="text-sm">{component}</NeoText>
                    </div>
                  ))}
                </div>
              </div>

              <div className="flex justify-center">
                <NeoButton
                  variant="secondary"
                  onClick={() => handleImplementFramework()}
                  className="px-6 py-2"
                >
                  <Eye className="h-4 w-4 mr-2" />
                  View Framework Details
                </NeoButton>
              </div>
            </div>
          )}
        </NeoCard>
      )}

      {/* Continue Button */}
      {Object.values(frameworkStatus).every(f => f.completed) && (
        <div className="text-center">
          <NeoButton
            variant="primary"
            onClick={handleContinue}
            className="px-8 py-3"
          >
            Continue to Governance Excellence
            <ArrowRight className="h-5 w-5 ml-2" />
          </NeoButton>
        </div>
      )}

      {/* Implementation Guidelines */}
      <NeoAlert variant="info">
        <div className="flex items-start gap-4">
          <div className="flex-shrink-0">
            <Zap className="h-6 w-6" />
          </div>
          <div>
            <NeoText variant="bold" className="mb-2">Implementation Guidelines</NeoText>
            <NeoText className="mb-2">• Implement all four governance frameworks for comprehensive coverage</NeoText>
            <NeoText className="mb-2">• Prioritize monitoring and compliance frameworks for immediate value</NeoText>
            <NeoText>• Ensure proper integration between frameworks for optimal governance</NeoText>
          </div>
        </div>
      </NeoAlert>
    </div>
  )
}

