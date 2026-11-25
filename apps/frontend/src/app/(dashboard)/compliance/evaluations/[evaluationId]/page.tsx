'use client'

import '@/astryx/pages/evaluations.css'
import Link from 'next/link'
import { useParams, usePathname, useRouter, useSearchParams } from 'next/navigation'
import { Fragment, useEffect, useMemo, useRef, useState, type ReactNode } from 'react'
import { Activity, ArrowLeftRight, Bot, Boxes, Check, Cloud, Code, Cpu, Database, Info, MessageSquare, Network, Play, Plug, Scale, Server, Upload } from 'lucide-react'
import { Banner } from '@astryxdesign/core/Banner'
import { Button } from '@astryxdesign/core/Button'
import { FileInput } from '@astryxdesign/core/FileInput'
import { MetadataList, MetadataListItem } from '@astryxdesign/core/MetadataList'
import { SegmentedControl, SegmentedControlItem } from '@astryxdesign/core/SegmentedControl'
import { Selector } from '@astryxdesign/core/Selector'
import { TextArea } from '@astryxdesign/core/TextArea'
import { Token } from '@astryxdesign/core/Token'
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
  type RunWay,
} from '@/lib/api/hooks/usePacks'
import { setSystemKind } from '@/lib/api/hooks/useLifecycle'
import { KIND_LABEL } from '@/astryx/data/discovery'
import { defaultWay, keptAs, presetFor, proves } from '@/astryx/data/evaluations'
import { useSystemContext } from '@/components/workflow/SystemContext'
import { Drawer } from '@astryxdesign/core/Drawer'
import { TraceView } from '@/components/traces/TraceView'
import { ExplanationResult } from '@/components/explain/ExplainParts'
import { BTN, BTN_P, Crumbs, EnginePill, ErrorNote, Heading, LABEL, Loading, MUTED, Pill, ResultPill, when } from '@/components/packs/parts'

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

function DetailTable({ rows, onTrace }: { rows: Array<Record<string, unknown>>; onTrace?: (row: Record<string, unknown>) => void }) {
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
                <td key={k} className="max-w-[280px] break-words py-1.5 pr-3 tabular-nums">
                  {(k === 'traceId' || k === 'session') && onTrace && typeof row[k] === 'string'
                    ? <button type="button" onClick={() => onTrace({ ...row, traceId: row[k] })} className="font-mono font-semibold underline">{show(row[k])}</button>
                    : show(row[k])}
                </td>
              ))}
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  )
}

function RunResult({ run, onTrace }: { run: EngineRun; onTrace?: (row: Record<string, unknown>) => void }) {
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
        {run.thresholdLoosened && <Pill tone="warn">Loosened thresholds: not counted as proof</Pill>}
        {run.partialRead && run.status === 'passed' && <Pill tone="warn">Read part of the week&apos;s live runs: not counted as proof</Pill>}
        <span className={`text-[13px] ${MUTED}`}>
          {run.systemName}, {when(run.createdAt)}
          {Object.values(run.files).length > 0 && `, from ${run.source === 'connection' ? 'the connection to ' : ''}${Object.values(run.files).join(' and ')}`}
          {run.judge && `, judged by ${run.judge.model}${run.judge.sharesProviderWithSystem ? ', the same provider as the system' : ''}`}
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
          <DetailTable rows={rows} onTrace={run.source === 'traces' ? onTrace : undefined} />
        </div>
      ))}
      {(run.detailTotal ?? 0) > (run.detail?.length ?? 0) && (
        <p className={`m-0 text-xs ${MUTED}`}>Showing {run.detail?.length} of {run.detailTotal} rows.</p>
      )}
    </div>
  )
}

const DECISION_LABEL: Record<string, string> = { benign: 'Reviewed: not poisoning', poisoned: 'Confirmed poisoning', resolved: 'Resolved', accepted: 'Accepted' }

