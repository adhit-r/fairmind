"use client"

import React, { useState, useCallback } from 'react'
import { useDropzone } from 'react-dropzone'
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/common/card'
import { Button } from '@/components/ui/common/button'
import { Input } from '@/components/ui/common/input'
import { Label } from '@/components/ui/common/label'
import { Textarea } from '@/components/ui/common/textarea'
import { Badge } from '@/components/ui/common/badge'
import { Alert, AlertDescription } from '@/components/ui/common/alert'
import { 
  Upload, 
  FileText, 
  CheckCircle, 
  AlertTriangle, 
  X,
  Database,
  Info
} from 'lucide-react'

interface ModelUploadProps {
  onUploadComplete?: (model: any) => void
  onCancel?: () => void
}

interface UploadedFile {
  file: File
  id: string
  status: 'uploading' | 'success' | 'error'
  progress: number
  error?: string
}

const SUPPORTED_FORMATS = [
  '.pkl', '.joblib', '.h5', '.hdf5', '.onnx', '.pb', '.pt', '.pth', 
  '.safetensors', '.tflite', '.mlmodel'
]

const MAX_FILE_SIZE = 500 * 1024 * 1024 // 500MB

export function ModelUpload({ onUploadComplete, onCancel }: ModelUploadProps) {
  const [uploadedFiles, setUploadedFiles] = useState<UploadedFile[]>([])
  const [modelMetadata, setModelMetadata] = useState({
    name: '',
    version: '',
    description: '',
    type: '',
    framework: '',
    tags: ''
  })
  const [isUploading, setIsUploading] = useState(false)
  const [uploadError, setUploadError] = useState<string | null>(null)

  const onDrop = useCallback((acceptedFiles: File[], rejectedFiles: any[]) => {
    setUploadError(null)
    
    // Handle rejected files
    if (rejectedFiles.length > 0) {
      const errors = rejectedFiles.map(({ file, errors }) => {
        const errorMessages = errors.map((e: any) => e.message).join(', ')
        return `${file.name}: ${errorMessages}`
      })
      setUploadError(`Upload rejected: ${errors.join('; ')}`)
      return
    }

    // Add accepted files
    const newFiles: UploadedFile[] = acceptedFiles.map(file => ({
      file,
      id: Math.random().toString(36).substr(2, 9),
      status: 'uploading',
      progress: 0
    }))

    setUploadedFiles(prev => [...prev, ...newFiles])

    // Simulate upload progress
    newFiles.forEach(file => {
      simulateUpload(file.id)
    })
  }, [])

  const simulateUpload = (fileId: string) => {
    const interval = setInterval(() => {
      setUploadedFiles(prev => prev.map(file => {
        if (file.id === fileId) {
          const newProgress = Math.min(file.progress + Math.random() * 20, 100)
          const newStatus = newProgress >= 100 ? 'success' : 'uploading'
          
          if (newStatus === 'success') {
            clearInterval(interval)
          }
          
          return { ...file, progress: newProgress, status: newStatus }
        }
        return file
      }))
    }, 200)
  }

  const removeFile = (fileId: string) => {
    setUploadedFiles(prev => prev.filter(file => file.id !== fileId))
  }

  const { getRootProps, getInputProps, isDragActive } = useDropzone({
    onDrop,
    accept: {
      'application/octet-stream': SUPPORTED_FORMATS,
      'application/x-python-code': ['.py'],
      'text/plain': ['.txt', '.json', '.yaml', '.yml']
    },
    maxSize: MAX_FILE_SIZE,
    multiple: true
  })

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault()
    
    if (uploadedFiles.length === 0) {
      setUploadError('Please upload at least one model file')
      return
    }

    if (!modelMetadata.name || !modelMetadata.version) {
      setUploadError('Please provide model name and version')
      return
    }

    setIsUploading(true)
    setUploadError(null)

    try {
      // Simulate API call
      await new Promise(resolve => setTimeout(resolve, 2000))

      const model = {
        id: Math.random().toString(36).substr(2, 9),
        name: modelMetadata.name,
        version: modelMetadata.version,
        description: modelMetadata.description,
        type: modelMetadata.type || 'custom',
        framework: modelMetadata.framework || 'unknown',
        tags: modelMetadata.tags.split(',').map(tag => tag.trim()).filter(Boolean),
        files: uploadedFiles.map(f => f.file.name),
        uploadDate: new Date().toISOString(),
        status: 'testing'
      }

      onUploadComplete?.(model)
    } catch (error) {
      setUploadError('Failed to upload model. Please try again.')
    } finally {
      setIsUploading(false)
    }
  }

  const getFileIcon = (fileName: string) => {
    const ext = fileName.toLowerCase().split('.').pop()
    switch (ext) {
      case 'pkl':
      case 'joblib':
        return '🐍'
      case 'h5':
      case 'hdf5':
        return '📊'
      case 'onnx':
        return '🔄'
      case 'pb':
        return '🧠'
      case 'pt':
      case 'pth':
        return '🔥'
      default:
        return '📄'
    }
  }

  return (
    <div className="max-w-4xl mx-auto space-y-6">
      <div className="text-center">
        <h2 className="text-2xl font-bold text-gray-900 mb-2">Upload ML Model</h2>
        <p className="text-gray-600">Add your machine learning models to the SQ1 registry</p>
      </div>

      <form onSubmit={handleSubmit} className="space-y-6">
        {/* File Upload Area */}
        <Card>
          <CardHeader>
            <CardTitle className="flex items-center">
              <Upload className="w-5 h-5 mr-2" />
              Model Files
            </CardTitle>
          </CardHeader>
          <CardContent>
            <div
              {...getRootProps()}
              className={`border-2 border-dashed rounded-lg p-8 text-center cursor-pointer transition-colors ${
                isDragActive 
                  ? 'border-blue-500 bg-blue-50' 
                  : 'border-gray-300 hover:border-gray-400'
              }`}
            >
              <input {...getInputProps()} />
              <Upload className="w-12 h-12 text-gray-400 mx-auto mb-4" />
              {isDragActive ? (
                <p className="text-blue-600 font-medium">Drop the files here...</p>
              ) : (
                <div>
                  <p className="text-gray-600 mb-2">
                    Drag & drop model files here, or <span className="text-blue-600 font-medium">click to browse</span>
                  </p>
                  <p className="text-sm text-gray-500">
                    Supported formats: {SUPPORTED_FORMATS.join(', ')}
                  </p>
                  <p className="text-sm text-gray-500">Max file size: 500MB</p>
                </div>
              )}
            </div>

            {/* Uploaded Files */}
            {uploadedFiles.length > 0 && (
              <div className="mt-6 space-y-3">
                <h4 className="font-medium text-gray-900">Uploaded Files</h4>
                {uploadedFiles.map((file) => (
                  <div key={file.id} className="flex items-center justify-between p-3 bg-gray-50 rounded-lg">
                    <div className="flex items-center space-x-3">
                      <span className="text-2xl">{getFileIcon(file.file.name)}</span>
                      <div>
                        <p className="font-medium text-sm">{file.file.name}</p>
                        <p className="text-xs text-gray-500">
                          {(file.file.size / 1024 / 1024).toFixed(2)} MB
                        </p>
                      </div>
                    </div>
                    <div className="flex items-center space-x-2">
                      {file.status === 'uploading' && (
                        <div className="flex items-center space-x-2">
                          <div className="w-16 bg-gray-200 rounded-full h-2">
                            <div 
                              className="bg-blue-600 h-2 rounded-full transition-all duration-300"
                              style={{ width: `${file.progress}%` }}
                            />
                          </div>
                          <span className="text-xs text-gray-500">{Math.round(file.progress)}%</span>
                        </div>
                      )}
                      {file.status === 'success' && (
                        <CheckCircle className="w-5 h-5 text-green-600" />
                      )}
                      {file.status === 'error' && (
                        <AlertTriangle className="w-5 h-5 text-red-600" />
                      )}
                      <Button
                        type="button"
                        variant="ghost"
                        size="sm"
                        onClick={() => removeFile(file.id)}
                        className="text-gray-400 hover:text-red-600"
                      >
                        <X className="w-4 h-4" />
                      </Button>
                    </div>
                  </div>
                ))}
              </div>
            )}
          </CardContent>
        </Card>

        {/* Model Metadata */}
        <Card>
          <CardHeader>
            <CardTitle className="flex items-center">
              <Database className="w-5 h-5 mr-2" />
              Model Information
            </CardTitle>
          </CardHeader>
          <CardContent className="space-y-4">
            <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
              <div>
                <Label htmlFor="name">Model Name *</Label>
                <Input
                  id="name"
                  value={modelMetadata.name}
                  onChange={(e) => setModelMetadata(prev => ({ ...prev, name: e.target.value }))}
                  placeholder="e.g., Credit Risk Model v2.1"
                  required
                />
              </div>
              <div>
                <Label htmlFor="version">Version *</Label>
                <Input
                  id="version"
                  value={modelMetadata.version}
                  onChange={(e) => setModelMetadata(prev => ({ ...prev, version: e.target.value }))}
                  placeholder="e.g., 2.1.0"
                  required
                />
              </div>
            </div>

            <div>
              <Label htmlFor="description">Description</Label>
              <Textarea
                id="description"
                value={modelMetadata.description}
                onChange={(e) => setModelMetadata(prev => ({ ...prev, description: e.target.value }))}
                placeholder="Describe what this model does, its purpose, and key features..."
                rows={3}
              />
            </div>

            <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
              <div>
                <Label htmlFor="type">Model Type</Label>
                <Input
                  id="type"
                  value={modelMetadata.type}
                  onChange={(e) => setModelMetadata(prev => ({ ...prev, type: e.target.value }))}
                  placeholder="e.g., Classification, Regression, NLP"
                />
              </div>
              <div>
                <Label htmlFor="framework">Framework</Label>
                <Input
                  id="framework"
                  value={modelMetadata.framework}
                  onChange={(e) => setModelMetadata(prev => ({ ...prev, framework: e.target.value }))}
                  placeholder="e.g., TensorFlow, PyTorch, Scikit-learn"
                />
              </div>
            </div>

            <div>
              <Label htmlFor="tags">Tags</Label>
              <Input
                id="tags"
                value={modelMetadata.tags}
                onChange={(e) => setModelMetadata(prev => ({ ...prev, tags: e.target.value }))}
                placeholder="e.g., finance, credit-risk, production, experimental"
              />
              <p className="text-xs text-gray-500 mt-1">
                Separate tags with commas
              </p>
            </div>
          </CardContent>
        </Card>

        {/* Error Display */}
        {uploadError && (
          <Alert variant="destructive">
            <AlertTriangle className="h-4 w-4" />
            <AlertDescription>{uploadError}</AlertDescription>
          </Alert>
        )}

        {/* Info Alert */}
        <Alert>
          <Info className="h-4 w-4" />
          <AlertDescription>
            After upload, your model will be automatically tested for bias, security vulnerabilities, 
            and compliance issues. You'll receive detailed reports and recommendations.
          </AlertDescription>
        </Alert>

        {/* Action Buttons */}
        <div className="flex justify-end space-x-4">
          <Button
            type="button"
            variant="outline"
            onClick={onCancel}
            disabled={isUploading}
          >
            Cancel
          </Button>
          <Button
            type="submit"
            disabled={isUploading || uploadedFiles.length === 0}
            className="min-w-[120px]"
          >
            {isUploading ? (
              <>
                <div className="animate-spin rounded-full h-4 w-4 border-b-2 border-white mr-2" />
                Uploading...
              </>
            ) : (
              <>
                <Upload className="w-4 h-4 mr-2" />
                Upload Model
              </>
            )}
          </Button>
        </div>
      </form>
    </div>
  )
}
