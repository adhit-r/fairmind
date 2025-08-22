"use client"

import React, { useState, useEffect } from 'react'
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/common/card'
import { Button } from '@/components/ui/common/button'
import { Badge } from '@/components/ui/common/badge'
import { Progress } from '@/components/ui/common/progress'
import { Alert, AlertDescription } from '@/components/ui/common/alert'
import { 
  TestTube, 
  Shield, 
  Target, 
  BarChart3, 
  CheckCircle, 
  AlertTriangle, 
  Clock,
  Play,
  Download,
  Eye,
  TrendingUp,
  TrendingDown
} from 'lucide-react'

interface Model {
  id: string
  name: string
  version: string
  type: string
  status: 'active' | 'testing' | 'archived'
  uploadDate: string
  lastTested?: string
  biasScore?: number
  securityScore?: number
}

interface TestResult {
  id: string
  modelId: string
  testType: 'bias' | 'security' | 'performance' | 'compliance'
  status: 'running' | 'completed' | 'failed'
  progress: number
  score?: number
  issues?: string[]
  recommendations?: string[]
  completedAt?: string
}

interface ModelTestingProps {
  models: Model[]
  onTestComplete?: (result: TestResult) => void
}

const TEST_TYPES = [
  {
    id: 'bias',
    name: 'Bias Detection',
    description: 'Analyze model for fairness and bias issues',
    icon: Target,
    color: 'bg-green-100 text-green-800',
    duration: 30000 // 30 seconds
  },
  {
    id: 'security',
    name: 'Security Testing',
    description: 'Test for vulnerabilities and security issues',
    icon: Shield,
    color: 'bg-red-100 text-red-800',
    duration: 45000 // 45 seconds
  },
  {
    id: 'performance',
    name: 'Performance Analysis',
    description: 'Evaluate model performance and efficiency',
    icon: BarChart3,
    color: 'bg-blue-100 text-blue-800',
    duration: 25000 // 25 seconds
  },
  {
    id: 'compliance',
    name: 'Compliance Check',
    description: 'Verify regulatory and compliance requirements',
    icon: CheckCircle,
    color: 'bg-purple-100 text-purple-800',
    duration: 35000 // 35 seconds
  }
]

