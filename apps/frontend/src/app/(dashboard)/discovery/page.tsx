'use client'

import '@/astryx/pages/systems.css'
import { useRouter } from 'next/navigation'
import { useRef, useState, type FormEvent } from 'react'
import { Banner } from '@astryxdesign/core/Banner'
import { Button } from '@astryxdesign/core/Button'
import { Drawer } from '@astryxdesign/core/Drawer'
import { EmptyState } from '@astryxdesign/core/EmptyState'
import { Heading, Text } from '@astryxdesign/core/Text'
import { HStack, VStack } from '@astryxdesign/core/Layout'
import { Skeleton } from '@astryxdesign/core/Skeleton'
import { Selector } from '@astryxdesign/core/Selector'
import { TextInput } from '@astryxdesign/core/TextInput'
import { Token } from '@astryxdesign/core/Token'
import { useSystemContext } from '@/components/workflow/SystemContext'
import { KIND_LABEL, MAX_LOG_BYTES, SOURCE_LABEL, SOURCES, useDiscovery, when, type DiscoveredAsset, type Integration, type IntegrationKind } from '@/astryx/data/discovery'

const KINDS = Object.keys(SOURCES) as IntegrationKind[]

type Sync = NonNullable<Integration['lastSync']>
function syncLine(s: Sync | null | undefined, kind: IntegrationKind): string {
  if (!s) return kind === 'proxy_logs' ? 'No logs uploaded yet' : 'Not synced yet'
  if (s.error) return `Last sync failed: ${s.error}`
  return `${kind === 'proxy_logs' ? 'Read' : 'Synced'} ${when(s.at)} · ${s.found ?? 0} found, ${s.created ?? 0} new, ${s.updated ?? 0} updated`
}

/** What a connector reads, from its stored config. */
function where(i: Integration): string {
  const c = i.config as Record<string, string | undefined>
  switch (i.kind) {
    case 'mlflow':
      return c.tracking_uri ?? ''
    case 'github':
      return `github.com/${c.owner ?? ''}`
    case 'huggingface':
      return `huggingface.co/${c.owner ?? ''}`
    case 'aws':
      return `AWS ${c.regions || 'us-east-1'}`
    case 'azure':
      return `Azure subscriptions ${c.subscription_ids ?? ''}`
    case 'gcp':
      return `Google Cloud ${c.project_id ?? ''} · ${c.locations || 'us-central1'}`
    case 'okta':
      return c.domain ?? ''
    case 'litellm':
      return c.base_url ?? ''
    case 'mcp_registry':
      return c.registry_url ?? ''
    case 'proxy_logs':
      return 'Uploaded log exports; the files are not kept'
    default:
      return `${SOURCES[i.kind]?.label ?? i.kind} organisation`
  }
}

const num = (v: unknown) => (typeof v === 'number' ? v.toLocaleString('en-GB') : null)
const list = (v: unknown) => (Array.isArray(v) && v.length ? v.slice(0, 4).join(', ') : null)

/** What the scan saw in an item, from its stored metadata. */
function detail(a: DiscoveredAsset): string {
  const m = a.metadata
  if (a.source === 'huggingface') {
    return [m.pipeline_tag, m.library, m.license && `licence ${m.license}`, typeof m.downloads === 'number' && `${m.downloads.toLocaleString('en-GB')} downloads`].filter(Boolean).join(' · ')
  }
  if (a.source === 'mlflow') {
    const n = (m.versions?.length ?? 0) as number
    return `${n} version${n === 1 ? '' : 's'}${m.description ? ` · ${m.description}` : ''}`
  }
  if (a.source === 'github' && a.kind !== 'mcp_server') {
    const sig = m.signals as { llm_sdks?: string[]; ml_libraries?: string[]; agent_configs?: string[]; model_files?: string[]; mcp_servers?: string[] } | undefined
    return [...(sig?.llm_sdks ?? []), ...(sig?.ml_libraries ?? []), ...(sig?.agent_configs ?? []), ...(sig?.model_files ?? []), ...(sig?.mcp_servers ?? []).map((n) => `MCP ${n}`)].slice(0, 6).join(' · ')
  }
  // Newer sources: show the facts that are present, most telling first.
  const parts = [
    m.service && m.service !== a.name ? m.service : m.vendor,
    m.model && `model ${m.model}`,
    list(m.models_last_30_days) && `models ${list(m.models_last_30_days)}`,
    num(m.requests_last_30_days) && `${num(m.requests_last_30_days)} requests in 30 days`,
    num(m.tokens_last_30_days) && `${num(m.tokens_last_30_days)} tokens in 30 days`,
    num(m.requests) && `${num(m.requests)} requests in the log`,
    num(m.distinct_users) && `${num(m.distinct_users)} people`,
    num(m.distinct_users_30_days) && `${num(m.distinct_users_30_days)} people signed in`,
    m.self_consent_only && `${m.users_who_consented} people consented without an admin`,
    num(m.active_users_90_days) && `${num(m.active_users_90_days)} active people in 90 days`,
    num(m.users) && `${num(m.users)} people`,
    m.transport && `${m.transport}${m.url ? ` ${m.url}` : m.command ? ` ${m.command}` : ''}`,
    m.repo && a.kind === 'mcp_server' && `in ${m.repo}`,
    m.project && `project ${m.project}`,
    m.workspace && `workspace ${m.workspace}`,
    m.region,
    m.status,
  ]
  return parts.filter(Boolean).slice(0, 5).join(' · ')
}

