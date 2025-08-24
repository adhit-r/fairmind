"use client"

import { useState, useEffect } from 'react'
import { 
  AlertTriangle, 
  CheckCircle, 
  Clock, 
  Eye,
  TrendingUp,
  TrendingDown,
  BarChart3,
  Users,
  Target,
  FileText,
  Download,
  RefreshCw,
  Info,
  XCircle,
  AlertCircle,
  Brain,
  Shield,
  Plus,
  Lightbulb,
  TestTube,
  Play,
  Pause,
  Settings,
  Zap,
  Globe,
  Calendar,
  MapPin,
  UserCheck,
  Scale,
  Activity,
  ChevronRight,
  ChevronDown,
  Sparkles,
  Cpu,
  Database,
  BarChart,
  PieChart,
  LineChart,
  ArrowRight,
  Upload,
  Search,
  Filter,
  Star,
  Award,
  Target as TargetIcon,
  Users as UsersIcon,
  Scale as ScaleIcon,
  TrendingUp as TrendingUpIcon
} from "lucide-react"
import { fairmindAPI, Dataset, BiasAnalysisRequest, BiasAnalysisResult } from "@/lib/fairmind-api"

interface AnalysisStep {
  id: string
  name: string
  description: string
  status: 'pending' | 'running' | 'completed' | 'failed'
  progress: number
  details?: any
  error?: string
  icon: any
  estimated_time: string
}

