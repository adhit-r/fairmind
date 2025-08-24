"use client"

import React, { useState, useEffect, useMemo, useCallback } from 'react'
import { 
  ChartBarIcon, 
  ShieldCheckIcon, 
  EyeIcon, 
  CogIcon,
  BellIcon,
  UserCircleIcon,
  SunIcon,
  MoonIcon,
  ArrowRightIcon,
  ChevronDownIcon,
  Bars3Icon as MenuIcon,
  XMarkIcon as XIcon
} from '@heroicons/react/24/outline'

// Modern Navigation Component
const Navigation = ({ isOpen, onToggle }: { isOpen: boolean; onToggle: () => void }) => (
  <nav className={`fixed top-0 left-0 h-full w-64 bg-white/95 backdrop-blur-xl border-r border-gray-200/50 transform transition-transform duration-300 ease-in-out z-50 ${
    isOpen ? 'translate-x-0' : '-translate-x-full'
  }`}>
    <div className="p-6">
      <div className="flex items-center justify-between mb-8">
        <h2 className="text-xl font-bold text-gray-900">FairMind</h2>
        <button onClick={onToggle} className="p-2 hover:bg-gray-100 rounded-lg transition-colors">
          <XIcon className="w-5 h-5" />
        </button>
      </div>
      
      <div className="space-y-2">
        <a href="/" className="flex items-center p-3 text-gray-700 hover:bg-blue-50 hover:text-blue-600 rounded-lg transition-all group">
          <ChartBarIcon className="w-5 h-5 mr-3 group-hover:scale-110 transition-transform" />
          Dashboard
        </a>
        <a href="/bias-detection" className="flex items-center p-3 text-gray-700 hover:bg-green-50 hover:text-green-600 rounded-lg transition-all group">
          <ShieldCheckIcon className="w-5 h-5 mr-3 group-hover:scale-110 transition-transform" />
          Bias Detection
        </a>
        <a href="/security-testing" className="flex items-center p-3 text-gray-700 hover:bg-purple-50 hover:text-purple-600 rounded-lg transition-all group">
          <EyeIcon className="w-5 h-5 mr-3 group-hover:scale-110 transition-transform" />
          Security Testing
        </a>
        <a href="/model-registry" className="flex items-center p-3 text-gray-700 hover:bg-orange-50 hover:text-orange-600 rounded-lg transition-all group">
          <CogIcon className="w-5 h-5 mr-3 group-hover:scale-110 transition-transform" />
          Model Registry
        </a>
      </div>
    </div>
  </nav>
)

// Modern Stat Card with proper alignment
const StatCard = React.memo(({ title, value, change, icon: Icon, color, onClick }: {
  title: string
  value: string | number
  change?: { value: number; type: 'increase' | 'decrease' }
  icon: React.ComponentType<{ className?: string }>
  color: string
  onClick?: () => void
}) => (
  <div 
    onClick={onClick}
    className={`group relative overflow-hidden bg-white/80 backdrop-blur-sm border border-gray-200/50 rounded-2xl p-6 hover:shadow-xl hover:scale-105 transition-all duration-300 cursor-pointer ${
      onClick ? 'hover:border-blue-300' : ''
    }`}
  >
    {/* Background gradient */}
    <div className={`absolute inset-0 bg-gradient-to-br ${color} opacity-5 group-hover:opacity-10 transition-opacity`} />
    
    <div className="relative flex items-center justify-between mb-4">
      <div className={`p-3 rounded-xl ${color} shadow-lg group-hover:scale-110 transition-transform duration-300`}>
        <Icon className="w-6 h-6 text-white" />
      </div>
      {change && (
        <div className={`flex items-center space-x-1 px-2 py-1 rounded-full text-sm font-medium ${
          change.type === 'increase' 
            ? 'bg-green-100 text-green-700' 
            : 'bg-red-100 text-red-700'
        }`}>
          <span>{change.type === 'increase' ? '+' : '-'}{Math.abs(change.value)}%</span>
        </div>
      )}
    </div>
    
    <div className="relative">
      <h3 className="text-3xl font-bold text-gray-900 mb-2 group-hover:text-blue-600 transition-colors">
        {value}
      </h3>
      <p className="text-sm text-gray-600 font-medium">{title}</p>
    </div>
    
    {/* Hover effect */}
    <div className="absolute inset-0 bg-gradient-to-r from-transparent via-white/20 to-transparent -translate-x-full group-hover:translate-x-full transition-transform duration-700" />
  </div>
))

