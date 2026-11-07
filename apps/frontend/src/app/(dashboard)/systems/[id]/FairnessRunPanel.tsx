'use client'

import { useRef, useState } from 'react'
import type { AttributeConfirmation, CsvInspection, FairnessMapping, FairnessRunResult } from '@/lib/api/hooks/useSystemFile'
import { Pill } from '@/components/packs/parts'
import { cn } from '@/lib/utils'
import { VerdictExplainer } from './VerdictExplainer'

const field = 'h-9 w-full rounded-[10px] border border-[rgba(21,23,26,.14)] bg-white px-2.5 text-[13px] outline-none focus:border-[var(--fm-ink)]'
const area = 'w-full rounded-[10px] border border-[rgba(21,23,26,.14)] bg-white px-2.5 py-2 text-[13px] outline-none focus:border-[var(--fm-ink)]'
const label = 'block text-[11.5px] font-medium text-[var(--fm-ink2)]'
const MIN_REASON = 12

type Column = CsvInspection['columns'][number]

/**
 * Grounds FairMind looks for and the column-name hint for each, copied from the backend (fairness_run_service
 * GROUNDS and ATTRIBUTE_HINTS) so the uncovered grounds shown here are the ones the server will ask a reason for.
 */
const GROUNDS = ['gender', 'age', 'caste or social category', 'religion', 'disability', 'language', 'marital status', 'region']
const HINTS: Record<string, string | null> = {
  gender: 'gender', sex: 'gender',
  age: 'age', age_band: 'age', age_group: 'age', dob: 'age', date_of_birth: 'age', birth_date: 'age', birthdate: 'age',
  caste: 'caste or social category', social_category: 'caste or social category',
  religion: 'religion', disability: 'disability', language: 'language', marital: 'marital status',
  region: 'region', state: 'region', district: 'region', urban_rural: 'region', city_tier: 'region',
  race: null, ethnicity: null, nationality: null,
}
const GENDER_VALUES = new Set(['m', 'f', 'male', 'female', 'x', 'other', 'transgender', 'nonbinary', 'non-binary'])
const RESERVATION_VALUES = new Set(['gen', 'general', 'obc', 'sc', 'st', 'ews'])
// Case matters: the backend reads Yes/No but not YES/NO as binary (TRUE/FALSE arrive as booleans, sampled "True"/"False").
const BINARY_VALUES = new Set(['0', '1', '0.0', '1.0', 'true', 'false', 'True', 'False', 'yes', 'no', 'Yes', 'No'])

function pct(v: number) {
  return `${Math.round(v * 100)}%`
}
function num(v: number) {
  return v.toFixed(3)
}
function on(iso: string | null) {
  return iso ? new Date(iso).toLocaleDateString('en-GB', { day: 'numeric', month: 'short', year: 'numeric' }) : ''
}

/** Lower-case words of a column name, split as the backend splits them: "applicantAgeBand" gives applicant, age, band; "DOBDate" gives dob, date. */
export function words(name: string): string[] {
  return (name.match(/[A-Z]+(?![a-z])|[A-Z]?[a-z]+|[0-9]+/g) ?? []).map((t) => t.toLowerCase())
}

/**
 * The one ground a column covers, by the backend's rules: values that look like reservation categories or gender
 * win, then the longest hint found as whole adjacent words of the name. A column the inspection gave no status
 * (it was mapped as outcome, prediction or score, or is no candidate) covers nothing.
 */
export function groundOf(c: Pick<Column, 'name' | 'distinct' | 'sample' | 'attribute'>): string | null {
  if (c.attribute.status === null) return null
  // ponytail: only the sampled values reach the browser, so value checks need every distinct value sampled; the server checks the whole column
  const values = c.distinct >= 2 && c.sample.length >= c.distinct ? c.sample.map((v) => v.trim().toLowerCase()) : []
  if (values.length && values.every((v) => RESERVATION_VALUES.has(v))) return 'caste or social category'
  if (values.length && values.every((v) => GENDER_VALUES.has(v))) return 'gender'
  if (c.name.trim().toLowerCase() === 'tier') return 'region'
  const ws = words(c.name)
  let best: [number, string] | null = null
  for (const hint of Object.keys(HINTS)) {
    const run = words(hint)
    const found = ws.some((_, i) => run.every((t, j) => ws[i + j] === t))
    if (found && (!best || run.length > best[0] || (run.length === best[0] && hint > best[1]))) best = [run.length, hint]
  }
  return best ? HINTS[best[1]] : null
}

