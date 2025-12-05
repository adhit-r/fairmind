'use client'

import { useState } from 'react'
import { useLifecycle } from '@/lib/api/hooks/useLifecycle'
import { Card } from '@/components/ui/card'
import { Button } from '@/components/ui/button'
import { Input } from '@/components/ui/input'
import { Label } from '@/components/ui/label'
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '@/components/ui/select'
import { Badge } from '@/components/ui/badge'
import { Progress } from '@/components/ui/progress'
import { Alert, AlertDescription } from '@/components/ui/alert'
import { useForm } from 'react-hook-form'
import { zodResolver } from '@hookform/resolvers/zod'
import { lifecycleSchema, type LifecycleFormData } from '@/lib/validations/schemas'
import { useToast } from '@/hooks/use-toast'
import { IconActivity, IconCheck, IconX, IconAlertTriangle } from '@tabler/icons-react'

const LIFECYCLE_STAGES = [
  'Design',
  'Development',
  'Testing',
  'Deployment',
  'Monitoring',
  'Retirement',
]

export default function LifecyclePage() {
  const { processStage, getSummary, loading, error } = useLifecycle()
  const { toast } = useToast()
  const [systemId, setSystemId] = useState('')
  const [summary, setSummary] = useState<any>(null)

  const {
    register,
    handleSubmit,
    formState: { errors },
    reset,
  } = useForm<LifecycleFormData>({
    resolver: zodResolver(lifecycleSchema),
  })

  const onSubmit = async (data: LifecycleFormData) => {
    try {
      await processStage(data)
      toast({
        title: 'Lifecycle stage processed',
        description: `Stage ${data.stage} has been processed successfully.`,
      })
      reset()
      if (data.systemId) {
        const result = await getSummary(data.systemId)
        setSummary(result)
      }
    } catch (err) {
      toast({
        title: 'Processing failed',
        description: err instanceof Error ? err.message : 'An error occurred',
        variant: 'destructive',
      })
    }
  }

  const handleGetSummary = async () => {
    if (!systemId.trim()) {
      toast({
        title: 'System ID required',
        description: 'Please enter a system ID',
        variant: 'destructive',
      })
      return
    }
    try {
      const result = await getSummary(systemId)
      setSummary(result)
    } catch (err) {
      toast({
        title: 'Failed to fetch summary',
        description: err instanceof Error ? err.message : 'An error occurred',
        variant: 'destructive',
      })
    }
  }

  return (
    <div className="space-y-6">
      {/* Header */}
      <div>
        <h1 className="text-4xl font-bold">Lifecycle Management</h1>
        <p className="text-muted-foreground mt-1">
          Manage AI system lifecycle stages and compliance checks
        </p>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        {/* Process Stage Form */}
        <Card className="p-6 border-2 border-black shadow-brutal">
          <h2 className="text-2xl font-bold mb-4">Process Lifecycle Stage</h2>
          
          {error && (
            <Alert className="mb-4 border-2 border-red-500">
              <IconAlertTriangle className="h-4 w-4" />
              <AlertDescription>{error.message}</AlertDescription>
            </Alert>
          )}

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
              <Label htmlFor="stage">Stage</Label>
              <Select
                onValueChange={(value) => {
                  register('stage').onChange({ target: { value } })
                }}
              >
                <SelectTrigger className="border-2 border-black">
                  <SelectValue placeholder="Select lifecycle stage" />
                </SelectTrigger>
                <SelectContent>
                  {LIFECYCLE_STAGES.map((stage) => (
                    <SelectItem key={stage} value={stage.toLowerCase()}>
                      {stage}
                    </SelectItem>
                  ))}
                </SelectContent>
              </Select>
              {errors.stage && (
                <p className="text-sm text-red-600">{errors.stage.message}</p>
              )}
            </div>

            <Button type="submit" className="w-full" disabled={loading}>
              {loading ? 'Processing...' : 'Process Stage'}
            </Button>
          </form>
        </Card>

        {/* Summary */}
        <Card className="p-6 border-2 border-black shadow-brutal">
          <h2 className="text-2xl font-bold mb-4">Lifecycle Summary</h2>
          
          <div className="space-y-4 mb-4">
            <div className="flex gap-4">
              <Input
                value={systemId}
                onChange={(e) => setSystemId(e.target.value)}
                placeholder="Enter system ID"
                className="border-2 border-black"
              />
              <Button variant="default" onClick={handleGetSummary}>
                Get Summary
              </Button>
            </div>
          </div>

          {summary ? (
            <div className="space-y-4">
              <div className="p-4 border-2 border-black bg-white">
                <p className="text-sm font-medium mb-2">Current Stage</p>
                <Badge variant="default" className="border-2 border-black">
                  {summary.currentStage}
                </Badge>
              </div>

              <div className="space-y-2">
                <p className="text-sm font-medium">Stage Progress</p>
                {LIFECYCLE_STAGES.map((stage, index) => {
                  const isCompleted = summary.stages?.some(
                    (s: any) => s.stage.toLowerCase() === stage.toLowerCase()
                  )
                  const isCurrent = summary.currentStage?.toLowerCase() === stage.toLowerCase()
                  
                  return (
                    <div key={stage} className="flex items-center gap-2">
                      {isCompleted ? (
                        <IconCheck className="h-4 w-4 text-green-600" />
                      ) : isCurrent ? (
                        <IconActivity className="h-4 w-4 text-orange" />
                      ) : (
                        <IconX className="h-4 w-4 text-muted-foreground" />
                      )}
                      <span className={isCurrent ? 'font-bold' : ''}>{stage}</span>
                    </div>
                  )
                })}
              </div>
            </div>
          ) : (
            <div className="text-center py-12 text-muted-foreground">
              <IconActivity className="h-12 w-12 mx-auto mb-4 opacity-50" />
              <p>Enter a system ID to view lifecycle summary</p>
            </div>
          )}
        </Card>
      </div>
    </div>
  )
}

