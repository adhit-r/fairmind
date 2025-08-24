"use client"

import { useState, useEffect } from 'react'
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/common/card"
import { Button } from "@/components/ui/common/button"
import { Badge } from "@/components/ui/common/badge"
import { Input } from "@/components/ui/common/input"
import { Textarea } from "@/components/ui/common/textarea"
import { Alert, AlertDescription } from "@/components/ui/common/alert"
import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/components/ui/common/tabs"
import { 
  Upload, 
  FileText, 
  Database, 
  Search, 
  Filter,
  Plus,
  Eye,
  Download,
  Trash2,
  Edit,
  CheckCircle,
  XCircle,
  AlertTriangle,
  Info,
  Clock,
  User,
  Building,
  Tag,
  BarChart3,
  Shield,
  Fingerprint
} from "lucide-react"
import { fairmindAPI } from "@/lib/fairmind-api"

interface ModelCatalogItem {
  id: string
  name: string
  version: string
  description: string
  framework: string
  architecture: string
  file_size: number
  upload_date: string
  uploaded_by: string
  organization: string
  tags: string[]
  status: 'active' | 'archived' | 'draft'
  file_path: string
  metadata: {
    accuracy?: number
    precision?: number
    recall?: number
    f1_score?: number
    training_date?: string
    dataset_info?: string
    model_type?: string
  }
  provenance?: {
    signature_verified: boolean
    checksum: string
    digital_signature: string
  }
}

