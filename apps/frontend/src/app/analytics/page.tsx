'use client'

import React, { useState, useEffect } from 'react'
import { useRouter } from 'next/navigation'
import {
  ArrowLeft,
  BarChart3,
  TrendingUp,
  TrendingDown,
  Target,
  Shield,
  AlertTriangle,
  CheckCircle,
  Clock,
  Download,
  FileText,
  Users,
  Activity,
  PieChart,
  LineChart,
  Eye,
  Filter
} from 'lucide-react'
import { PageWrapper } from '@/components/core/PageWrapper'
import { Card } from '@/components/core/Card'
import { Button } from '@/components/core/Button'

interface AnalyticsMetric {
  id: string
  title: string
  value: string
  change: string
  trend: 'up' | 'down' | 'neutral'
  icon: React.ReactNode
}

interface TestResult {
  id: string
  model: string
  testType: string
  score: number
  status: 'passed' | 'failed' | 'warning'
  date: string
}

interface Report {
  id: string
  title: string
  type: string
  status: 'completed' | 'generating' | 'failed'
  date: string
  size: string
}

const demoMetrics: AnalyticsMetric[] = [
  {
    id: '1',
    title: 'Total Models',
    value: '24',
    change: '+12%',
    trend: 'up',
    icon: <BarChart3 className="h-5 w-5" />
  },
  {
    id: '2',
    title: 'Average Accuracy',
    value: '87.3%',
    change: '+2.1%',
    trend: 'up',
    icon: <Target className="h-5 w-5" />
  },
  {
    id: '3',
    title: 'Bias Score',
    value: '92.1%',
    change: '-1.2%',
    trend: 'down',
    icon: <Shield className="h-5 w-5" />
  },
  {
    id: '4',
    title: 'Security Score',
    value: '94.7%',
    change: '+0.8%',
    trend: 'up',
    icon: <AlertTriangle className="h-5 w-5" />
  }
]

const demoTestResults: TestResult[] = [
  {
    id: '1',
    model: 'Credit Risk Model v2.1',
    testType: 'Bias Detection',
    score: 89.2,
    status: 'passed',
    date: '2024-01-17T10:00:00Z'
  },
  {
    id: '2',
    model: 'Fraud Detection AI',
    testType: 'Security Testing',
    score: 94.1,
    status: 'passed',
    date: '2024-01-16T14:30:00Z'
  },
  {
    id: '3',
    model: 'Customer Segmentation',
    testType: 'Performance Test',
    score: 76.8,
    status: 'warning',
    date: '2024-01-15T09:15:00Z'
  },
  {
    id: '4',
    model: 'Loan Approval System',
    testType: 'Compliance Check',
    score: 91.5,
    status: 'passed',
    date: '2024-01-14T16:45:00Z'
  }
]

const demoReports: Report[] = [
  {
    id: '1',
    title: 'Monthly Bias Analysis Report',
    type: 'Bias Detection',
    status: 'completed',
    date: '2024-01-17T10:00:00Z',
    size: '2.4 MB'
  },
  {
    id: '2',
    title: 'Security Assessment Q1 2024',
    type: 'Security Testing',
    status: 'completed',
    date: '2024-01-16T14:30:00Z',
    size: '1.8 MB'
  },
  {
    id: '3',
    title: 'Compliance Audit Report',
    type: 'Compliance',
    status: 'generating',
    date: '2024-01-15T09:15:00Z',
    size: '3.2 MB'
  }
]

