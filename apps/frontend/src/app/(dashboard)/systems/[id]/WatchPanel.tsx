'use client'

import { useState } from 'react'
import Link from 'next/link'
import type { MonitoringPolicy, MonitoringRunSummary } from '@/lib/api/hooks/useSystemFile'
import type { LiveRunSummary } from '@/lib/api/hooks/usePacks'
import { cn } from '@/lib/utils'

const CADENCES = [
  { hours: 24, label: 'Daily', cron: '0 6 * * *' },
  { hours: 168, label: 'Weekly', cron: '0 6 * * 1' },
  { hours: 720, label: 'Monthly', cron: '0 6 1 * *' },
]
const STALE_AFTER_CADENCES = 1.5
const TREND_LENGTH = 10

function cronFor(hours: number) {
  return (CADENCES.find((c) => c.hours >= hours) ?? CADENCES[CADENCES.length - 1]).cron
}

function age(iso: string) {
  const hours = (Date.now() - new Date(iso).getTime()) / 3_600_000
  if (hours >= 48) return `${Math.floor(hours / 24)} days ago`
  if (hours >= 1) return `${Math.floor(hours)} hours ago`
  return 'under an hour ago'
}

function shortDate(iso: string) {
  return new Date(iso).toLocaleDateString('en-GB', { day: 'numeric', month: 'short' })
}

export function workflow(systemId: string, cron: string, attributes: string[]) {
  const columns = attributes.length ? attributes.join(',') : '${{ vars.FAIRMIND_ATTRIBUTES }}'
  return `name: FairMind monitoring
on:
  schedule:
    - cron: "${cron}"
  workflow_dispatch:

jobs:
  monitor:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - uses: actions/setup-python@v5
        with:
          python-version: "3.12"
      - name: Export recent production decisions
        run: python scripts/export_decisions.py --out artifacts/decisions.csv
      - name: Record a monitoring snapshot
        env:
          FAIRMIND_API_URL: \${{ vars.FAIRMIND_API_URL }}
          FAIRMIND_API_KEY: \${{ secrets.FAIRMIND_API_KEY }}
        run: |
          pipx install fairmind-cli
          fairmind monitor --system ${systemId} --file artifacts/decisions.csv \\
            --attributes "${columns}" --prediction "\${{ vars.FAIRMIND_PREDICTION_COLUMN }}"
`
}

const SNAPSHOT_CHECKS: Record<string, string> = { disparate_impact: 'impact ratio', selection_rate_stable: 'selection-rate drift', score_stable: 'score drift' }

/** A snapshot's bar label: the lowest impact ratio, then the checks it actually failed, which may be drift rather than the ratio. */
export function snapshotLabel(run: Pick<MonitoringRunSummary, 'allChecksPass' | 'attributes'>, ratio: number | null): string {
  const lead = `Lowest impact ratio ${ratio === null ? 'not available' : ratio.toFixed(2)}`
  if (run.allChecksPass === null) return `${lead}, check result not recorded`
  if (run.allChecksPass) return `${lead}, all checks within thresholds`
  const failing = run.attributes.flatMap((a) => Object.entries(a.checks ?? {}).filter(([, ok]) => !ok).map(([k]) => `${a.attribute} ${SNAPSHOT_CHECKS[k] ?? k.replace(/_/g, ' ')}`))
  return `${lead}, outside thresholds: ${failing.length ? failing.join(', ') : 'at least one check'}`
}

const LIVE_RUN_EVALUATIONS: Record<string, string> = {
  'EV-MON-02': 'Tool calls', 'EV-TST-03': 'Groundedness', 'EV-DAT-01': 'Prompt drift', 'EV-AGT-02': 'Out-of-scope actions',
  'EV-TST-06': 'Tool-call correctness', 'EV-MON-05': 'Runaway loops', 'EV-SEC-16': 'Secrets in context',
}
const RESULT_TONE: Record<string, string> = { passed: 'text-[#1f7a4d]', failed: 'text-[#b4232c]', insufficient: 'text-[var(--fm-ink2)]' }

