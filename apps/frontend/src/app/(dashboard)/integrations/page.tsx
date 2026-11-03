'use client'

import Link from 'next/link'
import { useRouter } from 'next/navigation'
import { useState, type FormEvent } from 'react'
import { useIntegrations, type DiscoveredAsset, type IntegrationKind } from '@/lib/api/hooks/useIntegrations'
import { useSystemContext } from '@/components/workflow/SystemContext'
import { STAGES } from '@/components/layout/AppShell'
import { cn } from '@/lib/utils'

const field =
  'h-9 w-full rounded-[10px] border border-[rgba(21,23,26,.14)] bg-white px-3 text-[13.5px] outline-none focus:border-[var(--fm-ink)]'
const label = 'block text-[12px] font-medium text-[var(--fm-ink2)]'
const KIND_LABEL: Record<DiscoveredAsset['kind'], string> = {
  ml_model: 'ML model',
  llm_app: 'LLM application',
  ai_assisted_dev: 'AI-assisted development',
}
const KIND_NAME: Record<IntegrationKind, string> = { mlflow: 'MLflow registry', github: 'GitHub org', huggingface: 'Hugging Face' }
const SOURCE_LABEL: Record<IntegrationKind, string> = { mlflow: 'MLflow', github: 'GitHub', huggingface: 'Hugging Face' }
const STAGE_LABEL = Object.fromEntries(STAGES.map((s) => [s.key, s.label]))

function when(iso: string | null) {
  return iso ? new Date(iso).toLocaleString('en-GB', { day: 'numeric', month: 'short', hour: '2-digit', minute: '2-digit' }) : 'never'
}

function AddConnector({ onCreate }: { onCreate: (b: { kind: IntegrationKind; name: string; config: Record<string, unknown>; token?: string }) => Promise<void> }) {
  const [kind, setKind] = useState<IntegrationKind>('mlflow')
  const [busy, setBusy] = useState(false)
  const [err, setErr] = useState<string | null>(null)

  async function submit(e: FormEvent<HTMLFormElement>) {
    e.preventDefault()
    const form = e.currentTarget
    const f = new FormData(form)
    const v = (k: string) => String(f.get(k) ?? '').trim()
    setBusy(true)
    setErr(null)
    try {
      await onCreate({
        kind,
        name: v('name'),
        config:
          kind === 'mlflow'
            ? { tracking_uri: v('tracking_uri') }
            : kind === 'github'
              ? { owner: v('owner'), repos: v('repos') }
              : { owner: v('owner'), name_contains: v('name_contains'), pipeline_tag: v('pipeline_tag'), library: v('library') },
        token: v('token') || undefined,
      })
      form.reset()
    } catch (x) {
      setErr(x instanceof Error ? x.message : 'Could not add connector')
    } finally {
      setBusy(false)
    }
  }

  return (
    <form onSubmit={submit} className="grid gap-3 border-t border-[var(--fm-line)] pt-4">
      <div className="flex gap-1 rounded-full bg-[var(--fm-bg)] p-1 text-[12.5px] font-medium">
        {(Object.keys(KIND_NAME) as IntegrationKind[]).map((k) => (
          <button
            key={k}
            type="button"
            onClick={() => setKind(k)}
            className={cn('h-7 flex-1 rounded-full text-[var(--fm-ink2)]', kind === k && 'bg-[var(--fm-ink)] text-white')}
          >
            {KIND_NAME[k]}
          </button>
        ))}
      </div>
      <div>
        <label className={label} htmlFor="name">Name</label>
        <input id="name" name="name" required className={field} autoComplete="off" />
      </div>
      {kind === 'mlflow' ? (
        <div>
          <label className={label} htmlFor="tracking_uri">Tracking URI</label>
          <input id="tracking_uri" name="tracking_uri" required className={field} inputMode="url" autoComplete="off" />
        </div>
      ) : kind === 'huggingface' ? (
        <>
          <div>
            <label className={label} htmlFor="owner">User or organisation on the Hub</label>
            <input id="owner" name="owner" required className={field} autoComplete="off" />
          </div>
          <div>
            <label className={label} htmlFor="name_contains">Name contains (optional)</label>
            <input id="name_contains" name="name_contains" className={field} autoComplete="off" />
          </div>
          <div className="grid grid-cols-2 gap-2">
            <div>
              <label className={label} htmlFor="pipeline_tag">Pipeline tag (optional)</label>
              <input id="pipeline_tag" name="pipeline_tag" className={field} autoComplete="off" />
            </div>
            <div>
              <label className={label} htmlFor="library">Library (optional)</label>
              <input id="library" name="library" className={field} autoComplete="off" />
            </div>
          </div>
        </>
      ) : (
        <>
          <div>
            <label className={label} htmlFor="owner">Organisation or user</label>
            <input id="owner" name="owner" required className={field} autoComplete="off" />
          </div>
          <div>
            <label className={label} htmlFor="repos">Only these repos (optional, comma-separated)</label>
            <input id="repos" name="repos" className={field} autoComplete="off" />
          </div>
        </>
      )}
      <div>
        <label className={label} htmlFor="token">{kind === 'github'
            ? 'Token (optional; without one, public repos only, 12 per sync)'
            : kind === 'huggingface'
              ? 'Token (optional; without one, public models only, 12 per sync)'
              : 'Token (optional)'}</label>
        <input id="token" name="token" type="password" className={field} autoComplete="off" />
      </div>
      {err && <p className="rounded-[10px] bg-[#fde9ea] px-3 py-2 text-[12.5px] text-[#b4232c]">{err}</p>}
      <button type="submit" disabled={busy} className="h-9 rounded-full bg-[var(--fm-ink)] text-[13px] font-semibold text-white disabled:opacity-60">
        {busy ? 'Adding' : 'Add connector'}
      </button>
    </form>
  )
}

