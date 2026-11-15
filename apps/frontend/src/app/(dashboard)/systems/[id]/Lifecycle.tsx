'use client'

import '@/astryx/pages/lifecycle.css'
import { Archive, Database, FileText, Lock, MessageSquare, PowerOff, ShieldCheck, Unplug, Users } from 'lucide-react'
import { useState, type ReactNode } from 'react'
import { Badge } from '@astryxdesign/core/Badge'
import { Banner } from '@astryxdesign/core/Banner'
import { HStack, VStack } from '@astryxdesign/core/Layout'
import { Heading, Text } from '@astryxdesign/core/Text'
import type { CheckSnapshot, Chain, Retirement, SystemChange } from '@/lib/api/hooks/useLifecycle'
import type { GateCheck } from '@/lib/api/hooks/useSystemFile'
import { when } from '@/astryx/data/system-file'
import { columns, type CellClass } from './versions'


const REASON_LABEL: Record<string, string> = { replaced: 'Replaced', not_needed: 'No longer needed', failed_review: 'Failed review', rule_changed: 'Rule changed' }


export function Cell({ state, size, frozen, label }: { state: CellClass; size?: 'sm' | 'lg'; frozen?: boolean; label?: string }) {
  return <span className={`fm-lc-cell ${state}${size ? ` ${size}` : ''}${frozen ? ' frozen' : ''}`} role={label ? 'img' : undefined} aria-label={label} aria-hidden={label ? undefined : true} />
}

const STATE_WORD: Record<CellClass, string> = { proven: 'Measured', attested: 'Attested', open: 'Open', reopen: 'Reopened by a change' }

export function Legend({ reopen = true }: { reopen?: boolean }) {
  const keys: CellClass[] = reopen ? ['proven', 'attested', 'open', 'reopen'] : ['proven', 'attested', 'open']
  return (
    <div className="fm-lc-legend">
      {keys.map((k) => <span key={k}><Cell state={k} size="sm" />{STATE_WORD[k]}</span>)}
    </div>
  )
}

/** Each version as a column of the gate's checks: what a change reopened reads at a glance. */
export function VersionsCard({ changes, checks, approved, createdAt }: { changes: SystemChange[]; checks: GateCheck[]; approved: boolean; createdAt?: string }) {
  const [now] = useState(() => Date.now())
  if (changes.length === 0) return null
  const cols = columns(changes, checks, approved)
  const starts = [createdAt, ...changes.map((c) => c.createdAt)].map((t) => (t ? +new Date(t) : NaN))
  const spans = starts.map((t, i) => Math.max(1, ((i + 1 < starts.length ? starts[i + 1] : now) - t) / 86_400_000) || 1).slice(-cols.length)
  return (
    <section className="fm-card" aria-labelledby="sf-versions">
      <VStack gap={4}>
        <HStack gap={2} vAlign="center" hAlign="between" wrap="wrap">
          <Heading level={2} id="sf-versions">Versions and changes</Heading>
          <Text type="supporting" color="secondary">{changes.length} {changes.length === 1 ? 'change' : 'changes'} recorded</Text>
        </HStack>
        <VStack gap={1}>
          <div className="fm-lc-lane" aria-hidden>
            {cols.map((c, i) => <b key={c.key} className={c.tone === 'old' ? '' : c.tone} style={{ flex: spans[i] }} />)}
          </div>
          <div className="fm-lc-lanelbl">
            {cols.map((c, i) => <span key={c.key} style={{ flex: spans[i] }}>{c.title}</span>)}
          </div>
        </VStack>
        <div className="fm-lc-grid" style={{ gridTemplateColumns: `150px repeat(${cols.length}, minmax(96px, 1fr))` }}>
          <span />
          {cols.map((c) => <div key={c.key} className={`fm-lc-vh ${c.tone}`}><b>{c.title}</b><span>{c.sub}</span></div>)}
          <span />
          {cols.map((c) => <div key={c.key} className="fm-lc-chg">{c.pill && <span className={`fm-lc-pill${c.pill.material ? ' mat' : ''}`}>{c.pill.label}</span>}</div>)}
          {checks.map((check) => [
            <Text key={check.key} type="body" weight="semibold">{check.label}</Text>,
            ...cols.map((c) => {
              const state = c.cells[check.key] ?? 'open'
              return <div key={`${c.key}:${check.key}`} className="fm-lc-c"><Cell state={state} size="lg" frozen={c.tone === 'old'} label={`${check.label}, ${c.title}: ${STATE_WORD[state]}`} /></div>
            }),
          ])}
        </div>
        <Legend />
      </VStack>
    </section>
  )
}

