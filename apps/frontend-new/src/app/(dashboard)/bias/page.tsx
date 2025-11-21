'use client'

import { useState } from 'react'
import { useBiasDetection } from '@/lib/api/hooks/useBiasDetection'
import { useDatasets } from '@/lib/api/hooks/useDatasets'
import { Card } from '@/components/ui/card'
import { Button } from '@/components/ui/button'
import { Input } from '@/components/ui/input'
import { Label } from '@/components/ui/label'
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '@/components/ui/select'
import { Textarea } from '@/components/ui/textarea'
import { Alert, AlertDescription } from '@/components/ui/alert'
import { useToast } from '@/hooks/use-toast'
import { IconTarget, IconCheck, IconX, IconDatabase } from '@tabler/icons-react'

export default function BiasDetectionPage() {
  const { runBiasTest, loading, error } = useBiasDetection()
  const { datasets, loading: datasetsLoading } = useDatasets()
  const { toast } = useToast()
  const [formData, setFormData] = useState({
    modelId: '',
    datasetId: '',
    testType: '',
    parameters: '',
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

      const parameters = formData.parameters ? JSON.parse(formData.parameters) : {}
      const result = await runBiasTest({
        modelId: formData.modelId,
        datasetId: formData.datasetId,
        testType: formData.testType,
        parameters,
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
              <Label htmlFor="modelId">Model ID</Label>
              <Input
                id="modelId"
                value={formData.modelId}
                onChange={(e) => setFormData({ ...formData, modelId: e.target.value })}
                placeholder="Enter model ID"
                required
                className="border-2 border-black"
              />
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
              <Label htmlFor="testType">Test Type</Label>
              <Select
                value={formData.testType}
                onValueChange={(value) => setFormData({ ...formData, testType: value })}
              >
                <SelectTrigger className="border-2 border-black">
                  <SelectValue placeholder="Select test type" />
                </SelectTrigger>
                <SelectContent>
                  <SelectItem value="weat">WEAT (Word Embedding Association Test)</SelectItem>
                  <SelectItem value="fairness">Fairness Metrics</SelectItem>
                  <SelectItem value="image">Image Bias</SelectItem>
                  <SelectItem value="text">Text Bias</SelectItem>
                </SelectContent>
              </Select>
            </div>

            <div className="space-y-2">
              <Label htmlFor="parameters">Parameters (JSON)</Label>
              <Textarea
                id="parameters"
                value={formData.parameters}
                onChange={(e) => setFormData({ ...formData, parameters: e.target.value })}
                placeholder='{"threshold": 0.05, "confidence": 0.95}'
                className="border-2 border-black font-mono"
                rows={4}
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
                <p className="text-sm font-medium mb-2">Test ID</p>
                <p className="font-mono text-sm">{results.testId}</p>
              </div>

              {results.summary && (
                <div className="p-4 border-2 border-black bg-white">
                  <p className="text-sm font-medium mb-2">Summary</p>
                  <div className="grid grid-cols-2 gap-2">
                    <div>
                      <p className="text-xs text-muted-foreground">Total Tests</p>
                      <p className="text-lg font-bold">{results.summary.totalTests}</p>
                    </div>
                    <div>
                      <p className="text-xs text-muted-foreground">Passed</p>
                      <p className="text-lg font-bold text-green-600">{results.summary.passed}</p>
                    </div>
                    <div>
                      <p className="text-xs text-muted-foreground">Failed</p>
                      <p className="text-lg font-bold text-red-600">{results.summary.failed}</p>
                    </div>
                    <div>
                      <p className="text-xs text-muted-foreground">Risk Level</p>
                      <p className="text-lg font-bold">{results.summary.riskLevel}</p>
                    </div>
                  </div>
                </div>
              )}

              {results.results && results.results.length > 0 && (
                <div className="space-y-2">
                  <p className="text-sm font-medium">Test Results</p>
                  {results.results.map((result: any, index: number) => (
                    <div
                      key={index}
                      className="p-3 border-2 border-black bg-white flex items-center justify-between"
                    >
                      <span className="font-medium">{result.metric}</span>
                      <div className="flex items-center gap-2">
                        <span className="text-sm">{result.value.toFixed(3)}</span>
                        {result.passed ? (
                          <IconCheck className="h-4 w-4 text-green-600" />
                        ) : (
                          <IconX className="h-4 w-4 text-red-600" />
                        )}
                      </div>
                    </div>
                  ))}
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

