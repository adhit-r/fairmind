'use client'

import { createContext, useCallback, useContext, useEffect, useState } from 'react'
import { apiClient, type ApiResponse } from '@/lib/api/api-client'
import { useOrgResource, withOrg } from '@/lib/api/hooks/usePacks'
import type { DiscoveredAsset, IntegrationKind } from '@/lib/api/hooks/useIntegrations'

function unwrap<T>(res: ApiResponse<T>): T {
  if (res.success && res.data !== undefined) return res.data
  throw new Error(res.error || 'Request failed')
}

/* ------------------------------------------------------------------ Discovery review */

export type Strength = 'strong' | 'fair' | 'single'
export type Tier = 'low' | 'medium' | 'high' | 'critical'

export interface OwnerCheck {
  email: string
  sentAt: string
  expiresAt: string
  answeredAt: string | null
}

export interface OwnerAnswers {
  own: 'yes' | 'someone_else' | 'unknown'
  other_owner?: string | null
  purpose: string
  users: string
  data_in: string
  personal_data: boolean | null
  acts_without_person: boolean | null
  moves_money: boolean | null
  decides_about_people: boolean | null
  tools_allowed: string[] | null
  never_do: string
}

export interface ReachFact {
  key: string
  label: string
  value: 'yes' | 'no' | 'unknown'
  detail: string
  by: 'owner' | 'source' | null
}

export interface Candidate {
  id: string
  name: string
  kind: string
  strength: Strength
  sources: IntegrationKind[]
  sightings: number
  firstSeen: string
  lastSeen: string
  suggestedTier: Tier
  ownerCheck: OwnerCheck | null
  owners: { email: string; reasons: string[] }[]
}

export interface CandidateDetail extends Candidate {
  members: DiscoveredAsset[]
  checks: { type: 'name' | 'service' | 'repo' | 'person'; label: string; sources: IntegrationKind[] }[]
  reach: ReachFact[]
  tierReasons: string[]
  frameworks: string[]
  answers: OwnerAnswers | null
  mismatches: string[]
  tools: string[]
}

const D = '/api/v1/discovery'

function isCandidate(c: Candidate | null): c is Candidate {
  return !!c && typeof c.id === 'string' && !!c.id && typeof c.name === 'string' &&
    Number.isInteger(c.sightings) && c.sightings > 0 && ['low', 'medium', 'high', 'critical'].includes(c.suggestedTier) &&
    Array.isArray(c.sources) && Array.isArray(c.owners)
}

/** The navigation badge and the Discovery queue share one read of the merged candidates. */
export function useCandidateQueue() {
  const { data, loading, error, reload } = useOrgResource<Candidate[]>(`${D}/candidates`)
  const candidates = Array.isArray(data) && data.every(isCandidate) ? data : null
  return {
    candidates: error ? [] : candidates ?? [], loading, refresh: reload,
    error: error || (!loading && !candidates ? 'The candidate list was incomplete.' : null),
  }
}

export const CandidateQueueContext = createContext<ReturnType<typeof useCandidateQueue> | null>(null)

export function useCandidates() {
  const queue = useContext(CandidateQueueContext)
  if (!queue) throw new Error('Discovery requires the candidate queue from the dashboard.')
  return queue
}

export function useCandidate(id: string | null) {
  const { data, loading, error, errorStatus, reload } = useOrgResource<CandidateDetail>(id ? `${D}/candidates/${encodeURIComponent(id)}` : null)
  // A merged candidate may also be opened by one of its member sighting IDs.
  const matches = isCandidate(data) && Array.isArray(data.members) && data.members.length > 0 &&
    data.members.every((member) => member && typeof member.id === 'string') && (data.id === id || data.members.some((member) => member.id === id)) &&
    Array.isArray(data.checks) && Array.isArray(data.reach) && Array.isArray(data.tierReasons) && Array.isArray(data.frameworks) &&
    Array.isArray(data.mismatches) && Array.isArray(data.tools)
  return {
    detail: !error && matches ? data : null, loading, notFound: errorStatus === 404,
    error: error || (id && !loading && !matches ? 'The requested candidate and its sightings could not be verified.' : null), refresh: reload,
  }
}

