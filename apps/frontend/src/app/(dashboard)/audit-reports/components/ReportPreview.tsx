'use client'

import {
  IconAlertHexagon,
  IconCircleCheck,
  IconClock,
  IconFileText,
  IconShieldCheck,
  IconTool,
} from '@tabler/icons-react'
import { Badge } from '@/components/ui/badge'
import { Progress } from '@/components/ui/progress'

interface ReportData {
  system?: {
    name: string
    owner: string
    riskTier: string
    lifecycleStage: string
    readiness: number
  }
  risks?: Array<{
    id: string
    title: string
    severity: string
    status: string
    description: string
    mitigation: string
  }>
  evidence?: Array<{
    id: string
    type: string
    title: string
    status: string
    confidence: number
  }>
  remediation?: Array<{
    id: string
    title: string
    status: string
    priority: string
    owner: string
  }>
  approvals?: Array<{
    id: string
    status: string
    requestedBy: string
    decisionNotes: string
    createdAt: string
  }>
  generatedAt?: string
}

interface ReportPreviewProps {
  reportType: string
  system: ReportData['system']
  data: ReportData
  sections: string[]
  frameworks: string[]
}

const SEVERITY_COLORS: Record<string, string> = {
  critical: 'border-red-600 bg-red-50 text-red-800',
  high: 'border-orange-500 bg-orange-50 text-orange-800',
  medium: 'border-amber-500 bg-amber-50 text-amber-800',
  low: 'border-emerald-500 bg-emerald-50 text-emerald-800',
}

function formatDate(ts?: string) {
  if (!ts) return '—'
  const d = new Date(ts)
  return Number.isNaN(d.getTime()) ? ts : d.toLocaleDateString()
}

