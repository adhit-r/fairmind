'use client'

import '@/astryx/pages/discovery.css'
import '@/astryx/pages/tasks.css'
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

type Vendor = NonNullable<(typeof SOURCES)[IntegrationKind]['vendor']>
/** A vendor's connections in catalogue order, each with the kinds (plans) behind it. */
function connections(vendor: Vendor) {
  const out: Array<{ name: string; kinds: IntegrationKind[] }> = []
  for (const k of KINDS) {
    const s = SOURCES[k]
    if (s.vendor !== vendor) continue
    const name = s.connection ?? s.label
    const c = out.find((x) => x.name === name)
    if (c) c.kinds.push(k)
    else out.push({ name, kinds: [k] })
  }
  return out
}
const connectionNames = (vendor: Vendor) => connections(vendor).map((c) => c.name)
/** Catalogue rows: a vendor's kinds collapse into one row that opens on its first connection. */
function entries(kinds: IntegrationKind[]) {
  const rows: Array<{ k: IntegrationKind; vendor?: Vendor; all: IntegrationKind[] }> = []
  for (const k of kinds) {
    const vendor = SOURCES[k].vendor
    if (!vendor) rows.push({ k, all: [k] })
    else if (!rows.some((r) => r.vendor === vendor)) rows.push({ k: connections(vendor)[0].kinds[0], vendor, all: KINDS.filter((x) => SOURCES[x].vendor === vendor) })
  }
  return rows
}

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
            {entries(kinds).map(({ k, vendor, all }) => {
              const sel = vendor ? SOURCES[pick].vendor === vendor : pick === k
              const on = all.some((x) => connected.has(x))
              return (
                <button key={vendor ?? k} type="button" className={`dv-pick${sel ? ' sel' : ''}`} aria-pressed={sel} onClick={() => onPick(k)}>
                  <SourceMark kind={k} />
                  <span style={{ minWidth: 0 }}>
                    <span className="nm" style={{ display: 'block' }}>{vendor ?? SOURCES[k].label}</span>
                    <span className="sub" style={{ display: 'block' }}>{vendor ? connectionNames(vendor).join(' and ') : SOURCES[k].reads}</span>
                  </span>
                  {on && <span className="tag">Connected</span>}
                </button>
              )
            })}
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


const APPS: Record<string, string[]> = {
  chatgpt_workspace: ['Google Drive', 'SharePoint', 'OneDrive', 'GitHub', 'Gmail', 'Outlook', 'Slack', 'Box', 'Notion'],
  claude_team: ['Google Drive', 'Gmail', 'Google Calendar', 'GitHub', 'Slack', 'Notion', 'Asana', 'Linear'],
}
const REVIEW = [
  { days: '30', label: 'Month' },
  { days: '90', label: 'Quarter' },
  { days: '180', label: '6 months' },
]

