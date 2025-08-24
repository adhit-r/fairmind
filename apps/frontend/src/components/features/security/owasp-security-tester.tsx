"use client"

import React, { useState, useEffect } from 'react'
import { Card, Button, StatusBadge } from '@/components/spectrum2'
import { 
  Shield, 
  AlertTriangle, 
  CheckCircle, 
  XCircle, 
  Info, 
  BarChart3, 
  PieChart, 
  LineChart, 
  TrendingUp, 
  TrendingDown, 
  Users, 
  Target, 
  Eye, 
  FileText, 
  Download, 
  Upload, 
  Search, 
  Filter, 
  Settings, 
  RefreshCw, 
  Play, 
  Pause, 
  Clock, 
  Database, 
  Brain, 
  Zap, 
  Activity, 
  ChevronRight, 
  ChevronDown, 
  HelpCircle, 
  BookOpen, 
  Video, 
  MessageSquare, 
  Mail, 
  Bell, 
  User, 
  LogOut, 
  Home, 
  Lock,
  Cpu,
  Globe,
  Scale,
  Bug,
  AlertCircle,
  CheckSquare,
  Square
} from 'lucide-react'
import { api } from '@/config/api'

interface SecurityAnalysisResult {
  analysis_id: string
  model_id: string
  overall_score: number
  risk_level: 'low' | 'medium' | 'high' | 'critical'
  total_tests: number
  passed_tests: number
  failed_tests: number
  warning_tests: number
  critical_issues: number
  high_issues: number
  medium_issues: number
  low_issues: number
  test_results: Array<{
    test_id: string
    category: string
    name: string
    description: string
    severity: string
    status: 'passed' | 'failed' | 'warning' | 'error'
    details: any
    recommendations: string[]
  }>
  summary: {
    model_info: {
      id: string
      name: string
      version: string
      type: string
      framework: string
      risk_profile: string
    }
    test_coverage: {
      total_tests: number
      categories_tested: string[]
      automated_tests: number
      manual_tests: number
      advanced_patterns_tested: number
      ml_analysis_performed: boolean
    }
    threat_landscape: Record<string, number>
    performance_metrics: {
      test_duration: number
      cache_hits: number
      cache_misses: number
      concurrent_tests: number
      throughput: number
    }
    compliance_mapping: Record<string, any>
  }
  recommendations: string[]
  timestamp: string
}

interface Model {
  id: string
  name: string
  type: 'llm' | 'classic_ml'
  framework: string
  version: string
  status: string
}

interface SecurityTest {
  id: string
  category: string
  name: string
  description: string
  severity: 'critical' | 'high' | 'medium' | 'low'
  test_type: 'automated' | 'manual'
}

