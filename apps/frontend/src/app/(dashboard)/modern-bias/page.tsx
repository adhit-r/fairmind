'use client'

import { useState } from 'react'
import { useModernBias } from '@/lib/api/hooks/useModernBias'
import { useModels } from '@/lib/api/hooks/useModels'
import { generateBiasPDF, generateBiasJSON, type BiasEvaluationPDFData } from '@/lib/export/pdf-generator'
import { Card } from '@/components/ui/card'
import { Button } from '@/components/ui/button'
import { Input } from '@/components/ui/input'
import { Label } from '@/components/ui/label'
import { Textarea } from '@/components/ui/textarea'
import { Alert, AlertDescription, AlertTitle } from '@/components/ui/alert'
import { Badge } from '@/components/ui/badge'
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/ui/tabs'
import { Progress } from '@/components/ui/progress'
import { useToast } from '@/hooks/use-toast'
import {
  IconAlertTriangle,
  IconBrain,
  IconCheck,
  IconDownload,
  IconEye,
  IconFile,
  IconFileText,
  IconFlame,
  IconLock,
  IconRefresh,
  IconShield,
  IconX,
  IconZoomIn
} from '@tabler/icons-react'

// Bias test categories for form
const BIAS_TESTS = [
  { id: 'stereoset', label: 'StereoSet', description: 'Stereotype detection in generated text', category: 'extrinsic' },
  { id: 'crowspairs', label: 'CrowS-Pairs', description: 'Crowdsourced stereotype pairs', category: 'extrinsic' },
  { id: 'weat', label: 'WEAT', description: 'Word Embedding Association Test', category: 'intrinsic' },
  { id: 'seat', label: 'SEAT', description: 'Sentence Embedding Association Test', category: 'intrinsic' },
  { id: 'minimal_pairs', label: 'Minimal Pairs', description: 'Minimal pair perturbation test', category: 'representational' },
  { id: 'bbq', label: 'BBQ', description: 'Bias Benchmark for QA', category: 'allocational' },
]

interface BiasEvaluationRequest {
  model_description: string
  model_type: 'llm' | 'image_gen' | 'audio_gen' | 'video_gen'
  selected_tests: string[]
  test_samples?: string
  protected_attributes?: string[]
}

interface ComprehensiveBiasResult {
  timestamp: string
  model_type: string
  evaluation_summary: {
    total_tests: number
    tests_passed: number
    tests_failed: number
    overall_bias_rate: number
    evaluation_time?: string
  }
  bias_tests: {
    pre_deployment?: { [key: string]: any }
    real_time_monitoring?: { [key: string]: any }
    post_deployment?: { [key: string]: any }
  }
  explainability_analysis: {
    methods_used?: string[]
    insights?: string[]
    visualizations?: string[]
    confidence?: number
  }
  overall_risk: 'low' | 'medium' | 'high' | 'critical'
  risk_factors?: string[]
  recommendations: string[]
  compliance_status: {
    gdpr_compliant?: boolean
    ai_act_compliant?: boolean
    fairness_score?: number
  }
}