/** A plan with no admin API: the admin describes the workspace once, and FairMind asks again on the review cadence. */
function WorkspaceForm({ kind, onDone, onSwitch }: { kind: IntegrationKind; onDone: () => void; onSwitch: (k: IntegrationKind) => void }) {
  const spec = SOURCES[kind]
  const chatgpt = kind === 'chatgpt_workspace'
  const assistant = chatgpt ? 'custom GPT' : 'project'
  const [v, setV] = useState<Record<string, string>>({ name: spec.label, memory: 'on', history: 'until deleted' })
  const [assistants, setAssistants] = useState<Array<{ name: string; purpose: string; audience: string }>>([{ name: '', purpose: '', audience: 'workspace' }])
  const [apps, setApps] = useState<string[]>([])
  const [other, setOther] = useState('')
  const [review, setReview] = useState('90')
  const [busy, setBusy] = useState(false)
  const [err, setErr] = useState<string | null>(null)
  const set = (k: string) => (value: string) => setV((p) => ({ ...p, [k]: value }))
  const f = (k: string) => (v[k] ?? '').trim()
  const described = Boolean(f('workspace_name'))
  const toggleApp = (a: string) => setApps((p) => (p.includes(a) ? p.filter((x) => x !== a) : [...p, a]))

  async function connect() {
    setBusy(true)
    setErr(null)
    try {
      const config = {
        workspace_name: f('workspace_name'),
        plan: spec.plan,
        seats: f('seats'),
        owner: f('owner'),
        assistants: assistants.filter((a) => a.name.trim()),
        apps: [...apps, ...other.split(',').map((x) => x.trim()).filter(Boolean)],
        memory: f('memory'),
        history: f('history'),
        review_days: Number(review),
      }
      const created = await createSource({ kind, name: f('name') || spec.label, config })
      await syncSource(created.id).catch(() => undefined)
      onDone()
    } catch (e) {
      setErr(e instanceof Error ? e.message : 'Could not save the workspace')
      setBusy(false)
    }
  }

  return (
    <>
      <Banner
        status="info"
        title={`${chatgpt ? 'OpenAI' : 'Anthropic'} offers no admin API for ${spec.plan} workspaces`}
        description="You describe the workspace once. FairMind checks who really uses it from your sign-in and traffic sources, and asks you to review the description on a schedule."
      />
      <Step n={1} done={described} title="Describe the workspace">
        <Text color="secondary" size="sm">Copy these from the admin settings, under Workspace.</Text>
        <div className="dv-fields">
          <TextInput label="Workspace name" value={v.workspace_name ?? ''} onChange={set('workspace_name')} isRequired />
          <TextInput label="Seats" value={v.seats ?? ''} onChange={set('seats')} isOptional />
          <div className="wide">
            <TextInput label="Owner" description="Who administers the workspace" value={v.owner ?? ''} onChange={set('owner')} isOptional />
          </div>
        </div>
      </Step>
      <Step n={2} done={described} title="What it shares and can reach">
        <Text weight="semibold" size="sm">{chatgpt ? 'Custom GPTs shared in the workspace' : 'Projects shared in the workspace'}</Text>
        <VStack gap={2}>
          {assistants.map((a, i) => (
            <div key={i} className="dv-fields" style={{ gridTemplateColumns: 'minmax(140px,1fr) minmax(180px,1.6fr) 170px auto', alignItems: 'end' }}>
              <TextInput label="Name" value={a.name} onChange={(x) => setAssistants((p) => p.map((y, j) => (j === i ? { ...y, name: x } : y)))} />
              <TextInput label="What it is for" value={a.purpose} onChange={(x) => setAssistants((p) => p.map((y, j) => (j === i ? { ...y, purpose: x } : y)))} />
              <label style={{ display: 'flex', flexDirection: 'column', gap: 6, fontSize: 13, fontWeight: 600 }}>
                Who can use it
                <select className="tk-in" value={a.audience} onChange={(e) => setAssistants((p) => p.map((y, j) => (j === i ? { ...y, audience: e.target.value } : y)))}>
                  <option value="workspace">Whole workspace</option>
                  <option value="groups">Some groups</option>
                  <option value="owner">Only its owner</option>
                </select>
              </label>
              <Button variant="ghost" size="sm" label="Remove" aria-label={`Remove this ${assistant}`} onClick={() => setAssistants((p) => p.filter((_, j) => j !== i))} />
            </div>
          ))}
          <HStack>
            <Button variant="secondary" size="sm" label={`Add a ${assistant}`} onClick={() => setAssistants((p) => [...p, { name: '', purpose: '', audience: 'workspace' }])} />
          </HStack>
        </VStack>
        <Text weight="semibold" size="sm">Apps it can reach</Text>
        <div className="dv-chips" role="group" aria-label="Apps it can reach">
          {APPS[kind].map((a) => (
            <label key={a} className="dv-chip" style={{ cursor: 'pointer', display: 'inline-flex', gap: 6, alignItems: 'center' }}>
              <input type="checkbox" checked={apps.includes(a)} onChange={() => toggleApp(a)} /> {a}
            </label>
          ))}
        </div>
        <TextInput label="Other apps" description="Comma separated" value={other} onChange={setOther} isOptional />
        <div className="dv-fields">
          <label style={{ display: 'flex', flexDirection: 'column', gap: 6, fontSize: 13, fontWeight: 600 }}>
            Memory
            <select className="tk-in" value={v.memory} onChange={(e) => set('memory')(e.target.value)}>
              <option value="on">On</option>
              <option value="off">Off</option>
            </select>
          </label>
          <label style={{ display: 'flex', flexDirection: 'column', gap: 6, fontSize: 13, fontWeight: 600 }}>
            Conversation history kept
            <select className="tk-in" value={v.history} onChange={(e) => set('history')(e.target.value)}>
              <option value="until deleted">Until people delete it</option>
              <option value="set period">A set period</option>
            </select>
          </label>
        </div>
        <Text color="secondary" size="sm">Training on your data is off for business plans, as {chatgpt ? 'OpenAI' : 'Anthropic'} sets it.</Text>
      </Step>
      <Step n={3} done={false} title="Confirm who uses it">
        <Text color="secondary" size="sm">FairMind matches people with a seat against these sources once they are connected.</Text>
        <HStack gap={2} wrap="wrap">
          <Button variant="secondary" size="sm" label="Connect Okta" onClick={() => onSwitch('okta')} />
          <Button variant="secondary" size="sm" label="Connect Microsoft Entra" onClick={() => onSwitch('entra')} />
          <Button variant="secondary" size="sm" label="Upload proxy logs" onClick={() => onSwitch('proxy_logs')} />
        </HStack>
      </Step>
      <Step n={4} done={Boolean(f('name'))} title="Review it again">
        <SegmentedControl label="Ask for a review every" value={review} onChange={(x) => setReview(String(x))}>
          {REVIEW.map((r) => (
            <SegmentedControlItem key={r.days} value={r.days} label={r.label} />
          ))}
        </SegmentedControl>
        <TextInput label="Name" description="How this source appears on the Sources view." value={v.name ?? ''} onChange={set('name')} isRequired />
        {err && <Banner status="error" title="That did not work" description={err} />}
        <HStack gap={2}>
          <Button variant="primary" label={busy ? 'Saving' : 'Save the workspace'} isDisabled={!described || !f('name') || busy} onClick={() => void connect()} />
          <Button variant="ghost" label="Cancel" href="/discovery" />
        </HStack>
      </Step>
    </>
  )
}

