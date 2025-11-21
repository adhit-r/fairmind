'use client'

import { useState } from 'react'
import { useModernBias } from '@/lib/api/hooks/useModernBias'
import { useDatasets } from '@/lib/api/hooks/useDatasets'
import { Card } from '@/components/ui/card'
import { Button } from '@/components/ui/button'
import { Input } from '@/components/ui/input'
import { Label } from '@/components/ui/label'
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '@/components/ui/select'
import { Textarea } from '@/components/ui/textarea'
import { Alert, AlertDescription, AlertTitle } from '@/components/ui/alert'
import { Badge } from '@/components/ui/badge'
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/ui/tabs'
import { useToast } from '@/hooks/use-toast'
import { IconTarget, IconCheck, IconX, IconAlertTriangle, IconBrain, IconUpload, IconDatabase } from '@tabler/icons-react'
import { SimpleChart } from '@/components/charts/SimpleChart'
import { Dialog, DialogContent, DialogDescription, DialogHeader, DialogTitle, DialogTrigger } from '@/components/ui/dialog'

const TEST_TYPES = [
  { value: 'weat', label: 'WEAT (Word Embedding Association Test)' },
  { value: 'seat', label: 'SEAT (Sentence Embedding Association Test)' },
  { value: 'minimal-pairs', label: 'Minimal Pairs' },
  { value: 'stereoset', label: 'StereoSet' },
  { value: 'bbq', label: 'BBQ (Bias Benchmark for QA)' },
]

