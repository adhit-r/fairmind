'use client'

import { useCallback, useEffect, useState } from 'react'
import { apiClient, type ApiResponse } from '@/lib/api/api-client'
import type { DiscoveredAsset, Integration, IntegrationKind, IntegrationRun, IntegrationStep, RunStep } from '@/lib/api/hooks/useIntegrations'

export type { DiscoveredAsset, Integration, IntegrationKind, IntegrationRun, IntegrationStep, RunStep }

const BASE = '/api/v1/integrations'

/** How each source reads on screen. */
export const KIND_LABEL: Record<string, string> = {
  ml_model: 'Model',
  llm_app: 'LLM app',
  ai_assisted_dev: 'AI-assisted development',
  agent: 'Agent',
  ai_service: 'AI service',
  mcp_server: 'MCP server',
}

export interface SourceField {
  key: string
  label: string
  description?: string
  optional?: boolean
}

/** The places AI shows up in an organisation; each source watches one of them. */
export const LANES = [
  { key: 'code', label: 'Code and models' },
  { key: 'vendor', label: 'AI vendor accounts' },
  { key: 'cloud', label: 'Cloud' },
  { key: 'signin', label: 'Sign-in and workplace' },
  { key: 'traffic', label: 'Gateways and traffic' },
  { key: 'devices', label: 'Laptops' },
  { key: 'mcp', label: 'MCP servers' },
] as const
export type LaneKey = (typeof LANES)[number]['key']

export interface SourceSpec {
  label: string
  /** Two or three letters shown in the source's tile. */
  mark: string
  lane: LaneKey
  /** Read-only access the person grants, as the vendor names it. */
  permissions: string[]
  /** What the connector reads, in one line, shown in the drawer. */
  reads: string
  fields: SourceField[]
  /** Label of the secret, or null when the source takes none (uploads). */
  token: string | null
  tokenOptional?: boolean
  tokenDescription?: string
  /** Sources from one vendor share a card in the catalogue, each shown as one of its connections. */
  vendor?: 'OpenAI' | 'Anthropic'
  /** The connection's name on its vendor's card, e.g. "ChatGPT workspace" or "OpenAI API". */
  connection?: string
  /** The plan this kind stands for on a workspace connection, e.g. "Business or Team". */
  plan?: string
  /** Described by the workspace admin in a form, because the plan has no admin API to read. */
  described?: boolean
  /** Set up on another page instead of in the connect drawer. */
  managedIn?: { href: string; text: string }
}

const SECRET_NOTE = 'Stored encrypted on the server and never shown again.'
const MS_FIELDS: SourceField[] = [
  { key: 'tenant_id', label: 'Tenant ID' },
  { key: 'client_id', label: 'Application (client) ID' },
]

