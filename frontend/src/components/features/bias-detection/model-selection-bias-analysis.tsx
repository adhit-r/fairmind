"use client"

import { useState, useEffect } from 'react'
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card"
import { Button } from "@/components/ui/common/button"
import { Badge } from "@/components/ui/common/badge"
import { Progress } from "@/components/ui/common/progress"
import { Alert, AlertDescription } from "@/components/ui/common/alert"
import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/components/ui/common/tabs"
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from "@/components/ui/common/select"
import { Input } from "@/components/ui/common/input"
import { Label } from "@/components/ui/common/label"
import { Checkbox } from "@/components/ui/checkbox"
import { 
  AlertTriangle, 
  CheckCircle, 
  XCircle, 
  Info,
  BarChart3,
  PieChart,
  TrendingUp,
  TrendingDown,
  Users,
  Target,
  Shield,
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
  Bot,
  Database,
  Brain,
  TestTube,
  Zap,
  ArrowRight,
  Clock,
  Star,
  Tag
} from "lucide-react"
import { fairmindAPI } from "@/lib/fairmind-api"
import { ComprehensiveBiasDashboard } from "./comprehensive-bias-dashboard"
import { AIModel, Dataset } from "@/types"

interface BiasAnalysisRequest {
  model_id: string
  dataset_id: string
  sensitive_attributes: string[]
  target_column: string
  analysis_type: 'comprehensive' | 'quick' | 'targeted'
}

interface BiasAnalysisResult {
  id: string
  model_id: string
  dataset_id: string
  timestamp: string
  status: 'pending' | 'running' | 'completed' | 'failed'
  results?: any
  error?: string
}

