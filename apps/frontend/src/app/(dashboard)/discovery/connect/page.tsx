'use client'

import '@/astryx/pages/discovery.css'
import { useRouter, useSearchParams } from 'next/navigation'
import { Suspense, useMemo, useState } from 'react'
import { Banner } from '@astryxdesign/core/Banner'
import { Button } from '@astryxdesign/core/Button'
import { Heading, Text } from '@astryxdesign/core/Text'
import { HStack, VStack } from '@astryxdesign/core/Layout'
import { SegmentedControl, SegmentedControlItem } from '@astryxdesign/core/SegmentedControl'
import { TextInput } from '@astryxdesign/core/TextInput'
import { Token } from '@astryxdesign/core/Token'
import { SourceMark } from '@/astryx/DiscoveryParts'
import {
  KIND_LABEL,
  LANES,
  MAX_LOG_BYTES,
  SCHEDULES,
  SOURCES,
  createSource,
  previewSource,
  syncSource,
  uploadLogs,
  useDiscovery,
  type IntegrationKind,
  type Preview,
} from '@/astryx/data/discovery'

const KINDS = Object.keys(SOURCES) as IntegrationKind[]

function Catalog({ pick, onPick, connected }: { pick: IntegrationKind; onPick: (k: IntegrationKind) => void; connected: Set<string> }) {
  const [q, setQ] = useState('')
  const match = (k: IntegrationKind) => !q || `${SOURCES[k].label} ${SOURCES[k].reads}`.toLowerCase().includes(q.toLowerCase())
  return (
    <div className="dv-cat">
      <TextInput label="Find a source" isLabelHidden placeholder="Okta, AWS, proxy logs" value={q} onChange={setQ} />
      {LANES.map((l) => {
        const kinds = KINDS.filter((k) => SOURCES[k].lane === l.key && match(k))
        if (kinds.length === 0) return null
        const watched = KINDS.some((k) => SOURCES[k].lane === l.key && connected.has(k))
        return (
          <section key={l.key} aria-label={l.label}>
            <h3>
              <span>{l.label}</span>
              {!watched && <span className="gap">Not watched</span>}
            </h3>
            {kinds.map((k) => (
              <button key={k} type="button" className={`dv-pick${pick === k ? ' sel' : ''}`} aria-pressed={pick === k} onClick={() => onPick(k)}>
                <SourceMark kind={k} />
                <span style={{ minWidth: 0 }}>
                  <span className="nm" style={{ display: 'block' }}>{SOURCES[k].label}</span>
                  <span className="sub" style={{ display: 'block' }}>{SOURCES[k].reads}</span>
                </span>
                {connected.has(k) && <span className="tag">Connected</span>}
              </button>
            ))}
          </section>
        )
      })}
    </div>
  )
}

function Step({ n, done, title, children }: { n: number; done: boolean; title: string; children: React.ReactNode }) {
  return (
    <div className="dv-step">
      <span className={`dv-num${done ? ' done' : ''}`} aria-label={done ? `Step ${n} done` : `Step ${n}`}>
        {n}
      </span>
      <VStack gap={3}>
        <Heading level={3}>{title}</Heading>
        {children}
      </VStack>
    </div>
  )
}

