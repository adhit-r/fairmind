'use client'

import { useCallback, useEffect, useState } from 'react'
import { apiClient, type ApiResponse } from '@/lib/api/api-client'

export interface OrgMember {
  id: string
  user_id: string
  email: string | null
  name: string | null
  role: string
  status: string
  joined_at: string | null
}
export interface OrgRole {
  id: string
  name: string
  description: string | null
  permissions: string[]
  is_system_role: boolean
}
export interface ApiKeyRow {
  name: string
  description: string | null
  created_at: string | null
  expires_at: string | null
}
export interface AuditEntry {
  id: string
  user_id: string
  action: string
  resource_type: string
  resource_id: string | null
  status: 'success' | 'failure'
  error_message: string | null
  created_at: string | null
}

/** Loads one GET and exposes reload. `path` null means nothing to load yet. */
function useGet<T>(path: string | null, pick: (raw: any) => T, empty: T) {
  const [data, setData] = useState<T>(empty)
  const [loading, setLoading] = useState(Boolean(path))
  const [error, setError] = useState<string | null>(null)

  const reload = useCallback(async () => {
    if (!path) return
    setLoading(true)
    const res: ApiResponse<unknown> = await apiClient.get(path)
    setError(res.success ? null : res.error || 'Could not load this')
    if (res.success && res.data) setData(pick(res.data))
    setLoading(false)
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [path])

  useEffect(() => {
    void reload()
  }, [reload])
  return { data, loading, error, reload }
}

const orgPath = (orgId: string | undefined, tail: string) => (orgId ? `/api/v1/organizations/${orgId}/${tail}` : null)
const EMPTY_MEMBERS = [] as OrgMember[]
const EMPTY_ROLES = [] as OrgRole[]
const EMPTY_KEYS = [] as ApiKeyRow[]

export const useMembers = (orgId?: string) => useGet<OrgMember[]>(orgPath(orgId, 'members'), (r) => r.members ?? [], EMPTY_MEMBERS)
export const useRoles = (orgId?: string) => useGet<OrgRole[]>(orgPath(orgId, 'roles'), (r) => r.roles ?? [], EMPTY_ROLES)
export interface PendingInvitation {
  id: string
  email: string
  role: string
  expires_at: string | null
  created_at: string | null
}
const EMPTY_INVITES = [] as PendingInvitation[]
/** Pending invitations; owners and admins only, so pass `enabled` false for anyone else. */
export const useInvitations = (orgId: string | undefined, enabled: boolean) =>
  useGet<PendingInvitation[]>(enabled ? orgPath(orgId, 'invitations') : null, (r) => r.invitations ?? [], EMPTY_INVITES)
export interface OrgDomain { id: string; domain: string; verified_via: string; created_at: string | null }
export interface JoinRequest { id: string; email: string; name: string; message: string | null; created_at: string | null }
const EMPTY_DOMAINS = [] as OrgDomain[]
const EMPTY_JOINS = [] as JoinRequest[]
export const useDomains = (orgId?: string) => useGet<OrgDomain[]>(orgPath(orgId, 'domains'), (r) => r.domains ?? [], EMPTY_DOMAINS)
/** Sign-ups on this org's domains waiting for an owner or admin; pass `enabled` false for anyone else. */
export const useJoinRequests = (orgId: string | undefined, enabled: boolean) =>
  useGet<JoinRequest[]>(enabled ? orgPath(orgId, 'join-requests') : null, (r) => r.requests ?? [], EMPTY_JOINS)
export const useApiKeys = () => useGet<ApiKeyRow[]>('/api/v1/auth/api-keys', (r) => r.api_keys ?? [], EMPTY_KEYS)

/** Pending access requests; platform admins only (the endpoint answers 403 to anyone else). */
export const usePendingAccessRequests = (enabled: boolean) =>
  useGet<{ id: string }[]>(enabled ? '/api/v1/registrations?status_filter=pending' : null, (r) => r.requests ?? [], [])

export const PAGE_SIZE = 25
export function useOrgAuditLog(orgId: string | undefined, page: number) {
  return useGet<{ logs: AuditEntry[]; total: number }>(
    orgPath(orgId, `audit-logs?skip=${page * PAGE_SIZE}&limit=${PAGE_SIZE}`),
    (r) => ({ logs: r.logs ?? [], total: r.total ?? 0 }),
    { logs: [], total: 0 },
  )
}

export const inviteMember = (orgId: string, email: string, role: string) =>
  apiClient.post(`/api/v1/organizations/${orgId}/members/invite`, { email, role })
export const changeMemberRole = (orgId: string, memberId: string, role: string) =>
  apiClient.put(`/api/v1/organizations/${orgId}/members/${memberId}`, { role })
export const removeMember = (orgId: string, memberId: string) =>
  apiClient.delete(`/api/v1/organizations/${orgId}/members/${memberId}`)
export const setMemberStatus = (orgId: string, memberId: string, status: 'active' | 'suspended') =>
  apiClient.put(`/api/v1/organizations/${orgId}/members/${memberId}`, { status })
export const transferOwnership = (orgId: string, memberId: string) =>
  apiClient.post(`/api/v1/organizations/${orgId}/transfer-ownership`, { member_id: memberId })
export const leaveOrganisation = (orgId: string) => apiClient.post(`/api/v1/organizations/${orgId}/leave`, {})
export const addDomain = (orgId: string, domain: string) => apiClient.post(`/api/v1/organizations/${orgId}/domains`, { domain }, { enableRetry: false })
export const removeDomain = (orgId: string, id: string) => apiClient.delete(`/api/v1/organizations/${orgId}/domains/${id}`)
export const approveJoin = (orgId: string, id: string, role: string) =>
  apiClient.post(`/api/v1/organizations/${orgId}/join-requests/${id}/approve`, { role }, { enableRetry: false })
export const denyJoin = (orgId: string, id: string) => apiClient.post(`/api/v1/organizations/${orgId}/join-requests/${id}/deny`, {}, { enableRetry: false })
export const revokeInvitation = (orgId: string, invitationId: string) =>
  apiClient.delete(`/api/v1/organizations/${orgId}/invitations/${invitationId}`)
export const createApiKey = (name: string, description: string) =>
  apiClient.post<{ api_key: string; name: string; expires_at: string | null }>('/api/v1/auth/api-keys', {
    name,
    ...(description ? { description } : {}),
  })
export const deleteApiKey = (name: string) => apiClient.delete(`/api/v1/auth/api-keys/${encodeURIComponent(name)}`)
