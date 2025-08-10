"use client"

import { useState, useEffect } from 'react'
import { fairmindAPI } from '@/lib/fairmind-api'
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card"
import { Button } from "@/components/ui/button"
import { Badge } from "@/components/ui/badge"
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from "@/components/ui/select"
import { Alert, AlertDescription } from "@/components/ui/alert"
import { Progress } from "@/components/ui/progress"
import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/components/ui/tabs"
import { 
  Shield, 
  AlertTriangle, 
  CheckCircle, 
  Clock,
  Search,
  BarChart3,
  Download,
  Play,
  Eye,
  FileText,
  Zap,
  Target,
  TestTube,
  Bug,
  Lock,
  Unlock,
  Activity,
  TrendingUp,
  TrendingDown,
  Circle,
  Square,
  Triangle
} from "lucide-react"

interface OWASPSecurityTest {
  id: string
  category: string
  name: string
  description: string
  severity: string
  test_type: string
  enabled: boolean
  parameters: Record<string, any>
}

interface ModelInventoryItem {
  id: string
  name: string
  version: string
  type: string
  framework: string
  path: string
  size: string
  description: string
  metadata: Record<string, any>
}

interface SecurityAnalysis {
  analysis_id: string
  model_id: string
  created_at: string
  overall_score: number
  risk_level: string
  total_tests: number
  passed_tests: number
  failed_tests: number
  warning_tests: number
  critical_issues: number
  high_issues: number
  medium_issues: number
  low_issues: number
  test_results: any[]
  summary: any
  recommendations: string[]
}

