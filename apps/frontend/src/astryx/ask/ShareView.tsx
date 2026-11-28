'use client'

import { useEffect, useMemo, useState } from 'react'
import { Banner } from '@astryxdesign/core/Banner'
import { Button } from '@astryxdesign/core/Button'
import { Dialog, DialogHeader } from '@astryxdesign/core/Dialog'
import { HStack, VStack } from '@astryxdesign/core/Layout'
import { RadioList, RadioListItem } from '@astryxdesign/core/RadioList'
import { Skeleton } from '@astryxdesign/core/Skeleton'
import { Heading, Text } from '@astryxdesign/core/Text'
import { TextInput } from '@astryxdesign/core/TextInput'
import { SystemContextProvider } from '@/components/workflow/SystemContext'
import { apiClient } from '@/lib/api/api-client'
import { useSharedViews, usePackActions, type ShareViewBody } from '@/lib/api/hooks/usePacks'
import { AskBoard } from './AskBoard'

// Reads that belong to the page around the board, not to a figure on it.
const NOT_A_FIGURE = ['/boards', '/shared-views', '/ai-provider', '/packs/ask']

/** Draws the board out of sight and notes which figures it reads; ready once no new read has appeared for a moment. */
function ReadsOf({ board, onReady }: { board: string; onReady: (paths: string[]) => void }) {
  const [recording, setRecording] = useState(false)
  useEffect(() => {
    const seen = new Set<string>()
    apiClient.recorder = seen
    setRecording(true) // the board mounts only now: a child's effects run before its parent's, so it would read before anything listened
    let last = -1
    const tick = setInterval(() => {
      if (seen.size > 0 && seen.size === last) {
        clearInterval(tick)
        onReady([...seen].filter((p) => !NOT_A_FIGURE.some((x) => p.includes(x))))
      }
      last = seen.size
    }, 1200)
    return () => {
      clearInterval(tick)
      apiClient.recorder = null
    }
  }, [onReady])
  return (
    <div hidden aria-hidden="true">
      {recording && (
        <SystemContextProvider>
          <AskBoard board={board} />
        </SystemContextProvider>
      )}
    </div>
  )
}

const DAYS = { '7': 7, '30': 30, '90': 90 } as const

