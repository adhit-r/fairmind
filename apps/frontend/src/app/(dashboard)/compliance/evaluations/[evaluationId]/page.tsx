'use client'

import Link from 'next/link'
import { useParams } from 'next/navigation'
import { useEffect, useMemo, useRef, useState, type ReactNode } from 'react'
import {
  useAIProvider,
  useEngine,
  useEngineRun,
  useEngineRuns,
  useEvaluation,
  usePackActions,
  useSystemTarget,
  usePlatformConnections,
  type EngineRun,
  type EngineSpec,
  type EvaluationJob,
} from '@/lib/api/hooks/usePacks'
import { useSystemContext } from '@/components/workflow/SystemContext'
import { BTN_P, Crumbs, EnginePill, ErrorNote, Heading, LABEL, Loading, MUTED, Pill, ResultPill, when } from '@/components/packs/parts'

const FIELD = 'w-full rounded-[10px] border border-[var(--fm-line)] bg-white px-3 py-2 text-sm text-[var(--fm-ink)] focus:border-[var(--fm-ink)] focus:outline-none'
const ACCEPT: Record<string, string> = { csv: '.csv,text/csv', text: '.txt,.md,.env,.yaml,.yml,.json,.log,text/plain', json: '.json,application/json', binary: '' }

const ACRONYMS: Record<string, string> = { psi: 'PSI', ks: 'KS', auc: 'AUC', auroc: 'AUROC', ece: 'ECE', id: 'ID', f1: 'F1', mae: 'MAE', rmse: 'RMSE', r2: 'R2', fpr: 'FPR', tpr: 'TPR', url: 'URL' }

/** "datasetDrift" -> "Dataset drift", "maxPsi" -> "Max PSI" */
const label = (key: string) =>
  key
    .replace(/([a-z0-9])([A-Z])/g, '$1 $2')
    .replace(/_/g, ' ')
    .split(' ')
    .map((w, i) => ACRONYMS[w.toLowerCase()] ?? (i === 0 ? w.charAt(0).toUpperCase() + w.slice(1) : w.toLowerCase()))
    .join(' ')

function show(value: unknown): string {
  if (value === null || value === undefined || value === '') return '-'
  if (typeof value === 'boolean') return value ? 'Yes' : 'No'
  if (typeof value === 'number') return Number.isInteger(value) ? value.toLocaleString() : String(Number(value.toPrecision(4)))
  if (typeof value === 'object') return JSON.stringify(value)
  return String(value)
}

