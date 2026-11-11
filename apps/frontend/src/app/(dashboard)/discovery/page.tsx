'use client'

import '@/astryx/pages/systems.css'
import { useRouter } from 'next/navigation'
import { useState, type FormEvent } from 'react'
import { Banner } from '@astryxdesign/core/Banner'
import { Button } from '@astryxdesign/core/Button'
import { Drawer } from '@astryxdesign/core/Drawer'
import { EmptyState } from '@astryxdesign/core/EmptyState'
import { Heading, Text } from '@astryxdesign/core/Text'
import { HStack, VStack } from '@astryxdesign/core/Layout'
import { Skeleton } from '@astryxdesign/core/Skeleton'
import { TextInput } from '@astryxdesign/core/TextInput'
import { Token } from '@astryxdesign/core/Token'
import { useSystemContext } from '@/components/workflow/SystemContext'
import { KIND_LABEL, SOURCE_LABEL, useDiscovery, when, type DiscoveredAsset, type Integration, type IntegrationKind } from '@/astryx/data/discovery'

const KINDS: IntegrationKind[] = ['mlflow', 'github', 'huggingface']

type Sync = NonNullable<Integration['lastSync']>
function syncLine(s: Sync | null | undefined): string {
  if (!s) return 'Not synced yet'
  if (s.error) return `Last sync failed: ${s.error}`
  return `Synced ${when(s.at)} · ${s.found ?? 0} found, ${s.created ?? 0} new, ${s.updated ?? 0} updated`
}

/** What a connector reads, from its stored config. */
function where(i: Integration): string {
  const c = i.config
  if (i.kind === 'mlflow') return String(c.tracking_uri ?? '')
  return `${i.kind === 'github' ? 'github.com' : 'huggingface.co'}/${String(c.owner ?? '')}`
}

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
  const sig = m.signals as { llm_sdks?: string[]; ml_libraries?: string[]; agent_configs?: string[]; model_files?: string[] } | undefined
  return [...(sig?.llm_sdks ?? []), ...(sig?.ml_libraries ?? []), ...(sig?.agent_configs ?? []), ...(sig?.model_files ?? [])].slice(0, 6).join(' · ')
}

function AddConnector({ onCreate, onDone }: { onCreate: ReturnType<typeof useDiscovery>['create']; onDone: () => void }) {
  const [kind, setKind] = useState<IntegrationKind>('mlflow')
  const [v, setV] = useState<Record<string, string>>({})
  const [busy, setBusy] = useState(false)
  const [err, setErr] = useState<string | null>(null)
  const set = (k: string) => (value: string) => setV((p) => ({ ...p, [k]: value }))
  const f = (k: string) => (v[k] ?? '').trim()

  async function submit(e: FormEvent) {
    e.preventDefault()
    setBusy(true)
    setErr(null)
    try {
      await onCreate({
        kind,
        name: f('name'),
        config:
          kind === 'mlflow'
            ? { tracking_uri: f('tracking_uri') }
            : kind === 'github'
              ? { owner: f('owner'), repos: f('repos') }
              : { owner: f('owner'), name_contains: f('name_contains'), pipeline_tag: f('pipeline_tag'), library: f('library') },
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
      <div className="dsc-kinds" role="group" aria-label="Source">
        {KINDS.map((k) => (
          <Button key={k} size="sm" variant={kind === k ? 'primary' : 'secondary'} label={SOURCE_LABEL[k]} onClick={() => setKind(k)} />
        ))}
      </div>
      <TextInput label="Name" value={v.name ?? ''} onChange={set('name')} isRequired />
      {kind === 'mlflow' && <TextInput label="Tracking server address" value={v.tracking_uri ?? ''} onChange={set('tracking_uri')} isRequired />}
      {kind !== 'mlflow' && <TextInput label={kind === 'github' ? 'Organisation or user' : 'Organisation or user on Hugging Face'} value={v.owner ?? ''} onChange={set('owner')} isRequired />}
      {kind === 'github' && <TextInput label="Repositories" description="Names separated by commas; blank reads them all." value={v.repos ?? ''} onChange={set('repos')} isOptional />}
      {kind === 'huggingface' && (
        <>
          <TextInput label="Name contains" value={v.name_contains ?? ''} onChange={set('name_contains')} isOptional />
          <TextInput label="Pipeline tag" value={v.pipeline_tag ?? ''} onChange={set('pipeline_tag')} isOptional />
          <TextInput label="Library" value={v.library ?? ''} onChange={set('library')} isOptional />
        </>
      )}
      <TextInput label="Access token" description="Not needed for public sources. Stored on the server and never shown again." type="password" value={v.token ?? ''} onChange={set('token')} isOptional autoComplete="off" />
      {err && <Banner status="error" title="That did not work" description={err} />}
      <HStack>
        <Button variant="primary" label={busy ? 'Adding' : 'Add connector'} isDisabled={busy || !f('name')} onClick={() => void submit({ preventDefault() {} } as FormEvent)} />
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
                  <EmptyState title="No sources connected" description="Connect MLflow, GitHub or Hugging Face and FairMind reads the AI systems in them." actions={<Button variant="primary" label="Connect a source" onClick={() => setAdding(true)} />} />
                ) : (
                  d.integrations.map((i) => (
                    <div key={i.id} className="dsc-row">
                      <div>
                        <div className="nm">
                          {i.name} <Token size="sm" label={SOURCE_LABEL[i.kind] ?? i.kind} />
                        </div>
                        <div className="sub">{where(i)}</div>
                      </div>
                      <div className="sub">{syncLine(i.id in synced ? synced[i.id] : i.lastSync)}</div>
                      <HStack gap={2}>
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

      <Drawer isOpen={adding} onOpenChange={setAdding} label="Connect a source" width={480} padding={5}>
        <VStack gap={4}>
          <Heading level={2}>Connect a source</Heading>
          <AddConnector onCreate={d.create} onDone={() => setAdding(false)} />
        </VStack>
      </Drawer>
    </div>
  )
}
