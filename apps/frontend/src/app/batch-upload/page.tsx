'use client'

import React, { useState } from 'react'

interface UploadFile {
  id: string
  name: string
  size: number
  type: string
  status: 'pending' | 'uploading' | 'completed' | 'error'
  progress: number
  error?: string
}

export default function BatchUpload() {
  const [files, setFiles] = useState<UploadFile[]>([])
  const [dragActive, setDragActive] = useState(false)
  const [uploading, setUploading] = useState(false)

  const handleDrag = (e: React.DragEvent) => {
    e.preventDefault()
    e.stopPropagation()
    if (e.type === 'dragenter' || e.type === 'dragover') {
      setDragActive(true)
    } else if (e.type === 'dragleave') {
      setDragActive(false)
    }
  }

  const handleDrop = (e: React.DragEvent) => {
    e.preventDefault()
    e.stopPropagation()
    setDragActive(false)
    
    if (e.dataTransfer.files && e.dataTransfer.files[0]) {
      const newFiles = Array.from(e.dataTransfer.files).map((file, index) => ({
        id: `file-${Date.now()}-${index}`,
        name: file.name,
        size: file.size,
        type: file.type,
        status: 'pending' as const,
        progress: 0
      }))
      setFiles(prev => [...prev, ...newFiles])
    }
  }

  const handleFileSelect = (e: React.ChangeEvent<HTMLInputElement>) => {
    if (e.target.files && e.target.files[0]) {
      const newFiles = Array.from(e.target.files).map((file, index) => ({
        id: `file-${Date.now()}-${index}`,
        name: file.name,
        size: file.size,
        type: file.type,
        status: 'pending' as const,
        progress: 0
      }))
      setFiles(prev => [...prev, ...newFiles])
    }
  }

  const startUpload = async () => {
    setUploading(true)
    
    for (const file of files) {
      if (file.status === 'pending') {
        // Simulate upload progress
        setFiles(prev => prev.map(f => 
          f.id === file.id ? { ...f, status: 'uploading' } : f
        ))
        
        for (let i = 0; i <= 100; i += 10) {
          await new Promise(resolve => setTimeout(resolve, 200))
          setFiles(prev => prev.map(f => 
            f.id === file.id ? { ...f, progress: i } : f
          ))
        }
        
        setFiles(prev => prev.map(f => 
          f.id === file.id ? { ...f, status: 'completed' } : f
        ))
      }
    }
    
    setUploading(false)
  }

  const removeFile = (id: string) => {
    setFiles(prev => prev.filter(f => f.id !== id))
  }

  const formatFileSize = (bytes: number) => {
    if (bytes === 0) return '0 Bytes'
    const k = 1024
    const sizes = ['Bytes', 'KB', 'MB', 'GB']
    const i = Math.floor(Math.log(bytes) / Math.log(k))
    return parseFloat((bytes / Math.pow(k, i)).toFixed(2)) + ' ' + sizes[i]
  }

  const getStatusColor = (status: string) => {
    switch (status) {
      case 'completed': return 'text-green-400'
      case 'uploading': return 'text-yellow-400'
      case 'error': return 'text-red-400'
      default: return 'text-muted-foreground'
    }
  }

  return (
    <div className="space-y-6 p-4 md:p-6 max-w-[2000px] mx-auto">
      {/* Header */}
      <div className="space-y-2">
        <h1 className="text-2xl md:text-3xl font-bold tracking-tight text-gold">
          Batch Upload
        </h1>
        <p className="text-xs md:text-sm text-muted-foreground font-mono">
          Upload Multiple Models Simultaneously
        </p>
      </div>

      {/* Upload Area */}
      <div className="bg-card border border-border rounded-lg p-6">
        <div
          className={`border-2 border-dashed rounded-lg p-8 text-center transition-colors ${
            dragActive 
              ? 'border-gold bg-gold/5' 
              : 'border-border hover:border-gold/50'
          }`}
          onDragEnter={handleDrag}
          onDragLeave={handleDrag}
          onDragOver={handleDrag}
          onDrop={handleDrop}
        >
          <div className="space-y-4">
            <svg className="w-12 h-12 mx-auto text-muted-foreground" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M7 16a4 4 0 01-.88-7.903A5 5 0 1115.9 6L16 6a5 5 0 011 9.9M15 13l-3-3m0 0l-3 3m3-3v12" />
            </svg>
            <div>
              <h3 className="text-lg font-bold text-foreground">DRAG_AND_DROP_FILES</h3>
              <p className="text-sm text-muted-foreground font-mono">OR_CLICK_TO_SELECT_FILES</p>
            </div>
            <input
              type="file"
              multiple
              onChange={handleFileSelect}
              className="hidden"
              id="file-upload"
              accept=".json,.yaml,.yml,.txt,.csv,.zip,.tar.gz"
            />
            <label
              htmlFor="file-upload"
              className="inline-flex items-center gap-2 px-4 py-2 bg-gold text-gold-foreground rounded-md font-mono text-sm cursor-pointer hover:bg-gold/90 transition-colors"
            >
              <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 4v16m8-8H4" />
              </svg>
              SELECT_FILES
            </label>
          </div>
        </div>
      </div>

      {/* File List */}
      {files.length > 0 && (
        <div className="bg-card border border-border rounded-lg overflow-hidden">
          <div className="p-4 border-b border-border">
            <div className="flex items-center justify-between">
              <div>
                <h3 className="text-sm font-bold text-gold">SELECTED_FILES</h3>
                <p className="text-xs text-muted-foreground font-mono">
                  {files.length} {files.length === 1 ? 'FILE' : 'FILES'} SELECTED
                </p>
              </div>
              <div className="flex gap-2">
                <button
                  onClick={() => setFiles([])}
                  className="px-3 py-1 text-xs font-mono text-muted-foreground hover:text-foreground transition-colors"
                >
                  CLEAR_ALL
                </button>
                <button
                  onClick={startUpload}
                  disabled={uploading || files.every(f => f.status === 'completed')}
                  className="px-3 py-1 text-xs font-mono bg-gold text-gold-foreground rounded hover:bg-gold/90 transition-colors disabled:opacity-50 disabled:cursor-not-allowed"
                >
                  {uploading ? 'UPLOADING...' : 'START_UPLOAD'}
                </button>
              </div>
            </div>
          </div>
          <div className="p-4">
            <div className="space-y-3">
              {files.map((file) => (
                <div key={file.id} className="flex items-center justify-between p-3 bg-muted/50 rounded-lg">
                  <div className="flex items-center gap-3 flex-1 min-w-0">
                    <svg className="w-5 h-5 text-muted-foreground flex-shrink-0" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 12h6m-6 4h6m2 5H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z" />
                    </svg>
                    <div className="flex-1 min-w-0">
                      <p className="text-sm font-mono text-foreground truncate">{file.name}</p>
                      <p className="text-xs text-muted-foreground">{formatFileSize(file.size)}</p>
                    </div>
                  </div>
                  <div className="flex items-center gap-3">
                    {file.status === 'uploading' && (
                      <div className="w-20 bg-muted rounded-full h-2">
                        <div
                          className="bg-gold h-2 rounded-full transition-all duration-300"
                          style={{ width: `${file.progress}%` }}
                        ></div>
                      </div>
                    )}
                    <span className={`text-xs font-mono ${getStatusColor(file.status)}`}>
                      {file.status.toUpperCase()}
                    </span>
                    <button
                      onClick={() => removeFile(file.id)}
                      className="text-muted-foreground hover:text-foreground transition-colors"
                    >
                      <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M6 18L18 6M6 6l12 12" />
                      </svg>
                    </button>
                  </div>
                </div>
              ))}
            </div>
          </div>
        </div>
      )}

      {/* Upload Summary */}
      {files.length > 0 && (
        <div className="grid gap-4 sm:grid-cols-3">
          <div className="bg-card border border-border rounded-lg p-4">
            <div className="flex items-center justify-between">
              <div>
                <p className="text-xs text-muted-foreground font-mono">TOTAL_FILES</p>
                <p className="text-lg font-bold text-foreground">{files.length}</p>
              </div>
              <svg className="h-4 w-4 text-gold" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 12h6m-6 4h6m2 5H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z" />
              </svg>
            </div>
          </div>
          <div className="bg-card border border-border rounded-lg p-4">
            <div className="flex items-center justify-between">
              <div>
                <p className="text-xs text-muted-foreground font-mono">COMPLETED</p>
                <p className="text-lg font-bold text-foreground">
                  {files.filter(f => f.status === 'completed').length}
                </p>
              </div>
              <svg className="h-4 w-4 text-gold" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 12l2 2 4-4m5.618-4.016A11.955 11.955 0 0112 2.944a11.955 11.955 0 01-8.618 3.04A12.02 12.02 0 003 9c0 5.591 3.824 10.29 9 11.622 5.176-1.332 9-6.03 9-11.622 0-1.042-.133-2.052-.382-3.016z" />
              </svg>
            </div>
          </div>
          <div className="bg-card border border-border rounded-lg p-4">
            <div className="flex items-center justify-between">
              <div>
                <p className="text-xs text-muted-foreground font-mono">TOTAL_SIZE</p>
                <p className="text-lg font-bold text-foreground">
                  {formatFileSize(files.reduce((acc, f) => acc + f.size, 0))}
                </p>
              </div>
              <svg className="h-4 w-4 text-gold" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M4 7v10c0 2.21 3.582 4 8 4s8-1.79 8-4V7M4 7c0 2.21 3.582 4 8 4s8-1.79 8-4M4 7c0-2.21 3.582-4 8-4s8 1.79 8 4" />
              </svg>
            </div>
          </div>
        </div>
      )}
    </div>
  )
}