function AddConnector({ onCreate, onDone }: { onCreate: ReturnType<typeof useDiscovery>['create']; onDone: () => void }) {
  const [kind, setKind] = useState<IntegrationKind>('github')
  const [v, setV] = useState<Record<string, string>>({})
  const [busy, setBusy] = useState(false)
  const [err, setErr] = useState<string | null>(null)
  const set = (k: string) => (value: string) => setV((p) => ({ ...p, [k]: value }))
  const f = (k: string) => (v[k] ?? '').trim()
  const spec = SOURCES[kind]
  const ready = Boolean(f('name')) && spec.fields.every((x) => x.optional || f(x.key)) && (!spec.token || spec.tokenOptional || Boolean(f('token')))

  async function submit(e: FormEvent) {
    e.preventDefault()
    setBusy(true)
    setErr(null)
    try {
      await onCreate({
        kind,
        name: f('name'),
        config: Object.fromEntries(spec.fields.map((x) => [x.key, f(x.key)])),
        token: f('token') || undefined,
      })
      setV({})
      onDone()
    } catch (x) {
      setErr(x instanceof Error ? x.message : 'Could not add the connector')
    } finally {
      setBusy(false)
    }
  }

  return (
    <form onSubmit={submit} className="dsc-form">
      <Selector
        label="Source"
        value={kind}
        onChange={(k: string) => setKind(k as IntegrationKind)}
        options={KINDS.map((k) => ({ value: k, label: `${SOURCES[k].group} · ${SOURCES[k].label}` }))}
      />
      <Text color="secondary">{spec.reads}</Text>
      <TextInput label="Name" value={v.name ?? ''} onChange={set('name')} isRequired />
      {spec.fields.map((x) => (
        <TextInput key={`${kind}-${x.key}`} label={x.label} description={x.description} value={v[x.key] ?? ''} onChange={set(x.key)} isRequired={!x.optional} isOptional={x.optional} />
      ))}
      {spec.token && (
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
      )}
      {err && <Banner status="error" title="That did not work" description={err} />}
      <HStack>
        <Button variant="primary" label={busy ? 'Adding' : 'Add connector'} isDisabled={busy || !ready} onClick={() => void submit({ preventDefault() {} } as FormEvent)} />
      </HStack>
    </form>
  )
}

const GROUPS = [
  { key: 'new', title: 'Found, not registered' },
  { key: 'promoted', title: 'Registered' },
  { key: 'ignored', title: 'Ignored' },
] as const

