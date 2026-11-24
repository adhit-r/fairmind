'use client'

import '@/astryx/pages/discovery.css'
import { useRouter, useSearchParams } from 'next/navigation'
import Link from 'next/link'
import { ArrowLeft, ArrowRight, Plus } from 'lucide-react'
import { Suspense, useEffect, useRef, useState } from 'react'
import { Banner } from '@astryxdesign/core/Banner'
import { Button } from '@astryxdesign/core/Button'
import { EmptyState } from '@astryxdesign/core/EmptyState'
import { Heading, Text } from '@astryxdesign/core/Text'
import { HStack, VStack } from '@astryxdesign/core/Layout'
import { Selector } from '@astryxdesign/core/Selector'
import { Skeleton } from '@astryxdesign/core/Skeleton'
import { Tab, TabList } from '@astryxdesign/core/TabList'
import { recordParam } from '@/lib/assurance/evaluationLinks'
import { Button as Pill } from '@/components/ui/button'
import { SourceMark, where } from '@/astryx/DiscoveryParts'
import { CandidatePanel, WaitingList } from '@/astryx/DiscoveryReview'
import { useCandidates, type Candidate } from '@/astryx/data/review'
import { DiscoveryFlow } from '@/astryx/DiscoveryFlow'
import { FoundList, SHOWS, type Show } from '@/astryx/FoundList'
import {
  HEALTH_LABEL,
  LANES,
  MAX_LOG_BYTES,
  SCHEDULES,
  SOURCES,
  SOURCE_LABEL,
  ago,
  healthOf,
  until,
  useDiscovery,
  type Health,
  type Integration,
  type IntegrationKind,
  type IntegrationRun,
  type LaneKey,
} from '@/astryx/data/discovery'

type D = ReturnType<typeof useDiscovery>
const KINDS = Object.keys(SOURCES) as IntegrationKind[]
const laneOf = (kind: string): LaneKey | undefined => SOURCES[kind as IntegrationKind]?.lane
const inLane = (c: Candidate, lane: LaneKey | null) => !lane || (lane === 'mcp' ? c.kind === 'mcp_server' || c.sources.includes('mcp_registry') : c.sources.some((s) => laneOf(s) === lane))

/** Re-render on a timer so "3 min ago" and live status stay true while the page is open. */
function useNow(ms: number) {
  const [now, setNow] = useState(() => Date.now())
  useEffect(() => {
    const t = setInterval(() => setNow(Date.now()), ms)
    return () => clearInterval(t)
  }, [ms])
  return now
}

/* ------------------------------------------------------------------ Overview */

function Areas({ d, lane, onLane }: { d: D; lane: LaneKey | null; onLane: (l: LaneKey | null) => void }) {
  return (
    <section className="fm-card" aria-labelledby="areas-title">
      <VStack gap={3}>
        <HStack hAlign="between" vAlign="center" wrap="wrap" gap={2}>
          <Heading level={2} id="areas-title">
            Where AI can show up
          </Heading>
          <Text color="secondary" size="sm">
            Solid: watched · Dashed: not watched
          </Text>
        </HStack>
        <div className="dv-lanes">
          {LANES.map((l) => {
            const kinds = KINDS.filter((k) => SOURCES[k].lane === l.key)
            const connected = new Set(d.integrations.filter((i) => SOURCES[i.kind]?.lane === l.key).map((i) => i.kind))
            // MCP servers also come from MCP configs in GitHub repos.
            const found =
              l.key === 'mcp'
                ? d.discovered.filter((a) => a.kind === 'mcp_server').length
                : d.discovered.filter((a) => laneOf(a.source) === l.key && a.kind !== 'mcp_server').length
            const watched = connected.size > 0 || (l.key === 'mcp' && d.integrations.some((i) => i.kind === 'github'))
            return (
              <button
                key={l.key}
                type="button"
                className={`dv-lane${watched ? '' : ' off'}${lane === l.key ? ' on' : ''}`}
                aria-pressed={lane === l.key}
                onClick={() => onLane(lane === l.key ? null : l.key)}
              >
                <span className="hd">
                  <span>{l.label}</span>
                  <span className="ct">{watched ? `${found} found` : 'Not watched'}</span>
                </span>
                <span className="dv-marks">
                  {kinds.map((k) => (
                    <SourceMark key={k} kind={k} ghost={!connected.has(k)} size="sm" />
                  ))}
                </span>
              </button>
            )
          })}
        </div>
      </VStack>
    </section>
  )
}

