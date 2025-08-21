"use client"

import { useState, useEffect } from 'react'
import { 
  Activity, 
  TrendingUp, 
  TrendingDown, 
  AlertTriangle, 
  CheckCircle, 
  Clock, 
  Eye, 
  Download, 
  Share, 
  Plus, 
  Settings, 
  RefreshCw, 
  Search, 
  Filter, 
  BarChart3,
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
  GitFork
} from "lucide-react"
import { fairmindAPI } from "@/lib/fairmind-api"

interface MonitoringMetric {
  id: string
  name: string
  type: 'performance' | 'security' | 'bias' | 'compliance' | 'availability'
  value: number
  unit: string
  trend: 'up' | 'down' | 'stable'
  status: 'healthy' | 'warning' | 'critical'
  last_updated: string
  threshold: {
    warning: number
    critical: number
  }
}

export default function MonitoringPage() {
  const [metrics, setMetrics] = useState<MonitoringMetric[]>([])
  const [loading, setLoading] = useState(true)
  const [selectedMetric, setSelectedMetric] = useState<MonitoringMetric | null>(null)
  const [searchTerm, setSearchTerm] = useState('')
  const [filterType, setFilterType] = useState('all')

  useEffect(() => {
    loadMonitoringData()
  }, [])

  const loadMonitoringData = async () => {
    try {
      setLoading(true)
      
      // In a real implementation, this would come from the API
      // For now, we'll generate realistic monitoring data
      const datasets = await fairmindAPI.getAvailableDatasets()
      
      const mockMetrics: MonitoringMetric[] = [
        {
          id: 'perf-1',
          name: 'Model Response Time',
          type: 'performance',
          value: Math.random() * 200 + 50,
          unit: 'ms',
          trend: ['up', 'down', 'stable'][Math.floor(Math.random() * 3)] as any,
          status: ['healthy', 'warning', 'critical'][Math.floor(Math.random() * 3)] as any,
          last_updated: new Date().toISOString(),
          threshold: { warning: 150, critical: 300 }
        },
        {
          id: 'sec-1',
          name: 'Security Score',
          type: 'security',
          value: Math.random() * 30 + 70,
          unit: '%',
          trend: ['up', 'down', 'stable'][Math.floor(Math.random() * 3)] as any,
          status: ['healthy', 'warning', 'critical'][Math.floor(Math.random() * 3)] as any,
          last_updated: new Date().toISOString(),
          threshold: { warning: 80, critical: 60 }
        },
        {
          id: 'bias-1',
          name: 'Bias Detection Score',
          type: 'bias',
          value: Math.random() * 40 + 60,
          unit: '%',
          trend: ['up', 'down', 'stable'][Math.floor(Math.random() * 3)] as any,
          status: ['healthy', 'warning', 'critical'][Math.floor(Math.random() * 3)] as any,
          last_updated: new Date().toISOString(),
          threshold: { warning: 75, critical: 50 }
        },
        {
          id: 'comp-1',
          name: 'Compliance Score',
          type: 'compliance',
          value: Math.random() * 20 + 80,
          unit: '%',
          trend: ['up', 'down', 'stable'][Math.floor(Math.random() * 3)] as any,
          status: ['healthy', 'warning', 'critical'][Math.floor(Math.random() * 3)] as any,
          last_updated: new Date().toISOString(),
          threshold: { warning: 85, critical: 70 }
        },
        {
          id: 'avail-1',
          name: 'System Uptime',
          type: 'availability',
          value: Math.random() * 5 + 95,
          unit: '%',
          trend: ['up', 'down', 'stable'][Math.floor(Math.random() * 3)] as any,
          status: ['healthy', 'warning', 'critical'][Math.floor(Math.random() * 3)] as any,
          last_updated: new Date().toISOString(),
          threshold: { warning: 99, critical: 95 }
        },
        {
          id: 'perf-2',
          name: 'Throughput',
          type: 'performance',
          value: Math.random() * 1000 + 500,
          unit: 'req/s',
          trend: ['up', 'down', 'stable'][Math.floor(Math.random() * 3)] as any,
          status: ['healthy', 'warning', 'critical'][Math.floor(Math.random() * 3)] as any,
          last_updated: new Date().toISOString(),
          threshold: { warning: 800, critical: 400 }
        }
      ]
      
      setMetrics(mockMetrics)
    } catch (error) {
      console.error('Error loading monitoring data:', error)
      setMetrics([])
    } finally {
      setLoading(false)
    }
  }

  const filteredMetrics = metrics.filter(metric => {
    const matchesSearch = metric.name.toLowerCase().includes(searchTerm.toLowerCase())
    const matchesFilter = filterType === 'all' || metric.type === filterType
    return matchesSearch && matchesFilter
  })

  const getMetricTypeColor = (type: string) => {
    switch (type) {
      case 'performance': return 'bg-blue-500'
      case 'security': return 'bg-red-500'
      case 'bias': return 'bg-yellow-500'
      case 'compliance': return 'bg-purple-500'
      case 'availability': return 'bg-green-500'
      default: return 'bg-gray-500'
    }
  }

  const getStatusColor = (status: string) => {
    switch (status) {
      case 'healthy': return 'bg-green-500'
      case 'warning': return 'bg-yellow-500'
      case 'critical': return 'bg-red-500'
      default: return 'bg-gray-500'
    }
  }

  const getTrendIcon = (trend: string) => {
    switch (trend) {
      case 'up': return <TrendingUp className="h-4 w-4 text-green-600" />
      case 'down': return <TrendingDown className="h-4 w-4 text-red-600" />
      case 'stable': return <Activity className="h-4 w-4 text-blue-600" />
      default: return <Activity className="h-4 w-4 text-gray-600" />
    }
  }

  const getMetricTypeIcon = (type: string) => {
    switch (type) {
      case 'performance': return Cpu
      case 'security': return Shield
      case 'bias': return Scale
      case 'compliance': return CheckCircle
      case 'availability': return Activity
      default: return Activity
    }
  }

  const getStatusText = (status: string) => {
    switch (status) {
      case 'healthy': return 'Healthy'
      case 'warning': return 'Warning'
      case 'critical': return 'Critical'
      default: return 'Unknown'
    }
  }

  return (
    <div className="space-y-8">
      {/* Header */}
      <div className="bg-gradient-to-r from-blue-50 to-purple-50 border-2 border-black rounded-lg p-8 shadow-4px-4px-0px-black">
        <div className="flex items-center justify-between">
          <div>
            <h1 className="text-3xl font-black text-gray-900 mb-2 flex items-center">
              <Activity className="h-8 w-8 mr-3 text-blue-600" />
              Real-Time Monitoring
            </h1>
            <p className="text-lg font-bold text-gray-600 mb-4">
              Monitor AI model performance, security, bias, and compliance metrics.
            </p>
            <div className="flex items-center space-x-4">
              <div className="flex items-center space-x-2 bg-blue-100 border-2 border-black px-3 py-1 rounded-lg">
                <Activity className="h-4 w-4 text-blue-800" />
                <span className="text-sm font-bold text-blue-800">{metrics.length} Metrics</span>
              </div>
              <div className="flex items-center space-x-2 bg-green-100 border-2 border-black px-3 py-1 rounded-lg">
                <Clock className="h-4 w-4 text-green-800" />
                <span className="text-sm font-bold text-green-800">Real-time</span>
              </div>
              <button 
                onClick={loadMonitoringData}
                disabled={loading}
                className="flex items-center space-x-2 bg-white border-2 border-black px-3 py-1 rounded-lg hover:bg-gray-50 shadow-2px-2px-0px-black transition-all duration-200 disabled:opacity-50"
              >
                <RefreshCw className={`h-4 w-4 text-gray-700 ${loading ? 'animate-spin' : ''}`} />
                <span className="text-sm font-bold text-gray-700">Refresh</span>
              </button>
            </div>
          </div>
          <div className="hidden md:block">
            <div className="w-20 h-20 bg-gradient-to-br from-green-600 to-blue-600 rounded-lg border-2 border-black shadow-4px-4px-0px-black flex items-center justify-center">
              <Activity className="h-10 w-10 text-white" />
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
                placeholder="Search metrics by name..."
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
              <option value="security">Security</option>
              <option value="bias">Bias</option>
              <option value="compliance">Compliance</option>
              <option value="availability">Availability</option>
            </select>
            <button className="bg-blue-500 text-white border-2 border-black px-6 py-3 rounded-lg font-bold hover:bg-blue-600 shadow-2px-2px-0px-black transition-all duration-200">
              <Plus className="h-4 w-4 mr-2" />
              Add Metric
            </button>
          </div>
        </div>
      </div>

      {/* Metrics Grid */}
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
      ) : filteredMetrics.length > 0 ? (
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
          {filteredMetrics.map((metric) => {
            const IconComponent = getMetricTypeIcon(metric.type)
            return (
              <div
                key={metric.id}
                onClick={() => setSelectedMetric(metric)}
                className="bg-white border-2 border-black rounded-lg p-6 shadow-4px-4px-0px-black cursor-pointer hover:shadow-6px-6px-0px-black transition-all duration-200"
              >
                <div className="flex items-center justify-between mb-4">
                  <div className="flex items-center space-x-3">
                    <div className={`p-2 rounded-lg border-2 border-black ${getMetricTypeColor(metric.type)}`}>
                      <IconComponent className="h-5 w-5 text-white" />
                    </div>
                    <div>
                      <h3 className="font-black text-gray-900">{metric.name}</h3>
                      <p className="text-sm font-bold text-gray-600 capitalize">{metric.type}</p>
                    </div>
                  </div>
                  <div className={`w-3 h-3 rounded-full ${getStatusColor(metric.status)}`}></div>
                </div>

                <div className="space-y-3 mb-4">
                  <div className="flex items-center justify-between">
                    <span className="text-sm font-bold text-gray-600">Current Value</span>
                    <span className="text-2xl font-black text-gray-900">
                      {metric.value.toFixed(1)}{metric.unit}
                    </span>
                  </div>
                  <div className="flex items-center justify-between">
                    <span className="text-sm font-bold text-gray-600">Status</span>
                    <span className={`px-2 py-1 rounded text-xs font-bold ${getStatusColor(metric.status)} text-white`}>
                      {getStatusText(metric.status)}
                    </span>
                  </div>
                  <div className="flex items-center justify-between">
                    <span className="text-sm font-bold text-gray-600">Trend</span>
                    <div className="flex items-center space-x-1">
                      {getTrendIcon(metric.trend)}
                      <span className="text-sm font-bold text-gray-600 capitalize">{metric.trend}</span>
                    </div>
                  </div>
                </div>

                <div className="flex items-center justify-between">
                  <div className="flex items-center space-x-2">
                    <Clock className="h-4 w-4 text-gray-400" />
                    <span className="text-xs font-bold text-gray-500">
                      {new Date(metric.last_updated).toLocaleTimeString()}
                    </span>
                  </div>
                  <ChevronRight className="h-4 w-4 text-gray-400" />
                </div>
              </div>
            )
          })}
        </div>
      ) : (
        <div className="text-center py-12">
          <Activity className="h-16 w-16 text-gray-400 mx-auto mb-4" />
          <h3 className="text-lg font-black text-gray-900 mb-2">No Metrics Found</h3>
          <p className="text-gray-600 font-bold">Try adjusting your search criteria or add a new metric.</p>
        </div>
      )}

      {/* Metric Details Modal */}
      {selectedMetric && (
        <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center p-4 z-50">
          <div className="bg-white border-2 border-black rounded-lg p-8 shadow-4px-4px-0px-black max-w-2xl w-full">
            <div className="flex items-center justify-between mb-6">
              <h2 className="text-2xl font-black text-gray-900 flex items-center">
                <Activity className="h-6 w-6 mr-3 text-blue-600" />
                {selectedMetric.name}
              </h2>
              <button
                onClick={() => setSelectedMetric(null)}
                className="p-2 rounded-lg border-2 border-black hover:bg-gray-50 shadow-2px-2px-0px-black transition-all duration-200"
              >
                <X className="h-5 w-5 text-gray-700" />
              </button>
            </div>

            <div className="space-y-6">
              <div>
                <h3 className="text-lg font-black text-gray-900 mb-4 flex items-center">
                  <Info className="h-5 w-5 mr-2 text-blue-600" />
                  Metric Information
                </h3>
                <div className="space-y-3">
                  <div className="flex justify-between">
                    <span className="font-bold text-gray-600">Type:</span>
                    <span className="font-black text-gray-900 capitalize">{selectedMetric.type}</span>
                  </div>
                  <div className="flex justify-between">
                    <span className="font-bold text-gray-600">Current Value:</span>
                    <span className="text-xl font-black text-gray-900">
                      {selectedMetric.value.toFixed(1)} {selectedMetric.unit}
                    </span>
                  </div>
                  <div className="flex justify-between">
                    <span className="font-bold text-gray-600">Status:</span>
                    <span className={`font-black px-2 py-1 rounded text-sm ${getStatusColor(selectedMetric.status)} text-white`}>
                      {getStatusText(selectedMetric.status)}
                    </span>
                  </div>
                  <div className="flex justify-between">
                    <span className="font-bold text-gray-600">Trend:</span>
                    <div className="flex items-center space-x-2">
                      {getTrendIcon(selectedMetric.trend)}
                      <span className="font-black text-gray-900 capitalize">{selectedMetric.trend}</span>
                    </div>
                  </div>
                </div>
              </div>

              <div>
                <h3 className="text-lg font-black text-gray-900 mb-4 flex items-center">
                  <AlertTriangle className="h-5 w-5 mr-2 text-yellow-600" />
                  Thresholds
                </h3>
                <div className="space-y-3">
                  <div className="flex justify-between">
                    <span className="font-bold text-gray-600">Warning Threshold:</span>
                    <span className="font-black text-yellow-600">{selectedMetric.threshold.warning} {selectedMetric.unit}</span>
                  </div>
                  <div className="flex justify-between">
                    <span className="font-bold text-gray-600">Critical Threshold:</span>
                    <span className="font-black text-red-600">{selectedMetric.threshold.critical} {selectedMetric.unit}</span>
                  </div>
                </div>
              </div>

              <div>
                <h3 className="text-lg font-black text-gray-900 mb-4 flex items-center">
                  <Clock className="h-5 w-5 mr-2 text-gray-600" />
                  Last Updated
                </h3>
                <p className="font-bold text-gray-700">
                  {new Date(selectedMetric.last_updated).toLocaleString()}
                </p>
              </div>
            </div>

            {/* Action Buttons */}
            <div className="mt-8 flex justify-center space-x-4">
              <button className="bg-blue-500 text-white border-2 border-black px-6 py-3 rounded-lg font-bold hover:bg-blue-600 shadow-2px-2px-0px-black transition-all duration-200">
                <Eye className="h-4 w-4 mr-2" />
                View History
              </button>
              <button className="bg-green-500 text-white border-2 border-black px-6 py-3 rounded-lg font-bold hover:bg-green-600 shadow-2px-2px-0px-black transition-all duration-200">
                <Download className="h-4 w-4 mr-2" />
                Export Data
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
