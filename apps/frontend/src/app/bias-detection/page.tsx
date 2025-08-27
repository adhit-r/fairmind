'use client'

import React, { useState, useEffect } from 'react'
import { 
  Eye, 
  Upload, 
  FileText, 
  BarChart3, 
  AlertTriangle, 
  CheckCircle, 
  Clock,
  TrendingUp,
  TrendingDown,
  Shield,
  Users,
  Activity,
  Zap,
  Brain,
  Target
} from 'lucide-react'
import { PageWrapper } from '@/components/core/PageWrapper'
import { Card } from '@/components/core/Card'
import { Button } from '@/components/core/Button'
import { api, type BiasAnalysisResult, type Dataset } from '@/config/api'

interface BiasAnalysis {
  id: string
  model_name: string
  status: 'completed' | 'running' | 'failed' | 'pending'
  created_at: string
  bias_score: number
  fairness_score: number
  protected_attributes: string[]
  recommendations: string[]
}

export default function BiasDetection() {
  const [biasAnalyses, setBiasAnalyses] = useState<BiasAnalysisResult[]>([])
  const [datasets, setDatasets] = useState<Dataset[]>([])
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)
  const [mounted, setMounted] = useState(false)

  useEffect(() => {
    setMounted(true)
  }, [])

  useEffect(() => {
    if (!mounted) return

    const fetchData = async () => {
      try {
        setLoading(true)
        
        // Fetch bias analysis history and available datasets
        const [analysesResponse, datasetsResponse] = await Promise.all([
          api.getBiasAnalysisHistory(),
          api.getBiasDatasets()
        ])

        if (analysesResponse.success && analysesResponse.data) {
          setBiasAnalyses(analysesResponse.data)
        }

        if (datasetsResponse.success && datasetsResponse.data) {
          setDatasets(datasetsResponse.data)
        }
      } catch (err) {
        console.error('Error fetching bias detection data:', err)
        setError(err instanceof Error ? err.message : 'Unknown error occurred')
      } finally {
        setLoading(false)
      }
    }

    fetchData()
  }, [mounted])

  // Calculate metrics from real data
  const modelsAnalyzed = biasAnalyses.length
  const averageBiasScore = biasAnalyses.length > 0 
    ? biasAnalyses.reduce((sum, analysis) => sum + (analysis.biasScore || 0), 0) / biasAnalyses.length 
    : 0
  const highRiskModels = biasAnalyses.filter(analysis => (analysis.biasScore || 0) > 0.7).length
  const averageFairnessScore = biasAnalyses.length > 0 
    ? biasAnalyses.reduce((sum, analysis) => sum + (analysis.fairnessScore || 0), 0) / biasAnalyses.length 
    : 0

  if (!mounted) {
    return (
      <div className="space-y-6 p-4 md:p-6 max-w-[2000px] mx-auto">
        <div className="text-center py-8">
          <div className="animate-pulse">Loading...</div>
        </div>
      </div>
    )
  }

  return (
    <div className="space-y-6 p-4 md:p-6 max-w-[2000px] mx-auto">
      {/* Header Section */}
      <div className="space-y-2">
        <h1 className="text-2xl md:text-3xl font-bold tracking-tight text-gold">
          BIAS_DETECTION
          </h1>
        <p className="text-xs md:text-sm text-muted-foreground font-mono">
          ANALYZE.AND.DETECT.BIAS.IN.AI.MODELS.FOR.FAIRNESS.AND.COMPLIANCE
        </p>
      </div>

      {/* Bias Detection Metrics */}
      <div className="grid gap-4 sm:grid-cols-2 lg:grid-cols-4">
        <div className="bg-card border border-border rounded-lg p-4">
          <div className="flex items-center justify-between">
            <div>
              <p className="text-xs text-muted-foreground font-mono">MODELS_ANALYZED</p>
              <p className="text-lg font-bold">{modelsAnalyzed}</p>
            </div>
            <div className="flex items-center gap-2">
              <svg className="h-4 w-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 19v-6a2 2 0 00-2-2H5a2 2 0 00-2 2v6a2 2 0 002 2h2a2 2 0 002-2zm0 0V9a2 2 0 012-2h2a2 2 0 012 2v10m-6 0a2 2 0 002 2h2a2 2 0 002-2m0 0V5a2 2 0 012-2h2a2 2 0 012 2v14a2 2 0 01-2 2h-2a2 2 0 01-2-2z" />
              </svg>
              <div className="flex items-center gap-1">
                <span className="text-xs text-muted-foreground">
                  {modelsAnalyzed > 0 ? `${modelsAnalyzed} ANALYZED` : 'NO_DATA'}
                </span>
              </div>
            </div>
          </div>
        </div>
        <div className="bg-card border border-border rounded-lg p-4">
          <div className="flex items-center justify-between">
            <div>
              <p className="text-xs text-muted-foreground font-mono">AVERAGE_BIAS_SCORE</p>
              <p className="text-lg font-bold">
                {averageBiasScore > 0 ? `${(averageBiasScore * 100).toFixed(1)}%` : '--'}
              </p>
            </div>
            <div className="flex items-center gap-2">
              <svg className="h-4 w-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 12l2 2 4-4m5.618-4.016A11.955 11.955 0 0112 2.944a11.955 11.955 0 01-8.618 3.04A12.02 12.02 0 003 9c0 5.591 3.824 10.29 9 11.622 5.176-1.332 9-6.03 9-11.622 0-1.042-.133-2.052-.382-3.016z" />
              </svg>
              <div className="flex items-center gap-1">
                <span className="text-xs text-muted-foreground">
                  {averageBiasScore > 0 ? 'ANALYZED' : 'NO_ANALYSIS'}
                </span>
              </div>
            </div>
          </div>
        </div>
        <div className="bg-card border border-border rounded-lg p-4">
          <div className="flex items-center justify-between">
            <div>
              <p className="text-xs text-muted-foreground font-mono">HIGH_RISK_MODELS</p>
              <p className="text-lg font-bold">{highRiskModels}</p>
            </div>
            <div className="flex items-center gap-2">
              <svg className="h-4 w-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 9v2m0 4h.01m-6.938 4h13.856c1.54 0 2.502-1.667 1.732-2.5L13.732 4c-.77-.833-1.964-.833-2.732 0L3.732 16.5c-.77.833.192 2.5 1.732 2.5z" />
              </svg>
              <div className="flex items-center gap-1">
                <span className="text-xs text-muted-foreground">
                  {highRiskModels > 0 ? 'ATTENTION_NEEDED' : 'CLEAN'}
                </span>
              </div>
            </div>
          </div>
        </div>
        <div className="bg-card border border-border rounded-lg p-4">
          <div className="flex items-center justify-between">
            <div>
              <p className="text-xs text-muted-foreground font-mono">FAIRNESS_SCORE</p>
              <p className="text-lg font-bold">
                {averageFairnessScore > 0 ? `${(averageFairnessScore * 100).toFixed(1)}%` : '--'}
              </p>
            </div>
            <div className="flex items-center gap-2">
              <svg className="h-4 w-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9.663 17h4.673M12 3v1m6.364 1.636l-.707.707M21 12h-1M4 12H3m3.343-5.657l-.707-.707m2.828 9.9a5 5 0 117.072 0l-.548.547A3.374 3.374 0 0014 18.469V19a2 2 0 11-4 0v-.531c0-.895-.356-1.754-.988-2.386l-.548-.547z" />
              </svg>
              <div className="flex items-center gap-1">
                <span className="text-xs text-muted-foreground">
                  {averageFairnessScore > 0 ? 'CALCULATED' : 'NO_DATA'}
                </span>
              </div>
            </div>
          </div>
        </div>
      </div>

      {/* Action Section */}
      <div className="flex flex-col sm:flex-row gap-4 items-start sm:items-center justify-between">
        <div className="flex flex-wrap gap-2">
          <button className="bg-gold text-gold-foreground hover:bg-gold/90 w-full sm:w-auto px-4 py-2 rounded font-mono text-sm transition-colors">
            <svg className="inline mr-2 h-4 w-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 4v16m8-8H4" />
            </svg>
            <span className="whitespace-nowrap">NEW_ANALYSIS</span>
          </button>
          <button className="bg-transparent border border-border hover:bg-accent w-full sm:w-auto px-4 py-2 rounded font-mono text-sm transition-colors">
            <svg className="inline mr-2 h-4 w-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M7 16a4 4 0 01-.88-7.903A5 5 0 1115.9 6L16 6a5 5 0 011 9.9M15 13l-3-3m0 0l-3 3m3-3v12" />
            </svg>
            <span className="whitespace-nowrap">BATCH_ANALYSIS</span>
          </button>
        </div>
      </div>

      {/* Main Content Grid */}
      <div className="grid gap-4 md:gap-6 grid-cols-1 lg:grid-cols-3">
        {/* Bias Analysis Chart */}
        <div className="bg-card border border-border rounded-lg lg:col-span-2 min-h-[500px] flex flex-col">
          <div className="p-4 border-b border-border">
            <h3 className="text-sm font-bold text-gold">BIAS_ANALYSIS_RADAR</h3>
            <p className="text-xs text-muted-foreground font-mono">
              DEMOGRAPHIC.BIAS.DETECTION.AND.FAIRNESS.METRICS
            </p>
          </div>
          <div className="flex-1 p-4">
            {loading ? (
              <div className="h-full w-full flex items-center justify-center">
                <div className="text-center">
                  <div className="animate-pulse">Loading bias analysis data...</div>
                </div>
              </div>
            ) : biasAnalyses.length > 0 ? (
              <div className="space-y-4">
                {biasAnalyses.slice(0, 5).map((analysis) => (
                  <div key={analysis.id} className="border border-border rounded p-3">
                    <div className="flex justify-between items-start">
                      <div>
                        <h4 className="font-mono text-sm font-bold">{analysis.modelName}</h4>
                        <p className="text-xs text-muted-foreground">
                          Bias Score: {((analysis.biasScore || 0) * 100).toFixed(1)}% | 
                          Fairness: {((analysis.fairnessScore || 0) * 100).toFixed(1)}%
                        </p>
                      </div>
                      <div className={`text-xs px-2 py-1 rounded ${
                        (analysis.biasScore || 0) > 0.7 ? 'bg-red-500/20 text-red-400' :
                        (analysis.biasScore || 0) > 0.3 ? 'bg-yellow-500/20 text-yellow-400' :
                        'bg-green-500/20 text-green-400'
                      }`}>
                        {(analysis.biasScore || 0) > 0.7 ? 'HIGH_RISK' :
                         (analysis.biasScore || 0) > 0.3 ? 'MEDIUM_RISK' : 'LOW_RISK'}
                      </div>
                    </div>
                  </div>
                ))}
              </div>
            ) : (
              <div className="h-full w-full flex items-center justify-center">
                <div className="text-center">
                  <div className="w-24 h-24 bg-muted rounded-lg flex items-center justify-center mx-auto mb-4">
                    <svg className="w-12 h-12 text-muted-foreground" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 12l2 2 4-4m5.618-4.016A11.955 11.955 0 0112 2.944a11.955 11.955 0 01-8.618 3.04A12.02 12.02 0 003 9c0 5.591 3.824 10.29 9 11.622 5.176-1.332 9-6.03 9-11.622 0-1.042-.133-2.052-.382-3.016z" />
                    </svg>
                  </div>
                  <h4 className="text-lg font-bold mb-2">NO_BIAS_DATA_AVAILABLE</h4>
                  <p className="text-sm text-muted-foreground font-mono">
                    UPLOAD_MODELS_TO_SEE_BIAS_ANALYSIS_RESULTS
                  </p>
                </div>
              </div>
            )}
          </div>
        </div>

        {/* Quick Analysis Panel */}
        <div className="bg-card border border-border rounded-lg min-h-[500px] flex flex-col">
          <div className="p-4 border-b border-border">
            <h3 className="text-sm font-bold text-gold">QUICK_ANALYSIS</h3>
            <p className="text-xs text-muted-foreground font-mono">RAPID.BIAS.DETECTION.TOOLS</p>
          </div>
          <div className="flex-1 p-4">
            <div className="space-y-4">
              <button className="w-full p-3 bg-gold text-gold-foreground hover:bg-gold/90 rounded font-mono text-sm transition-colors">
                <svg className="inline mr-2 h-4 w-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 4v16m8-8H4" />
                </svg>
                UPLOAD_MODEL_FOR_ANALYSIS
              </button>
              <button className="w-full p-3 bg-transparent border border-border hover:bg-accent rounded font-mono text-sm transition-colors">
                <svg className="inline mr-2 h-4 w-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M7 16a4 4 0 01-.88-7.903A5 5 0 1115.9 6L16 6a5 5 0 011 9.9M15 13l-3-3m0 0l-3 3m3-3v12" />
                </svg>
                RUN_BATCH_ANALYSIS
              </button>
              <button className="w-full p-3 bg-transparent border border-border hover:bg-accent rounded font-mono text-sm transition-colors">
                <svg className="inline mr-2 h-4 w-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 17v-2m3 2v-4m3 4v-6m2 10H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z" />
                </svg>
                GENERATE_BIAS_REPORT
              </button>
            </div>
          </div>
        </div>
      </div>

      {/* Protected Attributes Analysis */}
      <div className="grid gap-4 md:gap-6 grid-cols-1 md:grid-cols-3">
        <div className="bg-card border border-border rounded-lg min-h-[400px] flex flex-col">
          <div className="p-4 border-b border-border">
            <h3 className="text-sm font-bold text-gold">PROTECTED_ATTRIBUTES</h3>
            <p className="text-xs text-muted-foreground font-mono">DEMOGRAPHIC.BIAS.MONITORING</p>
          </div>
          <div className="flex-1 p-4">
            <div className="h-full w-full flex items-center justify-center">
              <div className="text-center">
                <div className="w-16 h-16 bg-muted rounded-lg flex items-center justify-center mx-auto mb-4">
                  <svg className="w-8 h-8 text-muted-foreground" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 4.354a4 4 0 110 5.292M15 21H3v-1a6 6 0 0112 0v1zm0 0h6v-1a6 6 0 00-9-5.197m13.5-9a2.5 2.5 0 11-5 0 2.5 2.5 0 015 0z" />
                  </svg>
                </div>
                <h4 className="text-sm font-bold mb-2">NO_ATTRIBUTES_DETECTED</h4>
                <p className="text-xs text-muted-foreground font-mono">ANALYZE_MODELS_TO_DETECT_BIAS</p>
              </div>
            </div>
          </div>
        </div>
        <div className="bg-card border border-border rounded-lg min-h-[400px] flex flex-col">
          <div className="p-4 border-b border-border">
            <h3 className="text-sm font-bold text-gold">FAIRNESS_METRICS</h3>
            <p className="text-xs text-muted-foreground font-mono">EQUALITY.OF.OUTCOME.MEASURES</p>
          </div>
          <div className="flex-1 p-4">
            <div className="h-full w-full flex items-center justify-center">
              <div className="text-center">
                <div className="w-16 h-16 bg-muted rounded-lg flex items-center justify-center mx-auto mb-4">
                  <svg className="w-8 h-8 text-muted-foreground" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 12l2 2 4-4m5.618-4.016A11.955 11.955 0 0112 2.944a11.955 11.955 0 01-8.618 3.04A12.02 12.02 0 003 9c0 5.591 3.824 10.29 9 11.622 5.176-1.332 9-6.03 9-11.622 0-1.042-.133-2.052-.382-3.016z" />
                  </svg>
                </div>
                <h4 className="text-sm font-bold mb-2">NO_FAIRNESS_DATA</h4>
                <p className="text-xs text-muted-foreground font-mono">RUN_ANALYSIS_TO_GET_METRICS</p>
              </div>
            </div>
          </div>
        </div>
        <div className="bg-card border border-border rounded-lg min-h-[400px] flex flex-col">
          <div className="p-4 border-b border-border">
            <h3 className="text-sm font-bold text-gold">BIAS_RECOMMENDATIONS</h3>
            <p className="text-xs text-muted-foreground font-mono">MITIGATION.STRATEGIES.AND.ACTIONS</p>
          </div>
          <div className="flex-1 p-4">
            <div className="h-full w-full flex items-center justify-center">
              <div className="text-center">
                <div className="w-16 h-16 bg-muted rounded-lg flex items-center justify-center mx-auto mb-4">
                  <svg className="w-8 h-8 text-muted-foreground" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9.663 17h4.673M12 3v1m6.364 1.636l-.707.707M21 12h-1M4 12H3m3.343-5.657l-.707-.707m2.828 9.9a5 5 0 117.072 0l-.548.547A3.374 3.374 0 0014 18.469V19a2 2 0 11-4 0v-.531c0-.895-.356-1.754-.988-2.386l-.548-.547z" />
                  </svg>
                </div>
                <h4 className="text-sm font-bold mb-2">NO_RECOMMENDATIONS</h4>
                <p className="text-xs text-muted-foreground font-mono">ANALYZE_MODELS_FOR_SUGGESTIONS</p>
              </div>
            </div>
          </div>
        </div>
      </div>

      {/* Recent Bias Analysis Table */}
      <div className="bg-card border border-border rounded-lg overflow-hidden">
        <div className="p-4 border-b border-border">
          <div className="flex flex-col space-y-1.5">
            <h3 className="text-sm font-bold text-gold">RECENT_BIAS_ANALYSIS</h3>
            <p className="text-xs text-muted-foreground font-mono">LATEST.BIAS.DETECTION.RESULTS</p>
          </div>
        </div>
        <div className="p-4">
          <div className="rounded-md border border-border">
            <table className="w-full">
              <thead>
                <tr className="border-b border-border">
                  <th className="text-left p-3 text-xs font-mono">MODEL_NAME</th>
                  <th className="text-left p-3 text-xs font-mono">BIAS_SCORE</th>
                  <th className="text-left p-3 text-xs font-mono">FAIRNESS_SCORE</th>
                  <th className="text-left p-3 text-xs font-mono">STATUS</th>
                  <th className="text-left p-3 text-xs font-mono">ANALYSIS_DATE</th>
                  <th className="text-right p-3 text-xs font-mono">ACTIONS</th>
                </tr>
              </thead>
              <tbody>
                <tr className="border-b border-border">
                  <td className="p-3 text-xs font-mono text-muted-foreground" colSpan={6}>
                    <div className="text-center py-8">
                      <div className="w-16 h-16 bg-muted rounded-lg flex items-center justify-center mx-auto mb-4">
                        <svg className="w-8 h-8 text-muted-foreground" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 12l2 2 4-4m5.618-4.016A11.955 11.955 0 0112 2.944a11.955 11.955 0 01-8.618 3.04A12.02 12.02 0 003 9c0 5.591 3.824 10.29 9 11.622 5.176-1.332 9-6.03 9-11.622 0-1.042-.133-2.052-.382-3.016z" />
                        </svg>
                      </div>
                      <h4 className="text-sm font-bold mb-2">NO_BIAS_ANALYSIS_PERFORMED</h4>
                      <p className="text-xs text-muted-foreground font-mono">
                        UPLOAD_MODELS_TO_START_BIAS_DETECTION
                      </p>
                    </div>
                  </td>
                </tr>
              </tbody>
            </table>
          </div>
        </div>
      </div>
    </div>
  )
}
