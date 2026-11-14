'use client'

import '@/astryx/pages/system-file.css'
import NextLink from 'next/link'
import { useParams, useRouter } from 'next/navigation'
import { useEffect, useMemo, useRef, useState, type ReactNode } from 'react'
import { useMediaQuery } from '@astryxdesign/core/hooks'
import { Avatar } from '@astryxdesign/core/Avatar'
import { Badge } from '@astryxdesign/core/Badge'
import { Banner } from '@astryxdesign/core/Banner'
import { Button } from '@astryxdesign/core/Button'
import { Card } from '@astryxdesign/core/Card'
import { Dialog, DialogHeader } from '@astryxdesign/core/Dialog'
import { Divider } from '@astryxdesign/core/Divider'
import { Drawer } from '@astryxdesign/core/Drawer'
import { EmptyState } from '@astryxdesign/core/EmptyState'
import { HStack, StackItem, VStack } from '@astryxdesign/core/Layout'
import { Layout, LayoutContent } from '@astryxdesign/core/Layout'
import { Link } from '@astryxdesign/core/Link'
import { MetadataList, MetadataListItem } from '@astryxdesign/core/MetadataList'
import { ProgressBar } from '@astryxdesign/core/ProgressBar'
import { Skeleton } from '@astryxdesign/core/Skeleton'
import { Tab, TabList } from '@astryxdesign/core/TabList'
import { Heading, Text } from '@astryxdesign/core/Text'
import { TextArea } from '@astryxdesign/core/TextArea'
import { Token } from '@astryxdesign/core/Token'
import { useOrg } from '@/context/OrgContext'
import { useSystemContext } from '@/components/workflow/SystemContext'
import { ApplicabilityForm } from '@/components/workflow/ApplicabilityForm'
import { StoredAnalyses } from '@/components/workflow/StoredAnalyses'
import { checkCell, classLabel } from '@/components/ui/matrix'
import { shortFrameworkName, tierBasis, useApplicability } from '@/lib/api/hooks/useApplicability'
import { useAutopilot } from '@/lib/api/hooks/useAutopilot'
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
import { TargetPanel } from './TargetPanel'
import { RequirementsTab } from './RequirementsTab'
import { RecordTab } from './RecordTab'
import { LeavesOpen } from './LeavesOpen'
import { VerdictExplainer, stepLine, stepTitle, tierOverride } from './VerdictExplainer'

// Environmental is left out: an attestation would shadow any later assessment, which the path recommends instead.
const ATTESTABLE = new Set<string>(['data_governance', 'human_oversight', 'monitoring'])
const isAttestable = (key: string): key is AttestableCheck => ATTESTABLE.has(key)

const CELL_VARIANT = { proven: 'success', attested: 'success', estimated: 'accent', fails: 'error', stale: 'warning' } as const
const READINESS_LABEL: Record<string, string> = {
  empty: 'No evidence yet',
  needs_evidence: 'Needs evidence',
  collected: 'Evidence collected, not yet linked',
  linked: 'Evidence linked to controls',
  review_ready: 'Review-ready',
}
const REQUEST_TONE = { not_requested: 'neutral', pending: 'orange', approved: 'green', rejected: 'red' } as const

type Panel =
  | { kind: 'fairness' | 'monitoring' | 'watch' | 'target' | 'analyses' | 'explain' | 'tier' | 'decide' }
  | { kind: 'attest'; check: AttestableCheck }

