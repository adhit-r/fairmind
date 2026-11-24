'use client'

import { createContext, useContext, useMemo, type ReactNode } from 'react'
import { useOrg } from '@/context/OrgContext'
import { useSession } from '@/context/SessionContext'
import { API_ENDPOINTS } from '@/lib/api/endpoints'
import { useOrgResource, useWaitingRuns, type Resource } from '@/lib/api/hooks/usePacks'
import { usePlan } from '@/lib/api/hooks/usePlan'
import { usePolicyResource, type Policy, type PolicyAlert } from '@/lib/api/hooks/usePolicies'
import { useApprovalRequests, useSystemRecords } from '@/astryx/data/approvals'
import { useMyAuditWork } from '@/lib/api/hooks/useInternalAudit'
import type { SystemRecord } from '@/lib/api/hooks/useSystemFile'

export type Kind = 'approval' | 'run' | 'plan' | 'tier' | 'ack' | 'policy' | 'alert' | 'audit'
export const KIND: Record<Kind, { label: string; color: 'orange' | 'blue' | 'green' | 'red' | 'gray' }> = {
  approval: { label: 'Release approval', color: 'orange' },
  run: { label: 'Workflow run', color: 'blue' },
  plan: { label: 'Plan task', color: 'gray' },
  tier: { label: 'Tier sign-off', color: 'orange' },
  ack: { label: 'Read a policy', color: 'green' },
  policy: { label: 'Policy approval', color: 'orange' },
  alert: { label: 'Policy alert', color: 'red' },
  audit: { label: 'Internal audit', color: 'blue' },
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
  reportAssignments: Resource<ReviewAssignment[]>
  total: number | undefined
  loading: boolean
  errors: string[]
  reload: () => void
  records: SystemRecord[] | null
}

type ReviewAssignment = {
  title: string
  systemName: string
  run: {
    id: string; systemId: string; definitionId: string; dateFrom: string; dateTo: string
    status: 'ready'; reviewState: 'awaiting_review'; reviewer: { id: string }
  }
}

const textPresent = (value: unknown): value is string => typeof value === 'string' && value.trim().length > 0
const calendarDay = /^\d{4}-\d{2}-\d{2}$/
const uuid = /^(?:[\da-f]{32}|[\da-f]{8}(?:-[\da-f]{4}){3}-[\da-f]{12})$/i
const reviewerKey = (id?: string) => typeof id === 'string' && uuid.test(id) ? id.replace(/-/g, '').toLowerCase() : id

function assignedReport(row: ReviewAssignment | null, userId?: string) {
  const run = row?.run
  return Boolean(row && run && userId && reviewerKey(run.reviewer?.id) === reviewerKey(userId) && run.status === 'ready' && run.reviewState === 'awaiting_review'
    && textPresent(row.title) && textPresent(row.systemName) && textPresent(run.id) && textPresent(run.definitionId) && textPresent(run.systemId)
    && typeof run.dateFrom === 'string' && typeof run.dateTo === 'string' && calendarDay.test(run.dateFrom) && calendarDay.test(run.dateTo)
    && Number.isFinite(Date.parse(run.dateFrom)) && Number.isFinite(Date.parse(run.dateTo)) && run.dateFrom <= run.dateTo)
}

const Ctx = createContext<NeedsYou | null>(null)

/**
 * Everything that waits on a person, built once for the dashboard: the Needs you
 * page lists it and the menu counts it, so the two always agree, and acting on
 * the page reloads the count too.
 */
export function NeedsYouProvider({ children }: { children: ReactNode }) {
  const { user } = useSession()
  return <NeedsYouScope key={user?.id} userId={user?.id}>{children}</NeedsYouScope>
}

