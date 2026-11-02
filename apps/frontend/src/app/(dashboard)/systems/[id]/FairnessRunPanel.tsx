'use client'

import { useRef, useState } from 'react'
import type { CsvInspection, FairnessMapping, FairnessRunResult } from '@/lib/api/hooks/useSystemFile'
import { cn } from '@/lib/utils'

const field = 'h-9 w-full rounded-[10px] border border-[rgba(21,23,26,.14)] bg-white px-2.5 text-[13px] outline-none focus:border-[var(--fm-ink)]'
const label = 'block text-[11.5px] font-medium text-[var(--fm-ink2)]'

function pct(v: number) {
  return `${Math.round(v * 100)}%`
}
function num(v: number) {
  return v.toFixed(3)
}

/**
 * The first verdict: a predictions CSV in, measured fairness evidence out.
 * Three states: pick a file, confirm the column mapping, read the result.
 */
export function FairnessRunPanel({
  inspect,
  run,
  onDone,
}: {
  inspect: (file: File) => Promise<CsvInspection>
  run: (file: File, mapping: FairnessMapping) => Promise<FairnessRunResult>
  onDone?: (result: FairnessRunResult) => void
}) {
  const fileRef = useRef<HTMLInputElement>(null)
  const [file, setFile] = useState<File | null>(null)
  const [inspection, setInspection] = useState<CsvInspection | null>(null)
  const [mapping, setMapping] = useState<FairnessMapping>({ outcome: '', attributes: [] })
  const [result, setResult] = useState<FairnessRunResult | null>(null)
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
      setMapping({
        outcome: info.suggested.outcome ?? '',
        prediction: info.suggested.prediction ?? undefined,
        score: info.suggested.score ?? undefined,
        attributes: info.suggested.attributes,
      })
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
      const out = await run(file, mapping)
      setResult(out)
      onDone?.(out)
    } catch (e) {
      setError(e instanceof Error ? e.message : 'The run failed')
    } finally {
      setBusy(null)
    }
  }

  const toggleAttribute = (name: string) =>
    setMapping((m) => ({ ...m, attributes: m.attributes.includes(name) ? m.attributes.filter((a) => a !== name) : [...m.attributes, name] }))

  const canRun = Boolean(file && mapping.outcome && (mapping.prediction || mapping.score) && mapping.attributes.length > 0)

  return (
    <div className="grid gap-3 rounded-[12px] border border-[var(--fm-line)] bg-[var(--fm-bg)] p-4 sm:col-span-2 xl:col-span-3">
      <div className="flex flex-wrap items-center justify-between gap-2">
        <div>
          <div className="text-[13.5px] font-semibold">Fairness test from predictions</div>
          <div className="text-[12px] text-[var(--fm-ink2)]">
            A CSV with one row per decision: the outcome, the model&apos;s prediction or score, and the protected attributes. Nothing leaves this backend.
          </div>
        </div>
        <label className="inline-flex h-9 cursor-pointer items-center rounded-full bg-[var(--fm-ink)] px-4 text-[12.5px] font-semibold text-white">
          {file ? 'Choose another file' : 'Choose CSV'}
          <input ref={fileRef} type="file" accept=".csv,text/csv" className="sr-only" onChange={(e) => void pick(e.target.files?.[0] ?? null)} />
        </label>
      </div>

      {file && (
        <div className="text-[12px] text-[var(--fm-ink2)]">
          {file.name}
          {inspection && ` · ${inspection.rows.toLocaleString()} rows · ${inspection.columns.length} columns`}
          {busy === 'inspect' && ' · reading'}
        </div>
      )}

      {inspection && !result && (
        <div className="grid gap-3">
          <div className="grid gap-3 sm:grid-cols-3">
            <div>
              <label className={label} htmlFor="fr-outcome">Outcome (what happened)</label>
              <select id="fr-outcome" value={mapping.outcome} onChange={(e) => setMapping((m) => ({ ...m, outcome: e.target.value }))} className={field}>
                <option value="">Choose a column</option>
                {columns.map((c) => <option key={c} value={c}>{c}</option>)}
              </select>
            </div>
            <div>
              <label className={label} htmlFor="fr-prediction">Prediction (0 or 1)</label>
              <select id="fr-prediction" value={mapping.prediction ?? ''} onChange={(e) => setMapping((m) => ({ ...m, prediction: e.target.value || undefined }))} className={field}>
                <option value="">None, use the score</option>
                {columns.map((c) => <option key={c} value={c}>{c}</option>)}
              </select>
            </div>
            <div>
              <label className={label} htmlFor="fr-score">Score (0 to 1, optional)</label>
              <select id="fr-score" value={mapping.score ?? ''} onChange={(e) => setMapping((m) => ({ ...m, score: e.target.value || undefined }))} className={field}>
                <option value="">None</option>
                {columns.map((c) => <option key={c} value={c}>{c}</option>)}
              </select>
            </div>
          </div>
          <div>
            <div className={label}>Protected attributes</div>
            <div className="mt-1 flex flex-wrap gap-1.5">
              {inspection.columns
                .filter((c) => c.name !== mapping.outcome && c.name !== mapping.prediction && c.name !== mapping.score && c.distinct <= 50)
                .map((c) => {
                  const on = mapping.attributes.includes(c.name)
                  return (
                    <button
                      key={c.name}
                      type="button"
                      onClick={() => toggleAttribute(c.name)}
                      className={cn('rounded-full border px-2.5 py-1 text-[12px]', on ? 'border-[var(--fm-ink)] bg-[var(--fm-ink)] text-white' : 'border-[var(--fm-line)] bg-white text-[var(--fm-ink2)]')}
                      title={`${c.distinct} distinct: ${c.sample.join(', ')}`}
                    >
                      {c.name}
                    </button>
                  )
                })}
            </div>
          </div>
          <div className="flex items-center gap-3">
            <button type="button" disabled={!canRun || busy !== null} onClick={() => void go()} className="h-9 rounded-full bg-[var(--fm-ink)] px-4 text-[12.5px] font-semibold text-white disabled:opacity-60">
              {busy === 'run' ? 'Running' : 'Run fairness test'}
            </button>
            <span className="text-[11.5px] text-[var(--fm-ink3)]">Bootstrap intervals and permutation tests; a minute at most for large files.</span>
          </div>
        </div>
      )}

      {error && <p className="rounded-[10px] bg-[#fde9ea] px-3 py-2 text-[12.5px] text-[#b4232c]">{error}</p>}

      {result && (
        <div className="grid gap-3">
          <div className="text-[13px]">
            <span className={cn('font-semibold', result.result.all_checks_pass ? 'text-[#1f7a4d]' : 'text-[#b4232c]')}>
              {result.result.all_checks_pass ? 'All checks within thresholds' : 'At least one check outside thresholds'}
            </span>
            <span className="text-[var(--fm-ink2)]">
              {' '}· {result.result.rows.toLocaleString()} rows · evidence confidence {result.result.evidence_confidence.toFixed(2)} (measured) · saved as evidence
            </span>
          </div>
          <div className="overflow-x-auto">
            <table className="w-full min-w-[640px] text-[12.5px]">
              <thead className="text-left text-[11px] uppercase tracking-wide text-[var(--fm-ink3)]">
                <tr>
                  <th className="pb-1.5 font-medium">Attribute</th>
                  <th className="pb-1.5 font-medium">Groups</th>
                  <th className="pb-1.5 text-right font-medium">Impact ratio</th>
                  <th className="pb-1.5 text-right font-medium">Equal opp. gap</th>
                  <th className="pb-1.5 text-right font-medium">Eq. odds gap</th>
                  <th className="pb-1.5 text-right font-medium">Calibration gap</th>
                </tr>
              </thead>
              <tbody>
                {result.result.attributes.map((a) => (
                  <tr key={a.attribute} className="border-t border-[var(--fm-line)] align-top">
                    <td className="py-2 font-medium">
                      {a.attribute}
                      {a.small_groups.length > 0 && <div className="text-[11px] font-normal text-[#a14d00]">Small groups: {a.small_groups.join(', ')}</div>}
                    </td>
                    <td className="py-2 text-[var(--fm-ink2)]">
                      {Object.entries(a.selection_rates).map(([g, r]) => (
                        <div key={g} className="tabular-nums">{g}: {pct(r)} selected of {a.groups[g]}</div>
                      ))}
                    </td>
                    <td className={cn('py-2 text-right tabular-nums', !a.checks.disparate_impact && 'text-[#b4232c] font-semibold')}>{num(a.disparate_impact_ratio)}</td>
                    <td className={cn('py-2 text-right tabular-nums', !a.checks.equal_opportunity && 'text-[#b4232c] font-semibold')}>
                      {num(a.equal_opportunity.value)}
                      <div className="text-[11px] font-normal text-[var(--fm-ink3)]">{num(a.equal_opportunity.confidence_interval[0])} to {num(a.equal_opportunity.confidence_interval[1])}</div>
                    </td>
                    <td className={cn('py-2 text-right tabular-nums', !a.checks.equalized_odds && 'text-[#b4232c] font-semibold')}>
                      {num(a.equalized_odds.value)}
                      <div className="text-[11px] font-normal text-[var(--fm-ink3)]">{num(a.equalized_odds.confidence_interval[0])} to {num(a.equalized_odds.confidence_interval[1])}</div>
                    </td>
                    <td className={cn('py-2 text-right tabular-nums', a.calibration && !a.checks.calibration && 'text-[#b4232c] font-semibold')}>
                      {a.calibration ? num(a.calibration.value) : <span className="text-[var(--fm-ink3)]">No score column</span>}
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
          <div className="text-[11.5px] text-[var(--fm-ink3)]">
            Thresholds: impact ratio at or above {result.result.thresholds.disparate_impact_ratio} (four-fifths rule), gaps at or below {result.result.thresholds.gap}. Intervals are 95% bootstrap.
          </div>
          <div>
            <button type="button" onClick={() => void pick(null)} className="text-[12.5px] font-medium text-[var(--fm-ink2)] underline-offset-2 hover:underline">Run another file</button>
          </div>
        </div>
      )}
    </div>
  )
}
