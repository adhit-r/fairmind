'use client'

import React, { useState } from 'react'
import {
  Card,
  CardContent,
  CardDescription,
  CardHeader,
  CardTitle,
} from '@/components/ui/card'
import { Badge } from '@/components/ui/badge'
import { Button } from '@/components/ui/button'
import {
  Collapsible,
  CollapsibleContent,
  CollapsibleTrigger,
} from '@/components/ui/collapsible'
import { AlertCircle, ChevronDown, ExternalLink } from 'lucide-react'

interface RemediationStep {
  step_number: number
  description: string
  effort_level: 'low' | 'medium' | 'high'
  estimated_days: number
}

interface ComplianceGap {
  control_id: string
  control_name: string
  category: string
  severity: 'critical' | 'high' | 'medium' | 'low'
  failed_checks: string[]
  remediation_steps: RemediationStep[]
  legal_citation: string
  evidence_id?: string
}

interface GapAnalysisPanelProps {
  gaps: ComplianceGap[]
  onViewEvidence?: (evidenceId: string) => void
}

const getSeverityColor = (severity: string) => {
  switch (severity) {
    case 'critical':
      return 'bg-red-100 text-red-800 border-red-300'
    case 'high':
      return 'bg-orange-100 text-orange-800 border-orange-300'
    case 'medium':
      return 'bg-yellow-100 text-yellow-800 border-yellow-300'
    case 'low':
      return 'bg-blue-100 text-blue-800 border-blue-300'
    default:
      return 'bg-gray-100 text-gray-800 border-gray-300'
  }
}

const getSeverityIcon = (severity: string) => {
  switch (severity) {
    case 'critical':
      return ''
    case 'high':
      return '🟠'
    case 'medium':
      return '🟡'
    case 'low':
      return ''
    default:
      return ''
  }
}

const getEffortColor = (effort: string) => {
  switch (effort) {
    case 'low':
      return 'bg-green-50 text-green-700'
    case 'medium':
      return 'bg-yellow-50 text-yellow-700'
    case 'high':
      return 'bg-red-50 text-red-700'
    default:
      return 'bg-gray-50 text-gray-700'
  }
}

