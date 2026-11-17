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
import { LANES, SOURCES, ago, type IntegrationKind } from '@/astryx/data/discovery'
import {
  listTools,
  markExpected,
  nudgePerson,
  reopenFinding,
  agentSettings,
  createAgent,
  downloadScript,
  getAgent,
  newAgentSecret,
  newNotifierSecret,
  setAgentRules,
  getReading,
  getScriptStatus,
  getTenantRules,
  newScriptToken,
  setScriptDomains,
  setToolStance,
  useEvidence,
  writeReading,
  useLaptops,
  useShadowAI,
  type Evidence,
  type EvidenceRow,
  type Finding,
  type AgentAction,
  type AgentEvent,
  type AgentRule,
  type AgentStatus,
  type EdgeModel,
  type Reading,
  type ScriptStatus,
  type TenantRules,
  type Story,
  type FindingType,
  type ShadowAI,
  type Stance,
  type ToolStance,
} from '@/astryx/data/review'

const TYPE_LABEL: Record<FindingType, string> = {
  personal_account: 'people on personal accounts',
  leaver_key: "leavers' keys still active",
  leaver_seat: "leavers' seats still held",
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
  {
    type: 'personal_account',
    needs: 'the laptop script and an approved tool; or a seat list (Cursor, Copilot or ChatGPT Enterprise) with proxy logs or a laptop source; or proxy logs with a user column, Okta, and an approved tool marked "company accounts sign in through Okta"',
    on: (c) => (c.proxyLogs && c.okta && c.ssoTools > 0) || (c.seatLists.length > 0 && (c.proxyLogs || c.laptops > 0)) || (!!c.laptopScript && c.approvedTools > 0),
  },
  { type: 'leaver_key', needs: 'OpenAI Admin API or LiteLLM, and Okta or Entra ID with the people step on', on: (c) => c.people > 0 },
  { type: 'leaver_seat', needs: 'a seat list, and Okta or Entra ID with the people step on', on: (c) => c.seatLists.length > 0 && c.people > 0 },
  { type: 'gateway_bypass', needs: 'proxy logs and a LiteLLM gateway', on: (c) => c.proxyLogs && c.gateway },
  { type: 'not_allowed', needs: 'any sign-in, traffic or laptop source, and a tool marked not allowed', on: (c) => (c.proxyLogs || c.okta || c.entra || c.laptops > 0) && c.approvedTools > 0 },
  { type: 'self_consent', needs: 'Entra ID', on: (c) => c.entra },
  { type: 'unregistered_mcp', needs: 'an MCP registry, and GitHub or the laptop script', on: (c) => c.mcpRegistry && (!!c.sourceKinds?.includes('github') || !!c.laptopScript) },
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

      <ReadingCard subjectKey={f.key} onUseNudge={canNudge ? setMessage : undefined} />

      {f.person && <PersonTools person={f.person} />}

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
      await setToolStance(t.key, { status: status === 'not_reviewed' ? null : status, teams: status === 'limited' ? teamList : [], sso_required: sso, tenant_ids: t.stance?.tenantIds ?? [] })
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
                  <span className="nm" id={`sh-tool-${t.key}`}>{t.label}</span>
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
                  aria-describedby={`sh-tool-${t.key}`}
                  value={sso}
                  isDisabled={busy === t.key || status === 'not_reviewed' || status === 'not_allowed'}
                  onChange={(on: boolean) => void save(t, status, on)}
                />
              </div>
            )
          })}
        </div>
        <ProxyRules tools={tools} onSaved={async () => setTools(await listTools())} />
      </VStack>
    </section>
  )
}

