'use client'

import '@/astryx/pages/system-file.css'
import NextLink from 'next/link'
import { useParams, useRouter, useSearchParams } from 'next/navigation'
import { Suspense, useEffect, useMemo, useRef, useState, type ReactNode } from 'react'
import { ArrowDown, ArrowLeft, ChevronDown } from 'lucide-react'
import { useMediaQuery } from '@astryxdesign/core/hooks'
import { Avatar } from '@astryxdesign/core/Avatar'
import { Badge } from '@astryxdesign/core/Badge'
import { Banner } from '@astryxdesign/core/Banner'
import { Button } from '@astryxdesign/core/Button'
import { Card } from '@astryxdesign/core/Card'
import { Dialog, DialogHeader } from '@astryxdesign/core/Dialog'
import { Drawer } from '@astryxdesign/core/Drawer'
import { EmptyState } from '@astryxdesign/core/EmptyState'
import { HStack, StackItem, VStack } from '@astryxdesign/core/Layout'
import { Layout, LayoutContent } from '@astryxdesign/core/Layout'
import { Link } from '@astryxdesign/core/Link'
import { MetadataList, MetadataListItem } from '@astryxdesign/core/MetadataList'
import { Skeleton } from '@astryxdesign/core/Skeleton'
import { Tab, TabList } from '@astryxdesign/core/TabList'
import { Heading, Text } from '@astryxdesign/core/Text'
import { TextArea } from '@astryxdesign/core/TextArea'
import { Token } from '@astryxdesign/core/Token'
import { useOrg } from '@/context/OrgContext'
import { useSystemContext } from '@/components/workflow/SystemContext'
import { FindingRetestDraft } from '@/components/workflow/FindingRetestDraft'
import { recordParam } from '@/lib/assurance/evaluationLinks'
import { CheckEvidenceLinks } from '@/components/workflow/CheckEvidenceLinks'
import { HomeFailureEvidence, useHomeFailureRecord } from '@/components/workflow/HomeFailureEvidence'
import { Button as Pill } from '@/components/ui/button'
import { ApplicabilityForm } from '@/components/workflow/ApplicabilityForm'
import { StoredAnalyses } from '@/components/workflow/StoredAnalyses'
import { checkCell, classLabel } from '@/components/ui/matrix'
import { shortFrameworkName, tierBasis, useApplicability } from '@/lib/api/hooks/useApplicability'
import { useAutopilot } from '@/lib/api/hooks/useAutopilot'
import { isOpenRisk } from '@/lib/api/hooks/useRisks'
import { useEnvironmentalImpact } from '@/lib/api/hooks/useAIGovernance'
import { systemFileScopeKey, useSystemFile, type AttestableCheck, type GatePathStep } from '@/lib/api/hooks/useSystemFile'
import {
  KIND_LABEL, RISK_TONE, SOURCE_LABEL, STAGE_LABEL, VERDICT_META, approvalStatusOf, buildTrace, cap, stepWho, when,
} from '@/astryx/data/system-file'
import { AutopilotCard } from './AutopilotCard'
import { AttestPanel } from './AttestPanel'
import { FairnessRunPanel } from './FairnessRunPanel'
import { MonitoringRunPanel } from './MonitoringRunPanel'
import { WatchPanel } from './WatchPanel'
import { DecisionsCard, ReasonStack } from '@/components/explain/ExplainParts'
import { TargetPanel } from './TargetPanel'
import { OwnerPanel } from './OwnerPanel'
import { RequirementsTab } from './RequirementsTab'
import { RecordTab } from './RecordTab'
import { LeavesOpen } from './LeavesOpen'
import { HASH_PANEL, VerdictExplainer, stepLine, stepTitle, tierOverride } from './VerdictExplainer'
import { RetiredCard, VersionsCard } from './Lifecycle'
import { useRetirement, useSystemChanges } from '@/lib/api/hooks/useLifecycle'
import { SystemReviewHistory, SystemReviewTrail } from './SystemReviewTrail'

// Environmental is left out: an attestation would shadow any later assessment, which the path recommends instead.
const ATTESTABLE = new Set<string>(['data_governance', 'human_oversight', 'monitoring'])
const isAttestable = (key: string): key is AttestableCheck => ATTESTABLE.has(key)

const CHECK_STATE = {
  proven: 'Passes', attested: 'Attested', estimated: 'Estimated', fails: 'Fails',
  stale: 'Out of date', open: 'Nothing on file', partial: 'Partial evidence', excluded: 'Out of scope',
  planned: 'Planned', atorg: 'Covered by the organisation',
} as const
const READINESS_LABEL: Record<string, string> = {
  empty: 'No evidence yet',
  needs_evidence: 'Needs evidence',
  collected: 'Evidence collected, not yet linked',
  linked: 'Evidence linked to controls',
  review_ready: 'Review-ready',
}
const REQUEST_TONE = { not_requested: 'neutral', pending: 'orange', approved: 'green', rejected: 'red' } as const

type Panel =
  | { kind: 'monitoring'; findingId?: string | null }
  | { kind: 'fairness' | 'watch' | 'target' | 'analyses' | 'explain' | 'tier' | 'decide' | 'owner' }
  | { kind: 'attest'; check: AttestableCheck }

const PANEL_TITLE: Record<Panel['kind'], string> = {
  fairness: 'Run a fairness test',
  monitoring: 'Record a monitoring snapshot',
  watch: 'Monitoring and live runs',
  target: 'Model connection',
  analyses: 'Stored analyses',
  explain: 'How the verdict was reached',
  tier: 'Tier and rules',
  decide: 'Release decision',
  owner: 'Change owner',
  attest: 'Attest a check',
}

