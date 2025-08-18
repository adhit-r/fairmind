"use client"

import { useState, useEffect } from 'react'
import { Button } from "@/components/ui/common/button"
import { Input } from "@/components/ui/common/input"
import { Label } from "@/components/ui/common/label"
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card"
import { Alert, AlertDescription } from "@/components/ui/common/alert"
import { Badge } from "@/components/ui/common/badge"
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from "@/components/ui/common/select"
import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/components/ui/common/tabs"
import { Dialog, DialogContent, DialogDescription, DialogHeader, DialogTitle, DialogTrigger } from "@/components/ui/common/dialog"
import { 
  Plus, 
  Search, 
  Filter, 
  Grid, 
  List, 
  Eye, 
  Edit, 
  Trash2, 
  Upload, 
  Download,
  Shield,
  AlertTriangle,
  CheckCircle,
  Clock,
  BarChart3,
  Settings,
  FileText,
  Bot,
  Database,
  Code,
  Zap,
  ArrowRight,
  MoreHorizontal,
  Star,
  Users,
  Calendar,
  Tag,
  TrendingUp
} from "lucide-react"
import { fairmindAPI } from "@/lib/fairmind-api"
import { AIModel } from "@/types"

interface ModelCardProps {
  model: AIModel
  onView: (model: AIModel) => void
  onEdit: (model: AIModel) => void
  onDelete: (model: AIModel) => void
  onAnalyze: (model: AIModel) => void
}

function ModelCard({ model, onView, onEdit, onDelete, onAnalyze }: ModelCardProps) {
  const getStatusColor = (status: string) => {
    switch (status.toLowerCase()) {
      case 'active': return 'bg-green-100 text-green-800'
      case 'draft': return 'bg-yellow-100 text-yellow-800'
      case 'archived': return 'bg-gray-100 text-gray-800'
      case 'deprecated': return 'bg-red-100 text-red-800'
      default: return 'bg-gray-100 text-gray-800'
    }
  }

  const getTypeIcon = (type: string) => {
    switch (type.toLowerCase()) {
      case 'classification': return <BarChart3 className="h-4 w-4" />
      case 'regression': return <TrendingUp className="h-4 w-4" />
      case 'nlp': return <FileText className="h-4 w-4" />
      case 'computer_vision': return <Eye className="h-4 w-4" />
      case 'recommendation': return <Star className="h-4 w-4" />
      default: return <Bot className="h-4 w-4" />
    }
  }

  return (
    <Card className="hover:shadow-md transition-shadow duration-200">
      <CardHeader className="pb-3">
        <div className="flex items-start justify-between">
          <div className="flex items-center space-x-2">
            <div className="h-8 w-8 bg-primary/10 rounded-lg flex items-center justify-center">
              {getTypeIcon(model.type)}
            </div>
            <div>
              <CardTitle className="text-lg">{model.name}</CardTitle>
              <CardDescription className="text-sm">
                Version {model.version} • {model.framework}
              </CardDescription>
            </div>
          </div>
          <Badge className={getStatusColor(model.status)}>
            {model.status}
          </Badge>
        </div>
      </CardHeader>
      <CardContent className="space-y-3">
        <div className="flex items-center justify-between text-sm text-muted-foreground">
          <span>Type: {model.type}</span>
          <span>Framework: {model.framework}</span>
        </div>
        
        <div className="flex items-center justify-between text-sm text-muted-foreground">
          <span>Accuracy: {model.metadata?.performance?.accuracy ? `${(model.metadata.performance.accuracy * 100).toFixed(1)}%` : 'N/A'}</span>
          <span>Updated: {new Date(model.updatedAt).toLocaleDateString()}</span>
        </div>

        <div className="flex items-center space-x-1">
          <Badge variant="outline" className="text-xs">
            <Users className="h-3 w-3 mr-1" />
            System
          </Badge>
          {model.metadata?.tags && model.metadata.tags.length > 0 && (
            <Badge variant="outline" className="text-xs">
              <Tag className="h-3 w-3 mr-1" />
              {model.metadata.tags.length} tags
            </Badge>
          )}
        </div>

        <div className="flex items-center justify-between pt-2 border-t">
          <div className="flex space-x-1">
            <Button
              variant="ghost"
              size="sm"
              onClick={() => onView(model)}
              className="h-8 px-2"
            >
              <Eye className="h-4 w-4" />
            </Button>
            <Button
              variant="ghost"
              size="sm"
              onClick={() => onEdit(model)}
              className="h-8 px-2"
            >
              <Edit className="h-4 w-4" />
            </Button>
            <Button
              variant="ghost"
              size="sm"
              onClick={() => onAnalyze(model)}
              className="h-8 px-2"
            >
              <BarChart3 className="h-4 w-4" />
            </Button>
          </div>
          <Button
            variant="ghost"
            size="sm"
            onClick={() => onDelete(model)}
            className="h-8 px-2 text-destructive hover:text-destructive"
          >
            <Trash2 className="h-4 w-4" />
          </Button>
        </div>
      </CardContent>
    </Card>
  )
}

