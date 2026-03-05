'use client'

import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/ui/tabs'
import { Alert, AlertDescription } from '@/components/ui/alert'
import { Button } from '@/components/ui/button'
import { IconInfoCircle, IconRefresh, IconArrowRight } from '@tabler/icons-react'
import { useAvailableModels, useBatchEvaluate } from '@/lib/api/hooks/useLLMJudge'
import { InputForm } from './components/InputForm'
import { BiasScoreCard } from './components/BiasScoreCard'
import { EvidencePanel } from './components/EvidencePanel'
import { RecommendationsPanel } from './components/RecommendationsPanel'

/**
 * LLM-as-Judge Page
 *
 * Allows users to:
 * 1. Input text or upload files
 * 2. Select judge model(s)
 * 3. Choose bias categories to evaluate
 * 4. Review detailed results with evidence and recommendations
 */
export default function LLMJudgePage() {
  // ========================================================================
  // Hooks
  // ========================================================================

  const { models, categories, loading: modelsLoading, error: modelsError } = useAvailableModels()
  const { evaluateBatch, result, loading, error, clearResult } = useBatchEvaluate()

  // ========================================================================
  // Handlers
  // ========================================================================

  const handleEvaluate = async (
    text: string,
    judgeModel: string,
    biasCategories: string[],
    targetModel: string
  ) => {
    await evaluateBatch(text, judgeModel, biasCategories, targetModel)
  }

  const handleNewEvaluation = () => {
    clearResult()
  }

  // ========================================================================
  // Render
  // ========================================================================

  const hasResults = result && Object.keys(result.results).length > 0

  return (
    <div className="space-y-8">
      {/* Page Header */}
      <div>
        <h1 className="text-4xl font-bold mb-3">LLM-as-a-Judge</h1>
        <p className="text-gray-600 text-lg">
          Use advanced LLMs to evaluate your content for subtle bias and fairness issues across multiple
          dimensions
        </p>
      </div>

      {/* Info Alert */}
      <Alert className="border-2 border-blue-500 bg-blue-50">
        <IconInfoCircle className="h-5 w-5 text-blue-600" />
        <AlertDescription className="text-blue-900">
          <strong>New Feature:</strong> LLM-as-Judge evaluation is now available. Your text is evaluated by
          state-of-the-art judge models for comprehensive bias detection.
        </AlertDescription>
      </Alert>

      {/* Main Content */}
      {!hasResults ? (
        // Input Phase
        <div className="space-y-6">
          {modelsError && (
            <Alert className="border-2 border-red-500 bg-red-50">
              <AlertDescription className="text-red-900">
                Failed to load available models. Please refresh the page.
              </AlertDescription>
            </Alert>
          )}

          <InputForm
            loading={loading || modelsLoading}
            error={error}
            onEvaluate={handleEvaluate}
            availableModels={models}
            availableCategories={categories}
          />

          {/* How It Works */}
          <div className="grid md:grid-cols-3 gap-4">
            <div className="border-2 border-black p-4 rounded space-y-2">
              <div className="text-2xl font-bold">1</div>
              <p className="font-semibold">Input Text</p>
              <p className="text-sm text-gray-600">
                Paste or upload the content you want to evaluate for bias
              </p>
            </div>
            <div className="border-2 border-black p-4 rounded space-y-2">
              <div className="text-2xl font-bold">2</div>
              <p className="font-semibold">Configure Judge</p>
              <p className="text-sm text-gray-600">
                Select your judge model and bias categories to evaluate
              </p>
            </div>
            <div className="border-2 border-black p-4 rounded space-y-2">
              <div className="text-2xl font-bold">3</div>
              <p className="font-semibold">Review Results</p>
              <p className="text-sm text-gray-600">
                Get detailed analysis with evidence and actionable recommendations
              </p>
            </div>
          </div>

          {/* FAQ */}
          <div className="bg-gray-50 border-2 border-gray-300 p-6 rounded space-y-4">
            <h3 className="font-bold text-lg">Frequently Asked Questions</h3>

            <div className="space-y-3">
              <details className="group cursor-pointer">
                <summary className="font-semibold text-sm hover:text-blue-600">
                  What is LLM-as-Judge evaluation?
                </summary>
                <p className="text-sm text-gray-700 mt-2 ml-4">
                  It uses advanced AI models (like GPT-4 or Claude) as &#34;judges&#34; to evaluate your text for
                  various types of bias. The judge model applies reasoning and provides detailed analysis.
                </p>
              </details>

              <details className="group cursor-pointer">
                <summary className="font-semibold text-sm hover:text-blue-600">
                  Which bias categories can I evaluate?
                </summary>
                <p className="text-sm text-gray-700 mt-2 ml-4">
                  You can evaluate for: Gender, Race, Age, Cultural, Socioeconomic, Intersectional, Professional,
                  and Religious bias.
                </p>
              </details>

              <details className="group cursor-pointer">
                <summary className="font-semibold text-sm hover:text-blue-600">
                  Is my text private?
                </summary>
                <p className="text-sm text-gray-700 mt-2 ml-4">
                  Your text is sent to the selected judge model provider for evaluation. Please review their
                  privacy policies. FairMind does not store your submitted text.
                </p>
              </details>

              <details className="group cursor-pointer">
                <summary className="font-semibold text-sm hover:text-blue-600">
                  How accurate is the evaluation?
                </summary>
                <p className="text-sm text-gray-700 mt-2 ml-4">
                  LLM-as-Judge is a powerful method but not perfect. Always review the reasoning and evidence
                  provided. For critical applications, combine with other evaluation methods.
                </p>
              </details>
            </div>
          </div>
        </div>
      ) : (
        // Results Phase
        <div className="space-y-6">
          {/* Results Header */}
          <div className="flex justify-between items-start">
            <div>
              <h2 className="text-2xl font-bold mb-2">Evaluation Results</h2>
              <p className="text-gray-600">
                Comprehensive bias analysis across {Object.keys(result.results).length} categor
                {Object.keys(result.results).length === 1 ? 'y' : 'ies'}
              </p>
            </div>
            <Button
              onClick={handleNewEvaluation}
              className="border-2 border-black font-bold"
              variant="neutral"
            >
              <IconRefresh className="w-4 h-4 mr-2" />
              New Evaluation
            </Button>
          </div>

          {/* Results Tabs */}
          <Tabs defaultValue={Object.keys(result.results)[0]} className="space-y-6">
            <TabsList className="border-2 border-black w-full overflow-x-auto">
              {Object.keys(result.results).map((category) => (
                <TabsTrigger
                  key={category}
                  value={category}
                  className="border-r-2 border-black last:border-r-0 capitalize"
                >
                  {category}
                </TabsTrigger>
              ))}
            </TabsList>

            {/* Render Results for Each Category */}
            {Object.entries(result.results).map(([category, categoryResult]) => (
              <TabsContent key={category} value={category} className="space-y-6 mt-6">
                {/* Bias Score Card */}
                <BiasScoreCard result={categoryResult} />

                {/* Evidence Panel */}
                <EvidencePanel result={categoryResult} />

                {/* Recommendations Panel */}
                <RecommendationsPanel result={categoryResult} />

                {/* Full Reasoning */}
                <div className="border-2 border-black shadow-brutal p-6 rounded space-y-3">
                  <h3 className="font-bold text-lg">Judge's Full Reasoning</h3>
                  <p className="text-sm leading-relaxed bg-gray-50 p-4 rounded border border-gray-300">
                    {categoryResult.reasoning}
                  </p>
                  <div className="text-xs text-gray-600 pt-3 border-t">
                    <p>
                      <strong>Evaluated by:</strong> {categoryResult.judge_model}
                    </p>
                    <p>
                      <strong>Timestamp:</strong> {new Date(categoryResult.timestamp).toLocaleString()}
                    </p>
                  </div>
                </div>
              </TabsContent>
            ))}
          </Tabs>

          {/* Summary Statistics */}
          <div className="grid md:grid-cols-4 gap-4">
            <div className="border-2 border-black p-4 rounded text-center">
              <div className="text-3xl font-bold">
                {Math.round(
                  (Object.values(result.results).reduce((sum, r) => sum + r.bias_score, 0) /
                    Object.keys(result.results).length) *
                    100
                )}
                %
              </div>
              <p className="text-xs text-gray-600 uppercase font-bold mt-2">Avg Bias Score</p>
            </div>

            <div className="border-2 border-black p-4 rounded text-center">
              <div className="text-3xl font-bold">
                {Object.values(result.results).reduce((sum, r) => sum + r.detected_biases.length, 0)}
              </div>
              <p className="text-xs text-gray-600 uppercase font-bold mt-2">Total Biases Found</p>
            </div>

            <div className="border-2 border-black p-4 rounded text-center">
              <div className="text-3xl font-bold">
                {Object.values(result.results).reduce((sum, r) => sum + r.recommendations.length, 0)}
              </div>
              <p className="text-xs text-gray-600 uppercase font-bold mt-2">Recommendations</p>
            </div>

            <div className="border-2 border-black p-4 rounded text-center">
              <div className="text-3xl font-bold">
                {Math.round(
                  (Object.values(result.results).reduce((sum, r) => sum + r.confidence, 0) /
                    Object.keys(result.results).length) *
                    100
                )}
                %
              </div>
              <p className="text-xs text-gray-600 uppercase font-bold mt-2">Avg Confidence</p>
            </div>
          </div>

          {/* Next Steps */}
          <div className="bg-gradient-to-r from-green-50 to-blue-50 border-2 border-green-400 p-6 rounded space-y-4">
            <h3 className="font-bold text-lg">
              <IconArrowRight className="w-5 h-5 inline mr-2" />
              Next Steps
            </h3>
            <ol className="text-sm space-y-2 list-decimal list-inside">
              <li>Review the detected biases in each category above</li>
              <li>Read the judge&#39;s reasoning for each evaluation</li>
              <li>Implement the recommendations to improve your content</li>
              <li>Run a new evaluation to verify improvements</li>
            </ol>
          </div>
        </div>
      )}
    </div>
  )
}
