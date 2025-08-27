'use client'

import React, { useState, useEffect } from 'react'
import { 
  Shield, 
  AlertTriangle, 
  CheckCircle, 
  Clock, 
  Activity, 
  Zap,
  Lock,
  Eye,
  FileText,
  BarChart3,
  TrendingUp,
  TrendingDown
} from 'lucide-react'
import { PageWrapper } from '@/components/core/PageWrapper'
import { Card } from '@/components/core/Card'
import { Button } from '@/components/core/Button'
import { api, type SecurityAnalysisResult, type SecurityTest } from '@/config/api'

interface SecurityTest {
  id: string
  model_name: string
  status: 'completed' | 'running' | 'failed' | 'pending'
  created_at: string
  security_score: number
  vulnerabilities: number
  recommendations: string[]
  test_type: 'owasp' | 'custom' | 'comprehensive'
}

export default function SecurityTestingPage() {
  const [securityAnalyses, setSecurityAnalyses] = useState<SecurityAnalysisResult[]>([])
  const [securityTests, setSecurityTests] = useState<SecurityTest[]>([])
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
        
        // Fetch security analysis history and available tests
        const [analysesResponse, testsResponse] = await Promise.all([
          api.getSecurityTestHistory(),
          api.getSecurityTests()
        ])

        if (analysesResponse.success && analysesResponse.data) {
          setSecurityAnalyses(analysesResponse.data)
        }

        if (testsResponse.success && testsResponse.data) {
          setSecurityTests(testsResponse.data)
        }
      } catch (err) {
        console.error('Error fetching security testing data:', err)
        setError(err instanceof Error ? err.message : 'Unknown error occurred')
      } finally {
        setLoading(false)
      }
    }

    fetchData()
  }, [mounted])

  // Calculate metrics from real data
  const totalTests = securityAnalyses.length
  const completedTests = securityAnalyses.filter(analysis => analysis.testSummary?.passedTests).length
  const totalVulnerabilities = securityAnalyses.reduce((sum, analysis) => 
    sum + (analysis.issueBreakdown?.critical || 0) + (analysis.issueBreakdown?.high || 0), 0)
  const averageSecurityScore = securityAnalyses.length > 0 
    ? securityAnalyses.reduce((sum, analysis) => sum + (analysis.securityScore || 0), 0) / securityAnalyses.length 
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
          SECURITY_TESTING
          </h1>
        <p className="text-xs md:text-sm text-muted-foreground font-mono">
          COMPREHENSIVE.AI.LLM.SECURITY.TESTING.WITH.OWASP.TOP.10.COVERAGE
        </p>
      </div>

      {/* Security Testing Metrics */}
      <div className="grid gap-4 sm:grid-cols-2 lg:grid-cols-4">
        <div className="bg-card border border-border rounded-lg p-4">
          <div className="flex items-center justify-between">
            <div>
              <p className="text-xs text-muted-foreground font-mono">TOTAL_TESTS</p>
              <p className="text-lg font-bold">{totalTests}</p>
            </div>
            <div className="flex items-center gap-2">
              <svg className="h-4 w-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 15v2m-6 4h12a2 2 0 002-2v-6a2 2 0 00-2-2H6a2 2 0 00-2 2v6a2 2 0 002 2zm10-10V7a4 4 0 00-8 0v4h8z" />
              </svg>
              <div className="flex items-center gap-1">
                <span className="text-xs text-muted-foreground">
                  {totalTests > 0 ? `${totalTests} TESTS` : 'NO_TESTS'}
                </span>
              </div>
            </div>
          </div>
        </div>
        <div className="bg-card border border-border rounded-lg p-4">
          <div className="flex items-center justify-between">
            <div>
              <p className="text-xs text-muted-foreground font-mono">COMPLETED_TESTS</p>
              <p className="text-lg font-bold">{completedTests}</p>
            </div>
            <div className="flex items-center gap-2">
              <svg className="h-4 w-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 12l2 2 4-4m6 2a9 9 0 11-18 0 9 9 0 0118 0z" />
              </svg>
              <div className="flex items-center gap-1">
                <span className="text-xs text-muted-foreground">
                  {completedTests > 0 ? `${completedTests} COMPLETED` : 'NO_COMPLETED'}
                </span>
              </div>
            </div>
          </div>
        </div>
        <div className="bg-card border border-border rounded-lg p-4">
          <div className="flex items-center justify-between">
            <div>
              <p className="text-xs text-muted-foreground font-mono">VULNERABILITIES</p>
              <p className="text-lg font-bold">{totalVulnerabilities}</p>
            </div>
            <div className="flex items-center gap-2">
              <svg className="h-4 w-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 9v2m0 4h.01m-6.938 4h13.856c1.54 0 2.502-1.667 1.732-2.5L13.732 4c-.77-.833-1.964-.833-2.732 0L3.732 16.5c-.77.833.192 2.5 1.732 2.5z" />
              </svg>
              <div className="flex items-center gap-1">
                <span className="text-xs text-muted-foreground">
                  {totalVulnerabilities > 0 ? 'ATTENTION_NEEDED' : 'CLEAN'}
                </span>
              </div>
            </div>
          </div>
        </div>
        <div className="bg-card border border-border rounded-lg p-4">
          <div className="flex items-center justify-between">
            <div>
              <p className="text-xs text-muted-foreground font-mono">AVG_SECURITY_SCORE</p>
              <p className="text-lg font-bold">
                {averageSecurityScore > 0 ? `${averageSecurityScore.toFixed(1)}%` : '--'}
              </p>
            </div>
            <div className="flex items-center gap-2">
              <svg className="h-4 w-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 12l2 2 4-4m5.618-4.016A11.955 11.955 0 0112 2.944a11.955 11.955 0 01-8.618 3.04A12.02 12.02 0 003 9c0 5.591 3.824 10.29 9 11.622 5.176-1.332 9-6.03 9-11.622 0-1.042-.133-2.052-.382-3.016z" />
              </svg>
              <div className="flex items-center gap-1">
                <span className="text-xs text-muted-foreground">
                  {averageSecurityScore > 0 ? 'CALCULATED' : 'NO_DATA'}
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
            <span className="whitespace-nowrap">NEW_SECURITY_TEST</span>
          </button>
          <button className="bg-transparent border border-border hover:bg-accent w-full sm:w-auto px-4 py-2 rounded font-mono text-sm transition-colors">
            <svg className="inline mr-2 h-4 w-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M7 16a4 4 0 01-.88-7.903A5 5 0 1115.9 6L16 6a5 5 0 011 9.9M15 13l-3-3m0 0l-3 3m3-3v12" />
            </svg>
            <span className="whitespace-nowrap">BATCH_TESTING</span>
          </button>
        </div>
      </div>

      {/* Main Content Grid */}
      <div className="grid gap-4 md:gap-6 grid-cols-1 lg:grid-cols-3">
        {/* Security Analysis Chart */}
        <div className="bg-card border border-border rounded-lg lg:col-span-2 min-h-[500px] flex flex-col">
          <div className="p-4 border-b border-border">
            <h3 className="text-sm font-bold text-gold">SECURITY_ANALYSIS_RESULTS</h3>
            <p className="text-xs text-muted-foreground font-mono">
              OWASP.AI.LLM.SECURITY.TESTING.AND.VULNERABILITY.ASSESSMENT
            </p>
          </div>
          <div className="flex-1 p-4">
            {loading ? (
              <div className="h-full w-full flex items-center justify-center">
                <div className="text-center">
                  <div className="animate-pulse">Loading security analysis data...</div>
                </div>
              </div>
            ) : securityAnalyses.length > 0 ? (
              <div className="space-y-4">
                {securityAnalyses.slice(0, 5).map((analysis) => (
                  <div key={analysis.id} className="border border-border rounded p-3">
                    <div className="flex justify-between items-start">
                      <div>
                        <h4 className="font-mono text-sm font-bold">{analysis.modelName}</h4>
                        <p className="text-xs text-muted-foreground">
                          Security Score: {analysis.securityScore}% | 
                          Vulnerabilities: {analysis.vulnerabilities}
                        </p>
                      </div>
                      <div className={`text-xs px-2 py-1 rounded ${
                        analysis.riskLevel === 'critical' ? 'bg-red-500/20 text-red-400' :
                        analysis.riskLevel === 'high' ? 'bg-orange-500/20 text-orange-400' :
                        analysis.riskLevel === 'medium' ? 'bg-yellow-500/20 text-yellow-400' :
                        'bg-green-500/20 text-green-400'
                      }`}>
                        {analysis.riskLevel.toUpperCase()}_RISK
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
                      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 15v2m-6 4h12a2 2 0 002-2v-6a2 2 0 00-2-2H6a2 2 0 00-2 2v6a2 2 0 002 2zm10-10V7a4 4 0 00-8 0v4h8z" />
                    </svg>
                  </div>
                  <h4 className="text-lg font-bold mb-2">NO_SECURITY_DATA_AVAILABLE</h4>
                  <p className="text-sm text-muted-foreground font-mono">
                    RUN_SECURITY_TESTS_TO_SEE_VULNERABILITY_ANALYSIS
                  </p>
                </div>
              </div>
            )}
          </div>
        </div>

        {/* Quick Testing Panel */}
        <div className="bg-card border border-border rounded-lg min-h-[500px] flex flex-col">
          <div className="p-4 border-b border-border">
            <h3 className="text-sm font-bold text-gold">QUICK_TESTING</h3>
            <p className="text-xs text-muted-foreground font-mono">RAPID.SECURITY.TESTING.TOOLS</p>
          </div>
          <div className="flex-1 p-4">
            <div className="space-y-4">
              <button className="w-full p-3 bg-gold text-gold-foreground hover:bg-gold/90 rounded font-mono text-sm transition-colors">
                <svg className="inline mr-2 h-4 w-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 4v16m8-8H4" />
                </svg>
                RUN_OWASP_TEST
              </button>
              <button className="w-full p-3 bg-transparent border border-border hover:bg-accent rounded font-mono text-sm transition-colors">
                <svg className="inline mr-2 h-4 w-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M7 16a4 4 0 01-.88-7.903A5 5 0 1115.9 6L16 6a5 5 0 011 9.9M15 13l-3-3m0 0l-3 3m3-3v12" />
                </svg>
                COMPREHENSIVE_SCAN
              </button>
              <button className="w-full p-3 bg-transparent border border-border hover:bg-accent rounded font-mono text-sm transition-colors">
                <svg className="inline mr-2 h-4 w-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 17v-2m3 2v-4m3 4v-6m2 10H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z" />
                </svg>
                GENERATE_SECURITY_REPORT
              </button>
            </div>
          </div>
        </div>
      </div>

      {/* OWASP Categories Analysis */}
      <div className="grid gap-4 md:gap-6 grid-cols-1 md:grid-cols-3">
        <div className="bg-card border border-border rounded-lg min-h-[400px] flex flex-col">
          <div className="p-4 border-b border-border">
            <h3 className="text-sm font-bold text-gold">OWASP_CATEGORIES</h3>
            <p className="text-xs text-muted-foreground font-mono">AI.LLM.SECURITY.CATEGORIES</p>
          </div>
          <div className="flex-1 p-4">
            <div className="h-full w-full flex items-center justify-center">
              <div className="text-center">
                <div className="w-16 h-16 bg-muted rounded-lg flex items-center justify-center mx-auto mb-4">
                  <svg className="w-8 h-8 text-muted-foreground" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 9v2m0 4h.01m-6.938 4h13.856c1.54 0 2.502-1.667 1.732-2.5L13.732 4c-.77-.833-1.964-.833-2.732 0L3.732 16.5c-.77.833.192 2.5 1.732 2.5z" />
                  </svg>
                </div>
                <h4 className="text-sm font-bold mb-2">NO_OWASP_TESTS</h4>
                <p className="text-xs text-muted-foreground font-mono">RUN_OWASP_ANALYSIS_TO_DETECT_VULNERABILITIES</p>
              </div>
            </div>
          </div>
        </div>
        <div className="bg-card border border-border rounded-lg min-h-[400px] flex flex-col">
          <div className="p-4 border-b border-border">
            <h3 className="text-sm font-bold text-gold">PENETRATION_TESTING</h3>
            <p className="text-xs text-muted-foreground font-mono">ADVANCED.SECURITY.ASSESSMENT</p>
          </div>
          <div className="flex-1 p-4">
            <div className="h-full w-full flex items-center justify-center">
              <div className="text-center">
                <div className="w-16 h-16 bg-muted rounded-lg flex items-center justify-center mx-auto mb-4">
                  <svg className="w-8 h-8 text-muted-foreground" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M13 10V3L4 14h7v7l9-11h-7z" />
                  </svg>
                </div>
                <h4 className="text-sm font-bold mb-2">NO_PENETRATION_TESTS</h4>
                <p className="text-xs text-muted-foreground font-mono">PERFORM_PENETRATION_TESTING_FOR_DEEP_ANALYSIS</p>
              </div>
            </div>
          </div>
        </div>
        <div className="bg-card border border-border rounded-lg min-h-[400px] flex flex-col">
          <div className="p-4 border-b border-border">
            <h3 className="text-sm font-bold text-gold">SECURITY_RECOMMENDATIONS</h3>
            <p className="text-xs text-muted-foreground font-mono">MITIGATION.STRATEGIES.AND.BEST.PRACTICES</p>
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
                <p className="text-xs text-muted-foreground font-mono">RUN_TESTS_TO_GET_SECURITY_SUGGESTIONS</p>
              </div>
            </div>
          </div>
        </div>
      </div>

      {/* Security Test History Table */}
      <div className="bg-card border border-border rounded-lg overflow-hidden">
        <div className="p-4 border-b border-border">
          <div className="flex flex-col space-y-1.5">
            <h3 className="text-sm font-bold text-gold">SECURITY_TEST_HISTORY</h3>
            <p className="text-xs text-muted-foreground font-mono">LATEST.SECURITY.TESTING.RESULTS</p>
          </div>
        </div>
        <div className="p-4">
          <div className="rounded-md border border-border">
            <table className="w-full">
              <thead>
                <tr className="border-b border-border">
                  <th className="text-left p-3 text-xs font-mono">MODEL_NAME</th>
                  <th className="text-left p-3 text-xs font-mono">TEST_TYPE</th>
                  <th className="text-left p-3 text-xs font-mono">SECURITY_SCORE</th>
                  <th className="text-left p-3 text-xs font-mono">VULNERABILITIES</th>
                  <th className="text-left p-3 text-xs font-mono">STATUS</th>
                  <th className="text-left p-3 text-xs font-mono">TEST_DATE</th>
                  <th className="text-right p-3 text-xs font-mono">ACTIONS</th>
                </tr>
              </thead>
              <tbody>
                <tr className="border-b border-border">
                  <td className="p-3 text-xs font-mono text-muted-foreground" colSpan={7}>
                    <div className="text-center py-8">
                      <div className="w-16 h-16 bg-muted rounded-lg flex items-center justify-center mx-auto mb-4">
                        <svg className="w-8 h-8 text-muted-foreground" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 15v2m-6 4h12a2 2 0 002-2v-6a2 2 0 00-2-2H6a2 2 0 00-2 2v6a2 2 0 002 2zm10-10V7a4 4 0 00-8 0v4h8z" />
                        </svg>
                      </div>
                      <h4 className="text-sm font-bold mb-2">NO_SECURITY_TESTS_PERFORMED</h4>
                      <p className="text-xs text-muted-foreground font-mono">
                        RUN_SECURITY_TESTS_TO_ANALYZE_MODEL_VULNERABILITIES
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
