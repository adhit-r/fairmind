'use client'

import Link from 'next/link'
import { useParams, useRouter } from 'next/navigation'
import { useMemo, useState, type ReactNode } from 'react'
import { useOrg } from '@/context/OrgContext'
import { useSystemContext } from '@/components/workflow/SystemContext'
import { useEnvironmentalImpact } from '@/lib/api/hooks/useAIGovernance'
import { useSystemFile, type SystemRecord } from '@/lib/api/hooks/useSystemFile'
import { cn } from '@/lib/utils'

type JourneyKey = 'onboard' | 'assess' | 'govern' | 'remediate' | 'decision' | 'operate'
type StageStatus = 'done' | 'current' | 'upcoming'

const JOURNEY: Array<{ key: JourneyKey; label: string; purpose: string }> = [
  { key: 'onboard', label: 'Onboard', purpose: 'The system exists in the record with an owner and a tier.' },
  { key: 'assess', label: 'Assess', purpose: 'Evaluations produce evidence about how the system behaves.' },
  { key: 'govern', label: 'Govern', purpose: 'Evidence is bound to framework controls until the record is review-ready.' },
  { key: 'remediate', label: 'Remediate', purpose: 'Open findings are closed before anyone is asked to decide.' },
  { key: 'decision', label: 'Decision', purpose: 'A release decision is requested and recorded against the evidence.' },
  { key: 'operate', label: 'Operate', purpose: 'The system runs, is watched, and its audit record stays current.' },
]

const READINESS_LABEL: Record<string, string> = {
  empty: 'No evidence yet',
  needs_evidence: 'Needs evidence',
  collected: 'Evidence collected, not yet linked',
  linked: 'Evidence linked to controls',
  review_ready: 'Review-ready',
}

function businessLine(m: Record<string, any> | undefined) {
  return (m?.business_line || m?.businessLine || m?.business_unit || m?.businessUnit || m?.department || '') as string
}

function when(iso?: string | null) {
  return iso ? new Date(iso).toLocaleDateString('en-GB', { day: 'numeric', month: 'short', year: 'numeric' }) : ''
}

function currentStage(system: SystemRecord, approvalStatus: string | null | undefined): JourneyKey {
  if (approvalStatus === 'pending') return 'decision'
  return system.lifecycleSummary?.stage ?? system.lifecycleStage
}

function Fact({ label, value }: { label: string; value: ReactNode }) {
  return (
    <div className="min-w-0">
      <div className="text-[11px] font-semibold uppercase tracking-[.08em] text-[var(--fm-ink3)]">{label}</div>
      <div className="mt-0.5 truncate text-[13.5px]">{value}</div>
    </div>
  )
}

function Action({ children, onClick, href, primary = true, disabled }: { children: ReactNode; onClick?: () => void; href?: string; primary?: boolean; disabled?: boolean }) {
  const cls = cn(
    'inline-flex h-9 items-center rounded-full px-4 text-[12.5px] font-semibold disabled:opacity-60',
    primary ? 'bg-[var(--fm-ink)] text-white' : 'border border-[var(--fm-line)] bg-white font-medium text-[var(--fm-ink2)] hover:border-[var(--fm-ink)] hover:text-[var(--fm-ink)]',
  )
  if (href && !onClick) return <Link href={href} className={cls}>{children}</Link>
  return <button type="button" onClick={onClick} disabled={disabled} className={cls}>{children}</button>
}