export function ModelTesting({ models, onTestComplete }: ModelTestingProps) {
  const [selectedModel, setSelectedModel] = useState<Model | null>(null)
  const [runningTests, setRunningTests] = useState<TestResult[]>([])
  const [completedTests, setCompletedTests] = useState<TestResult[]>([])
  const [isRunning, setIsRunning] = useState(false)

  const startTest = async (model: Model, testType: string) => {
    const testConfig = TEST_TYPES.find(t => t.id === testType)
    if (!testConfig) return

    const testResult: TestResult = {
      id: Math.random().toString(36).substr(2, 9),
      modelId: model.id,
      testType: testType as any,
      status: 'running',
      progress: 0
    }

    setRunningTests(prev => [...prev, testResult])
    setIsRunning(true)

    // Simulate test progress
    const interval = setInterval(() => {
      setRunningTests(prev => prev.map(test => {
        if (test.id === testResult.id) {
          const newProgress = Math.min(test.progress + Math.random() * 15, 100)
          
          if (newProgress >= 100) {
            clearInterval(interval)
            
            // Generate test results
            const completedTest: TestResult = {
              ...test,
              status: 'completed',
              progress: 100,
              score: Math.floor(Math.random() * 40) + 60, // 60-100
              issues: generateIssues(testType),
              recommendations: generateRecommendations(testType),
              completedAt: new Date().toISOString()
            }

            setCompletedTests(prev => [...prev, completedTest])
            setRunningTests(prev => prev.filter(t => t.id !== test.id))
            onTestComplete?.(completedTest)
            
            if (runningTests.length === 1) {
              setIsRunning(false)
            }
            
            return completedTest
          }
          
          return { ...test, progress: newProgress }
        }
        return test
      }))
    }, 500)
  }

  const generateIssues = (testType: string): string[] => {
    const issues = {
      bias: [
        'Statistical parity difference exceeds threshold (0.15)',
        'Equalized odds violation detected',
        'Demographic parity gap identified'
      ],
      security: [
        'Model extraction vulnerability detected',
        'Adversarial attack susceptibility high',
        'Data poisoning risk identified'
      ],
      performance: [
        'Latency exceeds acceptable threshold',
        'Memory usage optimization needed',
        'Throughput below expected levels'
      ],
      compliance: [
        'GDPR compliance gaps identified',
        'Model explainability requirements not met',
        'Audit trail incomplete'
      ]
    }
    
    return issues[testType as keyof typeof issues]?.slice(0, Math.floor(Math.random() * 2) + 1) || []
  }

  const generateRecommendations = (testType: string): string[] => {
    const recommendations = {
      bias: [
        'Retrain model with balanced dataset',
        'Implement fairness constraints',
        'Add bias monitoring in production'
      ],
      security: [
        'Implement model watermarking',
        'Add input validation layers',
        'Deploy adversarial training'
      ],
      performance: [
        'Optimize model architecture',
        'Implement model quantization',
        'Add caching mechanisms'
      ],
      compliance: [
        'Implement comprehensive logging',
        'Add model explainability features',
        'Create audit documentation'
      ]
    }
    
    return recommendations[testType as keyof typeof recommendations]?.slice(0, Math.floor(Math.random() * 2) + 1) || []
  }

  const getScoreColor = (score: number) => {
    if (score >= 90) return 'text-green-600'
    if (score >= 75) return 'text-yellow-600'
    return 'text-red-600'
  }

  const getScoreIcon = (score: number) => {
    if (score >= 90) return <TrendingUp className="w-4 h-4" />
    if (score >= 75) return <TrendingUp className="w-4 h-4" />
    return <TrendingDown className="w-4 h-4" />
  }

  return (
    <div className="space-y-6">
      {/* Model Selection */}
      <Card>
        <CardHeader>
          <CardTitle>Select Model to Test</CardTitle>
        </CardHeader>
        <CardContent>
          {models.length === 0 ? (
            <div className="text-center py-8">
              <TestTube className="w-16 h-16 text-gray-400 mx-auto mb-4" />
              <h3 className="text-lg font-semibold text-gray-900 mb-2">No Models Available</h3>
              <p className="text-gray-600">Upload models first to start testing</p>
            </div>
          ) : (
            <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
              {models.map((model) => (
                <Card 
                  key={model.id} 
                  className={`cursor-pointer transition-all ${
                    selectedModel?.id === model.id 
                      ? 'ring-2 ring-blue-500 bg-blue-50' 
                      : 'hover:shadow-md'
                  }`}
                  onClick={() => setSelectedModel(model)}
                >
                  <CardContent className="p-4">
                    <div className="flex justify-between items-start mb-2">
                      <div>
                        <h4 className="font-semibold">{model.name}</h4>
                        <p className="text-sm text-gray-600">v{model.version}</p>
                      </div>
                      <Badge variant="outline">{model.type}</Badge>
                    </div>
                    <p className="text-xs text-gray-500">
                      Uploaded: {new Date(model.uploadDate).toLocaleDateString()}
                    </p>
                  </CardContent>
                </Card>
              ))}
            </div>
          )}
        </CardContent>
      </Card>

      {/* Test Types */}
      {selectedModel && (
        <Card>
          <CardHeader>
            <CardTitle>Test Options for {selectedModel.name}</CardTitle>
          </CardHeader>
          <CardContent>
            <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
              {TEST_TYPES.map((testType) => {
                const isRunning = runningTests.some(t => 
                  t.modelId === selectedModel.id && t.testType === testType.id
                )
                const isCompleted = completedTests.some(t => 
                  t.modelId === selectedModel.id && t.testType === testType.id
                )
                
                return (
                  <Card key={testType.id} className="relative">
                    <CardContent className="p-4">
                      <div className="flex items-start justify-between mb-3">
                        <div className="flex items-center space-x-3">
                          <div className={`p-2 rounded-lg ${testType.color}`}>
                            <testType.icon className="w-5 h-5" />
                          </div>
                          <div>
                            <h4 className="font-semibold">{testType.name}</h4>
                            <p className="text-sm text-gray-600">{testType.description}</p>
                          </div>
                        </div>
                        {isCompleted && (
                          <CheckCircle className="w-5 h-5 text-green-600" />
                        )}
                      </div>

                      {isRunning && (
                        <div className="space-y-2">
                          <div className="flex justify-between text-sm">
                            <span>Running...</span>
                            <span>{runningTests.find(t => 
                              t.modelId === selectedModel.id && t.testType === testType.id
                            )?.progress || 0}%</span>
                          </div>
                          <Progress 
                            value={runningTests.find(t => 
                              t.modelId === selectedModel.id && t.testType === testType.id
                            )?.progress || 0} 
                          />
                        </div>
                      )}

                      {isCompleted && (
                        <div className="space-y-2">
                          <div className="flex justify-between items-center">
                            <span className="text-sm">Score:</span>
                            <div className="flex items-center space-x-1">
                              {getScoreIcon(completedTests.find(t => 
                                t.modelId === selectedModel.id && t.testType === testType.id
                              )?.score || 0)}
                              <span className={`font-semibold ${getScoreColor(completedTests.find(t => 
                                t.modelId === selectedModel.id && t.testType === testType.id
                              )?.score || 0)}`}>
                                {completedTests.find(t => 
                                  t.modelId === selectedModel.id && t.testType === testType.id
                                )?.score || 0}%
                              </span>
                            </div>
                          </div>
                        </div>
                      )}

                      <div className="flex space-x-2 mt-4">
                        <Button
                          size="sm"
                          onClick={() => startTest(selectedModel, testType.id)}
                          disabled={isRunning || isCompleted}
                          className="flex-1"
                        >
                          {isRunning ? (
                            <>
                              <div className="animate-spin rounded-full h-3 w-3 border-b-2 border-white mr-2" />
                              Running
                            </>
                          ) : isCompleted ? (
                            <>
                              <Eye className="w-3 h-3 mr-2" />
                              View Results
                            </>
                          ) : (
                            <>
                              <Play className="w-3 h-3 mr-2" />
                              Start Test
                            </>
                          )}
                        </Button>
                        {isCompleted && (
                          <Button size="sm" variant="outline">
                            <Download className="w-3 h-3" />
                          </Button>
                        )}
                      </div>
                    </CardContent>
                  </Card>
                )
              })}
            </div>
          </CardContent>
        </Card>
      )}

      {/* Running Tests */}
      {runningTests.length > 0 && (
        <Card>
          <CardHeader>
            <CardTitle className="flex items-center">
              <Clock className="w-5 h-5 mr-2" />
              Running Tests ({runningTests.length})
            </CardTitle>
          </CardHeader>
          <CardContent>
            <div className="space-y-4">
              {runningTests.map((test) => {
                const model = models.find(m => m.id === test.modelId)
                const testConfig = TEST_TYPES.find(t => t.id === test.testType)
                
                return (
                  <div key={test.id} className="flex items-center justify-between p-4 bg-gray-50 rounded-lg">
                    <div className="flex items-center space-x-3">
                      <div className={`p-2 rounded-lg ${testConfig?.color}`}>
                        <testConfig?.icon className="w-4 h-4" />
                      </div>
                      <div>
                        <p className="font-medium">{model?.name}</p>
                        <p className="text-sm text-gray-600">{testConfig?.name}</p>
                      </div>
                    </div>
                    <div className="flex items-center space-x-4">
                      <div className="w-32">
                        <Progress value={test.progress} />
                      </div>
                      <span className="text-sm font-medium">{test.progress}%</span>
                    </div>
                  </div>
                )
              })}
            </div>
          </CardContent>
        </Card>
      )}

      {/* Completed Tests */}
      {completedTests.length > 0 && (
        <Card>
          <CardHeader>
            <CardTitle className="flex items-center">
              <CheckCircle className="w-5 h-5 mr-2" />
              Test Results ({completedTests.length})
            </CardTitle>
          </CardHeader>
          <CardContent>
            <div className="space-y-4">
              {completedTests.map((test) => {
                const model = models.find(m => m.id === test.modelId)
                const testConfig = TEST_TYPES.find(t => t.id === test.testType)
                
                return (
                  <Card key={test.id} className="border-l-4 border-green-500">
                    <CardContent className="p-4">
                      <div className="flex items-start justify-between mb-3">
                        <div className="flex items-center space-x-3">
                          <div className={`p-2 rounded-lg ${testConfig?.color}`}>
                            <testConfig?.icon className="w-4 h-4" />
                          </div>
                          <div>
                            <p className="font-medium">{model?.name}</p>
                            <p className="text-sm text-gray-600">{testConfig?.name}</p>
                          </div>
                        </div>
                        <div className="flex items-center space-x-2">
                          {getScoreIcon(test.score || 0)}
                          <span className={`font-semibold ${getScoreColor(test.score || 0)}`}>
                            {test.score}%
                          </span>
                        </div>
                      </div>

                      {test.issues && test.issues.length > 0 && (
                        <Alert variant="destructive" className="mb-3">
                          <AlertTriangle className="h-4 w-4" />
                          <AlertDescription>
                            <div className="space-y-1">
                              <p className="font-medium">Issues Found:</p>
                              <ul className="text-sm space-y-1">
                                {test.issues.map((issue, index) => (
                                  <li key={index}>• {issue}</li>
                                ))}
                              </ul>
                            </div>
                          </AlertDescription>
                        </Alert>
                      )}

                      {test.recommendations && test.recommendations.length > 0 && (
                        <Alert className="mb-3">
                          <CheckCircle className="h-4 w-4" />
                          <AlertDescription>
                            <div className="space-y-1">
                              <p className="font-medium">Recommendations:</p>
                              <ul className="text-sm space-y-1">
                                {test.recommendations.map((rec, index) => (
                                  <li key={index}>• {rec}</li>
                                ))}
                              </ul>
                            </div>
                          </AlertDescription>
                        </Alert>
                      )}

                      <div className="flex justify-between items-center text-xs text-gray-500">
                        <span>Completed: {test.completedAt ? new Date(test.completedAt).toLocaleString() : ''}</span>
                        <Button size="sm" variant="outline">
                          <Download className="w-3 h-3 mr-1" />
                          Download Report
                        </Button>
                      </div>
                    </CardContent>
                  </Card>
                )
              })}
            </div>
          </CardContent>
        </Card>
      )}
    </div>
  )
}
