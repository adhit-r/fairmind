'use client'

import { useState } from 'react'
import type { MonitoringPolicy, MonitoringRunSummary } from '@/lib/api/hooks/useSystemFile'
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

function workflow(systemId: string, cron: string, attributes: string[]) {
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
          pipx install ./apps/cli
          fairmind monitor --system ${systemId} --file artifacts/decisions.csv \\
            --attributes "${columns}" --prediction "\${{ vars.FAIRMIND_PREDICTION_COLUMN }}"
`
}

/** Expected cadence, snapshot age, the last snapshots as bars, and the cron job that keeps them coming. */
export function WatchPanel({
  systemId,
  policy,
  runs,
  save,
}: {
  systemId: string
  policy: MonitoringPolicy | null
  runs: MonitoringRunSummary[]
  save: (policy: { cadenceHours: number }) => Promise<unknown>
}) {
  const [saving, setSaving] = useState(false)
  const [error, setError] = useState<string | null>(null)
  const [copied, setCopied] = useState(false)
  if (!policy) return null

  const latest = runs[0]
  const stale = latest ? Date.now() - new Date(latest.createdAt).getTime() > STALE_AFTER_CADENCES * policy.cadenceHours * 3_600_000 : false
  const options = CADENCES.some((c) => c.hours === policy.cadenceHours) ? CADENCES : [...CADENCES, { hours: policy.cadenceHours, label: `Every ${policy.cadenceHours} hours`, cron: cronFor(policy.cadenceHours) }]
  const trend = runs.slice(0, TREND_LENGTH).reverse().map((r) => ({
    at: r.createdAt,
    ok: r.allChecksPass !== false,
    ratio: r.attributes.length ? Math.min(...r.attributes.map((a) => a.disparateImpactRatio)) : null,
    drift: r.attributes.reduce<number | null>((m, a) => (a.maxRateDrift === null || a.maxRateDrift === undefined ? m : Math.max(m ?? 0, a.maxRateDrift)), null),
  }))
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

  async function copy() {
    try {
      await navigator.clipboard.writeText(snippet)
      setCopied(true)
      setTimeout(() => setCopied(false), 2000)
    } catch {
      setError('Copy is blocked by the browser; select the text and copy it')
    }
  }

  return (
    <div className="grid min-w-0 gap-4 rounded-[12px] border border-[var(--fm-line)] bg-[var(--fm-bg)] p-4 sm:col-span-2 xl:col-span-3">
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
                <svg width="28" height="40" viewBox="0 0 28 40" role="img" aria-label={`Impact ratio ${t.ratio === null ? 'not available' : t.ratio.toFixed(2)}, ${t.ok ? 'within thresholds' : 'outside thresholds'}`}>
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
            {copied ? 'Copied' : 'Copy workflow'}
          </button>
        </div>
        <pre className="max-h-72 overflow-auto rounded-[10px] border border-[var(--fm-line)] bg-white p-3 text-[11.5px] leading-relaxed">{snippet}</pre>
        <div className="text-[11.5px] text-[var(--fm-ink3)]">
          Add the repository secret FAIRMIND_API_KEY and the variables FAIRMIND_API_URL and FAIRMIND_PREDICTION_COLUMN{latest ? '' : ', FAIRMIND_ATTRIBUTES'}. The job fails when a snapshot drifts, so your team hears about it in Actions as well.
        </div>
      </div>
    </div>
  )
}
