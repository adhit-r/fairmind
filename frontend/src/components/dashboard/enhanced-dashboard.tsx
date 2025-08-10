"use client"

import { useState, useEffect } from 'react'
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card"
import { Button } from "@/components/ui/button"
import { Badge } from "@/components/ui/badge"
import { Progress } from "@/components/ui/progress"
import { Alert, AlertDescription } from "@/components/ui/alert"
import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/components/ui/tabs"
import { 
  TrendingUp, 
  TrendingDown, 
  AlertTriangle, 
  CheckCircle, 
  Clock, 
  Users, 
  Shield, 
  Bot,
  BarChart3,
  Target,
  Lock,
  FileText,
  Activity,
  Eye,
  Zap,
  ArrowRight,
  RefreshCw,
  Settings,
  Download,
  Calendar,
  Star,
  AlertCircle,
  Info
} from "lucide-react"
import { fairmindAPI } from "@/lib/fairmind-api"
import { useAuth } from "@/contexts/auth-context"

interface DashboardMetric {
  title: string
  value: string | number
  change: number
  changeType: 'increase' | 'decrease' | 'neutral'
  icon: React.ReactNode
  description: string
}

interface RecentActivity {
  id: string
  type: 'model_upload' | 'analysis_complete' | 'security_alert' | 'compliance_check'
  title: string
  description: string
  timestamp: string
  status: 'success' | 'warning' | 'error' | 'info'
}

interface QuickAction {
  title: string
  description: string
  icon: React.ReactNode
  action: () => void
  color: string
}

