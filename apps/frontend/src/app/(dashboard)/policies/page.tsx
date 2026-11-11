'use client'

import '@/astryx/pages/policies.css'
import Link from 'next/link'
import { useMemo, useState } from 'react'
import { Banner } from '@astryxdesign/core/Banner'
import { Badge } from '@astryxdesign/core/Badge'
import { Button } from '@astryxdesign/core/Button'
import { Dialog, DialogHeader } from '@astryxdesign/core/Dialog'
import { EmptyState } from '@astryxdesign/core/EmptyState'
import { HStack, Layout, LayoutContent, LayoutFooter, VStack } from '@astryxdesign/core/Layout'
import { Skeleton } from '@astryxdesign/core/Skeleton'
import { Tab, TabList } from '@astryxdesign/core/TabList'
import { Heading, Text } from '@astryxdesign/core/Text'
import { TextArea } from '@astryxdesign/core/TextArea'
import { Token } from '@astryxdesign/core/Token'
import { useOrgId } from '@/lib/api/hooks/useOrgId'
import {
  usePolicyActions,
  usePolicyResource,
  type AIDraftedPolicy,
  type EnforcementRun,
  type Evaluation,
  type Policy,
  type PolicyAlert,
  type PolicyStatus,
} from '@/lib/api/hooks/usePolicies'

const STATUS: Record<PolicyStatus, { label: string; color: 'gray' | 'blue' | 'green' | 'orange' }> = {
  draft: { label: 'Draft', color: 'gray' },
  in_review: { label: 'In review', color: 'orange' },
  approved: { label: 'Approved', color: 'blue' },
  published: { label: 'Published', color: 'green' },
  retired: { label: 'Retired', color: 'gray' },
}
const when = (iso: string) => new Date(iso).toLocaleString('en-GB', { day: 'numeric', month: 'short', hour: '2-digit', minute: '2-digit' })

