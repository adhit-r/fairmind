'use client'

import '@/astryx/pages/system-file.css'
import '@/astryx/pages/lifecycle.css'
import NextLink from 'next/link'
import { useParams, useRouter } from 'next/navigation'
import { useMemo, useState, type ReactNode } from 'react'
import { ArrowDown, Box, Database, FileText, ListTree, SlidersHorizontal, Users } from 'lucide-react'
import { Badge } from '@astryxdesign/core/Badge'
import { Banner } from '@astryxdesign/core/Banner'
import { Button } from '@astryxdesign/core/Button'
import { EmptyState } from '@astryxdesign/core/EmptyState'
import { HStack, VStack } from '@astryxdesign/core/Layout'
import { Skeleton } from '@astryxdesign/core/Skeleton'
import { Heading, Text } from '@astryxdesign/core/Text'
import { TextArea } from '@astryxdesign/core/TextArea'
import { TextInput } from '@astryxdesign/core/TextInput'
import { useSystemChanges, type PartKey } from '@/lib/api/hooks/useLifecycle'
import { useSystemFile } from '@/lib/api/hooks/useSystemFile'
import { RISK_TONE, cap } from '@/astryx/data/system-file'
import { Cell } from '../Lifecycle'

const PART_ICON: Record<PartKey, ReactNode> = {
  data: <Database size={34} strokeWidth={1.6} aria-hidden />,
  model: <Box size={34} strokeWidth={1.6} aria-hidden />,
  tools: <ListTree size={34} strokeWidth={1.6} aria-hidden />,
  threshold: <SlidersHorizontal size={34} strokeWidth={1.6} aria-hidden />,
  use: <Users size={34} strokeWidth={1.6} aria-hidden />,
  docs: <FileText size={34} strokeWidth={1.6} aria-hidden />,
}

/** Record a change: tap the parts that changed and see which gate checks it reopens before it is recorded. */
export default function RecordChangePage() {
  const { id } = useParams<{ id: string }>()
  const router = useRouter()
  const file = useSystemFile(id)
  const changes = useSystemChanges(id)
  const [picked, setPicked] = useState<PartKey[]>([])
  const [version, setVersion] = useState('')
  const [note, setNote] = useState('')
  const [busy, setBusy] = useState(false)
  const [error, setError] = useState<string | null>(null)

  const parts = useMemo(() => changes.data?.parts ?? [], [changes.data])
  const reopened = useMemo(() => new Set(parts.filter((p) => picked.includes(p.key)).flatMap((p) => p.reopens)), [parts, picked])
  const s = file.system
  const checks = file.gate?.checks ?? []

  if (file.loading || changes.loading) return <VStack gap={4}><Skeleton height={40} /><Skeleton height={320} /></VStack>
  if (!s) return <EmptyState title="System not found" description={file.error ?? 'This system could not be loaded.'} />
  if (s.lifecycleStage === 'retired') return <EmptyState title="This system is retired" description="Its file is read only, so no change can be recorded." actions={<Button label="Back to the system file" variant="secondary" href={`/systems/${id}`} />} />

  const toggle = (k: PartKey) => setPicked((p) => (p.includes(k) ? p.filter((x) => x !== k) : [...p, k]))
  const kind = picked.length === 0 ? { label: 'Pick what changed', tone: 'neutral' as const } : reopened.size ? { label: 'Material change', tone: 'orange' as const } : { label: 'Minor change', tone: 'green' as const }

  const submit = async () => {
    setBusy(true)
    setError(null)
    try {
      await changes.record({ parts: picked, toVersion: version.trim() || undefined, note: note.trim() || undefined })
      router.push(`/systems/${id}`)
    } catch (e) {
      setError(e instanceof Error ? e.message : 'Could not record the change')
      setBusy(false)
    }
  }

  return (
    <VStack gap={5}>
      <HStack gap={2} vAlign="center" wrap="wrap" className="fm-sf-crumb">
        <NextLink href="/systems">AI systems</NextLink><span aria-hidden>/</span>
        <NextLink href={`/systems/${id}`}>{s.name}</NextLink><span aria-hidden>/</span>
        <span>Record a change</span>
      </HStack>
      <HStack gap={3} vAlign="center" wrap="wrap">
        <Heading level={1}>{s.name}</Heading>
        <Badge variant={RISK_TONE[s.riskTier]} label={`${cap(s.riskTier)} risk`} />
      </HStack>
      {error && <Banner status="error" title="Not recorded" description={error} />}
      {changes.error && <Banner status="error" title="Could not load the parts" description={changes.error} />}

      <section className="fm-card" aria-labelledby="ch-what">
        <VStack gap={5}>
          <Heading level={2} id="ch-what">What changed</Heading>
          <div className="fm-lc-parts">
            {parts.map((p) => (
              <button key={p.key} type="button" className="fm-lc-part" aria-pressed={picked.includes(p.key)} onClick={() => toggle(p.key)}>
                <span className="ico">{PART_ICON[p.key]}</span>
                {p.label}
                <span className="tag">{picked.includes(p.key) ? (p.reopens.length ? `reopens ${p.reopens.length}` : 'nothing reopens') : ''}</span>
              </button>
            ))}
          </div>
          <HStack hAlign="center"><ArrowDown size={20} aria-hidden /></HStack>
          <div className="fm-lc-impact">
            {checks.map((c) => {
              const hit = reopened.has(c.key)
              return (
                <div key={c.key} className={`fm-lc-chk${hit ? ' reopen' : ''}`}>
                  <Cell state={hit ? 'reopen' : c.state} label={`${c.label}: ${hit ? 'reopens' : c.state}`} />
                  {c.label}
                </div>
              )
            })}
          </div>
          <HStack gap={4} vAlign="center" wrap="wrap">
            <span className="fm-lc-big">{reopened.size}</span>
            <Text type="supporting" color="secondary">of {checks.length} checks reopen</Text>
            <Badge variant={kind.tone} label={kind.label} />
            {reopened.size > 0 && <Text type="supporting" color="secondary">Evidence filed before this change stops counting for those checks.</Text>}
          </HStack>
        </VStack>
      </section>

      <section className="fm-card" aria-label="Details">
        <VStack gap={4}>
          <HStack gap={4} wrap="wrap">
            <TextInput label="New version" isOptional value={version} onChange={setVersion} width={220} />
          </HStack>
          <TextArea label="What is different" isOptional value={note} onChange={setNote} rows={2} />
          <HStack gap={2}>
            <Button label="Record change" variant="primary" isDisabled={picked.length === 0 || busy} isLoading={busy} onClick={() => void submit()} />
            <Button label="Cancel" variant="secondary" href={`/systems/${id}`} />
          </HStack>
          <Text type="supporting" color="secondary">Recorded in your name and sealed with the earlier changes to this system.</Text>
        </VStack>
      </section>
    </VStack>
  )
}