/** Every source FairMind can read, with the settings each one needs. Order is the order in the picker. */
export const SOURCES: Record<IntegrationKind, SourceSpec> = {
  github: {
    label: 'GitHub',
    mark: 'GH',
    lane: 'code',
    permissions: ['Contents: read', 'Metadata: read'],
    reads: 'Repositories that use LLM SDKs or ML libraries, AI coding-agent files and MCP server configs.',
    fields: [
      { key: 'owner', label: 'Organisation or user' },
      { key: 'repos', label: 'Repositories', description: 'Names separated by commas; blank reads them all.', optional: true },
    ],
    token: 'Access token',
    tokenOptional: true,
    tokenDescription: `Not needed for public repositories. ${SECRET_NOTE}`,
  },
  mlflow: {
    label: 'MLflow',
    mark: 'ML',
    lane: 'code',
    permissions: ['Read registered models'],
    reads: 'Registered models, their versions and stages.',
    fields: [{ key: 'tracking_uri', label: 'Tracking server address' }],
    token: 'Access token',
    tokenOptional: true,
    tokenDescription: SECRET_NOTE,
  },
  huggingface: {
    label: 'Hugging Face',
    mark: 'HF',
    lane: 'code',
    permissions: ['Read access token (private models only)'],
    reads: 'Models published by an organisation or user.',
    fields: [
      { key: 'owner', label: 'Organisation or user on Hugging Face' },
      { key: 'name_contains', label: 'Name contains', optional: true },
      { key: 'pipeline_tag', label: 'Pipeline tag', optional: true },
      { key: 'library', label: 'Library', optional: true },
    ],
    token: 'Access token',
    tokenOptional: true,
    tokenDescription: `Not needed for public models. ${SECRET_NOTE}`,
  },
  vllm: {
    label: 'vLLM server',
    mark: 'vL',
    lane: 'code',
    permissions: ['GET /v1/models', 'GET /metrics', 'GET /version'],
    reads: 'The models your own vLLM server serves, what each is built on, and the requests and tokens it has handled.',
    fields: [{ key: 'base_url', label: 'Server address', description: 'The public https address your apps call. A server only on your network needs a gateway or an allowlist for FairMind.' }],
    token: 'API key',
    tokenOptional: true,
    tokenDescription: `Only if the server was started with --api-key. ${SECRET_NOTE}`,
  },
  anthropic: {
    label: 'Anthropic API',
    mark: 'An',
    lane: 'vendor',
    vendor: 'Anthropic',
    connection: 'Claude API',
    permissions: ['Admin API key (read calls only)'],
    reads: 'Every API key in the organisation, the models and tokens each used in 30 days, and Claude Code use.',
    fields: [],
    token: 'Admin API key',
    tokenDescription: `Starts with sk-ant-admin. ${SECRET_NOTE}`,
  },
  claude_enterprise: {
    label: 'Claude Enterprise',
    mark: 'CE',
    lane: 'vendor',
    vendor: 'Anthropic',
    connection: 'Claude workspace',
    plan: 'Enterprise',
    permissions: ['read:compliance_org_data', 'read:compliance_user_data'],
    reads: 'Claude organisations, how many people use them, and shared projects.',
    fields: [],
    token: 'Compliance Access Key',
    tokenDescription: `Created in claude.ai admin settings with organisation and user read scopes. ${SECRET_NOTE}`,
  },
  openai: {
    label: 'OpenAI API',
    mark: 'OA',
    lane: 'vendor',
    vendor: 'OpenAI',
    connection: 'OpenAI API',
    permissions: ['Admin API key (read calls only)'],
    reads: 'Every project API key, its owner, and the models and requests it made in 30 days.',
    fields: [],
    token: 'Admin API key',
    tokenDescription: SECRET_NOTE,
  },
  chatgpt_workspace: {
    label: 'ChatGPT workspace',
    mark: 'GPT',
    lane: 'vendor',
    vendor: 'OpenAI',
    connection: 'ChatGPT workspace',
    plan: 'Business or Team',
    described: true,
    permissions: ['None: OpenAI offers no admin API for Business or Team workspaces'],
    reads: 'Seats, custom GPTs, the apps it can reach and its data settings, as the workspace admin describes them.',
    fields: [],
    token: null,
  },
  claude_team: {
    label: 'Claude Team',
    mark: 'CT',
    lane: 'vendor',
    vendor: 'Anthropic',
    connection: 'Claude workspace',
    plan: 'Team',
    described: true,
    permissions: ['None: the Claude Team plan has no admin API to read'],
    reads: 'Seats, shared projects, the connectors it can reach and its data settings, as the workspace admin describes them.',
    fields: [],
    token: null,
  },
  aws: {
    label: 'AWS',
    mark: 'AWS',
    lane: 'cloud',
    permissions: ['bedrock:List*', 'bedrock-agentcore:ListAgentRuntimes', 'cloudwatch:ListMetrics', 'sagemaker:ListEndpoints', 'sagemaker:ListModelPackageGroups'],
    reads: 'Bedrock models in use, custom models, agents and AgentCore runtimes, and SageMaker endpoints and registries.',
    fields: [
      { key: 'access_key_id', label: 'Access key ID' },
      { key: 'regions', label: 'Regions', description: 'Separated by commas; blank reads us-east-1.', optional: true },
      { key: 'role_arn', label: 'Role to assume', description: 'A read-only role ARN, if the key should assume one.', optional: true },
      { key: 'external_id', label: 'External ID', optional: true },
    ],
    token: 'Secret access key',
    tokenDescription: SECRET_NOTE,
  },
  azure: {
    label: 'Azure',
    mark: 'Az',
    lane: 'cloud',
    permissions: ['Reader role on each subscription'],
    reads: 'Model deployments in Azure OpenAI and AI Foundry, and Machine Learning workspaces.',
    fields: [...MS_FIELDS, { key: 'subscription_ids', label: 'Subscription IDs', description: 'Separated by commas. The app needs the Reader role on each.' }],
    token: 'Client secret',
    tokenDescription: SECRET_NOTE,
  },
  gcp: {
    label: 'Google Cloud',
    mark: 'GC',
    lane: 'cloud',
    permissions: ['roles/aiplatform.viewer'],
    reads: 'Vertex AI models, endpoints and Agent Engine agents.',
    fields: [
      { key: 'project_id', label: 'Project ID' },
      { key: 'locations', label: 'Regions', description: 'Separated by commas; blank reads us-central1.', optional: true },
    ],
    token: 'Service account key (JSON)',
    tokenDescription: `Paste the whole key file. The account needs the Vertex AI Viewer role. ${SECRET_NOTE}`,
  },
  okta: {
    label: 'Okta',
    mark: 'Ok',
    lane: 'signin',
    permissions: ['Read-only admin API token'],
    reads: 'AI services set up for single sign-on, with sign-ins and people in the last 30 days.',
    fields: [{ key: 'domain', label: 'Okta domain', description: 'For example acme.okta.com' }],
    token: 'API token',
    tokenDescription: `A read-only admin token. ${SECRET_NOTE}`,
  },
  entra: {
    label: 'Microsoft Entra ID',
    mark: 'En',
    lane: 'signin',
    permissions: ['Application.Read.All', 'Directory.Read.All'],
    reads: 'AI services among enterprise apps, and how many people consented to them without an admin.',
    fields: MS_FIELDS,
    token: 'Client secret',
    tokenDescription: `The app needs Application.Read.All and Directory.Read.All. ${SECRET_NOTE}`,
  },
  m365_copilot: {
    label: 'Microsoft 365 Copilot',
    mark: 'M365',
    lane: 'signin',
    permissions: ['LicenseAssignment.Read.All', 'Reports.Read.All', 'CopilotPackages.Read.All'],
    reads: 'Copilot licences, active users per app, and Copilot agents in the tenant.',
    fields: MS_FIELDS,
    token: 'Client secret',
    tokenDescription: `The app needs LicenseAssignment.Read.All, Reports.Read.All and CopilotPackages.Read.All. ${SECRET_NOTE}`,
  },
  cursor: {
    label: 'Cursor Business',
    mark: 'CU',
    lane: 'signin',
    permissions: ['Admin API key (Teams or Enterprise plan)'],
    reads: 'Who holds a company Cursor seat and the days each person used it, so personal accounts stand out in Shadow AI.',
    fields: [],
    token: 'Admin API key',
    tokenDescription: SECRET_NOTE,
  },
  github_copilot: {
    label: 'GitHub Copilot seats',
    mark: 'GC',
    lane: 'signin',
    permissions: ['read:org or manage_billing:copilot'],
    reads: 'Copilot seats with last activity. Seats are compared with usage only when GitHub shows their email addresses.',
    fields: [{ key: 'org', label: 'Organisation' }],
    token: 'Access token',
    tokenDescription: SECRET_NOTE,
  },
  chatgpt_enterprise: {
    label: 'ChatGPT Enterprise',
    mark: 'CG',
    lane: 'signin',
    permissions: ['SCIM token from the ChatGPT admin console'],
    reads: 'Workspace members over SCIM, so a personal ChatGPT account stands out in Shadow AI.',
    fields: [{ key: 'scim_url', label: 'SCIM address', description: 'Shown in the ChatGPT admin console next to the SCIM token.' }],
    token: 'SCIM token',
    tokenDescription: SECRET_NOTE,
  },
  jamf: {
    label: 'Jamf Pro',
    mark: 'JF',
    lane: 'devices',
    permissions: ['API client with Read Computers'],
    reads: 'Which AI apps are installed on each Mac, with its serial number and user. Other apps are never stored.',
    fields: [
      { key: 'url', label: 'Jamf Pro address' },
      { key: 'client_id', label: 'API client ID' },
    ],
    token: 'API client secret',
    tokenDescription: SECRET_NOTE,
  },
  intune: {
    label: 'Microsoft Intune',
    mark: 'IN',
    lane: 'devices',
    permissions: ['DeviceManagementManagedDevices.Read.All'],
    reads: 'Which AI apps are installed on each managed device, with its serial number and user. Other apps are never stored.',
    fields: MS_FIELDS,
    token: 'Client secret',
    tokenDescription: `The app needs DeviceManagementManagedDevices.Read.All. ${SECRET_NOTE}`,
  },
  defender: {
    label: 'Defender for Endpoint',
    mark: 'DF',
    lane: 'devices',
    permissions: ['ThreatHunting.Read.All'],
    reads: 'AI apps run in the last 30 days, connections to AI services per laptop and person, and AI browser extensions, through advanced hunting. Edge extensions come from here.',
    fields: MS_FIELDS,
    token: 'Client secret',
    tokenDescription: `The app needs ThreatHunting.Read.All (application). ${SECRET_NOTE}`,
  },
  crowdstrike: {
    label: 'CrowdStrike Falcon',
    mark: 'CS',
    lane: 'devices',
    permissions: ['Assets: Read', 'Hosts: Read'],
    reads: 'AI apps found on each host by Falcon Discover, with the host serial number and last user.',
    fields: [
      { key: 'base_url', label: 'API address', description: 'Your Falcon cloud, for example https://api.us-2.crowdstrike.com. Blank means https://api.crowdstrike.com.', optional: true },
      { key: 'client_id', label: 'API client ID' },
    ],
    token: 'API client secret',
    tokenDescription: SECRET_NOTE,
  },
  fleet: {
    label: 'Fleet (osquery)',
    mark: 'FL',
    lane: 'devices',
    permissions: ['An API-only user with the observer role'],
    reads: 'AI apps and extensions in the software inventory of every host osquery reports, with serial numbers and end users.',
    fields: [{ key: 'url', label: 'Fleet address' }],
    token: 'API token',
    tokenDescription: SECRET_NOTE,
  },
  laptop_script: {
    label: 'Laptop script',
    mark: 'LS',
    lane: 'devices',
    permissions: ['Your device management pushes a read-only script'],
    reads: 'Once a day per laptop: AI apps, editor extensions, MCP server names, and whether each app is signed in with a work or personal account. Never the address.',
    fields: [],
    token: null,
    managedIn: { href: '/shadow-ai?view=laptops', text: 'Set up the laptop script in Shadow AI: choose your company domains, create the token and download the script for macOS or Windows.' },
  },
  chrome: {
    label: 'Chrome Enterprise',
    mark: 'CH',
    lane: 'devices',
    permissions: ['chrome.management.reports.readonly', 'admin.directory.device.chromebrowsers.readonly'],
    reads: 'AI extensions in managed Chrome browsers, per device, with serial numbers and users from the directory.',
    fields: [{ key: 'admin_email', label: 'Admin email', description: 'A Workspace admin the service account acts as, through domain-wide delegation.' }],
    token: 'Service account key (JSON)',
    tokenDescription: `Grant the two read-only scopes to the service account under domain-wide delegation. ${SECRET_NOTE}`,
  },
  litellm: {
    label: 'LiteLLM gateway',
    mark: 'LL',
    lane: 'traffic',
    permissions: ['Master key or an admin key'],
    reads: 'Every virtual key routed through the gateway, with its team, models and spend.',
    fields: [{ key: 'base_url', label: 'Gateway address' }],
    token: 'Master key',
    tokenDescription: SECRET_NOTE,
  },
  proxy_logs: {
    label: 'Proxy or firewall logs',
    mark: 'Log',
    lane: 'traffic',
    permissions: ['A log export that names the destination host'],
    reads: 'Traffic to known AI services in an uploaded log export (CSV, JSON lines or plain text). The file is not kept.',
    fields: [],
    token: null,
  },
  mcp_registry: {
    label: 'MCP registry',
    mark: 'MCP',
    lane: 'mcp',
    permissions: ['Read access, if the registry is private'],
    reads: 'MCP servers approved in a registry that follows the MCP Registry API.',
    fields: [
      { key: 'registry_url', label: 'Registry address' },
      { key: 'search', label: 'Name contains', optional: true },
    ],
    token: 'Access token',
    tokenOptional: true,
    tokenDescription: SECRET_NOTE,
  },
}

