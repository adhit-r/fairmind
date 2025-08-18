"use client"

import { useState, useEffect } from 'react'
import React from 'react'
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/common/card"
import { Button } from "@/components/ui/common/button"
import { Badge } from "@/components/ui/common/badge"
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from "@/components/ui/common/select"
import { Alert, AlertDescription } from "@/components/ui/common/alert"
import { Progress } from "@/components/ui/common/progress"
import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/components/ui/common/tabs"
import { Textarea } from "@/components/ui/common/textarea"
import { Label } from "@/components/ui/common/label"
import { Switch } from "@/components/ui/common/switch"
import { Input } from "@/components/ui/common/input"
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
  LineChart
} from "lucide-react"
import { fairmindAPI } from "@/lib/fairmind-api"

interface Dataset {
  name: string
  samples: number
  columns: string[]
  description: string
}

interface BiasAnalysisResult {
  dataset_name: string
  total_samples: number
  overall_score: number
  assessment_status: string
  issues_found: Array<{
    type: string
    severity: string
    description: string
    details: any
  }>
  bias_details: Record<string, any>
  recommendations: string[]
  custom_rules_results: CustomRuleResult[]
  llm_analysis?: LLMAnalysisResult
  simulation_results?: SimulationResult
}

interface CustomRule {
  id: string
  name: string
  description: string
  category: 'statistical' | 'demographic' | 'behavioral' | 'temporal' | 'geographic' | 'custom'
  severity: 'low' | 'medium' | 'high' | 'critical'
  enabled: boolean
  parameters: Record<string, any>
  formula?: string
  explanation?: string
}

interface CustomRuleResult {
  rule_id: string
  rule_name: string
  passed: boolean
  score: number
  details: any
  recommendations: string[]
}

interface LLMAnalysisResult {
  summary: string
  detailed_analysis: string
  contextual_recommendations: string[]
  fairness_insights: string[]
  risk_assessment: string
}

interface SimulationResult {
  scenarios: SimulationScenario[]
  overall_impact: number
  recommendations: string[]
}

interface SimulationScenario {
  name: string
  description: string
  bias_impact: number
  confidence: number
  details: any
}

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

