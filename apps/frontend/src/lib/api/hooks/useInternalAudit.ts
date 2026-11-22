'use client'

import { apiClient } from '../api-client'
import { useOrgResource, withOrg } from './usePacks'

export type Grade = 'conformity' | 'observation' | 'minor_nc' | 'major_nc'
export const GRADES: Array<{ value: Grade; label: string }> = [
  { value: 'conformity', label: 'Conformity' },
  { value: 'observation', label: 'Observation' },
  { value: 'minor_nc', label: 'Minor NC' },
  { value: 'major_nc', label: 'Major NC' },
]
export const gradeLabel = (g: string | null) => GRADES.find((x) => x.value === g)?.label ?? 'Not concluded'

/** The internal audit is ISO/IEC 42001 clause 9.2; the backend takes the framework key. */
export const AUDIT_FRAMEWORK = 'ISO42001'

export interface Audit {
  id: string
  title: string
  frameworkKey: string
  periodStart: string
  periodEnd: string
  fieldworkStart: string | null
  fieldworkEnd: string | null
  leadAuditorId: string
  leadAuditorEmail: string | null
  planFilename: string | null
  planSha256: string | null
  planApprovedBy: string | null
  planApprovedAt: string | null
  status: string
  issuedBy: string | null
  issuedAt: string | null
  traceHead: string | null
  createdBy: string
  createdAt: string
}

export interface AuditArea {
  id: string
  auditId: string
  name: string
  clauses: string[]
  systemIds: string[]
  processOwner: string | null
  auditorId: string | null
  auditorEmail: string | null
  status: string
  checksTotal: number
  checksDone: number
  waitingOnOwner: number
}

export interface Conflict {
  areaId: string | null
  areaName: string | null
  auditorId: string | null
  kind?: string
  detail: string
}

export interface TeamMember {
  userId: string
  email: string | null
  role: 'lead' | 'auditor'
  checksDone: number
  checksTotal: number
}

export interface UnmatchedLine {
  line: number
  column: string
  value: string
  reason: string
}

export interface AuditView {
  audit: Audit
  team: TeamMember[]
  areas: AuditArea[]
  conflicts: Conflict[]
  gradeCounts: Partial<Record<Grade, number>> & { notConcluded: number }
  unmatchedLines: UnmatchedLine[]
}

export interface Evidence {
  kind: string
  ref: string
  text: string
  found: boolean
}

export interface OwnerAnswer {
  id: string
  email: string
  sentAt: string
  answeredAt: string | null
  questions: Array<{ key: string; text: string }>
  answers: Record<string, string> | null
}

export interface AuditCheck {
  id: string
  areaId: string
  clause: string
  clauseTitle: string | null
  systemId: string
  systemName: string | null
  question: string
  assistantSummary: string | null
  evidence: Evidence[]
  cellState: string | null
  suggestedGrade: Grade | null
  suggestedBasis: string | null
  grade: Grade | null
  statement: string | null
  overrideReason: string | null
  ownerCheckId: string | null
  remediationTaskId: string | null
  ownerAnswers: OwnerAnswer[]
}

export interface AreaView {
  area: AuditArea & { auditStatus: string; leadAuditorId: string; conflicts: Conflict[] }
  checks: AuditCheck[]
}

export interface TraceView {
  events: Array<{ seq: number; kind: string; actor: string | null; payload: Record<string, unknown>; prevHash: string; hash: string; createdAt: string }>
  valid: boolean
  head: string | null
}

export interface ManagementReview {
  audit: Audit
  resultsByClause: Array<{ clause: string; title: string | null; checks: number; concluded: number; grades: Record<string, number> }>
  openNonconformities: Array<{ checkId: string; clause: string; systemName: string | null; grade: Grade; statement: string; owner: string | null; dueDate: string | null; status: string | null }>
  counts: Record<string, number>
}

const base = '/api/v1/ai-governance/internal-audits'

/** An organisation member can be told apart from the rest by their user id; a plan-owner name is free text. */
export const mine = (userId: string | undefined, id: string | null | undefined) => !!userId && userId === id

/** The area's own auditor may conclude checks, only while it is in fieldwork. */
export const canConclude = (a: AreaView['area'], userId: string | undefined) => mine(userId, a.auditorId) && a.status === 'fieldwork' && a.auditStatus === 'fieldwork'

/** Every area accepted: the report can be issued. */
export const canIssue = (v: AuditView) => v.audit.status === 'fieldwork' && v.areas.length > 0 && v.areas.every((a) => a.status === 'accepted')

