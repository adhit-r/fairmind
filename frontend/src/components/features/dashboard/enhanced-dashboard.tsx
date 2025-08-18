"use client"

import { useState, useEffect } from 'react'
import { useSearchParams } from 'next/navigation'
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/common/card"
import { Button } from "@/components/ui/common/button"
import { Badge } from "@/components/ui/common/badge"
import { Progress } from "@/components/ui/common/progress"
import { 
  BarChart3, 
  Shield, 
  Target, 
  TrendingUp, 
  AlertTriangle, 
  CheckCircle, 
  Clock,
  Users,
  Database,
  Activity,
  Eye,
  Settings,
  Upload
} from "lucide-react"
import { useAuth } from "@/contexts/auth-context"
import { getOrganizationData, TEST_ORG_CONFIG } from "@/lib/supabase-auth"
import { 
  PerformanceMatrix 
} from "@/components/ui/charts/performance-matrix"
import { 
  RiskHeatmap 
} from "@/components/ui/charts/risk-heatmap"
import { 
  BiasDetectionRadar 
} from "@/components/ui/charts/bias-detection-radar"
import { 
  ComplianceTimeline 
} from "@/components/ui/charts/compliance-timeline"
import { 
  FairnessChart 
} from "@/components/ui/charts/fairness-chart"
import { 
  ModelDriftMonitor 
} from "@/components/ui/charts/model-drift-monitor"
import { 
  AIGovernanceChart 
} from "@/components/ui/charts/ai-governance-chart"
import { 
  NISTComplianceMatrix 
} from "@/components/ui/charts/nist-compliance-matrix"

interface DashboardData {
  models: any[]
  biasAnalyses: any[]
  securityTests: any[]
  complianceChecks: any[]
  recentActivity: any[]
  metrics: {
    totalModels: number
    biasScore: number
    securityScore: number
    complianceScore: number
    activeTests: number
  }
}

