"use client"

import { useState, useEffect } from 'react'
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card"
import { Button } from "@/components/ui/button"
import { Badge } from "@/components/ui/badge"
import { Progress } from "@/components/ui/progress"
import { Alert, AlertDescription } from "@/components/ui/alert"
import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/components/ui/tabs"
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
  Stop,
  Pause
} from "lucide-react"
import { fairmindAPI } from "@/lib/fairmind-api"

interface BiasAnalysisResult {
  timestamp: string
  dataset_info: {
    total_samples: number
    total_features: number
    missing_values_total: number
    missing_values_percentage: number
  }
  data_quality: {
    missing_values: Record<string, any>
    unexpected_values: Record<string, any>
    data_skew: Record<string, any>
  }
  bias_detection: {
    reporting_bias: any
    historical_bias: any
    selection_bias: any
    group_attribution_bias: any
    implicit_bias: any
  }
  fairness_metrics: Record<string, any>
  recommendations: string[]
}

interface BiasType {
  id: string
  name: string
  description: string
  severity: 'low' | 'medium' | 'high' | 'critical'
  detected: boolean
  details: any
}

export function ComprehensiveBiasDashboard() {
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState('')
  const [biasAnalysis, setBiasAnalysis] = useState<BiasAnalysisResult | null>(null)
  const [selectedDataset, setSelectedDataset] = useState('')
  const [sensitiveAttributes, setSensitiveAttributes] = useState<string[]>([])
  const [targetColumn, setTargetColumn] = useState('')

  // Mock bias analysis data for demonstration
  const mockBiasAnalysis: BiasAnalysisResult = {
    timestamp: new Date().toISOString(),
    dataset_info: {
      total_samples: 1645000,
      total_features: 12,
      missing_values_total: 12500,
      missing_values_percentage: 0.76
    },
    data_quality: {
      missing_values: {
        'SEX': { '1.0': 0.02, '2.0': 0.01 },
        'RAC1P': { '1.0': 0.05, '2.0': 0.03 }
      },
      unexpected_values: {
        'AGEP': { outlier_count: 1250, outlier_percentage: 0.08 },
        'PINCP': { outlier_count: 8900, outlier_percentage: 0.54 }
      },
      data_skew: {
        'SEX': {
          distribution: { '1.0': 0.52, '2.0': 0.48 },
          imbalance_ratio: 1.08,
          minority_group_size: 789600,
          majority_group_size: 854400
        },
        'RAC1P': {
          distribution: { '1.0': 0.72, '2.0': 0.28 },
          imbalance_ratio: 2.57,
          minority_group_size: 460600,
          majority_group_size: 1183400
        }
      }
    },
    bias_detection: {
      reporting_bias: {
        detected: true,
        target_distribution: { '0': 0.75, '1': 0.25 },
        max_proportion: 0.75,
        min_proportion: 0.25,
        ratio: 3.0,
        indicators: {
          extreme_distribution: false,
          very_skewed: true
        }
      },
      historical_bias: {
        detected: true,
        indicators: {
          'SEX': {
            detected: false,
            group_distribution: { '1.0': 0.52, '2.0': 0.48 },
            disparity_ratio: 1.08
          },
          'RAC1P': {
            detected: true,
            group_distribution: { '1.0': 0.72, '2.0': 0.28 },
            disparity_ratio: 2.57
          }
        }
      },
      selection_bias: {
        detected: false,
        indicators: {}
      },
      group_attribution_bias: {
        detected: true,
        indicators: {
          'SEX': {
            detected: true,
            strong_correlations: {
              'WKHP': 0.35,
              'SCHL': 0.28
            }
          }
        }
      },
      implicit_bias: {
        detected: true,
        indicators: {
          'SEX': {
            detected: true,
            significant_disparities: {
              'WKHP': {
                mean_disparity: 0.42,
                group_means: { '1.0': 42.5, '2.0': 35.2 }
              }
            }
          }
        }
      }
    },
    fairness_metrics: {
      'SEX': {
        demographic_parity: {
          acceptance_rates: { '1.0': 0.28, '2.0': 0.22 },
          disparity: 0.06,
          ratio: 1.27,
          fair: false,
          groups: ['1.0', '2.0']
        },
        equality_of_opportunity: {
          opportunity_rates: { '1.0': 0.85, '2.0': 0.73 },
          disparity: 0.12,
          ratio: 1.16,
          fair: false,
          groups: ['1.0', '2.0']
        }
      }
    },
    recommendations: [
      "High data imbalance detected in RAC1P (ratio: 2.57). Consider oversampling minority groups or collecting more balanced data.",
      "Reporting bias detected in target variable. Consider collecting more representative data or using techniques like SMOTE to balance the dataset.",
      "Historical bias detected. Consider using more recent data or applying bias mitigation techniques like MinDiff or Counterfactual Logit Pairing.",
      "Demographic parity violation detected for SEX. Consider applying fairness-aware training techniques.",
      "Equality of opportunity violation detected for SEX. Consider using techniques that ensure equal true positive rates across groups."
    ]
  }

  useEffect(() => {
    // Load mock data for demonstration
    setBiasAnalysis(mockBiasAnalysis)
  }, [])

  const handleRunAnalysis = async () => {
    if (!selectedDataset || sensitiveAttributes.length === 0 || !targetColumn) {
      setError('Please select dataset, sensitive attributes, and target column')
      return
    }

    setLoading(true)
    setError('')

    try {
      // In production, this would call the actual API
      const result = await fairmindAPI.analyzeBias({
        dataset_path: selectedDataset,
        sensitive_attributes: sensitiveAttributes,
        target_column: targetColumn
      })

      if (result.success) {
        setBiasAnalysis(result.data)
      }
    } catch (error: any) {
      setError('Failed to run bias analysis')
      console.error('Error running bias analysis:', error)
    } finally {
      setLoading(false)
    }
  }

  const getBiasSeverity = (biasType: string, detected: boolean, details: any): 'low' | 'medium' | 'high' | 'critical' => {
    if (!detected) return 'low'
    
    switch (biasType) {
      case 'reporting_bias':
        return details.ratio > 10 ? 'critical' : details.ratio > 5 ? 'high' : 'medium'
      case 'historical_bias':
        return details.disparity_ratio > 5 ? 'high' : 'medium'
      case 'group_attribution_bias':
        return Object.keys(details.strong_correlations || {}).length > 3 ? 'high' : 'medium'
      case 'implicit_bias':
        return Object.keys(details.significant_disparities || {}).length > 2 ? 'high' : 'medium'
      default:
        return 'medium'
    }
  }

  const getSeverityColor = (severity: string) => {
    switch (severity) {
      case 'critical': return 'bg-red-100 text-red-800 border-red-200'
      case 'high': return 'bg-orange-100 text-orange-800 border-orange-200'
      case 'medium': return 'bg-yellow-100 text-yellow-800 border-yellow-200'
      case 'low': return 'bg-green-100 text-green-800 border-green-200'
      default: return 'bg-gray-100 text-gray-800 border-gray-200'
    }
  }

  const getSeverityIcon = (severity: string) => {
    switch (severity) {
      case 'critical': return <XCircle className="h-4 w-4" />
      case 'high': return <AlertTriangle className="h-4 w-4" />
      case 'medium': return <Info className="h-4 w-4" />
      case 'low': return <CheckCircle className="h-4 w-4" />
      default: return <Info className="h-4 w-4" />
    }
  }

  const biasTypes: BiasType[] = [
    {
      id: 'reporting_bias',
      name: 'Reporting Bias',
      description: 'Frequency of events in dataset does not reflect real-world frequency',
      severity: getBiasSeverity('reporting_bias', biasAnalysis?.bias_detection.reporting_bias.detected || false, biasAnalysis?.bias_detection.reporting_bias || {}),
      detected: biasAnalysis?.bias_detection.reporting_bias.detected || false,
      details: biasAnalysis?.bias_detection.reporting_bias || {}
    },
    {
      id: 'historical_bias',
      name: 'Historical Bias',
      description: 'Historical data reflects past inequities',
      severity: getBiasSeverity('historical_bias', biasAnalysis?.bias_detection.historical_bias.detected || false, biasAnalysis?.bias_detection.historical_bias || {}),
      detected: biasAnalysis?.bias_detection.historical_bias.detected || false,
      details: biasAnalysis?.bias_detection.historical_bias || {}
    },
    {
      id: 'selection_bias',
      name: 'Selection Bias',
      description: 'Dataset examples not reflective of real-world distribution',
      severity: getBiasSeverity('selection_bias', biasAnalysis?.bias_detection.selection_bias.detected || false, biasAnalysis?.bias_detection.selection_bias || {}),
      detected: biasAnalysis?.bias_detection.selection_bias.detected || false,
      details: biasAnalysis?.bias_detection.selection_bias || {}
    },
    {
      id: 'group_attribution_bias',
      name: 'Group Attribution Bias',
      description: 'Generalizing individuals to entire groups',
      severity: getBiasSeverity('group_attribution_bias', biasAnalysis?.bias_detection.group_attribution_bias.detected || false, biasAnalysis?.bias_detection.group_attribution_bias || {}),
      detected: biasAnalysis?.bias_detection.group_attribution_bias.detected || false,
      details: biasAnalysis?.bias_detection.group_attribution_bias || {}
    },
    {
      id: 'implicit_bias',
      name: 'Implicit Bias',
      description: 'Assumptions based on personal experiences',
      severity: getBiasSeverity('implicit_bias', biasAnalysis?.bias_detection.implicit_bias.detected || false, biasAnalysis?.bias_detection.implicit_bias || {}),
      detected: biasAnalysis?.bias_detection.implicit_bias.detected || false,
      details: biasAnalysis?.bias_detection.implicit_bias || {}
    }
  ]

  const detectedBiasCount = biasTypes.filter(bias => bias.detected).length
  const criticalBiasCount = biasTypes.filter(bias => bias.detected && bias.severity === 'critical').length
  const highBiasCount = biasTypes.filter(bias => bias.detected && bias.severity === 'high').length

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-3xl font-bold">Comprehensive Bias Analysis</h1>
          <p className="text-muted-foreground">
            Advanced bias detection and analysis based on Google's ML Crash Course framework
          </p>
        </div>
        <div className="flex items-center space-x-2">
          <Badge variant="outline" className="flex items-center space-x-1">
            <Shield className="h-4 w-4" />
            <span>Bias Detection</span>
          </Badge>
          <Badge variant="outline" className="flex items-center space-x-1">
            <Target className="h-4 w-4" />
            <span>{detectedBiasCount} Detected</span>
          </Badge>
        </div>
      </div>

      {/* Error Display */}
      {error && (
        <Alert variant="destructive">
          <AlertTriangle className="h-4 w-4" />
          <AlertDescription>{error}</AlertDescription>
        </Alert>
      )}

      {/* Bias Overview Cards */}
      <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
        <Card>
          <CardHeader className="pb-2">
            <CardTitle className="text-sm font-medium">Total Bias Types</CardTitle>
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold">{biasTypes.length}</div>
            <p className="text-xs text-muted-foreground">Types analyzed</p>
          </CardContent>
        </Card>

        <Card>
          <CardHeader className="pb-2">
            <CardTitle className="text-sm font-medium">Detected Bias</CardTitle>
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold text-orange-600">{detectedBiasCount}</div>
            <p className="text-xs text-muted-foreground">Issues found</p>
          </CardContent>
        </Card>

        <Card>
          <CardHeader className="pb-2">
            <CardTitle className="text-sm font-medium">Critical Issues</CardTitle>
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold text-red-600">{criticalBiasCount}</div>
            <p className="text-xs text-muted-foreground">High priority</p>
          </CardContent>
        </Card>

        <Card>
          <CardHeader className="pb-2">
            <CardTitle className="text-sm font-medium">High Priority</CardTitle>
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold text-orange-600">{highBiasCount}</div>
            <p className="text-xs text-muted-foreground">Medium priority</p>
          </CardContent>
        </Card>
      </div>

      {/* Main Content Tabs */}
      <Tabs defaultValue="bias-types" className="space-y-4">
        <TabsList>
          <TabsTrigger value="bias-types">Bias Types</TabsTrigger>
          <TabsTrigger value="data-quality">Data Quality</TabsTrigger>
          <TabsTrigger value="fairness-metrics">Fairness Metrics</TabsTrigger>
          <TabsTrigger value="recommendations">Recommendations</TabsTrigger>
        </TabsList>

        <TabsContent value="bias-types" className="space-y-6">
          <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
            {biasTypes.map((bias) => (
              <Card key={bias.id} className={`border-2 ${bias.detected ? getSeverityColor(bias.severity) : 'border-gray-200'}`}>
                <CardHeader>
                  <div className="flex items-center justify-between">
                    <CardTitle className="flex items-center space-x-2">
                      {getSeverityIcon(bias.severity)}
                      <span>{bias.name}</span>
                    </CardTitle>
                    <Badge variant={bias.detected ? 'destructive' : 'secondary'}>
                      {bias.detected ? 'Detected' : 'Not Detected'}
                    </Badge>
                  </div>
                  <CardDescription>{bias.description}</CardDescription>
                </CardHeader>
                <CardContent>
                  {bias.detected && (
                    <div className="space-y-3">
                      <div className="text-sm">
                        <strong>Severity:</strong> {bias.severity.toUpperCase()}
                      </div>
                      {bias.id === 'reporting_bias' && bias.details.ratio && (
                        <div className="text-sm">
                          <strong>Distribution Ratio:</strong> {bias.details.ratio.toFixed(2)}:1
                        </div>
                      )}
                      {bias.id === 'historical_bias' && bias.details.indicators && (
                        <div className="text-sm">
                          <strong>Affected Groups:</strong> {
                            Object.keys(bias.details.indicators).filter(k => bias.details.indicators[k].detected).join(', ')
                          }
                        </div>
                      )}
                      {bias.id === 'group_attribution_bias' && bias.details.indicators && (
                        <div className="text-sm">
                          <strong>Strong Correlations:</strong> {
                            Object.keys(bias.details.indicators).filter(k => bias.details.indicators[k].detected).join(', ')
                          }
                        </div>
                      )}
                    </div>
                  )}
                </CardContent>
              </Card>
            ))}
          </div>
        </TabsContent>

        <TabsContent value="data-quality" className="space-y-6">
          <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
            {/* Data Skew Analysis */}
            <Card>
              <CardHeader>
                <CardTitle className="flex items-center space-x-2">
                  <PieChart className="h-5 w-5" />
                  <span>Data Skew Analysis</span>
                </CardTitle>
              </CardHeader>
              <CardContent>
                <div className="space-y-4">
                  {biasAnalysis?.data_quality.data_skew && Object.entries(biasAnalysis.data_quality.data_skew).map(([attr, skew]) => (
                    <div key={attr} className="space-y-2">
                      <div className="flex justify-between text-sm">
                        <span className="font-medium">{attr}</span>
                        <span className="text-muted-foreground">
                          Ratio: {skew.imbalance_ratio.toFixed(2)}:1
                        </span>
                      </div>
                      <Progress value={Math.min((skew.imbalance_ratio / 5) * 100, 100)} className="h-2" />
                      <div className="text-xs text-muted-foreground">
                        {skew.minority_group_size.toLocaleString()} minority vs {skew.majority_group_size.toLocaleString()} majority
                      </div>
                    </div>
                  ))}
                </div>
              </CardContent>
            </Card>

            {/* Missing Values Analysis */}
            <Card>
              <CardHeader>
                <CardTitle className="flex items-center space-x-2">
                  <AlertTriangle className="h-5 w-5" />
                  <span>Missing Values</span>
                </CardTitle>
              </CardHeader>
              <CardContent>
                <div className="space-y-4">
                  <div className="text-center">
                    <div className="text-2xl font-bold">{biasAnalysis?.dataset_info.missing_values_percentage.toFixed(2)}%</div>
                    <div className="text-sm text-muted-foreground">Overall missing values</div>
                  </div>
                  {biasAnalysis?.data_quality.missing_values && Object.entries(biasAnalysis.data_quality.missing_values).map(([attr, missing]) => (
                    <div key={attr} className="space-y-2">
                      <div className="text-sm font-medium">{attr}</div>
                      {Object.entries(missing).map(([group, rate]) => (
                        <div key={group} className="flex justify-between text-xs">
                          <span>Group {group}</span>
                          <span>{(rate * 100).toFixed(1)}%</span>
                        </div>
                      ))}
                    </div>
                  ))}
                </div>
              </CardContent>
            </Card>
          </div>
        </TabsContent>

        <TabsContent value="fairness-metrics" className="space-y-6">
          <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
            {biasAnalysis?.fairness_metrics && Object.entries(biasAnalysis.fairness_metrics).map(([attr, metrics]) => (
              <Card key={attr}>
                <CardHeader>
                  <CardTitle className="flex items-center space-x-2">
                    <Users className="h-5 w-5" />
                    <span>Fairness Metrics - {attr}</span>
                  </CardTitle>
                </CardHeader>
                <CardContent>
                  <div className="space-y-4">
                    {/* Demographic Parity */}
                    <div className="space-y-2">
                      <div className="flex items-center justify-between">
                        <span className="text-sm font-medium">Demographic Parity</span>
                        <Badge variant={metrics.demographic_parity.fair ? 'secondary' : 'destructive'}>
                          {metrics.demographic_parity.fair ? 'Fair' : 'Unfair'}
                        </Badge>
                      </div>
                      <div className="space-y-1">
                        {Object.entries(metrics.demographic_parity.acceptance_rates).map(([group, rate]) => (
                          <div key={group} className="flex justify-between text-xs">
                            <span>Group {group}</span>
                            <span>{(rate * 100).toFixed(1)}%</span>
                          </div>
                        ))}
                      </div>
                      <div className="text-xs text-muted-foreground">
                        Disparity: {(metrics.demographic_parity.disparity * 100).toFixed(1)}%
                      </div>
                    </div>

                    {/* Equality of Opportunity */}
                    <div className="space-y-2">
                      <div className="flex items-center justify-between">
                        <span className="text-sm font-medium">Equality of Opportunity</span>
                        <Badge variant={metrics.equality_of_opportunity.fair ? 'secondary' : 'destructive'}>
                          {metrics.equality_of_opportunity.fair ? 'Fair' : 'Unfair'}
                        </Badge>
                      </div>
                      <div className="space-y-1">
                        {Object.entries(metrics.equality_of_opportunity.opportunity_rates).map(([group, rate]) => (
                          <div key={group} className="flex justify-between text-xs">
                            <span>Group {group}</span>
                            <span>{(rate * 100).toFixed(1)}%</span>
                          </div>
                        ))}
                      </div>
                      <div className="text-xs text-muted-foreground">
                        Disparity: {(metrics.equality_of_opportunity.disparity * 100).toFixed(1)}%
                      </div>
                    </div>
                  </div>
                </CardContent>
              </Card>
            ))}
          </div>
        </TabsContent>

        <TabsContent value="recommendations" className="space-y-6">
          <Card>
            <CardHeader>
              <CardTitle className="flex items-center space-x-2">
                <FileText className="h-5 w-5" />
                <span>Bias Mitigation Recommendations</span>
              </CardTitle>
            </CardHeader>
            <CardContent>
              <div className="space-y-4">
                {biasAnalysis?.recommendations.map((recommendation, index) => (
                  <div key={index} className="flex items-start space-x-3 p-3 bg-muted rounded-lg">
                    <div className="flex-shrink-0 w-6 h-6 bg-primary text-primary-foreground rounded-full flex items-center justify-center text-sm font-bold">
                      {index + 1}
                    </div>
                    <p className="text-sm">{recommendation}</p>
                  </div>
                ))}
              </div>
            </CardContent>
          </Card>
        </TabsContent>
      </Tabs>
    </div>
  )
}
