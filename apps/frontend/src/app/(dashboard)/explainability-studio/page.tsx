/**
 * Explainability Studio
 * Deep analysis of why models produce certain outputs — attribution, attention, and counterfactuals.
 */

'use client'

import { useState } from 'react'
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card'
import { Button } from '@/components/ui/button'
import { Textarea } from '@/components/ui/textarea'
import { Label } from '@/components/ui/label'
import { Badge } from '@/components/ui/badge'
import { Progress } from '@/components/ui/progress'
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/ui/tabs'
import { Checkbox } from '@/components/ui/checkbox'
import { useModernBias } from '@/lib/api/hooks/useModernBias'
import { useToast } from '@/hooks/use-toast'
import {
  IconBrain,
  IconSparkles,
  IconMicroscope,
  IconChartBar,
  IconBulb,
  IconDownload,
  IconRefresh,
  IconCheck,
  IconAlertTriangle,
  IconInfoCircle,
  IconArrowRight,
  IconCode,
  IconEye,
  IconTarget,
  IconFlask,
} from '@tabler/icons-react'

// ─── Types ────────────────────────────────────────────────────────────────────

interface ExplainabilityResult {
  methods_used: string[]
  insights: string[]
  visualizations: string[]
  confidence: number
  feature_attributions?: Record<string, number>
  attention_patterns?: Record<string, number>
  counterfactuals?: Array<{
    original: string
    modified: string
    impact: number
    attribute: string
  }>
  bias_attribution?: Record<string, number>
}

// ─── Method configuration ─────────────────────────────────────────────────────

const EXPLAINABILITY_METHODS = [
  {
    id: 'attention',
    label: 'Attention Analysis',
    description: 'Visualize which tokens the model attends to most during inference',
    icon: IconEye,
    color: 'bg-blue-100 text-blue-700 border-blue-300',
  },
  {
    id: 'lime',
    label: 'LIME',
    description: 'Local surrogate models that approximate the decision boundary',
    icon: IconFlask,
    color: 'bg-purple-100 text-purple-700 border-purple-300',
  },
  {
    id: 'shap',
    label: 'SHAP Values',
    description: 'SHapley Additive exPlanations — game-theory attribution',
    icon: IconChartBar,
    color: 'bg-teal-100 text-teal-700 border-teal-300',
  },
  {
    id: 'integrated_gradients',
    label: 'Integrated Gradients',
    description: 'Gradient-based attribution along the interpolation path',
    icon: IconTarget,
    color: 'bg-orange-100 text-orange-700 border-orange-300',
  },
  {
    id: 'activation_patching',
    label: 'Activation Patching',
    description: 'Causal tracing to find which components drive behavior',
    icon: IconCode,
    color: 'bg-pink-100 text-pink-700 border-pink-300',
  },
] as const

// ─── Component ─────────────────────────────────────────────────────────────────

