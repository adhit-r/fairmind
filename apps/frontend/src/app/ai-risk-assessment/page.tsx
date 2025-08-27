'use client'

import React, { useState, useEffect } from 'react'

interface AIModel {
  id: string
  creator: string
  modelName: string
  accuracy: number
  fairness: number
  bias: number
  toxicity: number
  summary: number
  riskLevel: 'low' | 'medium' | 'high'
  deploymentStatus: 'sanctioned' | 'blocked' | 'guardrails'
}

interface RiskMetrics {
  overallAccuracy: number
  translation: number
  medicalReasoning: number
  legalReasoning: number
  mathematics: number
  closeBookQA: number
  openBookQA: number
  multipleChoiceQA: number
}

export default function AIRiskAssessmentPage() {
  const [models, setModels] = useState<AIModel[]>([])
  const [riskMetrics, setRiskMetrics] = useState<RiskMetrics | null>(null)
  const [loading, setLoading] = useState(true)
  const [selectedModel, setSelectedModel] = useState<string>('all')

  useEffect(() => {
    const loadData = async () => {
      setLoading(true)
      
      // Mock AI model data based on the reference image
      const mockModels: AIModel[] = [
        {
          id: '1',
          creator: 'Anthropic',
          modelName: 'Anthropic Claude',
          accuracy: 81.50,
          fairness: 83.00,
          bias: 58.30,
          toxicity: 63.30,
          summary: 53.10,
          riskLevel: 'medium',
          deploymentStatus: 'guardrails'
        },
        {
          id: '2',
          creator: 'OpenAI',
          modelName: 'GPT 3.5 Mar 1st',
          accuracy: 78.20,
          fairness: 67.80,
          bias: 44.00,
          toxicity: 57.00,
          summary: 50.00,
          riskLevel: 'medium',
          deploymentStatus: 'sanctioned'
        },
        {
          id: '3',
          creator: 'Meta',
          modelName: 'OPT (175B)',
          accuracy: 65.60,
          fairness: 68.00,
          bias: 58.00,
          toxicity: 43.80,
          summary: 59.50,
          riskLevel: 'high',
          deploymentStatus: 'blocked'
        },
        {
          id: '4',
          creator: 'Google',
          modelName: 'T5 (11B)',
          accuracy: 16.20,
          fairness: 18.10,
          bias: 46.70,
          toxicity: 57.20,
          summary: 11.90,
          riskLevel: 'high',
          deploymentStatus: 'blocked'
        },
        {
          id: '5',
          creator: 'Google',
          modelName: 'UL2 (20B)',
          accuracy: 20.50,
          fairness: 23.40,
          bias: 54.60,
          toxicity: 28.80,
          summary: 11.90,
          riskLevel: 'high',
          deploymentStatus: 'blocked'
        }
      ]

      // Mock risk metrics based on the reference image
      const mockRiskMetrics: RiskMetrics = {
        overallAccuracy: 56.7,
        translation: 18.7,
        medicalReasoning: 62.2,
        legalReasoning: 52.8,
        mathematics: 50.3,
        closeBookQA: 33.5,
        openBookQA: 67.8,
        multipleChoiceQA: 61.8
      }

      setModels(mockModels)
      setRiskMetrics(mockRiskMetrics)
      setLoading(false)
    }

    loadData()
  }, [])

  const getRiskLevelColor = (level: string) => {
    switch (level) {
      case 'low': return 'text-green-500 bg-green-500/10'
      case 'medium': return 'text-yellow-500 bg-yellow-500/10'
      case 'high': return 'text-red-500 bg-red-500/10'
      default: return 'text-gray-500 bg-gray-500/10'
    }
  }

  const getDeploymentStatusColor = (status: string) => {
    switch (status) {
      case 'sanctioned': return 'text-green-500 bg-green-500/10'
      case 'guardrails': return 'text-yellow-500 bg-yellow-500/10'
      case 'blocked': return 'text-red-500 bg-red-500/10'
      default: return 'text-gray-500 bg-gray-500/10'
    }
  }

  const getDeploymentStatusText = (status: string) => {
    switch (status) {
      case 'sanctioned': return 'SANCTIONED'
      case 'guardrails': return 'GUARDRAILS'
      case 'blocked': return 'BLOCKED'
      default: return 'UNKNOWN'
    }
  }

  const filteredModels = selectedModel === 'all' 
    ? models 
    : models.filter(model => model.riskLevel === selectedModel)

  if (loading) {
    return (
      <div className="space-y-6 p-4 md:p-6 max-w-[2000px] mx-auto">
        <div className="space-y-2">
          <h1 className="text-2xl md:text-3xl font-bold tracking-tight text-gold">
            AI_RISK_ASSESSMENT_DASHBOARD
          </h1>
          <p className="text-xs md:text-sm text-muted-foreground font-mono">
            COMPREHENSIVE.AI.RISK.ASSESSMENT.AND.MITIGATION
          </p>
        </div>
        <div className="flex items-center justify-center h-64">
          <div className="text-center">
            <div className="w-8 h-8 border-2 border-gold border-t-transparent rounded-full animate-spin mx-auto mb-4"></div>
            <p className="text-sm text-muted-foreground font-mono">LOADING_RISK_ASSESSMENT...</p>
          </div>
        </div>
      </div>
    )
  }

  return (
    <div className="space-y-6 p-4 md:p-6 max-w-[2000px] mx-auto">
      {/* Header */}
      <div className="space-y-2">
        <h1 className="text-2xl md:text-3xl font-bold tracking-tight text-gold">
          AI_RISK_ASSESSMENT_DASHBOARD
        </h1>
        <p className="text-xs md:text-sm text-muted-foreground font-mono">
          COMPREHENSIVE.AI.RISK.ASSESSMENT.AND.MITIGATION
        </p>
      </div>

      {/* Overview Cards */}
      <div className="grid gap-4 sm:grid-cols-2 lg:grid-cols-4">
        <div className="bg-card border border-border rounded-lg p-4">
          <div className="flex items-center justify-between">
            <div>
              <p className="text-xs text-muted-foreground font-mono">TOTAL_MODELS</p>
              <p className="text-lg font-bold text-foreground">{models.length}</p>
            </div>
            <div className="flex items-center gap-2">
              <svg className="h-4 w-4 text-gold" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 19v-6a2 2 0 00-2-2H5a2 2 0 00-2 2v6a2 2 0 002 2h2a2 2 0 002-2zm0 0V9a2 2 0 012-2h2a2 2 0 012 2v10m-6 0a2 2 0 002 2h2a2 2 0 002-2m0 0V5a2 2 0 012-2h2a2 2 0 012 2v14a2 2 0 01-2 2h-2a2 2 0 01-2-2z" />
              </svg>
            </div>
          </div>
        </div>

        <div className="bg-card border border-border rounded-lg p-4">
          <div className="flex items-center justify-between">
            <div>
              <p className="text-xs text-muted-foreground font-mono">HIGH_RISK_MODELS</p>
              <p className="text-lg font-bold text-red-500">
                {models.filter(m => m.riskLevel === 'high').length}
              </p>
            </div>
            <div className="flex items-center gap-2">
              <svg className="h-4 w-4 text-red-500" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 9v2m0 4h.01m-6.938 4h13.856c1.54 0 2.502-1.667 1.732-2.5L13.732 4c-.77-.833-1.964-.833-2.732 0L3.732 16.5c-.77.833.192 2.5 1.732 2.5z" />
              </svg>
            </div>
          </div>
        </div>

        <div className="bg-card border border-border rounded-lg p-4">
          <div className="flex items-center justify-between">
            <div>
              <p className="text-xs text-muted-foreground font-mono">BLOCKED_MODELS</p>
              <p className="text-lg font-bold text-red-500">
                {models.filter(m => m.deploymentStatus === 'blocked').length}
              </p>
            </div>
            <div className="flex items-center gap-2">
              <svg className="h-4 w-4 text-red-500" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M18.364 18.364A9 9 0 005.636 5.636m12.728 12.728L5.636 5.636m12.728 12.728L18.364 5.636M5.636 18.364l12.728-12.728" />
              </svg>
            </div>
          </div>
        </div>

        <div className="bg-card border border-border rounded-lg p-4">
          <div className="flex items-center justify-between">
            <div>
              <p className="text-xs text-muted-foreground font-mono">AVG_ACCURACY</p>
              <p className="text-lg font-bold text-foreground">
                {(models.reduce((sum, m) => sum + m.accuracy, 0) / models.length).toFixed(1)}%
              </p>
            </div>
            <div className="flex items-center gap-2">
              <svg className="h-4 w-4 text-gold" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M16 8v8m-4-5v5m-4-2v2m-2 4h12a2 2 0 002-2V6a2 2 0 00-2-2H6a2 2 0 00-2 2v12a2 2 0 002 2z" />
              </svg>
            </div>
          </div>
        </div>
      </div>

      {/* AI Model Performance Table */}
      <div className="space-y-4">
        <div className="flex items-center justify-between">
          <h2 className="text-xl font-bold tracking-tight text-foreground">
            AI_MODEL_PERFORMANCE_COMPARISON
          </h2>
          <div className="flex gap-2">
            {['all', 'low', 'medium', 'high'].map(level => (
              <button
                key={level}
                onClick={() => setSelectedModel(level)}
                className={`px-3 py-1 rounded-md text-xs font-mono ${
                  selectedModel === level
                    ? 'bg-gold text-gold-foreground'
                    : 'bg-accent text-accent-foreground hover:bg-accent/80'
                }`}
              >
                {level === 'all' ? 'ALL' : level.toUpperCase()}
              </button>
            ))}
          </div>
        </div>

        <div className="bg-card border border-border rounded-lg overflow-hidden">
          <div className="overflow-x-auto">
            <table className="w-full">
              <thead className="bg-accent/50">
                <tr>
                  <th className="px-4 py-3 text-left text-xs font-mono text-muted-foreground">MODEL_CREATOR</th>
                  <th className="px-4 py-3 text-left text-xs font-mono text-muted-foreground">MODEL_NAME</th>
                  <th className="px-4 py-3 text-left text-xs font-mono text-muted-foreground">ACCURACY</th>
                  <th className="px-4 py-3 text-left text-xs font-mono text-muted-foreground">FAIRNESS</th>
                  <th className="px-4 py-3 text-left text-xs font-mono text-muted-foreground">BIAS</th>
                  <th className="px-4 py-3 text-left text-xs font-mono text-muted-foreground">TOXICITY</th>
                  <th className="px-4 py-3 text-left text-xs font-mono text-muted-foreground">SUMMARY</th>
                  <th className="px-4 py-3 text-left text-xs font-mono text-muted-foreground">RISK_LEVEL</th>
                  <th className="px-4 py-3 text-left text-xs font-mono text-muted-foreground">DEPLOYMENT</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-border">
                {filteredModels.map((model) => (
                  <tr key={model.id} className="hover:bg-accent/20">
                    <td className="px-4 py-3 text-sm font-mono">{model.creator}</td>
                    <td className="px-4 py-3 text-sm font-mono font-semibold">{model.modelName}</td>
                    <td className="px-4 py-3 text-sm font-mono">{model.accuracy}%</td>
                    <td className="px-4 py-3 text-sm font-mono">{model.fairness}%</td>
                    <td className="px-4 py-3 text-sm font-mono">{model.bias}%</td>
                    <td className="px-4 py-3 text-sm font-mono">{model.toxicity}%</td>
                    <td className="px-4 py-3 text-sm font-mono font-semibold">{model.summary}%</td>
                    <td className="px-4 py-3">
                      <span className={`px-2 py-1 rounded-full text-xs font-mono ${getRiskLevelColor(model.riskLevel)}`}>
                        {model.riskLevel.toUpperCase()}
                      </span>
                    </td>
                    <td className="px-4 py-3">
                      <span className={`px-2 py-1 rounded-full text-xs font-mono ${getDeploymentStatusColor(model.deploymentStatus)}`}>
                        {getDeploymentStatusText(model.deploymentStatus)}
                      </span>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </div>
      </div>

      {/* Risk Assessment Radar Chart */}
      {riskMetrics && (
        <div className="space-y-4">
          <h2 className="text-xl font-bold tracking-tight text-foreground">
            RISK_ASSESSMENT_RADAR_CHART
          </h2>
          
          <div className="bg-card border border-border rounded-lg p-6">
            <div className="grid grid-cols-2 lg:grid-cols-4 gap-6">
              <div className="space-y-2">
                <p className="text-xs text-muted-foreground font-mono">OVERALL_ACCURACY</p>
                <p className="text-2xl font-bold text-foreground">{riskMetrics.overallAccuracy}</p>
                <div className="w-full bg-accent rounded-full h-2">
                  <div 
                    className="bg-gold h-2 rounded-full" 
                    style={{ width: `${riskMetrics.overallAccuracy}%` }}
                  ></div>
                </div>
              </div>

              <div className="space-y-2">
                <p className="text-xs text-muted-foreground font-mono">TRANSLATION</p>
                <p className="text-2xl font-bold text-foreground">{riskMetrics.translation}</p>
                <div className="w-full bg-accent rounded-full h-2">
                  <div 
                    className="bg-gold h-2 rounded-full" 
                    style={{ width: `${riskMetrics.translation}%` }}
                  ></div>
                </div>
              </div>

              <div className="space-y-2">
                <p className="text-xs text-muted-foreground font-mono">MEDICAL_REASONING</p>
                <p className="text-2xl font-bold text-foreground">{riskMetrics.medicalReasoning}</p>
                <div className="w-full bg-accent rounded-full h-2">
                  <div 
                    className="bg-gold h-2 rounded-full" 
                    style={{ width: `${riskMetrics.medicalReasoning}%` }}
                  ></div>
                </div>
              </div>

              <div className="space-y-2">
                <p className="text-xs text-muted-foreground font-mono">LEGAL_REASONING</p>
                <p className="text-2xl font-bold text-foreground">{riskMetrics.legalReasoning}</p>
                <div className="w-full bg-accent rounded-full h-2">
                  <div 
                    className="bg-gold h-2 rounded-full" 
                    style={{ width: `${riskMetrics.legalReasoning}%` }}
                  ></div>
                </div>
              </div>

              <div className="space-y-2">
                <p className="text-xs text-muted-foreground font-mono">MATHEMATICS</p>
                <p className="text-2xl font-bold text-foreground">{riskMetrics.mathematics}</p>
                <div className="w-full bg-accent rounded-full h-2">
                  <div 
                    className="bg-gold h-2 rounded-full" 
                    style={{ width: `${riskMetrics.mathematics}%` }}
                  ></div>
                </div>
              </div>

              <div className="space-y-2">
                <p className="text-xs text-muted-foreground font-mono">CLOSE_BOOK_QA</p>
                <p className="text-2xl font-bold text-foreground">{riskMetrics.closeBookQA}</p>
                <div className="w-full bg-accent rounded-full h-2">
                  <div 
                    className="bg-gold h-2 rounded-full" 
                    style={{ width: `${riskMetrics.closeBookQA}%` }}
                  ></div>
                </div>
              </div>

              <div className="space-y-2">
                <p className="text-xs text-muted-foreground font-mono">OPEN_BOOK_QA</p>
                <p className="text-2xl font-bold text-foreground">{riskMetrics.openBookQA}</p>
                <div className="w-full bg-accent rounded-full h-2">
                  <div 
                    className="bg-gold h-2 rounded-full" 
                    style={{ width: `${riskMetrics.openBookQA}%` }}
                  ></div>
                </div>
              </div>

              <div className="space-y-2">
                <p className="text-xs text-muted-foreground font-mono">MULTIPLE_CHOICE_QA</p>
                <p className="text-2xl font-bold text-foreground">{riskMetrics.multipleChoiceQA}</p>
                <div className="w-full bg-accent rounded-full h-2">
                  <div 
                    className="bg-gold h-2 rounded-full" 
                    style={{ width: `${riskMetrics.multipleChoiceQA}%` }}
                  ></div>
                </div>
              </div>
            </div>
          </div>
        </div>
      )}

      {/* Risk Mitigation Information */}
      <div className="space-y-4">
        <h2 className="text-xl font-bold tracking-tight text-foreground">
          RISK_MITIGATION_GUIDELINES
        </h2>
        
        <div className="bg-card border border-border rounded-lg p-6">
          <div className="space-y-6">
            <div>
              <h3 className="font-semibold text-foreground mb-2">PRE_DEVELOPMENT_RISK_ASSESSMENT</h3>
              <p className="text-sm text-muted-foreground">
                Assess risks at pre-development and development stages. Implement risk mitigation steps 
                leveraging model cards that offer predefined risk evaluations for AI models, including 
                model description, intended use, limitations, and ethical considerations.
              </p>
            </div>
            
            <div>
              <h3 className="font-semibold text-foreground mb-2">RISK_RATINGS_AND_CLASSIFICATIONS</h3>
              <p className="text-sm text-muted-foreground">
                Risk ratings provide comprehensive details covering toxicity, maliciousness, bias, 
                copyright considerations, hallucination risks, and model efficiency in terms of energy 
                consumption and inference runtime.
              </p>
            </div>

            <div>
              <h3 className="font-semibold text-foreground mb-2">DEPLOYMENT_DECISIONS</h3>
              <div className="grid grid-cols-1 md:grid-cols-3 gap-4 mt-3">
                <div className="p-3 border border-green-500/20 rounded-lg bg-green-500/5">
                  <p className="text-xs font-mono text-green-500 mb-1">SANCTIONED</p>
                  <p className="text-xs text-muted-foreground">Models approved for deployment with standard monitoring</p>
                </div>
                <div className="p-3 border border-yellow-500/20 rounded-lg bg-yellow-500/5">
                  <p className="text-xs font-mono text-yellow-500 mb-1">GUARDRAILS</p>
                  <p className="text-xs text-muted-foreground">Models requiring additional safety measures before deployment</p>
                </div>
                <div className="p-3 border border-red-500/20 rounded-lg bg-red-500/5">
                  <p className="text-xs font-mono text-red-500 mb-1">BLOCKED</p>
                  <p className="text-xs text-muted-foreground">Models blocked from deployment due to high risk factors</p>
                </div>
              </div>
            </div>
          </div>
        </div>
      </div>
    </div>
  )
}
