'use client'

import '@/astryx/pages/discovery.css'
import '@/astryx/pages/shadow-ai.css'
import { useRouter, useSearchParams } from 'next/navigation'
import { Suspense, useEffect, useMemo, useState } from 'react'
import { Banner } from '@astryxdesign/core/Banner'
import { Button } from '@astryxdesign/core/Button'
import { EmptyState } from '@astryxdesign/core/EmptyState'
import { HStack, VStack } from '@astryxdesign/core/Layout'
import { Selector } from '@astryxdesign/core/Selector'
import { Skeleton } from '@astryxdesign/core/Skeleton'
import { Switch } from '@astryxdesign/core/Switch'
import { Tab, TabList } from '@astryxdesign/core/TabList'
import { Heading, Text } from '@astryxdesign/core/Text'
import { TextArea } from '@astryxdesign/core/TextArea'
import { TextInput } from '@astryxdesign/core/TextInput'
import { SourceMark } from '@/astryx/DiscoveryParts'
import { ago } from '@/astryx/data/discovery'
import {
  listTools,
  markExpected,
  nudgePerson,
  reopenFinding,
  setToolStance,
  useShadowAI,
  type Finding,
  type FindingType,
  type ShadowAI,
  type Stance,
  type ToolStance,
} from '@/astryx/data/review'

const TYPE_LABEL: Record<FindingType, string> = {
  personal_account: 'people on personal accounts',
  leaver_key: "leavers' keys still active",
  gateway_bypass: 'calls skipping the gateway',
  not_allowed: "tools you don't allow",
  self_consent: 'apps people let in on their own',
  unregistered_mcp: 'MCP servers not in your registry',
}
const TYPES = Object.keys(TYPE_LABEL) as FindingType[]
const SEV_LABEL = { critical: 'Critical', high: 'High', medium: 'Medium' } as const
const CONF = ['possible', 'likely', 'confirmed'] as const
const STANCE_LABEL: Record<Stance, string> = { approved: 'Approved', limited: 'Approved for some teams', not_allowed: 'Not allowed', not_reviewed: 'Not reviewed' }

/** What each check needs, for the coverage list. */
const CHECKS: { type: FindingType; needs: string; on: (c: ShadowAI['coverage']) => boolean }[] = [
  { type: 'personal_account', needs: 'Proxy logs with a user column, Okta, and an approved tool marked "company accounts sign in through Okta"', on: (c) => c.proxyLogs && c.okta && c.ssoTools > 0 },
  { type: 'leaver_key', needs: 'OpenAI Admin API or LiteLLM, and Okta or Entra ID with the people step on', on: (c) => c.people > 0 },
  { type: 'gateway_bypass', needs: 'Proxy logs and a LiteLLM gateway', on: (c) => c.proxyLogs && c.gateway },
  { type: 'not_allowed', needs: 'Any sign-in or traffic source, and a tool marked not allowed', on: (c) => (c.proxyLogs || c.okta || c.entra) && c.approvedTools > 0 },
  { type: 'self_consent', needs: 'Entra ID', on: (c) => c.entra },
  { type: 'unregistered_mcp', needs: 'GitHub and an MCP registry', on: (c) => c.mcpRegistry },
]

function nudgeText(f: Finding): string {
  const tool = f.title.replace(/^Personal | account$/g, '')
  return `Hi,\n\nIt looks like ${tool} on your account is being used with a personal login rather than your company account. Please sign in with your company account, so your work stays under the company's agreement with the vendor.\n\nIf this is wrong, reply to this email and let us know.`
}

function Scale({ value }: { value: Finding['confidence'] }) {
  return (
    <div className="sh-scale" role="img" aria-label={`How sure: ${value}`}>
      {CONF.map((c) => (
        <span key={c} className={c === value ? 'on' : ''}>
          {c[0].toUpperCase() + c.slice(1)}
        </span>
      ))}
    </div>
  )
}

