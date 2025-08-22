"use client"

import { useState, useEffect } from 'react'
import { 
  Brain, 
  TestTube, 
  Play, 
  Pause, 
  Square, 
  RotateCcw, 
  Save, 
  Edit, 
  Trash2, 
  Copy, 
  Share, 
  Bookmark, 
  Tag, 
  Hash, 
  Link, 
  Unlink, 
  GitBranch, 
  GitCommit, 
  GitMerge, 
  GitPullRequest, 
  GitCompare, 
  GitFork, 
  X, 
  CheckCircle, 
  AlertTriangle, 
  Info, 
  HelpCircle, 
  Star, 
  Award, 
  Calendar, 
  MapPin, 
  UserCheck, 
  Scale, 
  ChevronRight, 
  ChevronDown, 
  Sparkles, 
  BarChart, 
  PieChart, 
  LineChart, 
  ArrowRight, 
  FileUp, 
  Search, 
  Filter, 
  Eye, 
  Download, 
  Plus, 
  Settings, 
  RefreshCw, 
  ZoomIn, 
  ZoomOut, 
  Shield,
  Database,
  Cpu,
  Zap,
  Target,
  Users,
  Globe,
  Lock,
  Activity,
  TrendingUp,
  BarChart3,
  FileText,
  Network
} from "lucide-react"
import { fairmindAPI } from "@/lib/fairmind-api"

interface LLMTest {
  id: string
  name: string
  model: string
  test_type: 'prompt_injection' | 'jailbreak' | 'bias' | 'hallucination' | 'privacy' | 'robustness'
  status: 'pending' | 'running' | 'completed' | 'failed'
  results: {
    score: number
    vulnerabilities: string[]
    recommendations: string[]
    test_cases: number
    passed: number
    failed: number
  }
  created_at: string
  updated_at: string
}