/** The lifespan bar: time in use against the years the records are kept. */
export function Lifespan({ from, lastDay, until, tall }: { from?: string; lastDay: string; until: string; tall?: boolean }) {
  const start = from ? +new Date(from) : +new Date(lastDay)
  const used = Math.max(1, +new Date(lastDay) - start)
  const kept = Math.max(1, +new Date(until) - +new Date(lastDay))
  return (
    <VStack gap={1}>
      <div className={`fm-lc-life${tall ? ' tall' : ''}`} aria-hidden>
        <b style={{ flex: used }} />
        <b className="kept" style={{ flex: kept }} />
      </div>
      <div className="fm-lc-lifel">
        <span>{from ? `In use ${when(from)} to ${when(lastDay)}` : `In use to ${when(lastDay)}`}</span>
        <span>Records kept to {when(until)}</span>
      </div>
    </VStack>
  )
}

const TASK_ICON: Record<string, ReactNode> = {
  stopped: <PowerOff size={18} aria-hidden />,
  no_pending: <ShieldCheck size={18} aria-hidden />,
  personal_data: <Database size={18} aria-hidden />,
  disconnected: <Unplug size={18} aria-hidden />,
  told: <MessageSquare size={18} aria-hidden />,
  replacement: <Users size={18} aria-hidden />,
}

const chainLine = (chain: Chain | undefined) => (chain?.status === 'broken' ? `Seal chain broken at ${chain.at}` : 'Seal chain intact')

/** A retired system's file: read only, its lifespan, the gate as it stood, and the sealed retirement record. */
export function RetiredCard({ record, createdAt, replacementName, chain }: { record: Retirement; createdAt?: string; replacementName?: string; chain?: Chain }) {
  return (
    <VStack gap={5}>
      <Banner
        status="info"
        title={`Retired ${when(record.lastDay)}`}
        description={`${REASON_LABEL[record.reason] ?? record.reason}${replacementName ? `, replaced by ${replacementName}` : ''}. This file is read only.`}
        icon={<Lock size={16} aria-hidden />}
      />
      <section className="fm-card" aria-labelledby="sf-life">
        <VStack gap={3}>
          <Heading level={2} id="sf-life">Lifespan</Heading>
          <Lifespan from={createdAt} lastDay={record.lastDay} until={record.retainUntil} tall />
          {record.retainBasis && <Text type="supporting" color="secondary">{record.retainBasis}</Text>}
        </VStack>
      </section>
      <section className="fm-card" aria-labelledby="sf-frozen">
        <VStack gap={3}>
          <Heading level={2} id="sf-frozen">Gate at retirement</Heading>
          <div className="fm-lc-impact">
            {record.gateSnapshot.map((c: CheckSnapshot) => (
              <div key={c.key} className="fm-lc-chk"><Cell state={c.state} frozen label={`${c.label}: ${STATE_WORD[c.state]}`} />{c.label}</div>
            ))}
          </div>
          <Legend reopen={false} />
        </VStack>
      </section>
      <section className="fm-card" aria-labelledby="sf-retire-rec">
        <VStack gap={3}>
          <HStack gap={2} vAlign="center" hAlign="between" wrap="wrap">
            <Heading level={2} id="sf-retire-rec">Retirement record</Heading>
            <Badge variant={chain?.status === 'broken' ? 'red' : 'green'} label={chainLine(chain)} />
          </HStack>
          <div className="fm-lc-recs">
            {record.tasks.map((t) => (
              <div key={t.key} className="fm-lc-rec">
                <span className="ico">{TASK_ICON[t.key] ?? <Archive size={18} aria-hidden />}</span>
                <Text type="body" weight="semibold">{t.label}</Text>
                <small>{t.who === 'fairmind' ? 'Checked by FairMind' : `Confirmed by ${t.by ?? record.retiredBy}`}</small>
              </div>
            ))}
          </div>
          <HStack gap={2} vAlign="center" wrap="wrap">
            <FileText size={16} aria-hidden />
            <Text type="supporting" color="secondary">Signed off by {record.retiredBy}, {when(record.retiredAt)}</Text>
            <span className="fm-lc-hash">{record.seal.slice(0, 4)}…{record.seal.slice(-4)}</span>
          </HStack>
          {record.note && <Text type="supporting">{record.note}</Text>}
        </VStack>
      </section>
    </VStack>
  )
}