export default function ExplainabilityStudioPage() {
  const { runExplainabilityAnalysis, loading } = useModernBias()
  const { toast } = useToast()

  const [modelOutput, setModelOutput] = useState('')
  const [selectedMethods, setSelectedMethods] = useState<string[]>(['attention', 'shap'])
  const [includeVisualizations, setIncludeVisualizations] = useState(true)
  const [results, setResults] = useState<ExplainabilityResult | null>(null)
  const [activeTab, setActiveTab] = useState('overview')

  // ─── Method toggle ──────────────────────────────────────────────────────────

  const toggleMethod = (methodId: string) => {
    setSelectedMethods(prev =>
      prev.includes(methodId) ? prev.filter(m => m !== methodId) : [...prev, methodId]
    )
  }

  // ─── Run analysis ───────────────────────────────────────────────────────────

  const handleRunAnalysis = async () => {
    if (!modelOutput.trim()) {
      toast({
        title: 'Model output required',
        description: 'Please enter at least one model output sample to analyze.',
        variant: 'destructive',
      })
      return
    }
    if (selectedMethods.length === 0) {
      toast({
        title: 'No methods selected',
        description: 'Select at least one explainability method to run.',
        variant: 'destructive',
      })
      return
    }

    try {
      const data = await runExplainabilityAnalysis({
        modelOutputs: [{ text: modelOutput.trim() }],
        methods: selectedMethods,
        includeVisualizations,
      })
      setResults(data)
      setActiveTab('overview')
      toast({
        title: 'Analysis complete',
        description: `${data?.methods_used?.length ?? selectedMethods.length} methods applied successfully.`,
      })
    } catch (err) {
      toast({
        title: 'Analysis failed',
        description: err instanceof Error ? err.message : 'An unexpected error occurred.',
        variant: 'destructive',
      })
    }
  }

  // ─── Export ─────────────────────────────────────────────────────────────────

  const handleExportJSON = () => {
    if (!results) return
    const blob = new Blob([JSON.stringify({ generated_at: new Date().toISOString(), results }, null, 2)], {
      type: 'application/json',
    })
    const url = URL.createObjectURL(blob)
    const a = document.createElement('a')
    a.href = url
    a.download = `explainability_${new Date().toISOString().split('T')[0]}.json`
    a.click()
    URL.revokeObjectURL(url)
  }

  // ─── Helpers ────────────────────────────────────────────────────────────────

  const getConfidenceColor = (confidence: number) => {
    if (confidence >= 0.8) return 'text-green-700'
    if (confidence >= 0.6) return 'text-yellow-700'
    return 'text-red-700'
  }

  const getConfidenceBg = (confidence: number) => {
    if (confidence >= 0.8) return 'bg-green-50 border-green-300'
    if (confidence >= 0.6) return 'bg-yellow-50 border-yellow-300'
    return 'bg-red-50 border-red-300'
  }

  const getAttributionWidth = (value: number, max: number) =>
    max > 0 ? Math.abs(value / max) * 100 : 0

  const getAttributionColor = (value: number) =>
    value >= 0 ? 'bg-teal-500' : 'bg-red-500'

  // ─── Render ─────────────────────────────────────────────────────────────────

  return (
    <div className="space-y-6">
      {/* ── Page Header ─────────────────────────────────────────────────────── */}
      <div className="flex items-start justify-between">
        <div className="flex items-center gap-4">
          <div className="p-3 bg-purple-100 rounded-[14px] shadow-[var(--fm-shadow)]">
            <IconMicroscope className="h-8 w-8 text-purple-700" />
          </div>
          <div>
            <h1 className="text-4xl font-semibold tracking-tight">Explainability Studio</h1>
            <p className="text-muted-foreground mt-1 text-sm">
              Understand <span className="font-bold text-foreground">why</span> your model makes
              decisions — attribution, attention, and counterfactual analysis.
            </p>
          </div>
        </div>
        {results && (
          <Button
            variant="neutral"
            onClick={handleExportJSON}
            className="font-bold fm-card"
          >
            <IconDownload className="h-4 w-4 mr-2" />
            Export JSON
          </Button>
        )}
      </div>

      {/* ── Main Layout ─────────────────────────────────────────────────────── */}
      <div className="grid grid-cols-1 lg:grid-cols-5 gap-6">

        {/* ── Config Panel (left 2 cols) ──────────────────────────────────── */}
        <div className="lg:col-span-2 space-y-4">

          {/* Model Output Input */}
          <Card className="fm-card">
            <CardHeader className="border-b border-[var(--fm-line)] pb-4">
              <CardTitle className="flex items-center gap-2 text-base">
                <IconBrain className="h-5 w-5 text-purple-600" />
                Model Output Sample
              </CardTitle>
              <CardDescription>
                Paste the raw text output your model generated
              </CardDescription>
            </CardHeader>
            <CardContent className="pt-4">
              <div className="space-y-2">
                <Label htmlFor="model-output" className="font-semibold text-xs uppercase tracking-wider">
                  Output Text
                </Label>
                <Textarea
                  id="model-output"
                  value={modelOutput}
                  onChange={e => setModelOutput(e.target.value)}
                  placeholder="Paste the model's output here…&#10;&#10;Example: 'The candidate John Smith is highly qualified for this engineering role. His technical background is impressive.'&#10;&#10;The studio will analyze attribution, attention patterns, and fairness-relevant features."
                  className="border border-[var(--fm-line)] min-h-[180px] resize-none font-mono text-sm focus-visible:ring-0 focus-visible:border-purple-500"
                />
                <p className="text-xs text-muted-foreground">
                  {modelOutput.trim().split(/\s+/).filter(Boolean).length} words
                </p>
              </div>
            </CardContent>
          </Card>

          {/* Method Selection */}
          <Card className="fm-card">
            <CardHeader className="border-b border-[var(--fm-line)] pb-4">
              <CardTitle className="flex items-center gap-2 text-base">
                <IconSparkles className="h-5 w-5 text-orange-500" />
                Explainability Methods
              </CardTitle>
              <CardDescription>
                Select which analysis techniques to apply
              </CardDescription>
            </CardHeader>
            <CardContent className="pt-4 space-y-3">
              {EXPLAINABILITY_METHODS.map(method => {
                const Icon = method.icon
                const isSelected = selectedMethods.includes(method.id)
                return (
                  <button
                    key={method.id}
                    onClick={() => toggleMethod(method.id)}
                    className={`w-full flex items-start gap-3 p-3 border-2 text-left transition-all ${
                      isSelected
                        ? 'border-[var(--fm-line)] bg-[var(--fm-ink)] text-white'
                        : 'border-[var(--fm-line)] bg-white hover:bg-gray-50'
                    }`}
                  >
                    <div className={`p-1.5 border mt-0.5 ${isSelected ? 'border-white bg-white/10' : 'border-[var(--fm-line)]'}`}>
                      <Icon className={`h-4 w-4 ${isSelected ? 'text-white' : ''}`} />
                    </div>
                    <div className="flex-1 min-w-0">
                      <div className="flex items-center justify-between gap-2">
                        <span className="font-bold text-sm">{method.label}</span>
                        {isSelected && (
                          <IconCheck className="h-4 w-4 flex-shrink-0" />
                        )}
                      </div>
                      <p className={`text-xs mt-0.5 ${isSelected ? 'text-white/70' : 'text-muted-foreground'}`}>
                        {method.description}
                      </p>
                    </div>
                  </button>
                )
              })}

              {/* Include visualizations toggle */}
              <div className="flex items-center gap-3 pt-2 border-t border-dashed border-[var(--fm-line)]">
                <Checkbox
                  id="viz"
                  checked={includeVisualizations}
                  onCheckedChange={v => setIncludeVisualizations(!!v)}
                  className="border border-[var(--fm-line)]"
                />
                <Label htmlFor="viz" className="text-sm font-bold cursor-pointer">
                  Include visualization metadata
                </Label>
              </div>
            </CardContent>
          </Card>

          {/* Run button */}
          <Button
            onClick={handleRunAnalysis}
            disabled={loading || selectedMethods.length === 0 || !modelOutput.trim()}
            className="w-full font-semibold text-base h-12 bg-[var(--fm-ink)] text-white hover:bg-black disabled:opacity-50 rounded-[14px] shadow-[var(--fm-shadow)]"
          >
            {loading ? (
              <>
                <IconRefresh className="h-5 w-5 mr-2 animate-spin" />
                Analyzing…
              </>
            ) : (
              <>
                <IconMicroscope className="h-5 w-5 mr-2" />
                Run Explainability Analysis
              </>
            )}
          </Button>

          {selectedMethods.length > 0 && (
            <p className="text-xs text-center text-muted-foreground">
              {selectedMethods.length} method{selectedMethods.length !== 1 ? 's' : ''} selected ·{' '}
              ~{selectedMethods.length * 8}–{selectedMethods.length * 15}s runtime
            </p>
          )}
        </div>

        {/* ── Results Panel (right 3 cols) ─────────────────────────────────── */}
        <div className="lg:col-span-3">
          {!results && !loading ? (
            /* Empty state */
            <Card className="h-full min-h-[500px] flex flex-col items-center justify-center text-center fm-card">
              <CardContent className="pt-12 pb-12">
                <div className="p-6 border border-dashed border-[rgba(21,23,26,.14)] inline-block mb-6">
                  <IconMicroscope className="h-16 w-16 text-purple-300" />
                </div>
                <h3 className="text-xl font-semibold mb-2">No Analysis Yet</h3>
                <p className="text-muted-foreground text-sm max-w-sm">
                  Configure your model output and select explainability methods, then run the
                  analysis to see results here.
                </p>
                <div className="mt-6 flex flex-col gap-3 text-left max-w-xs mx-auto">
                  {[
                    'Paste a model output on the left',
                    'Choose explainability methods',
                    'Click Run Analysis',
                  ].map((step, i) => (
                    <div key={i} className="flex items-center gap-3">
                      <span className="flex-shrink-0 w-6 h-6 border border-[var(--fm-line)] bg-[var(--fm-ink)] text-white text-xs font-semibold flex items-center justify-center">
                        {i + 1}
                      </span>
                      <span className="text-sm text-muted-foreground">{step}</span>
                    </div>
                  ))}
                </div>
              </CardContent>
            </Card>
          ) : loading ? (
            /* Loading state */
            <Card className="h-full min-h-[500px] flex flex-col items-center justify-center fm-card">
              <CardContent className="pt-12 text-center">
                <div className="p-4 bg-purple-100 border border-[var(--fm-line)] inline-block mb-4 animate-pulse">
                  <IconBrain className="h-12 w-12 text-purple-700" />
                </div>
                <h3 className="text-xl font-semibold mb-2">Analyzing Model Behavior</h3>
                <p className="text-muted-foreground text-sm mb-6">
                  Running {selectedMethods.length} explainability method
                  {selectedMethods.length !== 1 ? 's' : ''}…
                </p>
                <div className="space-y-2 max-w-xs mx-auto">
                  {selectedMethods.map((m, i) => {
                    const method = EXPLAINABILITY_METHODS.find(e => e.id === m)
                    return (
                      <div key={m} className="flex items-center gap-2 text-sm">
                        <IconRefresh className="h-3 w-3 animate-spin text-purple-600" />
                        <span className="text-muted-foreground">
                          Running {method?.label ?? m}…
                        </span>
                      </div>
                    )
                  })}
                </div>
              </CardContent>
            </Card>
          ) : results ? (
            /* Results */
            <div className="space-y-4">
              {/* Confidence + Methods summary */}
              <div className="grid grid-cols-3 gap-3">
                <div className={`p-3 ${getConfidenceBg(results.confidence ?? 0)} rounded-[14px] shadow-[var(--fm-shadow)]`}>
                  <p className="text-xs font-semibold uppercase tracking-wider text-muted-foreground">
                    Confidence
                  </p>
                  <p className={`text-2xl font-semibold mt-1 ${getConfidenceColor(results.confidence ?? 0)}`}>
                    {((results.confidence ?? 0) * 100).toFixed(0)}%
                  </p>
                </div>
                <div className="p-3 bg-gray-50 rounded-[14px] shadow-[var(--fm-shadow)]">
                  <p className="text-xs font-semibold uppercase tracking-wider text-muted-foreground">
                    Methods Used
                  </p>
                  <p className="text-2xl font-semibold mt-1">
                    {results.methods_used?.length ?? selectedMethods.length}
                  </p>
                </div>
                <div className="p-3 bg-gray-50 rounded-[14px] shadow-[var(--fm-shadow)]">
                  <p className="text-xs font-semibold uppercase tracking-wider text-muted-foreground">
                    Insights
                  </p>
                  <p className="text-2xl font-semibold mt-1">
                    {results.insights?.length ?? 0}
                  </p>
                </div>
              </div>

              {/* Tabs */}
              <Card className="fm-card">
                <Tabs value={activeTab} onValueChange={setActiveTab}>
                  <div className="border-b border-[var(--fm-line)] px-4 pt-4">
                    <TabsList className="bg-transparent p-0 h-auto gap-1">
                      {[
                        { id: 'overview', label: 'Overview', icon: IconBulb },
                        { id: 'attribution', label: 'Attribution', icon: IconChartBar },
                        { id: 'attention', label: 'Attention', icon: IconEye },
                        { id: 'counterfactuals', label: 'Counterfactuals', icon: IconFlask },
                      ].map(tab => {
                        const Icon = tab.icon
                        return (
                          <TabsTrigger
                            key={tab.id}
                            value={tab.id}
                            className="flex items-center gap-1.5 px-3 py-2 rounded-full text-[13px] font-medium text-[var(--fm-ink2)] data-[state=active]:bg-[var(--fm-ink)] data-[state=active]:text-white"
                          >
                            <Icon className="h-3.5 w-3.5" />
                            {tab.label}
                          </TabsTrigger>
                        )
                      })}
                    </TabsList>
                  </div>

                  {/* Overview Tab */}
                  <TabsContent value="overview" className="p-6 space-y-5 mt-0">
                    {/* Methods used */}
                    <div className="space-y-2">
                      <h3 className="font-semibold text-sm tracking-wider">Methods Applied</h3>
                      <div className="flex flex-wrap gap-2">
                        {(results.methods_used ?? selectedMethods).map(m => {
                          const method = EXPLAINABILITY_METHODS.find(e => e.id === m)
                          return (
                            <Badge
                              key={m}
                              className={`border-2 font-bold text-xs ${method?.color ?? 'bg-gray-100 text-gray-700 border-gray-300'}`}
                            >
                              {method?.label ?? m}
                            </Badge>
                          )
                        })}
                      </div>
                    </div>

                    {/* Insights */}
                    {results.insights && results.insights.length > 0 && (
                      <div className="space-y-2">
                        <h3 className="font-semibold text-sm tracking-wider flex items-center gap-2">
                          <IconBulb className="h-4 w-4 text-yellow-600" />
                          Key Insights
                        </h3>
                        <ul className="space-y-2">
                          {results.insights.map((insight, i) => (
                            <li
                              key={i}
                              className="flex gap-3 p-3 border border-[var(--fm-line)] bg-yellow-50"
                            >
                              <span className="flex-shrink-0 font-semibold text-yellow-700 text-sm">
                                {String(i + 1).padStart(2, '0')}
                              </span>
                              <span className="text-sm">{insight}</span>
                            </li>
                          ))}
                        </ul>
                      </div>
                    )}

                    {/* Confidence progress */}
                    <div className="space-y-2">
                      <div className="flex justify-between items-center">
                        <h3 className="font-semibold text-sm tracking-wider">Analysis Confidence</h3>
                        <span className={`font-semibold text-sm ${getConfidenceColor(results.confidence ?? 0)}`}>
                          {((results.confidence ?? 0) * 100).toFixed(1)}%
                        </span>
                      </div>
                      <Progress
                        value={(results.confidence ?? 0) * 100}
                        className="h-3 border border-[var(--fm-line)]"
                      />
                      <p className="text-xs text-muted-foreground">
                        {(results.confidence ?? 0) >= 0.8
                          ? 'High confidence — results are reliable for audit documentation.'
                          : (results.confidence ?? 0) >= 0.6
                          ? 'Moderate confidence — consider adding more output samples.'
                          : 'Low confidence — more samples or methods needed for reliable results.'}
                      </p>
                    </div>

                    {/* Visualizations note */}
                    {results.visualizations && results.visualizations.length > 0 && (
                      <div className="border border-[var(--fm-line)] p-3 bg-blue-50 flex gap-3">
                        <IconInfoCircle className="h-5 w-5 text-blue-600 flex-shrink-0 mt-0.5" />
                        <div>
                          <p className="text-sm font-bold text-blue-900">
                            {results.visualizations.length} Visualization{results.visualizations.length !== 1 ? 's' : ''} Generated
                          </p>
                          <p className="text-xs text-blue-700 mt-0.5">
                            {results.visualizations.join(', ')}
                          </p>
                        </div>
                      </div>
                    )}
                  </TabsContent>

                  {/* Attribution Tab */}
                  <TabsContent value="attribution" className="p-6 space-y-5 mt-0">
                    <h3 className="font-semibold text-sm tracking-wider flex items-center gap-2">
                      <IconChartBar className="h-4 w-4 text-teal-600" />
                      Feature Attribution
                    </h3>

                    {results.feature_attributions && Object.keys(results.feature_attributions).length > 0 ? (
                      <div className="space-y-2">
                        {(() => {
                          const attrs = results.feature_attributions!
                          const values = Object.values(attrs)
                          const maxVal = Math.max(...values.map(Math.abs))
                          return Object.entries(attrs)
                            .sort(([, a], [, b]) => Math.abs(b) - Math.abs(a))
                            .map(([feature, value]) => (
                              <div key={feature} className="space-y-1">
                                <div className="flex justify-between items-center text-sm">
                                  <span className="font-bold font-mono">{feature}</span>
                                  <span className={`font-semibold text-xs ${value >= 0 ? 'text-teal-700' : 'text-red-700'}`}>
                                    {value >= 0 ? '+' : ''}{value.toFixed(4)}
                                  </span>
                                </div>
                                <div className="h-5 bg-gray-100 border border-[var(--fm-line)] relative overflow-hidden">
                                  <div
                                    className={`h-full ${getAttributionColor(value)} transition-all`}
                                    style={{ width: `${getAttributionWidth(value, maxVal)}%` }}
                                  />
                                </div>
                              </div>
                            ))
                        })()}
                      </div>
                    ) : results.bias_attribution && Object.keys(results.bias_attribution).length > 0 ? (
                      <div className="space-y-2">
                        <p className="text-xs text-muted-foreground font-semibold uppercase tracking-wider mb-3">
                          Bias-Specific Attribution
                        </p>
                        {(() => {
                          const attrs = results.bias_attribution!
                          const maxVal = Math.max(...Object.values(attrs).map(Math.abs))
                          return Object.entries(attrs)
                            .sort(([, a], [, b]) => Math.abs(b) - Math.abs(a))
                            .map(([attr, value]) => (
                              <div key={attr} className="space-y-1">
                                <div className="flex justify-between items-center text-sm">
                                  <span className="font-bold capitalize">{attr.replace(/_/g, ' ')}</span>
                                  <span className={`font-semibold text-xs ${value >= 0.5 ? 'text-red-700' : 'text-yellow-700'}`}>
                                    {(value * 100).toFixed(1)}% contribution
                                  </span>
                                </div>
                                <div className="h-5 bg-gray-100 border border-[var(--fm-line)] relative overflow-hidden">
                                  <div
                                    className={`h-full ${value >= 0.5 ? 'bg-red-500' : 'bg-yellow-500'} transition-all`}
                                    style={{ width: `${getAttributionWidth(value, maxVal)}%` }}
                                  />
                                </div>
                              </div>
                            ))
                        })()}
                      </div>
                    ) : (
                      <div className="border border-dashed border-[rgba(21,23,26,.14)] p-8 text-center">
                        <IconChartBar className="h-10 w-10 text-muted-foreground/40 mx-auto mb-3" />
                        <p className="text-sm text-muted-foreground font-bold">
                          No feature attribution data returned
                        </p>
                        <p className="text-xs text-muted-foreground mt-1">
                          Try selecting SHAP or Integrated Gradients methods
                        </p>
                      </div>
                    )}
                  </TabsContent>

                  {/* Attention Tab */}
                  <TabsContent value="attention" className="p-6 space-y-5 mt-0">
                    <h3 className="font-semibold text-sm tracking-wider flex items-center gap-2">
                      <IconEye className="h-4 w-4 text-blue-600" />
                      Attention Patterns
                    </h3>

                    {results.attention_patterns && Object.keys(results.attention_patterns).length > 0 ? (
                      <div className="space-y-3">
                        <p className="text-xs text-muted-foreground">
                          Token attention weights from the model's final attention layer. Higher values
                          indicate tokens the model focused on most during generation.
                        </p>
                        <div className="flex flex-wrap gap-2">
                          {(() => {
                            const patterns = results.attention_patterns!
                            const maxVal = Math.max(...Object.values(patterns))
                            return Object.entries(patterns)
                              .sort(([, a], [, b]) => b - a)
                              .map(([token, weight]) => {
                                const intensity = maxVal > 0 ? weight / maxVal : 0
                                const opacity = Math.max(0.1, intensity)
                                return (
                                  <span
                                    key={token}
                                    className="px-2 py-1 border border-[var(--fm-line)] text-sm font-mono font-bold"
                                    style={{
                                      backgroundColor: `rgba(59, 130, 246, ${opacity})`,
                                      color: intensity > 0.6 ? 'white' : 'black',
                                    }}
                                    title={`Attention weight: ${weight.toFixed(4)}`}
                                  >
                                    {token}
                                  </span>
                                )
                              })
                          })()}
                        </div>
                        <p className="text-xs text-muted-foreground">
                          Darker blue = higher attention weight
                        </p>
                      </div>
                    ) : (
                      <div className="border border-dashed border-[rgba(21,23,26,.14)] p-8 text-center">
                        <IconEye className="h-10 w-10 text-muted-foreground/40 mx-auto mb-3" />
                        <p className="text-sm text-muted-foreground font-bold">
                          No attention pattern data returned
                        </p>
                        <p className="text-xs text-muted-foreground mt-1">
                          Enable the Attention Analysis method to view attention patterns
                        </p>
                      </div>
                    )}
                  </TabsContent>

                  {/* Counterfactuals Tab */}
                  <TabsContent value="counterfactuals" className="p-6 space-y-5 mt-0">
                    <div className="flex items-start justify-between">
                      <div>
                        <h3 className="font-semibold text-sm tracking-wider flex items-center gap-2">
                          <IconFlask className="h-4 w-4 text-pink-600" />
                          Counterfactual Examples
                        </h3>
                        <p className="text-xs text-muted-foreground mt-1">
                          "What if this attribute changed?" — minimal edits that flip model behavior.
                        </p>
                      </div>
                    </div>

                    {results.counterfactuals && results.counterfactuals.length > 0 ? (
                      <div className="space-y-4">
                        {results.counterfactuals.map((cf, i) => (
                          <div key={i} className="border border-[var(--fm-line)] p-4 space-y-3">
                            <div className="flex items-center justify-between">
                              <Badge className="border border-[var(--fm-line)] font-bold bg-pink-100 text-pink-800 border-pink-300">
                                {cf.attribute}
                              </Badge>
                              <span className={`text-sm font-semibold ${cf.impact >= 0.5 ? 'text-red-700' : 'text-yellow-700'}`}>
                                Δ {(cf.impact * 100).toFixed(0)}% impact
                              </span>
                            </div>
                            <div className="grid grid-cols-2 gap-3">
                              <div className="border border-[var(--fm-line)] p-3 bg-gray-50">
                                <p className="text-xs font-semibold uppercase tracking-wider text-muted-foreground mb-1">
                                  Original
                                </p>
                                <p className="text-sm">{cf.original}</p>
                              </div>
                              <div className="border border-[var(--fm-line)] p-3 bg-pink-50">
                                <p className="text-xs font-semibold uppercase tracking-wider text-pink-700 mb-1">
                                  Counterfactual
                                </p>
                                <p className="text-sm">{cf.modified}</p>
                              </div>
                            </div>
                          </div>
                        ))}
                      </div>
                    ) : (
                      <div className="border border-dashed border-[rgba(21,23,26,.14)] p-8 text-center">
                        <IconFlask className="h-10 w-10 text-muted-foreground/40 mx-auto mb-3" />
                        <p className="text-sm text-muted-foreground font-bold">
                          No counterfactual examples returned
                        </p>
                        <p className="text-xs text-muted-foreground mt-1">
                          The backend may not have generated counterfactuals for this output
                        </p>
                      </div>
                    )}
                  </TabsContent>
                </Tabs>
              </Card>

              {/* Next step CTA */}
              <div className="p-4 bg-[var(--fm-ink)] text-white flex items-center justify-between rounded-[14px] shadow-[var(--fm-shadow)]">
                <div>
                  <p className="font-semibold">Ready to run a full bias evaluation?</p>
                  <p className="text-white/70 text-xs mt-0.5">
                    Use the LLM Bias Detection suite for StereoSet, WEAT, BBQ, and more.
                  </p>
                </div>
                <a href="/llm-testing">
                  <Button
                    variant="noShadow"
                    className="border border-white/40 bg-transparent text-white hover:bg-white hover:text-black font-bold"
                  >
                    Run Bias Evaluation
                    <IconArrowRight className="h-4 w-4 ml-2" />
                  </Button>
                </a>
              </div>
            </div>
          ) : null}
        </div>
      </div>
    </div>
  )
}
