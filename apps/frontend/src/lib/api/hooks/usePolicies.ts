/**
 * Organization AI policies: drafting, distribution, framework mapping and enforcement.
 */

import { useCallback, useEffect, useState } from 'react'
import { apiClient, type ApiResponse } from '../api-client'
import { API_ENDPOINTS } from '../endpoints'

export type PolicyStatus = 'draft' | 'in_review' | 'approved' | 'published' | 'retired'
export type PolicyAction = 'submit' | 'reject' | 'approve' | 'publish' | 'revise' | 'retire'
export type RuleOutcome = 'pass' | 'fail' | 'not_applicable'

/** A rule condition: a fact test, or all / any / not over nested conditions. */
export type Condition =
  | { fact: string; op: string; value?: unknown }
  | { all: Condition[] }
  | { any: Condition[] }
  | { not: Condition }

export interface PolicyRule {
  id: string
  title: string
  severity: 'low' | 'medium' | 'high' | 'critical'
  enforcement: 'block' | 'warn'
  when?: Condition
  check: Condition
  controls: string[]
}

export interface Policy {
  id: string
  name: string
  summary: string
  body: string
  owner: string | null
  status: PolicyStatus
  version: number
  publishedVersion: number | null
  enforced: boolean
  rules: PolicyRule[]
  controlRefs: string[]
  createdBy: string
  submittedBy: string | null
  approvedBy: string | null
  approvedAt: string | null
  createdAt: string
  updatedAt: string
  acknowledgement: { required: number; acknowledged: number; mine: boolean }
}

export interface PolicyVersion {
  version: number
  name: string
  summary: string
  body: string
  rules: PolicyRule[]
  approvedBy: string | null
  publishedBy: string
  publishedAt: string
}

export interface Acknowledgement {
  userId: string
  email: string
  name: string | null
  role: string
  acknowledgedAt: string | null
}

export interface Evaluation {
  policyId: string
  policyVersion: number
  systemId: string
  systemName: string
  ruleId: string
  outcome: RuleOutcome
  severity: string
  enforcement: 'block' | 'warn'
  detail: string
  evaluatedAt: string
}

export type ControlStatus = 'passing' | 'failing' | 'unchecked' | 'unmapped'

export interface CoverageControl {
  ref: string
  externalId: string
  title: string
  requirementId: string
  requirementTitle: string
  status: ControlStatus
  coveredBy: Array<{
    policyId: string
    policyName: string
    policyVersion: number
    ruleId: string
    ruleTitle: string
    enforcement: 'block' | 'warn'
    passingSystems: number
    failingSystems: number
  }>
}

export interface FrameworkCoverage {
  frameworkKey: string
  name: string
  versionLabel: string
  totalControls: number
  coveredControls: number
  passingControls: number
  failingControls: number
  uncheckedControls: number
  controls: CoverageControl[]
}

export interface RuleLanguage {
  facts: Array<{ name: string; description: string }>
  ops: string[]
}

export interface EnforcementRun {
  runId: string
  evaluatedAt: string
  systems: number
  policies: number
  passed: number
  failed: number
  notApplicable: number
  blocking: number
}

export type PolicyDraft = Partial<Pick<Policy, 'name' | 'summary' | 'body' | 'owner' | 'rules'>>

function unwrap<T>(response: ApiResponse<T>): T {
  if (!response.success) throw new Error(response.error || 'Policy request failed')
  return response.data as T
}

/** Load one resource for the current org; `reload` refetches it. */
export function usePolicyResource<T>(orgId: string | null, path: string) {
  const [state, setState] = useState<{ data: T | null; loading: boolean; error: string | null }>({
    data: null,
    loading: true,
    error: null,
  })
  const reload = useCallback(async () => {
    if (!orgId) return
    setState((s) => ({ ...s, loading: true, error: null }))
    try {
      const data = unwrap(await apiClient.get<T>(`${API_ENDPOINTS.aiGovernance.policies(orgId)}${path}`))
      setState({ data, loading: false, error: null })
    } catch (err) {
      setState({ data: null, loading: false, error: err instanceof Error ? err.message : 'Policy request failed' })
    }
  }, [orgId, path])
  useEffect(() => {
    void reload()
  }, [reload])
  return { ...state, reload }
}

export function usePolicyActions(orgId: string | null) {
  const base = orgId ? API_ENDPOINTS.aiGovernance.policies(orgId) : ''
  return {
    create: async (draft: PolicyDraft) => unwrap(await apiClient.post<Policy>(base, draft)),
    update: async (id: string, draft: PolicyDraft) => unwrap(await apiClient.patch<Policy>(`${base}/${id}`, draft)),
    remove: async (id: string) => unwrap(await apiClient.delete<{ deleted: boolean }>(`${base}/${id}`)),
    act: async (id: string, action: PolicyAction) => unwrap(await apiClient.post<Policy>(`${base}/${id}/actions`, { action })),
    acknowledge: async (id: string) => unwrap(await apiClient.post<Policy>(`${base}/${id}/acknowledge`)),
    enforce: async (policyId?: string) => unwrap(await apiClient.post<EnforcementRun>(`${base}/enforce`, policyId ? { policyId } : {})),
  }
}
