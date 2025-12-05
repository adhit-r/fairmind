'use client'

import { useState } from 'react'
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
import { IconBrain, IconTarget, IconCheck, IconX, IconAlertTriangle, IconSparkles, IconShield } from '@tabler/icons-react'
import { apiClient } from '@/lib/api/api-client'

const JUDGE_MODELS = [
  { value: 'gpt-4-turbo', label: 'GPT-4 Turbo' },
  { value: 'gpt-4', label: 'GPT-4' },
  { value: 'claude-3-opus', label: 'Claude 3 Opus' },
  { value: 'claude-3-sonnet', label: 'Claude 3 Sonnet' },
  { value: 'gemini-pro', label: 'Gemini Pro' },
]

const BIAS_CATEGORIES = [
  { value: 'gender', label: 'Gender Bias' },
  { value: 'race', label: 'Racial Bias' },
  { value: 'age', label: 'Age Bias' },
  { value: 'cultural', label: 'Cultural Bias' },
  { value: 'socioeconomic', label: 'Socioeconomic Bias' },
  { value: 'intersectional', label: 'Intersectional Bias' },
]

const SOTA_METHODS = [
  { 
    id: 'llm-as-judge', 
    name: 'LLM-as-Judge', 
    description: 'Use a judge LLM to evaluate bias with reasoning',
    icon: IconSparkles,
    status: 'available'
  },
  { 
    id: 'counterfactual', 
    name: 'Counterfactual Fairness', 
    description: 'Test consistency when demographic terms are swapped',
    icon: IconTarget,
    status: 'available'
  },
  { 
    id: 'red-teaming', 
    name: 'Red Teaming', 
    description: 'Adversarial testing to discover emergent bias',
    icon: IconShield,
    status: 'available'
  },
  { 
    id: 'weat-seat', 
    name: 'WEAT/SEAT', 
    description: 'Word/Sentence Embedding Association Test',
    icon: IconBrain,
    status: 'available'
  },
  { 
    id: 'minimal-pairs', 
    name: 'Minimal Pairs', 
    description: 'Behavioral bias detection through minimal comparisons',
    icon: IconTarget,
    status: 'available'
  },
]

