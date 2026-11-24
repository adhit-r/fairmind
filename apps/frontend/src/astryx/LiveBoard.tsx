'use client'

import { pollWhileVisible } from '@/lib/poll'
import './board.css'
import Link from 'next/link'
import { useSearchParams } from 'next/navigation'
import { Suspense, useEffect, useMemo, useState } from 'react'
import { ArrowRight, ArrowUpRight, ChevronDown } from 'lucide-react'
import { Button } from '@astryxdesign/core/Button'
import { Drawer } from '@astryxdesign/core/Drawer'
import { EmptyState } from '@astryxdesign/core/EmptyState'
import { Heading, Text } from '@astryxdesign/core/Text'
import { MetadataList, MetadataListItem } from '@astryxdesign/core/MetadataList'
import { Skeleton } from '@astryxdesign/core/Skeleton'
import { Token } from '@astryxdesign/core/Token'
import { VStack } from '@astryxdesign/core/Layout'
import { useSystemContext } from '@/components/workflow/SystemContext'
import { CheckEvidenceLinks } from '@/components/workflow/CheckEvidenceLinks'
import { HomeFailureBreakdown, HomeFailureEvidence, useHomeFailureRecord } from '@/components/workflow/HomeFailureEvidence'
import { Card } from '@/components/ui/card'
import { useOrg } from '@/context/OrgContext'
import { HomeCheckMatrix } from '@/astryx/HomeCheckMatrix'
import { HomeLifecycleChart } from '@/astryx/HomeLifecycleChart'
import { useEstateGates, type EstateGate } from '@/lib/api/hooks/useEstate'
import { useNeedsYou } from '@/astryx/data/needsYou'
import type { GateCheck } from '@/lib/api/hooks/useSystemFile'
import { checkCell, classLabel, KIND_TITLE, type CellState } from '@/components/ui/matrix'

/** The release checks the gate can score (environmental only where the organisation weighs it), in the order the release story reads, then the decision. */
const CHECKS: Array<{ key: GateCheck['key']; name: string; group: string }> = [
  { key: 'data_governance', name: 'Data governance', group: 'Data' },
  { key: 'fairness', name: 'Fairness', group: 'Test' },
  { key: 'human_oversight', name: 'Human oversight', group: 'Test' },
  { key: 'environmental', name: 'Environment', group: 'Test' },
  { key: 'monitoring', name: 'Monitoring', group: 'Operate' },
]
type Col = { key: string; name: string; group: string }
const ALL_COLS: Col[] = [...CHECKS.slice(0, 4), { key: 'decision', name: 'Decision', group: 'Release' }, CHECKS[4]]

/** A decision cell: approved is proven; a pending request waits on a person; a rejection fails. */
type DecisionState = 'proven' | 'needs' | 'fails' | 'planned'
function decisionCell(status: string | null | undefined): DecisionState {
  if (status === 'approved') return 'proven'
  if (status === 'pending') return 'needs'
  if (status === 'rejected') return 'fails'
  return 'planned'
}
const DECISION_WORD: Record<DecisionState, string> = {
  proven: 'Approved',
  needs: 'Waiting for a reviewer',
  fails: 'Rejected',
  planned: 'Not requested',
}
const WORD: Record<CellState | 'unavailable', string> = {
  proven: 'Proven',
  estimated: 'Estimated',
  partial: 'Partial',
  attested: 'Attested',
  excluded: 'Excluded',
  planned: 'Planned',
  open: 'Nothing on file',
  fails: 'Fails',
  stale: 'Out of date',
  atorg: 'Held at organisation',
  unavailable: 'Check result unavailable',
}
const TOKEN: Record<string, 'green' | 'red' | 'orange' | 'blue' | 'gray'> = {
  proven: 'green',
  estimated: 'blue',
  attested: 'green',
  fails: 'red',
  stale: 'orange',
  needs: 'orange',
}