function Setup({ kind, onDone }: { kind: IntegrationKind; onDone: () => void }) {
  const spec = SOURCES[kind]
  const [v, setV] = useState<Record<string, string>>({ name: spec.label })
  const [schedule, setSchedule] = useState('1440')
  const [file, setFile] = useState<File | null>(null)
  const [preview, setPreview] = useState<Preview | null>(null)
  const [busy, setBusy] = useState<'preview' | 'connect' | null>(null)
  const [err, setErr] = useState<string | null>(null)
  const [copied, setCopied] = useState(false)
  const f = (k: string) => (v[k] ?? '').trim()
  const set = (k: string) => (value: string) => {
    setV((p) => ({ ...p, [k]: value }))
    setPreview(null) // access changed; the earlier preview no longer describes it
  }
  const logs = kind === 'proxy_logs'
  const accessReady = spec.fields.every((x) => x.optional || f(x.key)) && (!spec.token || spec.tokenOptional || Boolean(f('token')))
  const body = () => ({
    kind,
    name: f('name') || spec.label,
    config: { ...Object.fromEntries(spec.fields.map((x) => [x.key, f(x.key)])), ...(logs ? {} : { schedule_minutes: Number(schedule) }) },
    token: f('token') || undefined,
  })

  async function runPreview() {
    setBusy('preview')
    setErr(null)
    try {
      setPreview(await previewSource(body()))
    } catch (e) {
      setErr(e instanceof Error ? e.message : 'FairMind could not read that source')
    } finally {
      setBusy(null)
    }
  }

  async function connect() {
    if (logs && file && file.size > MAX_LOG_BYTES) {
      setErr('That log file is over 20 MB. Export a shorter period or only the destination host column.')
      return
    }
    setBusy('connect')
    setErr(null)
    try {
      const created = await createSource(body())
      // The first read happens now, so the Sources view opens with real data rather than a wait.
      if (logs) {
        if (file) await uploadLogs(created.id, await file.text())
      } else {
        await syncSource(created.id).catch(() => undefined) // a failed first read shows on the Sources view
      }
      onDone()
    } catch (e) {
      setErr(e instanceof Error ? e.message : 'Could not connect the source')
      setBusy(null)
    }
  }

  return (
    <section className="fm-card" aria-labelledby="setup-title">
      <VStack gap={2}>
        <HStack gap={3} vAlign="center">
          <SourceMark kind={kind} />
          <VStack gap={0}>
            <Heading level={2} id="setup-title">
              {spec.label}
            </Heading>
            <Text color="secondary" size="sm">
              {spec.reads}
            </Text>
          </VStack>
        </HStack>

        <Step n={1} done={accessReady} title={logs ? 'Name this log source' : 'Give read-only access'}>
          <VStack gap={1}>
            <HStack hAlign="between" vAlign="center">
              <Text size="sm" color="secondary">
                {logs ? 'What the export needs' : 'Permissions to grant'}
              </Text>
              {!logs && (
                <Button
                  size="sm"
                  variant="ghost"
                  label={copied ? 'Copied' : 'Copy'}
                  onClick={() => {
                    void navigator.clipboard?.writeText(spec.permissions.join('\n'))
                    setCopied(true)
                    setTimeout(() => setCopied(false), 1500)
                  }}
                />
              )}
            </HStack>
            <pre className="dv-perms">{spec.permissions.join('\n')}</pre>
          </VStack>
          <div className="dv-fields">
            {spec.fields.map((x) => (
              <TextInput key={`${kind}-${x.key}`} label={x.label} description={x.description} value={v[x.key] ?? ''} onChange={set(x.key)} isRequired={!x.optional} isOptional={x.optional} />
            ))}
            {spec.token && (
              <div className="wide">
                <TextInput
                  label={spec.token}
                  description={spec.tokenDescription}
                  type="password"
                  value={v.token ?? ''}
                  onChange={set('token')}
                  isRequired={!spec.tokenOptional}
                  isOptional={spec.tokenOptional}
                  autoComplete="off"
                />
              </div>
            )}
          </div>
        </Step>

        <Step n={2} done={logs ? Boolean(file) : Boolean(preview)} title={logs ? 'Choose a log export' : 'See what it would find'}>
          {logs ? (
            <VStack gap={2}>
              <Text color="secondary" size="sm">
                CSV, JSON lines or plain text, up to 20 MB. FairMind reads the destination hosts and does not keep the file.
              </Text>
              <input type="file" accept=".csv,.log,.txt,.json,.jsonl,text/plain,text/csv,application/json" aria-label="Log export" onChange={(e) => setFile(e.target.files?.[0] ?? null)} />
            </VStack>
          ) : (
            <VStack gap={2}>
              <Text color="secondary" size="sm">
                FairMind reads the source once with this access and shows the result. Nothing is saved.
              </Text>
              <HStack>
                <Button variant="secondary" label={busy === 'preview' ? 'Reading the source' : 'Preview'} isDisabled={!accessReady || busy !== null} onClick={() => void runPreview()} />
              </HStack>
              {preview && (
                <div className="dv-preview" aria-live="polite">
                  <HStack gap={3} vAlign="end">
                    <span className="dv-big">{preview.found}</span>
                    <Text color="secondary">{preview.found === 1 ? 'item it would find' : 'items it would find'}</Text>
                  </HStack>
                  <div className="dv-chips">
                    {Object.entries(preview.byKind).map(([k, n]) => (
                      <span key={k} className="dv-chip">
                        {n} {KIND_LABEL[k] ?? k}
                      </span>
                    ))}
                  </div>
                  {preview.sample.map((s) => (
                    <HStack key={`${s.kind}-${s.name}`} gap={2} vAlign="center">
                      <Text>{s.name}</Text>
                      <Token size="sm" label={KIND_LABEL[s.kind] ?? s.kind} />
                      <span className={`dv-chip ${s.tier}`}>{s.tier} risk</span>
                    </HStack>
                  ))}
                  {preview.found > preview.sample.length && (
                    <Text color="secondary" size="sm">
                      and {preview.found - preview.sample.length} more
                    </Text>
                  )}
                </div>
              )}
            </VStack>
          )}
        </Step>

        <Step n={3} done={Boolean(f('name'))} title={logs ? 'Connect' : 'Keep watching'}>
          {!logs && (
            <SegmentedControl label="How often FairMind reads it" value={schedule} onChange={(x) => setSchedule(String(x))}>
              {SCHEDULES.map((s) => (
                <SegmentedControlItem key={s.minutes} value={String(s.minutes)} label={s.label} />
              ))}
            </SegmentedControl>
          )}
          <TextInput label="Name" description="How this source appears on the Sources view." value={v.name ?? ''} onChange={set('name')} isRequired />
          {err && <Banner status="error" title="That did not work" description={err} />}
          <HStack gap={2}>
            <Button
              variant="primary"
              label={busy === 'connect' ? 'Connecting' : logs ? 'Connect and read the file' : 'Connect and start watching'}
              isDisabled={!accessReady || !f('name') || busy !== null || (logs && !file)}
              onClick={() => void connect()}
            />
            <Button variant="ghost" label="Cancel" href="/discovery" />
          </HStack>
        </Step>
      </VStack>
    </section>
  )
}

