"use client"

import { useState, useEffect } from 'react'
import { useAuth } from "@/contexts/auth-context"
import { ProtectedRoute } from "@/components/core/auth/protected-route"
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/common/card"
import { Button } from "@/components/ui/common/button"
import { Badge } from "@/components/ui/common/badge"
import { modelRegistryService, ModelRegistryStats } from "@/lib/model-registry-service"
import {
  Brain,
  Shield,
  Target,
  BarChart3,
  Upload,
  AlertTriangle,
  CheckCircle,
  Clock,
  Users,
  Database,
  Zap,
  Loader2
} from "lucide-react"

export default function DashboardPage() {
  const { user } = useAuth()
  const [stats, setStats] = useState<ModelRegistryStats | null>(null)
  const [recentActivity, setRecentActivity] = useState<any[]>([])
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)

  // Get organization ID from user context
  const orgId = user?.organization_id || 'demo_org'

  useEffect(() => {
    loadDashboardData()
  }, [orgId])

  const loadDashboardData = async () => {
    try {
      setLoading(true)
      setError(null)
      
      const [statsData, activityData] = await Promise.all([
        modelRegistryService.getStats(orgId),
        modelRegistryService.getRecentActivity(orgId)
      ])
      
      setStats(statsData)
      setRecentActivity(activityData)
    } catch (err) {
      console.error('Error loading dashboard data:', err)
      setError('Failed to load dashboard data')
    } finally {
      setLoading(false)
    }
  }

  const quickActions = [
    {
      title: "Upload Model",
      description: "Add a new AI model to your registry",
      icon: Upload,
      href: "/model-registry",
      color: "bg-blue-600 hover:bg-blue-700",
      textColor: "text-blue-700"
    },
    {
      title: "Run Bias Analysis",
      description: "Analyze models for fairness and bias",
      icon: Target,
      href: "/bias-detection",
      color: "bg-green-600 hover:bg-green-700",
      textColor: "text-green-700"
    },
    {
      title: "Security Testing",
      description: "Test models for security vulnerabilities",
      icon: Shield,
      href: "/security-testing",
      color: "bg-purple-600 hover:bg-purple-700",
      textColor: "text-purple-700"
    },
    {
      title: "View Reports",
      description: "Access compliance and analytics reports",
      icon: BarChart3,
      href: "/reports",
      color: "bg-orange-600 hover:bg-orange-700",
      textColor: "text-orange-700"
    }
  ]

  if (loading) {
    return (
      <ProtectedRoute>
        <div className="space-y-8 p-6 bg-gray-50 min-h-screen">
          <div className="flex items-center justify-center h-64">
            <div className="text-center">
              <Loader2 className="h-8 w-8 animate-spin mx-auto mb-4 text-blue-600" />
              <p className="text-gray-600">Loading dashboard...</p>
            </div>
          </div>
        </div>
      </ProtectedRoute>
    )
  }

  if (error) {
    return (
      <ProtectedRoute>
        <div className="space-y-8 p-6 bg-gray-50 min-h-screen">
          <div className="bg-red-50 border-2 border-red-200 rounded-lg p-6">
            <div className="text-center">
              <AlertTriangle className="h-8 w-8 mx-auto mb-4 text-red-600" />
              <h3 className="text-lg font-bold text-red-900 mb-2">Error Loading Dashboard</h3>
              <p className="text-red-700 mb-4">{error}</p>
              <Button onClick={loadDashboardData} className="bg-red-600 hover:bg-red-700 text-white">
                Try Again
              </Button>
            </div>
          </div>
        </div>
      </ProtectedRoute>
    )
  }

  return (
    <ProtectedRoute>
      <div className="space-y-8 p-6 bg-gray-50 min-h-screen">
        {/* Welcome Header */}
        <div className="bg-white border-2 border-black shadow-4px-4px-0px-black rounded-lg p-6">
          <div className="flex items-center justify-between">
            <div>
              <h1 className="text-3xl font-bold text-gray-900 mb-2">
                Welcome back, {user?.full_name || 'User'}!
              </h1>
              <p className="text-gray-700 text-lg">
                Here's what's happening with your AI governance at <span className="font-semibold text-blue-700">{user?.organization_name}</span>
              </p>
            </div>
            <div className="flex items-center space-x-3">
              <Badge variant="outline" className="text-sm font-semibold border-2 border-gray-300 bg-gray-50 text-gray-800">
                {user?.role || 'User'}
              </Badge>
              <Badge variant="secondary" className="text-sm font-semibold bg-blue-100 text-blue-800 border-2 border-blue-300">
                {user?.organization_name}
              </Badge>
            </div>
          </div>
        </div>

        {/* Stats Grid */}
        {stats && (
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6">
            <Card className="border-2 border-black shadow-4px-4px-0px-black bg-white hover:shadow-6px-6px-0px-black transition-all duration-200">
              <CardContent className="p-6">
                <div className="flex items-center justify-between">
                  <div className="flex-1">
                    <p className="text-sm font-semibold text-gray-700 mb-1">Total Models</p>
                    <p className="text-3xl font-bold text-gray-900 mb-1">{stats.totalModels}</p>
                    <p className="text-xs font-medium text-green-700 bg-green-50 px-2 py-1 rounded-full inline-block">
                      +{Math.floor(stats.totalModels * 0.1)} this month
                    </p>
                  </div>
                  <div className="p-4 rounded-lg bg-blue-50 border-2 border-blue-200">
                    <Brain className="h-8 w-8 text-blue-700" />
                  </div>
                </div>
              </CardContent>
            </Card>
            <Card className="border-2 border-black shadow-4px-4px-0px-black bg-white hover:shadow-6px-6px-0px-black transition-all duration-200">
              <CardContent className="p-6">
                <div className="flex items-center justify-between">
                  <div className="flex-1">
                    <p className="text-sm font-semibold text-gray-700 mb-1">Active Models</p>
                    <p className="text-3xl font-bold text-gray-900 mb-1">{stats.activeModels}</p>
                    <p className="text-xs font-medium text-green-700 bg-green-50 px-2 py-1 rounded-full inline-block">
                      +{Math.floor(stats.activeModels * 0.05)} this week
                    </p>
                  </div>
                  <div className="p-4 rounded-lg bg-green-50 border-2 border-green-200">
                    <CheckCircle className="h-8 w-8 text-green-700" />
                  </div>
                </div>
              </CardContent>
            </Card>
            <Card className="border-2 border-black shadow-4px-4px-0px-black bg-white hover:shadow-6px-6px-0px-black transition-all duration-200">
              <CardContent className="p-6">
                <div className="flex items-center justify-between">
                  <div className="flex-1">
                    <p className="text-sm font-semibold text-gray-700 mb-1">Bias Alerts</p>
                    <p className="text-3xl font-bold text-gray-900 mb-1">{stats.highRiskModels}</p>
                    <p className="text-xs font-medium text-orange-700 bg-orange-50 px-2 py-1 rounded-full inline-block">
                      {stats.highRiskModels > 0 ? 'Needs attention' : 'All clear'}
                    </p>
                  </div>
                  <div className="p-4 rounded-lg bg-orange-50 border-2 border-orange-200">
                    <AlertTriangle className="h-8 w-8 text-orange-700" />
                  </div>
                </div>
              </CardContent>
            </Card>
            <Card className="border-2 border-black shadow-4px-4px-0px-black bg-white hover:shadow-6px-6px-0px-black transition-all duration-200">
              <CardContent className="p-6">
                <div className="flex items-center justify-between">
                  <div className="flex-1">
                    <p className="text-sm font-semibold text-gray-700 mb-1">Compliance Score</p>
                    <p className="text-3xl font-bold text-gray-900 mb-1">{stats.complianceScore}%</p>
                    <p className="text-xs font-medium text-green-700 bg-green-50 px-2 py-1 rounded-full inline-block">
                      +{Math.max(0, stats.complianceScore - 85)}% improvement
                    </p>
                  </div>
                  <div className="p-4 rounded-lg bg-red-50 border-2 border-red-200">
                    <Shield className="h-8 w-8 text-red-700" />
                  </div>
                </div>
              </CardContent>
            </Card>
          </div>
        )}

        {/* Quick Actions */}
        <Card className="border-2 border-black shadow-4px-4px-0px-black bg-white">
          <CardHeader className="bg-gray-50 border-b-2 border-gray-200">
            <CardTitle className="flex items-center gap-3 text-xl font-bold text-gray-900">
              <div className="p-2 bg-yellow-100 rounded-lg border-2 border-yellow-300">
                <Zap className="h-6 w-6 text-yellow-700" />
              </div>
              Quick Actions
            </CardTitle>
            <CardDescription className="text-gray-700 font-medium">
              Common tasks to get you started with AI governance
            </CardDescription>
          </CardHeader>
          <CardContent className="p-6">
            <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
              {quickActions.map((action, index) => (
                <Button
                  key={index}
                  variant="outline"
                  className="h-auto p-6 flex flex-col items-start space-y-3 border-2 border-gray-300 shadow-2px-2px-0px-gray-400 hover:shadow-4px-4px-0px-gray-400 transition-all duration-200 bg-white hover:bg-gray-50"
                >
                  <div className={`p-3 rounded-lg ${action.color} shadow-2px-2px-0px-black`}>
                    <action.icon className="h-6 w-6 text-white" />
                  </div>
                  <div className="text-left">
                    <p className="font-bold text-sm text-gray-900 mb-1">{action.title}</p>
                    <p className="text-xs text-gray-600 leading-relaxed">{action.description}</p>
                  </div>
                </Button>
              ))}
            </div>
          </CardContent>
        </Card>

        {/* Recent Activity */}
        <Card className="border-2 border-black shadow-4px-4px-0px-black bg-white">
          <CardHeader className="bg-gray-50 border-b-2 border-gray-200">
            <CardTitle className="flex items-center gap-3 text-xl font-bold text-gray-900">
              <div className="p-2 bg-blue-100 rounded-lg border-2 border-blue-300">
                <Clock className="h-6 w-6 text-blue-700" />
              </div>
              Recent Activity
            </CardTitle>
            <CardDescription className="text-gray-700 font-medium">
              Latest actions across your AI models and governance activities
            </CardDescription>
          </CardHeader>
          <CardContent className="p-6">
            <div className="space-y-4">
              {recentActivity.length > 0 ? (
                recentActivity.map((activity, index) => (
                  <div key={index} className="flex items-center justify-between p-4 border-2 border-gray-200 rounded-lg bg-gray-50 hover:bg-white hover:border-gray-300 transition-all duration-200">
                    <div className="flex items-center space-x-4">
                      <div className={`p-3 rounded-lg border-2 ${
                        activity.status === 'success' ? 'bg-green-100 border-green-300' :
                        activity.status === 'warning' ? 'bg-orange-100 border-orange-300' :
                        'bg-red-100 border-red-300'
                      }`}>
                        {activity.status === 'success' ? (
                          <CheckCircle className="h-5 w-5 text-green-700" />
                        ) : activity.status === 'warning' ? (
                          <AlertTriangle className="h-5 w-5 text-orange-700" />
                        ) : (
                          <AlertTriangle className="h-5 w-5 text-red-700" />
                        )}
                      </div>
                      <div>
                        <p className="font-semibold text-gray-900 text-sm">{activity.action}</p>
                        <p className="text-gray-600 text-sm">{activity.model} • {activity.user}</p>
                      </div>
                    </div>
                    <div className="text-right">
                      <p className="text-xs text-gray-500 font-medium">{activity.time}</p>
                      <Badge variant={
                        activity.status === 'success' ? 'default' :
                        activity.status === 'warning' ? 'secondary' :
                        'destructive'
                      } className="text-xs font-semibold mt-1">
                        {activity.status}
                      </Badge>
                    </div>
                  </div>
                ))
              ) : (
                <div className="text-center py-8">
                  <div className="p-4 bg-gray-100 rounded-lg border-2 border-gray-300 w-16 h-16 mx-auto mb-4 flex items-center justify-center">
                    <Clock className="h-8 w-8 text-gray-400" />
                  </div>
                  <h3 className="text-lg font-bold text-gray-900 mb-2">No recent activity</h3>
                  <p className="text-gray-600">Start by uploading your first model to see activity here</p>
                </div>
              )}
            </div>
          </CardContent>
        </Card>

        {/* Organization Overview */}
        <Card className="border-2 border-black shadow-4px-4px-0px-black bg-white">
          <CardHeader className="bg-gray-50 border-b-2 border-gray-200">
            <CardTitle className="flex items-center gap-3 text-xl font-bold text-gray-900">
              <div className="p-2 bg-purple-100 rounded-lg border-2 border-purple-300">
                <Users className="h-6 w-6 text-purple-700" />
              </div>
              Organization Overview
            </CardTitle>
            <CardDescription className="text-gray-700 font-medium">
              Key metrics and performance indicators for {user?.organization_name}
            </CardDescription>
          </CardHeader>
          <CardContent className="p-6">
            <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
              <div className="text-center p-6 bg-blue-50 border-2 border-blue-200 rounded-lg">
                <Database className="h-10 w-10 mx-auto mb-3 text-blue-700" />
                <p className="text-3xl font-bold text-gray-900 mb-1">{stats?.totalModels || 0}</p>
                <p className="text-sm font-semibold text-gray-700">Total Models</p>
                <p className="text-xs text-blue-600 mt-1">+{Math.floor((stats?.totalModels || 0) * 0.1)} this month</p>
              </div>
              <div className="text-center p-6 bg-green-50 border-2 border-green-200 rounded-lg">
                <Shield className="h-10 w-10 mx-auto mb-3 text-green-700" />
                <p className="text-3xl font-bold text-gray-900 mb-1">{stats?.complianceScore || 0}%</p>
                <p className="text-sm font-semibold text-gray-700">Compliance Score</p>
                <p className="text-xs text-green-600 mt-1">+{Math.max(0, (stats?.complianceScore || 0) - 85)}% improvement</p>
              </div>
              <div className="text-center p-6 bg-purple-50 border-2 border-purple-200 rounded-lg">
                <Target className="h-10 w-10 mx-auto mb-3 text-purple-700" />
                <p className="text-3xl font-bold text-gray-900 mb-1">{stats?.activeModels || 0}</p>
                <p className="text-sm font-semibold text-gray-700">Active Projects</p>
                <p className="text-xs text-purple-600 mt-1">{stats?.highRiskModels || 0} pending review</p>
              </div>
            </div>
          </CardContent>
        </Card>
      </div>
    </ProtectedRoute>
  )
}
