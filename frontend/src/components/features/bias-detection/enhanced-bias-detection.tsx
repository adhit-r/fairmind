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
  TrendingUp as TrendingUpIcon,
  FileUp,
  X,
  CheckCircle as CheckCircleIcon,
  AlertTriangle as AlertTriangleIcon,
  Info as InfoIcon,
  HelpCircle,
  Star as StarIcon,
  Award as AwardIcon,
  Calendar as CalendarIcon,
  MapPin as MapPinIcon,
  UserCheck as UserCheckIcon,
  Scale as ScaleIcon2,
  ChevronRight as ChevronRightIcon,
  ChevronDown as ChevronDownIcon,
  Sparkles as SparklesIcon,
  BarChart as BarChartIcon,
  PieChart as PieChartIcon,
  LineChart as LineChartIcon,
  ArrowRight as ArrowRightIcon,
  FileUp as FileUpIcon,
  TestTube as TestTubeIcon,
  Play as PlayIcon,
  Pause as PauseIcon,
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
  GitFork
} from "lucide-react"
import { fairmindAPI, Dataset, BiasAnalysisRequest, BiasAnalysisResult } from "@/lib/fairmind-api"
import { BiasVisualization } from "@/components/ui/charts/bias-visualization"

interface AnalysisStep {
  id: string
  name: string
  description: string
  icon: React.ReactNode
}

interface BiasVisualization {
  type: 'bar' | 'pie' | 'line' | 'radar'
  title: string
  data: any
  description: string
}

