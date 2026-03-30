'use client'

import { useEffect, useState } from 'react'
import {
  IconAlertHexagon,
  IconAlertTriangle,
  IconCheck,
  IconCircleCheck,
  IconClock,
  IconDatabase,
  IconLoader2,
  IconShieldCheck,
  IconShieldOff,
  IconX,
} from '@tabler/icons-react'

import { Sheet, SheetContent, SheetHeader, SheetTitle } from '@/components/ui/sheet'
import { Badge } from '@/components/ui/badge'
import { Progress } from '@/components/ui/progress'
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/ui/tabs'
import type { AISystem, GovernanceRisk, SystemApproval } from '@/lib/api/hooks/useModelInventory'
import { LifecycleStepper } from './LifecycleStepper'
import { RiskHeatmap } from './RiskHeatmap'

interface SystemDetailDrawerProps {
  system: AISystem | null
  open: boolean
  onClose: () => void
  onFetchRisks: (systemId: string) => Promise<{ risks: GovernanceRisk[]; summary: any }>
  onFetchApprovals: (systemId: string) => Promise<SystemApproval[]>
}

const RISK_SEVERITY_COLORS: Record<string, string> = {
  critical: 'border-red-600 bg-red-50 text-red-800',
  high: 'border-orange-500 bg-orange-50 text-orange-800',
  medium: 'border-amber-500 bg-amber-50 text-amber-800',
  low: 'border-emerald-500 bg-emerald-50 text-emerald-800',
}

function formatDate(ts: string) {
  if (!ts) return '—'
  const d = new Date(ts)
  return Number.isNaN(d.getTime()) ? ts : d.toLocaleDateString()
}

