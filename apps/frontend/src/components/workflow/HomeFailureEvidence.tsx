'use client'

import { ArrowDown, ArrowRight } from 'lucide-react'
import Link from 'next/link'
import { useId } from 'react'
import { Button } from '@/components/ui/button'
import { checkEvidenceIds } from '@/components/workflow/CheckEvidenceLinks'
import { API_ENDPOINTS } from '@/lib/api/endpoints'
import { useOrgResource } from '@/lib/api/hooks/usePacks'
import type { GateCheck } from '@/lib/api/hooks/useSystemFile'
import { evidenceRecordHref } from '@/lib/assurance/evidenceLinks'
import './home-failure-breakdown.css'
import './failure-evidence.css'

type ProofCheck = Pick<GateCheck, 'label' | 'evidenceId' | 'failureEvidenceIds'>
type ProofRecord = { id: string; systemId: string; title: string; type: string; content: unknown }
type RecordState = { record: ProofRecord | null; loading: boolean }

const metrics = [
  { key: 'disparate_impact', label: 'Disparate impact ratio', minimum: true },
  { key: 'equal_opportunity', label: 'Equal opportunity gap', minimum: false },
  { key: 'equalized_odds', label: 'Equalized odds gap', minimum: false },
  { key: 'calibration', label: 'Calibration gap', minimum: false },
] as const

function object(value: unknown): Record<string, unknown> {
  return value !== null && typeof value === 'object' && !Array.isArray(value) ? value as Record<string, unknown> : {}
}

function finite(value: unknown): value is number {
  return typeof value === 'number' && Number.isFinite(value)
}

type FailedMetric = typeof metrics[number] & {
  attribute: string
  value: number
  threshold: number
  row: Record<string, unknown>
}

/** A threshold crossing alone can pass. Prefer an explicitly failed ratio, then the other failed measurements. */
function failedMeasurements(record: ProofRecord): FailedMetric[] {
  const content = object(record.content)
  if (record.type !== 'fairness_test' || !Array.isArray(content.attributes)) return []
  const failed: FailedMetric[] = []
  for (const spec of metrics) {
    for (const item of content.attributes) {
      const row = object(item)
      if (typeof row.attribute !== 'string' || !row.attribute.trim() || object(row.checks)[spec.key] !== false) continue
      const metric = object(row[spec.key])
      const value = metric.value ?? (spec.minimum ? row.disparate_impact_ratio : undefined)
      const threshold = metric.threshold ?? object(content.thresholds)[spec.minimum ? 'disparate_impact_ratio' : 'gap']
      if (!finite(value) || !finite(threshold) || metric.is_fair === true) continue
      const name = row.attribute === 'age_cat' ? 'Age group' : row.attribute.replaceAll('_', ' ')
      failed.push({ ...spec, attribute: name, row, value, threshold })
    }
  }
  return failed
}

function EvidenceMeasurement({ record }: { record: ProofRecord }) {
  const [measure] = failedMeasurements(record)
  if (!measure) {
    const { summary } = object(record.content)
    return typeof summary === 'string' && summary.trim() ? <p>{summary}</p> : null
  }
  const { value, threshold, minimum } = measure
  const showScale = minimum && value >= 0 && value <= 1 && threshold >= 0 && threshold <= 1
  const close = value !== threshold && value.toFixed(2) === threshold.toFixed(2)
  const observed = close ? String(value) : value.toFixed(2)
  const bound = minimum ? 'minimum' : 'maximum'
  return (
    <div className="fm-home-proof-measure">
      <span className="fm-home-proof-metric">{measure.label} · {measure.attribute}</span>
      <span className="fm-home-proof-values">
        <span className="sr-only">Observed {value}, {bound} {threshold}.</span>
        <span className="fm-observed" aria-hidden="true"><b title={String(value)}>{observed}</b> observed</span>
        <span className="fm-bound" aria-hidden="true">
          <b title={String(threshold)}>{close ? String(threshold) : threshold.toFixed(2)}</b> {bound}
        </span>
      </span>
      {showScale && (
        <span className="fm-home-proof-scale" aria-hidden="true">
          <i style={{ width: `${value * 100}%` }} />
          <b style={{ left: `${threshold * 100}%` }} />
        </span>
      )}
    </div>
  )
}

export function useHomeFailureRecord(systemId?: string, check?: ProofCheck): RecordState {
  const first = check && checkEvidenceIds(check, true)[0]
  const path = first && systemId
    ? `${API_ENDPOINTS.aiGovernance.evidenceItem(encodeURIComponent(first))}?${new URLSearchParams({ system_id: systemId })}`
    : null
  const { data, loading } = useOrgResource<ProofRecord>(path)
  return { record: data && data.id === first && data.systemId === systemId ? data : null, loading }
}