function Tiles({ findings, type, onType }: { findings: Finding[]; type: FindingType | null; onType: (t: FindingType | null) => void }) {
  const shown = TYPES.filter((t) => findings.some((f) => f.type === t))
  if (!shown.length) return null
  return (
    <div className="sh-tiles">
      {shown.map((t) => {
        const n = findings.filter((f) => f.type === t).length
        return (
          <button key={t} type="button" className={`sh-tile${type === t ? ' on' : ''}`} aria-pressed={type === t} onClick={() => onType(type === t ? null : t)}>
            <span className="n">{n}</span>
            <span className="t">{TYPE_LABEL[t]}</span>
          </button>
        )
      })}
    </div>
  )
}

function UsageMap({ map }: { map: ShadowAI['map'] }) {
  if (!map.tools.length || !map.teams.length) return null
  return (
    <section className="fm-card" aria-labelledby="map-title">
      <VStack gap={3}>
        <HStack hAlign="between" vAlign="center" wrap="wrap" gap={2}>
          <div>
            <Heading level={2} id="map-title">
              What you approved, and what people use
            </Heading>
            <Text size="sm" color="secondary">
              People per team, from Okta sign-ins and proxy logs. Teams come from your directory.
            </Text>
          </div>
          <Button size="sm" variant="ghost" label="Edit approved tools" href="/shadow-ai?view=tools" />
        </HStack>
        <div className="sh-mapwrap">
          <table className="sh-map">
            <thead>
              <tr>
                <th scope="col">Team</th>
                {map.tools.map((t) => (
                  <th key={t.key} scope="col">
                    {t.label}
                    <span className={`st ${t.status}`}>{t.status === 'limited' && t.teams.length ? `Approved for ${t.teams.join(', ')}` : STANCE_LABEL[t.status]}</span>
                  </th>
                ))}
              </tr>
            </thead>
            <tbody>
              {map.teams.map((team) => (
                <tr key={team}>
                  <th scope="row">{team}</th>
                  {map.tools.map((t) => {
                    const c = map.cells[team]?.[t.key] ?? { company: 0, personal: 0, unapproved: 0 }
                    const empty = !c.company && !c.personal && !c.unapproved
                    return (
                      <td key={t.key}>
                        {empty ? (
                          <span className="sh-sq none" aria-label="None seen" />
                        ) : (
                          <>
                            {c.company > 0 && (
                              <span className="sh-c">
                                <span className="sh-sq co" aria-hidden="true" />
                                {c.company}
                              </span>
                            )}
                            {c.personal > 0 && (
                              <span className="sh-c">
                                <span className="sh-sq pe" aria-hidden="true" />
                                {c.personal}
                              </span>
                            )}
                            {c.unapproved > 0 && (
                              <span className="sh-c">
                                <span className="sh-sq un" aria-hidden="true" />
                                {c.unapproved}
                              </span>
                            )}
                          </>
                        )}
                      </td>
                    )
                  })}
                </tr>
              ))}
            </tbody>
          </table>
        </div>
        <div className="sh-legend">
          <span><span className="sh-sq co" />Company account</span>
          <span><span className="sh-sq pe" />Personal account</span>
          <span><span className="sh-sq un" />Tool not approved</span>
          <span><span className="sh-sq none" />None seen</span>
        </div>
      </VStack>
    </section>
  )
}

function FindingList({ findings, selected, onPick }: { findings: Finding[]; selected: string | null; onPick: (key: string) => void }) {
  return (
    <section className="fm-card dv-wlist" aria-label="Findings">
      <div className="dv-wlist-hd">
        <Text size="sm" weight="semibold" color="secondary">
          {findings.length} {findings.length === 1 ? 'finding' : 'findings'}
        </Text>
        <Text size="sm" color="secondary">
          Most serious first
        </Text>
      </div>
      {findings.map((f) => (
        <button key={f.key} type="button" className={`dv-witem${selected === f.key ? ' on' : ''}`} aria-current={selected === f.key} onClick={() => onPick(f.key)}>
          <span style={{ minWidth: 0 }}>
            <span className="nm">{f.title}</span>
            <span className="k">
              {[f.team && f.team !== 'No team' ? f.team : null, f.subject, `since ${ago(f.firstSeen)}`].filter(Boolean).join(' · ')}
            </span>
          </span>
          <span className={`dv-chip sev-${f.severity}`}>{SEV_LABEL[f.severity]}</span>
          <span className={`sh-cf ${f.confidence}`}>
            <i aria-hidden="true" />
            {f.confidence[0].toUpperCase() + f.confidence.slice(1)}
          </span>
          {f.status === 'expected' ? <span className="dv-chip">Expected</span> : f.nudgedAt ? <span className="dv-chip">Nudged {ago(f.nudgedAt)}</span> : <span />}
        </button>
      ))}
    </section>
  )
}

