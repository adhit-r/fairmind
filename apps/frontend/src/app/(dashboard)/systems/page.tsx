'use client'

import '@/astryx/pages/systems.css'
import { Suspense, useMemo, useState } from 'react'
import { useRouter, useSearchParams } from 'next/navigation'
import { Bot, Box, Check, MessageSquare, Search, X } from 'lucide-react'
import { Banner } from '@astryxdesign/core/Banner'
import { Button } from '@astryxdesign/core/Button'
import { Drawer } from '@astryxdesign/core/Drawer'
import { EmptyState } from '@astryxdesign/core/EmptyState'
import { Heading, Text } from '@astryxdesign/core/Text'
import { HStack, VStack } from '@astryxdesign/core/Layout'
import { MetadataList, MetadataListItem } from '@astryxdesign/core/MetadataList'
import { Skeleton } from '@astryxdesign/core/Skeleton'
import { TextInput } from '@astryxdesign/core/TextInput'
import { Token } from '@astryxdesign/core/Token'
import { useSystemContext, type AISystemSummary } from '@/components/workflow/SystemContext'
import { useEstateGates, type EstateGate } from '@/lib/api/hooks/useEstate'
import { useIntegrations, type DiscoveredAsset } from '@/lib/api/hooks/useIntegrations'
import { checkCell } from '@/components/ui/matrix'
import { KIND_LABEL, SOURCE_LABEL } from '@/astryx/data/discovery'

const HAND = 'hand'
const SHOW = 4
const COLUMNS = [
  { key: 'found', title: 'Found, not registered' },
  { key: 'registered', title: 'Registered, being checked' },
  { key: 'approved', title: 'Approved and watched' },
] as const
type Column = (typeof COLUMNS)[number]['key']

const KIND_ICON: Record<string, typeof Bot> = { ml_model: Box, llm_app: MessageSquare, ai_assisted_dev: Bot }

/** The one mini state for a registered system: fails or out of date need attention, approved is proven. */
function miniState(gate: EstateGate | undefined): { cls: string; word: string } {
  if (!gate) return { cls: 'open', word: 'No gate result yet' }
  const states = gate.checks.map((c) => checkCell(c))
  if (states.includes('fails')) return { cls: 'fails', word: 'A check fails' }
  if (states.includes('stale')) return { cls: 'needs', word: 'A check is out of date' }
  if (gate.approvalStatus === 'approved') return { cls: 'proven', word: 'Approved' }
  if (gate.approvalStatus === 'pending') return { cls: 'needs', word: 'Waiting for a reviewer' }
  return gate.verdict === 'go' ? { cls: 'estimated', word: 'Ready for a decision' } : { cls: 'open', word: 'Checks still open' }
}

function Mini({ cls, word }: { cls: string; word: string }) {
  return (
    <i className={`cell mini ${cls}`} role="img" aria-label={word} title={word}>
      {cls === 'proven' && <Check size={13} strokeWidth={2.6} aria-hidden />}
      {cls === 'fails' && <X size={13} strokeWidth={2.6} aria-hidden />}
      {cls === 'needs' && <b />}
    </i>
  )
}

type Item =
  | { type: 'found'; id: string; name: string; source: string; kind?: string; asset: DiscoveredAsset }
  | { type: 'system'; id: string; name: string; source: string; kind?: string; system: AISystemSummary; gate?: EstateGate }

