'use client'

import Link from 'next/link'
import { useEffect, useMemo, useState } from 'react'
import {
  IconArrowRight,
  IconChecklist,
  IconFileAnalytics,
  IconFileCheck,
  IconLockCheck,
  IconRosetteDiscountCheck,
  IconShieldCheck,
} from '@tabler/icons-react'

import { useSystemContext } from '@/components/workflow/SystemContext'
import { Badge } from '@/components/ui/badge'
import { Button } from '@/components/ui/button'
import { Card } from '@/components/ui/card'
import { useAIGovernance } from '@/lib/api/hooks/useAIGovernance'
import { useCompliance } from '@/lib/api/hooks/useCompliance'
import { useEvidence } from '@/lib/api/hooks/useEvidence'
import { useRemediation } from '@/lib/api/hooks/useRemediation'
import { useRisks } from '@/lib/api/hooks/useRisks'

function formatTimestamp(value?: string | null) {
  if (!value) return 'Not available'
  const date = new Date(value)
  if (Number.isNaN(date.getTime())) return 'Not available'
  return date.toLocaleString()
}

export default function ReportsPage() {
  const { selectedSystem } = useSystemContext()
  const { getSystemApproval } = useAIGovernance()
  const { data: complianceData, loading: complianceLoading } = useCompliance()
  const { summary: riskSummary, loading: risksLoading } = useRisks(selectedSystem.id)
  const { summary: evidenceSummary, loading: evidenceLoading } = useEvidence(selectedSystem.id)
  const { summary: remediationSummary, loading: remediationLoading } = useRemediation(selectedSystem.id)
  const [approvalState, setApprovalState] = useState<Awaited<ReturnType<typeof getSystemApproval>> | null>(null)

  useEffect(() => {
    let active = true

    const loadApproval = async () => {
      try {
        const state = await getSystemApproval(selectedSystem.id)
        if (active) {
          setApprovalState(state)
        }
      } catch {
        if (active) {
          setApprovalState(null)
        }
      }
    }

    void loadApproval()

    return () => {
      active = false
    }
  }, [getSystemApproval, selectedSystem.id])

  const loading = complianceLoading || risksLoading || evidenceLoading || remediationLoading

  const reportState = useMemo(() => {
    const overallComplianceRate = complianceData?.frameworks?.length
      ? Math.round(
          complianceData.frameworks.reduce((sum, framework) => sum + framework.compliance, 0) /
            complianceData.frameworks.length
        )
      : 0

    const approvalRequest = approvalState?.request || null
    const latestDecision = approvalState?.decisions?.[approvalState.decisions.length - 1] || null
    const releaseStatus = latestDecision?.decision === 'approved'
      ? 'Approved'
      : approvalRequest?.status === 'pending'
        ? 'Pending approval'
        : 'Draft'

    const openCritical = riskSummary.bySeverity.critical + riskSummary.bySeverity.high
    const completedRemediation = remediationSummary.completed
    const activeRemediation = remediationSummary.active
    const evidenceCoverage = evidenceSummary.totalEvidence > 0
      ? Math.round((evidenceSummary.linkedEvidence / evidenceSummary.totalEvidence) * 100)
      : 0

    return {
      overallComplianceRate,
      releaseStatus,
      approvalRequest,
      latestDecision,
      openCritical,
      completedRemediation,
      activeRemediation,
      evidenceCoverage,
      readinessChecklist: [
        {
          label: 'Approval request created',
          done: Boolean(approvalRequest),
        },
        {
          label: 'Evidence linked to governance entities',
          done: evidenceSummary.linkedEvidence > 0,
        },
        {
          label: 'Critical remediation closed',
          done: activeRemediation === 0,
        },
        {
          label: 'Approval decision recorded',
          done: latestDecision?.decision === 'approved',
        },
      ],
    }
  }, [approvalState, complianceData, evidenceSummary.linkedEvidence, evidenceSummary.totalEvidence, remediationSummary.active, remediationSummary.completed, riskSummary.bySeverity.critical, riskSummary.bySeverity.high])

  return (
    <div className="space-y-6">
      <Card className="overflow-hidden border-4 border-black bg-[linear-gradient(135deg,#fff4de_0%,#fff 58%,#e9f7f0_100%)] shadow-[8px_8px_0px_0px_rgba(0,0,0,1)]">
        <div className="grid gap-0 xl:grid-cols-[1.15fr_0.85fr]">
          <div className="border-b-4 border-black p-6 xl:border-b-0 xl:border-r-4">
            <div className="flex flex-wrap items-center gap-2">
              <Badge className="border-2 border-black bg-black px-3 py-1 font-black uppercase text-white">
                <IconFileAnalytics className="mr-2 h-4 w-4" />
                Proof layer
              </Badge>
              <Badge variant="outline" className="border-2 border-black bg-white px-3 py-1 font-bold uppercase">
                {selectedSystem.name}
              </Badge>
            </div>

            <h1 className="mt-4 text-4xl font-black uppercase tracking-tight text-balance">
              Reports should prove what got approved and why
            </h1>
            <p className="mt-3 max-w-2xl text-sm text-slate-700">
              This page turns the selected AI system’s governance state into a release-ready summary.
              It ties approval, evidence, remediation, and risk posture into one defensible view.
            </p>

            <div className="mt-5 grid gap-4 md:grid-cols-3">
              <div className="border-2 border-black bg-white p-4 shadow-[4px_4px_0px_0px_#000]">
                <p className="text-xs font-bold uppercase text-muted-foreground">Release status</p>
                <p className="mt-2 text-3xl font-black">{reportState.releaseStatus}</p>
              </div>
              <div className="border-2 border-black bg-white p-4 shadow-[4px_4px_0px_0px_#000]">
                <p className="text-xs font-bold uppercase text-muted-foreground">Evidence coverage</p>
                <p className="mt-2 text-3xl font-black">{reportState.evidenceCoverage}%</p>
              </div>
              <div className="border-2 border-black bg-white p-4 shadow-[4px_4px_0px_0px_#000]">
                <p className="text-xs font-bold uppercase text-muted-foreground">Compliance rate</p>
                <p className="mt-2 text-3xl font-black">{reportState.overallComplianceRate}%</p>
              </div>
            </div>
          </div>

          <div className="bg-black p-6 text-white">
            <p className="text-xs font-black uppercase tracking-[0.22em] text-orange">Report intent</p>
            <div className="mt-4 space-y-3">
              <div className="border-2 border-white p-4">
                <p className="font-black uppercase">1. Show final state</p>
                <p className="mt-1 text-sm text-slate-200">
                  Capture whether the system is draft, pending approval, or approved.
                </p>
              </div>
              <div className="border-2 border-white p-4">
                <p className="font-black uppercase">2. Show supporting proof</p>
                <p className="mt-1 text-sm text-slate-200">
                  Link evidence coverage, remediation closure, and risk posture to that status.
                </p>
              </div>
              <div className="border-2 border-white p-4">
                <p className="font-black uppercase">3. Export audit story</p>
                <p className="mt-1 text-sm text-slate-200">
                  Send stakeholders to the audit report once the approval chain is complete.
                </p>
              </div>
            </div>
          </div>
        </div>
      </Card>

      <div className="grid gap-4 md:grid-cols-4">
        <Card className="border-2 border-black p-5 shadow-brutal">
          <p className="text-xs font-black uppercase tracking-[0.2em] text-muted-foreground">Open severe risks</p>
          <p className="mt-2 text-3xl font-black">{reportState.openCritical}</p>
          <p className="mt-1 text-sm text-muted-foreground">High + critical items still visible in the risk register.</p>
        </Card>
        <Card className="border-2 border-black p-5 shadow-brutal">
          <p className="text-xs font-black uppercase tracking-[0.2em] text-muted-foreground">Evidence linked</p>
          <p className="mt-2 text-3xl font-black">{evidenceSummary.linkedEvidence}</p>
          <p className="mt-1 text-sm text-muted-foreground">Artifacts attached to governance entities.</p>
        </Card>
        <Card className="border-2 border-black p-5 shadow-brutal">
          <p className="text-xs font-black uppercase tracking-[0.2em] text-muted-foreground">Remediation closed</p>
          <p className="mt-2 text-3xl font-black">{reportState.completedRemediation}</p>
          <p className="mt-1 text-sm text-muted-foreground">Corrective actions completed and ready to reference.</p>
        </Card>
        <Card className="border-2 border-black p-5 shadow-brutal">
          <p className="text-xs font-black uppercase tracking-[0.2em] text-muted-foreground">Approval decisions</p>
          <p className="mt-2 text-3xl font-black">{approvalState?.decisions?.length || 0}</p>
          <p className="mt-1 text-sm text-muted-foreground">Recorded decisions on the selected AI system.</p>
        </Card>
      </div>

      <div className="grid gap-6 xl:grid-cols-[1.05fr_0.95fr]">
        <Card className="border-2 border-black p-6 shadow-brutal">
          <h2 className="text-2xl font-black uppercase">Release Summary</h2>
          <p className="mt-2 text-sm text-muted-foreground">
            This is the narrative a stakeholder or auditor needs before reading deeper artifacts.
          </p>

          {loading ? (
            <p className="mt-6 text-sm text-muted-foreground">Loading current governance state...</p>
          ) : (
            <div className="mt-6 space-y-4">
              <div className="rounded-2xl border-2 border-black bg-slate-50 p-4">
                <p className="text-xs font-bold uppercase text-muted-foreground">Approval request</p>
                <p className="mt-1 text-lg font-black">
                  {reportState.approvalRequest ? reportState.approvalRequest.status : 'Not submitted'}
                </p>
                <p className="mt-1 text-sm text-slate-700">
                  {reportState.approvalRequest
                    ? `Requested on ${formatTimestamp(reportState.approvalRequest.createdAt)} by ${reportState.approvalRequest.requested_by || 'unknown'}.`
                    : 'No approval request has been opened yet for this AI system.'}
                </p>
              </div>

              <div className="rounded-2xl border-2 border-black bg-slate-50 p-4">
                <p className="text-xs font-bold uppercase text-muted-foreground">Latest recorded decision</p>
                <p className="mt-1 text-lg font-black">
                  {reportState.latestDecision ? reportState.latestDecision.decision : 'No decision recorded'}
                </p>
                <p className="mt-1 text-sm text-slate-700">
                  {reportState.latestDecision
                    ? reportState.latestDecision.notes || 'Decision note not provided.'
                    : 'Use AI Governance to submit and decide the release request.'}
                </p>
              </div>

              <div className="rounded-2xl border-2 border-black bg-slate-50 p-4">
                <p className="text-xs font-bold uppercase text-muted-foreground">Evidence summary</p>
                <p className="mt-1 text-sm text-slate-700">
                  {evidenceSummary.totalEvidence} artifacts collected, {evidenceSummary.linkedEvidence} linked,
                  readiness state: <span className="font-bold uppercase">{evidenceSummary.decisionReadiness.replace(/_/g, ' ')}</span>.
                </p>
              </div>
            </div>
          )}
        </Card>

        <Card className="border-2 border-black p-6 shadow-brutal">
          <h2 className="text-2xl font-black uppercase">Readiness Checklist</h2>
          <p className="mt-2 text-sm text-muted-foreground">
            These are the proof points that should be present before the report is shared externally.
          </p>

          <div className="mt-6 space-y-3">
            {reportState.readinessChecklist.map((item) => (
              <div key={item.label} className="flex items-start gap-3 rounded-2xl border-2 border-black bg-white p-4">
                {item.done ? (
                  <IconRosetteDiscountCheck className="mt-0.5 h-5 w-5 text-emerald-600" />
                ) : (
                  <IconChecklist className="mt-0.5 h-5 w-5 text-orange-600" />
                )}
                <div>
                  <p className="font-black uppercase">{item.label}</p>
                  <p className="text-sm text-slate-700">
                    {item.done ? 'Present in current state.' : 'Still missing from the selected AI system history.'}
                  </p>
                </div>
              </div>
            ))}
          </div>

          <div className="mt-6 flex flex-col gap-3">
            <Button asChild variant="default" className="w-full">
              <Link href="/audit-reports">
                Open audit traceability
                <IconArrowRight className="ml-2 h-4 w-4" />
              </Link>
            </Button>
            <Button asChild variant="neutral" className="w-full border-2 border-black font-bold">
              <Link href="/ai-governance">
                Return to approval gate
                <IconArrowRight className="ml-2 h-4 w-4" />
              </Link>
            </Button>
          </div>
        </Card>
      </div>

      <Card className="border-2 border-black p-6 shadow-brutal">
        <h2 className="text-2xl font-black uppercase">What this report can currently prove</h2>
        <div className="mt-5 grid gap-4 md:grid-cols-3">
          <div className="rounded-2xl border-2 border-black bg-slate-50 p-4">
            <div className="flex items-center gap-3">
              <IconShieldCheck className="h-5 w-5" />
              <p className="font-black uppercase">Governance state</p>
            </div>
            <p className="mt-2 text-sm text-slate-700">
              Release status, approval request state, and decision notes for the selected AI system.
            </p>
          </div>
          <div className="rounded-2xl border-2 border-black bg-slate-50 p-4">
            <div className="flex items-center gap-3">
              <IconFileCheck className="h-5 w-5" />
              <p className="font-black uppercase">Evidence trail</p>
            </div>
            <p className="mt-2 text-sm text-slate-700">
              Linked artifact counts, evidence readiness, and missing proof signals.
            </p>
          </div>
          <div className="rounded-2xl border-2 border-black bg-slate-50 p-4">
            <div className="flex items-center gap-3">
              <IconLockCheck className="h-5 w-5" />
              <p className="font-black uppercase">Remediation closure</p>
            </div>
            <p className="mt-2 text-sm text-slate-700">
              Active versus completed corrective actions tied to the system’s release posture.
            </p>
          </div>
        </div>
      </Card>
    </div>
  )
}
