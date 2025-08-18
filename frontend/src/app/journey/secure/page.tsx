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
  Lock,
  Shield,
  AlertTriangle,
  CheckCircle,
  Play,
  ArrowRight,
  Eye,
  Zap,
  Bug,
  Key,
  Database,
  Network
} from 'lucide-react'

export default function SecurePage() {
  const router = useRouter()
  const [currentTest, setCurrentTest] = useState('prompt-injection')
  const [testResults, setTestResults] = useState({
    'prompt-injection': { completed: false, score: 0, vulnerabilities: [] },
    'output-handling': { completed: false, score: 0, vulnerabilities: [] },
    'data-poisoning': { completed: false, score: 0, vulnerabilities: [] },
    'denial-service': { completed: false, score: 0, vulnerabilities: [] },
    'supply-chain': { completed: false, score: 0, vulnerabilities: [] }
  })

  const securityTests = [
    {
      id: 'prompt-injection',
      title: 'Prompt Injection',
      description: 'Test for prompt injection vulnerabilities in LLM systems',
      icon: <Bug className="h-6 w-6" />,
      color: 'bg-red-500',
      estimatedTime: '3 min',
      category: 'OWASP Top 10 AI/LLM #1'
    },
    {
      id: 'output-handling',
      title: 'Insecure Output Handling',
      description: 'Validate output handling and content filtering',
      icon: <Shield className="h-6 w-6" />,
      color: 'bg-orange-500',
      estimatedTime: '2 min',
      category: 'OWASP Top 10 AI/LLM #2'
    },
    {
      id: 'data-poisoning',
      title: 'Training Data Poisoning',
      description: 'Detect poisoned training data and model manipulation',
      icon: <Database className="h-6 w-6" />,
      color: 'bg-yellow-500',
      estimatedTime: '4 min',
      category: 'OWASP Top 10 AI/LLM #3'
    },
    {
      id: 'denial-service',
      title: 'Model Denial of Service',
      description: 'Test for resource exhaustion and DoS vulnerabilities',
      icon: <Network className="h-6 w-6" />,
      color: 'bg-purple-500',
      estimatedTime: '3 min',
      category: 'OWASP Top 10 AI/LLM #4'
    },
    {
      id: 'supply-chain',
      title: 'Supply Chain Vulnerabilities',
      description: 'Assess third-party model and dependency risks',
      icon: <Key className="h-6 w-6" />,
      color: 'bg-blue-500',
      estimatedTime: '2 min',
      category: 'OWASP Top 10 AI/LLM #5'
    }
  ]

  const handleTestClick = (testId: string) => {
    setCurrentTest(testId)
  }

  const handleRunTest = () => {
    // Simulate security test running
    setTimeout(() => {
      const results = {
        ...testResults,
        [currentTest]: {
          completed: true,
          score: Math.floor(Math.random() * 30) + 70, // 70-100
          vulnerabilities: [
            'Potential prompt injection vulnerability detected',
            'Output filtering may be insufficient',
            'Recommend implementing input validation'
          ]
        }
      }
      setTestResults(results)
    }, 3000)
  }

  const handleContinue = () => {
    router.push('/journey/implement')
  }

  const getTestStatus = (testId: string) => {
    const result = testResults[testId as keyof typeof testResults]
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
          <Lock className="h-8 w-8 inline mr-3" />
          Security Implementation
        </NeoHeading>
        <NeoText className="text-xl max-w-3xl mx-auto">
          OWASP Top 10 AI/LLM security testing and vulnerability assessment.
          Identify and mitigate security risks in your AI systems.
        </NeoText>
      </div>

      {/* Security Overview */}
      <NeoCard>
        <div className="flex items-center justify-between mb-6">
          <h2 className="neo-heading neo-heading--lg">Security Assessment Progress</h2>
          <div className="flex items-center gap-2">
            <div className="w-4 h-4 bg-green-500 rounded-full"></div>
            <span className="neo-text text-sm">Passed</span>
            <div className="w-4 h-4 bg-yellow-500 rounded-full ml-4"></div>
            <span className="neo-text text-sm">Warning</span>
            <div className="w-4 h-4 bg-red-500 rounded-full ml-4"></div>
            <span className="neo-text text-sm">Failed</span>
          </div>
        </div>
        
        <div className="w-full bg-gray-200 rounded-full h-3 mb-4">
          <div 
            className="bg-gradient-to-r from-green-500 to-blue-500 h-3 rounded-full" 
            style={{ width: `${(Object.values(testResults).filter(r => r.completed).length / 5) * 100}%` }}
          ></div>
        </div>
        
        <div className="flex justify-between text-sm">
          <span>{Object.values(testResults).filter(r => r.completed).length} of 5 Tests</span>
          <span>{Math.round((Object.values(testResults).filter(r => r.completed).length / 5) * 100)}% Complete</span>
        </div>
      </NeoCard>

      {/* Security Tests */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
        {securityTests.map((test) => {
          const status = getTestStatus(test.id)
          const isActive = currentTest === test.id
          
          return (
            <div
              key={test.id}
              className={`neo-card cursor-pointer transition-all duration-300 hover:scale-105 ${
                isActive ? 'border-blue-500 border-4' : ''
              }`}
              onClick={() => handleTestClick(test.id)}
            >
              <div className="flex items-start gap-4">
                <div className={`w-12 h-12 ${test.color} rounded-lg flex items-center justify-center text-white`}>
                  {test.icon}
                </div>
                
                <div className="flex-1">
                  <div className="flex items-center justify-between mb-2">
                    <h3 className="neo-heading neo-heading--md">{test.title}</h3>
                    <NeoBadge variant={status.status === 'excellent' ? 'success' : status.status === 'good' ? 'info' : status.status === 'fair' ? 'warning' : 'danger'}>
                      {status.text}
                    </NeoBadge>
                  </div>
                  
                  <p className="neo-text text-gray-600 mb-3">{test.description}</p>
                  
                  <div className="space-y-2 text-sm text-gray-500">
                    <div>⏱️ {test.estimatedTime}</div>
                    <div>🛡️ {test.category}</div>
                    {testResults[test.id as keyof typeof testResults].completed && (
                      <div>📊 Score: {testResults[test.id as keyof typeof testResults].score}/100</div>
                    )}
                  </div>
                </div>
              </div>
            </div>
          )
        })}
      </div>

      {/* Current Test Details */}
      {currentTest && (
        <NeoCard>
          <div className="flex items-center gap-4 mb-6">
            <div className={`w-12 h-12 ${securityTests.find(t => t.id === currentTest)?.color} rounded-lg flex items-center justify-center text-white`}>
              {securityTests.find(t => t.id === currentTest)?.icon}
            </div>
            <div>
              <h3 className="neo-heading neo-heading--lg">
                {securityTests.find(t => t.id === currentTest)?.title} Security Test
              </h3>
              <p className="neo-text text-gray-600">
                {securityTests.find(t => t.id === currentTest)?.description}
              </p>
            </div>
          </div>

          {!testResults[currentTest as keyof typeof testResults].completed ? (
            <div className="space-y-6">
              <div>
                <h4 className="neo-heading neo-heading--md mb-4">Test Methodology:</h4>
                <div className="grid grid-cols-1 md:grid-cols-2 gap-3">
                  <div className="flex items-center gap-3 p-3 bg-gray-50 rounded-lg">
                    <div className="w-6 h-6 bg-gray-300 rounded-full flex items-center justify-center text-xs">1</div>
                    <NeoText className="text-sm">Input validation testing</NeoText>
                  </div>
                  <div className="flex items-center gap-3 p-3 bg-gray-50 rounded-lg">
                    <div className="w-6 h-6 bg-gray-300 rounded-full flex items-center justify-center text-xs">2</div>
                    <NeoText className="text-sm">Vulnerability scanning</NeoText>
                  </div>
                  <div className="flex items-center gap-3 p-3 bg-gray-50 rounded-lg">
                    <div className="w-6 h-6 bg-gray-300 rounded-full flex items-center justify-center text-xs">3</div>
                    <NeoText className="text-sm">Penetration testing</NeoText>
                  </div>
                  <div className="flex items-center gap-3 p-3 bg-gray-50 rounded-lg">
                    <div className="w-6 h-6 bg-gray-300 rounded-full flex items-center justify-center text-xs">4</div>
                    <NeoText className="text-sm">Risk assessment</NeoText>
                  </div>
                </div>
              </div>

              <div className="flex justify-center">
                <NeoButton
                  variant="primary"
                  onClick={handleRunTest}
                  className="px-8 py-3"
                >
                  <Play className="h-5 w-5 mr-2" />
                  Run Security Test
                </NeoButton>
              </div>
            </div>
          ) : (
            <div className="space-y-6">
              <div className="text-center">
                <div className="text-4xl font-bold text-green-600 mb-2">
                  {testResults[currentTest as keyof typeof testResults].score}/100
                </div>
                <NeoText className="text-lg">Security Test Complete</NeoText>
              </div>

              <div>
                <h4 className="neo-heading neo-heading--md mb-4">Vulnerabilities Found:</h4>
                <div className="space-y-3">
                  {testResults[currentTest as keyof typeof testResults].vulnerabilities.map((vuln, index) => (
                    <div key={index} className="flex items-start gap-3 p-3 bg-yellow-50 border-l-4 border-yellow-400 rounded">
                      <AlertTriangle className="h-5 w-5 text-yellow-600 mt-0.5" />
                      <NeoText className="text-sm">{vuln}</NeoText>
                    </div>
                  ))}
                </div>
              </div>

              <div className="flex justify-center">
                <NeoButton
                  variant="secondary"
                  onClick={() => handleRunTest()}
                  className="px-6 py-2"
                >
                  <Eye className="h-4 w-4 mr-2" />
                  View Detailed Report
                </NeoButton>
              </div>
            </div>
          )}
        </NeoCard>
      )}

      {/* Continue Button */}
      {Object.values(testResults).every(r => r.completed) && (
        <div className="text-center">
          <NeoButton
            variant="primary"
            onClick={handleContinue}
            className="px-8 py-3"
          >
            Continue to Governance Framework
            <ArrowRight className="h-5 w-5 ml-2" />
          </NeoButton>
        </div>
      )}

      {/* Security Guidelines */}
      <NeoAlert variant="info">
        <div className="flex items-start gap-4">
          <div className="flex-shrink-0">
            <Zap className="h-6 w-6" />
          </div>
          <div>
            <NeoText variant="bold" className="mb-2">Security Guidelines</NeoText>
            <NeoText className="mb-2">• Run all five OWASP AI/LLM security tests for comprehensive coverage</NeoText>
            <NeoText className="mb-2">• Address high-priority vulnerabilities (scores below 85) immediately</NeoText>
            <NeoText>• Implement security controls based on test results and recommendations</NeoText>
          </div>
        </div>
      </NeoAlert>
    </div>
  )
}

