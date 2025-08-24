'use client'

import React, { useState, useEffect } from 'react'
import { useRouter } from 'next/navigation'
import { 
  ArrowLeft, 
  TestTube, 
  BarChart3, 
  Shield, 
  Target, 
  AlertTriangle, 
  Clock, 
  Users, 
  FileText,
  Brain,
  Zap,
  Activity,
  CheckCircle,
  Play
} from 'lucide-react'
import { PageWrapper } from '@/components/core/PageWrapper'
import { Card } from '@/components/core/Card'
import { Button } from '@/components/core/Button'

interface Model {
  id: string
  name: string
  description: string
  version: string
  type: string
  status: 'active' | 'inactive' | 'testing' | 'failed'
  accuracy?: number
  last_tested?: string
}

const demoModels: Model[] = [
  {
    id: 'model-1',
    name: 'Credit Risk Model',
    description: 'ML model for credit risk assessment and loan approval',
    version: '2.1.0',
    type: 'Classification',
    status: 'active',
    accuracy: 85.2,
    last_tested: '2024-01-15T10:00:00Z'
  },
  {
    id: 'model-2',
    name: 'Fraud Detection AI',
    description: 'AI model for detecting fraudulent transactions',
    version: '1.5.2',
    type: 'Classification',
    status: 'active',
    accuracy: 92.4,
    last_tested: '2024-01-16T14:30:00Z'
  },
  {
    id: 'model-3',
    name: 'Customer Segmentation',
    description: 'Clustering model for customer segmentation',
    version: '1.2.0',
    type: 'Clustering',
    status: 'testing',
    accuracy: 87.1,
    last_tested: '2024-01-17T09:15:00Z'
  }
]