function wordFor(col: Col, state: string) {
  return col.key === 'decision' ? DECISION_WORD[state as DecisionState] : WORD[state as keyof typeof WORD]
}

function selectBoardCell(systemId?: string, check?: string) {
  const url = new URL(window.location.href)
  if (systemId && check) {
    url.searchParams.set('system', systemId)
    url.searchParams.set('check', check)
  } else {
    url.searchParams.delete('system')
    url.searchParams.delete('check')
  }
  window.history.replaceState(null, '', url)
}

/** Every registered system against every release check, from the release gate of each. */
export function LiveBoard() {
  return <Suspense fallback={<Skeleton height={112} />}><EstateBoard /></Suspense>
}

function EstateBoard() {
  const { systems, loading: systemsLoading, error: systemsError, refreshSystems } = useSystemContext()
  const { selectedOrg } = useOrg()
  const gates = useEstateGates()
  // The menu's Needs you counts everything waiting on a person; the release card counts decisions only.
  const inbox = useNeedsYou()
  const params = useSearchParams()
  const [checkedAt, setCheckedAt] = useState<Date | null>(null)

  // The board is live: it re-reads the gates every minute and says when it last did.
  useEffect(() => {
    if (gates.data) setCheckedAt(new Date())
  }, [gates.data])
  useEffect(() => {
    return pollWhileVisible(() => gates.reload(), 60_000)
  }, [gates])

  const active = useMemo(() => systems.filter((s) => s.stage !== 'retired'), [systems])
  const rows = useMemo(() => {
    const gateList = Array.isArray(gates.data) ? gates.data : []
    const byId = new Map(gateList.filter((g) => Array.isArray(g?.checks)).map((g) => [g.systemId, g]))
    return active.flatMap((s) => {
      const gate = byId.get(s.id)
      return gate ? [{ system: s, gate }] : []
    })
  }, [active, gates.data])
  // An organisation that keeps energy use out of its release gate gets no Environment column.
  const COLS = rows.some(({ gate }) => gate.checks.some((c) => c.key === 'environmental')) ? ALL_COLS : ALL_COLS.filter((c) => c.key !== 'environmental')

  const stateOf = (gate: EstateGate, col: Col): string => {
    if (col.key === 'decision') return decisionCell(gate.approvalStatus)
    const check = gate.checks.find((c) => c.key === col.key)
    return check ? checkCell(check) : 'unavailable'
  }
  const failures = rows.flatMap(({ system, gate }) => gate.checks
    .filter((check) => checkCell(check) === 'fails')
    .map((check) => ({ system, check })))
  const lead = failures[0]
  const proof = useHomeFailureRecord(lead?.system.id, lead?.check)

  if ((gates.loading && !gates.data) || systemsLoading) {
    return (
      <section className="fm-board" aria-busy="true" aria-label="Loading the board">
        <div className="fm-board-pad">
          <VStack gap={2}>
            {[0, 1, 2, 3, 4].map((i) => (
              <Skeleton key={i} height={28} />
            ))}
          </VStack>
        </div>
      </section>
    )
  }
  if (systemsError) {
    return (
      <section className="fm-board">
        <EmptyState title="The system register could not load" description={systemsError} actions={<Button label="Try again" onClick={() => void refreshSystems()} />} />
      </section>
    )
  }
  if (!active.length) {
    return (
      <section className="fm-board">
        <EmptyState
          title={systems.length ? 'No active AI systems' : 'No registered AI systems yet'}
          description="Register systems by hand or from a CSV, or connect a source and let discovery find them. Each registered system gets a row here."
          actions={
            <>
              <Button variant="primary" label="Register systems" href="/onboard" />
              <Button label="Find unregistered AI" href="/discovery" />
            </>
          }
        />
      </section>
    )
  }
  const covered = new Set(rows.map((r) => r.system.id))
  const unavailable = gates.error ? active : active.filter((s) => !covered.has(s.id))
  const missingResults = unavailable.length > 0 && (
    <section className="fm-card fm-board-act" aria-label="Unavailable release checks">
      <VStack gap={2}>
        <Heading level={2}>Release checks unavailable</Heading>
        <Text>{gates.error ?? 'The gate returned no results for these systems.'}</Text>
        <ul className="fm-board-names">
          {unavailable.map((s) => <li key={s.id}><Link href={`/systems/${encodeURIComponent(s.id)}`}>{s.name}</Link></li>)}
        </ul>
        <Button label="Retry release checks" variant="secondary" onClick={gates.reload} />
      </VStack>
    </section>
  )
  if (gates.error || !rows.length) return <>{missingResults}<HomeLifecycleChart systems={active} /></>
  const partial = unavailable.length > 0 || rows.some(({ gate }) => COLS.some((c) => stateOf(gate, c) === 'unavailable'))

  // The matrix's disclosure keeps entirely empty systems reachable without adding empty columns.
  const blank = (gate: EstateGate) => COLS.every((c) => ['open', 'planned'].includes(stateOf(gate, c)))
  const empty = rows.filter((r) => blank(r.gate))
  const shown = rows.filter((r) => !blank(r.gate))
  const pending = rows.filter((r) => r.gate.approvalStatus === 'pending')
  const noEvidence = (gate: EstateGate) => COLS.filter((c) => c.key !== 'decision').every((c) => stateOf(gate, c) === 'open')

  const selectedRow = params?.getAll('system').length === 1 && rows.find((r) => r.system.id === params.get('system'))
  const selectedCol = params?.getAll('check').length === 1 && COLS.find((c) => c.key === params.get('check'))
  const open = selectedRow && selectedCol ? { ...selectedRow, col: selectedCol } : null
  const sel = open ? stateOf(open.gate, open.col) : null
  const others = inbox.total === undefined ? undefined : Math.max(0, inbox.items.length - pending.length) + (inbox.reportAssignments.data?.length ?? 0)
  const selCheck = open && open.col.key !== 'decision' ? open.gate.checks.find((c) => c.key === open.col.key) : undefined
  const failureCount = `${failures.length} failed release ${failures.length === 1 ? 'check' : 'checks'}`
  const checkName = (key: string, fallback: string) => CHECKS.find((col) => col.key === key)?.name ?? fallback
  const checkHref = (systemId: string, key: string) => {
    const query = new URLSearchParams(params?.toString())
    query.set('system', systemId)
    query.set('check', key)
    return `/dashboard?${query}`
  }
  const otherFailureLinks = failures.slice(1).map(({ system, check }) => {
    const name = checkName(check.key, check.label)
    return (
      <li key={`${system.id}/${check.key}`}>
        <Link href={checkHref(system.id, check.key)} scroll={false} aria-label={`Review ${name} on ${system.name}`}>
          <span><strong>{system.name}</strong> · {name}</span><ArrowUpRight size={15} aria-hidden />
        </Link>
      </li>
    )
  })
  const realChecks = rows.flatMap(({ gate }) => gate.checks)
  const systemsWithProof = rows.filter(({ gate }) => gate.checks.some((c) => c.evidenceId || c.failureEvidenceIds?.length)).length
  const openChecks = realChecks.filter((c) => checkCell(c) === 'open').length
  const outOfDate = realChecks.filter((c) => checkCell(c) === 'stale').length
  const higherRisk = active.filter((system) => system.riskTier === 'high' || system.riskTier === 'critical').length
  const coveragePercent = Math.round(systemsWithProof / active.length * 100)
  const knownFailures = `${failures.length} failing ${failures.length === 1 ? 'check' : 'checks'}${partial ? ' in available results' : ''}`
  const scope = <p className="fm-home-scope">{selectedOrg?.name && <>{selectedOrg.name}<span aria-hidden>/</span></>}AI estate</p>

  return (
    <>
      <Card className="fm-home-workspace">
        {lead ? (
          <section className="fm-home-focus" aria-label={failureCount}>
            {scope}
            <p className="fm-home-status"><i aria-hidden />{failureCount}</p>
            <h1>{lead.system.name}</h1>
            <div className="fm-home-byline">
              <Link href={checkHref(lead.system.id, lead.check.key)} scroll={false} aria-label={`Review ${checkName(lead.check.key, lead.check.label)} on ${lead.system.name}`}>
                {checkName(lead.check.key, lead.check.label)} check <ArrowUpRight size={14} aria-hidden />
              </Link>
              <span>{lead.system.riskTier} risk</span>
            </div>
            <HomeFailureEvidence systemId={lead.system.id} check={lead.check} {...proof} />
            {partial && <p className="fm-home-note">Some release checks could not be read.</p>}
            {otherFailureLinks.length > 0 && <div className="fm-home-other-failures">
              <h2>Also needs review</h2>
              <ul>{otherFailureLinks.slice(0, 2)}</ul>
              {otherFailureLinks.length > 2 && <details>
                <summary>{otherFailureLinks.length - 2} more failed {otherFailureLinks.length === 3 ? 'check' : 'checks'} <ChevronDown size={15} aria-hidden /></summary>
                <ul>{otherFailureLinks.slice(2)}</ul>
              </details>}
            </div>}
          </section>
        ) : (
          <section className="fm-home-focus" aria-label="Estate summary">
            {scope}
            <h1>{active.length} AI {active.length === 1 ? 'system' : 'systems'} under governance</h1>
            <p className="fm-home-intro">{pending.length ? 'A human release decision is pending.' : !shown.length ? 'These systems are waiting for their first release evidence.' : outOfDate ? 'Release evidence needs refreshing.' : 'Review the recorded checks for each active system.'}</p>
            {partial && <p className="fm-home-note">Some release checks could not be read.</p>}
            <Link className="fm-home-secondary" href={pending.length ? '#bd-needs' : '/systems'}>{pending.length ? 'Review release requests' : 'View system register'} <ArrowRight size={16} aria-hidden /></Link>
          </section>
        )}
        <HomeCheckMatrix shown={shown} empty={empty} columns={COLS} stateOf={stateOf} wordFor={wordFor}
          partial={partial} checkedAt={checkedAt} onRefresh={gates.reload} onSelect={selectBoardCell} />
      </Card>

      {missingResults}
      {pending.length > 0 && (
        <section className="fm-card fm-board-act" aria-labelledby="bd-needs">
          <Heading level={2} id="bd-needs">{pending.length === 1 ? `${pending[0].system.name} is waiting for a release decision` : `${pending.length} systems are waiting for a release decision`}</Heading>
          {pending.some((r) => noEvidence(r.gate)) && <p>Some release requests have no check evidence yet. Run a first evaluation before deciding.</p>}
          <ul>{pending.map((r) => <li key={r.system.id}>
            <Link href={`/systems/${encodeURIComponent(r.system.id)}?decide`}>Review release for {r.system.name}</Link>
          </li>)}</ul>
          {others !== undefined && others > 0 && <Link href="/needs-you">{others} more {others === 1 ? 'item needs' : 'items need'} review</Link>}
        </section>
      )}

      <div className="fm-home-analysis">
        {lead && <HomeFailureBreakdown record={proof.record} systemName={lead.system.name} />}
        <HomeLifecycleChart systems={active} />
      </div>

      <section className="fm-home-overview" aria-labelledby="bd-overview">
        <header>
          <h2 id="bd-overview">Estate overview</h2>
          <div className="fm-home-utilities">
            <Link href="/discovery">Find unregistered AI <ArrowUpRight size={14} aria-hidden /></Link>
            <Link href="/systems">Open AI systems <ArrowRight size={14} aria-hidden /></Link>
          </div>
        </header>
        <div className="fm-home-metrics">
          <Card className="fm-home-metric">
            <h3>Evidence coverage</h3>
            <p className="fm-home-number">{partial ? systemsWithProof : `${coveragePercent}%`}</p>
            {!partial && <span className="fm-home-track" aria-hidden><i style={{ width: `${coveragePercent}%` }} /></span>}
            <p>{partial ? 'Systems with known linked evidence. Coverage is incomplete.' : `${systemsWithProof} of ${active.length} active systems have linked evidence`}</p>
          </Card>
          <Card className="fm-home-metric">
            <h3>Checks without evidence</h3>
            <p className="fm-home-number">{openChecks}<small> / {realChecks.length}</small></p>
            <p>{partial ? 'Across available results' : 'Across the active system gates'}</p>
          </Card>
          <Card className="fm-home-metric">
            <h3>High or critical risk</h3>
            <p className="fm-home-number">{higherRisk}<small> / {active.length}</small></p>
            <p>Registered active systems</p>
          </Card>
          <Card className="fm-home-metric">
            <h3>Release decisions pending</h3>
            <p className="fm-home-number">{pending.length}{partial && <small> known</small>}</p>
            <p>{knownFailures}</p>
            {outOfDate > 0 && <p>{outOfDate} {outOfDate === 1 ? 'check' : 'checks'} out of date</p>}
          </Card>
        </div>
      </section>

      <Drawer isOpen={open !== null} onOpenChange={(o) => !o && selectBoardCell()} label={open ? `${open.col.name} on ${open.system.name}` : 'Check'} width={440} padding={5}>
        {open && sel && (
          <VStack gap={5}>
            <VStack gap={2} align="start">
              <Token size="sm" color={TOKEN[sel] ?? 'gray'} label={open.col.key === 'decision' ? DECISION_WORD[sel as DecisionState] : WORD[sel as CellState]} />
              <Heading level={2}>{open.col.name}</Heading>
              <Text type="supporting">
                {open.system.name} · {open.system.riskTier} risk
              </Text>
            </VStack>
            <MetadataList label={{ width: 120 }}>
              {selCheck ? (
                <>
                  <MetadataListItem label="What it means">{sel === 'fails' ? 'One or more results still fail their thresholds.' : KIND_TITLE[sel as CellState] ?? WORD[sel as CellState]}</MetadataListItem>
                  <MetadataListItem label={sel === 'fails' ? 'Latest record type' : 'How we know'}>{selCheck.evidenceClass ? classLabel(selCheck.evidenceClass) : 'No evidence yet'}</MetadataListItem>
                  <MetadataListItem label={sel === 'fails' ? 'Check confidence' : 'Confidence'}>{selCheck.confidence.toFixed(2)}</MetadataListItem>
                  <MetadataListItem label={sel === 'fails' ? 'Failure evidence' : 'Evidence'}>
                    <CheckEvidenceLinks systemId={open.system.id} check={selCheck} failed={sel === 'fails'} />
                  </MetadataListItem>
                </>
              ) : open.col.key === 'decision' ? (
                <>
                  <MetadataListItem label="Release decision">{DECISION_WORD[sel as DecisionState]}</MetadataListItem>
                  <MetadataListItem label="Gate verdict">{open.gate.verdict.replace(/_/g, ' ')}</MetadataListItem>
                  <MetadataListItem label="Confidence">{open.gate.confidence.toFixed(2)}</MetadataListItem>
                </>
              ) : <MetadataListItem label="Evidence">Check result unavailable</MetadataListItem>}
            </MetadataList>
            <VStack gap={2}>
              {open.col.key === 'decision' && sel === 'needs' && <Button variant="primary" label="Decide now" href={`/systems/${encodeURIComponent(open.system.id)}?decide`} />}
              <Button variant={sel === 'needs' || sel === 'fails' ? 'secondary' : 'primary'} label="Open the system file" href={`/systems/${encodeURIComponent(open.system.id)}`} />
            </VStack>
          </VStack>
        )}
      </Drawer>
    </>
  )
}