function AssetRow({ a, onPromote, onIgnore }: { a: DiscoveredAsset; onPromote: (body: Record<string, string>) => Promise<void>; onIgnore: () => Promise<void> }) {
  const [tier, setTier] = useState(a.suggestedTier)
  const [stage, setStage] = useState(a.suggestedStage)
  const [line, setLine] = useState<string>(a.metadata.business_line || '')
  const [busy, setBusy] = useState(false)
  const sig = a.metadata.signals as { llm_sdks?: string[]; ml_libraries?: string[]; agent_configs?: string[]; model_files?: string[] } | undefined
  const m = a.metadata
  const detail =
    a.source === 'huggingface'
      ? [
          m.pipeline_tag,
          m.library,
          m.license && `licence ${m.license}`,
          typeof m.downloads === 'number' && `${m.downloads.toLocaleString('en-GB')} downloads`,
          m.last_modified && `updated ${when(m.last_modified)}`,
          m.datasets?.length > 0 && `datasets ${m.datasets.slice(0, 3).join(', ')}`,
          m.languages?.length > 0 && `languages ${m.languages.slice(0, 4).join(', ')}`,
          m.gated && 'gated',
          m.private && 'private',
        ]
          .filter(Boolean)
          .join(' · ')
      : a.source === 'mlflow'
      ? `${(a.metadata.versions?.length ?? 0) as number} version${a.metadata.versions?.length === 1 ? '' : 's'}${a.metadata.description ? ` · ${a.metadata.description}` : ''}`
      : [...(sig?.llm_sdks ?? []), ...(sig?.ml_libraries ?? []), ...(sig?.agent_configs ?? []), ...(sig?.model_files ?? [])].slice(0, 6).join(' · ')

  return (
    <div className="grid gap-3 border-t border-[var(--fm-line)] py-3.5 lg:grid-cols-[minmax(0,1.4fr)_minmax(0,1fr)_auto] lg:items-center">
      <div className="min-w-0">
        <div className="flex items-center gap-2 text-[13.5px] font-semibold">
          <span className="truncate">{a.name}</span>
          <span className="rounded-full bg-[var(--fm-bg)] px-2 py-0.5 text-[11px] font-medium text-[var(--fm-ink2)]">{KIND_LABEL[a.kind]}</span>
        </div>
        <div className="truncate text-[12px] text-[var(--fm-ink2)]">
          {m.url ? (
            <a href={m.url} target="_blank" rel="noreferrer" className="hover:text-[var(--fm-ink)] hover:underline">{SOURCE_LABEL[a.source]}</a>
          ) : (
            SOURCE_LABEL[a.source]
          )}{' '}
          · {a.externalId}
          {detail && ` · ${detail}`}
        </div>
      </div>
      <div className="grid grid-cols-3 gap-2">
        <select aria-label="Risk tier" value={tier} onChange={(e) => setTier(e.target.value as typeof tier)} className={`${field} capitalize`}>
          {['low', 'medium', 'high', 'critical'].map((t) => <option key={t} value={t}>{t}</option>)}
        </select>
        <select aria-label="Lifecycle stage" value={stage} onChange={(e) => setStage(e.target.value as typeof stage)} className={field}>
          {STAGES.map((s) => <option key={s.key} value={s.key}>{s.label}</option>)}
        </select>
        <input aria-label="Business line" placeholder="Business line" value={line} onChange={(e) => setLine(e.target.value)} className={field} />
      </div>
      <div className="flex gap-2">
        <button
          type="button"
          disabled={busy}
          onClick={async () => {
            setBusy(true)
            try {
              await onPromote({ risk_tier: tier, lifecycle_stage: stage, business_line: line })
            } finally {
              setBusy(false)
            }
          }}
          className="h-9 rounded-full bg-[var(--fm-ink)] px-4 text-[12.5px] font-semibold text-white disabled:opacity-60"
        >
          Govern
        </button>
        <button type="button" disabled={busy} onClick={onIgnore} className="h-9 rounded-full border border-[var(--fm-line)] bg-white px-3 text-[12.5px] font-medium text-[var(--fm-ink2)]">
          Ignore
        </button>
      </div>
    </div>
  )
}

