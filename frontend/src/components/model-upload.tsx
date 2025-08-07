"use client"

import { useState, useRef } from 'react'
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card"
import { Button } from "@/components/ui/button"
import { Input } from "@/components/ui/input"
import { Label } from "@/components/ui/label"
import { Textarea } from "@/components/ui/textarea"
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from "@/components/ui/select"
import { Badge } from "@/components/ui/badge"
import { Progress } from "@/components/ui/progress"
import { Alert, AlertDescription } from "@/components/ui/alert"
import { Upload, File, X, CheckCircle, AlertCircle, Info } from "lucide-react"

interface UploadedFile {
  id: string
  name: string
  size: number
  type: string
  status: 'uploading' | 'success' | 'error'
  progress: number
  error?: string
}

interface ModelMetadata {
  name: string
  version: string
  description: string
  type: string
  framework: string
  tags: string[]
  company: string
  risk_level: string
  deployment_environment: string
}

export function ModelUpload() {
  const [uploadedFiles, setUploadedFiles] = useState<UploadedFile[]>([])
  const [modelMetadata, setModelMetadata] = useState<ModelMetadata>({
    name: '',
    version: '',
    description: '',
    type: '',
    framework: '',
    tags: [],
    company: '',
    risk_level: 'medium',
    deployment_environment: 'development'
  })
  const [currentStep, setCurrentStep] = useState(1)
  const [isUploading, setIsUploading] = useState(false)
  const fileInputRef = useRef<HTMLInputElement>(null)

  const handleFileUpload = (event: React.ChangeEvent<HTMLInputElement>) => {
    const files = event.target.files
    if (!files) return

    const newFiles: UploadedFile[] = Array.from(files).map((file, index) => ({
      id: `file-${Date.now()}-${index}`,
      name: file.name,
      size: file.size,
      type: file.type,
      status: 'uploading' as const,
      progress: 0
    }))

    setUploadedFiles(prev => [...prev, ...newFiles])
    simulateUpload(newFiles)
  }

  const simulateUpload = (files: UploadedFile[]) => {
    setIsUploading(true)
    
    files.forEach((file, index) => {
      const interval = setInterval(() => {
        setUploadedFiles(prev => prev.map(f => {
          if (f.id === file.id) {
            const newProgress = f.progress + Math.random() * 20
            if (newProgress >= 100) {
              clearInterval(interval)
              return {
                ...f,
                progress: 100,
                status: 'success' as const
              }
            }
            return { ...f, progress: newProgress }
          }
          return f
        }))
      }, 200)
    })

    setTimeout(() => {
      setIsUploading(false)
    }, 3000)
  }

  const removeFile = (fileId: string) => {
    setUploadedFiles(prev => prev.filter(f => f.id !== fileId))
  }

  const handleMetadataChange = (field: keyof ModelMetadata, value: string | string[]) => {
    setModelMetadata(prev => ({ ...prev, [field]: value }))
  }

  const handleTagInput = (value: string) => {
    if (value.includes(',')) {
      const newTags = value.split(',').map(tag => tag.trim()).filter(tag => tag)
      setModelMetadata(prev => ({ ...prev, tags: [...prev.tags, ...newTags] }))
    }
  }

  const removeTag = (tagToRemove: string) => {
    setModelMetadata(prev => ({
      ...prev,
      tags: prev.tags.filter(tag => tag !== tagToRemove)
    }))
  }

  const handleSubmit = async () => {
    // Handle model registration
    console.log('Submitting model:', { files: uploadedFiles, metadata: modelMetadata })
  }

  const getFileIcon = (fileName: string) => {
    const extension = fileName.split('.').pop()?.toLowerCase()
    switch (extension) {
      case 'py':
      case 'pyc':
        return '🐍'
      case 'pt':
      case 'pth':
        return '🔥'
      case 'onnx':
        return '📦'
      case 'pb':
        return '🤖'
      case 'h5':
        return '📊'
      default:
        return '📄'
    }
  }

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
      <div>
        <h2 className="text-2xl font-bold text-foreground">Model Upload</h2>
        <p className="text-muted-foreground">
          Upload AI models for testing, simulation, and governance activities
        </p>
      </div>

      {/* Progress Steps */}
      <div className="flex items-center space-x-4">
        {[1, 2, 3].map((step) => (
          <div key={step} className="flex items-center space-x-2">
            <div className={`w-8 h-8 rounded-full flex items-center justify-center text-sm font-medium ${
              step <= currentStep 
                ? 'bg-primary text-primary-foreground' 
                : 'bg-muted text-muted-foreground'
            }`}>
              {step}
            </div>
            <span className={`text-sm ${
              step <= currentStep ? 'text-foreground' : 'text-muted-foreground'
            }`}>
              {step === 1 ? 'Upload Files' : step === 2 ? 'Metadata' : 'Review'}
            </span>
            {step < 3 && (
              <div className={`w-8 h-1 ${
                step < currentStep ? 'bg-primary' : 'bg-muted'
              }`} />
            )}
          </div>
        ))}
      </div>

      {/* Step 1: File Upload */}
      {currentStep === 1 && (
        <Card>
          <CardHeader>
            <CardTitle>Upload Model Files</CardTitle>
          </CardHeader>
          <CardContent className="space-y-4">
            <div className="border-2 border-dashed border-border rounded-lg p-8 text-center">
              <Upload className="mx-auto h-12 w-12 text-muted-foreground mb-4" />
              <div className="space-y-2">
                <p className="text-lg font-medium">Drop your model files here</p>
                <p className="text-sm text-muted-foreground">
                  Supported formats: .py, .pt, .pth, .onnx, .pb, .h5
                </p>
                <Button 
                  onClick={() => fileInputRef.current?.click()}
                  disabled={isUploading}
                >
                  Choose Files
                </Button>
              </div>
              <input
                ref={fileInputRef}
                type="file"
                multiple
                accept=".py,.pt,.pth,.onnx,.pb,.h5,.model,.pkl,.joblib"
                onChange={handleFileUpload}
                className="hidden"
              />
            </div>

            {uploadedFiles.length > 0 && (
              <div className="space-y-2">
                <h4 className="font-medium">Uploaded Files</h4>
                {uploadedFiles.map((file) => (
                  <div key={file.id} className="flex items-center justify-between p-3 border rounded-lg">
                    <div className="flex items-center space-x-3">
                      <span className="text-2xl">{getFileIcon(file.name)}</span>
                      <div>
                        <p className="font-medium">{file.name}</p>
                        <p className="text-sm text-muted-foreground">
                          {formatFileSize(file.size)}
                        </p>
                      </div>
                    </div>
                    <div className="flex items-center space-x-2">
                      {file.status === 'uploading' && (
                        <div className="w-24">
                          <Progress value={file.progress} className="h-2" />
                        </div>
                      )}
                      {file.status === 'success' && (
                        <CheckCircle className="h-5 w-5 text-green-500" />
                      )}
                      {file.status === 'error' && (
                        <AlertCircle className="h-5 w-5 text-red-500" />
                      )}
                      <Button
                        size="sm"
                        variant="outline"
                        onClick={() => removeFile(file.id)}
                      >
                        <X className="h-4 w-4" />
                      </Button>
                    </div>
                  </div>
                ))}
              </div>
            )}

            {uploadedFiles.length > 0 && (
              <div className="flex justify-end">
                <Button 
                  onClick={() => setCurrentStep(2)}
                  disabled={isUploading || uploadedFiles.some(f => f.status === 'uploading')}
                >
                  Next: Metadata
                </Button>
              </div>
            )}
          </CardContent>
        </Card>
      )}

      {/* Step 2: Metadata */}
      {currentStep === 2 && (
        <Card>
          <CardHeader>
            <CardTitle>Model Metadata</CardTitle>
          </CardHeader>
          <CardContent className="space-y-6">
            <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
              <div className="space-y-2">
                <Label htmlFor="name">Model Name</Label>
                <Input
                  id="name"
                  value={modelMetadata.name}
                  onChange={(e) => handleMetadataChange('name', e.target.value)}
                  placeholder="e.g., GPT-4, Credit Scoring Model"
                />
              </div>
              <div className="space-y-2">
                <Label htmlFor="version">Version</Label>
                <Input
                  id="version"
                  value={modelMetadata.version}
                  onChange={(e) => handleMetadataChange('version', e.target.value)}
                  placeholder="e.g., 1.0.0"
                />
              </div>
            </div>

            <div className="space-y-2">
              <Label htmlFor="description">Description</Label>
              <Textarea
                id="description"
                value={modelMetadata.description}
                onChange={(e) => handleMetadataChange('description', e.target.value)}
                placeholder="Describe the model's purpose, capabilities, and use cases..."
                rows={3}
              />
            </div>

            <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
              <div className="space-y-2">
                <Label htmlFor="type">Model Type</Label>
                <Select value={modelMetadata.type} onValueChange={(value) => handleMetadataChange('type', value)}>
                  <SelectTrigger>
                    <SelectValue placeholder="Select model type" />
                  </SelectTrigger>
                  <SelectContent>
                    <SelectItem value="LLM">LLM</SelectItem>
                    <SelectItem value="Traditional ML">Traditional ML</SelectItem>
                    <SelectItem value="Computer Vision">Computer Vision</SelectItem>
                    <SelectItem value="NLP">NLP</SelectItem>
                    <SelectItem value="Recommendation">Recommendation</SelectItem>
                  </SelectContent>
                </Select>
              </div>
              <div className="space-y-2">
                <Label htmlFor="framework">Framework</Label>
                <Select value={modelMetadata.framework} onValueChange={(value) => handleMetadataChange('framework', value)}>
                  <SelectTrigger>
                    <SelectValue placeholder="Select framework" />
                  </SelectTrigger>
                  <SelectContent>
                    <SelectItem value="PyTorch">PyTorch</SelectItem>
                    <SelectItem value="TensorFlow">TensorFlow</SelectItem>
                    <SelectItem value="Scikit-learn">Scikit-learn</SelectItem>
                    <SelectItem value="ONNX">ONNX</SelectItem>
                    <SelectItem value="Hugging Face">Hugging Face</SelectItem>
                    <SelectItem value="Custom">Custom</SelectItem>
                  </SelectContent>
                </Select>
              </div>
            </div>

            <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
              <div className="space-y-2">
                <Label htmlFor="company">Company</Label>
                <Input
                  id="company"
                  value={modelMetadata.company}
                  onChange={(e) => handleMetadataChange('company', e.target.value)}
                  placeholder="e.g., OpenAI, BankCorp"
                />
              </div>
              <div className="space-y-2">
                <Label htmlFor="risk-level">Risk Level</Label>
                <Select value={modelMetadata.risk_level} onValueChange={(value) => handleMetadataChange('risk_level', value)}>
                  <SelectTrigger>
                    <SelectValue />
                  </SelectTrigger>
                  <SelectContent>
                    <SelectItem value="low">Low</SelectItem>
                    <SelectItem value="medium">Medium</SelectItem>
                    <SelectItem value="high">High</SelectItem>
                    <SelectItem value="critical">Critical</SelectItem>
                  </SelectContent>
                </Select>
              </div>
            </div>

            <div className="space-y-2">
              <Label htmlFor="tags">Tags (comma-separated)</Label>
              <Input
                id="tags"
                placeholder="e.g., NLP, Text Generation, Conversational AI"
                onKeyDown={(e) => {
                  if (e.key === 'Enter') {
                    e.preventDefault()
                    handleTagInput(e.currentTarget.value)
                    e.currentTarget.value = ''
                  }
                }}
              />
              {modelMetadata.tags.length > 0 && (
                <div className="flex flex-wrap gap-2">
                  {modelMetadata.tags.map((tag) => (
                    <Badge key={tag} variant="secondary" className="flex items-center space-x-1">
                      <span>{tag}</span>
                      <button
                        onClick={() => removeTag(tag)}
                        className="ml-1 hover:text-destructive"
                      >
                        <X className="h-3 w-3" />
                      </button>
                    </Badge>
                  ))}
                </div>
              )}
            </div>

            <div className="flex justify-between">
              <Button variant="outline" onClick={() => setCurrentStep(1)}>
                Back
              </Button>
              <Button onClick={() => setCurrentStep(3)}>
                Next: Review
              </Button>
            </div>
          </CardContent>
        </Card>
      )}

      {/* Step 3: Review */}
      {currentStep === 3 && (
        <Card>
          <CardHeader>
            <CardTitle>Review & Submit</CardTitle>
          </CardHeader>
          <CardContent className="space-y-6">
            <div className="space-y-4">
              <div>
                <h4 className="font-medium mb-2">Uploaded Files</h4>
                <div className="space-y-2">
                  {uploadedFiles.map((file) => (
                    <div key={file.id} className="flex items-center space-x-2 p-2 border rounded">
                      <span>{getFileIcon(file.name)}</span>
                      <span className="font-medium">{file.name}</span>
                      <span className="text-sm text-muted-foreground">
                        ({formatFileSize(file.size)})
                      </span>
                      {file.status === 'success' && (
                        <CheckCircle className="h-4 w-4 text-green-500" />
                      )}
                    </div>
                  ))}
                </div>
              </div>

              <div>
                <h4 className="font-medium mb-2">Model Metadata</h4>
                <div className="grid grid-cols-1 md:grid-cols-2 gap-4 text-sm">
                  <div>
                    <span className="text-muted-foreground">Name:</span>
                    <p className="font-medium">{modelMetadata.name}</p>
                  </div>
                  <div>
                    <span className="text-muted-foreground">Version:</span>
                    <p className="font-medium">{modelMetadata.version}</p>
                  </div>
                  <div>
                    <span className="text-muted-foreground">Type:</span>
                    <p className="font-medium">{modelMetadata.type}</p>
                  </div>
                  <div>
                    <span className="text-muted-foreground">Framework:</span>
                    <p className="font-medium">{modelMetadata.framework}</p>
                  </div>
                  <div>
                    <span className="text-muted-foreground">Company:</span>
                    <p className="font-medium">{modelMetadata.company}</p>
                  </div>
                  <div>
                    <span className="text-muted-foreground">Risk Level:</span>
                    <p className="font-medium">{modelMetadata.risk_level}</p>
                  </div>
                  <div className="md:col-span-2">
                    <span className="text-muted-foreground">Description:</span>
                    <p className="font-medium">{modelMetadata.description}</p>
                  </div>
                  {modelMetadata.tags.length > 0 && (
                    <div className="md:col-span-2">
                      <span className="text-muted-foreground">Tags:</span>
                      <div className="flex flex-wrap gap-1 mt-1">
                        {modelMetadata.tags.map((tag) => (
                          <Badge key={tag} variant="secondary">
                            {tag}
                          </Badge>
                        ))}
                      </div>
                    </div>
                  )}
                </div>
              </div>
            </div>

            <Alert>
              <Info className="h-4 w-4" />
              <AlertDescription>
                By submitting this model, you agree to our governance policies and confirm that this model has been tested for bias and compliance.
              </AlertDescription>
            </Alert>

            <div className="flex justify-between">
              <Button variant="outline" onClick={() => setCurrentStep(2)}>
                Back
              </Button>
              <Button onClick={handleSubmit}>
                Submit Model
              </Button>
            </div>
          </CardContent>
        </Card>
      )}
    </div>
  )
} 