export const traceSnippet = (systemId: string) => `from fairmind import FairMind

fm = FairMind()
fm.record_trace("${systemId}", run_id, steps=steps, status="ok")
`

/** Live runs the system's own code sends: runs per day with errors, the last run, and the evaluations that read them. */
function LiveRuns({ systemId, live, onCopy, copied }: { systemId: string; live: LiveRunSummary | null; onCopy: (text: string) => void; copied: boolean }) {
  const max = Math.max(1, ...(live?.days ?? []).map((d) => d.runs))
  const sending = !!live?.lastRunAt
  return (
    <div className="grid min-w-0 gap-3 rounded-[12px] border border-[var(--fm-line)] bg-[var(--fm-bg)] p-4">
      <div>
        <div className="text-[13.5px] font-semibold">Live runs</div>
        <div className="text-[12px] text-[var(--fm-ink2)]">
          {sending ? <>Last run {age(live.lastRunAt as string)}. Evaluations read the last 7 days.</> : 'None sent yet. Add the code below where your agent finishes a run.'}
        </div>
      </div>
      {sending && live && (
        <>
          <div className="flex flex-wrap gap-5 tabular-nums">
            <div><div className="text-[11px] font-medium uppercase tracking-wide text-[var(--fm-ink3)]">Last 7 days</div><div className="text-[18px] font-semibold">{live.week.runs.toLocaleString()}</div></div>
            <div><div className="text-[11px] font-medium uppercase tracking-wide text-[var(--fm-ink3)]">Errors</div><div className={`text-[18px] font-semibold ${live.week.errors ? 'text-[#b4232c]' : ''}`}>{live.week.errors.toLocaleString()}</div></div>
          </div>
          <div>
            <div className="text-[11px] font-medium uppercase tracking-wide text-[var(--fm-ink3)]">Runs per day, errors in red</div>
            <div className="mt-2 flex gap-1 overflow-x-auto">
              {live.days.map((d) => {
                const h = Math.round((40 * d.runs) / max)
                const e = d.runs ? Math.max(d.errors ? 2 : 0, Math.round((h * d.errors) / d.runs)) : 0
                return (
                  <div key={d.date} className="grid w-[22px] shrink-0 justify-items-center gap-0.5 text-[11px] tabular-nums text-[var(--fm-ink3)]">
                    <svg width="18" height="40" viewBox="0 0 18 40" role="img" aria-label={`${d.date}: ${d.runs} runs, ${d.errors} errors`}>
                      <rect x="0" y="0" width="18" height="40" rx="3" fill="var(--fm-line)" />
                      <rect x="0" y={40 - h} width="18" height={h} rx="3" fill="#1f7a4d" />
                      {e > 0 && <rect x="0" y={40 - h} width="18" height={e} rx="2" fill="#b4232c" />}
                    </svg>
                    <span>{Number(d.date.slice(8))}</span>
                  </div>
                )
              })}
            </div>
          </div>
          <div className="grid gap-1.5">
            {Object.entries(LIVE_RUN_EVALUATIONS).map(([id, name]) => {
              const run = live.evaluations.find((e) => e.evaluationId === id)
              return (
                <div key={id} className="flex flex-wrap items-center justify-between gap-2 text-[12.5px]">
                  <span><span className="font-semibold">{name}</span> <span className="text-[var(--fm-ink3)]">{id}</span>{' '}
                    {run ? <span className={RESULT_TONE[run.status] ?? ''}>{run.status}, {age(run.createdAt)}</span> : <span className="text-[var(--fm-ink2)]">not run on live runs yet</span>}
                  </span>
                  <Link href={`/compliance/evaluations/${id}?system=${encodeURIComponent(systemId)}&source=traces`} className="h-8 rounded-full border border-[var(--fm-line)] bg-white px-3 py-1.5 text-[12px] font-semibold">
                    {run ? 'Open' : 'Run on live runs'}
                  </Link>
                </div>
              )
            })}
          </div>
        </>
      )}
      <div className="grid gap-2">
        <div className="flex flex-wrap items-center justify-between gap-2">
          <div>
            <div className="text-[13px] font-semibold">Send live runs</div>
            <div className="text-[12px] text-[var(--fm-ink2)]">Add this where your agent finishes a run. The API key stays on your side.</div>
          </div>
          <button type="button" onClick={() => onCopy(traceSnippet(systemId))} className="h-9 rounded-full border border-[var(--fm-line)] bg-white px-4 text-[12.5px] font-semibold">
            {copied ? 'Copied' : 'Copy code'}
          </button>
        </div>
        <pre className="overflow-auto rounded-[10px] border border-[var(--fm-line)] bg-white p-3 text-[11.5px] leading-relaxed">{traceSnippet(systemId)}</pre>
      </div>
    </div>
  )
}

