'use client'

import type { ReactNode } from 'react'
import { LABEL, MUTED, Pill, cap } from '@/components/packs/parts'

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

const SEVERITY_TONE: Record<string, 'block' | 'warn' | 'plain'> = { critical: 'block', high: 'warn' }
const APPROVAL_TONE: Record<string, 'done' | 'block'> = { approved: 'done', rejected: 'block' }
const row = 'flex items-start justify-between gap-2 border-t border-[var(--fm-line)] py-2.5'

function formatDate(ts?: string) {
  if (!ts) return 'date not recorded'
  const d = new Date(ts)
  return Number.isNaN(d.getTime()) ? ts : d.toLocaleDateString()
}

function Section({ title, children }: { title: string; children: ReactNode }) {
  return (
    <section>
      <h3 className={LABEL}>{title}</h3>
      <div className="mt-2">{children}</div>
    </section>
  )
}

const None = ({ children }: { children: ReactNode }) => <p className={`text-[12.5px] ${MUTED}`}>{children}</p>

export function ReportPreview({ reportType, system, data, sections, frameworks }: ReportPreviewProps) {
  // A list the snapshot did not capture is unknown, not empty, so its counts read "Not recorded" instead of 0.
  const risks = Array.isArray(data.risks) ? data.risks : null
  const evidence = Array.isArray(data.evidence) ? data.evidence : null
  const remediation = data.remediation ?? []
  const approvals = data.approvals ?? []

  const openRemediation = remediation.filter((t) => t.status !== 'done')
  const latestApproval = approvals[0]
  const readiness = typeof system?.readiness === 'number' ? system.readiness : null

  const showSection = (key: string) => sections.length === 0 || sections.includes(key)

  return (
    <div className="grid gap-5 rounded-[12px] border border-[var(--fm-line)] bg-white p-5">
      <div className="flex flex-wrap items-start justify-between gap-2 border-b border-[var(--fm-line)] pb-4">
        <div>
          <p className={LABEL}>
            {reportType === 'compliance'
              ? 'Compliance Audit Report'
              : reportType === 'bias'
              ? 'Bias Assessment Report'
              : 'Governance Summary Report'}
          </p>
          <h2 className="mt-1 text-[20px] font-semibold tracking-[-.02em]">{system?.name ?? 'AI System'}</h2>
          <p className={`text-[12.5px] ${MUTED}`}>
            {[
              `Owner: ${system?.owner || 'Unassigned'}`,
              system?.riskTier && `Risk tier: ${system.riskTier}`,
              system?.lifecycleStage && `Stage: ${system.lifecycleStage}`,
            ].filter(Boolean).join(' · ')}
          </p>
        </div>
        <div className={`text-right text-[12px] ${MUTED}`}>
          <p>Generated {formatDate(data.generatedAt)}</p>
          {frameworks.length > 0 && <p className="mt-0.5">Frameworks: {frameworks.join(', ')}</p>}
        </div>
      </div>

      {showSection('executive_summary') && (
        <Section title="Executive Summary">
          <dl className="grid grid-cols-2 gap-x-6 gap-y-3 sm:grid-cols-4">
            {[
              { label: 'Readiness', value: readiness === null ? 'Not recorded' : `${readiness}%` },
              { label: 'Open risks', value: risks ? risks.filter((r) => r.status !== 'resolved').length : 'Not recorded' },
              { label: 'Critical', value: risks ? risks.filter((r) => r.severity === 'critical').length : 'Not recorded' },
              { label: 'Evidence', value: evidence ? evidence.length : 'Not recorded' },
            ].map(({ label, value }) => (
              <div key={label}>
                <dt className={`text-[12px] ${MUTED}`}>{label}</dt>
                <dd className="mt-0.5 text-[18px] font-semibold tabular-nums">{value}</dd>
              </div>
            ))}
          </dl>
          {readiness !== null && (
            <div
              role="progressbar"
              aria-label="Governance readiness"
              aria-valuemin={0}
              aria-valuemax={100}
              aria-valuenow={readiness}
              className="mt-3 h-1.5 overflow-hidden rounded-full bg-[rgba(21,23,26,.08)]"
            >
              <div className="h-full rounded-full bg-[var(--fm-ink)]" style={{ width: `${Math.min(100, Math.max(0, readiness))}%` }} />
            </div>
          )}
        </Section>
      )}

      {showSection('risk_overview') && risks && risks.length > 0 && (
        <Section title="Risk Overview">
          {risks.slice(0, 6).map((risk) => (
            <div key={risk.id} className={row}>
              <div className="min-w-0 flex-1">
                <div className="flex flex-wrap items-center gap-2">
                  <p className="text-[13px] font-semibold">{risk.title}</p>
                  <Pill tone={SEVERITY_TONE[risk.severity] ?? 'plain'}>{cap(risk.severity)}</Pill>
                </div>
                {risk.description && <p className={`mt-0.5 text-[12px] ${MUTED}`}>{risk.description}</p>}
              </div>
              <Pill>{cap(risk.status)}</Pill>
            </div>
          ))}
          {risks.length > 6 && <None>{risks.length - 6} more risks not shown</None>}
        </Section>
      )}

      {showSection('compliance_status') && frameworks.length > 0 && (
        <Section title="Compliance Status">
          <div className="flex flex-wrap gap-2">
            {frameworks.map((fw) => <Pill key={fw}>{fw} · referenced</Pill>)}
          </div>
        </Section>
      )}

      {showSection('evidence_summary') && (
        <Section title="Evidence Summary">
          {!evidence || evidence.length === 0 ? (
            <None>No evidence records found.</None>
          ) : (
            <>
              {evidence.slice(0, 5).map((item) => (
                <div key={item.id} className={row}>
                  <p className="text-[13px] font-semibold">{item.title || item.type}</p>
                  <div className="flex items-center gap-2">
                    {typeof item.confidence === 'number' && (
                      <span className={`text-[12px] ${MUTED}`}>{item.confidence}% confidence</span>
                    )}
                    <Pill>{cap(item.status)}</Pill>
                  </div>
                </div>
              ))}
              {evidence.length > 5 && <None>{evidence.length - 5} more items</None>}
            </>
          )}
        </Section>
      )}

      {showSection('remediations') && (
        <Section title={`Open Remediations (${openRemediation.length})`}>
          {remediation.length === 0 ? (
            <None>No remediation items were recorded in this snapshot.</None>
          ) : openRemediation.length === 0 ? (
            <None>All {remediation.length} remediation tasks in this snapshot are resolved.</None>
          ) : (
            openRemediation.slice(0, 5).map((task) => (
              <div key={task.id} className={row}>
                <p className="text-[13px] font-semibold">{task.title}</p>
                <Pill>{cap(task.priority)}</Pill>
              </div>
            ))
          )}
        </Section>
      )}

      {showSection('decision_log') && (
        <Section title="Latest Approval Decision">
          {!latestApproval ? (
            <None>No approval decisions recorded.</None>
          ) : (
            <div className="border-t border-[var(--fm-line)] py-2.5">
              <div className="flex items-center gap-2">
                <Pill tone={APPROVAL_TONE[latestApproval.status] ?? 'plain'}>{cap(latestApproval.status)}</Pill>
                <span className={`ml-auto text-[12px] ${MUTED}`}>{formatDate(latestApproval.createdAt)}</span>
              </div>
              {latestApproval.decisionNotes && <p className="mt-1.5 text-[12.5px]">{latestApproval.decisionNotes}</p>}
            </div>
          )}
        </Section>
      )}
    </div>
  )
}