export function SystemDetailDrawer({
  system,
  open,
  onClose,
  onFetchRisks,
  onFetchApprovals,
}: SystemDetailDrawerProps) {
  const [risks, setRisks] = useState<GovernanceRisk[]>([])
  const [riskSummary, setRiskSummary] = useState<any>(null)
  const [approvals, setApprovals] = useState<SystemApproval[]>([])
  const [loadingRisks, setLoadingRisks] = useState(false)
  const [loadingApprovals, setLoadingApprovals] = useState(false)

  useEffect(() => {
    if (!system || !open) return
    setLoadingRisks(true)
    onFetchRisks(system.id)
      .then(({ risks: r, summary: s }) => { setRisks(r); setRiskSummary(s) })
      .catch(() => {})
      .finally(() => setLoadingRisks(false))

    setLoadingApprovals(true)
    onFetchApprovals(system.id)
      .then((a) => setApprovals(a))
      .catch(() => {})
      .finally(() => setLoadingApprovals(false))
  }, [system?.id, open])

  if (!system) return null

  const ls = system.lifecycleSummary

  const recommendationColor =
    ls.releaseRecommendation === 'Go' ? 'bg-emerald-600 text-white' :
    ls.releaseRecommendation === 'Conditional Go' ? 'bg-amber-400 text-black' :
    'bg-red-600 text-white'

  return (
    <Sheet open={open} onOpenChange={(o) => { if (!o) onClose() }}>
      <SheetContent className="w-full overflow-y-auto border-l-4 border-black sm:max-w-2xl">
        <SheetHeader className="border-b-2 border-black pb-4">
          <div className="space-y-3">
            <SheetTitle className="text-2xl font-black uppercase leading-tight">
              {system.name}
            </SheetTitle>
            <div className="flex flex-wrap items-center gap-2">
              <Badge className="border-2 border-black bg-black px-2 py-0.5 text-[11px] font-black uppercase text-white">
                {system.riskTier} risk
              </Badge>
              <Badge className="border-2 border-black bg-white px-2 py-0.5 text-[11px] font-bold uppercase">
                Owner: {system.owner || 'unassigned'}
              </Badge>
              <Badge
                className={`border-2 border-black px-3 py-1 text-[11px] font-black uppercase shadow-[2px_2px_0px_0px_#000] ${recommendationColor}`}
              >
                {ls.releaseRecommendation}
              </Badge>
            </div>
          </div>
        </SheetHeader>

        <div className="space-y-6 pt-5">
          {/* Lifecycle stepper */}
          <LifecycleStepper currentStage={system.lifecycleStage} readiness={system.readiness} />

          {/* KPI row */}
          <div className="grid grid-cols-2 gap-3 sm:grid-cols-4">
            {[
              { label: 'Open risks', value: ls.openRisks, warn: ls.openRisks > 0 },
              { label: 'Active remediation', value: ls.activeRemediation, warn: ls.activeRemediation > 0 },
              { label: 'Critical blockers', value: ls.criticalBlockers, warn: ls.criticalBlockers > 0 },
              { label: 'Missing evidence', value: ls.missingEvidence, warn: ls.missingEvidence > 0 },
            ].map(({ label, value, warn }) => (
              <div key={label} className={`rounded-xl border-2 border-black p-3 ${warn && value > 0 ? 'bg-red-50' : 'bg-white'}`}>
                <p className="text-[10px] font-bold uppercase text-muted-foreground">{label}</p>
                <p className={`mt-0.5 text-2xl font-black ${warn && value > 0 ? 'text-red-700' : ''}`}>{value}</p>
              </div>
            ))}
          </div>

          {/* Readiness bar */}
          <div className="space-y-1.5">
            <div className="flex justify-between text-xs font-bold uppercase text-muted-foreground">
              <span>Governance readiness</span>
              <span>{system.readiness}%</span>
            </div>
            <Progress value={system.readiness} className="h-3 border-2 border-black" />
          </div>

          <Tabs defaultValue="risks">
            <TabsList className="w-full border-2 border-black">
              <TabsTrigger value="risks" className="flex-1 font-bold uppercase">
                Risk register
              </TabsTrigger>
              <TabsTrigger value="decisions" className="flex-1 font-bold uppercase">
                Decision log
              </TabsTrigger>
              <TabsTrigger value="info" className="flex-1 font-bold uppercase">
                System info
              </TabsTrigger>
            </TabsList>

            {/* Risk register tab */}
            <TabsContent value="risks" className="mt-4 space-y-4">
              {loadingRisks ? (
                <div className="flex items-center justify-center py-10">
                  <IconLoader2 className="h-6 w-6 animate-spin" />
                </div>
              ) : (
                <>
                  {risks.length > 0 && <RiskHeatmap risks={risks} />}

                  {riskSummary && (
                    <div className="grid grid-cols-4 gap-2">
                      {(['critical', 'high', 'medium', 'low'] as const).map((sev) => (
                        <div key={sev} className={`rounded-lg border-2 border-black p-2 text-center ${RISK_SEVERITY_COLORS[sev]}`}>
                          <p className="text-[10px] font-bold uppercase">{sev}</p>
                          <p className="text-xl font-black">{riskSummary.bySeverity?.[sev] ?? 0}</p>
                        </div>
                      ))}
                    </div>
                  )}

                  {risks.length === 0 ? (
                    <div className="rounded-xl border-2 border-dashed border-black/30 bg-slate-50 p-8 text-center">
                      <IconShieldCheck className="mx-auto h-8 w-8 text-emerald-600" />
                      <p className="mt-2 font-bold text-emerald-700">No risks recorded</p>
                    </div>
                  ) : (
                    <div className="space-y-2">
                      {risks.map((risk) => (
                        <div key={risk.id} className={`rounded-xl border-2 p-3 ${RISK_SEVERITY_COLORS[risk.severity] || 'border-black bg-white'}`}>
                          <div className="flex items-start justify-between gap-2">
                            <div className="min-w-0 flex-1">
                              <div className="flex items-center gap-2">
                                <IconAlertHexagon className="h-3.5 w-3.5 shrink-0" />
                                <p className="font-bold leading-tight">{risk.title}</p>
                              </div>
                              {risk.description && (
                                <p className="mt-1 text-xs opacity-80">{risk.description}</p>
                              )}
                              {risk.mitigation && (
                                <p className="mt-1 text-xs font-medium">Mitigation: {risk.mitigation}</p>
                              )}
                            </div>
                            <Badge className="shrink-0 border-2 border-current bg-transparent px-2 py-0.5 text-[10px] font-black uppercase">
                              {risk.status}
                            </Badge>
                          </div>
                        </div>
                      ))}
                    </div>
                  )}
                </>
              )}
            </TabsContent>

            {/* Decision log tab */}
            <TabsContent value="decisions" className="mt-4 space-y-3">
              {loadingApprovals ? (
                <div className="flex items-center justify-center py-10">
                  <IconLoader2 className="h-6 w-6 animate-spin" />
                </div>
              ) : approvals.length === 0 ? (
                <div className="rounded-xl border-2 border-dashed border-black/30 bg-slate-50 p-8 text-center">
                  <IconClock className="mx-auto h-8 w-8 text-muted-foreground" />
                  <p className="mt-2 font-bold text-muted-foreground">No approval decisions yet</p>
                  <p className="mt-0.5 text-xs text-muted-foreground">
                    Governance decisions will appear here once approval reviews are completed.
                  </p>
                </div>
              ) : (
                <div className="space-y-3">
                  <p className="text-[10px] font-black uppercase tracking-[0.2em] text-muted-foreground">
                    Append-only governance decisions
                  </p>
                  {approvals.map((approval) => (
                    <div key={approval.id} className={`rounded-xl border-2 p-4 ${
                      approval.status === 'approved' ? 'border-emerald-500 bg-emerald-50' :
                      approval.status === 'rejected' ? 'border-red-500 bg-red-50' :
                      'border-black bg-white'
                    }`}>
                      <div className="flex items-start justify-between gap-3">
                        <div className="flex items-center gap-2">
                          {approval.status === 'approved' ? (
                            <IconCircleCheck className="h-5 w-5 text-emerald-600" />
                          ) : approval.status === 'rejected' ? (
                            <IconShieldOff className="h-5 w-5 text-red-600" />
                          ) : (
                            <IconClock className="h-5 w-5 text-muted-foreground" />
                          )}
                          <div>
                            <p className="font-black uppercase">{approval.status}</p>
                            {approval.requested_by && (
                              <p className="text-xs text-muted-foreground">Requested by: {approval.requested_by}</p>
                            )}
                          </div>
                        </div>
                        <span className="text-xs text-muted-foreground">{formatDate(approval.createdAt)}</span>
                      </div>
                      {approval.decision_notes && (
                        <p className="mt-2 text-sm">{approval.decision_notes}</p>
                      )}
                    </div>
                  ))}
                </div>
              )}
            </TabsContent>

            {/* System info tab */}
            <TabsContent value="info" className="mt-4">
              <div className="space-y-3">
                {[
                  { label: 'System ID', value: system.id },
                  { label: 'Workspace', value: system.workspaceId || '—' },
                  { label: 'Owner', value: system.owner || 'Unassigned' },
                  { label: 'Risk tier', value: system.riskTier },
                  { label: 'Lifecycle stage', value: system.lifecycleStage },
                  { label: 'Registered', value: formatDate(system.createdAt) },
                  { label: 'Last updated', value: formatDate(system.updatedAt) },
                ].map(({ label, value }) => (
                  <div key={label} className="flex items-start justify-between gap-3 rounded-lg border-2 border-black bg-white p-3">
                    <p className="text-xs font-bold uppercase text-muted-foreground">{label}</p>
                    <p className="text-right text-xs font-semibold font-mono">{value}</p>
                  </div>
                ))}
                {Object.entries(system.metadata || {}).map(([k, v]) => (
                  <div key={k} className="flex items-start justify-between gap-3 rounded-lg border-2 border-black/20 bg-slate-50 p-3">
                    <p className="text-xs font-bold uppercase text-muted-foreground">{k}</p>
                    <p className="text-right text-xs font-semibold">{String(v)}</p>
                  </div>
                ))}
              </div>
            </TabsContent>
          </Tabs>
        </div>
      </SheetContent>
    </Sheet>
  )
}
