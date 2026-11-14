'use client'

import '@/astryx/pages/discovery.css'
import { useRouter, useSearchParams } from 'next/navigation'
import { Suspense, useEffect, useRef, useState } from 'react'
import { Banner } from '@astryxdesign/core/Banner'
import { Button } from '@astryxdesign/core/Button'
import { EmptyState } from '@astryxdesign/core/EmptyState'
import { Heading, Text } from '@astryxdesign/core/Text'
import { HStack, VStack } from '@astryxdesign/core/Layout'
import { Selector } from '@astryxdesign/core/Selector'
import { Skeleton } from '@astryxdesign/core/Skeleton'
import { Tab, TabList } from '@astryxdesign/core/TabList'
import { SourceMark, where } from '@/astryx/DiscoveryParts'
import { CandidatePanel, WaitingList } from '@/astryx/DiscoveryReview'
import { useCandidates, type Candidate } from '@/astryx/data/review'
import { DiscoveryFlow } from '@/astryx/DiscoveryFlow'
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

function Flow({ d }: { d: D }) {
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
          <span><i className="dv-key" style={{ background: 'var(--color-text-primary)' }} /><b>{reg}</b> registered</span>
          <span><i className="dv-key" style={{ background: 'var(--color-text-warning)' }} /><b>{wait}</b> waiting for you</span>
          <span><i className="dv-key" style={{ background: 'var(--color-border)' }} /><b>{ign}</b> ignored</span>
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
                <Button size="sm" variant="ghost" label="Remove" isDisabled={busyId !== null} onClick={() => run(i.id, () => d.remove(i.id))} />
              </HStack>
            </div>
          )
        })}
      </VStack>
    </section>
  )
}

/* ------------------------------------------------------------------ Page */

function DiscoveryView() {
  const router = useRouter()
  const params = useSearchParams()
  const v = params.get('view')
  const view = v === 'sources' || v === 'flow' || v === 'waiting' ? v : 'overview'
  const d = useDiscovery()
  const c = useCandidates()
  const picked = params.get('c')
  const selected = view === 'waiting' ? (c.candidates.find((x) => x.id === picked)?.id ?? c.candidates[0]?.id ?? null) : null
  const openCandidate = (id: string) => router.replace(`/discovery?view=waiting&c=${encodeURIComponent(id)}`)
  const changed = () => void Promise.all([c.refresh(), d.refresh()])
  const [lane, setLane] = useState<LaneKey | null>(null)
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
  const waiting = c.candidates.length

  return (
    <div className="fm-page">
      <VStack gap={5}>
        <HStack gap={4} hAlign="between" vAlign="end" wrap="wrap">
          <VStack gap={1}>
            <Heading level={1}>Discovery</Heading>
            <Text color="secondary">
              {d.loading
                ? 'Reading connectors'
                : `${d.integrations.length} source${d.integrations.length === 1 ? '' : 's'} watched · ${d.discovered.length} sightings · ${waiting} waiting for you`}
            </Text>
          </VStack>
          <HStack gap={2}>
            <Button label="See AI systems" variant="secondary" href="/systems" />
            <Button label="Connect a source" variant="primary" href="/discovery/connect" />
          </HStack>
        </HStack>

        <TabList value={view} onChange={(t) => router.replace(t === 'overview' ? '/discovery' : `/discovery?view=${t}`)} hasDivider aria-label="Discovery view">
          <Tab value="overview" label="Overview" />
          <Tab value="waiting" label={`Waiting${waiting ? ` ${waiting}` : ''}`} />
          <Tab value="flow" label="Flow" />
          <Tab value="sources" label={`Sources${failing ? ` · ${failing} failing` : ''}`} />
        </TabList>

        {error && <Banner status="error" title="That did not work" description={error} isDismissable onDismiss={() => setError(null)} />}

        {d.loading ? (
          <VStack gap={2} aria-busy="true">
            {[0, 1, 2].map((i) => (
              <Skeleton key={i} height={96} />
            ))}
          </VStack>
        ) : d.error ? (
          <EmptyState title="Discovery could not load" description={d.error} actions={<Button label="Try again" onClick={() => void d.refresh()} />} />
        ) : view === 'flow' ? (
          d.integrations.length === 0 ? (
            <EmptyState title="No sources connected" description="Connect a source and its reads appear here as a flow into your inventory." actions={<Button variant="primary" label="Connect a source" href="/discovery/connect" />} />
          ) : (
            <DiscoveryFlow d={d} onReview={() => router.replace('/discovery?view=waiting')} />
          )
        ) : view === 'waiting' ? (
          c.loading ? (
            <Skeleton height={320} />
          ) : c.error ? (
            <EmptyState title="What is waiting could not load" description={c.error} actions={<Button label="Try again" onClick={() => void c.refresh()} />} />
          ) : (
            <div className="dv-split">
              <WaitingList candidates={c.candidates} selected={selected} onPick={openCandidate} />
              {selected ? <CandidatePanel key={selected} id={selected} onChanged={changed} /> : <EmptyState title="Nothing waiting" description="Connectors on a schedule keep looking." />}
            </div>
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
            <Areas d={d} lane={lane} onLane={setLane} />
            <Flow d={d} />
            <WaitingList
              candidates={c.candidates.filter((x) => inLane(x, lane))}
              onPick={openCandidate}
              title={`Waiting for you (${c.candidates.filter((x) => inLane(x, lane)).length})${lane ? ` · ${LANES.find((l) => l.key === lane)?.label}` : ''}`}
            />
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
