'use client'

import { useState } from 'react'
import { useBiasDetection } from '@/lib/api/hooks/useBiasDetection'
import { useDatasets } from '@/lib/api/hooks/useDatasets'
import { useModels } from '@/lib/api/hooks/useModels'
import { Card } from '@/components/ui/card'
import { Button } from '@/components/ui/button'
import { Input } from '@/components/ui/input'
import { Label } from '@/components/ui/label'
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '@/components/ui/select'
import { Textarea } from '@/components/ui/textarea'
import { Alert, AlertDescription } from '@/components/ui/alert'
import { useToast } from '@/hooks/use-toast'
import { IconTarget, IconCheck, IconX, IconDatabase, IconBrain } from '@tabler/icons-react'

export default function BiasDetectionPage() {
  const { runBiasTest, loading, error } = useBiasDetection()
  const { datasets, loading: datasetsLoading } = useDatasets()
  const { data: models, loading: modelsLoading } = useModels()
  const { toast } = useToast()
  const [formData, setFormData] = useState({
    modelId: '',
    datasetId: '',
    sensitiveAttributes: '',
    targetColumn: '',
  })
  const [results, setResults] = useState<any>(null)

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault()

    try {
      if (!formData.datasetId) {
        toast({
          title: "Dataset required",
          description: "Please select a dataset for bias detection",
          variant: "destructive",
        })
        return
      }

      const result = await runBiasTest({
        dataset_id: formData.datasetId,
        model_id: formData.modelId,
        sensitive_attributes: formData.sensitiveAttributes.split(',').map(s => s.trim()).filter(s => s),
        target_column: formData.targetColumn,
      })
      setResults(result)
      toast({
        title: "Bias test completed",
        description: "Test results are ready for review.",
      })
    } catch (err) {
      toast({
        title: "Bias test failed",
        description: err instanceof Error ? err.message : "An error occurred",
        variant: "destructive",
      })
    }
  }

  return (
    <div className="space-y-6">
      {/* Header */}
      <div>
        <h1 className="text-4xl font-bold">Bias Detection</h1>
        <p className="text-muted-foreground mt-1">
          Detect and analyze bias in your AI models
        </p>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        {/* Test Form */}
        <Card className="p-6 border-2 border-black shadow-brutal">
          <h2 className="text-2xl font-bold mb-4">Run Bias Test</h2>

          {error && (
            <Alert className="mb-4 border-2 border-red-500">
              <AlertDescription>{error.message}</AlertDescription>
            </Alert>
          )}

          <form onSubmit={handleSubmit} className="space-y-4">
            <div className="space-y-2">
              <Label htmlFor="modelId">Model *</Label>
              <Select
                value={formData.modelId}
                onValueChange={(value) => setFormData({ ...formData, modelId: value })}
                disabled={modelsLoading}
              >
                <SelectTrigger className="border-2 border-black">
                  <SelectValue placeholder={modelsLoading ? "Loading models..." : "Select model"} />
                </SelectTrigger>
                <SelectContent>
                  {models.length === 0 ? (
                    <SelectItem value="none" disabled>No models available</SelectItem>
                  ) : (
                    models.map((model) => (
                      <SelectItem key={model.id} value={model.id}>
                        {model.name} ({model.version})
                      </SelectItem>
                    ))
                  )}
                </SelectContent>
              </Select>
              {models.length === 0 && !modelsLoading && (
                <p className="text-sm text-muted-foreground">
                  <IconBrain className="inline h-4 w-4 mr-1" />
                  No models found. <a href="/models" className="underline">Upload a model</a> first.
                </p>
              )}
            </div>

            <div className="space-y-2">
              <Label htmlFor="datasetId">Dataset *</Label>
              <Select
                value={formData.datasetId}
                onValueChange={(value) => setFormData({ ...formData, datasetId: value })}
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
              <Label htmlFor="sensitiveAttributes">Sensitive Attributes (comma-separated) *</Label>
              <Input
                id="sensitiveAttributes"
                value={formData.sensitiveAttributes}
                onChange={(e) => setFormData({ ...formData, sensitiveAttributes: e.target.value })}
                placeholder="gender, race, age"
                required
                className="border-2 border-black"
              />
            </div>

            <div className="space-y-2">
              <Label htmlFor="targetColumn">Target Column *</Label>
              <Input
                id="targetColumn"
                value={formData.targetColumn}
                onChange={(e) => setFormData({ ...formData, targetColumn: e.target.value })}
                placeholder="income, loan_status"
                required
                className="border-2 border-black"
              />
            </div>

            <Button type="submit" className="w-full" disabled={loading}>
              {loading ? 'Running test...' : 'Run Bias Test'}
            </Button>
          </form>
        </Card>

        {/* Results */}
        <Card className="p-6 border-2 border-black shadow-brutal">
          <h2 className="text-2xl font-bold mb-4">Test Results</h2>

          {results ? (
            <div className="space-y-4">
              <div className="p-4 border-2 border-black bg-white">
                <p className="text-sm font-medium mb-2">Analysis ID</p>
                <p className="font-mono text-sm">{results.analysis_id}</p>
              </div>

              {results.dataset_info && (
                <div className="p-4 border-2 border-black bg-white">
                  <p className="text-sm font-medium mb-2">Dataset Info</p>
                  <div className="grid grid-cols-2 gap-2">
                    <div>
                      <p className="text-xs text-muted-foreground">Total Samples</p>
                      <p className="text-lg font-bold">{results.dataset_info.total_samples}</p>
                    </div>
                    <div>
                      <p className="text-xs text-muted-foreground">Total Features</p>
                      <p className="text-lg font-bold">{results.dataset_info.total_features}</p>
                    </div>
                  </div>
                </div>
              )}

              {results.fairness_metrics && Object.keys(results.fairness_metrics).length > 0 && (
                <div className="space-y-2">
                  <p className="text-sm font-medium">Fairness Metrics</p>
                  {Object.entries(results.fairness_metrics).map(([attr, metrics]: [string, any]) => (
                    <div key={attr} className="p-3 border-2 border-black bg-white">
                      <p className="font-bold mb-2">{attr}</p>
                      <div className="space-y-1">
                        <div className="flex justify-between">
                          <span className="text-sm">Demographic Parity</span>
                          <span className={`text-sm font-mono ${metrics.demographic_parity.fair ? 'text-green-600' : 'text-red-600'}`}>
                            {metrics.demographic_parity.fair ? 'Fair' : 'Unfair'} ({metrics.demographic_parity.disparity.toFixed(3)})
                          </span>
                        </div>
                        <div className="flex justify-between">
                          <span className="text-sm">Equality of Opportunity</span>
                          <span className={`text-sm font-mono ${metrics.equality_of_opportunity.fair ? 'text-green-600' : 'text-red-600'}`}>
                            {metrics.equality_of_opportunity.fair ? 'Fair' : 'Unfair'} ({metrics.equality_of_opportunity.disparity.toFixed(3)})
                          </span>
                        </div>
                      </div>
                    </div>
                  ))}
                </div>
              )}

              {results.recommendations && results.recommendations.length > 0 && (
                <div className="p-4 border-2 border-black bg-white">
                  <p className="text-sm font-medium mb-2">Recommendations</p>
                  <ul className="list-disc list-inside space-y-1">
                    {results.recommendations.map((rec: string, index: number) => (
                      <li key={index} className="text-sm">{rec}</li>
                    ))}
                  </ul>
                </div>
              )}
            </div>
          ) : (
            <div className="text-center py-12 text-muted-foreground">
              <IconTarget className="h-12 w-12 mx-auto mb-4 opacity-50" />
              <p>No test results yet</p>
              <p className="text-sm">Run a bias test to see results here</p>
            </div>
          )}
        </Card>
      </div>
    </div>
  )
}

