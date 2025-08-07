"use client"

import { useState, useEffect } from 'react'
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card"
import { Button } from "@/components/ui/button"
import { Badge } from "@/components/ui/badge"
import { Input } from "@/components/ui/input"
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from "@/components/ui/select"
import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/components/ui/tabs"
import { Search, Filter, Download, Upload, Eye, Play, Settings } from "lucide-react"

interface AIModel {
  id: string
  name: string
  version: string
  type: 'LLM' | 'Traditional ML' | 'Computer Vision' | 'NLP' | 'Recommendation'
  status: 'active' | 'inactive' | 'testing' | 'deprecated'
  accuracy: number
  fairness_score: number
  compliance_score: number
  last_updated: string
  description: string
  tags: string[]
  company: string
  risk_level: 'low' | 'medium' | 'high' | 'critical'
  deployment_environment: string
  model_size: string
  training_data: string
  performance_metrics: {
    precision: number
    recall: number
    f1_score: number
    auc: number
  }
}

export function ModelCatalog() {
  const [models, setModels] = useState<AIModel[]>([])
  const [filteredModels, setFilteredModels] = useState<AIModel[]>([])
  const [searchTerm, setSearchTerm] = useState('')
  const [selectedType, setSelectedType] = useState<string>('all')
  const [selectedStatus, setSelectedStatus] = useState<string>('all')
  const [selectedCompany, setSelectedCompany] = useState<string>('all')
  const [loading, setLoading] = useState(true)

  // Mock data - in real app, this would come from API
  const mockModels: AIModel[] = [
    {
      id: 'gpt-4-2024',
      name: 'GPT-4',
      version: '2024',
      type: 'LLM',
      status: 'active',
      accuracy: 94.2,
      fairness_score: 87.5,
      compliance_score: 92.1,
      last_updated: '2024-01-15',
      description: 'Advanced language model for text generation and analysis',
      tags: ['NLP', 'Text Generation', 'Conversational AI'],
      company: 'OpenAI',
      risk_level: 'medium',
      deployment_environment: 'Production',
      model_size: '1.7T parameters',
      training_data: 'Web text, books, articles',
      performance_metrics: {
        precision: 0.92,
        recall: 0.89,
        f1_score: 0.90,
        auc: 0.94
      }
    },
    {
      id: 'claude-3-opus',
      name: 'Claude 3 Opus',
      version: '3.0',
      type: 'LLM',
      status: 'active',
      accuracy: 96.8,
      fairness_score: 91.2,
      compliance_score: 94.7,
      last_updated: '2024-01-10',
      description: 'High-performance language model with enhanced reasoning',
      tags: ['Reasoning', 'Analysis', 'Code Generation'],
      company: 'Anthropic',
      risk_level: 'low',
      deployment_environment: 'Production',
      model_size: '2.1T parameters',
      training_data: 'Diverse text corpus',
      performance_metrics: {
        precision: 0.95,
        recall: 0.93,
        f1_score: 0.94,
        auc: 0.96
      }
    },
    {
      id: 'credit-scoring-v3',
      name: 'Credit Scoring Model',
      version: '3.0',
      type: 'Traditional ML',
      status: 'active',
      accuracy: 89.5,
      fairness_score: 78.3,
      compliance_score: 85.2,
      last_updated: '2024-01-08',
      description: 'Machine learning model for credit risk assessment',
      tags: ['Finance', 'Risk Assessment', 'Credit'],
      company: 'BankCorp',
      risk_level: 'high',
      deployment_environment: 'Production',
      model_size: '500MB',
      training_data: 'Financial records, credit history',
      performance_metrics: {
        precision: 0.88,
        recall: 0.91,
        f1_score: 0.89,
        auc: 0.92
      }
    },
    {
      id: 'fraud-detection-v2',
      name: 'Fraud Detection',
      version: '2.1',
      type: 'Traditional ML',
      status: 'testing',
      accuracy: 92.1,
      fairness_score: 85.7,
      compliance_score: 88.9,
      last_updated: '2024-01-12',
      description: 'Real-time fraud detection for financial transactions',
      tags: ['Security', 'Fraud', 'Real-time'],
      company: 'SecureBank',
      risk_level: 'critical',
      deployment_environment: 'Testing',
      model_size: '750MB',
      training_data: 'Transaction logs, fraud patterns',
      performance_metrics: {
        precision: 0.91,
        recall: 0.93,
        f1_score: 0.92,
        auc: 0.94
      }
    },
    {
      id: 'image-classifier-v1',
      name: 'Image Classifier',
      version: '1.0',
      type: 'Computer Vision',
      status: 'active',
      accuracy: 96.3,
      fairness_score: 89.1,
      compliance_score: 91.5,
      last_updated: '2024-01-05',
      description: 'Computer vision model for image classification',
      tags: ['Computer Vision', 'Image Processing'],
      company: 'VisionTech',
      risk_level: 'medium',
      deployment_environment: 'Production',
      model_size: '2.1GB',
      training_data: 'ImageNet, custom datasets',
      performance_metrics: {
        precision: 0.95,
        recall: 0.94,
        f1_score: 0.94,
        auc: 0.96
      }
    }
  ]

  useEffect(() => {
    // Simulate API call
    setTimeout(() => {
      setModels(mockModels)
      setFilteredModels(mockModels)
      setLoading(false)
    }, 1000)
  }, [])

  useEffect(() => {
    let filtered = models

    // Apply search filter
    if (searchTerm) {
      filtered = filtered.filter(model =>
        model.name.toLowerCase().includes(searchTerm.toLowerCase()) ||
        model.description.toLowerCase().includes(searchTerm.toLowerCase()) ||
        model.tags.some(tag => tag.toLowerCase().includes(searchTerm.toLowerCase()))
      )
    }

    // Apply type filter
    if (selectedType !== 'all') {
      filtered = filtered.filter(model => model.type === selectedType)
    }

    // Apply status filter
    if (selectedStatus !== 'all') {
      filtered = filtered.filter(model => model.status === selectedStatus)
    }

    // Apply company filter
    if (selectedCompany !== 'all') {
      filtered = filtered.filter(model => model.company === selectedCompany)
    }

    setFilteredModels(filtered)
  }, [models, searchTerm, selectedType, selectedStatus, selectedCompany])

  const getStatusColor = (status: string) => {
    switch (status) {
      case 'active': return 'bg-green-500'
      case 'testing': return 'bg-yellow-500'
      case 'inactive': return 'bg-gray-500'
      case 'deprecated': return 'bg-red-500'
      default: return 'bg-gray-500'
    }
  }

  const getRiskColor = (risk: string) => {
    switch (risk) {
      case 'low': return 'bg-green-100 text-green-800'
      case 'medium': return 'bg-yellow-100 text-yellow-800'
      case 'high': return 'bg-orange-100 text-orange-800'
      case 'critical': return 'bg-red-100 text-red-800'
      default: return 'bg-gray-100 text-gray-800'
    }
  }

  const handleModelSelect = (modelId: string) => {
    // Handle model selection for testing/activities
    console.log('Selected model:', modelId)
  }

  if (loading) {
    return (
      <div className="flex items-center justify-center h-64">
        <div className="text-muted-foreground">Loading model catalog...</div>
      </div>
    )
  }

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div>
          <h2 className="text-2xl font-bold text-foreground">Model Catalog</h2>
          <p className="text-muted-foreground">
            Browse and select AI models for testing and governance activities
          </p>
        </div>
        <div className="flex items-center space-x-2">
          <Button variant="outline" size="sm">
            <Upload className="mr-2 h-4 w-4" />
            Upload Model
          </Button>
          <Button variant="outline" size="sm">
            <Download className="mr-2 h-4 w-4" />
            Export
          </Button>
        </div>
      </div>

      {/* Filters */}
      <Card>
        <CardHeader>
          <CardTitle className="text-lg">Filters</CardTitle>
        </CardHeader>
        <CardContent>
          <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
            <div className="space-y-2">
              <label className="text-sm font-medium">Search</label>
              <div className="relative">
                <Search className="absolute left-3 top-3 h-4 w-4 text-muted-foreground" />
                <Input
                  placeholder="Search models..."
                  value={searchTerm}
                  onChange={(e) => setSearchTerm(e.target.value)}
                  className="pl-10"
                />
              </div>
            </div>
            <div className="space-y-2">
              <label className="text-sm font-medium">Type</label>
              <Select value={selectedType} onValueChange={setSelectedType}>
                <SelectTrigger>
                  <SelectValue />
                </SelectTrigger>
                <SelectContent>
                  <SelectItem value="all">All Types</SelectItem>
                  <SelectItem value="LLM">LLM</SelectItem>
                  <SelectItem value="Traditional ML">Traditional ML</SelectItem>
                  <SelectItem value="Computer Vision">Computer Vision</SelectItem>
                  <SelectItem value="NLP">NLP</SelectItem>
                  <SelectItem value="Recommendation">Recommendation</SelectItem>
                </SelectContent>
              </Select>
            </div>
            <div className="space-y-2">
              <label className="text-sm font-medium">Status</label>
              <Select value={selectedStatus} onValueChange={setSelectedStatus}>
                <SelectTrigger>
                  <SelectValue />
                </SelectTrigger>
                <SelectContent>
                  <SelectItem value="all">All Status</SelectItem>
                  <SelectItem value="active">Active</SelectItem>
                  <SelectItem value="testing">Testing</SelectItem>
                  <SelectItem value="inactive">Inactive</SelectItem>
                  <SelectItem value="deprecated">Deprecated</SelectItem>
                </SelectContent>
              </Select>
            </div>
            <div className="space-y-2">
              <label className="text-sm font-medium">Company</label>
              <Select value={selectedCompany} onValueChange={setSelectedCompany}>
                <SelectTrigger>
                  <SelectValue />
                </SelectTrigger>
                <SelectContent>
                  <SelectItem value="all">All Companies</SelectItem>
                  <SelectItem value="OpenAI">OpenAI</SelectItem>
                  <SelectItem value="Anthropic">Anthropic</SelectItem>
                  <SelectItem value="BankCorp">BankCorp</SelectItem>
                  <SelectItem value="SecureBank">SecureBank</SelectItem>
                  <SelectItem value="VisionTech">VisionTech</SelectItem>
                </SelectContent>
              </Select>
            </div>
          </div>
        </CardContent>
      </Card>

      {/* Model Grid */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
        {filteredModels.map((model) => (
          <Card key={model.id} className="hover:shadow-lg transition-shadow">
            <CardHeader>
              <div className="flex items-start justify-between">
                <div className="space-y-1">
                  <CardTitle className="text-lg">{model.name}</CardTitle>
                  <p className="text-sm text-muted-foreground">v{model.version}</p>
                </div>
                <div className="flex items-center space-x-2">
                  <div className={`w-3 h-3 rounded-full ${getStatusColor(model.status)}`} />
                  <Badge variant="outline" className={getRiskColor(model.risk_level)}>
                    {model.risk_level}
                  </Badge>
                </div>
              </div>
            </CardHeader>
            <CardContent className="space-y-4">
              <p className="text-sm text-muted-foreground">{model.description}</p>
              
              <div className="space-y-2">
                <div className="flex items-center justify-between text-sm">
                  <span>Accuracy</span>
                  <span className="font-medium">{model.accuracy}%</span>
                </div>
                <div className="flex items-center justify-between text-sm">
                  <span>Fairness</span>
                  <span className="font-medium">{model.fairness_score}%</span>
                </div>
                <div className="flex items-center justify-between text-sm">
                  <span>Compliance</span>
                  <span className="font-medium">{model.compliance_score}%</span>
                </div>
              </div>

              <div className="flex flex-wrap gap-1">
                {model.tags.slice(0, 3).map((tag) => (
                  <Badge key={tag} variant="secondary" className="text-xs">
                    {tag}
                  </Badge>
                ))}
                {model.tags.length > 3 && (
                  <Badge variant="secondary" className="text-xs">
                    +{model.tags.length - 3}
                  </Badge>
                )}
              </div>

              <div className="flex items-center justify-between text-xs text-muted-foreground">
                <span>{model.company}</span>
                <span>{model.last_updated}</span>
              </div>

              <div className="flex items-center space-x-2">
                <Button 
                  size="sm" 
                  className="flex-1"
                  onClick={() => handleModelSelect(model.id)}
                >
                  <Play className="mr-2 h-4 w-4" />
                  Select
                </Button>
                <Button size="sm" variant="outline">
                  <Eye className="h-4 w-4" />
                </Button>
                <Button size="sm" variant="outline">
                  <Settings className="h-4 w-4" />
                </Button>
              </div>
            </CardContent>
          </Card>
        ))}
      </div>

      {filteredModels.length === 0 && (
        <Card>
          <CardContent className="flex items-center justify-center h-32">
            <div className="text-center">
              <p className="text-muted-foreground">No models found matching your criteria</p>
              <Button 
                variant="outline" 
                className="mt-2"
                onClick={() => {
                  setSearchTerm('')
                  setSelectedType('all')
                  setSelectedStatus('all')
                  setSelectedCompany('all')
                }}
              >
                Clear Filters
              </Button>
            </div>
          </CardContent>
        </Card>
      )}
    </div>
  )
} 