// Modern Quick Action Card
const QuickAction = React.memo(({ title, description, icon: Icon, onClick, color }: {
  title: string
  description: string
  icon: React.ComponentType<{ className?: string }>
  onClick: () => void
  color: string
}) => (
  <button 
    onClick={onClick}
    className="group relative overflow-hidden bg-white/80 backdrop-blur-sm border border-gray-200/50 rounded-2xl p-6 hover:shadow-xl hover:scale-105 transition-all duration-300 text-left"
  >
    {/* Background gradient */}
    <div className={`absolute inset-0 bg-gradient-to-br ${color} opacity-5 group-hover:opacity-10 transition-opacity`} />
    
    <div className="relative">
      <div className={`p-3 rounded-xl ${color} w-fit mb-4 shadow-lg group-hover:scale-110 transition-transform duration-300`}>
        <Icon className="w-6 h-6 text-white" />
      </div>
      
      <h4 className="font-semibold text-gray-900 mb-2 group-hover:text-blue-600 transition-colors">{title}</h4>
      <p className="text-sm text-gray-600 mb-4">{description}</p>
      
      <div className="flex items-center text-blue-600 font-medium text-sm group-hover:translate-x-1 transition-transform">
        <span>Get Started</span>
        <ArrowRightIcon className="w-4 h-4 ml-1" />
      </div>
    </div>
    
    {/* Hover effect */}
    <div className="absolute inset-0 bg-gradient-to-r from-transparent via-white/20 to-transparent -translate-x-full group-hover:translate-x-full transition-transform duration-700" />
  </button>
))

// Modern Activity Item
const ActivityItem = React.memo(({ activity }: { activity: {
  id: string
  type: string
  title: string
  timestamp: string
  status: 'success' | 'warning' | 'error'
} }) => (
  <div className="group flex items-center space-x-4 p-4 rounded-xl bg-gray-50/50 hover:bg-white hover:shadow-md transition-all duration-300">
    <div className={`w-3 h-3 rounded-full ${
      activity.status === 'success' ? 'bg-green-500' :
      activity.status === 'warning' ? 'bg-yellow-500' : 'bg-red-500'
    } group-hover:scale-125 transition-transform`} />
    
    <div className="flex-1 min-w-0">
      <p className="text-sm font-medium text-gray-900 truncate group-hover:text-blue-600 transition-colors">
        {activity.title}
      </p>
      <p className="text-xs text-gray-500">{activity.timestamp}</p>
    </div>
    
    <ChevronDownIcon className="w-4 h-4 text-gray-400 group-hover:text-gray-600 transition-colors" />
  </div>
))

