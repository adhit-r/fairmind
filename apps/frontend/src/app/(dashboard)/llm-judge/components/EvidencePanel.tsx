'use client'

import { useState } from 'react'
import { Card } from '@/components/ui/card'
import { Button } from '@/components/ui/button'
import { Badge } from '@/components/ui/badge'
import { IconChevronDown, IconChevronUp, IconCopy, IconCheck } from '@tabler/icons-react'
import { BiasEvaluationResult } from '@/lib/api/hooks/useLLMJudge'

export interface EvidencePanelProps {
  result: BiasEvaluationResult
}

/**
 * Component to display detected biases and evidence
 */
export function EvidencePanel({ result }: EvidencePanelProps) {
  const [expandedBias, setExpandedBias] = useState<number | null>(0)
  const [copiedIndex, setCopiedIndex] = useState<number | null>(null)

  // ========================================================================
  // Handlers
  // ========================================================================

  const copyToClipboard = async (text: string, index: number) => {
    try {
      await navigator.clipboard.writeText(text)
      setCopiedIndex(index)
      setTimeout(() => setCopiedIndex(null), 2000)
    } catch (err) {
      console.error('Failed to copy:', err)
    }
  }

  // ========================================================================
  // Render
  // ========================================================================

  if (result.detected_biases.length === 0) {
    return (
      <Card className="border-2 border-black shadow-brutal p-6">
        <div className="text-center py-8">
          <p className="text-lg font-semibold mb-2">No Biases Detected</p>
          <p className="text-sm text-gray-600">
            The text passed the evaluation for {result.bias_category} bias without significant issues.
          </p>
        </div>
      </Card>
    )
  }

  return (
    <Card className="border-2 border-black shadow-brutal">
      <div className="p-6 border-b-2 border-black">
        <h3 className="text-xl font-bold">Detected Biases & Evidence</h3>
        <p className="text-sm text-gray-600 mt-1">
          Specific instances of bias with supporting evidence from the judge model
        </p>
      </div>

      <div className="divide-y-2 divide-black">
        {result.detected_biases.map((bias, index) => (
          <div key={index} className="p-6 space-y-3">
            {/* Bias Header */}
            <button
              onClick={() =>
                setExpandedBias(expandedBias === index ? null : index)
              }
              className="w-full text-left flex items-center justify-between hover:bg-gray-50 p-3 -m-3 rounded"
            >
              <div className="flex-1">
                <Badge className="bg-red-600 text-white mb-2 capitalize">
                  {bias}
                </Badge>
                <p className="text-sm text-gray-600">
                  {result.evidence[index] ? 'Has supporting evidence' : 'No specific evidence'}
                </p>
              </div>
              {expandedBias === index ? (
                <IconChevronUp className="w-5 h-5 text-black flex-shrink-0" />
              ) : (
                <IconChevronDown className="w-5 h-5 text-gray-400 flex-shrink-0" />
              )}
            </button>

            {/* Expanded Content */}
            {expandedBias === index && result.evidence[index] && (
              <div className="mt-4 space-y-3 bg-gray-50 p-4 rounded border border-gray-300">
                <div className="space-y-2">
                  <p className="text-xs font-bold uppercase text-gray-600">Evidence from Text</p>
                  <p className="text-sm font-mono bg-white p-3 rounded border border-gray-200 italic text-gray-700">
                    &quot;{result.evidence[index]}&quot;
                  </p>
                </div>

                {/* Copy Button */}
                <Button
                  size="sm"
                  variant="neutral"
                  onClick={() => copyToClipboard(result.evidence[index], index)}
                  className="w-full border-2 border-gray-400"
                >
                  {copiedIndex === index ? (
                    <>
                      <IconCheck className="w-4 h-4 mr-2" />
                      Copied!
                    </>
                  ) : (
                    <>
                      <IconCopy className="w-4 h-4 mr-2" />
                      Copy Evidence
                    </>
                  )}
                </Button>
              </div>
            )}
          </div>
        ))}
      </div>

      {/* Summary */}
      <div className="bg-blue-50 border-t-2 border-black p-4">
        <p className="text-xs text-blue-900">
          <strong>💡 How to use:</strong> Click on each detected bias to see the supporting evidence from your
          text. Use this information to revise your content and remove these biases.
        </p>
      </div>
    </Card>
  )
}
