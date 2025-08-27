'use client'

import React, { useState, useEffect } from 'react'
import { api, type GovernanceMetrics, type RecentActivity } from '../config/api'

export default function Home() {
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)
  const [metrics, setMetrics] = useState<GovernanceMetrics | null>(null)
  const [recentActivity, setRecentActivity] = useState<RecentActivity[]>([])
  const [mounted, setMounted] = useState(false)

  useEffect(() => {
    setMounted(true)
  }, [])

  useEffect(() => {
    if (!mounted) return

    const fetchDashboardData = async () => {
      try {
        setLoading(true)
        setError(null)
        console.log('🔄 Fetching real dashboard data from backend...')

        // Fetch governance metrics
        const metricsResponse = await api.getGovernanceMetrics()
        if (metricsResponse.success && metricsResponse.data) {
          setMetrics(metricsResponse.data)
          console.log('✅ Governance metrics loaded:', metricsResponse.data)
        } else {
          console.warn('⚠️ No governance metrics data received')
        }

        // Fetch recent activity
        const activityResponse = await api.getRecentActivity()
        if (activityResponse.success && activityResponse.data) {
          setRecentActivity(activityResponse.data)
          console.log('✅ Recent activity loaded:', activityResponse.data)
        } else {
          console.warn('⚠️ No recent activity data received')
        }

      } catch (err) {
        console.error('❌ Error fetching dashboard data:', err)
        setError(err instanceof Error ? err.message : 'Failed to load dashboard data')
      } finally {
        setLoading(false)
      }
    }

    fetchDashboardData()
  }, [mounted])

  if (!mounted) {
    return null
  }

  if (loading) {
    return (
      <div className="space-y-6 p-4 md:p-6 max-w-[2000px] mx-auto">
        <div className="space-y-2">
          <h1 className="text-2xl md:text-3xl font-bold tracking-tight text-gold">
            FairMind Dashboard
          </h1>
          <p className="text-xs md:text-sm text-muted-foreground font-mono">
            AI Governance & Compliance Platform
          </p>
        </div>
        <div className="flex items-center justify-center h-64">
          <div className="text-center">
            <div className="w-8 h-8 border-2 border-gold border-t-transparent rounded-full animate-spin mx-auto mb-4"></div>
            <p className="text-sm text-muted-foreground font-mono">Loading real-time data...</p>
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
            FairMind Dashboard
          </h1>
          <p className="text-xs md:text-sm text-muted-foreground font-mono">
            AI Governance & Compliance Platform
          </p>
        </div>
        <div className="bg-red-500/10 border border-red-500/20 rounded-lg p-6">
          <div className="flex items-center gap-3 mb-4">
            <span className="text-2xl">⚠️</span>
            <h2 className="text-xl font-bold text-red-400">Connection Error</h2>
          </div>
          <p className="text-sm text-muted-foreground font-mono mb-4">
            Unable to connect to the backend service. Please ensure the backend is running on port 8001.
          </p>
          <p className="text-xs text-muted-foreground font-mono">
            Error: {error}
          </p>
          <button 
            onClick={() => window.location.reload()}
            className="mt-4 px-4 py-2 bg-gold text-gold-foreground rounded-md font-mono text-sm hover:bg-gold/90 transition-colors"
          >
            Retry Connection
          </button>
        </div>
      </div>
    )
  }

  return (
    <div className="space-y-6 p-4 md:p-6 max-w-[2000px] mx-auto">
      {/* Header */}
      <div className="space-y-2">
        <h1 className="text-2xl md:text-3xl font-bold tracking-tight text-gold">
          FairMind Dashboard
        </h1>
        <p className="text-xs md:text-sm text-muted-foreground font-mono">
          AI Governance & Compliance Platform
        </p>
      </div>

      {/* Governance Metrics */}
      <div className="bg-card border border-border rounded-lg p-6">
        <div className="flex items-center justify-between mb-6">
          <div>
            <h2 className="text-xl font-bold text-foreground">Governance Overview</h2>
            <p className="text-sm text-muted-foreground font-mono">
              Real-time AI governance metrics and compliance status
            </p>
          </div>
          <div className="text-right">
            <div className="text-3xl font-bold text-gold">
              {metrics?.llmSafetyScore || 0}%
            </div>
            <span className="text-sm text-muted-foreground font-mono">LLM Safety Score</span>
          </div>
        </div>
        
        <div className="grid gap-4 sm:grid-cols-2 lg:grid-cols-4">
          <div className="text-center">
            <div className="text-2xl font-bold text-foreground">
              {metrics?.totalModels || 0}
            </div>
            <div className="text-xs text-muted-foreground font-mono">Total Models</div>
          </div>
          <div className="text-center">
            <div className="text-2xl font-bold text-green-400">
              {metrics?.activeModels || 0}
            </div>
            <div className="text-xs text-muted-foreground font-mono">Active Models</div>
          </div>
          <div className="text-center">
            <div className="text-2xl font-bold text-orange-400">
              {metrics?.criticalRisks || 0}
            </div>
            <div className="text-xs text-muted-foreground font-mono">Critical Risks</div>
          </div>
          <div className="text-center">
            <div className="text-2xl font-bold text-blue-400">
              {metrics?.nistCompliance || 0}%
            </div>
            <div className="text-xs text-muted-foreground font-mono">NIST Compliance</div>
          </div>
        </div>
      </div>

      {/* Recent Activity */}
      <div className="bg-card border border-border rounded-lg p-6">
        <div className="flex items-center justify-between mb-6">
          <div>
            <h2 className="text-xl font-bold text-foreground">Recent Activity</h2>
            <p className="text-sm text-muted-foreground font-mono">
              Latest AI governance activities and compliance events
            </p>
          </div>
          <button className="px-4 py-2 bg-gold text-gold-foreground rounded-md font-mono text-sm hover:bg-gold/90 transition-colors">
            View All Activity
          </button>
        </div>
        
        <div className="space-y-4">
          {recentActivity.length > 0 ? (
            recentActivity.map((activity) => (
              <div key={activity.id} className="flex items-center gap-4 p-4 border border-border rounded-lg">
                <div className="flex-shrink-0">
                  <span className="text-2xl">
                    {activity.type === 'model_upload' && '📤'}
                    {activity.type === 'bias_analysis' && '⚖️'}
                    {activity.type === 'security_test' && '🛡️'}
                    {activity.type === 'compliance_check' && '📋'}
                  </span>
                </div>
                <div className="flex-1 min-w-0">
                  <div className="flex items-center gap-2 mb-1">
                    <h3 className="text-sm font-bold text-foreground truncate">
                      {activity.modelName}
                    </h3>
                    <span className={`inline-flex px-2 py-1 rounded text-xs font-mono ${
                      activity.status === 'completed' ? 'text-green-400 bg-green-500/20' :
                      activity.status === 'running' ? 'text-blue-400 bg-blue-500/20' :
                      'text-red-400 bg-red-500/20'
                    }`}>
                      {activity.status.toUpperCase()}
                    </span>
                  </div>
                  <p className="text-xs text-muted-foreground font-mono mb-1">
                    {activity.description}
                  </p>
                  <p className="text-xs text-muted-foreground font-mono">
                    {new Date(activity.timestamp).toLocaleString()}
                  </p>
                </div>
              </div>
            ))
          ) : (
            <div className="text-center py-8">
              <div className="text-4xl mb-4">📊</div>
              <h3 className="text-lg font-bold text-foreground mb-2">No Recent Activity</h3>
              <p className="text-sm text-muted-foreground font-mono">
                No recent activities found. Start by uploading a model or running an analysis.
              </p>
            </div>
          )}
        </div>
      </div>

      {/* Quick Actions */}
      <div className="grid gap-4 sm:grid-cols-2 lg:grid-cols-4">
        <div className="bg-card border border-border rounded-lg p-4 text-center hover:bg-accent transition-colors cursor-pointer">
          <div className="text-3xl mb-2">🤖</div>
          <h3 className="text-sm font-bold text-foreground mb-1">Upload Model</h3>
          <p className="text-xs text-muted-foreground font-mono">Register new AI model</p>
        </div>
        <div className="bg-card border border-border rounded-lg p-4 text-center hover:bg-accent transition-colors cursor-pointer">
          <div className="text-3xl mb-2">⚖️</div>
          <h3 className="text-sm font-bold text-foreground mb-1">Bias Analysis</h3>
          <p className="text-xs text-muted-foreground font-mono">Run fairness assessment</p>
        </div>
        <div className="bg-card border border-border rounded-lg p-4 text-center hover:bg-accent transition-colors cursor-pointer">
          <div className="text-3xl mb-2">🛡️</div>
          <h3 className="text-sm font-bold text-foreground mb-1">Security Test</h3>
          <p className="text-xs text-muted-foreground font-mono">OWASP security testing</p>
        </div>
        <div className="bg-card border border-border rounded-lg p-4 text-center hover:bg-accent transition-colors cursor-pointer">
          <div className="text-3xl mb-2">📋</div>
          <h3 className="text-sm font-bold text-foreground mb-1">Compliance Check</h3>
          <p className="text-xs text-muted-foreground font-mono">Regulatory compliance</p>
        </div>
      </div>

      {/* System Status */}
      <div className="bg-card border border-border rounded-lg p-4">
        <div className="flex items-center justify-between">
          <div className="flex items-center gap-2">
            <div className="w-2 h-2 bg-green-400 rounded-full"></div>
            <span className="text-sm font-mono text-foreground">Backend Connected</span>
          </div>
          <div className="text-xs text-muted-foreground font-mono">
            Last updated: {new Date().toLocaleTimeString()}
          </div>
        </div>
      </div>
    </div>
  )
}
