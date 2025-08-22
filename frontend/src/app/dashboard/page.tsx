"use client"

import React, { useState, useEffect } from 'react'
import { useRouter } from 'next/navigation'
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/common/card'
import { Button } from '@/components/ui/common/button'
import { Badge } from '@/components/ui/common/badge'
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/ui/common/tabs'
import { 
  Upload, 
  TestTube, 
  Shield, 
  BarChart3, 
  Settings, 
  Plus,
  FileText,
    AlertTriangle,
    CheckCircle,
    Clock,
    Users,
    Database
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

interface DashboardStats {
  totalModels: number
  activeModels: number
  modelsInTesting: number
  criticalIssues: number
  recentTests: number
}

export default function DashboardPage() {
  const router = useRouter()
  const [models, setModels] = useState<Model[]>([])
  const [stats, setStats] = useState<DashboardStats>({
    totalModels: 0,
    activeModels: 0,
    modelsInTesting: 0,
    criticalIssues: 0,
    recentTests: 0
  })
  const [isLoading, setIsLoading] = useState(true)

  useEffect(() => {
    // Simulate loading dashboard data
    setTimeout(() => {
      setIsLoading(false)
    }, 1000)
  }, [])

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

  if (isLoading) {
    return (
      <div className="flex items-center justify-center min-h-screen">
        <div className="text-center">
          <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-blue-600 mx-auto mb-4"></div>
          <p className="text-gray-600">Loading SQ1 Dashboard...</p>
        </div>
      </div>
    )
  }

  return (
    <div className="container mx-auto p-6 space-y-6">
      {/* Header */}
      <div className="flex justify-between items-center">
        <div>
          <h1 className="text-3xl font-bold text-gray-900">SQ1 Dashboard</h1>
          <p className="text-gray-600">AI Governance & Model Management</p>
        </div>
        <div className="flex items-center space-x-4">
          <Badge variant="outline" className="bg-blue-50 text-blue-700">
            <Users className="w-4 h-4 mr-1" />
            SQ1 Team
          </Badge>
          <Button>
            <Plus className="w-4 h-4 mr-2" />
            Add Model
          </Button>
        </div>
      </div>

      {/* Stats Cards */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6">
        <Card>
          <CardContent className="p-6">
            <div className="flex items-center justify-between">
              <div>
                <p className="text-sm font-medium text-gray-600">Total Models</p>
                <p className="text-2xl font-bold text-gray-900">{stats.totalModels}</p>
              </div>
              <Database className="w-8 h-8 text-blue-600" />
            </div>
          </CardContent>
        </Card>

        <Card>
          <CardContent className="p-6">
            <div className="flex items-center justify-between">
              <div>
                <p className="text-sm font-medium text-gray-600">Active Models</p>
                <p className="text-2xl font-bold text-green-600">{stats.activeModels}</p>
              </div>
              <CheckCircle className="w-8 h-8 text-green-600" />
            </div>
          </CardContent>
        </Card>

        <Card>
          <CardContent className="p-6">
            <div className="flex items-center justify-between">
              <div>
                <p className="text-sm font-medium text-gray-600">In Testing</p>
                <p className="text-2xl font-bold text-yellow-600">{stats.modelsInTesting}</p>
              </div>
              <TestTube className="w-8 h-8 text-yellow-600" />
            </div>
          </CardContent>
        </Card>

        <Card>
          <CardContent className="p-6">
            <div className="flex items-center justify-between">
              <div>
                <p className="text-sm font-medium text-gray-600">Critical Issues</p>
                <p className="text-2xl font-bold text-red-600">{stats.criticalIssues}</p>
              </div>
              <AlertTriangle className="w-8 h-8 text-red-600" />
            </div>
          </CardContent>
        </Card>
      </div>

      {/* Main Content */}
      <Tabs defaultValue="overview" className="space-y-6">
        <TabsList className="grid w-full grid-cols-4">
          <TabsTrigger value="overview">Overview</TabsTrigger>
          <TabsTrigger value="models">Model Registry</TabsTrigger>
          <TabsTrigger value="testing">Testing</TabsTrigger>
          <TabsTrigger value="analytics">Analytics</TabsTrigger>
        </TabsList>

        <TabsContent value="overview" className="space-y-6">
          {models.length === 0 ? (
            <Card className="border-dashed border-2 border-gray-300">
              <CardContent className="p-12 text-center">
                <Upload className="w-16 h-16 text-gray-400 mx-auto mb-4" />
                <h3 className="text-xl font-semibold text-gray-900 mb-2">
                  Welcome to SQ1 Dashboard
                </h3>
                <p className="text-gray-600 mb-6 max-w-md mx-auto">
                  Get started by uploading your first ML model. We'll help you test it for bias, 
                  security, and compliance issues.
                </p>
                <div className="space-y-4">
                                          <Button size="lg" className="w-full sm:w-auto" onClick={() => router.push('/model-upload')}>
                        <Upload className="w-4 h-4 mr-2" />
                        Upload Your First Model
                        </Button>
                  <div className="text-sm text-gray-500">
                    Supported formats: .pkl, .joblib, .h5, .onnx, .pb
                  </div>
                </div>
              </CardContent>
            </Card>
          ) : (
            <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
              <Card>
                <CardHeader>
                  <CardTitle className="flex items-center">
                    <BarChart3 className="w-5 h-5 mr-2" />
                    Recent Activity
                  </CardTitle>
                </CardHeader>
                <CardContent>
                  <div className="space-y-4">
                    {models.slice(0, 3).map((model) => (
                      <div key={model.id} className="flex items-center justify-between p-3 bg-gray-50 rounded-lg">
                        <div>
                          <p className="font-medium">{model.name}</p>
                          <p className="text-sm text-gray-600">v{model.version}</p>
                        </div>
                        <Badge className={getStatusColor(model.status)}>
                          {model.status}
                        </Badge>
                      </div>
                    ))}
                  </div>
                </CardContent>
              </Card>

              <Card>
                <CardHeader>
                  <CardTitle className="flex items-center">
                    <Shield className="w-5 h-5 mr-2" />
                    Security Overview
                  </CardTitle>
                </CardHeader>
                <CardContent>
                  <div className="space-y-4">
                    <div className="flex justify-between items-center">
                      <span>Models with Issues</span>
                      <Badge variant="destructive">{stats.criticalIssues}</Badge>
                    </div>
                    <div className="flex justify-between items-center">
                      <span>Tests This Week</span>
                      <Badge variant="secondary">{stats.recentTests}</Badge>
                    </div>
                  </div>
                </CardContent>
              </Card>
            </div>
          )}
        </TabsContent>

        <TabsContent value="models" className="space-y-6">
                              <div className="flex justify-between items-center">
                    <h2 className="text-xl font-semibold">Model Registry</h2>
                    <Button onClick={() => router.push('/model-upload')}>
                        <Plus className="w-4 h-4 mr-2" />
                        Add Model
                    </Button>
                    </div>

          {models.length === 0 ? (
            <Card className="border-dashed border-2 border-gray-300">
              <CardContent className="p-12 text-center">
                <Database className="w-16 h-16 text-gray-400 mx-auto mb-4" />
                <h3 className="text-xl font-semibold text-gray-900 mb-2">
                  No Models Yet
                </h3>
                <p className="text-gray-600 mb-6">
                  Upload your ML models to start testing them for bias, security, and compliance.
                </p>
                                        <Button size="lg" onClick={() => router.push('/model-upload')}>
                            <Upload className="w-4 h-4 mr-2" />
                            Upload Model
                        </Button>
              </CardContent>
            </Card>
          ) : (
            <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
              {models.map((model) => (
                <Card key={model.id} className="hover:shadow-lg transition-shadow">
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
                      <span>Uploaded:</span>
                      <span>{new Date(model.uploadDate).toLocaleDateString()}</span>
                    </div>
                    {model.biasScore && (
                      <div className="flex justify-between text-sm">
                        <span>Bias Score:</span>
                        <span className={`font-medium ${getScoreColor(model.biasScore)}`}>
                          {model.biasScore}%
                        </span>
                      </div>
                    )}
                    {model.securityScore && (
                      <div className="flex justify-between text-sm">
                        <span>Security Score:</span>
                        <span className={`font-medium ${getScoreColor(model.securityScore)}`}>
                          {model.securityScore}%
                        </span>
                      </div>
                    )}
                    <div className="flex space-x-2 pt-2">
                      <Button size="sm" variant="outline" className="flex-1">
                        <TestTube className="w-4 h-4 mr-1" />
                        Test
                      </Button>
                      <Button size="sm" variant="outline" className="flex-1">
                        <BarChart3 className="w-4 h-4 mr-1" />
                        Analyze
                      </Button>
                    </div>
                  </CardContent>
                </Card>
              ))}
            </div>
          )}
        </TabsContent>

        <TabsContent value="testing" className="space-y-6">
                              <div className="flex justify-between items-center">
                    <h2 className="text-xl font-semibold">Model Testing</h2>
                    <Button onClick={() => router.push('/model-testing')}>
                        <TestTube className="w-4 h-4 mr-2" />
                        Run New Test
                    </Button>
                    </div>

          <Card>
            <CardContent className="p-6">
              <div className="text-center">
                <TestTube className="w-16 h-16 text-gray-400 mx-auto mb-4" />
                <h3 className="text-xl font-semibold text-gray-900 mb-2">
                  No Tests Yet
                </h3>
                <p className="text-gray-600 mb-6">
                  Start testing your models for bias detection, security vulnerabilities, and compliance issues.
                </p>
                                        <Button size="lg" onClick={() => router.push('/model-testing')}>
                            <TestTube className="w-4 h-4 mr-2" />
                            Start Testing
                        </Button>
              </div>
            </CardContent>
          </Card>
        </TabsContent>

        <TabsContent value="analytics" className="space-y-6">
                              <div className="flex justify-between items-center">
                    <h2 className="text-xl font-semibold">Analytics & Reports</h2>
                    <Button onClick={() => router.push('/analytics')}>
                        <FileText className="w-4 h-4 mr-2" />
                        View Analytics
                    </Button>
                    </div>

          <Card>
            <CardContent className="p-6">
              <div className="text-center">
                <BarChart3 className="w-16 h-16 text-gray-400 mx-auto mb-4" />
                <h3 className="text-xl font-semibold text-gray-900 mb-2">
                  No Analytics Data
                </h3>
                <p className="text-gray-600 mb-6">
                  Analytics and reports will appear here once you start testing your models.
                </p>
                                        <Button size="lg" onClick={() => router.push('/analytics')}>
                            <BarChart3 className="w-4 h-4 mr-2" />
                            View Analytics
                        </Button>
              </div>
            </CardContent>
          </Card>
        </TabsContent>
      </Tabs>
    </div>
  )
}
