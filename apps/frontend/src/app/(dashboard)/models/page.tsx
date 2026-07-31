'use client'

import { useState } from 'react'
import { useModels } from '@/lib/api/hooks/useModels'
import { useAIGovernance } from '@/lib/api/hooks/useAIGovernance'
import { Card } from '@/components/ui/card'
import { Button } from '@/components/ui/button'
import { Table, TableBody, TableCell, TableHead, TableHeader, TableRow } from '@/components/ui/table'
import { Badge } from '@/components/ui/badge'
import { Skeleton } from '@/components/ui/skeleton'
import { Alert, AlertDescription } from '@/components/ui/alert'
import { Dialog, DialogContent, DialogDescription, DialogFooter, DialogHeader, DialogTitle, DialogTrigger } from '@/components/ui/dialog'
import { Input } from '@/components/ui/input'
import { Label } from '@/components/ui/label'
import { Textarea } from '@/components/ui/textarea'
import { useToast } from '@/hooks/use-toast'
import {
  IconBrain,
  IconPlus,
  IconUpload,
  IconAlertTriangle,
  IconCheck,
  IconX,
} from '@tabler/icons-react';
import Link from 'next/link';
import { useModelUpload } from '@/lib/api/hooks/useModelUpload';

// Hook and handler will be defined inside the component

