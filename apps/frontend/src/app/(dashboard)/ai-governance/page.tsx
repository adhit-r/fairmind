'use client'

import Link from 'next/link'
import { useEffect, useMemo, useState } from 'react'
import { useAIGovernance } from '@/lib/api/hooks/useAIGovernance'
import { useCompliance } from '@/lib/api/hooks/useCompliance'
import { useEvidence } from '@/lib/api/hooks/useEvidence'
import { usePolicies } from '@/lib/api/hooks/usePolicies'
import { useRemediation } from '@/lib/api/hooks/useRemediation'
import { useRisks } from '@/lib/api/hooks/useRisks'
import { useSystemContext } from '@/components/workflow/SystemContext'
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card'
import { Button } from '@/components/ui/button'
import { Badge } from '@/components/ui/badge'
import { Progress } from '@/components/ui/progress'
import { StatCard } from '@/components/charts/StatCard'
import { PieChart } from '@/components/charts/PieChart'
import { Skeleton } from '@/components/ui/skeleton'
import { Alert, AlertDescription, AlertTitle } from '@/components/ui/alert'
import {
  IconAlertTriangle,
  IconArrowRight,
  IconCheck,
  IconClipboardCheck,
  IconFileCheck,
  IconLockExclamation,
  IconShield,
  IconSparkles,
} from '@tabler/icons-react'