function Flow({ d, onShow }: { d: D; onShow: (s: Show) => void }) {
  const n = (s: string) => d.discovered.filter((a) => a.status === s).length
  const [reg, wait, ign] = [n('promoted'), n('new'), n('ignored')]
  if (reg + wait + ign === 0) return null
  return (
    <section className="fm-card" aria-labelledby="flow-title">
      <VStack gap={2}>
        <HStack hAlign="between">
          <Heading level={2} id="flow-title">
            From found to governed
          </Heading>
          <Text color="secondary" size="sm">
            {reg + wait + ign} items
          </Text>
        </HStack>
        <div className="dv-flow" role="img" aria-label={`${reg} registered, ${wait} waiting, ${ign} ignored`}>
          {reg > 0 && <span style={{ flex: reg, background: 'var(--color-text-primary)' }} />}
          {wait > 0 && <span style={{ flex: wait, background: 'var(--color-text-warning)' }} />}
          {ign > 0 && <span style={{ flex: ign, background: 'var(--color-border)' }} />}
        </div>
        <div className="dv-legend">
          <span><i className="dv-key" style={{ background: 'var(--color-text-primary)' }} /><button type="button" className="dv-flow-link" onClick={() => onShow('registered')}><b>{reg}</b> registered</button></span>
          <span><i className="dv-key" style={{ background: 'var(--color-text-warning)' }} /><button type="button" className="dv-flow-link" onClick={() => onShow('waiting')}><b>{wait}</b> waiting for you</button></span>
          <span><i className="dv-key" style={{ background: 'var(--color-border)' }} /><button type="button" className="dv-flow-link" onClick={() => onShow('ignored')}><b>{ign}</b> ignored</button></span>
        </div>
      </VStack>
    </section>
  )
}

/* ------------------------------------------------------------------ Sources */

function RunStrip({ runs }: { runs: IntegrationRun[] }) {
  const shown = [...runs].reverse() // oldest left, newest right
  const max = Math.max(1, ...shown.map((r) => r.found ?? 0))
  return (
    <div className="dv-runs" role="img" aria-label={`Last ${shown.length} reads, ${shown.filter((r) => r.status === 'failed').length} failed`}>
      {shown.length === 0 && <span className="empty" style={{ height: 4, width: 60 }} />}
      {shown.map((r) => (
        <span
          key={r.id}
          className={r.status === 'failed' ? 'failed' : r.created ? 'new' : r.found ? '' : 'empty'}
          style={{ height: r.status === 'failed' ? 10 : Math.max(4, Math.round(((r.found ?? 0) / max) * 32)) }}
          title={`${new Date(r.finishedAt).toLocaleString('en-GB')} · ${r.trigger} · ${r.status === 'failed' ? r.error : `${r.found} found, ${r.created} new`}`}
        />
      ))}
    </div>
  )
}

function lastChange(i: Integration): { text: string; err?: boolean } | null {
  const r = i.recentRuns?.[0]
  if (!r) return null
  if (r.status === 'failed') return { text: r.error ?? 'The last read failed', err: true }
  if (r.created) return { text: `${r.created} new: ${r.newNames.slice(0, 3).join(', ')}${r.created > 3 ? ', and more' : ''}` }
  return { text: `No change · ${r.found ?? 0} known` }
}

/** How much of the account the last read covered: a GitHub read only reports repos with AI in them. */
function coverage(i: Integration): string | null {
  const s = i.lastSync?.scanned
  if (!s) return null
  const part = s.read < s.listed ? `the first ${s.read} of ${s.listed}` : `all ${s.listed}`
  return `Read ${part} repos${s.token ? '' : ' · no token, so public repos only'}`
}

/** What the last good read found, step by step, with examples. */
function LastFound({ i }: { i: Integration }) {
  const run = i.recentRuns?.find((r) => r.status === 'ok')
  if (!run?.steps?.length) return null
  const title = (key: string) => i.steps?.find((s) => s.key === key)?.title ?? key
  return (
    <details className="meta">
      <summary>What the last read found</summary>
      <ul style={{ margin: '4px 0 0', paddingLeft: 16 }}>
        {run.steps.map((st) => (
          <li key={st.key}>
            <b>{title(st.key)}</b>: {st.off ? 'turned off' : st.found === 0 ? 'nothing found' : `${st.found} (${st.samples.map((x) => x.name).join(', ')}${st.found > st.samples.length ? `, and ${st.found - st.samples.length} more` : ''})`}
          </li>
        ))}
      </ul>
    </details>
  )
}