function DetailTable({ rows }: { rows: Array<Record<string, unknown>> }) {
  const keys = useMemo(() => {
    const seen = new Set<string>()
    for (const row of rows) Object.keys(row).forEach((k) => k !== 'kind' && seen.add(k))
    return [...seen]
  }, [rows])
  return (
    <div className="overflow-x-auto">
      <table className="w-full border-collapse text-left text-[12.5px]">
        <thead>
          <tr className={MUTED}>
            {keys.map((k) => (
              <th key={k} scope="col" className="whitespace-nowrap py-1.5 pr-3 font-semibold">{label(k)}</th>
            ))}
          </tr>
        </thead>
        <tbody>
          {rows.map((row, i) => (
            <tr key={i} className="border-t border-[#15171a14] align-top">
              {keys.map((k) => (
                <td key={k} className="max-w-[280px] break-words py-1.5 pr-3 tabular-nums">{show(row[k])}</td>
              ))}
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  )
}

function RunResult({ run }: { run: EngineRun }) {
  // Engines that report more than one kind of row (features and samples, say) get a table per kind.
  const groups = useMemo(() => {
    const out = new Map<string, Array<Record<string, unknown>>>()
    for (const row of run.detail ?? []) {
      const kind = typeof row.kind === 'string' ? row.kind : ''
      out.set(kind, [...(out.get(kind) ?? []), row])
    }
    return [...out.entries()]
  }, [run.detail])
  return (
    <div className="flex flex-col gap-4">
      <div className="flex flex-wrap items-center gap-2.5">
        <ResultPill status={run.status} />
        <span className={`text-[13px] ${MUTED}`}>
          {run.systemName}, {when(run.createdAt)}
          {Object.values(run.files).length > 0 && `, from ${run.source === 'connection' ? 'the connection to ' : ''}${Object.values(run.files).join(' and ')}`}
          {run.judge && `, judged by ${run.judge.model}`}
        </span>
      </div>
      <p className="m-0 leading-normal text-[var(--fm-ink)]">{run.summary}</p>
      <dl className="m-0 grid grid-cols-[repeat(auto-fill,minmax(150px,1fr))] gap-3">
        {Object.entries(run.metrics).map(([k, v]) => (
          <div key={k} className="rounded-[10px] border border-[var(--fm-line)] px-3 py-2">
            <dt className={LABEL}>{label(k)}</dt>
            <dd className="m-0 mt-0.5 text-base font-semibold tabular-nums text-[var(--fm-ink)]">{show(v)}</dd>
          </div>
        ))}
      </dl>
      {groups.map(([kind, rows]) => (
        <div key={kind} className="flex flex-col gap-1.5">
          {kind && <h3 className="m-0 text-[13px] font-semibold text-[var(--fm-ink)]">{label(kind)}s</h3>}
          <DetailTable rows={rows} />
        </div>
      ))}
      {(run.detailTotal ?? 0) > (run.detail?.length ?? 0) && (
        <p className={`m-0 text-xs ${MUTED}`}>Showing {run.detail?.length} of {run.detailTotal} rows.</p>
      )}
    </div>
  )
}

/** What a behaviour test calls: the system under test (from its page) and the judge (the organisation's AI provider). */
function Connections({ spec, systemId, onReady }: { spec: EngineSpec; systemId: string; onReady: (ready: boolean) => void }) {
  const provider = useAIProvider()
  const target = useSystemTarget(spec.live === 'target' && systemId ? systemId : undefined)
  const cfg = provider.data?.config
  const judgeOk = !!cfg && cfg.enabled && cfg.keyReadable
  const t = target.data?.target
  const targetOk = spec.live !== 'target' || (!!t && t.authReadable)
  useEffect(() => onReady(judgeOk && targetOk), [judgeOk, targetOk, onReady])
  const row = (label: string, value: ReactNode) => (
    <div className="flex flex-col gap-0.5">
      <span className={LABEL}>{label}</span>
      <span className="text-[13px] leading-snug text-[var(--fm-ink)]">{value}</span>
    </div>
  )
  return (
    <div className="flex flex-col gap-2.5 rounded-[10px] border border-[var(--fm-line)] px-3 py-2.5">
      {spec.live === 'target' &&
        row(
          'System under test',
          !systemId ? (
            <span className={MUTED}>Choose a system first</span>
          ) : target.error ? (
            <span>
              Could not check the connection. {target.error}{' '}
              <button type="button" onClick={target.reload} className="font-semibold underline">Try again</button>
            </span>
          ) : target.loading && !target.data ? (
            <span className={MUTED}>Checking</span>
          ) : t ? (
            <span className="break-all">{t.url}{t.model ? `, ${t.model}` : ''}{t.authReadable ? '' : ' (auth value unreadable, enter it again)'}</span>
          ) : (
            <span>
              Not connected. <Link href={`/systems/${encodeURIComponent(systemId)}#target`} className="font-semibold underline">Connect it on the system&apos;s page</Link>
            </span>
          ),
        )}
      {spec.live === 'agent' && row('Agent under test', "FairMind's packs agent, on your AI provider")}
      {row(
        'Judge',
        provider.error ? (
          <span>
            Could not check the AI provider. {provider.error}{' '}
            <button type="button" onClick={provider.reload} className="font-semibold underline">Try again</button>
          </span>
        ) : provider.loading && !provider.data ? (
          <span className={MUTED}>Checking</span>
        ) : judgeOk ? (
          `${cfg.providerName}, ${cfg.model}`
        ) : (
          <span>
            No AI provider is on. <Link href="/org-admin/settings#ai-provider" className="font-semibold underline">Set one up in organisation settings</Link>
          </span>
        ),
      )}
    </div>
  )
}

const sleep = (ms: number) => new Promise((r) => setTimeout(r, ms))

function RunForm({ evaluationId, spec, live, onDone }: { evaluationId: string; spec: EngineSpec; live: boolean; onDone: (run: EngineRun) => void }) {
  const { systems, selectedSystem } = useSystemContext()
  const { runEvaluation, getJob, getRun } = usePackActions()
  const [systemId, setSystemId] = useState('')
  const [files, setFiles] = useState<Record<string, File | null>>({})
  const [params, setParams] = useState<Record<string, string>>({})
  const [busy, setBusy] = useState(false)
  const [failure, setFailure] = useState<string | null>(null)
  const [job, setJob] = useState<EvaluationJob | null>(null)
  const [connected, setConnected] = useState(!spec.live)
  const mounted = useRef(true)

  useEffect(() => {
    mounted.current = true
    return () => {
      mounted.current = false
    }
  }, [])
  const connections = usePlatformConnections()
  const connection = connections.data?.find((c) => c.connected && c.keyReadable) ?? null
  const [source, setSource] = useState<'upload' | 'connection' | null>(null)
  const from = spec.platform ? source ?? (connection ? 'connection' : 'upload') : 'upload'

  useEffect(() => {
    if (!systemId && selectedSystem?.id) setSystemId(selectedSystem.id)
  }, [selectedSystem, systemId])

  const filesReady = from === 'connection' ? !!connection : spec.slots.every((s) => !s.required || files[s.name])
  const ready = !!systemId && connected && filesReady && spec.params.every((p) => !p.required || (params[p.name] ?? '').trim())

  /** A behaviour test answers with a job; follow it until the run is stored. */
  async function follow(started: EvaluationJob) {
    let current = started
    while (mounted.current && current.status === 'running') {
      setJob(current)
      await sleep(2000)
      const res = await getJob(current.id)
      if (res.error || !res.data) return setFailure(res.error)
      current = res.data
    }
    setJob(null)
    if (current.status === 'failed') return setFailure(current.error ?? 'The run stopped')
    if (current.evidenceId) {
      const run = await getRun(current.evidenceId)
      if (run.error || !run.data) setFailure(run.error)
      else onDone(run.data)
    }
  }

  async function submit() {
    setBusy(true)
    setFailure(null)
    const values: Record<string, unknown> = {}
    for (const p of spec.params) {
      const raw = (params[p.name] ?? '').trim()
      if (!raw) continue
      if (p.kind === 'number') values[p.name] = Number(raw)
      else if (p.kind === 'json') {
        try {
          values[p.name] = JSON.parse(raw)
        } catch {
          setFailure(`${p.label} is not valid JSON`)
          setBusy(false)
          return
        }
      } else values[p.name] = raw
    }
    const form = new FormData()
    form.append('system_id', systemId)
    form.append('params', JSON.stringify(values))
    if (live) form.append('mode', 'live')
    form.append('source', from)
    if (from === 'upload') for (const s of spec.slots) if (files[s.name]) form.append(s.name, files[s.name] as File)
    const res = await runEvaluation(evaluationId, form)
    if (res.error || !res.data) setFailure(res.error)
    else if ('job' in res.data) await follow(res.data.job)
    else onDone(res.data)
    setBusy(false)
  }

  return (
    <form
      className="flex flex-col gap-4"
      onSubmit={(e) => {
        e.preventDefault()
        submit()
      }}
    >
      <p className={`m-0 text-[13px] leading-normal ${MUTED}`}>{from === 'connection' ? spec.platformMethod : spec.method}</p>
      {spec.platform && (
        <fieldset className="m-0 flex flex-col gap-1.5 border-0 p-0">
          <legend className="mb-1.5 text-[13px] font-semibold text-[var(--fm-ink)]">Read from</legend>
          <div className="flex flex-wrap gap-2" role="radiogroup">
            {(['connection', 'upload'] as const).map((value) => (
              <button
                key={value}
                type="button"
                role="radio"
                aria-checked={from === value}
                onClick={() => setSource(value)}
                className={`rounded-full border px-3.5 py-1.5 text-[13px] font-semibold ${
                  from === value ? 'border-[var(--fm-ink)] bg-[var(--fm-ink)] text-white' : 'border-[var(--fm-line)] bg-white text-[var(--fm-ink)]'
                }`}
              >
                {value === 'connection' ? `From connection${connection ? `: ${connection.name}` : ''}` : 'Upload'}
              </button>
            ))}
          </div>
          {from === 'connection' && !connection && !connections.loading && (
            <span className={`text-xs ${MUTED}`}>
              No agent platform is connected. Connect one in <Link href="/org-admin/settings#platform-connections" className="font-semibold underline">organization settings</Link>, or upload an export.
            </span>
          )}
          {from === 'connection' && connection && (
            <span className={`text-xs ${MUTED}`}>FairMind lists the platform's agents, environments, vaults, memory stores, deployments and recent sessions with read-only calls when you run.</span>
          )}
          {spec.judge && (
            <span className={`text-xs ${MUTED}`}>Uses your model from organization settings, AI provider, when one is set.</span>
          )}
        </fieldset>
      )}
      <div className="flex flex-col gap-1.5">
        <label htmlFor="eval-system" className="text-[13px] font-semibold text-[var(--fm-ink)]">AI system</label>
        <select id="eval-system" value={systemId} onChange={(e) => setSystemId(e.target.value)} className={FIELD} required>
          <option value="">Choose the system this result belongs to</option>
          {systems.map((s) => (
            <option key={s.id} value={s.id}>{s.name}</option>
          ))}
        </select>
        {systems.length === 0 && (
          <span className={`text-xs ${MUTED}`}>
            Register an AI system first: <Link href="/systems" className="font-semibold underline">AI systems</Link>
          </span>
        )}
      </div>
      {spec.live && <Connections spec={spec} systemId={systemId} onReady={setConnected} />}
      {from === 'upload' && spec.slots.map((s) => (
        <div key={s.name} className="flex flex-col gap-1.5">
          <label htmlFor={`slot-${s.name}`} className="text-[13px] font-semibold text-[var(--fm-ink)]">
            {s.label}{s.required ? '' : ' (optional)'}
          </label>
          <input
            id={`slot-${s.name}`}
            type="file"
            accept={ACCEPT[s.kind] || undefined}
            onChange={(e) => setFiles((f) => ({ ...f, [s.name]: e.target.files?.[0] ?? null }))}
            className="text-sm text-[var(--fm-ink)] file:mr-3 file:rounded-full file:border file:border-[var(--fm-line)] file:bg-white file:px-3 file:py-1.5 file:text-[13px] file:font-semibold"
          />
          <span className={`text-xs ${MUTED}`}>{s.help}</span>
        </div>
      ))}
      {spec.params.length > 0 && (
        <details className="rounded-[10px] border border-[var(--fm-line)] px-3 py-2" open={spec.params.some((p) => p.required)}>
          <summary className="cursor-pointer text-[13px] font-semibold text-[var(--fm-ink)]">Settings</summary>
          <div className="mt-3 flex flex-col gap-3.5">
            {spec.params.map((p) => (
              <div key={p.name} className="flex flex-col gap-1.5">
                <label htmlFor={`param-${p.name}`} className="text-[13px] font-semibold text-[var(--fm-ink)]">
                  {p.label}{p.required ? '' : ' (optional)'}
                </label>
                {p.kind === 'json' ? (
                  <textarea
                    id={`param-${p.name}`}
                    rows={3}
                    value={params[p.name] ?? ''}
                    onChange={(e) => setParams((v) => ({ ...v, [p.name]: e.target.value }))}
                    className={`${FIELD} font-mono`}
                  />
                ) : (
                  <input
                    id={`param-${p.name}`}
                    type={p.kind === 'number' ? 'number' : 'text'}
                    step="any"
                    value={params[p.name] ?? ''}
                    placeholder={p.default !== null && p.default !== undefined ? String(p.default) : ''}
                    onChange={(e) => setParams((v) => ({ ...v, [p.name]: e.target.value }))}
                    className={FIELD}
                  />
                )}
                <span className={`text-xs ${MUTED}`}>{p.help}</span>
              </div>
            ))}
          </div>
        </details>
      )}
      {failure && <ErrorNote message={failure} />}
      {job && (
        <div className="flex flex-col gap-1.5" role="status">
          <span className={`text-[13px] ${MUTED}`}>
            {job.phase ?? 'Running'}{job.total > 0 ? `: ${job.done} of ${job.total}` : ''}
          </span>
          <div className="h-1.5 overflow-hidden rounded-full bg-[var(--fm-line)]">
            <div className="h-full rounded-full bg-[var(--fm-ink)] transition-[width]" style={{ width: `${job.total ? (job.done / job.total) * 100 : 4}%` }} />
          </div>
        </div>
      )}
      <div>
        <button type="submit" className={BTN_P} disabled={!ready || busy}>{busy ? 'Running' : 'Run evaluation'}</button>
      </div>
      {spec.live && <p className={`m-0 text-xs ${MUTED}`}>Runs in the background; you can leave this page and find the result under Runs.</p>}
    </form>
  )
}

export default function EvaluationPage() {
  const { evaluationId } = useParams<{ evaluationId: string }>()
  const evaluation = useEvaluation(evaluationId)
  const runnable = !!evaluation.data?.runnable
  const engine = useEngine(evaluationId, runnable)
  const runs = useEngineRuns(evaluationId, runnable)
  const [openId, setOpenId] = useState<string | null>(null)
  const [fresh, setFresh] = useState<EngineRun | null>(null)
  const [live, setLive] = useState(false)
  const opened = useEngineRun(fresh ? null : openId)
  const shown = fresh ?? opened.data

  if (evaluation.loading && !evaluation.data) return <Loading label="Loading evaluation" />
  if (evaluation.error || !evaluation.data) {
    return (
      <div className="flex flex-col gap-4">
        <Crumbs items={[{ label: 'Frameworks', href: '/compliance' }, { label: 'Evaluations', href: '/compliance/evaluations' }, { label: evaluationId }]} />
        <ErrorNote message={`This evaluation could not be loaded. ${evaluation.error ?? ''}`} onRetry={evaluation.reload} />
      </div>
    )
  }
  const e = evaluation.data

  return (
    <div className="flex flex-col gap-[22px]">
      <Crumbs items={[{ label: 'Frameworks', href: '/compliance' }, { label: 'Evaluations', href: '/compliance/evaluations' }, { label: e.name }]} />
      <Heading title={e.name} lead={e.measures} />
      <div className="flex flex-wrap gap-2">
        <Pill>{e.id}</Pill>
        {runnable ? <Pill tone="done" dot>Runs in FairMind</Pill> : <EnginePill engine={e.engine} />}
        {e.results && e.results.status !== 'not_run' && <ResultPill status={e.results.status} />}
      </div>
      <dl className="m-0 grid grid-cols-[repeat(auto-fill,minmax(220px,1fr))] gap-4 rounded-2xl bg-white p-5">
        {([
          ['Metric', e.metric],
          ['Pass when', e.threshold],
          ['Applies to', e.appliesTo],
          ['Pack', e.pack.name],
          ['Requirements it tests', `${e.tests.length}`],
        ] as const).map(([k, v]) => (
          <div key={k} className="flex flex-col gap-0.5">
            <dt className={LABEL}>{k}</dt>
            <dd className="m-0 text-sm leading-snug text-[var(--fm-ink)]">{v || '-'}</dd>
          </div>
        ))}
      </dl>

      {!runnable ? (
        <section className="rounded-2xl bg-white p-5">
          <h2 className="m-0 text-base font-semibold text-[var(--fm-ink)]">Not runnable in FairMind yet</h2>
          <p className={`mb-0 mt-2 text-sm leading-normal ${MUTED}`}>
            FairMind cannot run this evaluation yet. It needs a connection to the system&apos;s platform or evidence FairMind does not collect.
          </p>
        </section>
      ) : (
        <div className="grid gap-[22px] lg:grid-cols-[minmax(0,420px)_minmax(0,1fr)]">
          <section className="rounded-2xl bg-white p-5">
            <h2 className="mb-3 mt-0 text-base font-semibold text-[var(--fm-ink)]">Run this evaluation</h2>
            {engine.error ? (
              <ErrorNote message={engine.error} onRetry={engine.reload} />
            ) : !engine.data ? (
              <Loading label="Loading" />
            ) : (
              <div className="flex flex-col gap-4">
              {engine.data.alternate && (
                <div className="flex gap-2" role="group" aria-label="How to run">
                  {([[false, 'From uploaded files'], [true, 'Against the live system']] as const).map(([v, text]) => (
                    <button
                      key={text}
                      type="button"
                      aria-pressed={live === v}
                      onClick={() => setLive(v)}
                      className={`rounded-full px-3 py-1.5 text-[12.5px] font-semibold ${live === v ? 'bg-[var(--fm-ink)] text-white' : 'border border-[var(--fm-line)] bg-white text-[var(--fm-ink2)]'}`}
                    >
                      {text}
                    </button>
                  ))}
                </div>
              )}
              <RunForm
                key={live ? 'live' : 'files'}
                evaluationId={e.id}
                spec={live && engine.data.alternate ? engine.data.alternate : engine.data}
                live={live && !!engine.data.alternate}
                onDone={(run) => {
                  setFresh(run)
                  setOpenId(run.id)
                  runs.reload()
                  evaluation.reload()
                }}
              />
              </div>
            )}
          </section>
          <section className="flex min-w-0 flex-col gap-[22px]">
            <div className="rounded-2xl bg-white p-5">
              <h2 className="mb-3 mt-0 text-base font-semibold text-[var(--fm-ink)]">Runs</h2>
              {runs.data && runs.data.length === 0 && <p className={`m-0 text-sm ${MUTED}`}>No runs yet. Each run is kept as measured evidence on its AI system.</p>}
              <ul className="m-0 flex list-none flex-col p-0">
                {(runs.data ?? []).map((r) => (
                  <li key={r.id} className="border-t border-[#15171a14] first:border-t-0">
                    <button
                      type="button"
                      onClick={() => {
                        setFresh(null)
                        setOpenId(r.id)
                      }}
                      className={`flex w-full flex-wrap items-center gap-2.5 py-2.5 text-left text-[13px] ${openId === r.id ? 'font-semibold' : ''}`}
                    >
                      <ResultPill status={r.status} />
                      <span className="text-[var(--fm-ink)]">{r.systemName}</span>
                      <span className={MUTED}>{when(r.createdAt)}</span>
                    </button>
                  </li>
                ))}
              </ul>
            </div>
          </section>
        </div>
      )}
      {runnable && shown && (
        <section className="rounded-2xl bg-white p-5">
          <h2 className="mb-3 mt-0 text-base font-semibold text-[var(--fm-ink)]">Result</h2>
          <RunResult run={shown} />
        </section>
      )}
    </div>
  )
}