export default function LLMBiasDetectionPage() {
  const { loading, error } = useModernBias()
  const { models, loading: modelsLoading } = useModels()
  const { toast } = useToast()

  const [activeTab, setActiveTab] = useState<'form' | 'results'>('form')
  const [results, setResults] = useState<ComprehensiveBiasResult | null>(null)
  const [isRunning, setIsRunning] = useState(false)

  const [formData, setFormData] = useState<BiasEvaluationRequest>({
    model_description: '',
    model_type: 'llm',
    selected_tests: ['stereoset', 'crowspairs', 'weat'],
    protected_attributes: ['gender', 'race', 'age'],
  })

  const handleRunEvaluation = async () => {
    if (!formData.model_description.trim()) {
      toast({
        title: 'Model description required',
        description: 'Please provide a description of the LLM you want to test.',
        variant: 'destructive',
      })
      return
    }

    if (formData.selected_tests.length === 0) {
      toast({
        title: 'At least one test required',
        description: 'Select at least one bias test to run.',
        variant: 'destructive',
      })
      return
    }

    try {
      setIsRunning(true)

      // Mock comprehensive evaluation - in production this would call the backend
      const mockResults: ComprehensiveBiasResult = {
        timestamp: new Date().toISOString(),
        model_type: formData.model_type,
        evaluation_summary: {
          total_tests: formData.selected_tests.length,
          tests_passed: Math.floor(formData.selected_tests.length * 0.6),
          tests_failed: Math.ceil(formData.selected_tests.length * 0.4),
          overall_bias_rate: 0.42,
          evaluation_time: '2m 34s',
        },
        bias_tests: {
          pre_deployment: {
            stereoset: { bias_score: 0.38, confidence: 0.87, status: 'warning' },
            crowspairs: { bias_score: 0.51, confidence: 0.92, status: 'high_risk' },
            weat: { bias_score: 0.29, confidence: 0.91, status: 'low_risk' },
          },
          real_time_monitoring: {
            sentiment_bias: { score: 0.33, trend: 'stable' },
            representation_bias: { score: 0.45, trend: 'increasing' },
          },
          post_deployment: {
            user_feedback_bias: { negative_rate: 0.12, fair_rating: 0.78 },
          },
        },
        explainability_analysis: {
          methods_used: ['attention_visualization', 'activation_patching', 'counterfactual'],
          confidence: 0.85,
          insights: [
            'Model shows higher association of certain professions with specific genders',
            'Attention heads 4, 8, and 12 disproportionately weight demographic tokens',
            'Counterfactual analysis reveals 23% performance drop when demographic terms are masked',
          ],
          visualizations: ['/api/v1/visualizations/attention-heatmap.png'],
        },
        overall_risk: 'medium',
        risk_factors: [
          'Gender bias detected in profession-related outputs',
          'Underrepresentation of minority groups in training data',
          'Context-dependent bias in certain domains',
        ],
        recommendations: [
          'Implement debiasing techniques during training',
          'Expand training data to include underrepresented groups',
          'Add fairness constraints to the loss function',
          'Monitor model behavior in production for drift',
          'Conduct regular fairness audits (monthly)',
        ],
        compliance_status: {
          gdpr_compliant: false,
          ai_act_compliant: false,
          fairness_score: 0.58,
        },
      }

      // Simulate API call delay
      await new Promise(resolve => setTimeout(resolve, 2000))

      setResults(mockResults)
      setActiveTab('results')

      toast({
        title: 'Evaluation completed',
        description: 'Bias detection analysis finished. Review the results tab.',
      })
    } catch (err) {
      toast({
        title: 'Evaluation failed',
        description: err instanceof Error ? err.message : 'An error occurred during evaluation.',
        variant: 'destructive',
      })
    } finally {
      setIsRunning(false)
    }
  }

  const handleToggleTest = (testId: string) => {
    setFormData(prev => ({
      ...prev,
      selected_tests: prev.selected_tests.includes(testId)
        ? prev.selected_tests.filter(t => t !== testId)
        : [...prev.selected_tests, testId],
    }))
  }

  const handleExportPDF = () => {
    if (!results) {
      toast({
        title: 'No results to export',
        description: 'Please run an evaluation first.',
        variant: 'destructive',
      })
      return
    }

    try {
      const pdfData: BiasEvaluationPDFData = {
        timestamp: results.timestamp,
        modelType: results.model_type,
        modelDescription: formData.model_description,
        evaluationSummary: results.evaluation_summary,
        overallRisk: results.overall_risk as any,
        riskFactors: results.risk_factors,
        complianceStatus: results.compliance_status,
        explainabilityAnalysis: results.explainability_analysis,
        recommendations: results.recommendations,
        selectedTests: formData.selected_tests,
      }

      generateBiasPDF(pdfData)

      toast({
        title: 'PDF exported',
        description: 'Bias evaluation report has been downloaded.',
      })
    } catch (error) {
      toast({
        title: 'Export failed',
        description: error instanceof Error ? error.message : 'Failed to generate PDF',
        variant: 'destructive',
      })
    }
  }

  const handleExportJSON = () => {
    if (!results) {
      toast({
        title: 'No results to export',
        description: 'Please run an evaluation first.',
        variant: 'destructive',
      })
      return
    }

    try {
      const jsonData: BiasEvaluationPDFData = {
        timestamp: results.timestamp,
        modelType: results.model_type,
        modelDescription: formData.model_description,
        evaluationSummary: results.evaluation_summary,
        overallRisk: results.overall_risk as any,
        riskFactors: results.risk_factors,
        complianceStatus: results.compliance_status,
        explainabilityAnalysis: results.explainability_analysis,
        recommendations: results.recommendations,
        selectedTests: formData.selected_tests,
      }

      generateBiasJSON(jsonData)

      toast({
        title: 'JSON exported',
        description: 'Evaluation data has been downloaded in JSON format.',
      })
    } catch (error) {
      toast({
        title: 'Export failed',
        description: error instanceof Error ? error.message : 'Failed to generate JSON',
        variant: 'destructive',
      })
    }
  }

  const getRiskColor = (risk: string) => {
    switch (risk) {
      case 'low':
        return 'bg-green-100 text-green-800 border-green-300'
      case 'medium':
        return 'bg-yellow-100 text-yellow-800 border-yellow-300'
      case 'high':
        return 'bg-orange-100 text-orange-800 border-orange-300'
      case 'critical':
        return 'bg-red-100 text-red-800 border-red-300'
      default:
        return 'bg-gray-100 text-gray-800 border-gray-300'
    }
  }

  const getRiskIcon = (risk: string) => {
    switch (risk) {
      case 'low':
        return <IconCheck className="h-5 w-5" />
      case 'medium':
        return <IconAlertTriangle className="h-5 w-5" />
      case 'high':
        return <IconFlame className="h-5 w-5" />
      case 'critical':
        return <IconX className="h-5 w-5" />
      default:
        return null
    }
  }

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="border-b-4 border-black pb-4">
        <h1 className="text-4xl font-bold">LLM Bias Detection</h1>
        <p className="text-muted-foreground mt-2">
          Comprehensive bias testing with WEAT, SEAT, StereoSet, CrowS-Pairs, Minimal Pairs, and BBQ. Includes explainability analysis and compliance assessment.
        </p>
      </div>

      {error && (
        <Alert className="border-2 border-red-500 bg-red-50 shadow-brutal">
          <IconAlertTriangle className="h-4 w-4" />
          <AlertTitle>Error</AlertTitle>
          <AlertDescription>{error.message}</AlertDescription>
        </Alert>
      )}

      <Tabs value={activeTab} onValueChange={(v) => setActiveTab(v as 'form' | 'results')} className="space-y-4">
        <TabsList className="border-2 border-black bg-white">
          <TabsTrigger value="form" className="border-r-2 border-black">
            Test Configuration
          </TabsTrigger>
          <TabsTrigger value="results" disabled={!results}>
            Results & Analysis
          </TabsTrigger>
        </TabsList>

        {/* Form Tab */}
        <TabsContent value="form" className="space-y-6">
          <Card className="p-6 border-4 border-black shadow-brutal-lg">
            <div className="space-y-6">
              {/* Model Description */}
              <div className="space-y-3">
                <Label className="text-lg font-bold">LLM Details *</Label>
                <Textarea
                  placeholder="Example: GPT-3.5 fine-tuned for customer service with 1.3B parameters. Trained on conversation data from 2021-2024. Used for automated support ticket responses."
                  value={formData.model_description}
                  onChange={(e) => setFormData({ ...formData, model_description: e.target.value })}
                  className="border-2 border-black focus:border-4 font-mono text-sm"
                  rows={4}
                  disabled={isRunning}
                />
                <p className="text-xs text-muted-foreground">
                  Describe your LLM: architecture, size, training data, purpose, and deployment context
                </p>
              </div>

              {/* Model Type */}
              <div className="space-y-3">
                <Label className="text-lg font-bold">Model Type</Label>
                <div className="grid grid-cols-2 gap-3">
                  {['llm', 'image_gen', 'audio_gen', 'video_gen'].map(type => (
                    <button
                      key={type}
                      onClick={() => setFormData({ ...formData, model_type: type as any })}
                      disabled={isRunning}
                      className={`p-3 border-2 text-left font-medium transition-all ${
                        formData.model_type === type
                          ? 'border-black bg-black text-white'
                          : 'border-black bg-white hover:bg-gray-100'
                      }`}
                    >
                      {type === 'llm' ? 'LLM' : type === 'image_gen' ? 'Image Gen' : type === 'audio_gen' ? 'Audio Gen' : 'Video Gen'}
                    </button>
                  ))}
                </div>
              </div>

              {/* Test Selection */}
              <div className="space-y-3">
                <Label className="text-lg font-bold">Bias Tests ({formData.selected_tests.length} selected)</Label>
                <div className="grid grid-cols-1 md:grid-cols-2 gap-3">
                  {BIAS_TESTS.map(test => (
                    <button
                      key={test.id}
                      onClick={() => handleToggleTest(test.id)}
                      disabled={isRunning}
                      className={`p-3 border-2 text-left transition-all ${
                        formData.selected_tests.includes(test.id)
                          ? 'border-4 border-black bg-black text-white shadow-brutal'
                          : 'border-black bg-white hover:bg-gray-50'
                      }`}
                    >
                      <div className="font-bold text-sm">{test.label}</div>
                      <div className="text-xs opacity-75 mt-1">{test.description}</div>
                    </button>
                  ))}
                </div>
              </div>

              {/* Protected Attributes */}
              <div className="space-y-3">
                <Label className="text-lg font-bold">Protected Attributes</Label>
                <div className="flex flex-wrap gap-2">
                  {['gender', 'race', 'age', 'religion', 'disability', 'nationality'].map(attr => (
                    <button
                      key={attr}
                      onClick={() => {
                        const attrs = formData.protected_attributes || []
                        setFormData({
                          ...formData,
                          protected_attributes: attrs.includes(attr)
                            ? attrs.filter(a => a !== attr)
                            : [...attrs, attr],
                        })
                      }}
                      disabled={isRunning}
                      className={`px-3 py-2 border-2 text-sm font-medium transition-all ${
                        (formData.protected_attributes || []).includes(attr)
                          ? 'border-black bg-black text-white'
                          : 'border-black bg-white hover:bg-gray-100'
                      }`}
                    >
                      {attr}
                    </button>
                  ))}
                </div>
              </div>

              {/* Run Button */}
              <Button
                onClick={handleRunEvaluation}
                disabled={isRunning || loading}
                size="lg"
                className="w-full border-2 border-black font-bold h-12 text-base shadow-brutal hover:shadow-brutal-lg"
              >
                {isRunning ? (
                  <>
                    <IconRefresh className="h-5 w-5 mr-2 animate-spin" />
                    Running Evaluation...
                  </>
                ) : (
                  <>
                    <IconBrain className="h-5 w-5 mr-2" />
                    Run Comprehensive Bias Evaluation
                  </>
                )}
              </Button>
            </div>
          </Card>
        </TabsContent>

        {/* Results Tab */}
        <TabsContent value="results" className="space-y-6">
          {results && (
            <>
              {/* Overall Risk Banner */}
              <div className={`border-4 border-black p-6 shadow-brutal-lg ${getRiskColor(results.overall_risk)}`}>
                <div className="flex items-center justify-between">
                  <div>
                    <div className="flex items-center gap-2 mb-1">
                      {getRiskIcon(results.overall_risk)}
                      <h2 className="text-2xl font-bold uppercase">
                        {results.overall_risk} Risk
                      </h2>
                    </div>
                    <p className="font-medium">
                      {results.evaluation_summary.overall_bias_rate && (
                        `Overall Bias Rate: ${(results.evaluation_summary.overall_bias_rate * 100).toFixed(1)}%`
                      )}
                    </p>
                  </div>
                  <div className="text-right">
                    <div className="text-3xl font-bold">
                      {results.evaluation_summary.tests_passed}/{results.evaluation_summary.total_tests}
                    </div>
                    <p className="text-sm font-medium">Tests Passed</p>
                  </div>
                </div>
              </div>

              {/* Risk Factors */}
              {results.risk_factors && results.risk_factors.length > 0 && (
                <Card className="p-6 border-2 border-red-500 shadow-brutal">
                  <h3 className="text-xl font-bold mb-4 flex items-center gap-2">
                    <IconFlame className="h-5 w-5 text-red-500" />
                    Risk Factors
                  </h3>
                  <ul className="space-y-2">
                    {results.risk_factors.map((factor, idx) => (
                      <li key={idx} className="flex gap-3 text-sm">
                        <span className="font-bold text-red-600 flex-shrink-0">•</span>
                        <span>{factor}</span>
                      </li>
                    ))}
                  </ul>
                </Card>
              )}

              {/* Evaluation Summary */}
              <Card className="p-6 border-2 border-black shadow-brutal">
                <h3 className="text-xl font-bold mb-4">Evaluation Summary</h3>
                <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
                  <div className="border-l-4 border-black pl-3">
                    <p className="text-xs text-muted-foreground">Total Tests</p>
                    <p className="text-2xl font-bold">{results.evaluation_summary.total_tests}</p>
                  </div>
                  <div className="border-l-4 border-green-500 pl-3">
                    <p className="text-xs text-muted-foreground">Passed</p>
                    <p className="text-2xl font-bold text-green-600">{results.evaluation_summary.tests_passed}</p>
                  </div>
                  <div className="border-l-4 border-red-500 pl-3">
                    <p className="text-xs text-muted-foreground">Failed</p>
                    <p className="text-2xl font-bold text-red-600">{results.evaluation_summary.tests_failed}</p>
                  </div>
                  <div className="border-l-4 border-blue-500 pl-3">
                    <p className="text-xs text-muted-foreground">Duration</p>
                    <p className="text-xl font-bold">{results.evaluation_summary.evaluation_time || 'N/A'}</p>
                  </div>
                </div>
              </Card>

              {/* Compliance Status */}
              <Card className="p-6 border-2 border-black shadow-brutal">
                <h3 className="text-xl font-bold mb-4 flex items-center gap-2">
                  <IconShield className="h-5 w-5" />
                  Compliance Status
                </h3>
                <div className="space-y-3">
                  <div className="flex items-center justify-between p-3 border-2 border-black bg-gray-50">
                    <span className="font-medium">GDPR Compliance</span>
                    <Badge variant={results.compliance_status.gdpr_compliant ? 'default' : 'destructive'} className="border-2 border-black">
                      {results.compliance_status.gdpr_compliant ? 'Compliant' : 'Non-Compliant'}
                    </Badge>
                  </div>
                  <div className="flex items-center justify-between p-3 border-2 border-black bg-gray-50">
                    <span className="font-medium">EU AI Act</span>
                    <Badge variant={results.compliance_status.ai_act_compliant ? 'default' : 'destructive'} className="border-2 border-black">
                      {results.compliance_status.ai_act_compliant ? 'Compliant' : 'Non-Compliant'}
                    </Badge>
                  </div>
                  {results.compliance_status.fairness_score !== undefined && (
                    <div className="space-y-2 p-3 border-2 border-black bg-gray-50">
                      <div className="flex items-center justify-between">
                        <span className="font-medium">Fairness Score</span>
                        <span className="font-bold">{(results.compliance_status.fairness_score * 100).toFixed(1)}%</span>
                      </div>
                      <Progress value={results.compliance_status.fairness_score * 100} className="h-2 border border-black" />
                    </div>
                  )}
                </div>
              </Card>

              {/* Explainability Analysis */}
              {results.explainability_analysis && (
                <Card className="p-6 border-2 border-black shadow-brutal">
                  <h3 className="text-xl font-bold mb-4 flex items-center gap-2">
                    <IconEye className="h-5 w-5" />
                    Explainability Analysis
                  </h3>
                  <div className="space-y-4">
                    {results.explainability_analysis.methods_used && (
                      <div>
                        <p className="font-medium mb-2">Methods Used:</p>
                        <div className="flex flex-wrap gap-2">
                          {results.explainability_analysis.methods_used.map((method, idx) => (
                            <Badge key={idx} variant="outline" className="border-2 border-black">
                              {method.replace(/_/g, ' ')}
                            </Badge>
                          ))}
                        </div>
                      </div>
                    )}
                    {results.explainability_analysis.confidence !== undefined && (
                      <div className="space-y-2">
                        <p className="font-medium">Analysis Confidence: {(results.explainability_analysis.confidence * 100).toFixed(1)}%</p>
                        <Progress value={results.explainability_analysis.confidence * 100} className="h-2 border border-black" />
                      </div>
                    )}
                    {results.explainability_analysis.insights && results.explainability_analysis.insights.length > 0 && (
                      <div>
                        <p className="font-medium mb-2">Key Insights:</p>
                        <ul className="space-y-2">
                          {results.explainability_analysis.insights.map((insight, idx) => (
                            <li key={idx} className="flex gap-3 text-sm p-2 bg-blue-50 border-l-4 border-blue-500">
                              <IconZoomIn className="h-4 w-4 flex-shrink-0 mt-0.5 text-blue-600" />
                              <span>{insight}</span>
                            </li>
                          ))}
                        </ul>
                      </div>
                    )}
                  </div>
                </Card>
              )}

              {/* Recommendations */}
              {results.recommendations && results.recommendations.length > 0 && (
                <Card className="p-6 border-2 border-green-500 shadow-brutal bg-green-50">
                  <h3 className="text-xl font-bold mb-4">Recommendations</h3>
                  <ul className="space-y-3">
                    {results.recommendations.map((rec, idx) => (
                      <li key={idx} className="flex gap-3 text-sm">
                        <span className="font-bold text-green-600 flex-shrink-0">{idx + 1}.</span>
                        <span>{rec}</span>
                      </li>
                    ))}
                  </ul>
                </Card>
              )}

              {/* Export Options */}
              <div className="flex gap-3">
                <Button
                  variant="outline"
                  className="flex-1 border-2 border-black font-bold hover:bg-black hover:text-white"
                  onClick={handleExportPDF}
                >
                  <IconFile className="h-4 w-4 mr-2" />
                  Export as PDF
                </Button>
                <Button
                  variant="outline"
                  className="flex-1 border-2 border-black font-bold hover:bg-black hover:text-white"
                  onClick={handleExportJSON}
                >
                  <IconFileText className="h-4 w-4 mr-2" />
                  Export as JSON
                </Button>
              </div>
            </>
          )}
        </TabsContent>
      </Tabs>
    </div>
  )
}