function confirmRemove(d: D, i: Integration): boolean {
  const pending = d.discovered.filter((a) => a.integrationId === i.id && a.status !== 'promoted').length
  return window.confirm(
    `Remove ${i.name} (${where(i)})?\n\n` +
      `FairMind stops reading it${pending ? ` and drops the ${pending} found item${pending === 1 ? '' : 's'} not yet registered` : ''}. ` +
      'AI systems you already registered stay.\n\nTo read a different account, connect it again afterwards.',
  )
}

function Sources({ d, busyId, run, onUpload }: { d: D; busyId: string | null; run: (id: string, fn: () => Promise<void>) => void; onUpload: (id: string) => void }) {
  const now = useNow(30_000)
  const { refresh } = d
  // Scheduled reads land on the server; pick them up while this view is open.
  useEffect(() => {
    const t = setInterval(() => void refresh(), 60_000)
    return () => clearInterval(t)
  }, [refresh])
  const health = d.integrations.map((i) => healthOf(i, now))
  const count = (h: Health) => health.filter((x) => x === h).length
  if (d.integrations.length === 0) {
    return <EmptyState title="No sources connected" description="Connect a source and FairMind keeps reading it on the schedule you pick." actions={<Button variant="primary" label="Connect a source" href="/discovery/connect" />} />
  }
  return (
    <section className="fm-card" aria-labelledby="src-title">
      <VStack gap={2}>
        <HStack hAlign="between" vAlign="center" wrap="wrap" gap={2}>
          <Heading level={2} id="src-title">
            Connected sources
          </Heading>
          <div className="dv-summary">
            {(['live', 'failing', 'overdue', 'manual', 'waiting', 'upload'] as Health[])
              .filter((h) => count(h) > 0)
              .map((h) => (
                <span key={h} className="dv-pill">
                  <i className={`dv-dot ${h}`} />
                  <b>{count(h)}</b>
                  {HEALTH_LABEL[h].toLowerCase()}
                </span>
              ))}
          </div>
        </HStack>
        {d.integrations.map((i, idx) => {
          const h = health[idx]
          const change = lastChange(i)
          return (
            <div key={i.id} className="dv-src">
              <HStack gap={3} vAlign="start">
                <SourceMark kind={i.kind} />
                <div style={{ minWidth: 0 }}>
                  <div style={{ fontWeight: 600 }}>{i.name}</div>
                  <div className="meta">{where(i)}</div>
                  {change && <div className={`dv-change${change.err ? ' err' : ''}`}>{change.text}</div>}
                  {coverage(i) && <div className="meta">{coverage(i)}</div>}
                  <LastFound i={i} />
                </div>
              </HStack>
              <div className="meta">
                <div>
                  <i className={`dv-dot ${h}`} />
                  <b>{HEALTH_LABEL[h]}</b>
                </div>
                <div>Last fetched {ago(i.lastSyncedAt, now)}</div>
                <div>{i.kind === 'proxy_logs' ? (i.lastSyncedAt ? 'Upload a newer export to read again' : 'Upload an export to read it') : i.scheduleMinutes ? `Next read ${until(i.nextSyncAt, now)}` : 'Reads only when you sync'}</div>
              </div>
              <VStack gap={2}>
                <RunStrip runs={i.recentRuns ?? []} />
                {i.kind !== 'proxy_logs' && (
                  <Selector
                    label={`How often to read ${i.name}`}
                    isLabelHidden
                    size="sm"
                    value={String(i.scheduleMinutes ?? 0)}
                    options={SCHEDULES.map((s) => ({ value: String(s.minutes), label: s.label }))}
                    onChange={(v: string) => run(i.id, () => d.setSchedule(i.id, Number(v)))}
                  />
                )}
              </VStack>
              <HStack gap={2}>
                {i.kind === 'proxy_logs' ? (
                  <Button size="sm" variant="secondary" label={busyId === i.id ? 'Reading' : 'Upload logs'} isDisabled={busyId !== null} onClick={() => onUpload(i.id)} />
                ) : (
                  <Button size="sm" variant="secondary" label={busyId === i.id ? 'Reading' : 'Sync now'} isDisabled={busyId !== null} onClick={() => run(i.id, async () => void (await d.sync(i.id)))} />
                )}
                <Button size="sm" variant="ghost" label="Remove" isDisabled={busyId !== null} onClick={() => confirmRemove(d, i) && run(i.id, () => d.remove(i.id))} />
              </HStack>
            </div>
          )
        })}
      </VStack>
    </section>
  )
}

