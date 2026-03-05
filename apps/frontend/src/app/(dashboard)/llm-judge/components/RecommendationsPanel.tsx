'use client'

import { useState } from 'react'
import { Card } from '@/components/ui/card'
import { Button } from '@/components/ui/button'
import { Badge } from '@/components/ui/badge'
import { IconChevronDown, IconChevronUp, IconDownload, IconBulb } from '@tabler/icons-react'
import { BiasEvaluationResult } from '@/lib/api/hooks/useLLMJudge'

export interface RecommendationsPanelProps {
  result: BiasEvaluationResult
}

/**
 * Component to display recommendations for fixing detected biases
 */
export function RecommendationsPanel({ result }: RecommendationsPanelProps) {
  const [expandedIndex, setExpandedIndex] = useState<number | null>(0)

  // ========================================================================
  // Helpers
  // ========================================================================

  const getSeverityBadgeColor = (
    bias: string
  ): { bg: string; text: string } => {
    const detected = result.detected_biases.includes(bias)
    if (detected) {
      return { bg: 'bg-red-100', text: 'text-red-800' }
    }
    return { bg: 'bg-green-100', text: 'text-green-800' }
  }

  const downloadRecommendations = () => {
    const content = `Bias Evaluation Recommendations
================================

Category: ${result.bias_category.toUpperCase()}
Judge Model: ${result.judge_model}
Bias Score: ${Math.round(result.bias_score * 100)}%
Severity: ${result.severity.toUpperCase()}

${result.recommendations.length > 0 ? 'RECOMMENDATIONS' : 'No recommendations'}
${result.recommendations.length > 0 ? '===============' : ''}
${result.recommendations
  .map((rec, i) => `${i + 1}. ${rec}`)
  .join('\n')}

${result.detected_biases.length > 0 ? '\nDETECTED BIASES' : ''}
${result.detected_biases.length > 0 ? '===============' : ''}
${result.detected_biases
  .map((bias, i) => `${i + 1}. ${bias}`)
  .join('\n')}

REASONING
=========
${result.reasoning}

---
Generated: ${result.timestamp}
Evaluation ID: ${result.evaluation_id}
`

    const element = document.createElement('a')
    element.setAttribute(
      'href',
      'data:text/plain;charset=utf-8,' + encodeURIComponent(content)
    )
    element.setAttribute('download', `bias-recommendations-${Date.now()}.txt`)
    element.style.display = 'none'
    document.body.appendChild(element)
    element.click()
    document.body.removeChild(element)
  }

  // ========================================================================
  // Render
  // ========================================================================

  if (result.recommendations.length === 0) {
    return (
      <Card className="border-2 border-black shadow-brutal p-6">
        <div className="text-center py-8 space-y-3">
          <IconBulb className="w-12 h-12 mx-auto text-yellow-600" />
          <div>
            <p className="text-lg font-semibold mb-2">No Recommendations Needed</p>
            <p className="text-sm text-gray-600">
              Your text performed well on the {result.bias_category} bias evaluation!
            </p>
          </div>
        </div>
      </Card>
    )
  }

  return (
    <Card className="border-2 border-black shadow-brutal">
      <div className="p-6 border-b-2 border-black space-y-4">
        <div>
          <h3 className="text-xl font-bold">Improvement Recommendations</h3>
          <p className="text-sm text-gray-600 mt-1">
            Actionable suggestions to reduce bias and improve fairness
          </p>
        </div>

        <Button
          onClick={downloadRecommendations}
          variant="neutral"
          size="sm"
          className="border-2 border-black font-bold"
        >
          <IconDownload className="w-4 h-4 mr-2" />
          Download Report
        </Button>
      </div>

      <div className="divide-y-2 divide-black">
        {result.recommendations.map((recommendation, index) => (
          <div key={index} className="p-6">
            {/* Recommendation Header */}
            <button
              onClick={() =>
                setExpandedIndex(expandedIndex === index ? null : index)
              }
              className="w-full text-left flex items-center justify-between hover:bg-gray-50 p-3 -m-3 rounded group"
            >
              <div className="flex-1 min-w-0">
                <div className="flex items-center gap-2 mb-2">
                  <Badge className="bg-blue-600 text-white flex-shrink-0">
                    #{index + 1}
                  </Badge>
                  <span className="font-semibold group-hover:underline truncate">
                    {recommendation.substring(0, 60)}
                    {recommendation.length > 60 ? '...' : ''}
                  </span>
                </div>
              </div>
              {expandedIndex === index ? (
                <IconChevronUp className="w-5 h-5 text-black flex-shrink-0 ml-2" />
              ) : (
                <IconChevronDown className="w-5 h-5 text-gray-400 flex-shrink-0 ml-2" />
              )}
            </button>

            {/* Expanded Content */}
            {expandedIndex === index && (
              <div className="mt-4 space-y-4 bg-blue-50 p-4 rounded border-2 border-blue-200">
                <div className="space-y-2">
                  <p className="text-sm font-bold uppercase text-gray-700">Full Recommendation</p>
                  <p className="text-sm leading-relaxed text-gray-800">
                    {recommendation}
                  </p>
                </div>

                {/* Implementation Tips */}
                <div className="bg-white p-3 rounded border border-blue-200">
                  <p className="text-xs font-bold uppercase text-gray-600 mb-2">
                    💭 How to implement this
                  </p>
                  <ul className="text-xs text-gray-700 space-y-1 list-disc list-inside">
                    <li>Review the evidence provided to understand the specific issue</li>
                    <li>Rewrite the text to be more inclusive and neutral</li>
                    <li>Re-evaluate after making changes</li>
                  </ul>
                </div>
              </div>
            )}
          </div>
        ))}
      </div>

      {/* Action Bar */}
      <div className="bg-purple-50 border-t-2 border-black p-4 space-y-3">
        <p className="text-xs font-bold uppercase text-purple-900">Next Steps</p>
        <ol className="text-xs text-purple-900 space-y-2 list-decimal list-inside">
          <li>Review each recommendation above</li>
          <li>Modify your text based on the suggestions</li>
          <li>Re-run the evaluation to see improvements</li>
          <li>Iterate until you reach your fairness goals</li>
        </ol>
      </div>
    </Card>
  )
}
