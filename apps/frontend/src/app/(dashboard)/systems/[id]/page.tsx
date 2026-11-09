'use client'

import Link from 'next/link'
import { useParams, useRouter } from 'next/navigation'
import { cloneElement, isValidElement, useEffect, useMemo, useState, type ReactNode } from 'react'
import { useOrg } from '@/context/OrgContext'
import { useSystemContext } from '@/components/workflow/SystemContext'
import { ApplicabilityForm } from '@/components/workflow/ApplicabilityForm'
import { Pill, cap } from '@/components/packs/parts'
import { shortFrameworkName, tierBasis, useApplicability } from '@/lib/api/hooks/useApplicability'
import { useEnvironmentalImpact } from '@/lib/api/hooks/useAIGovernance'
import { systemFileScopeKey, useSystemFile, type AttestableCheck, type FairnessRunSummary, type SystemRecord } from '@/lib/api/hooks/useSystemFile'
import { FairnessRunPanel } from './FairnessRunPanel'
import { MonitoringRunPanel } from './MonitoringRunPanel'
import { WatchPanel } from './WatchPanel'
import { AttestForm } from './AttestForm'
import { ConditionsForm } from './ConditionsForm'
import { RequirementsTab } from './RequirementsTab'
import { RecordTab } from './RecordTab'
import { LeavesOpen } from './LeavesOpen'
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/ui/tabs'
import { checkCell } from '@/components/ui/matrix'
import { VERDICT_LABEL, VERDICT_TONE, VerdictExplainer, tierOverride } from './VerdictExplainer'
import { TargetPanel } from './TargetPanel'
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

// Environmental is left out: an attestation would shadow any later assessment, which the path recommends instead.
const ATTESTABLE = new Set<string>(['data_governance', 'human_oversight', 'monitoring'])
const isAttestable = (key: string): key is AttestableCheck => ATTESTABLE.has(key)

const CHECK_NAMES: Record<string, string> = { disparate_impact: 'impact ratio', equal_opportunity: 'equal opportunity', equalized_odds: 'equalized odds', calibration: 'calibration' }

/**
 * "Within thresholds, gender 0.95, region 0.91", "Checks pass; outside thresholds but not statistically significant:
 * gender impact ratio" or "Outside thresholds: gender calibration, region equalized odds".
 */
function fairnessSummary(run: FairnessRunSummary): string {
  const noisy = run.attributes.flatMap((a) => (a.passedOnSignificance ?? []).map((k) => `${a.attribute} ${CHECK_NAMES[k] ?? k.replace(/_/g, ' ')}`))
  if (run.allChecksPass && noisy.length) return `Checks pass; outside thresholds but not statistically significant: ${noisy.join(', ')}`
  if (run.allChecksPass) return `Within thresholds, ${run.attributes.map((a) => `${a.attribute} ${a.disparateImpactRatio.toFixed(2)}`).join(', ')}`
  const failing = run.attributes.flatMap((a) => Object.entries(a.checks).filter(([, ok]) => !ok).map(([k]) => `${a.attribute} ${CHECK_NAMES[k] ?? k.replace(/_/g, ' ')}`))
  return failing.length ? `Outside thresholds: ${failing.join(', ')}` : 'Outside thresholds'
}

const CHECK_STATE: Record<string, string> = { proven: 'proven', attested: 'attested', open: 'open' }
const TAB_LIST = 'h-auto rounded-full border border-[var(--fm-line)] bg-white p-0.5 text-[var(--fm-ink2)]'
const TAB = 'h-7 rounded-full px-3 text-[12.5px] font-medium text-[var(--fm-ink2)] hover:text-[var(--fm-ink)] data-[state=active]:bg-[var(--fm-ink)] data-[state=active]:text-white data-[state=active]:shadow-none'
const SOURCE: Record<string, string> = { mlflow: 'MLflow registry', github: 'GitHub', manual: 'Registered manually' }

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
  if (value === '' || value == null) return null
  return (
    <div className="min-w-0">
      <div className="text-[11px] font-semibold uppercase tracking-[.08em] text-[var(--fm-ink3)]">{label}</div>
      <div className="mt-0.5 truncate text-[13.5px]">{value}</div>
    </div>
  )
}