/** The flagged items of a run that waits for review, each with its latest decision, and a form to review the next. */
function ReviewList({ run, onReviewed }: { run: EngineRun; onReviewed: (run: EngineRun) => void }) {
  const { reviewRunItem } = usePackActions()
  const items = run.review?.items ?? []
  const latest = useMemo(() => new Map((run.review?.decisions ?? []).map((d) => [d.item, d])), [run.review?.decisions])
  const choices = run.review?.choices ?? []
  const [item, setItem] = useState<string | undefined>()
  const [decision, setDecision] = useState<string | undefined>()
  const [note, setNote] = useState('')
  const [busy, setBusy] = useState(false)
  const [error, setError] = useState<string | null>(null)
  const open = items.filter((i) => !latest.has(i.item))
  const chosen = item ?? open[0]?.item
  const state = run.review?.state
  async function save() {
    if (state !== 'ready' || !chosen || !decision || !note.trim()) return
    setBusy(true)
    setError(null)
    const res = await reviewRunItem(run.id, chosen, decision, note.trim())
    setBusy(false)
    if (res.error || !res.data) return setError(res.error ?? 'Could not save the review')
    setItem(undefined)
    setNote('')
    onReviewed(res.data)
  }
  return (
    <section className="flex flex-col gap-3" aria-labelledby="ev-review">
      <h3 id="ev-review" className="m-0 text-[13px] font-semibold text-[var(--fm-ink)]">Review ({items.length - open.length} of {items.length} reviewed)</h3>
      <ul className="m-0 flex list-none flex-col gap-1.5 p-0">
        {items.map((i) => {
          const d = latest.get(i.item)
          return (
            <li key={i.item} className="flex flex-wrap items-baseline gap-2 border-t border-[var(--fm-line)] pt-1.5 text-[12.5px]">
              <Token size="sm" color={!d ? 'gray' : d.decision === 'poisoned' ? 'red' : 'green'} label={d ? DECISION_LABEL[d.decision] ?? d.decision : 'Not reviewed'} />
              <span className="font-mono font-semibold text-[var(--fm-ink)]">{i.item}</span>
              <span className={MUTED}>{i.label}</span>
              {d && <span className={MUTED}>{d.note} ({d.by}, {when(d.at)})</span>}
            </li>
          )
        })}
      </ul>
      {state === 'ready' ? (
        <>
          {error && <Banner status="error" title="Review not saved" description={error} />}
          <div className="grid gap-3 sm:grid-cols-2">
            <Selector label="Item" options={items.map((i) => ({ value: i.item, label: `${i.item}${latest.has(i.item) ? ' (reviewed)' : ''}` }))} value={chosen} onChange={setItem} />
            <Selector label="Decision" placeholder="Choose a decision" options={choices.map((c) => ({ value: c, label: DECISION_LABEL[c] ?? c }))} value={decision} onChange={setDecision} />
          </div>
          <TextArea label="Note" rows={2} value={note} onChange={(v) => setNote(v)} description="What you checked; kept with the run as evidence, under your name." />
          <div>
            <Button label="Save review" variant="primary" isDisabled={!chosen || !decision || !note.trim() || busy} isLoading={busy} onClick={() => void save()} />
          </div>
        </>
      ) : (
        <p className={`m-0 text-sm ${MUTED}`}>
          {state === 'superseded' ? 'This run was superseded. Open the latest result under Runs.' : 'You have read-only access to this review.'}
        </p>
      )}
    </section>
  )
}

const WAY_LABEL: Record<RunWay, string> = { calls_system: 'Call the system', live_runs: 'Live runs', platform: 'Platform connection', fairmind_data: "FairMind's data", files: 'Upload files' }
const WAY_ICON: Record<RunWay, typeof Plug> = { calls_system: Plug, live_runs: Activity, platform: Network, fairmind_data: Database, files: Upload }
/** What a ready or missing way reads as beside the system. */
const WAY_STATE: Partial<Record<RunWay, [ready: string, missing: string]>> = {
  calls_system: ['Connected', 'Not connected'],
  live_runs: ['Live runs this week', 'No live runs'],
  platform: ['Platform connected', 'Platform not connected'],
  fairmind_data: ['On file in FairMind', 'Nothing on file yet'],
}
/** What the chosen way asks of the system, for the header. */
const WAY_HEAD: Record<RunWay, string> = { calls_system: 'Calls the system', live_runs: 'Reads live runs', platform: 'Reads the platform', fairmind_data: "Reads FairMind's records", files: 'Needs a file' }
const KIND_ICON: Record<string, typeof Plug> = { llm_app: MessageSquare, ml_model: Boxes, agent: Bot, ai_service: Cloud, ai_assisted_dev: Code, mcp_server: Server }

function Node({ icon, title, sub, state }: { icon: ReactNode; title: string; sub?: string; state?: 'ok' | 'missing' }) {
  return (
    <div className="fm-ev-node">
      <span className={`fm-ev-node-icon${state === 'missing' ? ' is-missing' : ''}`} aria-hidden>
        {icon}
        {state === 'ok' && <span className="fm-ev-node-ok"><Check size={10} strokeWidth={3.5} /></span>}
      </span>
      <span className="fm-ev-node-title">{title}</span>
      {sub && <span className="fm-ev-muted fm-ev-small">{sub}</span>}
    </div>
  )
}

function Arrow({ label, broken, muted }: { label?: string; broken?: boolean; muted?: boolean }) {
  return (
    <div className={`fm-ev-arrow${broken ? ' is-broken' : muted ? ' is-muted' : ''}`}>
      <span className="fm-ev-small">{label || ' '}</span>
      <svg width="100%" height="14" viewBox="0 0 120 14" preserveAspectRatio="none" fill="none" stroke="currentColor" strokeWidth="1.6" strokeLinecap="round" aria-hidden>
        {broken ? <><path d="M2 7h48M70 7h48" strokeDasharray="3 5" /><path d="M56 2l8 10M64 2l-8 10" /></> : <><path d="M2 7h110" strokeDasharray="4 4" /><path d="M106 2l6 5-6 5" /></>}
      </svg>
    </div>
  )
}

