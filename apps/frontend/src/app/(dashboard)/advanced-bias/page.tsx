'use client'

import { useState } from 'react'
import { useAdvancedBias } from '@/lib/api/hooks/useAdvancedBias'
import { useDatasets } from '@/lib/api/hooks/useDatasets'
import { Card } from '@/components/ui/card'
import { Button } from '@/components/ui/button'
import { Input } from '@/components/ui/input'
import { Label } from '@/components/ui/label'
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '@/components/ui/select'
import { Textarea } from '@/components/ui/textarea'
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/ui/tabs'
import { Badge } from '@/components/ui/badge'
import { useForm } from 'react-hook-form'
import { zodResolver } from '@hookform/resolvers/zod'
import { advancedBiasSchema, type AdvancedBiasFormData } from '@/lib/validations/schemas'
import { useToast } from '@/hooks/use-toast'
import { IconTarget, IconBrain, IconCheck, IconX, IconDatabase } from '@tabler/icons-react'

const ANALYSIS_TYPES = [
  { value: 'causal', label: 'Causal Analysis' },
  { value: 'counterfactual', label: 'Counterfactual Analysis' },
  { value: 'intersectional', label: 'Intersectional Analysis' },
  { value: 'adversarial', label: 'Adversarial Testing' },
  { value: 'temporal', label: 'Temporal Analysis' },
  { value: 'contextual', label: 'Contextual Analysis' },
]