export function OWASPSecurityDashboard() {
  const [selectedModel, setSelectedModel] = useState<string>('')
  const [selectedCategories, setSelectedCategories] = useState<string[]>([])
  const [availableTests, setAvailableTests] = useState<OWASPSecurityTest[]>([])
  const [testCategories, setTestCategories] = useState<string[]>([])
  const [modelInventory, setModelInventory] = useState<ModelInventoryItem[]>([])
  const [securityAnalysis, setSecurityAnalysis] = useState<SecurityAnalysis | null>(null)
  const [analysisHistory, setAnalysisHistory] = useState<any[]>([])
  const [loading, setLoading] = useState(false)
  const [analyzing, setAnalyzing] = useState(false)
  const [error, setError] = useState<string | null>(null)
  const [activeTab, setActiveTab] = useState('run-analysis')

  // Load initial data
  useEffect(() => {
    loadInitialData()
  }, [])

  const loadInitialData = async () => {
    try {
      setLoading(true)
      setError(null)

      const [testsResponse, categoriesResponse, modelsResponse, historyResponse] = await Promise.all([
        fairmindAPI.getOWASPTests(),
        fairmindAPI.getOWASPCategories(),
        fairmindAPI.getOWASPModelInventory(),
        fairmindAPI.listOWASPSecurityAnalyses()
      ])

      if (testsResponse.success) setAvailableTests(testsResponse.data)
      if (categoriesResponse.success) setTestCategories(categoriesResponse.data)
      if (modelsResponse.success) setModelInventory(modelsResponse.data)
      if (historyResponse.success) setAnalysisHistory(historyResponse.data.analyses)

    } catch (error) {
      setError('Failed to load OWASP security data')
      console.error('Error loading OWASP data:', error)
    } finally {
      setLoading(false)
    }
  }

  const handleRunAnalysis = async () => {
    if (!selectedModel) {
      setError('Please select a model to analyze')
      return
    }

    try {
      setAnalyzing(true)
      setError(null)

      const result = await fairmindAPI.runOWASPSecurityAnalysis({
        model_id: selectedModel,
        test_categories: selectedCategories.length > 0 ? selectedCategories : undefined,
        include_all_tests: selectedCategories.length === 0,
        test_parameters: {},
        priority: 'normal'
      })

      if (result.success && result.data) {
        setSecurityAnalysis(result.data)
        setActiveTab('results')
        
        // Refresh analysis history
        const historyResponse = await fairmindAPI.listOWASPSecurityAnalyses()
        if (historyResponse.success) {
          setAnalysisHistory(historyResponse.data.analyses)
        }
      }
    } catch (error) {
      setError('Failed to run security analysis')
      console.error('Error running analysis:', error)
    } finally {
      setAnalyzing(false)
    }
  }

  const getRiskColor = (risk: string) => {
    switch (risk.toLowerCase()) {
      case 'low': return 'bg-green-100 text-green-800'
      case 'medium': return 'bg-yellow-100 text-yellow-800'
      case 'high': return 'bg-orange-100 text-orange-800'
      case 'critical': return 'bg-red-100 text-red-800'
      default: return 'bg-gray-100 text-gray-800'
    }
  }

  const getSeverityIcon = (severity: string) => {
    switch (severity.toLowerCase()) {
      case 'critical': return <Triangle className="h-4 w-4 text-red-600" />
      case 'high': return <Square className="h-4 w-4 text-orange-600" />
      case 'medium': return <Circle className="h-4 w-4 text-yellow-600" />
      case 'low': return <Circle className="h-4 w-4 text-green-600" />
      default: return <Circle className="h-4 w-4 text-gray-600" />
    }
  }

  const getStatusIcon = (status: string) => {
    switch (status.toLowerCase()) {
      case 'passed': return <CheckCircle className="h-4 w-4 text-green-600" />
      case 'failed': return <AlertTriangle className="h-4 w-4 text-red-600" />
      case 'warning': return <Clock className="h-4 w-4 text-yellow-600" />
      default: return <Circle className="h-4 w-4 text-gray-600" />
    }
  }

  const getTestTypeIcon = (testType: string) => {
    switch (testType.toLowerCase()) {
      case 'automated': return <Zap className="h-4 w-4 text-blue-600" />
      case 'manual': return <Target className="h-4 w-4 text-purple-600" />
      case 'hybrid': return <Activity className="h-4 w-4 text-indigo-600" />
      default: return <TestTube className="h-4 w-4 text-gray-600" />
    }
  }

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div>
          <h2 className="text-2xl font-bold text-foreground">OWASP Top 10 AI/LLM Security</h2>
          <p className="text-muted-foreground">
            Comprehensive security testing and analysis for AI/LLM systems based on OWASP standards
          </p>
        </div>
        <div className="flex items-center space-x-2">
          <Button variant="outline" size="sm">
            <Download className="mr-2 h-4 w-4" />
            Export Report
          </Button>
          <Button variant="outline" size="sm">
            <BarChart3 className="mr-2 h-4 w-4" />
            View Analytics
          </Button>
        </div>
      </div>

      {/* Error Alert */}
      {error && (
        <Alert variant="destructive">
          <AlertTriangle className="h-4 w-4" />
          <AlertDescription>{error}</AlertDescription>
        </Alert>
      )}

      {/* Main Content */}
      <Tabs value={activeTab} onValueChange={setActiveTab} className="space-y-4">
        <TabsList className="grid w-full grid-cols-4">
          <TabsTrigger value="run-analysis">Run Analysis</TabsTrigger>
          <TabsTrigger value="results">Results</TabsTrigger>
          <TabsTrigger value="history">History</TabsTrigger>
          <TabsTrigger value="tests">Test Library</TabsTrigger>
        </TabsList>

        {/* Run Analysis Tab */}
        <TabsContent value="run-analysis" className="space-y-4">
          <Card>
            <CardHeader>
              <CardTitle className="text-lg">Security Analysis Configuration</CardTitle>
            </CardHeader>
            <CardContent className="space-y-4">
              {/* Model Selection */}
              <div className="space-y-2">
                <label className="text-sm font-medium">Select Model</label>
                <Select value={selectedModel} onValueChange={setSelectedModel}>
                  <SelectTrigger>
                    <SelectValue placeholder="Choose a model to analyze" />
                  </SelectTrigger>
                  <SelectContent>
                    {modelInventory.map((model) => (
                      <SelectItem key={model.id} value={model.id}>
                        <div className="flex items-center space-x-2">
                          <span>{model.name}</span>
                          <Badge variant="outline" className="text-xs">
                            {model.type}
                          </Badge>
                        </div>
                      </SelectItem>
                    ))}
                  </SelectContent>
                </Select>
              </div>

              {/* Test Categories */}
              <div className="space-y-2">
                <label className="text-sm font-medium">Test Categories (Optional)</label>
                <div className="grid grid-cols-2 gap-2">
                  {testCategories.map((category) => (
                    <div key={category} className="flex items-center space-x-2">
                      <input
                        type="checkbox"
                        id={category}
                        checked={selectedCategories.includes(category)}
                        onChange={(e) => {
                          if (e.target.checked) {
                            setSelectedCategories([...selectedCategories, category])
                          } else {
                            setSelectedCategories(selectedCategories.filter(c => c !== category))
                          }
                        }}
                        className="rounded"
                      />
                      <label htmlFor={category} className="text-sm">
                        {category}
                      </label>
                    </div>
                  ))}
                </div>
                <p className="text-xs text-muted-foreground">
                  Leave empty to run all tests
                </p>
              </div>

              {/* Run Analysis Button */}
              <Button 
                onClick={handleRunAnalysis} 
                disabled={analyzing || !selectedModel}
                className="w-full"
              >
                {analyzing ? (
                  <>
                    <Clock className="mr-2 h-4 w-4 animate-spin" />
                    Running Analysis...
                  </>
                ) : (
                  <>
                    <Play className="mr-2 h-4 w-4" />
                    Run Security Analysis
                  </>
                )}
              </Button>
            </CardContent>
          </Card>

          {/* Model Information */}
          {selectedModel && (
            <Card>
              <CardHeader>
                <CardTitle className="text-lg">Selected Model</CardTitle>
              </CardHeader>
              <CardContent>
                {(() => {
                  const model = modelInventory.find(m => m.id === selectedModel)
                  if (!model) return null
                  
                  return (
                    <div className="space-y-3">
                      <div className="flex items-center justify-between">
                        <span className="text-sm font-medium">Name:</span>
                        <span className="text-sm">{model.name}</span>
                      </div>
                      <div className="flex items-center justify-between">
                        <span className="text-sm font-medium">Version:</span>
                        <span className="text-sm">{model.version}</span>
                      </div>
                      <div className="flex items-center justify-between">
                        <span className="text-sm font-medium">Type:</span>
                        <Badge variant="outline">{model.type}</Badge>
                      </div>
                      <div className="flex items-center justify-between">
                        <span className="text-sm font-medium">Framework:</span>
                        <span className="text-sm">{model.framework}</span>
                      </div>
                      <div className="flex items-center justify-between">
                        <span className="text-sm font-medium">Size:</span>
                        <span className="text-sm">{model.size}</span>
                      </div>
                    </div>
                  )
                })()}
              </CardContent>
            </Card>
          )}
        </TabsContent>

        {/* Results Tab */}
        <TabsContent value="results" className="space-y-4">
          {securityAnalysis ? (
            <>
              {/* Overview Metrics */}
              <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
                <Card>
                  <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
                    <CardTitle className="text-sm font-medium">Security Score</CardTitle>
                    <Shield className="h-4 w-4 text-muted-foreground" />
                  </CardHeader>
                  <CardContent>
                    <div className="text-2xl font-bold">
                      {securityAnalysis.overall_score.toFixed(1)}/100
                    </div>
                    <Badge className={getRiskColor(securityAnalysis.risk_level)}>
                      {securityAnalysis.risk_level}
                    </Badge>
                  </CardContent>
                </Card>

                <Card>
                  <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
                    <CardTitle className="text-sm font-medium">Critical Issues</CardTitle>
                    <AlertTriangle className="h-4 w-4 text-red-600" />
                  </CardHeader>
                  <CardContent>
                    <div className="text-2xl font-bold text-red-600">
                      {securityAnalysis.critical_issues}
                    </div>
                    <p className="text-xs text-muted-foreground">
                      Critical vulnerabilities
                    </p>
                  </CardContent>
                </Card>

                <Card>
                  <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
                    <CardTitle className="text-sm font-medium">High Issues</CardTitle>
                    <AlertTriangle className="h-4 w-4 text-orange-600" />
                  </CardHeader>
                  <CardContent>
                    <div className="text-2xl font-bold text-orange-600">
                      {securityAnalysis.high_issues}
                    </div>
                    <p className="text-xs text-muted-foreground">
                      High severity issues
                    </p>
                  </CardContent>
                </Card>

                <Card>
                  <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
                    <CardTitle className="text-sm font-medium">Tests Passed</CardTitle>
                    <CheckCircle className="h-4 w-4 text-green-600" />
                  </CardHeader>
                  <CardContent>
                    <div className="text-2xl font-bold text-green-600">
                      {securityAnalysis.passed_tests}/{securityAnalysis.total_tests}
                    </div>
                    <p className="text-xs text-muted-foreground">
                      Tests passed
                    </p>
                  </CardContent>
                </Card>
              </div>

              {/* Test Results */}
              <Card>
                <CardHeader>
                  <CardTitle className="text-lg">Test Results</CardTitle>
                </CardHeader>
                <CardContent>
                  <div className="space-y-4">
                    {securityAnalysis.test_results.map((result, index) => (
                      <div key={index} className="border rounded-lg p-4">
                        <div className="flex items-center justify-between mb-2">
                          <div className="flex items-center space-x-2">
                            {getStatusIcon(result.status)}
                            <span className="font-medium">{result.name}</span>
                            <Badge variant="outline">{result.category}</Badge>
                          </div>
                          <div className="flex items-center space-x-2">
                            {getSeverityIcon(result.severity)}
                            <Badge className={getRiskColor(result.severity)}>
                              {result.severity}
                            </Badge>
                          </div>
                        </div>
                        <p className="text-sm text-muted-foreground mb-2">
                          {result.description}
                        </p>
                        {result.recommendations && result.recommendations.length > 0 && (
                          <div className="mt-2">
                            <p className="text-sm font-medium text-orange-600 mb-1">Recommendations:</p>
                            <ul className="text-sm text-muted-foreground space-y-1">
                              {result.recommendations.map((rec, idx) => (
                                <li key={idx}>• {rec}</li>
                              ))}
                            </ul>
                          </div>
                        )}
                      </div>
                    ))}
                  </div>
                </CardContent>
              </Card>

              {/* Recommendations */}
              {securityAnalysis.recommendations && securityAnalysis.recommendations.length > 0 && (
                <Card>
                  <CardHeader>
                    <CardTitle className="text-lg">Security Recommendations</CardTitle>
                  </CardHeader>
                  <CardContent>
                    <div className="space-y-3">
                      {securityAnalysis.recommendations.map((recommendation, index) => (
                        <div key={index} className="flex items-start space-x-3 p-3 bg-muted rounded-lg">
                          <div className="flex-shrink-0 w-6 h-6 bg-primary text-primary-foreground rounded-full flex items-center justify-center text-xs font-bold">
                            {index + 1}
                          </div>
                          <p className="text-sm">{recommendation}</p>
                        </div>
                      ))}
                    </div>
                  </CardContent>
                </Card>
              )}
            </>
          ) : (
            <Card>
              <CardContent className="flex items-center justify-center py-8">
                <div className="text-center">
                  <Shield className="h-12 w-12 text-muted-foreground mx-auto mb-4" />
                  <p className="text-muted-foreground">
                    No analysis results available. Run a security analysis to see results.
                  </p>
                </div>
              </CardContent>
            </Card>
          )}
        </TabsContent>

        {/* History Tab */}
        <TabsContent value="history" className="space-y-4">
          <Card>
            <CardHeader>
              <CardTitle className="text-lg">Analysis History</CardTitle>
            </CardHeader>
            <CardContent>
              {analysisHistory.length > 0 ? (
                <div className="space-y-4">
                  {analysisHistory.map((analysis) => (
                    <div key={analysis.analysis_id} className="border rounded-lg p-4">
                      <div className="flex items-center justify-between mb-2">
                        <div className="flex items-center space-x-2">
                          <span className="font-medium">{analysis.model_name}</span>
                          <Badge className={getRiskColor(analysis.risk_level)}>
                            {analysis.risk_level}
                          </Badge>
                        </div>
                        <div className="flex items-center space-x-2">
                          <span className="text-sm text-muted-foreground">
                            {new Date(analysis.created_at).toLocaleDateString()}
                          </span>
                          <Button variant="outline" size="sm">
                            <Eye className="h-4 w-4" />
                          </Button>
                        </div>
                      </div>
                      <div className="grid grid-cols-4 gap-4 text-sm">
                        <div>
                          <span className="text-muted-foreground">Score:</span>
                          <span className="ml-1 font-medium">{analysis.overall_score}</span>
                        </div>
                        <div>
                          <span className="text-muted-foreground">Tests:</span>
                          <span className="ml-1 font-medium">{analysis.total_tests}</span>
                        </div>
                        <div>
                          <span className="text-muted-foreground">Critical:</span>
                          <span className="ml-1 font-medium text-red-600">{analysis.critical_issues}</span>
                        </div>
                        <div>
                          <span className="text-muted-foreground">High:</span>
                          <span className="ml-1 font-medium text-orange-600">{analysis.high_issues}</span>
                        </div>
                      </div>
                    </div>
                  ))}
                </div>
              ) : (
                <div className="text-center py-8">
                  <FileText className="h-12 w-12 text-muted-foreground mx-auto mb-4" />
                  <p className="text-muted-foreground">No analysis history available.</p>
                </div>
              )}
            </CardContent>
          </Card>
        </TabsContent>

        {/* Test Library Tab */}
        <TabsContent value="tests" className="space-y-4">
          <Card>
            <CardHeader>
              <CardTitle className="text-lg">OWASP Test Library</CardTitle>
            </CardHeader>
            <CardContent>
              {availableTests.length > 0 ? (
                <div className="space-y-4">
                  {availableTests.map((test) => (
                    <div key={test.id} className="border rounded-lg p-4">
                      <div className="flex items-center justify-between mb-2">
                        <div className="flex items-center space-x-2">
                          {getTestTypeIcon(test.test_type)}
                          <span className="font-medium">{test.name}</span>
                          <Badge variant="outline">{test.category}</Badge>
                        </div>
                        <div className="flex items-center space-x-2">
                          {getSeverityIcon(test.severity)}
                          <Badge className={getRiskColor(test.severity)}>
                            {test.severity}
                          </Badge>
                        </div>
                      </div>
                      <p className="text-sm text-muted-foreground mb-2">
                        {test.description}
                      </p>
                      <div className="flex items-center space-x-2 text-xs text-muted-foreground">
                        <span>Type: {test.test_type}</span>
                        <span>•</span>
                        <span>Status: {test.enabled ? 'Enabled' : 'Disabled'}</span>
                      </div>
                    </div>
                  ))}
                </div>
              ) : (
                <div className="text-center py-8">
                  <TestTube className="h-12 w-12 text-muted-foreground mx-auto mb-4" />
                  <p className="text-muted-foreground">No tests available.</p>
                </div>
              )}
            </CardContent>
          </Card>
        </TabsContent>
      </Tabs>
    </div>
  )
}
