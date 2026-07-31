'use client'

import { useState, useRef } from 'react'
import Link from 'next/link'
import { useDatasets } from '@/lib/api/hooks/useDatasets'
import { Card } from '@/components/ui/card'
import { Button } from '@/components/ui/button'
import { Input } from '@/components/ui/input'
import { Label } from '@/components/ui/label'
import { Textarea } from '@/components/ui/textarea'
import { Table, TableBody, TableCell, TableHead, TableHeader, TableRow } from '@/components/ui/table'
import { Badge } from '@/components/ui/badge'
import { Alert, AlertDescription, AlertTitle } from '@/components/ui/alert'
import { Skeleton } from '@/components/ui/skeleton'
import { Dialog, DialogContent, DialogDescription, DialogHeader, DialogTitle, DialogTrigger } from '@/components/ui/dialog'
import { useToast } from '@/hooks/use-toast'
import { IconUpload, IconDatabase, IconFileText, IconAlertTriangle, IconCheck, IconX } from '@tabler/icons-react'
import type { Dataset } from '@/lib/api/hooks/useDatasets'

export default function DatasetsPage() {
  const { datasets, loading, error, uploadDataset, refetch } = useDatasets()
  const { toast } = useToast()
  const fileInputRef = useRef<HTMLInputElement>(null)
  const [dialogOpen, setDialogOpen] = useState(false)
  const [uploading, setUploading] = useState(false)
  const [uploadForm, setUploadForm] = useState({
    name: '',
    description: '',
    file: null as File | null,
  })

  const handleFileSelect = (e: React.ChangeEvent<HTMLInputElement>) => {
    const file = e.target.files?.[0]
    if (file) {
      if (!file.name.match(/\.(csv|parquet)$/i)) {
        toast({
          title: "Invalid file type",
          description: "Please upload a CSV or Parquet file",
          variant: "destructive",
        })
        return
      }
      setUploadForm({ ...uploadForm, file, name: uploadForm.name || file.name.replace(/\.(csv|parquet)$/i, '') })
    }
  }

  const handleUpload = async (e: React.FormEvent) => {
    e.preventDefault()
    if (!uploadForm.file) {
      toast({
        title: "No file selected",
        description: "Please select a file to upload",
        variant: "destructive",
      })
      return
    }

    try {
      setUploading(true)
      await uploadDataset(uploadForm.file, uploadForm.name || undefined, uploadForm.description || undefined)
      toast({
        title: "Dataset uploaded",
        description: "Dataset has been uploaded successfully",
      })
      setDialogOpen(false)
      setUploadForm({ name: '', description: '', file: null })
      if (fileInputRef.current) {
        fileInputRef.current.value = ''
      }
      refetch()
    } catch (err) {
      toast({
        title: "Upload failed",
        description: err instanceof Error ? err.message : "Failed to upload dataset",
        variant: "destructive",
      })
    } finally {
      setUploading(false)
    }
  }

  const formatDate = (dateString: string) => {
    return new Date(dateString).toLocaleDateString('en-US', {
      year: 'numeric',
      month: 'short',
      day: 'numeric',
    })
  }

  if (loading && datasets.length === 0) {
    return (
      <div className="space-y-6">
        <Skeleton className="h-10 w-48" />
        <div className="space-y-4">
          {[...Array(3)].map((_, i) => (
            <Skeleton key={i} className="h-24" />
          ))}
        </div>
      </div>
    )
  }

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-4xl font-bold">Datasets</h1>
          <p className="text-muted-foreground mt-1">
            Upload and manage datasets for bias detection and analysis
          </p>
        </div>
        <Dialog open={dialogOpen} onOpenChange={setDialogOpen}>
          <DialogTrigger asChild>
            <Button variant="default" className="border-2 border-black shadow-brutal">
              <IconUpload className="mr-2 h-4 w-4" />
              Upload Dataset
            </Button>
          </DialogTrigger>
          <DialogContent className="border-4 border-black shadow-brutal-lg">
            <DialogHeader>
              <DialogTitle>Upload Dataset</DialogTitle>
              <DialogDescription>
                Upload a CSV or Parquet file for bias detection analysis
              </DialogDescription>
            </DialogHeader>
            <form onSubmit={handleUpload} className="space-y-4">
              <div className="space-y-2">
                <Label htmlFor="file">Dataset File *</Label>
                <Input
                  id="file"
                  type="file"
                  accept=".csv,.parquet"
                  onChange={handleFileSelect}
                  ref={fileInputRef}
                  className="border-2 border-black"
                  required
                />
                {uploadForm.file && (
                  <p className="text-sm text-muted-foreground">
                    Selected: {uploadForm.file.name} ({(uploadForm.file.size / 1024 / 1024).toFixed(2)} MB)
                  </p>
                )}
              </div>
              <div className="space-y-2">
                <Label htmlFor="name">Dataset Name</Label>
                <Input
                  id="name"
                  value={uploadForm.name}
                  onChange={(e) => setUploadForm({ ...uploadForm, name: e.target.value })}
                  placeholder="Enter dataset name"
                  className="border-2 border-black"
                />
              </div>
              <div className="space-y-2">
                <Label htmlFor="description">Description</Label>
                <Textarea
                  id="description"
                  value={uploadForm.description}
                  onChange={(e) => setUploadForm({ ...uploadForm, description: e.target.value })}
                  placeholder="Enter dataset description"
                  className="border-2 border-black"
                  rows={3}
                />
              </div>
              <div className="flex gap-2 justify-end">
                <Button
                  type="button"
                  variant="noShadow"
                  onClick={() => setDialogOpen(false)}
                  className="border-2 border-black"
                >
                  Cancel
                </Button>
                <Button type="submit" disabled={uploading || !uploadForm.file}>
                  {uploading ? 'Uploading...' : 'Upload'}
                </Button>
              </div>
            </form>
          </DialogContent>
        </Dialog>
      </div>

      {error && (
        <Alert className="border-2 border-red-500 shadow-brutal">
          <IconAlertTriangle className="h-4 w-4" />
          <AlertTitle>Error</AlertTitle>
          <AlertDescription>{error}</AlertDescription>
        </Alert>
      )}

      {/* Datasets Table */}
      {datasets.length === 0 ? (
        <Card className="p-12 border-2 border-black shadow-brutal">
          <div className="text-center">
            <IconDatabase className="h-16 w-16 mx-auto mb-4 text-muted-foreground opacity-50" />
            <h3 className="text-xl font-bold mb-2">No datasets yet</h3>
            <p className="text-muted-foreground mb-4">
              Upload your first dataset to start bias detection analysis
            </p>
            <Button
              variant="default"
              onClick={() => setDialogOpen(true)}
              className="border-2 border-black shadow-brutal"
            >
              <IconUpload className="mr-2 h-4 w-4" />
              Upload Dataset
            </Button>
          </div>
        </Card>
      ) : (
        <Card className="p-6 border-2 border-black shadow-brutal">
          <Table>
            <TableHeader>
              <TableRow>
                <TableHead>Name</TableHead>
                <TableHead>Type</TableHead>
                <TableHead>Rows</TableHead>
                <TableHead>Columns</TableHead>
                <TableHead>Created</TableHead>
                <TableHead>Status</TableHead>
                <TableHead></TableHead>
              </TableRow>
            </TableHeader>
            <TableBody>
              {datasets.map((dataset: Dataset) => (
                <TableRow key={dataset.id} className="hover:bg-muted/50 cursor-pointer">
                  <TableCell className="font-medium">
                    <div>
                      <p>{dataset.name}</p>
                      {dataset.description && (
                        <p className="text-sm text-muted-foreground">{dataset.description}</p>
                      )}
                    </div>
                  </TableCell>
                  <TableCell>
                    <Badge variant="secondary" className="border-2 border-black">
                      {dataset.file_type.toUpperCase()}
                    </Badge>
                  </TableCell>
                  <TableCell>{dataset.row_count?.toLocaleString() || 'N/A'}</TableCell>
                  <TableCell>{dataset.column_count || 'N/A'}</TableCell>
                  <TableCell>{formatDate(dataset.created_at)}</TableCell>
                  <TableCell>
                    <Badge variant="default" className="border-2 border-black bg-green-500">
                      <IconCheck className="h-3 w-3 mr-1" />
                      Active
                    </Badge>
                  </TableCell>
                  <TableCell>
                    <Link href={`/dashboard/datasets/${dataset.id}`}>
                      <Button variant="neutral" size="sm">
                        View
                      </Button>
                    </Link>
                  </TableCell>
                </TableRow>
              ))}
            </TableBody>
          </Table>
        </Card>
      )}
    </div>
  )
}