export default function ModelsPage() {
  const { data: models, loading, error, refetch } = useModels()
  const { registerModel, loading: registering } = useAIGovernance()
  const { toast } = useToast()
  const [dialogOpen, setDialogOpen] = useState(false)
  // Model upload hook
  const { uploadModel, uploading, progress, error: uploadError, reset: resetUpload } = useModelUpload();
  const handleFileChange = async (e: React.ChangeEvent<HTMLInputElement>) => {
    const file = e.target.files?.[0];
    if (!file) return;
    try {
      const result = await uploadModel(file);
      toast({
        title: 'Model uploaded',
        description: `Model ID: ${(result as any).model_id}`,
      });
      refetch();
    } catch (err) {
      toast({
        title: 'Upload failed',
        description: err instanceof Error ? err.message : 'Unexpected error',
        variant: 'destructive',
      });
    } finally {
      resetUpload();
    }
  };
  const [formData, setFormData] = useState({
    model_id: '',
    name: '',
    model_type: '',
    version: '',
    description: '',
    capabilities: '',
    input_format: '',
    output_format: '',
  })

  const handleRegister = async (e: React.FormEvent) => {
    e.preventDefault()
    try {
      const capabilities = formData.capabilities.split(',').map(c => c.trim()).filter(c => c)
      await registerModel({
        model_id: formData.model_id,
        name: formData.name,
        model_type: formData.model_type,
        version: formData.version,
        description: formData.description,
        capabilities,
        input_format: formData.input_format,
        output_format: formData.output_format,
      })
      toast({
        title: "Model registered",
        description: "The model has been successfully registered.",
      })
      setDialogOpen(false)
      setFormData({
        model_id: '',
        name: '',
        model_type: '',
        version: '',
        description: '',
        capabilities: '',
        input_format: '',
        output_format: '',
      })
      refetch()
    } catch (err) {
      toast({
        title: "Registration failed",
        description: err instanceof Error ? err.message : "An error occurred",
        variant: "destructive",
      })
    }
  }

  const getStatusBadge = (status: string) => {
    const variants: Record<string, { variant: 'default' | 'secondary' | 'destructive', label: string }> = {
      active: { variant: 'default', label: 'Active' },
      inactive: { variant: 'secondary', label: 'Inactive' },
      deprecated: { variant: 'destructive', label: 'Deprecated' },
    }
    const config = variants[status] || variants.inactive
    return <Badge variant={config.variant} className="border-2 border-black">{config.label}</Badge>
  }

  if (loading) {
    return (
      <div className="space-y-6">
        <Skeleton className="h-10 w-48" />
        <Skeleton className="h-96" />
      </div>
    )
  }

  if (error) {
    return (
      <Alert className="border-2 border-red-500 shadow-brutal">
        <IconAlertTriangle className="h-4 w-4" />
        <AlertDescription>{error.message}</AlertDescription>
      </Alert>
    )
  }

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-4xl font-bold">Model Registry</h1>
          <p className="text-muted-foreground mt-1">
            Manage and monitor your AI models
          </p>
        </div>
        <div className="flex gap-2">

          <div className="flex items-center gap-2">
            <input
              type="file"
              accept=".pkl,.h5,.pt,.pth,.onnx,.joblib,.keras"
              id="model-upload-input"
              className="hidden"
              onChange={handleFileChange}
            />
            <label htmlFor="model-upload-input" className="cursor-pointer">
              <Button variant="default" disabled={uploading}>
                <IconUpload className="mr-2 h-4 w-4" />
                {uploading ? 'Uploading...' : 'Upload Model'}
              </Button>
            </label>
            {uploading && progress && (
              <div className="w-32 text-sm">
                {progress.percentage}%
              </div>
            )}
            {uploadError && (
              <Alert variant="destructive" className="mt-2">
                <AlertDescription>{uploadError}</AlertDescription>
              </Alert>
            )}
          </div>
          <Dialog open={dialogOpen} onOpenChange={setDialogOpen}>
            <DialogTrigger asChild>
              <Button variant="default">
                <IconPlus className="mr-2 h-4 w-4" />
                Register Model
              </Button>
            </DialogTrigger>
            <DialogContent className="border-2 border-black shadow-brutal max-w-2xl max-h-[90vh] overflow-y-auto">
              <DialogHeader>
                <DialogTitle className="text-2xl font-bold">Register New Model</DialogTitle>
                <DialogDescription>
                  Register a new AI model in the governance system
                </DialogDescription>
              </DialogHeader>
              <form onSubmit={handleRegister} className="space-y-4">
                <div className="grid grid-cols-2 gap-4">
                  <div className="space-y-2">
                    <Label htmlFor="model_id">Model ID *</Label>
                    <Input
                      id="model_id"
                      value={formData.model_id}
                      onChange={(e) => setFormData({ ...formData, model_id: e.target.value })}
                      placeholder="model-001"
                      required
                      className="border-2 border-black"
                    />
                  </div>
                  <div className="space-y-2">
                    <Label htmlFor="name">Name *</Label>
                    <Input
                      id="name"
                      value={formData.name}
                      onChange={(e) => setFormData({ ...formData, name: e.target.value })}
                      placeholder="Credit Risk Model"
                      required
                      className="border-2 border-black"
                    />
                  </div>
                </div>
                <div className="grid grid-cols-2 gap-4">
                  <div className="space-y-2">
                    <Label htmlFor="model_type">Model Type *</Label>
                    <Input
                      id="model_type"
                      value={formData.model_type}
                      onChange={(e) => setFormData({ ...formData, model_type: e.target.value })}
                      placeholder="llm, classification, etc."
                      required
                      className="border-2 border-black"
                    />
                  </div>
                  <div className="space-y-2">
                    <Label htmlFor="version">Version *</Label>
                    <Input
                      id="version"
                      value={formData.version}
                      onChange={(e) => setFormData({ ...formData, version: e.target.value })}
                      placeholder="1.0.0"
                      required
                      className="border-2 border-black"
                    />
                  </div>
                </div>
                <div className="space-y-2">
                  <Label htmlFor="description">Description *</Label>
                  <Textarea
                    id="description"
                    value={formData.description}
                    onChange={(e) => setFormData({ ...formData, description: e.target.value })}
                    placeholder="Model description..."
                    required
                    className="border-2 border-black"
                    rows={3}
                  />
                </div>
                <div className="space-y-2">
                  <Label htmlFor="capabilities">Capabilities (comma-separated) *</Label>
                  <Input
                    id="capabilities"
                    value={formData.capabilities}
                    onChange={(e) => setFormData({ ...formData, capabilities: e.target.value })}
                    placeholder="text-generation, question-answering"
                    required
                    className="border-2 border-black"
                  />
                </div>
                <div className="grid grid-cols-2 gap-4">
                  <div className="space-y-2">
                    <Label htmlFor="input_format">Input Format *</Label>
                    <Input
                      id="input_format"
                      value={formData.input_format}
                      onChange={(e) => setFormData({ ...formData, input_format: e.target.value })}
                      placeholder="text, json, etc."
                      required
                      className="border-2 border-black"
                    />
                  </div>
                  <div className="space-y-2">
                    <Label htmlFor="output_format">Output Format *</Label>
                    <Input
                      id="output_format"
                      value={formData.output_format}
                      onChange={(e) => setFormData({ ...formData, output_format: e.target.value })}
                      placeholder="text, json, etc."
                      required
                      className="border-2 border-black"
                    />
                  </div>
                </div>
                <DialogFooter>
                  <Button
                    type="button"
                    variant="noShadow"
                    onClick={() => setDialogOpen(false)}
                  >
                    Cancel
                  </Button>
                  <Button type="submit" variant="default" disabled={registering}>
                    {registering ? 'Registering...' : 'Register Model'}
                  </Button>
                </DialogFooter>
              </form>
            </DialogContent>
          </Dialog>
        </div>
      </div>

      {/* Models Table */}
      <Card className="p-6 border-2 border-black shadow-brutal">
        {models.length === 0 ? (
          <div className="text-center py-12">
            <IconBrain className="h-12 w-12 mx-auto text-muted-foreground mb-4" />
            <p className="text-lg font-medium mb-2">No models registered</p>
            <p className="text-muted-foreground mb-4">
              Get started by registering your first AI model
            </p>
            <Dialog open={dialogOpen} onOpenChange={setDialogOpen}>
              <DialogTrigger asChild>
                <Button variant="default">
                  <IconPlus className="mr-2 h-4 w-4" />
                  Register Model
                </Button>
              </DialogTrigger>
              <DialogContent className="border-2 border-black shadow-brutal max-w-2xl max-h-[90vh] overflow-y-auto">
                <DialogHeader>
                  <DialogTitle className="text-2xl font-bold">Register New Model</DialogTitle>
                  <DialogDescription>
                    Register a new AI model in the governance system
                  </DialogDescription>
                </DialogHeader>
                <form onSubmit={handleRegister} className="space-y-4">
                  <div className="grid grid-cols-2 gap-4">
                    <div className="space-y-2">
                      <Label htmlFor="model_id_empty">Model ID *</Label>
                      <Input
                        id="model_id_empty"
                        value={formData.model_id}
                        onChange={(e) => setFormData({ ...formData, model_id: e.target.value })}
                        placeholder="model-001"
                        required
                        className="border-2 border-black"
                      />
                    </div>
                    <div className="space-y-2">
                      <Label htmlFor="name_empty">Name *</Label>
                      <Input
                        id="name_empty"
                        value={formData.name}
                        onChange={(e) => setFormData({ ...formData, name: e.target.value })}
                        placeholder="Credit Risk Model"
                        required
                        className="border-2 border-black"
                      />
                    </div>
                  </div>
                  <div className="grid grid-cols-2 gap-4">
                    <div className="space-y-2">
                      <Label htmlFor="model_type_empty">Model Type *</Label>
                      <Input
                        id="model_type_empty"
                        value={formData.model_type}
                        onChange={(e) => setFormData({ ...formData, model_type: e.target.value })}
                        placeholder="llm, classification, etc."
                        required
                        className="border-2 border-black"
                      />
                    </div>
                    <div className="space-y-2">
                      <Label htmlFor="version_empty">Version *</Label>
                      <Input
                        id="version_empty"
                        value={formData.version}
                        onChange={(e) => setFormData({ ...formData, version: e.target.value })}
                        placeholder="1.0.0"
                        required
                        className="border-2 border-black"
                      />
                    </div>
                  </div>
                  <div className="space-y-2">
                    <Label htmlFor="description_empty">Description *</Label>
                    <Textarea
                      id="description_empty"
                      value={formData.description}
                      onChange={(e) => setFormData({ ...formData, description: e.target.value })}
                      placeholder="Model description..."
                      required
                      className="border-2 border-black"
                      rows={3}
                    />
                  </div>
                  <div className="space-y-2">
                    <Label htmlFor="capabilities_empty">Capabilities (comma-separated) *</Label>
                    <Input
                      id="capabilities_empty"
                      value={formData.capabilities}
                      onChange={(e) => setFormData({ ...formData, capabilities: e.target.value })}
                      placeholder="text-generation, question-answering"
                      required
                      className="border-2 border-black"
                    />
                  </div>
                  <div className="grid grid-cols-2 gap-4">
                    <div className="space-y-2">
                      <Label htmlFor="input_format_empty">Input Format *</Label>
                      <Input
                        id="input_format_empty"
                        value={formData.input_format}
                        onChange={(e) => setFormData({ ...formData, input_format: e.target.value })}
                        placeholder="text, json, etc."
                        required
                        className="border-2 border-black"
                      />
                    </div>
                    <div className="space-y-2">
                      <Label htmlFor="output_format_empty">Output Format *</Label>
                      <Input
                        id="output_format_empty"
                        value={formData.output_format}
                        onChange={(e) => setFormData({ ...formData, output_format: e.target.value })}
                        placeholder="text, json, etc."
                        required
                        className="border-2 border-black"
                      />
                    </div>
                  </div>
                  <DialogFooter>
                    <Button
                      type="button"
                      variant="noShadow"
                      onClick={() => setDialogOpen(false)}
                    >
                      Cancel
                    </Button>
                    <Button type="submit" variant="default" disabled={registering}>
                      {registering ? 'Registering...' : 'Register Model'}
                    </Button>
                  </DialogFooter>
                </form>
              </DialogContent>
            </Dialog>
          </div>
        ) : (
          <Table>
            <TableHeader>
              <TableRow className="border-2 border-black">
                <TableHead className="font-bold">Name</TableHead>
                <TableHead className="font-bold">Version</TableHead>
                <TableHead className="font-bold">Type</TableHead>
                <TableHead className="font-bold">Status</TableHead>
                <TableHead className="font-bold">Created</TableHead>
                <TableHead className="font-bold">Actions</TableHead>
              </TableRow>
            </TableHeader>
            <TableBody>
              {models.map((model) => (
                <TableRow key={model.id} className="border-b-2 border-black">
                  <TableCell className="font-medium">{model.name}</TableCell>
                  <TableCell>{model.version}</TableCell>
                  <TableCell>{model.type}</TableCell>
                  <TableCell>{getStatusBadge(model.status)}</TableCell>
                  <TableCell>
                    {new Date(model.createdAt).toLocaleDateString()}
                  </TableCell>
                  <TableCell>
                    <div className="flex gap-2">
                      <Link href={`/models/${model.id}`}>
                        <Button variant="noShadow" size="sm">
                          View
                        </Button>
                      </Link>
                      <Button variant="noShadow" size="sm">
                        Edit
                      </Button>
                    </div>
                  </TableCell>
                </TableRow>
              ))}
            </TableBody>
          </Table>
        )}
      </Card>
    </div>
  )
}

