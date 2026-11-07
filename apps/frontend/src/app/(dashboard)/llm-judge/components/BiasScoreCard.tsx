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
        return {
          bg: 'bg-green-100',
          text: 'text-green-900',
          border: 'border-green-400',
          icon: <IconCircleCheck className="w-5 h-5 text-green-600" />,
        }
      default:
        // An unrated severity is not a pass: keep it neutral, never green.
        return {
          bg: 'bg-[var(--fm-bg)]',
          text: 'text-[var(--fm-ink2)]',
          border: 'border-[var(--fm-line)]',
          icon: <IconInfoCircle className="w-5 h-5 text-[var(--fm-ink2)]" />,
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

  const categoryLabel = result.bias_category.charAt(0).toUpperCase() + result.bias_category.slice(1)

  // The judge produced no usable score: say so, never show a number.
  if (result.status === 'insufficient' || result.bias_score == null) {
    return (
      <Card className="fm-card p-6 space-y-4">
        <div className="flex items-start justify-between gap-3">
          <div className="space-y-1">
            <h3 className="text-xl font-semibold tracking-tight text-[var(--fm-ink)]">Not scored</h3>
            <p className="text-sm text-[var(--fm-ink2)]">{categoryLabel} Bias</p>
          </div>
          <span className="rounded-full bg-[#fff4d6] px-3 py-1 text-xs font-semibold text-[#8a5a00]">
            Insufficient result
          </span>
        </div>
        <p className="text-sm leading-relaxed text-[var(--fm-ink2)] border-t border-[var(--fm-line)] pt-4">
          {result.reasoning}
        </p>
        <p className="text-xs text-[var(--fm-ink2)]">
          Judge model: <span className="font-mono text-[var(--fm-ink)]">{result.judge_model}</span>
        </p>
      </Card>
    )
  }

  const severity = result.severity.toLowerCase()
  const severityStyle = getSeverityColor(severity)
  const scoreValue = Math.round(result.bias_score * 100)
  const confidenceValue = result.confidence == null ? null : Math.round(result.confidence * 100)

  // ========================================================================
  // Render
  // ========================================================================

  return (
    <Card
      className={`border ${severityStyle.border} p-6 space-y-6 ${severityStyle.bg}`}
    >
      {/* Header */}
      <div className="flex items-start justify-between">
        <div className="space-y-2">
          <div className="flex items-center gap-2">
            {severityStyle.icon}
            <h3 className="text-xl font-bold capitalize">{severity} Severity</h3>
          </div>
          <p className={`text-sm font-medium ${severityStyle.text}`}>
            {categoryLabel} Bias
          </p>
        </div>
        <Badge variant="outline" className={`border font-bold text-lg px-3 py-1 capitalize`}>
          {getScoreInterpretation(result.bias_score)}
        </Badge>
      </div>

      {/* Bias Score */}
      <div className="space-y-3 bg-white/50 p-4 rounded border border-[var(--fm-line)]">
        <div className="flex justify-between items-center">
          <span className="font-semibold">Bias Score</span>
          <span className="text-2xl font-bold font-mono">{scoreValue}%</span>
        </div>
        <Progress
          value={scoreValue}
          className={`h-3 border border-[var(--fm-line)] ${getScoreColor(result.bias_score)}`}
        />
        <p className="text-xs text-gray-700">
          0% = No Bias | 50% = Moderate Bias | 100% = Extreme Bias
        </p>
      </div>

      {/* Confidence Level */}
      {confidenceValue != null && (
      <div className="space-y-3 bg-white/50 p-4 rounded border border-[var(--fm-line)]">
        <div className="flex justify-between items-center">
          <span className="font-semibold">Judge Confidence</span>
          <span className="text-lg font-bold font-mono">{confidenceValue}%</span>
        </div>
        <Progress value={confidenceValue} className="h-2 border border-gray-400 bg-gray-100" />
        <p className="text-xs text-gray-700">
          How confident the judge model is in this evaluation
        </p>
      </div>
      )}

      {/* Judge Info */}
      <div className="grid grid-cols-2 gap-3 bg-white/50 p-4 rounded border border-[var(--fm-line)]">
        <div>
          <p className="text-xs text-gray-600 uppercase font-semibold">Judge Model</p>
          <p className="font-mono font-semibold">{result.judge_model}</p>
        </div>
        <div>
          <p className="text-xs text-gray-600 uppercase font-semibold">Evaluation ID</p>
          <p className="font-mono text-xs truncate">{result.evaluation_id.substring(0, 8)}...</p>
        </div>
      </div>

      {/* Key Insights */}
      {result.detected_biases.length > 0 && (
        <div className="space-y-2 bg-white/50 p-4 rounded border border-[var(--fm-line)]">
          <p className="text-sm font-semibold">Key Biases Detected</p>
          <div className="flex flex-wrap gap-2">
            {result.detected_biases.slice(0, 5).map((bias, i) => (
              <Badge key={i} variant="secondary" className="bg-[var(--fm-ink)] text-white">
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
      <div className="grid grid-cols-3 gap-2 text-center bg-white/50 p-3 rounded border border-[var(--fm-line)]">
        <div>
          <p className="text-xs font-semibold uppercase text-gray-600">Detected Biases</p>
          <p className="text-2xl font-bold">{result.detected_biases.length}</p>
        </div>
        <div>
          <p className="text-xs font-semibold uppercase text-gray-600">Recommendations</p>
          <p className="text-2xl font-bold">{result.recommendations.length}</p>
        </div>
        <div>
          <p className="text-xs font-semibold uppercase text-gray-600">Evidence</p>
          <p className="text-2xl font-bold">{result.evidence.length}</p>
        </div>
      </div>
    </Card>
  )
}