export default function AnalyticsPage() {
  return (
    <div className="space-y-6 p-4 md:p-6 max-w-[2000px] mx-auto">
      {/* Header Section */}
      <div className="space-y-2">
        <h1 className="text-2xl md:text-3xl font-bold tracking-tight text-gold">
          ANALYTICS
        </h1>
        <p className="text-xs md:text-sm text-muted-foreground font-mono">
          COMPREHENSIVE.INSIGHTS.INTO.MODEL.PERFORMANCE.AND.TESTING.RESULTS
        </p>
      </div>

      {/* Analytics Metrics */}
      <div className="grid gap-4 sm:grid-cols-2 lg:grid-cols-4">
        <div className="bg-card border border-border rounded-lg p-4">
            <div className="flex items-center justify-between">
              <div>
              <p className="text-xs text-muted-foreground font-mono">TOTAL_MODELS</p>
              <p className="text-lg font-bold">0</p>
            </div>
            <div className="flex items-center gap-2">
              <svg className="h-4 w-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M19 11H5m14 0a2 2 0 012 2v6a2 2 0 01-2 2H5a2 2 0 01-2-2v-6a2 2 0 012-2m14 0V9a2 2 0 00-2-2M5 11V9a2 2 0 012-2m0 0V5a2 2 0 012-2h6a2 2 0 012 2v2M7 7h10" />
              </svg>
              <div className="flex items-center gap-1">
                <span className="text-xs text-muted-foreground">NO_MODELS</span>
              </div>
            </div>
          </div>
        </div>
        <div className="bg-card border border-border rounded-lg p-4">
            <div className="flex items-center justify-between">
              <div>
              <p className="text-xs text-muted-foreground font-mono">AVERAGE_ACCURACY</p>
              <p className="text-lg font-bold">--</p>
            </div>
            <div className="flex items-center gap-2">
              <svg className="h-4 w-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 12l2 2 4-4m5.618-4.016A11.955 11.955 0 0112 2.944a11.955 11.955 0 01-8.618 3.04A12.02 12.02 0 003 9c0 5.591 3.824 10.29 9 11.622 5.176-1.332 9-6.03 9-11.622 0-1.042-.133-2.052-.382-3.016z" />
              </svg>
              <div className="flex items-center gap-1">
                <span className="text-xs text-muted-foreground">NO_DATA</span>
              </div>
            </div>
          </div>
        </div>
        <div className="bg-card border border-border rounded-lg p-4">
            <div className="flex items-center justify-between">
              <div>
              <p className="text-xs text-muted-foreground font-mono">BIAS_SCORE</p>
              <p className="text-lg font-bold">--</p>
            </div>
            <div className="flex items-center gap-2">
              <svg className="h-4 w-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 4.354a4 4 0 110 5.292M15 21H3v-1a6 6 0 0112 0v1zm0 0h6v-1a6 6 0 00-9-5.197m13.5-9a2.5 2.5 0 11-5 0 2.5 2.5 0 015 0z" />
              </svg>
              <div className="flex items-center gap-1">
                <span className="text-xs text-muted-foreground">NO_ANALYSIS</span>
              </div>
            </div>
          </div>
        </div>
        <div className="bg-card border border-border rounded-lg p-4">
            <div className="flex items-center justify-between">
              <div>
              <p className="text-xs text-muted-foreground font-mono">SECURITY_SCORE</p>
              <p className="text-lg font-bold">--</p>
            </div>
            <div className="flex items-center gap-2">
              <svg className="h-4 w-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 15v2m-6 4h12a2 2 0 002-2v-6a2 2 0 00-2-2H6a2 2 0 00-2 2v6a2 2 0 002 2zm10-10V7a4 4 0 00-8 0v4h8z" />
              </svg>
              <div className="flex items-center gap-1">
                <span className="text-xs text-muted-foreground">NO_TESTS</span>
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
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 17v-2m3 2v-4m3 4v-6m2 10H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z" />
            </svg>
            <span className="whitespace-nowrap">GENERATE_REPORT</span>
          </button>
          <button className="bg-transparent border border-border hover:bg-accent w-full sm:w-auto px-4 py-2 rounded font-mono text-sm transition-colors">
            <svg className="inline mr-2 h-4 w-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 10v6m0 0l-3-3m3 3l3-3m2 8H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z" />
            </svg>
            <span className="whitespace-nowrap">EXPORT_DATA</span>
          </button>
                  </div>
                </div>

      {/* Main Content Grid */}
      <div className="grid gap-4 md:gap-6 grid-cols-1 lg:grid-cols-3">
        {/* Analytics Dashboard */}
        <div className="bg-card border border-border rounded-lg lg:col-span-2 min-h-[500px] flex flex-col">
          <div className="p-4 border-b border-border">
            <h3 className="text-sm font-bold text-gold">ANALYTICS_DASHBOARD</h3>
            <p className="text-xs text-muted-foreground font-mono">
              PERFORMANCE.METRICS.AND.TRENDING.ANALYSIS
            </p>
          </div>
          <div className="flex-1 p-4">
            <div className="h-full w-full flex items-center justify-center">
                <div className="text-center">
                <div className="w-24 h-24 bg-muted rounded-lg flex items-center justify-center mx-auto mb-4">
                  <svg className="w-12 h-12 text-muted-foreground" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M16 8v8m-4-5v5m-4-2v2m-2 4h12a2 2 0 002-2V6a2 2 0 00-2-2H6a2 2 0 00-2 2v12a2 2 0 002 2z" />
                  </svg>
                </div>
                <h4 className="text-lg font-bold mb-2">NO_ANALYTICS_DATA_AVAILABLE</h4>
                <p className="text-sm text-muted-foreground font-mono">
                  UPLOAD_MODELS_AND_RUN_TESTS_TO_SEE_ANALYTICS
                </p>
              </div>
            </div>
          </div>
                        </div>

        {/* Quick Actions */}
        <div className="bg-card border border-border rounded-lg min-h-[500px] flex flex-col">
          <div className="p-4 border-b border-border">
            <h3 className="text-sm font-bold text-gold">QUICK_ACTIONS</h3>
            <p className="text-xs text-muted-foreground font-mono">RAPID.ANALYTICS.TOOLS</p>
                      </div>
          <div className="flex-1 p-4">
            <div className="space-y-4">
              <button className="w-full p-3 bg-gold text-gold-foreground hover:bg-gold/90 rounded font-mono text-sm transition-colors">
                <svg className="inline mr-2 h-4 w-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 17v-2m3 2v-4m3 4v-6m2 10H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z" />
                </svg>
                GENERATE_REPORT
              </button>
              <button className="w-full p-3 bg-transparent border border-border hover:bg-accent rounded font-mono text-sm transition-colors">
                <svg className="inline mr-2 h-4 w-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 10v6m0 0l-3-3m3 3l3-3m2 8H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z" />
                </svg>
                EXPORT_DATA
              </button>
              <button className="w-full p-3 bg-transparent border border-border hover:bg-accent rounded font-mono text-sm transition-colors">
                <svg className="inline mr-2 h-4 w-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M3 4a1 1 0 011-1h16a1 1 0 011 1v2.586a1 1 0 01-.293.707l-6.414 6.414a1 1 0 00-.293.707V17l-4 4v-6.586a1 1 0 00-.293-.707L3.293 7.293A1 1 0 013 6.586V4z" />
                </svg>
                FILTER_RESULTS
              </button>
                      </div>
                    </div>
                    </div>
                  </div>

      {/* Analytics Categories */}
      <div className="grid gap-4 md:gap-6 grid-cols-1 md:grid-cols-3">
        <div className="bg-card border border-border rounded-lg min-h-[400px] flex flex-col">
          <div className="p-4 border-b border-border">
            <h3 className="text-sm font-bold text-gold">TEST_RESULTS</h3>
            <p className="text-xs text-muted-foreground font-mono">RECENT.TESTING.ANALYSIS</p>
          </div>
          <div className="flex-1 p-4">
            <div className="h-full w-full flex items-center justify-center">
              <div className="text-center">
                <div className="w-16 h-16 bg-muted rounded-lg flex items-center justify-center mx-auto mb-4">
                  <svg className="w-8 h-8 text-muted-foreground" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 12l2 2 4-4m5.618-4.016A11.955 11.955 0 0112 2.944a11.955 11.955 0 01-8.618 3.04A12.02 12.02 0 003 9c0 5.591 3.824 10.29 9 11.622 5.176-1.332 9-6.03 9-11.622 0-1.042-.133-2.052-.382-3.016z" />
                  </svg>
                </div>
                <h4 className="text-sm font-bold mb-2">NO_TEST_RESULTS</h4>
                <p className="text-xs text-muted-foreground font-mono">RUN_TESTS_TO_SEE_RESULTS</p>
                      </div>
                    </div>
          </div>
                      </div>
        <div className="bg-card border border-border rounded-lg min-h-[400px] flex flex-col">
          <div className="p-4 border-b border-border">
            <h3 className="text-sm font-bold text-gold">GENERATED_REPORTS</h3>
            <p className="text-xs text-muted-foreground font-mono">ANALYTICS.AND.COMPLIANCE.REPORTS</p>
                  </div>
          <div className="flex-1 p-4">
            <div className="h-full w-full flex items-center justify-center">
              <div className="text-center">
                <div className="w-16 h-16 bg-muted rounded-lg flex items-center justify-center mx-auto mb-4">
                  <svg className="w-8 h-8 text-muted-foreground" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 12h6m-6 4h6m2 5H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z" />
                  </svg>
                </div>
                <h4 className="text-sm font-bold mb-2">NO_REPORTS_GENERATED</h4>
                <p className="text-xs text-muted-foreground font-mono">GENERATE_REPORTS_TO_SEE_ANALYTICS</p>
              </div>
                  </div>
          </div>
        </div>
        <div className="bg-card border border-border rounded-lg min-h-[400px] flex flex-col">
          <div className="p-4 border-b border-border">
            <h3 className="text-sm font-bold text-gold">PERFORMANCE_TRENDS</h3>
            <p className="text-xs text-muted-foreground font-mono">MODEL.PERFORMANCE.OVER.TIME</p>
          </div>
          <div className="flex-1 p-4">
            <div className="h-full w-full flex items-center justify-center">
                <div className="text-center">
                <div className="w-16 h-16 bg-muted rounded-lg flex items-center justify-center mx-auto mb-4">
                  <svg className="w-8 h-8 text-muted-foreground" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M13 7h8m0 0v8m0-8l-8 8-4-4-6 6" />
                  </svg>
                </div>
                <h4 className="text-sm font-bold mb-2">NO_TREND_DATA</h4>
                <p className="text-xs text-muted-foreground font-mono">UPLOAD_MODELS_TO_SEE_TRENDS</p>
              </div>
            </div>
          </div>
                        </div>
                      </div>

      {/* Analytics Reports Table */}
      <div className="bg-card border border-border rounded-lg overflow-hidden">
        <div className="p-4 border-b border-border">
          <div className="flex flex-col space-y-1.5">
            <h3 className="text-sm font-bold text-gold">ANALYTICS_REPORTS</h3>
            <p className="text-xs text-muted-foreground font-mono">COMPREHENSIVE.ANALYTICS.AND.REPORTING</p>
          </div>
        </div>
        <div className="p-4">
          <div className="rounded-md border border-border">
            <table className="w-full">
              <thead>
                <tr className="border-b border-border">
                  <th className="text-left p-3 text-xs font-mono">REPORT_NAME</th>
                  <th className="text-left p-3 text-xs font-mono">TYPE</th>
                  <th className="text-left p-3 text-xs font-mono">STATUS</th>
                  <th className="text-left p-3 text-xs font-mono">GENERATED_DATE</th>
                  <th className="text-left p-3 text-xs font-mono">SIZE</th>
                  <th className="text-right p-3 text-xs font-mono">ACTIONS</th>
                </tr>
              </thead>
              <tbody>
                <tr className="border-b border-border">
                  <td className="p-3 text-xs font-mono text-muted-foreground" colSpan={6}>
                    <div className="text-center py-8">
                      <div className="w-16 h-16 bg-muted rounded-lg flex items-center justify-center mx-auto mb-4">
                        <svg className="w-8 h-8 text-muted-foreground" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 17v-2m3 2v-4m3 4v-6m2 10H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z" />
                        </svg>
                      </div>
                      <h4 className="text-sm font-bold mb-2">NO_ANALYTICS_REPORTS</h4>
                      <p className="text-xs text-muted-foreground font-mono">
                        GENERATE_REPORTS_TO_SEE_ANALYTICS_AND_INSIGHTS
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