/** Share of an area's checks already concluded, for the progress bar. */
export const progressPct = (a: Pick<AuditArea, 'checksDone' | 'checksTotal'>) => (a.checksTotal ? Math.round((a.checksDone / a.checksTotal) * 100) : 0)

/** A different grade from the suggested one needs a reason before it is recorded. */
export const needsOverride = (grade: Grade | null, suggested: Grade | null) => !!grade && !!suggested && grade !== suggested

async function send<T>(call: () => Promise<{ success: boolean; data?: T; error?: string }>, fail: string): Promise<T> {
  const res = await call()
  if (!res.success || res.data === undefined) throw new Error(res.error || fail)
  return res.data
}
const post = <T,>(path: string, orgId: string, body: unknown, fail: string) =>
  send(() => apiClient.post<T>(withOrg(path, orgId), body, { enableRetry: false }), fail)

export const useAudits = () => useOrgResource<{ audits: Audit[] }>(base)
export const useAudit = (id: string | undefined) => useOrgResource<AuditView>(id ? `${base}/${encodeURIComponent(id)}` : null)
export const useAuditArea = (areaId: string | undefined) => useOrgResource<AreaView>(areaId ? `${base}/areas/${encodeURIComponent(areaId)}` : null)
export const useAuditTrace = (id: string | undefined) => useOrgResource<TraceView>(id ? `${base}/${encodeURIComponent(id)}/trace` : null)
export const useManagementReview = (id: string | undefined) =>
  useOrgResource<ManagementReview>(id ? `${base}/${encodeURIComponent(id)}/management-review` : null)

export interface NewAudit {
  title: string
  periodStart: string
  periodEnd: string
  fieldworkStart?: string
  fieldworkEnd?: string
  leadAuditorId: string
}
export const createAudit = (orgId: string, a: NewAudit) =>
  post<{ id: string }>(base, orgId, {
    title: a.title.trim(),
    framework_key: AUDIT_FRAMEWORK,
    period_start: a.periodStart,
    period_end: a.periodEnd,
    ...(a.fieldworkStart ? { fieldwork_start: a.fieldworkStart } : {}),
    ...(a.fieldworkEnd ? { fieldwork_end: a.fieldworkEnd } : {}),
    lead_auditor_id: a.leadAuditorId,
  }, 'Could not create the audit')

export const uploadPlan = (orgId: string, id: string, file: File) => {
  const form = new FormData()
  form.append('file', file)
  return post<{ areas: number; checks: number; unmatchedLines: UnmatchedLine[] }>(`${base}/${encodeURIComponent(id)}/plan`, orgId, form, 'Could not read the plan')
}
export const approvePlan = (orgId: string, id: string, approvedBy: string) =>
  post(`${base}/${encodeURIComponent(id)}/plan/approve`, orgId, { approved_by: approvedBy }, 'Could not approve the plan')
export const prepareEvidence = (orgId: string, id: string) =>
  post<{ prepared: number }>(`${base}/${encodeURIComponent(id)}/prepare`, orgId, {}, 'Could not prepare the evidence')
export const reassignArea = (orgId: string, areaId: string, auditorId: string) =>
  send(() => apiClient.patch(withOrg(`${base}/areas/${encodeURIComponent(areaId)}`, orgId), { auditor_id: auditorId }, { enableRetry: false }), 'Could not reassign the area')
export const askOwner = (orgId: string, checkId: string, email: string, text: string) =>
  post<{ link: string; expiresAt: string; emailSent: boolean }>(`${base}/checks/${encodeURIComponent(checkId)}/ask-owner`, orgId, { email, text }, 'Could not send the question')
export const concludeCheck = (orgId: string, checkId: string, grade: Grade, statement: string, overrideReason?: string) =>
  post(`${base}/checks/${encodeURIComponent(checkId)}/conclude`, orgId, { grade, statement, ...(overrideReason ? { override_reason: overrideReason } : {}) }, 'Could not record the conclusion')
export const sendToLead = (orgId: string, areaId: string) => post(`${base}/areas/${encodeURIComponent(areaId)}/send-to-lead`, orgId, {}, 'Could not send the area')
export const acceptArea = (orgId: string, areaId: string) => post(`${base}/areas/${encodeURIComponent(areaId)}/accept`, orgId, {}, 'Could not accept the area')
export const issueAudit = (orgId: string, id: string) => post(`${base}/${encodeURIComponent(id)}/issue`, orgId, {}, 'Could not issue the report')