export function EnhancedDashboard() {
  const { user, profile } = useAuth()
  const searchParams = useSearchParams()
  const [data, setData] = useState<DashboardData | null>(null)
  const [loading, setLoading] = useState(true)
  const [orgType, setOrgType] = useState<'test' | 'new'>('new')

  useEffect(() => {
    const loadDashboardData = async () => {
      setLoading(true)
      try {
        // Check if this is a test organization
        const isTestOrg = searchParams.get('org') === 'test' || 
                         user?.email?.includes('demo') || 
                         user?.email?.includes('test')

        if (isTestOrg) {
          setOrgType('test')
          // Use test organization data
          const testData = TEST_ORG_CONFIG
          setData({
            models: testData.models,
            biasAnalyses: testData.bias_analyses,
            securityTests: testData.security_tests,
            complianceChecks: testData.compliance_checks,
            recentActivity: [
              {
                id: '1',
                type: 'bias_analysis',
                title: 'Bias analysis completed for Credit Risk Model',
                description: 'Statistical parity bias detected: 15% difference',
                timestamp: '2024-01-16T11:00:00Z',
                severity: 'medium'
              },
              {
                id: '2',
                type: 'security_test',
                title: 'Security test completed for Fraud Detection Model',
                description: 'Potential prompt injection vulnerability found',
                timestamp: '2024-01-17T13:30:00Z',
                severity: 'high'
              },
              {
                id: '3',
                type: 'compliance_check',
                title: 'Compliance check completed for Customer Segmentation',
                description: 'GDPR compliance gaps identified',
                timestamp: '2024-01-18T15:45:00Z',
                severity: 'medium'
              }
            ],
            metrics: {
              totalModels: testData.models.length,
              biasScore: Math.round(testData.bias_analyses[0]?.score * 100) || 85,
              securityScore: Math.round(testData.security_tests[0]?.score * 100) || 92,
              complianceScore: Math.round(testData.compliance_checks[0]?.score * 100) || 88,
              activeTests: 2
            }
          })
        } else {
          setOrgType('new')
          // For new organizations, start with empty data
          setData({
            models: [],
            biasAnalyses: [],
            securityTests: [],
            complianceChecks: [],
            recentActivity: [],
            metrics: {
              totalModels: 0,
              biasScore: 0,
              securityScore: 0,
              complianceScore: 0,
              activeTests: 0
            }
          })
        }
      } catch (error) {
        console.error('Error loading dashboard data:', error)
      } finally {
        setLoading(false)
      }
    }

    if (user) {
      loadDashboardData()
    }
  }, [user, searchParams])

  if (loading) {
    return (
      <div className="flex items-center justify-center h-64">
        <div className="text-center">
          <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-primary mx-auto"></div>
          <p className="mt-2 text-muted-foreground">Loading dashboard...</p>
        </div>
      </div>
    )
  }

  if (!data) {
    return (
      <div className="text-center py-8">
        <p className="text-muted-foreground">No data available</p>
      </div>
    )
  }

  const getSeverityColor = (severity: string) => {
    switch (severity) {
      case 'high': return 'bg-red-100 text-red-800'
      case 'medium': return 'bg-yellow-100 text-yellow-800'
      case 'low': return 'bg-green-100 text-green-800'
      default: return 'bg-gray-100 text-gray-800'
    }
  }

  const getActivityIcon = (type: string) => {
    switch (type) {
      case 'bias_analysis': return <Target className="h-4 w-4" />
      case 'security_test': return <Shield className="h-4 w-4" />
      case 'compliance_check': return <CheckCircle className="h-4 w-4" />
      default: return <Activity className="h-4 w-4" />
    }
  }

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-bold">AI Governance Dashboard</h1>
          <p className="text-muted-foreground">
            {orgType === 'test' ? 'Demo Organization - Sample Data' : 'Your Organization'}
          </p>
        </div>
        <div className="flex items-center gap-2">
          {orgType === 'test' && (
            <Badge variant="secondary" className="bg-blue-100 text-blue-800">
              Demo Mode
            </Badge>
          )}
          <Button variant="outline" size="sm">
            <Settings className="h-4 w-4 mr-2" />
            Settings
          </Button>
        </div>
      </div>

      {/* Key Metrics */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
        <Card>
          <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
            <CardTitle className="text-sm font-medium">Total Models</CardTitle>
            <Database className="h-4 w-4 text-muted-foreground" />
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold">{data.metrics.totalModels}</div>
            <p className="text-xs text-muted-foreground">
              {data.metrics.totalModels > 0 ? 'Active models' : 'No models uploaded'}
            </p>
          </CardContent>
        </Card>

        <Card>
          <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
            <CardTitle className="text-sm font-medium">Bias Score</CardTitle>
            <Target className="h-4 w-4 text-muted-foreground" />
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold">{data.metrics.biasScore}%</div>
            <Progress value={data.metrics.biasScore} className="mt-2" />
          </CardContent>
        </Card>

        <Card>
          <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
            <CardTitle className="text-sm font-medium">Security Score</CardTitle>
            <Shield className="h-4 w-4 text-muted-foreground" />
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold">{data.metrics.securityScore}%</div>
            <Progress value={data.metrics.securityScore} className="mt-2" />
          </CardContent>
        </Card>

        <Card>
          <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
            <CardTitle className="text-sm font-medium">Compliance Score</CardTitle>
            <CheckCircle className="h-4 w-4 text-muted-foreground" />
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold">{data.metrics.complianceScore}%</div>
            <Progress value={data.metrics.complianceScore} className="mt-2" />
          </CardContent>
        </Card>
      </div>

      {/* Charts Grid */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        <Card>
          <CardHeader>
            <CardTitle>AI Governance Overview</CardTitle>
            <CardDescription>Overall governance metrics and trends</CardDescription>
          </CardHeader>
          <CardContent>
            <AIGovernanceChart />
          </CardContent>
        </Card>

        <Card>
          <CardHeader>
            <CardTitle>Bias Detection Radar</CardTitle>
            <CardDescription>Bias metrics across different dimensions</CardDescription>
          </CardHeader>
          <CardContent>
            <BiasDetectionRadar />
          </CardContent>
        </Card>

        <Card>
          <CardHeader>
            <CardTitle>Risk Heatmap</CardTitle>
            <CardDescription>Security and compliance risk assessment</CardDescription>
          </CardHeader>
          <CardContent>
            <RiskHeatmap />
          </CardContent>
        </Card>

        <Card>
          <CardHeader>
            <CardTitle>Performance Matrix</CardTitle>
            <CardDescription>Model performance and accuracy metrics</CardDescription>
          </CardHeader>
          <CardContent>
            <PerformanceMatrix />
          </CardContent>
        </Card>
      </div>

      {/* Recent Activity */}
      <Card>
        <CardHeader>
          <CardTitle>Recent Activity</CardTitle>
          <CardDescription>Latest governance activities and alerts</CardDescription>
        </CardHeader>
        <CardContent>
          {data.recentActivity.length > 0 ? (
            <div className="space-y-4">
              {data.recentActivity.map((activity) => (
                <div key={activity.id} className="flex items-start gap-4 p-4 border rounded-lg">
                  <div className="flex-shrink-0">
                    {getActivityIcon(activity.type)}
                  </div>
                  <div className="flex-1 min-w-0">
                    <p className="text-sm font-medium">{activity.title}</p>
                    <p className="text-sm text-muted-foreground">{activity.description}</p>
                    <p className="text-xs text-muted-foreground mt-1">
                      {new Date(activity.timestamp).toLocaleString()}
                    </p>
                  </div>
                  <Badge className={getSeverityColor(activity.severity)}>
                    {activity.severity}
                  </Badge>
                </div>
              ))}
            </div>
          ) : (
            <div className="text-center py-8">
              <Activity className="h-12 w-12 mx-auto text-muted-foreground mb-4" />
              <p className="text-muted-foreground">No recent activity</p>
              <p className="text-sm text-muted-foreground mt-1">
                Start by uploading models and running assessments
              </p>
            </div>
          )}
        </CardContent>
      </Card>

      {/* Quick Actions */}
      {orgType === 'new' && (
        <Card>
          <CardHeader>
            <CardTitle>Get Started</CardTitle>
            <CardDescription>Begin your AI governance journey</CardDescription>
          </CardHeader>
          <CardContent>
            <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
              <Button className="h-20 flex-col" variant="outline">
                <Upload className="h-6 w-6 mb-2" />
                <span>Upload Models</span>
              </Button>
              <Button className="h-20 flex-col" variant="outline">
                <Target className="h-6 w-6 mb-2" />
                <span>Run Bias Tests</span>
              </Button>
              <Button className="h-20 flex-col" variant="outline">
                <Shield className="h-6 w-6 mb-2" />
                <span>Security Scan</span>
              </Button>
            </div>
          </CardContent>
        </Card>
      )}
    </div>
  )
}
