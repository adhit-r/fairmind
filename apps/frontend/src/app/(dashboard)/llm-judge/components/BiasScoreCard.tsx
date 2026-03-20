'use client'

import { Card } from '@/components/ui/card'
import { Badge } from '@/components/ui/badge'
import { Progress } from '@/components/ui/progress'
import { IconAlertTriangle, IconAlertCircle, IconCircleCheck, IconInfoCircle } from '@tabler/icons-react'
import { BiasEvaluationResult } from '@/lib/api/hooks/useLLMJudge'

export interface BiasScoreCardProps {
  result: BiasEvaluationResult
}

/**
 * Component to display a bias evaluation score and severity
 */
export function BiasScoreCard({ result }: BiasScoreCardProps) {
  // ========================================================================
  // Helper Functions
  // ========================================================================

  const getSeverityColor = (
    severity: string
  ): {
    bg: string
    text: string
    border: string
    icon: React.ReactNode
  } => {
    switch (severity) {
      case 'critical':
        return {
          bg: 'bg-red-100',
          text: 'text-red-900',
          border: 'border-red-400',
          icon: <IconAlertTriangle className="w-5 h-5 text-red-600" />,
        }
      case 'high':
        return {
          bg: 'bg-orange-100',
          text: 'text-orange-900',
          border: 'border-orange-400',
          icon: <IconAlertCircle className="w-5 h-5 text-orange-600" />,
        }
      case 'medium':
        return {
          bg: 'bg-yellow-100',
          text: 'text-yellow-900',
          border: 'border-yellow-400',
          icon: <IconInfoCircle className="w-5 h-5 text-yellow-600" />,
        }
      case 'low':
      default:
        return {
          bg: 'bg-green-100',
          text: 'text-green-900',
          border: 'border-green-400',
          icon: <IconCircleCheck className="w-5 h-5 text-green-600" />,
        }
    }
  }

  const getScoreColor = (score: number): string => {
    if (score >= 0.8) return 'bg-red-500'
    if (score >= 0.6) return 'bg-orange-500'
    if (score >= 0.4) return 'bg-yellow-500'
    return 'bg-green-500'
  }

  const getScoreInterpretation = (score: number): string => {
    if (score >= 0.8) return 'High Bias Detected'
    if (score >= 0.6) return 'Moderate Bias Detected'
    if (score >= 0.4) return 'Some Bias Detected'
    return 'Low/No Bias'
  }

  const severity = result.severity.toLowerCase()
  const severityStyle = getSeverityColor(severity)
  const scoreValue = Math.round(result.bias_score * 100)
  const confidenceValue = Math.round(result.confidence * 100)

  // ========================================================================
  // Render
  // ========================================================================

  return (
    <Card
      className={`border-2 ${severityStyle.border} shadow-brutal p-6 space-y-6 ${severityStyle.bg}`}
    >
      {/* Header */}
      <div className="flex items-start justify-between">
        <div className="space-y-2">
          <div className="flex items-center gap-2">
            {severityStyle.icon}
            <h3 className="text-xl font-bold capitalize">{severity} Severity</h3>
          </div>
          <p className={`text-sm font-medium ${severityStyle.text}`}>
            {result.bias_category.charAt(0).toUpperCase() + result.bias_category.slice(1)} Bias
          </p>
        </div>
        <Badge variant="outline" className={`border-2 font-bold text-lg px-3 py-1 capitalize`}>
          {getScoreInterpretation(result.bias_score)}
        </Badge>
      </div>

      {/* Bias Score */}
      <div className="space-y-3 bg-white/50 p-4 rounded border border-black/20">
        <div className="flex justify-between items-center">
          <span className="font-semibold">Bias Score</span>
          <span className="text-2xl font-bold font-mono">{scoreValue}%</span>
        </div>
        <Progress
          value={scoreValue}
          className={`h-3 border border-black ${getScoreColor(result.bias_score)}`}
        />
        <p className="text-xs text-gray-700">
          0% = No Bias | 50% = Moderate Bias | 100% = Extreme Bias
        </p>
      </div>

      {/* Confidence Level */}
      <div className="space-y-3 bg-white/50 p-4 rounded border border-black/20">
        <div className="flex justify-between items-center">
          <span className="font-semibold">Judge Confidence</span>
          <span className="text-lg font-bold font-mono">{confidenceValue}%</span>
        </div>
        <Progress value={confidenceValue} className="h-2 border border-gray-400 bg-gray-100" />
        <p className="text-xs text-gray-700">
          How confident the judge model is in this evaluation
        </p>
      </div>

      {/* Judge Info */}
      <div className="grid grid-cols-2 gap-3 bg-white/50 p-4 rounded border border-black/20">
        <div>
          <p className="text-xs text-gray-600 uppercase font-bold">Judge Model</p>
          <p className="font-mono font-semibold">{result.judge_model}</p>
        </div>
        <div>
          <p className="text-xs text-gray-600 uppercase font-bold">Evaluation ID</p>
          <p className="font-mono text-xs truncate">{result.evaluation_id.substring(0, 8)}...</p>
        </div>
      </div>

      {/* Key Insights */}
      {result.detected_biases.length > 0 && (
        <div className="space-y-2 bg-white/50 p-4 rounded border border-black/20">
          <p className="text-sm font-semibold">Key Biases Detected</p>
          <div className="flex flex-wrap gap-2">
            {result.detected_biases.slice(0, 5).map((bias, i) => (
              <Badge key={i} variant="secondary" className="bg-black text-white">
                {bias}
              </Badge>
            ))}
            {result.detected_biases.length > 5 && (
              <Badge variant="secondary" className="bg-gray-400 text-white">
                +{result.detected_biases.length - 5} more
              </Badge>
            )}
          </div>
        </div>
      )}

      {/* Quick Stats */}
      <div className="grid grid-cols-3 gap-2 text-center bg-white/50 p-3 rounded border border-black/20">
        <div>
          <p className="text-xs font-bold uppercase text-gray-600">Detected Biases</p>
          <p className="text-2xl font-bold">{result.detected_biases.length}</p>
        </div>
        <div>
          <p className="text-xs font-bold uppercase text-gray-600">Recommendations</p>
          <p className="text-2xl font-bold">{result.recommendations.length}</p>
        </div>
        <div>
          <p className="text-xs font-bold uppercase text-gray-600">Evidence</p>
          <p className="text-2xl font-bold">{result.evidence.length}</p>
        </div>
      </div>
    </Card>
  )
}