/** Share an Ask board as a sealed, read-only view. The server fetches the figures again and seals them; nothing here is sent as a figure. */
export function ShareView({ question, board }: { question: string; board: string }) {
  const { shareView } = usePackActions()
  const views = useSharedViews()
  const [open, setOpen] = useState(false)
  const [paths, setPaths] = useState<string[] | null>(null)
  const [access, setAccess] = useState<'named' | 'link'>('named')
  const [emails, setEmails] = useState('')
  const [days, setDays] = useState<keyof typeof DAYS>('30')
  const [busy, setBusy] = useState(false)
  const [error, setError] = useState<string | null>(null)
  const [made, setMade] = useState<{ link: string; expiresAt: string } | null>(null)
  const [copied, setCopied] = useState(false)

  const people = useMemo(() => emails.split(/[\s,;]+/).filter(Boolean), [emails])
  const canCreate = paths !== null && !busy && (access === 'link' || people.length > 0)

  const close = (o: boolean) => {
    setOpen(o)
    if (!o) {
      setPaths(null)
      setMade(null)
      setError(null)
      setCopied(false)
    }
  }
  const create = async () => {
    if (!paths) return
    setBusy(true)
    setError(null)
    const body: ShareViewBody = { question, board, paths, access, emails: access === 'named' ? people : [], days: DAYS[days] }
    const res = await shareView(body)
    setBusy(false)
    if (res.data) {
      setMade({ link: res.data.link, expiresAt: res.data.expiresAt })
      views.reload()
    } else setError(res.error)
  }

  return (
    <>
      <Button label="Share as a view" variant="secondary" onClick={() => setOpen(true)} />
      <Dialog isOpen={open} onOpenChange={close} width={560}>
        <DialogHeader title="Share this board as a view" subtitle="The person you share it with can look, not change anything." onOpenChange={close} />
        <div style={{ padding: '0 24px 24px' }}>
          {open && !made && <ReadsOf board={board} onReady={setPaths} />}
          {made ? (
            <VStack gap={3}>
              <Banner status="success" title="The view is sealed" description={access === 'named' ? 'Each person was emailed the link and will be asked for a one-time code.' : 'Anyone with the link can open it until it expires.'} />
              <Text style={{ wordBreak: 'break-all' }}>{made.link}</Text>
              <Text color="secondary" size="sm">Expires {new Date(made.expiresAt).toLocaleDateString()}. You can close it earlier under Shared views.</Text>
              <HStack gap={2} hAlign="end">
                <Button label="Close" variant="ghost" onClick={() => close(false)} />
                <Button label={copied ? 'Copied' : 'Copy link'} variant="primary" onClick={() => void navigator.clipboard.writeText(made.link).then(() => setCopied(true))} />
              </HStack>
            </VStack>
          ) : (
            <VStack gap={4}>
              <RadioList label="What they see" value="sealed" onChange={() => {}}>
                <RadioListItem value="sealed" label="Sealed snapshot" description="The figures are frozen as of now and carry a seal. What they open next week is what you sent today." />
              </RadioList>
              <Text color="secondary" size="sm">A live view that reads current figures is coming later.</Text>
              <RadioList label="Who can open it" value={access} onChange={(v) => setAccess(v as 'named' | 'link')}>
                <RadioListItem value="named" label="Named people" description="Each person gets a one-time code by email. No FairMind account needed." />
                <RadioListItem value="link" label="Anyone with the link" description="No sign-in. Anyone who has the link can open it until it expires." />
              </RadioList>
              {access === 'named' && <TextInput label="Email addresses" value={emails} onChange={setEmails} placeholder="auditor@example.com, reviewer@example.com" />}
              <RadioList label="Expires" value={days} onChange={(v) => setDays(v as keyof typeof DAYS)}>
                <RadioListItem value="7" label="7 days" />
                <RadioListItem value="30" label="30 days" />
                <RadioListItem value="90" label="90 days" />
              </RadioList>
              <Text color="secondary" size="sm">Nothing here approves a release or says a system complies. The view only shows what is on file. Items waiting on you are left out.</Text>
              {error && <Banner status="error" title="Could not share" description={error} />}
              {paths === null && <Skeleton height={20} />}
              <HStack gap={2} hAlign="end">
                <Button label="Cancel" variant="ghost" onClick={() => close(false)} />
                <Button label={busy ? 'Sealing...' : 'Create view'} variant="primary" isDisabled={!canCreate} onClick={() => void create()} />
              </HStack>
            </VStack>
          )}
        </div>
      </Dialog>
    </>
  )
}

/** The views this person shared, with who opened them; hidden until there is one. */
export function SharedViews() {
  const views = useSharedViews()
  const { revokeView } = usePackActions()
  const [error, setError] = useState<string | null>(null)
  const list = views.data?.views ?? []
  if (!list.length && !error) return null
  const revoke = async (id: string) => {
    const res = await revokeView(id)
    setError(res.error)
    views.reload()
  }
  return (
    <section aria-label="Shared views">
      <VStack gap={3}>
        <Heading level={2}>Shared views</Heading>
        {error && <Text color="secondary" size="sm">{error}</Text>}
        {list.map((v) => {
          const closed = v.revoked ? 'Revoked' : v.expired ? 'Expired' : null
          return (
            <HStack key={v.id} gap={3} hAlign="between" vAlign="center" wrap="wrap">
              <VStack gap={1}>
                <Text weight="semibold">{v.question}</Text>
                <Text color="secondary" size="sm">
                  Sealed {new Date(v.sealedAt).toLocaleDateString()}, {closed ?? `expires ${new Date(v.expiresAt).toLocaleDateString()}`}.{' '}
                  {v.access === 'link' ? 'Anyone with the link.' : v.readers.map((r) => `${r.email} (opened ${r.opens})`).join(', ')}
                </Text>
              </VStack>
              {!closed && <Button label="Revoke" variant="secondary" onClick={() => void revoke(v.id)} />}
            </HStack>
          )
        })}
      </VStack>
    </section>
  )
}
