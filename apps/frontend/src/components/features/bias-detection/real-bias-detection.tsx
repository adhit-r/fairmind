"use client"

import { useState, useEffect } from 'react'
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/common/card"
import { Button } from "@/components/ui/common/button"
import { Badge } from "@/components/ui/common/badge"
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from "@/components/ui/common/select"
import { Alert, AlertDescription } from "@/components/ui/common/alert"
import { Progress } from "@/components/ui/common/progress"
import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/components/ui/common/tabs"
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
  AlertCircle
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
}

export function RealBiasDetection() {
  const [datasets, setDatasets] = useState<Dataset[]>([])
  const [selectedDataset, setSelectedDataset] = useState<string>('')
  const [targetColumn, setTargetColumn] = useState<string>('')
  const [sensitiveColumns, setSensitiveColumns] = useState<string[]>([])
  const [availableColumns, setAvailableColumns] = useState<string[]>([])
  const [loading, setLoading] = useState(false)
  const [analysisResult, setAnalysisResult] = useState<BiasAnalysisResult | null>(null)
  const [error, setError] = useState<string>('')

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
      setDatasets(response)
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

  const runBiasAnalysis = async () => {
    if (!selectedDataset || !targetColumn || sensitiveColumns.length === 0) {
      setError('Please select dataset, target column, and at least one sensitive column')
      return
    }

    setLoading(true)
    setError('')

    try {
      const response = await fairmindAPI.analyzeDatasetBias({
        dataset_name: selectedDataset,
        target_column: targetColumn,
        sensitive_columns: sensitiveColumns
      })

      setAnalysisResult(response)
    } catch (error) {
      setError('Error running bias analysis')
    } finally {
      setLoading(false)
    }
  }

  const getSeverityColor = (severity: string) => {
    switch (severity.toLowerCase()) {
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

  const getScoreColor = (score: number) => {
    if (score >= 80) return 'text-green-600'
    if (score >= 60) return 'text-yellow-600'
    return 'text-red-600'
  }

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-bold">Real Bias Detection Assessment</h1>
          <p className="text-gray-600">Analyze actual datasets for bias using statistical methods</p>
        </div>
        <Button onClick={loadAvailableDatasets} variant="outline" size="sm">
          <RefreshCw className="h-4 w-4 mr-2" />
          Refresh Datasets
        </Button>
      </div>

      {/* Configuration Section */}
      <Card>
        <CardHeader>
          <CardTitle>Analysis Configuration</CardTitle>
          <CardDescription>Select dataset and configure bias analysis parameters</CardDescription>
        </CardHeader>
        <CardContent className="space-y-4">
          {/* Dataset Selection */}
          <div className="space-y-2">
            <label className="text-sm font-medium">Dataset</label>
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
              <label className="text-sm font-medium">Target Column</label>
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
              <label className="text-sm font-medium">Sensitive Columns (for bias analysis)</label>
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

          {/* Run Analysis Button */}
          {selectedDataset && targetColumn && sensitiveColumns.length > 0 && (
            <Button 
              onClick={runBiasAnalysis} 
              disabled={loading}
              className="w-full"
            >
              {loading ? (
                <>
                  <Clock className="h-4 w-4 mr-2 animate-spin" />
                  Analyzing...
                </>
              ) : (
                <>
                  <Target className="h-4 w-4 mr-2" />
                  Run Bias Analysis
                </>
              )}
            </Button>
          )}
        </CardContent>
      </Card>

      {/* Error Display */}
      {error && (
        <Alert variant="destructive">
          <XCircle className="h-4 w-4" />
          <AlertDescription>{error}</AlertDescription>
        </Alert>
      )}

      {/* Analysis Results */}
      {analysisResult && (
        <div className="space-y-6">
          {/* Overall Assessment */}
          <Card>
            <CardHeader>
              <CardTitle className="flex items-center gap-2">
                <BarChart3 className="h-5 w-5" />
                Bias Detection Assessment
              </CardTitle>
              <CardDescription>
                Test your models for bias against protected groups
              </CardDescription>
            </CardHeader>
            <CardContent>
              <div className="flex items-center justify-between mb-6">
                <div>
                  <h3 className="text-lg font-semibold">{analysisResult.dataset_name}</h3>
                  <p className="text-sm text-gray-600">
                    {analysisResult.total_samples} samples analyzed
                  </p>
                </div>
                <div className="text-right">
                  <div className={`text-3xl font-bold ${getScoreColor(analysisResult.overall_score)}`}>
                    {analysisResult.overall_score}/100
                  </div>
                  <div className="text-sm text-gray-600">
                    {analysisResult.assessment_status}
                  </div>
                </div>
              </div>

              {/* Issues Found */}
              {analysisResult.issues_found.length > 0 ? (
                <div className="space-y-3">
                  <h4 className="font-medium">Issues Found:</h4>
                  {analysisResult.issues_found.map((issue, index) => (
                    <Alert key={index} className={getSeverityColor(issue.severity)}>
                      <AlertTriangle className="h-4 w-4" />
                      <AlertDescription>
                        <div className="font-medium">{issue.type}</div>
                        <div className="text-sm">{issue.description}</div>
                      </AlertDescription>
                    </Alert>
                  ))}
                </div>
              ) : (
                <Alert>
                  <CheckCircle className="h-4 w-4" />
                  <AlertDescription>
                    No significant bias detected in the analyzed attributes.
                  </AlertDescription>
                </Alert>
              )}
            </CardContent>
          </Card>

          {/* Detailed Analysis */}
          <Tabs defaultValue="bias-metrics" className="w-full">
            <TabsList className="grid w-full grid-cols-3">
              <TabsTrigger value="bias-metrics">Bias Metrics</TabsTrigger>
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

            <TabsContent value="fairness-tests" className="space-y-4">
              <Card>
                <CardHeader>
                  <CardTitle>Statistical Fairness Tests</CardTitle>
                </CardHeader>
                <CardContent>
                  {Object.entries(analysisResult.bias_details).map(([attribute, details]) => (
                    <div key={attribute} className="mb-6">
                      <h4 className="font-medium mb-3">{attribute}</h4>
                      {details.fairness_tests.chi_square_test && (
                        <div className="p-3 bg-blue-50 rounded mb-3">
                          <div className="font-medium">Chi-Square Test</div>
                          <div className="text-sm">
                            p-value: {details.fairness_tests.chi_square_test.p_value.toFixed(4)}
                          </div>
                          <div className="text-sm">
                            {details.fairness_tests.chi_square_test.interpretation}
                          </div>
                        </div>
                      )}
                    </div>
                  ))}
                </CardContent>
              </Card>
            </TabsContent>

            <TabsContent value="recommendations" className="space-y-4">
              <Card>
                <CardHeader>
                  <CardTitle>Mitigation Recommendations</CardTitle>
                </CardHeader>
                <CardContent>
                  <div className="space-y-3">
                    {analysisResult.recommendations.map((recommendation, index) => (
                      <Alert key={index}>
                        <Info className="h-4 w-4" />
                        <AlertDescription>{recommendation}</AlertDescription>
                      </Alert>
                    ))}
                  </div>
                </CardContent>
              </Card>
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
      )}
    </div>
  )
}
