'use client'

import Link from 'next/link'
import { useEffect, useMemo, useState } from 'react'
import {
  IconArrowRight,
  IconFileAnalytics,
  IconFileText,
  IconGitBranch,
  IconHistory,
  IconScale,
  IconShieldHalfFilled,
  IconTool,
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

export default function AuditReportsPage() {
  const { selectedSystem } = useSystemContext()
  const { getSystemApproval } = useAIGovernance()
  const { data: complianceData, loading: complianceLoading } = useCompliance()
  const { data: risks, loading: risksLoading } = useRisks(selectedSystem.id)
  const { data: evidence, summary: evidenceSummary, loading: evidenceLoading } = useEvidence(selectedSystem.id)
  const { tasks: remediationTasks, loading: remediationLoading } = useRemediation(selectedSystem.id)
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

  const auditView = useMemo(() => {
    const frameworkNames = complianceData?.frameworks?.map((framework) => framework.name) || []
    const latestDecision = approvalState?.decisions?.[approvalState.decisions.length - 1] || null
    const topRisks = risks
      .filter((risk) => risk.severity === 'critical' || risk.severity === 'high')
      .slice(0, 4)

    return {
      frameworkNames,
      latestDecision,
      topRisks,
      linkedEvidence: evidence.filter((item: any) => item.linkedEntityCount > 0),
      openRemediation: remediationTasks.filter((task) => task.status !== 'done'),
      closedRemediation: remediationTasks.filter((task) => task.status === 'done'),
    }
  }, [approvalState, complianceData, evidence, remediationTasks, risks])

  return (
    <div className="space-y-6">
      <Card className="overflow-hidden border-4 border-black bg-[linear-gradient(135deg,#e9f7f0_0%,#fff 58%,#fff4de_100%)] shadow-[8px_8px_0px_0px_rgba(0,0,0,1)]">
        <div className="grid gap-0 xl:grid-cols-[1.15fr_0.85fr]">
          <div className="border-b-4 border-black p-6 xl:border-b-0 xl:border-r-4">
            <div className="flex flex-wrap items-center gap-2">
              <Badge className="border-2 border-black bg-black px-3 py-1 font-black uppercase text-white">
                <IconFileAnalytics className="mr-2 h-4 w-4" />
                Audit traceability
              </Badge>
              <Badge variant="outline" className="border-2 border-black bg-white px-3 py-1 font-bold uppercase">
                {selectedSystem.name}
              </Badge>
            </div>

            <h1 className="mt-4 text-4xl font-black uppercase tracking-tight text-balance">
              Audit reports should show the full decision chain
            </h1>
            <p className="mt-3 max-w-2xl text-sm text-slate-700">
              This page ties together the selected AI system’s risks, evidence, remediation tasks,
              frameworks, and approval history so the release story is traceable end to end.
            </p>

            <div className="mt-5 grid gap-4 md:grid-cols-3">
              <div className="border-2 border-black bg-white p-4 shadow-[4px_4px_0px_0px_#000]">
                <p className="text-xs font-bold uppercase text-muted-foreground">Approval events</p>
                <p className="mt-2 text-3xl font-black">{approvalState?.decisions?.length || 0}</p>
              </div>
              <div className="border-2 border-black bg-white p-4 shadow-[4px_4px_0px_0px_#000]">
                <p className="text-xs font-bold uppercase text-muted-foreground">Linked evidence</p>
                <p className="mt-2 text-3xl font-black">{auditView.linkedEvidence.length}</p>
              </div>
              <div className="border-2 border-black bg-white p-4 shadow-[4px_4px_0px_0px_#000]">
                <p className="text-xs font-bold uppercase text-muted-foreground">Closed remediation</p>
                <p className="mt-2 text-3xl font-black">{auditView.closedRemediation.length}</p>
              </div>
            </div>
          </div>

          <div className="bg-black p-6 text-white">
            <p className="text-xs font-black uppercase tracking-[0.22em] text-orange">Audit logic</p>
            <div className="mt-4 space-y-3">
              <div className="border-2 border-white p-4">
                <p className="font-black uppercase">Risk to task</p>
                <p className="mt-1 text-sm text-slate-200">
                  Show which high-severity risks drove remediation work.
                </p>
              </div>
              <div className="border-2 border-white p-4">
                <p className="font-black uppercase">Task to evidence</p>
                <p className="mt-1 text-sm text-slate-200">
                  Show which artifacts support the closure and readiness state.
                </p>
              </div>
              <div className="border-2 border-white p-4">
                <p className="font-black uppercase">Evidence to decision</p>
                <p className="mt-1 text-sm text-slate-200">
                  Show the approval request and the final decision note.
                </p>
              </div>
            </div>
          </div>
        </div>
      </Card>

      {loading ? (
        <Card className="border-2 border-black p-6 shadow-brutal">
          <p className="text-sm text-muted-foreground">Loading audit traceability for the selected AI system...</p>
        </Card>
      ) : (
        <>
          <div className="grid gap-6 xl:grid-cols-[1.05fr_0.95fr]">
            <Card className="border-2 border-black p-6 shadow-brutal">
              <h2 className="text-2xl font-black uppercase">Decision History</h2>
              <div className="mt-5 space-y-4">
                <div className="rounded-2xl border-2 border-black bg-slate-50 p-4">
                  <div className="flex items-center gap-3">
                    <IconHistory className="h-5 w-5" />
                    <div>
                      <p className="font-black uppercase">Latest approval decision</p>
                      <p className="text-sm text-slate-700">
                        {auditView.latestDecision
                          ? `${auditView.latestDecision.decision} at ${formatTimestamp(auditView.latestDecision.createdAt)}`
                          : 'No approval decision has been recorded yet.'}
                      </p>
                    </div>
                  </div>
                </div>

                <div className="rounded-2xl border-2 border-black bg-slate-50 p-4">
                  <div className="flex items-center gap-3">
                    <IconScale className="h-5 w-5" />
                    <div>
                      <p className="font-black uppercase">Decision note</p>
                      <p className="text-sm text-slate-700">
                        {auditView.latestDecision?.notes || 'No decision note available.'}
                      </p>
                    </div>
                  </div>
                </div>

                <div className="rounded-2xl border-2 border-black bg-slate-50 p-4">
                  <div className="flex items-center gap-3">
                    <IconShieldHalfFilled className="h-5 w-5" />
                    <div>
                      <p className="font-black uppercase">Frameworks referenced</p>
                      <p className="text-sm text-slate-700">
                        {auditView.frameworkNames.length > 0
                          ? auditView.frameworkNames.join(', ')
                          : 'No framework data available.'}
                      </p>
                    </div>
                  </div>
                </div>
              </div>
            </Card>

            <Card className="border-2 border-black p-6 shadow-brutal">
              <h2 className="text-2xl font-black uppercase">Traceability Summary</h2>
              <div className="mt-5 space-y-4">
                <div className="rounded-2xl border-2 border-black bg-white p-4">
                  <p className="text-xs font-bold uppercase text-muted-foreground">Evidence readiness</p>
                  <p className="mt-1 text-lg font-black uppercase">{evidenceSummary.decisionReadiness.replace(/_/g, ' ')}</p>
                </div>
                <div className="rounded-2xl border-2 border-black bg-white p-4">
                  <p className="text-xs font-bold uppercase text-muted-foreground">Missing signals</p>
                  <div className="mt-2 flex flex-wrap gap-2">
                    {evidenceSummary.missingSignals.length > 0 ? (
                      evidenceSummary.missingSignals.map((item) => (
                        <Badge key={item} variant="outline" className="border-2 border-black bg-slate-50 px-3 py-1 font-bold">
                          {item}
                        </Badge>
                      ))
                    ) : (
                      <span className="text-sm text-slate-700">No major missing evidence signals are currently flagged.</span>
                    )}
                  </div>
                </div>
                <div className="rounded-2xl border-2 border-black bg-white p-4">
                  <p className="text-xs font-bold uppercase text-muted-foreground">Open remediation tasks</p>
                  <p className="mt-1 text-lg font-black">{auditView.openRemediation.length}</p>
                </div>
              </div>
            </Card>
          </div>

          <div className="grid gap-6 xl:grid-cols-3">
            <Card className="border-2 border-black p-6 shadow-brutal">
              <div className="flex items-center gap-3">
                <IconGitBranch className="h-5 w-5" />
                <h2 className="text-2xl font-black uppercase">Top Risks</h2>
              </div>
              <div className="mt-5 space-y-3">
                {auditView.topRisks.length > 0 ? (
                  auditView.topRisks.map((risk) => (
                    <div key={risk.id} className="rounded-2xl border-2 border-black bg-slate-50 p-4">
                      <p className="font-black uppercase">{risk.title}</p>
                      <p className="mt-1 text-sm text-slate-700">{risk.description}</p>
                    </div>
                  ))
                ) : (
                  <p className="text-sm text-muted-foreground">No high or critical risks are currently visible.</p>
                )}
              </div>
            </Card>

            <Card className="border-2 border-black p-6 shadow-brutal">
              <div className="flex items-center gap-3">
                <IconFileText className="h-5 w-5" />
                <h2 className="text-2xl font-black uppercase">Linked Evidence</h2>
              </div>
              <div className="mt-5 space-y-3">
                {auditView.linkedEvidence.slice(0, 4).map((item: any) => (
                  <div key={item.id} className="rounded-2xl border-2 border-black bg-slate-50 p-4">
                    <p className="font-black uppercase">{item.type}</p>
                    <p className="mt-1 text-sm text-slate-700">
                      Captured {formatTimestamp(item.timestamp)} • {item.linkedEntityCount} linked entities
                    </p>
                  </div>
                ))}
                {auditView.linkedEvidence.length === 0 && (
                  <p className="text-sm text-muted-foreground">No linked evidence is available yet.</p>
                )}
              </div>
            </Card>

            <Card className="border-2 border-black p-6 shadow-brutal">
              <div className="flex items-center gap-3">
                <IconTool className="h-5 w-5" />
                <h2 className="text-2xl font-black uppercase">Remediation Trail</h2>
              </div>
              <div className="mt-5 space-y-3">
                {remediationTasks.slice(0, 4).map((task) => (
                  <div key={task.id} className="rounded-2xl border-2 border-black bg-slate-50 p-4">
                    <p className="font-black uppercase">{task.title}</p>
                    <p className="mt-1 text-sm text-slate-700">
                      {task.status.replace(/_/g, ' ')} • updated {formatTimestamp(task.updatedAt)}
                    </p>
                  </div>
                ))}
                {remediationTasks.length === 0 && (
                  <p className="text-sm text-muted-foreground">No remediation tasks are attached to this system yet.</p>
                )}
              </div>
            </Card>
          </div>

          <Card className="border-2 border-black p-6 shadow-brutal">
            <h2 className="text-2xl font-black uppercase">Export path</h2>
            <p className="mt-2 text-sm text-muted-foreground">
              FairMind can now show the approval chain, but export packaging is still a presentation-layer summary.
              The next step is generating an auditor-ready bundle from this same traceability graph.
            </p>
            <div className="mt-5 flex flex-col gap-3 sm:flex-row">
              <Button asChild variant="default">
                <Link href="/reports">
                  Return to release summary
                  <IconArrowRight className="ml-2 h-4 w-4" />
                </Link>
              </Button>
              <Button asChild variant="neutral" className="border-2 border-black font-bold">
                <Link href="/ai-governance">
                  Review governance gate
                  <IconArrowRight className="ml-2 h-4 w-4" />
                </Link>
              </Button>
            </div>
          </Card>
        </>
      )}
    </div>
  )
}
