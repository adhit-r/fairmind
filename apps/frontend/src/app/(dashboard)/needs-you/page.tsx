'use client'

import '@/astryx/pages/needs-you.css'
import { useMemo, useState } from 'react'
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
import { useSystemContext } from '@/components/workflow/SystemContext'
import { useOrg } from '@/context/OrgContext'
import { usePackActions, useWaitingRuns } from '@/lib/api/hooks/usePacks'
import { usePlan } from '@/lib/api/hooks/usePlan'
import { usePolicyActions, usePolicyResource, type Policy, type PolicyAlert } from '@/lib/api/hooks/usePolicies'
import { acceptOverride } from '@/lib/api/hooks/useApplicability'
import { decideRequest, useApprovalRequests, useSystemRecords } from '@/astryx/data/approvals'

type Kind = 'approval' | 'run' | 'plan' | 'tier' | 'ack' | 'policy' | 'alert'
const KIND: Record<Kind, { label: string; color: 'orange' | 'blue' | 'green' | 'red' | 'gray' }> = {
  approval: { label: 'Release approval', color: 'orange' },
  run: { label: 'Workflow run', color: 'blue' },
  plan: { label: 'Plan task', color: 'gray' },
  tier: { label: 'Tier sign-off', color: 'orange' },
  ack: { label: 'Read a policy', color: 'green' },
  policy: { label: 'Policy approval', color: 'orange' },
  alert: { label: 'Policy alert', color: 'red' },
}

interface Item {
  id: string
  kind: Kind
  title: string
  detail: string
  who: string
  href?: string
  /** What the primary button does; absent when the row is a link only. */
  cta?: string
  /** True when the action needs the side panel (notes and a choice). */
  panel?: boolean
}

export default function NeedsYouPage() {
  const { systems } = useSystemContext()
  const { selectedOrg } = useOrg()
  const orgId = selectedOrg?.id ?? null
  const approvals = useApprovalRequests()
  const records = useSystemRecords()
  const waiting = useWaitingRuns()
  const plan = usePlan()
  const policies = usePolicyResource<Policy[]>(orgId, '')
  const alerts = usePolicyResource<PolicyAlert[]>(orgId, '/alerts')
  const packActions = usePackActions()
  const policyActions = usePolicyActions(orgId)

  const [filter, setFilter] = useState<'all' | Kind>('all')
  const [openId, setOpenId] = useState<string | null>(null)
  const [notes, setNotes] = useState('')
  const [busy, setBusy] = useState<string | null>(null)
  const [message, setMessage] = useState<{ status: 'error' | 'success'; text: string } | null>(null)

  const names = useMemo(() => new Map(systems.map((s) => [s.id, s.name])), [systems])
  const mine = useMemo(() => new Set(systems.map((s) => s.id)), [systems])

  const items = useMemo<Item[]>(() => {
    const out: Item[] = []
    for (const r of approvals.data ?? []) {
      if (r.status !== 'pending' || !mine.has(r.entity_id)) continue
      out.push({ id: `approval:${r.id}`, kind: 'approval', title: `Release decision for ${names.get(r.entity_id) ?? 'a system'}`, detail: 'Waiting for a reviewer to approve or reject the release.', who: r.requested_by ? `Requested by ${r.requested_by}` : 'Requested', cta: 'Review', panel: true })
    }
    for (const run of waiting.data ?? []) {
      const approval = run.waitingFor === 'approval'
      out.push({ id: `run:${run.id}`, kind: 'run', title: run.workflowName, detail: approval ? `Waiting for a decision at ${run.currentStep ?? 'a gate'}.` : `Waiting for your input at ${run.currentStep ?? 'a step'}.`, who: 'Workflow run', href: `/runs?run=${encodeURIComponent(run.id)}`, cta: approval ? 'Decide' : 'Open run', panel: approval })
    }
    for (const t of plan.data?.tasks ?? []) {
      if (t.state !== 'needs_you' && t.state !== 'review') continue
      out.push({ id: `plan:${t.key}`, kind: 'plan', title: t.title, detail: t.state === 'review' ? 'An agent finished this; it waits for your review.' : 'This task needs a person.', who: t.owner ? `Owner ${t.owner}` : 'No owner yet', href: '/plan', cta: 'Open plan' })
    }
    for (const s of records.data ?? []) {
      const a = s.applicability
      if (!a || !a.tierBelowSuggestion || a.overrideAcceptedBy) continue
      out.push({ id: `tier:${s.id}`, kind: 'tier', title: `Tier lowered on ${s.name}`, detail: `Set to ${a.tier} where the rules suggested ${a.suggestedTier}.${a.reason ? ` Reason: ${a.reason}` : ''}`, who: `Changed by ${a.confirmedBy}`, cta: 'Accept lower tier' })
    }
    for (const p of policies.data ?? []) {
      if (p.status === 'published' && p.acknowledgement && !p.acknowledgement.mine) {
        out.push({ id: `ack:${p.id}`, kind: 'ack', title: p.name, detail: p.summary || 'Published policy that you have not acknowledged.', who: `${p.acknowledgement.acknowledged} of ${p.acknowledgement.required} have read it`, cta: 'Acknowledge' })
      }
      if (p.status === 'in_review') {
        out.push({ id: `policy:${p.id}`, kind: 'policy', title: p.name, detail: p.summary || 'Submitted for approval.', who: p.submittedBy ? `Submitted by ${p.submittedBy}` : 'Submitted', cta: 'Review', panel: true })
      }
    }
    for (const al of alerts.data ?? []) {
      if (al.status !== 'open' || al.acknowledgedAt) continue
      out.push({ id: `alert:${al.id}`, kind: 'alert', title: `${al.ruleTitle} on ${al.systemName}`, detail: al.detail, who: `${al.policyName}, ${al.severity}`, href: `/systems/${encodeURIComponent(al.systemId)}`, cta: 'Acknowledge' })
    }
    return out
  }, [approvals.data, waiting.data, plan.data, records.data, policies.data, alerts.data, mine, names])

  const loading = [approvals, records, waiting, policies, alerts].some((r) => r.loading && !r.data) || (!plan.data && !plan.error)
  const errors = [approvals.error, records.error, waiting.error, policies.error, alerts.error, plan.error].filter(Boolean) as string[]
  const visible = filter === 'all' ? items : items.filter((i) => i.kind === filter)
  const counts = (k: Kind) => items.filter((i) => i.kind === k).length
  const open = items.find((i) => i.id === openId) ?? null

  const reloadAll = () => {
    approvals.reload()
    records.reload()
    waiting.reload()
    policies.reload()
    alerts.reload()
    void plan.reload()
  }
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
      const rec = records.data?.find((s) => s.id === key)
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
    if (item.kind === 'approval') {
      const d = choice === 'approve' ? 'approved' : 'rejected'
      return run(item.id, () => decideRequest(key, d, notes.trim()), d === 'approved' ? 'Release approved.' : 'Release rejected.')
    }
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
              <Button label={open.kind === 'run' || open.kind === 'policy' ? 'Approve' : 'Approve release'} variant="primary" isLoading={busy === open.id} onClick={() => decide(open, 'approve')} />
              {open.kind === 'run' && <Button label="Request changes" variant="secondary" isDisabled={busy === open.id} onClick={() => decide(open, 'request_changes')} />}
              <Button label={open.kind === 'policy' ? 'Send back' : 'Reject'} variant="secondary" isDisabled={busy === open.id} onClick={() => decide(open, 'reject')} />
            </HStack>
          </VStack>
        )}
      </Drawer>
    </div>
  )
}
