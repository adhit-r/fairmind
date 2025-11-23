'use client'

import { useState } from 'react'
import { useRisks } from '@/lib/api/hooks/useRisks'
import { Card } from '@/components/ui/card'
import { Button } from '@/components/ui/button'
import { Table, TableBody, TableCell, TableHead, TableHeader, TableRow } from '@/components/ui/table'
import { Badge } from '@/components/ui/badge'
import { Dialog, DialogContent, DialogDescription, DialogHeader, DialogTitle, DialogTrigger } from '@/components/ui/dialog'
import { Input } from '@/components/ui/input'
import { Label } from '@/components/ui/label'
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '@/components/ui/select'
import { Textarea } from '@/components/ui/textarea'
import { useForm } from 'react-hook-form'
import { zodResolver } from '@hookform/resolvers/zod'
import { riskAssessmentSchema, type RiskAssessmentFormData } from '@/lib/validations/schemas'
import { useToast } from '@/hooks/use-toast'
import { Skeleton } from '@/components/ui/skeleton'
import { PieChart } from '@/components/charts/PieChart'
import { IconAlertTriangle, IconPlus } from '@tabler/icons-react'

export default function RisksPage() {
  const { data: risks, loading, error, assessRisks } = useRisks()
  const { toast } = useToast()
  const [dialogOpen, setDialogOpen] = useState(false)

  const {
    register,
    handleSubmit,
    formState: { errors },
    reset,
  } = useForm<RiskAssessmentFormData>({
    resolver: zodResolver(riskAssessmentSchema),
  })

  const onSubmit = async (data: RiskAssessmentFormData) => {
    try {
      await assessRisks(data)
      toast({
        title: 'Risk assessed',
        description: 'Risk assessment has been completed successfully.',
      })
      setDialogOpen(false)
      reset()
    } catch (err) {
      toast({
        title: 'Assessment failed',
        description: err instanceof Error ? err.message : 'An error occurred',
        variant: 'destructive',
      })
    }
  }

  // Prepare data for pie chart
  const riskDistribution = [
    { name: 'Critical', value: risks.filter(r => r.severity === 'critical').length },
    { name: 'High', value: risks.filter(r => r.severity === 'high').length },
    { name: 'Medium', value: risks.filter(r => r.severity === 'medium').length },
    { name: 'Low', value: risks.filter(r => r.severity === 'low').length },
  ].filter(item => item.value > 0)

  const getSeverityBadge = (severity: string) => {
    const variants: Record<string, { variant: 'default' | 'secondary' | 'destructive', label: string }> = {
      critical: { variant: 'destructive', label: 'Critical' },
      high: { variant: 'destructive', label: 'High' },
      medium: { variant: 'secondary', label: 'Medium' },
      low: { variant: 'default', label: 'Low' },
    }
    const config = variants[severity] || variants.low
    return <Badge variant={config.variant} className="border-2 border-black">{config.label}</Badge>
  }

  if (loading && !risks.length) {
    return (
      <div className="space-y-6">
        <Skeleton className="h-10 w-48" />
        <Skeleton className="h-96" />
      </div>
    )
  }

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-4xl font-bold">Risk Management</h1>
          <p className="text-muted-foreground mt-1">
            Assess and manage risks in your AI systems
          </p>
        </div>
        <Dialog open={dialogOpen} onOpenChange={setDialogOpen}>
          <DialogTrigger asChild>
            <Button variant="default">
              <IconPlus className="mr-2 h-4 w-4" />
              Assess Risk
            </Button>
          </DialogTrigger>
          <DialogContent className="border-2 border-black shadow-brutal-lg">
            <DialogHeader>
              <DialogTitle>Assess Risk</DialogTitle>
              <DialogDescription>
                Create a new risk assessment
              </DialogDescription>
            </DialogHeader>
            <form onSubmit={handleSubmit(onSubmit)} className="space-y-4">
              <div className="space-y-2">
                <Label htmlFor="systemId">System ID</Label>
                <Input
                  id="systemId"
                  {...register('systemId')}
                  className="border-2 border-black"
                />
                {errors.systemId && (
                  <p className="text-sm text-red-600">{errors.systemId.message}</p>
                )}
              </div>

              <div className="space-y-2">
                <Label htmlFor="riskType">Risk Type</Label>
                <Input
                  id="riskType"
                  {...register('riskType')}
                  className="border-2 border-black"
                />
                {errors.riskType && (
                  <p className="text-sm text-red-600">{errors.riskType.message}</p>
                )}
              </div>

              <div className="space-y-2">
                <Label htmlFor="severity">Severity</Label>
                <Select
                  onValueChange={(value) => {
                    register('severity').onChange({ target: { value } })
                  }}
                >
                  <SelectTrigger className="border-2 border-black">
                    <SelectValue placeholder="Select severity" />
                  </SelectTrigger>
                  <SelectContent>
                    <SelectItem value="low">Low</SelectItem>
                    <SelectItem value="medium">Medium</SelectItem>
                    <SelectItem value="high">High</SelectItem>
                    <SelectItem value="critical">Critical</SelectItem>
                  </SelectContent>
                </Select>
                {errors.severity && (
                  <p className="text-sm text-red-600">{errors.severity.message}</p>
                )}
              </div>

              <div className="space-y-2">
                <Label htmlFor="description">Description</Label>
                <Textarea
                  id="description"
                  {...register('description')}
                  className="border-2 border-black"
                  rows={4}
                />
                {errors.description && (
                  <p className="text-sm text-red-600">{errors.description.message}</p>
                )}
              </div>

              <div className="flex gap-2">
                <Button type="submit" variant="default" className="flex-1">
                  Assess
                </Button>
                <Button
                  type="button"
                  variant="noShadow"
                  onClick={() => setDialogOpen(false)}
                >
                  Cancel
                </Button>
              </div>
            </form>
          </DialogContent>
        </Dialog>
      </div>

      {/* Risk Distribution Chart */}
      {riskDistribution.length > 0 && (
        <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
          <PieChart
            title="Risk Distribution"
            data={riskDistribution}
          />
        </div>
      )}

      {/* Risks Table */}
      <Card className="p-6 border-2 border-black shadow-brutal">
        {error && (
          <div className="mb-4 p-4 border-2 border-red-500 bg-red-50">
            <p className="text-red-600">{error.message}</p>
          </div>
        )}

        {risks.length === 0 ? (
          <div className="text-center py-12">
            <IconAlertTriangle className="h-12 w-12 mx-auto text-muted-foreground mb-4" />
            <p className="text-lg font-medium mb-2">No risks identified</p>
            <p className="text-muted-foreground mb-4">
              All systems are currently risk-free
            </p>
          </div>
        ) : (
          <Table>
            <TableHeader>
              <TableRow className="border-2 border-black">
                <TableHead className="font-bold">Title</TableHead>
                <TableHead className="font-bold">Severity</TableHead>
                <TableHead className="font-bold">Status</TableHead>
                <TableHead className="font-bold">Description</TableHead>
                <TableHead className="font-bold">Actions</TableHead>
              </TableRow>
            </TableHeader>
            <TableBody>
              {risks.map((risk) => (
                <TableRow key={risk.id} className="border-b-2 border-black">
                  <TableCell className="font-medium">{risk.title}</TableCell>
                  <TableCell>{getSeverityBadge(risk.severity)}</TableCell>
                  <TableCell>
                    <Badge variant="default" className="border-2 border-black">
                      {risk.status}
                    </Badge>
                  </TableCell>
                  <TableCell className="max-w-md truncate">{risk.description}</TableCell>
                  <TableCell>
                    <Button variant="noShadow" size="sm">
                      View Details
                    </Button>
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