function Action({ children, onClick, href, primary = true, disabled, expanded, small }: { children: ReactNode; onClick?: () => void; href?: string; primary?: boolean; disabled?: boolean; expanded?: boolean; small?: boolean }) {
  const cls = cn(
    'inline-flex shrink-0 items-center rounded-full font-semibold disabled:opacity-60',
    small ? 'h-7 px-3 text-[12px]' : 'h-9 px-4 text-[12.5px]',
    primary ? 'bg-[var(--fm-ink)] text-white' : 'border border-[var(--fm-line)] bg-white font-medium text-[var(--fm-ink2)] hover:border-[var(--fm-ink)] hover:text-[var(--fm-ink)]',
  )
  if (href && !onClick) return <Link href={href} className={cls}>{children}</Link>
  return <button type="button" onClick={onClick} disabled={disabled} aria-expanded={expanded} className={cls}>{children}</button>
}

/**
 * One stage of the Journey card: a 44px row (number, name, one short status, its primary action as a small pill)
 * that expands to the stage's content. Collapsed content stays mounted, so an open form survives a collapse.
 * Only the current stage's pill is ink; the other collapsed rows carry theirs as secondary pills.
 */
function Stage({ step, status, note, pill, expanded, onToggle, children, primary, actions }: { step: (typeof JOURNEY)[number]; status: StageStatus; note?: string; pill?: ReactNode; expanded: boolean; onToggle: () => void; children: ReactNode; primary?: ReactNode; actions?: ReactNode }) {
  const n = JOURNEY.indexOf(step) + 1
  return (
    <section id={step.key} data-stage={step.key} aria-label={step.label} className="scroll-mt-4">
      <div className="flex min-h-11 flex-wrap items-center gap-x-3 gap-y-1.5 px-5 py-1.5">
        <h2 className="flex min-h-8 min-w-0 flex-auto self-stretch">
          <button type="button" onClick={onToggle} aria-expanded={expanded} aria-controls={`${step.key}-body`} className="flex min-w-0 flex-1 items-center gap-3 text-left">
            <span
              className={cn(
                'inline-block h-2.5 w-2.5 shrink-0 rounded-full',
                status === 'done' && 'bg-[var(--fm-ink)]',
                status === 'current' && 'bg-[var(--fm-brand)]',
                status === 'upcoming' && 'border border-[var(--fm-ink3)] bg-transparent',
              )}
              aria-hidden="true"
            />
            <span className="w-3 shrink-0 text-[12px] tabular-nums text-[var(--fm-ink3)]">{n}</span>
            <span className="text-[14px] font-semibold">{step.label}</span>
            <span className="truncate text-[12px] font-medium text-[var(--fm-ink3)]">{note ?? (status === 'done' ? 'Done' : status === 'current' ? 'Now' : 'Next')}</span>
          </button>
        </h2>
        {!expanded && (isValidElement<{ primary?: boolean }>(pill) ? cloneElement(pill, { primary: status === 'current' }) : pill)}
      </div>
      <div id={`${step.key}-body`} className={cn('gap-4 px-5 pb-5 lg:grid-cols-[180px_minmax(0,1fr)_auto] lg:items-start', expanded ? 'grid' : 'hidden')}>
        <p className="text-[12.5px] leading-snug text-[var(--fm-ink2)]">{step.purpose}</p>
        <div className="grid gap-3 sm:grid-cols-2 xl:grid-cols-3">{children}</div>
        <div className="flex flex-col items-start gap-2 lg:items-end">
          {primary}
          {actions && <div className="flex flex-wrap gap-2 lg:max-w-[400px] lg:justify-end">{actions}</div>}
        </div>
      </div>
    </section>
  )
}

/** Remounts per organisation and system, so open forms, errors and busy flags never carry over to another system. */
export default function SystemFilePage() {
  const { id } = useParams<{ id: string }>()
  const { selectedOrg } = useOrg()
  return <SystemFileBody key={systemFileScopeKey(selectedOrg?.id, id)} id={id} />
}

