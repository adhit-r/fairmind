'use client'

import '@/astryx/pages/system-file.css'
import '@/astryx/pages/lifecycle.css'
import NextLink from 'next/link'
import { useParams, useRouter } from 'next/navigation'
import { useState, type ComponentProps, type ReactNode } from 'react'
import { Check, CircleMinus, Repeat, Scale, TriangleAlert } from 'lucide-react'
import { Banner } from '@astryxdesign/core/Banner'
import { Button } from '@astryxdesign/core/Button'
import { DateInput } from '@astryxdesign/core/DateInput'
import { EmptyState } from '@astryxdesign/core/EmptyState'
import { HStack, VStack } from '@astryxdesign/core/Layout'
import { NumberInput } from '@astryxdesign/core/NumberInput'
import { Selector } from '@astryxdesign/core/Selector'
import { Skeleton } from '@astryxdesign/core/Skeleton'
import { Heading, Text } from '@astryxdesign/core/Text'
import { TextArea } from '@astryxdesign/core/TextArea'
import { useSystemContext } from '@/components/workflow/SystemContext'
import { useRetirement, type RetireReason, type RetireTask } from '@/lib/api/hooks/useLifecycle'
import { useSystemFile } from '@/lib/api/hooks/useSystemFile'
import { Lifespan } from '../Lifecycle'

const REASONS: { key: RetireReason; label: string; icon: ReactNode }[] = [
  { key: 'replaced', label: 'Replaced', icon: <Repeat size={20} aria-hidden /> },
  { key: 'not_needed', label: 'No longer needed', icon: <CircleMinus size={20} aria-hidden /> },
  { key: 'failed_review', label: 'Failed review', icon: <TriangleAlert size={20} aria-hidden /> },
  { key: 'rule_changed', label: 'Rule changed', icon: <Scale size={20} aria-hidden /> },
]
const COLUMNS: { key: RetireTask['column']; label: string }[] = [
  { key: 'wind_down', label: 'Wind down' },
  { key: 'clean_up', label: 'Clean up' },
  { key: 'close_out', label: 'Close out' },
]

type ISODate = NonNullable<ComponentProps<typeof DateInput>['value']>
const today = () => new Date().toISOString().slice(0, 10)
const addYears = (iso: string, years: number) => {
  const d = new Date(`${iso}T00:00:00Z`)
  d.setUTCFullYear(d.getUTCFullYear() + years)
  return d.toISOString().slice(0, 10)
}