function FindingPanel({ f, onChanged }: { f: Finding; onChanged: () => Promise<void> }) {
  const [message, setMessage] = useState(() => nudgeText(f))
  const [reason, setReason] = useState('')
  const [busy, setBusy] = useState(false)
  const [note, setNote] = useState<{ ok: boolean; text: string } | null>(null)
  async function act(fn: () => Promise<unknown>, done: string) {
    setBusy(true)
    setNote(null)
    try {
      await fn()
      await onChanged()
      setNote({ ok: true, text: done })
    } catch (e) {
      setNote({ ok: false, text: e instanceof Error ? e.message : 'That did not work' })
    } finally {
      setBusy(false)
    }
  }
  const canNudge = f.type === 'personal_account' && !!f.person
  return (
    <VStack gap={4}>
      <section className="fm-card">
        <HStack hAlign="between" vAlign="start" wrap="wrap" gap={3}>
          <VStack gap={2}>
            <HStack gap={2} vAlign="center" wrap="wrap">
              <Heading level={2}>{f.title}</Heading>
              <span className={`dv-chip sev-${f.severity}`}>{SEV_LABEL[f.severity]}</span>
            </HStack>
            <HStack gap={2} vAlign="center" wrap="wrap">
              <span className="dv-av" aria-hidden="true">
                {f.subject.slice(0, 2).toUpperCase()}
              </span>
              <Text weight="semibold">{f.person ?? f.subject}</Text>
              {f.team && f.team !== 'No team' && (
                <Text size="sm" color="secondary">
                  {f.team}
                </Text>
              )}
            </HStack>
            <Text size="sm" color="secondary">
              First seen {ago(f.firstSeen)} · last seen {ago(f.lastSeen)}
              {f.nudgedAt ? ` · nudged ${ago(f.nudgedAt)}` : ''}
            </Text>
          </VStack>
          <VStack gap={1}>
            <Text size="sm" weight="semibold" color="secondary">
              How sure
            </Text>
            <Scale value={f.confidence} />
          </VStack>
        </HStack>
      </section>

      <section className="fm-card" aria-labelledby="know-title">
        <VStack gap={3}>
          <div>
            <Heading level={3} id="know-title">
              How we know
            </Heading>
            <Text size="sm" color="secondary">
              {f.evidence.length > 1 ? `No single source says it. ${f.evidence.length} sources together do.` : 'From one source.'}
            </Text>
          </div>
          <ol className="sh-chain">
            {f.evidence.map((e, i) => (
              <li key={i}>
                <SourceMark kind={e.source} />
                <span>
                  <span className="t">{e.title}</span>
                  <span className="s">{e.detail}</span>
                </span>
              </li>
            ))}
          </ol>
          <div className="dv-miss">
            <span className="dot" aria-hidden="true" />
            <span>{f.verdict}</span>
          </div>
          {f.confirm && f.confidence !== 'confirmed' && (
            <div className="sh-maybe">
              <span className="dv-mark ghost" aria-hidden="true">
                +
              </span>
              <span>
                <span className="t">Would make it confirmed</span>
                <span className="s">{f.confirm}</span>
              </span>
            </div>
          )}
        </VStack>
      </section>

      {note && <Banner status={note.ok ? 'success' : 'error'} title={note.ok ? 'Done' : 'That did not work'} description={note.text} isDismissable onDismiss={() => setNote(null)} />}

      <div className="dv-two">
        {canNudge ? (
          <section className="fm-card" aria-labelledby="nudge-title">
            <VStack gap={3}>
              <Heading level={3} id="nudge-title">
                Nudge {f.person} first
              </Heading>
              <TextArea label="Message" rows={8} value={message} onChange={(v) => setMessage(v)} description="Sent by email. Edit it before you send." />
              <HStack gap={2}>
                <Button variant="primary" label={busy ? 'Sending' : f.nudgedAt ? 'Send again' : 'Send nudge'} isDisabled={busy || !message.trim()} onClick={() => void act(() => nudgePerson(f.key, message), `Sent to ${f.person}`)} />
              </HStack>
            </VStack>
          </section>
        ) : (
          <section className="fm-card">
            <VStack gap={2}>
              <Heading level={3}>What to do</Heading>
              <Text size="sm">{f.verdict}</Text>
            </VStack>
          </section>
        )}
        <section className="fm-card" aria-labelledby="handle-title">
          <VStack gap={3}>
            <Heading level={3} id="handle-title">
              {f.status === 'expected' ? 'Marked as expected' : 'Not a problem?'}
            </Heading>
            {f.status === 'expected' ? (
              <>
                <Text size="sm">{f.reason}</Text>
                <HStack>
                  <Button variant="secondary" label="Reopen" isDisabled={busy} onClick={() => void act(() => reopenFinding(f.key), 'Reopened')} />
                </HStack>
              </>
            ) : (
              <>
                <TextInput label="Why it is expected" value={reason} onChange={setReason} description="Kept with the finding, so the next person sees why." />
                <HStack>
                  <Button variant="secondary" label="Mark as expected" isDisabled={busy || !reason.trim()} onClick={() => void act(() => markExpected(f.key, reason.trim()), 'Marked as expected')} />
                </HStack>
              </>
            )}
          </VStack>
        </section>
      </div>
    </VStack>
  )
}

