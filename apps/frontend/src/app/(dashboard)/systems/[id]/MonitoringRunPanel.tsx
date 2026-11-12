'use client'

import { useState } from 'react'
import type { CsvInspection, MonitoringMapping, MonitoringRunResult } from '@/lib/api/hooks/useSystemFile'
import { cn } from '@/lib/utils'

const field = 'h-9 w-full rounded-[10px] border border-[rgba(21,23,26,.14)] bg-white px-2.5 text-[13px] outline-none focus:border-[var(--fm-ink)]'
const label = 'block text-[11.5px] font-medium text-[var(--fm-ink2)]'

function num(v: number | null | undefined, digits = 3) {
  return v === null || v === undefined ? 'n/a' : v.toFixed(digits)
}

/** Current production decisions against the last fairness run: selection-rate drift, impact ratio, score PSI. */
export function MonitoringRunPanel({
  inspect,
  run,
  hasBaseline,
}: {
  inspect: (file: File) => Promise<CsvInspection>
  run: (file: File, mapping: MonitoringMapping) => Promise<MonitoringRunResult>
  hasBaseline: boolean
}) {
  const [file, setFile] = useState<File | null>(null)
  const [inspection, setInspection] = useState<CsvInspection | null>(null)
  const [mapping, setMapping] = useState<MonitoringMapping>({ attributes: [] })
  const [result, setResult] = useState<MonitoringRunResult | null>(null)
  const [busy, setBusy] = useState<'inspect' | 'run' | null>(null)
  const [error, setError] = useState<string | null>(null)
  const columns = inspection?.columns.map((c) => c.name) ?? []

  async function pick(f: File | null) {
    setResult(null)
    setInspection(null)
    setError(null)
    setFile(f)
    if (!f) return
    setBusy('inspect')
    try {
      const info = await inspect(f)
      setInspection(info)
      setMapping({ prediction: info.suggested.prediction ?? undefined, score: info.suggested.score ?? undefined, attributes: info.suggested.attributes })
    } catch (e) {
      setError(e instanceof Error ? e.message : 'Could not read the file')
    } finally {
      setBusy(null)
    }
  }

  async function go() {
    if (!file) return
    setBusy('run')
    setError(null)
    try {
      setResult(await run(file, mapping))
    } catch (e) {
      setError(e instanceof Error ? e.message : 'The run failed')
    } finally {
      setBusy(null)
    }
  }

  const canRun = Boolean(file && (mapping.prediction || mapping.score) && mapping.attributes.length > 0)

  return (
    <div className="grid min-w-0 gap-3 rounded-[12px] border border-[var(--fm-line)] bg-[var(--fm-bg)] p-4 sm:col-span-2 xl:col-span-3">
      <div className="flex flex-wrap items-center justify-between gap-2">
        <div>
          <div className="text-[13.5px] font-semibold">Monitoring snapshot from production decisions</div>
          <div className="text-[12px] text-[var(--fm-ink2)]">
            A CSV of recent decisions with the model&apos;s prediction or score and the protected attributes.{' '}
            {hasBaseline ? 'Compared against the latest fairness run.' : 'Run a fairness test first to have a baseline for drift; without one only current rates are measured.'}
          </div>
        </div>
        <label className="inline-flex h-9 cursor-pointer items-center rounded-full bg-[var(--fm-ink)] px-4 text-[12.5px] font-semibold text-white">
          {file ? 'Choose another file' : 'Choose CSV'}
          <input type="file" accept=".csv,text/csv" className="sr-only" onChange={(e) => void pick(e.target.files?.[0] ?? null)} />
        </label>
      </div>
      {file && <div className="text-[12px] text-[var(--fm-ink2)]">{file.name}{inspection && ` · ${inspection.rows.toLocaleString()} rows`}{busy === 'inspect' && ' · reading'}</div>}

      {inspection && !result && (
        <div className="grid gap-3">
          <div className="grid gap-3 sm:grid-cols-2">
            <div>
              <label className={label} htmlFor="mr-prediction">Prediction (0 or 1)</label>
              <select id="mr-prediction" value={mapping.prediction ?? ''} onChange={(e) => setMapping((m) => ({ ...m, prediction: e.target.value || undefined }))} className={field}>
                <option value="">None, use the score</option>
                {columns.map((c) => <option key={c} value={c}>{c}</option>)}
              </select>
            </div>
            <div>
              <label className={label} htmlFor="mr-score">Score (0 to 1)</label>
              <select id="mr-score" value={mapping.score ?? ''} onChange={(e) => setMapping((m) => ({ ...m, score: e.target.value || undefined }))} className={field}>
                <option value="">None</option>
                {columns.map((c) => <option key={c} value={c}>{c}</option>)}
              </select>
            </div>
          </div>
          <div>
            <div className={label}>Protected attributes</div>
            <div className="mt-1 flex flex-wrap gap-1.5">
              {inspection.columns.filter((c) => c.name !== mapping.prediction && c.name !== mapping.score && c.distinct <= 50).map((c) => {
                const on = mapping.attributes.includes(c.name)
                return (
                  <button key={c.name} type="button" onClick={() => setMapping((m) => ({ ...m, attributes: on ? m.attributes.filter((a) => a !== c.name) : [...m.attributes, c.name] }))}
                    className={cn('rounded-full border px-2.5 py-1 text-[12px]', on ? 'border-[var(--fm-ink)] bg-[var(--fm-ink)] text-white' : 'border-[var(--fm-line)] bg-white text-[var(--fm-ink2)]')}>
                    {c.name}
                  </button>
                )
              })}
            </div>
          </div>
          <div>
            <button type="button" disabled={!canRun || busy !== null} onClick={() => void go()} className="h-9 rounded-full bg-[var(--fm-ink)] px-4 text-[12.5px] font-semibold text-white disabled:opacity-60">
              {busy === 'run' ? 'Running' : 'Record snapshot'}
            </button>
          </div>
        </div>
      )}

      {error && <p className="rounded-[10px] bg-[#fde9ea] px-3 py-2 text-[12.5px] text-[#b4232c]">{error}</p>}

      {result && (
        <div className="grid gap-3">
          <div className="text-[13px]">
            <span className={cn('font-semibold', result.result.all_checks_pass ? 'text-[#1f7a4d]' : 'text-[#b4232c]')}>
              {result.result.all_checks_pass ? 'Stable against the baseline' : 'Drift or disparity outside thresholds'}
            </span>
            <span className="text-[var(--fm-ink2)]">
              {' '}· {result.result.rows.toLocaleString()} rows · overall score PSI {num(result.result.overall_psi)} · saved as monitoring evidence
            </span>
          </div>
          <div className="overflow-x-auto">
            <table className="w-full text-[12.5px]">
              <thead className="text-left text-[11px] uppercase tracking-wide text-[var(--fm-ink3)]">
                <tr><th scope="col" className="pb-1.5 font-medium">Attribute</th><th scope="col" className="pb-1.5 font-medium">Selection now vs baseline</th><th scope="col" className="pb-1.5 text-right font-medium">Max rate drift</th><th scope="col" className="pb-1.5 text-right font-medium">Impact ratio</th><th scope="col" className="pb-1.5 text-right font-medium">Worst PSI</th></tr>
              </thead>
              <tbody>
                {result.result.attributes.map((a) => (
                  <tr key={a.attribute} className="border-t border-[var(--fm-line)] align-top">
                    <td className="py-2 font-medium">{a.attribute}</td>
                    <td className="py-2 text-[var(--fm-ink2)]">
                      {Object.entries(a.selection_rates).map(([g, r]) => (
                        <div key={g} className="tabular-nums">{g}: {Math.round(r * 100)}%{a.baseline_selection_rates[g] !== undefined && ` (was ${Math.round(a.baseline_selection_rates[g] * 100)}%)`}</div>
                      ))}
                    </td>
                    <td className={cn('py-2 text-right tabular-nums', a.checks.selection_rate_stable === false && 'font-semibold text-[#b4232c]')}>{num(a.max_rate_drift)}</td>
                    <td className={cn('py-2 text-right tabular-nums', !a.checks.disparate_impact && 'font-semibold text-[#b4232c]')}>{num(a.disparate_impact_ratio)}</td>
                    <td className={cn('py-2 text-right tabular-nums', a.checks.score_stable === false && 'font-semibold text-[#b4232c]')}>{num(a.worst_psi)}</td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
          <div className="text-[11.5px] text-[var(--fm-ink3)]">
            Thresholds: rate drift at or below {result.result.thresholds.rate_drift}, impact ratio at or above {result.result.thresholds.disparate_impact_ratio}, PSI below {result.result.thresholds.psi_moderate} stable and above {result.result.thresholds.psi_significant} significant.
          </div>
          <button type="button" onClick={() => void pick(null)} className="justify-self-start text-[12.5px] font-medium text-[var(--fm-ink2)] underline-offset-2 hover:underline">Record another snapshot</button>
        </div>
      )}
    </div>
  )
}