export function EnhancedModelCatalog() {
  const [models, setModels] = useState<ModelCatalogItem[]>([])
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState<string>('')
  const [searchTerm, setSearchTerm] = useState('')
  const [selectedFramework, setSelectedFramework] = useState<string>('all')
  const [showUploadForm, setShowUploadForm] = useState(false)
  const [selectedModel, setSelectedModel] = useState<ModelCatalogItem | null>(null)

  // Upload form state
  const [uploadForm, setUploadForm] = useState({
    name: '',
    version: '',
    description: '',
    framework: '',
    architecture: '',
    organization: '',
    tags: '',
    modelFile: null as File | null
  })

  useEffect(() => {
    loadModels()
  }, [])

  const loadModels = async () => {
    try {
      setLoading(true)
      // const response = await fairmindAPI.getModels()
      // if (response.success) {
      //   setModels(response.data)
      // } else {
      //   setError('Failed to load models')
      // }
      // Mock data for now
      setModels([])
    } catch (error) {
      setError('Error loading models')
    } finally {
      setLoading(false)
    }
  }

  const handleFileUpload = (event: React.ChangeEvent<HTMLInputElement>) => {
    const file = event.target.files?.[0]
    if (file) {
      setUploadForm(prev => ({ ...prev, modelFile: file }))
    }
  }

  const handleUpload = async () => {
    if (!uploadForm.modelFile) {
      setError('Please select a model file')
      return
    }

    try {
      setLoading(true)
      
      // Create form data for file upload
      const formData = new FormData()
      formData.append('file', uploadForm.modelFile)
      formData.append('name', uploadForm.name)
      formData.append('version', uploadForm.version)
      formData.append('description', uploadForm.description)
      formData.append('framework', uploadForm.framework)
      formData.append('architecture', uploadForm.architecture)
      formData.append('organization', uploadForm.organization)
      formData.append('tags', uploadForm.tags)

      // const response = await fairmindAPI.uploadModel(formData)
      
      // if (response.success) {
      //   setShowUploadForm(false)
      //   setUploadForm({
      //     name: '',
      //     version: '',
      //     description: '',
      //     framework: '',
      //     architecture: '',
      //     organization: '',
      //     tags: '',
      //     modelFile: null
      //   })
      //   loadModels()
      // } else {
      //   setError(response.error || 'Failed to upload model')
      // }
      // Mock success for now
      setShowUploadForm(false)
      setUploadForm({
        name: '',
        version: '',
        description: '',
        framework: '',
        architecture: '',
        organization: '',
        tags: '',
        modelFile: null
      })
    } catch (error) {
      setError('Error uploading model')
    } finally {
      setLoading(false)
    }
  }

  const filteredModels = models.filter(model => {
    const matchesSearch = model.name.toLowerCase().includes(searchTerm.toLowerCase()) ||
                         model.description.toLowerCase().includes(searchTerm.toLowerCase()) ||
                         model.tags.some(tag => tag.toLowerCase().includes(searchTerm.toLowerCase()))
    
    const matchesFramework = selectedFramework === 'all' || model.framework === selectedFramework
    
    return matchesSearch && matchesFramework
  })

  const frameworks = Array.from(new Set(models.map(model => model.framework)))

  const formatFileSize = (bytes: number) => {
    if (bytes === 0) return '0 Bytes'
    const k = 1024
    const sizes = ['Bytes', 'KB', 'MB', 'GB']
    const i = Math.floor(Math.log(bytes) / Math.log(k))
    return parseFloat((bytes / Math.pow(k, i)).toFixed(2)) + ' ' + sizes[i]
  }

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-bold">Model Catalog</h1>
          <p className="text-gray-600">Manage and track your AI/ML models with provenance</p>
        </div>
        <Button onClick={() => setShowUploadForm(true)}>
          <Plus className="h-4 w-4 mr-2" />
          Upload Model
        </Button>
      </div>

      {/* Upload Form */}
      {showUploadForm && (
        <Card>
          <CardHeader>
            <CardTitle>Upload New Model</CardTitle>
            <CardDescription>Add a new model to the catalog with provenance tracking</CardDescription>
          </CardHeader>
          <CardContent className="space-y-4">
            <div className="grid grid-cols-2 gap-4">
              <div>
                <label className="text-sm font-medium">Model Name</label>
                <Input
                  value={uploadForm.name}
                  onChange={(e) => setUploadForm({...uploadForm, name: e.target.value})}
                  placeholder="Enter model name"
                />
              </div>
              <div>
                <label className="text-sm font-medium">Version</label>
                <Input
                  value={uploadForm.version}
                  onChange={(e) => setUploadForm({...uploadForm, version: e.target.value})}
                  placeholder="1.0.0"
                />
              </div>
              <div>
                <label className="text-sm font-medium">Framework</label>
                <Input
                  value={uploadForm.framework}
                  onChange={(e) => setUploadForm({...uploadForm, framework: e.target.value})}
                  placeholder="e.g., TensorFlow, PyTorch"
                />
              </div>
              <div>
                <label className="text-sm font-medium">Architecture</label>
                <Input
                  value={uploadForm.architecture}
                  onChange={(e) => setUploadForm({...uploadForm, architecture: e.target.value})}
                  placeholder="e.g., ResNet-50, BERT"
                />
              </div>
              <div>
                <label className="text-sm font-medium">Organization</label>
                <Input
                  value={uploadForm.organization}
                  onChange={(e) => setUploadForm({...uploadForm, organization: e.target.value})}
                  placeholder="Your organization"
                />
              </div>
              <div>
                <label className="text-sm font-medium">Tags</label>
                <Input
                  value={uploadForm.tags}
                  onChange={(e) => setUploadForm({...uploadForm, tags: e.target.value})}
                  placeholder="image-classification, computer-vision"
                />
              </div>
            </div>
            
            <div>
              <label className="text-sm font-medium">Description</label>
              <Textarea
                value={uploadForm.description}
                onChange={(e) => setUploadForm({...uploadForm, description: e.target.value})}
                placeholder="Describe the model's purpose, training data, and use cases"
                rows={3}
              />
            </div>

            <div>
              <label className="text-sm font-medium">Model File (Pickle/ONNX/H5)</label>
              <Input
                type="file"
                accept=".pkl,.pickle,.onnx,.h5,.hdf5,.pb,.pt,.pth"
                onChange={handleFileUpload}
              />
              <p className="text-xs text-gray-500 mt-1">
                Supported formats: Pickle (.pkl), ONNX (.onnx), HDF5 (.h5), TensorFlow (.pb), PyTorch (.pt)
              </p>
            </div>

            <div className="flex gap-2">
              <Button onClick={handleUpload} disabled={loading || !uploadForm.modelFile}>
                {loading ? 'Uploading...' : 'Upload Model'}
              </Button>
              <Button onClick={() => setShowUploadForm(false)} variant="outline">
                Cancel
              </Button>
            </div>
          </CardContent>
        </Card>
      )}

      {/* Error Display */}
      {error && (
        <Alert variant="destructive">
          <XCircle className="h-4 w-4" />
          <AlertDescription>{error}</AlertDescription>
        </Alert>
      )}

      {/* Search and Filters */}
      <Card>
        <CardContent className="pt-6">
          <div className="flex gap-4">
            <div className="flex-1">
              <div className="relative">
                <Search className="absolute left-3 top-1/2 transform -translate-y-1/2 text-gray-400 h-4 w-4" />
                <Input
                  placeholder="Search models..."
                  value={searchTerm}
                  onChange={(e) => setSearchTerm(e.target.value)}
                  className="pl-10"
                />
              </div>
            </div>
            <div className="w-48">
              <select
                value={selectedFramework}
                onChange={(e) => setSelectedFramework(e.target.value)}
                className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
              >
                <option value="all">All Frameworks</option>
                {frameworks.map(framework => (
                  <option key={framework} value={framework}>{framework}</option>
                ))}
              </select>
            </div>
          </div>
        </CardContent>
      </Card>

      {/* Models Grid */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
        {filteredModels.map((model) => (
          <Card 
            key={model.id} 
            className="cursor-pointer hover:shadow-lg transition-shadow"
            onClick={() => setSelectedModel(model)}
          >
            <CardHeader className="pb-3">
              <div className="flex items-start justify-between">
                <div className="flex-1">
                  <CardTitle className="text-lg">{model.name}</CardTitle>
                  <CardDescription>v{model.version}</CardDescription>
                </div>
                <Badge variant={model.status === 'active' ? 'default' : 'secondary'}>
                  {model.status}
                </Badge>
              </div>
            </CardHeader>
            <CardContent className="space-y-3">
              <p className="text-sm text-gray-600 line-clamp-2">{model.description}</p>
              
              <div className="flex items-center gap-2 text-sm text-gray-500">
                <Database className="h-4 w-4" />
                <span>{model.framework}</span>
              </div>

              <div className="flex items-center gap-2 text-sm text-gray-500">
                <BarChart3 className="h-4 w-4" />
                <span>{model.architecture}</span>
              </div>

              <div className="flex items-center gap-2 text-sm text-gray-500">
                <Clock className="h-4 w-4" />
                <span>{new Date(model.upload_date).toLocaleDateString()}</span>
              </div>

              <div className="flex items-center gap-2 text-sm text-gray-500">
                <User className="h-4 w-4" />
                <span>{model.uploaded_by}</span>
              </div>

              {model.provenance && (
                <div className="flex items-center gap-2">
                  {model.provenance.signature_verified ? (
                    <Badge className="bg-green-100 text-green-800">
                      <CheckCircle className="h-3 w-3 mr-1" />
                      Verified
                    </Badge>
                  ) : (
                    <Badge className="bg-red-100 text-red-800">
                      <XCircle className="h-3 w-3 mr-1" />
                      Unverified
                    </Badge>
                  )}
                </div>
              )}

              <div className="flex flex-wrap gap-1">
                {model.tags.slice(0, 3).map((tag, index) => (
                  <Badge key={index} variant="outline" className="text-xs">
                    {tag}
                  </Badge>
                ))}
                {model.tags.length > 3 && (
                  <Badge variant="outline" className="text-xs">
                    +{model.tags.length - 3} more
                  </Badge>
                )}
              </div>

              <div className="flex items-center justify-between pt-2">
                <span className="text-sm text-gray-500">
                  {formatFileSize(model.file_size)}
                </span>
                <div className="flex gap-1">
                  <Button size="sm" variant="outline">
                    <Eye className="h-3 w-3" />
                  </Button>
                  <Button size="sm" variant="outline">
                    <Download className="h-3 w-3" />
                  </Button>
                </div>
              </div>
            </CardContent>
          </Card>
        ))}
      </div>

      {filteredModels.length === 0 && !loading && (
        <div className="text-center py-12">
          <Database className="h-12 w-12 mx-auto mb-4 text-gray-400" />
          <h3 className="text-lg font-medium text-gray-900 mb-2">No models found</h3>
          <p className="text-gray-500 mb-4">
            {searchTerm || selectedFramework !== 'all' 
              ? 'Try adjusting your search criteria' 
              : 'Get started by uploading your first model'}
          </p>
          {!searchTerm && selectedFramework === 'all' && (
            <Button onClick={() => setShowUploadForm(true)}>
              <Plus className="h-4 w-4 mr-2" />
              Upload Model
            </Button>
          )}
        </div>
      )}

      {/* Model Details Modal */}
      {selectedModel && (
        <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50">
          <div className="bg-white rounded-lg p-6 max-w-2xl w-full mx-4 max-h-[90vh] overflow-y-auto">
            <div className="flex items-center justify-between mb-4">
              <h2 className="text-xl font-bold">{selectedModel.name}</h2>
              <Button variant="outline" onClick={() => setSelectedModel(null)}>
                <XCircle className="h-4 w-4" />
              </Button>
            </div>
            
            <Tabs defaultValue="overview">
              <TabsList>
                <TabsTrigger value="overview">Overview</TabsTrigger>
                <TabsTrigger value="metadata">Metadata</TabsTrigger>
                <TabsTrigger value="provenance">Provenance</TabsTrigger>
              </TabsList>
              
              <TabsContent value="overview" className="space-y-4">
                <div>
                  <h3 className="font-medium mb-2">Description</h3>
                  <p className="text-gray-600">{selectedModel.description}</p>
                </div>
                
                <div className="grid grid-cols-2 gap-4">
                  <div>
                    <h3 className="font-medium mb-2">Model Information</h3>
                    <div className="space-y-1 text-sm">
                      <div><span className="text-gray-500">Version:</span> {selectedModel.version}</div>
                      <div><span className="text-gray-500">Framework:</span> {selectedModel.framework}</div>
                      <div><span className="text-gray-500">Architecture:</span> {selectedModel.architecture}</div>
                      <div><span className="text-gray-500">File Size:</span> {formatFileSize(selectedModel.file_size)}</div>
                    </div>
                  </div>
                  
                  <div>
                    <h3 className="font-medium mb-2">Performance Metrics</h3>
                    <div className="space-y-1 text-sm">
                      {selectedModel.metadata.accuracy && (
                        <div><span className="text-gray-500">Accuracy:</span> {(selectedModel.metadata.accuracy * 100).toFixed(2)}%</div>
                      )}
                      {selectedModel.metadata.precision && (
                        <div><span className="text-gray-500">Precision:</span> {(selectedModel.metadata.precision * 100).toFixed(2)}%</div>
                      )}
                      {selectedModel.metadata.recall && (
                        <div><span className="text-gray-500">Recall:</span> {(selectedModel.metadata.recall * 100).toFixed(2)}%</div>
                      )}
                      {selectedModel.metadata.f1_score && (
                        <div><span className="text-gray-500">F1 Score:</span> {(selectedModel.metadata.f1_score * 100).toFixed(2)}%</div>
                      )}
                    </div>
                  </div>
                </div>
              </TabsContent>
              
              <TabsContent value="metadata" className="space-y-4">
                <div className="grid grid-cols-2 gap-4">
                  <div>
                    <h3 className="font-medium mb-2">Upload Information</h3>
                    <div className="space-y-1 text-sm">
                      <div><span className="text-gray-500">Uploaded by:</span> {selectedModel.uploaded_by}</div>
                      <div><span className="text-gray-500">Organization:</span> {selectedModel.organization}</div>
                      <div><span className="text-gray-500">Upload date:</span> {new Date(selectedModel.upload_date).toLocaleString()}</div>
                      <div><span className="text-gray-500">Status:</span> {selectedModel.status}</div>
                    </div>
                  </div>
                  
                  <div>
                    <h3 className="font-medium mb-2">Tags</h3>
                    <div className="flex flex-wrap gap-1">
                      {selectedModel.tags.map((tag, index) => (
                        <Badge key={index} variant="outline">
                          {tag}
                        </Badge>
                      ))}
                    </div>
                  </div>
                </div>
              </TabsContent>
              
              <TabsContent value="provenance" className="space-y-4">
                {selectedModel.provenance ? (
                  <div className="space-y-4">
                    <div className="flex items-center gap-2">
                      <Shield className="h-5 w-5" />
                      <h3 className="font-medium">Digital Signature Verification</h3>
                    </div>
                    
                    <div className="grid grid-cols-2 gap-4">
                      <div>
                        <div className="flex items-center gap-2 mb-2">
                          {selectedModel.provenance.signature_verified ? (
                            <CheckCircle className="h-4 w-4 text-green-600" />
                          ) : (
                            <XCircle className="h-4 w-4 text-red-600" />
                          )}
                          <span className="text-sm font-medium">
                            {selectedModel.provenance.signature_verified ? 'Verified' : 'Unverified'}
                          </span>
                        </div>
                      </div>
                      
                      <div>
                        <div className="flex items-center gap-2 mb-2">
                          <Fingerprint className="h-4 w-4 text-blue-600" />
                          <span className="text-sm font-medium">Checksum</span>
                        </div>
                        <p className="text-xs font-mono bg-gray-100 p-2 rounded">
                          {selectedModel.provenance.checksum}
                        </p>
                      </div>
                    </div>
                  </div>
                ) : (
                  <div className="text-center py-8">
                    <AlertTriangle className="h-12 w-12 mx-auto mb-4 text-gray-400" />
                    <p className="text-gray-500">No provenance information available</p>
                  </div>
                )}
              </TabsContent>
            </Tabs>
          </div>
        </div>
      )}
    </div>
  )
}