/** A vendor's connections side by side; a workspace connection also picks its plan. */
function VendorTiles({ kind, onSwitch, connected }: { kind: IntegrationKind; onSwitch: (k: IntegrationKind) => void; connected: Set<string> }) {
  const vendor = SOURCES[kind].vendor!
  const conns = connections(vendor)
  const current = conns.find((c) => c.kinds.includes(kind))!
  return (
    <VStack gap={3}>
      <div className="dv-conns" role="group" aria-label={`${vendor} connections`}>
        {conns.map((c) => {
          const on = c.kinds.some((k) => connected.has(k))
          const sel = c === current
          return (
            <button key={c.name} type="button" className={`dv-conn${sel ? ' sel' : ''}${on ? ' on' : ''}`} aria-pressed={sel} onClick={() => onSwitch(c.kinds[0])}>
              <span className="cn">{c.name}</span>
              <span className="cs">{SOURCES[c.kinds[0]].reads}</span>
              <span className="st">{on ? 'Connected' : sel ? 'Setting up' : 'Not connected'}</span>
            </button>
          )
        })}
      </div>
      {(current.kinds.length > 1 || vendor === 'OpenAI') && current.kinds.some((k) => SOURCES[k].plan) && (
        <HStack gap={3} vAlign="center" wrap="wrap">
          <Text weight="semibold" size="sm">Which plan is it on?</Text>
          <div className="dv-plan" role="group" aria-label="Plan">
            {current.kinds.map((k) => (
              <button key={k} type="button" aria-pressed={k === kind} className={k === kind ? 'on' : ''} onClick={() => onSwitch(k)}>
                {SOURCES[k].plan}
              </button>
            ))}
            {vendor === 'OpenAI' && current.name === 'ChatGPT workspace' && (
              <button type="button" disabled aria-disabled="true" title="Coming soon: reading the ChatGPT Enterprise Compliance and Analytics APIs">
                Enterprise or Edu · coming soon
              </button>
            )}
          </div>
        </HStack>
      )}
    </VStack>
  )
}

function Setup({ kind, onDone, onSwitch, connected }: { kind: IntegrationKind; onDone: () => void; onSwitch: (k: IntegrationKind) => void; connected: Set<string> }) {
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
              {spec.vendor ?? spec.label}
            </Heading>
            <Text color="secondary" size="sm">
              {spec.vendor ? `Connect ${connectionNames(spec.vendor).join(', the ')}, or both. Each one is read on its own.` : spec.reads}
            </Text>
          </VStack>
        </HStack>
        {spec.vendor && <VendorTiles kind={kind} onSwitch={onSwitch} connected={connected} />}
        {spec.managedIn ? (
          <VStack gap={2}>
            <Text size="sm">{spec.managedIn.text}</Text>
            <HStack>
              <Button variant="primary" label="Set it up" href={spec.managedIn.href} />
            </HStack>
          </VStack>
        ) : spec.described ? (
          <WorkspaceForm kind={kind} onDone={onDone} onSwitch={onSwitch} />
        ) : (
        <>

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
        </>
        )}
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
          <Setup key={pick} kind={pick} onDone={() => router.push('/discovery?view=sources')} onSwitch={setChosen} connected={connected} />
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