/** A behaviour test: FairMind writes probes, the system (or its live runs, or FairMind's agent) answers, the judge decides. Without both ends, the steps to set them up. */
function Flow({ spec, system, recorded, replays = false, sending, answers, onReady }: { spec: EngineSpec; system: { id: string; name: string; kind?: string | null }; recorded: boolean; replays?: boolean; sending: string; answers: string; onReady: (ready: boolean) => void }) {
  const provider = useAIProvider()
  const calls = spec.live === 'target' && !recorded // live runs already hold the answers, so the system is not called
  const target = useSystemTarget(calls ? system.id : undefined)
  const cfg = provider.data?.config
  const judgeOk = !!cfg && cfg.enabled && cfg.keyReadable
  const t = target.data?.target
  const targetOk = !calls || (!!t && t.authReadable)
  const checking = (calls && target.loading && !target.data) || (provider.loading && !provider.data)
  useEffect(() => onReady(judgeOk && targetOk), [judgeOk, targetOk, onReady])
  const KindIcon = KIND_ICON[system.kind ?? ''] ?? Cpu
  const steps = [
    ...(calls
      ? [{ done: targetOk, label: targetOk ? `${system.name} connected` : t ? `Enter ${system.name}'s auth value again` : `Connect ${system.name}`, href: `/systems/${encodeURIComponent(system.id)}#target`, action: 'Connect' }]
      : []),
    { done: judgeOk, label: judgeOk && cfg ? `Judge set: ${cfg.providerName}` : 'Set a judge model', href: '/settings?section=ai-provider', action: 'Set up' },
  ]
  const left = steps.filter((s) => !s.done).length
  const ring = 2 * Math.PI * 16
  return (
    <>
      <section className="fm-ev-card fm-ev-flow" aria-label="How it runs">
        <Node icon={<img src="/logo.png" alt="" width={30} height={30} />} title="FairMind" sub={recorded ? 'reads runs' : replays ? 'replays decisions' : 'writes probes'} />
        <Arrow label={calls && !targetOk ? 'no connection' : sending} broken={calls && !targetOk} />
        <Node
          icon={spec.live === 'agent' ? <Bot size={26} /> : recorded ? <Activity size={26} /> : <KindIcon size={26} />}
          title={spec.live === 'agent' ? "FairMind's agent" : recorded ? 'Live runs' : system.name}
          sub={targetOk ? 'answers' : undefined}
          state={calls ? (targetOk ? 'ok' : 'missing') : undefined}
        />
        <Arrow label={targetOk ? answers : ''} muted={!targetOk} />
        <Node icon={<Scale size={24} />} title="Judge" sub={judgeOk && cfg ? cfg.providerName : 'not set'} state={judgeOk ? 'ok' : 'missing'} />
      </section>
      {target.error && <ErrorNote message={`Could not check the connection. ${target.error}`} onRetry={target.reload} />}
      {provider.error && <ErrorNote message={`Could not check the AI provider. ${provider.error}`} onRetry={provider.reload} />}
      {!checking && left > 0 && (
        <section className="fm-ev-card" aria-labelledby="ev-setup">
          <div className="fm-ev-setup-head">
            <svg width="40" height="40" viewBox="0 0 40 40" role="img" aria-label={`${steps.length - left} of ${steps.length} done`}>
              <circle cx="20" cy="20" r="16" fill="none" className="fm-ev-ring-track" strokeWidth="5" />
              <circle cx="20" cy="20" r="16" fill="none" className="fm-ev-ring-done" strokeWidth="5" strokeLinecap="round" strokeDasharray={`${(ring * (steps.length - left)) / steps.length} ${ring}`} transform="rotate(-90 20 20)" />
            </svg>
            <h2 id="ev-setup" className="fm-ev-h2">{left} {left === 1 ? 'step' : 'steps'} left</h2>
          </div>
          <ol className="fm-ev-steps">
            {steps.map((s) => (
              <li key={s.label} className={s.done ? 'is-done' : 'is-todo'}>
                <span className="fm-ev-step-mark" aria-hidden>{s.done ? <Check size={14} strokeWidth={3} /> : <Plug size={14} />}</span>
                <span className="fm-ev-step-label">{s.label}</span>
                {!s.done && <Button label={s.action} variant="primary" size="sm" href={s.href} />}
              </li>
            ))}
          </ol>
        </section>
      )}
    </>
  )
}

/** The 95% bound each offered probe count shows with none failing, against the pass limit. */
function ProofBars({ bounds, limit, count, needed }: { bounds: Array<{ count: number; bound: number }>; limit: number | null; count: number; needed: number | null }) {
  const scale = Math.max(...bounds.map((b) => b.bound), limit ?? 0) || 1
  const at = (v: number) => `${Math.min(100, (v / scale) * 100)}%`
  const none = limit !== null && !bounds.some((b) => proves(b.bound, limit))
  // a zero limit is zero tolerance on the server: no count bounds a rate at 0, any failure fails
  if (limit === 0) return <span className="fm-ev-muted fm-ev-small">0% limit: any failure fails.</span>
  return (
    <div className="fm-ev-proof">
      {bounds.map((b) => {
        const ok = limit !== null && proves(b.bound, limit)
        return (
          <div key={b.count} className={`fm-ev-proof-row${b.count === count ? ' is-on' : ''}`}>
            <span>{b.count}</span>
            <span className="fm-ev-proof-track" aria-hidden>
              <span className={`fm-ev-proof-fill${limit === null ? '' : ok ? ' is-ok' : ' is-no'}`} style={{ width: at(b.bound) }} />
              {limit !== null && <span className="fm-ev-proof-limit" style={{ left: at(limit) }} />}
            </span>
            <span className={limit === null ? 'fm-ev-muted' : ok ? 'fm-ev-ok' : 'fm-ev-no'}>
              {limit === null ? `under ${b.bound}%` : ok ? `shows ${limit}% or less` : `cannot show ${limit}%`}
            </span>
          </div>
        )
      })}
      {limit !== null && <span className="fm-ev-muted fm-ev-small">{limit}% limit; bars: highest rate still possible at 95% with none failing.</span>}
      {none && needed && <span className="fm-ev-muted fm-ev-small">Showing {limit}% takes {needed} probes with none failing: upload a probe set.</span>}
    </div>
  )
}