function ToolsTab({ onSaved }: { onSaved: () => void }) {
  const [tools, setTools] = useState<ToolStance[] | null>(null)
  const [error, setError] = useState<string | null>(null)
  const [busy, setBusy] = useState<string | null>(null)
  const [teams, setTeams] = useState<Record<string, string>>({})
  const [q, setQ] = useState('')
  useEffect(() => {
    listTools()
      .then((t) => {
        setTools(t)
        setTeams(Object.fromEntries(t.map((x) => [x.key, (x.stance?.teams ?? []).join(', ')])))
      })
      .catch((e) => setError(e instanceof Error ? e.message : 'Could not load the tools'))
  }, [])
  async function save(t: ToolStance, status: Stance, sso: boolean) {
    setBusy(t.key)
    setError(null)
    try {
      const teamList = (teams[t.key] ?? '').split(',').map((x) => x.trim()).filter(Boolean)
      await setToolStance(t.key, { status: status === 'not_reviewed' ? null : status, teams: status === 'limited' ? teamList : [], sso_required: sso })
      setTools(await listTools())
      onSaved()
    } catch (e) {
      setError(e instanceof Error ? e.message : 'Not saved')
    } finally {
      setBusy(null)
    }
  }
  if (!tools) return error ? <Banner status="error" title="Could not load" description={error} /> : <Skeleton height={320} />
  const shown = tools.filter((t) => !q || `${t.label} ${t.vendor}`.toLowerCase().includes(q.toLowerCase()))
  shown.sort((a, b) => Number(!a.stance) - Number(!b.stance))
  return (
    <section className="fm-card" aria-labelledby="tools-title">
      <VStack gap={3}>
        <div>
          <Heading level={2} id="tools-title">
            Approved tools
          </Heading>
          <Text size="sm" color="secondary">
            Shadow AI compares what people use with this list. Mark the tools whose company accounts sign in through Okta, so personal accounts stand out.
          </Text>
        </div>
        {error && <Banner status="error" title="Not saved" description={error} />}
        <TextInput label="Find a tool" isLabelHidden placeholder="Find a tool" value={q} onChange={setQ} />
        <div className="sh-tools">
          {shown.map((t) => {
            const status: Stance = t.stance?.status ?? 'not_reviewed'
            const sso = !!t.stance?.sso_required
            return (
              <div key={t.key} className="sh-tool">
                <span style={{ minWidth: 0 }}>
                  <span className="nm">{t.label}</span>
                  <span className="k">{t.vendor}</span>
                </span>
                <Selector
                  label={`Stance on ${t.label}`}
                  isLabelHidden
                  size="sm"
                  value={status}
                  options={(Object.keys(STANCE_LABEL) as Stance[]).map((s) => ({ value: s, label: STANCE_LABEL[s] }))}
                  onChange={(v: string) => (v === 'limited' && !(teams[t.key] ?? '').trim() ? setTools((all) => all && all.map((x) => (x.key === t.key ? { ...x, stance: { status: 'limited', teams: [], sso_required: sso, note: null, updatedAt: '' } } : x))) : void save(t, v as Stance, sso))}
                />
                {status === 'limited' ? (
                  <HStack gap={2} vAlign="end">
                    <TextInput label="Teams" size="sm" value={teams[t.key] ?? ''} onChange={(v) => setTeams((p) => ({ ...p, [t.key]: v }))} placeholder="Engineering, Support" />
                    <Button size="sm" variant="secondary" label="Save" isDisabled={busy === t.key || !(teams[t.key] ?? '').trim()} onClick={() => void save(t, 'limited', sso)} />
                  </HStack>
                ) : (
                  <span />
                )}
                <Switch
                  label="Company accounts sign in through Okta"
                  value={sso}
                  isDisabled={busy === t.key || status === 'not_reviewed' || status === 'not_allowed'}
                  onChange={(on: boolean) => void save(t, status, on)}
                />
              </div>
            )
          })}
        </div>
      </VStack>
    </section>
  )
}