export function ModelSelectionBiasAnalysis() {
  const [datasets, setDatasets] = useState<Dataset[]>([])
  const [selectedDataset, setSelectedDataset] = useState<string>('')
  const [targetColumn, setTargetColumn] = useState<string>('')
  const [sensitiveColumns, setSensitiveColumns] = useState<string[]>([])
  const [availableColumns, setAvailableColumns] = useState<string[]>([])
  const [loading, setLoading] = useState(false)
  const [analysisResult, setAnalysisResult] = useState<BiasAnalysisResult | null>(null)
  const [error, setError] = useState<string>('')
  const [currentStep, setCurrentStep] = useState<'setup' | 'analysis' | 'results'>('setup')
  const [analysisProgress, setAnalysisProgress] = useState(0)

  // Load available datasets
  useEffect(() => {
    const loadDatasets = async () => {
      try {
        setLoading(true)
        const availableDatasets = await fairmindAPI.getAvailableDatasets()
        setDatasets(availableDatasets)
      } catch (err) {
        setError('Failed to load datasets')
        console.error('Error loading datasets:', err)
      } finally {
        setLoading(false)
      }
    }
    loadDatasets()
  }, [])

  // Load dataset columns when dataset is selected
  useEffect(() => {
    if (selectedDataset) {
      const dataset = datasets.find(d => d.name === selectedDataset)
      if (dataset) {
        setAvailableColumns(dataset.columns || [])
        setTargetColumn('')
        setSensitiveColumns([])
      }
    }
  }, [selectedDataset, datasets])

  const handleDatasetSelect = (datasetName: string) => {
    setSelectedDataset(datasetName)
  }

  const handleTargetColumnSelect = (column: string) => {
    setTargetColumn(column)
  }

  const handleSensitiveColumnToggle = (column: string) => {
    setSensitiveColumns(prev => 
      prev.includes(column) 
        ? prev.filter(c => c !== column)
        : [...prev, column]
    )
  }

  const handleStartAnalysis = async () => {
    if (!selectedDataset || !targetColumn || sensitiveColumns.length === 0) {
      setError('Please select a dataset, target column, and at least one sensitive column')
      return
    }

    try {
      setCurrentStep('analysis')
      setAnalysisProgress(0)
      setError('')

      // Simulate progress
      const progressInterval = setInterval(() => {
        setAnalysisProgress(prev => {
          if (prev >= 90) {
            clearInterval(progressInterval)
            return 90
          }
          return prev + 10
        })
      }, 500)

      // Make API call
      const request: BiasAnalysisRequest = {
        dataset_name: selectedDataset,
        target_column: targetColumn,
        sensitive_columns: sensitiveColumns
      }

      const result = await fairmindAPI.analyzeDatasetBias(request)
      setAnalysisResult(result)
      
      clearInterval(progressInterval)
      setAnalysisProgress(100)
      setCurrentStep('results')
    } catch (err) {
      console.error('Analysis failed:', err)
      setError('Analysis failed. Please try again.')
      setCurrentStep('setup')
    }
  }

  const handleReset = () => {
    setSelectedDataset('')
    setTargetColumn('')
    setSensitiveColumns([])
    setAnalysisResult(null)
    setError('')
    setCurrentStep('setup')
    setAnalysisProgress(0)
  }

  const getBiasScoreColor = (score: number) => {
    if (score >= 80) return 'text-green-600'
    if (score >= 60) return 'text-yellow-600'
    return 'text-red-600'
  }

  const getBiasScoreLabel = (score: number) => {
    if (score >= 80) return 'High'
    if (score >= 60) return 'Medium'
    return 'Low'
  }

  return (
    <div className="space-y-8">
      {/* Header */}
      <div className="bg-gradient-to-r from-blue-50 to-purple-50 border-2 border-black rounded-lg p-8 shadow-4px-4px-0px-black">
        <div className="flex items-center justify-between">
          <div>
            <h1 className="text-3xl font-black text-gray-900 mb-2 flex items-center">
              <TestTube className="h-8 w-8 mr-3 text-blue-600" />
              Model Selection Bias Analysis
            </h1>
            <p className="text-lg font-bold text-gray-600 mb-4">
              Analyze your datasets for fairness issues and bias detection.
            </p>
            <div className="flex items-center space-x-4">
              <div className="flex items-center space-x-2 bg-blue-100 border-2 border-black px-3 py-1 rounded-lg">
                <Brain className="h-4 w-4 text-blue-800" />
                <span className="text-sm font-bold text-blue-800">AI-Powered Analysis</span>
              </div>
              <div className="flex items-center space-x-2 bg-green-100 border-2 border-black px-3 py-1 rounded-lg">
                <Shield className="h-4 w-4 text-green-800" />
                <span className="text-sm font-bold text-green-800">Compliance Ready</span>
              </div>
            </div>
          </div>
          <div className="hidden md:block">
            <div className="w-20 h-20 bg-gradient-to-br from-red-600 to-orange-600 rounded-lg border-2 border-black shadow-4px-4px-0px-black flex items-center justify-center">
              <AlertTriangle className="h-10 w-10 text-white" />
            </div>
          </div>
        </div>
      </div>

      {/* Error Display */}
      {error && (
        <div className="bg-red-50 border-2 border-red-300 rounded-lg p-4">
          <div className="flex items-center">
            <AlertTriangle className="h-5 w-5 text-red-600 mr-2" />
            <span className="font-bold text-red-800">{error}</span>
          </div>
        </div>
      )}

      {/* Main Content */}
      <div className="space-y-6">
        {currentStep === 'setup' && (
          <div className="space-y-6">
            {/* Step 1: Dataset Selection */}
            <div className="bg-white border-2 border-black rounded-lg p-6 shadow-4px-4px-0px-black">
              <h2 className="text-xl font-black text-gray-900 mb-6 flex items-center">
                <Database className="h-6 w-6 mr-3 text-blue-600" />
                Step 1: Select Dataset
              </h2>
              
              {loading ? (
                <div className="space-y-4">
                  {[1, 2].map((i) => (
                    <div key={i} className="animate-pulse">
                      <div className="h-20 bg-gray-200 rounded-lg"></div>
                    </div>
                  ))}
                </div>
              ) : (
                <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                  {datasets.map((dataset) => (
                    <div
                      key={dataset.name}
                      onClick={() => handleDatasetSelect(dataset.name)}
                      className={`p-6 border-2 rounded-lg cursor-pointer transition-all duration-200 ${
                        selectedDataset === dataset.name
                          ? 'border-blue-500 bg-blue-50 shadow-4px-4px-0px-black'
                          : 'border-gray-300 bg-white hover:border-gray-400 shadow-2px-2px-0px-black'
                      }`}
                    >
                      <div className="flex items-center justify-between mb-3">
                        <h3 className="font-black text-gray-900">{dataset.name}</h3>
                        <div className="text-sm font-bold text-gray-600">
                          {dataset.samples.toLocaleString()} samples
                        </div>
                      </div>
                      <p className="text-sm font-bold text-gray-600 mb-3">{dataset.description}</p>
                      <div className="flex flex-wrap gap-2">
                        {dataset.columns?.slice(0, 3).map((column) => (
                          <span key={column} className="px-2 py-1 bg-gray-100 text-xs font-bold text-gray-700 rounded border">
                            {column}
                          </span>
                        ))}
                        {dataset.columns && dataset.columns.length > 3 && (
                          <span className="px-2 py-1 bg-gray-100 text-xs font-bold text-gray-700 rounded border">
                            +{dataset.columns.length - 3} more
                          </span>
                        )}
                      </div>
                    </div>
                  ))}
                </div>
              )}
            </div>

            {/* Step 2: Column Selection */}
            {selectedDataset && (
              <div className="bg-white border-2 border-black rounded-lg p-6 shadow-4px-4px-0px-black">
                <h2 className="text-xl font-black text-gray-900 mb-6 flex items-center">
                  <Target className="h-6 w-6 mr-3 text-green-600" />
                  Step 2: Configure Analysis
                </h2>
                
                <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
                  {/* Target Column */}
                  <div>
                    <h3 className="font-black text-gray-900 mb-3">Target Column (What to predict)</h3>
                    <div className="grid grid-cols-2 gap-2">
                      {availableColumns.map((column) => (
                        <button
                          key={column}
                          onClick={() => handleTargetColumnSelect(column)}
                          className={`p-3 border-2 rounded-lg font-bold text-sm transition-all duration-200 ${
                            targetColumn === column
                              ? 'border-green-500 bg-green-50 shadow-2px-2px-0px-black'
                              : 'border-gray-300 bg-white hover:border-gray-400'
                          }`}
                        >
                          {column}
                        </button>
                      ))}
                    </div>
                  </div>

                  {/* Sensitive Columns */}
                  <div>
                    <h3 className="font-black text-gray-900 mb-3">Sensitive Columns (Check for bias)</h3>
                    <div className="grid grid-cols-2 gap-2">
                      {availableColumns.map((column) => (
                        <button
                          key={column}
                          onClick={() => handleSensitiveColumnToggle(column)}
                          className={`p-3 border-2 rounded-lg font-bold text-sm transition-all duration-200 ${
                            sensitiveColumns.includes(column)
                              ? 'border-red-500 bg-red-50 shadow-2px-2px-0px-black'
                              : 'border-gray-300 bg-white hover:border-gray-400'
                          }`}
                        >
                          {column}
                        </button>
                      ))}
                    </div>
                  </div>
                </div>

                {/* Start Analysis Button */}
                <div className="mt-6 flex justify-center">
                  <button
                    onClick={handleStartAnalysis}
                    disabled={!targetColumn || sensitiveColumns.length === 0}
                    className="bg-blue-500 text-white border-2 border-black px-8 py-3 rounded-lg font-bold hover:bg-blue-600 shadow-2px-2px-0px-black transition-all duration-200 disabled:opacity-50 disabled:cursor-not-allowed"
                  >
                    <Play className="h-5 w-5 mr-2" />
                    Start Bias Analysis
                  </button>
                </div>
              </div>
            )}
          </div>
        )}

        {currentStep === 'analysis' && (
          <div className="bg-white border-2 border-black rounded-lg p-12 shadow-4px-4px-0px-black text-center">
            <div className="w-24 h-24 bg-blue-500 border-2 border-black rounded-lg mx-auto mb-6 flex items-center justify-center shadow-4px-4px-0px-black">
              <TestTube className="h-12 w-12 text-white animate-pulse" />
            </div>
            <h2 className="text-2xl font-black text-gray-900 mb-4">Analyzing Dataset for Bias</h2>
            <p className="text-lg font-bold text-gray-600 mb-6">
              Running comprehensive fairness analysis...
            </p>
            
            <div className="w-full bg-gray-200 border border-black rounded-full h-4 mb-4">
              <div 
                className="bg-gradient-to-r from-blue-500 to-green-500 h-4 rounded-full border border-black transition-all duration-500"
                style={{ width: `${analysisProgress}%` }}
              ></div>
            </div>
            <div className="font-bold text-gray-700">{analysisProgress}% Complete</div>
          </div>
        )}

        {currentStep === 'results' && analysisResult && (
          <div className="space-y-6">
            {/* Overall Score */}
            <div className="bg-white border-2 border-black rounded-lg p-8 shadow-4px-4px-0px-black text-center">
              <h2 className="text-2xl font-black text-gray-900 mb-4">Analysis Complete</h2>
              <div className="flex items-center justify-center space-x-6">
                <div className="text-center">
                  <div className={`text-6xl font-black ${getBiasScoreColor(analysisResult.overall_score)}`}>
                    {analysisResult.overall_score}
                  </div>
                  <div className="text-lg font-bold text-gray-600">Overall Score</div>
                </div>
                <div className="text-center">
                  <span className={`px-4 py-2 rounded-lg font-bold text-sm ${
                    analysisResult.overall_score >= 80 ? 'bg-green-100 text-green-800' :
                    analysisResult.overall_score >= 60 ? 'bg-yellow-100 text-yellow-800' :
                    'bg-red-100 text-red-800'
                  }`}>
                    {getBiasScoreLabel(analysisResult.overall_score)} Fairness
                  </span>
                </div>
              </div>
            </div>

            {/* Issues Found */}
            {analysisResult.issues_found.length > 0 && (
              <div className="bg-white border-2 border-black rounded-lg p-6 shadow-4px-4px-0px-black">
                <h3 className="text-xl font-black text-gray-900 mb-4 flex items-center">
                  <AlertTriangle className="h-5 w-5 mr-2 text-red-600" />
                  Bias Issues Detected
                </h3>
                <div className="space-y-4">
                  {analysisResult.issues_found.map((issue, index) => (
                    <div key={index} className="bg-red-50 border-2 border-red-300 rounded-lg p-4">
                      <div className="flex items-center justify-between mb-2">
                        <div className="font-black text-red-800">{issue.type}</div>
                        <span className={`px-2 py-1 rounded text-xs font-bold ${
                          issue.severity === 'critical' ? 'bg-red-500 text-white' :
                          issue.severity === 'high' ? 'bg-orange-500 text-white' :
                          issue.severity === 'medium' ? 'bg-yellow-500 text-white' :
                          'bg-blue-500 text-white'
                        }`}>
                          {issue.severity.toUpperCase()}
                        </span>
                      </div>
                      <p className="text-sm font-bold text-red-700">{issue.description}</p>
                    </div>
                  ))}
                </div>
              </div>
            )}

            {/* Recommendations */}
            {analysisResult.recommendations.length > 0 && (
              <div className="bg-white border-2 border-black rounded-lg p-6 shadow-4px-4px-0px-black">
                <h3 className="text-xl font-black text-gray-900 mb-4 flex items-center">
                  <Lightbulb className="h-5 w-5 mr-2 text-yellow-600" />
                  Recommendations
                </h3>
                <div className="space-y-3">
                  {analysisResult.recommendations.map((recommendation, index) => (
                    <div key={index} className="flex items-start space-x-3">
                      <div className="w-2 h-2 bg-blue-500 rounded-full mt-2 flex-shrink-0"></div>
                      <p className="text-sm font-bold text-gray-700">{recommendation}</p>
                    </div>
                  ))}
                </div>
              </div>
            )}

            {/* Action Buttons */}
            <div className="flex justify-center space-x-4">
              <button className="bg-blue-500 text-white border-2 border-black px-6 py-3 rounded-lg font-bold hover:bg-blue-600 shadow-2px-2px-0px-black transition-all duration-200">
                <Download className="h-4 w-4 mr-2" />
                Download Report
              </button>
              <button className="bg-green-500 text-white border-2 border-black px-6 py-3 rounded-lg font-bold hover:bg-green-600 shadow-2px-2px-0px-black transition-all duration-200">
                <Eye className="h-4 w-4 mr-2" />
                View Details
              </button>
              <button 
                onClick={handleReset}
                className="bg-gray-500 text-white border-2 border-black px-6 py-3 rounded-lg font-bold hover:bg-gray-600 shadow-2px-2px-0px-black transition-all duration-200"
              >
                <RefreshCw className="h-4 w-4 mr-2" />
                New Analysis
              </button>
            </div>
          </div>
        )}
      </div>
    </div>
  )
}