/** A data-only evaluation: the files it compares and when it passes. */
function Compare({ slots, threshold, psi, system }: { slots: EngineSpec['slots']; threshold: string; psi: number | null; system: string }) {
  const pair = slots.length === 2 // two files: an older set against a recent one
  return (
    <section className="fm-ev-card" aria-label={pair ? 'What it compares' : 'What it reads'}>
      <div className="fm-ev-compare">
        {slots.map((s, i) => (
          <Fragment key={s.name}>
            {pair && i === 1 && <ArrowLeftRight size={22} className="fm-ev-muted" aria-hidden />}
            <figure className="fm-ev-doc">
              <span className={`fm-ev-doc-stack${pair && i === 1 ? ' is-recent' : ''}`} aria-hidden><span /><span /></span>
              <figcaption>{s.label}</figcaption>
            </figure>
          </Fragment>
        ))}
        <div className="fm-ev-passes">
          <span className="fm-ev-label">Passes when</span>
          <span className="fm-ev-big">{psi !== null ? `PSI under ${psi}` : threshold || '-'}</span>
          {psi !== null && (
            <>
              <span className="fm-ev-meter" aria-hidden><span className="is-ok" /><span className="is-no" /><span className="fm-ev-meter-mark" /></span>
              <span className="fm-ev-meter-legend fm-ev-small fm-ev-muted"><span>stable</span><span>{psi}</span><span>shifted</span></span>
            </>
          )}
        </div>
      </div>
      <p className="fm-ev-note">
        <Info size={16} aria-hidden />
        Reads the files you upload. {system} is not called.
      </p>
    </section>
  )
}

const sleep = (ms: number) => new Promise((r) => setTimeout(r, ms))

