'use client'

import Link from 'next/link'
import { useParams } from 'next/navigation'
import { useEffect, useMemo, useState } from 'react'
import { useEngine, useEngineRun, useEngineRuns, useEvaluation, usePackActions, type EngineRun, type EngineSpec } from '@/lib/api/hooks/usePacks'
import { useSystemContext } from '@/components/workflow/SystemContext'
import { BTN_P, Crumbs, EnginePill, ErrorNote, Heading, LABEL, Loading, MUTED, Pill, ResultPill, when } from '@/components/packs/parts'

const FIELD = 'w-full rounded-[10px] border border-[var(--fm-line)] bg-white px-3 py-2 text-sm text-[var(--fm-ink)] focus:border-[var(--fm-ink)] focus:outline-none'
const ACCEPT: Record<string, string> = { csv: '.csv,text/csv', text: '.txt,.md,.env,.yaml,.yml,.json,.log,text/plain', json: '.json,application/json', binary: '' }

/** "datasetDrift" -> "Dataset drift" */
const label = (key: string) => key.replace(/([a-z0-9])([A-Z])/g, '$1 $2').replace(/_/g, ' ').replace(/^./, (c) => c.toUpperCase()).replace(/ ([A-Z])/g, (m) => m.toLowerCase())

function show(value: unknown): string {
  if (value === null || value === undefined || value === '') return '-'
  if (typeof value === 'boolean') return value ? 'Yes' : 'No'
  if (typeof value === 'number') return Number.isInteger(value) ? value.toLocaleString() : String(Number(value.toPrecision(4)))
  if (typeof value === 'object') return JSON.stringify(value)
  return String(value)
}

function RunResult({ run }: { run: EngineRun }) {
  const keys = useMemo(() => {
    const seen = new Set<string>()
    for (const row of run.detail ?? []) Object.keys(row).forEach((k) => seen.add(k))
    return [...seen]
  }, [run.detail])
  return (
    <div className="flex flex-col gap-4">
      <div className="flex flex-wrap items-center gap-2.5">
        <ResultPill status={run.status} />
        <span className={`text-[13px] ${MUTED}`}>
          {run.systemName}, {when(run.createdAt)}
          {Object.values(run.files).length > 0 && `, from ${Object.values(run.files).join(' and ')}`}
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
      {keys.length > 0 && (
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
              {(run.detail ?? []).map((row, i) => (
                <tr key={i} className="border-t border-[#15171a14] align-top">
                  {keys.map((k) => (
                    <td key={k} className="max-w-[280px] break-words py-1.5 pr-3 tabular-nums">{show(row[k])}</td>
                  ))}
                </tr>
              ))}
            </tbody>
          </table>
          {(run.detailTotal ?? 0) > (run.detail?.length ?? 0) && (
            <p className={`mt-2 text-xs ${MUTED}`}>Showing {run.detail?.length} of {run.detailTotal} rows.</p>
          )}
        </div>
      )}
    </div>
  )
}

function RunForm({ evaluationId, spec, onDone }: { evaluationId: string; spec: EngineSpec; onDone: (run: EngineRun) => void }) {
  const { systems, selectedSystem } = useSystemContext()
  const { runEvaluation } = usePackActions()
  const [systemId, setSystemId] = useState('')
  const [files, setFiles] = useState<Record<string, File | null>>({})
  const [params, setParams] = useState<Record<string, string>>({})
  const [busy, setBusy] = useState(false)
  const [failure, setFailure] = useState<string | null>(null)

  useEffect(() => {
    if (!systemId && selectedSystem?.id) setSystemId(selectedSystem.id)
  }, [selectedSystem, systemId])

  const ready = !!systemId && spec.slots.every((s) => !s.required || files[s.name]) && spec.params.every((p) => !p.required || (params[p.name] ?? '').trim())

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
    for (const s of spec.slots) if (files[s.name]) form.append(s.name, files[s.name] as File)
    const res = await runEvaluation(evaluationId, form)
    setBusy(false)
    if (res.error || !res.data) setFailure(res.error)
    else onDone(res.data)
  }

  return (
    <form
      className="flex flex-col gap-4"
      onSubmit={(e) => {
        e.preventDefault()
        submit()
      }}
    >
      <p className={`m-0 text-[13px] leading-normal ${MUTED}`}>{spec.method}</p>
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
      {spec.slots.map((s) => (
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
      <div>
        <button type="submit" className={BTN_P} disabled={!ready || busy}>{busy ? 'Running' : 'Run evaluation'}</button>
      </div>
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
            FairMind cannot compute this evaluation from uploaded files. It needs a connection to the system under test or to its platform, which is not built yet.
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
              <RunForm
                evaluationId={e.id}
                spec={engine.data}
                onDone={(run) => {
                  setFresh(run)
                  setOpenId(run.id)
                  runs.reload()
                  evaluation.reload()
                }}
              />
            )}
          </section>
          <section className="flex min-w-0 flex-col gap-[22px]">
            {shown && (
              <div className="rounded-2xl bg-white p-5">
                <h2 className="mb-3 mt-0 text-base font-semibold text-[var(--fm-ink)]">Result</h2>
                <RunResult run={shown} />
              </div>
            )}
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
    </div>
  )
}