export default function IntegrationsPage() {
  const { integrations, discovered, loading, error, create, remove, sync, promote, ignore } = useIntegrations()
  const { refreshSystems, setSelectedSystemId } = useSystemContext()
  const router = useRouter()
  const [syncing, setSyncing] = useState<string | null>(null)
  const [syncErr, setSyncErr] = useState<string | null>(null)

  return (
    <div className="grid gap-4">
      <div>
        <div className="text-[12.5px] font-medium text-[var(--fm-ink2)]">
          <Link href="/dashboard" className="hover:text-[var(--fm-ink)]">Today</Link> · Integrations
        </div>
        <h1 className="mt-1.5 text-[30px] font-semibold leading-[1.1] tracking-[-.03em]">Integrations</h1>
        <p className="mt-2 max-w-[640px] text-[15px] text-[var(--fm-ink2)]">
          Connect where your models and AI code already live. Each sync lists what it finds; rules suggest a tier and stage; you decide what enters governance.
          Prefer to type one in? <Link href="/onboard" className="font-medium text-[var(--fm-ink)] underline-offset-2 hover:underline">Register manually</Link>.
        </p>
      </div>

      <div className="grid gap-4 xl:grid-cols-[360px_minmax(0,1fr)]">
        <section className="fm-card grid content-start gap-4 p-5" aria-label="Connectors">
          <h2 className="text-[15px] font-semibold">Connectors</h2>
          {integrations.length === 0 && !loading && <p className="text-[13px] text-[var(--fm-ink2)]">None yet. Add one below.</p>}
          {integrations.map((i) => (
            <div key={i.id} className="rounded-[12px] border border-[var(--fm-line)] bg-[var(--fm-bg)] p-3.5">
              <div className="flex items-center justify-between gap-2">
                <div className="min-w-0">
                  <div className="truncate text-[13.5px] font-semibold">{i.name}</div>
                  <div className="truncate text-[12px] text-[var(--fm-ink2)]">
                    {i.kind === 'mlflow'
                      ? String(i.config.tracking_uri ?? '')
                      : `${i.kind === 'github' ? 'github.com' : 'huggingface.co'}/${String(i.config.owner ?? '')}`}
                  </div>
                </div>
                <button
                  type="button"
                  disabled={syncing === i.id}
                  onClick={async () => {
                    setSyncing(i.id)
                    setSyncErr(null)
                    try {
                      await sync(i.id)
                    } catch (e) {
                      setSyncErr(e instanceof Error ? e.message : 'Sync failed')
                    } finally {
                      setSyncing(null)
                    }
                  }}
                  className="h-8 flex-none rounded-full bg-[var(--fm-ink)] px-3.5 text-[12.5px] font-semibold text-white disabled:opacity-60"
                >
                  {syncing === i.id ? 'Syncing' : 'Sync'}
                </button>
              </div>
              <div className="mt-2 flex items-center justify-between text-[11.5px] text-[var(--fm-ink3)]">
                <span>
                  Last sync {when(i.lastSyncedAt)}
                  {i.lastSync?.error ? ` · failed: ${i.lastSync.error}` : i.lastSync && ` · ${i.lastSync.found} found, ${i.lastSync.created} new`}
                </span>
                <button type="button" onClick={() => remove(i.id)} className="hover:text-[var(--fm-ink)]">Remove</button>
              </div>
            </div>
          ))}
          {syncErr && <p className="rounded-[10px] bg-[#fde9ea] px-3 py-2 text-[12.5px] text-[#b4232c]">{syncErr}</p>}
          <AddConnector onCreate={create} />
        </section>

        <section className="fm-card p-5" aria-label="Discovered">
          <div className="flex items-baseline justify-between gap-3">
            <h2 className="text-[15px] font-semibold">Discovered, awaiting review</h2>
            <span className="text-[12.5px] tabular-nums text-[var(--fm-ink2)]">{discovered.length}</span>
          </div>
          <p className="text-[12.5px] text-[var(--fm-ink2)]">Suggestions come from registry stages, tags and dependency signals. Adjust, then Govern.</p>
          {error && <p className="mt-3 rounded-[10px] bg-[#fde9ea] px-3 py-2 text-[12.5px] text-[#b4232c]">{error}</p>}
          <div className="mt-3">
            {discovered.length === 0 && !loading && (
              <p className="border-t border-[var(--fm-line)] pt-4 text-[13px] text-[var(--fm-ink2)]">Nothing waiting. Sync a connector to discover systems.</p>
            )}
            {discovered.map((a) => (
              <AssetRow
                key={a.id}
                a={a}
                onPromote={async (body) => {
                  const out = await promote(a.id, body)
                  await refreshSystems()
                  setSelectedSystemId(out.systemId)
                  router.push(`/systems/${out.systemId}`)
                }}
                onIgnore={() => ignore(a.id)}
              />
            ))}
          </div>
        </section>
      </div>
    </div>
  )
}