export const SOURCE_LABEL: Record<string, string> = Object.fromEntries(Object.entries(SOURCES).map(([k, s]) => [k, s.label]))
export const MAX_LOG_BYTES = 20 * 1024 * 1024

export const SCHEDULES = [
  { minutes: 0, label: 'Manual' },
  { minutes: 60, label: 'Hourly' },
  { minutes: 360, label: 'Every 6 hours' },
  { minutes: 1440, label: 'Daily' },
] as const

export type Health = 'live' | 'overdue' | 'failing' | 'manual' | 'waiting' | 'upload'
export const HEALTH_LABEL: Record<Health, string> = {
  live: 'Live',
  overdue: 'Overdue',
  failing: 'Failing',
  manual: 'Manual',
  waiting: 'Waiting for first read',
  upload: 'Reads uploads',
}

/** Whether a connector is watching as planned, from its schedule and its last run. */
export function healthOf(i: Integration, now = Date.now()): Health {
  const last = i.recentRuns?.[0]
  if (last?.status === 'failed') return 'failing'
  if (i.kind === 'proxy_logs') return 'upload'
  // Sources read before run history was kept have lastSyncedAt but no runs.
  if (!i.scheduleMinutes) return last || i.lastSyncedAt ? 'manual' : 'waiting'
  if (!i.lastSyncedAt) return 'waiting'
  // The server checks for due schedules every few minutes; allow that much before calling it late.
  const late = i.nextSyncAt ? now - new Date(i.nextSyncAt).getTime() > 15 * 60 * 1000 : false
  return late ? 'overdue' : 'live'
}