/** Grounds none of the ticked columns covers. For display; the server recomputes it when the run is confirmed. */
export function uncoveredGrounds(columns: Column[], ticked: string[]): string[] {
  const covered = new Set(columns.filter((c) => ticked.includes(c.name)).map(groundOf))
  return GROUNDS.filter((g) => !covered.has(g))
}

/** True when the outcome is not 0/1, true/false or yes/no, so the run must be told which value is favourable. */
export function needsFavourable(sample: string[]): boolean {
  return sample.some((v) => !BINARY_VALUES.has(v))
}

/**
 * What a confirmed run sends and what it still needs. A column picked as outcome, prediction or score is not
 * sent as a protected attribute; if it was suggested, it counts as unticked and needs the removal reason.
 */
export function confirmState(inspection: CsvInspection, mapping: FairnessMapping, removalReason: string, uncoveredReason: string) {
  const mapped = new Set([mapping.outcome, mapping.prediction, mapping.score])
  const attributes = mapping.attributes.filter((a) => !mapped.has(a))
  const removed = inspection.suggested.attributes.filter((a) => !attributes.includes(a))
  const uncovered = uncoveredGrounds(inspection.columns, attributes)
  const outcomeSample = inspection.columns.find((c) => c.name === mapping.outcome)?.sample ?? []
  const favourable = Boolean(mapping.outcome) && needsFavourable(outcomeSample)
  const ready = Boolean(
    inspection.fileSha256 &&
      mapping.outcome &&
      (mapping.prediction || mapping.score) &&
      attributes.length > 0 &&
      (!favourable || mapping.favorableLabel) &&
      (removed.length === 0 || removalReason.trim().length >= MIN_REASON) &&
      (uncovered.length === 0 || uncoveredReason.trim().length >= MIN_REASON),
  )
  return { mapped, attributes, removed, uncovered, outcomeSample, favourable, ready }
}

/** "gender", "gender and age", "gender, age and region". */
export function listText(names: string[]): string {
  return names.length < 2 ? names.join('') : `${names.slice(0, -1).join(', ')} and ${names[names.length - 1]}`
}

/** Where the pre-ticked attributes came from. Reuse from an unconfirmed run never claims a person confirmed it. */
export function sourceLine(i: Pick<CsvInspection, 'attributeSource' | 'confirmedBy' | 'confirmedAt' | 'previousRunUnconfirmed'>): string {
  if (i.attributeSource === 'none') return 'No column looks like a protected attribute. Choose them.'
  if (i.attributeSource === 'inferred') return 'Suggested from column names and values. Check every row.'
  if (i.previousRunUnconfirmed || !i.confirmedBy) return 'Using the attributes from the last run.'
  return `Using the attributes ${i.confirmedBy} confirmed on ${on(i.confirmedAt)}. Change them if this file differs.`
}

/**
 * The first verdict: a predictions CSV in, measured fairness evidence out.
 * Three states: pick a file, confirm the column mapping and protected attributes, read the result.
 */