export const GapAnalysisPanel: React.FC<GapAnalysisPanelProps> = ({
  gaps,
  onViewEvidence,
}) => {
  const [expandedGaps, setExpandedGaps] = useState<Set<string>>(new Set())

  const toggleGap = (controlId: string) => {
    const newExpanded = new Set(expandedGaps)
    if (newExpanded.has(controlId)) {
      newExpanded.delete(controlId)
    } else {
      newExpanded.add(controlId)
    }
    setExpandedGaps(newExpanded)
  }

  const criticalGaps = gaps.filter(g => g.severity === 'critical')
  const highGaps = gaps.filter(g => g.severity === 'high')
  const mediumGaps = gaps.filter(g => g.severity === 'medium')
  const lowGaps = gaps.filter(g => g.severity === 'low')

  const totalRemediationDays = gaps.reduce((sum, gap) => {
    return sum + gap.remediation_steps.reduce((stepSum, step) => stepSum + step.estimated_days, 0)
  }, 0)

  if (gaps.length === 0) {
    return (
      <Card>
        <CardHeader>
          <CardTitle>Compliance Gaps</CardTitle>
          <CardDescription>No compliance gaps detected</CardDescription>
        </CardHeader>
        <CardContent>
          <div className="flex items-center justify-center h-32">
            <p className="text-green-600 font-medium"> All requirements are met</p>
          </div>
        </CardContent>
      </Card>
    )
  }

  return (
    <div className="space-y-6">
      {/* Gap Summary */}
      <Card>
        <CardHeader>
          <CardTitle>Compliance Gaps Summary</CardTitle>
          <CardDescription>
            Overview of identified compliance gaps and remediation effort
          </CardDescription>
        </CardHeader>
        <CardContent>
          <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
            <div className="bg-red-50 p-4 rounded-lg border border-red-200">
              <p className="text-sm text-gray-600">Critical</p>
              <p className="text-2xl font-bold text-red-600">{criticalGaps.length}</p>
            </div>
            <div className="bg-orange-50 p-4 rounded-lg border border-orange-200">
              <p className="text-sm text-gray-600">High</p>
              <p className="text-2xl font-bold text-orange-600">{highGaps.length}</p>
            </div>
            <div className="bg-yellow-50 p-4 rounded-lg border border-yellow-200">
              <p className="text-sm text-gray-600">Medium</p>
              <p className="text-2xl font-bold text-yellow-600">{mediumGaps.length}</p>
            </div>
            <div className="bg-blue-50 p-4 rounded-lg border border-blue-200">
              <p className="text-sm text-gray-600">Low</p>
              <p className="text-2xl font-bold text-blue-600">{lowGaps.length}</p>
            </div>
          </div>

          <div className="mt-6 p-4 bg-gray-50 rounded-lg border border-gray-200">
            <p className="text-sm text-gray-600">Estimated Total Remediation Effort</p>
            <p className="text-2xl font-bold text-gray-800">{totalRemediationDays} days</p>
            <p className="text-xs text-gray-500 mt-1">
              Based on estimated effort for all remediation steps
            </p>
          </div>
        </CardContent>
      </Card>

      {/* Gaps by Severity */}
      {[
        { severity: 'critical', gaps: criticalGaps, label: 'Critical Gaps' },
        { severity: 'high', gaps: highGaps, label: 'High Priority Gaps' },
        { severity: 'medium', gaps: mediumGaps, label: 'Medium Priority Gaps' },
        { severity: 'low', gaps: lowGaps, label: 'Low Priority Gaps' },
      ].map(
        section =>
          section.gaps.length > 0 && (
            <Card key={section.severity}>
              <CardHeader>
                <CardTitle className="flex items-center gap-2">
                  <span>{getSeverityIcon(section.severity)}</span>
                  {section.label}
                </CardTitle>
                <CardDescription>
                  {section.gaps.length} gap{section.gaps.length !== 1 ? 's' : ''} identified
                </CardDescription>
              </CardHeader>
              <CardContent className="space-y-4">
                {section.gaps.map(gap => (
                  <Collapsible key={gap.control_id}>
                    <CollapsibleTrigger asChild>
                      <button
                        onClick={() => toggleGap(gap.control_id)}
                        className={`w-full p-4 rounded-lg border-2 text-left transition-colors ${getSeverityColor(gap.severity)} hover:opacity-80`}
                      >
                        <div className="flex items-start justify-between">
                          <div className="flex-1">
                            <h4 className="font-semibold">{gap.control_name}</h4>
                            <p className="text-sm opacity-75 mt-1">{gap.category}</p>
                          </div>
                          <ChevronDown
                            className={`h-5 w-5 transition-transform ${
                              expandedGaps.has(gap.control_id) ? 'rotate-180' : ''
                            }`}
                          />
                        </div>
                      </button>
                    </CollapsibleTrigger>

                    <CollapsibleContent className="mt-2 p-4 bg-gray-50 rounded-lg border border-gray-200 space-y-4">
                      {/* Failed Checks */}
                      <div>
                        <h5 className="font-semibold text-sm mb-2 flex items-center gap-2">
                          <AlertCircle className="h-4 w-4" />
                          Failed Checks
                        </h5>
                        <ul className="space-y-1">
                          {gap.failed_checks.map((check, idx) => (
                            <li key={idx} className="text-sm text-gray-700 flex items-start gap-2">
                              <span className="text-red-500 mt-1">•</span>
                              <span>{check}</span>
                            </li>
                          ))}
                        </ul>
                      </div>

                      {/* Legal Citation */}
                      <div>
                        <h5 className="font-semibold text-sm mb-2">Legal Citation</h5>
                        <p className="text-sm text-gray-700 bg-white p-2 rounded border border-gray-300">
                          {gap.legal_citation}
                        </p>
                      </div>

                      {/* Remediation Steps */}
                      <div>
                        <h5 className="font-semibold text-sm mb-3">Remediation Steps</h5>
                        <div className="space-y-3">
                          {gap.remediation_steps.map(step => (
                            <div
                              key={step.step_number}
                              className={`p-3 rounded-lg border ${getEffortColor(step.effort_level)}`}
                            >
                              <div className="flex items-start justify-between">
                                <div className="flex-1">
                                  <p className="font-medium text-sm">
                                    Step {step.step_number}: {step.description}
                                  </p>
                                  <p className="text-xs mt-1 opacity-75">
                                    Estimated effort: {step.estimated_days} day{step.estimated_days !== 1 ? 's' : ''}
                                  </p>
                                </div>
                                <Badge className="ml-2">{step.effort_level.toUpperCase()}</Badge>
                              </div>
                            </div>
                          ))}
                        </div>
                      </div>

                      {/* Evidence Link */}
                      {gap.evidence_id && (
                        <div className="pt-2 border-t border-gray-300">
                          <Button
                            variant="outline"
                            size="sm"
                            onClick={() => onViewEvidence?.(gap.evidence_id!)}
                            className="w-full"
                          >
                            <ExternalLink className="h-4 w-4 mr-2" />
                            View Related Evidence
                          </Button>
                        </div>
                      )}
                    </CollapsibleContent>
                  </Collapsible>
                ))}
              </CardContent>
            </Card>
          )
      )}
    </div>
  )
}

export default GapAnalysisPanel