function RunForm({ evaluationId, spec, live, way, liveRunsOwn = null, system, threshold, onDone }: {
  evaluationId: string
  spec: EngineSpec
  live: boolean
  way: RunWay
  liveRunsOwn?: EngineSpec | null
  system: { id: string; name: string; kind?: string | null }
  threshold: string
  onDone: (run: EngineRun) => void
}) {
  const { runEvaluation, getJob, getRun } = usePackActions()
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
  const from = way === 'live_runs' ? 'traces' : way === 'platform' ? 'connection' : way === 'fairmind_data' ? 'fairmind' : 'upload'
  // Reading live runs may use an engine of its own (Explanation quality replays them), with its own settings.
  const active = from === 'traces' && liveRunsOwn ? liveRunsOwn : spec

  // A behaviour test whose probes can be written, uploaded or taken from a benchmark offers that as one choice.
  const probeSlot = spec.slots.find((s) => s.name === 'probes' && !s.required)
  const countParam = spec.params.find((p) => p.name === 'probe_count')
  const benchParam = spec.params.find((p) => p.name === 'probe_source')
  const choosing = from === 'upload' && !!probeSlot && !!countParam
  const [probes, setProbes] = useState('write') // 'write', 'upload' or a benchmark name
  const slots = choosing ? spec.slots.filter((s) => s !== probeSlot) : spec.slots
  // Column names describe an uploaded file, and which columns to compare; the server sets them when it reads live runs.
  const settings = (choosing ? spec.params.filter((p) => p !== countParam && p !== benchParam) : active.params)
    .filter((p) => from !== 'traces' || !(p.name.endsWith('_column') || p.name === 'features' || p.name === 'ignore'))
  // Files a person may add to live runs, such as a drift reference in place of the weeks before.
  const liveUploads = from === 'traces' ? (spec.liveRunsUploads ?? []).flatMap((u) => spec.slots.filter((s) => s.name === u.name).map((s) => ({ ...s, help: u.help }))) : []
  const sampling = choosing ? spec.sampling : null
  const agreed = Number((params.max_rate ?? '').trim())
  const limit = sampling ? sampling.limit ?? ((params.max_rate ?? '').trim() && !Number.isNaN(agreed) ? agreed : null) : null
  const preset = sampling ? presetFor(sampling.bounds, limit) : null
  const count = (params.probe_count ?? '').trim() || String(preset ?? countParam?.default ?? '')
  const psiParam = spec.params.find((p) => p.name === 'psi_limit' && typeof p.default === 'number')
  const psi = psiParam ? Number((params.psi_limit ?? '').trim() || psiParam.default) : null

  const filesReady = from === 'traces' || from === 'fairmind' ? true : from === 'connection' ? !!connection : slots.every((s) => !s.required || files[s.name]) && (!choosing || probes !== 'upload' || !!files.probes)
  const ready = (!active.live || connected) && filesReady && settings.every((p) => !p.required || (params[p.name] ?? '').trim())

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
    for (const p of active.params) {
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
    if (choosing) {
      delete values.probe_count
      delete values.probe_source
      if (probes === 'write') values.probe_count = Number(count)
      else if (probes !== 'upload') values.probe_source = probes
    }
    const form = new FormData()
    form.append('system_id', system.id)
    form.append('params', JSON.stringify(values))
    if (live) form.append('mode', 'live')
    form.append('source', from)
    if (from === 'upload')
      for (const s of spec.slots) if (files[s.name] && (!choosing || s !== probeSlot || probes === 'upload')) form.append(s.name, files[s.name] as File)
    for (const s of liveUploads) if (files[s.name]) form.append(s.name, files[s.name] as File)
    const res = await runEvaluation(evaluationId, form)
    if (res.error || !res.data) setFailure(res.error)
    else if ('job' in res.data) await follow(res.data.job)
    else onDone(res.data)
    setBusy(false)
  }

  const sending = choosing ? (probes === 'write' ? `${count} probes` : probes === 'upload' ? 'your probes' : `${probes} set`) : ''
  return (
    <form
      className="fm-ev-stack"
      onSubmit={(e) => {
        e.preventDefault()
        submit()
      }}
    >
      {active.live ? (
        <Flow spec={active} system={system} recorded={from === 'traces' && active === spec} replays={from === 'traces' && active !== spec} sending={sending} answers={choosing && probes === 'write' ? `${count} answers` : ''} onReady={setConnected} />
      ) : (
        way === 'files' && slots.length > 0 && <Compare slots={slots} threshold={threshold} psi={psi} system={system.name} />
      )}
      <section className="fm-ev-card fm-ev-stack" aria-label="Run">
        {choosing && probeSlot && countParam && connected && (
          <>
            <div className="fm-ev-between">
              <h2 className="fm-ev-h2">Probes</h2>
              {probes === 'write' && sampling && (
                <SegmentedControl label="Number of probes" value={count} onChange={(v) => setParams((p) => ({ ...p, probe_count: v }))} size="sm">
                  {sampling.bounds.map((b) => (
                    <SegmentedControlItem key={b.count} label={String(b.count)} value={String(b.count)} />
                  ))}
                </SegmentedControl>
              )}
            </div>
            {probes === 'write' && sampling && <ProofBars bounds={sampling.bounds} limit={limit} count={Number(count)} needed={sampling.needed} />}
            {probes === 'write' && !sampling && (
              <span className="fm-ev-inline">
                <input
                  id="param-probe_count"
                  type="number"
                  min={1}
                  aria-label={countParam.label}
                  value={params.probe_count ?? ''}
                  placeholder={String(countParam.default ?? '')}
                  onChange={(e) => setParams((v) => ({ ...v, probe_count: e.target.value }))}
                  className={FIELD.replace('w-full', 'w-24')}
                />
                <span className="fm-ev-muted fm-ev-small">{countParam.help}</span>
              </span>
            )}
            <SegmentedControl label="Probes from" value={probes} onChange={setProbes} size="sm">
              <SegmentedControlItem label="Written for this system" value="write" />
              {(benchParam?.options ?? []).map((o) => (
                <SegmentedControlItem key={o} label={`${o} set`} value={o} />
              ))}
              <SegmentedControlItem label="Your CSV" value="upload" />
            </SegmentedControl>
            {probes === 'upload' && (
              <FileInput label={probeSlot.label} description={probeSlot.help} accept={ACCEPT[probeSlot.kind] || undefined} value={files.probes ?? null} onChange={(f) => setFiles((v) => ({ ...v, probes: Array.isArray(f) ? f[0] ?? null : f }))} />
            )}
          </>
        )}
        {from === 'connection' && (
          <span className="fm-ev-muted fm-ev-small">
            {connection ? (
              `FairMind reads ${connection.name} with read-only calls when you run.`
            ) : connections.loading ? (
              'Checking the platform connection'
            ) : (
              <>
                No agent platform is connected. <Link href="/settings?section=connections" className="font-semibold underline">Connect one in organization settings</Link>.
              </>
            )}
          </span>
        )}
        {from === 'connection' && spec.judge && <JudgeNote />}
        {from === 'fairmind' && <span className="fm-ev-muted fm-ev-small">FairMind reads what it already holds for {system.name}; nothing is uploaded.</span>}
        {(from === 'upload' ? slots : liveUploads).length > 0 && (
          <div className="fm-ev-drops">
            {(from === 'upload' ? slots : liveUploads).map((s) => (
              <FileInput
                key={s.name}
                mode="dropzone"
                label={s.label}
                description={s.help}
                isOptional={!s.required || from === 'traces'}
                accept={ACCEPT[s.kind] || undefined}
                value={files[s.name] ?? null}
                onChange={(f) => setFiles((v) => ({ ...v, [s.name]: Array.isArray(f) ? f[0] ?? null : f }))}
              />
            ))}
          </div>
        )}
        {settings.length > 0 && (
          <details className="rounded-[10px] border border-[var(--fm-line)] px-3 py-2" open={settings.some((p) => p.required)}>
            <summary className="cursor-pointer text-[13px] font-semibold text-[var(--fm-ink)]">Settings</summary>
            <div className="mt-3 flex flex-col gap-3.5">
              {settings.map((p) => (
                <div key={p.name} className="flex flex-col gap-1.5">
                  <label htmlFor={`param-${p.name}`} className="text-[13px] font-semibold text-[var(--fm-ink)]">
                    {p.label}{p.required ? '' : ' (optional)'}
                  </label>
                  {p.options?.length ? (
                    <select
                      id={`param-${p.name}`}
                      value={params[p.name] ?? ''}
                      onChange={(e) => setParams((v) => ({ ...v, [p.name]: e.target.value }))}
                      className={FIELD}
                    >
                      <option value="">None</option>
                      {p.options.map((o) => (
                        <option key={o} value={o}>{o}</option>
                      ))}
                    </select>
                  ) : p.kind === 'json' ? (
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
        <div className="fm-ev-between">
          <span className="fm-ev-muted fm-ev-small">{active.live ? 'Runs in the background; the result also shows under Runs.' : from === 'connection' ? spec.platformMethod : active.method}</span>
          <Button type="submit" label={busy ? 'Running' : 'Run evaluation'} variant="primary" icon={<Play size={14} aria-hidden />} isDisabled={!ready || busy} isLoading={busy} />
        </div>
      </section>
    </form>
  )
}

/** A judged platform check uses the organisation's AI provider model. */
function JudgeNote() {
  const provider = useAIProvider()
  const cfg = provider.data?.config
  if (provider.loading && !provider.data) return null
  return cfg && cfg.enabled && cfg.keyReadable ? (
    <span className="fm-ev-muted fm-ev-small">Judged by {cfg.providerName}, your AI provider model.</span>
  ) : (
    <span className="fm-ev-muted fm-ev-small">
      Judged by your AI provider model. <Link href="/settings?section=ai-provider" className="font-semibold underline">Set one</Link>
    </span>
  )
}

/** The system has no kind yet: ask for it, since which evaluations fit depends on it. */
function KindPrompt({ system, onSaved }: { system: { id: string; name: string }; onSaved: () => void }) {
  const [kind, setKind] = useState<string | undefined>()
  const [busy, setBusy] = useState(false)
  const [error, setError] = useState<string | null>(null)
  async function save() {
    if (!kind) return
    setBusy(true)
    setError(null)
    try {
      await setSystemKind(system.id, kind)
      onSaved()
    } catch (e) {
      setError(e instanceof Error ? e.message : 'Could not save the kind')
      setBusy(false)
    }
  }
  return (
    <section className="fm-ev-card fm-ev-stack" aria-labelledby="ev-kind">
      <h2 id="ev-kind" className="fm-ev-h2">What kind of system is {system.name}?</h2>
      {error && <Banner status="error" title="Kind not saved" description={error} />}
      <div className="fm-ev-inline">
        <div className="fm-ev-grow">
          <Selector label="Kind" placeholder="Choose a kind" options={Object.entries(KIND_LABEL).map(([value, label]) => ({ value, label }))} value={kind} onChange={setKind} />
        </div>
        <Button label="Save kind" variant="primary" isDisabled={!kind || busy} isLoading={busy} onClick={() => void save()} />
      </div>
    </section>
  )
}

const SideCard = ({ label, children }: { label: string; children: ReactNode }) => (
  <div className="fm-ev-card fm-ev-side-card">
    <span className="fm-ev-label">{label}</span>
    {children}
  </div>
)

export default function EvaluationPage() {
  const { evaluationId } = useParams<{ evaluationId: string }>()
  const search = useSearchParams()
  const router = useRouter()
  const pathname = usePathname()
  const { systems: allSystems, selectedSystem, refreshSystems } = useSystemContext()
  const systems = allSystems.filter((s) => s.metadata?.source !== 'fallback')
  const evaluation = useEvaluation(evaluationId)
  const runnable = !!evaluation.data?.runnable
  const [picked, setPicked] = useState<string | null>(null)
  const fallback = selectedSystem?.metadata?.source === 'fallback' ? '' : selectedSystem?.id ?? ''
  const systemId = picked ?? search.get('system') ?? fallback
  const system = systems.find((s) => s.id === systemId)
  const engine = useEngine(evaluationId, runnable, system ? systemId : undefined)
  const runs = useEngineRuns(evaluationId, runnable)
  const [openId, setOpenId] = useState<string | null>(null)
  const [fresh, setFresh] = useState<EngineRun | null>(null)
  const [chosenWay, setChosenWay] = useState<RunWay | null>(null)
  const [trace, setTrace] = useState<{ id: string; flag?: string } | null>(null)
  const opened = useEngineRun(fresh ? null : openId)
  const shown = fresh ?? opened.data

  const choose = (id: string) => {
    setPicked(id)
    setChosenWay(null)
    const q = new URLSearchParams(search.toString())
    q.set('system', id)
    router.replace(`${pathname}?${q.toString()}`, { scroll: false })
  }

  if (evaluation.loading && !evaluation.data) return <Loading label="Loading evaluation" />
  if (evaluation.error || !evaluation.data) {
    return (
      <div className="flex flex-col gap-4">
        <Crumbs items={[{ label: 'Evaluations', href: '/evaluations' }, { label: evaluationId }]} />
        <ErrorNote message={`This evaluation could not be loaded. ${evaluation.error ?? ''}`} onRetry={evaluation.reload} />
      </div>
    )
  }
  const e = evaluation.data
  const spec = engine.data
  const ways = spec?.ways ?? []
  const asked = search.get('source') === 'traces' ? 'live_runs' : null
  // An engine with no way listed (FairMind's own agent) runs as it always has.
  const way: RunWay | null = spec ? (chosenWay && ways.some((w) => w.way === chosenWay) ? chosenWay : defaultWay(ways, asked) ?? 'files') : null
  const behaviour = spec && way === 'calls_system' ? (spec.live === 'target' ? spec : spec.alternate?.live === 'target' ? spec.alternate : null) : null
  const runSpec = behaviour ?? spec
  const kind = spec?.kind ?? null
  const KindIcon = KIND_ICON[kind ?? ''] ?? Cpu
  const mine = (runs.data ?? []).filter((r) => !system || r.systemId === system.id)
  const live = !!runSpec?.live
  const kept = way ? keptAs(way, live, !!spec?.liveRunsEngine) : null
  // the stored run is model judged when a live engine runs, a judged platform check reads the platform, or live runs are replayed
  const judged = live || (way === 'platform' && !!runSpec?.judge) || (way === 'live_runs' && !!spec?.liveRunsEngine)
  const showPasses = !(way === 'files' && runSpec && !runSpec.live && runSpec.slots.length > 0)

  return (
    <div className="fm-ev-run">
      <Crumbs items={[{ label: 'Evaluations', href: `/evaluations${system ? `?system=${encodeURIComponent(system.id)}` : ''}` }, { label: e.name }]} />
      <Heading title={e.name} lead={e.measures} />
      <div className="flex flex-wrap gap-2">
        <Pill>{e.id}</Pill>
        {!runnable ? <EnginePill engine={e.engine} /> : way && system ? <Pill tone="done" dot>{way === 'files' && live ? 'Runs live' : WAY_HEAD[way]}</Pill> : <Pill tone="done" dot>Runs in FairMind</Pill>}
        {e.judgeNotValidated && <Pill>Judge not validated</Pill>}
        {e.results && e.results.status !== 'not_run' && <ResultPill status={e.results.status} />}
      </div>

      {runnable && (
        <div className="fm-ev-card fm-ev-sysbar">
          <span className="fm-ev-sysicon" aria-hidden><KindIcon size={20} /></span>
          <div className="fm-ev-grow">
            <Selector
              label="Testing"
              placeholder={systems.length ? 'Choose a system' : 'No systems registered'}
              options={systems.map((s) => ({ value: s.id, label: s.name }))}
              value={system ? system.id : undefined}
              onChange={choose}
              isDisabled={systems.length === 0}
            />
          </div>
          <div className="fm-ev-chips">
            {system && spec && <Token size="sm" color={kind ? 'blue' : 'gray'} label={kind ? KIND_LABEL[kind] ?? kind : 'Kind not set'} />}
            {spec?.fit === 'other' && ways.length > 0 && <Token size="sm" color="orange" label={`Meant for ${e.appliesTo || 'another kind'}`} />}
            {ways.map((w) => WAY_STATE[w.way] && (
              <Token key={w.way} size="sm" color={w.ready ? 'green' : w.way === 'calls_system' ? 'orange' : 'gray'} label={w.reason ? 'Runner only' : WAY_STATE[w.way]![w.ready ? 0 : 1]} />
            ))}
          </div>
        </div>
      )}
      {runnable && systems.length === 0 && (
        <span className={`text-xs ${MUTED}`}>
          Register an AI system first: <Link href="/onboard" className="font-semibold underline">Register a system</Link>
        </span>
      )}

      <div className="fm-ev-run-grid">
        <div className="fm-ev-stack fm-ev-run-main">
          {!runnable ? (
            <section className="fm-ev-card">
              <h2 className="fm-ev-h2">Not runnable in FairMind yet</h2>
              <p className="fm-ev-muted">FairMind cannot run this evaluation yet. It needs a connection to the system&apos;s platform or evidence FairMind does not collect.</p>
            </section>
          ) : !system ? null : engine.error ? (
            <ErrorNote message={engine.error} onRetry={engine.reload} />
          ) : !spec || !runSpec || !way ? (
            <Loading label="Loading" />
          ) : spec.fit === 'unknown' && ways.length > 0 ? (
            <KindPrompt
              system={system}
              onSaved={() => {
                engine.reload()
                void refreshSystems()
              }}
            />
          ) : (
            <>
              {ways.length > 1 && (
                <SegmentedControl label="Run by" value={way} onChange={(v) => setChosenWay(v as RunWay)} size="sm">
                  {ways.map((w) => {
                    const Icon = WAY_ICON[w.way]
                    const off = !w.ready && (w.way === 'live_runs' || w.way === 'platform' || w.way === 'fairmind_data')
                    return <SegmentedControlItem key={w.way} value={w.way} label={off ? `${WAY_LABEL[w.way]}, ${w.reason ? 'runner only' : 'none yet'}` : WAY_LABEL[w.way]} icon={<Icon size={14} aria-hidden />} isDisabled={off} />
                  })}
                </SegmentedControl>
              )}
              {ways.map((w) => !w.ready && w.reason && <span key={w.way} className="fm-ev-muted fm-ev-small">{w.reason}.</span>)}
              <RunForm
                key={`${system.id}-${way}`}
                evaluationId={e.id}
                spec={runSpec}
                live={!!behaviour && behaviour !== spec}
                way={way}
                liveRunsOwn={way === 'live_runs' ? spec.liveRunsEngine ?? null : null}
                system={{ id: system.id, name: system.name, kind }}
                threshold={e.threshold}
                onDone={(run) => {
                  setFresh(run)
                  setOpenId(run.id)
                  runs.reload()
                  evaluation.reload()
                }}
              />
            </>
          )}
        </div>

        <aside className="fm-ev-stack fm-ev-run-side" aria-label="About this evaluation">
          {showPasses && (
            <SideCard label="Passes when">
              <span className="fm-ev-big">{e.threshold || '-'}</span>
              {e.metric && <span className="fm-ev-muted fm-ev-small">{e.metric}</span>}
            </SideCard>
          )}
          <SideCard label="Counts toward">
            <span><span className="fm-ev-num">{e.tests.length}</span> <span className="fm-ev-muted">{e.tests.length === 1 ? 'requirement' : 'requirements'}</span></span>
            {e.tests.length > 0 && (
              <details className="fm-ev-details">
                <summary>See them</summary>
                <ul>
                  {e.tests.map((t) => (
                    <li key={t.key}>{t.framework} {t.control}: {t.title}</li>
                  ))}
                </ul>
              </details>
            )}
          </SideCard>
          {runnable && way && kept && (
            <SideCard label="Kept as">
              <span className="fm-ev-chips">
                <Token size="sm" color={kept === 'Measured live' ? 'green' : 'gray'} label={kept} />
                {judged && <Token size="sm" color="gray" label="Model judged" />}
              </span>
              {way === 'files' && !live && <span className="fm-ev-muted fm-ev-small">File hashes sealed</span>}
              {live && way !== 'live_runs' && <span className="fm-ev-muted fm-ev-small">Every verdict is stored with the run.</span>}
            </SideCard>
          )}
          <SideCard label="About">
            <MetadataList columns="single" label={{ position: 'start', width: 80 }}>
              <MetadataListItem label="Applies to">{e.appliesTo || 'Not stated'}</MetadataListItem>
              <MetadataListItem label="Pack">{e.pack.name}</MetadataListItem>
            </MetadataList>
          </SideCard>
          {runnable && (
            <SideCard label={system ? 'Runs on this system' : 'Runs'}>
              {runs.data && mine.length === 0 && <span className="fm-ev-muted fm-ev-small">None yet</span>}
              <ul className="fm-ev-runs">
                {mine.map((r) => (
                  <li key={r.id}>
                    <button
                      type="button"
                      aria-pressed={openId === r.id}
                      onClick={() => {
                        setFresh(null)
                        setOpenId(r.id)
                      }}
                    >
                      <ResultPill status={r.status} />
                      {!system && <span>{r.systemName}</span>}
                      <span className="fm-ev-muted">{when(r.createdAt)}</span>
                    </button>
                  </li>
                ))}
              </ul>
            </SideCard>
          )}
        </aside>
      </div>

      {runnable && shown && (
        <section className="rounded-2xl bg-white p-5">
          <h2 className="mb-3 mt-0 text-base font-semibold text-[var(--fm-ink)]">Result</h2>
          {shown.source === 'traces' && e.id === 'EV-OVS-04' ? (
            <div className="flex flex-col gap-4">
              <div className="flex flex-wrap items-center gap-2.5">
                <ResultPill status={shown.status} />
                <span className={`text-[13px] ${MUTED}`}>{shown.systemName}, {when(shown.createdAt)}, from live runs{shown.judge && `, judged by ${shown.judge.model}`}</span>
              </div>
              <p className="m-0 leading-normal text-[var(--fm-ink)]">{shown.summary}</p>
              <ExplanationResult run={shown} onTrace={(id, flag) => setTrace({ id, flag })} />
            </div>
          ) : <RunResult run={shown} onTrace={(row) => setTrace({ id: String(row.traceId), flag: typeof row.reason === 'string' && row.verdict !== 'grounded' ? row.reason : Array.isArray(row.reasons) ? row.reasons.join('; ') : undefined })} />}
          {shown.review && !shown.reviewOf && shown.status === 'insufficient' && (
            <div className="mt-4">
              <ReviewList key={shown.id} run={shown} onReviewed={(run) => { setFresh(run); setOpenId(run.id); runs.reload() }} />
            </div>
          )}
          <div className="mt-4 flex flex-wrap gap-2">
            <Link href={`/systems/${encodeURIComponent(shown.systemId)}`} className={BTN_P}>Open the system file</Link>
            <Link href={`/risks?system=${encodeURIComponent(shown.systemId)}`} className={BTN}>Open findings</Link>
          </div>
        </section>
      )}
      {shown && (
        <Drawer isOpen={trace !== null} onOpenChange={(o) => !o && setTrace(null)} label="Live run" width={560} padding={5}>
          {trace && (
            <div className="flex flex-col gap-4">
              <h2 className="m-0 text-lg font-semibold text-[var(--fm-ink)]">Live run</h2>
              <TraceView systemId={shown.systemId} traceId={trace.id} flag={trace.flag} />
            </div>
          )}
        </Drawer>
      )}
    </div>
  )
}