export default function ModernBiasPage() {
  const { runComprehensiveEvaluation, runWEATTest, getBiasTests, getBiasCategories, loading, error } = useModernBias()
  const { datasets, loading: datasetsLoading } = useDatasets()
  const { toast } = useToast()
  const [activeTab, setActiveTab] = useState('comprehensive')
  const [results, setResults] = useState<any>(null)
  
  const [comprehensiveForm, setComprehensiveForm] = useState({
    modelId: '',
    datasetId: '',
    testTypes: [] as string[],
    evaluationDatasets: [] as string[],
  })

  const [weatForm, setWeatForm] = useState({
    targetWords: '',
    attributeWordsA: '',
    attributeWordsB: '',
    embeddings: '',
  })

  const handleComprehensiveEvaluation = async (e: React.FormEvent) => {
    e.preventDefault()
    if (!comprehensiveForm.datasetId) {
      toast({
        title: "Dataset required",
        description: "Please select a dataset for bias evaluation",
        variant: "destructive",
      })
      return
    }

    try {
      const result = await runComprehensiveEvaluation({
        modelId: comprehensiveForm.modelId,
        datasetId: comprehensiveForm.datasetId,
        testTypes: comprehensiveForm.testTypes,
        evaluationDatasets: comprehensiveForm.evaluationDatasets,
      })
      setResults(result)
      toast({
        title: "Evaluation completed",
        description: "Comprehensive bias evaluation has been completed successfully.",
      })
    } catch (err) {
      toast({
        title: "Evaluation failed",
        description: err instanceof Error ? err.message : "An error occurred",
        variant: "destructive",
      })
    }
  }

  const handleWEATTest = async (e: React.FormEvent) => {
    e.preventDefault()
    try {
      const targetWords = weatForm.targetWords.split(',').map(w => w.trim()).filter(w => w)
      const attributeWordsA = weatForm.attributeWordsA.split(',').map(w => w.trim()).filter(w => w)
      const attributeWordsB = weatForm.attributeWordsB.split(',').map(w => w.trim()).filter(w => w)
      
      let embeddings: Record<string, number[]> = {}
      try {
        embeddings = JSON.parse(weatForm.embeddings)
      } catch {
        throw new Error('Invalid embeddings JSON format')
      }

      const result = await runWEATTest({
        targetWords,
        attributeWordsA,
        attributeWordsB,
        embeddings,
      })
      setResults(result)
      toast({
        title: "WEAT test completed",
        description: "WEAT test has been completed successfully.",
      })
    } catch (err) {
      toast({
        title: "WEAT test failed",
        description: err instanceof Error ? err.message : "An error occurred",
        variant: "destructive",
      })
    }
  }

  return (
    <div className="space-y-6">
      {/* Header */}
      <div>
        <h1 className="text-4xl font-bold">Modern Bias Detection</h1>
        <p className="text-muted-foreground mt-1">
          Advanced bias detection using WEAT, SEAT, Minimal Pairs, StereoSet, and BBQ tests
        </p>
      </div>

      {error && (
        <Alert className="border-2 border-red-500 shadow-brutal">
          <IconAlertTriangle className="h-4 w-4" />
          <AlertTitle>Error</AlertTitle>
          <AlertDescription>{error.message}</AlertDescription>
        </Alert>
      )}

      <Tabs value={activeTab} onValueChange={setActiveTab} className="space-y-4">
        <TabsList className="border-2 border-black">
          <TabsTrigger value="comprehensive" className="border-r-2 border-black">Comprehensive Evaluation</TabsTrigger>
          <TabsTrigger value="weat" className="border-r-2 border-black">WEAT Test</TabsTrigger>
          <TabsTrigger value="results">Results</TabsTrigger>
        </TabsList>

        <TabsContent value="comprehensive" className="space-y-4">
          <Card className="p-6 border-2 border-black shadow-brutal">
            <h2 className="text-2xl font-bold mb-4">Comprehensive Bias Evaluation</h2>
            <form onSubmit={handleComprehensiveEvaluation} className="space-y-4">
              <div className="space-y-2">
                <Label htmlFor="modelId">Model ID *</Label>
                <Input
                  id="modelId"
                  value={comprehensiveForm.modelId}
                  onChange={(e) => setComprehensiveForm({ ...comprehensiveForm, modelId: e.target.value })}
                  placeholder="Enter model ID"
                  required
                  className="border-2 border-black"
                />
              </div>

              <div className="space-y-2">
                <Label htmlFor="datasetId">Dataset *</Label>
                <Select
                  value={comprehensiveForm.datasetId}
                  onValueChange={(value) => setComprehensiveForm({ ...comprehensiveForm, datasetId: value })}
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
                <Label>Test Types</Label>
                <div className="grid grid-cols-2 gap-2">
                  {TEST_TYPES.map((test) => (
                    <div key={test.value} className="flex items-center space-x-2">
                      <input
                        type="checkbox"
                        id={test.value}
                        checked={comprehensiveForm.testTypes.includes(test.value)}
                        onChange={(e) => {
                          if (e.target.checked) {
                            setComprehensiveForm({
                              ...comprehensiveForm,
                              testTypes: [...comprehensiveForm.testTypes, test.value],
                            })
                          } else {
                            setComprehensiveForm({
                              ...comprehensiveForm,
                              testTypes: comprehensiveForm.testTypes.filter(t => t !== test.value),
                            })
                          }
                        }}
                        className="border-2 border-black"
                      />
                      <Label htmlFor={test.value} className="font-normal">{test.label}</Label>
                    </div>
                  ))}
                </div>
              </div>

              <Button type="submit" variant="default" disabled={loading} className="w-full">
                {loading ? 'Running Evaluation...' : 'Run Comprehensive Evaluation'}
              </Button>
            </form>
          </Card>
        </TabsContent>

        <TabsContent value="weat" className="space-y-4">
          <Card className="p-6 border-2 border-black shadow-brutal">
            <h2 className="text-2xl font-bold mb-4">WEAT Test</h2>
            <form onSubmit={handleWEATTest} className="space-y-4">
              <div className="space-y-2">
                <Label htmlFor="targetWords">Target Words (comma-separated) *</Label>
                <Input
                  id="targetWords"
                  value={weatForm.targetWords}
                  onChange={(e) => setWeatForm({ ...weatForm, targetWords: e.target.value })}
                  placeholder="doctor, nurse, engineer, teacher"
                  required
                  className="border-2 border-black"
                />
              </div>

              <div className="space-y-2">
                <Label htmlFor="attributeWordsA">Attribute Words A (comma-separated) *</Label>
                <Input
                  id="attributeWordsA"
                  value={weatForm.attributeWordsA}
                  onChange={(e) => setWeatForm({ ...weatForm, attributeWordsA: e.target.value })}
                  placeholder="male, man, he, his"
                  required
                  className="border-2 border-black"
                />
              </div>

              <div className="space-y-2">
                <Label htmlFor="attributeWordsB">Attribute Words B (comma-separated) *</Label>
                <Input
                  id="attributeWordsB"
                  value={weatForm.attributeWordsB}
                  onChange={(e) => setWeatForm({ ...weatForm, attributeWordsB: e.target.value })}
                  placeholder="female, woman, she, her"
                  required
                  className="border-2 border-black"
                />
              </div>

              <div className="space-y-2">
                <Label htmlFor="embeddings">Embeddings (JSON format) *</Label>
                <Textarea
                  id="embeddings"
                  value={weatForm.embeddings}
                  onChange={(e) => setWeatForm({ ...weatForm, embeddings: e.target.value })}
                  placeholder='{"doctor": [0.1, 0.2, ...], "nurse": [0.3, 0.4, ...]}'
                  required
                  className="border-2 border-black font-mono text-sm"
                  rows={6}
                />
              </div>

              <Button type="submit" variant="default" disabled={loading} className="w-full">
                {loading ? 'Running WEAT Test...' : 'Run WEAT Test'}
              </Button>
            </form>
          </Card>
        </TabsContent>

        <TabsContent value="results" className="space-y-4">
          {results ? (
            <Card className="p-6 border-2 border-black shadow-brutal">
              <h2 className="text-2xl font-bold mb-4">Test Results</h2>
              
              {results.overallBiasScore !== undefined && (
                <div className="mb-6">
                  <div className="flex items-center justify-between mb-2">
                    <Label className="text-lg">Overall Bias Score</Label>
                    <Badge variant={results.overallBiasScore > 0.7 ? 'destructive' : results.overallBiasScore > 0.5 ? 'secondary' : 'default'} className="border-2 border-black">
                      {(results.overallBiasScore * 100).toFixed(1)}%
                    </Badge>
                  </div>
                  <div className="h-4 bg-gray-200 border-2 border-black">
                    <div 
                      className="h-full bg-orange-500" 
                      style={{ width: `${results.overallBiasScore * 100}%` }}
                    />
                  </div>
                </div>
              )}

              {results.biasScore !== undefined && (
                <div className="mb-6">
                  <div className="flex items-center justify-between mb-2">
                    <Label className="text-lg">Bias Score</Label>
                    <Badge variant={results.biasScore > 0.7 ? 'destructive' : results.biasScore > 0.5 ? 'secondary' : 'default'} className="border-2 border-black">
                      {(results.biasScore * 100).toFixed(1)}%
                    </Badge>
                  </div>
                  <div className="h-4 bg-gray-200 border-2 border-black">
                    <div 
                      className="h-full bg-orange-500" 
                      style={{ width: `${results.biasScore * 100}%` }}
                    />
                  </div>
                </div>
              )}

              {results.testResults && results.testResults.length > 0 && (
                <div className="space-y-3">
                  <h3 className="text-lg font-bold">Test Results</h3>
                  {results.testResults.map((test: any, index: number) => (
                    <div key={index} className="p-4 border-2 border-black bg-white">
                      <div className="flex items-center justify-between mb-2">
                        <span className="font-medium">{test.testName || test.testType}</span>
                        <Badge variant={test.isBiased ? 'destructive' : 'default'} className="border-2 border-black">
                          {test.isBiased ? 'Biased' : 'Not Biased'}
                        </Badge>
                      </div>
                      <div className="text-sm text-muted-foreground">
                        Score: {(test.biasScore * 100).toFixed(1)}% | Confidence: {(test.confidence * 100).toFixed(1)}%
                      </div>
                      {test.recommendations && test.recommendations.length > 0 && (
                        <div className="mt-2">
                          <Label className="text-sm font-medium">Recommendations:</Label>
                          <ul className="list-disc list-inside text-sm text-muted-foreground">
                            {test.recommendations.map((rec: string, i: number) => (
                              <li key={i}>{rec}</li>
                            ))}
                          </ul>
                        </div>
                      )}
                    </div>
                  ))}
                </div>
              )}

              {results.recommendations && results.recommendations.length > 0 && (
                <div className="mt-6">
                  <h3 className="text-lg font-bold mb-2">Recommendations</h3>
                  <ul className="list-disc list-inside space-y-1">
                    {results.recommendations.map((rec: string, i: number) => (
                      <li key={i} className="text-muted-foreground">{rec}</li>
                    ))}
                  </ul>
                </div>
              )}
            </Card>
          ) : (
            <Card className="p-6 border-2 border-black shadow-brutal">
              <div className="text-center py-12">
                <IconBrain className="h-12 w-12 mx-auto text-muted-foreground mb-4" />
                <p className="text-lg font-medium mb-2">No results yet</p>
                <p className="text-muted-foreground">
                  Run a bias test to see results here
                </p>
              </div>
            </Card>
          )}
        </TabsContent>
      </Tabs>
    </div>
  )
}

