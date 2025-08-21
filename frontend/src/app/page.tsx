"use client"

import { useState, useEffect } from 'react'
import { 
  TrendingUp, 
  AlertTriangle, 
  Shield, 
  Brain, 
  Users, 
  FileText, 
  BarChart3, 
  Activity,
  CheckCircle,
  Clock,
  Zap,
  Target,
  Settings,
  Eye,
  Database,
  Cpu,
  Globe,
  Lock,
  Upload as UploadIcon,
  RefreshCw
} from "lucide-react"
import { JourneyNavigation } from "@/components/core/navigation/journey-navigation"
import { fairmindAPI } from "@/lib/fairmind-api"
import { dashboardService, DashboardStats, DashboardActivity } from "@/lib/dashboard-service"
import { useAuth } from "@/contexts/auth-context"

interface ActivityItem {
  action: string
  model: string
  time: string
  status: 'success' | 'info' | 'warning' | 'error'
}

export default function HomePage() {
  const { user } = useAuth()
  const [stats, setStats] = useState<DashboardStats>({
    totalModels: 0,
    activeModels: 0,
    biasAlerts: 0,
    complianceScore: 0,
    recentScans: 0,
    totalUsers: 0,
    totalOrganizations: 0,
    geographicBiasAnalyses: 0
  })
  const [recentActivity, setRecentActivity] = useState<ActivityItem[]>([])
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState('')

  // Get organization ID from user context
  const orgId = user?.organization_id || 'demo_org'

  useEffect(() => {
    loadDashboardData()
  }, [orgId])

  const loadDashboardData = async () => {
    try {
      setLoading(true)
      setError('')

      // Load real data from dashboard service
      const [dashboardStats, dashboardActivity] = await Promise.all([
        dashboardService.getDashboardStats(orgId),
        dashboardService.getRecentActivity(orgId)
      ])

      setStats(dashboardStats)

      // Use real activity from dashboard service
      const activity: ActivityItem[] = dashboardActivity.map((item: DashboardActivity) => ({
        action: item.action,
        model: item.model,
        time: item.time,
        status: item.status
      }))

      setRecentActivity(activity)

    } catch (err) {
      console.error('Error loading dashboard data:', err)
      setError('Failed to load dashboard data')
      
      // Fallback to default data
      setStats({
        totalModels: 0,
        activeModels: 0,
        biasAlerts: 0,
        complianceScore: 0,
        recentScans: 0,
        totalUsers: 0,
        totalOrganizations: 0,
        geographicBiasAnalyses: 0
      })
      setRecentActivity([])
    } finally {
      setLoading(false)
    }
  }

  const quickStats = [
    { 
      label: "Total Models", 
      value: loading ? "..." : stats.totalModels.toString(), 
      icon: Brain, 
      color: "bg-blue-100 text-blue-800" 
    },
    { 
      label: "Active Models", 
      value: loading ? "..." : stats.activeModels.toString(), 
      icon: CheckCircle, 
      color: "bg-green-100 text-green-800" 
    },
    { 
      label: "Bias Alerts", 
      value: loading ? "..." : stats.biasAlerts.toString(), 
      icon: AlertTriangle, 
      color: "bg-red-100 text-red-800" 
    },
    { 
      label: "Compliance Score", 
      value: loading ? "..." : `${stats.complianceScore}%`, 
      icon: Shield, 
      color: "bg-purple-100 text-purple-800" 
    }
  ]

  const quickActions = [
    { title: "Run Bias Analysis", description: "Analyze model for fairness issues", icon: AlertTriangle, color: "bg-red-500", href: "/bias-detection" },
    { title: "Upload Model", description: "Add new model to registry", icon: UploadIcon, color: "bg-blue-500", href: "/model-upload" },
    { title: "Security Scan", description: "Check for vulnerabilities", icon: Shield, color: "bg-green-500", href: "/security" },
    { title: "View Reports", description: "Generate compliance reports", icon: FileText, color: "bg-purple-500", href: "/reports" }
  ]

  return (
    <div className="space-y-8">
      {/* Welcome Section */}
      <div className="bg-white border-2 border-black rounded-lg p-6 shadow-4px-4px-0px-black">
        <div className="flex items-center justify-between">
          <div>
            <h1 className="text-3xl font-bold text-gray-900 mb-2">
              Welcome to FairMind AI Governance
            </h1>
            <p className="text-gray-600">
              Monitor, analyze, and govern your AI models with comprehensive bias detection and compliance tools.
            </p>
          </div>
          <div className="flex items-center space-x-4">
            <button 
              onClick={loadDashboardData}
              disabled={loading}
              className="bg-white border-2 border-black px-4 py-2 rounded-lg hover:bg-gray-50 shadow-2px-2px-0px-black transition-all duration-200 flex items-center space-x-2"
            >
              <RefreshCw className={`h-4 w-4 ${loading ? 'animate-spin' : ''}`} />
              <span>Refresh</span>
            </button>
          </div>
        </div>
      </div>

      {/* Quick Stats */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6">
        {quickStats.map((stat, index) => (
          <div key={index} className="bg-white border-2 border-black rounded-lg p-6 shadow-4px-4px-0px-black">
            <div className="flex items-center justify-between">
              <div>
                <p className="text-sm font-semibold text-gray-600 uppercase tracking-wide">
                  {stat.label}
                </p>
                <p className="text-3xl font-bold text-gray-900 mt-2">
                  {stat.value}
                </p>
              </div>
              <div className={`p-3 rounded-lg ${stat.color}`}>
                <stat.icon className="h-6 w-6" />
              </div>
            </div>
          </div>
        ))}
      </div>

      {/* Quick Actions */}
      <div className="bg-white border-2 border-black rounded-lg p-6 shadow-4px-4px-0px-black">
        <h2 className="text-xl font-bold text-gray-900 mb-4">Quick Actions</h2>
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
          {quickActions.map((action, index) => (
            <a
              key={index}
              href={action.href}
              className="group block p-4 border-2 border-black rounded-lg hover:bg-gray-50 shadow-2px-2px-0px-black transition-all duration-200"
            >
              <div className="flex items-center space-x-3">
                <div className={`p-2 rounded-lg ${action.color} text-white`}>
                  <action.icon className="h-5 w-5" />
                </div>
                <div>
                  <h3 className="font-semibold text-gray-900 group-hover:text-blue-600">
                    {action.title}
                  </h3>
                  <p className="text-sm text-gray-600">
                    {action.description}
                  </p>
                </div>
              </div>
            </a>
          ))}
        </div>
      </div>

      {/* Recent Activity */}
      <div className="bg-white border-2 border-black rounded-lg p-6 shadow-4px-4px-0px-black">
        <div className="flex items-center justify-between mb-4">
          <h2 className="text-xl font-bold text-gray-900">Recent Activity</h2>
          <a href="/activity" className="text-blue-600 hover:text-blue-800 text-sm font-semibold">
            View All Activity
          </a>
        </div>
        
        {loading ? (
          <div className="space-y-4">
            {[1, 2, 3].map((i) => (
              <div key={i} className="animate-pulse">
                <div className="h-4 bg-gray-200 rounded w-3/4 mb-2"></div>
                <div className="h-3 bg-gray-200 rounded w-1/2"></div>
              </div>
            ))}
          </div>
        ) : recentActivity.length > 0 ? (
          <div className="space-y-4">
            {recentActivity.slice(0, 5).map((activity, index) => (
              <div key={index} className="flex items-center space-x-3 p-3 border-2 border-gray-200 rounded-lg">
                <div className={`p-2 rounded-lg ${
                  activity.status === 'success' ? 'bg-green-100 text-green-800' :
                  activity.status === 'warning' ? 'bg-yellow-100 text-yellow-800' :
                  activity.status === 'error' ? 'bg-red-100 text-red-800' :
                  'bg-blue-100 text-blue-800'
                }`}>
                  {activity.status === 'success' ? <CheckCircle className="h-4 w-4" /> :
                   activity.status === 'warning' ? <AlertTriangle className="h-4 w-4" /> :
                   activity.status === 'error' ? <AlertTriangle className="h-4 w-4" /> :
                   <Activity className="h-4 w-4" />}
                </div>
                <div className="flex-1">
                  <p className="font-semibold text-gray-900">{activity.action}</p>
                  <p className="text-sm text-gray-600">{activity.model}</p>
                </div>
                <div className="text-sm text-gray-500 flex items-center space-x-1">
                  <Clock className="h-3 w-3" />
                  <span>{activity.time}</span>
                </div>
              </div>
            ))}
          </div>
        ) : (
          <div className="text-center py-8">
            <Activity className="h-12 w-12 text-gray-400 mx-auto mb-4" />
            <p className="text-gray-600">No recent activity</p>
          </div>
        )}
      </div>

      {/* Error Display */}
      {error && (
        <div className="bg-red-50 border-2 border-red-200 rounded-lg p-4">
          <div className="flex items-center space-x-2">
            <AlertTriangle className="h-5 w-5 text-red-600" />
            <p className="text-red-800">{error}</p>
          </div>
        </div>
      )}
    </div>
  )
}