export function FairnessRunPanel({
  inspect,
  run,
  onDone,
}: {
  inspect: (file: File) => Promise<CsvInspection>
  run: (file: File, mapping: FairnessMapping, confirmation: AttributeConfirmation) => Promise<FairnessRunResult>
  onDone?: (result: FairnessRunResult) => void
}) {
  const fileRef = useRef<HTMLInputElement>(null)
  const [file, setFile] = useState<File | null>(null)
  const [inspection, setInspection] = useState<CsvInspection | null>(null)
  const [mapping, setMapping] = useState<FairnessMapping>({ outcome: '', attributes: [] })
  const [removalReason, setRemovalReason] = useState('')
  const [uncoveredReason, setUncoveredReason] = useState('')
  const [notTested, setNotTested] = useState<{ grounds: string[]; reason?: string } | null>(null)
  const [result, setResult] = useState<FairnessRunResult | null>(null)
  const [busy, setBusy] = useState<'inspect' | 'run' | null>(null)
  const [error, setError] = useState<string | null>(null)

  const columns = inspection?.columns.map((c) => c.name) ?? []
  const suggested = inspection?.suggested.attributes ?? []
  const state = inspection ? confirmState(inspection, mapping, removalReason, uncoveredReason) : null
  const { mapped, attributes, removed, uncovered, outcomeSample, favourable } = state ?? {
    mapped: new Set<string | undefined>(), attributes: [], removed: [], uncovered: [], outcomeSample: [], favourable: false,
  }
  const rank = (c: Column) => (suggested.includes(c.name) ? 0 : c.attribute.status === 'possible' ? 1 : c.attribute.status === 'too_many_values' ? 3 : 2)
  // Columns over 50 values stay hidden unless their name looks protected, then they show disabled with the bin hint.
  const rows = (inspection?.columns ?? [])
    .filter((c) => !mapped.has(c.name) && (c.distinct <= 50 || c.attribute.status === 'too_many_values'))
    .sort((a, b) => rank(a) - rank(b))

  async function pick(f: File | null) {
    setResult(null)
    setInspection(null)
    setError(null)
    setRemovalReason('')
    setUncoveredReason('')
    setNotTested(null)
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
    if (!file || !inspection) return
    setBusy('run')
    setError(null)
    const confirmation: AttributeConfirmation = {
      sha256: inspection.fileSha256,
      removalReason: removed.length ? removalReason.trim() : undefined,
      uncoveredReason: uncovered.length ? uncoveredReason.trim() : undefined,
    }
    try {
      const out = await run(file, { ...mapping, attributes }, confirmation)
      setNotTested(uncovered.length ? { grounds: uncovered, reason: confirmation.uncoveredReason } : null)
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

  const canRun = Boolean(file && state?.ready)

  return (
    <div id="first-verdict" className="grid gap-3 rounded-[12px] border border-[var(--fm-line)] bg-[var(--fm-bg)] p-4 sm:col-span-2 xl:col-span-3">
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
          {inspection?.fileSha256 && ` · fingerprint sha256 ${inspection.fileSha256.slice(0, 4)}…${inspection.fileSha256.slice(-4)}`}
          {busy === 'inspect' && ' · reading'}
        </div>
      )}

      {inspection && !result && (
        <div className="grid gap-3">
          <div className="grid gap-3 sm:grid-cols-3">
            <div>
              <label className={label} htmlFor="fr-outcome">Outcome (what happened)</label>
              <select id="fr-outcome" value={mapping.outcome} onChange={(e) => setMapping((m) => ({ ...m, outcome: e.target.value, favorableLabel: undefined }))} className={field}>
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
            {favourable && (
              <div>
                <label className={label} htmlFor="fr-favourable">Favourable value of {mapping.outcome}</label>
                <select id="fr-favourable" value={mapping.favorableLabel ?? ''} onChange={(e) => setMapping((m) => ({ ...m, favorableLabel: e.target.value || undefined }))} className={field}>
                  <option value="">Choose the value that counts as favourable</option>
                  {outcomeSample.map((v) => <option key={v} value={v}>{v}</option>)}
                </select>
              </div>
            )}
          </div>

          <div className="grid gap-2">
            <div className="text-[12.5px] font-semibold">Protected attributes</div>
            <p className="text-[12px] text-[var(--fm-ink2)]">{sourceLine(inspection)}</p>
            <div className="overflow-x-auto">
              <table className="w-full min-w-[640px] text-[12.5px]">
                <thead className="text-left text-[11px] uppercase tracking-wide text-[var(--fm-ink3)]">
                  <tr>
                    <th className="w-[84px] pb-1.5 font-medium">Protected</th>
                    <th className="pb-1.5 font-medium">Column</th>
                    <th className="pb-1.5 font-medium">Values</th>
                    <th className="pb-1.5 font-medium">Why it&apos;s listed</th>
                  </tr>
                </thead>
                <tbody>
                  {rows.map((c, i) => {
                    const ticked = mapping.attributes.includes(c.name)
                    const wasSuggested = suggested.includes(c.name)
                    const binning = c.attribute.status === 'too_many_values'
                    const id = `fr-attr-${i}`
                    return (
                      <tr key={c.name} className={cn('border-t border-[var(--fm-line)] align-top', wasSuggested && !ticked && 'bg-[#fffaf6]', binning && 'opacity-75')}>
                        <td className="py-2.5 pr-2">
                          <input id={id} type="checkbox" checked={ticked} disabled={binning} onChange={() => toggleAttribute(c.name)} className="h-[18px] w-[18px] accent-[var(--fm-ink)]" />
                          <label htmlFor={id} className="sr-only">{binning ? `${c.name} cannot be grouped` : `${c.name} is a protected attribute`}</label>
                        </td>
                        <td className="py-2.5 pr-2 font-semibold">
                          <span className="mr-1.5">{c.name}</span>
                          {wasSuggested && <Pill tone="run">suggested</Pill>}
                          {!wasSuggested && c.attribute.status === 'possible' && (
                            <span className="inline-flex rounded-full border border-[rgba(21,23,26,.12)] bg-white px-2.5 py-[2px] text-[11.5px] font-semibold text-[var(--fm-ink2)]">possible</span>
                          )}
                          {wasSuggested && !ticked && <span className="ml-1"><Pill tone="you">you unticked it</Pill></span>}
                        </td>
                        <td className="py-2.5 pr-2 text-[var(--fm-ink2)]">
                          {binning ? `${c.distinct.toLocaleString()} values` : `${c.distinct} · ${c.sample.join(', ')}${c.distinct > c.sample.length ? ' …' : ''}`}
                        </td>
                        <td className="py-2.5 pr-2 text-[var(--fm-ink2)]">
                          {binning ? (
                            <>
                              {c.attribute.basis ? `${c.attribute.basis}, but it has` : 'It looks protected but has'} too many values to group. Bin it into bands before upload.{' '}
                              <Pill tone="info">Automatic banding: coming soon</Pill>
                            </>
                          ) : (
                            c.attribute.basis ??
                            (wasSuggested && inspection.attributeSource === 'confirmed'
                              ? inspection.previousRunUnconfirmed || !inspection.confirmedBy
                                ? 'Used in the last run'
                                : `Confirmed by ${inspection.confirmedBy} on ${on(inspection.confirmedAt)}`
                              : '')
                          )}
                        </td>
                      </tr>
                    )
                  })}
                </tbody>
              </table>
            </div>
          </div>

          {removed.length > 0 && (
            <div className="grid gap-1 rounded-[10px] bg-[#fffaf6] p-3">
              <label className={label} htmlFor="fr-removal">
                {removed.length === 1 ? `Why isn't ${removed[0]} a protected attribute here?` : `Why aren't ${listText(removed)} protected attributes here?`} (required, {MIN_REASON} characters or more)
              </label>
              <textarea id="fr-removal" rows={2} minLength={MIN_REASON} value={removalReason} onChange={(e) => setRemovalReason(e.target.value)} className={area} />
            </div>
          )}

          {uncovered.length > 0 && (
            <div className="grid gap-2 rounded-[12px] border border-[var(--fm-line)] bg-white p-3">
              <div className="text-[12.5px] font-semibold">Grounds FairMind looks for that the ticked columns don&apos;t cover</div>
              <div className="flex flex-wrap gap-1.5">
                {uncovered.map((g) => (
                  <span key={g} className="rounded-full border border-[rgba(21,23,26,.12)] bg-white px-2.5 py-1 text-[12px] text-[var(--fm-ink2)]">{g}</span>
                ))}
              </div>
              <label className={label} htmlFor="fr-uncovered">Where are these tested, or why don&apos;t they apply? (required, {MIN_REASON} characters or more)</label>
              <textarea id="fr-uncovered" rows={2} minLength={MIN_REASON} value={uncoveredReason} onChange={(e) => setUncoveredReason(e.target.value)} className={area} />
              <div className="text-[12px] text-[var(--fm-ink2)]">The result will say &quot;Not tested: {listText(uncovered)}&quot;, with this reason.</div>
            </div>
          )}

          <div className="flex flex-wrap items-center gap-3">
            <button type="button" disabled={!canRun || busy !== null} onClick={() => void go()} className="h-9 rounded-full bg-[var(--fm-ink)] px-4 text-[12.5px] font-semibold text-white disabled:opacity-60">
              {busy === 'run' ? 'Running' : 'Confirm attributes and run'}
            </button>
            <span className="max-w-[640px] text-[11.5px] leading-[1.45] text-[var(--fm-ink3)]">
              {attributes.length === 0
                ? 'Tick the protected attributes to test.'
                : `You confirm ${listText(attributes)} ${attributes.length === 1 ? 'is the protected attribute' : 'are the protected attributes'} for this test. The suggestion, your changes, your reasons and the file fingerprint are saved with the result. Monitoring reuses these attributes.`}
            </span>
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
              {' '}· {result.result.rows.toLocaleString()} rows · evidence confidence {result.result.evidence_confidence.toFixed(2)} (measured) · saved as evidence · attributes confirmed by you
            </span>
          </div>
          {notTested && (
            <div className="text-[12.5px] text-[var(--fm-ink2)]">
              Not tested: {listText(notTested.grounds)}.{notTested.reason && ` ${notTested.reason}`}
            </div>
          )}
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
          <VerdictExplainer gate={result.gate} compact />
          <div>
            <button type="button" onClick={() => void pick(null)} className="text-[12.5px] font-medium text-[var(--fm-ink2)] underline-offset-2 hover:underline">Run another file</button>
          </div>
        </div>
      )}
    </div>
  )
}