function discoveryAction(path: string, orgId: string | null) {
  if (!orgId) throw new Error('Choose an organisation to review this candidate.')
  return withOrg(`${D}/${path}`, orgId)
}

export async function askOwner(id: string, email: string, orgId: string | null) {
  return unwrap(await apiClient.post<{ link: string; expiresAt: string; emailSent: boolean }>(discoveryAction(`candidates/${encodeURIComponent(id)}/ask`, orgId), { email }))
}

export interface Decision {
  decision: 'approve' | 'conditions' | 'retire'
  conditions: string[]
  review_days: 30 | 90 | 180
  risk_tier?: Tier
  owner?: string
}

export async function decide(id: string, body: Decision, orgId: string | null) {
  return unwrap(await apiClient.post<{ decision: string; systemId: string | null }>(discoveryAction(`candidates/${encodeURIComponent(id)}/decide`, orgId), body))
}

export async function ignoreCandidate(id: string, orgId: string | null) {
  return unwrap(await apiClient.post<{ status: string }>(discoveryAction(`candidates/${encodeURIComponent(id)}/ignore`, orgId), {}))
}

export async function splitSighting(assetId: string, orgId: string | null) {
  return unwrap(await apiClient.post<{ split: string }>(discoveryAction(`assets/${encodeURIComponent(assetId)}/split`, orgId), {}))
}

/* ------------------------------------------------------------------ Shadow AI */

export type FindingType = 'personal_account' | 'leaver_key' | 'leaver_seat' | 'gateway_bypass' | 'not_allowed' | 'self_consent' | 'unregistered_mcp'
export type Confidence = 'possible' | 'likely' | 'confirmed'

export interface Finding {
  key: string
  type: FindingType
  title: string
  severity: 'critical' | 'high' | 'medium'
  confidence: Confidence
  subject: string
  evidence: { source: IntegrationKind; title: string; detail: string }[]
  verdict: string
  confirm?: string
  service?: string | null
  person?: string | null
  team?: string
  status: 'open' | 'expected'
  reason: string | null
  firstSeen: string
  lastSeen: string
  nudgedAt: string | null
}

export type Stance = 'approved' | 'limited' | 'not_allowed' | 'not_reviewed'

export interface ShadowAI {
  findings: Finding[]
  resolved: { key: string; firstSeen: string; lastSeen: string }[]
  stories: Story[]
  map: {
    tools: { key: string; label: string; status: Stance; teams: string[] }[]
    teams: string[]
    cells: Record<string, Record<string, { company: number; personal: number; unapproved: number }>>
  }
  coverage: { proxyLogs: boolean; okta: boolean; entra: boolean; gateway: boolean; mcpRegistry: boolean; people: number; approvedTools: number; ssoTools: number; seatLists: string[]; laptops: number; sourceKinds: string[]; laptopScript?: boolean; browsers?: number }
}

export interface ToolStance {
  key: string
  label: string
  vendor: string
  category: string
  stance: { status: Exclude<Stance, 'not_reviewed'>; teams: string[]; sso_required: boolean; note: string | null; updatedAt: string; tenantIds?: string[] } | null
}

const S = '/api/v1/shadow-ai'

export function useShadowAI() {
  const [data, setData] = useState<ShadowAI | null>(null)
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)
  const refresh = useCallback(async () => {
    try {
      setData(unwrap(await apiClient.get<ShadowAI>(S)))
      setError(null)
    } catch (e) {
      setError(e instanceof Error ? e.message : 'Could not load Shadow AI')
    } finally {
      setLoading(false)
    }
  }, [])
  useEffect(() => {
    void refresh()
  }, [refresh])
  return { data, loading, error, refresh }
}

export async function listTools() {
  return unwrap(await apiClient.get<ToolStance[]>(`${S}/tools`))
}