export function HomeFailureEvidence({ systemId, check, record, loading, showGroupComparison = true }: RecordState & {
  systemId: string
  check: ProofCheck
  showGroupComparison?: boolean
}) {
  const [first, ...others] = checkEvidenceIds(check, true)
  if (!first || !systemId) return <p className="fm-home-proof-detail">Source record unavailable.</p>
  const title = (typeof record?.title === 'string' && record.title.trim()) || `${check.label} evidence`
  return (
    <div className="fm-home-proof">
      <div className="fm-home-proof-detail">
        <strong>{title}</strong>
        {record && <EvidenceMeasurement record={record} />}
        {!record && !loading && <p>Record details unavailable.</p>}
      </div>
      <div className="fm-home-proof-links">
        <Button asChild size="lg" className="fm-home-proof-pill">
          <Link href={evidenceRecordHref(systemId, first)} aria-label={`Open evidence for ${title}`}>
            Open evidence <ArrowRight aria-hidden="true" />
          </Link>
        </Button>
        {showGroupComparison && failureBreakdown(record) && (
          <button type="button" className="fm-home-compare" aria-controls="home-selection-rates" onClick={() => {
            const chart = document.getElementById('home-selection-rates')
            chart?.focus({ preventScroll: true })
            chart?.scrollIntoView({ block: 'start' })
          }}>Compare groups <ArrowDown size={14} aria-hidden /></button>
        )}
        {others.map((id, index) => (
          <Link className="fm-home-proof-extra" key={id} href={evidenceRecordHref(systemId, id)}>
            Open evidence record {index + 2}
          </Link>
        ))}
      </div>
    </div>
  )
}

function sampleSize(value: unknown): string | null {
  return finite(value) && Number.isSafeInteger(value) && value > 0 ? value.toLocaleString('en-US') : null
}

function selectionGroups(row: Record<string, unknown>) {
  const rates = Object.entries(object(row.selection_rates))
  const sizes = object(row.groups)
  const groups = rates.flatMap(([label, rate]) =>
    label.trim() && finite(rate) && rate >= 0 && rate <= 1 ? [{ label, rate, size: sampleSize(sizes[label]) }] : [],
  )
  if (groups.length < 2 || groups.length !== rates.length) return []
  return groups.sort((a, b) => a.rate - b.rate || a.label.localeCompare(b.label))
}

function failureBreakdown(record: ProofRecord | null) {
  if (!record) return null
  for (const measure of failedMeasurements(record)) {
    if (measure.key !== 'disparate_impact') continue
    const groups = selectionGroups(measure.row)
    if (groups.length) return { measure, groups, rows: sampleSize(object(record.content).rows) }
  }
  return null
}

export function HomeFailureBreakdown({ record, systemName }: { record: ProofRecord | null; systemName: string }) {
  const heading = useId()
  const breakdown = failureBreakdown(record)
  if (!breakdown) return null
  const { measure, groups, rows } = breakdown
  const low = groups[0].rate
  const high = groups[groups.length - 1].rate
  const ratio = high > 0 ? (low / high).toFixed(2) : null
  return (
      <figure id="home-selection-rates" tabIndex={-1} className="fm-home-breakdown" aria-labelledby={heading}>
        <figcaption>
          <h2 id={heading}>Selection rate by {measure.attribute === 'Age group' ? 'age group' : measure.attribute}</h2>
          <p>{systemName}{rows && ` · ${rows} records`}</p>
        </figcaption>
        <ul className="fm-selection-groups">
          {groups.map(({ label, rate, size }) => (
            <li key={label}>
              <div className="fm-selection-group">
                <span>{label}</span>
                {size && <small>{size} records</small>}
              </div>
              <span className="fm-selection-track" aria-hidden="true">
                <i style={{ width: `${rate * 100}%` }} />
              </span>
              <strong>{(rate * 100).toFixed(1)}%</strong>
            </li>
          ))}
        </ul>
        <div className="fm-selection-axis" aria-hidden="true">
          <span>0%</span><span>50%</span><span>100%</span>
        </div>
        {ratio !== null && ratio === measure.value.toFixed(2) && (
          <p className="fm-selection-ratio"><span>Lowest rate ÷ highest rate</span>
            <strong>{(low * 100).toFixed(1)}% ÷ {(high * 100).toFixed(1)}% = {ratio}</strong>
          </p>
        )}
      </figure>
  )
}
