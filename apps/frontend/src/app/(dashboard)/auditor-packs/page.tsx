'use client'

import '@/astryx/pages/auditor-packs.css'
import { Suspense, useEffect, useMemo, useState } from 'react'
import { useSearchParams } from 'next/navigation'
import { Banner } from '@astryxdesign/core/Banner'
import { Button } from '@astryxdesign/core/Button'
import { Card } from '@astryxdesign/core/Card'
import { CheckboxList, CheckboxListItem } from '@astryxdesign/core/CheckboxList'
import { Dialog, DialogHeader } from '@astryxdesign/core/Dialog'
import { EmptyState } from '@astryxdesign/core/EmptyState'
import { HStack, VStack } from '@astryxdesign/core/Layout'
import { Skeleton } from '@astryxdesign/core/Skeleton'
import { Heading, Text } from '@astryxdesign/core/Text'
import { TextInput } from '@astryxdesign/core/TextInput'
import { Token } from '@astryxdesign/core/Token'

import { useSystemContext } from '@/components/workflow/SystemContext'
import { useEvidencePacks, type PackShareResult, type PackSummary } from '@/lib/api/hooks/useEvidencePacks'
import { downloadPack, sharePack, stopSharingPack } from '@/astryx/data/packs'

const day = (ts: string | null) => {
  if (!ts) return ''
  const d = new Date(ts)
  return Number.isNaN(d.getTime()) ? ts : d.toLocaleDateString('en-GB', { day: 'numeric', month: 'short', year: 'numeric' })
}

export default function AuditorPacksPage() {
  return (
    <Suspense fallback={<div className="fm-page"><Skeleton height={120} /></div>}>
      <AuditorPacks />
    </Suspense>
  )
}