export default function AdvancedBiasPage() {
  const {
    runCausalAnalysis,
    runCounterfactualAnalysis,
    runIntersectionalAnalysis,
    runAdversarialTesting,
    loading,
    error,
  } = useAdvancedBias()
  const { datasets, loading: datasetsLoading } = useDatasets()
  const { toast } = useToast()
  const [results, setResults] = useState<any>(null)
  const [activeTab, setActiveTab] = useState('causal')
  const [selectedDataset, setSelectedDataset] = useState('')

  const {
    register,
    handleSubmit,
    formState: { errors },
    watch,
    reset,
  } = useForm<AdvancedBiasFormData>({
    resolver: zodResolver(advancedBiasSchema),
  })

  const analysisType = watch('analysisType')

  const onSubmit = async (data: AdvancedBiasFormData) => {
    if (!selectedDataset) {
      toast({
        title: "Dataset required",
        description: "Please select a dataset for bias analysis",
        variant: "destructive",
      })
      return
    }

    try {
      let result
      const analysisParams = { modelId: data.modelId, datasetId: selectedDataset, ...data.parameters }
      switch (data.analysisType) {
        case 'causal':
          result = await runCausalAnalysis(analysisParams)
          break
        case 'counterfactual':
          result = await runCounterfactualAnalysis(analysisParams)
          break
        case 'intersectional':
          result = await runIntersectionalAnalysis(analysisParams)
          break
        case 'adversarial':
          result = await runAdversarialTesting(analysisParams)
          break
        default:
          throw new Error('Unsupported analysis type')
      }
      setResults(result)
      toast({
        title: 'Analysis completed',
        description: `${ANALYSIS_TYPES.find(t => t.value === data.analysisType)?.label} completed successfully.`,
      })
    } catch (err) {
      toast({
        title: 'Analysis failed',
        description: err instanceof Error ? err.message : 'An error occurred',
        variant: 'destructive',
      })
    }
  }

  return (
    <div className="space-y-6">
      {/* Header */}
      <div>
        <h1 className="text-4xl font-bold">Advanced Bias Detection</h1>
        <p className="text-muted-foreground mt-1">
          Advanced bias analysis techniques for comprehensive evaluation
        </p>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        {/* Analysis Form */}
        <Card className="p-6 border-2 border-black shadow-brutal">
          <h2 className="text-2xl font-bold mb-4">Run Advanced Analysis</h2>

          <form onSubmit={handleSubmit(onSubmit)} className="space-y-4">
            <div className="space-y-2">
              <Label htmlFor="modelId">Model ID</Label>
              <Input
                id="modelId"
                {...register('modelId')}
                className="border-2 border-black"
                placeholder="Enter model ID"
              />
              {errors.modelId && (
                <p className="text-sm text-red-600">{errors.modelId.message}</p>
              )}
            </div>

            <div className="space-y-2">
              <Label htmlFor="datasetId">Dataset *</Label>
              <Select
                value={selectedDataset}
                onValueChange={setSelectedDataset}
                disabled={datasetsLoading}
              >
                <SelectTrigger className="border-2 border-black">
                  <SelectValue placeholder={datasetsLoading ? "Loading datasets..." : "Select dataset"} />
                </SelectTrigger>
                <SelectContent>
                  {datasets.length === 0 ? (
                    <SelectItem value="none" disabled>No datasets available</SelectItem>
                  ) : (
                    datasets.map((dataset) => (
                      <SelectItem key={dataset.id} value={dataset.id}>
                        {dataset.name} ({dataset.file_type.toUpperCase()})
                      </SelectItem>
                    ))
                  )}
                </SelectContent>
              </Select>
              {datasets.length === 0 && !datasetsLoading && (
                <p className="text-sm text-muted-foreground">
                  <IconDatabase className="inline h-4 w-4 mr-1" />
                  No datasets found. <a href="/datasets" className="underline">Upload a dataset</a> first.
                </p>
              )}
            </div>

            <div className="space-y-2">
              <Label htmlFor="analysisType">Analysis Type</Label>
              <Select
                value={analysisType}
                onValueChange={(value) => {
                  register('analysisType').onChange({ target: { value } })
                  setActiveTab(value)
                }}
              >
                <SelectTrigger className="border-2 border-black">
                  <SelectValue placeholder="Select analysis type" />
                </SelectTrigger>
                <SelectContent>
                  {ANALYSIS_TYPES.map((type) => (
                    <SelectItem key={type.value} value={type.value}>
                      {type.label}
                    </SelectItem>
                  ))}
                </SelectContent>
              </Select>
              {errors.analysisType && (
                <p className="text-sm text-red-600">{errors.analysisType.message}</p>
              )}
            </div>

            <div className="space-y-2">
              <Label htmlFor="parameters">Parameters (JSON)</Label>
              <Textarea
                id="parameters"
                {...register('parameters')}
                className="border-2 border-black font-mono"
                rows={6}
                placeholder='{"sensitiveAttributes": ["gender", "race"], "threshold": 0.05}'
              />
              {errors.parameters && (
                <p className="text-sm text-red-600">{String(errors.parameters.message)}</p>
              )}
            </div>

            <Button type="submit" className="w-full" disabled={loading}>
              {loading ? 'Running analysis...' : 'Run Analysis'}
            </Button>
          </form>
        </Card>

        {/* Results */}
        <Card className="p-6 border-2 border-black shadow-brutal">
          <h2 className="text-2xl font-bold mb-4">Analysis Results</h2>

          {results ? (
            <div className="space-y-4">
              <div className="p-4 border-2 border-black bg-white">
                <p className="text-sm font-medium mb-2">Analysis ID</p>
                <p className="font-mono text-sm">{results.id}</p>
              </div>

              <div className="p-4 border-2 border-black bg-white">
                <p className="text-sm font-medium mb-2">Type</p>
                <Badge variant="default" className="border-2 border-black">
                  {results.type}
                </Badge>
              </div>

              {results.results && (
                <div className="p-4 border-2 border-black bg-white">
                  <p className="text-sm font-medium mb-2">Results</p>
                  <pre className="text-xs bg-gray-50 p-2 border-2 border-black overflow-auto max-h-64">
                    {JSON.stringify(results.results, null, 2)}
                  </pre>
                </div>
              )}

              <div className="p-4 border-2 border-black bg-white">
                <p className="text-sm font-medium mb-2">Timestamp</p>
                <p className="text-sm">{new Date(results.timestamp).toLocaleString()}</p>
              </div>
            </div>
          ) : (
            <div className="text-center py-12 text-muted-foreground">
              <IconBrain className="h-12 w-12 mx-auto mb-4 opacity-50" />
              <p>No analysis results yet</p>
              <p className="text-sm">Run an analysis to see results here</p>
            </div>
          )}
        </Card>
      </div>

      {/* Analysis Types Info */}
      <Card className="p-6 border-2 border-black shadow-brutal">
        <h2 className="text-2xl font-bold mb-4">Analysis Types</h2>
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
          {ANALYSIS_TYPES.map((type) => (
            <div
              key={type.value}
              className="p-4 border-2 border-black bg-white"
            >
              <h3 className="font-bold mb-2">{type.label}</h3>
              <p className="text-sm text-muted-foreground">
                {type.value === 'causal' && 'Analyze causal relationships in bias'}
                {type.value === 'counterfactual' && 'Evaluate counterfactual fairness'}
                {type.value === 'intersectional' && 'Detect intersectional bias'}
                {type.value === 'adversarial' && 'Test adversarial robustness'}
                {type.value === 'temporal' && 'Analyze bias over time'}
                {type.value === 'contextual' && 'Context-aware bias detection'}
              </p>
            </div>
          ))}
        </div>
      </Card>
    </div>
  )
}

