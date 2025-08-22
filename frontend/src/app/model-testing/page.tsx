"use client"

import React, { useState, useEffect } from 'react'
import { ModelTesting } from '@/components/features/model-registry/model-testing'
import { useRouter } from 'next/navigation'
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/common/card'
import { Button } from '@/components/ui/common/button'
import { Badge } from '@/components/ui/common/badge'
import { Progress } from '@/components/ui/common/progress'
import { ArrowLeft, TestTube, BarChart3, Shield, Target, AlertTriangle, Clock, Users, FileText } from 'lucide-react'
import { demoModels } from '@/data/demo-data'

export default function ModelTestingPage() {
  const router = useRouter()
  const [models, setModels] = useState(demoModels)
  const [selectedModel, setSelectedModel] = useState<string>('')
  const [showTesting, setShowTesting] = useState(false)

  const handleBack = () => {
    router.push('/dashboard')
  }

  const handleModelSelect = (modelId: string) => {
    setSelectedModel(modelId)
    setShowTesting(true)
  }

  const handleBackToSelection = () => {
    setShowTesting(false)
    setSelectedModel('')
  }

  const getStatusColor = (status: string) => {
    switch (status) {
      case 'active': return 'bg-green-100 text-green-800'
      case 'testing': return 'bg-yellow-100 text-yellow-800'
      case 'archived': return 'bg-gray-100 text-gray-800'
      default: return 'bg-gray-100 text-gray-800'
    }
  }

  const getScoreColor = (score: number) => {
    if (score >= 80) return 'text-green-600'
    if (score >= 60) return 'text-yellow-600'
    return 'text-red-600'
  }

  if (showTesting && selectedModel) {
    const model = models.find(m => m.id === selectedModel)
    if (!model) return null

    return (
      <div className="container mx-auto p-6">
        <div className="mb-6">
          <Button
            variant="ghost"
            onClick={handleBackToSelection}
            className="mb-4"
          >
            <ArrowLeft className="w-4 h-4 mr-2" />
            Back to Model Selection
          </Button>
        </div>

        <ModelTesting
          models={models}
          selectedModel={model}
          onBack={handleBackToSelection}
        />
      </div>
    )
  }

  return (
    <div className="container mx-auto p-6">
      <div className="mb-6">
        <Button
          variant="ghost"
          onClick={handleBack}
          className="mb-4"
        >
          <ArrowLeft className="w-4 h-4 mr-2" />
          Back to Dashboard
        </Button>
      </div>

      <div className="mb-8">
        <h1 className="text-3xl font-bold text-gray-900 mb-2">Model Testing</h1>
        <p className="text-gray-600">Select a model to test for bias, security, performance, and compliance issues</p>
      </div>

      {models.length === 0 ? (
        <Card className="border-dashed border-2 border-gray-300">
          <CardContent className="p-12 text-center">
            <TestTube className="w-16 h-16 text-gray-400 mx-auto mb-4" />
            <h3 className="text-xl font-semibold text-gray-900 mb-2">
              No Models Available for Testing
            </h3>
            <p className="text-gray-600 mb-6">
              Upload some models first to start testing them for bias, security, and compliance issues.
            </p>
            <Button onClick={() => router.push('/model-upload')}>
              Upload Model
            </Button>
          </CardContent>
        </Card>
      ) : (
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
          {models.map((model) => (
            <Card
              key={model.id}
              className="hover:shadow-lg transition-shadow cursor-pointer"
              onClick={() => handleModelSelect(model.id)}
            >
              <CardHeader>
                <div className="flex justify-between items-start">
                  <div>
                    <CardTitle className="text-lg">{model.name}</CardTitle>
                    <p className="text-sm text-gray-600">v{model.version}</p>
                  </div>
                  <Badge className={getStatusColor(model.status)}>
                    {model.status}
                  </Badge>
                </div>
              </CardHeader>
              <CardContent className="space-y-4">
                <div className="flex justify-between text-sm">
                  <span>Type:</span>
                  <span className="font-medium">{model.type}</span>
                </div>
                <div className="flex justify-between text-sm">
                  <span>Framework:</span>
                  <span className="font-medium">{model.framework}</span>
                </div>
                <div className="flex justify-between text-sm">
                  <span>Team:</span>
                  <span className="font-medium">{model.team}</span>
                </div>
                <div className="flex justify-between text-sm">
                  <span>Uploaded:</span>
                  <span>{new Date(model.uploadDate).toLocaleDateString()}</span>
                </div>
                {model.lastTested && (
                  <div className="flex justify-between text-sm">
                    <span>Last Tested:</span>
                    <span>{new Date(model.lastTested).toLocaleDateString()}</span>
                  </div>
                )}

                <div className="pt-4 border-t space-y-2">
                  <div className="flex justify-between text-sm">
                    <span>Bias Score:</span>
                    <span className={`font-medium ${getScoreColor(model.biasScore)}`}>
                      {model.biasScore}%
                    </span>
                  </div>
                  <div className="flex justify-between text-sm">
                    <span>Security Score:</span>
                    <span className={`font-medium ${getScoreColor(model.securityScore)}`}>
                      {model.securityScore}%
                    </span>
                  </div>
                  <div className="flex justify-between text-sm">
                    <span>Compliance Score:</span>
                    <span className={`font-medium ${getScoreColor(model.complianceScore)}`}>
                      {model.complianceScore}%
                    </span>
                  </div>
                </div>

                <div className="pt-4 border-t">
                  <div className="flex space-x-2">
                    <Button size="sm" className="flex-1">
                      <TestTube className="w-4 h-4 mr-1" />
                      Test
                    </Button>
                    <Button size="sm" variant="outline" className="flex-1">
                      <BarChart3 className="w-4 h-4 mr-1" />
                      View Results
                    </Button>
                  </div>
                </div>
              </CardContent>
            </Card>
          ))}
        </div>
      )}

      {/* Testing Overview */}
      <div className="mt-12">
        <h2 className="text-2xl font-bold text-gray-900 mb-6">Testing Capabilities</h2>
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6">
          <Card>
            <CardContent className="p-6 text-center">
              <Target className="w-12 h-12 text-blue-600 mx-auto mb-4" />
              <h3 className="font-semibold text-gray-900 mb-2">Bias Detection</h3>
              <p className="text-sm text-gray-600">
                Comprehensive analysis for demographic parity, equalized odds, and equal opportunity
              </p>
            </CardContent>
          </Card>

          <Card>
            <CardContent className="p-6 text-center">
              <Shield className="w-12 h-12 text-green-600 mx-auto mb-4" />
              <h3 className="font-semibold text-gray-900 mb-2">Security Analysis</h3>
              <p className="text-sm text-gray-600">
                Vulnerability assessment, adversarial testing, and model robustness evaluation
              </p>
            </CardContent>
          </Card>

          <Card>
            <CardContent className="p-6 text-center">
              <BarChart3 className="w-12 h-12 text-purple-600 mx-auto mb-4" />
              <h3 className="font-semibold text-gray-900 mb-2">Performance Testing</h3>
              <p className="text-sm text-gray-600">
                Accuracy, latency, throughput, and resource utilization analysis
              </p>
            </CardContent>
          </Card>

          <Card>
            <CardContent className="p-6 text-center">
              <TestTube className="w-12 h-12 text-orange-600 mx-auto mb-4" />
              <h3 className="font-semibold text-gray-900 mb-2">Compliance Check</h3>
              <p className="text-sm text-gray-600">
                GDPR, CCPA, SOX, and industry-specific regulatory compliance verification
              </p>
            </CardContent>
          </Card>
        </div>
      </div>

      {/* Testing Statistics */}
      <div className="mt-12">
        <h2 className="text-2xl font-bold text-gray-900 mb-6">Testing Statistics</h2>
        <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
          <Card>
            <CardContent className="p-6">
              <div className="flex items-center justify-between mb-4">
                <div>
                  <p className="text-sm font-medium text-gray-600">Total Tests Run</p>
                  <p className="text-2xl font-bold text-gray-900">18</p>
                </div>
                <TestTube className="w-8 h-8 text-blue-600" />
              </div>
              <div className="space-y-2">
                <div className="flex justify-between text-sm">
                  <span>This Week:</span>
                  <span className="font-medium">5</span>
                </div>
                <div className="flex justify-between text-sm">
                  <span>This Month:</span>
                  <span className="font-medium">18</span>
                </div>
              </div>
            </CardContent>
          </Card>

          <Card>
            <CardContent className="p-6">
              <div className="flex items-center justify-between mb-4">
                <div>
                  <p className="text-sm font-medium text-gray-600">Average Test Duration</p>
                  <p className="text-2xl font-bold text-gray-900">2m 45s</p>
                </div>
                <Clock className="w-8 h-8 text-green-600" />
              </div>
              <div className="space-y-2">
                <div className="flex justify-between text-sm">
                  <span>Bias Tests:</span>
                  <span className="font-medium">1m 30s</span>
                </div>
                <div className="flex justify-between text-sm">
                  <span>Security Tests:</span>
                  <span className="font-medium">3m 15s</span>
                </div>
              </div>
            </CardContent>
          </Card>

          <Card>
            <CardContent className="p-6">
              <div className="flex items-center justify-between mb-4">
                <div>
                  <p className="text-sm font-medium text-gray-600">Issues Found</p>
                  <p className="text-2xl font-bold text-red-600">6</p>
                </div>
                <AlertTriangle className="w-8 h-8 text-red-600" />
              </div>
              <div className="space-y-2">
                <div className="flex justify-between text-sm">
                  <span>Critical:</span>
                  <span className="font-medium text-red-600">1</span>
                </div>
                <div className="flex justify-between text-sm">
                  <span>Medium:</span>
                  <span className="font-medium text-yellow-600">3</span>
                </div>
                <div className="flex justify-between text-sm">
                  <span>Low:</span>
                  <span className="font-medium text-blue-600">2</span>
                </div>
              </div>
            </CardContent>
          </Card>
        </div>
      </div>
    </div>
  )
}
