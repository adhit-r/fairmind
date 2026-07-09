'use client'

import Link from 'next/link'
import { useEffect, useMemo, useState } from 'react'
import { useAIGovernance, useEnvironmentalImpact, type EnvironmentalImpactReport } from '@/lib/api/hooks/useAIGovernance'
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
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/ui/tabs'
import {
  IconAlertTriangle,
  IconArrowRight,
  IconCheck,
  IconClipboardCheck,
  IconFileCheck,
  IconLockExclamation,
  IconRouteAltLeft,
  IconShield,
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
  const {
    data: environmentalImpact,
    loading: environmentalLoading,
    error: environmentalError,
    emptyReason: environmentalEmptyReason,
  } = useEnvironmentalImpact(selectedSystem.id)
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

  type BlockerEntry = {
    text: string
    remediationHref?: string
  }

  const governanceState = useMemo(() => {
    const blockerEntries: BlockerEntry[] = []

    if (riskSummary.bySeverity.critical > 0) {
      blockerEntries.push({
        text: `${riskSummary.bySeverity.critical} critical risk item(s) remain open.`,
        remediationHref: `/remediation?source=governance_blocker&priority=critical&title=${encodeURIComponent('Resolve critical risk items')}&description=${encodeURIComponent(`${riskSummary.bySeverity.critical} critical risk item(s) remain open for ${selectedSystem.name}. Review and mitigate before approval.`)}`,
      })
    }
    if (riskSummary.bySeverity.high > 0) {
      blockerEntries.push({
        text: `${riskSummary.bySeverity.high} high-severity risk item(s) still need mitigation or acceptance.`,
        remediationHref: `/remediation?source=governance_blocker&priority=high&title=${encodeURIComponent('Mitigate high-severity risks')}&description=${encodeURIComponent(`${riskSummary.bySeverity.high} high-severity risk item(s) still need mitigation for ${selectedSystem.name}.`)}`,
      })
    }
    if (overallComplianceRate < 70) {
      blockerEntries.push({
        text: `Compliance coverage is only ${overallComplianceRate}%. Core controls are still failing.`,
        remediationHref: `/remediation?source=governance_blocker&priority=critical&title=${encodeURIComponent('Resolve failing compliance controls')}&description=${encodeURIComponent(`Compliance coverage is only ${overallComplianceRate}% for ${selectedSystem.name}. Core controls are failing.`)}`,
      })
    } else if (overallComplianceRate < 85) {
      blockerEntries.push({
        text: `Compliance coverage is ${overallComplianceRate}%. Approval should stay conditional until framework gaps are reduced.`,
        remediationHref: `/remediation?source=governance_blocker&priority=high&title=${encodeURIComponent('Improve compliance coverage')}&description=${encodeURIComponent(`Compliance coverage is ${overallComplianceRate}% for ${selectedSystem.name}. Reduce framework gaps before full approval.`)}`,
      })
    }
    if (evidenceSummary.decisionReadiness !== 'review_ready') {
      blockerEntries.push({
        text: evidenceSummary.recommendedNextStep || 'Evidence is not yet linked strongly enough for approval review.',
        remediationHref: `/remediation?source=evidence_gap&priority=high&title=${encodeURIComponent('Strengthen evidence linkage')}&description=${encodeURIComponent(evidenceSummary.recommendedNextStep || 'Evidence is not yet linked strongly enough for approval review.')}`,
      })
    }
    if (evidenceSummary.missingSignals.length > 0) {
      blockerEntries.push({
        text: `Evidence gaps: ${evidenceSummary.missingSignals.join(', ')}.`,
        remediationHref: `/evidence`,
      })
    }
    if (remediationSummary.active > 0) {
      blockerEntries.push({
        text: `${remediationSummary.active} remediation task(s) are still active.`,
        remediationHref: `/remediation`,
      })
    }
    if (remediationSummary.retestRequiredTasks > remediationSummary.completed) {
      blockerEntries.push({
        text: 'At least one remediation task still requires a completed re-test before sign-off.',
        remediationHref: `/remediation`,
      })
    }

    const seen = new Set<string>()
    const uniqueBlockers = blockerEntries.filter((entry) => {
      if (seen.has(entry.text)) return false
      seen.add(entry.text)
      return true
    })

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
      blockerTexts: uniqueBlockers.map((b) => b.text),
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
    selectedSystem.name,
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

      <Tabs defaultValue="release-gate" className="space-y-6">
        <TabsList className="h-auto flex-wrap justify-start gap-2 rounded-none border-4 border-black bg-white p-2 shadow-[6px_6px_0px_0px_rgba(0,0,0,1)]">
          <TabsTrigger
            value="release-gate"
            className="rounded-none border-2 border-transparent px-4 py-2 text-xs font-black uppercase data-[state=active]:border-black data-[state=active]:bg-primary data-[state=active]:text-primary-foreground data-[state=active]:shadow-[3px_3px_0px_0px_rgba(0,0,0,1)]"
          >
            Release Gate
          </TabsTrigger>
          <TabsTrigger
            value="environmental-impact"
            className="rounded-none border-2 border-transparent px-4 py-2 text-xs font-black uppercase data-[state=active]:border-black data-[state=active]:bg-orange data-[state=active]:text-black data-[state=active]:shadow-[3px_3px_0px_0px_rgba(0,0,0,1)]"
          >
            Environmental Impact
          </TabsTrigger>
        </TabsList>

        <TabsContent value="release-gate" className="space-y-6">
      <Card className="overflow-hidden border-4 border-black bg-[#f8fbf7] shadow-[8px_8px_0px_0px_rgba(0,0,0,1)]">
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
                    <div key={blocker.text} className="flex items-start justify-between gap-2">
                      <p className="flex-1">• {blocker.text}</p>
                      {blocker.remediationHref && (
                        <Link
                          href={blocker.remediationHref}
                          className="shrink-0 border border-white/40 bg-white/10 px-2 py-0.5 text-[11px] font-black uppercase text-white transition hover:bg-orange hover:text-black hover:border-orange"
                        >
                          <IconRouteAltLeft className="inline h-3 w-3 mr-1" />
                          Remediate
                        </Link>
                      )}
                    </div>
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
              {remediationSummary.criticalActive > 0 && (
                <div className="border-2 border-red-600 bg-red-50 p-4">
                  <div className="flex items-start gap-3">
                    <IconAlertTriangle className="mt-0.5 h-5 w-5 text-red-700 shrink-0" />
                    <div className="space-y-2">
                      <p className="font-black uppercase text-red-800">
                        {remediationSummary.criticalActive} critical remediation task{remediationSummary.criticalActive !== 1 ? 's' : ''} open
                      </p>
                      <p className="text-sm text-red-700">
                        The "Approve release" action is blocked until all critical remediation tasks are resolved or their priority is reduced.
                      </p>
                      <Link
                        href="/remediation"
                        className="inline-flex items-center gap-1.5 border-2 border-red-700 bg-red-700 px-3 py-1.5 text-xs font-black uppercase text-white transition hover:bg-white hover:text-red-700"
                      >
                        <IconRouteAltLeft className="h-3.5 w-3.5" />
                        Review critical remediations
                      </Link>
                    </div>
                  </div>
                </div>
              )}
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
                  <IconFileCheck className="h-5 w-5" />
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
                      {remediationSummary.criticalActive > 0
                        ? `Resolve ${remediationSummary.criticalActive} critical remediation task${remediationSummary.criticalActive !== 1 ? 's' : ''} before the approval gate can be cleared.`
                        : governanceState.recommendation === 'Go'
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
                      disabled={approvalLoading || remediationSummary.criticalActive > 0}
                      title={remediationSummary.criticalActive > 0 ? 'Resolve critical remediation tasks before approving' : undefined}
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
                      {remediationSummary.criticalActive > 0 ? 'Approval blocked: critical remediations open' : 'Approve release'}
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
        </TabsContent>

        <TabsContent value="environmental-impact" className="space-y-6">
          <EnvironmentalImpactSection
            systemName={selectedSystem.name}
            data={environmentalImpact}
            loading={environmentalLoading}
            error={environmentalError}
            emptyReason={environmentalEmptyReason}
          />
        </TabsContent>
      </Tabs>
    </div>
  )
}

type EnvironmentalImpactSectionProps = {
  systemName: string
  data: EnvironmentalImpactReport | null
  loading: boolean
  error: Error | null
  emptyReason: string | null
}

type AnyRecord = Record<string, unknown>

type EnvironmentalControlView = {
  id: string
  label: string
  status: string
  score: number | null
  evidenceCount: number
  blockerCount: number
  blockers: string[]
}

type EnvironmentalImpactView = {
  version: string
  generatedAt: string
  totalEnergyKwh: number | null
  totalCarbonKgCo2e: number | null
  computeHours: number | null
  inferenceCount: number | null
  trainingRuns: number | null
  location: string
  market: string
  locationCarbonKgCo2e: number | null
  marketCarbonKgCo2e: number | null
  gridIntensityGCo2eKwh: number | null
  marketInstrument: string
  gCo2ePerRequest: number | null
  kgCo2ePerThousandInferences: number | null
  kwhPerThousandInferences: number | null
  kgCo2ePerComputeHour: number | null
  provenanceSource: string
  methodology: string
  boundary: string
  dataQuality: string
  measurementWindow: string
  uncertainty: string
  confidence: string
  confidencePercent: number | null
  recommendationStatus: string
  recommendationText: string
  coverage: EnvironmentalControlView[]
  blockers: Array<{
    id: string
    title: string
    severity: string
    owner: string
    state: string
    dueDate: string
  }>
  mitigationState: string
  mitigationOwner: string
  mitigationDueDate: string
  exceptionState: string
  exceptionReason: string
  exceptionAcceptedBy: string
  evidenceLinks: Array<{
    id: string
    title: string
    url: string | null
    source: string
    confidence: string
  }>
  versionTrail: Array<{
    id: string
    version: string
    createdAt: string
    author: string
    notes: string
  }>
}

const ENVIRONMENTAL_CONTROLS = [
  { id: 'ENV-1', label: 'Workload boundary' },
  { id: 'ENV-2', label: 'Energy measurement' },
  { id: 'ENV-3', label: 'Carbon accounting' },
  { id: 'ENV-4', label: 'Location and market basis' },
  { id: 'ENV-5', label: 'Mitigation and exception' },
  { id: 'ENV-6', label: 'Evidence and versioning' },
]

function EnvironmentalImpactSection({
  systemName,
  data,
  loading,
  error,
  emptyReason,
}: EnvironmentalImpactSectionProps) {
  const view = useMemo(() => buildEnvironmentalImpactView(data), [data])
  const hasData = Boolean(data)

  if (loading) {
    return <EnvironmentalImpactLoading />
  }

  return (
    <div className="space-y-6">
      {error && (
        <Alert className="border-2 border-red-500 bg-red-50 shadow-brutal">
          <IconAlertTriangle className="h-4 w-4" />
          <AlertTitle>Environmental Data Unavailable</AlertTitle>
          <AlertDescription>{error.message}</AlertDescription>
        </Alert>
      )}

      {!error && emptyReason && (
        <Alert className="border-2 border-black bg-[#fff4de] shadow-brutal">
          <IconAlertTriangle className="h-4 w-4" />
          <AlertTitle>Environmental Data Pending</AlertTitle>
          <AlertDescription>
            {emptyReason} The dashboard is holding each environmental field in a visible placeholder state.
          </AlertDescription>
        </Alert>
      )}

      <Card className="overflow-hidden border-4 border-black bg-[#f8fbf7] shadow-[8px_8px_0px_0px_rgba(0,0,0,1)]">
        <CardContent className="grid gap-0 p-0 xl:grid-cols-[1.15fr_0.85fr]">
          <div className="border-b-4 border-black p-6 xl:border-b-0 xl:border-r-4">
            <p className="text-xs font-black uppercase tracking-[0.22em] text-muted-foreground">Environmental Impact</p>
            <h2 className="mt-2 text-3xl font-black uppercase">Carbon Readiness For {systemName}</h2>
            <p className="mt-3 max-w-2xl text-sm text-slate-700">
              Energy, carbon, confidence, and evidence are shown as audit fields. Missing values stay explicit until the backend returns a packet.
            </p>

            <div className="mt-5 grid gap-4 md:grid-cols-3">
              <EnvironmentalMetricTile
                label="Total Carbon"
                value={formatMetric(view.totalCarbonKgCo2e, 'kg CO2e')}
                detail={hasData ? 'All reported workload phases' : 'Awaiting environmental packet'}
              />
              <EnvironmentalMetricTile
                label="Market Carbon"
                value={formatMetric(view.marketCarbonKgCo2e, 'kg CO2e')}
                detail={view.market}
              />
              <EnvironmentalMetricTile
                label="Confidence"
                value={view.confidence}
                detail={view.dataQuality}
              />
            </div>
          </div>

          <div className="bg-black p-6 text-white">
            <p className="text-xs font-black uppercase tracking-[0.22em] text-orange">Environmental Gate</p>
            <div className="mt-4 border-2 border-white p-4">
              <p className="font-black uppercase">Recommendation</p>
              <p className={`mt-2 text-3xl font-black ${recommendationClass(view.recommendationStatus)}`}>
                {view.recommendationStatus}
              </p>
              <p className="mt-2 text-sm text-slate-200">{view.recommendationText}</p>
            </div>
            <div className="mt-4 grid gap-3 sm:grid-cols-2">
              <div className="border-2 border-white p-4">
                <p className="text-xs font-bold uppercase text-slate-300">Blockers</p>
                <p className="mt-2 text-2xl font-black">{view.blockers.length}</p>
              </div>
              <div className="border-2 border-white p-4">
                <p className="text-xs font-bold uppercase text-slate-300">Exception</p>
                <p className="mt-2 text-lg font-black uppercase">{view.exceptionState}</p>
              </div>
            </div>
            <div className="mt-4 border-2 border-white p-4">
              <p className="text-xs font-bold uppercase text-slate-300">Version</p>
              <p className="mt-2 font-black">{view.version}</p>
              <p className="mt-1 text-sm text-slate-200">{view.generatedAt}</p>
            </div>
          </div>
        </CardContent>
      </Card>

      <div className="grid grid-cols-1 gap-4 md:grid-cols-2 xl:grid-cols-5">
        <EnvironmentalMetricTile label="Energy Total" value={formatMetric(view.totalEnergyKwh, 'kWh')} detail="Measured or estimated energy" />
        <EnvironmentalMetricTile label="Compute Hours" value={formatMetric(view.computeHours, 'h')} detail="Training and inference compute" />
        <EnvironmentalMetricTile label="Inferences" value={formatIntegerMetric(view.inferenceCount)} detail="Requests in measurement window" />
        <EnvironmentalMetricTile label="Training Runs" value={formatIntegerMetric(view.trainingRuns)} detail="Runs included in boundary" />
        <EnvironmentalMetricTile label="Intensity" value={formatMetric(view.gCo2ePerRequest, 'g CO2e/request')} detail="Primary request intensity" />
      </div>

      <div className="grid grid-cols-1 gap-6 xl:grid-cols-3">
        <Card className="xl:col-span-2">
          <CardHeader className="border-b-2 border-black bg-[#fff4de]">
            <CardTitle className="text-xl font-black uppercase">ENV-1 To ENV-6 Coverage</CardTitle>
          </CardHeader>
          <CardContent className="grid gap-4 p-6 md:grid-cols-2">
            {view.coverage.map((control) => (
              <div key={control.id} className="border-2 border-black bg-white p-4">
                <div className="flex items-start justify-between gap-3">
                  <div>
                    <p className="text-xs font-black uppercase text-muted-foreground">{control.id}</p>
                    <h3 className="mt-1 font-black uppercase">{control.label}</h3>
                  </div>
                  <EnvironmentalStatusBadge status={control.status} />
                </div>
                <div className="mt-4 flex items-center justify-between text-sm">
                  <span>Coverage</span>
                  <span className="font-black">{control.score === null ? 'Unknown' : `${control.score}%`}</span>
                </div>
                <Progress value={control.score ?? 0} className="mt-2 h-3 rounded-none border-2 border-black" />
                <div className="mt-3 grid grid-cols-2 gap-2 text-xs">
                  <div className="border border-black p-2">
                    <p className="font-bold uppercase text-muted-foreground">Evidence</p>
                    <p className="mt-1 font-black">{control.evidenceCount}</p>
                  </div>
                  <div className="border border-black p-2">
                    <p className="font-bold uppercase text-muted-foreground">Blockers</p>
                    <p className="mt-1 font-black">{control.blockerCount}</p>
                  </div>
                </div>
                {control.blockers.length > 0 && (
                  <p className="mt-3 text-sm text-red-700">{control.blockers.slice(0, 2).join(', ')}</p>
                )}
              </div>
            ))}
          </CardContent>
        </Card>

        <Card>
          <CardHeader className="border-b-2 border-black bg-[#e9f7f0]">
            <CardTitle className="text-xl font-black uppercase">Provenance And Uncertainty</CardTitle>
          </CardHeader>
          <CardContent className="space-y-3 p-6">
            <EnvironmentalField label="Source" value={view.provenanceSource} />
            <EnvironmentalField label="Methodology" value={view.methodology} />
            <EnvironmentalField label="Boundary" value={view.boundary} />
            <EnvironmentalField label="Measurement Window" value={view.measurementWindow} />
            <EnvironmentalField label="Uncertainty" value={view.uncertainty} />
            <EnvironmentalField label="Confidence" value={view.confidence} />
          </CardContent>
        </Card>
      </div>

      <div className="grid grid-cols-1 gap-6 xl:grid-cols-3">
        <Card>
          <CardHeader className="border-b-2 border-black bg-[#f8fbf7]">
            <CardTitle className="text-xl font-black uppercase">Location And Market Carbon</CardTitle>
          </CardHeader>
          <CardContent className="space-y-3 p-6">
            <EnvironmentalField label="Location" value={view.location} />
            <EnvironmentalField label="Market" value={view.market} />
            <EnvironmentalField label="Location-Based Carbon" value={formatMetric(view.locationCarbonKgCo2e, 'kg CO2e')} />
            <EnvironmentalField label="Market-Based Carbon" value={formatMetric(view.marketCarbonKgCo2e, 'kg CO2e')} />
            <EnvironmentalField label="Grid Intensity" value={formatMetric(view.gridIntensityGCo2eKwh, 'g CO2e/kWh')} />
            <EnvironmentalField label="Market Instrument" value={view.marketInstrument} />
          </CardContent>
        </Card>

        <Card>
          <CardHeader className="border-b-2 border-black bg-[#fff4de]">
            <CardTitle className="text-xl font-black uppercase">Intensity</CardTitle>
          </CardHeader>
          <CardContent className="space-y-3 p-6">
            <EnvironmentalField label="Request Intensity" value={formatMetric(view.gCo2ePerRequest, 'g CO2e/request')} />
            <EnvironmentalField label="Per 1k Inferences" value={formatMetric(view.kgCo2ePerThousandInferences, 'kg CO2e')} />
            <EnvironmentalField label="Energy Per 1k Inferences" value={formatMetric(view.kwhPerThousandInferences, 'kWh')} />
            <EnvironmentalField label="Per Compute Hour" value={formatMetric(view.kgCo2ePerComputeHour, 'kg CO2e/h')} />
          </CardContent>
        </Card>

        <Card>
          <CardHeader className="border-b-2 border-black bg-[#fde8e8]">
            <CardTitle className="text-xl font-black uppercase">Mitigation And Exception</CardTitle>
          </CardHeader>
          <CardContent className="space-y-3 p-6">
            <EnvironmentalField label="Mitigation State" value={view.mitigationState} />
            <EnvironmentalField label="Owner" value={view.mitigationOwner} />
            <EnvironmentalField label="Due Date" value={view.mitigationDueDate} />
            <EnvironmentalField label="Exception State" value={view.exceptionState} />
            <EnvironmentalField label="Exception Reason" value={view.exceptionReason} />
            <EnvironmentalField label="Accepted By" value={view.exceptionAcceptedBy} />
          </CardContent>
        </Card>
      </div>

      <div className="grid grid-cols-1 gap-6 xl:grid-cols-3">
        <Card>
          <CardHeader className="border-b-2 border-black bg-[#fde8e8]">
            <CardTitle className="text-xl font-black uppercase">Blockers</CardTitle>
          </CardHeader>
          <CardContent className="space-y-3 p-6">
            {view.blockers.length > 0 ? (
              view.blockers.map((blocker) => (
                <div key={blocker.id} className="border-2 border-black bg-white p-4">
                  <div className="flex items-start justify-between gap-3">
                    <p className="font-black uppercase">{blocker.title}</p>
                    <Badge className="rounded-none border-2 border-black bg-red-600 text-white">{blocker.severity}</Badge>
                  </div>
                  <p className="mt-2 text-sm text-slate-700">{blocker.state}</p>
                  <p className="mt-2 text-xs font-bold uppercase text-muted-foreground">
                    {blocker.owner} / {blocker.dueDate}
                  </p>
                </div>
              ))
            ) : (
              <p className="border-2 border-black bg-white p-4 text-sm text-slate-700">
                {hasData ? 'No environmental blockers returned.' : 'No blockers can be confirmed until an environmental packet is returned.'}
              </p>
            )}
          </CardContent>
        </Card>

        <Card>
          <CardHeader className="border-b-2 border-black bg-[#e9f7f0]">
            <CardTitle className="text-xl font-black uppercase">Evidence Links</CardTitle>
          </CardHeader>
          <CardContent className="space-y-3 p-6">
            {view.evidenceLinks.length > 0 ? (
              view.evidenceLinks.map((link) => (
                <div key={link.id} className="border-2 border-black bg-white p-4">
                  {link.url ? (
                    <a href={link.url} target="_blank" rel="noreferrer" className="font-black uppercase underline decoration-2 underline-offset-4">
                      {link.title}
                    </a>
                  ) : (
                    <p className="font-black uppercase">{link.title}</p>
                  )}
                  <p className="mt-2 text-sm text-slate-700">{link.source}</p>
                  <p className="mt-2 text-xs font-bold uppercase text-muted-foreground">Confidence: {link.confidence}</p>
                </div>
              ))
            ) : (
              <p className="border-2 border-black bg-white p-4 text-sm text-slate-700">
                No environmental evidence links returned.
              </p>
            )}
          </CardContent>
        </Card>

        <Card>
          <CardHeader className="border-b-2 border-black bg-[#fff4de]">
            <CardTitle className="text-xl font-black uppercase">Version Trail</CardTitle>
          </CardHeader>
          <CardContent className="space-y-3 p-6">
            {view.versionTrail.length > 0 ? (
              view.versionTrail.map((version) => (
                <div key={version.id} className="border-2 border-black bg-white p-4">
                  <div className="flex items-start justify-between gap-3">
                    <p className="font-black uppercase">{version.version}</p>
                    <p className="text-xs font-bold uppercase text-muted-foreground">{version.createdAt}</p>
                  </div>
                  <p className="mt-2 text-sm text-slate-700">{version.notes}</p>
                  <p className="mt-2 text-xs font-bold uppercase text-muted-foreground">{version.author}</p>
                </div>
              ))
            ) : (
              <p className="border-2 border-black bg-white p-4 text-sm text-slate-700">
                No environmental version trail returned.
              </p>
            )}
          </CardContent>
        </Card>
      </div>
    </div>
  )
}

function EnvironmentalImpactLoading() {
  return (
    <div className="space-y-6">
      <Skeleton className="h-48 w-full" />
      <div className="grid grid-cols-1 gap-4 md:grid-cols-2 xl:grid-cols-5">
        {[...Array(5)].map((_, index) => (
          <Skeleton key={index} className="h-28" />
        ))}
      </div>
      <div className="grid grid-cols-1 gap-6 xl:grid-cols-3">
        <Skeleton className="h-96 xl:col-span-2" />
        <Skeleton className="h-96" />
      </div>
    </div>
  )
}

function EnvironmentalMetricTile({ label, value, detail }: { label: string; value: string; detail: string }) {
  return (
    <div className="border-2 border-black bg-white p-4 shadow-[4px_4px_0px_0px_#000]">
      <p className="text-xs font-bold uppercase text-muted-foreground">{label}</p>
      <p className="mt-2 break-words text-2xl font-black">{value}</p>
      <p className="mt-2 text-sm text-slate-700">{detail}</p>
    </div>
  )
}

function EnvironmentalField({ label, value }: { label: string; value: string }) {
  return (
    <div className="border-2 border-black bg-white p-3">
      <p className="text-xs font-bold uppercase text-muted-foreground">{label}</p>
      <p className="mt-1 break-words text-sm font-black">{value}</p>
    </div>
  )
}

function EnvironmentalStatusBadge({ status }: { status: string }) {
  return (
    <Badge className={`rounded-none border-2 border-black px-2 py-1 text-[11px] font-black uppercase ${statusClass(status)}`}>
      {status}
    </Badge>
  )
}

function buildEnvironmentalImpactView(data: EnvironmentalImpactReport | null): EnvironmentalImpactView {
  const record = asRecord(data)
  const totals = asRecord(record.totals)
  const carbon = firstRecord(record, ['carbon', 'marketCarbon', 'market_carbon', 'locationMarketCarbon', 'location_market_carbon']).source
  const intensity = firstRecord(record, ['intensity', 'carbonIntensity', 'carbon_intensity']).source
  const provenance = firstRecord(record, ['provenance', 'sourceProvenance', 'source_provenance']).source
  const provenanceUncertainty = firstRecord(provenance, ['uncertainty']).source
  const rootUncertainty = firstRecord(record, ['uncertainty']).source
  const uncertainty = Object.keys(provenanceUncertainty).length > 0 ? provenanceUncertainty : rootUncertainty
  const recommendation = asRecord(record.recommendation)
  const recommendationText = firstString([recommendation], ['summary', 'nextStep', 'next_step', 'text', 'message'])
    || (typeof record.recommendation === 'string' ? record.recommendation : '')
  const confidenceRaw = record.confidence ?? provenance.confidence
  const exception = normalizeException(record)

  return {
    version: firstString([record], ['version', 'reportVersion', 'report_version']) || 'Not versioned',
    generatedAt: formatDate(firstString([record], ['generatedAt', 'generated_at', 'createdAt', 'created_at', 'updatedAt', 'updated_at'])),
    totalEnergyKwh: firstNumber([totals, record], ['energyKwh', 'energy_kwh', 'totalEnergyKwh', 'total_energy_kwh']),
    totalCarbonKgCo2e: firstNumber([totals, record], ['carbonKgCo2e', 'carbon_kg_co2e', 'totalCarbonKgCo2e', 'total_carbon_kg_co2e', 'kgCo2e', 'kg_co2e']),
    computeHours: firstNumber([totals, record], ['computeHours', 'compute_hours']),
    inferenceCount: firstNumber([totals, record], ['inferenceCount', 'inference_count', 'requests', 'requestCount', 'request_count']),
    trainingRuns: firstNumber([totals, record], ['trainingRuns', 'training_runs']),
    location: firstString([carbon, record], ['location', 'region', 'dataCenterRegion', 'data_center_region']) || 'Not reported',
    market: firstString([carbon, record], ['market', 'marketRegion', 'market_region']) || 'Not reported',
    locationCarbonKgCo2e: firstNumber([carbon, record], ['locationBasedKgCo2e', 'location_based_kg_co2e', 'locationCarbonKgCo2e', 'location_carbon_kg_co2e']),
    marketCarbonKgCo2e: firstNumber([carbon, record], ['marketBasedKgCo2e', 'market_based_kg_co2e', 'marketCarbonKgCo2e', 'market_carbon_kg_co2e']),
    gridIntensityGCo2eKwh: firstNumber([carbon, record], ['gridIntensityGCo2eKwh', 'grid_intensity_g_co2e_kwh', 'gridIntensity', 'grid_intensity']),
    marketInstrument: firstString([carbon], ['marketInstrument', 'market_instrument', 'renewableInstrument', 'renewable_instrument']) || 'Not reported',
    gCo2ePerRequest: firstNumber([intensity, record], ['gCo2ePerRequest', 'g_co2e_per_request', 'gramsCo2ePerRequest', 'grams_co2e_per_request']),
    kgCo2ePerThousandInferences: firstNumber([intensity, record], ['kgCo2ePerThousandInferences', 'kg_co2e_per_thousand_inferences', 'kgCo2ePer1kInferences', 'kg_co2e_per_1k_inferences']),
    kwhPerThousandInferences: firstNumber([intensity, record], ['kwhPerThousandInferences', 'kwh_per_thousand_inferences', 'kwhPer1kInferences', 'kwh_per_1k_inferences']),
    kgCo2ePerComputeHour: firstNumber([intensity, record], ['kgCo2ePerComputeHour', 'kg_co2e_per_compute_hour']),
    provenanceSource: firstString([provenance], ['source', 'sourceSystem', 'source_system']) || 'Not reported',
    methodology: firstString([provenance], ['methodology', 'method', 'calculationMethod', 'calculation_method']) || 'Not reported',
    boundary: firstString([provenance], ['boundary', 'systemBoundary', 'system_boundary', 'scope']) || 'Not reported',
    dataQuality: firstString([provenance], ['dataQuality', 'data_quality', 'quality']) || 'Unknown quality',
    measurementWindow: firstString([provenance, record], ['measurementWindow', 'measurement_window', 'window']) || 'Not reported',
    uncertainty: formatUncertainty(uncertainty),
    confidence: formatConfidence(confidenceRaw),
    confidencePercent: confidencePercent(confidenceRaw),
    recommendationStatus: firstString([recommendation, record], ['status', 'recommendationStatus', 'recommendation_status']) || (data ? 'Review Required' : 'Data Needed'),
    recommendationText: recommendationText || (data
      ? 'Environmental assessment returned without a recommendation summary.'
      : 'Environmental impact data has not been reported for this AI system.'),
    coverage: normalizeCoverage(record),
    blockers: normalizeBlockers(record),
    mitigationState: firstString([asRecord(record.mitigation)], ['state', 'status']) || 'Not started',
    mitigationOwner: firstString([asRecord(record.mitigation)], ['owner', 'assignee']) || 'Unassigned',
    mitigationDueDate: formatDate(firstString([asRecord(record.mitigation)], ['dueDate', 'due_date'])),
    exceptionState: exception.state,
    exceptionReason: exception.reason,
    exceptionAcceptedBy: exception.acceptedBy,
    evidenceLinks: normalizeEvidenceLinks(record),
    versionTrail: normalizeVersionTrail(record),
  }
}

function normalizeCoverage(record: AnyRecord): EnvironmentalControlView[] {
  const source = record.coverage ?? record.envCoverage ?? record.env_coverage ?? record.controls
  const rawControls = Array.isArray(source)
    ? source.map(asRecord)
    : Object.entries(asRecord(source)).map(([key, value]) => ({ ...asRecord(value), id: key }))

  return ENVIRONMENTAL_CONTROLS.map((control) => {
    const match = (rawControls.find((item) => {
      const id = firstString([item], ['id', 'controlId', 'control_id', 'control'])
      return id?.toUpperCase() === control.id
    }) || {}) as AnyRecord
    const scoreRaw = firstNumber([match], ['score', 'coverage', 'percent', 'percentage'])
    const score = scoreRaw === null ? null : Math.max(0, Math.min(100, Math.round(scoreRaw <= 1 ? scoreRaw * 100 : scoreRaw)))
    const evidenceItems = asArray(match.evidenceLinks ?? match.evidence_links ?? match.evidence)
    const blockerItems = asArray(match.blockers)
    const blockers = blockerItems.map((item) => {
      if (typeof item === 'string') return item
      return firstString([asRecord(item)], ['title', 'message', 'description']) || 'Unspecified blocker'
    })

    return {
      id: control.id,
      label: firstString([match], ['label', 'name']) || control.label,
      status: firstString([match], ['status', 'state']) || inferCoverageStatus(score),
      score,
      evidenceCount: firstNumber([match], ['evidenceCount', 'evidence_count']) ?? evidenceItems.length,
      blockerCount: firstNumber([match], ['blockerCount', 'blocker_count']) ?? blockers.length,
      blockers,
    }
  })
}

function normalizeBlockers(record: AnyRecord): EnvironmentalImpactView['blockers'] {
  return asArray(record.blockers).map((item, index) => {
    if (typeof item === 'string') {
      return {
        id: `blocker-${index}`,
        title: item,
        severity: 'blocker',
        owner: 'Unassigned',
        state: 'Open',
        dueDate: 'Not scheduled',
      }
    }

    const blocker = asRecord(item)
    return {
      id: firstString([blocker], ['id']) || `blocker-${index}`,
      title: firstString([blocker], ['title', 'message', 'description']) || 'Unspecified blocker',
      severity: firstString([blocker], ['severity', 'priority']) || 'blocker',
      owner: firstString([blocker], ['owner', 'assignee']) || 'Unassigned',
      state: firstString([blocker], ['state', 'status']) || 'Open',
      dueDate: formatDate(firstString([blocker], ['dueDate', 'due_date'])),
    }
  })
}

function normalizeException(record: AnyRecord) {
  const mitigation = asRecord(record.mitigation)
  const firstException = asArray(record.exceptions).map(asRecord)[0] || {}
  return {
    state: firstString([mitigation, firstException], ['exceptionState', 'exception_state', 'state', 'status']) || 'No exception',
    reason: firstString([mitigation, firstException], ['exceptionReason', 'exception_reason', 'reason']) || 'Not recorded',
    acceptedBy: firstString([mitigation, firstException], ['acceptedBy', 'accepted_by', 'reviewer']) || 'Not recorded',
  }
}

function normalizeEvidenceLinks(record: AnyRecord): EnvironmentalImpactView['evidenceLinks'] {
  return asArray(record.evidenceLinks ?? record.evidence_links ?? record.evidence).map((item, index) => {
    const link = asRecord(item)
    const url = firstString([link], ['url', 'href', 'link'])
    return {
      id: firstString([link], ['id']) || url || `evidence-${index}`,
      title: firstString([link], ['title', 'name', 'label']) || `Evidence ${index + 1}`,
      url: url || null,
      source: firstString([link], ['source', 'type']) || 'Source not reported',
      confidence: formatConfidence(link.confidence),
    }
  })
}

function normalizeVersionTrail(record: AnyRecord): EnvironmentalImpactView['versionTrail'] {
  const versions = asArray(record.versionTrail ?? record.version_trail ?? record.versions)
  if (versions.length === 0 && (record.version || record.generatedAt || record.generated_at)) {
    versions.push({
      version: record.version,
      createdAt: record.generatedAt ?? record.generated_at,
      author: record.author,
      notes: 'Current environmental packet',
    })
  }

  return versions.map((item, index) => {
    const version = asRecord(item)
    return {
      id: firstString([version], ['id']) || `version-${index}`,
      version: firstString([version], ['version', 'label']) || `Version ${index + 1}`,
      createdAt: formatDate(firstString([version], ['createdAt', 'created_at', 'generatedAt', 'generated_at'])),
      author: firstString([version], ['author', 'createdBy', 'created_by']) || 'Not recorded',
      notes: firstString([version], ['notes', 'summary', 'changeNote', 'change_note']) || 'No notes recorded',
    }
  })
}

function firstRecord(source: AnyRecord, keys: string[]): { source: AnyRecord; key: string | null } {
  for (const key of keys) {
    const value = source[key]
    const record = asRecord(value)
    if (Object.keys(record).length > 0) {
      return { source: record, key }
    }
  }
  return { source: {}, key: null }
}

function asRecord(value: unknown): AnyRecord {
  return value && typeof value === 'object' && !Array.isArray(value) ? value as AnyRecord : {}
}

function asArray(value: unknown): unknown[] {
  return Array.isArray(value) ? value : []
}

function firstNumber(sources: AnyRecord[], keys: string[]): number | null {
  for (const source of sources) {
    for (const key of keys) {
      const raw = source[key]
      const value = typeof raw === 'string' ? Number(raw) : raw
      if (typeof value === 'number' && Number.isFinite(value)) {
        return value
      }
    }
  }
  return null
}

function firstString(sources: AnyRecord[], keys: string[]): string | null {
  for (const source of sources) {
    for (const key of keys) {
      const value = source[key]
      if (typeof value === 'string' && value.trim()) {
        return value
      }
      if (typeof value === 'number' && Number.isFinite(value)) {
        return String(value)
      }
    }
  }
  return null
}

function formatMetric(value: number | null, unit: string): string {
  if (value === null) return 'Not reported'
  return `${formatNumber(value)} ${unit}`
}

function formatIntegerMetric(value: number | null): string {
  if (value === null) return 'Not reported'
  return new Intl.NumberFormat('en-US', { maximumFractionDigits: 0 }).format(value)
}

function formatNumber(value: number): string {
  return new Intl.NumberFormat('en-US', {
    maximumFractionDigits: value >= 100 ? 0 : 2,
  }).format(value)
}

function formatDate(value: string | null): string {
  if (!value) return 'Not recorded'
  const date = new Date(value)
  if (Number.isNaN(date.getTime())) return value
  return new Intl.DateTimeFormat('en-US', {
    month: 'short',
    day: 'numeric',
    year: 'numeric',
  }).format(date)
}

function formatConfidence(value: unknown): string {
  if (typeof value === 'string' && value.trim()) return value
  const percent = confidencePercent(value)
  return percent === null ? 'Not scored' : `${percent}%`
}

function confidencePercent(value: unknown): number | null {
  const numeric = typeof value === 'string' ? Number(value) : value
  if (typeof numeric !== 'number' || !Number.isFinite(numeric)) return null
  return Math.max(0, Math.min(100, Math.round(numeric <= 1 ? numeric * 100 : numeric)))
}

function formatUncertainty(uncertainty: AnyRecord): string {
  const lower = firstNumber([uncertainty], ['lower', 'lowerBound', 'lower_bound', 'min'])
  const upper = firstNumber([uncertainty], ['upper', 'upperBound', 'upper_bound', 'max'])
  const unit = firstString([uncertainty], ['unit']) || 'kg CO2e'
  const description = firstString([uncertainty], ['description', 'notes'])
  if (lower !== null && upper !== null) {
    return `${formatNumber(lower)} to ${formatNumber(upper)} ${unit}`
  }
  return description || 'Not reported'
}

function inferCoverageStatus(score: number | null): string {
  if (score === null) return 'Unknown'
  if (score >= 90) return 'Covered'
  if (score >= 50) return 'Partial'
  return 'Missing'
}

function statusClass(status: string): string {
  const normalized = status.toLowerCase()
  if (normalized.includes('cover') || normalized.includes('pass') || normalized.includes('ready')) {
    return 'bg-primary text-primary-foreground'
  }
  if (normalized.includes('partial') || normalized.includes('conditional') || normalized.includes('review')) {
    return 'bg-orange text-black'
  }
  if (normalized.includes('block') || normalized.includes('missing') || normalized.includes('fail')) {
    return 'bg-red-600 text-white'
  }
  return 'bg-white text-black'
}

function recommendationClass(status: string): string {
  const normalized = status.toLowerCase()
  if (normalized.includes('conditional') || normalized.includes('review')) return 'text-amber-300'
  if (normalized.includes('go') && !normalized.includes('no')) return 'text-emerald-300'
  if (normalized.includes('no') || normalized.includes('block') || normalized.includes('needed')) return 'text-red-300'
  return 'text-slate-100'
}