/** Retire a system: why, the closing tasks in three columns, and how long its records are kept. */
export default function RetirePage() {
  const { id } = useParams<{ id: string }>()
  const router = useRouter()
  const file = useSystemFile(id)
  const { systems } = useSystemContext()
  const [reason, setReason] = useState<RetireReason>('replaced')
  const [replacedBy, setReplacedBy] = useState<string>('')
  const ret = useRetirement(id, reason, reason === 'replaced' ? replacedBy || undefined : undefined)
  const [lastDay, setLastDay] = useState<string | undefined>(today())
  const [years, setYears] = useState<number | null>(null)
  const [confirmed, setConfirmed] = useState<string[]>([])
  const [note, setNote] = useState('')
  const [busy, setBusy] = useState(false)
  const [error, setError] = useState<string | null>(null)

  const s = file.system
  if (file.loading || (ret.loading && !ret.data)) return <VStack gap={4}><Skeleton height={40} /><Skeleton height={320} /></VStack>
  if (!s) return <EmptyState title="System not found" description={file.error ?? 'This system could not be loaded.'} />
  if (ret.data?.retired || s.lifecycleStage === 'retired') {
    return <EmptyState title="Already retired" description="This system's file is read only." actions={<Button label="Open the system file" variant="secondary" href={`/systems/${id}`} />} />
  }

  const tasks = ret.data?.tasks ?? []
  const isDone = (t: RetireTask) => (t.who === 'fairmind' ? t.done === true : confirmed.includes(t.key))
  const doneCount = tasks.filter(isDone).length
  const retention = ret.data?.retention ?? null
  const retainYears = years ?? retention?.years ?? null
  const others = systems.filter((o) => o.id !== id && o.stage !== 'retired' && o.metadata?.source !== 'fallback')
  const ready = tasks.length > 0 && doneCount === tasks.length && !!lastDay && !!retainYears && (reason !== 'replaced' || !!replacedBy)

  const toggle = (key: string) => setConfirmed((c) => (c.includes(key) ? c.filter((k) => k !== key) : [...c, key]))
  const submit = async () => {
    if (!lastDay || !retainYears) return
    setBusy(true)
    setError(null)
    try {
      await ret.retire({ reason, replacedBy: reason === 'replaced' ? replacedBy : undefined, lastDay, retainYears, confirmed, note: note.trim() || undefined })
      router.push(`/systems/${id}`)
    } catch (e) {
      setError(e instanceof Error ? e.message : 'Could not retire the system')
      setBusy(false)
    }
  }

  return (
    <VStack gap={5}>
      <HStack gap={2} vAlign="center" wrap="wrap" className="fm-sf-crumb">
        <NextLink href="/systems">AI systems</NextLink><span aria-hidden>/</span>
        <NextLink href={`/systems/${id}`}>{s.name}</NextLink><span aria-hidden>/</span>
        <span>Retire</span>
      </HStack>
      <Heading level={1}>Retire {s.name}</Heading>
      {error && <Banner status="error" title="Not retired" description={error} />}
      {ret.error && <Banner status="error" title="Could not load the closing tasks" description={ret.error} />}

      <section className="fm-card" aria-labelledby="rt-why">
        <VStack gap={4}>
          <Heading level={2} id="rt-why">Why</Heading>
          <div className="fm-lc-reasons">
            {REASONS.map((r) => (
              <button key={r.key} type="button" className="fm-lc-reason" aria-pressed={reason === r.key} onClick={() => setReason(r.key)}>
                <span className="ico">{r.icon}</span>{r.label}
              </button>
            ))}
          </div>
          <HStack gap={4} wrap="wrap" vAlign="end">
            {reason === 'replaced' && (
              <Selector
                label="Replaced by"
                placeholder={others.length ? 'Pick the system that replaces it' : 'No other system registered'}
                options={others.map((o) => ({ value: o.id, label: o.name }))}
                value={replacedBy}
                onChange={(v) => setReplacedBy(v ?? '')}
              />
            )}
            <DateInput label="Last day in use" value={lastDay as ISODate | undefined} onChange={setLastDay} />
          </HStack>
        </VStack>
      </section>

      <section className="fm-card" aria-labelledby="rt-tasks">
        <VStack gap={4}>
          <HStack gap={2} vAlign="center" hAlign="between" wrap="wrap">
            <Heading level={2} id="rt-tasks">Before it is retired</Heading>
            <Text type="supporting" color="secondary"><b>{doneCount}</b> of {tasks.length} done</Text>
          </HStack>
          <div className="fm-lc-prog" aria-hidden>{tasks.map((t) => <b key={t.key} className={isDone(t) ? 'on' : ''} />)}</div>
          <div className="fm-lc-cols">
            {COLUMNS.map((col, i) => (
              <div key={col.key} className="fm-lc-col">
                <div className="fm-lc-colh"><i>{i + 1}</i>{col.label}</div>
                {tasks.filter((t) => t.column === col.key).map((t) => {
                  const done = isDone(t)
                  const body = (
                    <>
                      <span className="fm-lc-ring">{done && <Check size={14} strokeWidth={3} aria-hidden />}</span>
                      <span>{t.label}<small>{t.who === 'fairmind' ? (t.done ? 'Checked by FairMind' : 'FairMind: not true yet') : 'You confirm'}</small></span>
                    </>
                  )
                  return t.who === 'person' ? (
                    <button key={t.key} type="button" className={`fm-lc-task${done ? ' done' : ''}`} aria-pressed={done} onClick={() => toggle(t.key)}>{body}</button>
                  ) : (
                    <div key={t.key} className={`fm-lc-task${done ? ' done' : ' blocked'}`}>{body}</div>
                  )
                })}
                {col.key === 'close_out' && lastDay && retainYears ? <Lifespan lastDay={lastDay} until={addYears(lastDay, retainYears)} /> : null}
              </div>
            ))}
          </div>
        </VStack>
      </section>

      <section className="fm-card" aria-label="Retention and sign-off">
        <VStack gap={4}>
          <HStack gap={4} wrap="wrap" vAlign="end">
            <NumberInput label="Keep records for (years)" value={retainYears} onChange={(v: number | null) => setYears(v)} min={1} max={50} />
            <Text type="supporting" color="secondary">{retention ? retention.basis : 'No rule here sets this for the risk tier; enter the period your policy requires.'}</Text>
          </HStack>
          <TextArea label="Note" isOptional value={note} onChange={setNote} rows={2} />
          <HStack gap={2} vAlign="center" wrap="wrap">
            <Button label="Retire system" variant="primary" isDisabled={!ready || busy} isLoading={busy} onClick={() => void submit()} />
            <Button label="Cancel" variant="secondary" href={`/systems/${id}`} />
            <Text type="supporting" color="secondary">Signed off in your name and sealed. The file becomes read only.</Text>
          </HStack>
        </VStack>
      </section>
    </VStack>
  )
}