const PANEL_TITLE: Record<Panel['kind'], string> = {
  fairness: 'Run a fairness test',
  monitoring: 'Record a monitoring snapshot',
  watch: 'Monitoring cadence',
  target: 'Fairness target',
  analyses: 'Stored analyses',
  explain: 'How the verdict was reached',
  tier: 'Tier and rules',
  decide: 'Release decision',
  attest: 'Attest a check',
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
  const file = useSystemFile(id)
  const { system, evidence, approval, remediation, risks, reports, gate, fairnessRuns, monitoringRuns, monitoringPolicy, seals, clauseMap, loading, error, refresh } = file
  const ap = useAutopilot(id, `${gate?.confidence ?? ''}-${evidence?.totalEvidence ?? 0}-${approval?.decisions.length ?? 0}`)
  const { confirm: confirmApplicability, acceptOverride } = useApplicability()
  const env = useEnvironmentalImpact(selectedOrg?.id, id)

  const [panel, setPanel] = useState<Panel | null>(null)
  const [tab, setTab] = useState<'file' | 'requirements' | 'record'>('file')
  const [busy, setBusy] = useState<string | null>(null)
  const [actionError, setActionError] = useState<string | null>(null)
  const [railOpen, setRailOpen] = useState(false)
  const isNarrow = useMediaQuery('(max-width: 1024px)')

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
      <div className="fm-page">
        <VStack gap={4}>
          <Skeleton width={220} height={14} />
          <Skeleton width={420} height={34} />
          <Skeleton width="100%" height={220} />
        </VStack>
      </div>
    )
  }
  if (error || !system) {
    return (
      <div className="fm-page">
        <EmptyState
          title="This system is not in your estate"
          description={error || 'It may belong to another organisation or have been removed.'}
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
  const recordedOpen = (risks?.risks ?? []).filter((r) => !['accepted', 'closed', 'resolved', 'mitigated'].includes(r.status))
  const envRec = env.data?.recommendation
  const envStatus = typeof envRec === 'string' ? envRec : envRec?.status
  const canRequest = status === 'not_requested' || status === 'rejected'

  const stepButton = (step: GatePathStep): ReactNode => {
    switch (step.action) {
      case 'fairness_run': return <Button label="Run the test" variant="secondary" onClick={() => setPanel({ kind: 'fairness' })} />
      case 'monitoring_snapshot': return <Button label="Record a snapshot" variant="secondary" onClick={() => setPanel({ kind: 'monitoring' })} />
      case 'attest': return isAttestable(step.check) ? <Button label="Attest" variant="secondary" onClick={() => setPanel({ kind: 'attest', check: step.check as AttestableCheck })} /> : null
      case 'environmental_assessment': return <Button label="Open assessment" variant="secondary" href={`/environment?system=${encodeURIComponent(id)}`} />
      case 'evidence_upload': return <Button label="Record evidence" variant="secondary" href={`/evidence?system=${encodeURIComponent(id)}`} />
    }
  }

  const primary = canRequest
    ? <Button label={status === 'rejected' ? 'Request a new decision' : 'Request release decision'} variant="primary" isDisabled={busy !== null} isLoading={busy === 'request'} onClick={() => void act('request', file.requestDecision)} />
    : status === 'pending' && req
      ? <Button label="Decide" variant="primary" onClick={() => setPanel({ kind: 'decide' })} />
      : null

  const rail = (
    <VStack gap={8}>
      <VStack gap={3}>
        <Heading level={3}>Details</Heading>
        <MetadataList label={{ width: 110 }}>
          <MetadataListItem label="Stage"><Text type="body">{STAGE_LABEL[status === 'pending' ? 'decision' : (s.lifecycleSummary?.stage ?? s.lifecycleStage)] ?? cap(s.lifecycleStage)}</Text></MetadataListItem>
          <MetadataListItem label="Risk tier"><Badge variant={RISK_TONE[s.riskTier]} label={cap(s.riskTier)} /></MetadataListItem>
          <MetadataListItem label="Owner"><Text type="body">{s.owner || 'No owner'}</Text></MetadataListItem>
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
          <MetadataListItem label="Fairness"><Text type="body">{fairnessRuns.length ? `${fairnessRuns.length} run${fairnessRuns.length === 1 ? '' : 's'}, latest ${when(fairnessRuns[0].createdAt)}` : 'Not measured yet'}</Text></MetadataListItem>
          <MetadataListItem label="Monitoring"><Text type="body">{monitoringRuns.length ? `${monitoringRuns[0].allChecksPass === false ? 'Drifting' : 'Stable'} on ${when(monitoringRuns[0].createdAt)}` : 'None recorded'}</Text></MetadataListItem>
          <MetadataListItem label="Environmental"><Text type="body">{env.loading ? 'Checking' : env.data ? `Assessed${envStatus ? `, ${String(envStatus).replace(/_/g, ' ')}` : ''}` : 'No assessment yet'}</Text></MetadataListItem>
          <MetadataListItem label="Audit reports"><Text type="body">{reports.length ? `${reports.length}, latest ${when(reports[0].createdAt)}` : 'None generated'}</Text></MetadataListItem>
        </MetadataList>
        {evidence?.recommendedNextStep && <Text type="supporting" color="secondary">{evidence.recommendedNextStep}</Text>}
        <HStack gap={2} wrap="wrap">
          <Button label="Evidence" variant="secondary" href={`/evidence?system=${encodeURIComponent(id)}`} />
          <Button label="Audit reports" variant="secondary" onClick={() => open('/audit-reports')} />
        </HStack>
      </VStack>
    </VStack>
  )

  const drawerBody = (() => {
    if (!panel) return null
    switch (panel.kind) {
      case 'fairness': return <FairnessRunPanel inspect={file.inspectCsv} run={file.runFairness} />
      case 'monitoring': return <MonitoringRunPanel inspect={file.inspectCsv} run={file.runMonitoring} hasBaseline={fairnessRuns.length > 0} />
      case 'watch': return <WatchPanel systemId={id} policy={monitoringPolicy} runs={monitoringRuns} save={file.saveMonitoringPolicy} />
      case 'target': return <TargetPanel systemId={id} />
      case 'analyses': return <StoredAnalyses systemId={id} sources={['judge', 'advanced']} />
      case 'explain': return gate ? <VerdictExplainer gate={gate} onAttest={(c) => isAttestable(c) && setPanel({ kind: 'attest', check: c })} onOpen={(href) => { setPanel(null); if (!href.startsWith('#')) open(href) }} /> : null
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
    <div className="fm-sf-main" hidden={tab !== 'file'}>
      {actionError && <Banner status="error" title="That did not work" description={actionError} isDismissable onDismiss={() => setActionError(null)} />}

      <section className="fm-card" aria-labelledby="sf-what">
        <VStack gap={4}>
          <Heading level={2} id="sf-what">What it is</Heading>
          {description && <Text type="body">{description}</Text>}
          <Text type="supporting" color="secondary">
            {[kind, SOURCE_LABEL[sourceKey] ?? cap(sourceKey), s.createdAt ? `created ${when(s.createdAt)}` : ''].filter(Boolean).join(' · ')}
          </Text>
          <HStack gap={2} vAlign="center" wrap="wrap">
            <Text type="supporting" color="secondary">{applicability ? tierBasis(applicability) : 'Tier not confirmed'}</Text>
            <Button label={applicability ? 'Change tier or rules' : 'Confirm tier and rules'} variant="secondary" size="sm" onClick={() => setPanel({ kind: 'tier' })} />
            {awaitingSecond && applicability && (
              <Button label="Accept the lower tier" variant="secondary" size="sm" isDisabled={busy !== null} isLoading={busy === 'accept'} onClick={() => void act('accept', async () => { await acceptOverride(id, applicability.evidenceId); await refresh() })} />
            )}
          </HStack>
          {override && <Text type="supporting" color="secondary">{override.text}</Text>}

          <Divider />
          {gate && verdict ? (
            <VStack gap={4}>
              <HStack gap={3} vAlign="center" wrap="wrap">
                <Heading level={3}>Release gate</Heading>
                <Badge variant={verdict.tone} label={verdict.label} />
                <Text type="supporting" color="secondary">Confidence <span className="fm-sf-num">{gate.confidence.toFixed(2)}</span>, {gate.band}. {gate.proven} proven, {gate.attested} attested, {gate.open} open.</Text>
              </HStack>
              <VStack gap={3}>
                {gate.checks.map((c) => {
                  const cell = checkCell(c)
                  const how = c.evidenceClass ? classLabel(c.evidenceClass) : cap(c.state)
                  return (
                    <div key={c.key} className="fm-sf-check">
                      <VStack gap={0}>
                        <Text type="body" weight="semibold">{c.label}</Text>
                        <Text type="supporting" color="secondary">
                          {how}{c.stale ? ', out of date' : ''}{c.fails ? ', fails its thresholds' : ''}
                        </Text>
                      </VStack>
                      <ProgressBar label={`${c.label} confidence`} isLabelHidden value={Math.round(c.confidence * 100)} variant={(CELL_VARIANT as Record<string, 'success' | 'accent' | 'error' | 'warning'>)[cell] ?? 'neutral'} />
                      <Text type="body" hasTabularNumbers>{c.state === 'open' && !c.confidence ? 'Open' : c.confidence.toFixed(2)}</Text>
                    </div>
                  )
                })}
              </VStack>
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

      <section className="fm-card" aria-labelledby="sf-needs">
        <VStack gap={4}>
          <HStack gap={2} vAlign="center" hAlign="between" wrap="wrap">
            <Heading level={2} id="sf-needs">What it needs</Heading>
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
          <Divider />
          <HStack gap={2} wrap="wrap">
            <Button label="Run a fairness test" variant="secondary" size="sm" onClick={() => setPanel({ kind: 'fairness' })} />
            <Button label="Record a monitoring snapshot" variant="secondary" size="sm" onClick={() => setPanel({ kind: 'monitoring' })} />
            <Button label="Monitoring cadence" variant="secondary" size="sm" onClick={() => setPanel({ kind: 'watch' })} />
            <Button label="Fairness target" variant="secondary" size="sm" onClick={() => setPanel({ kind: 'target' })} />
            <Button label="Stored analyses" variant="secondary" size="sm" onClick={() => setPanel({ kind: 'analyses' })} />
            <Button label="Open plan" variant="secondary" size="sm" href={`/systems/${encodeURIComponent(id)}/plan`} />
            <Button label="Run an evaluation" variant="secondary" size="sm" onClick={() => open('/tests')} />
            <Button label="Frameworks" variant="secondary" size="sm" href="/frameworks" />
            <Button label="Workflow runs" variant="secondary" size="sm" href="/runs" />
            <Button label="Monitoring" variant="secondary" size="sm" onClick={() => open('/monitoring')} />
          </HStack>
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
            if (step.action === 'environmental_assessment') return router.push(`/environment?system=${encodeURIComponent(id)}`)
            return router.push(`/evidence?system=${encodeURIComponent(id)}`)
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
    <div className="fm-page">
      <VStack gap={5}>
        <VStack gap={2}>
          <HStack gap={2} vAlign="center" className="fm-sf-crumb">
            <NextLink href="/systems">AI systems</NextLink>
            <span aria-hidden>/</span>
            <span>{s.name}</span>
          </HStack>
          <HStack gap={4} hAlign="between" vAlign="start" wrap="wrap">
            <Heading level={1} maxLines={2}>{s.name}</Heading>
            <HStack gap={2} vAlign="center">
              {primary}
              <span className="fm-sf-rail-toggle"><Button label="Details" variant="secondary" onClick={() => setRailOpen(true)} /></span>
            </HStack>
          </HStack>
          <HStack gap={2} vAlign="center" wrap="wrap">
            {verdict && <Badge variant={verdict.tone} label={verdict.label} />}
            <Badge variant={RISK_TONE[s.riskTier]} label={`${cap(s.riskTier)} risk`} />
            <HStack gap={1} vAlign="center">
              <Avatar name={s.owner || 'No owner'} size="xsm" />
              <Text type="supporting" color="secondary">{s.owner || 'No owner'}</Text>
            </HStack>
            {frameworks.map((f) => <Token key={f} label={f} color="blue" size="sm" />)}
          </HStack>
        </VStack>

        <TabList value={tab} onChange={(v) => setTab(v as typeof tab)} hasDivider>
          <Tab value="file" label="System file" />
          <Tab value="requirements" label="Requirements" />
          <Tab value="record" label="Record" />
        </TabList>

        <div className="fm-sf">
          <div className="fm-sf-main">
            {mainFile}
            {tab === 'requirements' && (
              <div className="fm-sf-embed"><RequirementsTab confirmed={applicability?.frameworks ?? clauseMap?.confirmed ?? []} clauseMap={clauseMap} /></div>
            )}
            {tab === 'record' && <div className="fm-sf-embed"><RecordTab seals={seals} approval={approval} /></div>}
          </div>
          <aside className="fm-sf-rail" aria-label="System details">{rail}</aside>
        </div>
      </VStack>

      <Drawer isOpen={panel !== null} onOpenChange={(o) => !o && setPanel(null)} label={panel ? PANEL_TITLE[panel.kind] : 'Panel'} width={560} padding={5}>
        {panel && (
          <VStack gap={4}>
            <Heading level={2}>{PANEL_TITLE[panel.kind]}</Heading>
            <div className="fm-sf-embed">{drawerBody}</div>
          </VStack>
        )}
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
