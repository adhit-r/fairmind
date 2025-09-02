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
  TrendingDown as TrendingDownIcon,
  CheckCircle as CheckCircleIcon,
  XCircle as XCircleIcon,
  Clock as ClockIcon,
  Cpu,
  Globe,
  Lock,
  Scale
} from 'lucide-react'
import { api } from '@/config/api'

interface BiasAnalysisResult {
  id: string
  modelId: string
  modelName: string
  datasetName: string
  timestamp: string
  overallScore: number
  status: 'good' | 'warning' | 'error'
  modelType: 'llm' | 'classic_ml'
  metrics: {
    demographic_parity?: number
    equalized_odds?: number
    equal_opportunity?: number
    statistical_parity?: number
    weat_score?: number
    seat_score?: number
  }
  biasDetails: {
    bias_types: {
      representational?: any
      allocational?: any
      contextual?: any
      privacy?: any
    }
    high_bias_attributes: string[]
    bias_severity: Record<string, string>
    bias_direction: Record<string, string>
  }
  recommendations: string[]
  risk_level: 'low' | 'medium' | 'high'
}

interface Dataset {
  name: string
  samples: number
  columns: string[]
  description: string
  target_column: string
  sensitive_columns: string[]
}

interface Model {
  id: string
  name: string
  type: 'llm' | 'classic_ml'
  framework: string
  version: string
  status: string
}