export async function setToolStance(key: string, body: { status: Exclude<Stance, 'not_reviewed'> | null; teams: string[]; sso_required: boolean; tenant_ids?: string[] }) {
  return unwrap(await apiClient.put<{ key: string }>(`${S}/tools/${encodeURIComponent(key)}`, body))
}

export async function markExpected(key: string, reason: string) {
  return unwrap(await apiClient.post<{ status: string }>(`${S}/findings/expected`, { key, reason }))
}

export async function reopenFinding(key: string) {
  return unwrap(await apiClient.post<{ status: string }>(`${S}/findings/reopen`, { key }))
}

export async function nudgePerson(key: string, message: string) {
  return unwrap(await apiClient.post<{ sentTo: string }>(`${S}/findings/nudge`, { key, message }))
}

export interface EvidenceRow {
  service: string
  label: string
  vendor: string
  stance: Stance
  onLaptop: { laptops: string[]; sources: string[]; kinds: string[]; versions: string[] } | null
  traffic: { requests: number; sources: string[] } | null
  seat: { status: 'held' | 'none' | 'unknown'; source: string } | null
  signedIn?: { class: 'work' | 'personal'; laptops: string[]; browsers?: string[] } | null
}

export interface Evidence {
  person: string | null
  team: string | null
  laptops: { id: string; name: string; serial: string | null; sources: string[] }[]
  people: string[]
  rows: EvidenceRow[]
  models?: EdgeModel[]
}

export interface LaptopSummary {
  id: string
  name: string
  serial: string | null
  people: string[]
  team: string
  sources: string[]
  tools: { service: string; label: string; stance: Stance }[]
  flagged: number
  models?: number
}

/** Every AI tool for one person or one laptop, by kind of evidence. */
export function useEvidence(person: string | null, laptop: string | null) {
  const [data, setData] = useState<Evidence | null>(null)
  const [error, setError] = useState<string | null>(null)
  useEffect(() => {
    if (!person && !laptop) return
    let cancelled = false
    const q = person ? `person=${encodeURIComponent(person)}` : `laptop=${encodeURIComponent(laptop ?? '')}`
    apiClient
      .get<Evidence>(`${S}/evidence?${q}`)
      .then((res) => {
        if (cancelled) return
        setData(unwrap(res))
        setError(null)
      })
      .catch((e) => !cancelled && setError(e instanceof Error ? e.message : 'Could not load the evidence'))
    return () => {
      cancelled = true
    }
  }, [person, laptop])
  return { data, error }
}

export function useLaptops(query: string) {
  const [data, setData] = useState<{ total: number; laptops: LaptopSummary[] } | null>(null)
  const [error, setError] = useState<string | null>(null)
  useEffect(() => {
    let cancelled = false
    const t = setTimeout(() => {
      apiClient
        .get<{ total: number; laptops: LaptopSummary[] }>(`${S}/laptops?q=${encodeURIComponent(query)}`)
        .then((res) => {
          if (cancelled) return
          setData(unwrap(res))
          setError(null)
        })
        .catch((e) => !cancelled && setError(e instanceof Error ? e.message : 'Could not load laptops'))
    }, 250)
    return () => {
      cancelled = true
      clearTimeout(t)
    }
  }, [query])
  return { data, error }
}

export interface Story {
  key: string
  service: string
  team: string
  title: string
  summary: string
  findingKeys: string[]
}

export interface Cited {
  text: string
  cites: number[]
}

/** FairMind's reading of a finding or story: the organisation's model explains the evidence and cites it. */
export interface Reading {
  paragraphs: Cited[]
  next_step: Cited | null
  nudge: string
  model: string | null
  createdAt: string
  stale: boolean
  evidence: { id: number; title: string; detail: string; source: string }[]
}

export async function getReading(key: string) {
  return unwrap(await apiClient.get<{ reading: Reading | null; modelConnected: boolean }>(`${S}/reading?key=${encodeURIComponent(key)}`))
}