export default function PoliciesPage() {
  const orgId = useOrgId()
  const policies = usePolicyResource<Policy[]>(orgId, '')
  const alerts = usePolicyResource<PolicyAlert[]>(orgId, '/alerts')
  const evaluations = usePolicyResource<Evaluation[]>(orgId, '/evaluations')
  const actions = usePolicyActions(orgId)
  const [tab, setTab] = useState<'all' | 'alerts'>('all')
  const [failure, setFailure] = useState<string | null>(null)
  const [enforcing, setEnforcing] = useState(false)
  const [ran, setRan] = useState<EnforcementRun | null>(null)
  const [draftOpen, setDraftOpen] = useState(false)
  const [brief, setBrief] = useState('')
  const [drafting, setDrafting] = useState(false)
  const [draftError, setDraftError] = useState<string | null>(null)
  const [drafted, setDrafted] = useState<AIDraftedPolicy | null>(null)

  const list = useMemo(() => policies.data ?? [], [policies.data])
  const open = useMemo(() => (alerts.data ?? []).filter((a) => a.status === 'open'), [alerts.data])
  const alertCount = useMemo(() => {
    const m = new Map<string, number>()
    for (const a of open) m.set(a.policyId, (m.get(a.policyId) ?? 0) + 1)
    return m
  }, [open])
  const failing = useMemo(() => {
    const m = new Map<string, number>()
    for (const e of evaluations.data ?? []) if (e.outcome === 'fail') m.set(e.policyId, (m.get(e.policyId) ?? 0) + 1)
    return m
  }, [evaluations.data])

  const facts = useMemo(() => {
    const by = (s: PolicyStatus) => list.filter((p) => p.status === s).length
    const required = list.reduce((n, p) => n + p.acknowledgement.required, 0)
    const done = list.reduce((n, p) => n + p.acknowledgement.acknowledged, 0)
    return { published: by('published'), review: by('in_review') + by('approved'), draft: by('draft'), required, done, alerts: open.length }
  }, [list, open])

  const guard = async (fn: () => Promise<unknown>) => {
    setFailure(null)
    try {
      await fn()
    } catch (e) {
      setFailure(e instanceof Error ? e.message : 'Request failed')
    }
  }
  const enforce = async () => {
    setEnforcing(true)
    await guard(async () => {
      setRan(await actions.enforce())
      await Promise.all([evaluations.reload(), policies.reload(), alerts.reload()])
    })
    setEnforcing(false)
  }
  const draft = async () => {
    setDrafting(true)
    setDraftError(null)
    try {
      setDrafted(await actions.draftWithAI(brief.trim()))
      setBrief('')
      await policies.reload()
    } catch (e) {
      setDraftError(e instanceof Error ? e.message : 'Request failed')
    }
    setDrafting(false)
  }
  const closeDraft = () => {
    setDraftOpen(false)
    setDraftError(null)
    setDrafted(null)
  }

  if (!orgId) return <div className="fm-page"><EmptyState title="Select an organisation" description="Policies belong to an organisation." /></div>
  if (policies.loading && !policies.data) {
    return (
      <div className="fm-page">
        <VStack gap={3} aria-busy="true">
          <Skeleton height={36} />
          <Skeleton height={80} />
          <Skeleton height={220} />
        </VStack>
      </div>
    )
  }
  if (policies.error && !policies.data) {
    return (
      <div className="fm-page">
        <EmptyState title="Policies could not load" description={policies.error} actions={<Button label="Try again" onClick={() => void policies.reload()} />} />
      </div>
    )
  }

  const shown = tab === 'alerts' ? list.filter((p) => alertCount.has(p.id)) : list

  return (
    <div className="fm-page">
      <VStack gap={5}>
        <HStack gap={4} hAlign="between" vAlign="end" wrap="wrap">
          <VStack gap={1}>
            <Heading level={1}>Policies</Heading>
            <Text color="secondary">Your organisation&apos;s AI policies, who has acknowledged them, and whether their rules hold on every system.</Text>
          </VStack>
          <HStack gap={2}>
            <Button label={enforcing ? 'Enforcing' : 'Enforce rules now'} variant="secondary" isDisabled={enforcing} onClick={() => void enforce()} />
            <Button label="Draft a policy with the agent" variant="primary" onClick={() => setDraftOpen(true)} />
          </HStack>
        </HStack>

        {failure && <Banner status="error" title="That did not work" description={failure} isDismissable onDismiss={() => setFailure(null)} />}
        {ran && (
          <Banner
            status={ran.blocking > 0 ? 'warning' : 'success'}
            title="Enforcement ran"
            description={`${ran.policies} polic${ran.policies === 1 ? 'y' : 'ies'} on ${ran.systems} system${ran.systems === 1 ? '' : 's'}: ${ran.passed} passed, ${ran.failed} failed${ran.blocking ? ` (${ran.blocking} blocking)` : ''}, ${ran.notApplicable} not applicable.`}
            isDismissable
            onDismiss={() => setRan(null)}
          />
        )}

        <ul className="po-facts" aria-label="Policy facts">
          <li><b>{facts.published}</b><span>published</span></li>
          <li><b>{facts.review}</b><span>in review or approved</span></li>
          <li><b>{facts.draft}</b><span>drafts</span></li>
          <li><b>{facts.done}</b><span>{facts.required ? `of ${facts.required} acknowledgements in` : 'acknowledgements in'}</span></li>
          <li><b>{facts.alerts}</b><span>open alerts</span></li>
        </ul>

        <section className="fm-card" aria-label="Policies">
          <VStack gap={3}>
            <TabList value={tab} onChange={(v) => setTab(v as 'all' | 'alerts')} aria-label="Policy view">
              <Tab value="all" label={`All ${list.length}`} />
              <Tab value="alerts" label={`With open alerts ${alertCount.size}`} />
            </TabList>
            {shown.length === 0 ? (
              <EmptyState
                title={tab === 'alerts' ? 'No policy has an open alert' : 'No policies yet'}
                description={tab === 'alerts' ? 'Every published rule holds on every system it applies to.' : 'Ask the agent to draft one from a short brief.'}
                actions={tab === 'all' ? <Button label="Draft a policy with the agent" variant="primary" onClick={() => setDraftOpen(true)} /> : undefined}
              />
            ) : (
              <div className="po-scroll">
                <table className="po-table">
                  <thead>
                    <tr>
                      <th scope="col">Policy</th>
                      <th scope="col">Status</th>
                      <th scope="col">Rules</th>
                      <th scope="col">Acknowledged</th>
                      <th scope="col">Enforcement</th>
                      <th scope="col">Alerts</th>
                    </tr>
                  </thead>
                  <tbody>
                    {shown.map((p) => {
                      const fails = failing.get(p.id) ?? 0
                      const st = STATUS[p.status]
                      return (
                        <tr key={p.id}>
                          <td className="name">
                            <Link href={`/policies/${encodeURIComponent(p.id)}`}>{p.name}</Link>
                            <small>
                              v{p.version}
                              {p.publishedVersion && p.publishedVersion !== p.version ? `, v${p.publishedVersion} in force` : ''}
                              {p.owner ? ` · ${p.owner}` : ''}
                            </small>
                          </td>
                          <td><Token size="sm" color={st.color} label={st.label} /></td>
                          <td className="num">{p.rules.length}</td>
                          <td className="num">{p.acknowledgement.required ? `${p.acknowledgement.acknowledged} of ${p.acknowledgement.required}` : 'Not distributed'}</td>
                          <td>{!p.enforced ? 'Not enforced' : fails ? <Token size="sm" color="red" label={`${fails} failing`} /> : <Token size="sm" color="green" label="Passing" />}</td>
                          <td className="num">{alertCount.get(p.id) ?? 0}</td>
                        </tr>
                      )
                    })}
                  </tbody>
                </table>
              </div>
            )}
          </VStack>
        </section>

        <VStack gap={3}>
          <HStack gap={2} vAlign="center">
            <Heading level={2}>Open alerts</Heading>
            <Badge variant={open.length ? 'warning' : 'neutral'} label={String(open.length)} />
            <Button label="All alerts" variant="ghost" size="sm" href="/alerts" />
          </HStack>
          {alerts.error ? (
            <EmptyState title="Alerts could not load" description={alerts.error} actions={<Button label="Try again" onClick={() => void alerts.reload()} />} />
          ) : open.length === 0 ? (
            <Text color="secondary">No published rule is failing on any system.</Text>
          ) : (
            <ul className="po-alerts">
              {open.map((a) => (
                <li key={a.id}>
                  <Token size="sm" color={a.enforcement === 'block' ? 'red' : 'orange'} label={a.enforcement === 'block' ? 'Blocking' : 'Warning'} />
                  <div className="grow">
                    <Text weight="semibold">{a.systemName}: {a.ruleTitle}</Text>
                    <small>{a.detail}</small>
                    <small>
                      Failing since {when(a.openedAt)} · <Link href={`/policies/${encodeURIComponent(a.policyId)}`}>{a.policyName}</Link>
                    </small>
                  </div>
                  <HStack gap={2}>
                    <Button label="Open the system" variant="secondary" size="sm" href={`/systems/${encodeURIComponent(a.systemId)}`} />
                    {a.acknowledgedAt ? (
                      <Text color="secondary">Acknowledged {when(a.acknowledgedAt)}</Text>
                    ) : (
                      <Button label="Acknowledge" variant="secondary" size="sm" onClick={() => void guard(async () => { await actions.acknowledgeAlert(a.id); await alerts.reload() })} />
                    )}
                  </HStack>
                </li>
              ))}
            </ul>
          )}
        </VStack>
      </VStack>

      <Dialog isOpen={draftOpen} onOpenChange={(o) => !o && closeDraft()}>
        <Layout
          header={<DialogHeader title="Draft a policy with the agent" subtitle="Your organisation's model writes the text and the rules the platform can check. It is saved as a draft for people to review and approve." onOpenChange={(o) => !o && closeDraft()} />}
          content={
            <LayoutContent padding={4}>
              <VStack gap={3}>
                <TextArea label="What should the policy say?" rows={5} maxLength={4000} value={brief} onChange={setBrief} description="At least 10 characters. For instance: high-risk credit models need a named owner and an approved release before they go live." />
                {draftError && (
                  <Banner
                    status="error"
                    title="The agent could not draft it"
                    description={
                      <>
                        {draftError} If no model is connected yet, <Link href="/settings">set one up in Settings</Link>.
                      </>
                    }
                  />
                )}
                {drafted && (
                  <Banner
                    status="success"
                    title={`Drafted ${drafted.name}`}
                    description={
                      <>
                        {drafted.rules.length} rule{drafted.rules.length === 1 ? '' : 's'} mapped to {drafted.controlRefs.length} control{drafted.controlRefs.length === 1 ? '' : 's'}
                        {drafted.draft.dropped.length ? `; left out ${drafted.draft.dropped.length} the platform cannot check` : ''}. <Link href={`/policies/${encodeURIComponent(drafted.id)}`}>Review it</Link>, then submit it for approval.
                      </>
                    }
                  />
                )}
              </VStack>
            </LayoutContent>
          }
          footer={
            <LayoutFooter hasDivider>
              <HStack gap={2} hAlign="end">
                <Button label="Close" variant="secondary" onClick={closeDraft} />
                <Button label={drafting ? 'Drafting' : 'Draft policy'} variant="primary" isDisabled={drafting || brief.trim().length < 10} onClick={() => void draft()} />
              </HStack>
            </LayoutFooter>
          }
        />
      </Dialog>
    </div>
  )
}