function ReadsTab({ coverage }: { coverage: ShadowAI['coverage'] }) {
  return (
    <div className="dv-two">
      <section className="fm-card">
        <VStack gap={3}>
          <Heading level={2}>Checks</Heading>
          {CHECKS.map((c) => {
            const on = c.on(coverage)
            return (
              <div key={c.type} className="sh-check">
                <i className={`dv-dot ${on ? 'live' : ''}`} aria-hidden="true" />
                <span>
                  <span className="t">{TYPE_LABEL[c.type][0].toUpperCase() + TYPE_LABEL[c.type].slice(1)}</span>
                  <span className="s">{on ? 'Running. ' : 'Not running: needs '}{on ? '' : c.needs.charAt(0).toLowerCase() + c.needs.slice(1)}</span>
                </span>
              </div>
            )
          })}
          <HStack>
            <Button variant="secondary" label="Connect a source" href="/discovery/connect" />
          </HStack>
        </VStack>
      </section>
      <section className="fm-card">
        <VStack gap={2}>
          <Heading level={2}>What this reads</Heading>
          <Text size="sm" weight="semibold" color="secondary">
            Reads
          </Text>
          <ul className="sh-rd">
            <li>Web domains and request counts per person, from log exports you upload</li>
            <li>Sign-ins to company apps, people&apos;s teams and who has left</li>
            <li>Vendor and gateway keys: owner and when last used</li>
            <li>MCP servers in code and in your registry</li>
          </ul>
          <Text size="sm" weight="semibold" color="secondary">
            Never reads
          </Text>
          <ul className="sh-rd">
            <li>Prompts, replies or file contents</li>
            <li>The address of anyone&apos;s personal account</li>
            <li>Screens or keystrokes</li>
          </ul>
          <Text size="sm" color="secondary">
            Tell staff about this in your acceptable use policy. People&apos;s names are shown only to members of your organisation in FairMind.
          </Text>
        </VStack>
      </section>
    </div>
  )
}