export function EnhancedDashboard() {
  const { profile } = useAuth()
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState('')
  const [metrics, setMetrics] = useState<DashboardMetric[]>([])
  const [recentActivity, setRecentActivity] = useState<RecentActivity[]>([])
  const [complianceStatus, setComplianceStatus] = useState({
    overall: 85,
    eu_ai_act: 90,
    gdpr: 75,
    nist: 80
  })

  useEffect(() => {
    loadDashboardData()
  }, [])

  const loadDashboardData = async () => {
    setLoading(true)
    setError('')

    try {
      // Load metrics summary
      const metricsResponse = await fairmindAPI.getMetricsSummary()
      if (metricsResponse.success) {
        setMetrics([
          {
            title: 'Total Models',
            value: metricsResponse.data.total_models || 0,
            change: 12,
            changeType: 'increase',
            icon: <Bot className="h-4 w-4" />,
            description: 'AI models in registry'
          },
          {
            title: 'Active Analyses',
            value: metricsResponse.data.active_analyses || 0,
            change: -3,
            changeType: 'decrease',
            icon: <BarChart3 className="h-4 w-4" />,
            description: 'Running bias detection'
          },
          {
            title: 'Security Score',
            value: `${metricsResponse.data.security_score || 85}%`,
            change: 5,
            changeType: 'increase',
            icon: <Shield className="h-4 w-4" />,
            description: 'OWASP compliance'
          },
          {
            title: 'Compliance Status',
            value: `${complianceStatus.overall}%`,
            change: 2,
            changeType: 'increase',
            icon: <Target className="h-4 w-4" />,
            description: 'Regulatory compliance'
          }
        ])
      }

      // Mock recent activity data
      setRecentActivity([
        {
          id: '1',
          type: 'model_upload',
          title: 'New Model Uploaded',
          description: 'Credit Risk Model v2.1 uploaded by John Doe',
          timestamp: '2 minutes ago',
          status: 'success'
        },
        {
          id: '2',
          type: 'analysis_complete',
          title: 'Bias Analysis Complete',
          description: 'Gender bias analysis completed for Loan Approval Model',
          timestamp: '15 minutes ago',
          status: 'warning'
        },
        {
          id: '3',
          type: 'security_alert',
          title: 'Security Vulnerability Detected',
          description: 'OWASP A01 vulnerability found in Chatbot Model',
          timestamp: '1 hour ago',
          status: 'error'
        },
        {
          id: '4',
          type: 'compliance_check',
          title: 'Compliance Check Passed',
          description: 'EU AI Act compliance check passed for all models',
          timestamp: '2 hours ago',
          status: 'success'
        }
      ])
    } catch (error: any) {
      setError('Failed to load dashboard data')
      console.error('Error loading dashboard:', error)
    } finally {
      setLoading(false)
    }
  }

  const quickActions: QuickAction[] = [
    {
      title: 'Upload Model',
      description: 'Register a new AI model',
      icon: <Bot className="h-5 w-5" />,
      action: () => console.log('Upload model'),
      color: 'bg-blue-500'
    },
    {
      title: 'Run Analysis',
      description: 'Start bias detection',
      icon: <BarChart3 className="h-5 w-5" />,
      action: () => console.log('Run analysis'),
      color: 'bg-green-500'
    },
    {
      title: 'Security Test',
      description: 'OWASP security testing',
      icon: <Shield className="h-5 w-5" />,
      action: () => console.log('Security test'),
      color: 'bg-purple-500'
    },
    {
      title: 'Generate Report',
      description: 'Create compliance report',
      icon: <FileText className="h-5 w-5" />,
      action: () => console.log('Generate report'),
      color: 'bg-orange-500'
    }
  ]

  const getActivityIcon = (type: string) => {
    switch (type) {
      case 'model_upload': return <Bot className="h-4 w-4" />
      case 'analysis_complete': return <BarChart3 className="h-4 w-4" />
      case 'security_alert': return <Shield className="h-4 w-4" />
      case 'compliance_check': return <Target className="h-4 w-4" />
      default: return <Activity className="h-4 w-4" />
    }
  }

  const getStatusColor = (status: string) => {
    switch (status) {
      case 'success': return 'text-green-600 bg-green-100'
      case 'warning': return 'text-yellow-600 bg-yellow-100'
      case 'error': return 'text-red-600 bg-red-100'
      case 'info': return 'text-blue-600 bg-blue-100'
      default: return 'text-gray-600 bg-gray-100'
    }
  }

  const getChangeIcon = (changeType: string) => {
    switch (changeType) {
      case 'increase': return <TrendingUp className="h-4 w-4 text-green-600" />
      case 'decrease': return <TrendingDown className="h-4 w-4 text-red-600" />
      default: return <Activity className="h-4 w-4 text-gray-600" />
    }
  }

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-3xl font-bold">Dashboard</h1>
          <p className="text-muted-foreground">
            Welcome back, {profile?.full_name || 'User'}
          </p>
        </div>
        <div className="flex items-center space-x-2">
          <Button
            variant="outline"
            size="sm"
            onClick={loadDashboardData}
            disabled={loading}
          >
            <RefreshCw className={`h-4 w-4 mr-2 ${loading ? 'animate-spin' : ''}`} />
            Refresh
          </Button>
          <Button variant="outline" size="sm">
            <Settings className="h-4 w-4 mr-2" />
            Customize
          </Button>
        </div>
      </div>

      {/* Error Display */}
      {error && (
        <Alert variant="destructive">
          <AlertCircle className="h-4 w-4" />
          <AlertDescription>{error}</AlertDescription>
        </Alert>
      )}

      {/* Key Metrics Grid */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6">
        {metrics.map((metric, index) => (
          <Card key={index} className="hover:shadow-md transition-shadow duration-200">
            <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
              <CardTitle className="text-sm font-medium text-muted-foreground">
                {metric.title}
              </CardTitle>
              <div className="h-8 w-8 bg-primary/10 rounded-lg flex items-center justify-center">
                {metric.icon}
              </div>
            </CardHeader>
            <CardContent>
              <div className="text-2xl font-bold">{metric.value}</div>
              <div className="flex items-center space-x-2 text-xs text-muted-foreground">
                {getChangeIcon(metric.changeType)}
                <span className={metric.changeType === 'increase' ? 'text-green-600' : metric.changeType === 'decrease' ? 'text-red-600' : 'text-gray-600'}>
                  {metric.change > 0 ? '+' : ''}{metric.change}%
                </span>
                <span>from last month</span>
              </div>
              <p className="text-xs text-muted-foreground mt-1">{metric.description}</p>
            </CardContent>
          </Card>
        ))}
      </div>

      {/* Main Content Tabs */}
      <Tabs defaultValue="overview" className="space-y-4">
        <TabsList>
          <TabsTrigger value="overview">Overview</TabsTrigger>
          <TabsTrigger value="compliance">Compliance</TabsTrigger>
          <TabsTrigger value="security">Security</TabsTrigger>
          <TabsTrigger value="activity">Activity</TabsTrigger>
        </TabsList>

        <TabsContent value="overview" className="space-y-6">
          <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
            {/* Quick Actions */}
            <Card>
              <CardHeader>
                <CardTitle className="text-lg">Quick Actions</CardTitle>
                <CardDescription>
                  Common tasks and shortcuts
                </CardDescription>
              </CardHeader>
              <CardContent className="space-y-3">
                {quickActions.map((action, index) => (
                  <Button
                    key={index}
                    variant="ghost"
                    className="w-full justify-start h-auto p-3"
                    onClick={action.action}
                  >
                    <div className={`h-8 w-8 rounded-lg flex items-center justify-center text-white mr-3 ${action.color}`}>
                      {action.icon}
                    </div>
                    <div className="text-left">
                      <div className="font-medium">{action.title}</div>
                      <div className="text-xs text-muted-foreground">{action.description}</div>
                    </div>
                    <ArrowRight className="h-4 w-4 ml-auto" />
                  </Button>
                ))}
              </CardContent>
            </Card>

            {/* Recent Activity */}
            <Card className="lg:col-span-2">
              <CardHeader>
                <CardTitle className="text-lg">Recent Activity</CardTitle>
                <CardDescription>
                  Latest updates and notifications
                </CardDescription>
              </CardHeader>
              <CardContent>
                <div className="space-y-4">
                  {recentActivity.map((activity) => (
                    <div key={activity.id} className="flex items-start space-x-3">
                      <div className={`h-8 w-8 rounded-full flex items-center justify-center ${getStatusColor(activity.status)}`}>
                        {getActivityIcon(activity.type)}
                      </div>
                      <div className="flex-1 space-y-1">
                        <p className="text-sm font-medium">{activity.title}</p>
                        <p className="text-sm text-muted-foreground">{activity.description}</p>
                        <p className="text-xs text-muted-foreground">{activity.timestamp}</p>
                      </div>
                    </div>
                  ))}
                </div>
                <Button variant="outline" className="w-full mt-4">
                  View All Activity
                </Button>
              </CardContent>
            </Card>
          </div>
        </TabsContent>

        <TabsContent value="compliance" className="space-y-6">
          <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
            {/* Compliance Overview */}
            <Card>
              <CardHeader>
                <CardTitle className="text-lg">Compliance Overview</CardTitle>
                <CardDescription>
                  Regulatory compliance status
                </CardDescription>
              </CardHeader>
              <CardContent className="space-y-4">
                <div className="space-y-3">
                  <div className="flex items-center justify-between">
                    <span className="text-sm font-medium">Overall Compliance</span>
                    <span className="text-sm font-bold">{complianceStatus.overall}%</span>
                  </div>
                  <Progress value={complianceStatus.overall} className="h-2" />
                </div>
                
                <div className="space-y-3">
                  <div className="flex items-center justify-between">
                    <span className="text-sm">EU AI Act</span>
                    <span className="text-sm">{complianceStatus.eu_ai_act}%</span>
                  </div>
                  <Progress value={complianceStatus.eu_ai_act} className="h-2" />
                </div>
                
                <div className="space-y-3">
                  <div className="flex items-center justify-between">
                    <span className="text-sm">GDPR</span>
                    <span className="text-sm">{complianceStatus.gdpr}%</span>
                  </div>
                  <Progress value={complianceStatus.gdpr} className="h-2" />
                </div>
                
                <div className="space-y-3">
                  <div className="flex items-center justify-between">
                    <span className="text-sm">NIST RMF</span>
                    <span className="text-sm">{complianceStatus.nist}%</span>
                  </div>
                  <Progress value={complianceStatus.nist} className="h-2" />
                </div>
              </CardContent>
            </Card>

            {/* Compliance Alerts */}
            <Card>
              <CardHeader>
                <CardTitle className="text-lg">Compliance Alerts</CardTitle>
                <CardDescription>
                  Recent compliance issues and actions needed
                </CardDescription>
              </CardHeader>
              <CardContent>
                <div className="space-y-3">
                  <Alert>
                    <AlertTriangle className="h-4 w-4" />
                    <AlertDescription>
                      GDPR compliance check due in 5 days
                    </AlertDescription>
                  </Alert>
                  <Alert>
                    <CheckCircle className="h-4 w-4" />
                    <AlertDescription>
                      EU AI Act requirements met for all models
                    </AlertDescription>
                  </Alert>
                  <Alert>
                    <Info className="h-4 w-4" />
                    <AlertDescription>
                      NIST RMF assessment scheduled for next week
                    </AlertDescription>
                  </Alert>
                </div>
              </CardContent>
            </Card>
          </div>
        </TabsContent>

        <TabsContent value="security" className="space-y-6">
          <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
            {/* Security Score */}
            <Card>
              <CardHeader>
                <CardTitle className="text-lg">Security Score</CardTitle>
                <CardDescription>
                  OWASP security assessment results
                </CardDescription>
              </CardHeader>
              <CardContent>
                <div className="text-center space-y-4">
                  <div className="relative w-32 h-32 mx-auto">
                    <div className="w-full h-full rounded-full border-8 border-gray-200 flex items-center justify-center">
                      <div className="text-2xl font-bold">85%</div>
                    </div>
                    <div className="absolute inset-0 rounded-full border-8 border-green-500" style={{
                      clipPath: 'polygon(50% 50%, 50% 0%, 85% 0%, 85% 85%, 0% 85%, 0% 50%)'
                    }}></div>
                  </div>
                  <div className="space-y-2">
                    <div className="flex justify-between text-sm">
                      <span>Critical Issues</span>
                      <span className="text-red-600 font-medium">2</span>
                    </div>
                    <div className="flex justify-between text-sm">
                      <span>High Issues</span>
                      <span className="text-orange-600 font-medium">5</span>
                    </div>
                    <div className="flex justify-between text-sm">
                      <span>Medium Issues</span>
                      <span className="text-yellow-600 font-medium">8</span>
                    </div>
                  </div>
                </div>
              </CardContent>
            </Card>

            {/* Security Vulnerabilities */}
            <Card>
              <CardHeader>
                <CardTitle className="text-lg">Recent Vulnerabilities</CardTitle>
                <CardDescription>
                  Latest security findings
                </CardDescription>
              </CardHeader>
              <CardContent>
                <div className="space-y-3">
                  <div className="flex items-center justify-between p-3 bg-red-50 rounded-lg">
                    <div>
                      <p className="font-medium text-red-800">Prompt Injection</p>
                      <p className="text-sm text-red-600">Chatbot Model</p>
                    </div>
                    <Badge variant="destructive">Critical</Badge>
                  </div>
                  <div className="flex items-center justify-between p-3 bg-orange-50 rounded-lg">
                    <div>
                      <p className="font-medium text-orange-800">Output Validation</p>
                      <p className="text-sm text-orange-600">Recommendation Model</p>
                    </div>
                    <Badge variant="secondary">High</Badge>
                  </div>
                  <div className="flex items-center justify-between p-3 bg-yellow-50 rounded-lg">
                    <div>
                      <p className="font-medium text-yellow-800">Data Poisoning</p>
                      <p className="text-sm text-yellow-600">Training Data</p>
                    </div>
                    <Badge variant="outline">Medium</Badge>
                  </div>
                </div>
              </CardContent>
            </Card>
          </div>
        </TabsContent>

        <TabsContent value="activity" className="space-y-6">
          <Card>
            <CardHeader>
              <CardTitle className="text-lg">Activity Timeline</CardTitle>
              <CardDescription>
                Detailed activity log and audit trail
              </CardDescription>
            </CardHeader>
            <CardContent>
              <div className="space-y-4">
                {recentActivity.map((activity, index) => (
                  <div key={activity.id} className="flex items-start space-x-4">
                    <div className="flex flex-col items-center">
                      <div className={`h-3 w-3 rounded-full ${activity.status === 'success' ? 'bg-green-500' : activity.status === 'warning' ? 'bg-yellow-500' : activity.status === 'error' ? 'bg-red-500' : 'bg-blue-500'}`}></div>
                      {index < recentActivity.length - 1 && (
                        <div className="w-0.5 h-8 bg-gray-200 mt-1"></div>
                      )}
                    </div>
                    <div className="flex-1 space-y-1">
                      <div className="flex items-center justify-between">
                        <p className="font-medium">{activity.title}</p>
                        <span className="text-sm text-muted-foreground">{activity.timestamp}</span>
                      </div>
                      <p className="text-sm text-muted-foreground">{activity.description}</p>
                    </div>
                  </div>
                ))}
              </div>
              <Button variant="outline" className="w-full mt-4">
                <Download className="h-4 w-4 mr-2" />
                Export Activity Log
              </Button>
            </CardContent>
          </Card>
        </TabsContent>
      </Tabs>
    </div>
  )
}