/* ------------------------------------------------------------------ Page */

function groupQueueBySource(candidates: Candidate[]) {
  const counts = new Map<IntegrationKind, number>()
  for (const candidate of candidates) {
    for (const source of new Set(candidate.sources)) {
      counts.set(source, (counts.get(source) ?? 0) + 1)
    }
  }
  return [...counts].sort(([firstKind, firstCount], [secondKind, secondCount]) =>
    secondCount - firstCount || (SOURCE_LABEL[firstKind] ?? firstKind).localeCompare(SOURCE_LABEL[secondKind] ?? secondKind))
}

function QueueSourceSummary({ groups, total, source, onSource }: {
  groups: ReturnType<typeof groupQueueBySource>
  total: number
  source: string | null
  onSource: (kind: string | null) => void
}) {
  return (
    <section className="dv-source-summary" aria-labelledby="dv-queue-sources">
      <h2 id="dv-queue-sources">Sources in the queue</h2>
      <p>Select a source to filter candidates.</p>
      <ul>
        {groups.map(([kind, count]) => (
          <li key={kind}>
            <button type="button" className="dv-source-filter" onClick={() => onSource(source === kind ? null : kind)}
              aria-pressed={source === kind} aria-label={`Filter by ${SOURCE_LABEL[kind] ?? kind}, ${count} of ${total} candidates`}>
              <SourceMark kind={kind} />
              <span className="dv-source-label">{SOURCE_LABEL[kind] ?? kind}</span>
              <strong>{count}</strong>
              <span className="dv-source-track" aria-hidden><i style={{ width: `${count / total * 100}%` }} /></span>
            </button>
          </li>
        ))}
      </ul>
      {groups.reduce((sum, [, count]) => sum + count, 0) > total &&
        <p>Some candidates appear under more than one source.</p>}
      <footer>
        {source ? <button type="button" onClick={() => onSource(null)}>Clear source filter</button>
          : <Link href="/discovery?view=sources">Manage sources <ArrowRight size={15} aria-hidden /></Link>}
      </footer>
    </section>
  )
}

function waitingHref(source: string | null, candidate?: string) {
  const query = new URLSearchParams({ view: 'found', show: 'waiting' })
  if (candidate) query.set('c', candidate)
  if (source) query.set('source', source)
  return `/discovery?${query}`
}