function ShadowView() {
  const router = useRouter()
  const params = useSearchParams()
  const v = params.get('view')
  const view = v === 'expected' || v === 'resolved' || v === 'tools' || v === 'reads' ? v : 'open'
  const { data, loading, error, refresh } = useShadowAI()
  const [type, setType] = useState<FindingType | null>(null)
  const open = useMemo(() => (data?.findings ?? []).filter((f) => f.status === 'open'), [data])
  const expected = useMemo(() => (data?.findings ?? []).filter((f) => f.status === 'expected'), [data])
  const list = (view === 'expected' ? expected : open).filter((f) => !type || f.type === type)
  const picked = params.get('f')
  const selected = list.find((f) => f.key === picked) ?? list[0] ?? null
  const go = (tab: string, f?: string) => router.replace(`/shadow-ai${tab === 'open' ? '' : `?view=${tab}`}${f ? `${tab === 'open' ? '?' : '&'}f=${encodeURIComponent(f)}` : ''}`)
  const off = data ? CHECKS.filter((c) => !c.on(data.coverage)).length : 0

  return (
    <div className="fm-page">
      <VStack gap={5}>
        <VStack gap={1}>
          <Heading level={1}>Shadow AI</Heading>
          <Text color="secondary">AI used outside what you approved, worked out by comparing your connected sources with each other. It never reads prompts or file contents.</Text>
        </VStack>
        <TabList value={view} onChange={(t) => go(t)} hasDivider aria-label="Shadow AI view">
          <Tab value="open" label={`Open${open.length ? ` ${open.length}` : ''}`} />
          <Tab value="expected" label={`Expected${expected.length ? ` ${expected.length}` : ''}`} />
          <Tab value="resolved" label="Resolved" />
          <Tab value="tools" label="Approved tools" />
          <Tab value="reads" label={`What it reads${off ? ` · ${off} off` : ''}`} />
        </TabList>
        {loading ? (
          <Skeleton height={360} />
        ) : error || !data ? (
          <EmptyState title="Shadow AI could not load" description={error ?? ''} actions={<Button label="Try again" onClick={() => void refresh()} />} />
        ) : view === 'tools' ? (
          <ToolsTab onSaved={() => void refresh()} />
        ) : view === 'reads' ? (
          <ReadsTab coverage={data.coverage} />
        ) : view === 'resolved' ? (
          <section className="fm-card">
            <VStack gap={2}>
              <Heading level={2}>Resolved</Heading>
              <Text size="sm" color="secondary">
                Findings that stopped showing up in your sources.
              </Text>
              {data.resolved.length === 0 && <Text color="secondary">Nothing resolved yet.</Text>}
              {data.resolved.map((r) => (
                <div key={r.key} className="dv-row" style={{ gridTemplateColumns: 'minmax(0, 1fr) auto' }}>
                  <span className="nm" style={{ overflowWrap: 'anywhere' }}>
                    {r.key.split(':').slice(1).join(':')}
                  </span>
                  <Text size="sm" color="secondary">
                    last seen {ago(r.lastSeen)}
                  </Text>
                </div>
              ))}
            </VStack>
          </section>
        ) : (
          <>
            {view === 'open' && off > 0 && (
              <Banner
                status="info"
                title={`${off} of ${CHECKS.length} checks are not running yet`}
                description="Each check compares two sources. See which sources each one needs."
                endContent={<Button size="sm" variant="secondary" label="See what it needs" onClick={() => go('reads')} />}
              />
            )}
            {view === 'open' && <Tiles findings={open} type={type} onType={setType} />}
            {view === 'open' && <UsageMap map={data.map} />}
            {list.length === 0 ? (
              <EmptyState
                title={view === 'expected' ? 'Nothing marked as expected' : 'No open findings'}
                description={view === 'expected' ? 'Findings you mark as expected, with the reason, appear here.' : 'Nothing your sources show is outside what you approved.'}
              />
            ) : (
              <div className="dv-split">
                <FindingList findings={list} selected={selected?.key ?? null} onPick={(k) => go(view, k)} />
                {selected && <FindingPanel key={selected.key} f={selected} onChanged={refresh} />}
              </div>
            )}
          </>
        )}
      </VStack>
    </div>
  )
}

export default function ShadowAIPage() {
  return (
    <Suspense fallback={null}>
      <ShadowView />
    </Suspense>
  )
}