interface ModelUploadWizardProps {
  isOpen: boolean
  onClose: () => void
  onSuccess: () => void
}

function ModelUploadWizard({ isOpen, onClose, onSuccess }: ModelUploadWizardProps) {
  const [currentStep, setCurrentStep] = useState(0)
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState('')
  const [modelData, setModelData] = useState({
    name: '',
    version: '',
    type: '',
    framework: '',
    description: '',
    tags: [] as string[],
    file: null as File | null
  })

  const modelTypes = [
    'Classification',
    'Regression',
    'NLP',
    'Computer Vision',
    'Recommendation',
    'Reinforcement Learning',
    'Other'
  ]

  const frameworks = [
    'TensorFlow',
    'PyTorch',
    'Scikit-learn',
    'XGBoost',
    'LightGBM',
    'Hugging Face',
    'OpenAI',
    'Other'
  ]

  const handleFileUpload = (event: React.ChangeEvent<HTMLInputElement>) => {
    const file = event.target.files?.[0]
    if (file) {
      setModelData({ ...modelData, file })
    }
  }

  const handleSubmit = async () => {
    if (!modelData.file) {
      setError('Please select a model file')
      return
    }

    setLoading(true)
    setError('')

    try {
      const formData = new FormData()
      formData.append('file', modelData.file)
      formData.append('name', modelData.name)
      formData.append('version', modelData.version)
      formData.append('type', modelData.type)
      formData.append('framework', modelData.framework)
      formData.append('description', modelData.description)
      formData.append('tags', JSON.stringify(modelData.tags))

      await fairmindAPI.uploadModel(modelData.file, {
        name: modelData.name,
        framework: modelData.framework,
        type: modelData.type as any
      })
      onSuccess()
      onClose()
    } catch (error: any) {
      setError(error.message || 'Failed to upload model')
    } finally {
      setLoading(false)
    }
  }

  const steps = [
    {
      title: 'Basic Information',
      description: 'Provide model details'
    },
    {
      title: 'File Upload',
      description: 'Upload your model file'
    },
    {
      title: 'Review & Submit',
      description: 'Review and complete upload'
    }
  ]

  return (
    <Dialog open={isOpen} onOpenChange={onClose}>
      <DialogContent className="max-w-2xl">
        <DialogHeader>
          <DialogTitle>Upload New Model</DialogTitle>
          <DialogDescription>
            Register a new AI model in your inventory
          </DialogDescription>
        </DialogHeader>

        {/* Progress Steps */}
        <div className="flex items-center space-x-2 mb-6">
          {steps.map((step, index) => (
            <div key={index} className="flex items-center">
              <div className={`h-8 w-8 rounded-full flex items-center justify-center text-sm ${
                index <= currentStep 
                  ? 'bg-primary text-primary-foreground' 
                  : 'bg-muted text-muted-foreground'
              }`}>
                {index + 1}
              </div>
              {index < steps.length - 1 && (
                <div className={`w-8 h-0.5 mx-2 ${
                  index < currentStep ? 'bg-primary' : 'bg-muted'
                }`} />
              )}
            </div>
          ))}
        </div>

        {/* Step Content */}
        {currentStep === 0 && (
          <div className="space-y-4">
            <div className="grid grid-cols-2 gap-4">
              <div className="space-y-2">
                <Label htmlFor="name">Model Name *</Label>
                <Input
                  id="name"
                  value={modelData.name}
                  onChange={(e) => setModelData({ ...modelData, name: e.target.value })}
                  placeholder="Enter model name"
                />
              </div>
              <div className="space-y-2">
                <Label htmlFor="version">Version *</Label>
                <Input
                  id="version"
                  value={modelData.version}
                  onChange={(e) => setModelData({ ...modelData, version: e.target.value })}
                  placeholder="e.g., 1.0.0"
                />
              </div>
            </div>
            
            <div className="grid grid-cols-2 gap-4">
              <div className="space-y-2">
                <Label htmlFor="type">Model Type *</Label>
                <Select value={modelData.type} onValueChange={(value) => setModelData({ ...modelData, type: value })}>
                  <SelectTrigger>
                    <SelectValue placeholder="Select model type" />
                  </SelectTrigger>
                  <SelectContent>
                    {modelTypes.map((type) => (
                      <SelectItem key={type} value={type}>{type}</SelectItem>
                    ))}
                  </SelectContent>
                </Select>
              </div>
              <div className="space-y-2">
                <Label htmlFor="framework">Framework *</Label>
                <Select value={modelData.framework} onValueChange={(value) => setModelData({ ...modelData, framework: value })}>
                  <SelectTrigger>
                    <SelectValue placeholder="Select framework" />
                  </SelectTrigger>
                  <SelectContent>
                    {frameworks.map((framework) => (
                      <SelectItem key={framework} value={framework}>{framework}</SelectItem>
                    ))}
                  </SelectContent>
                </Select>
              </div>
            </div>

            <div className="space-y-2">
              <Label htmlFor="description">Description</Label>
              <Input
                id="description"
                value={modelData.description}
                onChange={(e) => setModelData({ ...modelData, description: e.target.value })}
                placeholder="Describe your model"
              />
            </div>
          </div>
        )}

        {currentStep === 1 && (
          <div className="space-y-4">
            <div className="border-2 border-dashed border-muted-foreground/25 rounded-lg p-8 text-center">
              <Upload className="h-12 w-12 mx-auto mb-4 text-muted-foreground" />
              <Label htmlFor="file" className="cursor-pointer">
                <div className="space-y-2">
                  <p className="text-lg font-medium">Upload Model File</p>
                  <p className="text-sm text-muted-foreground">
                    Supported formats: .pkl, .joblib, .h5, .pb, .onnx, .pt
                  </p>
                  <p className="text-sm text-muted-foreground">
                    Maximum size: 500MB
                  </p>
                </div>
              </Label>
              <Input
                id="file"
                type="file"
                accept=".pkl,.joblib,.h5,.pb,.onnx,.pt"
                onChange={handleFileUpload}
                className="hidden"
              />
            </div>
            
            {modelData.file && (
              <div className="flex items-center space-x-2 p-3 bg-muted rounded-lg">
                <FileText className="h-4 w-4" />
                <span className="text-sm">{modelData.file.name}</span>
                <span className="text-xs text-muted-foreground">
                  ({(modelData.file.size / 1024 / 1024).toFixed(2)} MB)
                </span>
              </div>
            )}
          </div>
        )}

        {currentStep === 2 && (
          <div className="space-y-4">
            <Card>
              <CardHeader>
                <CardTitle className="text-lg">Review Model Details</CardTitle>
              </CardHeader>
              <CardContent className="space-y-3">
                <div className="grid grid-cols-2 gap-4 text-sm">
                  <div>
                    <span className="font-medium">Name:</span> {modelData.name}
                  </div>
                  <div>
                    <span className="font-medium">Version:</span> {modelData.version}
                  </div>
                  <div>
                    <span className="font-medium">Type:</span> {modelData.type}
                  </div>
                  <div>
                    <span className="font-medium">Framework:</span> {modelData.framework}
                  </div>
                </div>
                {modelData.description && (
                  <div>
                    <span className="font-medium">Description:</span> {modelData.description}
                  </div>
                )}
                {modelData.file && (
                  <div>
                    <span className="font-medium">File:</span> {modelData.file.name}
                  </div>
                )}
              </CardContent>
            </Card>

            {error && (
              <Alert variant="destructive">
                <AlertDescription>{error}</AlertDescription>
              </Alert>
            )}
          </div>
        )}

        {/* Navigation */}
        <div className="flex justify-between pt-4">
          <Button
            variant="outline"
            onClick={() => setCurrentStep(Math.max(0, currentStep - 1))}
            disabled={currentStep === 0}
          >
            Previous
          </Button>
          
          {currentStep < steps.length - 1 ? (
            <Button
              onClick={() => setCurrentStep(currentStep + 1)}
              disabled={
                (currentStep === 0 && (!modelData.name || !modelData.version || !modelData.type || !modelData.framework)) ||
                (currentStep === 1 && !modelData.file)
              }
            >
              Next
              <ArrowRight className="ml-2 h-4 w-4" />
            </Button>
          ) : (
            <Button onClick={handleSubmit} disabled={loading}>
              {loading ? 'Uploading...' : 'Upload Model'}
            </Button>
          )}
        </div>
      </DialogContent>
    </Dialog>
  )
}