function Stage({ step, status, children, actions }: { step: (typeof JOURNEY)[number]; status: StageStatus; children: ReactNode; actions: ReactNode }) {
  return (
    <section
      aria-label={step.label}
      className={cn('fm-card grid gap-4 p-5 lg:grid-cols-[180px_minmax(0,1fr)_auto] lg:items-start', status === 'upcoming' && 'opacity-80')}
    >
      <div>
        <div className="flex items-center gap-2">
          <span
            className={cn(
              'inline-block h-2.5 w-2.5 rounded-full',
              status === 'done' && 'bg-[var(--fm-ink)]',
              status === 'current' && 'bg-[var(--fm-brand)]',
              status === 'upcoming' && 'border border-[var(--fm-ink3)] bg-transparent',
            )}
            aria-hidden="true"
          />
          <h2 className="text-[15px] font-semibold">{step.label}</h2>
        </div>
        <div className="mt-1 text-[11.5px] font-medium uppercase tracking-[.06em] text-[var(--fm-ink3)]">
          {status === 'done' ? 'Done' : status === 'current' ? 'Now' : 'Next'}
        </div>
        <p className="mt-2 text-[12.5px] leading-snug text-[var(--fm-ink2)]">{step.purpose}</p>
      </div>
      <div className="grid gap-3 sm:grid-cols-2 xl:grid-cols-3">{children}</div>
      <div className="flex flex-wrap gap-2 lg:flex-col lg:items-stretch">{actions}</div>
    </section>
  )
}