function SystemFileBody({ id }: { id: string }) {
  const router = useRouter()
  const { selectedOrg } = useOrg()
  const { setSelectedSystemId } = useSystemContext()
  const { system, evidence, approval, remediation, risks, reports, gate, fairnessRuns, monitoringRuns, monitoringPolicy, seals, clauseMap, loading, error, refresh, requestDecision, recordDecision, inspectCsv, runFairness, runMonitoring, saveMonitoringPolicy, attest } = useSystemFile(id)
  const { confirm: confirmApplicability, acceptOverride } = useApplicability()
  const env = useEnvironmentalImpact(selectedOrg?.id, id)
  const [busy, setBusy] = useState<string | null>(null)
  const [actionError, setActionError] = useState<string | null>(null)
  const [attesting, setAttesting] = useState<AttestableCheck | null>(null)
  const [conditioning, setConditioning] = useState(false)
  const [confirmingTier, setConfirmingTier] = useState(false)
  const [tab, setTab] = useState('journey')
  // Stages the user opened or closed; the rest follow the default (current stage, and Decision while pending).
  const [toggled, setToggled] = useState<Partial<Record<JourneyKey, boolean>>>({})

  // An in-page link (#first-verdict, #operate, #decision, #onboard) opens the stage holding its target, then scrolls there.
  const reveal = (hash: string) => {
    const el = hash.length > 1 ? document.getElementById(decodeURIComponent(hash.slice(1))) : null
    const key = el?.closest<HTMLElement>('[data-stage]')?.dataset.stage as JourneyKey | undefined
    if (!el || !key) return
    setToggled((t) => ({ ...t, [key]: true }))
    requestAnimationFrame(() => el.scrollIntoView({ block: 'start' }))
  }
  useEffect(() => reveal(window.location.hash), [])

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
  // risks are this system's recorded findings; taxonomy suggestions come apart.
  const recordedOpen = (risks?.risks ?? []).filter((r) => !['accepted', 'closed', 'resolved', 'mitigated'].includes(r.status))
  const recordedSevere = recordedOpen.filter((r) => r.severity === 'high' || r.severity === 'critical')
  const suggested = risks?.suggested?.length ?? 0
  const req = approval?.request ?? null
  const decided = req && req.status !== 'pending' ? req : null
  const latestReport = reports[0]
  const latestMonitoring = monitoringRuns[0]
  const seal = seals[0]
  const isOpen = (key: JourneyKey) => toggled[key] ?? (key === current || (key === 'decision' && req?.status === 'pending'))
  const stage = (key: JourneyKey) => ({ status: statusOf(key), expanded: isOpen(key), onToggle: () => setToggled((t) => ({ ...t, [key]: !isOpen(key) })) })
  const override = tierOverride(gate?.explain)
  const envStatus = typeof env.data?.recommendation === 'string' ? env.data.recommendation : env.data?.recommendation?.status
  const applicability = s?.applicability ?? null
  const awaitingSecond = !!applicability?.tierBelowSuggestion && !applicability.overrideAcceptedBy
  // explain arrives with the gate's explanation fields; older gate payloads have none.
  const tierNote = (gate as (NonNullable<typeof gate> & { explain?: { tierNote?: string | null } }) | null)?.explain?.tierNote ?? null
  const tierLine = !applicability
    ? 'Tier not confirmed'
    : applicability.tierBelowSuggestion
      ? `Below the suggested ${cap(applicability.suggestedTier)}`
      : `${applicability.tier !== applicability.suggestedTier ? 'Above the suggested' : 'Suggested'} ${cap(applicability.suggestedTier)}, confirmed by ${applicability.confirmedBy} on ${when(applicability.confirmedAt)}`

  return (
    <div className="grid gap-4">
      <div className="text-[12.5px] font-medium text-[var(--fm-ink2)]">
        <Link href="/dashboard" className="hover:text-[var(--fm-ink)]">Today</Link> · {line || 'Unassigned'} · System file
      </div>

      <header className="min-w-0">
        <h1 className="truncate text-[30px] font-semibold leading-[1.1] tracking-[-.03em] lg:text-[34px]">{loading && !s ? 'Loading' : s?.name}</h1>
        {s && (
          <div className="mt-1.5 flex min-w-0 items-center gap-2 text-[13px] text-[var(--fm-ink2)]" title={[tierLine, tierNote].filter(Boolean).join('. ')}>
            <span className="truncate">
              <span className={cn(applicability?.tierBelowSuggestion && 'text-[#a14d00]')}>{cap(s.riskTier)} tier</span> · {s.owner || 'No owner'} · {SOURCE[source] ?? cap(source)}
            </span>
            {!applicability && <Pill tone="you">Not confirmed</Pill>}
          </div>
        )}
      </header>

      <section className="fm-card grid gap-3 p-5" aria-label="Release gate">
        <div className="flex flex-wrap items-baseline gap-x-3 gap-y-1">
          <span className="text-[44px] font-semibold leading-none tracking-[-.04em] tabular-nums" title={gate ? `Confidence, ${gate.band}` : undefined}>{gate ? gate.confidence.toFixed(2) : ''}</span>
          <span className={cn('text-[15px] font-semibold', gate ? VERDICT_TONE[gate.verdict] : '')} title={gate?.reasons.join(' ')}>{gate ? VERDICT_LABEL[gate.verdict] : ''}</span>
        </div>
        {gate && (() => {
          const total = Math.max(gate.proven + gate.attested + gate.open, 1)
          return (
            <>
              <div className="flex h-2 overflow-hidden rounded-full bg-[var(--fm-line)]" aria-hidden="true">
                <span className="bg-[var(--fm-ink)]" style={{ width: `${(gate.proven / total) * 100}%` }} />
                <span className="fm-tex" style={{ width: `${(gate.attested / total) * 100}%` }} />
              </div>
              <div className="flex flex-wrap gap-x-4 text-[12px] tabular-nums text-[var(--fm-ink2)]">
                <span className="flex items-center gap-1.5"><i aria-hidden className="fm-cel proven" />{gate.proven} proven</span>
                <span className="flex items-center gap-1.5"><i aria-hidden className="fm-cel attested" />{gate.attested} attested</span>
                <span className="flex items-center gap-1.5"><i aria-hidden className="fm-cel open" />{gate.open} open</span>
              </div>
            </>
          )
        })()}
      </section>

      <Tabs value={tab} onValueChange={setTab} className="grid grid-cols-[minmax(0,1fr)] gap-4">
        <TabsList aria-label="System file" className={cn(TAB_LIST, 'justify-self-start')}>
          <TabsTrigger value="journey" className={TAB}>Journey</TabsTrigger>
          <TabsTrigger value="requirements" className={TAB}>Requirements</TabsTrigger>
          <TabsTrigger value="record" className={TAB}>Record</TabsTrigger>
        </TabsList>
        <TabsContent value="requirements" className="mt-0 grid gap-4 data-[state=inactive]:hidden">
          <RequirementsTab confirmed={applicability?.frameworks ?? clauseMap?.confirmed ?? []} clauseMap={clauseMap} />
        </TabsContent>
        <TabsContent value="record" className="mt-0 grid gap-4 data-[state=inactive]:hidden">
          <RecordTab seals={seals} approval={approval} />
        </TabsContent>
        {/* Journey stays mounted, so an open form or a staged upload survives a look at another tab. */}
        <TabsContent value="journey" forceMount className="mt-0 grid gap-4 data-[state=inactive]:hidden">
          {actionError && <p className="rounded-[10px] bg-[#fde9ea] px-3 py-2 text-[13px] text-[#b4232c]">{actionError}</p>}

          <div
            className="fm-card divide-y divide-[var(--fm-line)]"
            onClickCapture={(e) => {
              const a = (e.target as HTMLElement).closest<HTMLAnchorElement>('a[href*="#"]')
              if (a && new URL(a.href).pathname === window.location.pathname) reveal(new URL(a.href).hash)
            }}
          >
          <Stage step={JOURNEY[0]} {...stage('onboard')} note={applicability ? undefined : 'Tier not confirmed'} pill={applicability
            ? <Action small href="#first-verdict">Run the first fairness test</Action>
            : <Action small onClick={() => { setToggled((t) => ({ ...t, onboard: true })); setConfirmingTier(true) }}>Confirm tier and rules</Action>} primary={applicability
            ? <Action href="#first-verdict">Run the first fairness test</Action>
            : <Action onClick={() => setConfirmingTier(!confirmingTier)} expanded={confirmingTier}>Confirm tier and rules</Action>} actions={applicability
            ? <Action onClick={() => setConfirmingTier(!confirmingTier)} expanded={confirmingTier} primary={false}>Change tier or rules</Action>
            : <Action href="/integrations" primary={false}>Connect sources</Action>}>
            <Fact label="Registered" value={when(s?.createdAt) || ''} />
            <Fact label="Rules it answers to" value={<span className="whitespace-normal">{applicability?.frameworks.length ? applicability.frameworks.map((f) => shortFrameworkName(f.name)).join(', ') : 'Not chosen'}</span>} />
            <Fact label="Tier basis" value={<span className="whitespace-normal">{tierBasis(applicability)}</span>} />
            <Fact
              label="Record"
              value={
                <span className="whitespace-normal">
                  {applicability ? `Applicability decision saved as evidence, rules version ${applicability.rulesVersion}` : s?.owner && line ? 'Owner and business line set' : 'Owner or business line missing'}
                </span>
              }
            />
            {awaitingSecond && applicability && (
              <div className="flex flex-wrap items-center gap-3 sm:col-span-2 xl:col-span-3">
                <span className="text-[12.5px] text-[#a14d00]">Lowered tier awaits a second person</span>
                <Action onClick={() => act('accept', async () => { await acceptOverride(id, applicability.evidenceId); await refresh() })} disabled={busy !== null} primary={false}>
                  {busy === 'accept' ? 'Accepting' : 'Accept the lower tier'}
                </Action>
              </div>
            )}
            {confirmingTier && s && (
              <div className="rounded-[12px] border border-[var(--fm-line)] p-4 sm:col-span-2 xl:col-span-3">
                <ApplicabilityForm
                  autoFocus
                  record={applicability}
                  currentTier={s.riskTier}
                  submitLabel="Confirm"
                  onCancel={() => setConfirmingTier(false)}
                  onSubmit={(body) => act('applicability', async () => {
                    await confirmApplicability(s.id, body)
                    setConfirmingTier(false)
                    await refresh()
                  })}
                />
              </div>
            )}
          </Stage>

          <Stage step={JOURNEY[1]} {...stage('assess')} pill={<Action small onClick={() => open('/tests')}>Run an evaluation</Action>} primary={<Action onClick={() => open('/tests')}>Run an evaluation</Action>} actions={<>
            <Action onClick={() => open('/bias')} primary={false}>Bias test</Action>
            <Action onClick={() => open('/ai-governance')} primary={false}>Environmental</Action>
          </>}>
            <Fact label="Environmental" value={env.loading ? 'Checking' : env.data ? `Assessed${envStatus ? `, ${String(envStatus).replace(/_/g, ' ')}` : ''}${env.data.generatedAt ? ` on ${when(env.data.generatedAt)}` : ''}` : 'No assessment yet'} />
            <Fact label="Evaluation runs" value={<span className="text-[var(--fm-ink2)]">Listed in the test workspace</span>} />
            <Fact
              label="Fairness"
              value={
                fairnessRuns.length === 0
                  ? 'Not measured yet'
                  : `${fairnessSummary(fairnessRuns[0])} · ${fairnessRuns.length} run${fairnessRuns.length === 1 ? '' : 's'}`
              }
            />
            <FairnessRunPanel inspect={inspectCsv} run={runFairness} />
            {id && <TargetPanel systemId={id} />}
          </Stage>

          <Stage step={JOURNEY[2]} {...stage('govern')} pill={<Action small onClick={() => open(`/systems/${encodeURIComponent(id)}/plan`)}>Open plan</Action>} primary={<Action onClick={() => open(`/systems/${encodeURIComponent(id)}/plan`)}>Open plan</Action>} actions={<>
            <Action onClick={() => open('/evidence?view=artifacts')} primary={false}>Record evidence</Action>
            <Action onClick={() => open('/compliance')} primary={false}>Frameworks</Action>
            <Action href="/compliance/runs" primary={false}>Workflow runs</Action>
          </>}>
            <Fact label="Evidence" value={evidence ? `${evidence.linkedEvidence} of ${evidence.totalEvidence} linked to controls` : ''} />
            <Fact label="Review state" value={evidence ? READINESS_LABEL[evidence.decisionReadiness] ?? evidence.decisionReadiness : ''} />
            <Fact label="Missing" value={!evidence ? '' : evidence.missingSignals.length ? evidence.missingSignals.join(', ') : 'Nothing flagged'} />
            {evidence?.recommendedNextStep && (
              <p className="text-[12.5px] text-[var(--fm-ink2)] sm:col-span-2 xl:col-span-3">{evidence.recommendedNextStep}</p>
            )}
          </Stage>

          <Stage step={JOURNEY[3]} {...stage('remediate')} note={recordedOpen.length ? `${recordedOpen.length} open` : undefined} pill={<Action small onClick={() => open('/risks')}>Open findings</Action>} primary={<Action onClick={() => open('/risks')}>Open findings</Action>} actions={<>
            <Action onClick={() => open('/remediation')} primary={false}>Remediation tasks</Action>
          </>}>
            <Fact label="Open findings" value={risks ? `${recordedOpen.length} recorded${suggested ? `, ${suggested} suggested by taxonomy` : ''}` : ''} />
            <Fact label="High or critical" value={risks ? `${recordedSevere.length}` : ''} />
            <Fact label="Active tasks" value={remediation ? `${remediation.summary.activeTasks}` : ''} />
          </Stage>

          <Stage step={JOURNEY[4]} {...stage('decision')} note={req ? cap(req.status) : undefined} pill={
            !req || decided?.status === 'rejected'
              ? <Action small onClick={() => act('request', requestDecision)} disabled={busy === 'request'}>{busy === 'request' ? 'Requesting' : 'Request release decision'}</Action>
              : req.status === 'pending' ? undefined : <Action small onClick={() => open('/audit-reports')} primary={false}>Release report</Action>
          } primary={!req || decided?.status === 'rejected' ? (
            <Action onClick={() => act('request', requestDecision)} disabled={busy === 'request'}>
              {busy === 'request' ? 'Requesting' : 'Request release decision'}
            </Action>
          ) : req.status === 'pending' ? (
            <Action
              onClick={() => (gate?.verdict === 'conditional_go' ? setConditioning(true) : void act('approve', () => recordDecision(req.id, 'approved')))}
              disabled={busy !== null || gate?.verdict === 'no_go'}
            >
              Approve release
            </Action>
          ) : undefined} actions={<>
            {req && decided?.status !== 'rejected' && (req.status === 'pending'
              ? <Action onClick={() => act('reject', () => recordDecision(req.id, 'rejected'))} disabled={busy !== null} primary={false}>Reject</Action>
              : <Action onClick={() => open('/audit-reports')} primary={false}>Release report</Action>)}
            {override && <p className={cn('max-w-[220px] text-[11.5px] leading-snug', override.pending ? 'text-[#a14d00]' : 'text-[var(--fm-ink3)]')}>{override.text}</p>}
          </>}>
            <Fact label="Request" value={!req ? 'Not requested' : req.status === 'pending' ? `Pending since ${when(req.createdAt)}` : `${req.status[0].toUpperCase()}${req.status.slice(1)}${req.updatedAt ? ` on ${when(req.updatedAt)}` : ''}`} />
            <Fact label="Decisions recorded" value={approval ? `${approval.decisions.length}` : ''} />
            <Fact label="Blocking" value={summary ? (summary.criticalBlockers ? `${summary.criticalBlockers} critical blocker${summary.criticalBlockers === 1 ? '' : 's'}` : 'Nothing blocking') : ''} />
            <Fact
              label="Evidence seal"
              value={
                !seal ? (
                  'Taken when a decision is recorded'
                ) : seal.verification.status === 'intact' ? (
                  <span><span className="text-[#1f7a4d]">Intact</span> · {seal.evidenceCount} record{seal.evidenceCount === 1 ? '' : 's'} sealed {when(seal.createdAt)}{seal.verification.addedSince ? `, ${seal.verification.addedSince} added since` : ''} · <span className="font-mono text-[11.5px]">{seal.chainHead.slice(0, 12)}</span></span>
                ) : (
                  <span className="text-[#b4232c]">Broken, {[seal.verification.changed.length && `${seal.verification.changed.length} changed`, seal.verification.missing.length && `${seal.verification.missing.length} missing`].filter(Boolean).join(', ')} since {when(seal.createdAt)}</span>
                )
              }
            />
            {gate && (
              <div className="sm:col-span-2 xl:col-span-3">
                <div className="text-[11px] font-semibold uppercase tracking-[.08em] text-[var(--fm-ink3)]">Gate checks</div>
                <ul className="mt-1 grid gap-1 sm:grid-cols-2 xl:grid-cols-3">
                  {gate.checks.map((c) => {
                    const attestable = c.state === 'open' && isAttestable(c.key) ? c.key : null
                    return (
                    <li key={c.key} className="flex items-center gap-2 text-[12.5px]">
                      <i aria-hidden="true" className={`fm-cel ${checkCell(c)}`} />
                      <span>{c.label}</span>
                      <span className="text-[var(--fm-ink3)]">{CHECK_STATE[c.state]}{c.confidence ? ` ${c.confidence.toFixed(2)}` : ''}</span>
                      {attestable && (
                        <button type="button" onClick={() => setAttesting(attesting === attestable ? null : attestable)} className="ml-auto text-[12px] font-medium text-[var(--fm-ink2)] underline-offset-2 hover:underline">
                          Attest
                        </button>
                      )}
                    </li>
                    )
                  })}
                </ul>
                {attesting && (
                  <AttestForm
                    key={attesting}
                    check={attesting}
                    onCancel={() => setAttesting(null)}
                    onSubmit={async (statement, reference) => {
                      await attest(attesting, statement, reference)
                      setAttesting(null)
                    }}
                  />
                )}
                <LeavesOpen clauseMap={clauseMap} />
                {gate.policy && gate.policy.blocking.length + gate.policy.warnings.length > 0 && (
                  <>
                    <div className="mt-3 text-[11px] font-semibold uppercase tracking-[.08em] text-[var(--fm-ink3)]">Policy rules</div>
                    <ul className="mt-1 flex flex-col gap-1">
                      {[...gate.policy.blocking.map((r) => ({ ...r, blocks: true })), ...gate.policy.warnings.map((r) => ({ ...r, blocks: false }))].map((r) => (
                        <li key={`${r.policyId}:${r.ruleId}`} className="flex flex-wrap items-baseline gap-x-2 text-[12.5px]">
                          <span className={r.blocks ? 'font-semibold text-[#b4232c]' : 'font-semibold text-[#a14d00]'}>{r.blocks ? 'Blocks release' : 'Warning'}</span>
                          <span>{r.ruleTitle}</span>
                          <Link href={`/policies/${r.policyId}`} className="text-[var(--fm-ink2)] underline-offset-2 hover:underline">{r.policyName}</Link>
                          {r.detail && <span className="text-[var(--fm-ink3)]">{r.detail}</span>}
                        </li>
                      ))}
                    </ul>
                  </>
                )}
                <VerdictExplainer gate={gate} onAttest={(check) => isAttestable(check) && setAttesting(check)} onOpen={open} />
              </div>
            )}
            {req?.status === 'pending' && gate?.verdict === 'no_go' && (
              <p className="text-[12.5px] text-[#b4232c] sm:col-span-2 xl:col-span-3">Approval is blocked: {gate.reasons[0]?.replace(/\.$/, '') ?? 'the release gate says no go'}.</p>
            )}
            {req?.status === 'pending' && gate?.verdict === 'conditional_go' && conditioning && (
              <div className="sm:col-span-2 xl:col-span-3">
                <ConditionsForm
                  onCancel={() => setConditioning(false)}
                  onSubmit={async (conditions) => {
                    await recordDecision(req.id, 'approved', conditions)
                    setConditioning(false)
                  }}
                />
              </div>
            )}
            {req?.decisionNotes && <p className="text-[12.5px] text-[var(--fm-ink2)] sm:col-span-2 xl:col-span-3">{req.decisionNotes}</p>}
          </Stage>

          <Stage step={JOURNEY[5]} {...stage('operate')} pill={<Action small onClick={() => open('/audit-reports')}>Generate audit report</Action>} primary={<Action onClick={() => open('/audit-reports')}>Generate audit report</Action>} actions={<>
            <Action onClick={() => open('/monitoring')} primary={false}>Monitoring</Action>
          </>}>
            <Fact label="Audit reports" value={reports.length ? `${reports.length}, latest ${when(latestReport.createdAt)}` : 'None generated'} />
            <Fact label="Monitoring snapshots" value={latestMonitoring ? `${latestMonitoring.allChecksPass ? 'Stable' : 'Drifting'} on ${when(latestMonitoring.createdAt)}${monitoringRuns.length > 1 ? `, ${monitoringRuns.length} snapshots` : ''}` : 'None recorded'} />
            <Fact label="Approved" value={decided?.status === 'approved' ? when(decided.updatedAt) || 'Yes' : 'Not yet'} />
            <WatchPanel systemId={id} policy={monitoringPolicy} runs={monitoringRuns} save={saveMonitoringPolicy} />
            <MonitoringRunPanel inspect={inspectCsv} run={runMonitoring} hasBaseline={fairnessRuns.length > 0} />
          </Stage>
          </div>
        </TabsContent>
      </Tabs>
    </div>
  )
}
