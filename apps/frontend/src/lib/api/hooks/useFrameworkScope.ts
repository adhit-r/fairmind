'use client'

import { apiClient } from '../api-client'
import { useOrgResource, withOrg } from './usePacks'

export type ScopeVerdict = 'in' | 'out'
export type ScopeStatus = 'draft' | 'confirmed' | 'waiting_owner'

export interface ScopeEvidence {
  kind: 'file' | 'dependency' | 'readme' | 'owner' | 'signal'
  ref: string
  text: string
}

export interface ScopeItem {
  systemId: string
  systemName: string
  source: string
  verdict: ScopeVerdict | 'unsure'
  reason: string
  confidence: 'high' | 'medium' | 'low'
  evidence: ScopeEvidence[]
  status: ScopeStatus
  decidedVerdict: ScopeVerdict | null
  decidedBy: string | null
  decidedAt: string | null
  evidenceId: string | null
}

export interface ScopeSummary {
  total: number
  sure: number
  check: number
  waitingOwner: number
  confirmedIn: number
  confirmedOut: number
}

export interface ScopeView {
  framework: { key: string; name: string; test: { text: string; version: string } }
  summary: ScopeSummary
  items: ScopeItem[]
}

export interface AskOwnerResult {
  link: string
  expiresAt: string
  emailSent: boolean
}

export const MIN_SCOPE_REASON = 12

const base = (key: string) => `/api/v1/ai-governance/frameworks/${encodeURIComponent(key)}/scope`

/** True when the agent is confident enough for "accept all": a clear verdict with high confidence, still a draft. */
export const isSure = (i: ScopeItem) => i.status === 'draft' && i.verdict !== 'unsure' && i.confidence === 'high'

/** Drafts the agent is sure of first, then other drafts, then waiting on owner, then confirmed last; stable within a group. */
export function sortQueue(items: ScopeItem[]): ScopeItem[] {
  const rank = (i: ScopeItem) =>
    i.status === 'confirmed' ? 3 : i.status === 'waiting_owner' ? 2 : i.verdict === 'unsure' ? 2 : 0
  return items.map((it, n) => ({ it, n })).sort((a, b) => rank(a.it) - rank(b.it) || a.n - b.n).map((x) => x.it)
}

/** The first draft that still needs a person, after `afterId` when given (wrapping round); null when none is left. Waiting on an owner is not waiting on you. */
export function nextItem(items: ScopeItem[], afterId?: string): ScopeItem | null {
  const open = items.filter((i) => i.status === 'draft')
  if (!open.length) return null
  const at = afterId ? items.findIndex((i) => i.systemId === afterId) : -1
  const later = items.slice(at + 1).find((i) => i.status === 'draft')
  return later ?? open[0]
}

export const hasDrafts = (v: ScopeView | null) => !!v && v.items.length > 0

export const allConfirmed = (v: ScopeView | null) => !!v && v.items.length > 0 && v.items.every((i) => i.status !== 'draft')

/** Count of drafts still needing a person. */
export const toReview = (v: ScopeView) => v.items.filter((i) => i.status === 'draft').length

/** One plain sentence for the framework page card. */
export function summaryLine(v: ScopeView): string {
  const s = v.summary
  if (allConfirmed(v)) return `Scope confirmed: ${s.confirmedIn} in scope, ${s.confirmedOut} out, ${s.waitingOwner} waiting on owner`
  return `We found ${s.total} system${s.total === 1 ? '' : 's'}. The agent sorted them for this framework.`
}

async function send<T>(call: () => Promise<{ success: boolean; data?: T; error?: string }>, fail: string): Promise<T> {
  const res = await call()
  if (!res.success || !res.data) throw new Error(res.error || fail)
  return res.data
}

export const fetchScope = (key: string, orgId: string) =>
  send(() => apiClient.get<ScopeView>(withOrg(base(key), orgId)), 'Could not load the scope')

/** Runs the agent over systems with no draft yet; slow, so only on a click. */
export const draftScope = (key: string, orgId: string) =>
  send(() => apiClient.post<ScopeView>(withOrg(`${base(key)}/draft`, orgId), {}, { enableRetry: false }), 'The agent could not sort the systems')

export const confirmScope = (key: string, orgId: string, systemId: string, verdict: ScopeVerdict, reason?: string) =>
  send(
    () => apiClient.post<ScopeItem>(withOrg(`${base(key)}/${encodeURIComponent(systemId)}/confirm`, orgId), { verdict, ...(reason ? { reason } : {}) }, { enableRetry: false }),
    'Could not record the decision',
  )

export const acceptSure = (key: string, orgId: string) =>
  send(() => apiClient.post<{ accepted: number; view: ScopeView }>(withOrg(`${base(key)}/accept-sure`, orgId), {}, { enableRetry: false }), 'Could not accept the sure ones')

export const askOwner = (key: string, orgId: string, systemId: string, email: string) =>
  send(
    () => apiClient.post<AskOwnerResult>(withOrg(`${base(key)}/${encodeURIComponent(systemId)}/ask-owner`, orgId), { email }, { enableRetry: false }),
    'Could not send the question',
  )

/** The current scope view for a framework; reload after any write. */
export const useFrameworkScope = (key: string | undefined) => useOrgResource<ScopeView>(key ? base(key) : null)