function ConnectView() {
  const router = useRouter()
  const params = useSearchParams()
  const d = useDiscovery()
  const connected = useMemo(() => new Set<string>(d.integrations.map((i) => i.kind)), [d.integrations])
  const asked = params.get('source') as IntegrationKind | null
  // Start on the first source in an area nobody watches yet: that is where AI goes unseen.
  const suggested = useMemo(
    () => LANES.flatMap((l) => KINDS.filter((k) => SOURCES[k].lane === l.key)).find((k) => !KINDS.some((o) => SOURCES[o].lane === SOURCES[k].lane && connected.has(o))) ?? 'github',
    [connected],
  )
  const [chosen, setChosen] = useState<IntegrationKind | null>(asked && SOURCES[asked] ? asked : null)
  const pick = chosen ?? suggested

  return (
    <div className="fm-page">
      <VStack gap={5}>
        <HStack gap={4} hAlign="between" vAlign="end" wrap="wrap">
          <VStack gap={1}>
            <Heading level={1}>Connect a source</Heading>
            <Text color="secondary">Pick where to look, see what FairMind would find, then choose how often it keeps watching.</Text>
          </VStack>
          <Button label="Back to Discovery" variant="secondary" href="/discovery" />
        </HStack>
        <div className="dv-connect">
          <Catalog pick={pick} onPick={setChosen} connected={connected} />
          <Setup key={pick} kind={pick} onDone={() => router.push('/discovery?view=sources')} />
        </div>
      </VStack>
    </div>
  )
}

export default function ConnectSourcePage() {
  return (
    <Suspense fallback={null}>
      <ConnectView />
    </Suspense>
  )
}
