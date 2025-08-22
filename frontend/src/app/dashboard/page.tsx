"use client"

import React from 'react'
import { useRouter } from 'next/navigation'
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/common/card'
import { Button } from '@/components/ui/common/button'
import { Badge } from '@/components/ui/common/badge'
import { Progress } from '@/components/ui/common/progress'
import { 
  Upload, 
  TestTube, 
  BarChart3, 
  Shield, 
  Target, 
  AlertTriangle,
  CheckCircle,
  Clock,
  TrendingUp,
  Users,
  FileText,
  Settings,
  Bell
} from 'lucide-react'
import { demoModels, demoAnalytics, demoNotifications } from '@/data/demo-data'

export default function DashboardPage() {
  const router = useRouter()

  const handleUploadModel = () => {
    router.push('/model-upload')
  }

  const handleTestModels = () => {
    router.push('/model-testing')
  }

  const handleViewAnalytics = () => {
    router.push('/analytics')
  }

  const getStatusColor = (status: string) => {
    switch (status) {
      case 'active': return 'bg-green-100 text-green-800'
      case 'testing': return 'bg-yellow-100 text-yellow-800'
      case 'archived': return 'bg-gray-100 text-gray-800'
      default: return 'bg-gray-100 text-gray-800'
    }
  }

  const getScoreColor = (score: number) => {
    if (score >= 80) return 'text-green-600'
    if (score >= 60) return 'text-yellow-600'
    return 'text-red-600'
  }

  const unreadNotifications = demoNotifications.filter(n => !n.read).length

  return (
    <div className="container mx-auto p-6">
      {/* Header */}
      <div className="flex justify-between items-center mb-8">
        <div>
          <h1 className="text-3xl font-bold text-gray-900">SQ1 AI Governance Dashboard</h1>
          <p className="text-gray-600 mt-2">Comprehensive AI model management and monitoring</p>
        </div>
        <div className="flex items-center space-x-4">
          <Button variant="outline" size="sm">
            <Bell className="w-4 h-4 mr-2" />
            {unreadNotifications > 0 && (
              <Badge variant="destructive" className="ml-1">
                {unreadNotifications}
              </Badge>
            )}
          </Button>
          <Button variant="outline" size="sm">
            <Settings className="w-4 h-4 mr-2" />
            Settings
          </Button>
        </div>
      </div>

      {/* Overview Stats */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6 mb-8">
        <Card>
          <CardContent className="p-6">
            <div className="flex items-center justify-between">
              <div>
                <p className="text-sm font-medium text-gray-600">Total Models</p>
                <p className="text-2xl font-bold text-gray-900">{demoAnalytics.overview.totalModels}</p>
              </div>
              <FileText className="w-8 h-8 text-blue-600" />
            </div>
            <div className="mt-4">
              <div className="flex justify-between text-sm mb-1">
                <span>Active</span>
                <span>{demoAnalytics.overview.activeModels}</span>
              </div>
              <Progress value={(demoAnalytics.overview.activeModels / demoAnalytics.overview.totalModels) * 100} className="h-2" />
            </div>
          </CardContent>
        </Card>

        <Card>
          <CardContent className="p-6">
            <div className="flex items-center justify-between">
              <div>
                <p className="text-sm font-medium text-gray-600">Average Bias Score</p>
                <p className={`text-2xl font-bold ${getScoreColor(demoAnalytics.overview.averageBiasScore)}`}>
                  {demoAnalytics.overview.averageBiasScore}%
                </p>
              </div>
              <Target className="w-8 h-8 text-blue-600" />
            </div>
            <div className="mt-4">
              <div className="flex items-center text-sm text-gray-600">
                <TrendingUp className="w-4 h-4 mr-1" />
                <span>+2.3% from last month</span>
              </div>
            </div>
          </CardContent>
        </Card>

        <Card>
          <CardContent className="p-6">
            <div className="flex items-center justify-between">
              <div>
                <p className="text-sm font-medium text-gray-600">Security Score</p>
                <p className={`text-2xl font-bold ${getScoreColor(demoAnalytics.overview.averageSecurityScore)}`}>
                  {demoAnalytics.overview.averageSecurityScore}%
                </p>
              </div>
              <Shield className="w-8 h-8 text-green-600" />
            </div>
            <div className="mt-4">
              <div className="flex items-center text-sm text-gray-600">
                <CheckCircle className="w-4 h-4 mr-1" />
                <span>All models secure</span>
              </div>
            </div>
          </CardContent>
        </Card>

        <Card>
          <CardContent className="p-6">
            <div className="flex items-center justify-between">
              <div>
                <p className="text-sm font-medium text-gray-600">Critical Issues</p>
                <p className="text-2xl font-bold text-red-600">{demoAnalytics.overview.criticalIssues}</p>
              </div>
              <AlertTriangle className="w-8 h-8 text-red-600" />
            </div>
            <div className="mt-4">
              <div className="flex items-center text-sm text-gray-600">
                <Clock className="w-4 h-4 mr-1" />
                <span>1 requires attention</span>
              </div>
            </div>
          </CardContent>
        </Card>
      </div>

      {/* Quick Actions */}
      <div className="mb-8">
        <h2 className="text-xl font-semibold text-gray-900 mb-4">Quick Actions</h2>
        <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
          <Button 
            onClick={handleUploadModel}
            className="h-20 flex flex-col items-center justify-center space-y-2 bg-blue-50 hover:bg-blue-100 border-blue-200"
          >
            <Upload className="w-6 h-6 text-blue-600" />
            <span className="text-blue-900 font-medium">Upload Your First Model</span>
          </Button>
          
          <Button 
            onClick={handleTestModels}
            className="h-20 flex flex-col items-center justify-center space-y-2 bg-green-50 hover:bg-green-100 border-green-200"
          >
            <TestTube className="w-6 h-6 text-green-600" />
            <span className="text-green-900 font-medium">Run New Test</span>
          </Button>
          
          <Button 
            onClick={handleViewAnalytics}
            className="h-20 flex flex-col items-center justify-center space-y-2 bg-purple-50 hover:bg-purple-100 border-purple-200"
          >
            <BarChart3 className="w-6 h-6 text-purple-600" />
            <span className="text-purple-900 font-medium">View Analytics</span>
          </Button>
        </div>
      </div>

      {/* Recent Models */}
      <div className="mb-8">
        <div className="flex justify-between items-center mb-4">
          <h2 className="text-xl font-semibold text-gray-900">Recent Models</h2>
          <Button variant="outline" size="sm">
            View All Models
          </Button>
        </div>
        
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
          {demoModels.slice(0, 3).map((model) => (
            <Card key={model.id} className="hover:shadow-lg transition-shadow cursor-pointer">
              <CardHeader>
                <div className="flex justify-between items-start">
                  <div>
                    <CardTitle className="text-lg">{model.name}</CardTitle>
                    <p className="text-sm text-gray-600">v{model.version}</p>
                  </div>
                  <Badge className={getStatusColor(model.status)}>
                    {model.status}
                  </Badge>
                </div>
              </CardHeader>
              <CardContent className="space-y-4">
                <div className="flex justify-between text-sm">
                  <span>Type:</span>
                  <span className="font-medium">{model.type}</span>
                </div>
                <div className="flex justify-between text-sm">
                  <span>Framework:</span>
                  <span className="font-medium">{model.framework}</span>
                </div>
                <div className="flex justify-between text-sm">
                  <span>Team:</span>
                  <span className="font-medium">{model.team}</span>
                </div>
                
                <div className="pt-4 border-t space-y-2">
                  <div className="flex justify-between text-sm">
                    <span>Bias Score:</span>
                    <span className={`font-medium ${getScoreColor(model.biasScore)}`}>
                      {model.biasScore}%
                    </span>
                  </div>
                  <div className="flex justify-between text-sm">
                    <span>Security Score:</span>
                    <span className={`font-medium ${getScoreColor(model.securityScore)}`}>
                      {model.securityScore}%
                    </span>
                  </div>
                </div>

                <div className="pt-4 border-t">
                  <div className="flex space-x-2">
                    <Button size="sm" className="flex-1">
                      <TestTube className="w-4 h-4 mr-1" />
                      Test
                    </Button>
                    <Button size="sm" variant="outline" className="flex-1">
                      <BarChart3 className="w-4 h-4 mr-1" />
                      View
                    </Button>
                  </div>
                </div>
              </CardContent>
            </Card>
          ))}
        </div>
      </div>

      {/* Team Performance */}
      <div className="mb-8">
        <h2 className="text-xl font-semibold text-gray-900 mb-4">Team Performance</h2>
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6">
          {demoAnalytics.teamPerformance.map((team) => (
            <Card key={team.team}>
              <CardContent className="p-6">
                <div className="flex items-center justify-between mb-4">
                  <h3 className="font-semibold text-gray-900">{team.team}</h3>
                  <Users className="w-5 h-5 text-gray-400" />
                </div>
                <div className="space-y-3">
                  <div className="flex justify-between text-sm">
                    <span>Models:</span>
                    <span className="font-medium">{team.models}</span>
                  </div>
                  <div className="flex justify-between text-sm">
                    <span>Avg Score:</span>
                    <span className={`font-medium ${getScoreColor(team.averageScore)}`}>
                      {team.averageScore}%
                    </span>
                  </div>
                  <div className="flex justify-between text-sm">
                    <span>Tests Run:</span>
                    <span className="font-medium">{team.testsRun}</span>
                  </div>
                  <div className="flex justify-between text-sm">
                    <span>Issues:</span>
                    <span className="font-medium text-red-600">{team.issues}</span>
                  </div>
                </div>
              </CardContent>
            </Card>
          ))}
        </div>
      </div>

      {/* Recent Activity */}
      <div>
        <h2 className="text-xl font-semibold text-gray-900 mb-4">Recent Activity</h2>
        <Card>
          <CardContent className="p-6">
            <div className="space-y-4">
              {demoNotifications.slice(0, 4).map((notification) => (
                <div key={notification.id} className="flex items-center space-x-4 p-3 rounded-lg hover:bg-gray-50">
                  <div className={`w-2 h-2 rounded-full ${
                    notification.severity === 'error' ? 'bg-red-500' :
                    notification.severity === 'warning' ? 'bg-yellow-500' : 'bg-blue-500'
                  }`} />
                  <div className="flex-1">
                    <p className="font-medium text-gray-900">{notification.title}</p>
                    <p className="text-sm text-gray-600">{notification.message}</p>
                  </div>
                  <div className="text-sm text-gray-500">
                    {new Date(notification.timestamp).toLocaleDateString()}
                  </div>
                  {!notification.read && (
                    <div className="w-2 h-2 bg-blue-500 rounded-full" />
                  )}
                </div>
              ))}
            </div>
          </CardContent>
        </Card>
      </div>
    </div>
  )
}