export default function AIGovernancePage() {
  const { selectedSystem } = useSystemContext()
  const {
    frameworks,
    loading: frameworksLoading,
    approvalLoading,
    error: frameworksError,
    getSystemApproval,
    requestSystemApproval,
    decideApprovalRequest,
  } = useAIGovernance()
  const { data: complianceData, loading: complianceLoading, error: complianceError } = useCompliance()
  const { data: policies, loading: policiesLoading } = usePolicies()
  const { summary: riskSummary, loading: risksLoading } = useRisks(selectedSystem.id)
  const { summary: evidenceSummary, loading: evidenceLoading } = useEvidence(selectedSystem.id)
  const { summary: remediationSummary, loading: remediationLoading } = useRemediation(selectedSystem.id)
  const [approvalState, setApprovalState] = useState<Awaited<ReturnType<typeof getSystemApproval>> | null>(null)
  const [approvalError, setApprovalError] = useState<string | null>(null)

  useEffect(() => {
    let active = true

    const loadApproval = async () => {
      try {
        setApprovalError(null)
        const state = await getSystemApproval(selectedSystem.id)
        if (active) {
          setApprovalState(state)
        }
      } catch (error) {
        if (active) {
          setApprovalError(error instanceof Error ? error.message : 'Failed to load approval state')
          setApprovalState(null)
        }
      }
    }

    void loadApproval()

    return () => {
      active = false
    }
  }, [getSystemApproval, selectedSystem.id])

  const complianceDistribution = useMemo(() => {
    if (!complianceData?.frameworks || complianceData.frameworks.length === 0) {
      return [
        { name: 'Compliant', value: 0 },
        { name: 'Partial', value: 0 },
        { name: 'Non-Compliant', value: 0 },
      ]
    }

    const compliant = complianceData.frameworks.filter((framework) => framework.status === 'compliant').length
    const partial = complianceData.frameworks.filter((framework) => framework.status === 'partial').length
    const nonCompliant = complianceData.frameworks.filter((framework) => framework.status === 'non-compliant').length

    return [
      { name: 'Compliant', value: compliant },
      { name: 'Partial', value: partial },
      { name: 'Non-Compliant', value: nonCompliant },
    ]
  }, [complianceData])

  const overallComplianceRate = useMemo(() => {
    if (!complianceData?.frameworks || complianceData.frameworks.length === 0) return 0
    const total = complianceData.frameworks.reduce((sum, framework) => sum + framework.compliance, 0)
    return Math.round(total / complianceData.frameworks.length)
  }, [complianceData])

  const failedControls = riskSummary.open + Math.max(0, Math.ceil((100 - overallComplianceRate) / 20))
  const evidenceCompleteness = useMemo(() => {
    if (evidenceSummary.totalEvidence === 0) {
      return 0
    }

    const linkScore = evidenceSummary.totalEvidence > 0
      ? Math.round((evidenceSummary.linkedEvidence / evidenceSummary.totalEvidence) * 45)
      : 0
    const confidenceScore = Math.round(evidenceSummary.averageConfidence * 35)
    const coverageScore = Math.min(evidenceSummary.totalEvidence * 5, 20)

    return Math.max(0, Math.min(100, linkScore + confidenceScore + coverageScore))
  }, [evidenceSummary.averageConfidence, evidenceSummary.linkedEvidence, evidenceSummary.totalEvidence])

  const loading = frameworksLoading || complianceLoading || policiesLoading || risksLoading || evidenceLoading || remediationLoading

  const governanceState = useMemo(() => {
    const blockers: string[] = []

    if (riskSummary.bySeverity.critical > 0) {
      blockers.push(`${riskSummary.bySeverity.critical} critical risk item(s) remain open.`)
    }
    if (riskSummary.bySeverity.high > 0) {
      blockers.push(`${riskSummary.bySeverity.high} high-severity risk item(s) still need mitigation or acceptance.`)
    }
    if (overallComplianceRate < 70) {
      blockers.push(`Compliance coverage is only ${overallComplianceRate}%. Core controls are still failing.`)
    } else if (overallComplianceRate < 85) {
      blockers.push(`Compliance coverage is ${overallComplianceRate}%. Approval should stay conditional until framework gaps are reduced.`)
    }
    if (evidenceSummary.decisionReadiness !== 'review_ready') {
      blockers.push(evidenceSummary.recommendedNextStep || 'Evidence is not yet linked strongly enough for approval review.')
    }
    if (evidenceSummary.missingSignals.length > 0) {
      blockers.push(`Evidence gaps: ${evidenceSummary.missingSignals.join(', ')}.`)
    }
    if (remediationSummary.active > 0) {
      blockers.push(`${remediationSummary.active} remediation task(s) are still active.`)
    }
    if (remediationSummary.retestRequiredTasks > remediationSummary.completed) {
      blockers.push('At least one remediation task still requires a completed re-test before sign-off.')
    }

    const uniqueBlockers = blockers.filter((item, index) => blockers.indexOf(item) === index)

    let recommendation: 'Go' | 'Conditional Go' | 'No-Go' = 'Go'
    if (
      riskSummary.bySeverity.critical > 0 ||
      overallComplianceRate < 70 ||
      evidenceSummary.totalEvidence === 0 ||
      evidenceSummary.decisionReadiness === 'needs_evidence'
    ) {
      recommendation = 'No-Go'
    } else if (
      riskSummary.open > 0 ||
      remediationSummary.active > 0 ||
      evidenceSummary.decisionReadiness !== 'review_ready' ||
      overallComplianceRate < 90
    ) {
      recommendation = 'Conditional Go'
    }

    return {
      recommendation,
      blockers: uniqueBlockers,
      releaseReady: recommendation === 'Go',
    }
  }, [
    evidenceSummary.decisionReadiness,
    evidenceSummary.missingSignals,
    evidenceSummary.recommendedNextStep,
    evidenceSummary.totalEvidence,
    overallComplianceRate,
    remediationSummary.active,
    remediationSummary.completed,
    remediationSummary.retestRequiredTasks,
    riskSummary.bySeverity.critical,
    riskSummary.bySeverity.high,
    riskSummary.open,
  ])

  const recommendationTone = governanceState.recommendation === 'Go'
    ? 'text-emerald-300'
    : governanceState.recommendation === 'Conditional Go'
      ? 'text-amber-300'
      : 'text-red-300'
  const latestApprovalRequest = approvalState?.request || null
  const latestDecision = approvalState?.decisions?.[approvalState.decisions.length - 1] || null

  if (loading) {
    return (
      <div className="space-y-6">
        <Skeleton className="h-32 w-full" />
        <div className="grid grid-cols-1 gap-4 lg:grid-cols-4">
          {[...Array(4)].map((_, index) => (
            <Skeleton key={index} className="h-32" />
          ))}
        </div>
        <div className="grid grid-cols-1 gap-6 xl:grid-cols-3">
          <Skeleton className="h-96 xl:col-span-2" />
          <Skeleton className="h-96" />
        </div>
      </div>
    )
  }

  return (
    <div className="space-y-6">
      {(frameworksError || complianceError || approvalError) && (
        <Alert className="border-2 border-red-500 shadow-brutal">
          <IconAlertTriangle className="h-4 w-4" />
          <AlertTitle>Governance Data Incomplete</AlertTitle>
          <AlertDescription>
            {frameworksError?.message || complianceError?.message || approvalError || 'Governance surfaces are partially unavailable.'}
          </AlertDescription>
        </Alert>
      )}

      <Card className="overflow-hidden border-4 border-black bg-[linear-gradient(135deg,#e9f7f0_0%,#fff 55%,#fff4de_100%)] shadow-[8px_8px_0px_0px_rgba(0,0,0,1)]">
        <CardContent className="grid gap-0 p-0 xl:grid-cols-[1.25fr_0.75fr]">
          <div className="border-b-4 border-black p-6 xl:border-b-0 xl:border-r-4">
            <p className="text-xs font-black uppercase tracking-[0.22em] text-muted-foreground">Governance Review</p>
            <h1 className="mt-2 text-4xl font-black uppercase">Can {selectedSystem.name} Move Forward?</h1>
            <p className="mt-3 max-w-2xl text-sm text-slate-700">
              This is the decision surface for the selected AI system. It should tell the team whether risks,
              policy controls, and evidence are strong enough for release approval.
            </p>

            <div className="mt-5 grid gap-4 md:grid-cols-3">
              <div className="border-2 border-black bg-white p-4 shadow-[4px_4px_0px_0px_#000]">
                <p className="text-xs font-bold uppercase text-muted-foreground">Compliance Rate</p>
                <p className="mt-2 text-4xl font-black">{overallComplianceRate}%</p>
                <Progress value={overallComplianceRate} className="mt-3 h-3 border-2 border-black" />
              </div>
              <div className="border-2 border-black bg-white p-4 shadow-[4px_4px_0px_0px_#000]">
                <p className="text-xs font-bold uppercase text-muted-foreground">Failed Controls</p>
                <p className="mt-2 text-4xl font-black text-red-600">{failedControls}</p>
                <p className="mt-2 text-sm text-slate-700">Open risks and incomplete framework coverage still need action.</p>
              </div>
              <div className="border-2 border-black bg-white p-4 shadow-[4px_4px_0px_0px_#000]">
                <p className="text-xs font-bold uppercase text-muted-foreground">Evidence Completeness</p>
                <p className="mt-2 text-4xl font-black">{evidenceCompleteness}%</p>
                <Progress value={evidenceCompleteness} className="mt-3 h-3 border-2 border-black" />
              </div>
            </div>
          </div>

          <div className="bg-black p-6 text-white">
            <p className="text-xs font-black uppercase tracking-[0.22em] text-orange">Decision Status</p>
            <div className="mt-4 border-2 border-white p-4">
              <p className="font-black uppercase">Current Recommendation</p>
              <p className={`mt-2 text-3xl font-black ${recommendationTone}`}>
                {governanceState.recommendation}
              </p>
              <p className="mt-2 text-sm text-slate-200">
                {governanceState.releaseReady
                  ? 'Risks, evidence, and remediation are aligned enough for release approval.'
                  : 'Approval should wait until the blockers below are resolved or explicitly accepted.'}
              </p>
            </div>
            <div className="mt-4 border-2 border-white p-4">
              <p className="font-black uppercase">Release blockers</p>
              <div className="mt-2 space-y-2 text-sm text-slate-200">
                {governanceState.blockers.length > 0 ? (
                  governanceState.blockers.slice(0, 4).map((blocker) => (
                    <p key={blocker}>• {blocker}</p>
                  ))
                ) : (
                  <p>• No material blockers are currently visible for this AI system.</p>
                )}
              </div>
            </div>
            <div className="mt-4 space-y-3">
              <Link href="/risks" className="block border-2 border-white bg-white/10 p-4 transition hover:bg-orange hover:text-black">
                <p className="font-black uppercase">Review blockers in risk register</p>
                <p className="mt-1 text-sm opacity-90">Start with scoped risks before touching reports or approvals.</p>
              </Link>
              <Link href="/evidence" className="block border-2 border-white bg-white/10 p-4 transition hover:bg-orange hover:text-black">
                <div className="flex items-center justify-between gap-2">
                  <p className="font-black uppercase">Close evidence gaps</p>
                  {evidenceSummary.missingSignals.length > 0 && (
                    <span className="shrink-0 rounded border-2 border-red-500 bg-red-500 px-2 py-0.5 text-xs font-black text-white">
                      {evidenceSummary.missingSignals.length} gap{evidenceSummary.missingSignals.length !== 1 ? 's' : ''}
                    </span>
                  )}
                </div>
                <p className="mt-1 text-sm opacity-90">
                  {evidenceSummary.missingSignals.length > 0
                    ? `Missing: ${evidenceSummary.missingSignals.slice(0, 2).join(', ')}${evidenceSummary.missingSignals.length > 2 ? ` +${evidenceSummary.missingSignals.length - 2} more` : ''}`
                    : 'Attach traceable proof to each important control or decision.'}
                </p>
              </Link>
            </div>
          </div>
        </CardContent>
      </Card>

      <div className="grid grid-cols-1 gap-4 md:grid-cols-2 xl:grid-cols-4">
        <StatCard
          title="Frameworks"
          value={frameworks.length}
          icon={<IconShield className="h-5 w-5" />}
        />
        <StatCard
          title="Policies"
          value={policies?.length || 0}
          icon={<IconClipboardCheck className="h-5 w-5" />}
        />
        <StatCard
          title="Open Risks"
          value={riskSummary.open}
          icon={<IconAlertTriangle className="h-5 w-5" />}
        />
        <StatCard
          title="Evidence Score"
          value={`${evidenceCompleteness}%`}
          icon={<IconFileCheck className="h-5 w-5" />}
        />
      </div>

      <div className="grid grid-cols-1 gap-6 xl:grid-cols-3">
        <Card className="xl:col-span-2">
          <CardHeader className="border-b-2 border-black bg-[#fff4de]">
            <div className="flex items-center justify-between">
              <CardTitle className="text-xl font-black uppercase">Framework Review</CardTitle>
              {evidenceSummary.missingSignals.length > 0 && (
                <Link
                  href="/evidence"
                  className="flex items-center gap-2 border-2 border-red-600 bg-red-50 px-3 py-1.5 text-xs font-black uppercase text-red-700 transition hover:bg-red-600 hover:text-white"
                >
                  <IconLockExclamation className="h-3.5 w-3.5" />
                  {evidenceSummary.missingSignals.length} evidence gap{evidenceSummary.missingSignals.length !== 1 ? 's' : ''}
                  <IconArrowRight className="h-3.5 w-3.5" />
                </Link>
              )}
            </div>
          </CardHeader>
          <CardContent className="space-y-4 p-6">
            {frameworks.map((framework) => {
              const compliance = complianceData?.frameworks?.find((item) => item.name === framework.name)?.compliance || 0
              return (
                <div key={framework.id} className="border-2 border-black bg-white p-4">
                  <div className="mb-2 flex items-center justify-between">
                    <h3 className="text-lg font-black">{framework.name}</h3>
                    <div className="flex items-center gap-2">
                      {evidenceSummary.decisionReadiness !== 'review_ready' && (
                        <Link href="/evidence">
                          <Badge className="border-2 border-amber-500 bg-amber-100 px-2 py-1 text-[11px] font-black uppercase text-amber-900 transition hover:bg-amber-500 hover:text-white">
                            evidence gaps
                          </Badge>
                        </Link>
                      )}
                      <Badge className="border-2 border-black bg-black text-white">
                        {framework.controls.length} controls
                      </Badge>
                    </div>
                  </div>
                  <p className="mb-3 text-sm text-muted-foreground">{framework.description}</p>
                  <div className="mb-2 flex items-center justify-between text-sm">
                    <span>Progress</span>
                    <span className="font-black">{compliance}%</span>
                  </div>
                  <Progress value={compliance} className="h-3 border-2 border-black" />
                </div>
              )
            })}
          </CardContent>
        </Card>

        <div className="space-y-6">
          <Card>
            <CardHeader className="border-b-2 border-black bg-[#fde8e8]">
              <CardTitle className="text-xl font-black uppercase">Approval Gate</CardTitle>
            </CardHeader>
            <CardContent className="space-y-4 p-6">
              <div className="border-2 border-black p-4">
                <div className="flex items-center gap-3">
                  <IconLockExclamation className="h-5 w-5" />
                  <div>
                    <p className="font-black uppercase">Gate state</p>
                    <p className="text-sm text-slate-700">
                      {governanceState.recommendation} based on risks, evidence readiness, remediation status, and compliance coverage.
                    </p>
                  </div>
                </div>
              </div>
              <div className="grid gap-3 sm:grid-cols-2">
                <div className="border-2 border-black p-4">
                  <p className="text-xs font-bold uppercase text-muted-foreground">Evidence readiness</p>
                  <p className="mt-2 text-lg font-black uppercase">{evidenceSummary.decisionReadiness.replace(/_/g, ' ')}</p>
                </div>
                <div className="border-2 border-black p-4">
                  <p className="text-xs font-bold uppercase text-muted-foreground">Active remediation</p>
                  <p className="mt-2 text-lg font-black">{remediationSummary.active}</p>
                </div>
              </div>
              <Button asChild variant="default" className="w-full">
                <Link href={governanceState.recommendation === 'No-Go' ? '/remediation' : '/evidence'}>
                  {governanceState.recommendation === 'No-Go' ? 'Resolve blockers first' : 'Review approval evidence'}
                  <IconArrowRight className="ml-2 h-4 w-4" />
                </Link>
              </Button>
              <div className="border-2 border-black p-4">
                <p className="text-xs font-bold uppercase text-muted-foreground">Persisted approval</p>
                <p className="mt-2 text-lg font-black uppercase">
                  {latestApprovalRequest ? latestApprovalRequest.status : 'not submitted'}
                </p>
                <p className="mt-1 text-sm text-slate-700">
                  {latestApprovalRequest
                    ? `Requested by ${latestApprovalRequest.requested_by || 'unknown'} on ${new Date(latestApprovalRequest.createdAt).toLocaleDateString()}.`
                    : 'No approval request has been opened for this AI system yet.'}
                </p>
              </div>
              {latestDecision && (
                <div className="border-2 border-black p-4">
                  <p className="text-xs font-bold uppercase text-muted-foreground">Latest decision</p>
                  <p className="mt-2 text-lg font-black uppercase">{latestDecision.decision}</p>
                  <p className="mt-1 text-sm text-slate-700">{latestDecision.notes || 'No decision note recorded.'}</p>
                </div>
              )}
            </CardContent>
          </Card>

          {complianceDistribution.some((entry) => entry.value > 0) && (
            <PieChart title="Compliance Distribution" data={complianceDistribution} />
          )}

          <Card>
            <CardHeader className="border-b-2 border-black bg-[#e9f7f0]">
              <CardTitle className="text-xl font-black uppercase">What Governance Should Resolve</CardTitle>
            </CardHeader>
            <CardContent className="space-y-3 p-6">
              <div className="border-2 border-black p-4">
                <div className="flex items-center gap-3">
                  <IconCheck className="h-5 w-5" />
                  <div>
                    <p className="font-black uppercase">Are controls passing?</p>
                    <p className="text-sm text-slate-700">Use frameworks plus risk register to decide what is actually release-blocking.</p>
                  </div>
                </div>
              </div>
              <div className="border-2 border-black p-4">
                <div className="flex items-center gap-3">
                  <IconSparkles className="h-5 w-5" />
                  <div>
                    <p className="font-black uppercase">Is the evidence defensible?</p>
                    <p className="text-sm text-slate-700">Evidence must connect assessments, remediation, and final decisions.</p>
                  </div>
                </div>
              </div>
              <div className="border-2 border-black p-4">
                <div className="flex items-center gap-3">
                  <IconArrowRight className="h-5 w-5" />
                  <div>
                    <p className="font-black uppercase">What next?</p>
                    <p className="text-sm text-slate-700">
                      {governanceState.recommendation === 'Go'
                        ? 'Evidence and remediation are aligned enough to prepare approval artifacts.'
                        : 'Move unresolved issues into remediation, close evidence gaps, then return here for sign-off.'}
                    </p>
                  </div>
                </div>
              </div>
              <div className="grid gap-2">
                <Button
                  type="button"
                  variant="default"
                  className="w-full"
                  disabled={approvalLoading || governanceState.recommendation === 'No-Go' || latestApprovalRequest?.status === 'pending'}
                  onClick={async () => {
                    try {
                      const nextState = await requestSystemApproval(selectedSystem.id, selectedSystem.owner)
                      setApprovalState(nextState)
                      setApprovalError(null)
                    } catch (error) {
                      setApprovalError(error instanceof Error ? error.message : 'Failed to submit approval request')
                    }
                  }}
                >
                  {approvalLoading ? 'Working...' : latestApprovalRequest?.status === 'pending' ? 'Approval request pending' : 'Submit for approval'}
                </Button>
                {latestApprovalRequest?.status === 'pending' && (
                  <>
                    <Button
                      type="button"
                      variant="neutral"
                      className="w-full border-2 border-black font-bold"
                      disabled={approvalLoading}
                      onClick={async () => {
                        try {
                          await decideApprovalRequest(
                            latestApprovalRequest.id,
                            'approved',
                            `Approved from governance gate with recommendation ${governanceState.recommendation}.`,
                            selectedSystem.owner
                          )
                          const refreshed = await getSystemApproval(selectedSystem.id)
                          setApprovalState(refreshed)
                          setApprovalError(null)
                        } catch (error) {
                          setApprovalError(error instanceof Error ? error.message : 'Failed to approve request')
                        }
                      }}
                    >
                      Approve release
                    </Button>
                    <Button
                      type="button"
                      variant="neutral"
                      className="w-full border-2 border-black font-bold"
                      disabled={approvalLoading}
                      onClick={async () => {
                        try {
                          await decideApprovalRequest(
                            latestApprovalRequest.id,
                            'rejected',
                            'Rejected from governance gate because blockers remain unresolved.',
                            selectedSystem.owner
                          )
                          const refreshed = await getSystemApproval(selectedSystem.id)
                          setApprovalState(refreshed)
                          setApprovalError(null)
                        } catch (error) {
                          setApprovalError(error instanceof Error ? error.message : 'Failed to reject request')
                        }
                      }}
                    >
                      Reject for now
                    </Button>
                  </>
                )}
              </div>
              <Button asChild variant="default" className="w-full">
                <Link href="/remediation">
                  Continue To Remediation
                  <IconArrowRight className="ml-2 h-4 w-4" />
                </Link>
              </Button>
            </CardContent>
          </Card>
        </div>
      </div>
    </div>
  )
}
