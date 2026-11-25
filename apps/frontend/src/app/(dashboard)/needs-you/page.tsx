'use client'

import '@/astryx/pages/needs-you.css'
import { useState } from 'react'
import { Banner } from '@astryxdesign/core/Banner'
import { Button } from '@astryxdesign/core/Button'
import { Drawer } from '@astryxdesign/core/Drawer'
import { EmptyState } from '@astryxdesign/core/EmptyState'
import { HStack, VStack } from '@astryxdesign/core/Layout'
import { SegmentedControl, SegmentedControlItem } from '@astryxdesign/core/SegmentedControl'
import { Skeleton } from '@astryxdesign/core/Skeleton'
import { Heading, Text } from '@astryxdesign/core/Text'
import { TextArea } from '@astryxdesign/core/TextArea'
import { Token } from '@astryxdesign/core/Token'
import { useOrg } from '@/context/OrgContext'
import { usePackActions } from '@/lib/api/hooks/usePacks'
import { usePolicyActions } from '@/lib/api/hooks/usePolicies'
import { acceptOverride } from '@/lib/api/hooks/useApplicability'
import { KIND, useNeedsYou, type Item, type Kind } from '@/astryx/data/needsYou'

export default function NeedsYouPage() {
  const { selectedOrg } = useOrg()
  const orgId = selectedOrg?.id ?? null
  const { items, loading, errors, reload: reloadAll, records } = useNeedsYou()
  const packActions = usePackActions()
  const policyActions = usePolicyActions(orgId)

  const [filter, setFilter] = useState<'all' | Kind>('all')
  const [openId, setOpenId] = useState<string | null>(null)
  const [notes, setNotes] = useState('')
  const [busy, setBusy] = useState<string | null>(null)
  const [message, setMessage] = useState<{ status: 'error' | 'success'; text: string } | null>(null)

  const visible = filter === 'all' ? items : items.filter((i) => i.kind === filter)
  const counts = (k: Kind) => items.filter((i) => i.kind === k).length
  const open = items.find((i) => i.id === openId) ?? null

  const run = async (id: string, work: () => Promise<string | null>, done: string) => {
    setBusy(id)
    setMessage(null)
    const err = await work()
    setBusy(null)
    if (err) setMessage({ status: 'error', text: err })
    else {
      setMessage({ status: 'success', text: done })
      setOpenId(null)
      setNotes('')
      reloadAll()
    }
  }
  const attempt = (fn: () => Promise<unknown>) => async () => {
    try {
      await fn()
      return null
    } catch (e) {
      return e instanceof Error ? e.message : 'Request failed'
    }
  }

  const quick = (item: Item) => {
    const [, key] = item.id.split(/:(.+)/)
    if (item.kind === 'tier') {
      const rec = records?.find((s) => s.id === key)
      const evidenceId = rec?.applicability?.evidenceId
      if (!evidenceId) return
      // A 403 means the person who lowered the tier cannot sign it off; the server's message is shown as is.
      return run(item.id, attempt(() => acceptOverride(key, evidenceId)), 'Lower tier accepted.')
    }
    if (item.kind === 'ack') return run(item.id, attempt(() => policyActions.acknowledge(key)), 'Policy acknowledged.')
    if (item.kind === 'alert') return run(item.id, attempt(() => policyActions.acknowledgeAlert(key)), 'Alert acknowledged.')
  }

  const decide = (item: Item, choice: string) => {
    const [, key] = item.id.split(/:(.+)/)
    if (item.kind === 'run') {
      return run(item.id, async () => (await packActions.decideRun(key, choice as 'approve' | 'request_changes' | 'reject', notes.trim() || undefined)).error, 'Decision recorded.')
    }
    if (item.kind === 'policy') {
      return run(item.id, attempt(() => policyActions.act(key, choice as 'approve' | 'reject')), choice === 'approve' ? 'Policy approved.' : 'Policy sent back.')
    }
  }

  return (
    <div className="fm-page">
      <VStack gap={5}>
        <VStack gap={1}>
          <Heading level={1}>Needs you</Heading>
          <Text color="secondary">Everything that waits on a person, in one list: decisions, sign-offs and things to read.</Text>
        </VStack>

        {message && <Banner status={message.status} title={message.text} isDismissable onDismiss={() => setMessage(null)} />}
        {errors.length > 0 && <Banner status="error" title="Some lists could not load" description={errors[0]} endContent={<Button label="Try again" size="sm" onClick={reloadAll} />} />}

        <SegmentedControl label="Filter by type" value={filter} onChange={(v) => setFilter(v as typeof filter)}>
          <SegmentedControlItem value="all" label={`All ${items.length}`} />
          {(Object.keys(KIND) as Kind[]).map((k) => (
            <SegmentedControlItem key={k} value={k} label={`${KIND[k].label} ${counts(k)}`} />
          ))}
        </SegmentedControl>

        <section className="fm-card" aria-label="Inbox">
          {loading ? (
            <VStack gap={2}>{[0, 1, 2, 3].map((i) => <Skeleton key={i} height={40} />)}</VStack>
          ) : visible.length === 0 ? (
            <EmptyState title="Nothing waits on you" description="No decisions, sign-offs or policies need a person right now. New ones appear here as they come up." />
          ) : (
            <div className="fm-inbox">
              {visible.map((item) => (
                <div key={item.id} className="fm-inbox-row">
                  <span><Token size="sm" color={KIND[item.kind].color} label={KIND[item.kind].label} /></span>
                  <div className="fm-inbox-what"><b>{item.title}</b><span>{item.detail}</span></div>
                  <span className="fm-inbox-who">{item.who}</span>
                  <div className="fm-inbox-act">
                    {item.href && (item.panel || item.kind === 'alert') && <Button label={item.kind === 'alert' ? 'Open system' : 'Open run'} size="sm" variant="ghost" href={item.href} />}
                    {item.href && !item.panel && item.kind !== 'alert' && <Button label={item.cta ?? 'Open'} size="sm" variant="secondary" href={item.href} />}
                    {item.panel && <Button label={item.cta ?? 'Review'} size="sm" variant="primary" onClick={() => { setOpenId(item.id); setNotes(''); setMessage(null) }} />}
                    {!item.panel && (item.kind === 'tier' || item.kind === 'ack' || item.kind === 'alert') && <Button label={item.cta ?? 'Done'} size="sm" variant="primary" isLoading={busy === item.id} onClick={() => quick(item)} />}
                  </div>
                </div>
              ))}
            </div>
          )}
        </section>
      </VStack>

      <Drawer isOpen={open !== null} onOpenChange={(o) => !o && setOpenId(null)} label={open?.title ?? 'Decision'} width={440} padding={5}>
        {open && (
          <VStack gap={4}>
            <VStack gap={2} align="start">
              <Token size="sm" color={KIND[open.kind].color} label={KIND[open.kind].label} />
              <Heading level={2}>{open.title}</Heading>
              <Text color="secondary">{open.detail}</Text>
              <Text type="supporting">{open.who}</Text>
            </VStack>
            {open.kind !== 'policy' && <TextArea label="Notes" description="Kept with the decision on the record." value={notes} onChange={setNotes} />}
            {message?.status === 'error' && <Banner status="error" title={message.text} />}
            <HStack gap={2} wrap="wrap">
              <Button label="Approve" variant="primary" isLoading={busy === open.id} onClick={() => decide(open, 'approve')} />
              {open.kind === 'run' && <Button label="Request changes" variant="secondary" isDisabled={busy === open.id} onClick={() => decide(open, 'request_changes')} />}
              <Button label={open.kind === 'policy' ? 'Send back' : 'Reject'} variant="secondary" isDisabled={busy === open.id} onClick={() => decide(open, 'reject')} />
            </HStack>
          </VStack>
        )}
      </Drawer>
    </div>
  )
}