export default function SystemFilePage() {
  const { id } = useParams<{ id: string }>()
  const router = useRouter()
  const { selectedOrg } = useOrg()
  const { setSelectedSystemId } = useSystemContext()
  const { system, evidence, approval, remediation, risks, reports, loading, error, requestDecision, recordDecision } = useSystemFile(id)
  const env = useEnvironmentalImpact(selectedOrg?.id, id)
  const [busy, setBusy] = useState<string | null>(null)
  const [actionError, setActionError] = useState<string | null>(null)

  const open = (href: string) => {
    if (id) setSelectedSystemId(id)
    router.push(href)
  }

  const act = async (key: string, fn: () => Promise<void>) => {
    setBusy(key)
    setActionError(null)
    try {
      await fn()
    } catch (e) {
      setActionError(e instanceof Error ? e.message : 'Action failed')
    } finally {
      setBusy(null)
    }
  }

  const current = useMemo(() => (system ? currentStage(system, approval?.request?.status) : 'onboard'), [system, approval])
  const currentIdx = JOURNEY.findIndex((s) => s.key === current)
  const statusOf = (key: JourneyKey): StageStatus => {
    const idx = JOURNEY.findIndex((s) => s.key === key)
    if (key === 'remediate' && idx < currentIdx && recordedOpen.length === 0 && (remediation?.summary.activeTasks ?? 0) === 0) return 'done'
    return idx < currentIdx ? 'done' : idx === currentIdx ? 'current' : 'upcoming'
  }

  if (!loading && (error || !system)) {
    return (
      <div className="mx-auto max-w-[720px]">
        <div className="text-[12.5px] font-medium text-[var(--fm-ink2)]"><Link href="/dashboard" className="hover:text-[var(--fm-ink)]">Today</Link> · System</div>
        <h1 className="mt-1.5 text-[30px] font-semibold tracking-[-.03em]">This system is not in your estate</h1>
        <p className="mt-2 text-[15px] text-[var(--fm-ink2)]">{error || 'It may belong to another organisation or have been removed.'}</p>
        <Link href="/dashboard" className="mt-5 inline-flex h-10 items-center rounded-full bg-[var(--fm-ink)] px-5 text-[13px] font-semibold text-white">Back to the estate</Link>
      </div>
    )
  }

  const s = system
  const summary = s?.lifecycleSummary
  const line = businessLine(s?.metadata)
  const source = (s?.metadata?.source as string | undefined) || 'manual'
  // The risk dashboard mixes stored findings with suggestions generated from
  // risk taxonomies (source mit or ibm). Only stored findings are this system's.
  const recorded = (risks?.risks ?? []).filter((r) => !['mit', 'ibm'].includes(String(r.source ?? '')))
  const recordedOpen = recorded.filter((r) => r.status !== 'accepted')
  const recordedSevere = recordedOpen.filter((r) => r.severity === 'high' || r.severity === 'critical')
  const suggested = (risks?.risks.length ?? 0) - recorded.length
  const req = approval?.request ?? null
  const decided = req && req.status !== 'pending' ? req : null
  const latestReport = reports[0]
  const envStatus = typeof env.data?.recommendation === 'string' ? env.data.recommendation : env.data?.recommendation?.status

  return (
    <div className="grid gap-4">
      <div className="text-[12.5px] font-medium text-[var(--fm-ink2)]">
        <Link href="/dashboard" className="hover:text-[var(--fm-ink)]">Today</Link> · {line || 'Unassigned'} · System file
      </div>

      <header className="fm-card grid gap-5 p-6 lg:grid-cols-[minmax(0,1fr)_auto] lg:items-end">
        <div className="min-w-0">
          <h1 className="truncate text-[30px] font-semibold leading-[1.1] tracking-[-.03em] lg:text-[34px]">{loading && !s ? 'Loading' : s?.name}</h1>
          <div className="mt-3 grid gap-x-8 gap-y-3 sm:grid-cols-2 lg:grid-cols-4">
            <Fact label="Owner" value={s?.owner || 'Unassigned'} />
            <Fact label="Business line" value={line || 'Unassigned'} />
            <Fact label="Risk tier" value={<span className="capitalize">{s?.riskTier ?? ''}</span>} />
            <Fact label="Source" value={source === 'mlflow' ? 'MLflow registry' : source === 'github' ? 'GitHub' : 'Registered manually'} />
          </div>
        </div>
        <div className="flex items-end gap-6">
          <div>
            <div className="text-[11px] font-semibold uppercase tracking-[.08em] text-[var(--fm-ink3)]">Stage</div>
            <div className="mt-0.5 text-[20px] font-semibold">{JOURNEY.find((j) => j.key === current)?.label}</div>
          </div>
          <div>
            <div className="text-[11px] font-semibold uppercase tracking-[.08em] text-[var(--fm-ink3)]">Readiness</div>
            <div className="mt-0.5 text-[20px] font-semibold tabular-nums">{summary ? `${summary.readiness}%` : ''}</div>
            <div className="max-w-[220px] text-[11.5px] leading-snug text-[var(--fm-ink3)]">From stage, linked evidence, open risks and active remediation.</div>
          </div>
        </div>
      </header>

      {actionError && <p className="rounded-[10px] bg-[#fde9ea] px-3 py-2 text-[13px] text-[#b4232c]">{actionError}</p>}

      <Stage step={JOURNEY[0]} status={statusOf('onboard')} actions={<>
        <Action onClick={() => open('/tests')}>Run the first evaluation</Action>
        <Action href="/integrations" primary={false}>Connect sources</Action>
      </>}>
        <Fact label="Registered" value={when(s?.createdAt) || ''} />
        <Fact label="Workspace" value={s?.workspaceId ? 'Assigned' : 'None'} />
        <Fact label="Record" value={s?.owner && line ? 'Owner and business line set' : 'Owner or business line missing'} />
      </Stage>

      <Stage step={JOURNEY[1]} status={statusOf('assess')} actions={<>
        <Action onClick={() => open('/tests')}>Run an evaluation</Action>
        <Action onClick={() => open('/bias')} primary={false}>Bias test</Action>
        <Action onClick={() => open('/ai-governance')} primary={false}>Environmental</Action>
      </>}>
        <Fact label="Environmental" value={env.loading ? 'Checking' : env.data ? `Assessed${envStatus ? `, ${String(envStatus).replace(/_/g, ' ')}` : ''}${env.data.generatedAt ? ` on ${when(env.data.generatedAt)}` : ''}` : 'No assessment yet'} />
        <Fact label="Evaluation runs" value={<span className="text-[var(--fm-ink2)]">Listed in the test workspace</span>} />
        <Fact label="Evidence produced" value={evidence ? `${evidence.totalEvidence} item${evidence.totalEvidence === 1 ? '' : 's'}` : ''} />
      </Stage>

      <Stage step={JOURNEY[2]} status={statusOf('govern')} actions={<>
        <Action onClick={() => open('/evidence')}>Record evidence</Action>
        <Action onClick={() => open('/compliance')} primary={false}>Frameworks</Action>
      </>}>
        <Fact label="Evidence" value={evidence ? `${evidence.linkedEvidence} of ${evidence.totalEvidence} linked to controls` : ''} />
        <Fact label="Review state" value={evidence ? READINESS_LABEL[evidence.decisionReadiness] ?? evidence.decisionReadiness : ''} />
        <Fact label="Missing" value={evidence && evidence.missingSignals.length ? evidence.missingSignals.join(', ') : 'Nothing flagged'} />
        {evidence?.recommendedNextStep && (
          <p className="text-[12.5px] text-[var(--fm-ink2)] sm:col-span-2 xl:col-span-3">{evidence.recommendedNextStep}</p>
        )}
      </Stage>

      <Stage step={JOURNEY[3]} status={statusOf('remediate')} actions={<>
        <Action onClick={() => open('/risks')}>Open findings</Action>
        <Action onClick={() => open('/remediation')} primary={false}>Remediation tasks</Action>
      </>}>
        <Fact label="Open findings" value={risks ? `${recordedOpen.length} recorded${suggested ? `, ${suggested} suggested by taxonomy` : ''}` : ''} />
        <Fact label="High or critical" value={risks ? `${recordedSevere.length}` : ''} />
        <Fact label="Active tasks" value={remediation ? `${remediation.summary.activeTasks}` : ''} />
      </Stage>

      <Stage step={JOURNEY[4]} status={statusOf('decision')} actions={<>
        {!req || decided?.status === 'rejected' ? (
          <Action onClick={() => act('request', requestDecision)} disabled={busy === 'request'}>
            {busy === 'request' ? 'Requesting' : 'Request release decision'}
          </Action>
        ) : req.status === 'pending' ? (
          <>
            <Action onClick={() => act('approve', () => recordDecision(req.id, 'approved'))} disabled={busy !== null}>Approve release</Action>
            <Action onClick={() => act('reject', () => recordDecision(req.id, 'rejected'))} disabled={busy !== null} primary={false}>Reject</Action>
          </>
        ) : (
          <Action onClick={() => open('/audit-reports')} primary={false}>Release report</Action>
        )}
      </>}>
        <Fact label="Request" value={!req ? 'Not requested' : req.status === 'pending' ? `Pending since ${when(req.createdAt)}` : `${req.status[0].toUpperCase()}${req.status.slice(1)}${req.updatedAt ? ` on ${when(req.updatedAt)}` : ''}`} />
        <Fact label="Decisions recorded" value={approval ? `${approval.decisions.length}` : ''} />
        <Fact label="Blocking" value={summary ? (summary.criticalBlockers ? `${summary.criticalBlockers} critical blocker${summary.criticalBlockers === 1 ? '' : 's'}` : 'Nothing blocking') : ''} />
        {req?.decisionNotes && <p className="text-[12.5px] text-[var(--fm-ink2)] sm:col-span-2 xl:col-span-3">{req.decisionNotes}</p>}
      </Stage>

      <Stage step={JOURNEY[5]} status={statusOf('operate')} actions={<>
        <Action onClick={() => open('/audit-reports')}>Generate audit report</Action>
        <Action onClick={() => open('/monitoring')} primary={false}>Monitoring</Action>
      </>}>
        <Fact label="Audit reports" value={reports.length ? `${reports.length}, latest ${when(latestReport.createdAt)}` : 'None generated'} />
        <Fact label="Live metrics" value={<span className="text-[var(--fm-ink2)]">Coming soon</span>} />
        <Fact label="Approved" value={decided?.status === 'approved' ? when(decided.updatedAt) || 'Yes' : 'Not yet'} />
      </Stage>
    </div>
  )
}
