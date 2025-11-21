'use client'

import { useState } from 'react'
import { useEvidence } from '@/lib/api/hooks/useEvidence'
import { Card } from '@/components/ui/card'
import { Button } from '@/components/ui/button'
import { Input } from '@/components/ui/input'
import { Label } from '@/components/ui/label'
import { Textarea } from '@/components/ui/textarea'
import { Slider } from '@/components/ui/slider'
import { Table, TableBody, TableCell, TableHead, TableHeader, TableRow } from '@/components/ui/table'
import { Badge } from '@/components/ui/badge'
import { useForm } from 'react-hook-form'
import { zodResolver } from '@hookform/resolvers/zod'
import { evidenceSchema, type EvidenceFormData } from '@/lib/validations/schemas'
import { useToast } from '@/hooks/use-toast'
import { IconFileText, IconUpload, IconCheck } from '@tabler/icons-react'

export default function EvidencePage() {
  const [systemId, setSystemId] = useState('')
  const { data, loading, error, collectEvidence } = useEvidence(systemId)
  const { toast } = useToast()
  const [confidence, setConfidence] = useState([0.8])

  const {
    register,
    handleSubmit,
    formState: { errors },
    reset,
  } = useForm<EvidenceFormData>({
    resolver: zodResolver(evidenceSchema),
    defaultValues: {
      confidence: 0.8,
    },
  })

  const onSubmit = async (data: EvidenceFormData) => {
    try {
      await collectEvidence({
        ...data,
        confidence: confidence[0],
      })
      toast({
        title: 'Evidence collected',
        description: 'Evidence has been successfully collected and stored.',
      })
      reset()
      setConfidence([0.8])
    } catch (err) {
      toast({
        title: 'Collection failed',
        description: err instanceof Error ? err.message : 'An error occurred',
        variant: 'destructive',
      })
    }
  }

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-4xl font-bold">Evidence Collection</h1>
          <p className="text-muted-foreground mt-1">
            Collect and manage evidence for AI governance compliance
          </p>
        </div>
        <Button variant="default">
          <IconUpload className="mr-2 h-4 w-4" />
          Upload Evidence
        </Button>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        {/* Collect Evidence Form */}
        <Card className="p-6 border-2 border-black shadow-brutal">
          <h2 className="text-2xl font-bold mb-4">Collect Evidence</h2>

          <form onSubmit={handleSubmit(onSubmit)} className="space-y-4">
            <div className="space-y-2">
              <Label htmlFor="systemId">System ID</Label>
              <Input
                id="systemId"
                {...register('systemId')}
                className="border-2 border-black"
                placeholder="Enter system ID"
              />
              {errors.systemId && (
                <p className="text-sm text-red-600">{errors.systemId.message}</p>
              )}
            </div>

            <div className="space-y-2">
              <Label htmlFor="type">Evidence Type</Label>
              <Input
                id="type"
                {...register('type')}
                className="border-2 border-black"
                placeholder="e.g., test_results, documentation, audit_log"
              />
              {errors.type && (
                <p className="text-sm text-red-600">{errors.type.message}</p>
              )}
            </div>

            <div className="space-y-2">
              <Label htmlFor="content">Content (JSON)</Label>
              <Textarea
                id="content"
                {...register('content')}
                className="border-2 border-black font-mono"
                rows={6}
                placeholder='{"key": "value"}'
              />
              {errors.content && (
                <p className="text-sm text-red-600">{String(errors.content.message)}</p>
              )}
            </div>

            <div className="space-y-2">
              <Label>Confidence: {(confidence[0] * 100).toFixed(0)}%</Label>
              <Slider
                value={confidence}
                onValueChange={setConfidence}
                min={0}
                max={1}
                step={0.01}
                className="border-2 border-black"
              />
            </div>

            <Button type="submit" className="w-full" disabled={loading}>
              {loading ? 'Collecting...' : 'Collect Evidence'}
            </Button>
          </form>
        </Card>

        {/* Evidence List */}
        <Card className="p-6 border-2 border-black shadow-brutal">
          <div className="flex items-center justify-between mb-4">
            <h2 className="text-2xl font-bold">Evidence Records</h2>
            <Input
              value={systemId}
              onChange={(e) => setSystemId(e.target.value)}
              placeholder="Filter by System ID"
              className="w-48 border-2 border-black"
            />
          </div>

          {loading && (
            <div className="text-center py-12 text-muted-foreground">
              Loading evidence...
            </div>
          )}

          {error && (
            <div className="text-center py-12 text-red-600">
              {error.message}
            </div>
          )}

          {!loading && !error && data.length > 0 && (
            <Table>
              <TableHeader>
                <TableRow className="border-2 border-black">
                  <TableHead className="font-bold">Type</TableHead>
                  <TableHead className="font-bold">Confidence</TableHead>
                  <TableHead className="font-bold">Timestamp</TableHead>
                  <TableHead className="font-bold">Actions</TableHead>
                </TableRow>
              </TableHeader>
              <TableBody>
                {data.map((evidence) => (
                  <TableRow key={evidence.id} className="border-b-2 border-black">
                    <TableCell>
                      <Badge variant="default" className="border-2 border-black">
                        {evidence.type}
                      </Badge>
                    </TableCell>
                    <TableCell>
                      <div className="flex items-center gap-2">
                        <span className="font-medium">{(evidence.confidence * 100).toFixed(0)}%</span>
                        {evidence.confidence > 0.8 && (
                          <IconCheck className="h-4 w-4 text-green-600" />
                        )}
                      </div>
                    </TableCell>
                    <TableCell>
                      {new Date(evidence.timestamp).toLocaleString()}
                    </TableCell>
                    <TableCell>
                      <Button variant="noShadow" size="sm">
                        View
                      </Button>
                    </TableCell>
                  </TableRow>
                ))}
              </TableBody>
            </Table>
          )}

          {!loading && !error && data.length === 0 && (
            <div className="text-center py-12 text-muted-foreground">
              <IconFileText className="h-12 w-12 mx-auto mb-4 opacity-50" />
              <p>No evidence records found</p>
              {systemId && <p className="text-sm">for system ID: {systemId}</p>}
            </div>
          )}
        </Card>
      </div>
    </div>
  )
}