export default function DiscoveryPage() {
  const router = useRouter()
  const { refreshSystems } = useSystemContext()
  const d = useDiscovery()
  const [adding, setAdding] = useState(false)
  const [busyId, setBusyId] = useState<string | null>(null)
  const [error, setError] = useState<string | null>(null)
  const [synced, setSynced] = useState<Record<string, Sync | null>>({})
  const fileInput = useRef<HTMLInputElement>(null)
  const uploadFor = useRef<string | null>(null)

  function readLogs(file: File | undefined) {
    const id = uploadFor.current
    if (fileInput.current) fileInput.current.value = ''
    if (!file || !id) return
    if (file.size > MAX_LOG_BYTES) {
      setError('That log file is over 20 MB. Export a shorter period or only the destination host column.')
      return
    }
    void run(id, async () => {
      const r = await d.upload(id, await file.text())
      setSynced((p) => ({ ...p, [id]: r }))
    })
  }

  async function run(id: string, fn: () => Promise<void>) {
    setBusyId(id)
    setError(null)
    try {
      await fn()
    } catch (e) {
      setError(e instanceof Error ? e.message : 'Something went wrong')
    } finally {
      setBusyId(null)
    }
  }

  return (
    <div className="fm-page">
      <VStack gap={5}>
        <HStack gap={4} hAlign="between" vAlign="end" wrap="wrap">
          <VStack gap={1}>
            <Heading level={1}>Discovery</Heading>
            <Text color="secondary">
              {d.loading
                ? 'Reading connectors'
                : `${d.integrations.length} connector${d.integrations.length === 1 ? '' : 's'}, ${d.discovered.filter((a) => a.status === 'new').length} found and not registered`}
            </Text>
          </VStack>
          <HStack gap={2}>
            <Button label="See AI systems" variant="secondary" href="/systems" />
            <Button label="Connect a source" variant="primary" onClick={() => setAdding(true)} />
          </HStack>
        </HStack>

        {error && <Banner status="error" title="That did not work" description={error} isDismissable onDismiss={() => setError(null)} />}

        {d.loading ? (
          <VStack gap={2} aria-busy="true">
            {[0, 1, 2].map((i) => (
              <Skeleton key={i} height={72} />
            ))}
          </VStack>
        ) : d.error ? (
          <EmptyState title="Discovery could not load" description={d.error} actions={<Button label="Try again" onClick={() => void d.refresh()} />} />
        ) : (
          <>
            <section className="fm-card" aria-labelledby="conn-title">
              <div className="dsc-card">
                <Heading level={2} id="conn-title">
                  Connectors
                </Heading>
                {d.integrations.length === 0 ? (
                  <EmptyState title="No sources connected" description="Connect code, model registries, AI vendor accounts, clouds, sign-in providers or gateways, and FairMind reads the AI systems in them." actions={<Button variant="primary" label="Connect a source" onClick={() => setAdding(true)} />} />
                ) : (
                  d.integrations.map((i) => (
                    <div key={i.id} className="dsc-row">
                      <div>
                        <div className="nm">
                          {i.name} <Token size="sm" label={SOURCE_LABEL[i.kind] ?? i.kind} />
                        </div>
                        <div className="sub">{where(i)}</div>
                      </div>
                      <div className="sub">{syncLine(i.id in synced ? synced[i.id] : i.lastSync, i.kind)}</div>
                      <HStack gap={2}>
                        {i.kind === 'proxy_logs' ? (
                          <Button
                            size="sm"
                            variant="secondary"
                            label={busyId === i.id ? 'Reading' : 'Upload logs'}
                            isDisabled={busyId !== null}
                            onClick={() => {
                              uploadFor.current = i.id
                              fileInput.current?.click()
                            }}
                          />
                        ) : (
                          <Button
                            size="sm"
                            variant="secondary"
                            label={busyId === i.id ? 'Syncing' : 'Sync now'}
                            isDisabled={busyId !== null}
                            onClick={() =>
                              run(i.id, async () => {
                                const r = await d.sync(i.id)
                                setSynced((p) => ({ ...p, [i.id]: r }))
                              })
                            }
                          />
                        )}
                        <Button size="sm" variant="ghost" label="Remove" isDisabled={busyId !== null} onClick={() => run(i.id, () => d.remove(i.id))} />
                      </HStack>
                    </div>
                  ))
                )}
              </div>
            </section>

            {GROUPS.map((g) => {
              const rows = d.discovered.filter((a) => a.status === g.key)
              if (rows.length === 0 && g.key !== 'new') return null
              return (
                <section key={g.key} className="fm-card" aria-labelledby={`g-${g.key}`}>
                  <div className="dsc-card">
                    <Heading level={2} id={`g-${g.key}`}>
                      {g.title} ({rows.length})
                    </Heading>
                    {rows.length === 0 && <Text color="secondary">Nothing found and waiting. Sync a connector to look again.</Text>}
                    {rows.map((a) => (
                      <div key={a.id} className="dsc-row">
                        <div>
                          <div className="nm">
                            {a.name} <Token size="sm" label={KIND_LABEL[a.kind] ?? a.kind} />
                          </div>
                          <div className="sub">
                            {SOURCE_LABEL[a.source] ?? a.source} · {a.externalId}
                          </div>
                        </div>
                        <div className="sub">
                          {detail(a)}
                          {g.key === 'new' && ` · suggested ${a.suggestedTier} risk, ${a.suggestedStage} stage`}
                        </div>
                        <HStack gap={2}>
                          {g.key === 'new' && (
                            <>
                              <Button
                                size="sm"
                                variant="primary"
                                label="Register it"
                                isDisabled={busyId !== null}
                                onClick={() =>
                                  run(a.id, async () => {
                                    const out = await d.promote(a.id)
                                    await refreshSystems()
                                    router.push(`/systems/${encodeURIComponent(out.systemId)}`)
                                  })
                                }
                              />
                              <Button size="sm" variant="ghost" label="Ignore" isDisabled={busyId !== null} onClick={() => run(a.id, () => d.ignore(a.id))} />
                            </>
                          )}
                          {g.key === 'promoted' && a.systemId && <Button size="sm" variant="secondary" label="Open system" href={`/systems/${encodeURIComponent(a.systemId)}`} />}
                        </HStack>
                      </div>
                    ))}
                  </div>
                </section>
              )
            })}
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
      <Drawer isOpen={adding} onOpenChange={setAdding} label="Connect a source" width={480} padding={5}>
        <VStack gap={4}>
          <Heading level={2}>Connect a source</Heading>
          <AddConnector onCreate={d.create} onDone={() => setAdding(false)} />
        </VStack>
      </Drawer>
    </div>
  )
}
