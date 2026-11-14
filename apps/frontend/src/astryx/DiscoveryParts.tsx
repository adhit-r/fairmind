import { SOURCES, type DiscoveredAsset, type Integration, type IntegrationKind } from '@/astryx/data/discovery'

/** A source's tile: its letters in a small square. Dashed when the source is not connected. */
export function SourceMark({ kind, ghost, size }: { kind: IntegrationKind; ghost?: boolean; size?: 'sm' }) {
  const s = SOURCES[kind]
  return (
    <span className={`dv-mark${size ? ` ${size}` : ''}${ghost ? ' ghost' : ''}`} title={s?.label} aria-hidden="true">
      {s?.mark ?? kind.slice(0, 2)}
    </span>
  )
}

/** What a connector reads, from its stored config. */
export function where(i: Integration): string {
  const c = i.config as Record<string, string | undefined>
  switch (i.kind) {
    case 'mlflow':
      return c.tracking_uri ?? ''
    case 'github':
      return `github.com/${c.owner ?? ''}`
    case 'huggingface':
      return `huggingface.co/${c.owner ?? ''}`
    case 'aws':
      return `AWS ${c.regions || 'us-east-1'}`
    case 'azure':
      return `Azure subscriptions ${c.subscription_ids ?? ''}`
    case 'gcp':
      return `Google Cloud ${c.project_id ?? ''} · ${c.locations || 'us-central1'}`
    case 'okta':
      return c.domain ?? ''
    case 'litellm':
      return c.base_url ?? ''
    case 'mcp_registry':
      return c.registry_url ?? ''
    case 'proxy_logs':
      return 'Uploaded log exports; the files are not kept'
    default:
      return `${SOURCES[i.kind]?.label ?? i.kind} organisation`
  }
}

const num = (v: unknown) => (typeof v === 'number' ? v.toLocaleString('en-GB') : null)
const list = (v: unknown) => (Array.isArray(v) && v.length ? v.slice(0, 4).join(', ') : null)

/** What the scan saw in an item, from its stored metadata. */
export function detail(a: DiscoveredAsset): string {
  const m = a.metadata
  if (a.source === 'huggingface') {
    return [m.pipeline_tag, m.library, m.license && `licence ${m.license}`, typeof m.downloads === 'number' && `${m.downloads.toLocaleString('en-GB')} downloads`].filter(Boolean).join(' · ')
  }
  if (a.source === 'mlflow') {
    const n = (m.versions?.length ?? 0) as number
    return `${n} version${n === 1 ? '' : 's'}${m.description ? ` · ${m.description}` : ''}`
  }
  if (a.source === 'github' && a.kind !== 'mcp_server') {
    const sig = m.signals as { llm_sdks?: string[]; ml_libraries?: string[]; agent_configs?: string[]; model_files?: string[]; mcp_servers?: string[] } | undefined
    return [...(sig?.llm_sdks ?? []), ...(sig?.ml_libraries ?? []), ...(sig?.agent_configs ?? []), ...(sig?.model_files ?? []), ...(sig?.mcp_servers ?? []).map((n) => `MCP ${n}`)].slice(0, 6).join(' · ')
  }
  // Newer sources: show the facts that are present, most telling first.
  const parts = [
    m.service && m.service !== a.name ? m.service : m.vendor,
    m.model && `model ${m.model}`,
    list(m.models_last_30_days) && `models ${list(m.models_last_30_days)}`,
    num(m.requests_last_30_days) && `${num(m.requests_last_30_days)} requests in 30 days`,
    num(m.tokens_last_30_days) && `${num(m.tokens_last_30_days)} tokens in 30 days`,
    num(m.requests) && `${num(m.requests)} requests in the log`,
    num(m.distinct_users) && `${num(m.distinct_users)} people`,
    num(m.distinct_users_30_days) && `${num(m.distinct_users_30_days)} people signed in`,
    m.self_consent_only && `${m.users_who_consented} people consented without an admin`,
    num(m.active_users_90_days) && `${num(m.active_users_90_days)} active people in 90 days`,
    num(m.users) && `${num(m.users)} people`,
    m.transport && `${m.transport}${m.url ? ` ${m.url}` : m.command ? ` ${m.command}` : ''}`,
    m.repo && a.kind === 'mcp_server' && `in ${m.repo}`,
    m.project && `project ${m.project}`,
    m.workspace && `workspace ${m.workspace}`,
    m.region,
    m.status,
  ]
  return parts.filter(Boolean).slice(0, 5).join(' · ')
}

