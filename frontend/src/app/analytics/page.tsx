"use client"

import { useState, useEffect } from 'react'
import { 
  BarChart3, 
  TrendingUp, 
  TrendingDown, 
  Activity, 
  Eye, 
  Download, 
  Share, 
  Plus, 
  Settings, 
  RefreshCw, 
  Search, 
  Filter, 
  Shield,
  Database,
  Cpu,
  Zap,
  Target,
  Users,
  Globe,
  Lock,
  Brain,
  TestTube,
  FileText,
  Network,
  X,
  Info,
  HelpCircle,
  Star,
  Award,
  Calendar,
  MapPin,
  UserCheck,
  Scale,
  ChevronRight,
  ChevronDown,
  Sparkles,
  BarChart,
  PieChart,
  LineChart,
  ArrowRight,
  FileUp,
  Play,
  Pause,
  RotateCcw,
  Save,
  Edit,
  Trash2,
  Copy,
  Bookmark,
  Tag,
  Hash,
  Link,
  Unlink,
  GitBranch,
  GitCommit,
  GitMerge,
  GitPullRequest,
  GitCompare,
  GitFork,
  CheckCircle,
  AlertTriangle,
  Clock
} from "lucide-react"
import { fairmindAPI } from "@/lib/fairmind-api"

interface AnalyticsData {
  id: string
  name: string
  type: 'performance' | 'bias' | 'security' | 'compliance' | 'usage'
  value: number
  change: number
  period: string
  data: {
    labels: string[]
    values: number[]
  }
  insights: string[]
}