export function ago(iso: string | null | undefined, now = Date.now()): string {
  if (!iso) return 'never'
  const s = Math.round((now - new Date(iso).getTime()) / 1000)
  if (s < 60) return 'just now'
  if (s < 3600) return `${Math.round(s / 60)} min ago`
  if (s < 86400) return `${Math.round(s / 3600)} h ago`
  return `${Math.round(s / 86400)} d ago`
}

export function until(iso: string | null | undefined, now = Date.now()): string {
  if (!iso) return ''
  const s = Math.round((new Date(iso).getTime() - now) / 1000)
  if (s <= 60) return 'due now'
  if (s < 3600) return `in ${Math.round(s / 60)} min`
  if (s < 86400) return `in ${Math.round(s / 3600)} h`
  return `in ${Math.round(s / 86400)} d`
}

export interface Preview {
  found: number
  byKind: Record<string, number>
  sample: { name: string; kind: string; tier: string }[]
}

type NewIntegration = { kind: IntegrationKind; name: string; config: Record<string, unknown>; token?: string }

/** Read a source with the given access without saving anything. */
export async function previewSource(body: NewIntegration): Promise<Preview> {
  return unwrap(await apiClient.post<Preview>(`${BASE}/preview`, body))
}

/** Create a connector and return it, without reloading any list (the connect page navigates away). */
export async function createSource(body: NewIntegration): Promise<Integration> {
  return unwrap(await apiClient.post<Integration>(BASE, body))
}