export default function LLMTestingPage() {
  const [tests, setTests] = useState<LLMTest[]>([])
  const [loading, setLoading] = useState(true)
  const [selectedTest, setSelectedTest] = useState<LLMTest | null>(null)
  const [searchTerm, setSearchTerm] = useState('')
  const [filterType, setFilterType] = useState('all')
  const [runningTest, setRunningTest] = useState<string | null>(null)

  useEffect(() => {
    loadLLMTests()
  }, [])

  const loadLLMTests = async () => {
    try {
      setLoading(true)
      
      // In a real implementation, this would come from the API
      // For now, we'll generate realistic LLM test data
      const datasets = await fairmindAPI.getAvailableDatasets()
      
      const testTypes = ['prompt_injection', 'jailbreak', 'bias', 'hallucination', 'privacy', 'robustness']
      const mockTests: LLMTest[] = []
      
      datasets.forEach((dataset, index) => {
        testTypes.forEach((testType, testIndex) => {
          const test: LLMTest = {
            id: `test-${index}-${testIndex}`,
            name: `${testType.replace('_', ' ').toUpperCase()} Test - ${dataset.name}`,
            model: `${dataset.name} LLM`,
            test_type: testType as any,
            status: ['pending', 'completed', 'failed'][Math.floor(Math.random() * 3)] as any,
            results: {
              score: Math.random() * 40 + 60, // 60-100
              vulnerabilities: [
                'Potential prompt injection vulnerability detected',
                'Model shows bias towards certain demographics',
                'Privacy concerns with data handling'
              ].slice(0, Math.floor(Math.random() * 3)),
              recommendations: [
                'Implement input validation',
                'Add bias detection mechanisms',
                'Enhance privacy controls'
              ].slice(0, Math.floor(Math.random() * 3)),
              test_cases: Math.floor(Math.random() * 50) + 10,
              passed: Math.floor(Math.random() * 40) + 5,
              failed: Math.floor(Math.random() * 10) + 1
            },
            created_at: new Date(Date.now() - Math.random() * 7 * 24 * 60 * 60 * 1000).toISOString(),
            updated_at: new Date(Date.now() - Math.random() * 24 * 60 * 60 * 1000).toISOString()
          }
          mockTests.push(test)
        })
      })
      
      setTests(mockTests)
    } catch (error) {
      console.error('Error loading LLM tests:', error)
      setTests([])
    } finally {
      setLoading(false)
    }
  }

  const runTest = async (testId: string) => {
    setRunningTest(testId)
    
    // Simulate test execution
    setTimeout(() => {
      setTests(prev => prev.map(test => 
        test.id === testId 
          ? { ...test, status: 'completed', updated_at: new Date().toISOString() }
          : test
      ))
      setRunningTest(null)
    }, 3000)
  }

  const filteredTests = tests.filter(test => {
    const matchesSearch = test.name.toLowerCase().includes(searchTerm.toLowerCase()) ||
                         test.model.toLowerCase().includes(searchTerm.toLowerCase())
    const matchesFilter = filterType === 'all' || test.test_type === filterType
    return matchesSearch && matchesFilter
  })

  const getTestTypeColor = (type: string) => {
    switch (type) {
      case 'prompt_injection': return 'bg-red-500'
      case 'jailbreak': return 'bg-orange-500'
      case 'bias': return 'bg-yellow-500'
      case 'hallucination': return 'bg-purple-500'
      case 'privacy': return 'bg-blue-500'
      case 'robustness': return 'bg-green-500'
      default: return 'bg-gray-500'
    }
  }

  const getStatusColor = (status: string) => {
    switch (status) {
      case 'completed': return 'bg-green-500'
      case 'running': return 'bg-blue-500'
      case 'failed': return 'bg-red-500'
      case 'pending': return 'bg-gray-500'
      default: return 'bg-gray-500'
    }
  }

  const getTestTypeIcon = (type: string) => {
    switch (type) {
      case 'prompt_injection': return Shield
      case 'jailbreak': return AlertTriangle
      case 'bias': return Scale
      case 'hallucination': return Brain
      case 'privacy': return Lock
      case 'robustness': return Cpu
      default: return TestTube
    }
  }

  return (
    <div className="space-y-8">
      {/* Header */}
      <div className="bg-gradient-to-r from-blue-50 to-purple-50 border-2 border-black rounded-lg p-8 shadow-4px-4px-0px-black">
        <div className="flex items-center justify-between">
          <div>
            <h1 className="text-3xl font-black text-gray-900 mb-2 flex items-center">
              <TestTube className="h-8 w-8 mr-3 text-blue-600" />
              LLM Security Testing
            </h1>
            <p className="text-lg font-bold text-gray-600 mb-4">
              Comprehensive testing for LLM vulnerabilities, bias, and security issues.
            </p>
            <div className="flex items-center space-x-4">
              <div className="flex items-center space-x-2 bg-blue-100 border-2 border-black px-3 py-1 rounded-lg">
                <TestTube className="h-4 w-4 text-blue-800" />
                <span className="text-sm font-bold text-blue-800">{tests.length} Tests</span>
              </div>
              <div className="flex items-center space-x-2 bg-green-100 border-2 border-black px-3 py-1 rounded-lg">
                <Shield className="h-4 w-4 text-green-800" />
                <span className="text-sm font-bold text-green-800">Security Focused</span>
              </div>
              <button 
                onClick={loadLLMTests}
                disabled={loading}
                className="flex items-center space-x-2 bg-white border-2 border-black px-3 py-1 rounded-lg hover:bg-gray-50 shadow-2px-2px-0px-black transition-all duration-200 disabled:opacity-50"
              >
                <RefreshCw className={`h-4 w-4 text-gray-700 ${loading ? 'animate-spin' : ''}`} />
                <span className="text-sm font-bold text-gray-700">Refresh</span>
              </button>
            </div>
          </div>
          <div className="hidden md:block">
            <div className="w-20 h-20 bg-gradient-to-br from-red-600 to-orange-600 rounded-lg border-2 border-black shadow-4px-4px-0px-black flex items-center justify-center">
              <TestTube className="h-10 w-10 text-white" />
            </div>
          </div>
        </div>
      </div>

      {/* Search and Filters */}
      <div className="bg-white border-2 border-black rounded-lg p-6 shadow-4px-4px-0px-black">
        <div className="flex flex-col md:flex-row gap-4">
          <div className="flex-1">
            <div className="relative">
              <Search className="absolute left-3 top-1/2 transform -translate-y-1/2 h-4 w-4 text-gray-400" />
              <input
                type="text"
                placeholder="Search tests by name or model..."
                value={searchTerm}
                onChange={(e) => setSearchTerm(e.target.value)}
                className="w-full pl-10 pr-4 py-3 border-2 border-gray-300 rounded-lg font-bold focus:border-blue-500 focus:outline-none"
              />
            </div>
          </div>
          <div className="flex gap-2">
            <select
              value={filterType}
              onChange={(e) => setFilterType(e.target.value)}
              className="px-4 py-3 border-2 border-gray-300 rounded-lg font-bold focus:border-blue-500 focus:outline-none"
            >
              <option value="all">All Test Types</option>
              <option value="prompt_injection">Prompt Injection</option>
              <option value="jailbreak">Jailbreak</option>
              <option value="bias">Bias Detection</option>
              <option value="hallucination">Hallucination</option>
              <option value="privacy">Privacy</option>
              <option value="robustness">Robustness</option>
            </select>
            <button className="bg-blue-500 text-white border-2 border-black px-6 py-3 rounded-lg font-bold hover:bg-blue-600 shadow-2px-2px-0px-black transition-all duration-200">
              <Plus className="h-4 w-4 mr-2" />
              New Test
            </button>
          </div>
        </div>
      </div>

      {/* Tests Grid */}
      {loading ? (
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
          {[1, 2, 3, 4, 5, 6].map((i) => (
            <div key={i} className="bg-white border-2 border-black rounded-lg p-6 shadow-4px-4px-0px-black animate-pulse">
              <div className="h-4 bg-gray-200 rounded mb-4"></div>
              <div className="h-3 bg-gray-200 rounded mb-2"></div>
              <div className="h-3 bg-gray-200 rounded w-3/4"></div>
            </div>
          ))}
        </div>
      ) : filteredTests.length > 0 ? (
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
          {filteredTests.map((test) => {
            const IconComponent = getTestTypeIcon(test.test_type)
            return (
              <div
                key={test.id}
                className="bg-white border-2 border-black rounded-lg p-6 shadow-4px-4px-0px-black hover:shadow-6px-6px-0px-black transition-all duration-200"
              >
                <div className="flex items-center justify-between mb-4">
                  <div className="flex items-center space-x-3">
                    <div className={`p-2 rounded-lg border-2 border-black ${getTestTypeColor(test.test_type)}`}>
                      <IconComponent className="h-5 w-5 text-white" />
                    </div>
                    <div>
                      <h3 className="font-black text-gray-900">{test.name}</h3>
                      <p className="text-sm font-bold text-gray-600">{test.model}</p>
                    </div>
                  </div>
                  <div className={`w-3 h-3 rounded-full ${getStatusColor(test.status)}`}></div>
                </div>

                <div className="space-y-3 mb-4">
                  <div className="flex items-center justify-between">
                    <span className="text-sm font-bold text-gray-600">Score</span>
                    <span className="text-lg font-black text-gray-900">{test.results.score.toFixed(1)}%</span>
                  </div>
                  <div className="flex items-center justify-between">
                    <span className="text-sm font-bold text-gray-600">Test Cases</span>
                    <span className="text-sm font-black text-gray-900">{test.results.test_cases}</span>
                  </div>
                  <div className="flex items-center justify-between">
                    <span className="text-sm font-bold text-gray-600">Passed/Failed</span>
                    <span className="text-sm font-black text-gray-900">
                      {test.results.passed}/{test.results.failed}
                    </span>
                  </div>
                </div>

                <div className="flex items-center justify-between">
                  <div className="flex items-center space-x-2">
                    <Calendar className="h-4 w-4 text-gray-400" />
                    <span className="text-xs font-bold text-gray-500">
                      {new Date(test.updated_at).toLocaleDateString()}
                    </span>
                  </div>
                  <div className="flex space-x-2">
                    {test.status === 'pending' && (
                      <button
                        onClick={() => runTest(test.id)}
                        disabled={runningTest === test.id}
                        className="bg-blue-500 text-white border-2 border-black px-3 py-1 rounded-lg font-bold text-sm hover:bg-blue-600 shadow-2px-2px-0px-black transition-all duration-200 disabled:opacity-50"
                      >
                        {runningTest === test.id ? (
                          <RefreshCw className="h-3 w-3 animate-spin" />
                        ) : (
                          <Play className="h-3 w-3" />
                        )}
                      </button>
                    )}
                    <button
                      onClick={() => setSelectedTest(test)}
                      className="bg-gray-500 text-white border-2 border-black px-3 py-1 rounded-lg font-bold text-sm hover:bg-gray-600 shadow-2px-2px-0px-black transition-all duration-200"
                    >
                      <Eye className="h-3 w-3" />
                    </button>
                  </div>
                </div>
              </div>
            )
          })}
        </div>
      ) : (
        <div className="text-center py-12">
          <TestTube className="h-16 w-16 text-gray-400 mx-auto mb-4" />
          <h3 className="text-lg font-black text-gray-900 mb-2">No Tests Found</h3>
          <p className="text-gray-600 font-bold">Try adjusting your search criteria or create a new test.</p>
        </div>
      )}

      {/* Test Details Modal */}
      {selectedTest && (
        <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center p-4 z-50">
          <div className="bg-white border-2 border-black rounded-lg p-8 shadow-4px-4px-0px-black max-w-4xl w-full max-h-[90vh] overflow-y-auto">
            <div className="flex items-center justify-between mb-6">
              <h2 className="text-2xl font-black text-gray-900 flex items-center">
                <TestTube className="h-6 w-6 mr-3 text-blue-600" />
                {selectedTest.name}
              </h2>
              <button
                onClick={() => setSelectedTest(null)}
                className="p-2 rounded-lg border-2 border-black hover:bg-gray-50 shadow-2px-2px-0px-black transition-all duration-200"
              >
                <X className="h-5 w-5 text-gray-700" />
              </button>
            </div>

            <div className="grid grid-cols-1 lg:grid-cols-2 gap-8">
              {/* Test Information */}
              <div className="space-y-6">
                <div>
                  <h3 className="text-lg font-black text-gray-900 mb-4 flex items-center">
                    <Info className="h-5 w-5 mr-2 text-blue-600" />
                    Test Information
                  </h3>
                  <div className="space-y-3">
                    <div className="flex justify-between">
                      <span className="font-bold text-gray-600">Model:</span>
                      <span className="font-black text-gray-900">{selectedTest.model}</span>
                    </div>
                    <div className="flex justify-between">
                      <span className="font-bold text-gray-600">Test Type:</span>
                      <span className="font-black text-gray-900 capitalize">{selectedTest.test_type.replace('_', ' ')}</span>
                    </div>
                    <div className="flex justify-between">
                      <span className="font-bold text-gray-600">Status:</span>
                      <span className={`font-black px-2 py-1 rounded text-sm ${getStatusColor(selectedTest.status)} text-white`}>
                        {selectedTest.status}
                      </span>
                    </div>
                    <div className="flex justify-between">
                      <span className="font-bold text-gray-600">Created:</span>
                      <span className="font-black text-gray-900">{new Date(selectedTest.created_at).toLocaleString()}</span>
                    </div>
                    <div className="flex justify-between">
                      <span className="font-bold text-gray-600">Updated:</span>
                      <span className="font-black text-gray-900">{new Date(selectedTest.updated_at).toLocaleString()}</span>
                    </div>
                  </div>
                </div>

                {/* Test Results */}
                <div>
                  <h3 className="text-lg font-black text-gray-900 mb-4 flex items-center">
                    <BarChart3 className="h-5 w-5 mr-2 text-green-600" />
                    Test Results
                  </h3>
                  <div className="space-y-3">
                    <div className="flex justify-between">
                      <span className="font-bold text-gray-600">Overall Score:</span>
                      <span className="text-2xl font-black text-gray-900">{selectedTest.results.score.toFixed(1)}%</span>
                    </div>
                    <div className="flex justify-between">
                      <span className="font-bold text-gray-600">Test Cases:</span>
                      <span className="font-black text-gray-900">{selectedTest.results.test_cases}</span>
                    </div>
                    <div className="flex justify-between">
                      <span className="font-bold text-gray-600">Passed:</span>
                      <span className="font-black text-green-600">{selectedTest.results.passed}</span>
                    </div>
                    <div className="flex justify-between">
                      <span className="font-bold text-gray-600">Failed:</span>
                      <span className="font-black text-red-600">{selectedTest.results.failed}</span>
                    </div>
                  </div>
                </div>
              </div>

              {/* Vulnerabilities & Recommendations */}
              <div className="space-y-6">
                {selectedTest.results.vulnerabilities.length > 0 && (
                  <div>
                    <h3 className="text-lg font-black text-gray-900 mb-4 flex items-center">
                      <AlertTriangle className="h-5 w-5 mr-2 text-red-600" />
                      Vulnerabilities Detected
                    </h3>
                    <div className="space-y-2">
                      {selectedTest.results.vulnerabilities.map((vuln, index) => (
                        <div key={index} className="p-3 bg-red-50 border-2 border-red-300 rounded-lg">
                          <p className="text-sm font-bold text-red-700">{vuln}</p>
                        </div>
                      ))}
                    </div>
                  </div>
                )}

                {selectedTest.results.recommendations.length > 0 && (
                  <div>
                    <h3 className="text-lg font-black text-gray-900 mb-4 flex items-center">
                      <CheckCircle className="h-5 w-5 mr-2 text-green-600" />
                      Recommendations
                    </h3>
                    <div className="space-y-2">
                      {selectedTest.results.recommendations.map((rec, index) => (
                        <div key={index} className="p-3 bg-green-50 border-2 border-green-300 rounded-lg">
                          <p className="text-sm font-bold text-green-700">{rec}</p>
                        </div>
                      ))}
                    </div>
                  </div>
                )}
              </div>
            </div>

            {/* Action Buttons */}
            <div className="mt-8 flex justify-center space-x-4">
              <button className="bg-blue-500 text-white border-2 border-black px-6 py-3 rounded-lg font-bold hover:bg-blue-600 shadow-2px-2px-0px-black transition-all duration-200">
                <Download className="h-4 w-4 mr-2" />
                Download Report
              </button>
              <button className="bg-green-500 text-white border-2 border-black px-6 py-3 rounded-lg font-bold hover:bg-green-600 shadow-2px-2px-0px-black transition-all duration-200">
                <Play className="h-4 w-4 mr-2" />
                Re-run Test
              </button>
              <button className="bg-purple-500 text-white border-2 border-black px-6 py-3 rounded-lg font-bold hover:bg-purple-600 shadow-2px-2px-0px-black transition-all duration-200">
                <Share className="h-4 w-4 mr-2" />
                Share Results
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  )
}