export function ModelSelectionBiasAnalysis() {
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState('')
  const [models, setModels] = useState<AIModel[]>([])
  const [datasets, setDatasets] = useState<Dataset[]>([])
  const [selectedModel, setSelectedModel] = useState<string>('')
  const [selectedDataset, setSelectedDataset] = useState<string>('')
  const [sensitiveAttributes, setSensitiveAttributes] = useState<string[]>([])
  const [targetColumn, setTargetColumn] = useState('')
  const [analysisType, setAnalysisType] = useState<'comprehensive' | 'quick' | 'targeted'>('comprehensive')
  const [availableAttributes, setAvailableAttributes] = useState<string[]>([])
  const [analysisHistory, setAnalysisHistory] = useState<BiasAnalysisResult[]>([])
  const [currentAnalysis, setCurrentAnalysis] = useState<BiasAnalysisResult | null>(null)
  const [showResults, setShowResults] = useState(false)

  // Load models and datasets on component mount
  useEffect(() => {
    loadModels()
    loadDatasets()
  }, [])

  // Load available attributes when dataset changes
  useEffect(() => {
    if (selectedDataset) {
      loadDatasetAttributes(selectedDataset)
    }
  }, [selectedDataset])

  const loadModels = async () => {
    try {
      setLoading(true)
      const response = await fairmindAPI.getModels()
      setModels(response || [])
    } catch (err) {
      setError('Failed to load models')
      console.error('Error loading models:', err)
    } finally {
      setLoading(false)
    }
  }

  const loadDatasets = async () => {
    try {
      setLoading(true)
      const response = await fairmindAPI.getDatasets()
      setDatasets(response || [])
    } catch (err) {
      setError('Failed to load datasets')
      console.error('Error loading datasets:', err)
    } finally {
      setLoading(false)
    }
  }

  const loadDatasetAttributes = async (datasetId: string) => {
    try {
      // Mock dataset attributes - in real implementation, this would come from the backend
      const mockAttributes = {
        'diabetes': ['age', 'sex', 'bmi', 'blood_pressure', 'insulin', 'diabetes_pedigree'],
        'titanic': ['age', 'sex', 'pclass', 'sibsp', 'parch', 'fare', 'embarked'],
        'credit_fraud': ['amount', 'oldbalanceOrg', 'newbalanceOrig', 'oldbalanceDest', 'newbalanceDest', 'type']
      }
      
      const dataset = datasets.find(d => d.path === datasetId)
      if (dataset) {
        const attributes = mockAttributes[dataset.name as keyof typeof mockAttributes] || []
        setAvailableAttributes(attributes)
      }
    } catch (err) {
      console.error('Error loading dataset attributes:', err)
    }
  }

  const handleAttributeToggle = (attribute: string) => {
    setSensitiveAttributes(prev => 
      prev.includes(attribute) 
        ? prev.filter(a => a !== attribute)
        : [...prev, attribute]
    )
  }

  const handleRunAnalysis = async () => {
    if (!selectedModel || !selectedDataset || sensitiveAttributes.length === 0 || !targetColumn) {
      setError('Please select a model, dataset, sensitive attributes, and target column')
      return
    }

    try {
      setLoading(true)
      setError('')

      const analysisRequest: BiasAnalysisRequest = {
        model_id: selectedModel,
        dataset_id: selectedDataset,
        sensitive_attributes: sensitiveAttributes,
        target_column: targetColumn,
        analysis_type: analysisType
      }

      // Create analysis record
      const analysisId = `bias_${Date.now()}`
      const newAnalysis: BiasAnalysisResult = {
        id: analysisId,
        model_id: selectedModel,
        dataset_id: selectedDataset,
        timestamp: new Date().toISOString(),
        status: 'running'
      }

      setCurrentAnalysis(newAnalysis)
      setAnalysisHistory(prev => [newAnalysis, ...prev])

      // Run bias analysis
      const response = await fairmindAPI.runBiasAnalysis(analysisRequest)
      
      if (response.success) {
        const completedAnalysis: BiasAnalysisResult = {
          ...newAnalysis,
          status: 'completed',
          results: response.data
        }
        setCurrentAnalysis(completedAnalysis)
        setAnalysisHistory(prev => 
          prev.map(a => a.id === analysisId ? completedAnalysis : a)
        )
        setShowResults(true)
      } else {
        throw new Error(response.error || 'Analysis failed')
      }

    } catch (err) {
      setError(`Bias analysis failed: ${err instanceof Error ? err.message : 'Unknown error'}`)
      if (currentAnalysis) {
        const failedAnalysis: BiasAnalysisResult = {
          ...currentAnalysis,
          status: 'failed',
          error: err instanceof Error ? err.message : 'Unknown error'
        }
        setCurrentAnalysis(failedAnalysis)
        setAnalysisHistory(prev => 
          prev.map(a => a.id === currentAnalysis.id ? failedAnalysis : a)
        )
      }
    } finally {
      setLoading(false)
    }
  }

  const getModelIcon = (type: string) => {
    switch (type.toLowerCase()) {
      case 'classification': return <BarChart3 className="h-4 w-4" />
      case 'regression': return <TrendingUp className="h-4 w-4" />
      case 'nlp': return <FileText className="h-4 w-4" />
      case 'computer_vision': return <Eye className="h-4 w-4" />
      case 'recommendation': return <Star className="h-4 w-4" />
      default: return <Bot className="h-4 w-4" />
    }
  }

  const getStatusColor = (status: string) => {
    switch (status) {
      case 'completed': return 'bg-green-100 text-green-800'
      case 'running': return 'bg-blue-100 text-blue-800'
      case 'failed': return 'bg-red-100 text-red-800'
      default: return 'bg-gray-100 text-gray-800'
    }
  }

  if (showResults && currentAnalysis?.results) {
    return (
      <div className="space-y-6">
        <div className="flex items-center justify-between">
          <h2 className="text-2xl font-bold">Bias Analysis Results</h2>
          <Button 
            variant="outline" 
            onClick={() => setShowResults(false)}
            className="flex items-center gap-2"
          >
            <ArrowRight className="h-4 w-4 rotate-180" />
            Back to Analysis
          </Button>
        </div>
        <ComprehensiveBiasDashboard />
      </div>
    )
  }

  return (
    <div className="space-y-6">
      <div className="text-center mb-8">
        <h1 className="text-3xl font-bold mb-4 flex items-center justify-center gap-3">
          <TestTube className="h-8 w-8" />
          Model Bias Analysis
        </h1>
        <p className="text-lg text-muted-foreground max-w-2xl mx-auto">
          Select models from your registry and analyze them for bias and fairness issues. 
          This comprehensive analysis will help you identify and mitigate potential biases in your AI systems.
        </p>
      </div>

      {error && (
        <Alert variant="destructive">
          <AlertTriangle className="h-4 w-4" />
          <AlertDescription>{error}</AlertDescription>
        </Alert>
      )}

      <Tabs defaultValue="setup" className="space-y-6">
        <TabsList className="grid w-full grid-cols-3">
          <TabsTrigger value="setup">Analysis Setup</TabsTrigger>
          <TabsTrigger value="history">Analysis History</TabsTrigger>
          <TabsTrigger value="insights">Quick Insights</TabsTrigger>
        </TabsList>

        <TabsContent value="setup" className="space-y-6">
          <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
            {/* Model Selection */}
            <Card>
              <CardHeader>
                <CardTitle className="flex items-center gap-2">
                  <Bot className="h-5 w-5" />
                  Select Model
                </CardTitle>
                <CardDescription>
                  Choose a model from your registry for bias analysis
                </CardDescription>
              </CardHeader>
              <CardContent className="space-y-4">
                <div className="space-y-2">
                  <Label htmlFor="model-select">Model</Label>
                  <Select value={selectedModel} onValueChange={setSelectedModel}>
                    <SelectTrigger>
                      <SelectValue placeholder="Select a model..." />
                    </SelectTrigger>
                    <SelectContent>
                      {models.map((model) => (
                        <SelectItem key={model.id} value={model.id}>
                          <div className="flex items-center gap-2">
                            {getModelIcon(model.type)}
                            <span>{model.name}</span>
                            <Badge variant="outline" className="ml-auto">
                              {model.type}
                            </Badge>
                          </div>
                        </SelectItem>
                      ))}
                    </SelectContent>
                  </Select>
                </div>

                {selectedModel && (
                  <div className="p-4 bg-muted rounded-lg">
                    <h4 className="font-semibold mb-2">Model Details</h4>
                    {(() => {
                      const model = models.find(m => m.id === selectedModel)
                      return model ? (
                        <div className="space-y-1 text-sm">
                                            <p><strong>Type:</strong> {model.type}</p>
                  <p><strong>Framework:</strong> {model.metadata?.framework || 'N/A'}</p>
                  <p><strong>Source:</strong> {model.filePath}</p>
                  {model.metadata?.description && (
                    <p><strong>Description:</strong> {model.metadata.description}</p>
                  )}
                        </div>
                      ) : null
                    })()}
                  </div>
                )}
              </CardContent>
            </Card>

            {/* Dataset Selection */}
            <Card>
              <CardHeader>
                <CardTitle className="flex items-center gap-2">
                  <Database className="h-5 w-5" />
                  Select Dataset
                </CardTitle>
                <CardDescription>
                  Choose a dataset for bias analysis
                </CardDescription>
              </CardHeader>
              <CardContent className="space-y-4">
                <div className="space-y-2">
                  <Label htmlFor="dataset-select">Dataset</Label>
                  <Select value={selectedDataset} onValueChange={setSelectedDataset}>
                    <SelectTrigger>
                      <SelectValue placeholder="Select a dataset..." />
                    </SelectTrigger>
                    <SelectContent>
                      {datasets.map((dataset) => (
                                        <SelectItem key={dataset.path} value={dataset.path}>
                  <div className="flex items-center gap-2">
                    <Database className="h-4 w-4" />
                    <span>{dataset.name}</span>
                    <Badge variant="outline" className="ml-auto">
                      {dataset.rows.toLocaleString()} rows
                    </Badge>
                  </div>
                </SelectItem>
                      ))}
                    </SelectContent>
                  </Select>
                </div>

                {selectedDataset && (
                  <div className="p-4 bg-muted rounded-lg">
                    <h4 className="font-semibold mb-2">Dataset Details</h4>
                    {(() => {
                                              const dataset = datasets.find(d => d.path === selectedDataset)
                                              return dataset ? (
                          <div className="space-y-1 text-sm">
                            <p><strong>Rows:</strong> {dataset.rows.toLocaleString()}</p>
                            <p><strong>Columns:</strong> {dataset.columns?.length || 0}</p>
                            <p><strong>Path:</strong> {dataset.path}</p>
                          </div>
                        ) : null
                    })()}
                  </div>
                )}
              </CardContent>
            </Card>
          </div>

          {/* Analysis Configuration */}
          <Card>
            <CardHeader>
              <CardTitle className="flex items-center gap-2">
                <Settings className="h-5 w-5" />
                Analysis Configuration
              </CardTitle>
              <CardDescription>
                Configure bias analysis parameters
              </CardDescription>
            </CardHeader>
            <CardContent className="space-y-6">
              <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
                <div className="space-y-2">
                  <Label htmlFor="analysis-type">Analysis Type</Label>
                  <Select value={analysisType} onValueChange={(value: any) => setAnalysisType(value)}>
                    <SelectTrigger>
                      <SelectValue />
                    </SelectTrigger>
                    <SelectContent>
                      <SelectItem value="comprehensive">Comprehensive Analysis</SelectItem>
                      <SelectItem value="quick">Quick Scan</SelectItem>
                      <SelectItem value="targeted">Targeted Analysis</SelectItem>
                    </SelectContent>
                  </Select>
                </div>

                <div className="space-y-2">
                  <Label htmlFor="target-column">Target Column</Label>
                  <Select value={targetColumn} onValueChange={setTargetColumn}>
                    <SelectTrigger>
                      <SelectValue placeholder="Select target column..." />
                    </SelectTrigger>
                    <SelectContent>
                      {availableAttributes.map((attr) => (
                        <SelectItem key={attr} value={attr}>
                          {attr}
                        </SelectItem>
                      ))}
                    </SelectContent>
                  </Select>
                </div>
              </div>

              <div className="space-y-2">
                <Label>Sensitive Attributes</Label>
                <div className="grid grid-cols-2 md:grid-cols-3 gap-2">
                  {availableAttributes.map((attr) => (
                    <div key={attr} className="flex items-center space-x-2">
                      <Checkbox
                        id={attr}
                        checked={sensitiveAttributes.includes(attr)}
                        onCheckedChange={() => handleAttributeToggle(attr)}
                      />
                      <Label htmlFor={attr} className="text-sm">{attr}</Label>
                    </div>
                  ))}
                </div>
                <p className="text-sm text-muted-foreground">
                  Select attributes that could be sources of bias (e.g., age, gender, race, etc.)
                </p>
              </div>
            </CardContent>
          </Card>

          {/* Run Analysis */}
          <Card>
            <CardContent className="pt-6">
              <Button 
                onClick={handleRunAnalysis}
                disabled={loading || !selectedModel || !selectedDataset || sensitiveAttributes.length === 0 || !targetColumn}
                className="w-full"
                size="lg"
              >
                {loading ? (
                  <>
                    <RefreshCw className="h-4 w-4 mr-2 animate-spin" />
                    Running Analysis...
                  </>
                ) : (
                  <>
                    <Play className="h-4 w-4 mr-2" />
                    Run Bias Analysis
                  </>
                )}
              </Button>
            </CardContent>
          </Card>
        </TabsContent>

        <TabsContent value="history" className="space-y-4">
          <h3 className="text-xl font-semibold">Analysis History</h3>
          {analysisHistory.length === 0 ? (
            <Card>
              <CardContent className="pt-6 text-center text-muted-foreground">
                No bias analyses have been run yet.
              </CardContent>
            </Card>
          ) : (
            <div className="space-y-4">
              {analysisHistory.map((analysis) => (
                <Card key={analysis.id} className="hover:shadow-md transition-shadow">
                  <CardContent className="pt-6">
                    <div className="flex items-center justify-between">
                      <div className="flex items-center gap-4">
                        <div className="flex items-center gap-2">
                          {analysis.status === 'completed' && <CheckCircle className="h-5 w-5 text-green-600" />}
                          {analysis.status === 'running' && <RefreshCw className="h-5 w-5 text-blue-600 animate-spin" />}
                          {analysis.status === 'failed' && <XCircle className="h-5 w-5 text-red-600" />}
                          <Badge className={getStatusColor(analysis.status)}>
                            {analysis.status}
                          </Badge>
                        </div>
                        <div>
                          <p className="font-medium">
                            {models.find(m => m.id === analysis.model_id)?.name || 'Unknown Model'}
                          </p>
                          <p className="text-sm text-muted-foreground">
                            {new Date(analysis.timestamp).toLocaleString()}
                          </p>
                        </div>
                      </div>
                      {analysis.status === 'completed' && (
                        <Button 
                          variant="outline" 
                          size="sm"
                          onClick={() => {
                            setCurrentAnalysis(analysis)
                            setShowResults(true)
                          }}
                        >
                          View Results
                        </Button>
                      )}
                    </div>
                    {analysis.error && (
                      <p className="text-sm text-red-600 mt-2">{analysis.error}</p>
                    )}
                  </CardContent>
                </Card>
              ))}
            </div>
          )}
        </TabsContent>

        <TabsContent value="insights" className="space-y-4">
          <h3 className="text-xl font-semibold">Quick Insights</h3>
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
            <Card>
              <CardContent className="pt-6">
                <div className="flex items-center gap-2 mb-2">
                  <AlertTriangle className="h-5 w-5 text-orange-600" />
                  <h4 className="font-semibold">Common Bias Types</h4>
                </div>
                <ul className="text-sm space-y-1">
                  <li>• Reporting Bias</li>
                  <li>• Historical Bias</li>
                  <li>• Selection Bias</li>
                  <li>• Group Attribution Bias</li>
                </ul>
              </CardContent>
            </Card>

            <Card>
              <CardContent className="pt-6">
                <div className="flex items-center gap-2 mb-2">
                  <Shield className="h-5 w-5 text-blue-600" />
                  <h4 className="font-semibold">Fairness Metrics</h4>
                </div>
                <ul className="text-sm space-y-1">
                  <li>• Demographic Parity</li>
                  <li>• Equality of Opportunity</li>
                  <li>• Counterfactual Fairness</li>
                  <li>• Equalized Odds</li>
                </ul>
              </CardContent>
            </Card>

            <Card>
              <CardContent className="pt-6">
                <div className="flex items-center gap-2 mb-2">
                  <Zap className="h-5 w-5 text-green-600" />
                  <h4 className="font-semibold">Mitigation Strategies</h4>
                </div>
                <ul className="text-sm space-y-1">
                  <li>• Data Augmentation</li>
                  <li>• MinDiff Training</li>
                  <li>• Counterfactual Logit Pairing</li>
                  <li>• Post-processing</li>
                </ul>
              </CardContent>
            </Card>
          </div>
        </TabsContent>
      </Tabs>
    </div>
  )
}