function AuditorPacks() {
  const preselect = useSearchParams().get('framework')
  const { systems } = useSystemContext()
  const real = useMemo(() => systems.filter((s) => s.metadata?.source !== 'fallback'), [systems])
  const { packs, frameworks, loading, error, refresh, create } = useEvidencePacks()

  const [building, setBuilding] = useState(false)
  const [title, setTitle] = useState('')
  const [pickedFrameworks, setPickedFrameworks] = useState<string[]>([])
  const [pickedSystems, setPickedSystems] = useState<string[]>([])
  const [busy, setBusy] = useState<string | null>(null)
  const [failure, setFailure] = useState<string | null>(null)
  const [notice, setNotice] = useState<string | null>(null)
  const [link, setLink] = useState<{ pack: PackSummary; share: PackShareResult } | null>(null)
  const [copied, setCopied] = useState(false)
  const [verifying, setVerifying] = useState(false)
  const [preselected, setPreselected] = useState(false)

  // ?framework=<key> opens the builder with that framework ticked.
  useEffect(() => {
    if (preselected || !preselect || frameworks.length === 0) return
    const match = frameworks.find((f) => f.key.toLowerCase() === preselect.toLowerCase())
    setPreselected(true)
    if (match) {
      setPickedFrameworks([match.key])
      setTitle(`${match.name} pack`)
      setBuilding(true)
    }
  }, [preselect, frameworks, preselected])

  const frameworkName = (key: string) => frameworks.find((f) => f.key === key)?.name ?? key
  const systemName = (id: string) => real.find((s) => s.id === id)?.name ?? 'Unknown system'
  const sharedCount = packs.filter((p) => p.share.shared && !p.share.expired).length
  const canBuild = title.trim() !== '' && pickedFrameworks.length > 0 && pickedSystems.length > 0 && busy === null

  async function build() {
    setBusy('build')
    setFailure(null)
    const res = await create({ title: title.trim(), frameworks: pickedFrameworks, systemIds: pickedSystems })
    setBusy(null)
    if (res.success && res.data) {
      setBuilding(false)
      setTitle('')
      setPickedFrameworks([])
      setPickedSystems([])
      setNotice(`Built "${res.data.title}".`)
    } else setFailure(res.error || res.message || 'The pack could not be built')
  }

  async function download(pack: PackSummary) {
    setBusy(`dl-${pack.id}`)
    const problem = await downloadPack(pack.id)
    setBusy(null)
    setFailure(problem)
  }

  async function share(pack: PackSummary) {
    setBusy(`share-${pack.id}`)
    setFailure(null)
    const res = await sharePack(pack.id)
    setBusy(null)
    if (res.success && res.data) {
      setCopied(false)
      setLink({ pack, share: res.data })
      void refresh()
    } else setFailure(res.error || res.message || 'The link could not be made')
  }

  async function stopSharing(pack: PackSummary) {
    setBusy(`stop-${pack.id}`)
    setFailure(null)
    const res = await stopSharingPack(pack.id)
    setBusy(null)
    if (res.success) void refresh()
    else setFailure(res.error || res.message || 'Sharing could not be stopped')
  }

  const url = link && typeof window !== 'undefined' ? `${window.location.origin}/verify/${link.pack.id}?t=${encodeURIComponent(link.share.token)}` : ''

  return (
    <div className="fm-page">
      <VStack gap={5}>
        <HStack gap={4} hAlign="between" vAlign="end" wrap="wrap">
          <VStack gap={1}>
            <Heading level={1}>Auditor packs</Heading>
            <Text color="secondary">
              {loading ? 'Loading packs.' : `${packs.length} pack${packs.length === 1 ? '' : 's'}, ${sharedCount} shared with an auditor.`}
            </Text>
          </VStack>
          <HStack gap={2} wrap="wrap">
            <Button label="How to verify a pack" variant="secondary" onClick={() => setVerifying(true)} />
            <Button label="Build a pack" variant="primary" onClick={() => setBuilding(true)} />
          </HStack>
        </HStack>

        {notice && <Banner status="success" title={notice} isDismissable onDismiss={() => setNotice(null)} />}
        {failure && <Banner status="error" title={failure} isDismissable onDismiss={() => setFailure(null)} />}

        {loading ? (
          <div className="fm-pk-grid">{[0, 1, 2].map((i) => <Skeleton key={i} height={170} />)}</div>
        ) : error ? (
          <EmptyState title="The packs could not load" description={error} actions={<Button label="Try again" onClick={() => void refresh()} />} />
        ) : packs.length === 0 ? (
          <EmptyState
            title="No packs built yet"
            description="A pack gathers the evidence, release decisions and framework coverage an auditor needs, with a hash that proves it was not changed."
            actions={<Button label="Build a pack" variant="primary" onClick={() => setBuilding(true)} />}
          />
        ) : (
          <div className="fm-pk-grid">
            {packs.map((p) => (
              <Card key={p.id} padding={4}>
                <VStack gap={3}>
                  <VStack gap={1}>
                    <div className="fm-pk-meta">
                      {p.frameworks.slice(0, 3).map((f) => <Token key={f} size="sm" label={frameworkName(f)} />)}
                      {p.frameworks.length > 3 && <Text color="secondary" size="sm">+{p.frameworks.length - 3}</Text>}
                    </div>
                    <Heading level={3}>{p.title}</Heading>
                    <Text color="secondary" size="sm">
                      {p.systemIds.length} system{p.systemIds.length === 1 ? '' : 's'}: {p.systemIds.map(systemName).join(', ')}
                    </Text>
                  </VStack>
                  <div className="fm-pk-meta">
                    {p.share.shared && !p.share.expired ? (
                      <Token size="sm" color="green" label={`Shared, expires ${day(p.share.expiresAt)}`} />
                    ) : p.share.expired ? (
                      <Token size="sm" color="orange" label={`Link expired ${day(p.share.expiresAt)}`} />
                    ) : (
                      <Token size="sm" label="Not shared" />
                    )}
                  </div>
                  <div className="fm-pk-meta">
                    <span className="fm-pk-hash">{p.manifestHash.slice(0, 12)}</span>
                    <Text color="secondary" size="sm">Built {day(p.createdAt)}{p.createdBy ? ` by ${p.createdBy}` : ''}</Text>
                  </div>
                  <HStack gap={2} wrap="wrap">
                    <Button label="Open" size="sm" href={`/evidence/packs/${p.id}`} />
                    <Button label="Share a link" size="sm" isLoading={busy === `share-${p.id}`} onClick={() => void share(p)} />
                    {p.share.shared && !p.share.expired && (
                      <Button label="Stop sharing" size="sm" variant="ghost" isLoading={busy === `stop-${p.id}`} onClick={() => void stopSharing(p)} />
                    )}
                    <Button label="Download" size="sm" variant="ghost" isLoading={busy === `dl-${p.id}`} onClick={() => void download(p)} />
                  </HStack>
                </VStack>
              </Card>
            ))}
          </div>
        )}
      </VStack>

      <Dialog isOpen={building} onOpenChange={setBuilding} width={560}>
        <DialogHeader title="Build a pack" subtitle="Choose what the auditor should see." onOpenChange={setBuilding} />
        <div className="fm-pk-body">
          <VStack gap={4}>
            <TextInput label="Title" value={title} onChange={setTitle} placeholder="For example, release review for Q4" />
            <CheckboxList label="Frameworks" value={pickedFrameworks} onChange={setPickedFrameworks}>
              {frameworks.map((f) => <CheckboxListItem key={f.key} value={f.key} label={f.name} />)}
            </CheckboxList>
            {real.length === 0 ? (
              <Text color="secondary">Register an AI system first.</Text>
            ) : (
              <CheckboxList label="AI systems" value={pickedSystems} onChange={setPickedSystems}>
                {real.map((s) => <CheckboxListItem key={s.id} value={s.id} label={s.name} />)}
              </CheckboxList>
            )}
            {failure && <Banner status="error" title={failure} />}
            <HStack gap={2} hAlign="end">
              <Button label="Cancel" variant="ghost" onClick={() => setBuilding(false)} />
              <Button label="Build pack" variant="primary" isDisabled={!canBuild} isLoading={busy === 'build'} onClick={() => void build()} />
            </HStack>
          </VStack>
        </div>
      </Dialog>

      <Dialog isOpen={link !== null} onOpenChange={(o) => !o && setLink(null)} width={560}>
        <DialogHeader title="Read-only link" subtitle={link?.pack.title} onOpenChange={() => setLink(null)} />
        <div className="fm-pk-body">
          <VStack gap={3}>
            <Banner status="warning" title="Copy this link now" description="It is shown once. Anyone with it can read this pack until it expires or you stop sharing." />
            <span className="fm-pk-link">{url}</span>
            <Text color="secondary" size="sm">Expires {link ? day(link.share.expiresAt) : ''}.</Text>
            <HStack gap={2} hAlign="end">
              <Button label="Close" variant="ghost" onClick={() => setLink(null)} />
              <Button
                label={copied ? 'Copied' : 'Copy link'}
                variant="primary"
                onClick={() => void navigator.clipboard.writeText(url).then(() => setCopied(true))}
              />
            </HStack>
          </VStack>
        </div>
      </Dialog>

      <Dialog isOpen={verifying} onOpenChange={setVerifying} width={560}>
        <DialogHeader title="Verify a pack offline" onOpenChange={setVerifying} />
        <div className="fm-pk-body">
          <VStack gap={3}>
            <Text>Download the pack, then check it on any machine. The check does not call FairMind, so an auditor can trust the result without trusting this server.</Text>
            <span className="fm-pk-link">fairmind verify pack.json</span>
            <Text color="secondary" size="sm">It recomputes the pack hash and each evidence chain, and reports any item that changed or went missing.</Text>
            <HStack hAlign="end"><Button label="Close" variant="primary" onClick={() => setVerifying(false)} /></HStack>
          </VStack>
        </div>
      </Dialog>
    </div>
  )
}
