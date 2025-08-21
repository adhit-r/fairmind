"use client"

import { useState, useEffect } from 'react'
import { useAuth } from "@/contexts/auth-context"
import { ProtectedRoute } from "@/components/core/auth/protected-route"
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/common/card"
import { Button } from "@/components/ui/common/button"
import { Badge } from "@/components/ui/common/badge"
import { Input } from "@/components/ui/common/input"
import { modelRegistryService, Model, ModelRegistryStats } from "@/lib/model-registry-service"
import {
  Brain,
  Upload,
  Search,
  Filter,
  Eye,
  Edit,
  Trash2,
  Plus,
  Database,
  Shield,
  Target,
  Clock,
  User,
  AlertTriangle,
  CheckCircle,
  Loader2
} from "lucide-react"

export default function ModelRegistryPage() {
  const { user } = useAuth()
  const [searchTerm, setSearchTerm] = useState('')
  const [selectedType, setSelectedType] = useState('all')
  const [selectedStatus, setSelectedStatus] = useState('all')
  const [models, setModels] = useState<Model[]>([])
  const [stats, setStats] = useState<ModelRegistryStats | null>(null)
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)

  // Get organization ID from user context
  const orgId = user?.organization_id || 'demo_org'

  useEffect(() => {
    loadData()
  }, [orgId])

  const loadData = async () => {
    try {
      setLoading(true)
      setError(null)
      
      const [modelsData, statsData] = await Promise.all([
        modelRegistryService.getModels(orgId),
        modelRegistryService.getStats(orgId)
      ])
      
      setModels(modelsData)
      setStats(statsData)
    } catch (err) {
      console.error('Error loading model registry data:', err)
      setError('Failed to load model registry data')
    } finally {
      setLoading(false)
    }
  }

  const filteredModels = models.filter(model => {
    const matchesSearch = model.name.toLowerCase().includes(searchTerm.toLowerCase()) ||
                         model.description.toLowerCase().includes(searchTerm.toLowerCase()) ||
                         model.tags.some(tag => tag.toLowerCase().includes(searchTerm.toLowerCase())) ||
                         model.use_case?.toLowerCase().includes(searchTerm.toLowerCase())
    const matchesType = selectedType === 'all' || model.type === selectedType
    const matchesStatus = selectedStatus === 'all' || modelRegistryService.getDisplayStatus(model) === selectedStatus
    
    return matchesSearch && matchesType && matchesStatus
  })

  const getStatusColor = (status: string) => {
    return modelRegistryService.getStatusColor(status)
  }

  const getRiskColor = (risk: string) => {
    return modelRegistryService.getRiskLevelColor(risk)
  }

  if (loading) {
    return (
      <ProtectedRoute>
        <div className="space-y-8 p-6 bg-gray-50 min-h-screen">
          <div className="flex items-center justify-center h-64">
            <div className="text-center">
              <Loader2 className="h-8 w-8 animate-spin mx-auto mb-4 text-blue-600" />
              <p className="text-gray-600">Loading model registry...</p>
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
              <h3 className="text-lg font-bold text-red-900 mb-2">Error Loading Data</h3>
              <p className="text-red-700 mb-4">{error}</p>
              <Button onClick={loadData} className="bg-red-600 hover:bg-red-700 text-white">
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
        {/* Header */}
        <div className="bg-white border-2 border-black shadow-4px-4px-0px-black rounded-lg p-6">
          <div className="flex items-center justify-between">
            <div>
              <h1 className="text-3xl font-bold text-gray-900 mb-2">Model Registry</h1>
              <p className="text-gray-700 text-lg">
                Manage your AI models for <span className="font-semibold text-blue-700">{user?.organization_name}</span>
              </p>
            </div>
            <Button className="border-2 border-black shadow-2px-2px-0px-black hover:shadow-4px-4px-0px-black transition-all duration-200 bg-blue-600 hover:bg-blue-700 text-white font-semibold">
              <Upload className="h-4 w-4 mr-2" />
              Upload Model
            </Button>
          </div>
        </div>

        {/* Stats */}
        {stats && (
          <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
            <Card className="border-2 border-black shadow-4px-4px-0px-black bg-white">
              <CardContent className="p-4">
                <div className="flex items-center space-x-3">
                  <div className="p-3 bg-blue-100 rounded-lg border-2 border-blue-300">
                    <Database className="h-6 w-6 text-blue-700" />
                  </div>
                  <div>
                    <p className="text-2xl font-bold text-gray-900">{stats.totalModels}</p>
                    <p className="text-sm font-semibold text-gray-700">Total Models</p>
                  </div>
                </div>
              </CardContent>
            </Card>
            <Card className="border-2 border-black shadow-4px-4px-0px-black bg-white">
              <CardContent className="p-4">
                <div className="flex items-center space-x-3">
                  <div className="p-3 bg-green-100 rounded-lg border-2 border-green-300">
                    <CheckCircle className="h-6 w-6 text-green-700" />
                  </div>
                  <div>
                    <p className="text-2xl font-bold text-gray-900">{stats.activeModels}</p>
                    <p className="text-sm font-semibold text-gray-700">Active Models</p>
                  </div>
                </div>
              </CardContent>
            </Card>
            <Card className="border-2 border-black shadow-4px-4px-0px-black bg-white">
              <CardContent className="p-4">
                <div className="flex items-center space-x-3">
                  <div className="p-3 bg-orange-100 rounded-lg border-2 border-orange-300">
                    <AlertTriangle className="h-6 w-6 text-orange-700" />
                  </div>
                  <div>
                    <p className="text-2xl font-bold text-gray-900">{stats.highRiskModels}</p>
                    <p className="text-sm font-semibold text-gray-700">High Risk</p>
                  </div>
                </div>
              </CardContent>
            </Card>
            <Card className="border-2 border-black shadow-4px-4px-0px-black bg-white">
              <CardContent className="p-4">
                <div className="flex items-center space-x-3">
                  <div className="p-3 bg-purple-100 rounded-lg border-2 border-purple-300">
                    <Shield className="h-6 w-6 text-purple-700" />
                  </div>
                  <div>
                    <p className="text-2xl font-bold text-gray-900">{stats.complianceScore}%</p>
                    <p className="text-sm font-semibold text-gray-700">Compliance</p>
                  </div>
                </div>
              </CardContent>
            </Card>
          </div>
        )}

        {/* Filters */}
        <Card className="border-2 border-black shadow-4px-4px-0px-black bg-white">
          <CardContent className="p-6">
            <div className="flex flex-col md:flex-row gap-4">
              <div className="flex-1">
                <div className="relative">
                  <Search className="absolute left-3 top-1/2 transform -translate-y-1/2 h-4 w-4 text-gray-400" />
                  <Input
                    placeholder="Search models..."
                    value={searchTerm}
                    onChange={(e) => setSearchTerm(e.target.value)}
                    className="pl-10 border-2 border-gray-300 focus:border-blue-500 focus:ring-2 focus:ring-blue-200"
                  />
                </div>
              </div>
              <div className="flex gap-2">
                <select
                  value={selectedType}
                  onChange={(e) => setSelectedType(e.target.value)}
                  className="px-4 py-2 border-2 border-gray-300 rounded-lg bg-white font-medium text-gray-700 focus:border-blue-500 focus:ring-2 focus:ring-blue-200"
                >
                  <option value="all">All Types</option>
                  <option value="classification">Classification</option>
                  <option value="regression">Regression</option>
                  <option value="clustering">Clustering</option>
                  <option value="nlp">NLP</option>
                  <option value="llm">LLM</option>
                  <option value="recommendation">Recommendation</option>
                  <option value="time_series">Time Series</option>
                </select>
                <select
                  value={selectedStatus}
                  onChange={(e) => setSelectedStatus(e.target.value)}
                  className="px-4 py-2 border-2 border-gray-300 rounded-lg bg-white font-medium text-gray-700 focus:border-blue-500 focus:ring-2 focus:ring-blue-200"
                >
                  <option value="all">All Status</option>
                  <option value="active">Active</option>
                  <option value="testing">Testing</option>
                  <option value="inactive">Inactive</option>
                </select>
              </div>
            </div>
          </CardContent>
        </Card>

        {/* Models Grid */}
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
          {filteredModels.map((model) => (
            <Card key={model.id} className="border-2 border-black shadow-4px-4px-0px-black bg-white hover:shadow-6px-6px-0px-black transition-all duration-200">
              <CardHeader className="bg-gray-50 border-b-2 border-gray-200">
                <div className="flex items-start justify-between">
                  <div className="flex-1">
                    <CardTitle className="text-lg font-bold text-gray-900 mb-1">{model.name}</CardTitle>
                    <CardDescription className="text-gray-700 font-medium">
                      {model.description}
                    </CardDescription>
                  </div>
                  <div className="flex space-x-1">
                    <Button variant="ghost" size="sm" className="p-2 hover:bg-gray-200">
                      <Eye className="h-4 w-4 text-gray-600" />
                    </Button>
                    <Button variant="ghost" size="sm" className="p-2 hover:bg-gray-200">
                      <Edit className="h-4 w-4 text-gray-600" />
                    </Button>
                    <Button variant="ghost" size="sm" className="p-2 hover:bg-gray-200">
                      <Trash2 className="h-4 w-4 text-gray-600" />
                    </Button>
                  </div>
                </div>
              </CardHeader>
              <CardContent className="p-6 space-y-4">
                <div className="grid grid-cols-2 gap-4 text-sm">
                  <div>
                    <span className="text-gray-600 font-medium">Version:</span>
                    <span className="font-semibold text-gray-900 ml-2">{model.version}</span>
                  </div>
                  <div>
                    <span className="text-gray-600 font-medium">Framework:</span>
                    <span className="font-semibold text-gray-900 ml-2">{model.framework}</span>
                  </div>
                  <div>
                    <span className="text-gray-600 font-medium">Type:</span>
                    <span className="font-semibold text-gray-900 ml-2 capitalize">{model.type}</span>
                  </div>
                  <div>
                    <span className="text-gray-600 font-medium">Status:</span>
                    <Badge className={`text-xs font-semibold border-2 ${getStatusColor(modelRegistryService.getDisplayStatus(model))} ml-2`}>
                      {modelRegistryService.getDisplayStatus(model)}
                    </Badge>
                  </div>
                </div>
                
                {model.use_case && (
                  <div>
                    <span className="text-gray-600 font-medium text-sm">Use Case:</span>
                    <p className="text-sm font-semibold text-gray-900 mt-1">{model.use_case}</p>
                  </div>
                )}
                
                <div className="flex items-center justify-between">
                  <Badge className={`text-xs font-semibold border-2 ${getRiskColor(model.risk_level)}`}>
                    {model.risk_level} risk
                  </Badge>
                </div>

                <div className="flex flex-wrap gap-1">
                  {model.tags.map((tag, index) => (
                    <Badge key={index} variant="outline" className="text-xs font-medium border-2 border-gray-300 bg-gray-50 text-gray-700">
                      {tag}
                    </Badge>
                  ))}
                </div>

                <div className="pt-3 border-t border-gray-200">
                  <div className="flex items-center justify-between text-xs text-gray-500">
                    <div className="flex items-center space-x-1">
                      <User className="h-3 w-3" />
                      <span className="font-medium">{model.company}</span>
                    </div>
                    <div className="flex items-center space-x-1">
                      <Clock className="h-3 w-3" />
                      <span className="font-medium">{modelRegistryService.formatTimeAgo(new Date(model.created_at))}</span>
                    </div>
                  </div>
                </div>

                <div className="flex space-x-2 pt-3">
                  <Button size="sm" className="flex-1 border-2 border-black shadow-2px-2px-0px-black bg-green-600 hover:bg-green-700 text-white font-semibold">
                    <Target className="h-4 w-4 mr-1" />
                    Analyze
                  </Button>
                  <Button size="sm" variant="outline" className="flex-1 border-2 border-gray-300 bg-white hover:bg-gray-50 font-semibold">
                    <Shield className="h-4 w-4 mr-1" />
                    Test
                  </Button>
                </div>
              </CardContent>
            </Card>
          ))}
        </div>

        {filteredModels.length === 0 && (
          <Card className="border-2 border-black shadow-4px-4px-0px-black bg-white">
            <CardContent className="p-12 text-center">
              <div className="p-4 bg-gray-100 rounded-lg border-2 border-gray-300 w-16 h-16 mx-auto mb-4 flex items-center justify-center">
                <Brain className="h-8 w-8 text-gray-400" />
              </div>
              <h3 className="text-lg font-bold text-gray-900 mb-2">No models found</h3>
              <p className="text-gray-600 mb-6">
                {searchTerm || selectedType !== 'all' || selectedStatus !== 'all' 
                  ? 'Try adjusting your search or filter criteria'
                  : 'Get started by uploading your first AI model'
                }
              </p>
              <Button className="border-2 border-black shadow-2px-2px-0px-black hover:shadow-4px-4px-0px-black transition-all duration-200 bg-blue-600 hover:bg-blue-700 text-white font-semibold">
                <Plus className="h-4 w-4 mr-2" />
                Upload Your First Model
              </Button>
            </CardContent>
          </Card>
        )}
      </div>
    </ProtectedRoute>
  )
}