export default function ModelTestingPage() {
  const router = useRouter()
  const [models, setModels] = useState<Model[]>(demoModels)
  const [selectedModel, setSelectedModel] = useState<string>('')
  const [showTesting, setShowTesting] = useState(false)
  const [isRunningTest, setIsRunningTest] = useState(false)

  const handleBack = () => {
    router.push('/')
  }

  const handleModelSelect = (modelId: string) => {
    setSelectedModel(modelId)
    setShowTesting(true)
  }

  const handleBackToSelection = () => {
    setShowTesting(false)
    setSelectedModel('')
  }

  const runTest = async () => {
    setIsRunningTest(true)
    // Simulate test execution
    await new Promise(resolve => setTimeout(resolve, 3000))
    setIsRunningTest(false)
    // Show success message or redirect
  }

  const getStatusIcon = (status: string) => {
    switch (status) {
      case 'active':
        return <CheckCircle className="h-4 w-4 text-green-400" />
      case 'testing':
        return <Clock className="h-4 w-4 text-blue-400" />
      case 'failed':
        return <AlertTriangle className="h-4 w-4 text-red-400" />
      default:
        return <Clock className="h-4 w-4 text-slate-400" />
    }
  }

  const getStatusColor = (status: string) => {
    switch (status) {
      case 'active':
        return 'bg-green-500/10 text-green-400 border-green-500/20'
      case 'testing':
        return 'bg-blue-500/10 text-blue-400 border-blue-500/20'
      case 'failed':
        return 'bg-red-500/10 text-red-400 border-red-500/20'
      default:
        return 'bg-slate-500/10 text-slate-400 border-slate-500/20'
    }
  }

  if (showTesting && selectedModel) {
    const model = models.find(m => m.id === selectedModel)
    if (!model) return null

    return (
      <PageWrapper title="Model Testing" subtitle={`Testing ${model.name}`}>
        <div className="mb-6">
          <Button 
            variant="ghost" 
            icon={ArrowLeft}
            onClick={handleBackToSelection}
          >
            Back to Model Selection
          </Button>
        </div>

        <Card title={`Testing ${model.name}`} icon={<TestTube className="h-5 w-5 text-blue-400" />}>
          <div className="space-y-6">
            <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
              <div>
                <label className="block text-sm font-medium text-slate-300 mb-2">Model Information</label>
                <div className="bg-slate-800/50 rounded-lg p-4 space-y-2">
                  <div className="flex justify-between">
                    <span className="text-slate-400">Name:</span>
                    <span className="text-white">{model.name}</span>
                  </div>
                  <div className="flex justify-between">
                    <span className="text-slate-400">Version:</span>
                    <span className="text-white">{model.version}</span>
                  </div>
                  <div className="flex justify-between">
                    <span className="text-slate-400">Type:</span>
                    <span className="text-white">{model.type}</span>
                  </div>
                  <div className="flex justify-between">
                    <span className="text-slate-400">Accuracy:</span>
                    <span className="text-green-400">{model.accuracy}%</span>
                  </div>
                </div>
              </div>

              <div>
                <label className="block text-sm font-medium text-slate-300 mb-2">Test Configuration</label>
                <div className="space-y-3">
                  <div className="flex items-center space-x-3">
                    <input type="checkbox" id="bias-test" className="rounded border-slate-600 bg-slate-800 text-blue-500" defaultChecked />
                    <label htmlFor="bias-test" className="text-sm text-slate-300">Bias Detection Test</label>
                  </div>
                  <div className="flex items-center space-x-3">
                    <input type="checkbox" id="security-test" className="rounded border-slate-600 bg-slate-800 text-blue-500" defaultChecked />
                    <label htmlFor="security-test" className="text-sm text-slate-300">Security Vulnerability Test</label>
                  </div>
                  <div className="flex items-center space-x-3">
                    <input type="checkbox" id="performance-test" className="rounded border-slate-600 bg-slate-800 text-blue-500" defaultChecked />
                    <label htmlFor="performance-test" className="text-sm text-slate-300">Performance Test</label>
                  </div>
                  <div className="flex items-center space-x-3">
                    <input type="checkbox" id="compliance-test" className="rounded border-slate-600 bg-slate-800 text-blue-500" defaultChecked />
                    <label htmlFor="compliance-test" className="text-sm text-slate-300">Compliance Test</label>
                  </div>
                </div>
              </div>
            </div>

            <div className="flex space-x-4 pt-4">
              <Button 
                onClick={runTest}
                loading={isRunningTest}
                disabled={isRunningTest}
                className="flex-1"
              >
                {isRunningTest ? 'Running Tests...' : 'Start Testing'}
              </Button>
              <Button 
                variant="outline"
                onClick={handleBackToSelection}
              >
                Cancel
              </Button>
            </div>
          </div>
        </Card>
      </PageWrapper>
    )
  }

  return (
    <PageWrapper title="Model Testing" subtitle="AI Model Testing & Validation">
      <div className="mb-6">
        <Button 
          variant="ghost" 
          icon={ArrowLeft}
          onClick={handleBack}
        >
          Back to Dashboard
        </Button>
      </div>

      <div className="mb-8">
        <h1 className="text-3xl font-bold text-white mb-2">Model Testing</h1>
        <p className="text-slate-400 text-lg">
          Select a model to test for bias, security, performance, and compliance issues
        </p>
      </div>

      {models.length === 0 ? (
        <Card>
          <div className="text-center py-12">
            <div className="w-16 h-16 bg-slate-700 rounded-2xl flex items-center justify-center mx-auto mb-4">
              <TestTube className="h-8 w-8 text-slate-400" />
            </div>
            <h3 className="text-xl font-semibold text-white mb-2">
              No Models Available for Testing
            </h3>
            <p className="text-slate-400 mb-6">
              Upload some models first to start testing them for bias, security, and compliance issues.
            </p>
            <Button onClick={() => router.push('/model-upload')}>
              Upload Model
            </Button>
          </div>
        </Card>
      ) : (
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
          {models.map((model) => (
            <Card 
              key={model.id} 
              hover 
              className="cursor-pointer group"
              onClick={() => handleModelSelect(model.id)}
            >
              <div className="flex items-start justify-between mb-4">
                <div className="flex items-center space-x-3">
                  <div className="w-10 h-10 bg-gradient-to-r from-blue-500 to-purple-600 rounded-xl flex items-center justify-center">
                    <Brain className="h-5 w-5 text-white" />
                  </div>
                  <div>
                    <h3 className="font-semibold text-white group-hover:text-blue-400 transition-colors">
                      {model.name}
                    </h3>
                    <p className="text-slate-400 text-sm">{model.type}</p>
                  </div>
                </div>
                <div className={`px-2 py-1 rounded-lg border text-xs font-medium ${getStatusColor(model.status)}`}>
                  <div className="flex items-center space-x-1">
                    {getStatusIcon(model.status)}
                    <span className="capitalize">{model.status}</span>
                  </div>
                </div>
              </div>

              <p className="text-slate-300 text-sm mb-4 line-clamp-2">
                {model.description}
              </p>

              <div className="grid grid-cols-2 gap-3 mb-4">
                <div className="text-center p-2 bg-slate-800/50 rounded-lg">
                  <p className="text-xs text-slate-400">Version</p>
                  <p className="text-sm font-semibold text-white">{model.version}</p>
                </div>
                <div className="text-center p-2 bg-slate-800/50 rounded-lg">
                  <p className="text-xs text-slate-400">Accuracy</p>
                  <p className="text-sm font-semibold text-green-400">{model.accuracy}%</p>
                </div>
              </div>

              <div className="flex items-center justify-between pt-4 border-t border-white/10">
                <div className="text-xs text-slate-500">
                  Last tested: {model.last_tested ? new Date(model.last_tested).toLocaleDateString() : 'Never'}
                </div>
                <div className="flex items-center space-x-2 text-blue-400 group-hover:text-blue-300 transition-colors">
                  <Play className="h-4 w-4" />
                  <span className="text-sm font-medium">Test</span>
                </div>
              </div>
            </Card>
          ))}
        </div>
      )}
    </PageWrapper>
  )
}