/** Expected cadence, snapshot age, the last snapshots as bars, and the cron job that keeps them coming; then live runs. */
export function WatchPanel({
  systemId,
  policy,
  runs,
  live = null,
  save,
}: {
  systemId: string
  policy: MonitoringPolicy | null
  runs: MonitoringRunSummary[]
  live?: LiveRunSummary | null
  save: (policy: { cadenceHours: number }) => Promise<unknown>
}) {
  const [saving, setSaving] = useState(false)
  const [error, setError] = useState<string | null>(null)
  const [copied, setCopied] = useState<'workflow' | 'code' | null>(null)
  const [now] = useState(() => Date.now())
  if (!policy) return null

  const latest = runs[0]
  const stale = latest ? now - new Date(latest.createdAt).getTime() > STALE_AFTER_CADENCES * policy.cadenceHours * 3_600_000 : false
  const options = CADENCES.some((c) => c.hours === policy.cadenceHours) ? CADENCES : [...CADENCES, { hours: policy.cadenceHours, label: `Every ${policy.cadenceHours} hours`, cron: cronFor(policy.cadenceHours) }]
  const trend = runs.slice(0, TREND_LENGTH).reverse().map((r) => {
    const ratio = r.attributes.length ? Math.min(...r.attributes.map((a) => a.disparateImpactRatio)) : null
    return {
      at: r.createdAt,
      ok: r.allChecksPass !== false,
      ratio,
      label: snapshotLabel(r, ratio),
      drift: r.attributes.reduce<number | null>((m, a) => (a.maxRateDrift === null || a.maxRateDrift === undefined ? m : Math.max(m ?? 0, a.maxRateDrift)), null),
    }
  })
  const snippet = workflow(systemId, cronFor(policy.cadenceHours), latest?.attributes.map((a) => a.attribute) ?? [])

  async function change(hours: number) {
    setSaving(true)
    setError(null)
    try {
      await save({ cadenceHours: hours })
    } catch (e) {
      setError(e instanceof Error ? e.message : 'Could not save the cadence')
    } finally {
      setSaving(false)
    }
  }

  async function copy(text = snippet, which: 'workflow' | 'code' = 'workflow') {
    try {
      await navigator.clipboard.writeText(text)
      setCopied(which)
      setTimeout(() => setCopied(null), 2000)
    } catch {
      setError('Copy is blocked by the browser; select the text and copy it')
    }
  }

  return (
    <div className="grid min-w-0 gap-4 sm:col-span-2 xl:col-span-3">
    <div className="grid min-w-0 gap-4 rounded-[12px] border border-[var(--fm-line)] bg-[var(--fm-bg)] p-4">
      <div className="flex flex-wrap items-end justify-between gap-3">
        <div>
          <div className="text-[13.5px] font-semibold">Watch</div>
          <div className="text-[12px] text-[var(--fm-ink2)]">
            {latest ? (
              <>Last snapshot {age(latest.createdAt)}{stale && <> · <span className="font-semibold text-[#b4232c]">stale</span>, the gate no longer counts it as proven</>}</>
            ) : (
              'No snapshot yet. Once one arrives the gate expects the next within one and a half cadences.'
            )}
          </div>
        </div>
        <div>
          <label className="block text-[11.5px] font-medium text-[var(--fm-ink2)]" htmlFor="watch-cadence">Expected cadence</label>
          <select id="watch-cadence" disabled={saving} value={policy.cadenceHours} onChange={(e) => void change(Number(e.target.value))} className="h-9 rounded-[10px] border border-[rgba(21,23,26,.14)] bg-white px-2.5 text-[13px] outline-none focus:border-[var(--fm-ink)]">
            {options.map((c) => <option key={c.hours} value={c.hours}>{c.label}</option>)}
          </select>
        </div>
      </div>
      {error && <p className="rounded-[10px] bg-[#fde9ea] px-3 py-2 text-[12.5px] text-[#b4232c]">{error}</p>}

      {trend.length > 0 && (
        <div>
          <div className="text-[11px] font-medium uppercase tracking-wide text-[var(--fm-ink3)]">Last {trend.length} snapshots, oldest to newest</div>
          <div className="mt-2 flex gap-2 overflow-x-auto">
            {trend.map((t) => (
              <div key={t.at} className="grid w-[58px] shrink-0 justify-items-center gap-0.5 text-[11.5px] tabular-nums">
                <svg width="28" height="40" viewBox="0 0 28 40" role="img" aria-label={t.label}>
                  <rect x="0" y="0" width="28" height="40" rx="4" fill="var(--fm-line)" />
                  <rect x="0" y={40 - 40 * Math.min(Math.max(t.ratio ?? 0, 0), 1)} width="28" height={40 * Math.min(Math.max(t.ratio ?? 0, 0), 1)} rx="4" fill={t.ok ? '#1f7a4d' : '#b4232c'} />
                </svg>
                <span className={cn('font-medium', !t.ok && 'text-[#b4232c]')}>{t.ratio === null ? 'n/a' : t.ratio.toFixed(2)}</span>
                <span className="text-[var(--fm-ink2)]">{t.drift === null ? 'n/a' : t.drift.toFixed(3)}</span>
                <span className="text-[var(--fm-ink3)]">{shortDate(t.at)}</span>
              </div>
            ))}
          </div>
          <div className="mt-1.5 text-[11.5px] text-[var(--fm-ink3)]">Per snapshot: lowest impact ratio across attributes (bar and first figure), then largest selection-rate drift, then the date.</div>
        </div>
      )}

      <div className="grid gap-2">
        <div className="flex flex-wrap items-center justify-between gap-2">
          <div>
            <div className="text-[13px] font-semibold">Schedule it</div>
            <div className="text-[12px] text-[var(--fm-ink2)]">
              Your side pushes the snapshot; FairMind stores no credentials. {policy.driftWindow} drifting snapshots in a row open a finding.
            </div>
          </div>
          <button type="button" onClick={() => void copy()} className="h-9 rounded-full border border-[var(--fm-line)] bg-white px-4 text-[12.5px] font-semibold">
            {copied === 'workflow' ? 'Copied' : 'Copy workflow'}
          </button>
        </div>
        <pre className="max-h-72 overflow-auto rounded-[10px] border border-[var(--fm-line)] bg-white p-3 text-[11.5px] leading-relaxed">{snippet}</pre>
        <div className="text-[11.5px] text-[var(--fm-ink3)]">
          Add the repository secret FAIRMIND_API_KEY and the variables FAIRMIND_API_URL and FAIRMIND_PREDICTION_COLUMN{latest ? '' : ', FAIRMIND_ATTRIBUTES'}. The job fails when a snapshot drifts, so your team hears about it in Actions as well.
        </div>
      </div>
    </div>
    <LiveRuns systemId={systemId} live={live} copied={copied === 'code'} onCopy={(text) => void copy(text, 'code')} />
    </div>
  )
}
