'use client'

import React, { useState, useEffect } from 'react'
import { api, type Model, type Dataset, type GovernanceMetrics, type RecentActivity, type SecurityAnalysisResult } from '../config/api'

export default function Home() {
  const [models, setModels] = useState<Model[]>([])
  const [datasets, setDatasets] = useState<Dataset[]>([])
  const [governanceMetrics, setGovernanceMetrics] = useState<GovernanceMetrics | null>(null)
  const [recentActivity, setRecentActivity] = useState<RecentActivity[]>([])
  const [securityResults, setSecurityResults] = useState<SecurityAnalysisResult[]>([])
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
        
        // Fetch comprehensive data in parallel
        const [
          modelsResponse, 
          datasetsResponse, 
          metricsResponse, 
          activityResponse,
          securityResponse
        ] = await Promise.all([
          api.getModels(),
          api.getBiasDatasets(),
          api.getGovernanceMetrics(),
          api.getRecentActivity(),
          api.getSecurityTestHistory()
        ])

        if (modelsResponse.success && modelsResponse.data) {
          setModels(modelsResponse.data)
        }

        if (datasetsResponse.success && datasetsResponse.data) {
          setDatasets(datasetsResponse.data)
        }

        if (metricsResponse.success && metricsResponse.data) {
          setGovernanceMetrics(metricsResponse.data)
        }

        if (activityResponse.success && activityResponse.data) {
          setRecentActivity(activityResponse.data)
        }

        if (securityResponse.success && securityResponse.data) {
          setSecurityResults(securityResponse.data)
        }
      } catch (err) {
        console.error('Error fetching dashboard data:', err)
        setError(err instanceof Error ? err.message : 'Unknown error occurred')
      } finally {
        setLoading(false)
      }
    }

    fetchData()
  }, [mounted])

  // Calculate metrics from real data
  const activeModels = models.filter(model => model.status === 'active').length
  const totalModels = models.length
  const totalDatasets = datasets.length
  const criticalRisks = securityResults.filter(result => result.riskLevel === 'critical').length
  const highRisks = securityResults.filter(result => result.riskLevel === 'high').length
  const totalRisks = criticalRisks + highRisks

  // Use governance metrics if available, otherwise calculate from data
  const metrics = governanceMetrics || {
    totalModels,
    activeModels,
    criticalRisks: totalRisks,
    llmSafetyScore: 85, // Default score
    nistCompliance: 78 // Default compliance score
  }

  // Show loading state until mounted to prevent hydration mismatch
  if (!mounted) {
    return (
      <div className="space-y-6 p-4 md:p-6 max-w-[2000px] mx-auto">
        <div className="space-y-2">
          <h1 className="text-2xl md:text-3xl font-bold tracking-tight text-gold">
            AI_GOVERNANCE_DASHBOARD
          </h1>
          <p className="text-xs md:text-sm text-muted-foreground font-mono">
            COMPREHENSIVE.AI.RISK.MANAGEMENT.AND.COMPLIANCE.MONITORING.PLATFORM
          </p>
        </div>
        <div className="flex items-center justify-center h-64">
          <div className="text-center">
            <div className="w-8 h-8 border-2 border-gold border-t-transparent rounded-full animate-spin mx-auto mb-4"></div>
            <p className="text-sm text-muted-foreground font-mono">INITIALIZING_DASHBOARD...</p>
          </div>
        </div>
      </div>
    )
  }

  if (loading) {
    return (
      <div className="space-y-6 p-4 md:p-6 max-w-[2000px] mx-auto">
        <div className="space-y-2">
          <h1 className="text-2xl md:text-3xl font-bold tracking-tight text-gold">
            AI_GOVERNANCE_DASHBOARD
          </h1>
          <p className="text-xs md:text-sm text-muted-foreground font-mono">
            COMPREHENSIVE.AI.RISK.MANAGEMENT.AND.COMPLIANCE.MONITORING.PLATFORM
          </p>
        </div>
        <div className="flex items-center justify-center h-64">
          <div className="text-center">
            <div className="w-8 h-8 border-2 border-gold border-t-transparent rounded-full animate-spin mx-auto mb-4"></div>
            <p className="text-sm text-muted-foreground font-mono">LOADING_DASHBOARD_DATA...</p>
          </div>
        </div>
      </div>
    )
  }

  if (error) {
    return (
      <div className="space-y-6 p-4 md:p-6 max-w-[2000px] mx-auto">
        <div className="space-y-2">
          <h1 className="text-2xl md:text-3xl font-bold tracking-tight text-gold">
            AI_GOVERNANCE_DASHBOARD
          </h1>
          <p className="text-xs md:text-sm text-muted-foreground font-mono">
            COMPREHENSIVE.AI.RISK.MANAGEMENT.AND.COMPLIANCE.MONITORING.PLATFORM
          </p>
        </div>
        <div className="bg-destructive/10 border border-destructive rounded-lg p-4">
          <p className="text-sm text-destructive font-mono">ERROR_LOADING_DATA: {error}</p>
        </div>
      </div>
    )
  }

  return (
    <div className="space-y-6 p-4 md:p-6 max-w-[2000px] mx-auto">
      {/* Header Section */}
      <div className="space-y-2">
        <h1 className="text-2xl md:text-3xl font-bold tracking-tight text-gold">
          AI_GOVERNANCE_DASHBOARD
        </h1>
        <p className="text-xs md:text-sm text-muted-foreground font-mono">
          COMPREHENSIVE.AI.RISK.MANAGEMENT.AND.COMPLIANCE.MONITORING.PLATFORM
        </p>
      </div>

      {/* Governance Metrics */}
      <div className="grid gap-4 sm:grid-cols-2 lg:grid-cols-4">
        <div className="bg-card border border-border rounded-lg p-4">
          <div className="flex items-center justify-between">
            <div>
              <p className="text-xs text-muted-foreground font-mono">NIST_COMPLIANCE</p>
              <p className="text-lg font-bold text-foreground">{metrics.nistCompliance}%</p>
            </div>
            <div className="flex items-center gap-2">
              <svg className="h-4 w-4 text-gold" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 12l2 2 4-4m5.618-4.016A11.955 11.955 0 0112 2.944a11.955 11.955 0 01-8.618 3.04A12.02 12.02 0 003 9c0 5.591 3.824 10.29 9 11.622 5.176-1.332 9-6.03 9-11.622 0-1.042-.133-2.052-.382-3.016z" />
              </svg>
              <div className="flex items-center gap-1">
                <span className="text-xs text-muted-foreground">{metrics.nistCompliance > 70 ? 'COMPLIANT' : 'ATTENTION_REQUIRED'}</span>
              </div>
            </div>
          </div>
        </div>
        <div className="bg-card border border-border rounded-lg p-4">
          <div className="flex items-center justify-between">
            <div>
              <p className="text-xs text-muted-foreground font-mono">ACTIVE_MODELS</p>
              <p className="text-lg font-bold text-foreground">{metrics.activeModels}</p>
            </div>
            <div className="flex items-center gap-2">
              <svg className="h-4 w-4 text-gold" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9.663 17h4.673M12 3v1m6.364 1.636l-.707.707M21 12h-1M4 12H3m3.343-5.657l-.707-.707m2.828 9.9a5 5 0 117.072 0l-.548.547A3.374 3.374 0 0014 18.469V19a2 2 0 11-4 0v-.531c0-.895-.356-1.754-.988-2.386l-.548-.547z" />
              </svg>
              <div className="flex items-center gap-1">
                <span className="text-xs text-muted-foreground">{metrics.activeModels > 0 ? 'RUNNING' : 'UPLOAD_FIRST'}</span>
              </div>
            </div>
          </div>
        </div>
        <div className="bg-card border border-border rounded-lg p-4">
          <div className="flex items-center justify-between">
            <div>
              <p className="text-xs text-muted-foreground font-mono">CRITICAL_RISKS</p>
              <p className="text-lg font-bold text-foreground">{metrics.criticalRisks}</p>
            </div>
            <div className="flex items-center gap-2">
              <svg className="h-4 w-4 text-gold" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 9v2m0 4h.01m-6.938 4h13.856c1.54 0 2.502-1.667 1.732-2.5L13.732 4c-.77-.833-1.964-.833-2.732 0L3.732 16.5c-.77.833.192 2.5 1.732 2.5z" />
              </svg>
              <div className="flex items-center gap-1">
                <span className="text-xs text-muted-foreground">{metrics.criticalRisks === 0 ? 'CLEAN' : 'ATTENTION_REQUIRED'}</span>
              </div>
            </div>
          </div>
        </div>
        <div className="bg-card border border-border rounded-lg p-4">
          <div className="flex items-center justify-between">
            <div>
              <p className="text-xs text-muted-foreground font-mono">LLM_SAFETY_SCORE</p>
              <p className="text-lg font-bold text-foreground">{metrics.llmSafetyScore}%</p>
            </div>
            <div className="flex items-center gap-2">
              <svg className="h-4 w-4 text-gold" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9.663 17h4.673M12 3v1m6.364 1.636l-.707.707M21 12h-1M4 12H3m3.343-5.657l-.707-.707m2.828 9.9a5 5 0 117.072 0l-.548.547A3.374 3.374 0 0014 18.469V19a2 2 0 11-4 0v-.531c0-.895-.356-1.754-.988-2.386l-.548-.547z" />
              </svg>
              <div className="flex items-center gap-1">
                <span className="text-xs text-muted-foreground">{metrics.llmSafetyScore > 80 ? 'SAFE' : 'ATTENTION_REQUIRED'}</span>
              </div>
            </div>
          </div>
        </div>
      </div>

      {/* Action Section */}
      <div className="flex flex-col sm:flex-row gap-4 items-start sm:items-center justify-between">
        <div className="flex flex-wrap gap-2">
          <a href="/model-upload" className="w-full sm:w-auto">
            <button className="bg-gold text-gold-foreground hover:bg-gold/90 w-full sm:w-auto px-4 py-2 rounded font-mono text-sm transition-colors font-bold">
              <svg className="inline mr-2 h-4 w-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 4v16m8-8H4" />
              </svg>
              <span className="whitespace-nowrap">NEW_SIMULATION</span>
            </button>
          </a>
          <a href="/bias-detection" className="w-full sm:w-auto">
            <button className="bg-transparent border border-border hover:bg-accent hover:text-accent-foreground w-full sm:w-auto px-4 py-2 rounded font-mono text-sm transition-colors text-foreground">
              <svg className="inline mr-2 h-4 w-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 12l2 2 4-4m5.618-4.016A11.955 11.955 0 0112 2.944a11.955 11.955 0 01-8.618 3.04A12.02 12.02 0 003 9c0 5.591 3.824 10.29 9 11.622 5.176-1.332 9-6.03 9-11.622 0-1.042-.133-2.052-.382-3.016z" />
              </svg>
              <span className="whitespace-nowrap">GOVERNANCE_REVIEW</span>
            </button>
          </a>
        </div>
      </div>

      {/* Primary Charts Grid */}
      <div className="grid gap-4 md:gap-6 grid-cols-1 lg:grid-cols-3">
        <div className="bg-card border border-border rounded-lg lg:col-span-2 min-h-[500px] flex flex-col">
          <div className="p-4 border-b border-border">
            <h3 className="text-sm font-bold text-gold">AI_GOVERNANCE_METRICS</h3>
            <p className="text-xs text-muted-foreground font-mono">
              FAIRNESS.ROBUSTNESS.EXPLAINABILITY.COMPLIANCE.LLM_SAFETY
            </p>
          </div>
          <div className="flex-1 p-4">
            {totalModels > 0 ? (
              <div className="h-full w-full flex items-center justify-center">
                <div className="text-center">
                  <div className="w-24 h-24 bg-muted rounded-lg flex items-center justify-center mx-auto mb-4">
                    <svg className="w-12 h-12 text-gold" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 19v-6a2 2 0 00-2-2H5a2 2 0 00-2 2v6a2 2 0 002 2h2a2 2 0 002-2zm0 0V9a2 2 0 012-2h2a2 2 0 012 2v10m-6 0a2 2 0 002 2h2a2 2 0 002-2m0 0V5a2 2 0 012-2h2a2 2 0 012 2v14a2 2 0 01-2 2h-2a2 2 0 01-2-2z" />
                    </svg>
                  </div>
                  <h4 className="text-lg font-bold mb-2 text-foreground">GOVERNANCE_DATA_AVAILABLE</h4>
                  <p className="text-sm text-muted-foreground font-mono">
                    {totalModels} MODELS_REGISTERED • {totalDatasets} DATASETS_AVAILABLE
                  </p>
                </div>
              </div>
            ) : (
              <div className="h-full w-full flex items-center justify-center">
                <div className="text-center">
                  <div className="w-24 h-24 bg-muted rounded-lg flex items-center justify-center mx-auto mb-4">
                    <svg className="w-12 h-12 text-muted-foreground" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 19v-6a2 2 0 00-2-2H5a2 2 0 00-2 2v6a2 2 0 002 2h2a2 2 0 002-2zm0 0V9a2 2 0 012-2h2a2 2 0 012 2v10m-6 0a2 2 0 002 2h2a2 2 0 002-2m0 0V5a2 2 0 012-2h2a2 2 0 012 2v14a2 2 0 01-2 2h-2a2 2 0 01-2-2z" />
                    </svg>
                  </div>
                  <h4 className="text-lg font-bold mb-2 text-foreground">NO_DATA_AVAILABLE</h4>
                  <p className="text-sm text-muted-foreground font-mono">
                    UPLOAD_MODELS_TO_SEE_GOVERNANCE_METRICS
                  </p>
                </div>
              </div>
            )}
          </div>
        </div>
        <div className="bg-card border border-border rounded-lg min-h-[500px] flex flex-col">
          <div className="p-4 border-b border-border">
            <h3 className="text-sm font-bold text-gold">BIAS_DETECTION_RADAR</h3>
            <p className="text-xs text-muted-foreground font-mono">DEMOGRAPHIC.BIAS.ANALYSIS</p>
          </div>
          <div className="flex-1 p-4">
            <div className="h-full w-full flex items-center justify-center">
              <div className="text-center">
                <div className="w-20 h-20 bg-muted rounded-lg flex items-center justify-center mx-auto mb-4">
                  <svg className="w-10 h-10 text-muted-foreground" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 12l2 2 4-4m5.618-4.016A11.955 11.955 0 0112 2.944a11.955 11.955 0 01-8.618 3.04A12.02 12.02 0 003 9c0 5.591 3.824 10.29 9 11.622 5.176-1.332 9-6.03 9-11.622 0-1.042-.133-2.052-.382-3.016z" />
                  </svg>
                </div>
                <h4 className="text-sm font-bold mb-2 text-foreground">NO_BIAS_DATA</h4>
                <p className="text-xs text-muted-foreground font-mono">RUN_BIAS_DETECTION_FIRST</p>
              </div>
            </div>
          </div>
        </div>
      </div>

      {/* Secondary Charts Grid */}
      <div className="grid gap-4 md:gap-6 grid-cols-1 md:grid-cols-3">
        <div className="bg-card border border-border rounded-lg min-h-[400px] flex flex-col">
          <div className="p-4 border-b border-border">
            <h3 className="text-sm font-bold text-gold">MODEL_LIFECYCLE_TRACKING</h3>
            <p className="text-xs text-muted-foreground font-mono">DEVELOPMENT.TO.DEPLOYMENT.METRICS</p>
          </div>
          <div className="flex-1 p-4">
            <div className="h-full w-full flex items-center justify-center">
              <div className="text-center">
                <div className="w-16 h-16 bg-muted rounded-lg flex items-center justify-center mx-auto mb-4">
                  <svg className="w-8 h-8 text-muted-foreground" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M13 10V3L4 14h7v7l9-11h-7z" />
                  </svg>
                </div>
                <h4 className="text-sm font-bold mb-2 text-foreground">NO_LIFECYCLE_DATA</h4>
                <p className="text-xs text-muted-foreground font-mono">UPLOAD_MODELS_TO_TRACK</p>
              </div>
            </div>
          </div>
        </div>
        <div className="bg-card border border-border rounded-lg min-h-[400px] flex flex-col">
          <div className="p-4 border-b border-border">
            <h3 className="text-sm font-bold text-gold">MODEL_DRIFT_MONITORING</h3>
            <p className="text-xs text-muted-foreground font-mono">REAL-TIME.DRIFT.DETECTION</p>
          </div>
          <div className="flex-1 p-4">
            <div className="h-full w-full flex items-center justify-center">
              <div className="text-center">
                <div className="w-16 h-16 bg-muted rounded-lg flex items-center justify-center mx-auto mb-4">
                  <svg className="w-8 h-8 text-muted-foreground" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 19v-6a2 2 0 00-2-2H5a2 2 0 00-2 2v6a2 2 0 002 2h2a2 2 0 002-2zm0 0V9a2 2 0 012-2h2a2 2 0 012 2v10m-6 0a2 2 0 002 2h2a2 2 0 002-2m0 0V5a2 2 0 012-2h2a2 2 0 012 2v14a2 2 0 01-2 2h-2a2 2 0 01-2-2z" />
                  </svg>
                </div>
                <h4 className="text-sm font-bold mb-2 text-foreground">NO_DRIFT_DATA</h4>
                <p className="text-xs text-muted-foreground font-mono">DEPLOY_MODELS_TO_MONITOR</p>
              </div>
            </div>
          </div>
        </div>
        <div className="bg-card border border-border rounded-lg min-h-[400px] flex flex-col">
          <div className="p-4 border-b border-border">
            <h3 className="text-sm font-bold text-gold">COMPLIANCE_TIMELINE</h3>
            <p className="text-xs text-muted-foreground font-mono">REGULATORY.ADHERENCE.TRENDS</p>
          </div>
          <div className="flex-1 p-4">
            <div className="h-full w-full flex items-center justify-center">
              <div className="text-center">
                <div className="w-16 h-16 bg-muted rounded-lg flex items-center justify-center mx-auto mb-4">
                  <svg className="w-8 h-8 text-muted-foreground" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M8 7V3m8 4V3m-9 8h10M5 21h14a2 2 0 002-2V7a2 2 0 00-2-2H5a2 2 0 00-2 2v12a2 2 0 002 2z" />
                  </svg>
                </div>
                <h4 className="text-sm font-bold mb-2 text-foreground">NO_COMPLIANCE_DATA</h4>
                <p className="text-xs text-muted-foreground font-mono">RUN_COMPLIANCE_CHECKS</p>
              </div>
            </div>
          </div>
        </div>
      </div>

      {/* Models and Assessments Table */}
      <div className="bg-card border border-border rounded-lg overflow-hidden">
        <div className="p-4 border-b border-border">
          <div className="flex flex-col space-y-1.5">
            <h3 className="text-sm font-bold text-gold">MODEL_REGISTRY_&_ASSESSMENTS</h3>
            <p className="text-xs text-muted-foreground font-mono">COMPREHENSIVE.MODEL.GOVERNANCE.AND.RISK.TRACKING</p>
          </div>
          <div className="mt-2">
            <div className="relative w-full sm:w-80">
              <svg className="absolute left-3 top-1/2 transform -translate-y-1/2 text-muted-foreground h-4 w-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M21 21l-6-6m2-5a7 7 0 11-14 0 7 7 0 0114 0z" />
              </svg>
              <input
                placeholder="SEARCH_MODELS_AND_ASSESSMENTS..."
                className="pl-10 font-mono text-xs h-9 w-full bg-background border border-border rounded px-3 text-foreground placeholder:text-muted-foreground"
              />
            </div>
          </div>
        </div>
        <div className="p-4">
          <div className="rounded-md border border-border">
            <table className="w-full">
              <thead>
                <tr className="border-b border-border">
                  <th className="text-left p-3 text-xs font-mono text-foreground">MODEL_NAME</th>
                  <th className="text-left p-3 text-xs font-mono text-foreground">TYPE</th>
                  <th className="text-left p-3 text-xs font-mono text-foreground">LAST_ASSESSED</th>
                  <th className="text-left p-3 text-xs font-mono text-foreground">STATUS</th>
                  <th className="text-left p-3 text-xs font-mono text-foreground">FAIRNESS</th>
                  <th className="text-left p-3 text-xs font-mono text-foreground">ROBUSTNESS</th>
                  <th className="text-left p-3 text-xs font-mono text-foreground">EXPLAINABILITY</th>
                  <th className="text-right p-3 text-xs font-mono text-foreground">ACTIONS</th>
                </tr>
              </thead>
              <tbody>
                {models.length > 0 ? (
                  models.map((model) => (
                    <tr key={model.id} className="border-b border-border">
                      <td className="p-3 text-xs font-mono text-foreground">{model.name}</td>
                      <td className="p-3 text-xs font-mono text-foreground">{model.version}</td>
                      <td className="p-3 text-xs font-mono text-muted-foreground">--</td>
                      <td className="p-3 text-xs font-mono">
                        <span className={`px-2 py-1 rounded text-xs ${
                          model.status === 'active' ? 'bg-green-500/20 text-green-400' :
                          model.status === 'testing' ? 'bg-yellow-500/20 text-yellow-400' :
                          'bg-red-500/20 text-red-400'
                        }`}>
                          {model.status.toUpperCase()}
                        </span>
                      </td>
                      <td className="p-3 text-xs font-mono text-muted-foreground">--</td>
                      <td className="p-3 text-xs font-mono text-muted-foreground">--</td>
                      <td className="p-3 text-xs font-mono text-muted-foreground">--</td>
                      <td className="p-3 text-xs font-mono text-right">
                        <button className="text-gold hover:text-gold/80 font-bold">VIEW</button>
                      </td>
                    </tr>
                  ))
                ) : (
                  <tr className="border-b border-border">
                    <td className="p-3 text-xs font-mono text-muted-foreground" colSpan={8}>
                      <div className="text-center py-8">
                        <div className="w-16 h-16 bg-muted rounded-lg flex items-center justify-center mx-auto mb-4">
                          <svg className="w-8 h-8 text-muted-foreground" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 12h6m-6 4h6m2 5H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z" />
                          </svg>
                        </div>
                        <h4 className="text-sm font-bold mb-2 text-foreground">NO_MODELS_REGISTERED</h4>
                        <p className="text-xs text-muted-foreground font-mono">
                          UPLOAD_YOUR_FIRST_MODEL_TO_GET_STARTED
                        </p>
                      </div>
                    </td>
                  </tr>
                )}
              </tbody>
            </table>
          </div>
        </div>
      </div>
    </div>
  )
}
