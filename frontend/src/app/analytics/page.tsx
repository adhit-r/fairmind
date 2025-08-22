"use client"

import React, { useState, useEffect } from 'react'
import { useRouter } from 'next/navigation'
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/common/card'
import { Button } from '@/components/ui/common/button'
import { Badge } from '@/components/ui/common/badge'
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/ui/common/tabs'
import { Progress } from '@/components/ui/common/progress'
import {
  ArrowLeft,
  BarChart3,
  TrendingUp,
  TrendingDown,
  Target,
  Shield,
  AlertTriangle,
  CheckCircle,
  Clock,
  Download,
  FileText,
  Users,
  Activity,
  PieChart,
  LineChart
} from 'lucide-react'
import { demoAnalytics, demoTestResults, demoReports } from '@/data/demo-data'

export default function AnalyticsPage() {
  const router = useRouter()
  const [analytics, setAnalytics] = useState(demoAnalytics)
  const [isLoading, setIsLoading] = useState(true)

  useEffect(() => {
    // Simulate loading analytics data
    setTimeout(() => {
      setIsLoading(false)
    }, 1000)
  }, [])

  const handleBack = () => {
    router.push('/dashboard')
  }

  const getStatusColor = (status: string) => {
    switch (status) {
      case 'completed': return 'bg-green-100 text-green-800'
      case 'running': return 'bg-yellow-100 text-yellow-800'
      case 'failed': return 'bg-red-100 text-red-800'
      default: return 'bg-gray-100 text-gray-800'
    }
  }

  const getScoreColor = (score: number) => {
    if (score >= 80) return 'text-green-600'
    if (score >= 60) return 'text-yellow-600'
    return 'text-red-600'
  }

  const getTrendIcon = (current: number, previous: number) => {
    if (current > previous) return <TrendingUp className="w-4 h-4 text-green-600" />
    if (current < previous) return <TrendingDown className="w-4 h-4 text-red-600" />
    return <div className="w-4 h-4" />
  }

  if (isLoading) {
    return (
      <div className="flex items-center justify-center min-h-screen">
        <div className="text-center">
          <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-blue-600 mx-auto mb-4"></div>
          <p className="text-gray-600">Loading Analytics...</p>
        </div>
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
        <h1 className="text-3xl font-bold text-gray-900 mb-2">Analytics & Reports</h1>
        <p className="text-gray-600">Comprehensive insights into your model performance and testing results</p>
      </div>

      {/* Overview Stats */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6 mb-8">
        <Card>
          <CardContent className="p-6">
            <div className="flex items-center justify-between">
              <div>
                <p className="text-sm font-medium text-gray-600">Average Bias Score</p>
                <p className={`text-2xl font-bold ${getScoreColor(analytics.overview.averageBiasScore)}`}>
                  {analytics.overview.averageBiasScore}%
                </p>
              </div>
              <Target className="w-8 h-8 text-blue-600" />
            </div>
            <div className="mt-4">
              <div className="flex items-center text-sm text-gray-600">
                <TrendingUp className="w-4 h-4 mr-1" />
                <span>+2.3% from last month</span>
              </div>
            </div>
          </CardContent>
        </Card>

        <Card>
          <CardContent className="p-6">
            <div className="flex items-center justify-between">
              <div>
                <p className="text-sm font-medium text-gray-600">Average Security Score</p>
                <p className={`text-2xl font-bold ${getScoreColor(analytics.overview.averageSecurityScore)}`}>
                  {analytics.overview.averageSecurityScore}%
                </p>
              </div>
              <Shield className="w-8 h-8 text-green-600" />
            </div>
            <div className="mt-4">
              <div className="flex items-center text-sm text-gray-600">
                <CheckCircle className="w-4 h-4 mr-1" />
                <span>All models secure</span>
              </div>
            </div>
          </CardContent>
        </Card>

        <Card>
          <CardContent className="p-6">
            <div className="flex items-center justify-between">
              <div>
                <p className="text-sm font-medium text-gray-600">Compliance Score</p>
                <p className={`text-2xl font-bold ${getScoreColor(analytics.overview.averageComplianceScore)}`}>
                  {analytics.overview.averageComplianceScore}%
                </p>
              </div>
              <CheckCircle className="w-8 h-8 text-purple-600" />
            </div>
            <div className="mt-4">
              <div className="flex items-center text-sm text-gray-600">
                <TrendingUp className="w-4 h-4 mr-1" />
                <span>+1.8% from last month</span>
              </div>
            </div>
          </CardContent>
        </Card>

        <Card>
          <CardContent className="p-6">
            <div className="flex items-center justify-between">
              <div>
                <p className="text-sm font-medium text-gray-600">Critical Issues</p>
                <p className="text-2xl font-bold text-red-600">
                  {analytics.overview.criticalIssues}
                </p>
              </div>
              <AlertTriangle className="w-8 h-8 text-red-600" />
            </div>
            <div className="mt-4">
              <div className="flex items-center text-sm text-gray-600">
                <Clock className="w-4 h-4 mr-1" />
                <span>1 requires attention</span>
              </div>
            </div>
          </CardContent>
        </Card>
      </div>

      <Tabs defaultValue="overview" className="space-y-6">
        <TabsList className="grid w-full grid-cols-5">
          <TabsTrigger value="overview">Overview</TabsTrigger>
          <TabsTrigger value="tests">Recent Tests</TabsTrigger>
          <TabsTrigger value="trends">Trends</TabsTrigger>
          <TabsTrigger value="teams">Team Performance</TabsTrigger>
          <TabsTrigger value="reports">Reports</TabsTrigger>
        </TabsList>

        <TabsContent value="overview" className="space-y-6">
          <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
            <Card>
              <CardHeader>
                <CardTitle className="flex items-center">
                  <BarChart3 className="w-5 h-5 mr-2" />
                  Model Performance Summary
                </CardTitle>
              </CardHeader>
              <CardContent>
                <div className="space-y-4">
                  <div className="flex justify-between items-center">
                    <span>Total Models</span>
                    <Badge variant="secondary">{analytics.overview.totalModels}</Badge>
                  </div>
                  <div className="flex justify-between items-center">
                    <span>Active Models</span>
                    <Badge variant="default">{analytics.overview.activeModels}</Badge>
                  </div>
                  <div className="flex justify-between items-center">
                    <span>Models in Testing</span>
                    <Badge variant="outline">{analytics.overview.modelsInTesting}</Badge>
                  </div>
                  <div className="flex justify-between items-center">
                    <span>Archived Models</span>
                    <Badge variant="outline">{analytics.overview.archivedModels}</Badge>
                  </div>
                  <div className="flex justify-between items-center">
                    <span>Total Tests Run</span>
                    <Badge variant="secondary">{analytics.overview.totalTests}</Badge>
                  </div>
                </div>
              </CardContent>
            </Card>

            <Card>
              <CardHeader>
                <CardTitle className="flex items-center">
                  <Target className="w-5 h-5 mr-2" />
                  Quality Metrics
                </CardTitle>
              </CardHeader>
              <CardContent>
                <div className="space-y-4">
                  <div>
                    <div className="flex justify-between text-sm mb-1">
                      <span>Bias Detection</span>
                      <span>{analytics.overview.averageBiasScore}%</span>
                    </div>
                    <Progress value={analytics.overview.averageBiasScore} className="h-2" />
                  </div>
                  <div>
                    <div className="flex justify-between text-sm mb-1">
                      <span>Security Analysis</span>
                      <span>{analytics.overview.averageSecurityScore}%</span>
                    </div>
                    <Progress value={analytics.overview.averageSecurityScore} className="h-2" />
                  </div>
                  <div>
                    <div className="flex justify-between text-sm mb-1">
                      <span>Compliance</span>
                      <span>{analytics.overview.averageComplianceScore}%</span>
                    </div>
                    <Progress value={analytics.overview.averageComplianceScore} className="h-2" />
                  </div>
                </div>
              </CardContent>
            </Card>
          </div>

          <Card>
            <CardHeader>
              <CardTitle className="flex items-center">
                <Activity className="w-5 h-5 mr-2" />
                Issue Distribution
              </CardTitle>
            </CardHeader>
            <CardContent>
              <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
                <div className="text-center">
                  <div className="text-3xl font-bold text-red-600 mb-2">{analytics.overview.criticalIssues}</div>
                  <div className="text-sm text-gray-600">Critical Issues</div>
                </div>
                <div className="text-center">
                  <div className="text-3xl font-bold text-yellow-600 mb-2">{analytics.overview.mediumIssues}</div>
                  <div className="text-sm text-gray-600">Medium Issues</div>
                </div>
                <div className="text-center">
                  <div className="text-3xl font-bold text-blue-600 mb-2">{analytics.overview.lowIssues}</div>
                  <div className="text-sm text-gray-600">Low Issues</div>
                </div>
              </div>
            </CardContent>
          </Card>
        </TabsContent>

        <TabsContent value="tests" className="space-y-6">
          <div className="flex justify-between items-center">
            <h2 className="text-xl font-semibold">Recent Test Results</h2>
            <Button variant="outline">
              <Download className="w-4 h-4 mr-2" />
              Export Data
            </Button>
          </div>

          <div className="space-y-4">
            {demoTestResults.map((test) => (
              <Card key={test.id}>
                <CardContent className="p-6">
                  <div className="flex items-center justify-between">
                    <div className="flex-1">
                      <div className="flex items-center space-x-4">
                        <div>
                          <h3 className="font-semibold text-gray-900">{test.modelName}</h3>
                          <p className="text-sm text-gray-600">{test.testType}</p>
                        </div>
                        <Badge className={getStatusColor(test.status)}>
                          {test.status}
                        </Badge>
                      </div>
                      <div className="mt-2 flex items-center space-x-6 text-sm text-gray-600">
                        <span>{new Date(test.date).toLocaleDateString()}</span>
                        <span>Duration: {test.duration}</span>
                        {test.score && (
                          <span className={`font-medium ${getScoreColor(test.score)}`}>
                            Score: {test.score}%
                          </span>
                        )}
                        {test.issues !== null && (
                          <span>Issues: {test.issues}</span>
                        )}
                        {test.recommendations !== null && (
                          <span>Recommendations: {test.recommendations}</span>
                        )}
                        {test.progress && (
                          <span>Progress: {test.progress}%</span>
                        )}
                      </div>
                    </div>
                    <div className="flex space-x-2">
                      <Button size="sm" variant="outline">
                        <FileText className="w-4 h-4 mr-1" />
                        View Details
                      </Button>
                      <Button size="sm" variant="outline">
                        <Download className="w-4 h-4 mr-1" />
                        Download
                      </Button>
                    </div>
                  </div>
                </CardContent>
              </Card>
            ))}
          </div>
        </TabsContent>

        <TabsContent value="trends" className="space-y-6">
          <h2 className="text-xl font-semibold">Performance Trends</h2>

          <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
            <Card>
              <CardHeader>
                <CardTitle>Bias Score Trend (12 Months)</CardTitle>
              </CardHeader>
              <CardContent>
                <div className="space-y-2">
                  {analytics.trends.biasScores.map((score, index) => (
                    <div key={index} className="flex items-center justify-between">
                      <span className="text-sm text-gray-600">Month {index + 1}</span>
                      <div className="flex items-center space-x-2">
                        <span className="font-medium">{score}%</span>
                        {index > 0 && getTrendIcon(score, analytics.trends.biasScores[index - 1])}
                      </div>
                    </div>
                  ))}
                </div>
              </CardContent>
            </Card>

            <Card>
              <CardHeader>
                <CardTitle>Security Score Trend (12 Months)</CardTitle>
              </CardHeader>
              <CardContent>
                <div className="space-y-2">
                  {analytics.trends.securityScores.map((score, index) => (
                    <div key={index} className="flex items-center justify-between">
                      <span className="text-sm text-gray-600">Month {index + 1}</span>
                      <div className="flex items-center space-x-2">
                        <span className="font-medium">{score}%</span>
                        {index > 0 && getTrendIcon(score, analytics.trends.securityScores[index - 1])}
                      </div>
                    </div>
                  ))}
                </div>
              </CardContent>
            </Card>
          </div>

          <Card>
            <CardHeader>
              <CardTitle>Test Volume Trend</CardTitle>
            </CardHeader>
            <CardContent>
              <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
                <div>
                  <h4 className="font-medium mb-3">Tests Run per Month</h4>
                  <div className="space-y-2">
                    {analytics.trends.testVolume.map((volume, index) => (
                      <div key={index} className="flex items-center justify-between">
                        <span className="text-sm text-gray-600">Month {index + 1}</span>
                        <span className="font-medium">{volume} tests</span>
                      </div>
                    ))}
                  </div>
                </div>
                <div>
                  <h4 className="font-medium mb-3">Model Uploads per Month</h4>
                  <div className="space-y-2">
                    {analytics.trends.modelUploads.map((uploads, index) => (
                      <div key={index} className="flex items-center justify-between">
                        <span className="text-sm text-gray-600">Month {index + 1}</span>
                        <span className="font-medium">{uploads} models</span>
                      </div>
                    ))}
                  </div>
                </div>
              </div>
            </CardContent>
          </Card>
        </TabsContent>

        <TabsContent value="teams" className="space-y-6">
          <h2 className="text-xl font-semibold">Team Performance Analysis</h2>

          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6">
            {analytics.teamPerformance.map((team) => (
              <Card key={team.team}>
                <CardContent className="p-6">
                  <div className="flex items-center justify-between mb-4">
                    <h3 className="font-semibold text-gray-900">{team.team}</h3>
                    <Users className="w-5 h-5 text-gray-400" />
                  </div>
                  <div className="space-y-3">
                    <div className="flex justify-between text-sm">
                      <span>Models:</span>
                      <span className="font-medium">{team.models}</span>
                    </div>
                    <div className="flex justify-between text-sm">
                      <span>Avg Score:</span>
                      <span className={`font-medium ${getScoreColor(team.averageScore)}`}>
                        {team.averageScore}%
                      </span>
                    </div>
                    <div className="flex justify-between text-sm">
                      <span>Tests Run:</span>
                      <span className="font-medium">{team.testsRun}</span>
                    </div>
                    <div className="flex justify-between text-sm">
                      <span>Issues:</span>
                      <span className="font-medium text-red-600">{team.issues}</span>
                    </div>
                  </div>
                  <div className="mt-4 pt-4 border-t">
                    <Button size="sm" variant="outline" className="w-full">
                      <BarChart3 className="w-4 h-4 mr-2" />
                      View Details
                    </Button>
                  </div>
                </CardContent>
              </Card>
            ))}
          </div>
        </TabsContent>

        <TabsContent value="reports" className="space-y-6">
          <div className="flex justify-between items-center">
            <h2 className="text-xl font-semibold">Generated Reports</h2>
            <Button>
              <FileText className="w-4 h-4 mr-2" />
              Generate New Report
            </Button>
          </div>

          {demoReports.length === 0 ? (
            <Card>
              <CardContent className="p-6">
                <div className="text-center">
                  <FileText className="w-16 h-16 text-gray-400 mx-auto mb-4" />
                  <h3 className="text-xl font-semibold text-gray-900 mb-2">
                    No Reports Generated Yet
                  </h3>
                  <p className="text-gray-600 mb-6">
                    Generate comprehensive reports for your models including bias analysis, security assessment, and compliance verification.
                  </p>
                  <Button size="lg">
                    <FileText className="w-4 h-4 mr-2" />
                    Generate First Report
                  </Button>
                </div>
              </CardContent>
            </Card>
          ) : (
            <div className="space-y-4">
              {demoReports.map((report) => (
                <Card key={report.id}>
                  <CardContent className="p-6">
                    <div className="flex items-center justify-between">
                      <div className="flex-1">
                        <h3 className="font-semibold text-gray-900">{report.name}</h3>
                        <p className="text-sm text-gray-600 mt-1">{report.summary}</p>
                        <div className="flex items-center space-x-4 mt-2 text-sm text-gray-600">
                          <span>Generated: {new Date(report.generatedAt).toLocaleDateString()}</span>
                          <span>Size: {report.size}</span>
                          <span>Models: {report.models.length}</span>
                        </div>
                      </div>
                      <div className="flex space-x-2">
                        <Button size="sm" variant="outline">
                          <FileText className="w-4 h-4 mr-1" />
                          View
                        </Button>
                        <Button size="sm" variant="outline">
                          <Download className="w-4 h-4 mr-1" />
                          Download
                        </Button>
                      </div>
                    </div>
                  </CardContent>
                </Card>
              ))}
            </div>
          )}
        </TabsContent>
      </Tabs>
    </div>
  )
}