export default function ModernDashboard() {
  const [isLoading, setIsLoading] = useState(true)
  const [theme, setTheme] = useState<'light' | 'dark'>('light')
  const [isNavOpen, setIsNavOpen] = useState(false)
  const [stats, setStats] = useState({
    totalModels: 0,
    activeModels: 0,
    biasTests: 0,
    securityScans: 0
  })

  // Memoized data
  const quickActions = useMemo(() => [
    {
      title: 'Run Bias Analysis',
      description: 'Detect bias in your AI models with advanced algorithms',
      icon: ShieldCheckIcon,
      color: 'bg-blue-500',
      action: () => window.location.href = '/bias-detection'
    },
    {
      title: 'Security Testing',
      description: 'OWASP security analysis for AI/ML models',
      icon: EyeIcon,
      color: 'bg-green-500',
      action: () => window.location.href = '/security-testing'
    },
    {
      title: 'Model Registry',
      description: 'Manage and track your AI model inventory',
      icon: CogIcon,
      color: 'bg-purple-500',
      action: () => window.location.href = '/model-registry'
    }
  ], [])

  const recentActivities = useMemo(() => [
    {
      id: '1',
      type: 'bias_analysis',
      title: 'Bias analysis completed for Credit Risk Model',
      timestamp: '2 minutes ago',
      status: 'success' as const
    },
    {
      id: '2',
      type: 'security_scan',
      title: 'Security scan started for Fraud Detection Model',
      timestamp: '5 minutes ago',
      status: 'warning' as const
    },
    {
      id: '3',
      type: 'model_deployment',
      title: 'New model deployed: Customer Segmentation v2.1',
      timestamp: '10 minutes ago',
      status: 'success' as const
    }
  ], [])

  // Optimized data fetching
  const fetchDashboardData = useCallback(async () => {
    try {
      await new Promise(resolve => setTimeout(resolve, 800))
      
      setStats({
        totalModels: 24,
        activeModels: 18,
        biasTests: 156,
        securityScans: 89
      })
    } catch (error) {
      console.error('Error fetching dashboard data:', error)
    } finally {
      setIsLoading(false)
    }
  }, [])

  useEffect(() => {
    fetchDashboardData()
  }, [fetchDashboardData])

  const toggleTheme = useCallback(() => {
    setTheme(prev => prev === 'light' ? 'dark' : 'light')
    document.documentElement.setAttribute('data-theme', theme === 'light' ? 'dark' : 'light')
  }, [theme])

  if (isLoading) {
    return (
      <div className="min-h-screen flex items-center justify-center bg-gradient-to-br from-blue-50 to-indigo-100">
        <div className="text-center">
          <div className="w-16 h-16 border-4 border-blue-500 border-t-transparent rounded-full animate-spin mx-auto mb-4"></div>
          <p className="text-gray-600 font-medium">Loading FairMind Dashboard...</p>
        </div>
      </div>
    )
  }

  return (
    <div className="min-h-screen bg-gradient-to-br from-blue-50 via-white to-indigo-50">
      {/* Navigation Overlay */}
      {isNavOpen && (
        <div 
          className="fixed inset-0 bg-black/20 backdrop-blur-sm z-40"
          onClick={() => setIsNavOpen(false)}
        />
      )}
      
      {/* Navigation */}
      <Navigation isOpen={isNavOpen} onToggle={() => setIsNavOpen(false)} />

      {/* Header */}
      <header className="sticky top-0 z-30 bg-white/80 backdrop-blur-xl border-b border-gray-200/50">
        <div className="max-w-7xl mx-auto px-6 py-4">
          <div className="flex items-center justify-between">
            <div className="flex items-center space-x-4">
              <button
                onClick={() => setIsNavOpen(true)}
                className="p-2 hover:bg-gray-100 rounded-lg transition-colors"
              >
                <MenuIcon className="w-6 h-6" />
              </button>
              
              <div>
                <h1 className="text-2xl font-bold text-gray-900">FairMind Dashboard</h1>
                <p className="text-sm text-gray-600">AI Governance & Bias Detection Platform</p>
              </div>
            </div>
            
            <div className="flex items-center space-x-4">
              <button
                onClick={toggleTheme}
                className="p-2 hover:bg-gray-100 rounded-lg transition-colors"
                aria-label="Toggle theme"
              >
                {theme === 'light' ? (
                  <MoonIcon className="w-5 h-5" />
                ) : (
                  <SunIcon className="w-5 h-5" />
                )}
              </button>
              
              <button className="p-2 hover:bg-gray-100 rounded-lg transition-colors relative">
                <BellIcon className="w-5 h-5" />
                <span className="absolute -top-1 -right-1 w-3 h-3 bg-red-500 rounded-full animate-pulse"></span>
              </button>
              
              <button className="p-2 hover:bg-gray-100 rounded-lg transition-colors">
                <UserCircleIcon className="w-5 h-5" />
              </button>
            </div>
          </div>
        </div>
      </header>

      {/* Main Content */}
      <main className="max-w-7xl mx-auto px-6 py-8">
        {/* Stats Grid */}
        <section className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6 mb-8">
          <StatCard
            title="Total Models"
            value={stats.totalModels}
            change={{ value: 12, type: 'increase' }}
            icon={ChartBarIcon}
            color="bg-blue-500"
            onClick={() => window.location.href = '/model-registry'}
          />
          <StatCard
            title="Active Models"
            value={stats.activeModels}
            change={{ value: 5, type: 'increase' }}
            icon={ShieldCheckIcon}
            color="bg-green-500"
            onClick={() => window.location.href = '/model-registry'}
          />
          <StatCard
            title="Bias Tests"
            value={stats.biasTests}
            change={{ value: 8, type: 'decrease' }}
            icon={EyeIcon}
            color="bg-purple-500"
            onClick={() => window.location.href = '/bias-detection'}
          />
          <StatCard
            title="Security Scans"
            value={stats.securityScans}
            change={{ value: 15, type: 'increase' }}
            icon={CogIcon}
            color="bg-orange-500"
            onClick={() => window.location.href = '/security-testing'}
          />
        </section>

        {/* Main Content Grid */}
        <div className="grid grid-cols-1 lg:grid-cols-3 gap-8">
          {/* Quick Actions */}
          <section className="lg:col-span-2">
            <h2 className="text-xl font-semibold text-gray-900 mb-6">Quick Actions</h2>
            <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
              {quickActions.map((action, index) => (
                <QuickAction
                  key={index}
                  title={action.title}
                  description={action.description}
                  icon={action.icon}
                  onClick={action.action}
                  color={action.color}
                />
              ))}
            </div>
          </section>

          {/* Recent Activity */}
          <section>
            <h2 className="text-xl font-semibold text-gray-900 mb-6">Recent Activity</h2>
            <div className="bg-white/80 backdrop-blur-sm border border-gray-200/50 rounded-2xl p-6">
              <div className="space-y-4">
                {recentActivities.map((activity) => (
                  <ActivityItem key={activity.id} activity={activity} />
                ))}
              </div>
            </div>
          </section>
        </div>

        {/* Performance Metrics */}
        <section className="mt-8">
          <h2 className="text-xl font-semibold text-gray-900 mb-6">Performance Overview</h2>
          <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
            <div className="bg-white/80 backdrop-blur-sm border border-gray-200/50 rounded-2xl p-6">
              <h3 className="text-lg font-semibold text-gray-900 mb-4">System Health</h3>
              <div className="space-y-4">
                <div className="flex items-center justify-between p-3 bg-green-50 rounded-lg">
                  <span className="text-sm text-gray-600">API Response Time</span>
                  <span className="text-sm font-medium text-green-600">45ms</span>
                </div>
                <div className="flex items-center justify-between p-3 bg-green-50 rounded-lg">
                  <span className="text-sm text-gray-600">Database Connection</span>
                  <span className="text-sm font-medium text-green-600">Connected</span>
                </div>
                <div className="flex items-center justify-between p-3 bg-yellow-50 rounded-lg">
                  <span className="text-sm text-gray-600">Storage Usage</span>
                  <span className="text-sm font-medium text-yellow-600">78%</span>
                </div>
              </div>
            </div>
            
            <div className="bg-white/80 backdrop-blur-sm border border-gray-200/50 rounded-2xl p-6">
              <h3 className="text-lg font-semibold text-gray-900 mb-4">Recent Alerts</h3>
              <div className="space-y-4">
                <div className="flex items-center space-x-3 p-3 bg-yellow-50 rounded-lg">
                  <div className="w-2 h-2 bg-yellow-500 rounded-full"></div>
                  <span className="text-sm text-gray-600">Model drift detected in Credit Risk Model</span>
                </div>
                <div className="flex items-center space-x-3 p-3 bg-green-50 rounded-lg">
                  <div className="w-2 h-2 bg-green-500 rounded-full"></div>
                  <span className="text-sm text-gray-600">Security scan completed successfully</span>
                </div>
                <div className="flex items-center space-x-3 p-3 bg-blue-50 rounded-lg">
                  <div className="w-2 h-2 bg-blue-500 rounded-full"></div>
                  <span className="text-sm text-gray-600">New model version deployed</span>
                </div>
              </div>
            </div>
          </div>
        </section>
      </main>
    </div>
  )
}