function DiscoveryView() {
  const router = useRouter()
  const params = useSearchParams()
  const v = params.get('view')
  const d = useDiscovery()
  const c = useCandidates()
  const picked = recordParam(params, 'c')
  const hasCandidateLink = picked !== undefined
  const asked = (v === 'waiting' ? 'waiting' : params.get('show')) as Show | null
  const waiting = c.loading || c.error ? null : c.candidates.length
  const show: Show = asked && SHOWS.includes(asked) ? asked : hasCandidateLink || waiting !== 0 ? 'waiting' : 'all'
  const view = v === 'sources' || v === 'flow' || v === 'overview' ? v
    : v === 'found' || v === 'waiting' || hasCandidateLink || asked || waiting !== 0 ? 'found' : 'overview'
  const groups = groupQueueBySource(c.candidates)
  const requestedSource = params.get('source')
  const source = groups.some(([kind]) => kind === requestedSource) ? requestedSource : null
  const visibleCandidates = source ? c.candidates.filter((candidate) => candidate.sources.some((kind) => kind === source)) : c.candidates
  const showFound = (s: Show) => router.push(`/discovery?view=found&show=${s}`)
  const openCandidate = (id: string) => router.push(waitingHref(source, id), { scroll: false })
  const setSource = (kind: string | null) => router.push(waitingHref(kind), { scroll: false })
  const changed = () => void Promise.all([c.refresh(), d.refresh()])
  const closeReviewed = () => {
    changed()
    router.replace(waitingHref(source))
  }
  const lane = LANES.find((l) => l.key === params.get('lane')) ?? null
  const setLane = (key: LaneKey | null) => router.push(key ? `/discovery?view=overview&lane=${key}` : '/discovery?view=overview', { scroll: false })
  const [reviewRevision, setReviewRevision] = useState(0)
  const [resolvedGroup, setResolvedGroup] = useState<{ member: string; group: string } | null>(null)
  const selectedPanel = useRef<HTMLDivElement>(null)
  const lastCandidate = useRef<string | null>(null)
  const queueArea = useRef<HTMLDivElement>(null)
  useEffect(() => {
    if (view !== 'found' || show !== 'waiting') {
      lastCandidate.current = null
      return
    }
    if (picked && lastCandidate.current !== picked) {
      lastCandidate.current = picked
      selectedPanel.current?.focus({ preventScroll: true })
      selectedPanel.current?.scrollIntoView({ block: 'start' })
    } else if (!picked && waiting !== null && lastCandidate.current) {
      const target = Array.from(queueArea.current?.querySelectorAll<HTMLElement>('[data-candidate-id]') ?? [])
        .find((element) => element.dataset.candidateId === lastCandidate.current)
      lastCandidate.current = null
      const next = target ?? queueArea.current
      next?.focus({ preventScroll: true })
      next?.scrollIntoView({ block: 'nearest' })
    }
  }, [picked, view, show, waiting])
  const [busyId, setBusyId] = useState<string | null>(null)
  const [error, setError] = useState<string | null>(null)
  const fileInput = useRef<HTMLInputElement>(null)
  const uploadFor = useRef<string | null>(null)

  async function run(id: string, fn: () => Promise<void>) {
    setBusyId(id)
    setError(null)
    try {
      await fn()
      void c.refresh() // a read may add sightings to what is waiting
    } catch (e) {
      setError(e instanceof Error ? e.message : 'Something went wrong')
    } finally {
      setBusyId(null)
    }
  }

  function readLogs(file: File | undefined) {
    const id = uploadFor.current
    if (fileInput.current) fileInput.current.value = ''
    if (!file || !id) return
    if (file.size > MAX_LOG_BYTES) {
      setError('That log file is over 20 MB. Export a shorter period or only the destination host column.')
      return
    }
    void run(id, async () => void (await d.upload(id, await file.text())))
  }

  const failing = d.integrations.filter((i) => healthOf(i) === 'failing').length
  const sourceDataReady = !d.loading && !d.error
  const sourceState = d.error
    ? <EmptyState title="Discovery sources could not load" description={d.error} actions={<Button label="Try again" onClick={() => void d.refresh()} />} />
    : <div role="status" aria-label="Loading discovery sources"><Skeleton height={160} /></div>
  const queueState = c.error
    ? <EmptyState title="Review queue could not load" description={c.error} actions={<Button label="Retry queue" onClick={() => void c.refresh()} />} />
    : <div role="status" aria-label="Loading review queue"><Skeleton height={160} /></div>
  const reviewed = sourceDataReady && picked ? d.discovered.find((a) => a.id === picked && (a.status === 'promoted' || a.status === 'ignored')) : undefined
  const queue = waiting === null ? queueState : !waiting ? (
    <EmptyState title="Nothing waiting for review" description="There are no candidates awaiting a decision." actions={<Button label="See all sightings" onClick={() => showFound('all')} />} />
  ) : <WaitingList candidates={visibleCandidates}
    title={source ? `${visibleCandidates.length} awaiting review from ${SOURCE_LABEL[source] ?? source}` : undefined}
    selected={resolvedGroup && resolvedGroup.member === picked ? resolvedGroup.group : picked}
    onPick={openCandidate} />

  return (
    <div className="dv-page">
      <VStack gap={5}>
        <header className="dv-page-heading">
          <div>
            <h1>Discovery</h1>
            {d.error && <p>Source counts unavailable</p>}
          </div>
          <Pill asChild variant="outline" size="lg" className="dv-connect-action">
            <Link href="/discovery/connect"><Plus size={16} aria-hidden /> Connect a source</Link>
          </Pill>
        </header>

        <TabList value={view} onChange={(t) => router.push(`/discovery?view=${t}`)} hasDivider className="dv-view-tabs" aria-label="Discovery view">
          <Tab value="found" label="Sightings" />
          <Tab value="overview" label="Overview" />
          <Tab value="flow" label="Flow" />
          <Tab value="sources" label="Sources"
            aria-label={sourceDataReady && failing ? `Sources · ${failing} failing` : undefined}
            endContent={sourceDataReady && failing ? <i className="dv-source-warning" aria-hidden title={`${failing} failing`} /> : undefined} />
        </TabList>

        {error && <Banner status="error" title="That did not work" description={error} isDismissable onDismiss={() => setError(null)} />}

        {view === 'found' ? (
          <FoundList discovered={sourceDataReady ? d.discovered : null} show={show} showFilters={!picked} onShow={showFound} onReview={openCandidate} sourceState={sourceState}>
            {picked === null ? (
              <EmptyState title="Candidate link is incomplete" description="Choose one candidate from the review queue." actions={<Button label="View waiting queue" onClick={() => showFound('waiting')} />} />
            ) : picked ? (
              <div className="dv-split">
                <div className="dv-selected" ref={selectedPanel} tabIndex={-1} role="region" aria-label="Candidate review">
                  <Link className="dv-back" href={waitingHref(source)} scroll={false}><ArrowLeft size={16} aria-hidden /> Back to review queue</Link>
                  <CandidatePanel
                    key={JSON.stringify([picked, reviewRevision])}
                    id={picked}
                    integrations={d.integrations}
                    reviewed={reviewed}
                    onChanged={changed}
                    onClosed={closeReviewed}
                    onResolved={setResolvedGroup}
                    onSplit={() => {
                      setResolvedGroup(null)
                      setReviewRevision((n) => n + 1)
                      changed()
                    }}
                  />
                </div>
                {!!visibleCandidates.length && <aside className="dv-side-queue">
                  <WaitingList candidates={visibleCandidates} selected={resolvedGroup && resolvedGroup.member === picked ? resolvedGroup.group : picked} onPick={openCandidate} compact />
                </aside>}
              </div>
            ) : (
              <div className="dv-queue-layout">
                {waiting !== null && groups.length > 1 && (
                  <label className="dv-mobile-source">
                    <span>Filter by source</span>
                    <select value={source ?? ''} onChange={(event) => setSource(event.target.value || null)}>
                      <option value="">All sources</option>
                      {groups.map(([kind, count]) => <option key={kind} value={kind}>{SOURCE_LABEL[kind] ?? kind} ({count})</option>)}
                    </select>
                  </label>
                )}
                <div className="dv-queue-main" ref={queueArea} tabIndex={-1}>{queue}</div>
                {!!waiting && !!groups.length && <QueueSourceSummary groups={groups} total={waiting} source={source} onSource={setSource} />}
              </div>
            )}
          </FoundList>
        ) : !sourceDataReady ? sourceState : view === 'flow' ? (
          d.integrations.length === 0 ? (
            <EmptyState title="No sources connected" description="Connect a source and its reads appear here as a flow into your inventory." actions={<Button variant="primary" label="Connect a source" href="/discovery/connect" />} />
          ) : (
            <DiscoveryFlow d={d} onReview={() => showFound('waiting')} />
          )
        ) : view === 'sources' ? (
          <Sources
            d={d}
            busyId={busyId}
            run={run}
            onUpload={(id) => {
              uploadFor.current = id
              fileInput.current?.click()
            }}
          />
        ) : (
          <>
            <Areas d={d} lane={lane?.key ?? null} onLane={setLane} />
            <Flow d={d} onShow={showFound} />
            {waiting === null ? queueState : (
              <WaitingList
                candidates={c.candidates.filter((x) => inLane(x, lane?.key ?? null))}
                onPick={openCandidate}
                title={lane ? `Waiting for review · ${lane.label}` : 'Waiting for review'}
                emptyLabel={lane ? `No candidates are waiting in ${lane.label}.` : undefined}
              />
            )}
          </>
        )}
      </VStack>
      <input
        ref={fileInput}
        type="file"
        accept=".csv,.log,.txt,.json,.jsonl,text/plain,text/csv,application/json"
        hidden
        aria-label="Log file to read"
        onChange={(e) => readLogs(e.target.files?.[0])}
      />
    </div>
  )
}

export default function DiscoveryPage() {
  return (
    <Suspense fallback={null}>
      <DiscoveryView />
    </Suspense>
  )
}