export default function AnalyticsPage() {
  const [analytics, setAnalytics] = useState<AnalyticsData[]>([])
  const [loading, setLoading] = useState(true)
  const [selectedAnalytic, setSelectedAnalytic] = useState<AnalyticsData | null>(null)
  const [searchTerm, setSearchTerm] = useState('')
  const [filterType, setFilterType] = useState('all')

  useEffect(() => {
    loadAnalyticsData()
  }, [])

  const loadAnalyticsData = async () => {
    try {
      setLoading(true)
      
      // In a real implementation, this would come from the API
      // For now, we'll generate realistic analytics data
      const datasets = await fairmindAPI.getAvailableDatasets()
      
      const mockAnalytics: AnalyticsData[] = [
        {
          id: 'perf-1',
          name: 'Model Performance Trends',
          type: 'performance',
          value: 87.5,
          change: 2.3,
          period: 'Last 30 days',
          data: {
            labels: ['Week 1', 'Week 2', 'Week 3', 'Week 4'],
            values: [82, 85, 86, 87.5]
          },
          insights: [
            'Performance improved by 2.3% over the last month',
            'Consistent upward trend in accuracy metrics',
            'Response time decreased by 15%'
          ]
        },
        {
          id: 'bias-1',
          name: 'Bias Detection Analysis',
          type: 'bias',
          value: 92.1,
          change: -1.2,
          period: 'Last 30 days',
          data: {
            labels: ['Week 1', 'Week 2', 'Week 3', 'Week 4'],
            values: [94, 93.5, 92.8, 92.1]
          },
          insights: [
            'Bias score decreased slightly by 1.2%',
            'Demographic parity improved in recent weeks',
            'Individual fairness metrics remain stable'
          ]
        },
        {
          id: 'sec-1',
          name: 'Security Metrics',
          type: 'security',
          value: 95.8,
          change: 3.1,
          period: 'Last 30 days',
          data: {
            labels: ['Week 1', 'Week 2', 'Week 3', 'Week 4'],
            values: [90, 92, 94, 95.8]
          },
          insights: [
            'Security score improved by 3.1%',
            'Vulnerability detection rate increased',
            'Adversarial robustness tests passed'
          ]
        },
        {
          id: 'comp-1',
          name: 'Compliance Tracking',
          type: 'compliance',
          value: 88.7,
          change: 1.5,
          period: 'Last 30 days',
          data: {
            labels: ['Week 1', 'Week 2', 'Week 3', 'Week 4'],
            values: [85, 86.5, 87.8, 88.7]
          },
          insights: [
            'Compliance score increased by 1.5%',
            'GDPR compliance maintained at 100%',
            'New audit requirements implemented'
          ]
        },
        {
          id: 'usage-1',
          name: 'System Usage Analytics',
          type: 'usage',
          value: 156,
          change: 12.5,
          period: 'Last 30 days',
          data: {
            labels: ['Week 1', 'Week 2', 'Week 3', 'Week 4'],
            values: [120, 135, 145, 156]
          },
          insights: [
            'System usage increased by 12.5%',
            'Peak usage during business hours',
            'New features adoption rate high'
          ]
        }
      ]
      
      setAnalytics(mockAnalytics)
    } catch (error) {
      console.error('Error loading analytics data:', error)
      setAnalytics([])
    } finally {
      setLoading(false)
    }
  }

  const filteredAnalytics = analytics.filter(analytic => {
    const matchesSearch = analytic.name.toLowerCase().includes(searchTerm.toLowerCase())
    const matchesFilter = filterType === 'all' || analytic.type === filterType
    return matchesSearch && matchesFilter
  })

  const getAnalyticTypeColor = (type: string) => {
    switch (type) {
      case 'performance': return 'bg-blue-500'
      case 'bias': return 'bg-yellow-500'
      case 'security': return 'bg-red-500'
      case 'compliance': return 'bg-purple-500'
      case 'usage': return 'bg-green-500'
      default: return 'bg-gray-500'
    }
  }

  const getAnalyticTypeIcon = (type: string) => {
    switch (type) {
      case 'performance': return Cpu
      case 'bias': return Scale
      case 'security': return Shield
      case 'compliance': return CheckCircle
      case 'usage': return Activity
      default: return BarChart3
    }
  }

  const getChangeColor = (change: number) => {
    return change >= 0 ? 'text-green-600' : 'text-red-600'
  }

  const getChangeIcon = (change: number) => {
    return change >= 0 ? <TrendingUp className="h-4 w-4" /> : <TrendingDown className="h-4 w-4" />
  }

  return (
    <div className="space-y-8">
      {/* Header */}
      <div className="bg-gradient-to-r from-blue-50 to-purple-50 border-2 border-black rounded-lg p-8 shadow-4px-4px-0px-black">
        <div className="flex items-center justify-between">
          <div>
            <h1 className="text-3xl font-black text-gray-900 mb-2 flex items-center">
              <BarChart3 className="h-8 w-8 mr-3 text-blue-600" />
              Analytics Dashboard
            </h1>
            <p className="text-lg font-bold text-gray-600 mb-4">
              Comprehensive analytics and insights for AI governance metrics.
            </p>
            <div className="flex items-center space-x-4">
              <div className="flex items-center space-x-2 bg-blue-100 border-2 border-black px-3 py-1 rounded-lg">
                <BarChart3 className="h-4 w-4 text-blue-800" />
                <span className="text-sm font-bold text-blue-800">{analytics.length} Analytics</span>
              </div>
              <div className="flex items-center space-x-2 bg-green-100 border-2 border-black px-3 py-1 rounded-lg">
                <TrendingUp className="h-4 w-4 text-green-800" />
                <span className="text-sm font-bold text-green-800">Real-time Data</span>
              </div>
              <button 
                onClick={loadAnalyticsData}
                disabled={loading}
                className="flex items-center space-x-2 bg-white border-2 border-black px-3 py-1 rounded-lg hover:bg-gray-50 shadow-2px-2px-0px-black transition-all duration-200 disabled:opacity-50"
              >
                <RefreshCw className={`h-4 w-4 text-gray-700 ${loading ? 'animate-spin' : ''}`} />
                <span className="text-sm font-bold text-gray-700">Refresh</span>
              </button>
            </div>
          </div>
          <div className="hidden md:block">
            <div className="w-20 h-20 bg-gradient-to-br from-purple-600 to-blue-600 rounded-lg border-2 border-black shadow-4px-4px-0px-black flex items-center justify-center">
              <BarChart3 className="h-10 w-10 text-white" />
            </div>
          </div>
        </div>
      </div>

      {/* Search and Filters */}
      <div className="bg-white border-2 border-black rounded-lg p-6 shadow-4px-4px-0px-black">
        <div className="flex flex-col md:flex-row gap-4">
          <div className="flex-1">
            <div className="relative">
              <Search className="absolute left-3 top-1/2 transform -translate-y-1/2 h-4 w-4 text-gray-400" />
              <input
                type="text"
                placeholder="Search analytics by name..."
                value={searchTerm}
                onChange={(e) => setSearchTerm(e.target.value)}
                className="w-full pl-10 pr-4 py-3 border-2 border-gray-300 rounded-lg font-bold focus:border-blue-500 focus:outline-none"
              />
            </div>
          </div>
          <div className="flex gap-2">
            <select
              value={filterType}
              onChange={(e) => setFilterType(e.target.value)}
              className="px-4 py-3 border-2 border-gray-300 rounded-lg font-bold focus:border-blue-500 focus:outline-none"
            >
              <option value="all">All Types</option>
              <option value="performance">Performance</option>
              <option value="bias">Bias</option>
              <option value="security">Security</option>
              <option value="compliance">Compliance</option>
              <option value="usage">Usage</option>
            </select>
            <button className="bg-blue-500 text-white border-2 border-black px-6 py-3 rounded-lg font-bold hover:bg-blue-600 shadow-2px-2px-0px-black transition-all duration-200">
              <Plus className="h-4 w-4 mr-2" />
              New Report
            </button>
          </div>
        </div>
      </div>

      {/* Analytics Grid */}
      {loading ? (
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
          {[1, 2, 3, 4, 5, 6].map((i) => (
            <div key={i} className="bg-white border-2 border-black rounded-lg p-6 shadow-4px-4px-0px-black animate-pulse">
              <div className="h-4 bg-gray-200 rounded mb-4"></div>
              <div className="h-3 bg-gray-200 rounded mb-2"></div>
              <div className="h-3 bg-gray-200 rounded w-3/4"></div>
            </div>
          ))}
        </div>
      ) : filteredAnalytics.length > 0 ? (
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
          {filteredAnalytics.map((analytic) => {
            const IconComponent = getAnalyticTypeIcon(analytic.type)
            return (
              <div
                key={analytic.id}
                onClick={() => setSelectedAnalytic(analytic)}
                className="bg-white border-2 border-black rounded-lg p-6 shadow-4px-4px-0px-black cursor-pointer hover:shadow-6px-6px-0px-black transition-all duration-200"
              >
                <div className="flex items-center justify-between mb-4">
                  <div className="flex items-center space-x-3">
                    <div className={`p-2 rounded-lg border-2 border-black ${getAnalyticTypeColor(analytic.type)}`}>
                      <IconComponent className="h-5 w-5 text-white" />
                    </div>
                    <div>
                      <h3 className="font-black text-gray-900">{analytic.name}</h3>
                      <p className="text-sm font-bold text-gray-600 capitalize">{analytic.type}</p>
                    </div>
                  </div>
                  <ChevronRight className="h-5 w-5 text-gray-400" />
                </div>

                <div className="space-y-3 mb-4">
                  <div className="flex items-center justify-between">
                    <span className="text-sm font-bold text-gray-600">Current Value</span>
                    <span className="text-2xl font-black text-gray-900">
                      {analytic.value.toFixed(1)}
                    </span>
                  </div>
                  <div className="flex items-center justify-between">
                    <span className="text-sm font-bold text-gray-600">Change</span>
                    <div className={`flex items-center space-x-1 ${getChangeColor(analytic.change)}`}>
                      {getChangeIcon(analytic.change)}
                      <span className="text-sm font-bold">
                        {analytic.change >= 0 ? '+' : ''}{analytic.change.toFixed(1)}%
                      </span>
                    </div>
                  </div>
                  <div className="flex items-center justify-between">
                    <span className="text-sm font-bold text-gray-600">Period</span>
                    <span className="text-sm font-black text-gray-900">{analytic.period}</span>
                  </div>
                </div>

                {/* Simple Chart Preview */}
                <div className="h-16 bg-gray-50 border-2 border-gray-200 rounded-lg p-2 mb-4">
                  <div className="flex items-end justify-between h-full space-x-1">
                    {analytic.data.values.map((value, index) => (
                      <div
                        key={index}
                        className="bg-blue-500 rounded-t"
                        style={{
                          width: '20%',
                          height: `${(value / Math.max(...analytic.data.values)) * 100}%`
                        }}
                      ></div>
                    ))}
                  </div>
                </div>

                <div className="flex items-center justify-between">
                  <div className="flex items-center space-x-2">
                    <Clock className="h-4 w-4 text-gray-400" />
                    <span className="text-xs font-bold text-gray-500">Updated now</span>
                  </div>
                  <div className="flex space-x-1">
                    <div className="w-2 h-2 rounded-full bg-green-500"></div>
                    <div className="w-2 h-2 rounded-full bg-blue-500"></div>
                    <div className="w-2 h-2 rounded-full bg-purple-500"></div>
                  </div>
                </div>
              </div>
            )
          })}
        </div>
      ) : (
        <div className="text-center py-12">
          <BarChart3 className="h-16 w-16 text-gray-400 mx-auto mb-4" />
          <h3 className="text-lg font-black text-gray-900 mb-2">No Analytics Found</h3>
          <p className="text-gray-600 font-bold">Try adjusting your search criteria or create a new report.</p>
        </div>
      )}

      {/* Analytics Details Modal */}
      {selectedAnalytic && (
        <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center p-4 z-50">
          <div className="bg-white border-2 border-black rounded-lg p-8 shadow-4px-4px-0px-black max-w-4xl w-full max-h-[90vh] overflow-y-auto">
            <div className="flex items-center justify-between mb-6">
              <h2 className="text-2xl font-black text-gray-900 flex items-center">
                <BarChart3 className="h-6 w-6 mr-3 text-blue-600" />
                {selectedAnalytic.name}
              </h2>
              <button
                onClick={() => setSelectedAnalytic(null)}
                className="p-2 rounded-lg border-2 border-black hover:bg-gray-50 shadow-2px-2px-0px-black transition-all duration-200"
              >
                <X className="h-5 w-5 text-gray-700" />
              </button>
            </div>

            <div className="grid grid-cols-1 lg:grid-cols-2 gap-8">
              {/* Analytics Information */}
              <div className="space-y-6">
                <div>
                  <h3 className="text-lg font-black text-gray-900 mb-4 flex items-center">
                    <Info className="h-5 w-5 mr-2 text-blue-600" />
                    Analytics Information
                  </h3>
                  <div className="space-y-3">
                    <div className="flex justify-between">
                      <span className="font-bold text-gray-600">Type:</span>
                      <span className="font-black text-gray-900 capitalize">{selectedAnalytic.type}</span>
                    </div>
                    <div className="flex justify-between">
                      <span className="font-bold text-gray-600">Current Value:</span>
                      <span className="text-2xl font-black text-gray-900">{selectedAnalytic.value.toFixed(1)}</span>
                    </div>
                    <div className="flex justify-between">
                      <span className="font-bold text-gray-600">Change:</span>
                      <div className={`flex items-center space-x-2 ${getChangeColor(selectedAnalytic.change)}`}>
                        {getChangeIcon(selectedAnalytic.change)}
                        <span className="font-black">
                          {selectedAnalytic.change >= 0 ? '+' : ''}{selectedAnalytic.change.toFixed(1)}%
                        </span>
                      </div>
                    </div>
                    <div className="flex justify-between">
                      <span className="font-bold text-gray-600">Period:</span>
                      <span className="font-black text-gray-900">{selectedAnalytic.period}</span>
                    </div>
                  </div>
                </div>

                {/* Insights */}
                <div>
                  <h3 className="text-lg font-black text-gray-900 mb-4 flex items-center">
                    <Sparkles className="h-5 w-5 mr-2 text-yellow-600" />
                    Key Insights
                  </h3>
                  <div className="space-y-2">
                    {selectedAnalytic.insights.map((insight, index) => (
                      <div key={index} className="p-3 bg-yellow-50 border-2 border-yellow-300 rounded-lg">
                        <p className="text-sm font-bold text-yellow-700">{insight}</p>
                      </div>
                    ))}
                  </div>
                </div>
              </div>

              {/* Chart */}
              <div className="space-y-6">
                <div>
                  <h3 className="text-lg font-black text-gray-900 mb-4 flex items-center">
                    <LineChart className="h-5 w-5 mr-2 text-green-600" />
                    Trend Analysis
                  </h3>
                  <div className="h-64 bg-gray-50 border-2 border-gray-200 rounded-lg p-4">
                    <div className="flex items-end justify-between h-full space-x-2">
                      {selectedAnalytic.data.values.map((value, index) => (
                        <div key={index} className="flex flex-col items-center space-y-2">
                          <div
                            className="bg-blue-500 rounded-t w-full"
                            style={{
                              height: `${(value / Math.max(...selectedAnalytic.data.values)) * 80}%`
                            }}
                          ></div>
                          <span className="text-xs font-bold text-gray-600">{selectedAnalytic.data.labels[index]}</span>
                          <span className="text-xs font-bold text-gray-900">{value}</span>
                        </div>
                      ))}
                    </div>
                  </div>
                </div>

                {/* Data Points */}
                <div>
                  <h3 className="text-lg font-black text-gray-900 mb-4 flex items-center">
                    <Database className="h-5 w-5 mr-2 text-purple-600" />
                    Data Points
                  </h3>
                  <div className="space-y-2">
                    {selectedAnalytic.data.labels.map((label, index) => (
                      <div key={index} className="flex justify-between p-2 bg-gray-50 border-2 border-gray-200 rounded-lg">
                        <span className="font-bold text-gray-700">{label}</span>
                        <span className="font-black text-gray-900">{selectedAnalytic.data.values[index]}</span>
                      </div>
                    ))}
                  </div>
                </div>
              </div>
            </div>

            {/* Action Buttons */}
            <div className="mt-8 flex justify-center space-x-4">
              <button className="bg-blue-500 text-white border-2 border-black px-6 py-3 rounded-lg font-bold hover:bg-blue-600 shadow-2px-2px-0px-black transition-all duration-200">
                <Download className="h-4 w-4 mr-2" />
                Export Report
              </button>
              <button className="bg-green-500 text-white border-2 border-black px-6 py-3 rounded-lg font-bold hover:bg-green-600 shadow-2px-2px-0px-black transition-all duration-200">
                <Share className="h-4 w-4 mr-2" />
                Share Analytics
              </button>
              <button className="bg-purple-500 text-white border-2 border-black px-6 py-3 rounded-lg font-bold hover:bg-purple-600 shadow-2px-2px-0px-black transition-all duration-200">
                <Settings className="h-4 w-4 mr-2" />
                Configure
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  )
}
