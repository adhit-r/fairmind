'use client'

import { createContext, useContext, useMemo, type ReactNode } from 'react'
import { useSystemContext } from '@/components/workflow/SystemContext'
import { useOrg } from '@/context/OrgContext'
import { useWaitingRuns } from '@/lib/api/hooks/usePacks'
import { usePlan } from '@/lib/api/hooks/usePlan'
import { usePolicyResource, type Policy, type PolicyAlert } from '@/lib/api/hooks/usePolicies'
import { useApprovalRequests, useSystemRecords } from '@/astryx/data/approvals'
import type { SystemRecord } from '@/lib/api/hooks/useSystemFile'

export type Kind = 'approval' | 'run' | 'plan' | 'tier' | 'ack' | 'policy' | 'alert'
export const KIND: Record<Kind, { label: string; color: 'orange' | 'blue' | 'green' | 'red' | 'gray' }> = {
  approval: { label: 'Release approval', color: 'orange' },
  run: { label: 'Workflow run', color: 'blue' },
  plan: { label: 'Plan task', color: 'gray' },
  tier: { label: 'Tier sign-off', color: 'orange' },
  ack: { label: 'Read a policy', color: 'green' },
  policy: { label: 'Policy approval', color: 'orange' },
  alert: { label: 'Policy alert', color: 'red' },
}

export interface Item {
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

interface NeedsYou {
  items: Item[]
  loading: boolean
  errors: string[]
  reload: () => void
  records: SystemRecord[] | null
}

const Ctx = createContext<NeedsYou | null>(null)

/**
 * Everything that waits on a person, built once for the dashboard: the Needs you
 * page lists it and the menu counts it, so the two always agree, and acting on
 * the page reloads the count too.
 */
export function NeedsYouProvider({ children }: { children: ReactNode }) {
  const { systems } = useSystemContext()
  const { selectedOrg } = useOrg()
  const orgId = selectedOrg?.id ?? null
  const approvals = useApprovalRequests()
  const records = useSystemRecords()
  const waiting = useWaitingRuns()
  const plan = usePlan()
  const policies = usePolicyResource<Policy[]>(orgId, '')
  const alerts = usePolicyResource<PolicyAlert[]>(orgId, '/alerts')

  const value = useMemo<NeedsYou>(() => {
    const names = new Map(systems.map((s) => [s.id, s.name]))
    const out: Item[] = []
    for (const r of approvals.data ?? []) {
      // Approval requests are not org-scoped yet; keep only this estate's systems.
      if (r.status !== 'pending' || !names.has(r.entity_id)) continue
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
    return {
      items: out,
      loading: [approvals, records, waiting, policies, alerts].some((r) => r.loading && !r.data) || (!plan.data && !plan.error),
      errors: [approvals.error, records.error, waiting.error, policies.error, alerts.error, plan.error].filter(Boolean) as string[],
      reload: () => {
        approvals.reload()
        records.reload()
        waiting.reload()
        policies.reload()
        alerts.reload()
        void plan.reload()
      },
      records: records.data,
    }
  }, [systems, approvals, records, waiting, plan, policies, alerts])

  return <Ctx.Provider value={value}>{children}</Ctx.Provider>
}

export function useNeedsYou(): NeedsYou {
  const value = useContext(Ctx)
  if (!value) throw new Error('useNeedsYou must be used inside NeedsYouProvider')
  return value
}