export function EnhancedBiasDetection() {
  const [datasets, setDatasets] = useState<Dataset[]>([])
  const [selectedDataset, setSelectedDataset] = useState<string>('')
  const [targetColumn, setTargetColumn] = useState<string>('')
  const [sensitiveColumns, setSensitiveColumns] = useState<string[]>([])
  const [availableColumns, setAvailableColumns] = useState<string[]>([])
  const [loading, setLoading] = useState(false)
  const [analysisResult, setAnalysisResult] = useState<BiasAnalysisResult | null>(null)
  const [error, setError] = useState<string>('')
  const [analysisSteps, setAnalysisSteps] = useState<AnalysisStep[]>([])
  const [customRules, setCustomRules] = useState<CustomRule[]>([])
  const [llmEnabled, setLlmEnabled] = useState(false)
  const [llmPrompt, setLlmPrompt] = useState('')
  const [simulationEnabled, setSimulationEnabled] = useState(false)
  const [activeTab, setActiveTab] = useState('setup')
  const [currentStep, setCurrentStep] = useState(0)
  const [showStepDetails, setShowStepDetails] = useState<Record<string, boolean>>({})

  // Initialize default custom rules
  useEffect(() => {
    const defaultRules: CustomRule[] = [
      {
        id: 'statistical_parity',
        name: 'Statistical Parity',
        description: 'Ensures equal positive prediction rates across protected groups',
        category: 'statistical',
        severity: 'high',
        enabled: true,
        parameters: { threshold: 0.1 },
        formula: '|P(Y=1|A=0) - P(Y=1|A=1)| ≤ threshold',
        explanation: 'Measures if different groups have similar positive prediction rates'
      },
      {
        id: 'demographic_parity',
        name: 'Demographic Parity',
        description: 'Checks for equal selection rates across demographic groups',
        category: 'demographic',
        severity: 'high',
        enabled: true,
        parameters: { threshold: 0.05 },
        formula: '|P(Ŷ=1|A=0) - P(Ŷ=1|A=1)| ≤ threshold',
        explanation: 'Ensures equal selection rates regardless of protected attributes'
      },
      {
        id: 'equal_opportunity',
        name: 'Equal Opportunity',
        description: 'Ensures equal true positive rates across groups',
        category: 'statistical',
        severity: 'medium',
        enabled: true,
        parameters: { threshold: 0.1 },
        formula: '|P(Ŷ=1|Y=1,A=0) - P(Ŷ=1|Y=1,A=1)| ≤ threshold',
        explanation: 'Focuses on equal treatment of positive cases across groups'
      },
      {
        id: 'individual_fairness',
        name: 'Individual Fairness',
        description: 'Similar individuals should receive similar predictions',
        category: 'behavioral',
        severity: 'high',
        enabled: false,
        parameters: { similarity_threshold: 0.8 },
        formula: 'd(Ŷ(x₁), Ŷ(x₂)) ≤ L·d(x₁, x₂)',
        explanation: 'Uses similarity metrics to ensure consistent treatment'
      },
      {
        id: 'temporal_fairness',
        name: 'Temporal Fairness',
        description: 'Checks for bias changes over time',
        category: 'temporal',
        severity: 'medium',
        enabled: false,
        parameters: { time_window: 30, drift_threshold: 0.15 },
        formula: '|Bias(t) - Bias(t-1)| ≤ drift_threshold',
        explanation: 'Monitors bias drift over time periods'
      },
      {
        id: 'geographic_fairness',
        name: 'Geographic Fairness',
        description: 'Ensures fairness across different geographic regions',
        category: 'geographic',
        severity: 'medium',
        enabled: false,
        parameters: { region_threshold: 0.12 },
        formula: 'max_region(Bias) - min_region(Bias) ≤ region_threshold',
        explanation: 'Compares bias metrics across geographic regions'
      }
    ]
    setCustomRules(defaultRules)
  }, [])

  // Initialize analysis steps
  useEffect(() => {
    const steps: AnalysisStep[] = [
      {
        id: 'data-validation',
        name: 'Data Validation',
        description: 'Validating dataset structure and quality',
        status: 'pending',
        progress: 0,
        icon: Database,
        estimated_time: '30 seconds'
      },
      {
        id: 'statistical-analysis',
        name: 'Statistical Analysis',
        description: 'Performing statistical bias analysis',
        status: 'pending',
        progress: 0,
        icon: BarChart,
        estimated_time: '2 minutes'
      },
      {
        id: 'custom-rules',
        name: 'Custom Rules Analysis',
        description: 'Applying custom bias detection rules',
        status: 'pending',
        progress: 0,
        icon: Shield,
        estimated_time: '1 minute'
      },
      {
        id: 'llm-analysis',
        name: 'LLM Analysis',
        description: 'Using LLM for advanced bias detection',
        status: 'pending',
        progress: 0,
        icon: Brain,
        estimated_time: '3 minutes'
      },
      {
        id: 'simulation',
        name: 'Bias Simulation',
        description: 'Running bias impact simulations',
        status: 'pending',
        progress: 0,
        icon: TestTube,
        estimated_time: '2 minutes'
      },
      {
        id: 'report-generation',
        name: 'Report Generation',
        description: 'Generating comprehensive bias report',
        status: 'pending',
        progress: 0,
        icon: FileText,
        estimated_time: '30 seconds'
      }
    ]
    setAnalysisSteps(steps)
  }, [])

  useEffect(() => {
    loadAvailableDatasets()
  }, [])

  useEffect(() => {
    if (selectedDataset) {
      loadDatasetInfo(selectedDataset)
    }
  }, [selectedDataset])

  const loadAvailableDatasets = async () => {
    try {
      const response = await fairmindAPI.getAvailableDatasets()
      if (response.success) {
        setDatasets(response.data)
      } else {
        setError('Failed to load datasets')
      }
    } catch (error) {
      setError('Error loading datasets')
    }
  }

  const loadDatasetInfo = async (datasetName: string) => {
    try {
      const response = await fairmindAPI.getDatasetInfo(datasetName)
      if (response.success) {
        setAvailableColumns(response.data.columns.map((col: any) => col.name))
        setTargetColumn('')
        setSensitiveColumns([])
      }
    } catch (error) {
      setError('Error loading dataset info')
    }
  }

  const updateStepStatus = (stepId: string, status: AnalysisStep['status'], progress: number, details?: any, error?: string) => {
    setAnalysisSteps(prev => prev.map(step => 
      step.id === stepId 
        ? { ...step, status, progress, details, error }
        : step
    ))
  }

  const runEnhancedBiasAnalysis = async () => {
    if (!selectedDataset || !targetColumn || sensitiveColumns.length === 0) {
      setError('Please select dataset, target column, and at least one sensitive column')
      return
    }

    setLoading(true)
    setError('')
    setCurrentStep(0)
    setAnalysisResult(null)

    // Reset all steps
    setAnalysisSteps(prev => prev.map(step => ({ ...step, status: 'pending', progress: 0 })))

    try {
      // Step 1: Data Validation
      updateStepStatus('data-validation', 'running', 0)
      await performDataValidation(selectedDataset)
      updateStepStatus('data-validation', 'completed', 100, { validated: true })

      // Step 2: Statistical Analysis
      updateStepStatus('statistical-analysis', 'running', 0)
      await performStatisticalAnalysis(selectedDataset, targetColumn, sensitiveColumns)
      updateStepStatus('statistical-analysis', 'completed', 100, { metrics: 'calculated' })

      // Step 3: Custom Rules Analysis
      updateStepStatus('custom-rules', 'running', 0)
      await performCustomRulesAnalysis(selectedDataset, targetColumn, sensitiveColumns, customRules)
      updateStepStatus('custom-rules', 'completed', 100, { rules_applied: customRules.filter(r => r.enabled).length })

      // Step 4: LLM Analysis (if enabled)
      if (llmEnabled) {
        updateStepStatus('llm-analysis', 'running', 0)
        await performLLMAnalysis(selectedDataset, targetColumn, sensitiveColumns, llmPrompt)
        updateStepStatus('llm-analysis', 'completed', 100, { llm_insights: 'generated' })
      }

      // Step 5: Simulation (if enabled)
      if (simulationEnabled) {
        updateStepStatus('simulation', 'running', 0)
        await performSimulation(selectedDataset, targetColumn, sensitiveColumns)
        updateStepStatus('simulation', 'completed', 100, { scenarios: 'simulated' })
      }

      // Step 6: Report Generation
      updateStepStatus('report-generation', 'running', 0)
      await generateFinalReport()
      updateStepStatus('report-generation', 'completed', 100, { report: 'generated' })

      // Get final results
      const response = await fairmindAPI.analyzeDatasetBias({
        dataset_name: selectedDataset,
        target_column: targetColumn,
        sensitive_columns: sensitiveColumns,
        custom_rules: customRules.filter(r => r.enabled),
        llm_enabled: llmEnabled,
        llm_prompt: llmPrompt,
        simulation_enabled: simulationEnabled
      })

      if (response.success) {
        setAnalysisResult(response.data)
      } else {
        setError(response.error || 'Analysis failed')
      }
    } catch (error: unknown) {
      const errorMessage = error instanceof Error ? error.message : 'Unknown error occurred'
      updateStepStatus('data-validation', 'failed', 0, {}, errorMessage)
      throw error
    } finally {
      setLoading(false)
    }
  }

  const performDataValidation = async (datasetName: string) => {
    try {
      // Real data validation
      const response = await fairmindAPI.getDatasetInfo(datasetName)
      if (!response.success) {
        throw new Error('Dataset validation failed')
      }
      
      // Simulate progress updates during validation
      for (let i = 0; i <= 100; i += 20) {
        updateStepStatus('data-validation', 'running', i)
        await new Promise(resolve => setTimeout(resolve, 100))
      }
    } catch (error: unknown) {
      const errorMessage = error instanceof Error ? error.message : 'Unknown error occurred'
      updateStepStatus('data-validation', 'failed', 0, {}, errorMessage)
      throw error
    }
  }

  const performStatisticalAnalysis = async (datasetName: string, targetCol: string, sensitiveCols: string[]) => {
    try {
      // Real statistical analysis
      const response = await fairmindAPI.analyzeDatasetBias({
        dataset_name: datasetName,
        target_column: targetCol,
        sensitive_columns: sensitiveCols,
        custom_rules: [],
        llm_enabled: false,
        simulation_enabled: false
      })
      
      if (!response.success) {
        throw new Error('Statistical analysis failed')
      }
      
      // Simulate progress updates during analysis
      for (let i = 0; i <= 100; i += 10) {
        updateStepStatus('statistical-analysis', 'running', i)
        await new Promise(resolve => setTimeout(resolve, 200))
      }
    } catch (error: unknown) {
      const errorMessage = error instanceof Error ? error.message : 'Unknown error occurred'
      updateStepStatus('statistical-analysis', 'failed', 0, {}, errorMessage)
      throw error
    }
  }

  const performCustomRulesAnalysis = async (datasetName: string, targetCol: string, sensitiveCols: string[], rules: CustomRule[]) => {
    try {
      const enabledRules = rules.filter(r => r.enabled)
      
      // Real custom rules analysis
      const response = await fairmindAPI.analyzeDatasetBias({
        dataset_name: datasetName,
        target_column: targetCol,
        sensitive_columns: sensitiveCols,
        custom_rules: enabledRules,
        llm_enabled: false,
        simulation_enabled: false
      })
      
      if (!response.success) {
        throw new Error('Custom rules analysis failed')
      }
      
      // Simulate progress updates during rules analysis
      for (let i = 0; i <= 100; i += 15) {
        updateStepStatus('custom-rules', 'running', i)
        await new Promise(resolve => setTimeout(resolve, 150))
      }
    } catch (error: unknown) {
      const errorMessage = error instanceof Error ? error.message : 'Unknown error occurred'
      updateStepStatus('custom-rules', 'failed', 0, {}, errorMessage)
      throw error
    }
  }

  const performLLMAnalysis = async (datasetName: string, targetCol: string, sensitiveCols: string[], prompt: string) => {
    try {
      // Real LLM analysis
      const response = await fairmindAPI.analyzeDatasetBias({
        dataset_name: datasetName,
        target_column: targetCol,
        sensitive_columns: sensitiveCols,
        custom_rules: [],
        llm_enabled: true,
        llm_prompt: prompt,
        simulation_enabled: false
      })
      
      if (!response.success) {
        throw new Error('LLM analysis failed')
      }
      
      // Simulate progress updates during LLM analysis (longer process)
      for (let i = 0; i <= 100; i += 5) {
        updateStepStatus('llm-analysis', 'running', i)
        await new Promise(resolve => setTimeout(resolve, 300))
      }
    } catch (error: unknown) {
      const errorMessage = error instanceof Error ? error.message : 'Unknown error occurred'
      updateStepStatus('llm-analysis', 'failed', 0, {}, errorMessage)
      throw error
    }
  }

  const performSimulation = async (datasetName: string, targetCol: string, sensitiveCols: string[]) => {
    try {
      // Real simulation
      const response = await fairmindAPI.analyzeDatasetBias({
        dataset_name: datasetName,
        target_column: targetCol,
        sensitive_columns: sensitiveCols,
        custom_rules: [],
        llm_enabled: false,
        simulation_enabled: true
      })
      
      if (!response.success) {
        throw new Error('Simulation failed')
      }
      
      // Simulate progress updates during simulation
      for (let i = 0; i <= 100; i += 8) {
        updateStepStatus('simulation', 'running', i)
        await new Promise(resolve => setTimeout(resolve, 250))
      }
    } catch (error: unknown) {
      const errorMessage = error instanceof Error ? error.message : 'Unknown error occurred'
      updateStepStatus('simulation', 'failed', 0, {}, errorMessage)
      throw error
    }
  }

  const generateFinalReport = async () => {
    try {
      // Simulate report generation progress
      for (let i = 0; i <= 100; i += 25) {
        updateStepStatus('report-generation', 'running', i)
        await new Promise(resolve => setTimeout(resolve, 100))
      }
    } catch (error: unknown) {
      const errorMessage = error instanceof Error ? error.message : 'Unknown error occurred'
      updateStepStatus('report-generation', 'failed', 0, {}, errorMessage)
      throw error
    }
  }

  const addCustomRule = () => {
    const newRule: CustomRule = {
      id: `custom_${Date.now()}`,
      name: 'New Custom Rule',
      description: 'Custom bias detection rule',
      category: 'custom',
      severity: 'medium',
      enabled: true,
      parameters: { threshold: 0.1 },
      formula: 'Custom formula',
      explanation: 'Custom explanation'
    }
    setCustomRules([...customRules, newRule])
  }

  const updateCustomRule = (ruleId: string, updates: Partial<CustomRule>) => {
    setCustomRules(prev => prev.map(rule => 
      rule.id === ruleId ? { ...rule, ...updates } : rule
    ))
  }

  const removeCustomRule = (ruleId: string) => {
    setCustomRules(prev => prev.filter(rule => rule.id !== ruleId))
  }

  const getSeverityColor = (severity: string) => {
    switch (severity.toLowerCase()) {
      case 'critical':
        return 'text-red-700 bg-red-50 border-red-300'
      case 'high':
        return 'text-red-600 bg-red-50 border-red-200'
      case 'medium':
        return 'text-orange-600 bg-orange-50 border-orange-200'
      case 'low':
        return 'text-yellow-600 bg-yellow-50 border-yellow-200'
      default:
        return 'text-gray-600 bg-gray-50 border-gray-200'
    }
  }

  const getCategoryIcon = (category: string) => {
    switch (category) {
      case 'statistical': return BarChart3
      case 'demographic': return Users
      case 'behavioral': return UserCheck
      case 'temporal': return Calendar
      case 'geographic': return MapPin
      case 'custom': return Settings
      default: return Shield
    }
  }

  const getStepIcon = (step: AnalysisStep) => {
    const IconComponent = step.icon
    return <IconComponent className="h-5 w-5" />
  }

  const getStepStatusIcon = (status: string) => {
    switch (status) {
      case 'completed':
        return <CheckCircle className="h-4 w-4 text-green-600" />
      case 'running':
        return <Clock className="h-4 w-4 text-blue-600 animate-spin" />
      case 'failed':
        return <XCircle className="h-4 w-4 text-red-600" />
      default:
        return <div className="h-4 w-4 rounded-full border-2 border-gray-300" />
    }
  }

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-3xl font-bold flex items-center gap-2">
            <Sparkles className="h-8 w-8 text-blue-600" />
            Enhanced Bias Detection
          </h1>
          <p className="text-gray-600">Advanced bias detection with custom rules, LLM analysis, and simulation</p>
        </div>
        <Button onClick={loadAvailableDatasets} variant="outline" size="sm">
          <RefreshCw className="h-4 w-4 mr-2" />
          Refresh Datasets
        </Button>
      </div>

      {/* Main Tabs */}
      <Tabs value={activeTab} onValueChange={setActiveTab} className="w-full">
        <TabsList className="grid w-full grid-cols-4">
          <TabsTrigger value="setup">Setup</TabsTrigger>
          <TabsTrigger value="custom-rules">Custom Rules</TabsTrigger>
          <TabsTrigger value="analysis">Analysis</TabsTrigger>
          <TabsTrigger value="results">Results</TabsTrigger>
        </TabsList>

        {/* Setup Tab */}
        <TabsContent value="setup" className="space-y-6">
          <Card>
            <CardHeader>
              <CardTitle className="flex items-center gap-2">
                <Database className="h-5 w-5" />
                Dataset Configuration
              </CardTitle>
              <CardDescription>Select dataset and configure analysis parameters</CardDescription>
            </CardHeader>
            <CardContent className="space-y-4">
              {/* Dataset Selection */}
              <div className="space-y-2">
                <Label>Dataset</Label>
                <Select value={selectedDataset} onValueChange={setSelectedDataset}>
                  <SelectTrigger>
                    <SelectValue placeholder="Select a dataset" />
                  </SelectTrigger>
                  <SelectContent>
                    {datasets.map((dataset) => (
                      <SelectItem key={dataset.name} value={dataset.name}>
                        <div className="flex flex-col">
                          <span className="font-medium">{dataset.name}</span>
                          <span className="text-xs text-gray-500">
                            {dataset.samples} samples • {dataset.description}
                          </span>
                        </div>
                      </SelectItem>
                    ))}
                  </SelectContent>
                </Select>
              </div>

              {/* Target Column Selection */}
              {selectedDataset && (
                <div className="space-y-2">
                  <Label>Target Column</Label>
                  <Select value={targetColumn} onValueChange={setTargetColumn}>
                    <SelectTrigger>
                      <SelectValue placeholder="Select target column" />
                    </SelectTrigger>
                    <SelectContent>
                      {availableColumns.map((column) => (
                        <SelectItem key={column} value={column}>
                          {column}
                        </SelectItem>
                      ))}
                    </SelectContent>
                  </Select>
                </div>
              )}

              {/* Sensitive Columns Selection */}
              {selectedDataset && targetColumn && (
                <div className="space-y-2">
                  <Label>Sensitive Columns (for bias analysis)</Label>
                  <div className="grid grid-cols-2 gap-2">
                    {availableColumns
                      .filter(col => col !== targetColumn)
                      .map((column) => (
                        <Button
                          key={column}
                          variant={sensitiveColumns.includes(column) ? "default" : "outline"}
                          size="sm"
                          onClick={() => {
                            if (sensitiveColumns.includes(column)) {
                              setSensitiveColumns(sensitiveColumns.filter(c => c !== column))
                            } else {
                              setSensitiveColumns([...sensitiveColumns, column])
                            }
                          }}
                        >
                          {column}
                        </Button>
                      ))}
                  </div>
                </div>
              )}
            </CardContent>
          </Card>

          {/* Advanced Options */}
          <Card>
            <CardHeader>
              <CardTitle className="flex items-center gap-2">
                <Settings className="h-5 w-5" />
                Advanced Options
              </CardTitle>
              <CardDescription>Configure LLM analysis and simulation features</CardDescription>
            </CardHeader>
            <CardContent className="space-y-4">
              {/* LLM Analysis */}
              <div className="flex items-center justify-between">
                <div className="space-y-1">
                  <Label className="flex items-center gap-2">
                    <Brain className="h-4 w-4" />
                    LLM Analysis
                  </Label>
                  <p className="text-sm text-gray-600">
                    Use AI to provide contextual bias analysis and recommendations
                  </p>
                </div>
                <Switch
                  checked={llmEnabled}
                  onCheckedChange={setLlmEnabled}
                />
              </div>

              {llmEnabled && (
                <div className="space-y-2">
                  <Label>Custom LLM Prompt (Optional)</Label>
                  <Textarea
                    placeholder="Enter custom prompt for LLM analysis..."
                    value={llmPrompt}
                    onChange={(e) => setLlmPrompt(e.target.value)}
                    rows={3}
                  />
                </div>
              )}

              {/* Simulation */}
              <div className="flex items-center justify-between">
                <div className="space-y-1">
                  <Label className="flex items-center gap-2">
                    <TestTube className="h-4 w-4" />
                    Bias Simulation
                  </Label>
                  <p className="text-sm text-gray-600">
                    Simulate bias impact under different scenarios
                  </p>
                </div>
                <Switch
                  checked={simulationEnabled}
                  onCheckedChange={setSimulationEnabled}
                />
              </div>
            </CardContent>
          </Card>
        </TabsContent>

        {/* Custom Rules Tab */}
        <TabsContent value="custom-rules" className="space-y-6">
          <Card>
            <CardHeader>
              <CardTitle className="flex items-center gap-2">
                <Shield className="h-5 w-5" />
                Custom Bias Detection Rules
              </CardTitle>
              <CardDescription>
                Configure and customize bias detection rules for your specific use case
              </CardDescription>
            </CardHeader>
            <CardContent className="space-y-4">
              {customRules.map((rule) => (
                <Card key={rule.id} className="border-l-4 border-l-blue-500">
                  <CardContent className="p-4">
                    <div className="flex items-start justify-between">
                      <div className="flex-1 space-y-2">
                        <div className="flex items-center gap-2">
                          {React.createElement(getCategoryIcon(rule.category), { className: "h-4 w-4" })}
                          <h4 className="font-medium">{rule.name}</h4>
                          <Badge variant={rule.severity === 'critical' ? 'destructive' : 'secondary'}>
                            {rule.severity}
                          </Badge>
                          <Switch
                            checked={rule.enabled}
                            onCheckedChange={(enabled) => updateCustomRule(rule.id, { enabled })}
                          />
                        </div>
                        <p className="text-sm text-gray-600">{rule.description}</p>
                        {rule.formula && (
                          <div className="bg-gray-50 p-2 rounded text-sm font-mono">
                            {rule.formula}
                          </div>
                        )}
                        {rule.explanation && (
                          <p className="text-xs text-gray-500">{rule.explanation}</p>
                        )}
                        
                        {/* Parameters */}
                        <div className="space-y-2">
                          <Label className="text-xs">Parameters</Label>
                          {Object.entries(rule.parameters).map(([key, value]) => (
                            <div key={key} className="flex items-center gap-2">
                              <Label className="text-xs w-20">{key}:</Label>
                              <Input
                                type="number"
                                value={value}
                                onChange={(e) => updateCustomRule(rule.id, {
                                  parameters: { ...rule.parameters, [key]: parseFloat(e.target.value) }
                                })}
                                className="w-24 h-8"
                              />
                            </div>
                          ))}
                        </div>
                      </div>
                      
                      {rule.category === 'custom' && (
                        <Button
                          variant="ghost"
                          size="sm"
                          onClick={() => removeCustomRule(rule.id)}
                          className="text-red-600 hover:text-red-700"
                        >
                          <XCircle className="h-4 w-4" />
                        </Button>
                      )}
                    </div>
                  </CardContent>
                </Card>
              ))}

              <Button onClick={addCustomRule} variant="outline" className="w-full">
                <Plus className="h-4 w-4 mr-2" />
                Add Custom Rule
              </Button>
            </CardContent>
          </Card>
        </TabsContent>

        {/* Analysis Tab */}
        <TabsContent value="analysis" className="space-y-6">
          {/* Analysis Steps */}
          <Card>
            <CardHeader>
              <CardTitle className="flex items-center gap-2">
                <Activity className="h-5 w-5" />
                Analysis Progress
              </CardTitle>
              <CardDescription>
                Step-by-step bias analysis process with detailed progress tracking
              </CardDescription>
            </CardHeader>
            <CardContent className="space-y-4">
              {analysisSteps.map((step, index) => (
                <div key={step.id} className="border rounded-lg p-4">
                  <div className="flex items-center justify-between">
                    <div className="flex items-center gap-3">
                      {getStepStatusIcon(step.status)}
                      <div className="flex items-center gap-2">
                        {getStepIcon(step)}
                        <div>
                          <h4 className="font-medium">{step.name}</h4>
                          <p className="text-sm text-gray-600">{step.description}</p>
                        </div>
                      </div>
                    </div>
                    <div className="text-right">
                      <div className="text-sm text-gray-600">~{step.estimated_time}</div>
                      <Button
                        variant="ghost"
                        size="sm"
                        onClick={() => setShowStepDetails(prev => ({ ...prev, [step.id]: !prev[step.id] }))}
                      >
                        {showStepDetails[step.id] ? <ChevronDown className="h-4 w-4" /> : <ChevronRight className="h-4 w-4" />}
                      </Button>
                    </div>
                  </div>

                  {/* Progress Bar */}
                  <div className="mt-3">
                    <Progress value={step.progress} className="h-2" />
                    <div className="text-xs text-gray-500 mt-1">
                      {step.progress.toFixed(0)}% complete
                    </div>
                  </div>

                  {/* Step Details */}
                  {showStepDetails[step.id] && (
                    <div className="mt-3 p-3 bg-gray-50 rounded">
                      <h5 className="font-medium mb-2">Step Details</h5>
                      {step.details && (
                        <div className="text-sm text-gray-600">
                          <pre className="whitespace-pre-wrap">{JSON.stringify(step.details, null, 2)}</pre>
                        </div>
                      )}
                      {step.error && (
                        <Alert variant="destructive" className="mt-2">
                          <XCircle className="h-4 w-4" />
                          <AlertDescription>{step.error}</AlertDescription>
                        </Alert>
                      )}
                    </div>
                  )}
                </div>
              ))}
            </CardContent>
          </Card>

          {/* Run Analysis Button */}
          {selectedDataset && targetColumn && sensitiveColumns.length > 0 && (
            <Card>
              <CardContent className="p-6">
                <Button 
                  onClick={runEnhancedBiasAnalysis} 
                  disabled={loading}
                  className="w-full h-12 text-lg"
                  size="lg"
                >
                  {loading ? (
                    <>
                      <Clock className="h-5 w-5 mr-2 animate-spin" />
                      Running Enhanced Analysis...
                    </>
                  ) : (
                    <>
                      <Zap className="h-5 w-5 mr-2" />
                      Start Enhanced Bias Analysis
                    </>
                  )}
                </Button>
                <p className="text-sm text-gray-600 mt-2 text-center">
                  This will run {customRules.filter(r => r.enabled).length} custom rules
                  {llmEnabled && ', LLM analysis'}
                  {simulationEnabled && ', and bias simulation'}
                </p>
              </CardContent>
            </Card>
          )}
        </TabsContent>

        {/* Results Tab */}
        <TabsContent value="results" className="space-y-6">
          {analysisResult ? (
            <div className="space-y-6">
              {/* Overall Assessment */}
              <Card>
                <CardHeader>
                  <CardTitle className="flex items-center gap-2">
                    <BarChart3 className="h-5 w-5" />
                    Enhanced Bias Detection Results
                  </CardTitle>
                  <CardDescription>
                    Comprehensive bias analysis with custom rules, LLM insights, and simulation
                  </CardDescription>
                </CardHeader>
                <CardContent>
                  <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
                    {/* Overall Score */}
                    <div className="text-center p-4 bg-blue-50 rounded-lg">
                      <div className="text-3xl font-bold text-blue-600">
                        {analysisResult.overall_score}/100
                      </div>
                      <div className="text-sm text-gray-600">Overall Score</div>
                    </div>

                    {/* Custom Rules Applied */}
                    <div className="text-center p-4 bg-green-50 rounded-lg">
                      <div className="text-3xl font-bold text-green-600">
                        {analysisResult.custom_rules_results?.length || 0}
                      </div>
                      <div className="text-sm text-gray-600">Rules Applied</div>
                    </div>

                    {/* Issues Found */}
                    <div className="text-center p-4 bg-red-50 rounded-lg">
                      <div className="text-3xl font-bold text-red-600">
                        {analysisResult.issues_found.length}
                      </div>
                      <div className="text-sm text-gray-600">Issues Found</div>
                    </div>
                  </div>
                </CardContent>
              </Card>

              {/* Custom Rules Results */}
              {analysisResult.custom_rules_results && analysisResult.custom_rules_results.length > 0 && (
                <Card>
                  <CardHeader>
                    <CardTitle className="flex items-center gap-2">
                      <Shield className="h-5 w-5" />
                      Custom Rules Analysis
                    </CardTitle>
                  </CardHeader>
                  <CardContent>
                    <div className="space-y-3">
                      {analysisResult.custom_rules_results.map((result, index) => (
                        <div key={index} className="flex items-center justify-between p-3 border rounded">
                          <div>
                            <h4 className="font-medium">{result.rule_name}</h4>
                            <div className="flex items-center gap-2 mt-1">
                              <Badge variant={result.passed ? 'default' : 'destructive'}>
                                {result.passed ? 'Passed' : 'Failed'}
                              </Badge>
                              <span className="text-sm text-gray-600">
                                Score: {result.score.toFixed(1)}/100
                              </span>
                            </div>
                          </div>
                          {result.passed ? (
                            <CheckCircle className="h-5 w-5 text-green-600" />
                          ) : (
                            <XCircle className="h-5 w-5 text-red-600" />
                          )}
                        </div>
                      ))}
                    </div>
                  </CardContent>
                </Card>
              )}

              {/* LLM Analysis Results */}
              {analysisResult.llm_analysis && (
                <Card>
                  <CardHeader>
                    <CardTitle className="flex items-center gap-2">
                      <Brain className="h-5 w-5" />
                      LLM Analysis Insights
                    </CardTitle>
                  </CardHeader>
                  <CardContent className="space-y-4">
                    <div>
                      <h4 className="font-medium mb-2">Summary</h4>
                      <p className="text-gray-600">{analysisResult.llm_analysis.summary}</p>
                    </div>
                    
                    <div>
                      <h4 className="font-medium mb-2">Contextual Recommendations</h4>
                      <div className="space-y-2">
                        {analysisResult.llm_analysis.contextual_recommendations.map((rec, index) => (
                          <Alert key={index}>
                            <Lightbulb className="h-4 w-4" />
                            <AlertDescription>{rec}</AlertDescription>
                          </Alert>
                        ))}
                      </div>
                    </div>

                    <div>
                      <h4 className="font-medium mb-2">Risk Assessment</h4>
                      <p className="text-gray-600">{analysisResult.llm_analysis.risk_assessment}</p>
                    </div>
                  </CardContent>
                </Card>
              )}

              {/* Simulation Results */}
              {analysisResult.simulation_results && (
                <Card>
                  <CardHeader>
                    <CardTitle className="flex items-center gap-2">
                      <TestTube className="h-5 w-5" />
                      Bias Simulation Results
                    </CardTitle>
                  </CardHeader>
                  <CardContent>
                    <div className="space-y-4">
                      <div className="text-center p-4 bg-purple-50 rounded-lg">
                        <div className="text-2xl font-bold text-purple-600">
                          {analysisResult.simulation_results.overall_impact.toFixed(1)}%
                        </div>
                        <div className="text-sm text-gray-600">Overall Bias Impact</div>
                      </div>

                      <div className="space-y-3">
                        <h4 className="font-medium">Simulation Scenarios</h4>
                        {analysisResult.simulation_results.scenarios.map((scenario, index) => (
                          <div key={index} className="p-3 border rounded">
                            <div className="flex items-center justify-between">
                              <div>
                                <h5 className="font-medium">{scenario.name}</h5>
                                <p className="text-sm text-gray-600">{scenario.description}</p>
                              </div>
                              <div className="text-right">
                                <div className="text-lg font-bold text-red-600">
                                  {scenario.bias_impact.toFixed(1)}%
                                </div>
                                <div className="text-xs text-gray-500">
                                  Confidence: {scenario.confidence.toFixed(0)}%
                                </div>
                              </div>
                            </div>
                          </div>
                        ))}
                      </div>
                    </div>
                  </CardContent>
                </Card>
              )}

              {/* Detailed Analysis */}
              <Tabs defaultValue="bias-metrics" className="w-full">
                <TabsList className="grid w-full grid-cols-4">
                  <TabsTrigger value="bias-metrics">Bias Metrics</TabsTrigger>
                  <TabsTrigger value="enhanced-analysis">Enhanced Analysis</TabsTrigger>
                  <TabsTrigger value="fairness-tests">Fairness Tests</TabsTrigger>
                  <TabsTrigger value="recommendations">Recommendations</TabsTrigger>
                </TabsList>

                <TabsContent value="bias-metrics" className="space-y-4">
                  <Card>
                    <CardHeader>
                      <CardTitle>Statistical Parity Analysis</CardTitle>
                    </CardHeader>
                    <CardContent>
                      {Object.entries(analysisResult.bias_details).map(([attribute, details]) => (
                        <div key={attribute} className="mb-6">
                          <h4 className="font-medium mb-3">{attribute}</h4>
                          <div className="space-y-2">
                            {Object.entries(details.statistical_parity).map(([value, metrics]: [string, any]) => (
                              <div key={value} className="flex justify-between items-center p-2 bg-gray-50 rounded">
                                <span className="font-medium">{value}</span>
                                <div className="text-right">
                                  <div className="text-sm">
                                    Positive Rate: {(metrics.positive_rate * 100).toFixed(1)}%
                                  </div>
                                  <div className="text-xs text-gray-600">
                                    Difference: {(metrics.difference_from_overall * 100).toFixed(1)}%
                                  </div>
                                </div>
                              </div>
                            ))}
                          </div>
                        </div>
                      ))}
                    </CardContent>
                  </Card>
                </TabsContent>

                <TabsContent value="enhanced-analysis" className="space-y-4">
                  {/* Fairlearn Analysis */}
                  {analysisResult.bias_details && Object.values(analysisResult.bias_details).some((details: any) => details.enhanced_metrics?.fairlearn) && (
                    <Card>
                      <CardHeader>
                        <CardTitle className="flex items-center gap-2">
                          <Shield className="h-5 w-5" />
                          Fairlearn Analysis
                        </CardTitle>
                        <CardDescription>Advanced fairness metrics using Microsoft Fairlearn</CardDescription>
                      </CardHeader>
                      <CardContent>
                        {Object.entries(analysisResult.bias_details).map(([attribute, details]: [string, any]) => (
                          details.enhanced_metrics?.fairlearn && (
                            <div key={attribute} className="mb-4 p-4 border rounded">
                              <h4 className="font-medium mb-2">{attribute}</h4>
                              <div className="grid grid-cols-2 gap-4">
                                <div>
                                  <div className="text-sm font-medium">Demographic Parity Difference</div>
                                  <div className={`text-lg font-bold ${
                                    Math.abs(details.enhanced_metrics.fairlearn.demographic_parity_difference) > 0.1 
                                      ? 'text-red-600' : 'text-green-600'
                                  }`}>
                                    {(details.enhanced_metrics.fairlearn.demographic_parity_difference * 100).toFixed(2)}%
                                  </div>
                                </div>
                                <div>
                                  <div className="text-sm font-medium">Equalized Odds Difference</div>
                                  <div className={`text-lg font-bold ${
                                    Math.abs(details.enhanced_metrics.fairlearn.equalized_odds_difference) > 0.1 
                                      ? 'text-red-600' : 'text-green-600'
                                  }`}>
                                    {(details.enhanced_metrics.fairlearn.equalized_odds_difference * 100).toFixed(2)}%
                                  </div>
                                </div>
                              </div>
                              <div className="mt-2">
                                <div className="text-sm font-medium">Overall Fairness Score</div>
                                <div className="text-2xl font-bold text-blue-600">
                                  {details.enhanced_metrics.fairlearn.overall_fairness_score.toFixed(1)}/100
                                </div>
                              </div>
                            </div>
                          )
                        ))}
                      </CardContent>
                    </Card>
                  )}

                  {/* AI Fairness 360 Analysis */}
                  {analysisResult.bias_details && Object.values(analysisResult.bias_details).some((details: any) => details.enhanced_metrics?.aif360) && (
                    <Card>
                      <CardHeader>
                        <CardTitle className="flex items-center gap-2">
                          <Scale className="h-5 w-5" />
                          AI Fairness 360 Analysis
                        </CardTitle>
                        <CardDescription>Comprehensive fairness metrics using IBM AI Fairness 360</CardDescription>
                      </CardHeader>
                      <CardContent>
                        {Object.entries(analysisResult.bias_details).map(([attribute, details]: [string, any]) => (
                          details.enhanced_metrics?.aif360 && (
                            <div key={attribute} className="mb-4 p-4 border rounded">
                              <h4 className="font-medium mb-2">{attribute}</h4>
                              <div className="grid grid-cols-2 gap-4">
                                <div>
                                  <div className="text-sm font-medium">Statistical Parity Difference</div>
                                  <div className={`text-lg font-bold ${
                                    Math.abs(details.enhanced_metrics.aif360.statistical_parity_difference) > 0.1 
                                      ? 'text-red-600' : 'text-green-600'
                                  }`}>
                                    {(details.enhanced_metrics.aif360.statistical_parity_difference * 100).toFixed(2)}%
                                  </div>
                                </div>
                                <div>
                                  <div className="text-sm font-medium">Equal Opportunity Difference</div>
                                  <div className={`text-lg font-bold ${
                                    Math.abs(details.enhanced_metrics.aif360.equal_opportunity_difference) > 0.1 
                                      ? 'text-red-600' : 'text-green-600'
                                  }`}>
                                    {(details.enhanced_metrics.aif360.equal_opportunity_difference * 100).toFixed(2)}%
                                  </div>
                                </div>
                                <div>
                                  <div className="text-sm font-medium">Disparate Impact</div>
                                  <div className={`text-lg font-bold ${
                                    details.enhanced_metrics.aif360.disparate_impact < 0.8 || details.enhanced_metrics.aif360.disparate_impact > 1.2
                                      ? 'text-red-600' : 'text-green-600'
                                  }`}>
                                    {details.enhanced_metrics.aif360.disparate_impact.toFixed(3)}
                                  </div>
                                </div>
                                <div>
                                  <div className="text-sm font-medium">Theil Index</div>
                                  <div className="text-lg font-bold text-blue-600">
                                    {details.enhanced_metrics.aif360.theil_index.toFixed(4)}
                                  </div>
                                </div>
                              </div>
                            </div>
                          )
                        ))}
                      </CardContent>
                    </Card>
                  )}

                  {/* Explainability Analysis */}
                  {analysisResult.bias_details && Object.values(analysisResult.bias_details).some((details: any) => details.explainability) && (
                    <Card>
                      <CardHeader>
                        <CardTitle className="flex items-center gap-2">
                          <Brain className="h-5 w-5" />
                          Explainability Analysis
                        </CardTitle>
                        <CardDescription>Model explanations using DALEX and SHAP</CardDescription>
                      </CardHeader>
                      <CardContent>
                        {Object.entries(analysisResult.bias_details).map(([attribute, details]: [string, any]) => (
                          details.explainability && (
                            <div key={attribute} className="mb-4 p-4 border rounded">
                              <h4 className="font-medium mb-2">{attribute}</h4>
                              
                              {/* DALEX Results */}
                              {details.explainability.dalex && (
                                <div className="mb-4">
                                  <h5 className="font-medium text-sm mb-2">DALEX Model Performance</h5>
                                  <div className="grid grid-cols-3 gap-4">
                                    <div>
                                      <div className="text-xs text-gray-600">R² Score</div>
                                      <div className="text-sm font-bold">{details.explainability.dalex.model_performance.r2.toFixed(3)}</div>
                                    </div>
                                    <div>
                                      <div className="text-xs text-gray-600">MAE</div>
                                      <div className="text-sm font-bold">{details.explainability.dalex.model_performance.mae.toFixed(3)}</div>
                                    </div>
                                    <div>
                                      <div className="text-xs text-gray-600">RMSE</div>
                                      <div className="text-sm font-bold">{details.explainability.dalex.model_performance.rmse.toFixed(3)}</div>
                                    </div>
                                  </div>
                                </div>
                              )}

                              {/* SHAP Results */}
                              {details.explainability.shap && (
                                <div>
                                  <h5 className="font-medium text-sm mb-2">SHAP Feature Importance (Top 5)</h5>
                                  <div className="space-y-1">
                                    {details.explainability.shap.feature_importance.slice(0, 5).map((feature: any, index: number) => (
                                      <div key={index} className="flex justify-between items-center text-sm">
                                        <span className="truncate">{feature.feature}</span>
                                        <span className="font-medium">{feature.importance.toFixed(4)}</span>
                                      </div>
                                    ))}
                                  </div>
                                </div>
                              )}
                            </div>
                          )
                        ))}
                      </CardContent>
                    </Card>
                  )}
                </TabsContent>
              </Tabs>

              {/* Action Buttons */}
              <div className="flex gap-3">
                <Button variant="outline" className="flex-1">
                  <Download className="h-4 w-4 mr-2" />
                  Export Report
                </Button>
                <Button className="flex-1">
                  <Eye className="h-4 w-4 mr-2" />
                  View Detailed Report
                </Button>
              </div>
            </div>
          ) : (
            <Card>
              <CardContent className="p-12 text-center">
                <BarChart3 className="h-12 w-12 text-gray-400 mx-auto mb-4" />
                <h3 className="text-lg font-medium text-gray-900 mb-2">No Analysis Results</h3>
                <p className="text-gray-600">
                  Run an enhanced bias analysis to see detailed results here.
                </p>
              </CardContent>
            </Card>
          )}
        </TabsContent>
      </Tabs>

      {/* Error Display */}
      {error && (
        <Alert variant="destructive">
          <XCircle className="h-4 w-4" />
          <AlertDescription>{error}</AlertDescription>
        </Alert>
      )}
    </div>
  )
}