function NeedsYouScope({ children, userId }: { children: ReactNode; userId?: string }) {
  const { selectedOrg } = useOrg()
  const orgId = selectedOrg?.id ?? null
  const approvals = useApprovalRequests()
  const records = useSystemRecords()
  const waiting = useWaitingRuns()
  const plan = usePlan()
  const policies = usePolicyResource<Policy[]>(orgId, '')
  const alerts = usePolicyResource<PolicyAlert[]>(orgId, '/alerts')
  const audits = useMyAuditWork()
  const assignments = useOrgResource<ReviewAssignment[]>(userId ? API_ENDPOINTS.aiGovernance.systemAssuranceReviewAssignments : null)

  const value = useMemo<NeedsYou>(() => {
    const errors: string[] = []
    function itemsFrom<T>(name: string, data: T[] | null | undefined, error: string | null, loading: boolean): T[] {
      if (error || (!loading && !Array.isArray(data))) errors.push(`${name}: ${error || 'Incomplete response'}`)
      return !error && Array.isArray(data) ? data : []
    }
    const systemRows = itemsFrom('System register', records.data, records.error, records.loading)
    const names = new Map(systemRows.map((s) => [s.id, s.name]))
    const planLoading = !plan.data && !plan.error
    const tasks = plan.data?.status === 'discovery' ? [] : plan.data?.tasks
    const out: Item[] = []
    for (const r of itemsFrom('Release approvals', approvals.data, approvals.error, approvals.loading)) {
      // Approval requests are not org-scoped yet; keep only this estate's systems.
      if (r.status !== 'pending' || !names.has(r.entity_id)) continue
      out.push({ id: `approval:${r.id}`, kind: 'approval', title: `Release decision for ${names.get(r.entity_id) ?? 'a system'}`, detail: 'Waiting for a reviewer to approve or reject the release.', who: r.requested_by ? `Requested by ${r.requested_by}` : 'Requested', cta: 'Review', href: `/systems/${encodeURIComponent(r.entity_id)}?decide` })
    }
    for (const run of itemsFrom('Workflow runs', waiting.data, waiting.error, waiting.loading)) {
      const approval = run.waitingFor === 'approval'
      out.push({ id: `run:${run.id}`, kind: 'run', title: run.workflowName, detail: approval ? `Waiting for a decision at ${run.currentStep ?? 'a gate'}.` : `Waiting for your input at ${run.currentStep ?? 'a step'}.`, who: 'Workflow run', href: `/runs?run=${encodeURIComponent(run.id)}`, cta: approval ? 'Decide' : 'Open run', panel: approval })
    }
    for (const t of itemsFrom('Plan tasks', tasks, plan.error, planLoading)) {
      if (t.state !== 'needs_you' && t.state !== 'review') continue
      out.push({ id: `plan:${t.key}`, kind: 'plan', title: t.title, detail: t.state === 'review' ? 'An agent finished this; it waits for your review.' : 'This task needs a person.', who: t.owner ? `Owner ${t.owner}` : 'No owner yet', href: '/plan', cta: 'Open plan' })
    }
    for (const s of systemRows) {
      const a = s.applicability
      if (!a || !a.tierBelowSuggestion || a.overrideAcceptedBy) continue
      out.push({ id: `tier:${s.id}`, kind: 'tier', title: `Tier lowered on ${s.name}`, detail: `Set to ${a.tier} where the rules suggested ${a.suggestedTier}.${a.reason ? ` Reason: ${a.reason}` : ''}`, who: `Changed by ${a.confirmedBy}`, cta: 'Accept lower tier' })
    }
    for (const p of itemsFrom('Policies', policies.data, policies.error, policies.loading)) {
      if (p.status === 'published' && p.acknowledgement && !p.acknowledgement.mine) {
        out.push({ id: `ack:${p.id}`, kind: 'ack', title: p.name, detail: p.summary || 'Published policy that you have not acknowledged.', who: `${p.acknowledgement.acknowledged} of ${p.acknowledgement.required} have read it`, cta: 'Acknowledge' })
      }
      if (p.status === 'in_review') {
        out.push({ id: `policy:${p.id}`, kind: 'policy', title: p.name, detail: p.summary || 'Submitted for approval.', who: p.submittedBy ? `Submitted by ${p.submittedBy}` : 'Submitted', cta: 'Review', panel: true })
      }
    }
    for (const al of itemsFrom('Policy alerts', alerts.data, alerts.error, alerts.loading)) {
      if (al.status !== 'open' || al.acknowledgedAt) continue
      out.push({ id: `alert:${al.id}`, kind: 'alert', title: `${al.ruleTitle} on ${al.systemName}`, detail: al.detail, who: `${al.policyName}, ${al.severity}`, href: `/systems/${encodeURIComponent(al.systemId)}`, cta: 'Acknowledge' })
    }
    for (const w of itemsFrom('Internal audits', audits.data?.items, audits.error, audits.loading)) {
      const area = `/internal-audit/${encodeURIComponent(w.auditId)}/areas/${encodeURIComponent(w.areaId)}`
      out.push(w.kind === 'conclude'
        ? { id: `audit:${w.areaId}`, kind: 'audit', title: `${w.areaName}: ${w.open} ${w.open === 1 ? 'check' : 'checks'} to conclude`, detail: 'You audit this area. Conclude each check, then send the area to the lead auditor.', who: w.auditTitle, href: area, cta: 'Open area' }
        : { id: `audit:${w.areaId}`, kind: 'audit', title: `Accept ${w.areaName}`, detail: 'The auditor sent this area to you as lead auditor.', who: w.auditTitle, href: area, cta: 'Review area' })
    }
    const reportRows = Array.isArray(assignments.data) && !assignments.error
      ? [...new Map(assignments.data.filter((row) => assignedReport(row, userId)).map((row) => [row.run.id, row])).values()] : null
    const reportAssignments = { ...assignments, data: reportRows }
    const loading = [approvals, records, waiting, policies, alerts, audits].some((r) => r.loading) || planLoading
    return {
      items: out,
      reportAssignments,
      total: loading || errors.length || assignments.loading || reportRows === null ? undefined : out.length + reportRows.length,
      loading,
      errors,
      reload: () => {
        approvals.reload()
        records.reload()
        waiting.reload()
        policies.reload()
        alerts.reload()
        audits.reload()
        assignments.reload()
        void plan.reload()
      },
      records: records.data,
    }
  }, [approvals, records, waiting, plan, policies, alerts, audits, assignments, userId])

  return <Ctx.Provider value={value}>{children}</Ctx.Provider>
}

export function useNeedsYou(): NeedsYou {
  const value = useContext(Ctx)
  if (!value) throw new Error('useNeedsYou must be used inside NeedsYouProvider')
  return value
}
