'use client'

import React, { useState, useEffect } from 'react'
import { useRouter } from 'next/navigation'
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
  GitFork,
  ArrowLeft
} from 'lucide-react'
import { PageWrapper } from '@/components/core/PageWrapper'
import { Card } from '@/components/core/Card'
import { Button } from '@/components/core/Button'

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
  icon: React.ReactNode
}

const demoMetrics: MonitoringMetric[] = [
  {
    id: '1',
    name: 'Model Performance',
    type: 'performance',
    value: 94.2,
    unit: '%',
    trend: 'up',
    status: 'healthy',
    last_updated: '2024-01-17T10:00:00Z',
    threshold: { warning: 85, critical: 75 },
    icon: <BarChart3 className="h-5 w-5" />
  },
  {
    id: '2',
    name: 'Security Score',
    type: 'security',
    value: 96.8,
    unit: '%',
    trend: 'up',
    status: 'healthy',
    last_updated: '2024-01-17T10:00:00Z',
    threshold: { warning: 90, critical: 80 },
    icon: <Shield className="h-5 w-5" />
  },
  {
    id: '3',
    name: 'Bias Detection',
    type: 'bias',
    value: 88.5,
    unit: '%',
    trend: 'down',
    status: 'warning',
    last_updated: '2024-01-17T10:00:00Z',
    threshold: { warning: 90, critical: 85 },
    icon: <Scale className="h-5 w-5" />
  },
  {
    id: '4',
    name: 'System Availability',
    type: 'availability',
    value: 99.9,
    unit: '%',
    trend: 'stable',
    status: 'healthy',
    last_updated: '2024-01-17T10:00:00Z',
    threshold: { warning: 99.5, critical: 99.0 },
    icon: <Activity className="h-5 w-5" />
  },
  {
    id: '5',
    name: 'Compliance Score',
    type: 'compliance',
    value: 92.1,
    unit: '%',
    trend: 'up',
    status: 'healthy',
    last_updated: '2024-01-17T10:00:00Z',
    threshold: { warning: 85, critical: 75 },
    icon: <CheckCircle className="h-5 w-5" />
  },
  {
    id: '6',
    name: 'API Response Time',
    type: 'performance',
    value: 245,
    unit: 'ms',
    trend: 'down',
    status: 'warning',
    last_updated: '2024-01-17T10:00:00Z',
    threshold: { warning: 300, critical: 500 },
    icon: <Zap className="h-5 w-5" />
  }
]