export async function writeReading(key: string) {
  return unwrap(await apiClient.post<{ reading: Reading; modelConnected: boolean }>(`${S}/reading`, { key }))
}

export interface ScriptStatus {
  connected: boolean
  domains: string[]
  hasToken: boolean
  laptops: number
  lastReportAt: string | null
}

export async function getScriptStatus() {
  return unwrap(await apiClient.get<ScriptStatus>(`${S}/laptop-script`))
}

export async function setScriptDomains(domains: string) {
  return unwrap(await apiClient.put<ScriptStatus>(`${S}/laptop-script`, { domains }))
}

export async function newScriptToken() {
  return unwrap(await apiClient.post<{ token: string }>(`${S}/laptop-script/token`, {}))
}

export async function downloadScript(os: 'macos' | 'windows') {
  return unwrap(await apiClient.get<{ filename: string; script: string }>(`${S}/laptop-script/download?os=${os}`))
}

export interface TenantRules {
  rules: { service: string; label: string; header: string; value: string; hosts: string[] }[]
  missing: { service: string; label: string; where: string }[]
}

export async function getTenantRules() {
  return unwrap(await apiClient.get<TenantRules>(`${S}/tenant-rules`))
}

export interface EdgeModel {
  runtime: 'ollama' | 'lm_studio' | 'huggingface'
  name: string
  size: number
  laptop: string
  source: string
}

export interface AgentStatus {
  connected: boolean
  hasSecret: boolean
  laptops: number
  quiet: { name: string; lastSeen: string }[]
  problems: { name: string; problem: string }[]
  events: AgentEvent[]
  rules: Record<AgentRule, AgentAction>
  domains: string[]
  notifiers: number
  hasNotifierSecret: boolean
}

export type AgentRule = 'personal_account' | 'not_allowed_app' | 'unregistered_mcp' | 'model_added'
export type AgentAction = 'log' | 'tell_you' | 'tell_person' | 'tell_both'

export interface AgentEvent {
  laptop: string
  kind: 'app_started' | 'account' | 'mcp_started' | 'model_added'
  service: string | null
  user?: string | null
  app?: string
  server?: string
  name?: string
  rule?: AgentRule | null
  action?: AgentAction
  forPerson?: string
  shownAt?: string | null
  at: string
}

export async function setAgentRules(rules: Partial<Record<AgentRule, AgentAction>>) {
  return unwrap(await apiClient.put<AgentStatus>(`${S}/agent/rules`, { rules }))
}

export async function getAgent() {
  return unwrap(await apiClient.get<AgentStatus>(`${S}/agent`))
}

export async function createAgent() {
  return unwrap(await apiClient.put<AgentStatus>(`${S}/agent`, {}))
}

export async function newAgentSecret() {
  return unwrap(await apiClient.post<{ secret: string }>(`${S}/agent/secret`, {}))
}

export async function agentSettings(os: 'macos' | 'windows') {
  return unwrap(await apiClient.get<{ filename: string; flags: string }>(`${S}/agent/settings?os=${os}`))
}

export async function newNotifierSecret() {
  return unwrap(await apiClient.post<{ secret: string; config: string }>(`${S}/agent/notifier-secret`, {}))
}

/** The browser extension: whether it can be set up, browsers reporting, and the banner on AI sites. */
export type BrowserStatus = { ready: boolean; hasToken: boolean; banner: boolean; domains: string[]; browsers: number; lastReportAt: string | null }
export type BrowserSettings = { token: string; policy: Record<string, unknown>; googleAdmin: Record<string, unknown> }

export async function getBrowserStatus() {
  return unwrap(await apiClient.get<BrowserStatus>(`${S}/browser-extension`))
}

export async function setBrowserBanner(banner: boolean) {
  return unwrap(await apiClient.put<BrowserStatus>(`${S}/browser-extension`, { banner }))
}

export async function newBrowserSettings() {
  return unwrap(await apiClient.post<BrowserSettings>(`${S}/browser-extension/token`, {}))
}