export async function syncSource(id: string) {
  return unwrap(await apiClient.post<Integration['lastSync']>(`${BASE}/${id}/sync`, {}))
}

export async function uploadLogs(id: string, text: string) {
  return unwrap(await apiClient.post<Integration['lastSync']>(`${BASE}/${id}/upload`, { text }))
}

function unwrap<T>(res: ApiResponse<T>): T {
  if (res.success && res.data !== undefined) return res.data
  throw new Error(res.error || 'Request failed')
}

/** Connectors and every discovered item (new, promoted and ignored), with the write actions. */
export function useDiscovery() {
  const [integrations, setIntegrations] = useState<Integration[]>([])
  const [discovered, setDiscovered] = useState<DiscoveredAsset[]>([])
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)

  const refresh = useCallback(async () => {
    try {
      const [i, d] = await Promise.all([
        apiClient.get<Integration[]>(BASE),
        apiClient.get<DiscoveredAsset[]>(`${BASE}/discovered?status=all`),
      ])
      setIntegrations(unwrap(i))
      setDiscovered(unwrap(d))
      setError(null)
    } catch (e) {
      setError(e instanceof Error ? e.message : 'Could not load discovery')
    } finally {
      setLoading(false)
    }
  }, [])

  useEffect(() => {
    void refresh()
  }, [refresh])

  const setSchedule = async (id: string, minutes: number) => {
    unwrap(await apiClient.patch<Integration>(`${BASE}/${id}`, { schedule_minutes: minutes }))
    await refresh()
  }
  /** Which steps of a source are not read. Saves one source; the caller refreshes once after a batch. */
  const setScope = async (id: string, disabledSteps: string[]) => {
    unwrap(await apiClient.patch<Integration>(`${BASE}/${id}`, { disabled_steps: disabledSteps }))
  }
  const create = async (body: NewIntegration) => {
    unwrap(await apiClient.post<Integration>(BASE, body))
    await refresh()
  }
  const remove = async (id: string) => {
    // 204 has no body, so data is undefined on success: check success, not data.
    const res = await apiClient.delete<null>(`${BASE}/${id}`)
    if (!res.success) throw new Error(res.error || 'The source could not be removed')
    await refresh()
  }
  const sync = async (id: string) => {
    try {
      return await syncSource(id)
    } finally {
      await refresh()
    }
  }
  const promote = async (id: string) => {
    const out = unwrap(await apiClient.post<{ systemId: string }>(`${BASE}/discovered/${id}/promote`, {}))
    await refresh()
    return out
  }
  const upload = async (id: string, text: string) => {
    try {
      return await uploadLogs(id, text)
    } finally {
      await refresh()
    }
  }
  const ignore = async (id: string) => {
    unwrap(await apiClient.post<{ status: string }>(`${BASE}/discovered/${id}/ignore`, {}))
    await refresh()
  }

  return { integrations, discovered, loading, error, refresh, create, remove, sync, upload, setSchedule, setScope, promote, ignore }
}

export function when(iso: string | null | undefined): string {
  return iso ? new Date(iso).toLocaleString('en-GB', { day: 'numeric', month: 'short', hour: '2-digit', minute: '2-digit' }) : 'never'
}