export function EnhancedModelRegistry() {
  const [models, setModels] = useState<AIModel[]>([])
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState('')
  const [searchTerm, setSearchTerm] = useState('')
  const [selectedType, setSelectedType] = useState<string>('all')
  const [selectedStatus, setSelectedStatus] = useState<string>('all')
  const [viewMode, setViewMode] = useState<'grid' | 'list'>('grid')
  const [uploadDialogOpen, setUploadDialogOpen] = useState(false)

  useEffect(() => {
    loadModels()
  }, [])

  const loadModels = async () => {
    setLoading(true)
    setError('')
    
    try {
      const response = await fairmindAPI.getModels()
      setModels(response)
    } catch (error: any) {
      setError('Failed to load models')
      console.error('Error loading models:', error)
    } finally {
      setLoading(false)
    }
  }

  const filteredModels = models.filter(model => {
    const matchesSearch = model.name.toLowerCase().includes(searchTerm.toLowerCase()) ||
                         model.metadata?.description?.toLowerCase().includes(searchTerm.toLowerCase())
    const matchesType = selectedType === 'all' || model.type.toLowerCase() === selectedType.toLowerCase()
    const matchesStatus = selectedStatus === 'all' || model.status.toLowerCase() === selectedStatus.toLowerCase()
    
    return matchesSearch && matchesType && matchesStatus
  })

  const handleView = (model: AIModel) => {
    // Navigate to model details page
    console.log('View model:', model)
  }

  const handleEdit = (model: AIModel) => {
    // Open edit dialog
    console.log('Edit model:', model)
  }

  const handleDelete = async (model: AIModel) => {
    if (confirm(`Are you sure you want to delete ${model.name}?`)) {
      try {
        // Call delete API
        console.log('Delete model:', model)
        await loadModels() // Refresh list
      } catch (error) {
        setError('Failed to delete model')
      }
    }
  }

  const handleAnalyze = (model: AIModel) => {
    // Navigate to analysis page
    console.log('Analyze model:', model)
  }

  const modelTypes = Array.from(new Set(models.map(m => m.type)))
  const modelStatuses = Array.from(new Set(models.map(m => m.status)))

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-3xl font-bold">Model Registry</h1>
          <p className="text-muted-foreground">
            Manage and track your AI models
          </p>
        </div>
        <Button onClick={() => setUploadDialogOpen(true)}>
          <Plus className="mr-2 h-4 w-4" />
          Upload Model
        </Button>
      </div>

      {/* Filters and Search */}
      <Card>
        <CardContent className="pt-6">
          <div className="flex flex-col md:flex-row gap-4">
            <div className="flex-1">
              <div className="relative">
                <Search className="absolute left-3 top-1/2 transform -translate-y-1/2 h-4 w-4 text-muted-foreground" />
                <Input
                  placeholder="Search models..."
                  value={searchTerm}
                  onChange={(e) => setSearchTerm(e.target.value)}
                  className="pl-10"
                />
              </div>
            </div>
            
            <div className="flex gap-2">
              <Select value={selectedType} onValueChange={setSelectedType}>
                <SelectTrigger className="w-32">
                  <SelectValue placeholder="Type" />
                </SelectTrigger>
                <SelectContent>
                  <SelectItem value="all">All Types</SelectItem>
                  {modelTypes.map((type) => (
                    <SelectItem key={type} value={type}>{type}</SelectItem>
                  ))}
                </SelectContent>
              </Select>
              
              <Select value={selectedStatus} onValueChange={setSelectedStatus}>
                <SelectTrigger className="w-32">
                  <SelectValue placeholder="Status" />
                </SelectTrigger>
                <SelectContent>
                  <SelectItem value="all">All Status</SelectItem>
                  {modelStatuses.map((status) => (
                    <SelectItem key={status} value={status}>{status}</SelectItem>
                  ))}
                </SelectContent>
              </Select>
              
              <div className="flex border rounded-md">
                <Button
                  variant={viewMode === 'grid' ? 'default' : 'ghost'}
                  size="sm"
                  onClick={() => setViewMode('grid')}
                  className="rounded-r-none"
                >
                  <Grid className="h-4 w-4" />
                </Button>
                <Button
                  variant={viewMode === 'list' ? 'default' : 'ghost'}
                  size="sm"
                  onClick={() => setViewMode('list')}
                  className="rounded-l-none"
                >
                  <List className="h-4 w-4" />
                </Button>
              </div>
            </div>
          </div>
        </CardContent>
      </Card>

      {/* Error Display */}
      {error && (
        <Alert variant="destructive">
          <AlertTriangle className="h-4 w-4" />
          <AlertDescription>{error}</AlertDescription>
        </Alert>
      )}

      {/* Models Grid/List */}
      {loading ? (
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
          {[...Array(6)].map((_, i) => (
            <Card key={i} className="animate-pulse">
              <CardHeader>
                <div className="h-4 bg-muted rounded w-3/4"></div>
                <div className="h-3 bg-muted rounded w-1/2"></div>
              </CardHeader>
              <CardContent>
                <div className="space-y-2">
                  <div className="h-3 bg-muted rounded"></div>
                  <div className="h-3 bg-muted rounded w-2/3"></div>
                </div>
              </CardContent>
            </Card>
          ))}
        </div>
      ) : filteredModels.length === 0 ? (
        <Card>
          <CardContent className="pt-6 text-center">
            <Bot className="h-12 w-12 mx-auto mb-4 text-muted-foreground" />
            <h3 className="text-lg font-medium mb-2">No models found</h3>
            <p className="text-muted-foreground mb-4">
              {searchTerm || selectedType !== 'all' || selectedStatus !== 'all'
                ? 'Try adjusting your search or filters'
                : 'Get started by uploading your first AI model'
              }
            </p>
            {!searchTerm && selectedType === 'all' && selectedStatus === 'all' && (
              <Button onClick={() => setUploadDialogOpen(true)}>
                <Plus className="mr-2 h-4 w-4" />
                Upload Your First Model
              </Button>
            )}
          </CardContent>
        </Card>
      ) : (
        <div className={viewMode === 'grid' 
          ? "grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6"
          : "space-y-4"
        }>
          {filteredModels.map((model) => (
            <ModelCard
              key={model.id}
              model={model}
              onView={handleView}
              onEdit={handleEdit}
              onDelete={handleDelete}
              onAnalyze={handleAnalyze}
            />
          ))}
        </div>
      )}

      {/* Upload Dialog */}
      <ModelUploadWizard
        isOpen={uploadDialogOpen}
        onClose={() => setUploadDialogOpen(false)}
        onSuccess={loadModels}
      />
    </div>
  )
}