export default function MonitoringPage() {
  const router = useRouter()
  const [metrics, setMetrics] = useState<MonitoringMetric[]>(demoMetrics)
  const [loading, setLoading] = useState(true)
  const [selectedMetric, setSelectedMetric] = useState<MonitoringMetric | null>(null)
  const [searchTerm, setSearchTerm] = useState('')
  const [filterType, setFilterType] = useState('all')

  useEffect(() => {
    // Simulate loading
    setTimeout(() => {
      setLoading(false)
    }, 1000)
  }, [])

  const handleBack = () => {
    router.push('/')
  }

  const getStatusColor = (status: string) => {
    switch (status) {
      case 'healthy':
        return 'bg-green-500/10 text-green-400 border-green-500/20'
      case 'warning':
        return 'bg-yellow-500/10 text-yellow-400 border-yellow-500/20'
      case 'critical':
        return 'bg-red-500/10 text-red-400 border-red-500/20'
      default:
        return 'bg-slate-500/10 text-slate-400 border-slate-500/20'
    }
  }

  const getStatusIcon = (status: string) => {
    switch (status) {
      case 'healthy':
        return <CheckCircle className="h-4 w-4 text-green-400" />
      case 'warning':
        return <AlertTriangle className="h-4 w-4 text-yellow-400" />
      case 'critical':
        return <AlertTriangle className="h-4 w-4 text-red-400" />
      default:
        return <Clock className="h-4 w-4 text-slate-400" />
    }
  }

  const getTrendIcon = (trend: string) => {
    switch (trend) {
      case 'up':
        return <TrendingUp className="h-4 w-4 text-green-400" />
      case 'down':
        return <TrendingDown className="h-4 w-4 text-red-400" />
      default:
        return <div className="h-4 w-4" />
    }
  }

  const getValueColor = (metric: MonitoringMetric) => {
    if (metric.status === 'critical') return 'text-red-400'
    if (metric.status === 'warning') return 'text-yellow-400'
    return 'text-green-400'
  }

  const filteredMetrics = metrics.filter(metric => {
    const matchesSearch = metric.name.toLowerCase().includes(searchTerm.toLowerCase())
    const matchesFilter = filterType === 'all' || metric.type === filterType
    return matchesSearch && matchesFilter
  })

  if (loading) {
    return (
      <PageWrapper title="Monitoring" subtitle="Loading monitoring data...">
        <div className="flex items-center justify-center py-12">
          <div className="text-center">
            <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-blue-500 mx-auto mb-4"></div>
            <p className="text-slate-400">Loading Monitoring Data...</p>
          </div>
        </div>
      </PageWrapper>
    )
  }

  return (
    <PageWrapper title="Model Monitoring" subtitle="Real-time monitoring of model performance, security, and compliance">
      <div className="mb-6">
        <Button 
          variant="ghost" 
          icon={ArrowLeft}
          onClick={handleBack}
        >
          Back to Dashboard
        </Button>
      </div>

      {/* Search and Filter */}
      <Card className="mb-8">
        <div className="flex flex-col md:flex-row gap-4">
          <div className="flex-1 relative">
            <Search className="absolute left-3 top-1/2 transform -translate-y-1/2 h-4 w-4 text-slate-400" />
            <input
              type="text"
              placeholder="Search metrics..."
              value={searchTerm}
              onChange={(e) => setSearchTerm(e.target.value)}
              className="w-full pl-10 pr-4 py-2 bg-slate-800/50 border border-white/10 rounded-xl text-white placeholder-slate-400 focus:outline-none focus:ring-2 focus:ring-blue-500/50"
            />
          </div>
          <select
            value={filterType}
            onChange={(e) => setFilterType(e.target.value)}
            className="px-4 py-2 bg-slate-800/50 border border-white/10 rounded-xl text-white focus:outline-none focus:ring-2 focus:ring-blue-500/50"
          >
            <option value="all">All Types</option>
            <option value="performance">Performance</option>
            <option value="security">Security</option>
            <option value="bias">Bias</option>
            <option value="compliance">Compliance</option>
            <option value="availability">Availability</option>
          </select>
          <Button variant="outline" icon={RefreshCw}>
            Refresh
          </Button>
        </div>
      </Card>

      {/* Metrics Grid */}
             <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6 mb-8">
         {filteredMetrics.map((metric) => (
           <div 
             key={metric.id} 
             className="cursor-pointer group"
             onClick={() => setSelectedMetric(metric)}
           >
             <Card hover>
            <div className="flex items-start justify-between mb-4">
              <div className="w-10 h-10 bg-gradient-to-r from-blue-500 to-purple-600 rounded-xl flex items-center justify-center">
                {metric.icon}
              </div>
              <div className="flex items-center space-x-2">
                {getTrendIcon(metric.trend)}
                <div className={`px-2 py-1 rounded-lg border text-xs font-medium ${getStatusColor(metric.status)}`}>
                  <div className="flex items-center space-x-1">
                    {getStatusIcon(metric.status)}
                    <span className="capitalize">{metric.status}</span>
                  </div>
                </div>
              </div>
            </div>

            <h3 className="text-lg font-semibold text-white mb-1">{metric.name}</h3>
            <div className="flex items-baseline space-x-2 mb-2">
              <span className={`text-2xl font-bold ${getValueColor(metric)}`}>
                {metric.value}{metric.unit}
              </span>
              <span className="text-sm text-slate-400">
                {metric.type}
              </span>
            </div>

            <div className="flex items-center justify-between text-xs text-slate-500">
              <span>Last updated: {new Date(metric.last_updated).toLocaleTimeString()}</span>
              <div className="flex items-center space-x-1 text-blue-400 group-hover:text-blue-300 transition-colors">
                <Eye className="h-3 w-3" />
                <span>View Details</span>
              </div>
            </div>
          </Card>
        </div>
        ))}
      </div>

      {/* Quick Stats */}
      <div className="grid grid-cols-1 md:grid-cols-4 gap-6 mb-8">
        <Card>
          <div className="text-center">
            <div className="w-12 h-12 bg-green-500/10 rounded-xl flex items-center justify-center mx-auto mb-3">
              <CheckCircle className="h-6 w-6 text-green-400" />
            </div>
            <h3 className="text-2xl font-bold text-white mb-1">
              {metrics.filter(m => m.status === 'healthy').length}
            </h3>
            <p className="text-sm text-slate-400">Healthy</p>
          </div>
        </Card>

        <Card>
          <div className="text-center">
            <div className="w-12 h-12 bg-yellow-500/10 rounded-xl flex items-center justify-center mx-auto mb-3">
              <AlertTriangle className="h-6 w-6 text-yellow-400" />
            </div>
            <h3 className="text-2xl font-bold text-white mb-1">
              {metrics.filter(m => m.status === 'warning').length}
            </h3>
            <p className="text-sm text-slate-400">Warnings</p>
          </div>
        </Card>

        <Card>
          <div className="text-center">
            <div className="w-12 h-12 bg-red-500/10 rounded-xl flex items-center justify-center mx-auto mb-3">
              <AlertTriangle className="h-6 w-6 text-red-400" />
            </div>
            <h3 className="text-2xl font-bold text-white mb-1">
              {metrics.filter(m => m.status === 'critical').length}
            </h3>
            <p className="text-sm text-slate-400">Critical</p>
          </div>
        </Card>

        <Card>
          <div className="text-center">
            <div className="w-12 h-12 bg-blue-500/10 rounded-xl flex items-center justify-center mx-auto mb-3">
              <Activity className="h-6 w-6 text-blue-400" />
            </div>
            <h3 className="text-2xl font-bold text-white mb-1">
              {metrics.length}
            </h3>
            <p className="text-sm text-slate-400">Total Metrics</p>
          </div>
        </Card>
      </div>

      {/* Quick Actions */}
      <Card title="Quick Actions" icon={<Settings className="h-5 w-5 text-purple-400" />}>
        <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
          <Button variant="outline" className="h-16 flex-col space-y-2">
            <Plus className="h-6 w-6" />
            <span>Add Metric</span>
          </Button>
          <Button variant="outline" className="h-16 flex-col space-y-2">
            <Download className="h-6 w-6" />
            <span>Export Data</span>
          </Button>
          <Button variant="outline" className="h-16 flex-col space-y-2">
            <Settings className="h-6 w-6" />
            <span>Configure Alerts</span>
          </Button>
        </div>
      </Card>
    </PageWrapper>
  )
}