export function OWASPSecurityTester() {
  const [isLoading, setIsLoading] = useState(false)
  const [error, setError] = useState<string | null>(null)
  const [selectedModel, setSelectedModel] = useState<string>('')
  const [selectedTests, setSelectedTests] = useState<string[]>([])
  const [selectedCategories, setSelectedCategories] = useState<string[]>([])
  const [analysisResult, setAnalysisResult] = useState<SecurityAnalysisResult | null>(null)
  const [availableModels, setAvailableModels] = useState<Model[]>([])
  const [availableTests, setAvailableTests] = useState<SecurityTest[]>([])
  const [analysisHistory, setAnalysisHistory] = useState<SecurityAnalysisResult[]>([])
  const [testMode, setTestMode] = useState<'comprehensive' | 'targeted'>('comprehensive')

  useEffect(() => {
    loadInitialData()
  }, [])

  const loadInitialData = async () => {
    try {
      // Load models and tests in parallel
      const [modelsResponse, testsResponse] = await Promise.all([
        api.getModels(),
        api.getSecurityTests?.() || Promise.resolve([])
      ])

      // Map API response to local Model interface
      const mappedModels = (modelsResponse?.data || []).map((apiModel: any) => ({
        id: apiModel.id,
        name: apiModel.name,
        type: apiModel.type || 'classic_ml',
        framework: apiModel.framework || '',
        version: apiModel.version || '',
        status: 'active'
      }))
      setAvailableModels(mappedModels)
      // Map API response to local SecurityTest interface
      const mappedTests = (testsResponse?.data || []).map((apiTest: any) => ({
        id: apiTest.id,
        name: apiTest.name,
        category: apiTest.category,
        description: apiTest.description,
        severity: apiTest.severity,
        test_type: 'automated' as const
      }))
      setAvailableTests(mappedTests)
    } catch (err) {
      console.error('Error loading initial data:', err)
      setError('Failed to load models and security tests')
    }
  }

  const runSecurityAnalysis = async () => {
    if (!selectedModel) {
      setError('Please select a model to test')
      return
    }

    setIsLoading(true)
    setError(null)

    try {
      const request = {
        modelId: selectedModel,
        testMode: testMode,
        testCategories: testMode === 'targeted' ? selectedCategories : undefined,
        testIds: testMode === 'targeted' ? selectedTests : undefined
      }

      const result = await api.runSecurityAnalysis(request)
      
      if (result?.success && result.data) {
        // Map API response to local SecurityAnalysisResult interface
        const mappedResult = {
          analysis_id: result.data.id,
          model_id: result.data.modelId,
          overall_score: result.data.overallScore,
          risk_level: result.data.riskLevel,
          total_tests: result.data.testSummary.totalTests,
          passed_tests: result.data.testSummary.passedTests,
          failed_tests: result.data.testSummary.failedTests,
          warning_tests: result.data.testSummary.skippedTests,
          critical_issues: result.data.issueBreakdown.critical,
          high_issues: result.data.issueBreakdown.high,
          medium_issues: result.data.issueBreakdown.medium,
          low_issues: result.data.issueBreakdown.low,
          test_results: result.data.testResults.map((test: any) => ({
            test_id: test.testId,
            category: test.category || 'general',
            name: test.testName,
            description: test.description,
            severity: test.severity,
            status: test.status,
            details: {},
            recommendations: test.recommendations
          })),
          summary: {
            model_info: {
              id: result.data.modelId,
              name: result.data.modelName,
              version: '1.0.0',
              type: 'unknown',
              framework: 'unknown',
              risk_profile: result.data.riskLevel
            },
            test_coverage: {
              total_tests: result.data.testSummary.totalTests,
              categories_tested: [],
              automated_tests: result.data.testSummary.passedTests + result.data.testSummary.failedTests,
              manual_tests: 0,
              advanced_patterns_tested: 0,
              ml_analysis_performed: false
            },
            threat_landscape: {},
            performance_metrics: {
              test_duration: result.data.performanceMetrics.executionTime,
              cache_hits: 0,
              cache_misses: 0,
              concurrent_tests: 1,
              throughput: 1.0
            },
            compliance_mapping: {}
          },
          recommendations: result.data.recommendations || [],
          timestamp: result.data.createdAt,
          severity: result.data.riskLevel
        }
        setAnalysisResult(mappedResult)
        setAnalysisHistory(prev => [mappedResult, ...prev.slice(0, 9)]) // Keep last 10
      } else {
        setError('Security analysis failed')
      }
    } catch (err) {
      console.error('Error running security analysis:', err)
      setError('Failed to run security analysis')
    } finally {
      setIsLoading(false)
    }
  }

  const getRiskLevelColor = (riskLevel: string) => {
    switch (riskLevel) {
      case 'low': return 'var(--spectrum-green-600)'
      case 'medium': return 'var(--spectrum-orange-600)'
      case 'high': return 'var(--spectrum-red-600)'
      case 'critical': return 'var(--spectrum-red-800)'
      default: return 'var(--spectrum-gray-400)'
    }
  }

  const getSeverityIcon = (severity: string) => {
    switch (severity) {
      case 'critical': return <XCircle size={16} style={{ color: 'var(--spectrum-red-800)' }} />
      case 'high': return <AlertTriangle size={16} style={{ color: 'var(--spectrum-red-600)' }} />
      case 'medium': return <AlertCircle size={16} style={{ color: 'var(--spectrum-orange-600)' }} />
      case 'low': return <Info size={16} style={{ color: 'var(--spectrum-blue-600)' }} />
      default: return <Info size={16} />
    }
  }

  const getStatusIcon = (status: string) => {
    switch (status) {
      case 'passed': return <CheckCircle size={16} style={{ color: 'var(--spectrum-green-600)' }} />
      case 'failed': return <XCircle size={16} style={{ color: 'var(--spectrum-red-600)' }} />
      case 'warning': return <AlertTriangle size={16} style={{ color: 'var(--spectrum-orange-600)' }} />
      case 'error': return <XCircle size={16} style={{ color: 'var(--spectrum-red-600)' }} />
      default: return <Info size={16} />
    }
  }

  const formatDate = (dateString: string) => {
    return new Date(dateString).toLocaleDateString('en-US', {
      month: 'short',
      day: 'numeric',
      hour: '2-digit',
      minute: '2-digit'
    })
  }

  const formatDuration = (seconds: number) => {
    if (seconds < 60) return `${seconds.toFixed(1)}s`
    const minutes = Math.floor(seconds / 60)
    const remainingSeconds = seconds % 60
    return `${minutes}m ${remainingSeconds.toFixed(0)}s`
  }

  return (
    <div className="spectrum-container">
      {/* Header */}
      <div className="spectrum-section">
        <div className="spectrum-flex spectrum-flex--justify-between spectrum-flex--align-center mb-6">
          <div>
            <h1 className="spectrum-heading spectrum-heading--size-xxl spectrum-text-gray-900 mb-2">
              OWASP Security Testing
            </h1>
            <p className="spectrum-body spectrum-text-gray-600">
              Comprehensive AI/LLM security testing with OWASP Top 10 coverage
            </p>
          </div>
          
          <div className="spectrum-flex spectrum-flex--gap-200">
            <Button variant="secondary" icon={<RefreshCw size={16} />} onClick={loadInitialData}>
              Refresh
            </Button>
            <Button variant="primary" icon={<Shield size={16} />} onClick={runSecurityAnalysis} disabled={isLoading}>
              {isLoading ? 'Testing...' : 'Run Security Test'}
            </Button>
          </div>
        </div>
      </div>

      {/* Error Display */}
      {error && (
        <Card className="spectrum-card spectrum-card--negative mb-6">
          <div className="spectrum-flex spectrum-flex--align-center spectrum-flex--gap-200">
            <AlertTriangle size={20} />
            <span>{error}</span>
          </div>
        </Card>
      )}

      {/* Configuration Section */}
      <Card className="spectrum-card mb-6">
        <div className="spectrum-card-header">
          <h2 className="spectrum-heading spectrum-heading--size-l">Test Configuration</h2>
        </div>
        <div className="spectrum-card-body">
          <div className="spectrum-grid spectrum-grid--cols-2 spectrum-grid--gap-400">
            
            {/* Test Mode Selection */}
            <div className="spectrum-field">
              <label className="spectrum-field-label">Test Mode</label>
              <div className="spectrum-flex spectrum-flex--gap-200">
                <Button 
                  variant={testMode === 'comprehensive' ? 'primary' : 'secondary'}
                  icon={<Shield size={16} />}
                  onClick={() => setTestMode('comprehensive')}
                >
                  Comprehensive
                </Button>
                <Button 
                  variant={testMode === 'targeted' ? 'primary' : 'secondary'}
                  icon={<Target size={16} />}
                  onClick={() => setTestMode('targeted')}
                >
                  Targeted
                </Button>
              </div>
            </div>

            {/* Model Selection */}
            <div className="spectrum-field">
              <label className="spectrum-field-label">Select Model</label>
              <select 
                className="spectrum-select"
                value={selectedModel}
                onChange={(e) => setSelectedModel(e.target.value)}
              >
                <option value="">Choose a model...</option>
                {availableModels.map(model => (
                  <option key={model.id} value={model.id}>
                    {model.name} ({model.type}) - {model.framework}
                  </option>
                ))}
              </select>
            </div>

            {/* Targeted Test Configuration */}
            {testMode === 'targeted' && (
              <>
                <div className="spectrum-field">
                  <label className="spectrum-field-label">Security Categories</label>
                  <div className="spectrum-flex spectrum-flex--wrap spectrum-flex--gap-100">
                    {['A01_2023_Prompt_Injection', 'A02_2023_Output_Manipulation', 'A03_2023_Training_Data_Poisoning', 'A04_2023_Model_Theft', 'A05_2023_Supply_Chain_Attacks', 'A06_2023_Permissions', 'A07_2023_Insufficient_Logging', 'A08_2023_Data_Leakage', 'A09_2023_Overreliance', 'A10_2023_Model_Inversion'].map(category => (
                      <Button
                        key={category}
                        variant={selectedCategories.includes(category) ? 'primary' : 'secondary'}
                        size="s"
                        onClick={() => {
                          setSelectedCategories(prev => 
                            prev.includes(category) 
                              ? prev.filter(c => c !== category)
                              : [...prev, category]
                          )
                        }}
                      >
                        {category.replace(/_/g, ' ')}
                      </Button>
                    ))}
                  </div>
                </div>

                <div className="spectrum-field">
                  <label className="spectrum-field-label">Specific Tests</label>
                  <div className="spectrum-flex spectrum-flex--wrap spectrum-flex--gap-100">
                    {availableTests.map(test => (
                      <Button
                        key={test.id}
                        variant={selectedTests.includes(test.id) ? 'primary' : 'secondary'}
                        size="s"
                        onClick={() => {
                          setSelectedTests(prev => 
                            prev.includes(test.id) 
                              ? prev.filter(t => t !== test.id)
                              : [...prev, test.id]
                          )
                        }}
                      >
                        {test.name}
                      </Button>
                    ))}
                  </div>
                </div>
              </>
            )}
          </div>
        </div>
      </Card>

      {/* Analysis Results */}
      {analysisResult && (
        <div className="spectrum-section">
          <Card className="spectrum-card mb-6">
            <div className="spectrum-card-header">
              <div className="spectrum-flex spectrum-flex--justify-between spectrum-flex--align-center">
                <h2 className="spectrum-heading spectrum-heading--size-l">Security Analysis Results</h2>
                <div className="spectrum-flex spectrum-flex--align-center spectrum-flex--gap-200">
                  <StatusBadge 
                    status={analysisResult.risk_level === 'low' ? 'success' : analysisResult.risk_level === 'medium' ? 'warning' : 'error'}
                  >
                    {analysisResult.risk_level.toUpperCase()}
                  </StatusBadge>
                  <span 
                    className="spectrum-text spectrum-text--size-s"
                    style={{ color: getRiskLevelColor(analysisResult.risk_level) }}
                  >
                    Score: {analysisResult.overall_score.toFixed(1)}%
                  </span>
                </div>
              </div>
            </div>
            <div className="spectrum-card-body">
              
              {/* Model Info */}
              <div className="spectrum-flex spectrum-flex--justify-between spectrum-flex--align-center mb-6">
                <div>
                  <h3 className="spectrum-heading spectrum-heading--size-m">Model Security Assessment</h3>
                  <p className="spectrum-body spectrum-text-gray-600">
                    {analysisResult.summary.model_info.name} v{analysisResult.summary.model_info.version} - {formatDate(analysisResult.timestamp)}
                  </p>
                </div>
                <div className="spectrum-text spectrum-text--size-xxl spectrum-text--bold" 
                     style={{ color: getRiskLevelColor(analysisResult.risk_level) }}>
                  {analysisResult.overall_score.toFixed(1)}%
                </div>
              </div>

              {/* Test Summary */}
              <div className="spectrum-grid spectrum-grid--cols-4 spectrum-grid--gap-400 mb-6">
                <Card className="spectrum-card">
                  <div className="spectrum-card-body text-center">
                    <div className="spectrum-text spectrum-text--size-xl spectrum-text--bold" style={{ color: 'var(--spectrum-green-600)' }}>
                      {analysisResult.passed_tests}
                    </div>
                    <div className="spectrum-text spectrum-text--size-s">Passed</div>
                  </div>
                </Card>
                <Card className="spectrum-card">
                  <div className="spectrum-card-body text-center">
                    <div className="spectrum-text spectrum-text--size-xl spectrum-text--bold" style={{ color: 'var(--spectrum-red-600)' }}>
                      {analysisResult.failed_tests}
                    </div>
                    <div className="spectrum-text spectrum-text--size-s">Failed</div>
                  </div>
                </Card>
                <Card className="spectrum-card">
                  <div className="spectrum-card-body text-center">
                    <div className="spectrum-text spectrum-text--size-xl spectrum-text--bold" style={{ color: 'var(--spectrum-orange-600)' }}>
                      {analysisResult.warning_tests}
                    </div>
                    <div className="spectrum-text spectrum-text--size-s">Warnings</div>
                  </div>
                </Card>
                <Card className="spectrum-card">
                  <div className="spectrum-card-body text-center">
                    <div className="spectrum-text spectrum-text--size-xl spectrum-text--bold" style={{ color: 'var(--spectrum-blue-600)' }}>
                      {analysisResult.total_tests}
                    </div>
                    <div className="spectrum-text spectrum-text--size-s">Total</div>
                  </div>
                </Card>
              </div>

              {/* Issue Breakdown */}
              <div className="spectrum-grid spectrum-grid--cols-4 spectrum-grid--gap-400 mb-6">
                <Card className="spectrum-card">
                  <div className="spectrum-card-body text-center">
                    <div className="spectrum-text spectrum-text--size-xl spectrum-text--bold" style={{ color: 'var(--spectrum-red-800)' }}>
                      {analysisResult.critical_issues}
                    </div>
                    <div className="spectrum-text spectrum-text--size-s">Critical</div>
                  </div>
                </Card>
                <Card className="spectrum-card">
                  <div className="spectrum-card-body text-center">
                    <div className="spectrum-text spectrum-text--size-xl spectrum-text--bold" style={{ color: 'var(--spectrum-red-600)' }}>
                      {analysisResult.high_issues}
                    </div>
                    <div className="spectrum-text spectrum-text--size-s">High</div>
                  </div>
                </Card>
                <Card className="spectrum-card">
                  <div className="spectrum-card-body text-center">
                    <div className="spectrum-text spectrum-text--size-xl spectrum-text--bold" style={{ color: 'var(--spectrum-orange-600)' }}>
                      {analysisResult.medium_issues}
                    </div>
                    <div className="spectrum-text spectrum-text--size-s">Medium</div>
                  </div>
                </Card>
                <Card className="spectrum-card">
                  <div className="spectrum-card-body text-center">
                    <div className="spectrum-text spectrum-text--size-xl spectrum-text--bold" style={{ color: 'var(--spectrum-blue-600)' }}>
                      {analysisResult.low_issues}
                    </div>
                    <div className="spectrum-text spectrum-text--size-s">Low</div>
                  </div>
                </Card>
              </div>

              {/* Performance Metrics */}
              <div className="spectrum-field mb-6">
                <label className="spectrum-field-label">Performance Metrics</label>
                <div className="spectrum-grid spectrum-grid--cols-4 spectrum-grid--gap-400">
                  <div className="spectrum-text spectrum-text--size-s">
                    <strong>Duration:</strong> {formatDuration(analysisResult.summary.performance_metrics.test_duration)}
                  </div>
                  <div className="spectrum-text spectrum-text--size-s">
                    <strong>Cache Hit Rate:</strong> {((analysisResult.summary.performance_metrics.cache_hits / (analysisResult.summary.performance_metrics.cache_hits + analysisResult.summary.performance_metrics.cache_misses)) * 100).toFixed(1)}%
                  </div>
                  <div className="spectrum-text spectrum-text--size-s">
                    <strong>Concurrent Tests:</strong> {analysisResult.summary.performance_metrics.concurrent_tests}
                  </div>
                  <div className="spectrum-text spectrum-text--size-s">
                    <strong>Throughput:</strong> {analysisResult.summary.performance_metrics.throughput.toFixed(1)} tests/s
                  </div>
                </div>
              </div>

              {/* Test Results */}
              <div className="spectrum-field">
                <label className="spectrum-field-label">Test Results</label>
                <div className="spectrum-list">
                  {analysisResult.test_results.map((test) => (
                    <div key={test.test_id} className="spectrum-list-item">
                      <div className="spectrum-flex spectrum-flex--justify-between spectrum-flex--align-center">
                        <div className="spectrum-flex spectrum-flex--align-center spectrum-flex--gap-200">
                          {getStatusIcon(test.status)}
                          <div>
                            <div className="spectrum-text spectrum-text--bold">{test.name}</div>
                            <div className="spectrum-text spectrum-text--size-s spectrum-text-gray-600">
                              {test.category.replace(/_/g, ' ')}
                            </div>
                          </div>
                        </div>
                        <div className="spectrum-flex spectrum-flex--align-center spectrum-flex--gap-200">
                          {getSeverityIcon(test.severity)}
                          <StatusBadge 
                            status={test.status === 'passed' ? 'success' : test.status === 'failed' ? 'error' : 'warning'}
                          >
                            {test.status.toUpperCase()}
                          </StatusBadge>
                        </div>
                      </div>
                      {test.recommendations.length > 0 && (
                        <div className="spectrum-text spectrum-text--size-s spectrum-text-gray-600 mt-2">
                          <strong>Recommendations:</strong> {test.recommendations.join(', ')}
                        </div>
                      )}
                    </div>
                  ))}
                </div>
              </div>

              {/* Recommendations */}
              <div className="spectrum-field">
                <label className="spectrum-field-label">Security Recommendations</label>
                <div className="spectrum-list">
                  {analysisResult.recommendations.map((rec, index) => (
                    <div key={index} className="spectrum-list-item">
                      <div className="spectrum-flex spectrum-flex--align-center spectrum-flex--gap-200">
                        <Info size={16} style={{ color: 'var(--spectrum-blue-600)' }} />
                        <span>{rec}</span>
                      </div>
                    </div>
                  ))}
                </div>
              </div>
            </div>
          </Card>
        </div>
      )}

      {/* Analysis History */}
      {analysisHistory.length > 0 && (
        <div className="spectrum-section">
          <Card className="spectrum-card">
            <div className="spectrum-card-header">
              <h2 className="spectrum-heading spectrum-heading--size-l">Security Analysis History</h2>
            </div>
            <div className="spectrum-card-body">
              <div className="spectrum-list">
                {analysisHistory.map((result) => (
                  <div key={result.analysis_id} className="spectrum-list-item">
                    <div className="spectrum-flex spectrum-flex--justify-between spectrum-flex--align-center">
                      <div>
                        <div className="spectrum-text spectrum-text--bold">{result.summary.model_info.name}</div>
                        <div className="spectrum-text spectrum-text--size-s spectrum-text-gray-600">
                          {formatDate(result.timestamp)} - {result.summary.model_info.framework}
                        </div>
                      </div>
                      <div className="spectrum-flex spectrum-flex--align-center spectrum-flex--gap-200">
                        <span 
                          className="spectrum-text spectrum-text--bold"
                          style={{ color: getRiskLevelColor(result.risk_level) }}
                        >
                          {result.overall_score.toFixed(1)}%
                        </span>
                        <StatusBadge 
                          status={result.risk_level === 'low' ? 'success' : result.risk_level === 'medium' ? 'warning' : 'error'}
                        >
                          {result.risk_level.toUpperCase()}
                        </StatusBadge>
                      </div>
                    </div>
                  </div>
                ))}
              </div>
            </div>
          </Card>
        </div>
      )}
    </div>
  )
}