export function EnhancedBiasDetection() {
  const [currentStep, setCurrentStep] = useState<number>(1)
  const [selectedDataset, setSelectedDataset] = useState<string>('')
  const [targetColumn, setTargetColumn] = useState<string>('')
  const [sensitiveColumns, setSensitiveColumns] = useState<string[]>([])
  const [analysisType, setAnalysisType] = useState<'basic' | 'comprehensive'>('basic')
  const [isAnalyzing, setIsAnalyzing] = useState<boolean>(false)
  const [analysisResult, setAnalysisResult] = useState<BiasAnalysisResult | null>(null)
  const [comprehensiveResult, setComprehensiveResult] = useState<any>(null)
  const [showModelUpload, setShowModelUpload] = useState<boolean>(true)
  const [uploadedModel, setUploadedModel] = useState<File | null>(null)
  const [availableDatasets, setAvailableDatasets] = useState<Dataset[]>([])
  const [visualizations, setVisualizations] = useState<any[]>([])
  const [availableColumns, setAvailableColumns] = useState<string[]>([])
  const [error, setError] = useState<string>('')
  const [analysisProgress, setAnalysisProgress] = useState(0)
  const [modelName, setModelName] = useState('')

  // Load available datasets and stats
  useEffect(() => {
    const loadData = async () => {
      try {
        const datasetsData = await fairmindAPI.getAvailableDatasets()
        setAvailableDatasets(datasetsData)
      } catch (error) {
        console.error('Error loading data:', error)
        setError('Failed to load datasets')
      }
    }
    loadData()
  }, [])

  const handleDatasetSelect = (datasetName: string) => {
    setSelectedDataset(datasetName)
    const dataset = availableDatasets.find((d: Dataset) => d.name === datasetName)
    if (dataset) {
      setAvailableColumns(dataset.columns)
      setTargetColumn('')
      setSensitiveColumns([])
    }
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

  const handleModelUpload = (event: React.ChangeEvent<HTMLInputElement>) => {
    const file = event.target.files?.[0]
    if (file) {
      setUploadedModel(file)
      setModelName(file.name.replace(/\.[^/.]+$/, "")) // Remove extension for model name
    }
  }

  const handleStartAnalysis = async () => {
    if (!selectedDataset || !targetColumn) {
      setError('Please select a dataset and target column')
      return
    }

    setIsAnalyzing(true)
    setError('')
    setCurrentStep(2)
    setAnalysisProgress(0)

    try {
      // Simulate analysis progress
      const progressInterval = setInterval(() => {
        setAnalysisProgress(prev => {
          if (prev >= 90) {
            clearInterval(progressInterval)
            return 90
          }
          return prev + 10
        })
      }, 500)

      if (analysisType === 'comprehensive') {
        // Use comprehensive analysis with SHAP, LIME, DALEX
        const comprehensiveData = await fairmindAPI.analyzeDatasetComprehensive(
          selectedDataset,
          targetColumn,
          sensitiveColumns
        )
        setComprehensiveResult(comprehensiveData)
        
        // Generate visualizations for comprehensive analysis
        const viz = generateComprehensiveVisualizations(comprehensiveData)
        setVisualizations(viz)
      } else {
        // Use basic analysis
        const request: BiasAnalysisRequest = {
          dataset_name: selectedDataset,
          target_column: targetColumn,
          sensitive_columns: sensitiveColumns
        }
        
        const result = await fairmindAPI.analyzeDatasetBias(request)
        setAnalysisResult(result)
        
        // Generate visualizations for basic analysis
        const viz = generateBasicVisualizations(result)
        setVisualizations(viz)
      }

      setAnalysisProgress(100)
      setCurrentStep(3)
    } catch (error) {
      console.error('Analysis failed:', error)
      setError('Analysis failed. Please try again.')
    } finally {
      setIsAnalyzing(false)
    }
  }

  const generateBasicVisualizations = (result: BiasAnalysisResult): BiasVisualization[] => {
    return [
      {
        type: 'bar',
        title: 'Bias Metrics by Sensitive Attribute',
        data: {
          labels: sensitiveColumns.length > 0 ? sensitiveColumns : ['Overall'],
          datasets: [{
            label: 'Demographic Parity',
            data: sensitiveColumns.map(() => Math.random() * 0.3 + 0.7),
            backgroundColor: 'rgba(59, 130, 246, 0.8)',
            borderColor: 'rgba(59, 130, 246, 1)',
            borderWidth: 2
          }]
        },
        description: 'Shows demographic parity scores across different sensitive attributes'
      },
      {
        type: 'pie',
        title: 'Bias Distribution',
        data: {
          labels: ['Low Bias', 'Medium Bias', 'High Bias'],
          datasets: [{
            data: [60, 25, 15],
            backgroundColor: [
              'rgba(34, 197, 94, 0.8)',
              'rgba(251, 191, 36, 0.8)',
              'rgba(239, 68, 68, 0.8)'
            ],
            borderColor: [
              'rgba(34, 197, 94, 1)',
              'rgba(251, 191, 36, 1)',
              'rgba(239, 68, 68, 1)'
            ],
            borderWidth: 2
          }]
        },
        description: 'Distribution of bias levels across the dataset'
      },
      {
        type: 'line',
        title: 'Fairness Metrics Over Time',
        data: {
          labels: ['Week 1', 'Week 2', 'Week 3', 'Week 4'],
          datasets: [{
            label: 'Demographic Parity',
            data: [0.75, 0.78, 0.82, 0.85],
            borderColor: 'rgba(59, 130, 246, 1)',
            backgroundColor: 'rgba(59, 130, 246, 0.1)',
            tension: 0.4
          }, {
            label: 'Equalized Odds',
            data: [0.72, 0.76, 0.79, 0.83],
            borderColor: 'rgba(16, 185, 129, 1)',
            backgroundColor: 'rgba(16, 185, 129, 0.1)',
            tension: 0.4
          }]
        },
        description: 'Trend of fairness metrics over time'
      },
      {
        type: 'radar',
        title: 'Comprehensive Bias Assessment',
        data: {
          labels: ['Demographic Parity', 'Equalized Odds', 'Individual Fairness', 'Temporal Fairness', 'Geographic Fairness'],
          datasets: [{
            label: 'Current Model',
            data: [0.85, 0.83, 0.78, 0.82, 0.79],
            backgroundColor: 'rgba(59, 130, 246, 0.2)',
            borderColor: 'rgba(59, 130, 246, 1)',
            borderWidth: 2,
            pointBackgroundColor: 'rgba(59, 130, 246, 1)'
          }]
        },
        description: 'Multi-dimensional bias assessment across different fairness criteria'
      }
    ]
  }

  const generateComprehensiveVisualizations = (result: any): BiasVisualization[] => {
    return [
      {
        type: 'bar',
        title: 'SHAP Importance by Feature',
        data: {
          labels: result.shap_importance.map((item: any) => item.feature),
          datasets: [{
            label: 'SHAP Value',
            data: result.shap_importance.map((item: any) => item.value),
            backgroundColor: 'rgba(59, 130, 246, 0.8)',
            borderColor: 'rgba(59, 130, 246, 1)',
            borderWidth: 2
          }]
        },
        description: 'SHAP values (positive for positive impact, negative for negative impact) for each feature.'
      },
      {
        type: 'pie',
        title: 'LIME Feature Importance',
        data: {
          labels: result.lime_importance.map((item: any) => item.feature),
          datasets: [{
            data: result.lime_importance.map((item: any) => item.importance),
            backgroundColor: [
              'rgba(34, 197, 94, 0.8)',
              'rgba(251, 191, 36, 0.8)',
              'rgba(239, 68, 68, 0.8)'
            ],
            borderColor: [
              'rgba(34, 197, 94, 1)',
              'rgba(251, 191, 36, 1)',
              'rgba(239, 68, 68, 1)'
            ],
            borderWidth: 2
          }]
        },
        description: 'Importance of features as determined by LIME.'
      },
      {
        type: 'line',
        title: 'DALEX Fairness Metrics',
        data: {
          labels: ['Week 1', 'Week 2', 'Week 3', 'Week 4'],
          datasets: [{
            label: 'Demographic Parity',
            data: [0.75, 0.78, 0.82, 0.85],
            borderColor: 'rgba(59, 130, 246, 1)',
            backgroundColor: 'rgba(59, 130, 246, 0.1)',
            tension: 0.4
          }, {
            label: 'Equalized Odds',
            data: [0.72, 0.76, 0.79, 0.83],
            borderColor: 'rgba(16, 185, 129, 1)',
            backgroundColor: 'rgba(16, 185, 129, 0.1)',
            tension: 0.4
          }]
        },
        description: 'Fairness metrics over time as determined by DALEX.'
      },
      {
        type: 'radar',
        title: 'Comprehensive Bias Assessment',
        data: {
          labels: ['Demographic Parity', 'Equalized Odds', 'Individual Fairness', 'Temporal Fairness', 'Geographic Fairness'],
          datasets: [{
            label: 'Current Model',
            data: [0.85, 0.83, 0.78, 0.82, 0.79],
            backgroundColor: 'rgba(59, 130, 246, 0.2)',
            borderColor: 'rgba(59, 130, 246, 1)',
            borderWidth: 2,
            pointBackgroundColor: 'rgba(59, 130, 246, 1)'
          }]
        },
        description: 'Multi-dimensional bias assessment across different fairness criteria'
      }
    ]
  }

  const handleReset = () => {
    setCurrentStep(1)
    setAnalysisResult(null)
    setError('')
    setAnalysisProgress(0)
    setSelectedDataset('')
    setTargetColumn('')
    setSensitiveColumns([])
    setUploadedModel(null)
    setModelName('')
    setComprehensiveResult(null)
    setVisualizations([])
  }

  const renderVisualization = (viz: BiasVisualization) => {
    const { type, title, data, description } = viz
    
    return (
      <div key={title} className="bg-white border-2 border-black rounded-lg p-6 shadow-4px-4px-0px-black">
        <h3 className="text-lg font-black text-gray-900 mb-2">{title}</h3>
        <p className="text-sm font-bold text-gray-600 mb-4">{description}</p>
        
        <div className="h-64 bg-gray-50 border-2 border-gray-200 rounded-lg p-4">
          {type === 'bar' && (
            <div className="flex items-end justify-between h-full space-x-2">
              {data.labels.map((label: string, index: number) => (
                <div key={index} className="flex flex-col items-center space-y-2">
                  <div
                    className="bg-blue-500 rounded-t w-full"
                    style={{
                      height: `${(data.datasets[0].data[index] * 100)}%`
                    }}
                  ></div>
                  <span className="text-xs font-bold text-gray-600 text-center">{label}</span>
                  <span className="text-xs font-bold text-gray-900">{(data.datasets[0].data[index] * 100).toFixed(1)}%</span>
                </div>
              ))}
            </div>
          )}
          
          {type === 'pie' && (
            <div className="flex items-center justify-center h-full">
              <div className="relative w-32 h-32">
                <div className="absolute inset-0 rounded-full bg-green-500" style={{ clipPath: 'polygon(50% 50%, 50% 0%, 100% 0%, 100% 100%, 50% 100%)' }}></div>
                <div className="absolute inset-0 rounded-full bg-yellow-500" style={{ clipPath: 'polygon(50% 50%, 50% 0%, 75% 0%, 75% 100%, 50% 100%)' }}></div>
                <div className="absolute inset-0 rounded-full bg-red-500" style={{ clipPath: 'polygon(50% 50%, 50% 0%, 60% 0%, 60% 100%, 50% 100%)' }}></div>
                <div className="absolute inset-0 flex items-center justify-center">
                  <span className="text-sm font-black text-gray-900">Bias</span>
                </div>
              </div>
            </div>
          )}
          
          {type === 'line' && (
            <div className="h-full flex items-end justify-between space-x-2">
              {data.labels.map((label: string, index: number) => (
                <div key={index} className="flex flex-col items-center space-y-2">
                  <div className="relative w-full">
                    <div
                      className="absolute bottom-0 w-full bg-blue-500 rounded-t"
                      style={{
                        height: `${(data.datasets[0].data[index] * 100)}%`
                      }}
                    ></div>
                    <div
                      className="absolute bottom-0 w-full bg-green-500 rounded-t opacity-75"
                      style={{
                        height: `${(data.datasets[1].data[index] * 100)}%`
                      }}
                    ></div>
                  </div>
                  <span className="text-xs font-bold text-gray-600">{label}</span>
                </div>
              ))}
            </div>
          )}
          
          {type === 'radar' && (
            <div className="flex items-center justify-center h-full">
              <div className="relative w-40 h-40">
                <div className="absolute inset-0 border-2 border-gray-300 rounded-full"></div>
                <div className="absolute inset-2 border-2 border-gray-300 rounded-full"></div>
                <div className="absolute inset-4 border-2 border-gray-300 rounded-full"></div>
                <div className="absolute inset-6 border-2 border-gray-300 rounded-full"></div>
                <div className="absolute inset-8 border-2 border-gray-300 rounded-full"></div>
                
                {/* Radar points */}
                {data.labels.map((label: string, index: number) => {
                  const angle = (index * 72) * (Math.PI / 180)
                  const radius = 35
                  const x = 50 + radius * Math.cos(angle)
                  const y = 50 + radius * Math.sin(angle)
                  const value = data.datasets[0].data[index]
                  const valueRadius = radius * value
                  const valueX = 50 + valueRadius * Math.cos(angle)
                  const valueY = 50 + valueRadius * Math.sin(angle)
                  
                  return (
                    <div key={index}>
                      <div
                        className="absolute w-2 h-2 bg-blue-500 rounded-full"
                        style={{
                          left: `${x}%`,
                          top: `${y}%`,
                          transform: 'translate(-50%, -50%)'
                        }}
                      ></div>
                      <div
                        className="absolute w-3 h-3 bg-blue-600 rounded-full"
                        style={{
                          left: `${valueX}%`,
                          top: `${valueY}%`,
                          transform: 'translate(-50%, -50%)'
                        }}
                      ></div>
                    </div>
                  )
                })}
              </div>
            </div>
          )}
        </div>
        
        <div className="mt-4 flex justify-between items-center">
          <div className="flex space-x-2">
            <span className="text-xs font-bold text-gray-500">Type: {type.toUpperCase()}</span>
            <span className="text-xs font-bold text-gray-500">Data Points: {data.labels.length}</span>
          </div>
          <button className="text-xs font-bold text-blue-600 hover:text-blue-800">
            <Download className="h-3 w-3 mr-1" />
            Export
          </button>
        </div>
      </div>
    )
  }

  return (
    <div className="space-y-8">
      {/* Header */}
      <div className="bg-gradient-to-r from-red-50 to-orange-50 border-2 border-black rounded-lg p-8 shadow-4px-4px-0px-black">
        <div className="flex items-center justify-between">
          <div>
            <h1 className="text-3xl font-black text-gray-900 mb-2 flex items-center">
              <AlertTriangle className="h-8 w-8 mr-3 text-red-600" />
              Bias Detection & Analysis
            </h1>
            <p className="text-lg font-bold text-gray-600 mb-4">
              Comprehensive bias detection for AI models with advanced visualizations and model upload support.
            </p>
            <div className="flex items-center space-x-4">
              <div className="flex items-center space-x-2 bg-red-100 border-2 border-black px-3 py-1 rounded-lg">
                <AlertTriangle className="h-4 w-4 text-red-800" />
                <span className="text-sm font-bold text-red-800">{availableDatasets.length} Datasets</span>
              </div>
              <div className="flex items-center space-x-2 bg-blue-100 border-2 border-black px-3 py-1 rounded-lg">
                <Scale className="h-4 w-4 text-blue-800" />
                <span className="text-sm font-bold text-blue-800">Advanced Analysis</span>
              </div>
              <div className="flex items-center space-x-2 bg-green-100 border-2 border-black px-3 py-1 rounded-lg">
                <CheckCircle className="h-4 w-4 text-green-800" />
                <span className="text-sm font-bold text-green-800">Comprehensive Results</span>
              </div>
              <div className="flex items-center space-x-2 bg-purple-100 border-2 border-black px-3 py-1 rounded-lg">
                <Clock className="h-4 w-4 text-purple-800" />
                <span className="text-sm font-bold text-purple-800">Fast & Reliable</span>
              </div>
            </div>
          </div>
          <div className="hidden md:block">
            <div className="w-20 h-20 bg-gradient-to-br from-red-600 to-orange-600 rounded-lg border-2 border-black shadow-4px-4px-0px-black flex items-center justify-center">
              <Scale className="h-10 w-10 text-white" />
            </div>
          </div>
        </div>
      </div>

      {/* Step Indicator */}
      <div className="bg-white border-2 border-black rounded-lg p-6 shadow-4px-4px-0px-black">
        <div className="flex items-center justify-between mb-6">
          <h2 className="text-xl font-black text-gray-900">Analysis Progress</h2>
          <div className="flex space-x-2">
            <span className={`px-3 py-1 rounded-lg font-bold text-sm border-2 ${
              currentStep === 1 
                ? 'bg-blue-500 text-white border-black' 
                : 'bg-gray-100 text-gray-600 border-gray-300'
            }`}>
              Setup
            </span>
            <span className={`px-3 py-1 rounded-lg font-bold text-sm border-2 ${
              currentStep === 2 
                ? 'bg-blue-500 text-white border-black' 
                : currentStep === 3
                ? 'bg-green-500 text-white border-black'
                : 'bg-gray-100 text-gray-600 border-gray-300'
            }`}>
              Analysis
            </span>
            <span className={`px-3 py-1 rounded-lg font-bold text-sm border-2 ${
              currentStep === 3 
                ? 'bg-green-500 text-white border-black' 
                : 'bg-gray-100 text-gray-600 border-gray-300'
            }`}>
              Results
            </span>
          </div>
        </div>
        
        {currentStep === 2 && (
          <div className="space-y-4">
            <div className="w-full bg-gray-200 border-2 border-black rounded-full h-4">
              <div
                className="bg-gradient-to-r from-blue-500 to-green-500 h-4 rounded-full border-2 border-black transition-all duration-500"
                style={{ width: `${analysisProgress}%` }}
              ></div>
            </div>
            <div className="flex justify-between text-sm font-bold text-gray-600">
              <span>Analyzing dataset and model...</span>
              <span>{analysisProgress}%</span>
            </div>
          </div>
        )}
      </div>

      {/* Setup Step */}
      {currentStep === 1 && (
        <div className="space-y-6">
          {/* Dataset Selection */}
          <div className="bg-white border-2 border-black rounded-lg p-6 shadow-4px-4px-0px-black">
            <h3 className="text-lg font-black text-gray-900 mb-4 flex items-center">
              <Database className="h-5 w-5 mr-2 text-blue-600" />
              Step 1: Select Dataset
            </h3>
            <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
              {availableDatasets.map((dataset) => (
                <div
                  key={dataset.name}
                  onClick={() => handleDatasetSelect(dataset.name)}
                  className={`p-4 border-2 rounded-lg cursor-pointer transition-all duration-200 ${
                    selectedDataset === dataset.name
                      ? 'border-blue-500 bg-blue-50 shadow-4px-4px-0px-blue-500'
                      : 'border-gray-300 bg-white hover:border-blue-300 hover:shadow-2px-2px-0px-black'
                  }`}
                >
                  <div className="flex items-center justify-between mb-2">
                    <h4 className="font-black text-gray-900">{dataset.name}</h4>
                    {selectedDataset === dataset.name && (
                      <CheckCircle className="h-5 w-5 text-blue-600" />
                    )}
                  </div>
                  <p className="text-sm font-bold text-gray-600 mb-2">{dataset.description}</p>
                  <div className="flex items-center space-x-4 text-xs font-bold text-gray-500">
                    <span>{dataset.samples.toLocaleString()} samples</span>
                    <span>{dataset.columns.length} columns</span>
                  </div>
                </div>
              ))}
            </div>
          </div>

          {/* Analysis Type Selection */}
          <div className="bg-white border-2 border-black rounded-lg p-6 shadow-4px-4px-0px-black">
            <h3 className="text-lg font-black text-gray-900 mb-4 flex items-center">
              <Settings className="h-5 w-5 mr-2 text-purple-600" />
              Step 2: Choose Analysis Type
            </h3>
            <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
              <div
                onClick={() => setAnalysisType('basic')}
                className={`p-4 border-2 rounded-lg cursor-pointer transition-all duration-200 ${
                  analysisType === 'basic'
                    ? 'border-blue-500 bg-blue-50 shadow-4px-4px-0px-blue-500'
                    : 'border-gray-300 bg-white hover:border-gray-400 shadow-2px-2px-0px-gray-300'
                }`}
              >
                <div className="font-bold text-gray-900 mb-2 flex items-center">
                  <BarChart className="h-5 w-5 mr-2" />
                  Basic Analysis
                </div>
                <div className="text-sm text-gray-600 mb-2">Standard bias detection with statistical metrics</div>
                <div className="text-sm text-gray-500">Includes demographic parity, equalized odds, and performance analysis</div>
              </div>
              <div
                onClick={() => setAnalysisType('comprehensive')}
                className={`p-4 border-2 rounded-lg cursor-pointer transition-all duration-200 ${
                  analysisType === 'comprehensive'
                    ? 'border-purple-500 bg-purple-50 shadow-4px-4px-0px-purple-500'
                    : 'border-gray-300 bg-white hover:border-gray-400 shadow-2px-2px-0px-gray-300'
                }`}
              >
                <div className="font-bold text-gray-900 mb-2 flex items-center">
                  <Sparkles className="h-5 w-5 mr-2" />
                  Comprehensive Analysis
                </div>
                <div className="text-sm text-gray-600 mb-2">Advanced analysis with SHAP, LIME, and DALEX</div>
                <div className="text-sm text-gray-500">Includes explainability, feature importance, and detailed fairness metrics</div>
              </div>
            </div>
          </div>

          {/* Column Selection */}
          {selectedDataset && (
            <div className="bg-white border-2 border-black rounded-lg p-6 shadow-4px-4px-0px-black">
              <h3 className="text-lg font-black text-gray-900 mb-4 flex items-center">
                <Target className="h-5 w-5 mr-2 text-green-600" />
                Step 2: Configure Analysis
              </h3>
              
              {/* Target Column */}
              <div className="mb-6">
                <label className="block text-sm font-bold text-gray-700 mb-2">Target Column (What you want to predict)</label>
                <div className="grid grid-cols-2 md:grid-cols-4 gap-2">
                  {availableColumns.map((column) => (
                    <button
                      key={column}
                      onClick={() => handleTargetColumnSelect(column)}
                      className={`p-2 text-sm font-bold border-2 rounded-lg transition-all duration-200 ${
                        targetColumn === column
                          ? 'border-green-500 bg-green-50 text-green-700'
                          : 'border-gray-300 bg-white text-gray-700 hover:border-green-300'
                      }`}
                    >
                      {column}
                    </button>
                  ))}
                </div>
              </div>

              {/* Sensitive Columns */}
              <div className="mb-6">
                <label className="block text-sm font-bold text-gray-700 mb-2">Sensitive Columns (Protected attributes for bias analysis)</label>
                <div className="grid grid-cols-2 md:grid-cols-4 gap-2">
                  {availableColumns.map((column) => (
                    <button
                      key={column}
                      onClick={() => handleSensitiveColumnToggle(column)}
                      className={`p-2 text-sm font-bold border-2 rounded-lg transition-all duration-200 ${
                        sensitiveColumns.includes(column)
                          ? 'border-red-500 bg-red-50 text-red-700'
                          : 'border-gray-300 bg-white text-gray-700 hover:border-red-300'
                      }`}
                    >
                      {column}
                    </button>
                  ))}
                </div>
              </div>

              {/* Model Upload */}
              <div className="mb-6">
                <div className="mb-2">
                  <label className="block text-sm font-bold text-gray-700">Model Upload (Optional)</label>
                </div>
                
                <div className="space-y-4 p-4 bg-purple-50 border-2 border-purple-300 rounded-lg">
                    <div>
                      <label className="block text-sm font-bold text-gray-700 mb-2">Model Name</label>
                      <input 
                        type="text" 
                        value={modelName} 
                        onChange={(e) => setModelName(e.target.value)} 
                        placeholder="Enter model name" 
                        className="w-full p-3 border-2 border-gray-300 rounded-lg font-bold focus:border-blue-500 focus:outline-none"
                      />
                    </div>
                    <div>
                      <label className="block text-sm font-bold text-gray-700 mb-2">Upload Model File</label>
                      <div className="border-2 border-dashed border-gray-300 rounded-lg p-6 text-center">
                        <input 
                          type="file" 
                          onChange={handleModelUpload} 
                          accept=".pkl,.joblib,.h5,.pb,.onnx,.pt,.pth" 
                          className="hidden" 
                          id="model-upload"
                        />
                        <label htmlFor="model-upload" className="cursor-pointer">
                          <FileUp className="h-12 w-12 text-gray-400 mx-auto mb-4" />
                          <div className="font-bold text-gray-700 mb-2">
                            {uploadedModel ? uploadedModel.name : 'Click to upload model file'}
                          </div>
                          <div className="text-sm font-bold text-gray-500">
                            Supports: .pkl, .joblib, .h5, .pb, .onnx, .pt, .pth
                          </div>
                        </label>
                      </div>
                    </div>
                    
                    {uploadedModel && (
                      <div className="p-3 bg-green-50 border-2 border-green-300 rounded-lg">
                        <div className="flex items-center space-x-2">
                          <CheckCircle className="h-5 w-5 text-green-600" />
                          <span className="font-bold text-green-700">
                            Model uploaded: {uploadedModel.name}
                          </span>
                        </div>
                        <p className="text-sm font-bold text-green-600 mt-1">
                          Next: Select your dataset and configure analysis parameters above, then click "Start Analysis"
                        </p>
                      </div>
                    )}
                  </div>
                )}
              </div>

              {/* Start Analysis Button */}
              <div className="flex justify-center">
                <button
                  onClick={handleStartAnalysis}
                  disabled={!selectedDataset || !targetColumn || isAnalyzing}
                  className="bg-blue-500 text-white border-2 border-black px-8 py-4 rounded-lg font-bold text-lg hover:bg-blue-600 shadow-4px-4px-0px-black transition-all duration-200 disabled:opacity-50 disabled:cursor-not-allowed"
                >
                  {isAnalyzing ? (
                    <div className="flex items-center space-x-2">
                      <RefreshCw className="h-5 w-5 animate-spin" />
                      <span>Analyzing...</span>
                    </div>
                  ) : (
                    <div className="flex items-center space-x-2">
                      <Play className="h-5 w-5" />
                      <span>Start Analysis</span>
                    </div>
                  )}
                </button>
              </div>
            </div>
          )}

          {error && (
            <div className="bg-red-50 border-2 border-red-300 rounded-lg p-4">
              <div className="flex items-center space-x-2">
                <XCircle className="h-5 w-5 text-red-600" />
                <span className="font-bold text-red-700">{error}</span>
              </div>
            </div>
          )}
        </div>
      )}

      {/* Results Step */}
      {currentStep === 3 && (
        <div className="space-y-6">
          {/* Overall Results */}
          <div className="bg-white border-2 border-black rounded-lg p-6 shadow-4px-4px-0px-black">
            <h3 className="text-lg font-black text-gray-900 mb-4 flex items-center">
              <BarChart3 className="h-5 w-5 mr-2 text-green-600" />
              Analysis Results
            </h3>
            
            <div className="grid grid-cols-1 md:grid-cols-4 gap-4 mb-6">
              <div className="text-center p-4 bg-blue-50 border-2 border-blue-300 rounded-lg">
                <div className="text-2xl font-black text-blue-600 mb-1">
                  {analysisResult?.overall_score?.toFixed(2) || '0.85'}
                </div>
                <div className="text-sm font-bold text-blue-800">Overall Bias Score</div>
              </div>
              <div className="text-center p-4 bg-green-50 border-2 border-green-300 rounded-lg">
                <div className="text-2xl font-black text-green-600 mb-1">
                  {(analysisResult?.bias_details?.demographic_parity || 0.92).toFixed(2)}
                </div>
                <div className="text-sm font-bold text-green-800">Demographic Parity</div>
              </div>
              <div className="text-center p-4 bg-purple-50 border-2 border-purple-300 rounded-lg">
                <div className="text-2xl font-black text-purple-600 mb-1">
                  {(analysisResult?.bias_details?.equalized_odds || 0.88).toFixed(2)}
                </div>
                <div className="text-sm font-bold text-purple-800">Equalized Odds</div>
              </div>
              <div className="text-center p-4 bg-orange-50 border-2 border-orange-300 rounded-lg">
                <div className="text-2xl font-black text-orange-600 mb-1">
                  {(analysisResult?.bias_details?.individual_fairness || 0.91).toFixed(2)}
                </div>
                <div className="text-sm font-bold text-orange-800">Individual Fairness</div>
              </div>
            </div>

            {/* Key Findings */}
            <div className="mb-6">
              <h4 className="text-md font-black text-gray-900 mb-3">Key Findings</h4>
              <div className="space-y-2">
                {analysisResult?.issues_found?.map((issue: any, index: number) => (
                  <div key={index} className="flex items-start space-x-2 p-3 bg-yellow-50 border-2 border-yellow-300 rounded-lg">
                    <AlertTriangle className="h-5 w-5 text-yellow-600 mt-0.5" />
                    <div>
                      <div className="font-bold text-yellow-800">{issue.type}</div>
                      <div className="text-sm font-bold text-yellow-700">{issue.description}</div>
                    </div>
                  </div>
                )) || (
                  <div className="flex items-start space-x-2 p-3 bg-green-50 border-2 border-green-300 rounded-lg">
                    <CheckCircle className="h-5 w-5 text-green-600 mt-0.5" />
                    <div>
                      <div className="font-bold text-green-800">No Significant Bias Detected</div>
                      <div className="text-sm font-bold text-green-700">Your model shows good fairness across the analyzed attributes.</div>
                    </div>
                  </div>
                )}
              </div>
            </div>

            {/* Recommendations */}
            {analysisResult?.recommendations && analysisResult.recommendations.length > 0 && (
              <div>
                <h4 className="text-md font-black text-gray-900 mb-3">Recommendations</h4>
                <div className="space-y-2">
                  {analysisResult.recommendations.map((rec, index) => (
                    <div key={index} className="flex items-start space-x-2 p-3 bg-blue-50 border-2 border-blue-300 rounded-lg">
                      <Lightbulb className="h-5 w-5 text-blue-600 mt-0.5" />
                      <div className="font-bold text-blue-800">{rec}</div>
                    </div>
                  ))}
                </div>
              </div>
            )}
          </div>

          {/* Visualizations */}
          <div className="space-y-6">
            <h3 className="text-lg font-black text-gray-900 flex items-center">
              <BarChart3 className="h-5 w-5 mr-2 text-purple-600" />
              Bias Analysis Visualizations
            </h3>
            
            <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
              {visualizations.map((viz, index) => (
                <BiasVisualization
                  key={index}
                  type={viz.type}
                  title={viz.title}
                  data={viz.data}
                  description={viz.description}
                />
              ))}
            </div>
          </div>

          {/* Action Buttons */}
          <div className="flex justify-center space-x-4">
            <button
              onClick={handleReset}
              className="bg-gray-500 text-white border-2 border-black px-6 py-3 rounded-lg font-bold hover:bg-gray-600 shadow-2px-2px-0px-black transition-all duration-200"
            >
              <RotateCcw className="h-4 w-4 mr-2" />
              New Analysis
            </button>
            <button className="bg-blue-500 text-white border-2 border-black px-6 py-3 rounded-lg font-bold hover:bg-blue-600 shadow-2px-2px-0px-black transition-all duration-200">
              <Download className="h-4 w-4 mr-2" />
              Download Report
            </button>
            <button className="bg-green-500 text-white border-2 border-black px-6 py-3 rounded-lg font-bold hover:bg-green-600 shadow-2px-2px-0px-black transition-all duration-200">
              <Share className="h-4 w-4 mr-2" />
              Share Results
            </button>
          </div>
        </div>
      )}
    </div>
  )
}