/** Remounts per organisation and system, so open forms, errors and busy flags never carry over to another system. */
export default function SystemFilePage() {
  const { id } = useParams<{ id: string }>()
  const { selectedOrg } = useOrg()
  return (
    <Suspense fallback={<div className="fm-system-file"><Skeleton width="100%" height={280} /></div>}>
      <SystemFileBody key={systemFileScopeKey(selectedOrg?.id, id)} id={id} />
    </Suspense>
  )
}

function SystemFileBody({ id }: { id: string }) {
  const router = useRouter()
  const search = useSearchParams()
  const { selectedOrg } = useOrg()
  const { setSelectedSystemId, systems } = useSystemContext()
  const file = useSystemFile(id)
  // The latest Explanation quality run on live runs: whether the reasons this system states for its decisions hold.
  const reasons = file.liveRuns?.evaluations.find((e) => e.evaluationId === 'EV-OVS-04')?.metrics ?? null
  const changes = useSystemChanges(id)
  const retirement = useRetirement(id)
  const { system, evidence, approval, remediation, risks, reports, fairnessRuns, evaluationRuns, monitoringRuns, monitoringPolicy, seals, clauseMap, loading, error, refresh } = file
  const gate = file.gate?.systemId && file.gate.systemId !== id ? null : file.gate
  const ap = useAutopilot(id, `${gate?.confidence ?? ''}-${evidence?.totalEvidence ?? 0}-${approval?.decisions.length ?? 0}`)
  const { confirm: confirmApplicability, acceptOverride } = useApplicability()
  const env = useEnvironmentalImpact(selectedOrg?.id, id)
  const failures = (gate?.checks ?? []).filter((check) => checkCell(check) === 'fails')
  const lead = failures[0]
  const gateSystemId = system?.id === id && gate?.systemId === id ? id : undefined
  const proof = useHomeFailureRecord(gateSystemId, lead)

  const [panel, setPanel] = useState<Panel | null>(null)
  const selectedTab = search.get('tab')
  const tab = selectedTab === 'requirements' || selectedTab === 'record' ? selectedTab : 'file'
  const setTab = (value: string) => {
    const next = new URLSearchParams(search)
    if (value === 'file') next.delete('tab')
    else next.set('tab', value)
    router.push(`/systems/${encodeURIComponent(id)}${next.size ? `?${next}` : ''}`, { scroll: false })
  }
  const [busy, setBusy] = useState<string | null>(null)
  const [actionError, setActionError] = useState<string | null>(null)
  const [railOpen, setRailOpen] = useState(false)
  const isNarrow = useMediaQuery('(max-width: 1024px)')

  // An evaluation page links here with #target when the model is not connected yet.
  useEffect(() => {
    if (window.location.hash === '#target') setPanel({ kind: 'target' })
    if (window.location.hash === '#operate') {
      const findingId = recordParam(new URLSearchParams(window.location.search), 'finding')
      setPanel({ kind: 'monitoring', findingId })
    }
  }, [])

  // The legacy pages read the system from the URL or the context.
  useEffect(() => {
    if (id) setSelectedSystemId(id)
  }, [id, setSelectedSystemId])

  const open = (href: string) => {
    const [path, hash] = href.split('#')
    router.push(`${path}${path.includes('?') ? '&' : '?'}system=${encodeURIComponent(id)}${hash ? `#${hash}` : ''}`)
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

  const trace = useMemo(() => buildTrace(ap.data?.events, approval), [ap.data?.events, approval])

  // Needs you and Decisions send reviewers here with ?decide: the decision is made beside the gate it rests on.
  const askedToDecide = useRef(typeof window !== 'undefined' && new URLSearchParams(window.location.search).has('decide'))
  const pendingRequest = gate && approvalStatusOf(gate, approval) === 'pending' ? approval?.request : null
  useEffect(() => {
    if (askedToDecide.current && pendingRequest) {
      askedToDecide.current = false
      setPanel({ kind: 'decide' })
    }
  }, [pendingRequest])

  if (loading && !system) {
    return (
      <div className="fm-system-file">
        <VStack gap={4}>
          <Skeleton width={220} height={14} />
          <Skeleton width="min(100%, 420px)" height={34} />
          <Skeleton width="100%" height={220} />
        </VStack>
      </div>
    )
  }
  if (error || !system) {
    return (
      <div className="fm-system-file">
        <EmptyState
          title="System file unavailable"
          description={error || 'This record could not be loaded for the selected organisation.'}
          actions={<><Button label="Try again" variant="secondary" onClick={() => void refresh()} /><Button label="Back to AI systems" variant="primary" href="/systems" /></>}
        />
      </div>
    )
  }

  const s = system
  const meta = s.metadata ?? {}
  const kind = KIND_LABEL[meta.asset_kind as string] ?? (meta.asset_kind ? cap(String(meta.asset_kind)) : '')
  const sourceKey = (meta.source as string | undefined) || 'manual'
  const description = typeof meta.description === 'string' ? meta.description.trim() : ''
  const applicability = s.applicability ?? null
  const awaitingSecond = !!applicability?.tierBelowSuggestion && !applicability.overrideAcceptedBy
  const frameworks = (applicability?.frameworks ?? clauseMap?.confirmed ?? []).map((f) => shortFrameworkName(f.name))
  const status = approvalStatusOf(gate, approval) as keyof typeof REQUEST_TONE
  const req = approval?.request ?? null
  const verdict = gate ? VERDICT_META[gate.verdict] : null
  const option = gate?.path?.toGo ?? gate?.path?.options?.[0] ?? null
  const override = tierOverride(gate?.explain)
  const seal = seals[0]
  const recordedOpen = (risks?.risks ?? []).filter(isOpenRisk)
  const envRec = env.data?.recommendation
  const envStatus = typeof envRec === 'string' ? envRec : envRec?.status
  const canRequest = status === 'not_requested' || status === 'rejected'

  const stepButton = (step: GatePathStep): ReactNode => {
    switch (step.action) {
      case 'fairness_run': return <Button label="Run the test" variant="secondary" onClick={() => setPanel({ kind: 'fairness' })} />
      case 'monitoring_snapshot': return <Button label="Record a snapshot" variant="secondary" onClick={() => setPanel({ kind: 'monitoring' })} />
      case 'evaluation_run': return step.evaluationId && step.source === 'traces'
        ? <Button label="Run on live runs" variant="secondary" onClick={() => open(`/compliance/evaluations/${encodeURIComponent(step.evaluationId as string)}?source=traces`)} />
        : <Button label="Run an evaluation" variant="secondary" onClick={() => open('/evaluations')} />
      case 'attest': return isAttestable(step.check) ? <Button label="Attest" variant="secondary" onClick={() => setPanel({ kind: 'attest', check: step.check as AttestableCheck })} /> : null
      case 'environmental_assessment': return <Button label="Open assessment" variant="secondary" href={`/environment?system=${encodeURIComponent(id)}`} />
      case 'evidence_upload': return <Button label="Record evidence" variant="secondary" href={`/evidence?system=${encodeURIComponent(id)}&check=${step.check}`} />
    }
  }

  // The explainer's in-page links open the matching panel; a decision opens only while a request waits for one,
  // and with none yet the link requests it.
  const openFromExplainer = (href: string) => {
    const kind = HASH_PANEL[href]
    if (kind && (kind !== 'decide' || (status === 'pending' && req))) return setPanel({ kind })
    setPanel(null)
    if (kind === 'decide' && canRequest && !retired) return void act('request', file.requestDecision)
    if (!href.startsWith('#')) open(href)
  }

  const retired = retirement.data?.retired ?? null
  const lifecycleActions = retired ? null : (
    <>
      <Button label="Record a change" variant="secondary" href={`/systems/${encodeURIComponent(id)}/change`} />
      <Button label="Retire" variant="ghost" href={`/systems/${encodeURIComponent(id)}/retire`} />
    </>
  )
  const versions = gate ? <VersionsCard changes={changes.data?.changes ?? []} checks={gate.checks} approved={status === 'approved'} createdAt={s.createdAt} /> : null
  const primary = retired ? null : canRequest
    ? <Button label={status === 'rejected' ? 'Request a new decision' : 'Request release decision'} variant="primary" isDisabled={busy !== null} isLoading={busy === 'request'} onClick={() => void act('request', file.requestDecision)} />
    : status === 'pending' && req
      ? <Button label="Decide" variant="primary" onClick={() => setPanel({ kind: 'decide' })} />
      : null
  const reviewDecision = status === 'pending' && req && !retired
  const showRequestInMenu = canRequest && !retired && (Boolean(lead) || gate?.verdict === 'no_go')
  const visibleChecks = (gate?.checks ?? []).slice().sort((a, b) =>
    Number(checkCell(b) === 'fails') - Number(checkCell(a) === 'fails'))

  function jumpToChecks() {
    const checks = document.getElementById('sf-checks')
    checks?.focus({ preventScroll: true })
    checks?.scrollIntoView({ block: 'start' })
  }

  const releaseOverview = (
    <section className="fm-sf-overview" aria-label="Release overview">
      <div className="fm-sf-focus">
        <div className="fm-sf-verdict" data-verdict={gate?.verdict ?? 'unavailable'}>
          <i aria-hidden />{verdict?.label ?? 'Release status unavailable'}
        </div>
        <h2>{lead ? (lead.key === 'fairness' ? 'Fairness check failed' : lead.label) : gate ? 'Release readiness' : 'Release gate unavailable'}</h2>
        {lead ? (
          <>
            <p className="fm-sf-context">{failures.length === 1 ? '1 failing release check' : `${failures.length} failing release checks`}</p>
            {gateSystemId ? <HomeFailureEvidence systemId={gateSystemId} check={lead} {...proof} showGroupComparison={false} />
              : <p className="fm-sf-context">Source record unavailable.</p>}
            {reviewDecision && <div className="fm-sf-release-action">{primary}</div>}
          </>
        ) : gate ? (
          <>
            <p className="fm-sf-context">{gate.reasons[0] ?? 'Review the checks that support this verdict.'}</p>
            <div className="fm-sf-release-action">
              {(!showRequestInMenu && primary) ||
                <Pill type="button" size="lg" onClick={jumpToChecks}>View release checks <ArrowDown size={15} aria-hidden /></Pill>}
            </div>
          </>
        ) : (
          <div className="fm-sf-release-action">
            <Pill type="button" variant="outline" size="lg" onClick={() => void refresh()}>Retry release checks</Pill>
          </div>
        )}
      </div>
      {lead && gateSystemId ? <SystemReviewTrail systemId={gateSystemId} check={lead} risks={risks} /> : (
        <div className="fm-sf-readiness">
          <h2>Check status</h2>
          {gate && visibleChecks.length > 0 ? (
            <ul>
              {visibleChecks.map((check) => <li key={check.key}><span>{check.label}</span>
                <span className="fm-sf-check-state" data-state={checkCell(check)}>{CHECK_STATE[checkCell(check)]}</span></li>)}
            </ul>
          ) : <p className="fm-sf-context">Check results are unavailable for this system.</p>}
        </div>
      )}
    </section>
  )

  const rail = (
    <VStack gap={8}>
      <VStack gap={3}>
        <Heading level={3}>Details</Heading>
        <MetadataList label={{ width: 110 }}>
          <MetadataListItem label="Stage"><Text type="body">{STAGE_LABEL[status === 'pending' ? 'decision' : (s.lifecycleSummary?.stage ?? s.lifecycleStage)] ?? cap(s.lifecycleStage)}</Text></MetadataListItem>
          <MetadataListItem label="Risk tier"><Badge variant={RISK_TONE[s.riskTier]} label={cap(s.riskTier)} /></MetadataListItem>
          <MetadataListItem label="Owner">
            <HStack gap={2} vAlign="center" wrap="wrap">
              <Text type="body">{s.owner || 'No owner'}</Text>
              {!retired && <Button label="Change" variant="secondary" size="sm" onClick={() => { setPanel({ kind: 'owner' }); setRailOpen(false) }} />}
            </HStack>
          </MetadataListItem>
          {kind && <MetadataListItem label="Kind"><Text type="body">{kind}</Text></MetadataListItem>}
          <MetadataListItem label="Source"><Text type="body">{SOURCE_LABEL[sourceKey] ?? cap(sourceKey)}</Text></MetadataListItem>
          <MetadataListItem label="Created"><Text type="body">{when(s.createdAt)}</Text></MetadataListItem>
          {ap.data && <MetadataListItem label="Autopilot"><Text type="body">{ap.data.mode === 'ask' ? 'Ask first' : cap(ap.data.mode)}</Text></MetadataListItem>}
          <MetadataListItem label="Frameworks">
            {frameworks.length ? <HStack gap={1} wrap="wrap">{frameworks.map((f) => <Token key={f} label={f} color="blue" size="sm" />)}</HStack> : <Text type="body" color="secondary">Not chosen</Text>}
          </MetadataListItem>
        </MetadataList>
      </VStack>

      <VStack gap={3}>
        <Heading level={3}>Decisions and seals</Heading>
        <HStack gap={2} vAlign="center" wrap="wrap">
          <Badge variant={REQUEST_TONE[status] ?? 'neutral'} label={cap(status)} />
          {req?.createdAt && <Text type="supporting" color="secondary">since {when(req.createdAt)}</Text>}
        </HStack>
        {(approval?.decisions ?? []).map((d) => (
          <VStack key={d.id} gap={0}>
            <Text type="body" weight="semibold">{cap(d.decision)} by {d.decided_by || 'a reviewer'}</Text>
            <Text type="supporting" color="secondary">{when(d.createdAt)}{d.notes ? `. ${d.notes}` : ''}</Text>
          </VStack>
        ))}
        {seals.length === 0 ? (
          <Text type="supporting" color="secondary">A seal is taken when a decision is recorded.</Text>
        ) : (
          seals.map((sl) => (
            <Card key={sl.id} variant="muted" padding={3}>
              <HStack gap={2} vAlign="center" wrap="wrap">
                <Badge variant={sl.verification.status === 'intact' ? 'green' : 'red'} label={sl.verification.status === 'intact' ? 'Intact' : 'Broken'} />
                <Text type="supporting" color="secondary">{cap(sl.decision)}, {sl.evidenceCount} record{sl.evidenceCount === 1 ? '' : 's'}, {when(sl.createdAt)}</Text>
                <span className="fm-sf-hash">{sl.chainHead.slice(0, 12)}</span>
              </HStack>
              {sl.verification.status === 'broken' && (
                <Text type="supporting" color="secondary">
                  {[sl.verification.changed.length && `${sl.verification.changed.length} changed`, sl.verification.missing.length && `${sl.verification.missing.length} missing`].filter(Boolean).join(', ')} since the seal.
                </Text>
              )}
            </Card>
          ))
        )}
        <Button label="Open the full record" variant="secondary" onClick={() => { setTab('record'); setRailOpen(false) }} />
      </VStack>

      <VStack gap={3}>
        <Heading level={3}>Findings</Heading>
        {risks ? (
          <Text type="body">{recordedOpen.length} open of {risks.summary.total} recorded{risks.suggested.length ? `, ${risks.suggested.length} suggested` : ''}</Text>
        ) : (
          <Text type="supporting" color="secondary">Not available yet</Text>
        )}
        <HStack gap={2} wrap="wrap">
          <Button label="Open findings" variant="secondary" href={`/findings?system=${encodeURIComponent(id)}`} />
          <Button label={`Remediation${remediation ? ` (${remediation.summary.activeTasks})` : ''}`} variant="secondary" onClick={() => open('/remediation')} />
        </HStack>
      </VStack>

      <VStack gap={3}>
        <Heading level={3}>Evidence</Heading>
        <MetadataList label={{ width: 110 }}>
          {evidence && <MetadataListItem label="Linked"><Text type="body">{evidence.linkedEvidence} of {evidence.totalEvidence} to controls</Text></MetadataListItem>}
          {evidence && <MetadataListItem label="Review state"><Text type="body">{READINESS_LABEL[evidence.decisionReadiness] ?? evidence.decisionReadiness}</Text></MetadataListItem>}
          {evidence && evidence.missingSignals.length > 0 && <MetadataListItem label="Missing"><Text type="body">{evidence.missingSignals.join(', ')}</Text></MetadataListItem>}
          <MetadataListItem label="Fairness"><Text type="body">{fairnessRuns.length ? `${fairnessRuns.length} run${fairnessRuns.length === 1 ? '' : 's'}, latest ${when(fairnessRuns[0].createdAt)}` : evaluationRuns.length ? 'No fairness test; see evaluations' : 'Not measured yet'}</Text></MetadataListItem>
          <MetadataListItem label="Evaluations">
            {evaluationRuns.length ? (
              <Text type="body">
                {/* the endpoint returns the newest 20 runs */}
                {evaluationRuns.length >= 20 ? '20+' : evaluationRuns.length} run{evaluationRuns.length === 1 ? '' : 's'}, latest{' '}
                <Link href={`/compliance/evaluations/${encodeURIComponent(evaluationRuns[0].evaluationId)}?system=${encodeURIComponent(id)}`}>{evaluationRuns[0].evaluationId}</Link>{' '}
                {evaluationRuns[0].status} on {when(evaluationRuns[0].createdAt)}
              </Text>
            ) : <Text type="body">None run</Text>}
          </MetadataListItem>
          <MetadataListItem label="Monitoring"><Text type="body">{monitoringRuns.length ? `${monitoringRuns[0].allChecksPass === false ? 'Drifting' : 'Stable'} on ${when(monitoringRuns[0].createdAt)}` : 'None recorded'}</Text></MetadataListItem>
          <MetadataListItem label="Live runs">
            {file.liveRuns?.lastRunAt
              ? <Link onClick={() => setPanel({ kind: 'watch' })}>{`${file.liveRuns.week.runs.toLocaleString()} this week, last run ${when(file.liveRuns.lastRunAt)}`}</Link>
              : <Text type="body">None sent</Text>}
          </MetadataListItem>
          {file.liveRuns?.decisions && (
            <MetadataListItem label="Decisions">
              <Text type="body">{(() => {
                const x = file.liveRuns.decisions.explained
                const tested = x.held + x.notHeld
                return tested ? `${x.held} of ${tested} reasons held` : `${file.liveRuns.decisions.total.toLocaleString()} sent, reasons not checked yet`
              })()}</Text>
            </MetadataListItem>
          )}
          <MetadataListItem label="Environmental"><Text type="body">{env.loading ? 'Checking' : env.data ? `Assessed${envStatus ? `, ${String(envStatus).replace(/_/g, ' ')}` : ''}` : 'No assessment yet'}</Text></MetadataListItem>
          <MetadataListItem label="Audit reports"><Text type="body">{reports.length ? `${reports.length}, latest ${when(reports[0].createdAt)}` : 'None generated'}</Text></MetadataListItem>
        </MetadataList>
        {evidence?.recommendedNextStep && <Text type="supporting" color="secondary">{evidence.recommendedNextStep}</Text>}
        <HStack gap={2} wrap="wrap">
          <Button label="Evidence" variant="secondary" href={`/evidence?system=${encodeURIComponent(id)}`} />
          <Button label="Audit reports" variant="secondary" onClick={() => open('/reports/system?view=assurance')} />
        </HStack>
      </VStack>
    </VStack>
  )

  const drawerBody = (() => {
    if (!panel) return null
    switch (panel.kind) {
      case 'fairness': return <FairnessRunPanel inspect={file.inspectCsv} run={file.runFairness} onDecide={!retired && ((status === 'pending' && req) || canRequest) ? () => openFromExplainer('#decision') : undefined} decideLabel={canRequest ? (status === 'rejected' ? 'Request a new decision' : 'Request release decision') : undefined} />
      case 'monitoring': {
        if (retired || s.lifecycleStage === 'retired') return <Text>This system is retired.</Text>
        const form = <MonitoringRunPanel inspect={file.inspectCsv} run={file.runMonitoring} hasBaseline={fairnessRuns.length > 0} />
        return panel.findingId === undefined ? form : (
          <FindingRetestDraft systemId={id} findingId={panel.findingId} source="fairmind.watch">{form}</FindingRetestDraft>
        )
      }
      case 'watch': return <WatchPanel systemId={id} policy={monitoringPolicy} runs={monitoringRuns} live={file.liveRuns} save={file.saveMonitoringPolicy} />
      case 'target': return <TargetPanel systemId={id} />
      case 'analyses': return <StoredAnalyses systemId={id} sources={['judge', 'advanced']} />
      case 'explain': return gate ? <VerdictExplainer gate={gate} onAttest={(c) => isAttestable(c) && setPanel({ kind: 'attest', check: c })} onOpen={openFromExplainer} /> : null
      case 'attest': return (
        <AttestPanel
          key={panel.check}
          check={panel.check}
          onCancel={() => setPanel(null)}
          onSubmit={async (statement, reference) => {
            await file.attest(panel.check, statement, reference)
            setPanel(null)
          }}
        />
      )
      case 'tier': return (
        <VStack gap={4}>
          <ApplicabilityForm
            autoFocus
            record={applicability}
            currentTier={s.riskTier}
            submitLabel="Confirm"
            onCancel={() => setPanel(null)}
            onSubmit={(body) => act('applicability', async () => {
              await confirmApplicability(s.id, body)
              setPanel(null)
              await refresh()
            })}
          />
        </VStack>
      )
      case 'owner': return (
        <OwnerPanel
          orgId={selectedOrg?.id}
          current={s.owner ?? ''}
          onCancel={() => setPanel(null)}
          onSubmit={async (owner) => {
            await changes.setOwner(owner)
            setPanel(null)
            await refresh()
          }}
        />
      )
      case 'decide': return req && gate ? (
        <DecidePanel
          verdict={gate.verdict}
          blocker={gate.reasons[0]}
          note={override?.text}
          onDecide={async (decision, notes) => {
            await file.recordDecision(req.id, decision, notes)
            setPanel(null)
          }}
          onCancel={() => setPanel(null)}
        />
      ) : null
    }
  })()

  const mainFile = (
    <div className="fm-sf-main">
      {releaseOverview}

      <section className="fm-card fm-sf-checks" aria-labelledby="sf-checks">
        <VStack gap={4}>
          <h2 id="sf-checks" tabIndex={-1}>Release checks</h2>
          {gate && verdict ? (
            <VStack gap={4}>
              <p className="fm-sf-context">Gate confidence <strong>{Math.round(gate.confidence * 100)}%</strong> · {gate.proven} proven · {gate.attested} attested · {gate.open} open{gate.failing ? ` · ${gate.failing} failing` : ''}</p>
              <ul className="fm-sf-check-list">
                {visibleChecks.map((c) => {
                  const cell = checkCell(c)
                  return (
                    <li key={c.key} className="fm-sf-check" data-state={cell}>
                      <div>
                        <h3>{c.label}</h3>
                        {c.evidenceClass && <p>{classLabel(c.evidenceClass)}{c.stale ? ' · Out of date' : ''}</p>}
                        {(c.evidenceId || cell === 'fails') && <CheckEvidenceLinks systemId={gateSystemId} check={c} failed={cell === 'fails'} showRecordId={false} />}
                      </div>
                      <span className="fm-sf-check-state" data-state={cell}>{CHECK_STATE[cell]}</span>
                      {c.key === 'human_oversight' && reasons && (
                        <div className="fm-sf-check-more">
                          <ReasonStack held={Number(reasons.reasonHeld ?? 0)} notHeld={Number(reasons.reasonTested ?? 0) - Number(reasons.reasonHeld ?? 0)}
                            notReproducible={Number(reasons.notReproducible ?? 0)} floor={typeof reasons.minReasonHeld === 'number' ? reasons.minReasonHeld : null} />
                        </div>
                      )}
                    </li>
                  )
                })}
              </ul>
              {gate.reasons.length > 0 && (
                <VStack gap={1}>
                  <Text type="supporting" weight="semibold">Why this verdict</Text>
                  {gate.reasons.map((r) => <Text key={r} type="supporting" color="secondary">{r}</Text>)}
                </VStack>
              )}
              {gate.policy && gate.policy.blocking.length + gate.policy.warnings.length > 0 && (
                <VStack gap={1}>
                  <Text type="supporting" weight="semibold">Policy rules</Text>
                  {[...gate.policy.blocking.map((r) => ({ ...r, blocks: true })), ...gate.policy.warnings.map((r) => ({ ...r, blocks: false }))].map((r) => (
                    <HStack key={`${r.policyId}:${r.ruleId}`} gap={2} vAlign="center" wrap="wrap">
                      <Badge variant={r.blocks ? 'red' : 'orange'} label={r.blocks ? 'Blocks release' : 'Warning'} />
                      <Text type="supporting">{r.ruleTitle}</Text>
                      <Link href={`/policies/${r.policyId}`} type="supporting">{r.policyName}</Link>
                      {r.detail && <Text type="supporting" color="secondary">{r.detail}</Text>}
                    </HStack>
                  ))}
                </VStack>
              )}
              <div className="fm-sf-embed"><LeavesOpen clauseMap={clauseMap} /></div>
              <HStack><Button label="How the verdict was reached" variant="secondary" size="sm" onClick={() => setPanel({ kind: 'explain' })} /></HStack>
            </VStack>
          ) : (
            <EmptyState isCompact title="Release gate not available yet" description="The gate could not be read for this system." actions={<Button label="Try again" variant="secondary" onClick={() => void refresh()} />} />
          )}
        </VStack>
      </section>

      {file.liveRuns?.decisions && (
        <section className="fm-card" aria-labelledby="sf-decisions">
          <VStack gap={4}>
            <HStack gap={3} hAlign="between" vAlign="center" wrap="wrap">
              <Heading level={2} id="sf-decisions">Decisions</Heading>
              <Text type="supporting" color="secondary">Last {file.liveRuns.days.length} days</Text>
            </HStack>
            <DecisionsCard d={file.liveRuns.decisions} latest={reasons ?? undefined} onOpen={() => open('/compliance/evaluations/EV-OVS-04?source=traces')} />
          </VStack>
        </section>
      )}

      {versions}

      <section className="fm-card" aria-labelledby="sf-needs">
        <VStack gap={4}>
          <HStack gap={2} vAlign="center" hAlign="between" wrap="wrap">
            <Heading level={2} id="sf-needs">Next steps</Heading>
            {option && <Text type="supporting" color="secondary">Confidence <span className="fm-sf-num">{gate?.confidence.toFixed(2)}</span> to <span className="fm-sf-num">{option.confidenceAfter.toFixed(2)}</span>, {VERDICT_META[option.verdictAfter].label}</Text>}
          </HStack>
          {gate && option && option.steps.length > 0 ? (
            <VStack gap={2}>
              {option.steps.map((step, i) => {
                const who = stepWho(step, ap.data?.steps)
                return (
                  <div key={`${step.check}:${step.action}`} className="fm-sf-step">
                    <span className="fm-sf-step-n">{i + 1}</span>
                    <VStack gap={0}>
                      <Text type="body" weight="semibold">{stepTitle(step, gate)}</Text>
                      <Text type="supporting" color="secondary">{stepLine(step)}</Text>
                      <HStack gap={1} wrap="wrap">
                        <Badge variant={who === 'agent' ? 'blue' : 'orange'} label={who === 'agent' ? 'Agent' : 'Person'} />
                        <Badge variant="green" label={`+${step.gain.toFixed(2)}`} />
                      </HStack>
                    </VStack>
                    {stepButton(step)}
                  </div>
                )
              })}
            </VStack>
          ) : gate ? (
            <Text type="body" color="secondary">{gate.verdict === 'go' ? 'Nothing more is needed for a go.' : 'No steps FairMind can record today move the verdict up.'}</Text>
          ) : null}
          {gate?.path && gate.path.approvalBlockers.length > 0 && (
            <VStack gap={1}>
              <Text type="supporting" weight="semibold">Before a decision can be approved</Text>
              {gate.path.approvalBlockers.map((b) => (
                <HStack key={b.key} gap={2} vAlign="center">
                  <Badge variant={b.met ? 'green' : 'red'} label={b.met ? 'Met' : 'Open'} />
                  <Text type="supporting">{b.text}</Text>
                </HStack>
              ))}
            </VStack>
          )}
          {gate?.path && (
            <VStack gap={1}>
              <Text type="supporting" color="secondary">Highest reachable today: {VERDICT_META[gate.path.ceiling.verdict].label} at <span className="fm-sf-num">{gate.path.ceiling.confidence.toFixed(2)}</span>.</Text>
              {gate.path.notes.map((n) => <Text key={n} type="supporting" color="secondary">{n}</Text>)}
            </VStack>
          )}
          <details className="fm-sf-disclosure">
            <summary>More assessment actions <ChevronDown size={15} aria-hidden /></summary>
            <HStack gap={2} wrap="wrap">
            <Button label="Run a fairness test" variant="secondary" size="sm" onClick={() => setPanel({ kind: 'fairness' })} />
            <Button label="Record a monitoring snapshot" variant="secondary" size="sm" onClick={() => setPanel({ kind: 'monitoring' })} />
            <Button label="Monitoring and live runs" variant="secondary" size="sm" onClick={() => setPanel({ kind: 'watch' })} />
            <Button label="Model connection" variant="secondary" size="sm" onClick={() => setPanel({ kind: 'target' })} />
            <Button label="Stored analyses" variant="secondary" size="sm" onClick={() => setPanel({ kind: 'analyses' })} />
            <Button label="Open plan" variant="secondary" size="sm" href={`/systems/${encodeURIComponent(id)}/plan`} />
            <Button label="Run an evaluation" variant="secondary" size="sm" onClick={() => open('/evaluations')} />
            <Button label="Frameworks" variant="secondary" size="sm" href="/frameworks" />
            <Button label="Workflow runs" variant="secondary" size="sm" href="/runs" />
            <Button label="Monitoring" variant="secondary" size="sm" onClick={() => open('/monitoring')} />
            </HStack>
          </details>
        </VStack>
      </section>

      <section className="fm-card" aria-labelledby="sf-what">
        <VStack gap={3}>
          <Heading level={2} id="sf-what">About this system</Heading>
          {description && <Text type="body">{description}</Text>}
          <Text type="supporting" color="secondary">
            {[kind, SOURCE_LABEL[sourceKey] ?? cap(sourceKey), s.createdAt ? `Created ${when(s.createdAt)}` : ''].filter(Boolean).join(' · ')}
          </Text>
          <HStack gap={2} vAlign="center" wrap="wrap">
            <Text type="supporting" color="secondary">{applicability ? tierBasis(applicability) : 'Tier unconfirmed'}</Text>
            <Button label={applicability ? 'Change tier or rules' : 'Confirm tier and rules'} variant="secondary" size="sm" onClick={() => setPanel({ kind: 'tier' })} />
            {awaitingSecond && applicability && (
              <Button label="Accept the lower tier" variant="secondary" size="sm" isDisabled={busy !== null} isLoading={busy === 'accept'} onClick={() => void act('accept', async () => { await acceptOverride(id, applicability.evidenceId); await refresh() })} />
            )}
          </HStack>
          {override && <Text type="supporting" color="secondary">{override.text}</Text>}
        </VStack>
      </section>

      <section className="fm-card fm-sf-embed" aria-label="Autopilot">
        <AutopilotCard
          systemId={id}
          reloadKey={`${gate?.confidence ?? ''}-${evidence?.totalEvidence ?? 0}`}
          onChanged={() => { void refresh(); void ap.reload() }}
          onPersonStep={(step) => {
            if (step.action === 'attest') return isAttestable(step.check) && setPanel({ kind: 'attest', check: step.check })
            if (step.action === 'request_release') return void act('request', file.requestDecision)
            if (step.action === 'fairness_run') return setPanel({ kind: 'fairness' })
            if (step.action === 'monitoring_snapshot') return setPanel({ kind: 'monitoring' })
            if (step.action === 'evaluation_run') return open(step.evaluationId ? `/compliance/evaluations/${encodeURIComponent(step.evaluationId)}` : '/evaluations')
            if (step.action === 'environmental_assessment') return router.push(`/environment?system=${encodeURIComponent(id)}`)
            return router.push(`/evidence?system=${encodeURIComponent(id)}&check=${step.check}`)
          }}
        />
      </section>

      <section className="fm-card" aria-labelledby="sf-trace">
        <VStack gap={4}>
          <Heading level={2} id="sf-trace">Agent and people trace</Heading>
          {trace.length === 0 ? (
            <Text type="body" color="secondary">Nothing recorded yet. Autopilot steps and release decisions appear here, newest first.</Text>
          ) : (
            <ol className="fm-sf-trace">
              {trace.map((e) => (
                <li key={e.key}>
                  <HStack gap={3} vAlign="start">
                    <Avatar name={e.who} size="sm" />
                    <StackItem size="fill">
                      <VStack gap={0}>
                        <HStack gap={2} vAlign="center" wrap="wrap">
                          <Text type="body" weight="semibold">{e.who}</Text>
                          {e.failed && <Badge variant="red" label="Failed" />}
                          <Text type="supporting" color="secondary">{when(e.at)}</Text>
                        </HStack>
                        <Text type="supporting" color="secondary">{e.body}</Text>
                      </VStack>
                    </StackItem>
                  </HStack>
                </li>
              ))}
            </ol>
          )}
        </VStack>
      </section>
    </div>
  )

  return (
    <div className="fm-system-file">
      <VStack gap={5}>
        <header className="fm-sf-header">
          <div className="fm-sf-header-bar">
            <NextLink href="/systems" className="fm-sf-crumb"><ArrowLeft size={15} aria-hidden /> AI systems</NextLink>
            <div className="fm-sf-tools">
              <Pill type="button" variant="outline" className="fm-sf-details-button" onClick={() => setRailOpen(true)}>Details</Pill>
              {!retired && (
                <details className="fm-sf-manage">
                  <summary>Manage system <ChevronDown size={15} aria-hidden /></summary>
                  <div>
                    {showRequestInMenu && primary}
                    {lifecycleActions}
                  </div>
                </details>
              )}
            </div>
          </div>
          <HStack gap={3} hAlign="between" vAlign="center" wrap="wrap">
            <h1>{s.name}</h1>
            <Pill asChild variant="outline" size="lg" className="px-4">
              <NextLink href={`/reports/system?system=${encodeURIComponent(id)}`} aria-label="Prepare system assurance report">
                System assurance report
              </NextLink>
            </Pill>
          </HStack>
          <dl className="fm-sf-identity">
            <div><dt>Owner</dt><dd>{s.owner || 'Unassigned'}</dd></div>
            <div><dt>Risk</dt><dd>{cap(s.riskTier)}</dd></div>
            <div><dt>Stage</dt><dd>{STAGE_LABEL[s.lifecycleSummary?.stage ?? s.lifecycleStage] ?? cap(s.lifecycleStage)}</dd></div>
          </dl>
        </header>

        <TabList value={tab} onChange={setTab} hasDivider>
          <Tab value="file" label="System file" />
          <Tab value="requirements" label="Requirements" />
          <Tab value="record" label="Record" />
        </TabList>

        {actionError && <Banner status="error" title="That did not work" description={actionError} isDismissable onDismiss={() => setActionError(null)} />}
        {tab === 'file' && (retired ? (
          <div className="fm-sf-main">
            <RetiredCard record={retired} createdAt={s.createdAt} replacementName={systems.find((o) => o.id === retired.replacedBy)?.name} chain={retirement.data?.chain} />
            {versions}
          </div>
        ) : mainFile)}
        {tab === 'requirements' && (
          <div className="fm-sf-embed">
            <RequirementsTab confirmed={applicability?.frameworks ?? clauseMap?.confirmed ?? []} clauseMap={clauseMap}
              onConfirmRules={retired ? undefined : () => setPanel({ kind: 'tier' })} />
          </div>
        )}
        {tab === 'record' && (
          <div className="fm-sf-main fm-sf-embed">
            <RecordTab seals={seals} approval={approval} />
            <SystemReviewHistory systemId={id} risks={risks} />
          </div>
        )}
      </VStack>

      <Drawer isOpen={panel !== null} onOpenChange={(o) => !o && setPanel(null)} label={panel ? PANEL_TITLE[panel.kind] : 'Panel'} width={560} padding={5}>
        {panel && (
          <VStack gap={4}>
            <Heading level={2}>{PANEL_TITLE[panel.kind]}</Heading>
            <div className="fm-sf-embed">{drawerBody}</div>
          </VStack>
        )}
      </Drawer>

      <Drawer isOpen={!isNarrow && railOpen} onOpenChange={setRailOpen} label="System details" width={460} padding={5}>
        {railOpen && rail}
      </Drawer>
      <Dialog variant="fullscreen" isOpen={isNarrow && railOpen} onOpenChange={setRailOpen}>
        <Layout
          header={<DialogHeader title="System details" onOpenChange={setRailOpen} />}
          content={<LayoutContent padding={4}>{rail}</LayoutContent>}
        />
      </Dialog>
    </div>
  )
}

/** Record the release decision: approve or reject with notes. A conditional go needs the conditions in writing. */
function DecidePanel({ verdict, blocker, note, onDecide, onCancel }: {
  verdict: 'go' | 'conditional_go' | 'no_go'
  blocker?: string
  note?: string
  onDecide: (decision: 'approved' | 'rejected', notes: string) => Promise<void>
  onCancel: () => void
}) {
  const [notes, setNotes] = useState('')
  const [busy, setBusy] = useState<'approved' | 'rejected' | null>(null)
  const [error, setError] = useState<string | null>(null)
  const conditional = verdict === 'conditional_go'
  const send = async (d: 'approved' | 'rejected') => {
    setBusy(d)
    setError(null)
    try {
      await onDecide(d, notes.trim())
    } catch (e) {
      setError(e instanceof Error ? e.message : 'Could not record the decision')
      setBusy(null)
    }
  }
  return (
    <VStack gap={4}>
      {error && <Banner status="error" title="Not recorded" description={error} />}
      {verdict === 'no_go' && <Banner status="warning" title="Approval is blocked" description={`${blocker?.replace(/\.$/, '') ?? 'The release gate says no go'}.`} />}
      {note && <Text type="supporting" color="secondary">{note}</Text>}
      <TextArea
        label={conditional ? 'Conditions' : 'Notes'}
        description={conditional ? 'The gate reads conditional go. Say what has to hold for this release to stay approved; it is recorded with your decision.' : 'Recorded with your decision and sealed with the evidence.'}
        isOptional={!conditional}
        value={notes}
        onChange={setNotes}
        rows={4}
      />
      <HStack gap={2}>
        <Button label="Approve release" variant="primary" isDisabled={busy !== null || verdict === 'no_go' || (conditional && notes.trim().length === 0)} isLoading={busy === 'approved'} onClick={() => void send('approved')} />
        <Button label="Reject" variant="destructive" isDisabled={busy !== null} isLoading={busy === 'rejected'} onClick={() => void send('rejected')} />
        <Button label="Cancel" variant="secondary" onClick={onCancel} />
      </HStack>
    </VStack>
  )
}