export function EnhancedBiasDetection() {
  const [isLoading, setIsLoading] = useState(false)
  const [error, setError] = useState<string | null>(null)
  const [selectedDataset, setSelectedDataset] = useState<string>('')
  const [selectedModel, setSelectedModel] = useState<string>('')
  const [targetColumn, setTargetColumn] = useState<string>('')
  const [sensitiveColumns, setSensitiveColumns] = useState<string[]>([])
  const [analysisResult, setAnalysisResult] = useState<BiasAnalysisResult | null>(null)
  const [availableDatasets, setAvailableDatasets] = useState<Dataset[]>([])
  const [availableModels, setAvailableModels] = useState<Model[]>([])
  const [analysisHistory, setAnalysisHistory] = useState<BiasAnalysisResult[]>([])
  const [modelType, setModelType] = useState<'llm' | 'classic_ml'>('classic_ml')

  useEffect(() => {
    loadInitialData()
  }, [])

  const loadInitialData = async () => {
    try {
      // Load datasets and models in parallel
      const [datasetsResponse, modelsResponse] = await Promise.all([
        api.getBiasDatasets(),
        api.getModels()
      ])

      // Map API response to local Dataset interface
      const mappedDatasets = (datasetsResponse?.data || []).map((apiDataset: any) => ({
        name: apiDataset.name,
        samples: apiDataset.size || 0,
        columns: apiDataset.columns || [],
        description: apiDataset.description || '',
        target_column: '',
        sensitive_columns: []
      }))
      setAvailableDatasets(mappedDatasets)
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
    } catch (err) {
      console.error('Error loading initial data:', err)
      setError('Failed to load datasets and models')
    }
  }

  const runBiasAnalysis = async () => {
    if (!selectedDataset || !selectedModel) {
      setError('Please select both dataset and model')
      return
    }

    setIsLoading(true)
    setError(null)

    try {
      let result: BiasAnalysisResult

             if (modelType === 'llm') {
         // LLM bias analysis
         const llmResponse = await api.analyzeBias({
           modelId: selectedModel,
           datasetId: selectedDataset,
           modelType: 'llm'
         })
         result = llmResponse as unknown as BiasAnalysisResult
       } else {
         // Classic ML bias analysis
         const mlResponse = await api.analyzeBias({
           modelId: selectedModel,
           datasetId: selectedDataset,
           modelType: 'classic_ml',
           targetColumn: targetColumn,
           sensitiveColumns: sensitiveColumns
         })
         result = mlResponse as unknown as BiasAnalysisResult
       }

      setAnalysisResult(result)
      setAnalysisHistory(prev => [result, ...prev.slice(0, 9)]) // Keep last 10
    } catch (err) {
      console.error('Error running bias analysis:', err)
      setError('Failed to run bias analysis')
    } finally {
      setIsLoading(false)
    }
  }

  const getStatusColor = (status: string) => {
    switch (status) {
      case 'good': return 'var(--spectrum-green-600)'
      case 'warning': return 'var(--spectrum-orange-600)'
      case 'error': return 'var(--spectrum-red-600)'
      default: return 'var(--spectrum-gray-400)'
    }
  }

  const getStatusIcon = (status: string) => {
    switch (status) {
      case 'good': return <CheckCircle size={16} />
      case 'warning': return <AlertTriangle size={16} />
      case 'error': return <XCircle size={16} />
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

  const getRiskLevelColor = (riskLevel: string) => {
    switch (riskLevel) {
      case 'low': return 'var(--spectrum-green-600)'
      case 'medium': return 'var(--spectrum-orange-600)'
      case 'high': return 'var(--spectrum-red-600)'
      default: return 'var(--spectrum-gray-400)'
    }
  }

  return (
    <div className="spectrum-container">
      {/* Header */}
      <div className="spectrum-section">
        <div className="spectrum-flex spectrum-flex--justify-between spectrum-flex--align-center mb-6">
          <div>
            <h1 className="spectrum-heading spectrum-heading--size-xxl spectrum-text-gray-900 mb-2">
              Enhanced Bias Detection & Analysis
            </h1>
            <p className="spectrum-body spectrum-text-gray-600">
              Comprehensive fairness analysis for both LLM and classic ML models
            </p>
          </div>
          
          <div className="spectrum-flex spectrum-flex--gap-200">
            <Button variant="secondary" icon={<RefreshCw size={16} />} onClick={loadInitialData}>
              Refresh
            </Button>
            <Button variant="primary" icon={<Play size={16} />} onClick={runBiasAnalysis} disabled={isLoading}>
              {isLoading ? 'Analyzing...' : 'Run Analysis'}
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
          <h2 className="spectrum-heading spectrum-heading--size-l">Analysis Configuration</h2>
        </div>
        <div className="spectrum-card-body">
          <div className="spectrum-grid spectrum-grid--cols-2 spectrum-grid--gap-400">
            
            {/* Model Type Selection */}
            <div className="spectrum-field">
              <label className="spectrum-field-label">Model Type</label>
              <div className="spectrum-flex spectrum-flex--gap-200">
                <Button 
                  variant={modelType === 'classic_ml' ? 'primary' : 'secondary'}
                  icon={<Cpu size={16} />}
                  onClick={() => setModelType('classic_ml')}
                >
                  Classic ML
                </Button>
                <Button 
                  variant={modelType === 'llm' ? 'primary' : 'secondary'}
                  icon={<Brain size={16} />}
                  onClick={() => setModelType('llm')}
                >
                  Language Model
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

            {/* Dataset Selection */}
            <div className="spectrum-field">
              <label className="spectrum-field-label">Select Dataset</label>
              <select 
                className="spectrum-select"
                value={selectedDataset}
                onChange={(e) => setSelectedDataset(e.target.value)}
              >
                <option value="">Choose a dataset...</option>
                {availableDatasets.map(dataset => (
                  <option key={dataset.name} value={dataset.name}>
                    {dataset.name} ({dataset.samples.toLocaleString()} samples)
                  </option>
                ))}
              </select>
            </div>

            {/* Classic ML specific fields */}
            {modelType === 'classic_ml' && (
              <>
                <div className="spectrum-field">
                  <label className="spectrum-field-label">Target Column</label>
                  <select 
                    className="spectrum-select"
                    value={targetColumn}
                    onChange={(e) => setTargetColumn(e.target.value)}
                  >
                    <option value="">Choose target column...</option>
                    {selectedDataset && availableDatasets.find(d => d.name === selectedDataset)?.columns.map(col => (
                      <option key={col} value={col}>{col}</option>
                    ))}
                  </select>
                </div>

                <div className="spectrum-field">
                  <label className="spectrum-field-label">Sensitive Columns</label>
                  <div className="spectrum-flex spectrum-flex--wrap spectrum-flex--gap-100">
                    {selectedDataset && availableDatasets.find(d => d.name === selectedDataset)?.columns.map(col => (
                      <Button
                        key={col}
                        variant={sensitiveColumns.includes(col) ? 'primary' : 'secondary'}
                        size="s"
                        onClick={() => {
                          setSensitiveColumns(prev => 
                            prev.includes(col) 
                              ? prev.filter(c => c !== col)
                              : [...prev, col]
                          )
                        }}
                      >
                        {col}
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
                <h2 className="spectrum-heading spectrum-heading--size-l">Analysis Results</h2>
                <div className="spectrum-flex spectrum-flex--align-center spectrum-flex--gap-200">
                                     <StatusBadge 
                     status={analysisResult.status === 'good' ? 'success' : analysisResult.status}
                   >
                     {analysisResult.status.toUpperCase()}
                   </StatusBadge>
                  <span 
                    className="spectrum-text spectrum-text--size-s"
                    style={{ color: getRiskLevelColor(analysisResult.risk_level) }}
                  >
                    Risk: {analysisResult.risk_level.toUpperCase()}
                  </span>
                </div>
              </div>
            </div>
            <div className="spectrum-card-body">
              
              {/* Overall Score */}
              <div className="spectrum-flex spectrum-flex--justify-between spectrum-flex--align-center mb-6">
                <div>
                  <h3 className="spectrum-heading spectrum-heading--size-m">Overall Fairness Score</h3>
                  <p className="spectrum-body spectrum-text-gray-600">
                    {analysisResult.modelName} - {formatDate(analysisResult.timestamp)}
                  </p>
                </div>
                <div className="spectrum-text spectrum-text--size-xxl spectrum-text--bold" 
                     style={{ color: getStatusColor(analysisResult.status) }}>
                  {analysisResult.overallScore.toFixed(1)}%
                </div>
              </div>

              {/* Bias Types Analysis */}
              <div className="spectrum-grid spectrum-grid--cols-2 spectrum-grid--gap-400 mb-6">
                {Object.entries(analysisResult.biasDetails.bias_types).map(([biasType, details]) => (
                  <Card key={biasType} className="spectrum-card">
                    <div className="spectrum-card-header">
                      <h4 className="spectrum-heading spectrum-heading--size-s">
                        {biasType.charAt(0).toUpperCase() + biasType.slice(1)} Bias
                      </h4>
                    </div>
                    <div className="spectrum-card-body">
                      {details && typeof details === 'object' && 'is_biased' in details ? (
                        <div className="spectrum-flex spectrum-flex--align-center spectrum-flex--gap-200">
                          {details.is_biased ? (
                            <AlertTriangle size={16} style={{ color: 'var(--spectrum-red-600)' }} />
                          ) : (
                            <CheckCircle size={16} style={{ color: 'var(--spectrum-green-600)' }} />
                          )}
                          <span>{details.is_biased ? 'Bias Detected' : 'No Bias Detected'}</span>
                        </div>
                      ) : (
                        <span className="spectrum-text spectrum-text-gray-600">Analysis pending</span>
                      )}
                    </div>
                  </Card>
                ))}
              </div>

              {/* Recommendations */}
              <div className="spectrum-field">
                <label className="spectrum-field-label">Recommendations</label>
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
              <h2 className="spectrum-heading spectrum-heading--size-l">Analysis History</h2>
            </div>
            <div className="spectrum-card-body">
              <div className="spectrum-list">
                {analysisHistory.map((result) => (
                  <div key={result.id} className="spectrum-list-item">
                    <div className="spectrum-flex spectrum-flex--justify-between spectrum-flex--align-center">
                      <div>
                        <div className="spectrum-text spectrum-text--bold">{result.modelName}</div>
                        <div className="spectrum-text spectrum-text--size-s spectrum-text-gray-600">
                          {formatDate(result.timestamp)} - {result.modelType}
                        </div>
                      </div>
                      <div className="spectrum-flex spectrum-flex--align-center spectrum-flex--gap-200">
                        <span 
                          className="spectrum-text spectrum-text--bold"
                          style={{ color: getStatusColor(result.status) }}
                        >
                          {result.overallScore.toFixed(1)}%
                        </span>
                        {getStatusIcon(result.status)}
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