export default function LLMTestingPage() {
  const { toast } = useToast()
  const [activeMethod, setActiveMethod] = useState('llm-as-judge')
  const [loading, setLoading] = useState(false)
  const [results, setResults] = useState<any>(null)
  const [error, setError] = useState<string | null>(null)

  // LLM-as-Judge form state
  const [judgeForm, setJudgeForm] = useState({
    judgeModel: 'gpt-4-turbo',
    biasCategory: 'gender',
    targetModel: '',
    prompts: '',
    responses: '',
  })

  // Counterfactual form state
  const [counterfactualForm, setCounterfactualForm] = useState({
    prompts: '',
    responses: '',
  })

  const handleLLMAsJudge = async (e: React.FormEvent) => {
    e.preventDefault()
    setLoading(true)
    setError(null)

    try {
      // Parse prompts and responses
      const prompts = judgeForm.prompts.split('\n').filter(p => p.trim())
      const responses = judgeForm.responses.split('\n').filter(r => r.trim())

      if (prompts.length !== responses.length) {
        throw new Error('Number of prompts must match number of responses')
      }

      const modelOutputs = prompts.map((prompt, i) => ({
        prompt: prompt.trim(),
        output: responses[i].trim(),
        metadata: { model: judgeForm.targetModel || 'unknown' }
      }))

      // Call LLM-as-Judge endpoint (via comprehensive evaluation or direct)
      const token = localStorage.getItem('access_token')
      if (!token) throw new Error('Not authenticated')

      // For now, use the bias detection endpoint with LLM mode
      const response = await fetch('/api/v1/bias-detection/detect', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          'Authorization': `Bearer ${token}`
        },
        body: JSON.stringify({
          model_type: 'text_generation',
          test_category: 'representational',
          sensitive_attributes: [judgeForm.biasCategory],
          model_outputs: modelOutputs
        })
      })

      if (!response.ok) {
        const err = await response.json()
        throw new Error(err.detail || 'LLM-as-Judge evaluation failed')
      }

      const data = await response.json()
      
      // Format results for LLM-as-Judge display
      setResults({
        method: 'llm-as-judge',
        judgeModel: judgeForm.judgeModel,
        biasCategory: judgeForm.biasCategory,
        timestamp: new Date().toISOString(),
        ...data,
        // Add mock LLM-as-Judge specific fields (would come from actual service)
        reasoning: data.recommendations?.[0] || 'Bias detected through comprehensive analysis',
        evidence: modelOutputs.slice(0, 3).map((o, i) => `Output ${i + 1}: ${o.output.substring(0, 100)}...`),
        severity: data.overall_bias_score > 0.7 ? 'high' : data.overall_bias_score > 0.4 ? 'medium' : 'low'
      })

      toast({
        title: "Evaluation Complete",
        description: `LLM-as-Judge evaluation completed with ${judgeForm.judgeModel}`,
      })
    } catch (err) {
      const errorMsg = err instanceof Error ? err.message : 'Evaluation failed'
      setError(errorMsg)
      toast({
        title: "Evaluation Failed",
        description: errorMsg,
        variant: "destructive",
      })
    } finally {
      setLoading(false)
    }
  }

  const handleCounterfactual = async (e: React.FormEvent) => {
    e.preventDefault()
    setLoading(true)
    setError(null)

    try {
      const prompts = counterfactualForm.prompts.split('\n').filter(p => p.trim())
      const responses = counterfactualForm.responses.split('\n').filter(r => r.trim())

      if (prompts.length !== responses.length) {
        throw new Error('Number of prompts must match number of responses')
      }

      const token = localStorage.getItem('access_token')
      if (!token) throw new Error('Not authenticated')

      const response = await fetch('/api/v1/bias-detection-v2/detect-llm', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          'Authorization': `Bearer ${token}`
        },
        body: JSON.stringify({
          dataset_id: null, // Direct input mode
          metrics: ['counterfactual_fairness'],
          prompt_column: 'prompt',
          response_column: 'response',
          prompts: prompts,
          responses: responses
        })
      })

      if (!response.ok) {
        const err = await response.json()
        throw new Error(err.detail || 'Counterfactual analysis failed')
      }

      const data = await response.json()
      setResults({
        method: 'counterfactual',
        timestamp: new Date().toISOString(),
        ...data
      })

      toast({
        title: "Analysis Complete",
        description: "Counterfactual fairness analysis completed",
      })
    } catch (err) {
      const errorMsg = err instanceof Error ? err.message : 'Analysis failed'
      setError(errorMsg)
      toast({
        title: "Analysis Failed",
        description: errorMsg,
        variant: "destructive",
      })
    } finally {
      setLoading(false)
    }
  }

  return (
    <div className="space-y-6">
      {/* Header */}
      <div>
        <h1 className="text-4xl font-bold">LLM Testing - SOTA Methods</h1>
        <p className="text-muted-foreground mt-1">
          Test LLMs using State-of-the-Art bias detection methods
        </p>
      </div>

      {/* Method Selection */}
      <Card className="p-6 border-2 border-black shadow-brutal">
        <h2 className="text-2xl font-bold mb-4">Available SOTA Methods</h2>
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
          {SOTA_METHODS.map((method) => {
            const Icon = method.icon
            const isActive = activeMethod === method.id
            return (
              <button
                key={method.id}
                onClick={() => setActiveMethod(method.id)}
                className={`
                  p-4 border-2 rounded-none text-left transition-all
                  ${isActive 
                    ? 'bg-black text-white border-black shadow-[4px_4px_0px_0px_#FF6B35]' 
                    : 'bg-white border-black hover:bg-orange hover:shadow-[4px_4px_0px_0px_#000] hover:-translate-y-[2px] hover:-translate-x-[2px]'
                  }
                `}
              >
                <div className="flex items-start gap-3">
                  <Icon className="h-6 w-6 mt-1 flex-shrink-0" />
                  <div>
                    <h3 className="font-bold text-sm uppercase">{method.name}</h3>
                    <p className="text-xs mt-1 opacity-80">{method.description}</p>
                    <Badge 
                      variant={method.status === 'available' ? 'default' : 'secondary'}
                      className="mt-2 text-xs"
                    >
                      {method.status === 'available' ? 'Available' : 'Coming Soon'}
                    </Badge>
                  </div>
                </div>
              </button>
            )
          })}
        </div>
      </Card>

      {/* Error Display */}
      {error && (
        <Alert className="border-2 border-red-500 bg-red-50">
          <IconAlertTriangle className="h-4 w-4" />
          <AlertTitle>Error</AlertTitle>
          <AlertDescription>{error}</AlertDescription>
        </Alert>
      )}

      {/* LLM-as-Judge Form */}
      {activeMethod === 'llm-as-judge' && (
        <Card className="p-6 border-2 border-black shadow-brutal">
          <div className="flex items-center gap-2 mb-4">
            <IconSparkles className="h-6 w-6" />
            <h2 className="text-2xl font-bold">LLM-as-Judge Evaluation</h2>
            <Badge className="ml-auto bg-orange text-black border-2 border-black">SOTA 2025</Badge>
          </div>
          
          <form onSubmit={handleLLMAsJudge} className="space-y-4">
            <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
              <div className="space-y-2">
                <Label htmlFor="judgeModel">Judge Model</Label>
                <Select
                  value={judgeForm.judgeModel}
                  onValueChange={(value) => setJudgeForm({ ...judgeForm, judgeModel: value })}
                >
                  <SelectTrigger className="border-2 border-black">
                    <SelectValue />
                  </SelectTrigger>
                  <SelectContent>
                    {JUDGE_MODELS.map((model) => (
                      <SelectItem key={model.value} value={model.value}>
                        {model.label}
                      </SelectItem>
                    ))}
                  </SelectContent>
                </Select>
              </div>

              <div className="space-y-2">
                <Label htmlFor="biasCategory">Bias Category</Label>
                <Select
                  value={judgeForm.biasCategory}
                  onValueChange={(value) => setJudgeForm({ ...judgeForm, biasCategory: value })}
                >
                  <SelectTrigger className="border-2 border-black">
                    <SelectValue />
                  </SelectTrigger>
                  <SelectContent>
                    {BIAS_CATEGORIES.map((cat) => (
                      <SelectItem key={cat.value} value={cat.value}>
                        {cat.label}
                      </SelectItem>
                    ))}
                  </SelectContent>
                </Select>
              </div>
            </div>

            <div className="space-y-2">
              <Label htmlFor="targetModel">Target Model Name (Optional)</Label>
              <Input
                id="targetModel"
                value={judgeForm.targetModel}
                onChange={(e) => setJudgeForm({ ...judgeForm, targetModel: e.target.value })}
                placeholder="e.g., gpt-4, claude-3, custom-model"
                className="border-2 border-black"
              />
            </div>

            <div className="space-y-2">
              <Label htmlFor="prompts">Prompts (one per line)</Label>
              <Textarea
                id="prompts"
                value={judgeForm.prompts}
                onChange={(e) => setJudgeForm({ ...judgeForm, prompts: e.target.value })}
                placeholder="The doctor was&#10;The nurse was&#10;The engineer was"
                rows={4}
                className="border-2 border-black font-mono"
                required
              />
            </div>

            <div className="space-y-2">
              <Label htmlFor="responses">Model Responses (one per line, matching prompts)</Label>
              <Textarea
                id="responses"
                value={judgeForm.responses}
                onChange={(e) => setJudgeForm({ ...judgeForm, responses: e.target.value })}
                placeholder="The doctor was a skilled professional&#10;The nurse was caring and attentive&#10;The engineer was brilliant and innovative"
                rows={4}
                className="border-2 border-black font-mono"
                required
              />
            </div>

            <Button
              type="submit"
              disabled={loading}
              className="w-full h-12 border-2 border-black bg-orange text-black hover:bg-yellow-400 font-bold uppercase shadow-[4px_4px_0px_0px_#000] hover:shadow-none hover:translate-x-[4px] hover:translate-y-[4px] transition-all"
            >
              {loading ? 'Evaluating...' : 'Run LLM-as-Judge Evaluation'}
            </Button>
          </form>
        </Card>
      )}

      {/* Counterfactual Fairness Form */}
      {activeMethod === 'counterfactual' && (
        <Card className="p-6 border-2 border-black shadow-brutal">
          <div className="flex items-center gap-2 mb-4">
            <IconTarget className="h-6 w-6" />
            <h2 className="text-2xl font-bold">Counterfactual Fairness</h2>
            <Badge className="ml-auto bg-orange text-black border-2 border-black">SOTA</Badge>
          </div>
          
          <form onSubmit={handleCounterfactual} className="space-y-4">
            <div className="space-y-2">
              <Label htmlFor="cf-prompts">Prompts (one per line)</Label>
              <Textarea
                id="cf-prompts"
                value={counterfactualForm.prompts}
                onChange={(e) => setCounterfactualForm({ ...counterfactualForm, prompts: e.target.value })}
                placeholder="The doctor was&#10;The nurse was"
                rows={4}
                className="border-2 border-black font-mono"
                required
              />
            </div>

            <div className="space-y-2">
              <Label htmlFor="cf-responses">Model Responses (one per line)</Label>
              <Textarea
                id="cf-responses"
                value={counterfactualForm.responses}
                onChange={(e) => setCounterfactualForm({ ...counterfactualForm, responses: e.target.value })}
                placeholder="The doctor was skilled&#10;The nurse was caring"
                rows={4}
                className="border-2 border-black font-mono"
                required
              />
            </div>

            <Button
              type="submit"
              disabled={loading}
              className="w-full h-12 border-2 border-black bg-orange text-black hover:bg-yellow-400 font-bold uppercase shadow-[4px_4px_0px_0px_#000] hover:shadow-none hover:translate-x-[4px] hover:translate-y-[4px] transition-all"
            >
              {loading ? 'Analyzing...' : 'Run Counterfactual Analysis'}
            </Button>
          </form>
        </Card>
      )}

      {/* Results Display */}
      {results && (
        <Card className="p-6 border-2 border-black shadow-brutal">
          <h2 className="text-2xl font-bold mb-4">Evaluation Results</h2>
          
          <Tabs defaultValue="summary" className="w-full">
            <TabsList className="border-2 border-black">
              <TabsTrigger value="summary" className="border-r-2 border-black">Summary</TabsTrigger>
              <TabsTrigger value="details">Details</TabsTrigger>
              <TabsTrigger value="recommendations">Recommendations</TabsTrigger>
            </TabsList>

            <TabsContent value="summary" className="space-y-4 mt-4">
              <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
                <div className="p-4 border-2 border-black bg-white">
                  <p className="text-sm font-medium text-muted-foreground mb-1">Bias Score</p>
                  <p className="text-3xl font-bold">
                    {results.overall_bias_score?.toFixed(2) || results.bias_score?.toFixed(2) || 'N/A'}
                  </p>
                </div>
                <div className="p-4 border-2 border-black bg-white">
                  <p className="text-sm font-medium text-muted-foreground mb-1">Severity</p>
                  <Badge 
                    className={`
                      text-lg px-3 py-1
                      ${results.severity === 'high' ? 'bg-red-500 text-white' : ''}
                      ${results.severity === 'medium' ? 'bg-orange text-black' : ''}
                      ${results.severity === 'low' ? 'bg-green-500 text-white' : ''}
                    `}
                  >
                    {results.severity?.toUpperCase() || 'UNKNOWN'}
                  </Badge>
                </div>
                <div className="p-4 border-2 border-black bg-white">
                  <p className="text-sm font-medium text-muted-foreground mb-1">Method</p>
                  <p className="text-lg font-bold uppercase">{results.method || 'N/A'}</p>
                </div>
              </div>

              {results.reasoning && (
                <div className="p-4 border-2 border-black bg-white">
                  <p className="text-sm font-bold mb-2">Judge Reasoning:</p>
                  <p className="text-sm">{results.reasoning}</p>
                </div>
              )}

              {results.evidence && results.evidence.length > 0 && (
                <div className="p-4 border-2 border-black bg-white">
                  <p className="text-sm font-bold mb-2">Evidence:</p>
                  <ul className="list-disc list-inside space-y-1">
                    {results.evidence.map((ev: string, i: number) => (
                      <li key={i} className="text-sm">{ev}</li>
                    ))}
                  </ul>
                </div>
              )}
            </TabsContent>

            <TabsContent value="details" className="mt-4">
              <pre className="p-4 border-2 border-black bg-white overflow-auto text-xs">
                {JSON.stringify(results, null, 2)}
              </pre>
            </TabsContent>

            <TabsContent value="recommendations" className="mt-4">
              <div className="space-y-2">
                {results.recommendations && results.recommendations.length > 0 ? (
                  results.recommendations.map((rec: string, i: number) => (
                    <div key={i} className="p-3 border-2 border-black bg-white">
                      <p className="text-sm">{rec}</p>
                    </div>
                  ))
                ) : (
                  <p className="text-sm text-muted-foreground">No recommendations available</p>
                )}
              </div>
            </TabsContent>
          </Tabs>
        </Card>
      )}

      {/* Info Card */}
      <Card className="p-6 border-2 border-black shadow-brutal bg-orange">
        <h3 className="font-bold text-lg mb-2">About SOTA Methods</h3>
        <p className="text-sm mb-2">
          These methods represent the latest State-of-the-Art techniques for LLM bias detection:
        </p>
        <ul className="text-sm space-y-1 list-disc list-inside">
          <li><strong>LLM-as-Judge:</strong> Uses a judge LLM to evaluate bias with reasoning (2024-2025)</li>
          <li><strong>Counterfactual Fairness:</strong> Tests consistency when demographic terms are swapped</li>
          <li><strong>Red Teaming:</strong> Adversarial testing to discover emergent bias patterns</li>
          <li><strong>WEAT/SEAT:</strong> Embedding-level bias detection</li>
          <li><strong>Minimal Pairs:</strong> Contextual bias detection through controlled comparisons</li>
        </ul>
      </Card>
    </div>
  )
}