function Lanes() {
  const router = useRouter()
  const params = useSearchParams()
  const stage = params.get('stage')
  const { systems, loading: sysLoading, error: sysError, refreshSystems } = useSystemContext()
  const gates = useEstateGates()
  const integ = useIntegrations()
  const [query, setQuery] = useState('')
  const [openKey, setOpenKey] = useState<string | null>(null)
  const [more, setMore] = useState<Record<string, boolean>>({})
  const [busy, setBusy] = useState(false)
  const [actionError, setActionError] = useState<string | null>(null)

  const items = useMemo<Array<Item & { column: Column }>>(() => {
    const byId = new Map((gates.data ?? []).map((g) => [g.systemId, g]))
    const real = systems.filter((s) => s.metadata?.source !== 'fallback' && s.id)
    const registered = real
      .filter((s) => !stage || s.stage === stage)
      .map((s) => {
        const gate = byId.get(s.id)
        const src = typeof s.metadata?.source === 'string' && s.metadata.source ? (s.metadata.source as string) : HAND
        const kind = typeof s.metadata?.asset_kind === 'string' ? (s.metadata.asset_kind as string) : undefined
        const column: Column = gate?.approvalStatus === 'approved' ? 'approved' : 'registered'
        return { type: 'system' as const, id: s.id, name: s.name, source: src, kind, system: s, gate, column }
      })
    const found = integ.discovered
      .filter((a) => a.status === 'new' && (!stage || a.suggestedStage === stage))
      .map((a) => ({ type: 'found' as const, id: a.id, name: a.name, source: a.source, kind: a.kind, asset: a, column: 'found' as Column }))
    const q = query.trim().toLowerCase()
    const all = [...found, ...registered]
    return q ? all.filter((i) => `${i.name} ${SOURCE_LABEL[i.source] ?? i.source} ${i.kind ? KIND_LABEL[i.kind] ?? '' : ''}`.toLowerCase().includes(q)) : all
  }, [systems, gates.data, integ.discovered, stage, query])

  const sources = useMemo(() => {
    const seen = Array.from(new Set(items.map((i) => i.source)))
    return seen.sort((a, b) => (a === HAND ? 1 : b === HAND ? -1 : a.localeCompare(b)))
  }, [items])

  const sel = items.find((i) => `${i.type}:${i.id}` === openKey) ?? null
  const count = (c: Column) => items.filter((i) => i.column === c).length
  const srcLabel = (s: string) => (s === HAND ? 'Added by hand' : SOURCE_LABEL[s] ?? s)

  if ((sysLoading && systems.length === 0) || (integ.loading && !integ.error)) {
    return (
      <VStack gap={2} aria-busy="true">
        {[0, 1, 2, 3].map((i) => (
          <Skeleton key={i} height={56} />
        ))}
      </VStack>
    )
  }
  const loadError = sysError ?? integ.error ?? gates.error
  if (loadError) {
    return (
      <EmptyState
        title="AI systems could not load"
        description={loadError}
        actions={
          <Button
            label="Try again"
            onClick={() => {
              void refreshSystems()
              gates.reload()
              void integ.refresh()
            }}
          />
        }
      />
    )
  }
  if (items.length === 0 && !query && !stage) {
    return (
      <EmptyState
        title="No AI systems yet"
        description="Connect GitHub, MLflow or Hugging Face to find them, or register one by hand."
        actions={<Button variant="primary" label="Find unregistered AI" href="/discovery" />}
      />
    )
  }

  async function register(asset: DiscoveredAsset) {
    setBusy(true)
    setActionError(null)
    try {
      const out = await integ.promote(asset.id)
      await refreshSystems()
      router.push(`/systems/${encodeURIComponent(out.systemId)}`)
    } catch (e) {
      setActionError(e instanceof Error ? e.message : 'Could not register it')
    } finally {
      setBusy(false)
    }
  }
  async function ignore(asset: DiscoveredAsset) {
    setBusy(true)
    setActionError(null)
    try {
      await integ.ignore(asset.id)
      setOpenKey(null)
    } catch (e) {
      setActionError(e instanceof Error ? e.message : 'Could not ignore it')
    } finally {
      setBusy(false)
    }
  }

  return (
    <VStack gap={4}>
      <HStack gap={3} hAlign="between" vAlign="center" wrap="wrap">
        <div className="sys-filter">
          {stage && (
            <>
              <Token size="sm" label={`Stage: ${stage}`} />
              <Button variant="ghost" size="sm" label="Clear stage" href="/systems" />
            </>
          )}
        </div>
        <TextInput type="search" label="Search systems" isLabelHidden placeholder="Search systems" value={query} onChange={setQuery} startIcon={Search} hasClear width={240} />
      </HStack>

      {items.length === 0 ? (
        <EmptyState title="Nothing matches" description={stage ? `No systems at the ${stage} stage match.` : 'No systems match that search.'} />
      ) : (
        <div className="sys-scroll">
          <div className="sys-lanes">
            <div className="sys-head">
              <Text type="supporting">Where it was found</Text>
            </div>
            {COLUMNS.map((c) => (
              <div key={c.key} className={`sys-head ${c.key}`}>
                <b>{count(c.key)}</b>
                <span>{c.title}</span>
              </div>
            ))}
            {sources.map((src) => {
              const total = items.filter((i) => i.source === src).length
              return [
                <div key={src} className="sys-src">
                  <b>{srcLabel(src)}</b>
                  <span>
                    {total} {total === 1 ? 'system' : 'systems'}
                  </span>
                </div>,
                ...COLUMNS.map((c) => {
                  const key = `${src}:${c.key}`
                  const list = items.filter((i) => i.source === src && i.column === c.key)
                  const visible = more[key] ? list : list.slice(0, SHOW)
                  return (
                    <div key={key} className={`sys-col ${c.key}`}>
                      {visible.map((i) => {
                        const Icon = i.kind ? KIND_ICON[i.kind] : undefined
                        const mini = i.type === 'system' ? miniState(i.gate) : null
                        return (
                          <button key={`${i.type}:${i.id}`} type="button" className="sys-item" aria-pressed={`${i.type}:${i.id}` === openKey} onClick={() => setOpenKey(`${i.type}:${i.id}`)}>
                            {Icon && <Icon size={16} aria-hidden />}
                            <span className="nm">{i.name}</span>
                            {mini && <Mini {...mini} />}
                          </button>
                        )
                      })}
                      {list.length > SHOW && (
                        <span className="sys-more">
                          <Button variant="ghost" size="sm" label={more[key] ? 'Show fewer' : `Show ${list.length - SHOW} more`} onClick={() => setMore((m) => ({ ...m, [key]: !m[key] }))} />
                        </span>
                      )}
                    </div>
                  )
                }),
              ]
            })}
          </div>
        </div>
      )}

      <Drawer isOpen={sel !== null} onOpenChange={(o) => { if (!o) { setOpenKey(null); setActionError(null) } }} label={sel?.name ?? 'System'} width={460} padding={5}>
        {sel && (
          <VStack gap={5}>
            <VStack gap={2} align="start">
              {sel.type === 'found' ? (
                <Token size="sm" color="orange" label="Found, not registered" />
              ) : (
                <Token size="sm" color="gray" label={miniState(sel.gate).word} />
              )}
              <Heading level={2}>{sel.name}</Heading>
            </VStack>
            <MetadataList label={{ width: 120 }}>
              <MetadataListItem label="Source">{srcLabel(sel.source)}</MetadataListItem>
              {sel.kind && <MetadataListItem label="Kind">{KIND_LABEL[sel.kind] ?? sel.kind}</MetadataListItem>}
              {sel.type === 'found' ? (
                <>
                  <MetadataListItem label="Where"><Text type="code">{sel.asset.externalId}</Text></MetadataListItem>
                  <MetadataListItem label="Suggested risk">{sel.asset.suggestedTier}</MetadataListItem>
                  <MetadataListItem label="Suggested stage">{sel.asset.suggestedStage}</MetadataListItem>
                </>
              ) : (
                <>
                  <MetadataListItem label="Owner">{sel.system.owner || 'Nobody yet'}</MetadataListItem>
                  <MetadataListItem label="Risk">{sel.system.riskTier}</MetadataListItem>
                  <MetadataListItem label="Stage">{sel.system.stage}</MetadataListItem>
                  {sel.gate && <MetadataListItem label="Gate verdict">{sel.gate.verdict.replace(/_/g, ' ')}</MetadataListItem>}
                </>
              )}
            </MetadataList>
            {actionError && <Banner status="error" title="That did not work" description={actionError} />}
            {sel.type === 'found' ? (
              <VStack gap={2}>
                <Button variant="primary" label="Register it" isDisabled={busy} onClick={() => register(sel.asset)} />
                <Button label="Ignore" isDisabled={busy} onClick={() => ignore(sel.asset)} />
              </VStack>
            ) : (
              <Button variant="primary" label="Open the system file" href={`/systems/${encodeURIComponent(sel.id)}`} />
            )}
          </VStack>
        )}
      </Drawer>
    </VStack>
  )
}

export default function SystemsPage() {
  return (
    <div className="fm-page">
      <VStack gap={5}>
        <HStack gap={4} hAlign="between" vAlign="end" wrap="wrap">
          <VStack gap={1}>
            <Heading level={1}>AI systems</Heading>
            <Text color="secondary">Every AI system found and registered, by where it came from and how far along it is.</Text>
          </VStack>
          <Button label="Find unregistered AI" variant="secondary" href="/discovery" />
        </HStack>
        <Suspense fallback={<Skeleton height={56} />}>
          <Lanes />
        </Suspense>
      </VStack>
    </div>
  )
}