export function ReportPreview({ reportType, system, data, sections, frameworks }: ReportPreviewProps) {
  const risks = data.risks ?? []
  const evidence = data.evidence ?? []
  const remediation = data.remediation ?? []
  const approvals = data.approvals ?? []

  const criticalRisks = risks.filter((r) => r.severity === 'critical').length
  const highRisks = risks.filter((r) => r.severity === 'high').length
  const openRemediation = remediation.filter((t) => t.status !== 'done').length
  const latestApproval = approvals[0]

  const showSection = (key: string) => sections.length === 0 || sections.includes(key)

  return (
    <div className="space-y-6 rounded-2xl border-4 border-black bg-white p-6 font-mono shadow-[6px_6px_0px_0px_#000]">
      {/* Report header */}
      <div className="border-b-4 border-black pb-4">
        <div className="flex flex-wrap items-start justify-between gap-2">
          <div>
            <p className="text-[10px] font-black uppercase tracking-[0.25em] text-muted-foreground">
              {reportType === 'compliance'
                ? 'Compliance Audit Report'
                : reportType === 'bias'
                ? 'Bias Assessment Report'
                : 'Governance Summary Report'}
            </p>
            <h2 className="mt-1 text-2xl font-black uppercase">{system?.name ?? 'AI System'}</h2>
            <p className="text-xs text-muted-foreground">
              Owner: {system?.owner || 'Unassigned'} · Risk tier: {system?.riskTier} · Stage:{' '}
              {system?.lifecycleStage}
            </p>
          </div>
          <div className="text-right text-xs text-muted-foreground">
            <p>Generated {formatDate(data.generatedAt)}</p>
            {frameworks.length > 0 && (
              <p className="mt-0.5">Frameworks: {frameworks.join(', ')}</p>
            )}
          </div>
        </div>
      </div>

      {/* Executive summary */}
      {showSection('executive_summary') && (
        <section>
          <h3 className="text-sm font-black uppercase tracking-widest text-muted-foreground">
            Executive Summary
          </h3>
          <div className="mt-3 grid grid-cols-2 gap-3 sm:grid-cols-4">
            {[
              { label: 'Readiness', value: `${system?.readiness ?? 0}%`, sub: 'governance' },
              { label: 'Open risks', value: risks.filter((r) => r.status !== 'resolved').length, warn: true },
              { label: 'Critical', value: criticalRisks, warn: criticalRisks > 0 },
              { label: 'Evidence', value: evidence.length, warn: false },
            ].map(({ label, value, warn, sub }) => (
              <div
                key={label}
                className={`rounded-lg border-2 border-black p-3 text-center ${warn && Number(value) > 0 ? 'bg-red-50' : 'bg-slate-50'}`}
              >
                <p className="text-[10px] font-bold uppercase text-muted-foreground">{label}</p>
                {sub && <p className="text-[9px] text-muted-foreground">{sub}</p>}
                <p className={`text-2xl font-black ${warn && Number(value) > 0 ? 'text-red-700' : ''}`}>
                  {value}
                </p>
              </div>
            ))}
          </div>
          {system && (
            <div className="mt-3 space-y-1">
              <div className="flex justify-between text-xs font-bold uppercase text-muted-foreground">
                <span>Governance readiness</span>
                <span>{system.readiness}%</span>
              </div>
              <Progress value={system.readiness} className="h-2 border border-black" />
            </div>
          )}
        </section>
      )}

      {/* Risk overview */}
      {showSection('risk_overview') && risks.length > 0 && (
        <section>
          <h3 className="text-sm font-black uppercase tracking-widest text-muted-foreground">
            Risk Overview
          </h3>
          <div className="mt-3 space-y-2">
            {risks.slice(0, 6).map((risk) => (
              <div
                key={risk.id}
                className={`flex items-start justify-between gap-2 rounded-lg border-2 p-3 ${SEVERITY_COLORS[risk.severity] || 'border-black bg-white'}`}
              >
                <div className="min-w-0 flex-1">
                  <div className="flex items-center gap-1.5">
                    <IconAlertHexagon className="h-3.5 w-3.5 shrink-0" />
                    <p className="text-sm font-bold leading-tight">{risk.title}</p>
                  </div>
                  {risk.description && (
                    <p className="mt-0.5 text-xs opacity-80">{risk.description}</p>
                  )}
                </div>
                <Badge className="shrink-0 border border-current bg-transparent px-2 py-0.5 text-[10px] font-black uppercase">
                  {risk.status}
                </Badge>
              </div>
            ))}
            {risks.length > 6 && (
              <p className="text-xs text-muted-foreground">+{risks.length - 6} more risks not shown</p>
            )}
          </div>
        </section>
      )}

      {/* Compliance status */}
      {showSection('compliance_status') && frameworks.length > 0 && (
        <section>
          <h3 className="text-sm font-black uppercase tracking-widest text-muted-foreground">
            Compliance Status
          </h3>
          <div className="mt-3 flex flex-wrap gap-2">
            {frameworks.map((fw) => (
              <div key={fw} className="rounded-lg border-2 border-black bg-slate-50 px-4 py-2">
                <p className="text-xs font-black uppercase">{fw}</p>
                <p className="text-[10px] text-muted-foreground">Referenced</p>
              </div>
            ))}
          </div>
        </section>
      )}

      {/* Evidence summary */}
      {showSection('evidence_summary') && (
        <section>
          <h3 className="text-sm font-black uppercase tracking-widest text-muted-foreground">
            Evidence Summary
          </h3>
          {evidence.length === 0 ? (
            <p className="mt-2 text-xs text-muted-foreground">No evidence records found.</p>
          ) : (
            <div className="mt-3 space-y-1.5">
              {evidence.slice(0, 5).map((item) => (
                <div
                  key={item.id}
                  className="flex items-center justify-between rounded-lg border border-black/20 bg-slate-50 px-3 py-2"
                >
                  <div className="flex items-center gap-2">
                    <IconFileText className="h-3.5 w-3.5 text-muted-foreground" />
                    <p className="text-xs font-semibold">{item.title || item.type}</p>
                  </div>
                  <div className="flex items-center gap-2">
                    <span className="text-[10px] text-muted-foreground">
                      {item.confidence}% confidence
                    </span>
                    <Badge variant="outline" className="border border-black text-[10px]">
                      {item.status}
                    </Badge>
                  </div>
                </div>
              ))}
              {evidence.length > 5 && (
                <p className="text-xs text-muted-foreground">+{evidence.length - 5} more items</p>
              )}
            </div>
          )}
        </section>
      )}

      {/* Open remediations */}
      {showSection('remediations') && (
        <section>
          <h3 className="text-sm font-black uppercase tracking-widest text-muted-foreground">
            Open Remediations ({openRemediation})
          </h3>
          {openRemediation === 0 ? (
            <div className="mt-2 flex items-center gap-2 text-emerald-700">
              <IconShieldCheck className="h-4 w-4" />
              <p className="text-xs font-bold">All remediation tasks are resolved.</p>
            </div>
          ) : (
            <div className="mt-3 space-y-1.5">
              {remediation
                .filter((t) => t.status !== 'done')
                .slice(0, 5)
                .map((task) => (
                  <div
                    key={task.id}
                    className="flex items-center justify-between rounded-lg border border-black/20 bg-amber-50 px-3 py-2"
                  >
                    <div className="flex items-center gap-2">
                      <IconTool className="h-3.5 w-3.5 text-amber-700" />
                      <p className="text-xs font-semibold">{task.title}</p>
                    </div>
                    <Badge variant="outline" className="border border-amber-500 text-[10px] text-amber-800">
                      {task.priority}
                    </Badge>
                  </div>
                ))}
            </div>
          )}
        </section>
      )}

      {/* Approval decision log */}
      {showSection('decision_log') && (
        <section>
          <h3 className="text-sm font-black uppercase tracking-widest text-muted-foreground">
            Latest Approval Decision
          </h3>
          {!latestApproval ? (
            <div className="mt-2 flex items-center gap-2 text-muted-foreground">
              <IconClock className="h-4 w-4" />
              <p className="text-xs">No approval decisions recorded.</p>
            </div>
          ) : (
            <div
              className={`mt-3 rounded-lg border-2 p-3 ${
                latestApproval.status === 'approved'
                  ? 'border-emerald-500 bg-emerald-50'
                  : latestApproval.status === 'rejected'
                  ? 'border-red-500 bg-red-50'
                  : 'border-black bg-slate-50'
              }`}
            >
              <div className="flex items-center gap-2">
                {latestApproval.status === 'approved' ? (
                  <IconCircleCheck className="h-4 w-4 text-emerald-600" />
                ) : (
                  <IconClock className="h-4 w-4 text-muted-foreground" />
                )}
                <p className="text-sm font-black uppercase">{latestApproval.status}</p>
                <span className="ml-auto text-xs text-muted-foreground">
                  {formatDate(latestApproval.createdAt)}
                </span>
              </div>
              {latestApproval.decisionNotes && (
                <p className="mt-1.5 text-xs">{latestApproval.decisionNotes}</p>
              )}
            </div>
          )}
        </section>
      )}
    </div>
  )
}