/** Proxy rules that limit ChatGPT and Claude sign-in to the company's own workspaces. */
function ProxyRules({ tools, onSaved }: { tools: ToolStance[]; onSaved: () => Promise<void> }) {
  const [rules, setRules] = useState<TenantRules | null>(null)
  const [ids, setIds] = useState<Record<string, string>>({})
  const [error, setError] = useState<string | null>(null)
  const stamp = tools.map((t) => `${t.key}:${t.stance?.status ?? ''}:${(t.stance?.tenantIds ?? []).join(',')}`).join('|')
  useEffect(() => {
    getTenantRules()
      .then(setRules)
      .catch((e) => setError(e instanceof Error ? e.message : 'Could not load the proxy rules'))
  }, [stamp])
  const eligible = tools.filter((t) => (t.key === 'chatgpt' || t.key === 'claude') && (t.stance?.status === 'approved' || t.stance?.status === 'limited'))
  if (!eligible.length) return null
  async function save(t: ToolStance) {
    if (!t.stance) return
    setError(null)
    try {
      const list = (ids[t.key] ?? (t.stance.tenantIds ?? []).join(', ')).split(/[\s,]+/).map((x) => x.trim()).filter(Boolean)
      await setToolStance(t.key, { status: t.stance.status, teams: t.stance.teams, sso_required: t.stance.sso_required, tenant_ids: list })
      await onSaved()
    } catch (e) {
      setError(e instanceof Error ? e.message : 'Not saved')
    }
  }
  return (
    <section className="sh-proxy" aria-labelledby="proxy-title">
      <VStack gap={3}>
        <div>
          <Heading level={3} id="proxy-title">
            Allow only your company workspaces
          </Heading>
          <Text size="sm" color="secondary">
            ChatGPT and Claude each accept a header that limits sign-in to the workspaces you list. Add it at your web proxy and personal accounts cannot sign in. It works only on traffic the proxy inspects, so Shadow AI still watches laptops off the network.
          </Text>
        </div>
        {error && <Banner status="error" title="Not saved" description={error} />}
        {eligible.map((t) => (
          <HStack key={t.key} gap={2} vAlign="end" wrap="wrap">
            <TextInput
              label={`${t.label} workspace IDs`}
              description={rules?.missing.find((m) => m.service === t.key)?.where ?? 'Separate several with commas.'}
              value={ids[t.key] ?? (t.stance?.tenantIds ?? []).join(', ')}
              onChange={(v) => setIds((p) => ({ ...p, [t.key]: v }))}
            />
            <Button variant="secondary" label="Save" onClick={() => void save(t)} />
          </HStack>
        ))}
        {rules?.rules.map((r) => (
          <div key={r.service} className="sh-rule">
            <Text size="sm" weight="semibold">
              {r.label}: add on requests to {r.hosts.join(', ')}
            </Text>
            <code className="sh-code">
              {r.header}: {r.value}
            </code>
          </div>
        ))}
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
                  <span className="s">{on ? 'Running. ' : 'Not running: needs '}{on ? '' : c.needs}</span>
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
            <li>Company seat lists and when each seat was last used</li>
            <li>AI apps installed on company laptops; other apps are not stored</li>
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

function Refs({ cites, evidence }: { cites: number[]; evidence: Reading['evidence'] }) {
  return (
    <>
      {cites.map((n) => {
        const e = evidence.find((x) => x.id === n)
        return (
          <span key={n} className="sh-ref" title={e ? `${e.title}: ${e.detail}` : undefined} aria-label={e ? `Evidence ${n}: ${e.title}, ${e.detail}` : `Evidence ${n}`}>
            {n}
          </span>
        )
      })}
    </>
  )
}

/** FairMind's reading: written by the organisation's own model, kept until the evidence changes. */
function ReadingCard({ subjectKey, onUseNudge }: { subjectKey: string; onUseNudge?: (text: string) => void }) {
  const [state, setState] = useState<{ reading: Reading | null; modelConnected: boolean } | null>(null)
  const [busy, setBusy] = useState(false)
  const [error, setError] = useState<string | null>(null)
  useEffect(() => {
    let cancelled = false
    getReading(subjectKey)
      .then((r) => !cancelled && setState(r))
      .catch((e) => !cancelled && setError(e instanceof Error ? e.message : 'Could not load the reading'))
    return () => {
      cancelled = true
    }
  }, [subjectKey])
  async function write() {
    setBusy(true)
    setError(null)
    try {
      setState(await writeReading(subjectKey))
    } catch (e) {
      setError(e instanceof Error ? e.message : 'FairMind could not read it')
    } finally {
      setBusy(false)
    }
  }
  const r = state?.reading
  const cited = r ? [...new Set([...r.paragraphs.flatMap((p) => p.cites), ...(r.next_step?.cites ?? [])])].sort((a, b) => a - b) : []
  return (
    <section className="fm-card" aria-labelledby={`reading-${subjectKey}`}>
      <VStack gap={3}>
        <HStack hAlign="between" vAlign="center" wrap="wrap" gap={2}>
          <Heading level={3} id={`reading-${subjectKey}`}>
            FairMind&apos;s reading
          </Heading>
          {r && <span className="dv-chip">Written by your connected model</span>}
        </HStack>
        {error && <Banner status="error" title="Not read" description={error} />}
        {!state && !error ? (
          <Skeleton height={80} />
        ) : r ? (
          <>
            {r.stale && (
              <Banner
                status="warning"
                title="The evidence changed since this was written"
                endContent={<Button size="sm" variant="secondary" label={busy ? 'Reading' : 'Read again'} isDisabled={busy} onClick={() => void write()} />}
              />
            )}
            <div className="sh-reading">
              {r.paragraphs.map((p, i) => (
                <p key={i}>
                  {p.text} <Refs cites={p.cites} evidence={r.evidence} />
                </p>
              ))}
            </div>
            {r.next_step && (
              <div className="dv-miss">
                <span className="dot" aria-hidden="true" />
                <span>
                  <b>Suggested next step.</b> {r.next_step.text} <Refs cites={r.next_step.cites} evidence={r.evidence} />
                </span>
              </div>
            )}
            {r.nudge && onUseNudge && (
              <HStack>
                <Button size="sm" variant="secondary" label="Use the drafted message" onClick={() => onUseNudge(r.nudge)} />
              </HStack>
            )}
            <ol className="sh-cites">
              {r.evidence
                .filter((e) => cited.includes(e.id))
                .map((e) => (
                  <li key={e.id}>
                    <span className="sh-ref" aria-hidden="true">
                      {e.id}
                    </span>
                    <span>
                      {e.title}: {e.detail}
                    </span>
                  </li>
                ))}
            </ol>
            <Text size="sm" color="secondary">
              {r.model ? `${r.model}, ` : ''}written {ago(r.createdAt)}. It explains and cites the evidence; it does not set how serious a finding is or how sure FairMind is. Names, laptops and serial numbers are replaced before anything is sent to the model.
            </Text>
          </>
        ) : (
          <VStack gap={2}>
            <Text size="sm" color="secondary">
              {state?.modelConnected
                ? 'FairMind can explain this in plain words with your connected model, citing the evidence above. Names and laptops are replaced before anything is sent.'
                : "Connect your organisation's AI model to have FairMind explain findings in plain words."}
            </Text>
            <HStack>
              {state?.modelConnected ? (
                <Button variant="secondary" label={busy ? 'Reading' : 'Read it with FairMind'} isDisabled={busy} onClick={() => void write()} />
              ) : (
                <Button variant="secondary" label="Connect a model" href="/settings" />
              )}
            </HStack>
          </VStack>
        )}
      </VStack>
    </section>
  )
}

function StoryCards({ stories, showing, onShow }: { stories: Story[]; showing: string | null; onShow: (key: string | null) => void }) {
  const [open, setOpen] = useState<string | null>(null)
  if (!stories.length) return null
  return (
    <VStack gap={3}>
      {stories.map((s) => (
        <section key={s.key} className="fm-card sh-story" aria-label={s.title}>
          <VStack gap={2}>
            <Text size="sm" weight="semibold" color="secondary">
              {s.findingKeys.length} findings are one story
            </Text>
            <Heading level={3}>{s.title}</Heading>
            <Text size="sm">{s.summary}</Text>
            <HStack gap={2} wrap="wrap">
              <Button size="sm" variant={showing === s.key ? 'primary' : 'secondary'} label={showing === s.key ? 'Show all findings' : 'Show these findings'} onClick={() => onShow(showing === s.key ? null : s.key)} />
              <Button size="sm" variant="ghost" label={open === s.key ? 'Hide the reading' : "FairMind's reading"} onClick={() => setOpen(open === s.key ? null : s.key)} />
            </HStack>
            {open === s.key && <ReadingCard subjectKey={s.key} />}
          </VStack>
        </section>
      ))}
    </VStack>
  )
}

/** Which places the connected sources watch, as a bar of segments, one per Discovery area. */
function CoverageStrip({ kinds }: { kinds: string[] }) {
  const lanes = LANES.filter((l) => l.key !== 'code' && l.key !== 'cloud')
  const on = new Set(kinds.map((k) => SOURCES[k as IntegrationKind]?.lane).filter(Boolean))
  const seen = lanes.filter((l) => on.has(l.key))
  return (
    <div className="sh-strip">
      <Text size="sm" weight="semibold" color="secondary">
        Seeing with
      </Text>
      <span className="sh-seg" aria-hidden="true">
        {lanes.map((l) => (
          <i key={l.key} className={on.has(l.key) ? 'f' : undefined} />
        ))}
      </span>
      <Text size="sm">{seen.length ? seen.map((l) => l.label).join(', ') : 'No sources yet'}</Text>
      {seen.length < lanes.length && (
        <Text size="sm" color="secondary">
          Not yet: {lanes.filter((l) => !on.has(l.key)).map((l) => l.label).join(', ')}
        </Text>
      )}
      <span className="sh-strip-end">
        <Button size="sm" variant="ghost" label="Sources" href="/discovery/connect" />
      </span>
    </div>
  )
}

function cell(r: EvidenceRow, k: 'onLaptop' | 'traffic'): { cls: string; label: string } {
  const approved = r.stance === 'approved' || r.stance === 'limited'
  const v = r[k]
  if (!v) return { cls: 'none', label: 'Not seen' }
  const how =
    k === 'onLaptop' && r.onLaptop
      ? `${r.onLaptop.kinds.map((x) => (x === 'used' ? 'run' : x === 'extension' ? 'browser extension' : 'installed')).join(', ')}, seen by ${r.onLaptop.sources.join(', ')}`
      : r.traffic
        ? `${r.traffic.requests} connections, seen by ${r.traffic.sources.join(', ')}`
        : ''
  return { cls: approved ? 'co' : 'un', label: `${approved ? '' : 'Not approved: '}${how}` }
}

function seatCell(r: EvidenceRow): { cls: string; label: string } {
  if (!r.seat) return { cls: 'none', label: 'No seat list connected' }
  if (r.seat.status === 'held') return { cls: 'co', label: `Company seat, from ${r.seat.source}` }
  if (r.seat.status === 'unknown') return { cls: 'none', label: `${r.seat.source} shows too few emails to compare` }
  return r.onLaptop || r.traffic ? { cls: 'pe', label: `In use with no company seat, from ${r.seat.source}` } : { cls: 'none', label: `No company seat, from ${r.seat.source}` }
}

function signedInCell(r: EvidenceRow): { cls: string; label: string } {
  if (!r.signedIn) return { cls: 'none', label: 'Not reported' }
  return r.signedIn.class === 'work'
    ? { cls: 'co', label: `Company account, on ${r.signedIn.laptops.join(', ')}` }
    : { cls: 'pe', label: `Account outside your company domains, on ${r.signedIn.laptops.join(', ')}` }
}

/** Each AI tool against each kind of evidence, as squares. */
function EvidenceGrid({ ev }: { ev: Evidence }) {
  if (!ev.rows.length) return <Text color="secondary">No AI tools seen yet.</Text>
  return (
    <VStack gap={2}>
      <div className="sh-mapwrap">
        <table className="sh-map sh-grid">
          <thead>
            <tr>
              <th scope="col">Tool</th>
              <th scope="col">On the laptop</th>
              <th scope="col">Traffic</th>
              <th scope="col">Company seat</th>
              <th scope="col">Signed in</th>
              <th scope="col">Your stance</th>
            </tr>
          </thead>
          <tbody>
            {ev.rows.map((r) => {
              const cells = [cell(r, 'onLaptop'), cell(r, 'traffic'), seatCell(r), signedInCell(r)]
              return (
                <tr key={r.service}>
                  <th scope="row">
                    {r.label}
                    <span className="st">{r.vendor}</span>
                  </th>
                  {cells.map((c, i) => (
                    <td key={i}>
                      <span className={`sh-sq ${c.cls}`} title={c.label} role="img" aria-label={c.label} />
                      {i === 1 && r.traffic ? <span className="sh-n">{r.traffic.requests}</span> : null}
                    </td>
                  ))}
                  <td>
                    <span className={`st ${r.stance}`}>{STANCE_LABEL[r.stance]}</span>
                  </td>
                </tr>
              )
            })}
          </tbody>
        </table>
      </div>
      <div className="sh-legend">
        <span><span className="sh-sq co" />Seen, approved or company seat</span>
        <span><span className="sh-sq pe" />No company seat, or a personal account</span>
        <span><span className="sh-sq un" />Seen, not approved</span>
        <span><span className="sh-sq none" />Not seen</span>
      </div>
    </VStack>
  )
}

function PersonTools({ person }: { person: string }) {
  const { data, error } = useEvidence(person, null)
  return (
    <section className="fm-card" aria-labelledby="tools-title">
      <VStack gap={3}>
        <div>
          <Heading level={3} id="tools-title">
            Every AI tool for {person}
          </Heading>
          <Text size="sm" color="secondary">
            {data?.laptops.length ? `On ${data.laptops.map((l) => l.name).join(', ')}, merged from ${[...new Set(data.laptops.flatMap((l) => l.sources))].join(', ')}.` : 'From every connected source.'} Hover a square to see which sources said it.
          </Text>
        </div>
        {error ? <Text color="secondary">{error}</Text> : data ? <EvidenceGrid ev={data} /> : <Skeleton height={140} />}
      </VStack>
    </section>
  )
}

function saveFile(name: string, body: string) {
  const url = URL.createObjectURL(new Blob([body], { type: 'text/plain' }))
  const a = document.createElement('a')
  a.href = url
  a.download = name
  a.click()
  URL.revokeObjectURL(url)
}

/** The read-only laptop script: company domains, a one-time ingest token and the script per system. */
function LaptopScriptCard() {
  const [st, setSt] = useState<ScriptStatus | null>(null)
  const [domains, setDomains] = useState('')
  const [token, setToken] = useState<string | null>(null)
  const [busy, setBusy] = useState(false)
  const [error, setError] = useState<string | null>(null)
  useEffect(() => {
    getScriptStatus()
      .then((s) => {
        setSt(s)
        setDomains(s.domains.join(', '))
      })
      .catch((e) => setError(e instanceof Error ? e.message : 'Could not load the laptop script'))
  }, [])
  async function act(fn: () => Promise<void>) {
    setBusy(true)
    setError(null)
    try {
      await fn()
    } catch (e) {
      setError(e instanceof Error ? e.message : 'That did not work')
    } finally {
      setBusy(false)
    }
  }
  async function download(os: 'macos' | 'windows') {
    const d = await downloadScript(os)
    saveFile(d.filename, d.script)
  }
  if (!st) return error ? <Banner status="error" title="Laptop script" description={error} /> : null
  return (
    <section className="fm-card" aria-labelledby="script-title">
      <VStack gap={3}>
        <HStack hAlign="between" vAlign="start" wrap="wrap" gap={2}>
          <div>
            <Heading level={3} id="script-title">
              Laptop script
            </Heading>
            <Text size="sm" color="secondary">
              Read-only, once a day, pushed by your device management. It reports AI apps, editor extensions, MCP server names and whether each app is signed in with a work or personal account. The address never leaves the laptop.
            </Text>
          </div>
          {st.connected && <span className="dv-chip">{st.laptops ? `${st.laptops} ${st.laptops === 1 ? 'laptop' : 'laptops'} reporting, last ${ago(st.lastReportAt)}` : 'No laptop has reported yet'}</span>}
        </HStack>
        {error && <Banner status="error" title="Not saved" description={error} />}
        <HStack gap={2} vAlign="end" wrap="wrap">
          <TextInput label="Company email domains" description="An account on these domains counts as a work account." value={domains} onChange={setDomains} placeholder="acme.com, acme.in" />
          <Button variant="secondary" label="Save domains" isDisabled={busy || !domains.trim()} onClick={() => void act(async () => setSt(await setScriptDomains(domains)))} />
        </HStack>
        {st.connected && (
          <>
            {token && (
              <Banner
                status="success"
                title="Ingest token, shown once"
                description={`${token}  Jamf: put it in script parameter 4. Intune scripts take no parameters, so put it in the script itself. Any earlier token has stopped working.`}
                endContent={<Button size="sm" variant="secondary" label="Copy" onClick={() => void navigator.clipboard.writeText(token)} />}
              />
            )}
            <HStack gap={2} wrap="wrap">
              <Button variant="secondary" label={st.hasToken ? 'Create a new token' : 'Create the token'} isDisabled={busy} onClick={() => void act(async () => setToken((await newScriptToken()).token))} />
              <Button variant="ghost" label="Download for macOS" isDisabled={busy} onClick={() => void act(() => download('macos'))} />
              <Button variant="ghost" label="Download for Windows" isDisabled={busy} onClick={() => void act(() => download('windows'))} />
            </HStack>
          </>
        )}
      </VStack>
    </section>
  )
}

const RUNTIME: Record<EdgeModel['runtime'], string> = { ollama: 'Ollama', lm_studio: 'LM Studio', huggingface: 'Hugging Face cache' }

function size(n: number): string {
  return n >= 1e9 ? `${(n / 1e9).toFixed(1)} GB` : n >= 1e6 ? `${Math.round(n / 1e6)} MB` : 'Size not known'
}

function ModelsOnLaptop({ models }: { models: EdgeModel[] }) {
  if (!models.length) return null
  return (
    <section className="fm-card" aria-labelledby="models-title">
      <VStack gap={3}>
        <div>
          <Heading level={3} id="models-title">
            Edge AI models on this laptop
          </Heading>
          <Text size="sm" color="secondary">
            Models local runtimes downloaded, by name. They run without any vendor seeing the data, so review them like any other AI system.
          </Text>
        </div>
        <div className="sh-mapwrap">
          <table className="sh-map">
            <thead>
              <tr>
                <th scope="col">Model</th>
                <th scope="col">Runtime</th>
                <th scope="col">Size</th>
                <th scope="col">Seen by</th>
              </tr>
            </thead>
            <tbody>
              {models.map((m) => (
                <tr key={`${m.runtime}:${m.name}`}>
                  <th scope="row">{m.name}</th>
                  <td>{RUNTIME[m.runtime]}</td>
                  <td>{size(m.size)}</td>
                  <td>{m.source}</td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </VStack>
    </section>
  )
}

const RULE_LABEL: Record<AgentRule, string> = {
  personal_account: 'A personal account signs in to an approved tool',
  not_allowed_app: 'A tool you do not allow starts',
  unregistered_mcp: 'An MCP server not in your registry starts',
  model_added: 'A new local model is downloaded',
}
const ACTION_LABEL: Record<AgentAction, string> = { log: 'Log only', tell_you: 'Tell you', tell_person: 'Tell the person', tell_both: 'Tell you and the person' }
const ACTION_DONE: Record<AgentAction, string> = { log: 'Logged', tell_you: 'Told you', tell_person: 'For the person', tell_both: 'Told you, for the person' }

function eventText(e: AgentEvent): string {
  if (e.kind === 'account') return `Cursor signed in with a personal account on ${e.laptop}`
  if (e.kind === 'mcp_started') return `MCP server ${e.server} started on ${e.laptop}`
  if (e.kind === 'model_added') return `New local model ${e.name} on ${e.laptop}`
  return `${e.app ?? e.service} started on ${e.laptop}`
}

/** The FairMind agent: osquery reporting to FairMind. Setup, health and what it saw today. */
function AgentCard() {
  const [st, setSt] = useState<AgentStatus | null>(null)
  const [secret, setSecret] = useState<string | null>(null)
  const [notifier, setNotifier] = useState<{ secret: string; config: string } | null>(null)
  const [busy, setBusy] = useState(false)
  const [error, setError] = useState<string | null>(null)
  useEffect(() => {
    getAgent()
      .then(setSt)
      .catch((e) => setError(e instanceof Error ? e.message : 'Could not load the agent'))
  }, [])
  async function act(fn: () => Promise<void>) {
    setBusy(true)
    setError(null)
    try {
      await fn()
    } catch (e) {
      setError(e instanceof Error ? e.message : 'That did not work')
    } finally {
      setBusy(false)
    }
  }
  async function flags(os: 'macos' | 'windows') {
    const d = await agentSettings(os)
    saveFile(d.filename, d.flags)
  }
  if (!st) return error ? <Banner status="error" title="FairMind agent" description={error} /> : null
  return (
    <section className="fm-card" aria-labelledby="agent-title">
      <VStack gap={3}>
        <HStack hAlign="between" vAlign="start" wrap="wrap" gap={2}>
          <div>
            <Heading level={3} id="agent-title">
              FairMind agent
            </Heading>
            <Text size="sm" color="secondary">
              osquery&apos;s official package, reporting to FairMind. It sees AI apps start as it happens on macOS and every minute on Windows, and lists edge AI models. It never blocks and never reads content.
            </Text>
          </div>
          {st.connected && <span className="dv-chip">{st.laptops ? `${st.laptops} ${st.laptops === 1 ? 'laptop' : 'laptops'} enrolled` : 'No laptop enrolled yet'}</span>}
        </HStack>
        {error && <Banner status="error" title="Not done" description={error} />}
        {!st.connected ? (
          <HStack>
            <Button variant="secondary" label="Set up the agent" isDisabled={busy} onClick={() => void act(async () => setSt(await createAgent()))} />
          </HStack>
        ) : (
          <>
            {secret && (
              <Banner
                status="success"
                title="Enrol secret, shown once"
                description={`${secret}  Save it as fairmind.secret next to the flags file. Laptops already enrolled keep working when you create a new one.`}
                endContent={<Button size="sm" variant="secondary" label="Copy" onClick={() => void navigator.clipboard.writeText(secret)} />}
              />
            )}
            <Text size="sm" color="secondary">
              Install osquery with your device management, put the flags file in osquery&apos;s folder and the secret beside it. On macOS, grant osqueryd Full Disk Access with a privacy profile, or it checks every minute instead of as it happens.
            </Text>
            <HStack gap={2} wrap="wrap">
              <Button variant="secondary" label={st.hasSecret ? 'Create a new enrol secret' : 'Create the enrol secret'} isDisabled={busy} onClick={() => void act(async () => setSecret((await newAgentSecret()).secret))} />
              <Button variant="ghost" label="osquery settings for macOS" isDisabled={busy} onClick={() => void act(() => flags('macos'))} />
              <Button variant="ghost" label="osquery settings for Windows" isDisabled={busy} onClick={() => void act(() => flags('windows'))} />
            </HStack>
            {(st.quiet.length > 0 || st.problems.length > 0) && (
              <VStack gap={1}>
                <Text size="sm" weight="semibold">
                  Needs attention
                </Text>
                {st.problems.map((p, i) => (
                  <Text key={`p${i}`} size="sm" color="secondary">
                    {p.name}: {p.problem}
                  </Text>
                ))}
                {st.quiet.map((q, i) => (
                  <Text key={`q${i}`} size="sm" color="secondary">
                    {q.name} has not checked in since {ago(q.lastSeen)}
                  </Text>
                ))}
              </VStack>
            )}
            <VStack gap={2}>
              <Text size="sm" weight="semibold">
                What the agent does
              </Text>
              {(Object.keys(RULE_LABEL) as AgentRule[]).map((r) => (
                <HStack key={r} hAlign="between" vAlign="center" wrap="wrap" gap={2}>
                  <Text size="sm">{RULE_LABEL[r]}</Text>
                  <Selector
                    label={`What the agent does when ${RULE_LABEL[r].toLowerCase()}`}
                    isLabelHidden
                    size="sm"
                    value={st.rules[r]}
                    options={(Object.keys(ACTION_LABEL) as AgentAction[]).map((a) => ({ value: a, label: ACTION_LABEL[a] }))}
                    onChange={(v: string) => void act(async () => setSt(await setAgentRules({ [r]: v as AgentAction })))}
                  />
                </HStack>
              ))}
              <Text size="sm" color="secondary">
                {st.domains.length
                  ? `The account check compares with your company domains (${st.domains.join(', ')}), on the laptop.`
                  : 'Set your company domains in the laptop script card to turn on the account check.'}{' '}
                Messages to the person are shown by the FairMind notifier where it is installed. The agent never blocks.
              </Text>
            </VStack>
            <VStack gap={2}>
              <HStack hAlign="between" vAlign="center" wrap="wrap" gap={2}>
                <Text size="sm" weight="semibold">
                  FairMind notifier
                </Text>
                <span className="dv-chip">{st.notifiers ? `On ${st.notifiers} ${st.notifiers === 1 ? 'laptop' : 'laptops'}` : 'Not installed yet'}</span>
              </HStack>
              <Text size="sm" color="secondary">
                A small app in the person&apos;s session that shows these messages and, on request, what the agent checks and every message it showed. Install it with its settings file from your device management. Release builds will be signed; until then it is for testing.
              </Text>
              {notifier && (
                <Banner
                  status="success"
                  title="Notifier settings, shown once"
                  description="Download notifier.json now and install it with the notifier. Any earlier notifier secret has stopped working for new laptops."
                  endContent={<Button size="sm" variant="secondary" label="Download notifier.json" onClick={() => saveFile('notifier.json', notifier.config)} />}
                />
              )}
              <HStack>
                <Button variant="secondary" label={st.hasNotifierSecret ? 'Create new notifier settings' : 'Create notifier settings'} isDisabled={busy} onClick={() => void act(async () => setNotifier(await newNotifierSecret()))} />
              </HStack>
            </VStack>
            {st.events.length > 0 && (
              <VStack gap={1}>
                <Text size="sm" weight="semibold">
                  As it happens
                </Text>
                <ol className="sh-cites">
                  {st.events.slice(0, 10).map((e, i) => (
                    <li key={i}>
                      <span className="sh-ref" aria-hidden="true">
                        {(e.app ?? e.server ?? e.name ?? e.service ?? '?').replace(/^@/, '').slice(0, 2).toUpperCase()}
                      </span>
                      <span>
                        {eventText(e)}
                        {e.user ? ` (${e.user})` : ''}, {ago(e.at)}
                        {e.action && e.action !== 'log' ? ` · ${ACTION_DONE[e.action]}` : ''}
                        {e.shownAt ? ` · shown to the person ${ago(e.shownAt)}` : ''}
                      </span>
                    </li>
                  ))}
                </ol>
              </VStack>
            )}
          </>
        )}
      </VStack>
    </section>
  )
}

function LaptopsTab({ picked, onPick }: { picked: string | null; onPick: (id: string) => void }) {
  const [q, setQ] = useState('')
  const { data, error } = useLaptops(q)
  const selected = data?.laptops.find((l) => l.id === picked) ?? data?.laptops[0] ?? null
  const ev = useEvidence(null, selected?.id ?? null)
  if (error) return <EmptyState title="Laptops could not load" description={error} />
  if (!data) return <Skeleton height={360} />
  if (!data.total && !q)
    return (
      <VStack gap={4}>
        <LaptopScriptCard />
        <AgentCard />
        <EmptyState
          title="No laptops yet"
          description="Run the laptop script, or connect Jamf, Intune, Defender for Endpoint, CrowdStrike, Fleet or Chrome Enterprise, to see which AI tools are on each laptop."
          actions={<Button label="Connect a source" href="/discovery/connect" />}
        />
      </VStack>
    )
  return (
    <VStack gap={4}>
      <LaptopScriptCard />
      <AgentCard />
      <div className="dv-split">
      <section className="fm-card dv-wlist" aria-label="Laptops">
        <div className="dv-wlist-hd">
          <div style={{ flex: 1 }}>
            <TextInput label="Find a laptop, serial or person" isLabelHidden placeholder="Find a laptop, serial or person" size="sm" value={q} onChange={setQ} />
          </div>
        </div>
        {data.laptops.map((l) => (
          <button key={l.id} type="button" className={`dv-witem${selected?.id === l.id ? ' on' : ''}`} aria-current={selected?.id === l.id} onClick={() => onPick(l.id)}>
            <span style={{ minWidth: 0 }}>
              <span className="nm">{l.name}</span>
              <span className="k">
                {[l.people[0], l.team !== 'No team' ? l.team : null, `${l.tools.length} AI ${l.tools.length === 1 ? 'tool' : 'tools'}`, l.models ? `${l.models} ${l.models === 1 ? 'model' : 'models'}` : null].filter(Boolean).join(' · ')}
              </span>
            </span>
            {l.flagged > 0 ? <span className="dv-chip sev-high">{l.flagged} not approved</span> : <span />}
            <span />
            <span />
          </button>
        ))}
        {data.total > data.laptops.length && (
          <div className="dv-wlist-hd">
            <Text size="sm" color="secondary">
              Showing {data.laptops.length} of {data.total}. Search to narrow.
            </Text>
          </div>
        )}
      </section>
      {selected && (
        <VStack gap={4}>
          <section className="fm-card">
            <VStack gap={2}>
              <Heading level={2}>{selected.name}</Heading>
              <Text size="sm" color="secondary">
                {[selected.serial ? `Serial ${selected.serial}` : null, selected.people.join(', ') || 'No person on record', `seen by ${selected.sources.join(', ')}`].filter(Boolean).join(' · ')}
              </Text>
            </VStack>
          </section>
          <section className="fm-card" aria-label="Every AI tool on this laptop">
            <VStack gap={3}>
              <Heading level={3}>Every AI tool on this laptop</Heading>
              {ev.error ? <Text color="secondary">{ev.error}</Text> : ev.data ? <EvidenceGrid ev={ev.data} /> : <Skeleton height={140} />}
            </VStack>
          </section>
          {ev.data?.models && <ModelsOnLaptop models={ev.data.models} />}
        </VStack>
      )}
      </div>
    </VStack>
  )
}

function ShadowView() {
  const router = useRouter()
  const params = useSearchParams()
  const v = params.get('view')
  const view = v === 'expected' || v === 'resolved' || v === 'tools' || v === 'reads' || v === 'laptops' ? v : 'open'
  const { data, loading, error, refresh } = useShadowAI()
  const [type, setType] = useState<FindingType | null>(null)
  const [story, setStory] = useState<string | null>(null)
  const open = useMemo(() => (data?.findings ?? []).filter((f) => f.status === 'open'), [data])
  const expected = useMemo(() => (data?.findings ?? []).filter((f) => f.status === 'expected'), [data])
  const storyKeys = view === 'open' ? data?.stories?.find((s) => s.key === story)?.findingKeys : undefined
  const list = (view === 'expected' ? expected : open).filter((f) => (!type || f.type === type) && (!storyKeys || storyKeys.includes(f.key)))
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
        {data && <CoverageStrip kinds={data.coverage.sourceKinds ?? []} />}
        <TabList value={view} onChange={(t) => go(t)} hasDivider aria-label="Shadow AI view">
          <Tab value="open" label={`Open${open.length ? ` ${open.length}` : ''}`} />
          <Tab value="expected" label={`Expected${expected.length ? ` ${expected.length}` : ''}`} />
          <Tab value="laptops" label={`Laptops${data?.coverage.laptops ? ` ${data.coverage.laptops}` : ''}`} />
          <Tab value="resolved" label="Resolved" />
          <Tab value="tools" label="Approved tools" />
          <Tab value="reads" label={`What it reads${off ? ` · ${off} off` : ''}`} />
        </TabList>
        {loading ? (
          <Skeleton height={360} />
        ) : error || !data ? (
          <EmptyState title="Shadow AI could not load" description={error ?? ''} actions={<Button label="Try again" onClick={() => void refresh()} />} />
        ) : view === 'laptops' ? (
          <LaptopsTab picked={picked} onPick={(id) => go('laptops', id)} />
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
            {view === 'open' && <StoryCards stories={data.stories ?? []} showing={story} onShow={setStory} />}
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
